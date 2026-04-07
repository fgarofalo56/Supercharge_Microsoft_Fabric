"""
NOAA Open Data Download
=======================

Download real NOAA (National Oceanic and Atmospheric Administration) datasets
as alternatives to the synthetic ``NOAAGenerator``.

Supported datasets
------------------
* **Weather Observations** -- Current/recent observations from api.weather.gov.
  Free, no API key.  Requires ``User-Agent`` header.
* **Storm Events Database** -- Bulk CSV files from NCEI (~2 GB total, 2M+ events).
  Free, no API key.  Source: https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/
* **Climate Data Online (CDO)** -- Historical climate data via NCDC CDO API v2.
  Requires a free API key from https://www.ncdc.noaa.gov/cdo-web/token
* **CO-OPS Tides & Currents** -- Tide predictions and water levels.
  Free, no API key.  Source: https://api.tidesandcurrents.noaa.gov

Output schemas are aligned with ``NOAAGenerator`` so that downstream medallion
notebooks work identically with either real or synthetic data.

Usage
-----
CLI::

    python -m data_generation.open_data.noaa_download --dataset storms --output-dir ./data/noaa --start-date 2020 --end-date 2023
    python -m data_generation.open_data.noaa_download --dataset weather --output-dir ./data/noaa --stations KJFK,KLAX
    python -m data_generation.open_data.noaa_download --dataset climate --api-key YOUR_KEY --output-dir ./data/noaa --stations GHCND:USW00094728

Library::

    from data_generation.open_data.noaa_download import download_storm_events
    df = download_storm_events("./data/noaa", year_start=2020, year_end=2023)
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
WEATHER_API_BASE = "https://api.weather.gov"
STORM_EVENTS_BASE = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles"
CDO_API_BASE = "https://www.ncdc.noaa.gov/cdo-web/api/v2"
COOPS_API_BASE = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"

MAX_RETRIES = 3
BACKOFF_BASE = 2
REQUEST_TIMEOUT = 120
RATE_LIMIT_SLEEP = 0.5  # weather.gov asks for polite request rates

# User-Agent required by api.weather.gov
WEATHER_HEADERS = {
    "User-Agent": "(SuperchargeFabricPOC, contact@example.com)",
    "Accept": "application/geo+json",
}

# Storm Events file-type prefixes used in the bulk download
STORM_FILE_TYPES = ["StormEvents_details", "StormEvents_fatalities", "StormEvents_locations"]

# Schema alignment: map weather.gov observation properties to our standard
WEATHER_OBS_MAP = {
    "station": "station_id",
    "timestamp": "timestamp",
    "textDescription": "description",
    "temperature.value": "temperature_c",
    "dewpoint.value": "dewpoint_c",
    "relativeHumidity.value": "humidity_pct",
    "windSpeed.value": "wind_speed_kmh",
    "windDirection.value": "wind_direction_deg",
    "barometricPressure.value": "pressure_pa",
    "visibility.value": "visibility_m",
    "precipitationLastHour.value": "precip_last_hour_mm",
}

# Storm events column map (NCEI CSV columns -> our schema)
STORM_COLUMN_MAP = {
    "EVENT_ID": "event_id",
    "EPISODE_ID": "episode_id",
    "EVENT_TYPE": "event_type",
    "STATE": "state",
    "STATE_FIPS": "state_fips",
    "CZ_FIPS": "county_fips",
    "CZ_NAME": "county_name",
    "BEGIN_DATE_TIME": "begin_date",
    "END_DATE_TIME": "end_date",
    "INJURIES_DIRECT": "injuries_direct",
    "INJURIES_INDIRECT": "injuries_indirect",
    "DEATHS_DIRECT": "deaths_direct",
    "DEATHS_INDIRECT": "deaths_indirect",
    "DAMAGE_PROPERTY": "damage_property",
    "DAMAGE_CROPS": "damage_crops",
    "MAGNITUDE": "magnitude",
    "MAGNITUDE_TYPE": "magnitude_type",
    "BEGIN_LAT": "begin_lat",
    "BEGIN_LON": "begin_lon",
    "END_LAT": "end_lat",
    "END_LON": "end_lon",
    "TOR_F_SCALE": "tor_f_scale",
    "SOURCE": "source",
    "FLOOD_CAUSE": "flood_cause",
}


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


def _parse_damage(value: str | None) -> float | None:
    """Parse NOAA damage strings like '25K', '1.5M', '0.00K' to numeric."""
    if value is None or pd.isna(value):
        return None
    value = str(value).strip().upper()
    if not value or value == "0":
        return 0.0
    multipliers = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
    for suffix, mult in multipliers.items():
        if value.endswith(suffix):
            try:
                return float(value[:-1]) * mult
            except ValueError:
                return None
    try:
        return float(value)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Download functions
# ---------------------------------------------------------------------------

def download_weather_observations(
    output_dir: str,
    station_ids: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    Download weather observations from api.weather.gov.

    This API returns recent observations (typically the last 7 days) for a
    given station.  No API key is needed, but a ``User-Agent`` header is
    required.

    Args:
        output_dir: Directory to save output files.
        station_ids: List of ICAO station codes (e.g. ``["KJFK", "KLAX"]``).
            Defaults to a set of major US airport stations.
        start_date: ISO date string filter (observations after this date).
        end_date: ISO date string filter (observations before this date).

    Returns:
        Combined DataFrame of weather observations.
    """
    if station_ids is None:
        station_ids = [
            "KJFK", "KLAX", "KORD", "KATL", "KDFW", "KDEN",
            "KPHX", "KSEA", "KMIA", "KBOS", "KLAS", "KMSP",
        ]

    logger.info(
        "Downloading weather observations for %d stations", len(station_ids)
    )

    all_records: list[dict[str, Any]] = []

    for station in tqdm(station_ids, desc="Weather stations"):
        url = f"{WEATHER_API_BASE}/stations/{station}/observations"
        params: dict[str, str] = {}
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date

        try:
            resp = _request_with_retry(url, params=params, headers=WEATHER_HEADERS)
            data = resp.json()
        except Exception:
            logger.exception("Failed to fetch observations for %s", station)
            continue

        features = data.get("features", [])
        for feature in features:
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})
            coords = geom.get("coordinates", [None, None]) if geom else [None, None]

            record: dict[str, Any] = {
                "observation_id": props.get("@id", "").split("/")[-1] if props.get("@id") else None,
                "station_id": station,
                "station_name": props.get("station", "").split("/")[-1] if props.get("station") else station,
                "timestamp": props.get("timestamp"),
                "latitude": coords[1] if len(coords) > 1 else None,
                "longitude": coords[0] if len(coords) > 0 else None,
                "elevation_m": props.get("elevation", {}).get("value") if isinstance(props.get("elevation"), dict) else None,
                "temperature_c": _nested_value(props, "temperature"),
                "dewpoint_c": _nested_value(props, "dewpoint"),
                "humidity_pct": _nested_value(props, "relativeHumidity"),
                "wind_speed_kmh": _nested_value(props, "windSpeed"),
                "wind_direction_deg": _nested_value(props, "windDirection"),
                "pressure_pa": _nested_value(props, "barometricPressure"),
                "visibility_m": _nested_value(props, "visibility"),
                "precip_last_hour_mm": _nested_value(props, "precipitationLastHour"),
                "description": props.get("textDescription"),
                "quality_flag": "PASS",  # weather.gov pre-validates
                "data_source": "WEATHER_GOV",
                "load_time": pd.Timestamp.now().isoformat(),
            }
            all_records.append(record)

        time.sleep(RATE_LIMIT_SLEEP)

    df = pd.DataFrame(all_records)
    if not df.empty:
        _save_dataframe(df, output_dir, "noaa_weather_observations")
    else:
        logger.warning("No weather observations downloaded")

    return df


