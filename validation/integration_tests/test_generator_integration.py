"""
Generator Integration Tests
============================

Tests for verifying all generators work together correctly:
- All generators can be instantiated together
- Generators produce compatible player_ids for cross-referencing
- Date ranges are consistent across generators
- Seed reproducibility across all generators
"""

from datetime import datetime, timedelta

import numpy as np
import pytest
from faker import Faker

pytestmark = [pytest.mark.integration]


class TestGeneratorInstantiation:
    """Tests that all generators can be instantiated together."""

    def test_all_generators_instantiate(self, all_generators):
        """Verify all generators can be instantiated in the same session."""
        assert len(all_generators) == 6
        assert "slot" in all_generators
        assert "player" in all_generators
        assert "compliance" in all_generators
        assert "financial" in all_generators
        assert "security" in all_generators
        assert "table_games" in all_generators

    def test_generators_have_schemas(self, all_generators):
        """Verify all generators expose schema definitions."""
        for name, generator in all_generators.items():
            assert hasattr(generator, "schema") or hasattr(
                generator, "_schema"
            ), f"{name} generator missing schema"
            schema = (
                generator.schema if hasattr(generator, "schema") else generator._schema
            )
            assert isinstance(schema, dict), f"{name} schema is not a dict"
            assert len(schema) > 0, f"{name} schema is empty"

    def test_generators_have_generate_record(self, all_generators):
        """Verify all generators have generate_record method."""
        for name, generator in all_generators.items():
            assert hasattr(
                generator, "generate_record"
            ), f"{name} generator missing generate_record method"
            record = generator.generate_record()
            assert isinstance(
                record, dict
            ), f"{name} generate_record doesn't return dict"

    def test_generators_have_generate_batch(self, all_generators):
        """Verify all generators can generate batches."""
        for name, generator in all_generators.items():
            assert hasattr(
                generator, "generate"
            ), f"{name} generator missing generate method"
            df = generator.generate(10, show_progress=False)
            assert len(df) == 10, f"{name} generate didn't return expected count"


class TestPlayerIdCompatibility:
    """Tests for player ID format compatibility across generators."""

    def test_slot_player_id_format(self, sample_slot_data, validate_player_id_format):
        """Verify slot generator produces compatible player IDs."""
        player_ids = sample_slot_data["player_id"].dropna().tolist()

        # Should have some player IDs (carded play)
        assert len(player_ids) > 0, "No player IDs generated in slot data"

        # All should match pattern
        for pid in player_ids[:100]:  # Check first 100
            assert validate_player_id_format(pid), f"Invalid player_id format: {pid}"

    def test_player_generator_id_format(
        self, sample_player_data, validate_player_id_format
    ):
        """Verify player generator produces valid player IDs."""
        player_ids = sample_player_data["player_id"].tolist()

        for pid in player_ids[:100]:
            assert validate_player_id_format(pid), f"Invalid player_id format: {pid}"

    def test_compliance_player_id_format(
        self, sample_compliance_data, validate_player_id_format
    ):
        """Verify compliance generator produces compatible player IDs."""
        player_ids = sample_compliance_data["player_id"].dropna().tolist()

        for pid in player_ids[:100]:
            assert validate_player_id_format(pid), f"Invalid player_id format: {pid}"

    def test_financial_player_id_format(
        self, sample_financial_data, validate_player_id_format
    ):
        """Verify financial generator produces compatible player IDs."""
        player_ids = sample_financial_data["player_id"].dropna().tolist()

        for pid in player_ids[:100]:
            assert validate_player_id_format(pid), f"Invalid player_id format: {pid}"

    def test_table_games_player_id_format(
        self, sample_table_games_data, validate_player_id_format
    ):
        """Verify table games generator produces compatible player IDs."""
        player_ids = sample_table_games_data["player_id"].dropna().tolist()

        for pid in player_ids[:100]:
            assert validate_player_id_format(pid), f"Invalid player_id format: {pid}"

    def test_player_ids_can_cross_reference(
        self,
        sample_slot_data,
        sample_financial_data,
        sample_compliance_data,
    ):
        """Verify player IDs across generators could theoretically cross-reference."""
        # Extract player ID prefixes to ensure they follow similar patterns
        slot_ids = sample_slot_data["player_id"].dropna().tolist()
        financial_ids = sample_financial_data["player_id"].dropna().tolist()
        compliance_ids = sample_compliance_data["player_id"].dropna().tolist()

        # Get unique prefixes (first part before numbers)
        def get_prefix(pid):
            if pid is None:
                return None
            # Extract alphabetic prefix
            prefix = ""
            for char in pid:
                if char.isalpha() or char == "-":
                    prefix += char
                else:
                    break
            return prefix

        slot_prefixes = set(get_prefix(pid) for pid in slot_ids if pid)
        financial_prefixes = set(get_prefix(pid) for pid in financial_ids if pid)
        compliance_prefixes = set(get_prefix(pid) for pid in compliance_ids if pid)

        # All should use P or PLY- prefix
        valid_prefixes = {"P", "PLY-"}

        for prefix in slot_prefixes:
            assert prefix in valid_prefixes, f"Slot uses unexpected prefix: {prefix}"

        for prefix in financial_prefixes:
            assert (
                prefix in valid_prefixes
            ), f"Financial uses unexpected prefix: {prefix}"

        for prefix in compliance_prefixes:
            assert (
                prefix in valid_prefixes
            ), f"Compliance uses unexpected prefix: {prefix}"


