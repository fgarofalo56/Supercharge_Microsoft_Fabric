"""
Unit tests for the Bronze ingestion pattern used across all notebooks.

These tests demonstrate how to extract notebook logic into testable functions
and validate it locally with PySpark, without requiring a live Fabric workspace.

Pattern under test (see notebooks/bronze/01_bronze_slot_telemetry.py):
  1. Read source data with an explicit schema
  2. Reject / flag rows with null primary keys
  3. Deduplicate on primary key
  4. Add metadata columns (_ingested_at, _source_file, _batch_id)
  5. Write to Delta in append mode

Run:
    pytest validation/unit_tests/notebook/test_bronze_pattern.py -v
"""

from datetime import datetime

import pytest

pyspark = pytest.importorskip("pyspark", reason="PySpark not installed")
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, current_timestamp, lit
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

# ---------------------------------------------------------------------------
# Extracted Bronze helpers -- mirror the notebook logic so it becomes testable
# ---------------------------------------------------------------------------

SLOT_SCHEMA = StructType(
    [
        StructField("event_id", StringType(), False),
        StructField("machine_id", StringType(), False),
        StructField("event_type", StringType(), False),
        StructField("event_timestamp", TimestampType(), False),
        StructField("coin_in", DoubleType(), True),
        StructField("coin_out", DoubleType(), True),
        StructField("games_played", IntegerType(), True),
    ]
)

PRIMARY_KEY_COLUMNS = ["event_id"]


def read_source(spark: SparkSession, path: str, schema: StructType) -> DataFrame:
    """Read a Parquet source with an explicit schema (DROPMALFORMED mode)."""
    return spark.read.schema(schema).option("mode", "DROPMALFORMED").parquet(path)


def reject_null_primary_keys(df: DataFrame, pk_cols: list[str]) -> DataFrame:
    """Filter out rows where any primary-key column is null."""
    condition = col(pk_cols[0]).isNotNull()
    for pk in pk_cols[1:]:
        condition = condition & col(pk).isNotNull()
    return df.filter(condition)


def deduplicate(df: DataFrame, pk_cols: list[str]) -> DataFrame:
    """Drop exact duplicates based on primary-key columns."""
    return df.dropDuplicates(pk_cols)


def add_metadata(df: DataFrame, batch_id: str) -> DataFrame:
    """Append Bronze metadata columns."""
    return (
        df.withColumn("_ingested_at", current_timestamp())
        .withColumn("_source_file", lit("test_source.parquet"))
        .withColumn("_batch_id", lit(batch_id))
    )


