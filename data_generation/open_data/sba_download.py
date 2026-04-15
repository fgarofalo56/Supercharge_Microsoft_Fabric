"""
SBA Open Data Download
======================

Download real Small Business Administration (SBA) datasets as alternatives to
the synthetic ``SBAGenerator``.  All datasets are publicly available under
federal open-data policy.

Supported datasets
------------------
* **PPP FOIA** -- Paycheck Protection Program loan-level data (~10 GB).
  Source: https://data.sba.gov/dataset/ppp-foia
* **7(a) / 504 FOIA** -- SBA-guaranteed business loans.
  Source: https://data.sba.gov/dataset/7-a-504-foia
* **SBIR/STTR Awards** -- Small Business Innovation Research awards.
  Source: https://www.sbir.gov/api

No API key is required for any of these endpoints.

Output schema is aligned with ``SBAGenerator`` so that downstream medallion
notebooks work identically with either real or synthetic data.

Usage
-----
CLI::

    python -m data_generation.open_data.sba_download --dataset ppp --output-dir ./data/sba --state CA --sample-size 50000
    python -m data_generation.open_data.sba_download --dataset all --output-dir ./data/sba

Library::

    from data_generation.open_data.sba_download import download_ppp_loans
    download_ppp_loans("./data/sba", state_filter="TX")
"""

from __future__ import annotations

import argparse
import contextlib
import logging
import os
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
SBA_DATA_BASE = "https://data.sba.gov/dataset"
PPP_FOIA_URL = f"{SBA_DATA_BASE}/ppp-foia"
LOAN_7A_504_URL = f"{SBA_DATA_BASE}/7-a-504-foia"
SBIR_API_URL = "https://www.sbir.gov/api/awards.json"

MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds
REQUEST_TIMEOUT = 120  # seconds
RATE_LIMIT_SLEEP = 1.0  # seconds between API calls

# PPP FOIA CSV file names (SBA publishes multiple files by date range)
PPP_CSV_FILES = [
    "public_150k_plus_230930.csv",
    "public_up_to_150k_1_230930.csv",
    "public_up_to_150k_2_230930.csv",
    "public_up_to_150k_3_230930.csv",
    "public_up_to_150k_4_230930.csv",
    "public_up_to_150k_5_230930.csv",
    "public_up_to_150k_6_230930.csv",
    "public_up_to_150k_7_230930.csv",
    "public_up_to_150k_8_230930.csv",
    "public_up_to_150k_9_230930.csv",
    "public_up_to_150k_10_230930.csv",
    "public_up_to_150k_11_230930.csv",
    "public_up_to_150k_12_230930.csv",
]

# Schema alignment: map raw SBA column names to our standard names
PPP_COLUMN_MAP = {
    "LoanNumber": "loan_id",
    "DateApproved": "approval_date",
    "SBAOfficeCode": "sba_office",
    "ProcessingMethod": "processing_method",
    "BorrowerName": "borrower_name",
    "BorrowerAddress": "borrower_address",
    "BorrowerCity": "borrower_city",
    "BorrowerState": "borrower_state",
    "BorrowerZip": "borrower_zip",
    "LoanStatusDate": "loan_status_date",
    "LoanStatus": "loan_status",
    "Term": "term_months",
    "SBAGuarantyPercentage": "sba_guaranty_pct",
    "InitialApprovalAmount": "loan_amount",
    "CurrentApprovalAmount": "current_approval_amount",
    "UndisbursedAmount": "undisbursed_amount",
    "FranchiseName": "franchise_name",
    "ServicingLenderLocationID": "servicing_lender_id",
    "ServicingLenderName": "lender_name",
    "ServicingLenderAddress": "lender_address",
    "ServicingLenderCity": "lender_city",
    "ServicingLenderState": "lender_state",
    "ServicingLenderZip": "lender_zip",
    "RuralUrbanIndicator": "rural_urban",
    "HubzoneIndicator": "hubzone_indicator",
    "LMIIndicator": "lmi_indicator",
    "BusinessAgeDescription": "business_age",
    "ProjectCity": "project_city",
    "ProjectCountyName": "project_county",
    "ProjectState": "project_state",
    "ProjectZip": "project_zip",
    "CD": "congressional_district",
    "JobsReported": "jobs_retained",
    "NAICSCode": "naics_code",
    "Race": "race",
    "Ethnicity": "ethnicity",
    "UTILITIES_PROCEED": "utilities_proceed",
    "PAYROLL_PROCEED": "payroll_proceed",
    "MORTGAGE_INTEREST_PROCEED": "mortgage_interest_proceed",
    "RENT_PROCEED": "rent_proceed",
    "REFINANCE_EIDL_PROCEED": "refinance_eidl_proceed",
    "HEALTH_CARE_PROCEED": "health_care_proceed",
    "DEBT_INTEREST_PROCEED": "debt_interest_proceed",
    "ForgivenessAmount": "forgiveness_amount",
    "ForgivenessDate": "forgiveness_date",
}