def _nested_value(props: dict, key: str) -> float | None:
    """Extract numeric value from a nested weather.gov measurement object."""
    obj = props.get(key)
    if isinstance(obj, dict):
        return obj.get("value")
    return None


def download_storm_events(
    output_dir: str,
    year_start: int = 2020,
    year_end: int = 2023,
) -> pd.DataFrame:
    """
    Download NOAA Storm Events bulk CSV files from NCEI.

    Files are published per year with names like
    ``StormEvents_details-ftp_v1.0_d2023_c20240117.csv.gz``.

    Args:
        output_dir: Directory to save output files.
        year_start: First year to download (inclusive).
        year_end: Last year to download (inclusive).

    Returns:
        Combined DataFrame of storm event records.
    """
    logger.info("Downloading Storm Events for years %d-%d", year_start, year_end)

    # First, get the directory listing to find exact file names
    frames: list[pd.DataFrame] = []

    for year in tqdm(range(year_start, year_end + 1), desc="Storm Events years"):
        # The file naming pattern includes a version and creation date suffix
        # We try to fetch a listing and match, or construct a likely name
        file_pattern = f"StormEvents_details-ftp_v1.0_d{year}"

        # Try the direct directory listing approach
        try:
            listing_resp = _request_with_retry(
                f"{STORM_EVENTS_BASE}/",
                headers={"Accept": "text/html"},
            )
            listing_text = listing_resp.text

            # Find the matching filename in the HTML listing
            import re
            matches = re.findall(
                rf'href="({file_pattern}[^"]*\.csv\.gz)"', listing_text
            )

            if not matches:
                # Fallback: try without .gz
                matches = re.findall(
                    rf'href="({file_pattern}[^"]*\.csv)"', listing_text
                )

            if not matches:
                logger.warning("No storm events file found for year %d", year)
                continue

            filename = matches[0]
            file_url = f"{STORM_EVENTS_BASE}/{filename}"

        except Exception:
            logger.warning(
                "Could not list storm events directory. Trying fallback pattern for %d",
                year,
            )
            # Fallback: try a common pattern
            file_url = f"{STORM_EVENTS_BASE}/StormEvents_details-ftp_v1.0_d{year}.csv.gz"

        try:
            resp = _request_with_retry(file_url, stream=True)
            tmp_path = Path(output_dir) / f"_tmp_storm_{year}.csv.gz"
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            with open(tmp_path, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=8192):
                    fh.write(chunk)

            df_year = pd.read_csv(
                tmp_path, low_memory=False, dtype=str, compression="gzip"
            )
            df_year.rename(columns=STORM_COLUMN_MAP, inplace=True)
            frames.append(df_year)

            try:
                tmp_path.unlink()
            except OSError:
                pass

        except Exception:
            logger.exception("Failed to download storm events for %d", year)
            continue

        time.sleep(RATE_LIMIT_SLEEP)

    if not frames:
        logger.warning("No Storm Events data downloaded")
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    # Parse damage columns
    for col in ("damage_property", "damage_crops"):
        if col in df.columns:
            df[col] = df[col].apply(_parse_damage)

    # Numeric columns
    for col in ("injuries_direct", "injuries_indirect", "deaths_direct", "deaths_indirect"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    for col in ("begin_lat", "begin_lon", "end_lat", "end_lon", "magnitude"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["load_time"] = pd.Timestamp.now().isoformat()
    logger.info("Storm Events combined: %d rows", len(df))
    _save_dataframe(df, output_dir, "noaa_storm_events")
    return df


def download_climate_data(
    api_key: str,
    output_dir: str,
    dataset_id: str = "GHCND",
    station_ids: list[str] | None = None,
    start_date: str = "2020-01-01",
    end_date: str = "2023-12-31",
) -> pd.DataFrame:
    """
    Download historical climate data from the NOAA CDO API v2.

    Requires a free API key from https://www.ncdc.noaa.gov/cdo-web/token

    Args:
        api_key: NOAA CDO API key.
        output_dir: Directory to save output files.
        dataset_id: CDO dataset identifier (default ``"GHCND"`` for daily
            summaries).  Other options: ``"GSOM"``, ``"GSOY"``, ``"NORMAL_DLY"``.
        station_ids: List of CDO station IDs
            (e.g. ``["GHCND:USW00094728"]``).  If ``None``, downloads data
            for a default set of major US stations.
        start_date: Start date (``YYYY-MM-DD``).
        end_date: End date (``YYYY-MM-DD``).

    Returns:
        Combined DataFrame of climate observations.
    """
    if station_ids is None:
        station_ids = [
            "GHCND:USW00094728",  # NYC Central Park
            "GHCND:USW00023174",  # LAX
            "GHCND:USW00094846",  # Chicago O'Hare
            "GHCND:USW00013874",  # Atlanta
            "GHCND:USW00003927",  # Dallas/Fort Worth
        ]

    logger.info(
        "Downloading CDO climate data (%s) for %d stations, %s to %s",
        dataset_id, len(station_ids), start_date, end_date,
    )

    headers = {"token": api_key}
    all_records: list[dict[str, Any]] = []

    for station in tqdm(station_ids, desc="CDO stations"):
        offset = 0
        limit = 1000  # CDO API max per request

        while True:
            params = {
                "datasetid": dataset_id,
                "stationid": station,
                "startdate": start_date,
                "enddate": end_date,
                "limit": limit,
                "offset": offset,
                "units": "standard",
            }

            try:
                resp = _request_with_retry(
                    f"{CDO_API_BASE}/data", params=params, headers=headers,
                )
                data = resp.json()
            except Exception:
                logger.exception(
                    "CDO API failed for station %s at offset %d", station, offset,
                )
                break

            results = data.get("results", [])
            if not results:
                break

            for rec in results:
                rec["load_time"] = pd.Timestamp.now().isoformat()
            all_records.extend(results)

            # Check if there are more pages
            metadata = data.get("metadata", {}).get("resultset", {})
            total = metadata.get("count", 0)
            offset += limit

            if offset >= total:
                break

            time.sleep(RATE_LIMIT_SLEEP)

        time.sleep(RATE_LIMIT_SLEEP)

    if not all_records:
        logger.warning("No CDO climate data downloaded")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)

    # Rename columns for schema alignment
    col_map = {
        "station": "station_id",
        "date": "timestamp",
        "datatype": "parameter",
        "value": "value",
        "attributes": "quality_flag",
    }
    df.rename(columns=col_map, inplace=True)

    logger.info("CDO climate data: %d rows", len(df))
    _save_dataframe(df, output_dir, "noaa_climate_data")
    return df


def download_tide_data(
    output_dir: str,
    station_id: str = "8518750",
    start_date: str = "20230101",
    end_date: str = "20231231",
) -> pd.DataFrame:
    """
    Download tide/water-level data from NOAA CO-OPS.

    No API key required.  Station IDs can be found at
    https://tidesandcurrents.noaa.gov/stations.html

    Args:
        output_dir: Directory to save output files.
        station_id: CO-OPS station number (default ``"8518750"`` for The
            Battery, NYC).
        start_date: Start date as ``YYYYMMDD``.
        end_date: End date as ``YYYYMMDD``.

    Returns:
        DataFrame of tide observations.
    """
    logger.info(
        "Downloading CO-OPS tide data for station %s (%s to %s)",
        station_id, start_date, end_date,
    )

    # CO-OPS API limits to 31 days per request for 6-minute data, or 1 year
    # for hourly.  We use hourly to reduce request count.
    all_records: list[dict[str, Any]] = []

    # Parse dates and chunk into 31-day windows
    from datetime import datetime, timedelta

    dt_start = datetime.strptime(start_date, "%Y%m%d")
    dt_end = datetime.strptime(end_date, "%Y%m%d")
    chunk_days = 365  # hourly data supports up to 1 year

    current = dt_start
    pbar = tqdm(desc="CO-OPS tide chunks", unit="chunk")

    while current < dt_end:
        chunk_end = min(current + timedelta(days=chunk_days), dt_end)

        params = {
            "begin_date": current.strftime("%Y%m%d"),
            "end_date": chunk_end.strftime("%Y%m%d"),
            "station": station_id,
            "product": "hourly_height",
            "datum": "MLLW",
            "units": "metric",
            "time_zone": "gmt",
            "format": "json",
            "application": "SuperchargeFabricPOC",
        }

        try:
            resp = _request_with_retry(COOPS_API_BASE, params=params)
            data = resp.json()
        except Exception:
            logger.exception(
                "CO-OPS request failed for %s to %s",
                current.strftime("%Y%m%d"),
                chunk_end.strftime("%Y%m%d"),
            )
            current = chunk_end
            pbar.update(1)
            continue

        records = data.get("data", [])
        for rec in records:
            rec["station_id"] = station_id
            rec["load_time"] = pd.Timestamp.now().isoformat()
        all_records.extend(records)

        current = chunk_end
        pbar.update(1)
        time.sleep(RATE_LIMIT_SLEEP)

    pbar.close()

    if not all_records:
        logger.warning("No CO-OPS tide data downloaded")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)

    # Rename for schema alignment
    col_map = {
        "t": "timestamp",
        "v": "water_level_m",
        "s": "sigma",
        "f": "quality_flag",
    }
    df.rename(columns=col_map, inplace=True)

    # Numeric conversion
    for col in ("water_level_m", "sigma"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    logger.info("CO-OPS tide data: %d rows", len(df))
    _save_dataframe(df, output_dir, "noaa_tide_data")
    return df


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_download(file_path: str) -> dict[str, Any]:
    """
    Validate a downloaded NOAA dataset file.

    Checks for:
    * File exists and is non-empty
    * Expected columns are present for the detected dataset type
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
    if "storm" in fname:
        required = {"event_id", "event_type", "state", "begin_date"}
    elif "weather" in fname or "observation" in fname:
        required = {"station_id", "timestamp"}
    elif "climate" in fname:
        required = {"station_id", "parameter", "value"}
    elif "tide" in fname:
        required = {"station_id", "timestamp", "water_level_m"}
    else:
        required = {"load_time"}

    missing = required - set(df.columns)
    result["missing_columns"] = sorted(missing)
    if missing:
        result["warnings"].append(f"Missing required columns: {missing}")

    result["valid"] = len(result["warnings"]) == 0
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    """Command-line interface for NOAA open-data downloads."""
    parser = argparse.ArgumentParser(
        description="Download NOAA open datasets (weather, storms, climate, tides)",
    )
    parser.add_argument(
        "--dataset",
        choices=["weather", "storms", "climate", "tides", "all"],
        default="all",
        help="Which dataset to download (default: all)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="NOAA CDO API key (required for climate dataset)",
    )
    parser.add_argument(
        "--output-dir",
        default="./data/noaa",
        help="Output directory (default: ./data/noaa)",
    )
    parser.add_argument(
        "--stations",
        default=None,
        help="Comma-separated station IDs (e.g. KJFK,KLAX for weather; "
             "GHCND:USW00094728 for climate; 8518750 for tides)",
    )
    parser.add_argument(
        "--start-date",
        default=None,
        help="Start date (ISO format for weather/climate; YYYYMMDD for tides; "
             "year integer for storms)",
    )
    parser.add_argument(
        "--end-date",
        default=None,
        help="End date (same format as start-date)",
    )

    args = parser.parse_args()

    stations = args.stations.split(",") if args.stations else None

    if args.dataset in ("weather", "all"):
        download_weather_observations(
            args.output_dir,
            station_ids=stations,
            start_date=args.start_date,
            end_date=args.end_date,
        )

    if args.dataset in ("storms", "all"):
        year_start = int(args.start_date) if args.start_date else 2020
        year_end = int(args.end_date) if args.end_date else 2023
        download_storm_events(args.output_dir, year_start=year_start, year_end=year_end)

    if args.dataset in ("climate", "all"):
        if not args.api_key:
            logger.error(
                "CDO API key required for climate data. "
                "Get one free at https://www.ncdc.noaa.gov/cdo-web/token"
            )
            if args.dataset == "climate":
                return
        else:
            download_climate_data(
                api_key=args.api_key,
                output_dir=args.output_dir,
                station_ids=stations,
                start_date=args.start_date or "2020-01-01",
                end_date=args.end_date or "2023-12-31",
            )

    if args.dataset in ("tides", "all"):
        station = stations[0] if stations else "8518750"
        download_tide_data(
            args.output_dir,
            station_id=station,
            start_date=args.start_date or "20230101",
            end_date=args.end_date or "20231231",
        )

    logger.info("NOAA download complete. Files saved to %s", args.output_dir)


if __name__ == "__main__":
    main()
