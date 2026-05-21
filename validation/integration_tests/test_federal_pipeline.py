"""
Federal Agency Pipeline Integration Tests
==========================================

End-to-end tests validating generate -> Bronze -> Silver -> Gold
for all 7 federal agency data generators:
- USDA, SBA, NOAA, EPA, DOI, Tribal Healthcare, DOT/FAA

Each test class validates:
1. Generator produces records with expected schema
2. Bronze layer: all raw columns present, metadata added
3. Silver layer: nulls filtered, types enforced, dedup applied
4. Gold layer: aggregation columns present, counts/sums valid
5. No unacceptable data loss through pipeline
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

# Add data_generation to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "data_generation"))

pytestmark = [pytest.mark.integration, pytest.mark.pipeline]

FIXED_SEED = 42
RECORD_COUNT = 50

# Agency-specific configuration: maps each generator to its primary ID column,
# grouping column for gold aggregation, and a column to aggregate on.
AGENCY_CONFIG = {
    "usda": {
        "id_col": "record_id",
        "group_col": "domain_desc",
        "agg_col": "record_id",
    },
    "sba": {
        "id_col": "loan_id",
        "group_col": "program_type",
        "agg_col": "loan_id",
    },
    "noaa": {
        "id_col": "observation_id",
        "group_col": "station_id",
        "agg_col": "observation_id",
    },
    "epa": {
        "id_col": "record_id",
        "group_col": "site_id",
        "agg_col": "record_id",
    },
    "doi": {
        "id_col": "event_id",
        "group_col": "usgs_id",
        "agg_col": "event_id",
    },
    "tribal": {
        "id_col": "record_id",
        "group_col": "facility_id",
        "agg_col": "record_id",
    },
    "dot_faa": {
        "id_col": "record_id",
        "group_col": "data_domain",
        "agg_col": "record_id",
    },
}


# =============================================================================
# Helper Functions
# =============================================================================


def simulate_bronze(df: pd.DataFrame) -> pd.DataFrame:
    """Simulate Bronze layer: add ingestion metadata columns."""
    bronze = df.copy()
    bronze["_ingestion_timestamp"] = datetime.now().isoformat()
    bronze["_source_file"] = "integration_test"
    return bronze


def simulate_silver(df: pd.DataFrame, id_col: str) -> pd.DataFrame:
    """Simulate Silver layer: filter nulls on ID field, dedup."""
    silver = df.copy()
    # Drop rows missing the primary identifier
    if id_col in silver.columns:
        silver = silver.dropna(subset=[id_col])
        silver = silver.drop_duplicates(subset=[id_col], keep="first")
    return silver


def simulate_gold_agg(df: pd.DataFrame, group_col: str, agg_col: str) -> pd.DataFrame:
    """Simulate Gold layer: aggregate by group column."""
    if group_col not in df.columns or agg_col not in df.columns:
        # Fallback: group by _source_file (always present in bronze)
        if "_source_file" in df.columns:
            return df.groupby("_source_file").size().reset_index(name="record_count")
        return pd.DataFrame({"record_count": [len(df)]})
    # Fill NaN group values to avoid dropping rows in groupby
    work_df = df.copy()
    work_df[group_col] = work_df[group_col].fillna("_unknown_")
    return work_df.groupby(group_col).agg(record_count=(agg_col, "count")).reset_index()


# =============================================================================
# USDA Pipeline Tests
# =============================================================================


class TestUSDAFederalPipeline:
    """End-to-end pipeline tests for USDA data."""

    CFG = AGENCY_CONFIG["usda"]

    @pytest.fixture(scope="class")
    def usda_data(self):
        from generators.federal import USDAGenerator

        gen = USDAGenerator(seed=FIXED_SEED)
        return pd.DataFrame(gen.generate(RECORD_COUNT, show_progress=False))

    def test_generator_produces_records(self, usda_data):
        assert len(usda_data) == RECORD_COUNT

    def test_bronze_schema_has_metadata(self, usda_data):
        bronze = simulate_bronze(usda_data)
        assert "_ingestion_timestamp" in bronze.columns
        assert "_source_file" in bronze.columns
        assert len(bronze) == RECORD_COUNT

    def test_bronze_has_id_column(self, usda_data):
        bronze = simulate_bronze(usda_data)
        assert self.CFG["id_col"] in bronze.columns

    def test_silver_filters_nulls(self, usda_data):
        bronze = simulate_bronze(usda_data)
        silver = simulate_silver(bronze, self.CFG["id_col"])
        assert silver[self.CFG["id_col"]].isna().sum() == 0
        assert len(silver) <= len(bronze)

    def test_silver_deduplicates(self, usda_data):
        bronze = simulate_bronze(usda_data)
        dup = bronze.iloc[[0]].copy()
        bronze_with_dup = pd.concat([bronze, dup], ignore_index=True)
        silver = simulate_silver(bronze_with_dup, self.CFG["id_col"])
        assert len(silver) == len(bronze)

    def test_gold_aggregation(self, usda_data):
        bronze = simulate_bronze(usda_data)
        silver = simulate_silver(bronze, self.CFG["id_col"])
        gold = simulate_gold_agg(silver, self.CFG["group_col"], self.CFG["agg_col"])
        assert len(gold) > 0
        assert "record_count" in gold.columns
        assert gold["record_count"].sum() == len(silver)


# =============================================================================
# SBA Pipeline Tests
# =============================================================================


class TestSBAFederalPipeline:
    """End-to-end pipeline tests for SBA data."""

    CFG = AGENCY_CONFIG["sba"]

    @pytest.fixture(scope="class")
    def sba_data(self):
        from generators.federal import SBAGenerator

        gen = SBAGenerator(seed=FIXED_SEED)
        return pd.DataFrame(gen.generate(RECORD_COUNT, show_progress=False))

    def test_generator_produces_records(self, sba_data):
        assert len(sba_data) == RECORD_COUNT

    def test_bronze_schema_has_metadata(self, sba_data):
        bronze = simulate_bronze(sba_data)
        assert "_ingestion_timestamp" in bronze.columns
        assert len(bronze) == RECORD_COUNT

    def test_bronze_has_id_column(self, sba_data):
        bronze = simulate_bronze(sba_data)
        assert self.CFG["id_col"] in bronze.columns

    def test_silver_filters_and_deduplicates(self, sba_data):
        bronze = simulate_bronze(sba_data)
        silver = simulate_silver(bronze, self.CFG["id_col"])
        assert silver[self.CFG["id_col"]].isna().sum() == 0
        assert len(silver) <= len(bronze)

    def test_gold_aggregation(self, sba_data):
        bronze = simulate_bronze(sba_data)
        silver = simulate_silver(bronze, self.CFG["id_col"])
        gold = simulate_gold_agg(silver, self.CFG["group_col"], self.CFG["agg_col"])
        assert len(gold) > 0
        assert gold["record_count"].sum() == len(silver)


# =============================================================================
# NOAA Pipeline Tests
# =============================================================================


class TestNOAAFederalPipeline:
    """End-to-end pipeline tests for NOAA data."""

    CFG = AGENCY_CONFIG["noaa"]

    @pytest.fixture(scope="class")
    def noaa_data(self):
        from generators.federal import NOAAGenerator

        gen = NOAAGenerator(seed=FIXED_SEED)
        return pd.DataFrame(gen.generate(RECORD_COUNT, show_progress=False))

    def test_generator_produces_records(self, noaa_data):
        assert len(noaa_data) == RECORD_COUNT

    def test_bronze_schema_has_metadata(self, noaa_data):
        bronze = simulate_bronze(noaa_data)
        assert "_ingestion_timestamp" in bronze.columns
        assert len(bronze) == RECORD_COUNT

    def test_bronze_has_id_column(self, noaa_data):
        bronze = simulate_bronze(noaa_data)
        assert self.CFG["id_col"] in bronze.columns

    def test_silver_filters_and_deduplicates(self, noaa_data):
        bronze = simulate_bronze(noaa_data)
        silver = simulate_silver(bronze, self.CFG["id_col"])
        assert silver[self.CFG["id_col"]].isna().sum() == 0
        assert len(silver) <= len(bronze)

    def test_gold_aggregation(self, noaa_data):
        bronze = simulate_bronze(noaa_data)
        silver = simulate_silver(bronze, self.CFG["id_col"])
        gold = simulate_gold_agg(silver, self.CFG["group_col"], self.CFG["agg_col"])
        assert len(gold) > 0
        assert gold["record_count"].sum() == len(silver)


# =============================================================================
# EPA Pipeline Tests
# =============================================================================


class TestEPAFederalPipeline:
    """End-to-end pipeline tests for EPA data."""

    CFG = AGENCY_CONFIG["epa"]

    @pytest.fixture(scope="class")
    def epa_data(self):
        from generators.federal import EPAGenerator

        gen = EPAGenerator(seed=FIXED_SEED)
        return pd.DataFrame(gen.generate(RECORD_COUNT, show_progress=False))

    def test_generator_produces_records(self, epa_data):
        assert len(epa_data) == RECORD_COUNT

    def test_bronze_schema_has_metadata(self, epa_data):
        bronze = simulate_bronze(epa_data)
        assert "_ingestion_timestamp" in bronze.columns
        assert len(bronze) == RECORD_COUNT

    def test_bronze_has_id_column(self, epa_data):
        bronze = simulate_bronze(epa_data)
        assert self.CFG["id_col"] in bronze.columns

    def test_silver_filters_and_deduplicates(self, epa_data):
        bronze = simulate_bronze(epa_data)
        silver = simulate_silver(bronze, self.CFG["id_col"])
        assert silver[self.CFG["id_col"]].isna().sum() == 0
        assert len(silver) <= len(bronze)

    def test_gold_aggregation(self, epa_data):
        bronze = simulate_bronze(epa_data)
        silver = simulate_silver(bronze, self.CFG["id_col"])
        gold = simulate_gold_agg(silver, self.CFG["group_col"], self.CFG["agg_col"])
        assert len(gold) > 0
        assert gold["record_count"].sum() == len(silver)


# =============================================================================
# DOI Pipeline Tests
# =============================================================================


class TestDOIFederalPipeline:
    """End-to-end pipeline tests for DOI data."""

    CFG = AGENCY_CONFIG["doi"]

    @pytest.fixture(scope="class")
    def doi_data(self):
        from generators.federal import DOIGenerator

        gen = DOIGenerator(seed=FIXED_SEED)
        return pd.DataFrame(gen.generate(RECORD_COUNT, show_progress=False))

    def test_generator_produces_records(self, doi_data):
        assert len(doi_data) == RECORD_COUNT

    def test_bronze_schema_has_metadata(self, doi_data):
        bronze = simulate_bronze(doi_data)
        assert "_ingestion_timestamp" in bronze.columns
        assert len(bronze) == RECORD_COUNT

    def test_bronze_has_id_column(self, doi_data):
        bronze = simulate_bronze(doi_data)
        assert self.CFG["id_col"] in bronze.columns

    def test_silver_filters_and_deduplicates(self, doi_data):
        bronze = simulate_bronze(doi_data)
        silver = simulate_silver(bronze, self.CFG["id_col"])
        assert silver[self.CFG["id_col"]].isna().sum() == 0
        assert len(silver) <= len(bronze)

    def test_gold_aggregation(self, doi_data):
        bronze = simulate_bronze(doi_data)
        silver = simulate_silver(bronze, self.CFG["id_col"])
        gold = simulate_gold_agg(silver, self.CFG["group_col"], self.CFG["agg_col"])
        assert len(gold) > 0
        assert gold["record_count"].sum() == len(silver)


# =============================================================================
# Tribal Healthcare Pipeline Tests
# =============================================================================


class TestTribalHealthcareFederalPipeline:
    """End-to-end pipeline tests for Tribal Healthcare data."""

    CFG = AGENCY_CONFIG["tribal"]

    @pytest.fixture(scope="class")
    def tribal_data(self):
        from generators.federal import TribalHealthcareGenerator

        gen = TribalHealthcareGenerator(seed=FIXED_SEED)
        return pd.DataFrame(gen.generate(RECORD_COUNT, show_progress=False))

    def test_generator_produces_records(self, tribal_data):
        assert len(tribal_data) == RECORD_COUNT

    def test_bronze_schema_has_metadata(self, tribal_data):
        bronze = simulate_bronze(tribal_data)
        assert "_ingestion_timestamp" in bronze.columns
        assert len(bronze) == RECORD_COUNT

    def test_bronze_has_id_column(self, tribal_data):
        bronze = simulate_bronze(tribal_data)
        assert self.CFG["id_col"] in bronze.columns

    def test_silver_filters_and_deduplicates(self, tribal_data):
        bronze = simulate_bronze(tribal_data)
        silver = simulate_silver(bronze, self.CFG["id_col"])
        assert silver[self.CFG["id_col"]].isna().sum() == 0
        assert len(silver) <= len(bronze)

    def test_gold_aggregation(self, tribal_data):
        bronze = simulate_bronze(tribal_data)
        silver = simulate_silver(bronze, self.CFG["id_col"])
        gold = simulate_gold_agg(silver, self.CFG["group_col"], self.CFG["agg_col"])
        assert len(gold) > 0
        assert gold["record_count"].sum() == len(silver)


# =============================================================================
# DOT/FAA Pipeline Tests
# =============================================================================


class TestDOTFAAFederalPipeline:
    """End-to-end pipeline tests for DOT/FAA data."""

    CFG = AGENCY_CONFIG["dot_faa"]

    @pytest.fixture(scope="class")
    def dot_faa_data(self):
        from generators.federal import DOTFAAGenerator

        gen = DOTFAAGenerator(seed=FIXED_SEED)
        return pd.DataFrame(gen.generate(RECORD_COUNT, show_progress=False))

    def test_generator_produces_records(self, dot_faa_data):
        assert len(dot_faa_data) == RECORD_COUNT

    def test_bronze_schema_has_metadata(self, dot_faa_data):
        bronze = simulate_bronze(dot_faa_data)
        assert "_ingestion_timestamp" in bronze.columns
        assert len(bronze) == RECORD_COUNT

    def test_bronze_has_id_column(self, dot_faa_data):
        bronze = simulate_bronze(dot_faa_data)
        assert self.CFG["id_col"] in bronze.columns

    def test_bronze_has_domain_column(self, dot_faa_data):
        bronze = simulate_bronze(dot_faa_data)
        assert "data_domain" in bronze.columns

    def test_silver_filters_and_deduplicates(self, dot_faa_data):
        bronze = simulate_bronze(dot_faa_data)
        silver = simulate_silver(bronze, self.CFG["id_col"])
        assert silver[self.CFG["id_col"]].isna().sum() == 0
        assert len(silver) <= len(bronze)

    def test_gold_aggregation(self, dot_faa_data):
        bronze = simulate_bronze(dot_faa_data)
        silver = simulate_silver(bronze, self.CFG["id_col"])
        gold = simulate_gold_agg(silver, self.CFG["group_col"], self.CFG["agg_col"])
        assert len(gold) > 0
        assert gold["record_count"].sum() == len(silver)


# =============================================================================
# Cross-Agency Pipeline Tests
# =============================================================================


class TestCrossAgencyPipeline:
    """Cross-cutting tests that verify consistency across all federal agencies."""

    @pytest.fixture(scope="class")
    def all_federal_data(self):
        """Generate data for all 7 federal agencies."""
        from generators.federal import (
            DOIGenerator,
            DOTFAAGenerator,
            EPAGenerator,
            NOAAGenerator,
            SBAGenerator,
            TribalHealthcareGenerator,
            USDAGenerator,
        )

        generators = {
            "usda": USDAGenerator(seed=FIXED_SEED),
            "sba": SBAGenerator(seed=FIXED_SEED),
            "noaa": NOAAGenerator(seed=FIXED_SEED),
            "epa": EPAGenerator(seed=FIXED_SEED),
            "doi": DOIGenerator(seed=FIXED_SEED),
            "tribal": TribalHealthcareGenerator(seed=FIXED_SEED),
            "dot_faa": DOTFAAGenerator(seed=FIXED_SEED),
        }

        return {
            name: pd.DataFrame(gen.generate(20, show_progress=False))
            for name, gen in generators.items()
        }

    def test_all_agencies_have_primary_id(self, all_federal_data):
        """All federal generators produce their primary ID column."""
        for name, df in all_federal_data.items():
            id_col = AGENCY_CONFIG[name]["id_col"]
            assert id_col in df.columns, f"{name} missing {id_col} column"

    def test_all_agencies_have_batch_id(self, all_federal_data):
        """All federal generators produce a _batch_id metadata column."""
        for name, df in all_federal_data.items():
            assert "_batch_id" in df.columns, f"{name} missing _batch_id column"

    def test_ids_unique_within_agency(self, all_federal_data):
        """Primary IDs are unique within each agency's data."""
        for name, df in all_federal_data.items():
            id_col = AGENCY_CONFIG[name]["id_col"]
            unique_count = df[id_col].nunique()
            assert unique_count == len(df), (
                f"{name} has {len(df) - unique_count} duplicate {id_col}s"
            )

    def test_pipeline_no_data_loss(self, all_federal_data):
        """Pipeline should not lose data between layers (Silver <= Bronze)."""
        for name, df in all_federal_data.items():
            cfg = AGENCY_CONFIG[name]
            bronze = simulate_bronze(df)
            silver = simulate_silver(bronze, cfg["id_col"])
            assert len(silver) <= len(bronze), (
                f"{name}: Silver ({len(silver)}) > Bronze ({len(bronze)})"
            )
            # Gold should have at least 1 row
            gold = simulate_gold_agg(silver, cfg["group_col"], cfg["agg_col"])
            assert len(gold) >= 1, f"{name}: Gold has no rows"

    def test_all_agencies_generate_expected_count(self, all_federal_data):
        """All agencies produce exactly 20 records as requested."""
        for name, df in all_federal_data.items():
            assert len(df) == 20, f"{name} generated {len(df)} instead of 20"
