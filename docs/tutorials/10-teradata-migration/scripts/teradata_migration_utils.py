"""
Teradata to Microsoft Fabric Migration Utilities
=================================================

This module provides utility functions for migrating data from Teradata
to Microsoft Fabric, including:
- Connection management
- Data validation
- SQL translation helpers
- Incremental load patterns

Usage:
    from teradata_migration_utils import TeradataMigrator

    migrator = TeradataMigrator(
        teradata_host="teradata.example.com",
        teradata_user="migration_user",
        fabric_workspace="casino-fabric-poc"
    )

    migrator.migrate_table("CASINO_DW.SLOT_TRANSACTIONS", "bronze.slot_transactions")
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, lit, current_timestamp, md5, concat_ws,
    sum as spark_sum, count, max as spark_max, min as spark_min
)
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TeradataMigrator:
    """
    Handles migration of data from Teradata to Microsoft Fabric.

    Supports:
    - Full table migration
    - Incremental migration with watermark
    - Data validation
    - Parallel table migration
    """

    def __init__(
        self,
        teradata_host: str,
        teradata_user: str,
        teradata_password: str,
        teradata_database: str = "DBC",
        fabric_lakehouse: str = "lh_bronze",
        spark: Optional[SparkSession] = None
    ):
        """
        Initialize the Teradata migrator.

        Args:
            teradata_host: Teradata server hostname
            teradata_user: Teradata username
            teradata_password: Teradata password
            teradata_database: Default Teradata database
            fabric_lakehouse: Target Fabric lakehouse name
            spark: Optional SparkSession (creates new if not provided)
        """
        self.teradata_host = teradata_host
        self.teradata_user = teradata_user
        self.teradata_password = teradata_password
        self.teradata_database = teradata_database
        self.fabric_lakehouse = fabric_lakehouse

        self.spark = spark or SparkSession.builder.getOrCreate()

        self.jdbc_url = f"jdbc:teradata://{teradata_host}/{teradata_database}"
        self.jdbc_properties = {
            "user": teradata_user,
            "password": teradata_password,
            "driver": "com.teradata.jdbc.TeraDriver"
        }

        logger.info(f"Initialized TeradataMigrator for {teradata_host}")

    def read_teradata_table(
        self,
        table_name: str,
        partition_column: Optional[str] = None,
        lower_bound: Optional[str] = None,
        upper_bound: Optional[str] = None,
        num_partitions: int = 8,
        fetch_size: int = 100000,
        custom_query: Optional[str] = None
    ) -> DataFrame:
        """
        Read a table from Teradata into a Spark DataFrame.

        Args:
            table_name: Full table name (DATABASE.TABLE)
            partition_column: Column for parallel reads
            lower_bound: Lower bound for partition column
            upper_bound: Upper bound for partition column
            num_partitions: Number of parallel partitions
            fetch_size: JDBC fetch size
            custom_query: Optional custom SQL query

        Returns:
            Spark DataFrame with table data
        """
        logger.info(f"Reading from Teradata: {table_name}")

        reader = self.spark.read.format("jdbc") \
            .option("url", self.jdbc_url) \
            .option("user", self.teradata_user) \
            .option("password", self.teradata_password) \
            .option("driver", "com.teradata.jdbc.TeraDriver") \
            .option("fetchsize", fetch_size)

        if custom_query:
            reader = reader.option("query", custom_query)
        else:
            reader = reader.option("dbtable", table_name)

        # Add partitioning for parallel reads
        if partition_column and lower_bound and upper_bound:
            reader = reader \
                .option("partitionColumn", partition_column) \
                .option("lowerBound", lower_bound) \
                .option("upperBound", upper_bound) \
                .option("numPartitions", num_partitions)

        df = reader.load()

        row_count = df.count()
        logger.info(f"Read {row_count:,} rows from {table_name}")

        return df

    def write_to_fabric(
        self,
        df: DataFrame,
        target_table: str,
        mode: str = "overwrite",
        partition_by: Optional[List[str]] = None,
        optimize: bool = True
    ) -> int:
        """
        Write DataFrame to Fabric Lakehouse as Delta table.

        Args:
            df: Source DataFrame
            target_table: Target table name (schema.table)
            mode: Write mode (overwrite, append, merge)
            partition_by: Columns to partition by
            optimize: Run OPTIMIZE after write

        Returns:
            Number of rows written
        """
        logger.info(f"Writing to Fabric: {target_table}")

        # Add migration metadata
        df_with_metadata = df \
            .withColumn("_migration_timestamp", current_timestamp()) \
            .withColumn("_source_system", lit("Teradata"))

        # Write to Delta
        writer = df_with_metadata.write.mode(mode).format("delta")

        if partition_by:
            writer = writer.partitionBy(*partition_by)

        writer.saveAsTable(target_table)

        row_count = df_with_metadata.count()
        logger.info(f"Wrote {row_count:,} rows to {target_table}")

        # Optimize table
        if optimize:
            self.spark.sql(f"OPTIMIZE {target_table}")
            logger.info(f"Optimized {target_table}")

        return row_count

    def migrate_table(
        self,
        source_table: str,
        target_table: str,
        partition_column: Optional[str] = None,
        partition_by: Optional[List[str]] = None,
        mode: str = "overwrite"
    ) -> Dict:
        """
        Migrate a single table from Teradata to Fabric.

        Args:
            source_table: Source Teradata table (DATABASE.TABLE)
            target_table: Target Fabric table (schema.table)
            partition_column: Column for parallel reads
            partition_by: Columns for Delta partitioning
            mode: Write mode

        Returns:
            Migration result dictionary
        """
        start_time = datetime.now()

        try:
            # Read from Teradata
            df = self.read_teradata_table(
                source_table,
                partition_column=partition_column
            )

            # Write to Fabric
            row_count = self.write_to_fabric(
                df,
                target_table,
                mode=mode,
                partition_by=partition_by
            )

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                "status": "SUCCESS",
                "source_table": source_table,
                "target_table": target_table,
                "row_count": row_count,
                "duration_seconds": duration,
                "rows_per_second": row_count / duration if duration > 0 else 0,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            }

            logger.info(f"Migration complete: {source_table} -> {target_table} "
                       f"({row_count:,} rows in {duration:.1f}s)")

        except Exception as e:
            result = {
                "status": "FAILED",
                "source_table": source_table,
                "target_table": target_table,
                "error": str(e),
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat()
            }
            logger.error(f"Migration failed: {source_table} - {e}")

        return result

    def migrate_incremental(
        self,
        source_table: str,
        target_table: str,
        watermark_column: str,
        watermark_value: Optional[datetime] = None
    ) -> Dict:
        """
        Perform incremental migration using watermark column.

        Args:
            source_table: Source Teradata table
            target_table: Target Fabric table
            watermark_column: Column to use for watermark (timestamp)
            watermark_value: Starting watermark (defaults to max in target)

        Returns:
            Migration result dictionary
        """
        # Get current watermark from target if not provided
        if watermark_value is None:
            try:
                watermark_df = self.spark.table(target_table) \
                    .select(spark_max(watermark_column).alias("max_watermark"))
                watermark_value = watermark_df.collect()[0]["max_watermark"]
            except:
                # Table doesn't exist, start from beginning
                watermark_value = datetime(2020, 1, 1)

        logger.info(f"Incremental load from watermark: {watermark_value}")

        # Build incremental query
        query = f"""
            SELECT * FROM {source_table}
            WHERE {watermark_column} > TIMESTAMP '{watermark_value}'
            ORDER BY {watermark_column}
        """

        # Read incremental data
        df = self.read_teradata_table(source_table, custom_query=query)

        if df.count() == 0:
            logger.info("No new data to migrate")
            return {
                "status": "NO_DATA",
                "source_table": source_table,
                "target_table": target_table,
                "watermark": str(watermark_value),
                "row_count": 0
            }

        # Append to target
        row_count = self.write_to_fabric(df, target_table, mode="append")

        # Get new watermark
        new_watermark = df.select(spark_max(watermark_column)).collect()[0][0]

        return {
            "status": "SUCCESS",
            "source_table": source_table,
            "target_table": target_table,
            "previous_watermark": str(watermark_value),
            "new_watermark": str(new_watermark),
            "row_count": row_count
        }


class DataValidator:
    """
    Validates migrated data between Teradata and Fabric.
    """

    def __init__(self, migrator: TeradataMigrator):
        self.migrator = migrator
        self.spark = migrator.spark

    def validate_row_counts(
        self,
        source_table: str,
        target_table: str,
        tolerance_pct: float = 0.01
    ) -> Dict:
        """
        Compare row counts between source and target.

        Args:
            source_table: Source Teradata table
            target_table: Target Fabric table
            tolerance_pct: Acceptable difference percentage

        Returns:
            Validation result
        """
        # Get source count
        source_count_df = self.migrator.read_teradata_table(
            source_table,
            custom_query=f"SELECT COUNT(*) AS cnt FROM {source_table}"
        )
        source_count = source_count_df.collect()[0]["cnt"]

        # Get target count
        target_count = self.spark.table(target_table).count()

        # Calculate difference
        diff = abs(source_count - target_count)
        diff_pct = (diff / source_count * 100) if source_count > 0 else 0

        passed = diff_pct <= tolerance_pct * 100

        return {
            "validation_type": "row_count",
            "source_table": source_table,
            "target_table": target_table,
            "source_count": source_count,
            "target_count": target_count,
            "difference": diff,
            "difference_pct": diff_pct,
            "tolerance_pct": tolerance_pct * 100,
            "passed": passed,
            "status": "PASS" if passed else "FAIL"
        }

    def validate_checksums(
        self,
        source_table: str,
        target_table: str,
        numeric_columns: List[str]
    ) -> Dict:
        """
        Compare numeric column checksums between source and target.

        Args:
            source_table: Source Teradata table
            target_table: Target Fabric table
            numeric_columns: List of numeric columns to checksum

        Returns:
            Validation result
        """
        # Build checksum query for Teradata
        sum_expressions = ", ".join([f"SUM({c}) AS sum_{c}" for c in numeric_columns])
        source_query = f"SELECT {sum_expressions} FROM {source_table}"

        source_df = self.migrator.read_teradata_table(
            source_table,
            custom_query=source_query
        )
        source_sums = source_df.collect()[0].asDict()

        # Get target checksums
        target_df = self.spark.table(target_table)
        agg_exprs = [spark_sum(col(c)).alias(f"sum_{c}") for c in numeric_columns]
        target_sums = target_df.agg(*agg_exprs).collect()[0].asDict()

        # Compare
        mismatches = []
        for col_name in numeric_columns:
            source_val = source_sums.get(f"sum_{col_name}", 0) or 0
            target_val = target_sums.get(f"sum_{col_name}", 0) or 0

            if abs(source_val - target_val) > 0.01:  # Allow small floating point diff
                mismatches.append({
                    "column": col_name,
                    "source_sum": source_val,
                    "target_sum": target_val,
                    "difference": source_val - target_val
                })

        return {
            "validation_type": "checksum",
            "source_table": source_table,
            "target_table": target_table,
            "columns_checked": numeric_columns,
            "mismatches": mismatches,
            "passed": len(mismatches) == 0,
            "status": "PASS" if len(mismatches) == 0 else "FAIL"
        }


class SQLTranslator:
    """
    Translates Teradata SQL to Fabric-compatible SQL.
    """

    # Common function mappings
    FUNCTION_MAPPINGS = {
        # Null handling
        "NVL": "COALESCE",
        "NULLIFZERO": "NULLIF({0}, 0)",
        "ZEROIFNULL": "COALESCE({0}, 0)",

        # String functions
        "OREPLACE": "REPLACE",
        "INDEX": "CHARINDEX",

        # Date functions
        "ADD_MONTHS": "DATEADD(MONTH, {1}, {0})",
        "CURRENT_DATE": "CAST(GETDATE() AS DATE)",
        "CURRENT_TIMESTAMP": "GETDATE()",
    }

    @staticmethod
    def translate_qualify(sql: str) -> str:
        """
        Translate QUALIFY clause to CTE with ROW_NUMBER filter.

        Example:
            Input: SELECT * FROM t QUALIFY ROW_NUMBER() OVER (PARTITION BY a ORDER BY b) = 1
            Output: WITH cte AS (SELECT *, ROW_NUMBER() OVER (...) AS rn FROM t)
                    SELECT * FROM cte WHERE rn = 1
        """
        import re

        # Simple pattern match for QUALIFY
        pattern = r"(SELECT\s+.+?\s+FROM\s+\S+.*?)\s+QUALIFY\s+(.+?)\s*=\s*(\d+)"
        match = re.search(pattern, sql, re.IGNORECASE | re.DOTALL)

        if not match:
            return sql

        select_part = match.group(1)
        window_func = match.group(2)
        value = match.group(3)

        # Create CTE
        translated = f"""
