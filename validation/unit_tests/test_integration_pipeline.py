"""
End-to-End Integration Pipeline Tests
======================================

Validates the full pipeline flow (Generator -> Bronze schema -> Silver transforms
-> Gold KPIs) for all 8 domains: Casino + 7 federal agencies.

These tests do NOT require Spark. They validate using pandas and the synthetic
generators, simulating the medallion architecture transformations that would
occur in Microsoft Fabric notebooks.

Test classes (8 classes x 4 tests = 32 total):
  1. TestCasinoIntegrationPipeline  - SlotMachineGenerator
  2. TestUSDAIntegrationPipeline    - USDAGenerator
  3. TestSBAIntegrationPipeline     - SBAGenerator
  4. TestNOAAIntegrationPipeline    - NOAAGenerator
  5. TestEPAIntegrationPipeline     - EPAGenerator
  6. TestDOIIntegrationPipeline     - DOIGenerator
  7. TestTribalHealthIntegrationPipeline - TribalHealthcareGenerator
  8. TestDotFaaIntegrationPipeline  - DOTFAAGenerator
"""

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Ensure generators are importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "data_generation"))

from generators.federal.doi_generator import DOIGenerator
from generators.federal.dot_faa_generator import DOTFAAGenerator
from generators.federal.epa_generator import EPAGenerator
from generators.federal.noaa_generator import NOAAGenerator
from generators.federal.sba_generator import SBAGenerator
from generators.federal.tribal_healthcare_generator import TribalHealthcareGenerator
from generators.federal.usda_generator import USDAGenerator
from generators.slot_machine_generator import SlotMachineGenerator

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------
SEED = 42
SAMPLE_SIZE = 50
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2024, 12, 31)


# ===========================================================================
# Helper functions: simulate medallion layer transforms
# ===========================================================================


def _bronze_ingest(records: list[dict]) -> pd.DataFrame:
    """Simulate Bronze layer: raw append-only ingestion with no transformations."""
    df = pd.DataFrame(records)
    df["_bronze_ingested_at"] = datetime.now().isoformat()
    return df


