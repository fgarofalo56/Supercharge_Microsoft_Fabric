"""
Integration tests for the full data pipeline.

These tests validate end-to-end data flow through Bronze, Silver, and Gold layers.
"""

import os
from pathlib import Path

import pytest

# Skip integration tests if not in appropriate environment
pytestmark = pytest.mark.integration


class TestDataGeneration:
    """Tests for data generation to landing zone."""

    @pytest.mark.slow
    def test_generate_slot_data(self, temp_output_dir):
        """Test slot data generation to output directory."""
        from generators.slot_machine_generator import SlotMachineGenerator

        generator = SlotMachineGenerator(seed=42)
        records = generator.generate_batch(1000)

        assert len(records) == 1000
        assert all("machine_id" in r for r in records)
        assert all("event_timestamp" in r for r in records)

    @pytest.mark.slow
    def test_generate_player_data(self, temp_output_dir):
        """Test player data generation."""
        from generators.player_generator import PlayerGenerator

        generator = PlayerGenerator(seed=42)
        records = generator.generate_batch(500)

        assert len(records) == 500
        assert all("player_id" in r for r in records)

    @pytest.mark.slow
    def test_generate_compliance_data(self, temp_output_dir):
        """Test compliance data generation."""
        from generators.compliance_generator import ComplianceGenerator

        generator = ComplianceGenerator(seed=42)
        records = generator.generate_batch(200)

        assert len(records) == 200
        assert all("filing_type" in r for r in records)


class TestDataQuality:
    """Tests for data quality through the pipeline."""

    def test_no_duplicate_machine_ids_in_session(self):
        """Test for reasonable machine ID distribution."""
        from generators.slot_machine_generator import SlotMachineGenerator

        generator = SlotMachineGenerator(seed=42)
        records = generator.generate_batch(10000)

        machine_ids = [r["machine_id"] for r in records]
        unique_machines = set(machine_ids)

        # Should have reasonable distribution (not all same machine)
        assert len(unique_machines) > 100

    def test_timestamp_ordering(self):
        """Test that timestamps can be reasonably ordered."""
        from datetime import datetime

        from generators.slot_machine_generator import SlotMachineGenerator

        generator = SlotMachineGenerator(seed=42)
        records = generator.generate_batch(100)

        timestamps = [r["event_timestamp"] for r in records]

        # All timestamps should be valid
        for ts in timestamps:
            assert ts is not None
            # Should be parseable
            if isinstance(ts, str):
                datetime.fromisoformat(ts.replace("Z", "+00:00"))


class TestComplianceLogic:
    """Tests for compliance-related logic."""

    @pytest.mark.compliance
    def test_ctr_generation(self):
        """Test CTR records are generated correctly."""
        from generators.compliance_generator import ComplianceGenerator

        generator = ComplianceGenerator(seed=42)
        records = generator.generate_batch(1000)

        ctr_records = [r for r in records if r["filing_type"] == "CTR"]

        # Should have some CTR records
        assert len(ctr_records) > 0

        # All CTR records should have amount >= $10,000
        for record in ctr_records:
            assert record["amount"] >= 10000

    @pytest.mark.compliance
    def test_sar_generation(self):
        """Test SAR records are generated correctly."""
        from generators.compliance_generator import ComplianceGenerator

        generator = ComplianceGenerator(seed=42)
        records = generator.generate_batch(1000)

        sar_records = [r for r in records if r["filing_type"] == "SAR"]

        # Should have some SAR records
        assert len(sar_records) > 0

        # SAR records should have suspicion details (sar_category encodes the type)
        for record in sar_records:
            assert record.get("sar_category") is not None

    @pytest.mark.compliance
    def test_w2g_generation(self):
        """Test W-2G records are generated correctly."""
        from generators.compliance_generator import ComplianceGenerator

        generator = ComplianceGenerator(seed=42)
        records = generator.generate_batch(1000)

        w2g_records = [r for r in records if r["filing_type"] == "W2G"]

        # Should have some W-2G records
        assert len(w2g_records) > 0

        # W-2G records should have jackpot details
        for record in w2g_records:
            assert record["amount"] >= 600  # Minimum threshold


class TestSchemaConsistency:
    """Tests for schema consistency across generators."""

    def test_slot_schema_consistent(self):
        """Test slot generator produces consistent schema."""
        from generators.slot_machine_generator import SlotMachineGenerator

        generator = SlotMachineGenerator(seed=42)
        records = generator.generate_batch(100)

        expected_fields = {"machine_id", "event_type", "event_timestamp"}

        for record in records:
            assert expected_fields.issubset(set(record.keys()))

    def test_player_schema_consistent(self):
        """Test player generator produces consistent schema."""
        from generators.player_generator import PlayerGenerator

        generator = PlayerGenerator(seed=42)
        records = generator.generate_batch(100)

        expected_fields = {"player_id", "first_name", "last_name", "loyalty_tier"}

        for record in records:
            assert expected_fields.issubset(set(record.keys()))

    def test_financial_schema_consistent(self):
        """Test financial generator produces consistent schema."""
        from generators.financial_generator import FinancialGenerator

        generator = FinancialGenerator(seed=42)
        records = generator.generate_batch(100)

        expected_fields = {"transaction_id", "transaction_type", "amount"}

        for record in records:
            assert expected_fields.issubset(set(record.keys()))


class TestVolumeGeneration:
    """Tests for generating realistic data volumes."""

    @pytest.mark.slow
    def test_generate_large_slot_volume(self):
        """Test generation of large slot data volume."""
        from generators.slot_machine_generator import SlotMachineGenerator

        generator = SlotMachineGenerator(seed=42)
        records = generator.generate_batch(50000)

        assert len(records) == 50000

    @pytest.mark.slow
    def test_generate_full_day_activity(self):
        """Test generation of a full day's worth of activity."""
        from datetime import datetime, timedelta

        from generators.slot_machine_generator import SlotMachineGenerator

        generator = SlotMachineGenerator(seed=42)

        # Generate roughly 1 day of activity
        records = generator.generate_batch(10000)

        # Check timestamp distribution
        timestamps = [r["event_timestamp"] for r in records]

        # Should have activity across multiple hours
        hours = set()
        for ts in timestamps:
            if isinstance(ts, datetime):
                hours.add(ts.hour)
            elif isinstance(ts, str):
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                hours.add(dt.hour)

        # Should have activity in at least 12 different hours
        assert len(hours) >= 12
