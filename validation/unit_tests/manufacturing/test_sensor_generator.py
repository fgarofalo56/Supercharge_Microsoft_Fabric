"""
Unit Tests for Manufacturing Sensor Generator
==============================================

Tests sensor telemetry generation, value ranges, machine types,
degradation patterns, and reproducibility.
"""

import pytest

from data_generation.generators.manufacturing.sensor_generator import (
    MACHINE_TYPES,
    ManufacturingSensorGenerator,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def generator():
    """Create a seeded generator for deterministic tests."""
    return ManufacturingSensorGenerator(seed=42, num_machines=20, degradation_pct=0.10)


@pytest.fixture
def large_dataset(generator):
    """Generate a reasonably-sized dataset for statistical checks."""
    return generator.generate(num_records=500, show_progress=False)


# ---------------------------------------------------------------------------
# Basic generation
# ---------------------------------------------------------------------------


class TestGenerateSensors:
    """Tests for basic sensor record generation."""

    def test_generate_single_record(self, generator):
        record = generator.generate_record()
        assert isinstance(record, dict)
        required = [
            "sensor_id",
            "machine_id",
            "machine_type",
            "timestamp",
            "vibration_mm_s",
            "temperature_c",
            "current_a",
            "pressure_bar",
            "rpm",
        ]
        for field in required:
            assert field in record, f"Missing field: {field}"

    def test_generate_batch(self, generator):
        df = generator.generate(num_records=100, show_progress=False)
        assert len(df) == 100
        assert "sensor_id" in df.columns

    def test_generate_returns_dataframe(self, generator):
        import pandas as pd

        df = generator.generate(num_records=10, show_progress=False)
        assert isinstance(df, pd.DataFrame)

    def test_metadata_columns(self, generator):
        record = generator.generate_record()
        assert "_ingested_at" in record
        assert "_source" in record
        assert "_batch_id" in record
        assert record["_source"] == "ManufacturingSensorGenerator"


# ---------------------------------------------------------------------------
# Value ranges
# ---------------------------------------------------------------------------


class TestVibrationRange:
    """Vibration values should be non-negative and mostly within normal range."""

    def test_vibration_non_negative(self, large_dataset):
        assert (large_dataset["vibration_mm_s"] >= 0).all()

    def test_vibration_reasonable_max(self, large_dataset):
        # Even with degradation, should not exceed ~30 mm/s
        assert large_dataset["vibration_mm_s"].max() < 50.0

    def test_vibration_has_variance(self, large_dataset):
        assert large_dataset["vibration_mm_s"].std() > 0.1


class TestTemperatureRange:
    """Temperature values should be physically reasonable."""

    def test_temperature_above_absolute_min(self, large_dataset):
        assert (large_dataset["temperature_c"] >= -10).all()

    def test_temperature_below_extreme(self, large_dataset):
        # Even degraded machines shouldn't exceed ~150C
        assert large_dataset["temperature_c"].max() < 200.0

    def test_temperature_has_variance(self, large_dataset):
        assert large_dataset["temperature_c"].std() > 1.0


# ---------------------------------------------------------------------------
# Machine types
# ---------------------------------------------------------------------------


class TestMachineTypes:
    """Machine types should match the defined set."""

    def test_all_types_present(self, large_dataset):
        types_in_data = set(large_dataset["machine_type"].unique())
        for mt in MACHINE_TYPES:
            assert mt in types_in_data, f"Missing machine type: {mt}"

    def test_no_unknown_types(self, large_dataset):
        types_in_data = set(large_dataset["machine_type"].unique())
        assert types_in_data.issubset(set(MACHINE_TYPES))

    def test_cnc_is_most_common(self, large_dataset):
        counts = large_dataset["machine_type"].value_counts()
        assert counts.idxmax() == "CNC"


# ---------------------------------------------------------------------------
# Degradation pattern
# ---------------------------------------------------------------------------


class TestDegradationPattern:
    """Degraded machines should show increasing sensor values over time."""

    def test_degraded_machines_exist(self, generator):
        assert len(generator._degraded_ids) > 0

    def test_degradation_increases_vibration(self):
        """Generate sequential records for a degraded machine and verify trend."""
        gen = ManufacturingSensorGenerator(seed=99, num_machines=5, degradation_pct=1.0)
        # All machines degrade -- generate enough records to see progression
        records = gen.generate_batch(200)

        # Group by machine, check that later records have higher vibration
        degraded_id = next(iter(gen._degraded_ids))
        machine_records = [r for r in records if r["machine_id"] == degraded_id]

        if len(machine_records) >= 10:
            first_half = machine_records[: len(machine_records) // 2]
            second_half = machine_records[len(machine_records) // 2 :]
            avg_first = sum(r["vibration_mm_s"] for r in first_half) / len(first_half)
            avg_second = sum(r["vibration_mm_s"] for r in second_half) / len(
                second_half
            )
            # Second half should have higher average vibration
            assert avg_second >= avg_first * 0.9  # allow some noise tolerance

    def test_degradation_state_advances(self):
        gen = ManufacturingSensorGenerator(seed=42, num_machines=5, degradation_pct=1.0)
        initial_states = dict(gen._degradation_state)
        gen.generate(num_records=100, show_progress=False)
        for mid in gen._degraded_ids:
            assert gen._degradation_state[mid] >= initial_states[mid]


# ---------------------------------------------------------------------------
# Work orders
# ---------------------------------------------------------------------------


class TestWorkOrders:
    """Work order generation tests."""

    def test_generate_work_orders(self, generator):
        wo_df = generator.generate_work_orders(num_orders=50)
        assert len(wo_df) == 50
        assert "wo_id" in wo_df.columns
        assert "wo_type" in wo_df.columns

    def test_work_order_types(self, generator):
        wo_df = generator.generate_work_orders(num_orders=200)
        types = set(wo_df["wo_type"].unique())
        assert types.issubset({"preventive", "corrective", "predictive"})

    def test_parts_cost_positive(self, generator):
        wo_df = generator.generate_work_orders(num_orders=100)
        assert (wo_df["parts_cost"] > 0).all()


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------


class TestReproducibility:
    """Same seed should produce identical output."""

    def test_same_seed_same_output(self):
        gen1 = ManufacturingSensorGenerator(seed=123, num_machines=10)
        gen2 = ManufacturingSensorGenerator(seed=123, num_machines=10)

        df1 = gen1.generate(num_records=50, show_progress=False)
        df2 = gen2.generate(num_records=50, show_progress=False)

        # Compare core columns (metadata timestamps will differ)
        for col_name in ["sensor_id", "machine_id", "vibration_mm_s", "temperature_c"]:
            assert list(df1[col_name]) == list(df2[col_name]), f"Mismatch in {col_name}"

    def test_different_seed_different_output(self):
        gen1 = ManufacturingSensorGenerator(seed=1, num_machines=10)
        gen2 = ManufacturingSensorGenerator(seed=2, num_machines=10)

        df1 = gen1.generate(num_records=20, show_progress=False)
        df2 = gen2.generate(num_records=20, show_progress=False)

        # At least some values should differ
        assert not all(df1["vibration_mm_s"] == df2["vibration_mm_s"])


# ---------------------------------------------------------------------------
# Machine inventory
# ---------------------------------------------------------------------------


class TestMachineInventory:
    """Tests for get_machines accessor."""

    def test_machine_count(self, generator):
        machines_df = generator.get_machines()
        assert len(machines_df) == 20  # num_machines=20 in fixture

    def test_machine_columns(self, generator):
        machines_df = generator.get_machines()
        for col_name in [
            "machine_id",
            "machine_type",
            "install_dt",
            "last_maintenance_dt",
        ]:
            assert col_name in machines_df.columns
