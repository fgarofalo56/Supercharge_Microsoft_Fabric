# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer: Player Master with SCD Type 2
# MAGIC
# MAGIC This notebook implements Slowly Changing Dimension Type 2 for player data,
# MAGIC tracking historical changes to player attributes over time.
# MAGIC
# MAGIC ## SCD Type 2 Pattern:
# MAGIC - Track changes to key attributes (tier, email, address)
# MAGIC - Maintain history with effective dates
# MAGIC - Current record flagged with is_current = True

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

from pyspark.sql.functions import (
    coalesce,
    col,
    concat_ws,
    count,
    current_date,
    current_timestamp,
    exists,
    filter,
    first,
    lit,
    sha2,
)
from delta.tables import DeltaTable
from datetime import datetime

# Parameters
batch_id = dbutils.widgets.get("batch_id") if "batch_id" in [w.name for w in dbutils.widgets.getAll()] else datetime.now().strftime("%Y%m%d_%H%M%S")

# Source and target
source_table = "lh_bronze.bronze_player_profile"
target_table = "lh_silver.silver_player_master"

print(f"Processing batch: {batch_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read Bronze Data

# COMMAND ----------

df_bronze = spark.table(source_table)

print(f"Bronze player records: {df_bronze.count():,}")
df_bronze.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define SCD Type 2 Tracked Attributes

# COMMAND ----------

# Attributes that trigger a new version when changed
TRACKED_ATTRIBUTES = [
    "loyalty_tier",
    "email",
    "phone",
    "address",
    "city",
    "state",
    "zip_code",
    "marketing_opt_in"
]

# Key column
KEY_COLUMN = "player_id"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prepare New Data

# COMMAND ----------

# Select and clean new records
df_new = df_bronze.select(
    col("player_id"),
    col("first_name"),
    col("last_name"),
    col("date_of_birth"),
    col("gender"),
    col("email"),
    col("phone"),
    col("address"),
    col("city"),
    col("state"),
    col("zip_code"),
    col("loyalty_tier"),
    col("enrollment_date"),
    col("marketing_opt_in"),
    col("ssn_hash"),
    col("_ingestion_timestamp").alias("source_timestamp")
)

# Add SCD columns for new records
df_new = df_new \
    .withColumn("effective_date", current_date()) \
    .withColumn("end_date", lit(None).cast("date")) \
    .withColumn("is_current", lit(True)) \
    .withColumn("version", lit(1)) \
    .withColumn("_silver_timestamp", current_timestamp()) \
    .withColumn("_batch_id", lit(batch_id))

# COMMAND ----------

# MAGIC %md
# MAGIC ## SCD Type 2 Merge Logic

# COMMAND ----------

# Check if target table exists
try:
    table_exists = spark.catalog.tableExists(target_table)
    
    if table_exists:
        print("Target table exists - performing SCD Type 2 merge")
    
        # Get current records from Silver
        silver_table = DeltaTable.forName(spark, target_table)
        df_current = silver_table.toDF().filter(col("is_current") == True)
    
        # Create hash of tracked attributes for comparison
        df_new_hashed = df_new.withColumn(
            "_attribute_hash",
            sha2(concat_ws("||", *[coalesce(col(c), lit("")) for c in TRACKED_ATTRIBUTES]), 256)
        )
    
        df_current_hashed = df_current.withColumn(
            "_attribute_hash",
            sha2(concat_ws("||", *[coalesce(col(c), lit("")) for c in TRACKED_ATTRIBUTES]), 256)
        )
    
        # Find records that have changed
        df_changed = df_new_hashed.alias("new") \
            .join(df_current_hashed.alias("current"), KEY_COLUMN, "left") \
            .filter(
                (col("current.player_id").isNull()) |  # New player
                (col("new._attribute_hash") != col("current._attribute_hash"))  # Changed attributes
            ) \
            .select("new.*")
    
        changed_count = df_changed.count()
        print(f"Records to process (new + changed): {changed_count:,}")
    
        if changed_count > 0:
            # Get list of changed player IDs
            changed_ids = [row.player_id for row in df_changed.select("player_id").distinct().collect()]
    
            # Close current records for changed players
            silver_table.update(
                condition = (col("player_id").isin(changed_ids)) & (col("is_current") == True),
                set = {
                    "end_date": current_date(),
                    "is_current": lit(False)
                }
            )
    
            # Calculate next version number for each player
            df_versions = spark.sql(f"""
                SELECT player_id, COALESCE(MAX(version), 0) as max_version
                FROM {target_table}
                GROUP BY player_id
            """)
    
            # Add version numbers to new records
            df_to_insert = df_changed.drop("_attribute_hash") \
                .join(df_versions, "player_id", "left") \
                .withColumn("version", coalesce(col("max_version"), lit(0)) + 1) \
                .drop("max_version")
    
            # Insert new versions
            df_to_insert.write \
                .format("delta") \
                .mode("append") \
                .saveAsTable(target_table)
    
            print(f"Inserted {df_to_insert.count():,} new versions")
        else:
            print("No changes detected")
    
    else:
        print("Target table does not exist - performing initial load")
    
        # Initial load
        df_new.write \
            .format("delta") \
            .mode("overwrite") \
            .saveAsTable(target_table)
    
        print(f"Initial load: {df_new.count():,} records")
except Exception as e:
    print(f"ERROR in lh_silver.silver_player_master (batch_id={batch_id}): {e}")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validation

# COMMAND ----------

# Total records
total_records = spark.sql(f"SELECT COUNT(*) as total FROM {target_table}").first()["total"]
print(f"Total records in Silver: {total_records:,}")

# Current records
current_records = spark.sql(f"SELECT COUNT(*) as current FROM {target_table} WHERE is_current = True").first()["current"]
print(f"Current records: {current_records:,}")

# Historical records
historical_records = total_records - current_records
print(f"Historical records: {historical_records:,}")

# COMMAND ----------

# Players with multiple versions (showing SCD working)
spark.sql(f"""
    SELECT
        player_id,
        COUNT(*) as versions,
        MIN(effective_date) as first_record,
        MAX(effective_date) as last_record
    FROM {target_table}
    GROUP BY player_id
    HAVING COUNT(*) > 1
    ORDER BY versions DESC
    LIMIT 10
""").show()

# COMMAND ----------

# Sample of versioned records
spark.sql(f"""
    SELECT
        player_id,
        loyalty_tier,
        effective_date,
        end_date,
        is_current,
        version
    FROM {target_table}
    WHERE player_id IN (
        SELECT player_id
        FROM {target_table}
        GROUP BY player_id
        HAVING COUNT(*) > 1
        LIMIT 1
    )
    ORDER BY version
""").show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Summary

# COMMAND ----------

# Quality metrics on current records
spark.sql(f"""
    SELECT
        COUNT(*) as total_current,
        COUNT(email) as has_email,
        COUNT(phone) as has_phone,
        COUNT(address) as has_address,
        COUNT(loyalty_tier) as has_tier,
        COUNT(DISTINCT loyalty_tier) as unique_tiers
    FROM {target_table}
    WHERE is_current = True
""").show()

# Tier distribution
spark.sql(f"""
    SELECT
        loyalty_tier,
        COUNT(*) as players,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as pct
    FROM {target_table}
    WHERE is_current = True
    GROUP BY loyalty_tier
    ORDER BY players DESC
""").show()