def _silver_dedup(
    df: pd.DataFrame, key_column: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Simulate Silver layer deduplication by business key.

    Returns:
        Tuple of (deduplicated DataFrame, rejected duplicates DataFrame).
    """
    duplicates = df[df.duplicated(subset=[key_column], keep="first")]
    deduped = df.drop_duplicates(subset=[key_column], keep="first")
    return deduped, duplicates


def _silver_validate_not_null(
    df: pd.DataFrame, required_cols: list[str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Simulate Silver layer null validation.

    Returns:
        Tuple of (valid records, rejected records with nulls in required columns).
    """
    mask = df[required_cols].notnull().all(axis=1)
    return df[mask].copy(), df[~mask].copy()


def _silver_validate_range(
    df: pd.DataFrame, column: str, low: float, high: float
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Simulate Silver layer range validation.

    Returns:
        Tuple of (records within range, records outside range).
    """
    if column not in df.columns:
        return df.copy(), pd.DataFrame()
    numeric_mask = pd.to_numeric(df[column], errors="coerce").notnull()
    in_range = numeric_mask & (df[column] >= low) & (df[column] <= high)
    return df[in_range].copy(), df[~in_range].copy()


def _silver_compute_dq_score(
    df: pd.DataFrame, required_cols: list[str]
) -> pd.DataFrame:
    """
    Compute a data quality score: fraction of required columns that are non-null.
    """
    result = df.copy()
    present = [c for c in required_cols if c in result.columns]
    if present:
        result["_dq_score"] = result[present].notnull().mean(axis=1)
    else:
        result["_dq_score"] = 1.0
    return result


def _gold_aggregate(
    df: pd.DataFrame, group_col: str, agg_col: str, agg_func: str = "sum"
) -> pd.DataFrame:
    """
    Simulate Gold layer aggregation.

    Returns:
        Aggregated DataFrame grouped by group_col.
    """
    if agg_col not in df.columns or group_col not in df.columns:
        return pd.DataFrame()
    numeric_col = pd.to_numeric(df[agg_col], errors="coerce")
    temp = df.copy()
    temp[agg_col] = numeric_col
    temp = temp.dropna(subset=[agg_col])
    if temp.empty:
        return pd.DataFrame()
    return (
        temp.groupby(group_col)
        .agg(
            **{
                f"{agg_col}_{agg_func}": (agg_col, agg_func),
                "record_count": (agg_col, "count"),
            }
        )
        .reset_index()
    )


# ===========================================================================
# 1. Casino Integration Pipeline
# ===========================================================================


class TestCasinoIntegrationPipeline:
    """End-to-end validation: SlotMachineGenerator -> Bronze schema -> Silver rules -> Gold KPIs."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.gen = SlotMachineGenerator(
            num_machines=20, seed=SEED, start_date=START_DATE, end_date=END_DATE
        )
        self.records = [self.gen.generate_record() for _ in range(SAMPLE_SIZE)]

    def test_generator_produces_valid_bronze_data(self):
        """Generator output matches Bronze layer expected schema."""
        df = _bronze_ingest(self.records)

        # Required Bronze columns for slot telemetry
        required = [
            "event_id",
            "machine_id",
            "event_type",
            "event_timestamp",
            "denomination",
            "machine_type",
            "manufacturer",
            "_source",
        ]
        for col in required:
            assert col in df.columns, f"Missing Bronze column: {col}"

        # Validate no nulls in required fields
        for col in required:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Bronze column '{col}' has {null_count} nulls"

        # Validate data types (pandas 2.x may return StringDtype for inferred
        # string columns; accept either object or any string-like dtype).
        import pandas as _pd

        assert df["denomination"].dtype in (np.float64, float, object)
        event_id_dtype = df["event_id"].dtype
        assert event_id_dtype == object or _pd.api.types.is_string_dtype(event_id_dtype)
        assert len(df) == SAMPLE_SIZE

        # Validate event_type is from allowed set
        valid_types = {
            "GAME_PLAY",
            "JACKPOT",
            "METER_UPDATE",
            "DOOR_OPEN",
            "DOOR_CLOSE",
            "BILL_IN",
            "TICKET_OUT",
            "TILT",
            "POWER_OFF",
            "POWER_ON",
        }
        assert set(df["event_type"].unique()).issubset(valid_types)

    def test_bronze_to_silver_transformations(self):
        """Silver layer rules produce valid cleansed data."""
        bronze = _bronze_ingest(self.records)

        # Dedup by event_id
        silver, dupes = _silver_dedup(bronze, "event_id")
        assert len(silver) + len(dupes) == len(bronze)

        # Validate non-null required fields
        silver, null_rejects = _silver_validate_not_null(
            silver, ["event_id", "machine_id", "event_type"]
        )
        assert len(null_rejects) == 0, (
            "Silver should have no null event_id/machine_id/event_type"
        )

        # Compute DQ score
        silver = _silver_compute_dq_score(
            silver, ["event_id", "machine_id", "event_type", "denomination", "coin_in"]
        )
        assert "_dq_score" in silver.columns
        assert silver["_dq_score"].min() > 0.0, (
            "Every Silver record has at least some fields"
        )

        # Validate denomination > 0
        denom_valid, _denom_invalid = _silver_validate_range(
            silver, "denomination", 0.001, 1000.0
        )
        assert len(denom_valid) == len(silver), "All denominations should be positive"

    def test_silver_to_gold_aggregations(self):
        """Gold layer aggregations produce valid KPIs."""
        bronze = _bronze_ingest(self.records)
        silver, _ = _silver_dedup(bronze, "event_id")

        # Gold KPI: total coin_in per machine_type
        gold = _gold_aggregate(silver, "machine_type", "coin_in", "sum")
        if not gold.empty:
            assert "coin_in_sum" in gold.columns
            assert "record_count" in gold.columns
            # No division by zero: record_count always > 0
            assert (gold["record_count"] > 0).all()
            # Aggregation grain: one row per machine_type
            assert gold["machine_type"].is_unique

        # Gold KPI: total coin_out per zone
        gold_zone = _gold_aggregate(silver, "zone", "coin_out", "sum")
        if not gold_zone.empty:
            assert gold_zone["zone"].is_unique

    def test_full_pipeline_data_lineage(self):
        """Record counts are consistent across layers."""
        bronze = _bronze_ingest(self.records)
        assert len(bronze) == SAMPLE_SIZE, "Bronze count == N (append-only)"

        silver, dupes = _silver_dedup(bronze, "event_id")
        silver_valid, silver_rejects = _silver_validate_not_null(
            silver, ["event_id", "machine_id", "event_type"]
        )
        # Silver count <= Bronze (dedup may reduce)
        assert len(silver) <= len(bronze)
        # No data loss: dupes + silver == bronze
        assert len(silver) + len(dupes) == len(bronze)
        # Rejects + passes == Silver count
        assert len(silver_valid) + len(silver_rejects) == len(silver)

        # Gold count <= Silver count (aggregation reduces)
        gold = _gold_aggregate(silver_valid, "machine_type", "coin_in", "sum")
        if not gold.empty:
            assert len(gold) <= len(silver_valid)


# ===========================================================================
# 2. USDA Integration Pipeline
# ===========================================================================


class TestUSDAIntegrationPipeline:
    """End-to-end validation: USDA generator -> Bronze schema -> Silver rules -> Gold KPIs."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.gen = USDAGenerator(seed=SEED, start_date=START_DATE, end_date=END_DATE)
        self.records = [
            self.gen.generate_record(domain="crop_production")
            for _ in range(SAMPLE_SIZE)
        ]

    def test_generator_produces_valid_bronze_data(self):
        """Generator output matches Bronze layer expected schema."""
        df = _bronze_ingest(self.records)

        required = [
            "record_id",
            "commodity",
            "year",
            "state_fips",
            "state_name",
            "statisticcat_desc",
            "unit_desc",
            "value",
            "source_desc",
            "agg_level_desc",
            "_source",
        ]
        for col in required:
            assert col in df.columns, f"Missing Bronze column: {col}"

        # No nulls in core required fields
        for col in [
            "record_id",
            "commodity",
            "year",
            "state_fips",
            "state_name",
            "value",
        ]:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Bronze column '{col}' has {null_count} nulls"

        assert len(df) == SAMPLE_SIZE

        # Validate commodity is from known set
        valid_commodities = {
            "CORN",
            "SOYBEANS",
            "WHEAT",
            "COTTON",
            "RICE",
            "BARLEY",
            "OATS",
            "SORGHUM",
            "HAY",
            "POTATOES",
        }
        assert set(df["commodity"].unique()).issubset(valid_commodities)

        # Validate year range
        years = df["year"].unique()
        assert all(2015 <= y <= 2025 for y in years)

    def test_bronze_to_silver_transformations(self):
        """Silver layer rules produce valid cleansed data."""
        bronze = _bronze_ingest(self.records)

        # Dedup by record_id
        silver, dupes = _silver_dedup(bronze, "record_id")
        assert len(silver) + len(dupes) == len(bronze)

        # Validate value > 0 (crop stats should be positive)
        value_valid, _value_invalid = _silver_validate_range(
            silver, "value", 0.0, float("inf")
        )
        assert len(value_valid) == len(silver), (
            "All crop production values should be >= 0"
        )

        # Compute DQ score
        silver = _silver_compute_dq_score(
            silver,
            ["record_id", "commodity", "year", "state_fips", "value", "cv_percent"],
        )
        # cv_percent can be null for CENSUS records, so DQ < 1.0 is expected for some
        assert silver["_dq_score"].min() >= 0.5, "DQ score should be at least 50%"

        # Standardize agg_level_desc
        valid_agg = {"NATIONAL", "STATE", "COUNTY"}
        assert set(silver["agg_level_desc"].unique()).issubset(valid_agg)

    def test_silver_to_gold_aggregations(self):
        """Gold layer aggregations produce valid KPIs."""
        bronze = _bronze_ingest(self.records)
        silver, _ = _silver_dedup(bronze, "record_id")

        # Gold KPI: average value per commodity
        gold = _gold_aggregate(silver, "commodity", "value", "mean")
        if not gold.empty:
            assert "value_mean" in gold.columns
            assert "record_count" in gold.columns
            assert (gold["record_count"] > 0).all(), "No division by zero"
            assert gold["commodity"].is_unique, "One row per commodity"

        # Gold KPI: sum by state
        gold_state = _gold_aggregate(silver, "state_name", "value", "sum")
        if not gold_state.empty:
            assert gold_state["state_name"].is_unique

    def test_full_pipeline_data_lineage(self):
        """Record counts are consistent across layers."""
        bronze = _bronze_ingest(self.records)
        assert len(bronze) == SAMPLE_SIZE

        silver, dupes = _silver_dedup(bronze, "record_id")
        silver_valid, silver_rejects = _silver_validate_not_null(
            silver, ["record_id", "commodity", "value"]
        )
        assert len(silver) <= len(bronze)
        assert len(silver) + len(dupes) == len(bronze)
        assert len(silver_valid) + len(silver_rejects) == len(silver)

        gold = _gold_aggregate(silver_valid, "commodity", "value", "mean")
        if not gold.empty:
            assert len(gold) <= len(silver_valid)


# ===========================================================================
# 3. SBA Integration Pipeline
# ===========================================================================


class TestSBAIntegrationPipeline:
    """End-to-end validation: SBA generator -> Bronze schema -> Silver rules -> Gold KPIs."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.gen = SBAGenerator(seed=SEED, start_date=START_DATE, end_date=END_DATE)
        self.records = [
            self.gen.generate_record(domain="ppp") for _ in range(SAMPLE_SIZE)
        ]

    def test_generator_produces_valid_bronze_data(self):
        """Generator output matches Bronze layer expected schema."""
        df = _bronze_ingest(self.records)

        required = [
            "loan_id",
            "program_type",
            "loan_amount",
            "approval_date",
            "borrower_name",
            "borrower_state",
            "naics_code",
            "loan_status",
            "term_months",
            "interest_rate",
            "_source",
        ]
        for col in required:
            assert col in df.columns, f"Missing Bronze column: {col}"

        for col in ["loan_id", "program_type", "loan_amount", "borrower_state"]:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Bronze column '{col}' has {null_count} nulls"

        assert len(df) == SAMPLE_SIZE

        # Validate program_type
        assert (df["program_type"] == "PPP").all(), "All records should be PPP domain"

        # Validate loan_amount > 0
        assert (df["loan_amount"] > 0).all(), "All loan amounts must be positive"

        # Validate interest_rate for PPP is 1.0
        assert (df["interest_rate"] == 1.0).all(), "PPP loans have fixed 1% rate"

    def test_bronze_to_silver_transformations(self):
        """Silver layer rules produce valid cleansed data."""
        bronze = _bronze_ingest(self.records)

        silver, dupes = _silver_dedup(bronze, "loan_id")
        assert len(silver) + len(dupes) == len(bronze)

        # Validate loan_amount range ($20K minimum for PPP)
        valid, _invalid = _silver_validate_range(
            silver, "loan_amount", 0.01, 10_000_001.0
        )
        assert len(valid) == len(silver), "All loan amounts should be within range"

        # Validate term_months is reasonable
        valid_term, _ = _silver_validate_range(silver, "term_months", 1, 600)
        assert len(valid_term) == len(silver)

        # Compute DQ score
        silver = _silver_compute_dq_score(
            silver,
            ["loan_id", "loan_amount", "borrower_name", "borrower_city", "naics_code"],
        )
        # borrower_city can be null (~5%) so some DQ < 1.0
        assert silver["_dq_score"].min() >= 0.6, "DQ score should be at least 60%"

        # Validate business_type is from known set
        valid_types = {
            "SOLE_PROPRIETORSHIP",
            "LLC",
            "CORPORATION",
            "PARTNERSHIP",
            "NON_PROFIT",
            "OTHER",
        }
        assert set(silver["business_type"].unique()).issubset(valid_types)

    def test_silver_to_gold_aggregations(self):
        """Gold layer aggregations produce valid KPIs."""
        bronze = _bronze_ingest(self.records)
        silver, _ = _silver_dedup(bronze, "loan_id")

        # Gold KPI: total loan_amount by borrower_state
        gold = _gold_aggregate(silver, "borrower_state", "loan_amount", "sum")
        if not gold.empty:
            assert "loan_amount_sum" in gold.columns
            assert (gold["record_count"] > 0).all()
            assert gold["borrower_state"].is_unique

        # Gold KPI: average loan_amount by loan_status
        gold_status = _gold_aggregate(silver, "loan_status", "loan_amount", "mean")
        if not gold_status.empty:
            assert gold_status["loan_status"].is_unique
            # No negative averages
            assert (gold_status["loan_amount_mean"] > 0).all()

    def test_full_pipeline_data_lineage(self):
        """Record counts are consistent across layers."""
        bronze = _bronze_ingest(self.records)
        assert len(bronze) == SAMPLE_SIZE

        silver, dupes = _silver_dedup(bronze, "loan_id")
        silver_valid, silver_rejects = _silver_validate_not_null(
            silver, ["loan_id", "loan_amount", "borrower_state"]
        )
        assert len(silver) <= len(bronze)
        assert len(silver) + len(dupes) == len(bronze)
        assert len(silver_valid) + len(silver_rejects) == len(silver)

        gold = _gold_aggregate(silver_valid, "borrower_state", "loan_amount", "sum")
        if not gold.empty:
            assert len(gold) <= len(silver_valid)


# ===========================================================================
# 4. NOAA Integration Pipeline
# ===========================================================================


class TestNOAAIntegrationPipeline:
    """End-to-end validation: NOAA generator -> Bronze schema -> Silver rules -> Gold KPIs."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.gen = NOAAGenerator(seed=SEED, start_date=START_DATE, end_date=END_DATE)
        self.records = [
            self.gen.generate_record(domain="weather") for _ in range(SAMPLE_SIZE)
        ]

    def test_generator_produces_valid_bronze_data(self):
        """Generator output matches Bronze layer expected schema."""
        df = _bronze_ingest(self.records)

        required = [
            "observation_id",
            "station_id",
            "station_name",
            "timestamp",
            "latitude",
            "longitude",
            "parameter",
            "value",
            "unit",
            "quality_flag",
            "_source",
        ]
        for col in required:
            assert col in df.columns, f"Missing Bronze column: {col}"

        for col in ["observation_id", "station_id", "parameter", "value"]:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Bronze column '{col}' has {null_count} nulls"

        assert len(df) == SAMPLE_SIZE

        # Validate station_id is from known set
        valid_stations = {
            "KJFK",
            "KLAX",
            "KORD",
            "KATL",
            "KDFW",
            "KDEN",
            "KPHX",
            "KSEA",
            "KMIA",
            "KBOS",
            "KLAS",
            "KMSP",
            "KIAH",
            "KSLC",
            "KPIT",
            "KDTW",
            "KSTL",
            "KMCO",
        }
        assert set(df["station_id"].unique()).issubset(valid_stations)

        # Validate latitude/longitude ranges
        assert (df["latitude"] >= -90).all() and (df["latitude"] <= 90).all()
        assert (df["longitude"] >= -180).all() and (df["longitude"] <= 180).all()

    def test_bronze_to_silver_transformations(self):
        """Silver layer rules produce valid cleansed data."""
        bronze = _bronze_ingest(self.records)

        # Dedup by observation_id
        silver, dupes = _silver_dedup(bronze, "observation_id")
        assert len(silver) + len(dupes) == len(bronze)

        # Filter out ERRONEOUS and MISSING quality flags
        quality_mask = ~silver["quality_flag"].isin(["ERRONEOUS", "MISSING"])
        silver_clean = silver[quality_mask].copy()
        silver_rejected = silver[~quality_mask].copy()
        # All records accounted for
        assert len(silver_clean) + len(silver_rejected) == len(silver)

        # Compute DQ score
        silver_clean = _silver_compute_dq_score(
            silver_clean,
            ["observation_id", "station_id", "parameter", "value", "quality_flag"],
        )
        assert silver_clean["_dq_score"].min() >= 0.8

        # Validate parameter is from known set
        valid_params = {
            "TEMPERATURE",
            "DEWPOINT",
            "HUMIDITY",
            "WIND_SPEED",
            "WIND_DIRECTION",
            "PRESSURE",
            "VISIBILITY",
            "PRECIPITATION",
            "CLOUD_COVER",
        }
        assert set(silver_clean["parameter"].unique()).issubset(valid_params)

    def test_silver_to_gold_aggregations(self):
        """Gold layer aggregations produce valid KPIs."""
        bronze = _bronze_ingest(self.records)
        silver, _ = _silver_dedup(bronze, "observation_id")

        # Gold KPI: average value per parameter
        gold = _gold_aggregate(silver, "parameter", "value", "mean")
        if not gold.empty:
            assert "value_mean" in gold.columns
            assert (gold["record_count"] > 0).all()
            assert gold["parameter"].is_unique

        # Gold KPI: observation count per station
        gold_station = _gold_aggregate(silver, "station_id", "value", "count")
        if not gold_station.empty:
            assert gold_station["station_id"].is_unique

    def test_full_pipeline_data_lineage(self):
        """Record counts are consistent across layers."""
        bronze = _bronze_ingest(self.records)
        assert len(bronze) == SAMPLE_SIZE

        silver, dupes = _silver_dedup(bronze, "observation_id")
        # Quality filter
        quality_mask = ~silver["quality_flag"].isin(["ERRONEOUS", "MISSING"])
        silver_clean = silver[quality_mask].copy()
        silver_rejected = silver[~quality_mask].copy()

        assert len(silver) <= len(bronze)
        assert len(silver) + len(dupes) == len(bronze)
        assert len(silver_clean) + len(silver_rejected) == len(silver)

        gold = _gold_aggregate(silver_clean, "parameter", "value", "mean")
        if not gold.empty:
            assert len(gold) <= len(silver_clean)


# ===========================================================================
# 5. EPA Integration Pipeline
# ===========================================================================


class TestEPAIntegrationPipeline:
    """End-to-end validation: EPA generator -> Bronze schema -> Silver rules -> Gold KPIs."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.gen = EPAGenerator(
            seed=SEED, start_date=START_DATE, end_date=END_DATE, domain="air_quality"
        )
        self.records = [
            self.gen.generate_record(domain="air_quality") for _ in range(SAMPLE_SIZE)
        ]

    def test_generator_produces_valid_bronze_data(self):
        """Generator output matches Bronze layer expected schema."""
        df = _bronze_ingest(self.records)

        required = [
            "record_id",
            "site_id",
            "parameter",
            "parameter_code",
            "date_local",
            "aqi_value",
            "aqi_category",
            "concentration",
            "units",
            "state_code",
            "_source",
        ]
        for col in required:
            assert col in df.columns, f"Missing Bronze column: {col}"

        for col in ["record_id", "site_id", "parameter", "aqi_value", "concentration"]:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Bronze column '{col}' has {null_count} nulls"

        assert len(df) == SAMPLE_SIZE

        # Validate AQI range (0-500)
        assert (df["aqi_value"] >= 0).all() and (df["aqi_value"] <= 500).all()

        # Validate parameter is from known set
        valid_params = {"PM2.5", "PM10", "OZONE", "CO", "SO2", "NO2", "LEAD"}
        assert set(df["parameter"].unique()).issubset(valid_params)

        # Validate AQI category is from known set
        valid_categories = {
            "GOOD",
            "MODERATE",
            "UNHEALTHY_SENSITIVE",
            "UNHEALTHY",
            "VERY_UNHEALTHY",
            "HAZARDOUS",
        }
        assert set(df["aqi_category"].unique()).issubset(valid_categories)

    def test_bronze_to_silver_transformations(self):
        """Silver layer rules produce valid cleansed data."""
        bronze = _bronze_ingest(self.records)

        # Dedup by record_id
        silver, dupes = _silver_dedup(bronze, "record_id")
        assert len(silver) + len(dupes) == len(bronze)

        # Validate concentration >= 0
        conc_valid, _conc_invalid = _silver_validate_range(
            silver, "concentration", 0.0, float("inf")
        )
        assert len(conc_valid) == len(silver), (
            "All concentrations should be non-negative"
        )

        # Validate AQI category matches AQI value
        for _, row in silver.iterrows():
            aqi = row["aqi_value"]
            cat = row["aqi_category"]
            if aqi <= 50:
                assert cat == "GOOD", f"AQI {aqi} should be GOOD, got {cat}"
            elif aqi <= 100:
                assert cat == "MODERATE", f"AQI {aqi} should be MODERATE, got {cat}"
            elif aqi <= 150:
                assert cat == "UNHEALTHY_SENSITIVE", f"AQI {aqi} mismatch: {cat}"
            elif aqi <= 200:
                assert cat == "UNHEALTHY", f"AQI {aqi} mismatch: {cat}"
            elif aqi <= 300:
                assert cat == "VERY_UNHEALTHY", f"AQI {aqi} mismatch: {cat}"
            else:
                assert cat == "HAZARDOUS", f"AQI {aqi} mismatch: {cat}"

        # Compute DQ score
        silver = _silver_compute_dq_score(
            silver,
            [
                "record_id",
                "site_id",
                "parameter",
                "concentration",
                "sample_duration",
                "county_name",
            ],
        )
        # sample_duration and county_name can be null, so DQ may be < 1.0
        assert silver["_dq_score"].min() >= 0.5

    def test_silver_to_gold_aggregations(self):
        """Gold layer aggregations produce valid KPIs."""
        bronze = _bronze_ingest(self.records)
        silver, _ = _silver_dedup(bronze, "record_id")

        # Gold KPI: average AQI per parameter
        gold = _gold_aggregate(silver, "parameter", "aqi_value", "mean")
        if not gold.empty:
            assert "aqi_value_mean" in gold.columns
            assert (gold["record_count"] > 0).all()
            assert gold["parameter"].is_unique
            # Average AQI should be within valid range
            assert (gold["aqi_value_mean"] >= 0).all()
            assert (gold["aqi_value_mean"] <= 500).all()

        # Gold KPI: max concentration per state
        gold_state = _gold_aggregate(silver, "state_code", "concentration", "max")
        if not gold_state.empty:
            assert gold_state["state_code"].is_unique

    def test_full_pipeline_data_lineage(self):
        """Record counts are consistent across layers."""
        bronze = _bronze_ingest(self.records)
        assert len(bronze) == SAMPLE_SIZE

        silver, dupes = _silver_dedup(bronze, "record_id")
        silver_valid, silver_rejects = _silver_validate_not_null(
            silver, ["record_id", "site_id", "parameter", "concentration"]
        )
        assert len(silver) <= len(bronze)
        assert len(silver) + len(dupes) == len(bronze)
        assert len(silver_valid) + len(silver_rejects) == len(silver)

        gold = _gold_aggregate(silver_valid, "parameter", "aqi_value", "mean")
        if not gold.empty:
            assert len(gold) <= len(silver_valid)