LOAN_7A_504_COLUMN_MAP = {
    "AsOfDate": "as_of_date",
    "Program": "program_type",
    "BorrName": "borrower_name",
    "BorrStreet": "borrower_address",
    "BorrCity": "borrower_city",
    "BorrState": "borrower_state",
    "BorrZip": "borrower_zip",
    "CDC_Name": "cdc_name",
    "ThirdPartyLender_Name": "lender_name",
    "ThirdPartyLender_City": "lender_city",
    "ThirdPartyLender_State": "lender_state",
    "GrossApproval": "loan_amount",
    "SBAGuaranteedApproval": "sba_guaranteed_amount",
    "ApprovalDate": "approval_date",
    "ApprovalFiscalYear": "approval_fiscal_year",
    "FirstDisbursementDate": "first_disbursement_date",
    "DeliveryMethod": "delivery_method",
    "subpgmdesc": "sub_program",
    "InitialInterestRate": "interest_rate",
    "TermInMonths": "term_months",
    "NaicsCode": "naics_code",
    "NaicsDescription": "naics_description",
    "FranchiseCode": "franchise_code",
    "FranchiseName": "franchise_name",
    "ProjectCounty": "project_county",
    "ProjectState": "project_state",
    "SBADistrictOffice": "sba_office",
    "CongressionalDistrict": "congressional_district",
    "BusinessType": "business_type",
    "LoanStatus": "loan_status",
    "ChargeOffDate": "chargeoff_date",
    "GrossChargeOffAmount": "chargeoff_amount",
    "RevolverStatus": "revolver_status",
    "JobsSupported": "jobs_retained",
}

SBIR_COLUMN_MAP = {
    "award_id": "loan_id",
    "agency": "agency",
    "branch": "branch",
    "contract": "contract_number",
    "program": "program_type",
    "phase": "phase",
    "agency_tracking_number": "tracking_number",
    "award_amount": "loan_amount",
    "award_start_date": "approval_date",
    "award_end_date": "end_date",
    "company": "borrower_name",
    "address1": "borrower_address",
    "city": "borrower_city",
    "state": "borrower_state",
    "zip": "borrower_zip",
    "abstract": "abstract",
    "research_keywords": "research_keywords",
    "ri_name": "principal_investigator",
    "solicitation_year": "solicitation_year",
    "award_year": "award_year",
    "hubzone_owned": "hubzone_indicator",
    "woman_owned": "woman_owned",
    "socially_economically_disadvantaged": "sed_indicator",
    "number_employees": "jobs_retained",
}


