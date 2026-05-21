"""
Unit tests for MultiSourceSimulator.

Covers all five CDC source types:
- sql_server  : Debezium-style LSN-based CDC
- azure_sql   : Fabric Mirroring / Change Feed
- cosmos_db   : Cosmos DB Change Feed Processor
- ibm_db2     : InfoSphere CDC / ASN Capture
- oracle      : LogMiner / GoldenGate
"""

from generators.streaming.multi_source_simulator import (
    SOURCE_CONFIG,
)

# All valid connector names across all source types
_ALL_CONNECTORS = {
    connector for cfg in SOURCE_CONFIG.values() for connector in cfg["connectors"]
}

_VALID_OPERATIONS = {"INSERT", "UPDATE", "DELETE", "READ"}

_SOURCE_TYPE_KEYS = list(SOURCE_CONFIG.keys())


class TestMultiSourceSimulator:
    """Tests for MultiSourceSimulator covering all CDC source types."""

    # ------------------------------------------------------------------
    # Basic field presence
    # ------------------------------------------------------------------

    def test_generate_sql_server_record(self, multi_source_simulator):
        """Generate a SQL Server CDC record and assert required top-level fields exist."""
        record = multi_source_simulator.generate_record(source_type="sql_server")

        assert record is not None
        assert "event_id" in record, "event_id field missing"
        assert "source_type" in record, "source_type field missing"
        assert "operation" in record, "operation field missing"
        assert "timestamp" in record, "timestamp field missing"
        assert "table_name" in record, "table_name field missing"

    # ------------------------------------------------------------------
    # source_type enum
    # ------------------------------------------------------------------

    def test_source_type_matches_domain(self, multi_source_simulator):
        """Generating with source_type='sql_server' must yield source_type='SQL_SERVER'."""
        record = multi_source_simulator.generate_record(source_type="sql_server")

        assert record["source_type"] == "SQL_SERVER", (
            f"Expected SQL_SERVER, got {record['source_type']}"
        )

    def test_all_source_types(self, multi_source_simulator):
        """Each of the five source types must produce a valid record with the correct enum."""
        expected_enums = {
            "sql_server": "SQL_SERVER",
            "azure_sql": "AZURE_SQL",
            "cosmos_db": "COSMOS_DB",
            "ibm_db2": "IBM_DB2",
            "oracle": "ORACLE",
        }
        for source_key, expected_enum in expected_enums.items():
            record = multi_source_simulator.generate_record(source_type=source_key)
            assert record is not None, (
                f"No record returned for source_type='{source_key}'"
            )
            assert record["source_type"] == expected_enum, (
                f"source_type='{source_key}' should yield enum '{expected_enum}', "
                f"got '{record['source_type']}'"
            )

    # ------------------------------------------------------------------
    # Operation validity
    # ------------------------------------------------------------------

    def test_operation_valid(self, multi_source_simulator, sample_size):
        """All generated operations across 100 records must be INSERT, UPDATE, DELETE, or READ."""
        for _ in range(sample_size):
            record = multi_source_simulator.generate_record()
            assert record["operation"] in _VALID_OPERATIONS, (
                f"Unexpected operation '{record['operation']}'"
            )

    # ------------------------------------------------------------------
    # Before/after image logic
    # ------------------------------------------------------------------

    def test_before_after_image_logic(self, multi_source_simulator):
        """
        Verify CDC image rules across a large sample:
          - INSERT  → after_image populated, before_image is None
          - DELETE  → before_image populated, after_image is None
          - UPDATE  → both images populated
          - READ    → after_image populated, before_image is None
        """
        counts = {op: 0 for op in _VALID_OPERATIONS}
        iterations = 500

        for _ in range(iterations):
            record = multi_source_simulator.generate_record()
            op = record["operation"]
            counts[op] += 1

            if op == "INSERT":
                assert record["after_image"] is not None, "INSERT must have after_image"
                assert record["before_image"] is None, (
                    "INSERT must not have before_image"
                )
            elif op == "DELETE":
                assert record["before_image"] is not None, (
                    "DELETE must have before_image"
                )
                assert record["after_image"] is None, "DELETE must not have after_image"
            elif op == "UPDATE":
                assert record["before_image"] is not None, (
                    "UPDATE must have before_image"
                )
                assert record["after_image"] is not None, "UPDATE must have after_image"
            elif op == "READ":
                assert record["after_image"] is not None, "READ must have after_image"
                assert record["before_image"] is None, "READ must not have before_image"

        # Sanity-check that we exercised at least INSERT and DELETE in the sample
        assert counts["INSERT"] > 0, "No INSERT operations seen in 500 records"
        assert counts["DELETE"] > 0, "No DELETE operations seen in 500 records"

    # ------------------------------------------------------------------
    # Connector name
    # ------------------------------------------------------------------

    def test_connector_name_valid(self, multi_source_simulator, sample_size):
        """connector_name must come from the known connector enum across all source types."""
        for source_key in _SOURCE_TYPE_KEYS:
            for _ in range(20):
                record = multi_source_simulator.generate_record(source_type=source_key)
                assert record["connector_name"] in _ALL_CONNECTORS, (
                    f"Unexpected connector '{record['connector_name']}' "
                    f"for source_type='{source_key}'"
                )

    # ------------------------------------------------------------------
    # Latency
    # ------------------------------------------------------------------

    def test_latency_positive(self, multi_source_simulator, sample_size):
        """latency_ms must be a non-negative integer for every source type."""
        for source_key in _SOURCE_TYPE_KEYS:
            for _ in range(20):
                record = multi_source_simulator.generate_record(source_type=source_key)
                assert isinstance(record["latency_ms"], int), (
                    f"latency_ms must be int, got {type(record['latency_ms'])}"
                )
                assert record["latency_ms"] >= 0, (
                    f"latency_ms must be >= 0, got {record['latency_ms']}"
                )

    # ------------------------------------------------------------------
    # Batch generation
    # ------------------------------------------------------------------

    def test_generate_batch(self, multi_source_simulator, sample_size):
        """generate_batch returns exactly the requested number of records."""
        batch = multi_source_simulator.generate_batch(
            count=sample_size, source_type="sql_server"
        )

        assert isinstance(batch, list), "generate_batch must return a list"
        assert len(batch) == sample_size, (
            f"Expected {sample_size} records, got {len(batch)}"
        )

    def test_generate_mixed_batch(self, multi_source_simulator, sample_size):
        """generate_mixed_batch produces the correct count and spans multiple source types."""
        batch = multi_source_simulator.generate_mixed_batch(count=sample_size)

        assert len(batch) == sample_size, (
            f"Expected {sample_size} records, got {len(batch)}"
        )

        observed_types = {record["source_type"] for record in batch}
        assert len(observed_types) > 1, (
            f"Mixed batch should contain multiple source_type values, "
            f"got only: {observed_types}"
        )

    # ------------------------------------------------------------------
    # Metadata columns
    # ------------------------------------------------------------------

    def test_metadata_columns(self, multi_source_simulator):
        """
        CDC records carry source-tracking metadata in load_time, schema_version,
        and sequence_number rather than the base add_metadata_columns fields.
        Verify all three are present and that sequence_number increments across
        successive calls.
        """
        record1 = multi_source_simulator.generate_record()
        record2 = multi_source_simulator.generate_record()

        for record in (record1, record2):
            assert "load_time" in record, "load_time metadata field missing"
            assert "schema_version" in record, "schema_version metadata field missing"
            assert "sequence_number" in record, "sequence_number metadata field missing"

        assert record2["sequence_number"] > record1["sequence_number"], (
            "sequence_number must increment between successive generate_record calls"
        )
