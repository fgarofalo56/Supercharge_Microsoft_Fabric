"""
DOI Open Data Download
======================

Download real Department of the Interior (DOI) datasets as alternatives to
the synthetic ``DOIGenerator``.

Supported datasets
------------------
* **USGS Earthquakes** -- Real-time and historical earthquake catalog via the
  FDSN Event Web Service.  GeoJSON format, no API key required.
  Source: https://earthquake.usgs.gov/fdsnws/event/1/
* **USGS NWIS (Water Data)** -- Streamflow, groundwater, and water quality
  from the National Water Information System.  No API key required.
  Source: https://waterservices.usgs.gov/nwis/
* **NPS Park Visitation** -- National Park Service visitor use statistics
  from IRMA.  No API key required.
  Source: https://irma.nps.gov/Stats/
* **FWS ECOS Species Data** -- Endangered and threatened species listings
  from the Environmental Conservation Online System.  No API key required.
  Source: https://ecos.fws.gov/ecp/

Output schemas are aligned with ``DOIGenerator`` so that downstream medallion
notebooks work identically with either real or synthetic data.

Usage
-----
CLI::

    python -m data-generation.open_data.doi_download --dataset earthquakes --output-dir ./data/doi --start-date 2023-01-01 --min-magnitude 4.0
    python -m data-generation.open_data.doi_download --dataset water --output-dir ./data/doi --start-date 2023-06-01 --end-date 2023-06-30
    python -m data-generation.open_data.doi_download --dataset all --output-dir ./data/doi

Library::

    from data_generation.open_data.doi_download import download_earthquakes
    df = download_earthquakes("./data/doi", start_date="2023-01-01", min_magnitude=4.0)
"""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
USGS_EARTHQUAKE_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"
USGS_NWIS_API = "https://waterservices.usgs.gov/nwis"
NPS_STATS_BASE = "https://irma.nps.gov/Stats/SSRSReports"
FWS_ECOS_BASE = "https://ecos.fws.gov/ecp/report"

MAX_RETRIES = 3
BACKOFF_BASE = 2
REQUEST_TIMEOUT = 120
RATE_LIMIT_SLEEP = 0.5

# USGS NWIS common parameter codes
NWIS_PARAMETER_CODES = {
    "discharge": "00060",       # Discharge, cubic feet per second
    "gage_height": "00065",     # Gage height, feet
    "temperature": "00010",     # Temperature, water, degrees Celsius
    "dissolved_oxygen": "00300", # Dissolved oxygen, mg/L
    "ph": "00400",              # pH, standard units
    "conductance": "00095",     # Specific conductance, microsiemens/cm
    "turbidity": "63680",       # Turbidity, FNU
}

# Well-known NPS park codes for default downloads
DEFAULT_PARK_CODES = [
    "GRCA",  # Grand Canyon
    "YELL",  # Yellowstone
    "YOSE",  # Yosemite
    "ZION",  # Zion
    "GRTE",  # Grand Teton
    "ACAD",  # Acadia
    "GLAC",  # Glacier
    "OLYM",  # Olympic
    "ROMO",  # Rocky Mountain
    "GRSM",  # Great Smoky Mountains
]

# Default NWIS sites (major river gages across the US)
DEFAULT_NWIS_SITES = [
    "01646500",  # Potomac River at Little Falls
    "07010000",  # Mississippi River at St. Louis
    "09380000",  # Colorado River at Lees Ferry
    "12340000",  # Clark Fork at St. Regis, MT
    "02089500",  # Neuse River at Kinston, NC
    "05586100",  # Illinois River at Valley City, IL
    "11303500",  # San Joaquin River near Vernalis, CA
    "14211720",  # Willamette River at Portland, OR
]