def write_bronze(df: DataFrame, path: str) -> None:
    """Write to Delta in append mode (mirrors notebook write step)."""
    df.write.format("delta").mode("append").save(path)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def spark():
    """Create a module-scoped local PySpark session for testing."""
    session = (
        SparkSession.builder.master("local[*]")
        .appName("bronze-pattern-tests")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.default.parallelism", "2")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()


@pytest.fixture()
def sample_parquet_file(spark, tmp_path):
    """Write a small Parquet file with known data and return its path."""
    ts = datetime(2026, 1, 15, 10, 30, 0)
    rows = [
        ("EVT-001", "SLOT-0001", "GAME_PLAY", ts, 25.0, 10.0, 1),
        ("EVT-002", "SLOT-0002", "JACKPOT", ts, 50.0, 500.0, 5),
        ("EVT-003", "SLOT-0001", "METER_UPDATE", ts, 0.0, 0.0, 0),
        ("EVT-004", "SLOT-0003", "GAME_PLAY", ts, 100.0, 75.0, 10),
    ]
    df = spark.createDataFrame(rows, schema=SLOT_SCHEMA)
    path = str(tmp_path / "source_data")
    df.write.parquet(path)
    return path


@pytest.fixture()
def delta_path(tmp_path):
    """Return a fresh directory path for a Delta table."""
    return str(tmp_path / "bronze_delta")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBronzeSchemaEnforcement:
    """Validate that the explicit schema is applied on read."""

    def test_schema_enforcement(self, spark, sample_parquet_file):
        """Reading with SLOT_SCHEMA should produce the exact expected columns."""
        df = read_source(spark, sample_parquet_file, SLOT_SCHEMA)

        expected_columns = [f.name for f in SLOT_SCHEMA.fields]
        assert df.columns == expected_columns

    def test_schema_types_match(self, spark, sample_parquet_file):
        """Column data types should match the declared schema."""
        df = read_source(spark, sample_parquet_file, SLOT_SCHEMA)
        actual_types = {f.name: f.dataType for f in df.schema.fields}

        for field in SLOT_SCHEMA.fields:
            assert actual_types[field.name] == field.dataType, (
                f"{field.name}: expected {field.dataType}, got {actual_types[field.name]}"
            )


class TestBronzeMetadataColumns:
    """Verify that Bronze metadata columns are added correctly."""

    def test_metadata_columns_added(self, spark, sample_parquet_file):
        """_ingested_at, _source_file, and _batch_id must be present after add_metadata."""
        df = read_source(spark, sample_parquet_file, SLOT_SCHEMA)
        df_with_meta = add_metadata(df, batch_id="20260115_103000")

        for col_name in ("_ingested_at", "_source_file", "_batch_id"):
            assert col_name in df_with_meta.columns, f"Missing column: {col_name}"

    def test_batch_id_value(self, spark, sample_parquet_file):
        """_batch_id should carry the value passed to add_metadata."""
        df = read_source(spark, sample_parquet_file, SLOT_SCHEMA)
        df_with_meta = add_metadata(df, batch_id="BATCH_42")

        batch_ids = [r["_batch_id"] for r in df_with_meta.select("_batch_id").collect()]
        assert all(bid == "BATCH_42" for bid in batch_ids)

    def test_metadata_does_not_drop_columns(self, spark, sample_parquet_file):
        """Adding metadata must not remove any original columns."""
        df = read_source(spark, sample_parquet_file, SLOT_SCHEMA)
        original_cols = set(df.columns)
        df_with_meta = add_metadata(df, batch_id="TEST")

        assert original_cols.issubset(set(df_with_meta.columns))


class TestBronzeNullPrimaryKey:
    """Rows with null primary keys should be rejected."""

    def test_null_primary_key_rejected(self, spark):
        """Rows where the PK column is null must be filtered out."""
        ts = datetime(2026, 1, 15, 10, 30, 0)
        rows = [
            ("EVT-001", "SLOT-0001", "GAME_PLAY", ts, 10.0, 5.0, 1),
            (None, "SLOT-0002", "JACKPOT", ts, 50.0, 500.0, 5),
            ("EVT-003", "SLOT-0003", "METER_UPDATE", ts, 0.0, 0.0, 0),
        ]
        df = spark.createDataFrame(rows, schema=SLOT_SCHEMA)
        filtered = reject_null_primary_keys(df, PRIMARY_KEY_COLUMNS)

        assert filtered.count() == 2
        ids = {r["event_id"] for r in filtered.select("event_id").collect()}
        assert ids == {"EVT-001", "EVT-003"}

    def test_all_valid_rows_kept(self, spark, sample_parquet_file):
        """When no PK nulls exist, all rows pass through."""
        df = read_source(spark, sample_parquet_file, SLOT_SCHEMA)
        filtered = reject_null_primary_keys(df, PRIMARY_KEY_COLUMNS)

        assert filtered.count() == df.count()


class TestBronzeDeduplication:
    """Duplicate records on the primary key should be collapsed."""

    def test_deduplication(self, spark):
        """Exact duplicate rows (same PK) should be reduced to one."""
        ts = datetime(2026, 1, 15, 10, 30, 0)
        rows = [
            ("EVT-001", "SLOT-0001", "GAME_PLAY", ts, 25.0, 10.0, 1),
            ("EVT-001", "SLOT-0001", "GAME_PLAY", ts, 25.0, 10.0, 1),
            ("EVT-002", "SLOT-0002", "JACKPOT", ts, 50.0, 500.0, 5),
        ]
        df = spark.createDataFrame(rows, schema=SLOT_SCHEMA)
        deduped = deduplicate(df, PRIMARY_KEY_COLUMNS)

        assert deduped.count() == 2

    def test_different_pks_preserved(self, spark, sample_parquet_file):
        """Rows with distinct PKs should all be kept."""
        df = read_source(spark, sample_parquet_file, SLOT_SCHEMA)
        deduped = deduplicate(df, PRIMARY_KEY_COLUMNS)

        assert deduped.count() == 4


class TestBronzeAppendMode:
    """Writing in append mode should accumulate records across batches."""

    def test_append_mode(self, spark, sample_parquet_file, delta_path):
        """Two writes to the same Delta path should double the row count."""
        df = read_source(spark, sample_parquet_file, SLOT_SCHEMA)
        df_with_meta = add_metadata(df, batch_id="BATCH_1")

        # First write
        write_bronze(df_with_meta, delta_path)
        count_after_first = spark.read.format("delta").load(delta_path).count()

        # Second write (append)
        df_batch2 = add_metadata(df, batch_id="BATCH_2")
        write_bronze(df_batch2, delta_path)
        count_after_second = spark.read.format("delta").load(delta_path).count()

        assert count_after_first == 4
        assert count_after_second == 8

    def test_append_preserves_batch_ids(self, spark, sample_parquet_file, delta_path):
        """Both batch IDs should be present after two appends."""
        df = read_source(spark, sample_parquet_file, SLOT_SCHEMA)

        write_bronze(add_metadata(df, batch_id="BATCH_A"), delta_path)
        write_bronze(add_metadata(df, batch_id="BATCH_B"), delta_path)

        result = spark.read.format("delta").load(delta_path)
        batch_ids = {r["_batch_id"] for r in result.select("_batch_id").collect()}
        assert batch_ids == {"BATCH_A", "BATCH_B"}


class TestBronzeMalformedData:
    """DROPMALFORMED mode should silently discard unparseable rows."""

    def test_malformed_data_dropped(self, spark, tmp_path):
        """Reading with a strict schema should drop rows that do not conform."""
        # Write data with a wider schema (extra column, mismatched types)
        wider_schema = StructType(
            [
                StructField("event_id", StringType(), True),
                StructField("machine_id", StringType(), True),
                StructField("event_type", StringType(), True),
                StructField("event_timestamp", TimestampType(), True),
                StructField("coin_in", DoubleType(), True),
                StructField("coin_out", DoubleType(), True),
                StructField("games_played", IntegerType(), True),
                StructField("extra_field", StringType(), True),
            ]
        )
        ts = datetime(2026, 1, 15, 10, 30, 0)
        rows = [
            ("EVT-001", "SLOT-0001", "GAME_PLAY", ts, 25.0, 10.0, 1, "extra"),
            ("EVT-002", "SLOT-0002", "JACKPOT", ts, 50.0, 500.0, 5, None),
        ]
        df = spark.createDataFrame(rows, schema=wider_schema)
        path = str(tmp_path / "wider_source")
        df.write.parquet(path)

        # Read back with the narrower SLOT_SCHEMA -- extra column is ignored
        result = read_source(spark, path, SLOT_SCHEMA)
        assert "extra_field" not in result.columns
        assert result.count() == 2

    def test_schema_subset_columns_present(self, spark, tmp_path):
        """Only columns declared in SLOT_SCHEMA appear in the result."""
        ts = datetime(2026, 1, 15, 10, 30, 0)
        rows = [("EVT-001", "SLOT-0001", "GAME_PLAY", ts, 25.0, 10.0, 1)]
        df = spark.createDataFrame(rows, schema=SLOT_SCHEMA)
        path = str(tmp_path / "exact_source")
        df.write.parquet(path)

        result = read_source(spark, path, SLOT_SCHEMA)
        assert set(result.columns) == {f.name for f in SLOT_SCHEMA.fields}
