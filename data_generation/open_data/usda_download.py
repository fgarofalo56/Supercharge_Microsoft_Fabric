"""
USDA Open Data Download Script
================================
Downloads real USDA datasets for POC demonstrations.
Supports both API-based and bulk file downloads.

Datasets:
1. NASS QuickStats API - Crop production statistics
2. FSIS Recall Data - Food safety recalls
3. SNAP Retailer Locator - EBT retailer locations
4. Census of Agriculture - Farm census data

Usage::

    # CLI
    python -m data_generation.open_data.usda_download --dataset nass --api-key YOUR_KEY
    python -m data_generation.open_data.usda_download --dataset fsis --output-dir ./output
    python -m data_generation.open_data.usda_download --dataset all --api-key YOUR_KEY

    # Library
    from data_generation.open_data.usda_download import download_nass_quickstats
    df_path = download_nass_quickstats(api_key="YOUR_KEY", commodity="CORN")

Downloaded parquet files are schema-aligned with the synthetic USDA generator
output so that downstream notebooks work with either data source.
"""

from __future__ import annotations

import argparse
import io
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("usda_download")


def _setup_logging(level: int = logging.INFO) -> None:
    """Configure logging with a consistent format."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.setLevel(level)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_OUTPUT_DIR = Path("output/usda_open_data")

# NASS QuickStats API
NASS_BASE_URL = "https://quickstats.nass.usda.gov/api/api_GET/"
NASS_PAGE_SIZE = 50_000  # API maximum per request

# FSIS Recall data
FSIS_RECALL_URL = (
    "https://www.fsis.usda.gov/sites/default/files/media_file/documents/"
    "fsis-recall-data.csv"
)

# SNAP Retailer Locator (ArcGIS Hub)
SNAP_BASE_URL = (
    "https://services1.arcgis.com/RLQu0rK7h4kbsBq5/arcgis/rest/services/"
    "Store_Locations/FeatureServer/0/query"
)
SNAP_PAGE_SIZE = 2000  # ArcGIS feature query limit

# Census of Agriculture (NASS QuickStats, source_desc=CENSUS)
CENSUS_BASE_URL = NASS_BASE_URL  # Same API, different parameters

# Retry / rate-limiting
MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 2.0
RATE_LIMIT_DELAY_SECONDS = 0.5  # Minimum gap between API calls

# ---------------------------------------------------------------------------
# Generator schema definitions (mirrors USDAGenerator output)
# These are the canonical column sets that downstream notebooks expect.
# ---------------------------------------------------------------------------
CROP_PRODUCTION_SCHEMA: dict[str, str] = {
    "record_id": "string",
    "commodity": "string",
    "year": "int",
    "state_fips": "string",
    "state_name": "string",
    "county_fips": "string",
    "county_name": "string",
    "statisticcat_desc": "string",
    "unit_desc": "string",
    "value": "float",
    "cv_percent": "float",
    "source_desc": "string",
    "agg_level_desc": "string",
    "domain_desc": "string",
    "reference_period_desc": "string",
    "load_time": "string",
    "_ingested_at": "string",
    "_source": "string",
    "_batch_id": "string",
}

FOOD_SAFETY_SCHEMA: dict[str, str] = {
    "recall_id": "string",
    "recall_number": "string",
    "recall_date": "string",
    "product_type": "string",
    "recall_class": "string",
    "reason": "string",
    "risk_level": "string",
    "company_name": "string",
    "establishment_number": "string",
    "city": "string",
    "state": "string",
    "pounds_recalled": "float",
    "distribution": "string",
    "status": "string",
    "press_release_url": "string",
    "load_time": "string",
    "_ingested_at": "string",
    "_source": "string",
    "_batch_id": "string",
}

SNAP_RETAILER_SCHEMA: dict[str, str] = {
    "record_id": "string",
    "store_name": "string",
    "store_type": "string",
    "address": "string",
    "city": "string",
    "state": "string",
    "zip_code": "string",
    "county": "string",
    "latitude": "float",
    "longitude": "float",
    "load_time": "string",
    "_ingested_at": "string",
    "_source": "string",
    "_batch_id": "string",
}

CENSUS_AG_SCHEMA: dict[str, str] = {
    "record_id": "string",
    "commodity": "string",
    "year": "int",
    "state_fips": "string",
    "state_name": "string",
    "county_fips": "string",
    "county_name": "string",
    "statisticcat_desc": "string",
    "unit_desc": "string",
    "value": "float",
    "source_desc": "string",
    "agg_level_desc": "string",
    "domain_desc": "string",
    "reference_period_desc": "string",
    "load_time": "string",
    "_ingested_at": "string",
    "_source": "string",
    "_batch_id": "string",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _request_with_retry(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    max_retries: int = MAX_RETRIES,
    initial_backoff: float = INITIAL_BACKOFF_SECONDS,
    timeout: int = 120,
) -> requests.Response:
    """
    Execute an HTTP request with exponential-backoff retries.

    Args:
        method: HTTP method (GET, POST, etc.).
        url: Target URL.
        params: Query parameters.
        headers: HTTP headers.
        max_retries: Number of retry attempts on failure.
        initial_backoff: Seconds to wait before the first retry (doubles each time).
        timeout: Per-request timeout in seconds.

    Returns:
        :class:`requests.Response` on success.

    Raises:
        requests.HTTPError: After all retries are exhausted.
    """
    backoff = initial_backoff
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.request(
                method,
                url,
                params=params,
                headers=headers,
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp
        except (requests.RequestException, requests.HTTPError) as exc:
            last_exc = exc
            if attempt < max_retries:
                logger.warning(
                    "Request to %s failed (attempt %d/%d): %s. "
                    "Retrying in %.1f s ...",
                    url,
                    attempt,
                    max_retries,
                    exc,
                    backoff,
                )
                time.sleep(backoff)
                backoff *= 2
            else:
                logger.error(
                    "Request to %s failed after %d attempts: %s",
                    url,
                    max_retries,
                    exc,
                )

    # Should be unreachable, but satisfy the type-checker
    raise requests.HTTPError(
        f"All {max_retries} attempts failed for {url}"
    ) from last_exc


def _rate_limit() -> None:
    """Pause briefly to respect API rate limits."""
    time.sleep(RATE_LIMIT_DELAY_SECONDS)


def _ensure_output_dir(output_dir: str | Path) -> Path:
    """Create and return the output directory path."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _add_metadata_columns(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """Append the three standard metadata columns expected by downstream notebooks."""
    now = datetime.now().isoformat()
    df["_ingested_at"] = now
    df["_source"] = source_name
    # Batch ID: first 8 chars of a hash of the current timestamp
    import hashlib
    batch_id = hashlib.sha256(now.encode()).hexdigest()[:8]
    df["_batch_id"] = batch_id
    return df


def _align_schema(
    df: pd.DataFrame,
    target_schema: dict[str, str],
) -> pd.DataFrame:
    """
    Align a DataFrame to a target schema.

    - Missing columns are added with ``None``.
    - Extra columns are dropped.
    - Columns are reordered to match the schema.
    - Basic type casting is applied (int, float, string).

    Args:
        df: Input DataFrame.
        target_schema: Mapping of column name to type string
                       (``"string"``, ``"int"``, ``"float"``).

    Returns:
        Schema-aligned DataFrame.
    """
    # Add missing columns
    for col in target_schema:
        if col not in df.columns:
            df[col] = None

    # Keep only schema columns, in order
    df = df[[c for c in target_schema if c in df.columns]].copy()

    # Cast types
    for col, dtype in target_schema.items():
        if col not in df.columns:
            continue
        try:
            if dtype == "int":
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
            elif dtype == "float":
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("Float64")
            elif dtype == "string":
                df[col] = df[col].astype("string")
        except (ValueError, TypeError):
            logger.debug("Could not cast column %s to %s", col, dtype)

    return df


def _save_parquet(df: pd.DataFrame, file_path: Path) -> Path:
    """Write a DataFrame to parquet and return the path."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(file_path, engine="pyarrow", index=False)
    logger.info("Saved %d rows to %s", len(df), file_path)
    return file_path


