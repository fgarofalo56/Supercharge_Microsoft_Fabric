# Cheat Sheets

> **Last Updated**: 2026-04-27 | **Version**: 1.0
> **Status**: Active | **Maintainer**: Engineering Team

Quick-reference cheat sheets for the four primary languages used in this POC: PySpark, KQL, T-SQL, and DAX. Each section is organized for fast lookup during development.

---

## PySpark + Fabric Cheat Sheet

### Read/Write Operations

```python
# ---- Delta Lake (primary format) ----

# Read Delta table by name (default Lakehouse)
df = spark.table("bronze_slot_telemetry")

# Read Delta table by path
df = spark.read.format("delta").load("Tables/bronze_slot_telemetry")

# Write Delta table (overwrite)
df.write.format("delta").mode("overwrite").saveAsTable("silver_slot_cleansed")

# Write Delta table (append)
df.write.format("delta").mode("append").saveAsTable("bronze_slot_telemetry")

# Write with schema evolution
df.write.format("delta").mode("append") \
    .option("mergeSchema", "true") \
    .saveAsTable("bronze_slot_telemetry")

# Write with V-Order (required for Direct Lake performance)
spark.conf.set("spark.sql.parquet.vorder.enabled", "true")
df.write.format("delta").mode("overwrite").saveAsTable("gold_slot_performance")

# ---- Parquet (landing zone) ----

# Read Parquet from Files section
df = spark.read.parquet("Files/landing/slot_telemetry/*.parquet")

# Read with explicit schema
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
schema = StructType([
    StructField("event_id", StringType(), False),
    StructField("amount", DoubleType(), True)
])
df = spark.read.schema(schema).parquet("Files/landing/data.parquet")

# ---- CSV ----
df = spark.read.option("header", "true").option("inferSchema", "true").csv("Files/landing/data.csv")

# ---- JSON ----
df = spark.read.option("multiline", "true").json("Files/landing/data.json")
```

### Schema Enforcement

```python
# Check schema
df.printSchema()
df.dtypes  # List of (column_name, type_string) tuples

# Cast columns
from pyspark.sql.functions import col
df = df.withColumn("amount", col("amount").cast("double"))

# Drop columns
df = df.drop("unwanted_column")

# Rename columns
df = df.withColumnRenamed("old_name", "new_name")

# Add NOT NULL constraint (Delta)
spark.sql("ALTER TABLE silver_financial ADD CONSTRAINT amount_nn CHECK (amount IS NOT NULL)")

# Add CHECK constraint
spark.sql("ALTER TABLE silver_financial ADD CONSTRAINT amount_pos CHECK (amount >= 0)")
```

### Common Transformations

```python
from pyspark.sql.functions import (
    col, lit, when, coalesce, concat, upper, lower, trim,
    year, month, dayofmonth, hour, date_format, current_timestamp,
    sum, avg, count, min, max, countDistinct,
    row_number, rank, dense_rank, lag, lead,
    explode, arrays_zip, from_json, to_json,
    sha2, md5, regexp_replace,
    broadcast
)
from pyspark.sql.window import Window

# ---- Filtering ----
df = df.filter(col("amount") > 10000)                   # CTR threshold
df = df.filter(col("event_date").between("2025-01-01", "2025-12-31"))

# ---- Window Functions ----
window_spec = Window.partitionBy("player_id").orderBy(col("event_ts").desc())
df = df.withColumn("row_num", row_number().over(window_spec))           # Dedup
df = df.withColumn("prev_amount", lag("amount", 1).over(window_spec))   # Previous value
df = df.withColumn("running_total", sum("amount").over(
    Window.partitionBy("player_id").orderBy("event_ts").rowsBetween(Window.unboundedPreceding, 0)
))

# ---- Pivot ----
pivot_df = df.groupBy("property_id").pivot("game_type").agg(sum("amount"))

# ---- Explode (flatten arrays) ----
df = df.withColumn("tag", explode(col("tags")))

# ---- UDF (use sparingly -- prefer built-in functions) ----
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType

@udf(returnType=StringType())
def mask_ssn(ssn):
    return f"XXX-XX-{ssn[-4:]}" if ssn and len(ssn) >= 4 else None

df = df.withColumn("masked_ssn", mask_ssn(col("ssn")))

# ---- MERGE / Upsert (Delta) ----
from delta.tables import DeltaTable

target = DeltaTable.forName(spark, "silver_player_master")
target.alias("t").merge(
    source_df.alias("s"),
    "t.player_id = s.player_id"
).whenMatchedUpdate(set={
    "name": "s.name",
    "tier": "s.tier",
    "updated_at": "s.updated_at"
}).whenNotMatchedInsertAll().execute()

# ---- Optimize / Vacuum ----
spark.sql("OPTIMIZE gold_slot_performance ZORDER BY (property_id, event_date)")
spark.sql("OPTIMIZE gold_slot_performance USING VORDER")
spark.sql("VACUUM gold_slot_performance RETAIN 168 HOURS")
```

