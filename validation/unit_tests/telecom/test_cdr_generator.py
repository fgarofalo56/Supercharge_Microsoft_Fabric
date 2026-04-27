"""
Unit tests for the Telecom CDR Generator.
"""

import sys
from pathlib import Path

import pytest

# Ensure repo root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from data_generation.generators.telecom.cdr_generator import TelecomCDRGenerator


# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------

@pytest.fixture
def generator():
    """Create a seeded TelecomCDRGenerator."""
    return TelecomCDRGenerator(seed=42, num_subscribers=50, num_cell_sites=20)


@pytest.fixture
def sample_size():
    return 200


@pytest.fixture
def sample_records(generator, sample_size):
    """Generate a batch of records for statistical tests."""
    return generator.generate(sample_size, show_progress=False).to_dict("records")


# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------

class TestGenerateCDRs:
    """Test CDR record generation."""

    def test_generate_cdrs(self, generator):
        """Test that generate produces the requested number of records."""
        df = generator.generate(100, show_progress=False)
        assert len(df) == 100

    def test_required_fields_present(self, generator):
        """Test that all required fields are in each record."""
        record = generator.generate_record()
        required = [
            "cdr_id", "subscriber_id", "call_type", "start_dt",
            "duration_sec", "bytes_up", "bytes_down", "cell_id",
            "sector", "rat_type", "rated_amount",
        ]
        for field in required:
            assert field in record, f"Missing field: {field}"

    def test_metadata_columns(self, generator):
        """Test that metadata columns are added."""
        record = generator.generate_record()
        assert "_ingested_at" in record
        assert "_source" in record
        assert "_batch_id" in record


class TestDurationPositive:
    """Test that voice/data durations are positive."""

    def test_duration_positive(self, sample_records):
        """Voice and data records must have duration > 0."""
        for r in sample_records:
            if r["call_type"] in ("voice", "data"):
                assert r["duration_sec"] > 0, (
                    f"{r['call_type']} record has duration={r['duration_sec']}"
                )

    def test_sms_duration_zero(self, sample_records):
        """SMS records must have duration == 0."""
        sms_records = [r for r in sample_records if r["call_type"] == "sms"]
        for r in sms_records:
            assert r["duration_sec"] == 0


class TestCallTypes:
    """Test call type distribution."""

    def test_call_types(self, sample_records):
        """All call types must be one of voice, sms, data."""
        valid = {"voice", "sms", "data"}
        for r in sample_records:
            assert r["call_type"] in valid, f"Invalid call type: {r['call_type']}"

    def test_call_type_distribution(self, sample_records):
        """Data should be the most common call type (~60%)."""
        counts = {}
        for r in sample_records:
            counts[r["call_type"]] = counts.get(r["call_type"], 0) + 1
        # Data should be most frequent
        assert counts.get("data", 0) > counts.get("voice", 0)
        assert counts.get("data", 0) > counts.get("sms", 0)


class TestChurnRate:
    """Test subscriber churn rate."""

    def test_churn_rate(self, generator):
        """Churn rate should be approximately 3% (within tolerance)."""
        churned = sum(1 for s in generator.subscribers if s["churn_flag"])
        total = len(generator.subscribers)
        rate = churned / total
        # Allow wide tolerance for small sample (50 subscribers)
        assert 0.0 <= rate <= 0.20, f"Churn rate {rate:.2%} outside expected range"

    def test_churn_flag_is_boolean(self, generator):
        """Churn flag must be a boolean."""
        for s in generator.subscribers:
            assert isinstance(s["churn_flag"], bool)


class TestCellIdFormat:
    """Test cell site ID format."""

    def test_cell_id_format(self, sample_records):
        """Cell IDs must follow CELL-XXXXX format."""
        for r in sample_records:
            assert r["cell_id"].startswith("CELL-"), f"Bad cell_id: {r['cell_id']}"
            suffix = r["cell_id"].split("-")[1]
            assert len(suffix) == 5 and suffix.isdigit()

    def test_sector_values(self, sample_records):
        """Sectors must be A, B, or C."""
        for r in sample_records:
            assert r["sector"] in ("A", "B", "C"), f"Bad sector: {r['sector']}"


class TestReproducibility:
    """Test that seeded generation is deterministic."""

    def test_reproducibility(self):
        """Two generators with the same seed must produce identical records."""
        gen1 = TelecomCDRGenerator(seed=99, num_subscribers=10, num_cell_sites=5)
        gen2 = TelecomCDRGenerator(seed=99, num_subscribers=10, num_cell_sites=5)

        records1 = gen1.generate(20, show_progress=False).to_dict("records")
        records2 = gen2.generate(20, show_progress=False).to_dict("records")

        for r1, r2 in zip(records1, records2):
            assert r1["cdr_id"] == r2["cdr_id"]
            assert r1["subscriber_id"] == r2["subscriber_id"]
            assert r1["call_type"] == r2["call_type"]
            assert r1["duration_sec"] == r2["duration_sec"]
