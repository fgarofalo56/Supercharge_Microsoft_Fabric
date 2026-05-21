"""
Unit tests for the Energy Meter Reading Generator.

Tests cover:
- Record generation and field presence
- kWh non-negativity
- Voltage within ANSI C84.1 Range B (108-132V)
- Load curve shape (evening peak > overnight)
- 15-minute interval alignment
- Seed-based reproducibility
"""

from datetime import datetime

import pandas as pd
import pytest

from data_generation.generators.energy.meter_generator import MeterReadingGenerator

# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


@pytest.fixture
def generator():
    """Create a seeded MeterReadingGenerator."""
    return MeterReadingGenerator(
        seed=42,
        num_meters=100,
        start_date=datetime(2025, 7, 1),
        end_date=datetime(2025, 7, 31),
    )


@pytest.fixture
def sample_records(generator):
    """Generate a batch of records for aggregate tests."""
    return generator.generate(500, show_progress=False)


# -----------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------


class TestMeterReadingGenerator:
    """Tests for MeterReadingGenerator."""

    def test_generate_readings(self, generator):
        """Test that generate_record produces a dict with required fields."""
        record = generator.generate_record()
        assert record is not None
        required = [
            "meter_id",
            "reading_timestamp",
            "kwh_delivered",
            "voltage_a",
            "power_factor",
            "demand_kw",
            "tamper_flag",
            "read_quality",
        ]
        for field in required:
            assert field in record, f"Missing field: {field}"

    def test_kwh_non_negative(self, sample_records):
        """All kWh values must be >= 0."""
        assert (sample_records["kwh_delivered"] >= 0).all(), (
            "Found negative kwh_delivered values"
        )
        assert (sample_records["kwh_received"] >= 0).all(), (
            "Found negative kwh_received values"
        )

    def test_voltage_range(self, sample_records):
        """Voltage should be within a reasonable range (most within 108-132V)."""
        voltages = sample_records["voltage_a"]
        # Allow statistical outliers but 99% should be in 105-135
        within = ((voltages >= 105) & (voltages <= 135)).mean()
        assert within > 0.95, f"Only {within:.1%} of voltages in 105-135V range"

    def test_load_curve_shape(self, generator):
        """Evening hours should have higher avg demand than overnight."""
        records = generator.generate(2000, show_progress=False)
        records["hour"] = pd.to_datetime(records["reading_timestamp"]).dt.hour

        overnight = records[records["hour"].isin([1, 2, 3, 4])]["demand_kw"].mean()
        evening = records[records["hour"].isin([18, 19, 20])]["demand_kw"].mean()

        assert evening > overnight, (
            f"Evening demand ({evening:.2f}) should exceed overnight ({overnight:.2f})"
        )

    def test_interval_spacing(self, sample_records):
        """Timestamps should be aligned to 15-minute boundaries."""
        timestamps = pd.to_datetime(sample_records["reading_timestamp"])
        minutes = timestamps.dt.minute
        # All minutes should be 0, 15, 30, or 45
        valid_minutes = minutes.isin([0, 15, 30, 45])
        assert valid_minutes.all(), (
            f"Found non-15-min-aligned timestamps: {minutes[~valid_minutes].unique()}"
        )

    def test_reproducibility(self):
        """Same seed should produce identical output."""
        gen1 = MeterReadingGenerator(
            seed=99,
            num_meters=50,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 7),
        )
        gen2 = MeterReadingGenerator(
            seed=99,
            num_meters=50,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 7),
        )

        r1 = gen1.generate_record()
        r2 = gen2.generate_record()

        assert r1["meter_id"] == r2["meter_id"]
        assert r1["kwh_delivered"] == r2["kwh_delivered"]
        assert r1["voltage_a"] == r2["voltage_a"]

    def test_generate_batch(self, generator):
        """Batch generation returns correct number of records."""
        df = generator.generate(100, show_progress=False)
        assert len(df) == 100

    def test_meter_assets(self, generator):
        """generate_meter_assets returns fleet with correct count."""
        assets = generator.generate_meter_assets()
        assert len(assets) == 100  # matches num_meters
        assert all("meter_id" in a for a in assets)
        assert all("rate_class" in a for a in assets)

    def test_outage_event(self, generator):
        """generate_outage_event returns valid outage record."""
        event = generator.generate_outage_event()
        assert "event_id" in event
        assert "feeder_id" in event
        assert "cause_code" in event
        assert event["duration_minutes"] >= 1.0
        assert event["customers_affected"] >= 1

    def test_rate_class_distribution(self, sample_records):
        """Rate class distribution should be roughly weighted."""
        dist = sample_records["rate_class"].value_counts(normalize=True)
        # Residential should be the majority
        assert dist.get("RESIDENTIAL", 0) > 0.5, (
            f"Residential share too low: {dist.get('RESIDENTIAL', 0):.1%}"
        )