### mssparkutils Commands

```python
# ---- File System ----
mssparkutils.fs.ls("Files/landing/")                     # List files
mssparkutils.fs.mkdirs("Files/archive/2025/")            # Create directory
mssparkutils.fs.cp("Files/a.parquet", "Files/b.parquet")  # Copy file
mssparkutils.fs.mv("Files/a.parquet", "Files/archive/")   # Move file
mssparkutils.fs.rm("Files/temp/", True)                   # Delete recursively
mssparkutils.fs.head("Files/config.json", 1000)           # Read first 1000 bytes

# ---- Notebook Orchestration ----
mssparkutils.notebook.run("01_bronze_slot_telemetry", timeout_seconds=600,
                          arguments={"batch_date": "2025-01-15"})

# Run multiple notebooks in parallel
mssparkutils.notebook.runMultiple([
    {"notebook": "01_bronze_slot_telemetry", "args": {"batch_date": "2025-01-15"}},
    {"notebook": "02_bronze_player_profile", "args": {"batch_date": "2025-01-15"}}
])

# Exit notebook with value (for pipeline return)
mssparkutils.notebook.exit("SUCCESS")

# ---- Credentials ----
token = mssparkutils.credentials.getToken("storage")      # Get access token
secret = mssparkutils.credentials.getSecret("kv-name", "secret-name")  # Key Vault

# ---- Lakehouse ----
mssparkutils.lakehouse.list()                              # List Lakehouses
mssparkutils.lakehouse.get("lh_bronze")                    # Get Lakehouse details
```

### Spark Configuration for Fabric

```python
# ---- Performance Tuning ----
spark.conf.set("spark.sql.shuffle.partitions", "8")             # POC scale (default 200)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "10485760")  # 10 MB
spark.conf.set("spark.sql.adaptive.enabled", "true")            # AQE (default in Fabric)
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")

# ---- V-Order for Direct Lake ----
spark.conf.set("spark.sql.parquet.vorder.enabled", "true")

# ---- Delta Lake ----
spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")

# ---- Memory ----
spark.conf.set("spark.driver.maxResultSize", "2g")              # Limit driver result size
```

---

## KQL Essentials

### Common Operators

```kql
// ---- Filter ----
SlotTelemetry
| where EventTimestamp > ago(1h)
| where PropertyId == "PROP-001"
| where Amount > 10000

// ---- Project (select columns) ----
SlotTelemetry
| project EventTimestamp, MachineId, Amount, GameType

// ---- Extend (add calculated columns) ----
SlotTelemetry
| extend HourOfDay = hourofday(EventTimestamp)
| extend IsHighValue = Amount > 1000

// ---- Summarize (aggregate) ----
SlotTelemetry
| summarize
    TotalCoinIn = sum(CoinIn),
    AvgBet = avg(BetAmount),
    EventCount = count(),
    UniquePlayersCount = dcount(PlayerId)
    by PropertyId, bin(EventTimestamp, 1h)

// ---- Join ----
SlotTelemetry
| join kind=inner (
    PlayerProfiles | project PlayerId, Tier, LTV
) on PlayerId
| where Tier == "Platinum"

// ---- Sort and Limit ----
SlotTelemetry
| top 100 by Amount desc

// ---- Render (visualization) ----
SlotTelemetry
| summarize TotalCoinIn = sum(CoinIn) by bin(EventTimestamp, 1h)
| render timechart
```

