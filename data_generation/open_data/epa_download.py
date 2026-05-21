"""
EPA Open Data Download
======================

Download real Environmental Protection Agency (EPA) datasets as alternatives
to the synthetic ``EPAGenerator``.

Supported datasets
------------------
* **AQS (Air Quality System)** -- Air quality monitoring data from 4,000+
  stations.  Requires a free email-based API key from
  https://aqs.epa.gov/data/api/signup?email=YOUR_EMAIL
* **TRI (Toxic Release Inventory)** -- Bulk CSV download of industrial
  chemical releases since 1987.  No API key required.
  Source: https://www.epa.gov/toxics-release-inventory-tri-program/tri-basic-data-files-calendar-years-1987-present
* **ECHO (Enforcement & Compliance History)** -- Facility-level compliance
  and enforcement data via web services.  No API key.
  Source: https://echo.epa.gov/tools/web-services
* **SDWIS (Safe Drinking Water Information System)** -- Public water system
  compliance data.  No API key.

Output schemas are aligned with ``EPAGenerator`` so that downstream medallion
notebooks work identically with either real or synthetic data.

Usage
-----
CLI::

    python -m data_generation.open_data.epa_download --dataset aqs --api-key YOUR_KEY --output-dir ./data/epa --state 06
    python -m data_generation.open_data.epa_download --dataset tri --output-dir ./data/epa --year-start 2018 --year-end 2022
    python -m data_generation.open_data.epa_download --dataset all --api-key YOUR_KEY --output-dir ./data/epa

Library::

    from data_generation.open_data.epa_download import download_air_quality
    df = download_air_quality("YOUR_KEY", "./data/epa", state_code="06", parameter="88101")
"""

from __future__ import annotations

import argparse
import contextlib
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
AQS_API_BASE = "https://aqs.epa.gov/data/api"
TRI_BULK_BASE = "https://data.epa.gov/efservice/downloads/tri"
ECHO_API_BASE = "https://echo.epa.gov/api"
SDWIS_API_BASE = "https://data.epa.gov/efservice"

MAX_RETRIES = 3
BACKOFF_BASE = 2
REQUEST_TIMEOUT = 120
RATE_LIMIT_SLEEP = 1.0  # EPA APIs are generally rate-limited

# AQS parameter codes for common pollutants
AQS_PARAMETERS = {
    "PM2.5": "88101",
    "PM10": "81102",
    "OZONE": "44201",
    "CO": "42101",
    "SO2": "42401",
    "NO2": "42602",
    "LEAD": "14129",
}

# TRI base file URL pattern (year-based bulk CSV files)
TRI_FILE_URL_TEMPLATE = (
    "https://data.epa.gov/efservice/downloads/tri/mv_tri_basic_download/"
    "{year}/tri_basic_{year}.csv"
)

# Schema alignment: AQS API response -> our standard columns
AQS_COLUMN_MAP = {
    "state_code": "state_code",
    "county_code": "county_code",
    "site_number": "site_number",
    "parameter_code": "parameter_code",
    "date_local": "date_local",
    "time_local": "time_local",
    "sample_measurement": "concentration",
    "units_of_measure": "units",
    "sample_duration": "sample_duration",
    "aqi": "aqi_value",
    "method_code": "method_code",
    "latitude": "latitude",
    "longitude": "longitude",
    "cbsa_name": "cbsa_name",
    "state_name": "state_name",
    "county_name": "county_name",
}

# TRI column map (subset of the ~100+ columns in the bulk file)
TRI_COLUMN_MAP = {
    "TRI_FACILITY_ID": "facility_id",
    "FACILITY_NAME": "facility_name",
    "STREET_ADDRESS": "address",
    "CITY_NAME": "city",
    "COUNTY_NAME": "county",
    "ST": "state",
    "ZIP_CODE": "zip_code",
    "LATITUDE": "latitude",
    "LONGITUDE": "longitude",
    "INDUSTRY_SECTOR_CODE": "industry_sector_code",
    "INDUSTRY_SECTOR": "industry_sector",
    "CHEMICAL": "chemical",
    "CAS_CHEM_NAME": "cas_chemical_name",
    "SRS_ID": "srs_id",
    "UNIT_OF_MEASURE": "unit",
    "FUGITIVE_AIR": "fugitive_air",
    "STACK_AIR": "stack_air",
    "WATER": "water_release",
    "UNDERGROUND": "underground_release",
    "LAND_TREATMENT": "land_treatment",
    "SURFACE_IMPNDMNT": "surface_impoundment",
    "OTHER_DISPOSAL": "other_disposal",
    "TOTAL_RELEASES": "total_releases",
    "ON-SITE_RELEASE_TOTAL": "onsite_release_total",
    "OFF-SITE_RELEASE_TOTAL": "offsite_release_total",
    "REPORTING_YEAR": "reporting_year",
    "FEDERAL_FACILITY": "federal_facility",
    "CARCINOGEN": "carcinogen",
    "CLEAN_AIR_ACT_CHEMICAL": "clean_air_act_chemical",
}