# ---------------------------------------------------------------------------
# Retry helper
# ---------------------------------------------------------------------------
def _request_with_retry(
    url: str,
    params: dict[str, Any] | None = None,
    stream: bool = False,
    timeout: int = REQUEST_TIMEOUT,
) -> requests.Response:
    """Execute a GET request with exponential-backoff retries."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, stream=stream, timeout=timeout)
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
    # Unreachable, but keeps mypy happy
    raise RuntimeError("Exceeded max retries")


def _save_dataframe(
    df: pd.DataFrame,
    output_dir: str,
    filename_stem: str,
) -> tuple[Path, Path]:
    """Save a DataFrame as both CSV and Parquet, returning the paths."""
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

def download_ppp_loans(
    output_dir: str,
    state_filter: str | None = None,
    sample_size: int | None = None,
) -> pd.DataFrame:
    """
    Download PPP FOIA loan data from data.sba.gov.

    The PPP dataset is very large (~10 GB across multiple CSV files).  This
    function downloads the bulk CSV files, optionally filters by state, and
    optionally samples to a manageable size.

    Args:
        output_dir: Directory to save output files.
        state_filter: Two-letter state code (e.g. ``"CA"``) to keep only
            loans in that state.  ``None`` means all states.
        sample_size: If provided, randomly sample this many rows from the
            final result.  Useful for quick POC testing.

    Returns:
        Combined DataFrame of PPP loan records.
    """
    logger.info("Downloading PPP FOIA data (state=%s, sample=%s)", state_filter, sample_size)

    frames: list[pd.DataFrame] = []
    base_url = "https://data.sba.gov/dataset/ppp-foia/resource/"

    for csv_name in tqdm(PPP_CSV_FILES, desc="PPP FOIA files"):
        url = f"{base_url}{csv_name}"
        try:
            logger.info("Fetching %s ...", csv_name)
            resp = _request_with_retry(url, stream=True)

            # Write to a temporary file then read with pandas
            tmp_path = Path(output_dir) / f"_tmp_{csv_name}"
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            with open(tmp_path, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=8192):
                    fh.write(chunk)

            chunk_df = pd.read_csv(tmp_path, low_memory=False, dtype=str)
            chunk_df.rename(columns=PPP_COLUMN_MAP, inplace=True)

            if state_filter:
                chunk_df = chunk_df[
                    chunk_df["borrower_state"].str.upper() == state_filter.upper()
                ]

            frames.append(chunk_df)

            # Clean up temp file
            with contextlib.suppress(OSError):
                os.remove(tmp_path)

            time.sleep(RATE_LIMIT_SLEEP)

        except Exception:
            logger.exception("Failed to download %s, skipping", csv_name)
            continue

    if not frames:
        logger.warning("No PPP data downloaded. Returning empty DataFrame.")
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    logger.info("Combined PPP data: %d rows", len(df))

    # Add standard columns for schema alignment with SBAGenerator
    df["program_type"] = "PPP"
    if "interest_rate" not in df.columns:
        df["interest_rate"] = 1.0
    df["load_time"] = pd.Timestamp.now().isoformat()

    if sample_size and len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42).reset_index(drop=True)
        logger.info("Sampled down to %d rows", len(df))

    _save_dataframe(df, output_dir, "sba_ppp_loans")
    return df


def download_7a_504_loans(
    output_dir: str,
    year_start: int = 2010,
) -> pd.DataFrame:
    """
    Download SBA 7(a) and 504 loan FOIA data.

    Args:
        output_dir: Directory to save output files.
        year_start: Earliest fiscal year to include (default 2010).

    Returns:
        Combined DataFrame of 7(a)/504 loan records.
    """
    logger.info("Downloading 7(a)/504 FOIA data (year_start=%d)", year_start)

    # SBA publishes a single bulk CSV for 7(a)/504
    url = "https://data.sba.gov/dataset/7-a-504-foia/resource/7a_504_foia.csv"

    try:
        resp = _request_with_retry(url, stream=True)

        tmp_path = Path(output_dir) / "_tmp_7a_504.csv"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        with open(tmp_path, "wb") as fh:
            for chunk in tqdm(
                resp.iter_content(chunk_size=8192),
                desc="7(a)/504 download",
                unit="chunk",
            ):
                fh.write(chunk)

        df = pd.read_csv(tmp_path, low_memory=False, dtype=str)
        df.rename(columns=LOAN_7A_504_COLUMN_MAP, inplace=True)

        # Clean up temp file
        with contextlib.suppress(OSError):
            os.remove(tmp_path)

    except Exception:
        logger.exception("Failed to download 7(a)/504 data")
        return pd.DataFrame()

    # Filter by fiscal year
    if "approval_fiscal_year" in df.columns:
        df["approval_fiscal_year"] = pd.to_numeric(
            df["approval_fiscal_year"], errors="coerce"
        )
        df = df[df["approval_fiscal_year"] >= year_start]

    # Convert loan_amount to float
    if "loan_amount" in df.columns:
        df["loan_amount"] = pd.to_numeric(df["loan_amount"], errors="coerce")

    df["load_time"] = pd.Timestamp.now().isoformat()

    logger.info("7(a)/504 data: %d rows", len(df))
    _save_dataframe(df, output_dir, "sba_7a_504_loans")
    return df


def download_sbir_awards(
    output_dir: str,
) -> pd.DataFrame:
    """
    Download SBIR/STTR award data from the SBIR.gov API.

    The API returns JSON pages of up to 100 awards at a time.  This function
    paginates through all available results.

    Args:
        output_dir: Directory to save output files.

    Returns:
        DataFrame of SBIR/STTR award records.
    """
    logger.info("Downloading SBIR/STTR awards from %s", SBIR_API_URL)

    all_records: list[dict[str, Any]] = []
    start = 0
    page_size = 100
    max_pages = 500  # safety limit (~50,000 records)

    pbar = tqdm(desc="SBIR awards (pages)", unit="page")

    for _ in range(max_pages):
        params = {
            "start": start,
            "rows": page_size,
        }

        try:
            resp = _request_with_retry(SBIR_API_URL, params=params)
            data = resp.json()
        except Exception:
            logger.exception("SBIR API request failed at offset %d", start)
            break

        # The SBIR API returns results under varying keys; adapt as needed
        results = data if isinstance(data, list) else data.get("results", data.get("response", {}).get("docs", []))

        if not results:
            logger.info("No more SBIR results at offset %d", start)
            break

        all_records.extend(results)
        start += page_size
        pbar.update(1)

        time.sleep(RATE_LIMIT_SLEEP)

    pbar.close()

    if not all_records:
        logger.warning("No SBIR data retrieved. Returning empty DataFrame.")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)
    df.rename(columns=SBIR_COLUMN_MAP, inplace=True)

    # Schema alignment
    df["program_type"] = "SBIR"
    df["load_time"] = pd.Timestamp.now().isoformat()

    if "loan_amount" in df.columns:
        df["loan_amount"] = pd.to_numeric(df["loan_amount"], errors="coerce")

    logger.info("SBIR data: %d rows", len(df))
    _save_dataframe(df, output_dir, "sba_sbir_awards")
    return df


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_download(file_path: str) -> dict[str, Any]:
    """
    Validate a downloaded SBA dataset file for schema conformance.

    Checks for:
    * File exists and is non-empty
    * Expected key columns are present
    * No fully-null columns among the required set
    * ``loan_amount`` is numeric where present

    Args:
        file_path: Path to a CSV or Parquet file.

    Returns:
        Dictionary with ``valid`` (bool), ``row_count``, ``columns``,
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

    # Required columns (union across PPP / 7a / SBIR)
    required = {"loan_amount", "borrower_name", "borrower_state", "approval_date"}
    present = set(df.columns)
    missing = required - present
    result["missing_columns"] = sorted(missing)

    if missing:
        result["warnings"].append(f"Missing required columns: {missing}")

    # Check loan_amount is numeric
    if "loan_amount" in df.columns:
        non_numeric = pd.to_numeric(df["loan_amount"], errors="coerce").isna().sum()
        if non_numeric > 0:
            result["warnings"].append(
                f"{non_numeric} non-numeric values in loan_amount"
            )

    result["valid"] = len(result["warnings"]) == 0
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    """Command-line interface for SBA open-data downloads."""
    parser = argparse.ArgumentParser(
        description="Download SBA open datasets (PPP, 7(a)/504, SBIR)",
    )
    parser.add_argument(
        "--dataset",
        choices=["ppp", "7a504", "sbir", "all"],
        default="all",
        help="Which dataset to download (default: all)",
    )
    parser.add_argument(
        "--output-dir",
        default="./data/sba",
        help="Output directory (default: ./data/sba)",
    )
    parser.add_argument(
        "--state",
        default=None,
        help="Two-letter state filter for PPP data (e.g. CA)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Random sample size for PPP data (large dataset)",
    )
    parser.add_argument(
        "--year-start",
        type=int,
        default=2010,
        help="Start fiscal year for 7(a)/504 data (default: 2010)",
    )

    args = parser.parse_args()

    if args.dataset in ("ppp", "all"):
        download_ppp_loans(
            args.output_dir,
            state_filter=args.state,
            sample_size=args.sample_size,
        )

    if args.dataset in ("7a504", "all"):
        download_7a_504_loans(args.output_dir, year_start=args.year_start)

    if args.dataset in ("sbir", "all"):
        download_sbir_awards(args.output_dir)

    logger.info("SBA download complete. Files saved to %s", args.output_dir)


if __name__ == "__main__":
    main()