### Time Series

```kql
// ---- Make-Series (create time series) ----
SlotTelemetry
| make-series AvgCoinIn = avg(CoinIn) default=0
    on EventTimestamp
    from ago(7d) to now() step 1h
    by PropertyId

// ---- Series Decompose (trend + seasonal + residual) ----
SlotTelemetry
| make-series CoinIn = sum(CoinIn) on EventTimestamp from ago(30d) to now() step 1h
| extend (Trend, Seasonal, Residual) = series_decompose(CoinIn)
| render timechart

// ---- Anomaly Detection ----
SlotTelemetry
| make-series CoinIn = sum(CoinIn) on EventTimestamp from ago(7d) to now() step 1h
| extend (Anomalies, Score, Baseline) = series_decompose_anomalies(CoinIn, 2.5)
| mv-expand EventTimestamp to typeof(datetime), CoinIn to typeof(double),
            Anomalies to typeof(int), Score to typeof(double)
| where Anomalies != 0

// ---- Sliding Window Aggregation ----
SlotTelemetry
| summarize CoinIn = sum(CoinIn) by bin(EventTimestamp, 5m), MachineId
| serialize
| extend RollingAvg = series_fir(CoinIn, repeat(1, 12), true, true)  // 1-hour rolling
```

### Materialized Views and Update Policies

```kql
// ---- Materialized View (pre-aggregated) ----
.create materialized-view HourlyCoinIn on table SlotTelemetry {
    SlotTelemetry
    | summarize TotalCoinIn = sum(CoinIn), EventCount = count()
        by PropertyId, MachineId, bin(EventTimestamp, 1h)
}

// ---- Update Policy (ETL on ingest) ----
// Transform raw data as it arrives in the source table
.alter table SlotTelemetryEnriched policy update @'[{
    "IsEnabled": true,
    "Source": "SlotTelemetryRaw",
    "Query": "SlotTelemetryRaw | extend HourOfDay = hourofday(EventTimestamp), IsWeekend = dayofweek(EventTimestamp) > 4",
    "IsTransactional": true
}]'

// ---- Retention Policy ----
.alter table SlotTelemetry policy retention softdelete = 90d recoverability = disabled
```

### Eventhouse-Specific Patterns

```kql
// ---- Streaming Ingestion ----
.alter table SlotTelemetry policy streamingingestion enable

// ---- Query external Delta tables (shortcut) ----
external_table("OneLake_SlotTelemetry")
| where event_date > ago(7d)
| summarize count() by property_id

// ---- Cross-database query ----
database("ComplianceRealTime").CTRAlerts
| join kind=inner (
    database("PlayerAnalytics").PlayerProfiles
) on player_id
```

---

## T-SQL Fabric Quirks

### Lakehouse SQL Endpoint (Read-Only)

```sql
-- The Lakehouse SQL endpoint is READ-ONLY. No INSERT/UPDATE/DELETE.

-- Supported: SELECT queries
SELECT TOP 100 event_id, amount, event_date
FROM lh_bronze.dbo.bronze_slot_telemetry
WHERE event_date >= '2025-01-01'
ORDER BY amount DESC;

-- Supported: Cross-database queries (within same workspace)
SELECT b.event_id, s.quality_score
FROM lh_bronze.dbo.bronze_slot_telemetry b
JOIN lh_silver.dbo.silver_slot_cleansed s ON b.event_id = s.event_id;

-- NOT supported in Lakehouse SQL endpoint:
-- INSERT, UPDATE, DELETE, MERGE
-- CREATE TABLE, ALTER TABLE
-- Stored procedures, functions, triggers
-- Temp tables (#temp)
-- CTEs with INSERT (CTE SELECTs are fine)
```

### Warehouse T-SQL