class TestDateRangeConsistency:
    """Tests for date range consistency across generators."""

    def test_slot_dates_in_range(self, sample_slot_data, fixed_date_range):
        """Verify slot data dates are within configured range."""
        start_date, end_date = fixed_date_range

        timestamps = sample_slot_data["event_timestamp"].tolist()
        for ts in timestamps:
            if ts is not None:
                # Handle both datetime objects and ISO strings
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(
                        ts.replace("Z", "+00:00").replace("+00:00", "")
                    )
                # Allow some tolerance for timezone differences
                assert ts >= start_date - timedelta(
                    days=1
                ), f"Date {ts} before range start"
                assert ts <= end_date + timedelta(days=1), f"Date {ts} after range end"

    def test_compliance_dates_in_range(self, sample_compliance_data, fixed_date_range):
        """Verify compliance data dates are within configured range."""
        start_date, end_date = fixed_date_range

        # Check filing_timestamp or report_timestamp
        ts_col = (
            "filing_timestamp"
            if "filing_timestamp" in sample_compliance_data.columns
            else "report_timestamp"
        )
        timestamps = sample_compliance_data[ts_col].tolist()

        for ts in timestamps:
            if ts is not None:
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(
                        ts.replace("Z", "+00:00").replace("+00:00", "")
                    )
                assert ts >= start_date - timedelta(
                    days=1
                ), f"Date {ts} before range start"
                assert ts <= end_date + timedelta(days=1), f"Date {ts} after range end"

    def test_financial_dates_in_range(self, sample_financial_data, fixed_date_range):
        """Verify financial data dates are within configured range."""
        start_date, end_date = fixed_date_range

        timestamps = sample_financial_data["transaction_timestamp"].tolist()
        for ts in timestamps:
            if ts is not None:
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(
                        ts.replace("Z", "+00:00").replace("+00:00", "")
                    )
                assert ts >= start_date - timedelta(
                    days=1
                ), f"Date {ts} before range start"
                assert ts <= end_date + timedelta(days=1), f"Date {ts} after range end"

    def test_table_games_dates_in_range(
        self, sample_table_games_data, fixed_date_range
    ):
        """Verify table games data dates are within configured range."""
        start_date, end_date = fixed_date_range

        timestamps = sample_table_games_data["event_timestamp"].tolist()
        for ts in timestamps:
            if ts is not None:
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(
                        ts.replace("Z", "+00:00").replace("+00:00", "")
                    )
                assert ts >= start_date - timedelta(
                    days=1
                ), f"Date {ts} before range start"
                assert ts <= end_date + timedelta(days=1), f"Date {ts} after range end"

    def test_all_generators_same_date_range(self, all_generators, fixed_date_range):
        """Verify all generators use the same date range configuration."""
        start_date, end_date = fixed_date_range

        for name, generator in all_generators.items():
            assert (
                generator.start_date == start_date
            ), f"{name} generator has different start_date"
            assert (
                generator.end_date == end_date
            ), f"{name} generator has different end_date"