# ===========================================================================
# 6. DOI Integration Pipeline
# ===========================================================================


class TestDOIIntegrationPipeline:
    """End-to-end validation: DOI generator -> Bronze schema -> Silver rules -> Gold KPIs."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.gen = DOIGenerator(seed=SEED, start_date=START_DATE, end_date=END_DATE)
        self.records = [
            self.gen.generate_record(domain="earthquake") for _ in range(SAMPLE_SIZE)
        ]

    def test_generator_produces_valid_bronze_data(self):
        """Generator output matches Bronze layer expected schema."""
        df = _bronze_ingest(self.records)

        required = [
            "event_id",
            "time",
            "latitude",
            "longitude",
            "depth_km",
            "magnitude",
            "mag_type",
            "place",
            "event_type",
            "status",
            "significance",
            "_source",
        ]
        for col in required:
            assert col in df.columns, f"Missing Bronze column: {col}"

        for col in ["event_id", "magnitude", "latitude", "longitude", "depth_km"]:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Bronze column '{col}' has {null_count} nulls"

        assert len(df) == SAMPLE_SIZE

        # Validate magnitude range (Gutenberg-Richter: 1.0 to 9.5)
        assert (df["magnitude"] >= 1.0).all() and (df["magnitude"] <= 9.5).all()

        # Validate depth is non-negative
        assert (df["depth_km"] >= 0).all()

        # Validate latitude/longitude
        assert (df["latitude"] >= -90).all() and (df["latitude"] <= 90).all()
        assert (df["longitude"] >= -180).all() and (df["longitude"] <= 180).all()

        # Validate event_type
        valid_types = {
            "EARTHQUAKE",
            "QUARRY_BLAST",
            "EXPLOSION",
            "VOLCANIC_ERUPTION",
            "ICE_QUAKE",
        }
        assert set(df["event_type"].unique()).issubset(valid_types)

    def test_bronze_to_silver_transformations(self):
        """Silver layer rules produce valid cleansed data."""
        bronze = _bronze_ingest(self.records)

        # Dedup by event_id
        silver, dupes = _silver_dedup(bronze, "event_id")
        assert len(silver) + len(dupes) == len(bronze)

        # Validate magnitude range
        mag_valid, _mag_invalid = _silver_validate_range(silver, "magnitude", 0.0, 10.0)
        assert len(mag_valid) == len(silver), "All magnitudes should be 0-10"

        # Validate depth range
        depth_valid, _depth_invalid = _silver_validate_range(
            silver, "depth_km", 0.0, 800.0
        )
        assert len(depth_valid) == len(silver), "All depths should be 0-800 km"

        # Validate significance is within 0-1000
        sig_valid, _ = _silver_validate_range(silver, "significance", 0, 1000)
        assert len(sig_valid) == len(silver)

        # Compute DQ score
        silver = _silver_compute_dq_score(
            silver,
            [
                "event_id",
                "magnitude",
                "depth_km",
                "latitude",
                "longitude",
                "felt",
                "mmi",
                "alert",
            ],
        )
        # felt, mmi, alert are often null for small earthquakes
        assert silver["_dq_score"].min() >= 0.4

    def test_silver_to_gold_aggregations(self):
        """Gold layer aggregations produce valid KPIs."""
        bronze = _bronze_ingest(self.records)
        silver, _ = _silver_dedup(bronze, "event_id")

        # Gold KPI: average magnitude per event_type
        gold = _gold_aggregate(silver, "event_type", "magnitude", "mean")
        if not gold.empty:
            assert "magnitude_mean" in gold.columns
            assert (gold["record_count"] > 0).all()
            assert gold["event_type"].is_unique
            # Average magnitude should be within valid range
            assert (gold["magnitude_mean"] >= 1.0).all()
            assert (gold["magnitude_mean"] <= 9.5).all()

        # Gold KPI: count by status
        gold_status = _gold_aggregate(silver, "status", "magnitude", "count")
        if not gold_status.empty:
            assert gold_status["status"].is_unique

    def test_full_pipeline_data_lineage(self):
        """Record counts are consistent across layers."""
        bronze = _bronze_ingest(self.records)
        assert len(bronze) == SAMPLE_SIZE

        silver, dupes = _silver_dedup(bronze, "event_id")
        silver_valid, silver_rejects = _silver_validate_not_null(
            silver, ["event_id", "magnitude", "latitude", "longitude"]
        )
        assert len(silver) <= len(bronze)
        assert len(silver) + len(dupes) == len(bronze)
        assert len(silver_valid) + len(silver_rejects) == len(silver)

        gold = _gold_aggregate(silver_valid, "event_type", "magnitude", "mean")
        if not gold.empty:
            assert len(gold) <= len(silver_valid)


# ===========================================================================
# 7. Tribal Healthcare Integration Pipeline
# ===========================================================================


class TestTribalHealthIntegrationPipeline:
    """End-to-end validation: Tribal Healthcare generator -> Bronze schema -> Silver rules -> Gold KPIs."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.gen = TribalHealthcareGenerator(
            seed=SEED, start_date=START_DATE, end_date=END_DATE
        )
        self.records = [self.gen.generate_record() for _ in range(SAMPLE_SIZE)]

    def test_generator_produces_valid_bronze_data(self):
        """Generator output matches Bronze layer expected schema."""
        df = _bronze_ingest(self.records)

        required = [
            "record_id",
            "patient_id",
            "facility_id",
            "facility_name",
            "encounter_type",
            "encounter_date",
            "icd10_code",
            "icd10_description",
            "tribal_affiliation",
            "service_unit",
            "area_office",
            "age_group",
            "gender",
            "insurance_type",
            "hipaa_consent",
            "phi_masked",
            "_source",
        ]
        for col in required:
            assert col in df.columns, f"Missing Bronze column: {col}"

        # Core fields must never be null
        for col in [
            "record_id",
            "patient_id",
            "facility_id",
            "encounter_type",
            "icd10_code",
            "tribal_affiliation",
        ]:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Bronze column '{col}' has {null_count} nulls"

        assert len(df) == SAMPLE_SIZE

        # Validate HIPAA compliance flags
        assert (df["hipaa_consent"] == True).all(), (
            "All records must have HIPAA consent"
        )
        assert (df["phi_masked"] == True).all(), "All records must have PHI masked"

        # Validate encounter_type from known set
        valid_encounter_types = {
            "outpatient",
            "inpatient",
            "emergency",
            "telehealth",
            "dental",
            "behavioral_health",
            "pharmacy",
            "laboratory",
        }
        assert set(df["encounter_type"].unique()).issubset(valid_encounter_types)

        # Validate gender
        valid_genders = {"M", "F", "X"}
        assert set(df["gender"].unique()).issubset(valid_genders)

        # Validate age_group
        valid_age_groups = {"0-4", "5-14", "15-24", "25-44", "45-64", "65+"}
        assert set(df["age_group"].unique()).issubset(valid_age_groups)

    def test_bronze_to_silver_transformations(self):
        """Silver layer rules produce valid cleansed data."""
        bronze = _bronze_ingest(self.records)

        # Dedup by record_id
        silver, dupes = _silver_dedup(bronze, "record_id")
        assert len(silver) + len(dupes) == len(bronze)

        # Validate ICD-10 code format (letter followed by digits and optional dot)
        icd10_pattern = silver["icd10_code"].str.match(r"^[A-Z]\d{2}")
        assert icd10_pattern.all(), (
            "All ICD-10 codes should start with letter + 2 digits"
        )

        # Validate facility_id format
        assert silver["facility_id"].str.startswith("IHS-").all(), (
            "All facility IDs start with IHS-"
        )

        # Validate lab results when present
        lab_records = silver[silver["lab_test_name"].notnull()]
        if len(lab_records) > 0:
            assert (lab_records["lab_result_value"].notnull()).all(), (
                "Lab records must have result values"
            )
            assert (lab_records["lab_result_unit"].notnull()).all(), (
                "Lab records must have result units"
            )
            # Validate abnormal flags are from known set
            valid_flags = {"N", "L", "H", "LL", "HH"}
            actual_flags = set(lab_records["lab_abnormal_flag"].dropna().unique())
            assert actual_flags.issubset(valid_flags), (
                f"Invalid lab flags: {actual_flags - valid_flags}"
            )

        # Compute DQ score
        silver = _silver_compute_dq_score(
            silver,
            [
                "record_id",
                "patient_id",
                "encounter_type",
                "icd10_code",
                "cpt_code",
                "provider_id",
                "medication_name",
                "lab_test_name",
            ],
        )
        # cpt_code, provider_id, medication_name, lab_test_name can be null
        assert silver["_dq_score"].min() >= 0.3

    def test_silver_to_gold_aggregations(self):
        """Gold layer aggregations produce valid KPIs."""
        bronze = _bronze_ingest(self.records)
        silver, _ = _silver_dedup(bronze, "record_id")

        # Gold KPI: encounter count by tribal_affiliation
        # Use a numeric proxy: create a count column
        silver_for_gold = silver.copy()
        silver_for_gold["encounter_count"] = 1
        gold = _gold_aggregate(
            silver_for_gold, "tribal_affiliation", "encounter_count", "sum"
        )
        if not gold.empty:
            assert "encounter_count_sum" in gold.columns
            assert (gold["record_count"] > 0).all()
            assert gold["tribal_affiliation"].is_unique

        # Gold KPI: encounter count by encounter_type
        gold_type = _gold_aggregate(
            silver_for_gold, "encounter_type", "encounter_count", "sum"
        )
        if not gold_type.empty:
            assert gold_type["encounter_type"].is_unique

        # Gold KPI: count by area_office
        gold_area = _gold_aggregate(
            silver_for_gold, "area_office", "encounter_count", "sum"
        )
        if not gold_area.empty:
            assert gold_area["area_office"].is_unique

    def test_full_pipeline_data_lineage(self):
        """Record counts are consistent across layers."""
        bronze = _bronze_ingest(self.records)
        assert len(bronze) == SAMPLE_SIZE

        silver, dupes = _silver_dedup(bronze, "record_id")
        silver_valid, silver_rejects = _silver_validate_not_null(
            silver, ["record_id", "patient_id", "encounter_type", "icd10_code"]
        )
        assert len(silver) <= len(bronze)
        assert len(silver) + len(dupes) == len(bronze)
        assert len(silver_valid) + len(silver_rejects) == len(silver)

        silver_for_gold = silver_valid.copy()
        silver_for_gold["encounter_count"] = 1
        gold = _gold_aggregate(
            silver_for_gold, "encounter_type", "encounter_count", "sum"
        )
        if not gold.empty:
            assert len(gold) <= len(silver_valid)