```sql
-- Full DML support in Warehouse

-- COPY INTO (high-performance bulk load)
COPY INTO dbo.staging_slot_telemetry
FROM 'https://storage.blob.core.windows.net/landing/slot_telemetry/*.parquet'
WITH (
    FILE_TYPE = 'PARQUET',
    CREDENTIAL = (IDENTITY = 'Managed Identity')
);

-- CTAS (Create Table As Select)
CREATE TABLE dbo.gold_daily_revenue
AS
SELECT
    CAST(event_date AS DATE) AS report_date,
    property_id,
    SUM(coin_in) AS total_coin_in,
    SUM(coin_out) AS total_coin_out,
    SUM(coin_in) - SUM(coin_out) AS net_revenue
FROM dbo.silver_slot_cleansed
GROUP BY CAST(event_date AS DATE), property_id;

-- Cross-database queries (within workspace)
SELECT w.*, l.additional_column
FROM my_warehouse.dbo.fact_table w
JOIN my_lakehouse.dbo.dim_table l ON w.key = l.key;

-- Limitations vs. SQL Server:
-- No linked servers
-- No cross-workspace queries
-- No SQL Agent jobs (use Pipelines instead)
-- No Always Encrypted
-- No FILESTREAM
```

### SQL Database T-SQL (Full Engine)

```sql
-- Full SQL Server engine with CRUD, stored procs, triggers

-- Change Tracking (for downstream CDC)
ALTER DATABASE CURRENT SET CHANGE_TRACKING = ON
    (CHANGE_RETENTION = 7 DAYS, AUTO_CLEANUP = ON);

ALTER TABLE dbo.player_profile ENABLE CHANGE_TRACKING;

-- Query changes since last sync
DECLARE @last_version BIGINT = 42;
SELECT ct.player_id, ct.SYS_CHANGE_OPERATION, p.*
FROM CHANGETABLE(CHANGES dbo.player_profile, @last_version) AS ct
LEFT JOIN dbo.player_profile p ON ct.player_id = p.player_id;

-- Stored Procedures (supported in SQL Database, NOT in Lakehouse/Warehouse)
CREATE PROCEDURE dbo.usp_UpdatePlayerTier
    @PlayerId NVARCHAR(50),
    @NewTier NVARCHAR(20)
AS
BEGIN
    UPDATE dbo.player_profile
    SET tier = @NewTier, updated_at = GETUTCDATE()
    WHERE player_id = @PlayerId;
END;

-- Triggers (supported)
CREATE TRIGGER trg_AuditPlayerChanges ON dbo.player_profile
AFTER UPDATE
AS
BEGIN
    INSERT INTO dbo.audit_log (table_name, operation, changed_at, old_values)
    SELECT 'player_profile', 'UPDATE', GETUTCDATE(),
           (SELECT * FROM DELETED FOR JSON AUTO);
END;
```

### Feature Comparison Quick Reference

| Feature | Lakehouse SQL EP | Warehouse | SQL Database |
|---|:---:|:---:|:---:|
| SELECT | Yes | Yes | Yes |
| INSERT/UPDATE/DELETE | No | Yes | Yes |
| COPY INTO | No | Yes | No |
| CTAS | No | Yes | Yes |
| Stored Procedures | No | No | Yes |
| Triggers | No | No | Yes |
| Change Tracking/CDC | No | No | Yes |
| Cross-Database Query | Yes | Yes | Yes |
| Temp Tables | No | Yes | Yes |
| Views | No | Yes | Yes |
| Direct Lake | Native | Via shortcut | Via mirroring |

---

## DAX Patterns

### Time Intelligence

```dax
// ---- Year-to-Date ----
Revenue YTD =
TOTALYTD(SUM(gold_financial_summary[net_revenue]), 'Calendar'[Date])

// ---- Quarter-to-Date ----
Revenue QTD =
TOTALQTD(SUM(gold_financial_summary[net_revenue]), 'Calendar'[Date])

// ---- Month-to-Date ----
Revenue MTD =
TOTALMTD(SUM(gold_financial_summary[net_revenue]), 'Calendar'[Date])

// ---- Rolling 12 Months ----
Revenue Rolling 12M =
CALCULATE(
    SUM(gold_financial_summary[net_revenue]),
    DATESINPERIOD('Calendar'[Date], MAX('Calendar'[Date]), -12, MONTH)
)

// ---- Same Period Last Year ----
Revenue SPLY =
CALCULATE(
    SUM(gold_financial_summary[net_revenue]),
    SAMEPERIODLASTYEAR('Calendar'[Date])
)

// ---- Year-over-Year Growth ----
YoY Growth % =
VAR CurrentYear = SUM(gold_financial_summary[net_revenue])
VAR PriorYear = [Revenue SPLY]
RETURN
IF(PriorYear <> 0, DIVIDE(CurrentYear - PriorYear, PriorYear), BLANK())
```