# ---------------------------------------------------------------------------
# 1. NASS QuickStats API
# ---------------------------------------------------------------------------

def download_nass_quickstats(
    api_key: str,
    commodity: str = "CORN",
    year_start: int = 2018,
    year_end: int = 2023,
    state_fips: str | None = None,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> Path:
    """
    Download crop production data from the NASS QuickStats API.

    The API is paginated at 50,000 records per call. This function handles
    pagination transparently and merges all pages into a single parquet file.

    API documentation: https://quickstats.nass.usda.gov/api

    Args:
        api_key: NASS API key (obtain from https://quickstats.nass.usda.gov/api#param_define).
        commodity: Commodity description (e.g. ``"CORN"``, ``"SOYBEANS"``, ``"WHEAT"``).
        year_start: First year (inclusive) to download.
        year_end: Last year (inclusive) to download.
        state_fips: Optional 2-digit state FIPS code to limit results (e.g. ``"17"`` for Illinois).
        output_dir: Directory for the output parquet file.

    Returns:
        Path to the saved parquet file.

    Raises:
        ValueError: If the API key is missing or empty.
        requests.HTTPError: After retries are exhausted.
    """
    if not api_key or not api_key.strip():
        raise ValueError(
            "A NASS API key is required. "
            "Sign up at https://quickstats.nass.usda.gov/api#param_define"
        )

    out = _ensure_output_dir(output_dir)
    commodity_upper = commodity.upper()

    logger.info(
        "Downloading NASS QuickStats: commodity=%s, years=%d-%d, state_fips=%s",
        commodity_upper,
        year_start,
        year_end,
        state_fips or "ALL",
    )

    all_records: list[dict[str, Any]] = []

    for year in tqdm(
        range(year_start, year_end + 1),
        desc=f"NASS {commodity_upper}",
        unit="year",
    ):
        offset = 0
        year_done = False

        while not year_done:
            params: dict[str, Any] = {
                "key": api_key,
                "commodity_desc": commodity_upper,
                "year": str(year),
                "statisticcat_desc": "PRODUCTION",
                "format": "JSON",
            }
            if state_fips:
                params["state_fips_code"] = state_fips

            # The NASS API does not have a formal offset parameter for
            # pagination. Instead we iterate over statistic categories
            # to keep result sets manageable. If a single year+commodity
            # returns more than 50K rows, we issue year+state queries.
            # For most commodities a year query stays well under 50K.

            _rate_limit()
            try:
                resp = _request_with_retry("GET", NASS_BASE_URL, params=params)
                data = resp.json()
            except requests.HTTPError as exc:
                # NASS returns 400 when there are no results for a query
                if "400" in str(exc):
                    logger.debug("No results for %s/%d - skipping", commodity_upper, year)
                    break
                raise

            rows = data.get("data", [])
            if not rows:
                logger.debug("No rows returned for %s/%d (offset=%d)", commodity_upper, year, offset)
                break

            all_records.extend(rows)
            logger.debug("Fetched %d rows for %s/%d", len(rows), commodity_upper, year)

            # If fewer than the page size were returned, we have all data
            if len(rows) < NASS_PAGE_SIZE:
                year_done = True
            else:
                # Unlikely for a single commodity+year, but handle gracefully
                logger.warning(
                    "NASS returned %d rows for %s/%d which hits the page limit. "
                    "Consider narrowing the query (e.g., by state).",
                    len(rows),
                    commodity_upper,
                    year,
                )
                year_done = True  # Cannot paginate further without state subdivision

    if not all_records:
        logger.warning(
            "No data returned from NASS for commodity=%s, years=%d-%d",
            commodity_upper,
            year_start,
            year_end,
        )
        # Return an empty parquet with the correct schema
        df = pd.DataFrame(columns=list(CROP_PRODUCTION_SCHEMA.keys()))
        file_path = out / f"nass_{commodity_upper.lower()}_{year_start}_{year_end}.parquet"
        return _save_parquet(df, file_path)

    df = pd.DataFrame(all_records)
    logger.info("Total rows downloaded from NASS: %d", len(df))

    # Map NASS API field names to generator schema columns
    df = _map_nass_to_schema(df)
    df = _add_metadata_columns(df, "NASS_QuickStats_API")
    df = _align_schema(df, CROP_PRODUCTION_SCHEMA)

    file_path = out / f"nass_{commodity_upper.lower()}_{year_start}_{year_end}.parquet"
    return _save_parquet(df, file_path)


def _map_nass_to_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map NASS QuickStats API response columns to the generator schema.

    The API returns fields like ``commodity_desc``, ``state_fips_code``,
    ``state_name``, ``Value``, etc.  This function renames and converts
    them to match :data:`CROP_PRODUCTION_SCHEMA`.
    """
    import uuid

    rename_map: dict[str, str] = {
        "commodity_desc": "commodity",
        "year": "year",
        "state_fips_code": "state_fips",
        "state_name": "state_name",
        "county_code": "county_fips",
        "county_name": "county_name",
        "statisticcat_desc": "statisticcat_desc",
        "unit_desc": "unit_desc",
        "Value": "value",
        "CV (%)": "cv_percent",
        "source_desc": "source_desc",
        "agg_level_desc": "agg_level_desc",
        "domain_desc": "domain_desc",
        "reference_period_desc": "reference_period_desc",
    }

    # Rename only columns that exist in the response
    existing_renames = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=existing_renames)

    # Generate record_id if not present
    if "record_id" not in df.columns:
        df["record_id"] = [str(uuid.uuid4()) for _ in range(len(df))]

    # Add load_time
    df["load_time"] = datetime.now().isoformat()

    # Clean the value column - NASS uses "(D)" for withheld data and commas
    if "value" in df.columns:
        df["value"] = (
            df["value"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        # Replace non-numeric markers with NaN
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Clean cv_percent similarly
    if "cv_percent" in df.columns:
        df["cv_percent"] = pd.to_numeric(
            df["cv_percent"].astype(str).str.strip(), errors="coerce"
        )

    # Build full county FIPS (state_fips + county_code) when county is present
    if "county_fips" in df.columns and "state_fips" in df.columns:
        mask = df["county_fips"].notna() & (df["county_fips"].astype(str).str.strip() != "")
        df.loc[mask, "county_fips"] = (
            df.loc[mask, "state_fips"].astype(str).str.zfill(2)
            + df.loc[mask, "county_fips"].astype(str).str.zfill(3)
        )

    return df


# ---------------------------------------------------------------------------
# 2. FSIS Recall Data
# ---------------------------------------------------------------------------

def download_fsis_recalls(
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    year_start: int | None = None,
) -> Path:
    """
    Download FSIS food safety recall data.

    No API key is required. The data is published as a CSV file by the
    Food Safety and Inspection Service.

    Args:
        output_dir: Directory for the output parquet file.
        year_start: Optional earliest year to include (filters after download).

    Returns:
        Path to the saved parquet file.

    Raises:
        requests.HTTPError: After retries are exhausted.
    """
    out = _ensure_output_dir(output_dir)
    logger.info("Downloading FSIS recall data from %s", FSIS_RECALL_URL)

    resp = _request_with_retry("GET", FSIS_RECALL_URL)

    # Parse CSV response
    df = pd.read_csv(
        io.StringIO(resp.text),
        encoding="utf-8",
        on_bad_lines="skip",
    )
    logger.info("Downloaded %d FSIS recall records", len(df))

    # Map to food safety schema
    df = _map_fsis_to_schema(df)

    # Filter by year if requested
    if year_start is not None and "recall_date" in df.columns:
        df["_recall_year"] = pd.to_datetime(
            df["recall_date"], errors="coerce"
        ).dt.year
        df = df[df["_recall_year"] >= year_start].drop(columns=["_recall_year"])
        logger.info("After year filter (>= %d): %d records", year_start, len(df))

    df = _add_metadata_columns(df, "FSIS_Recall_CSV")
    df = _align_schema(df, FOOD_SAFETY_SCHEMA)

    suffix = f"_from_{year_start}" if year_start else ""
    file_path = out / f"fsis_recalls{suffix}.parquet"
    return _save_parquet(df, file_path)


def _map_fsis_to_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map FSIS CSV columns to the generator food safety schema.

    FSIS column names vary across vintages. This function applies a
    best-effort mapping using case-insensitive matching and common
    variations.
    """
    import uuid

    # Normalise column names for matching
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Common FSIS column name -> schema name
    rename_map: dict[str, str] = {
        "recall_number": "recall_number",
        "recall_date": "recall_date",
        "product": "product_type",
        "product_type": "product_type",
        "classification": "recall_class",
        "recall_classification": "recall_class",
        "class": "recall_class",
        "reason_for_recall": "reason",
        "reason": "reason",
        "risk_level": "risk_level",
        "company": "company_name",
        "company_name": "company_name",
        "firm_name": "company_name",
        "establishment_number": "establishment_number",
        "establishment": "establishment_number",
        "est._number": "establishment_number",
        "city": "city",
        "state": "state",
        "pounds_recalled": "pounds_recalled",
        "quantity_recovered": "pounds_recalled",
        "distribution": "distribution",
        "distribution_pattern": "distribution",
        "status": "status",
        "current_status": "status",
        "press_release": "press_release_url",
        "press_release_url": "press_release_url",
    }

    existing_renames = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=existing_renames)

    # Generate IDs
    if "recall_id" not in df.columns:
        df["recall_id"] = [str(uuid.uuid4()) for _ in range(len(df))]

    # Derive risk_level from recall_class if missing
    if "risk_level" not in df.columns and "recall_class" in df.columns:
        risk_map = {"Class I": "HIGH", "Class II": "MEDIUM", "Class III": "LOW"}
        df["risk_level"] = df["recall_class"].map(risk_map)

    df["load_time"] = datetime.now().isoformat()

    # Clean pounds_recalled
    if "pounds_recalled" in df.columns:
        df["pounds_recalled"] = (
            df["pounds_recalled"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("lbs", "", regex=False)
            .str.replace("pounds", "", regex=False)
            .str.strip()
        )
        df["pounds_recalled"] = pd.to_numeric(df["pounds_recalled"], errors="coerce")

    return df


# ---------------------------------------------------------------------------
# 3. SNAP Retailer Locator
# ---------------------------------------------------------------------------

def download_snap_retailers(
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    state_fips: str | None = None,
) -> Path:
    """
    Download SNAP/EBT retailer locations from the USDA ArcGIS Hub.

    No API key is required. Results include geocoded latitude/longitude.
    Uses paginated feature queries because the ArcGIS service limits each
    response to 2,000 features.

    Args:
        output_dir: Directory for the output parquet file.
        state_fips: Optional 2-digit state FIPS code to filter results.
                    When ``None``, downloads data for all states (can be large).

    Returns:
        Path to the saved parquet file.

    Raises:
        requests.HTTPError: After retries are exhausted.
    """
    out = _ensure_output_dir(output_dir)
    state_label = state_fips or "all"
    logger.info("Downloading SNAP retailer data (state_fips=%s)", state_label)

    all_features: list[dict[str, Any]] = []
    offset = 0
    total_fetched = 0
    exceeded_transfer = False

    pbar = tqdm(desc="SNAP Retailers", unit=" records")

    while not exceeded_transfer:
        where_clause = "1=1"
        if state_fips:
            # The ArcGIS field name for state may be State or STATE
            where_clause = f"State = '{state_fips}' OR STATE = '{state_fips}'"

        params: dict[str, Any] = {
            "where": where_clause,
            "outFields": "*",
            "resultOffset": offset,
            "resultRecordCount": SNAP_PAGE_SIZE,
            "f": "json",
            "returnGeometry": "true",
            "outSR": "4326",  # WGS84 for lat/lon
        }

        _rate_limit()
        try:
            resp = _request_with_retry("GET", SNAP_BASE_URL, params=params)
            data = resp.json()
        except requests.HTTPError:
            logger.warning("SNAP query failed at offset %d, stopping pagination", offset)
            break

        features = data.get("features", [])
        if not features:
            break

        all_features.extend(features)
        total_fetched += len(features)
        pbar.update(len(features))

        # Check if there are more records
        exceeded_transfer = data.get("exceededTransferLimit", False) is False
        if len(features) < SNAP_PAGE_SIZE:
            break

        offset += SNAP_PAGE_SIZE

    pbar.close()
    logger.info("Total SNAP retailer features downloaded: %d", total_fetched)

    if not all_features:
        logger.warning("No SNAP retailer data returned for state_fips=%s", state_label)
        df = pd.DataFrame(columns=list(SNAP_RETAILER_SCHEMA.keys()))
        file_path = out / f"snap_retailers_{state_label}.parquet"
        return _save_parquet(df, file_path)

    # Flatten ArcGIS feature JSON to tabular form
    df = _flatten_snap_features(all_features)
    df = _add_metadata_columns(df, "SNAP_Retailer_ArcGIS")
    df = _align_schema(df, SNAP_RETAILER_SCHEMA)

    file_path = out / f"snap_retailers_{state_label}.parquet"
    return _save_parquet(df, file_path)


def _flatten_snap_features(features: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Convert ArcGIS feature JSON to a flat DataFrame.

    Each feature has an ``attributes`` dict and an optional ``geometry`` dict
    with ``x`` (longitude) and ``y`` (latitude).
    """
    import uuid

    rows: list[dict[str, Any]] = []
    for feat in features:
        attrs = feat.get("attributes", {})
        geom = feat.get("geometry", {})

        row: dict[str, Any] = {
            "record_id": str(uuid.uuid4()),
            "store_name": attrs.get("Store_Name") or attrs.get("store_name"),
            "store_type": attrs.get("Store_Type") or attrs.get("store_type"),
            "address": attrs.get("Address") or attrs.get("address"),
            "city": attrs.get("City") or attrs.get("city"),
            "state": attrs.get("State") or attrs.get("state"),
            "zip_code": str(attrs.get("Zip5") or attrs.get("zip5") or ""),
            "county": attrs.get("County") or attrs.get("county"),
            "latitude": geom.get("y"),
            "longitude": geom.get("x"),
            "load_time": datetime.now().isoformat(),
        }
        rows.append(row)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 4. Census of Agriculture
# ---------------------------------------------------------------------------

def download_census_of_agriculture(
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    census_year: int = 2022,
    api_key: str | None = None,
) -> Path:
    """
    Download Census of Agriculture summary data.

    The Census of Agriculture is conducted every five years. Valid census
    years include 2002, 2007, 2012, 2017, and 2022. Data is retrieved
    through the NASS QuickStats API with ``source_desc=CENSUS``.

    If no API key is provided, the function attempts to download the
    bulk CSV summary from the NASS website instead.

    Args:
        output_dir: Directory for the output parquet file.
        census_year: Census year (must be a valid census year).
        api_key: Optional NASS API key. Enables API-based download with
                 richer filtering; without it a pre-aggregated bulk file
                 is downloaded.

    Returns:
        Path to the saved parquet file.

    Raises:
        ValueError: If census_year is not a valid year.
        requests.HTTPError: After retries are exhausted.
    """
    valid_years = {2002, 2007, 2012, 2017, 2022}
    if census_year not in valid_years:
        raise ValueError(
            f"census_year must be one of {sorted(valid_years)}, got {census_year}"
        )

    out = _ensure_output_dir(output_dir)
    logger.info("Downloading Census of Agriculture for year %d", census_year)

    if api_key:
        return _download_census_via_api(api_key, census_year, out)
    else:
        return _download_census_bulk(census_year, out)


def _download_census_via_api(api_key: str, census_year: int, out: Path) -> Path:
    """Download Census data through the NASS QuickStats API."""

    # Key commodities to query for a representative census snapshot
    commodities = ["CORN", "SOYBEANS", "WHEAT", "COTTON", "CATTLE", "HOGS"]
    all_records: list[dict[str, Any]] = []

    for commodity in tqdm(commodities, desc=f"Census {census_year}", unit="commodity"):
        params: dict[str, Any] = {
            "key": api_key,
            "source_desc": "CENSUS",
            "year": str(census_year),
            "commodity_desc": commodity,
            "agg_level_desc": "STATE",
            "format": "JSON",
        }

        _rate_limit()
        try:
            resp = _request_with_retry("GET", CENSUS_BASE_URL, params=params)
            data = resp.json()
        except requests.HTTPError as exc:
            if "400" in str(exc):
                logger.debug("No census results for %s/%d", commodity, census_year)
                continue
            raise

        rows = data.get("data", [])
        all_records.extend(rows)
        logger.debug("Census %s/%d: %d rows", commodity, census_year, len(rows))

    if not all_records:
        logger.warning("No Census data returned for year %d", census_year)
        df = pd.DataFrame(columns=list(CENSUS_AG_SCHEMA.keys()))
        file_path = out / f"census_ag_{census_year}.parquet"
        return _save_parquet(df, file_path)

    df = pd.DataFrame(all_records)
    df = _map_nass_to_schema(df)
    df = _add_metadata_columns(df, "Census_of_Agriculture_API")
    df = _align_schema(df, CENSUS_AG_SCHEMA)

    file_path = out / f"census_ag_{census_year}.parquet"
    return _save_parquet(df, file_path)


def _download_census_bulk(census_year: int, out: Path) -> Path:
    """
    Download a pre-aggregated Census of Agriculture summary CSV.

    This is a fallback path for when no API key is available. The NASS
    website publishes summary tables; we download the state-level overview.
    """
    import uuid

    # NASS publishes census summary tables - try the QuickStats CSV endpoint
    csv_url = (
        f"https://quickstats.nass.usda.gov/results/"
        f"?source_desc=CENSUS&year={census_year}"
        f"&agg_level_desc=STATE&format=csv"
    )

    logger.info(
        "No API key provided. Attempting bulk CSV download for Census %d",
        census_year,
    )

    try:
        resp = _request_with_retry("GET", csv_url)
        df = pd.read_csv(io.StringIO(resp.text), on_bad_lines="skip")
        logger.info("Downloaded %d rows from Census bulk CSV", len(df))
    except (requests.HTTPError, pd.errors.ParserError) as exc:
        logger.warning(
            "Bulk CSV download failed (%s). Returning empty dataset. "
            "Provide an API key for reliable Census data access.",
            exc,
        )
        df = pd.DataFrame(columns=list(CENSUS_AG_SCHEMA.keys()))
        file_path = out / f"census_ag_{census_year}.parquet"
        return _save_parquet(df, file_path)

    # Apply the same mapping used for NASS API responses
    df = _map_nass_to_schema(df)

    # Add record IDs
    if "record_id" not in df.columns:
        df["record_id"] = [str(uuid.uuid4()) for _ in range(len(df))]

    df = _add_metadata_columns(df, "Census_of_Agriculture_Bulk")
    df = _align_schema(df, CENSUS_AG_SCHEMA)

    file_path = out / f"census_ag_{census_year}.parquet"
    return _save_parquet(df, file_path)


# ---------------------------------------------------------------------------
# 5. Validation
# ---------------------------------------------------------------------------

def validate_download(file_path: str | Path) -> dict[str, Any]:
    """
    Validate a downloaded parquet file.

    Performs the following checks:

    1. **File exists** and is readable.
    2. **Schema check** - Verifies that essential columns are present.
    3. **Row count** - Ensures the file is not empty.
    4. **Null check** - Reports percentage of nulls per column.
    5. **Data type check** - Verifies parquet column types are sensible.

    Args:
        file_path: Path to the parquet file.

    Returns:
        Dictionary with validation results::

            {
                "valid": bool,
                "file_path": str,
                "row_count": int,
                "column_count": int,
                "columns": [...],
                "null_percentages": {col: float, ...},
                "schema_issues": [...],
                "errors": [...],
            }
    """
    result: dict[str, Any] = {
        "valid": False,
        "file_path": str(file_path),
        "row_count": 0,
        "column_count": 0,
        "columns": [],
        "null_percentages": {},
        "schema_issues": [],
        "errors": [],
    }

    path = Path(file_path)

    # 1. File existence
    if not path.exists():
        result["errors"].append(f"File not found: {path}")
        return result

    if not path.suffix == ".parquet":
        result["errors"].append(f"Expected .parquet extension, got: {path.suffix}")
        return result

    # 2. Read the file
    try:
        table = pq.read_table(path)
        df = table.to_pandas()
    except Exception as exc:
        result["errors"].append(f"Failed to read parquet file: {exc}")
        return result

    result["row_count"] = len(df)
    result["column_count"] = len(df.columns)
    result["columns"] = list(df.columns)

    # 3. Row count check
    if len(df) == 0:
        result["schema_issues"].append("File contains 0 rows")

    # 4. Null percentage per column
    null_pcts: dict[str, float] = {}
    for col in df.columns:
        null_count = df[col].isna().sum()
        null_pcts[col] = round(float(null_count / max(len(df), 1)) * 100, 2)
    result["null_percentages"] = null_pcts

    # Flag columns that are entirely null
    fully_null = [c for c, pct in null_pcts.items() if pct == 100.0 and len(df) > 0]
    if fully_null:
        result["schema_issues"].append(
            f"Columns entirely null: {', '.join(fully_null)}"
        )

    # 5. Check for expected metadata columns
    expected_meta = {"_ingested_at", "_source", "_batch_id"}
    missing_meta = expected_meta - set(df.columns)
    if missing_meta:
        result["schema_issues"].append(
            f"Missing metadata columns: {', '.join(sorted(missing_meta))}"
        )

    # 6. Data type sanity
    schema = table.schema
    for i in range(len(schema)):
        field = schema.field(i)
        if "id" in field.name.lower() and not pa.types.is_string(field.type):
            if not pa.types.is_large_string(field.type) and not pa.types.is_dictionary(field.type):
                result["schema_issues"].append(
                    f"Column '{field.name}' looks like an ID but has type {field.type}"
                )

    # Overall validity: no hard errors and at least 1 row
    result["valid"] = len(result["errors"]) == 0 and result["row_count"] > 0

    return result


# ---------------------------------------------------------------------------
# 6. CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point for downloading USDA open datasets."""
    _setup_logging()

    parser = argparse.ArgumentParser(
        description="Download real USDA open datasets for POC demonstrations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Download NASS corn data with API key\n"
            "  python usda_download.py --dataset nass --api-key YOUR_KEY --commodity CORN\n"
            "\n"
            "  # Download FSIS recalls (no key needed)\n"
            "  python usda_download.py --dataset fsis\n"
            "\n"
            "  # Download SNAP retailers for Illinois\n"
            "  python usda_download.py --dataset snap --state 17\n"
            "\n"
            "  # Download all datasets\n"
            "  python usda_download.py --dataset all --api-key YOUR_KEY\n"
        ),
    )
    parser.add_argument(
        "--dataset",
        choices=["nass", "fsis", "snap", "census", "all"],
        required=True,
        help="Which dataset to download.",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="NASS API key (required for nass and census datasets, or 'all').",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--state",
        default=None,
        dest="state_fips",
        help="2-digit state FIPS code (e.g., 17 for Illinois).",
    )
    parser.add_argument(
        "--year-start",
        type=int,
        default=2018,
        help="Start year for data download (default: 2018).",
    )
    parser.add_argument(
        "--year-end",
        type=int,
        default=2023,
        help="End year for data download (default: 2023).",
    )
    parser.add_argument(
        "--commodity",
        default="CORN",
        help="Commodity for NASS download (default: CORN).",
    )
    parser.add_argument(
        "--census-year",
        type=int,
        default=2022,
        help="Census year for agriculture census (default: 2022).",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validation on downloaded files after completion.",
    )

    args = parser.parse_args()
    dataset = args.dataset
    output_dir = args.output_dir
    downloaded_files: list[Path] = []

    # Dispatch downloads
    if dataset in ("nass", "all"):
        if not args.api_key:
            logger.error("--api-key is required for NASS dataset download")
            if dataset == "nass":
                sys.exit(1)
        else:
            path = download_nass_quickstats(
                api_key=args.api_key,
                commodity=args.commodity,
                year_start=args.year_start,
                year_end=args.year_end,
                state_fips=args.state_fips,
                output_dir=output_dir,
            )
            downloaded_files.append(path)

    if dataset in ("fsis", "all"):
        path = download_fsis_recalls(
            output_dir=output_dir,
            year_start=args.year_start if args.year_start != 2018 else None,
        )
        downloaded_files.append(path)

    if dataset in ("snap", "all"):
        path = download_snap_retailers(
            output_dir=output_dir,
            state_fips=args.state_fips,
        )
        downloaded_files.append(path)

    if dataset in ("census", "all"):
        path = download_census_of_agriculture(
            output_dir=output_dir,
            census_year=args.census_year,
            api_key=args.api_key,
        )
        downloaded_files.append(path)

    # Summary
    logger.info("=" * 60)
    logger.info("Download complete. Files:")
    for fp in downloaded_files:
        logger.info("  %s", fp)

    # Optional validation
    if args.validate and downloaded_files:
        logger.info("=" * 60)
        logger.info("Running validation on downloaded files...")
        all_valid = True
        for fp in downloaded_files:
            result = validate_download(fp)
            status = "PASS" if result["valid"] else "FAIL"
            logger.info(
                "  [%s] %s - %d rows, %d columns",
                status,
                fp.name,
                result["row_count"],
                result["column_count"],
            )
            if result["schema_issues"]:
                for issue in result["schema_issues"]:
                    logger.warning("    Issue: %s", issue)
            if result["errors"]:
                for err in result["errors"]:
                    logger.error("    Error: %s", err)
                all_valid = False

        if not all_valid:
            logger.warning("Some validations failed. Review the output above.")
            sys.exit(1)

    logger.info("Done.")


if __name__ == "__main__":
    main()