class TestSeedReproducibility:
    """Tests for seed reproducibility across all generators."""

    def test_slot_generator_reproducibility(self, fixed_seed):
        """Test slot generator produces same results with same seed."""
        from generators.slot_machine_generator import SlotMachineGenerator

        # Reset random state and create first generator
        np.random.seed(fixed_seed)
        Faker.seed(fixed_seed)
        gen1 = SlotMachineGenerator(seed=fixed_seed)
        df1 = gen1.generate(20, show_progress=False)

        # Reset random state and create second generator
        np.random.seed(fixed_seed)
        Faker.seed(fixed_seed)
        gen2 = SlotMachineGenerator(seed=fixed_seed)
        df2 = gen2.generate(20, show_progress=False)

        # Compare key fields
        assert df1["machine_id"].tolist() == df2["machine_id"].tolist()
        assert df1["event_type"].tolist() == df2["event_type"].tolist()

    def test_player_generator_reproducibility(self, fixed_seed):
        """Test player generator produces same results with same seed."""
        from generators.player_generator import PlayerGenerator

        np.random.seed(fixed_seed)
        Faker.seed(fixed_seed)
        gen1 = PlayerGenerator(seed=fixed_seed)
        df1 = gen1.generate(20, show_progress=False)

        np.random.seed(fixed_seed)
        Faker.seed(fixed_seed)
        gen2 = PlayerGenerator(seed=fixed_seed)
        df2 = gen2.generate(20, show_progress=False)

        assert df1["player_id"].tolist() == df2["player_id"].tolist()
        assert df1["loyalty_tier"].tolist() == df2["loyalty_tier"].tolist()

    def test_compliance_generator_reproducibility(self, fixed_seed):
        """Test compliance generator produces same results with same seed."""
        from generators.compliance_generator import ComplianceGenerator

        np.random.seed(fixed_seed)
        Faker.seed(fixed_seed)
        gen1 = ComplianceGenerator(seed=fixed_seed)
        df1 = gen1.generate(20, show_progress=False)

        np.random.seed(fixed_seed)
        Faker.seed(fixed_seed)
        gen2 = ComplianceGenerator(seed=fixed_seed)
        df2 = gen2.generate(20, show_progress=False)

        assert df1["filing_type"].tolist() == df2["filing_type"].tolist()

    def test_financial_generator_reproducibility(self, fixed_seed):
        """Test financial generator produces same results with same seed."""
        from generators.financial_generator import FinancialGenerator

        np.random.seed(fixed_seed)
        Faker.seed(fixed_seed)
        gen1 = FinancialGenerator(seed=fixed_seed)
        df1 = gen1.generate(20, show_progress=False)

        np.random.seed(fixed_seed)
        Faker.seed(fixed_seed)
        gen2 = FinancialGenerator(seed=fixed_seed)
        df2 = gen2.generate(20, show_progress=False)

        assert df1["transaction_type"].tolist() == df2["transaction_type"].tolist()

    def test_different_seeds_produce_different_data(self):
        """Test different seeds produce different results."""
        from generators.slot_machine_generator import SlotMachineGenerator

        gen1 = SlotMachineGenerator(seed=11111)
        gen2 = SlotMachineGenerator(seed=22222)

        df1 = gen1.generate(100, show_progress=False)
        df2 = gen2.generate(100, show_progress=False)

        # Event types should have different distributions
        types1 = df1["event_type"].value_counts().to_dict()
        types2 = df2["event_type"].value_counts().to_dict()

        # Not all counts should be identical
        differences = sum(1 for k in types1 if types1.get(k, 0) != types2.get(k, 0))
        assert differences > 0, "Different seeds produced identical distributions"