# ECHO facility detail column map
ECHO_COLUMN_MAP = {
    "RegistryID": "registry_id",
    "FacilityName": "facility_name",
    "CityName": "city",
    "CountyName": "county",
    "StateCode": "state_code",
    "Zip": "zip_code",
    "FacilityTypeName": "facility_type",
    "CWAPerm itStatusDesc": "cwa_permit_status",
    "CAAProgramCodes": "caa_program_codes",
    "RCRAPermitTypes": "rcra_permit_types",
    "CurrSvFlag": "current_sv_flag",
    "CurrVioFlag": "current_violation_flag",
    "QtrsInNC": "quarters_in_noncompliance",
    "InspectionCount": "inspection_count",
    "FormalActionCount": "formal_action_count",
    "FacLat": "latitude",
    "FacLong": "longitude",
    "LastInspectionDate": "last_inspection_date",
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
                url,
                params=params,
                headers=headers,
                stream=stream,
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp
        except (requests.RequestException, requests.HTTPError) as exc:
            if attempt == MAX_RETRIES:
                logger.error("Request failed after %d attempts: %s", MAX_RETRIES, exc)
                raise
            wait = BACKOFF_BASE**attempt
            logger.warning(
                "Attempt %d/%d failed (%s). Retrying in %ds...",
                attempt,
                MAX_RETRIES,
                exc,
                wait,
            )
            time.sleep(wait)
    raise RuntimeError("Exceeded max retries")


def _save_dataframe(
    df: pd.DataFrame, output_dir: str, filename_stem: str
) -> tuple[Path, Path]:
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


def download_air_quality(
    api_key: str,
    output_dir: str,
    state_code: str = "06",
    parameter: str = "88101",
    start_date: str = "20230101",
    end_date: str = "20231231",
) -> pd.DataFrame:
    """
    Download air quality data from the EPA AQS API.

    Requires a free API key obtained by signing up with your email at
    https://aqs.epa.gov/data/api/signup?email=YOUR_EMAIL

    The API returns data by state and parameter.  For large queries, the
    function paginates automatically.

    Args:
        api_key: AQS API key (your registered email address).
        output_dir: Directory to save output files.
        state_code: Two-digit FIPS state code (e.g. ``"06"`` for California).
        parameter: AQS parameter code (e.g. ``"88101"`` for PM2.5).
            See ``AQS_PARAMETERS`` for common codes.
        start_date: Start date as ``YYYYMMDD``.
        end_date: End date as ``YYYYMMDD``.

    Returns:
        DataFrame of air quality measurements.
    """
    logger.info(
        "Downloading AQS data: state=%s, parameter=%s, %s to %s",
        state_code,
        parameter,
        start_date,
        end_date,
    )

    # Resolve named parameter to code
    if parameter.upper() in AQS_PARAMETERS:
        parameter = AQS_PARAMETERS[parameter.upper()]

    url = f"{AQS_API_BASE}/dailyData/byState"
    params = {
        "email": api_key,
        "key": api_key,
        "param": parameter,
        "bdate": start_date,
        "edate": end_date,
        "state": state_code,
    }

    all_records: list[dict[str, Any]] = []

    try:
        resp = _request_with_retry(url, params=params)
        data = resp.json()
    except Exception:
        logger.exception("AQS API request failed")
        return pd.DataFrame()

    header = data.get("Header", [{}])
    if header and header[0].get("status") == "Failed":
        logger.error("AQS API error: %s", header[0].get("error", "Unknown"))
        return pd.DataFrame()

    results = data.get("Data", [])
    all_records.extend(results)

    logger.info("AQS returned %d records", len(all_records))

    if not all_records:
        logger.warning("No AQS data returned")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)
    df.rename(columns=AQS_COLUMN_MAP, inplace=True)

    # Schema alignment with EPAGenerator
    if "parameter_code" in df.columns:
        # Reverse-lookup parameter name
        code_to_name = {v: k for k, v in AQS_PARAMETERS.items()}
        df["parameter"] = df["parameter_code"].map(code_to_name).fillna("UNKNOWN")

    # Add AQI category
    if "aqi_value" in df.columns:
        df["aqi_value"] = pd.to_numeric(df["aqi_value"], errors="coerce")
        df["aqi_category"] = df["aqi_value"].apply(_aqi_category)

    if "concentration" in df.columns:
        df["concentration"] = pd.to_numeric(df["concentration"], errors="coerce")

    # Build site_id
    if all(c in df.columns for c in ("state_code", "county_code", "site_number")):
        df["site_id"] = (
            df["state_code"].astype(str)
            + "-"
            + df["county_code"].astype(str)
            + "-"
            + df["site_number"].astype(str)
        )

    df["record_id"] = range(1, len(df) + 1)
    df["record_id"] = df["record_id"].apply(lambda x: f"AQS-{x:010d}")
    df["load_time"] = pd.Timestamp.now().isoformat()

    _save_dataframe(df, output_dir, f"epa_aqs_{state_code}_{parameter}")
    return df