# ---------------------------------------------------------------------------
# Retry helper
# ---------------------------------------------------------------------------
def _request_with_retry(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    stream: bool = False,
    timeout: int = REQUEST_TIMEOUT,
) -> requests.Response:
    """Execute a GET request with exponential-backoff retries."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(
                url, params=params, headers=headers, stream=stream, timeout=timeout,
            )
            resp.raise_for_status()
            return resp
        except (requests.RequestException, requests.HTTPError) as exc:
            if attempt == MAX_RETRIES:
                logger.error("Request failed after %d attempts: %s", MAX_RETRIES, exc)
                raise
            wait = BACKOFF_BASE ** attempt
            logger.warning(
                "Attempt %d/%d failed (%s). Retrying in %ds...",
                attempt,
                MAX_RETRIES,
                exc,
                wait,
            )
            time.sleep(wait)
    raise RuntimeError("Exceeded max retries")


def _save_dataframe(df: pd.DataFrame, output_dir: str, filename_stem: str) -> tuple[Path, Path]:
    """Save DataFrame as CSV + Parquet."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    csv_path = out / f"{filename_stem}.csv"
    parquet_path = out / f"{filename_stem}.parquet"
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False, engine="pyarrow")
    logger.info("Saved %d rows -> %s  (.csv + .parquet)", len(df), csv_path)
    return csv_path, parquet_path


# ---------------------------------------------------------------------------
# Download functions
# ---------------------------------------------------------------------------