# ===========================================================================
# 8. DOT/FAA Integration Pipeline
# ===========================================================================


class TestDotFaaIntegrationPipeline:
    """End-to-end validation: DOT/FAA generator -> Bronze schema -> Silver rules -> Gold KPIs."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.gen = DOTFAAGenerator(seed=SEED, start_date=START_DATE, end_date=END_DATE)
        self.records = [
            self.gen.generate_record(domain="flight_operations")
            for _ in range(SAMPLE_SIZE)
        ]

    def test_generator_produces_valid_bronze_data(self):
        """Generator output matches Bronze layer expected schema."""
        df = _bronze_ingest(self.records)

        required = [
            "record_id",
            "data_domain",
            "carrier_code",
            "carrier_name",
            "origin_airport",
            "destination_airport",
            "departure_date",
            "flight_number",
            "aircraft_type",
            "tail_number",
            "_source",
        ]
        for col in required:
            assert col in df.columns, f"Missing Bronze column: {col}"

        # Core fields must not be null
        for col in [
            "record_id",
            "carrier_code",
            "origin_airport",
            "destination_airport",
            "departure_date",
            "data_domain",
        ]:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Bronze column '{col}' has {null_count} nulls"

        assert len(df) == SAMPLE_SIZE

        # All records should be flight_operations domain
        assert (df["data_domain"] == "flight_operations").all()

        # Validate carrier codes are from known set
        valid_carriers = {
            "AA",
            "DL",
            "UA",
            "WN",
            "B6",
            "AS",
            "NK",
            "F9",
            "HA",
            "G4",
            "SY",
            "MX",
            "QX",
            "OH",
            "OO",
            "YX",
            "9E",
            "MQ",
            "YV",
            "CP",
        }
        assert set(df["carrier_code"].unique()).issubset(valid_carriers)

        # Validate airport codes are from known set
        valid_airports = {
            "ATL",
            "ORD",
            "DFW",
            "DEN",
            "LAX",
            "JFK",
            "SFO",
            "SEA",
            "MCO",
            "MIA",
            "LAS",
            "PHX",
            "IAH",
            "CLT",
            "EWR",
            "MSP",
            "DTW",
            "BOS",
            "PHL",
            "LGA",
            "FLL",
            "BWI",
            "DCA",
            "SAN",
            "TPA",
            "PDX",
            "SLC",
            "STL",
            "BNA",
            "AUS",
        }
        assert set(df["origin_airport"].unique()).issubset(valid_airports)
        assert set(df["destination_airport"].unique()).issubset(valid_airports)

        # Origin and destination should be different
        assert (df["origin_airport"] != df["destination_airport"]).all()

    def test_bronze_to_silver_transformations(self):
        """Silver layer rules produce valid cleansed data."""
        bronze = _bronze_ingest(self.records)

        # Dedup by record_id
        silver, dupes = _silver_dedup(bronze, "record_id")
        assert len(silver) + len(dupes) == len(bronze)

        # Validate delay_minutes: non-negative for non-cancelled flights
        non_cancelled = silver[silver["cancelled"] == False]
        if len(non_cancelled) > 0:
            delays = pd.to_numeric(non_cancelled["delay_minutes"], errors="coerce")
            valid_delays = delays.dropna()
            assert (valid_delays >= 0).all(), "Delay minutes must be non-negative"

        # Validate delay_cause is from known set
        valid_causes = {
            "none",
            "carrier",
            "weather",
            "nas",
            "security",
            "late_aircraft",
        }
        non_null_causes = silver["delay_cause"].dropna()
        if len(non_null_causes) > 0:
            assert set(non_null_causes.unique()).issubset(valid_causes)

        # Validate passengers > 0 for non-cancelled
        if len(non_cancelled) > 0:
            pax = pd.to_numeric(non_cancelled["passengers"], errors="coerce").dropna()
            assert (pax > 0).all(), "Passenger count should be positive"

        # Compute DQ score
        silver = _silver_compute_dq_score(
            silver,
            [
                "record_id",
                "carrier_code",
                "origin_airport",
                "destination_airport",
                "scheduled_departure",
                "actual_departure",
                "delay_minutes",
                "aircraft_type",
                "passengers",
            ],
        )
        # actual_departure and delay_minutes are null for cancelled flights
        assert silver["_dq_score"].min() >= 0.5

        # Validate tail number format (N + digits)
        tail_nums = silver["tail_number"].dropna()
        if len(tail_nums) > 0:
            assert tail_nums.str.startswith("N").all(), "US tail numbers start with N"

    def test_silver_to_gold_aggregations(self):
        """Gold layer aggregations produce valid KPIs."""
        bronze = _bronze_ingest(self.records)
        silver, _ = _silver_dedup(bronze, "record_id")

        # Gold KPI: average delay per carrier
        # Filter to non-cancelled with valid delay
        non_cancelled = silver[silver["cancelled"] == False].copy()
        non_cancelled["delay_minutes"] = pd.to_numeric(
            non_cancelled["delay_minutes"], errors="coerce"
        )
        gold = _gold_aggregate(non_cancelled, "carrier_code", "delay_minutes", "mean")
        if not gold.empty:
            assert "delay_minutes_mean" in gold.columns
            assert (gold["record_count"] > 0).all()
            assert gold["carrier_code"].is_unique
            # Average delay should be non-negative
            assert (gold["delay_minutes_mean"] >= 0).all()

        # Gold KPI: total passengers per origin airport
        silver_pax = silver.copy()
        silver_pax["passengers"] = pd.to_numeric(
            silver_pax["passengers"], errors="coerce"
        )
        gold_airport = _gold_aggregate(
            silver_pax, "origin_airport", "passengers", "sum"
        )
        if not gold_airport.empty:
            assert gold_airport["origin_airport"].is_unique

        # Gold KPI: cancellation rate per carrier
        silver_for_cancel = silver.copy()
        silver_for_cancel["_cancelled_int"] = silver_for_cancel["cancelled"].apply(
            lambda x: 1 if x is True else 0
        )
        gold_cancel = _gold_aggregate(
            silver_for_cancel, "carrier_code", "_cancelled_int", "mean"
        )
        if not gold_cancel.empty:
            # Cancellation rate should be between 0 and 1
            assert (gold_cancel["_cancelled_int_mean"] >= 0).all()
            assert (gold_cancel["_cancelled_int_mean"] <= 1).all()

    def test_full_pipeline_data_lineage(self):
        """Record counts are consistent across layers."""
        bronze = _bronze_ingest(self.records)
        assert len(bronze) == SAMPLE_SIZE

        silver, dupes = _silver_dedup(bronze, "record_id")
        silver_valid, silver_rejects = _silver_validate_not_null(
            silver,
            ["record_id", "carrier_code", "origin_airport", "destination_airport"],
        )
        assert len(silver) <= len(bronze)
        assert len(silver) + len(dupes) == len(bronze)
        assert len(silver_valid) + len(silver_rejects) == len(silver)

        # Gold aggregation produces fewer rows than Silver
        silver_pax = silver_valid.copy()
        silver_pax["passengers"] = pd.to_numeric(
            silver_pax["passengers"], errors="coerce"
        )
        gold = _gold_aggregate(silver_pax, "carrier_code", "passengers", "sum")
        if not gold.empty:
            assert len(gold) <= len(silver_valid)