### Direct Lake Specific

```dax
// ---- Fallback Prevention ----
// Avoid calculated tables (causes DQ fallback)
// BAD:  CalcTable = SUMMARIZE(FactTable, Dim[Column], "Total", SUM(FactTable[Amount]))
// GOOD: Pre-aggregate in Gold notebook, write as Delta table

// ---- Cardinality Hints ----
// High-cardinality columns (>10M unique values) can cause fallback.
// Reduce cardinality by bucketing in Gold layer:
//   df = df.withColumn("amount_bucket", (col("amount") / 100).cast("int") * 100)

// ---- Safe Measures (avoid DQ fallback) ----
Total Coin In = SUM(gold_slot_performance[total_coin_in])          // Safe
Avg Hold Pct  = AVERAGE(gold_slot_performance[hold_percentage])     // Safe
Player Count  = DISTINCTCOUNT(gold_player_360[player_id])           // Safe

// ---- Check for Fallback in DAX query ----
// Use Performance Analyzer in Power BI Desktop:
//   View > Performance Analyzer > Start Recording > Refresh Visuals
//   Look for "Direct Query" in the trace (indicates fallback)
```

### Common Measures

```dax
// ---- Running Total ----
Running Total Revenue =
CALCULATE(
    SUM(gold_financial_summary[net_revenue]),
    FILTER(
        ALL('Calendar'[Date]),
        'Calendar'[Date] <= MAX('Calendar'[Date])
    )
)

// ---- Rank ----
Property Revenue Rank =
RANKX(
    ALL(gold_slot_performance[property_id]),
    [Total Coin In],
    ,
    DESC,
    Dense
)

// ---- Percentage of Parent ----
Revenue % of Total =
DIVIDE(
    SUM(gold_financial_summary[net_revenue]),
    CALCULATE(SUM(gold_financial_summary[net_revenue]), ALL(gold_financial_summary[property_id]))
)

// ---- Moving Average ----
7-Day Moving Avg Revenue =
AVERAGEX(
    DATESINPERIOD('Calendar'[Date], MAX('Calendar'[Date]), -7, DAY),
    CALCULATE(SUM(gold_financial_summary[net_revenue]))
)

// ---- Casino-Specific: Theoretical Win ----
Theoretical Win =
SUMX(
    gold_slot_performance,
    gold_slot_performance[total_coin_in] * gold_slot_performance[hold_percentage]
)

// ---- Casino-Specific: Actual vs Theoretical ----
Actual vs Theo % =
DIVIDE(
    SUM(gold_slot_performance[total_coin_in]) - SUM(gold_slot_performance[total_coin_out]),
    [Theoretical Win]
)

// ---- Compliance: CTR Count ----
CTR Count =
CALCULATE(
    COUNTROWS(gold_compliance_reporting),
    gold_compliance_reporting[report_type] = "CTR"
)

// ---- Conditional Formatting Helper ----
Revenue Color =
SWITCH(
    TRUE(),
    [YoY Growth %] >= 0.10, "#2ECC71",   // Green: >10% growth
    [YoY Growth %] >= 0,    "#F39C12",   // Yellow: 0-10% growth
    "#E74C3C"                              // Red: decline
)
```

---

## See Also

- [Tutorials Cheat Sheet](tutorials/CHEAT_SHEET.md) -- POC-specific command reference
- [PySpark Notebooks](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/tree/main/notebooks) -- Working code examples
- [KQL Queries](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/blob/main/notebooks/real-time/02_kql_casino_floor.kql) -- Casino floor KQL
- [Power BI Best Practices](best-practices/power-bi-best-practices.md) -- DAX guidance
- [Direct Lake](features/direct-lake.md) -- Direct Lake guardrails and optimization

---

[Back to Docs](index.md) | [Decision Trees](DECISION_TREES.md) | [Troubleshooting](TROUBLESHOOTING_MATRIX.md)
