# Databricks notebook source
# MAGIC %md
# MAGIC # Notebook Utilities: Data Lineage
# MAGIC
# MAGIC Shared utility functions for adding data lineage metadata to medallion architecture notebooks.
# MAGIC
# MAGIC ## Usage
# MAGIC ```python
# MAGIC %run ../utils/lineage_utils
# MAGIC
# MAGIC # In Bronze notebooks:
# MAGIC df = add_bronze_lineage(df, source_path, batch_id)
# MAGIC
# MAGIC # In Silver notebooks:
# MAGIC df = add_silver_lineage(df, source_table, batch_id)
# MAGIC
# MAGIC # In Gold notebooks:
# MAGIC df = add_gold_lineage(df, source_table, batch_id, kpi_version="1.0")
# MAGIC ```

# COMMAND ----------

import uuid
from datetime import datetime

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, current_timestamp, lit


def generate_pipeline_run_id() -> str:
    """Generate a unique pipeline run ID for tracking lineage across layers."""
    return f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"


def add_bronze_lineage(
    df: DataFrame,
    source_path: str,
    batch_id: str,
    pipeline_run_id: str | None = None,
    source_system: str = "landing_zone",
) -> DataFrame:
    """Add Bronze layer lineage metadata columns.

    Args:
        df: Input DataFrame
        source_path: Path to source data
        batch_id: Batch identifier
        pipeline_run_id: Optional pipeline run ID (generated if not provided)
        source_system: Name of the source system

    Returns:
        DataFrame with lineage columns added
    """
    run_id = pipeline_run_id or generate_pipeline_run_id()

    return (
        df.withColumn("_lineage_layer", lit("bronze"))
        .withColumn("_lineage_source_system", lit(source_system))
        .withColumn("_lineage_source_path", lit(source_path))
        .withColumn("_lineage_pipeline_run_id", lit(run_id))
        .withColumn("_lineage_ingested_at", current_timestamp())
        .withColumn("_lineage_batch_id", lit(batch_id))
    )


def add_silver_lineage(
    df: DataFrame,
    source_table: str,
    batch_id: str,
    pipeline_run_id: str | None = None,
    transformations_applied: str = "",
) -> DataFrame:
    """Add Silver layer lineage metadata columns.

    Args:
        df: Input DataFrame
        source_table: Name of source Bronze table
        batch_id: Batch identifier
        pipeline_run_id: Optional pipeline run ID
        transformations_applied: Description of transformations

    Returns:
        DataFrame with lineage columns added
    """
    run_id = pipeline_run_id or generate_pipeline_run_id()

    return (
        df.withColumn("_lineage_layer", lit("silver"))
        .withColumn("_lineage_source_table", lit(source_table))
        .withColumn("_lineage_pipeline_run_id", lit(run_id))
        .withColumn("_lineage_processed_at", current_timestamp())
        .withColumn("_lineage_batch_id", lit(batch_id))
        .withColumn("_lineage_transformations", lit(transformations_applied))
    )


def add_gold_lineage(
    df: DataFrame,
    source_table: str,
    batch_id: str,
    pipeline_run_id: str | None = None,
    kpi_version: str = "1.0",
    aggregation_grain: str = "",
) -> DataFrame:
    """Add Gold layer lineage metadata columns.

    Args:
        df: Input DataFrame
        source_table: Name of source Silver table
        batch_id: Batch identifier
        pipeline_run_id: Optional pipeline run ID
        kpi_version: Version of the KPI calculation logic
        aggregation_grain: Description of aggregation level

    Returns:
        DataFrame with lineage columns added
    """
    run_id = pipeline_run_id or generate_pipeline_run_id()

    return (
        df.withColumn("_lineage_layer", lit("gold"))
        .withColumn("_lineage_source_table", lit(source_table))
        .withColumn("_lineage_pipeline_run_id", lit(run_id))
        .withColumn("_lineage_computed_at", current_timestamp())
        .withColumn("_lineage_batch_id", lit(batch_id))
        .withColumn("_lineage_kpi_version", lit(kpi_version))
        .withColumn("_lineage_aggregation_grain", lit(aggregation_grain))
    )


def get_lineage_summary(spark, table_name: str) -> None:
    """Print lineage summary for a table.

    Args:
        spark: SparkSession
        table_name: Name of the table to inspect
    """
    print(f"\n{'='*60}")
    print(f"Data Lineage Summary: {table_name}")
    print(f"{'='*60}")

    lineage_cols = [c for c in spark.table(table_name).columns if c.startswith("_lineage_")]

    if not lineage_cols:
        print("No lineage columns found in table.")
        return

    print(f"Lineage columns: {', '.join(lineage_cols)}")

    # Show latest lineage info
    spark.sql(f"""
        SELECT {', '.join(lineage_cols)}
        FROM {table_name}
        LIMIT 1
    """).show(truncate=False)