def download_earthquakes(
    output_dir: str,
    start_date: str = "2023-01-01",
    end_date: str = "2023-12-31",
    min_magnitude: float = 2.5,
) -> pd.DataFrame:
    """
    Download earthquake data from the USGS FDSN Event Web Service.

    Returns GeoJSON feature data converted to a tabular DataFrame.  No API
    key required.  The USGS limits results to 20,000 events per query.  For
    larger ranges, the function automatically splits by time windows.

    Args:
        output_dir: Directory to save output files.
        start_date: Start date in ISO format (``YYYY-MM-DD``).
        end_date: End date in ISO format (``YYYY-MM-DD``).
        min_magnitude: Minimum magnitude threshold (default 2.5).

    Returns:
        DataFrame of earthquake event records.
    """
    logger.info(
        "Downloading USGS earthquakes: %s to %s, M >= %.1f",
        start_date, end_date, min_magnitude,
    )

    from datetime import datetime, timedelta

    dt_start = datetime.fromisoformat(start_date)
    dt_end = datetime.fromisoformat(end_date)

    # Split into monthly chunks to stay under the 20,000 event limit
    all_records: list[dict[str, Any]] = []
    current = dt_start

    # Calculate total months for progress bar
    total_months = (dt_end.year - dt_start.year) * 12 + (dt_end.month - dt_start.month) + 1
    pbar = tqdm(total=total_months, desc="Earthquake months", unit="month")

    while current < dt_end:
        # End of current month
        if current.month == 12:
            chunk_end = datetime(current.year + 1, 1, 1) - timedelta(seconds=1)
        else:
            chunk_end = datetime(current.year, current.month + 1, 1) - timedelta(seconds=1)
        chunk_end = min(chunk_end, dt_end)

        params = {
            "format": "geojson",
            "starttime": current.strftime("%Y-%m-%d"),
            "endtime": chunk_end.strftime("%Y-%m-%d"),
            "minmagnitude": min_magnitude,
            "orderby": "time",
            "limit": 20000,
        }

        try:
            resp = _request_with_retry(USGS_EARTHQUAKE_API, params=params)
            data = resp.json()
        except Exception:
            logger.exception(
                "USGS earthquake query failed for %s to %s",
                current.strftime("%Y-%m-%d"),
                chunk_end.strftime("%Y-%m-%d"),
            )
            current = chunk_end + timedelta(days=1)
            pbar.update(1)
            continue

        features = data.get("features", [])
        for feature in features:
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})
            coords = geom.get("coordinates", [None, None, None])

            record: dict[str, Any] = {
                "event_id": feature.get("id"),
                "usgs_id": props.get("ids", "").strip(",") if props.get("ids") else None,
                "time": props.get("time"),  # milliseconds since epoch
                "latitude": coords[1] if len(coords) > 1 else None,
                "longitude": coords[0] if len(coords) > 0 else None,
                "depth_km": coords[2] if len(coords) > 2 else None,
                "magnitude": props.get("mag"),
                "mag_type": props.get("magType"),
                "place": props.get("place"),
                "event_type": props.get("type"),
                "status": props.get("status"),
                "tsunami": bool(props.get("tsunami", 0)),
                "significance": props.get("sig"),
                "felt": props.get("felt"),
                "cdi": props.get("cdi"),
                "mmi": props.get("mmi"),
                "alert": props.get("alert"),
                "net": props.get("net"),
                "nst": props.get("nst"),
                "gap": props.get("gap"),
                "rms": props.get("rms"),
                "url": props.get("url"),
                "load_time": pd.Timestamp.now().isoformat(),
            }
            all_records.append(record)

        logger.debug(
            "%s: %d events",
            current.strftime("%Y-%m"),
            len(features),
        )

        # Advance to next month
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)
        pbar.update(1)
        time.sleep(RATE_LIMIT_SLEEP)

    pbar.close()

    if not all_records:
        logger.warning("No earthquake data downloaded")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)

    # Convert epoch millis to ISO timestamp
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True).dt.strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )

    # Numeric conversions
    for col in ("magnitude", "depth_km", "cdi", "mmi", "gap", "rms"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ("significance", "felt", "nst"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    logger.info("Earthquake data: %d events", len(df))
    _save_dataframe(df, output_dir, "doi_usgs_earthquakes")
    return df


def download_water_data(
    output_dir: str,
    site_ids: list[str] | None = None,
    parameter_codes: list[str] | None = None,
    start_date: str = "2023-06-01",
    end_date: str = "2023-06-30",
) -> pd.DataFrame:
    """
    Download water data from USGS NWIS (National Water Information System).

    No API key required.  Returns instantaneous values (iv) or daily values
    (dv) depending on the date range.

    Args:
        output_dir: Directory to save output files.
        site_ids: List of USGS site numbers (e.g. ``["01646500"]``).
            Defaults to a curated set of major US river gages.
        parameter_codes: List of NWIS parameter codes (e.g. ``["00060"]``
            for discharge).  Defaults to discharge and gage height.
        start_date: Start date (``YYYY-MM-DD``).
        end_date: End date (``YYYY-MM-DD``).

    Returns:
        Combined DataFrame of water observations.
    """
    if site_ids is None:
        site_ids = DEFAULT_NWIS_SITES

    if parameter_codes is None:
        parameter_codes = ["00060", "00065"]  # discharge + gage height

    logger.info(
        "Downloading NWIS water data: %d sites, %d parameters, %s to %s",
        len(site_ids), len(parameter_codes), start_date, end_date,
    )

    all_records: list[dict[str, Any]] = []

    # NWIS accepts up to ~100 sites per request; batch if needed
    batch_size = 50
    site_batches = [
        site_ids[i:i + batch_size] for i in range(0, len(site_ids), batch_size)
    ]

    for batch in tqdm(site_batches, desc="NWIS site batches"):
        sites_str = ",".join(batch)
        params_str = ",".join(parameter_codes)

        # Try instantaneous values first
        url = f"{USGS_NWIS_API}/iv/"
        params = {
            "sites": sites_str,
            "parameterCd": params_str,
            "startDT": start_date,
            "endDT": end_date,
            "format": "json",
        }

        try:
            resp = _request_with_retry(url, params=params)
            data = resp.json()
        except Exception:
            logger.exception("NWIS IV request failed for sites: %s", sites_str)
            # Fallback: try daily values
            try:
                url_dv = f"{USGS_NWIS_API}/dv/"
                resp = _request_with_retry(url_dv, params=params)
                data = resp.json()
            except Exception:
                logger.exception("NWIS DV fallback also failed")
                continue

        # Parse NWIS JSON response (WaterML JSON format)
        time_series = data.get("value", {}).get("timeSeries", [])

        for ts in time_series:
            source_info = ts.get("sourceInfo", {})
            variable = ts.get("variable", {})
            site_code = source_info.get("siteCode", [{}])[0].get("value", "")
            site_name = source_info.get("siteName", "")
            geo = source_info.get("geoLocation", {}).get("geogLocation", {})
            lat = geo.get("latitude")
            lon = geo.get("longitude")
            param_code = variable.get("variableCode", [{}])[0].get("value", "")
            param_name = variable.get("variableName", "")
            unit = variable.get("unit", {}).get("unitCode", "")

            values_list = ts.get("values", [{}])
            for values_group in values_list:
                for val_entry in values_group.get("value", []):
                    record: dict[str, Any] = {
                        "site_id": site_code,
                        "site_name": site_name,
                        "latitude": lat,
                        "longitude": lon,
                        "timestamp": val_entry.get("dateTime"),
                        "parameter_code": param_code,
                        "parameter_name": param_name,
                        "value": val_entry.get("value"),
                        "unit": unit,
                        "qualifier": ",".join(val_entry.get("qualifiers", [])),
                        "load_time": pd.Timestamp.now().isoformat(),
                    }
                    all_records.append(record)

        time.sleep(RATE_LIMIT_SLEEP)

    if not all_records:
        logger.warning("No NWIS water data downloaded")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)

    # Numeric conversions
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    for col in ("latitude", "longitude"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    logger.info("NWIS water data: %d rows", len(df))
    _save_dataframe(df, output_dir, "doi_usgs_water_data")
    return df


def download_park_visitation(
    output_dir: str,
    park_codes: list[str] | None = None,
    year_start: int = 2010,
) -> pd.DataFrame:
    """
    Download National Park Service visitor use statistics from IRMA.

    The NPS publishes visitation data via SSRS reports that can be accessed
    as CSV downloads.  No API key required.

    Args:
        output_dir: Directory to save output files.
        park_codes: List of NPS park unit codes (e.g. ``["GRCA", "YELL"]``).
            Defaults to top-10 most-visited parks.
        year_start: Earliest year to include (default 2010).

    Returns:
        Combined DataFrame of park visitation records.
    """
    if park_codes is None:
        park_codes = DEFAULT_PARK_CODES

    logger.info(
        "Downloading NPS visitation for %d parks from %d",
        len(park_codes), year_start,
    )

    all_records: list[dict[str, Any]] = []

    for park_code in tqdm(park_codes, desc="NPS parks"):
        # NPS IRMA Stats API endpoint for visitation summary
        url = (
            f"{NPS_STATS_BASE}/ReportServer?"
            f"/VisitationAllYears"
            f"&UnitCode={park_code}"
            f"&rs:Format=CSV"
        )

        try:
            resp = _request_with_retry(url, timeout=60)
            # The response is CSV text
            from io import StringIO
            df_park = pd.read_csv(StringIO(resp.text))

            # NPS CSV typically has columns: Year, Month, RecreationVisitors, etc.
            # Normalize column names
            df_park.columns = [c.strip().replace(" ", "_").lower() for c in df_park.columns]

            if "year" in df_park.columns:
                df_park["year"] = pd.to_numeric(df_park["year"], errors="coerce")
                df_park = df_park[df_park["year"] >= year_start]

            df_park["park_code"] = park_code

            for _, row in df_park.iterrows():
                record = row.to_dict()
                record["load_time"] = pd.Timestamp.now().isoformat()
                all_records.append(record)

        except Exception:
            logger.exception("Failed to download NPS data for %s", park_code)
            # Fallback: try alternative NPS stats URL patterns
            try:
                alt_url = (
                    f"https://irma.nps.gov/Stats/SSRSReports/Park%20Specific%20Reports/"
                    f"Recreation%20Visitors%20By%20Month%20(1979%20-%20Last%20Calendar%20Year)"
                    f"?Park={park_code}"
                )
                resp = _request_with_retry(alt_url, timeout=60)
                logger.info("Fallback URL succeeded for %s (%d bytes)", park_code, len(resp.content))
            except Exception:
                logger.debug("Fallback also failed for %s", park_code)
            continue

        time.sleep(RATE_LIMIT_SLEEP)

    if not all_records:
        logger.warning("No NPS visitation data downloaded")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)

    # Standardize visitation column names
    vis_renames = {
        "recreationvisitors": "recreation_visitors",
        "recreation_visitors": "recreation_visitors",
        "nonrecreationvisitors": "non_recreation_visitors",
        "non_recreation_visitors": "non_recreation_visitors",
        "recreationhours": "recreation_hours",
        "recreation_hours": "recreation_hours",
    }
    for old, new in vis_renames.items():
        if old in df.columns and old != new:
            df.rename(columns={old: new}, inplace=True)

    # Numeric conversions
    for col in ("recreation_visitors", "non_recreation_visitors", "recreation_hours", "year"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    logger.info("NPS visitation data: %d rows", len(df))
    _save_dataframe(df, output_dir, "doi_nps_visitation")
    return df


def download_species_data(
    output_dir: str,
    status_filter: str | None = None,
) -> pd.DataFrame:
    """
    Download endangered and threatened species data from FWS ECOS.

    The ECOS system provides species listing data including status, habitat,
    and recovery plans.  No API key required.

    Args:
        output_dir: Directory to save output files.
        status_filter: Filter by ESA listing status.  Options include:
            ``"endangered"``, ``"threatened"``, ``"candidate"``,
            ``"proposed"``.  ``None`` returns all listed species.

    Returns:
        DataFrame of species listing records.
    """
    logger.info("Downloading FWS ECOS species data (status=%s)", status_filter)

    # ECOS species report in CSV format
    url = f"{FWS_ECOS_BASE}/species-listings-by-current-listing-status"

    all_records: list[dict[str, Any]] = []

    # ECOS provides a downloadable report; try multiple access patterns
    report_urls = [
        # Direct CSV export endpoint
        f"{FWS_ECOS_BASE}/species-listings-by-current-listing-status?format=csv",
        # Alternative: species search
        "https://ecos.fws.gov/ecp/pullreports/catalog/species/report/species/export?format=csv&columns=/species@cn,sn,status,desc,listing_date",
        # Fallback: ECOS REST-like endpoint
        "https://ecos.fws.gov/ecp/report/table/species-listings-by-current-listing-status.csv",
    ]

    df = pd.DataFrame()

    for report_url in report_urls:
        try:
            resp = _request_with_retry(report_url, timeout=90)

            if resp.headers.get("Content-Type", "").startswith("text/csv") or "csv" in report_url:
                from io import StringIO
                df = pd.read_csv(StringIO(resp.text), low_memory=False)
            else:
                # Try parsing as CSV anyway
                from io import StringIO
                df = pd.read_csv(StringIO(resp.text), low_memory=False)

            if not df.empty:
                logger.info("ECOS data retrieved: %d rows from %s", len(df), report_url)
                break

        except Exception:
            logger.debug("ECOS URL failed: %s", report_url)
            continue

        time.sleep(RATE_LIMIT_SLEEP)

    if df.empty:
        logger.warning("No ECOS species data downloaded")
        return pd.DataFrame()

    # Normalize column names
    df.columns = [c.strip().replace(" ", "_").lower() for c in df.columns]

    # Rename for schema alignment
    species_map = {
        "common_name": "common_name",
        "scientific_name": "scientific_name",
        "species_group": "species_group",
        "federal_listing_status": "listing_status",
        "status": "listing_status",
        "listing_date": "listing_date",
        "where_listed": "where_listed",
        "critical_habitat": "critical_habitat",
        "recovery_plan": "recovery_plan",
        "species_code": "species_code",
    }
    df.rename(columns=species_map, inplace=True)

    # Apply status filter
    if status_filter and "listing_status" in df.columns:
        df = df[
            df["listing_status"]
            .str.lower()
            .str.contains(status_filter.lower(), na=False)
        ]

    df["load_time"] = pd.Timestamp.now().isoformat()

    logger.info("ECOS species data: %d rows", len(df))
    _save_dataframe(df, output_dir, "doi_fws_species")
    return df


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_download(file_path: str) -> dict[str, Any]:
    """
    Validate a downloaded DOI dataset file.

    Checks for:
    * File exists and is non-empty
    * Expected columns present for the detected dataset type
    * Numeric columns parse correctly

    Args:
        file_path: Path to a CSV or Parquet file.

    Returns:
        Dictionary with ``valid``, ``row_count``, ``columns``,
        ``missing_columns``, and ``warnings``.
    """
    path = Path(file_path)
    result: dict[str, Any] = {
        "valid": False,
        "file": str(path),
        "row_count": 0,
        "columns": [],
        "missing_columns": [],
        "warnings": [],
    }

    if not path.exists():
        result["warnings"].append("File does not exist")
        return result

    if path.stat().st_size == 0:
        result["warnings"].append("File is empty")
        return result

    try:
        if path.suffix == ".parquet":
            df = pd.read_parquet(path)
        else:
            df = pd.read_csv(path, nrows=10_000, low_memory=False)
    except Exception as exc:
        result["warnings"].append(f"Failed to read file: {exc}")
        return result

    result["row_count"] = len(df)
    result["columns"] = list(df.columns)

    # Detect dataset type from filename
    fname = path.stem.lower()
    if "earthquake" in fname:
        required = {"event_id", "magnitude", "latitude", "longitude"}
    elif "water" in fname:
        required = {"site_id", "timestamp", "value"}
    elif "visitation" in fname or "nps" in fname:
        required = {"park_code", "year"}
    elif "species" in fname or "fws" in fname:
        required = {"common_name", "listing_status"}
    else:
        required = {"load_time"}

    missing = required - set(df.columns)
    result["missing_columns"] = sorted(missing)
    if missing:
        result["warnings"].append(f"Missing required columns: {missing}")

    # Validate earthquake numeric fields
    if "earthquake" in fname and "magnitude" in df.columns:
        mag = pd.to_numeric(df["magnitude"], errors="coerce")
        invalid_mags = mag.isna().sum()
        if invalid_mags > 0:
            result["warnings"].append(
                f"{invalid_mags} non-numeric magnitude values"
            )

    result["valid"] = len(result["warnings"]) == 0
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    """Command-line interface for DOI open-data downloads."""
    parser = argparse.ArgumentParser(
        description="Download DOI open datasets (earthquakes, water, parks, species)",
    )
    parser.add_argument(
        "--dataset",
        choices=["earthquakes", "water", "parks", "species", "all"],
        default="all",
        help="Which dataset to download (default: all)",
    )
    parser.add_argument(
        "--output-dir",
        default="./data/doi",
        help="Output directory (default: ./data/doi)",
    )
    parser.add_argument(
        "--start-date",
        default="2023-01-01",
        help="Start date for earthquakes/water (YYYY-MM-DD, default: 2023-01-01)",
    )
    parser.add_argument(
        "--end-date",
        default="2023-12-31",
        help="End date for earthquakes/water (YYYY-MM-DD, default: 2023-12-31)",
    )
    parser.add_argument(
        "--min-magnitude",
        type=float,
        default=2.5,
        help="Minimum earthquake magnitude (default: 2.5)",
    )
    parser.add_argument(
        "--sites",
        default=None,
        help="Comma-separated USGS NWIS site IDs (e.g. 01646500,07010000)",
    )
    parser.add_argument(
        "--parameters",
        default=None,
        help="Comma-separated NWIS parameter codes (e.g. 00060,00065)",
    )
    parser.add_argument(
        "--parks",
        default=None,
        help="Comma-separated NPS park codes (e.g. GRCA,YELL,YOSE)",
    )
    parser.add_argument(
        "--year-start",
        type=int,
        default=2010,
        help="Start year for park visitation data (default: 2010)",
    )
    parser.add_argument(
        "--status-filter",
        default=None,
        help="ESA listing status filter for species data "
             "(e.g. endangered, threatened, candidate)",
    )

    args = parser.parse_args()

    if args.dataset in ("earthquakes", "all"):
        download_earthquakes(
            args.output_dir,
            start_date=args.start_date,
            end_date=args.end_date,
            min_magnitude=args.min_magnitude,
        )

    if args.dataset in ("water", "all"):
        sites = args.sites.split(",") if args.sites else None
        params = args.parameters.split(",") if args.parameters else None
        download_water_data(
            args.output_dir,
            site_ids=sites,
            parameter_codes=params,
            start_date=args.start_date,
            end_date=args.end_date,
        )

    if args.dataset in ("parks", "all"):
        parks = args.parks.split(",") if args.parks else None
        download_park_visitation(
            args.output_dir,
            park_codes=parks,
            year_start=args.year_start,
        )

    if args.dataset in ("species", "all"):
        download_species_data(args.output_dir, status_filter=args.status_filter)

    logger.info("DOI download complete. Files saved to %s", args.output_dir)


if __name__ == "__main__":
    main()