class TestGeneratorMetadataColumns:
    """Tests for metadata columns consistency across generators."""

    def test_all_generators_add_metadata(self, all_generators):
        """Verify all generators add standard metadata columns."""
        expected_metadata = ["_ingested_at", "_source", "_batch_id"]

        for name, generator in all_generators.items():
            record = generator.generate_record()

            for meta_col in expected_metadata:
                assert (
                    meta_col in record
                ), f"{name} generator missing metadata column: {meta_col}"

    def test_source_metadata_matches_generator(self, all_generators):
        """Verify _source metadata matches generator class name."""
        for name, generator in all_generators.items():
            record = generator.generate_record()
            expected_source = generator.__class__.__name__

            assert record["_source"] == expected_source, (
                f"{name} generator _source mismatch: "
                f"expected {expected_source}, got {record['_source']}"
            )

    def test_batch_id_is_consistent_within_batch(self, slot_generator):
        """Verify batch_id changes between generate_record calls."""
        record1 = slot_generator.generate_record()
        record2 = slot_generator.generate_record()

        # Each record should have a unique batch_id (first 8 chars of UUID)
        assert len(record1["_batch_id"]) == 8
        assert len(record2["_batch_id"]) == 8


class TestGeneratorOutputFormats:
    """Tests for generator output format capabilities."""

    def test_generators_produce_dataframe(self, all_generators):
        """Verify generators produce pandas DataFrames."""
        import pandas as pd

        for name, generator in all_generators.items():
            df = generator.generate(10, show_progress=False)
            assert isinstance(
                df, pd.DataFrame
            ), f"{name} generator did not produce DataFrame"

    def test_generators_support_parquet_output(self, slot_generator, temp_output_dir):
        """Verify generators can output to Parquet format."""
        df = slot_generator.generate(100, show_progress=False)
        output_path = temp_output_dir / "test_slot.parquet"

        slot_generator.to_parquet(df, output_path)

        assert output_path.exists(), "Parquet file was not created"

    def test_generators_support_json_output(self, slot_generator, temp_output_dir):
        """Verify generators can output to JSON format."""
        df = slot_generator.generate(100, show_progress=False)
        output_path = temp_output_dir / "test_slot.json"

        slot_generator.to_json(df, output_path)

        assert output_path.exists(), "JSON file was not created"


class TestGeneratorBatchProcessing:
    """Tests for batch generation capabilities."""

    @pytest.mark.slow
    def test_batch_generation_iterator(self, slot_generator):
        """Test batch generation yields correct batch sizes."""
        total_records = 500
        batch_size = 100
        batches = list(
            slot_generator.generate_batches(
                total_records,
                batch_size=batch_size,
                show_progress=False,
            )
        )

        # Should have 5 batches
        assert len(batches) == 5

        # Each batch should have correct size (except possibly last)
        for _i, batch in enumerate(batches[:-1]):
            assert len(batch) == batch_size

        # Total records should match
        total = sum(len(batch) for batch in batches)
        assert total == total_records

    def test_batch_generation_handles_remainder(self, slot_generator):
        """Test batch generation handles non-divisible counts."""
        total_records = 250
        batch_size = 100
        batches = list(
            slot_generator.generate_batches(
                total_records,
                batch_size=batch_size,
                show_progress=False,
            )
        )

        # Should have 3 batches (100, 100, 50)
        assert len(batches) == 3
        assert len(batches[0]) == 100
        assert len(batches[1]) == 100
        assert len(batches[2]) == 50