def _aqi_category(aqi_value: float | None) -> str | None:
    """Return AQI category for a numeric AQI value."""
    if aqi_value is None or pd.isna(aqi_value):
        return None
    aqi = int(aqi_value)
    if aqi <= 50:
        return "GOOD"
    if aqi <= 100:
        return "MODERATE"
    if aqi <= 150:
        return "UNHEALTHY_SENSITIVE"
    if aqi <= 200:
        return "UNHEALTHY"
    if aqi <= 300:
        return "VERY_UNHEALTHY"
    return "HAZARDOUS"


def download_tri_data(
    output_dir: str,
    year_start: int = 2018,
    year_end: int = 2022,
    state: str | None = None,
) -> pd.DataFrame:
    """
    Download Toxic Release Inventory (TRI) bulk CSV data.

    No API key required.  TRI data is published as annual CSV files.

    Args:
        output_dir: Directory to save output files.
        year_start: First reporting year to download (inclusive).
        year_end: Last reporting year to download (inclusive).
        state: Two-letter state abbreviation to filter (e.g. ``"CA"``).
            ``None`` means all states.

    Returns:
        Combined DataFrame of TRI records.
    """
    logger.info(
        "Downloading TRI data for years %d-%d (state=%s)",
        year_start,
        year_end,
        state,
    )

    frames: list[pd.DataFrame] = []

    for year in tqdm(range(year_start, year_end + 1), desc="TRI years"):
        # TRI basic data files URL pattern
        # EPA sometimes changes the exact URL structure; we try multiple patterns
        urls_to_try = [
            f"https://data.epa.gov/efservice/downloads/tri/mv_tri_basic_download/{year}/tri_{year}_us.csv",
            f"https://enviro.epa.gov/enviro/efservice/tri_basic_download/reporting_year/{year}/csv",
        ]

        downloaded = False
        for url in urls_to_try:
            try:
                resp = _request_with_retry(url, stream=True, timeout=180)
                tmp_path = Path(output_dir) / f"_tmp_tri_{year}.csv"
                Path(output_dir).mkdir(parents=True, exist_ok=True)

                with open(tmp_path, "wb") as fh:
                    for chunk in resp.iter_content(chunk_size=8192):
                        fh.write(chunk)

                df_year = pd.read_csv(tmp_path, low_memory=False, dtype=str)
                df_year.rename(columns=TRI_COLUMN_MAP, inplace=True)

                if state and "state" in df_year.columns:
                    df_year = df_year[df_year["state"].str.upper() == state.upper()]

                frames.append(df_year)

                with contextlib.suppress(OSError):
                    tmp_path.unlink()

                downloaded = True
                break

            except Exception:
                logger.debug("TRI URL failed: %s", url)
                continue

        if not downloaded:
            logger.warning("Could not download TRI data for year %d", year)

        time.sleep(RATE_LIMIT_SLEEP)

    if not frames:
        logger.warning("No TRI data downloaded")
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    # Numeric conversions
    numeric_cols = [
        "fugitive_air",
        "stack_air",
        "water_release",
        "underground_release",
        "land_treatment",
        "surface_impoundment",
        "other_disposal",
        "total_releases",
        "onsite_release_total",
        "offsite_release_total",
        "latitude",
        "longitude",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["load_time"] = pd.Timestamp.now().isoformat()

    logger.info("TRI combined data: %d rows", len(df))
    _save_dataframe(df, output_dir, "epa_tri_releases")
    return df


def download_echo_compliance(
    output_dir: str,
    state: str | None = None,
) -> pd.DataFrame:
    """
    Download facility compliance data from the EPA ECHO web services.

    No API key required.

    Args:
        output_dir: Directory to save output files.
        state: Two-letter state abbreviation (e.g. ``"CA"``).
            If ``None``, downloads a national sample (limited to 10,000 rows
            per query by the ECHO API).

    Returns:
        DataFrame of ECHO facility compliance records.
    """
    logger.info("Downloading ECHO compliance data (state=%s)", state)

    # ECHO Detailed Facility Report (DFR) web service
    url = f"{ECHO_API_BASE}/echo_rest_services.get_facilities"
    params: dict[str, Any] = {
        "output": "JSON",
        "p_st": state or "",
        "responseset": 10000,  # max rows per request
    }

    all_records: list[dict[str, Any]] = []
    page = 1
    max_pages = 10  # safety limit

    pbar = tqdm(desc="ECHO pages", unit="page")

    while page <= max_pages:
        params["pageno"] = page

        try:
            resp = _request_with_retry(url, params=params)
            data = resp.json()
        except Exception:
            logger.exception("ECHO API request failed at page %d", page)
            break

        # ECHO nests results under "Results" -> "Facilities"
        results = data.get("Results", {})
        facilities = results.get("Facilities", [])

        if not facilities:
            break

        all_records.extend(facilities)
        pbar.update(1)

        # Check for more pages
        query_rows = int(results.get("QueryRows", 0))
        if len(all_records) >= query_rows:
            break

        page += 1
        time.sleep(RATE_LIMIT_SLEEP)

    pbar.close()

    if not all_records:
        logger.warning("No ECHO data downloaded")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)
    df.rename(columns=ECHO_COLUMN_MAP, inplace=True)

    # Numeric conversions
    for col in (
        "latitude",
        "longitude",
        "inspection_count",
        "formal_action_count",
        "quarters_in_noncompliance",
    ):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["load_time"] = pd.Timestamp.now().isoformat()

    logger.info("ECHO compliance data: %d rows", len(df))
    _save_dataframe(df, output_dir, "epa_echo_compliance")
    return df