WITH ranked_cte AS (
    {select_part},
    {window_func} AS _rn
)
SELECT * FROM ranked_cte WHERE _rn = {value}
""".strip()

        return translated

    @staticmethod
    def translate_date_arithmetic(sql: str) -> str:
        """
        Translate Teradata date arithmetic to T-SQL DATEADD.

        Example:
            Input: date_col + INTERVAL '7' DAY
            Output: DATEADD(DAY, 7, date_col)
        """
        import re

        # Pattern for INTERVAL addition
        pattern = r"(\w+)\s*\+\s*INTERVAL\s*'(\d+)'\s*(DAY|MONTH|YEAR|HOUR|MINUTE|SECOND)"

        def replace_interval(match):
            col = match.group(1)
            value = match.group(2)
            unit = match.group(3)
            return f"DATEADD({unit}, {value}, {col})"

        return re.sub(pattern, replace_interval, sql, flags=re.IGNORECASE)


# Example usage
if __name__ == "__main__":
    # Example SQL translation
    teradata_sql = """
    SELECT player_id, session_date, total_spend
    FROM casino.player_sessions
    QUALIFY ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY session_date DESC) = 1
    """

    translated = SQLTranslator.translate_qualify(teradata_sql)
    print("Translated SQL:")
    print(translated)
