# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Layer: Slot Machine Data Cleansing
# MAGIC
# MAGIC This notebook transforms Bronze slot telemetry data into cleansed Silver layer tables.
# MAGIC
# MAGIC ## Transformations Applied:
# MAGIC - Schema enforcement and type casting
# MAGIC - Null handling and default values
# MAGIC - Data quality validation and scoring
# MAGIC - Deduplication
# MAGIC - Standardization of codes and formats

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

from pyspark.sql.functions import (
    array,
    array_compact,
    col,
    count,
    current_timestamp,
    filter,
    hour,
    initcap,
    lit,
    to_date,
    to_timestamp,
    trim,
    upper,
    when,
)
from pyspark.sql.types import (
    DateType,
    DecimalType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)
from datetime import datetime

# Parameters (set by pipeline or manual)
batch_id = dbutils.widgets.get("batch_id") if "batch_id" in [w.name for w in dbutils.widgets.getAll()] else datetime.now().strftime("%Y%m%d_%H%M%S")

# Source and target
source_table = "lh_bronze.bronze_slot_telemetry"
target_table = "lh_silver.silver_slot_cleansed"

print(f"Processing batch: {batch_id}")
print(f"Source: {source_table}")
print(f"Target: {target_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Read Bronze Data

# COMMAND ----------

df_bronze = spark.table(source_table)

print(f"Bronze records: {df_bronze.count():,}")
print(f"Columns: {df_bronze.columns}")
df_bronze.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define Target Schema

# COMMAND ----------

# Expected Silver schema with strict types
silver_schema = StructType([
    StructField("machine_id", StringType(), False),
    StructField("event_type", StringType(), False),
    StructField("event_timestamp", TimestampType(), False),
    StructField("event_date", DateType(), False),
    StructField("event_hour", IntegerType(), True),
    StructField("coin_in", DecimalType(18, 2), True),
    StructField("coin_out", DecimalType(18, 2), True),
    StructField("games_played", IntegerType(), True),
    StructField("jackpot_amount", DecimalType(18, 2), True),
    StructField("zone", StringType(), True),
    StructField("denomination", DecimalType(5, 2), True),
    StructField("manufacturer", StringType(), True),
    StructField("machine_type", StringType(), True),
    StructField("player_id", StringType(), True),
    StructField("session_id", StringType(), True)
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality Rules

# COMMAND ----------

# Define valid values
VALID_EVENT_TYPES = ["GAME_PLAY", "JACKPOT", "METER_UPDATE", "DOOR_OPEN", "DOOR_CLOSE",
                     "POWER_ON", "POWER_OFF", "BILL_IN", "TICKET_OUT", "TILT"]
VALID_ZONES = ["North", "South", "East", "West", "VIP", "High Limit", "Penny"]
VALID_DENOMINATIONS = [0.01, 0.05, 0.25, 0.50, 1.00, 2.00, 5.00, 10.00, 25.00, 100.00]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Apply Transformations

# COMMAND ----------

# Step 1: Filter out records with null required fields
df_filtered = df_bronze \
    .filter(col("machine_id").isNotNull()) \
    .filter(col("event_timestamp").isNotNull()) \
    .filter(col("event_type").isNotNull())

print(f"After null filter: {df_filtered.count():,}")

# COMMAND ----------

# Step 2: Type casting and standardization
df_typed = df_filtered \
    .withColumn("event_timestamp", to_timestamp("event_timestamp")) \
    .withColumn("event_date", to_date("event_timestamp")) \
    .withColumn("event_hour", hour("event_timestamp")) \
    .withColumn("coin_in", col("coin_in").cast(DecimalType(18, 2))) \
    .withColumn("coin_out", col("coin_out").cast(DecimalType(18, 2))) \
    .withColumn("games_played", col("games_played").cast(IntegerType())) \
    .withColumn("jackpot_amount", col("jackpot_amount").cast(DecimalType(18, 2))) \
    .withColumn("denomination", col("denomination").cast(DecimalType(5, 2)))

# COMMAND ----------

# Step 3: Handle negative values (data quality rule)
df_cleaned = df_typed \
    .withColumn("coin_in",
        when(col("coin_in") < 0, lit(0)).otherwise(col("coin_in"))) \
    .withColumn("coin_out",
        when(col("coin_out") < 0, lit(0)).otherwise(col("coin_out"))) \
    .withColumn("games_played",
        when(col("games_played") < 0, lit(0)).otherwise(col("games_played")))

# COMMAND ----------

# Step 4: Standardize codes and values
df_standardized = df_cleaned \
    .withColumn("event_type", upper(trim(col("event_type")))) \
    .withColumn("zone", initcap(trim(col("zone")))) \
    .withColumn("machine_id", upper(trim(col("machine_id"))))

# COMMAND ----------

# Step 5: Validate against reference data
df_validated = df_standardized \
    .withColumn("is_valid_event_type",
        col("event_type").isin(VALID_EVENT_TYPES)) \
    .withColumn("is_valid_zone",
        col("zone").isin(VALID_ZONES) | col("zone").isNull()) \
    .withColumn("is_valid_denomination",
        col("denomination").isin(VALID_DENOMINATIONS) | col("denomination").isNull())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Calculate Data Quality Score

# COMMAND ----------

# Data quality scoring (0-100)
df_with_dq = df_validated \
    .withColumn("_dq_score",
        (
            when(col("is_valid_event_type"), lit(20)).otherwise(lit(0)) +
            when(col("is_valid_zone"), lit(20)).otherwise(lit(0)) +
            when(col("is_valid_denomination"), lit(20)).otherwise(lit(0)) +
            when(col("coin_in").isNotNull(), lit(20)).otherwise(lit(0)) +
            when(col("player_id").isNotNull(), lit(20)).otherwise(lit(10))  # Partial credit
        )
    ) \
    .withColumn("_dq_flags",
        array_compact(
            array(
                when(~col("is_valid_event_type"), lit("INVALID_EVENT_TYPE")),
                when(~col("is_valid_zone") & col("zone").isNotNull(), lit("INVALID_ZONE")),
                when(~col("is_valid_denomination") & col("denomination").isNotNull(), lit("INVALID_DENOM")),
                when(col("coin_in").isNull(), lit("MISSING_COIN_IN"))
            )
        )
    )

# Drop validation columns
df_with_dq = df_with_dq.drop("is_valid_event_type", "is_valid_zone", "is_valid_denomination")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deduplication

# COMMAND ----------

# Deduplicate on natural key
df_deduped = df_with_dq.dropDuplicates(["machine_id", "event_timestamp", "event_type"])

print(f"After deduplication: {df_deduped.count():,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Add Silver Metadata

# COMMAND ----------

df_silver = df_deduped \
    .withColumn("_silver_timestamp", current_timestamp()) \
    .withColumn("_batch_id", lit(batch_id))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write to Silver Table

# COMMAND ----------

# Select final columns
try:
    final_columns = [
        "machine_id", "event_type", "event_timestamp", "event_date", "event_hour",
        "coin_in", "coin_out", "games_played", "jackpot_amount",
        "zone", "denomination", "manufacturer", "machine_type",
        "player_id", "session_id",
        "_dq_score", "_dq_flags", "_silver_timestamp", "_batch_id"
    ]
    
    df_final = df_silver.select([col(c) for c in final_columns if c in df_silver.columns])
    
    # Write to Silver layer
    df_final.write \
        .format("delta") \
        .mode("overwrite") \
        .partitionBy("event_date") \
        .option("overwriteSchema", "true") \
        .saveAsTable(target_table)
    
    print(f"Written {df_final.count():,} records to {target_table}")
except Exception as e:
    print(f"ERROR in lh_silver.silver_slot_cleansed (batch_id={batch_id}): {e}")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validation

# COMMAND ----------

# Verify write
spark.sql(f"SELECT COUNT(*) as total FROM {target_table}").show()

# Data quality summary
spark.sql(f"""
    SELECT
        ROUND(AVG(_dq_score), 2) as avg_quality_score,
        COUNT(CASE WHEN _dq_score = 100 THEN 1 END) as perfect_records,
        COUNT(CASE WHEN _dq_score < 60 THEN 1 END) as low_quality_records
    FROM {target_table}
""").show()

# Quality by zone
spark.sql(f"""
    SELECT
        zone,
        COUNT(*) as records,
        ROUND(AVG(_dq_score), 2) as avg_quality
    FROM {target_table}
    GROUP BY zone
    ORDER BY avg_quality DESC
""").show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Optimize Table

# COMMAND ----------

spark.sql(f"OPTIMIZE {target_table} ZORDER BY (machine_id)")
print("Table optimized with Z-Order on machine_id")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Lakehouse Schemas (GA Dec 2025)
# MAGIC
# MAGIC Fabric Lakehouse now supports **schema-based table organization** (GA).
# MAGIC Instead of flat Lakehouse-qualified naming (`lh_silver.silver_slot_cleansed`),
# MAGIC tables can be organized into schemas for better discovery, access control,
# MAGIC and multi-domain isolation.
# MAGIC
# MAGIC ### Schema Pattern (Alternative to flat naming)
# MAGIC ```
# MAGIC Flat naming:   lh_silver.silver_slot_cleansed
# MAGIC Schema naming:  lh_silver.casino.silver_slot_cleansed
# MAGIC ```
# MAGIC
# MAGIC To adopt schemas, create the schema first, then save tables into it.
# MAGIC Both patterns coexist -- existing flat-named tables remain accessible.

# COMMAND ----------

# --- Lakehouse Schema Pattern (Optional, GA Dec 2025) ---
# Uncomment the following to organize Silver tables within Lakehouse schemas.
# This enables domain-based table isolation and finer-grained access control.
#
# Create schema (idempotent):
# spark.sql("CREATE SCHEMA IF NOT EXISTS casino")
#
# Write to schema-qualified table:
# df_final.write \
#     .format("delta") \
#     .mode("overwrite") \
#     .option("overwriteSchema", "true") \
#     .saveAsTable("casino.silver_slot_cleansed")
#
# For federal agency isolation:
# spark.sql("CREATE SCHEMA IF NOT EXISTS usda")
# spark.sql("CREATE SCHEMA IF NOT EXISTS noaa")
# spark.sql("CREATE SCHEMA IF NOT EXISTS epa")
# spark.sql("CREATE SCHEMA IF NOT EXISTS doi")
# spark.sql("CREATE SCHEMA IF NOT EXISTS sba")
#
# Schema-based access control:
# GRANT SELECT ON SCHEMA casino TO `casino-analysts@contoso.com`
# GRANT SELECT ON SCHEMA usda TO `usda-data-team@contoso.com`

print("Lakehouse Schema pattern available (see comments above)")
print("Current table uses flat naming for backward compatibility")