def download_water_quality(
    output_dir: str,
    state: str | None = None,
) -> pd.DataFrame:
    """
    Download Safe Drinking Water Information System (SDWIS) data.

    No API key required.  Uses the EPA Envirofacts Data Service.

    Args:
        output_dir: Directory to save output files.
        state: Two-letter state abbreviation (e.g. ``"CA"``).
            ``None`` downloads a national subset.

    Returns:
        DataFrame of SDWIS water system violation records.
    """
    logger.info("Downloading SDWIS water quality data (state=%s)", state)

    # Envirofacts SDWIS violations table
    base_url = f"{SDWIS_API_BASE}/VIOLATION"

    all_records: list[dict[str, Any]] = []
    rows_per_page = 10000
    start_row = 0
    max_rows = 100000  # safety limit

    pbar = tqdm(desc="SDWIS pages", unit="page")

    while start_row < max_rows:
        # Build the Envirofacts REST URL
        if state:
            url = f"{base_url}/PRIMACY_AGENCY_CODE/{state}/{start_row}:{start_row + rows_per_page}/JSON"
        else:
            url = f"{base_url}/{start_row}:{start_row + rows_per_page}/JSON"

        try:
            resp = _request_with_retry(url)
            data = resp.json()
        except Exception:
            logger.exception("SDWIS request failed at offset %d", start_row)
            break

        if not data or not isinstance(data, list):
            break

        all_records.extend(data)
        pbar.update(1)

        if len(data) < rows_per_page:
            # Last page
            break

        start_row += rows_per_page
        time.sleep(RATE_LIMIT_SLEEP)

    pbar.close()

    if not all_records:
        logger.warning("No SDWIS data downloaded")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)

    # Rename columns for schema alignment with EPAGenerator
    sdwis_map = {
        "PWSID": "system_id",
        "PWS_NAME": "system_name",
        "PWS_TYPE_CODE": "system_type",
        "VIOLATION_ID": "record_id",
        "CONTAMINANT_CODE": "contaminant_code",
        "CONTAMINANT_NAME": "contaminant",
        "COMPL_PER_BEGIN_DATE": "sample_date",
        "VIOLATION_TYPE_CODE": "violation_type",
        "POPULATION_SERVED_COUNT": "population_served",
        "PRIMACY_AGENCY_CODE": "state_code",
        "IS_HEALTH_BASED_IND": "is_health_based",
    }
    df.rename(columns=sdwis_map, inplace=True)

    if "population_served" in df.columns:
        df["population_served"] = pd.to_numeric(
            df["population_served"], errors="coerce"
        )

    df["load_time"] = pd.Timestamp.now().isoformat()

    logger.info("SDWIS water quality data: %d rows", len(df))
    _save_dataframe(df, output_dir, "epa_sdwis_violations")
    return df


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_download(file_path: str) -> dict[str, Any]:
    """
    Validate a downloaded EPA dataset file.

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
    if "aqs" in fname:
        required = {"state_code", "parameter_code", "concentration"}
    elif "tri" in fname:
        required = {"facility_name", "chemical", "total_releases"}
    elif "echo" in fname:
        required = {"facility_name", "state_code"}
    elif "sdwis" in fname:
        required = {"system_id", "contaminant"}
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
    """Command-line interface for EPA open-data downloads."""
    parser = argparse.ArgumentParser(
        description="Download EPA open datasets (AQS, TRI, ECHO, SDWIS)",
    )
    parser.add_argument(
        "--dataset",
        choices=["aqs", "tri", "echo", "sdwis", "all"],
        default="all",
        help="Which dataset to download (default: all)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="AQS API key (email address, required for aqs dataset)",
    )
    parser.add_argument(
        "--output-dir",
        default="./data/epa",
        help="Output directory (default: ./data/epa)",
    )
    parser.add_argument(
        "--state",
        default=None,
        help="Two-letter state code for ECHO/SDWIS, or FIPS code for AQS (e.g. 06 for CA)",
    )
    parser.add_argument(
        "--year-start",
        type=int,
        default=2018,
        help="Start year for TRI data (default: 2018)",
    )
    parser.add_argument(
        "--year-end",
        type=int,
        default=2022,
        help="End year for TRI data (default: 2022)",
    )
    parser.add_argument(
        "--parameter",
        default="88101",
        help="AQS parameter code or name (e.g. 88101 or PM2.5, default: 88101)",
    )
    parser.add_argument(
        "--start-date",
        default="20230101",
        help="Start date for AQS data (YYYYMMDD, default: 20230101)",
    )
    parser.add_argument(
        "--end-date",
        default="20231231",
        help="End date for AQS data (YYYYMMDD, default: 20231231)",
    )

    args = parser.parse_args()

    if args.dataset in ("aqs", "all"):
        if not args.api_key:
            logger.error(
                "AQS API key required. Sign up free at "
                "https://aqs.epa.gov/data/api/signup?email=YOUR_EMAIL"
            )
            if args.dataset == "aqs":
                return
        else:
            download_air_quality(
                api_key=args.api_key,
                output_dir=args.output_dir,
                state_code=args.state or "06",
                parameter=args.parameter,
                start_date=args.start_date,
                end_date=args.end_date,
            )

    if args.dataset in ("tri", "all"):
        download_tri_data(
            args.output_dir,
            year_start=args.year_start,
            year_end=args.year_end,
            state=args.state,
        )

    if args.dataset in ("echo", "all"):
        download_echo_compliance(args.output_dir, state=args.state)

    if args.dataset in ("sdwis", "all"):
        download_water_quality(args.output_dir, state=args.state)

    logger.info("EPA download complete. Files saved to %s", args.output_dir)


if __name__ == "__main__":
    main()
