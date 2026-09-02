# 🎰 Casino Analytics Cheat Sheet

> **Printable Quick Reference** | Microsoft Fabric POC

---

## 📊 PySpark Commands

### Reading & Writing Data

| Operation | Command |
|-----------|---------|
| **Read Delta** | `df = spark.read.format("delta").load("Tables/bronze_slot_telemetry")` |
| **Read CSV** | `df = spark.read.option("header", True).csv("Files/raw/players.csv")` |
| **Read JSON** | `df = spark.read.json("Files/raw/events/*.json")` |
| **Write Delta** | `df.write.format("delta").mode("overwrite").save("Tables/silver_player")` |
| **Append Delta** | `df.write.format("delta").mode("append").save("Tables/bronze_txn")` |

### Common Transformations

```python
# Filter high-value transactions
df.filter(col("amount") >= 10000)

# Select & rename columns
df.select(col("player_id"), col("amount").alias("wager_amount"))

# Group and aggregate
df.groupBy("casino_id", "game_type").agg(
    sum("amount").alias("total_wagered"),
    count("*").alias("transaction_count"),
    avg("amount").alias("avg_wager")
)

# Window functions (player ranking)
from pyspark.sql.window import Window
window = Window.partitionBy("casino_id").orderBy(desc("total_wagered"))
df.withColumn("rank", rank().over(window))

# Date extraction
df.withColumn("play_date", to_date(col("timestamp")))
df.withColumn("play_hour", hour(col("timestamp")))

# Join tables
players.join(transactions, "player_id", "left")
```

### Data Quality Checks

```python
# Count nulls per column
df.select([count(when(col(c).isNull(), c)).alias(c) for c in df.columns])

# Distinct counts
df.select(countDistinct("player_id").alias("unique_players"))

# Check for duplicates
df.groupBy("transaction_id").count().filter(col("count") > 1)
```

---

## 🔷 Delta Lake Operations

### MERGE (Upsert Pattern)

```python
from delta.tables import DeltaTable

target = DeltaTable.forPath(spark, "Tables/silver_player_profile")
source = spark.read.format("delta").load("Tables/bronze_player")

target.alias("t").merge(
    source.alias("s"),
    "t.player_id = s.player_id"
).whenMatchedUpdate(set={
    "email": "s.email",
    "tier_status": "s.tier_status",
    "updated_at": "current_timestamp()"
}).whenNotMatchedInsertAll().execute()
```

### Common Delta Operations

| Operation | Command |
|-----------|---------|
| **Optimize** | `spark.sql("OPTIMIZE silver_player_profile")` |
| **Z-Order** | `spark.sql("OPTIMIZE bronze_txn ZORDER BY (player_id, timestamp)")` |
| **Vacuum** | `spark.sql("VACUUM silver_player_profile RETAIN 168 HOURS")` |
| **History** | `spark.sql("DESCRIBE HISTORY silver_player_profile")` |
| **Time Travel** | `spark.read.option("versionAsOf", 5).format("delta").load(...)` |
| **Schema Evolution** | `df.write.option("mergeSchema", True).format("delta").mode("append")...` |

### SCD Type 2 Pattern

```python
# Add audit columns for slowly changing dimensions
df.withColumn("effective_from", current_timestamp()) \
  .withColumn("effective_to", lit(None).cast("timestamp")) \
  .withColumn("is_current", lit(True))
```

---

## 🏅 Medallion Architecture Patterns

### Bronze Layer (Raw Ingestion)

```python
# Append-only, minimal transformation
df_raw = spark.read.json("Files/raw/slot_events/")

df_bronze = df_raw \
    .withColumn("_ingested_at", current_timestamp()) \
    .withColumn("_source_file", input_file_name())

df_bronze.write.format("delta") \
    .mode("append") \
    .option("mergeSchema", True) \
    .save("Tables/bronze_slot_telemetry")
```

### Silver Layer (Cleansed & Validated)

```python
# Schema enforcement, deduplication, null handling
df_silver = spark.read.format("delta").load("Tables/bronze_slot_telemetry") \
    .filter(col("player_id").isNotNull()) \
    .dropDuplicates(["transaction_id"]) \
    .withColumn("amount", col("amount").cast("decimal(18,2)")) \
    .withColumn("player_id", upper(trim(col("player_id"))))

df_silver.write.format("delta") \
    .mode("overwrite") \
    .save("Tables/silver_slot_activity")
```

### Gold Layer (Aggregations & KPIs)

```python
# Business-level aggregations
df_gold = spark.read.format("delta").load("Tables/silver_slot_activity") \
    .groupBy("casino_id", "game_type", to_date("timestamp").alias("play_date")) \
    .agg(
        sum("amount").alias("total_wagered"),
        sum("win_amount").alias("total_payouts"),
        countDistinct("player_id").alias("unique_players"),
        count("*").alias("total_spins")
    ) \
    .withColumn("hold_percentage", 
        (col("total_wagered") - col("total_payouts")) / col("total_wagered") * 100)

df_gold.write.format("delta") \
    .mode("overwrite") \
    .save("Tables/gold_daily_gaming_summary")
```

---

## 📡 KQL Queries (Real-Time Analytics)

### Common Queries

```kql
// Last 15 minutes of slot activity
SlotTelemetry
| where ingestion_time() > ago(15m)
| summarize SpinCount = count(), TotalWagered = sum(Amount) by CasinoId
| order by TotalWagered desc

// Jackpot alerts (wins > $10,000)
SlotTelemetry
| where EventType == "WIN" and Amount >= 10000
| project Timestamp, MachineId, PlayerId, Amount
| order by Amount desc

// Player session analysis
SlotTelemetry
| where PlayerId == "PLR-12345"
| summarize 
    SessionStart = min(Timestamp),
    SessionEnd = max(Timestamp),
    TotalWagered = sum(Amount),
    Spins = count()
| extend SessionDuration = SessionEnd - SessionStart

// Anomaly detection (unusual betting patterns)
SlotTelemetry
| where ingestion_time() > ago(1h)
| summarize AvgBet = avg(Amount), StdDev = stdev(Amount) by PlayerId
| where AvgBet > 500 or StdDev > 200

// CTR candidates (approaching $10,000 threshold)
FinancialTransactions
| where TransactionType in ("CASH_IN", "CHIP_PURCHASE")
| where ingestion_time() > ago(24h)
| summarize DailyTotal = sum(Amount) by PlayerId
| where DailyTotal >= 8000 and DailyTotal < 10000
| order by DailyTotal desc
```

### Time Intelligence

```kql
// Hourly trend comparison
SlotTelemetry
| where Timestamp > ago(7d)
| summarize HourlyRevenue = sum(Amount) by bin(Timestamp, 1h), CasinoId
| render timechart

// Day-over-day comparison  
SlotTelemetry
| summarize Today = sumif(Amount, Timestamp > ago(1d)),
            Yesterday = sumif(Amount, Timestamp between (ago(2d) .. ago(1d)))
| extend Change = round((Today - Yesterday) / Yesterday * 100, 2)
```

---

## 📈 DAX Measures (Power BI)

### Core Gaming Metrics

```dax
// Total Gaming Revenue (GGR)
GGR = SUM(gold_daily_gaming[total_wagered]) - SUM(gold_daily_gaming[total_payouts])

// Hold Percentage
Hold % = DIVIDE([GGR], SUM(gold_daily_gaming[total_wagered]), 0) * 100

// Theoretical Win
Theoretical Win = SUM(gold_daily_gaming[total_wagered]) * 0.08  // 8% house edge

// Win/Loss Variance
Win Variance = [GGR] - [Theoretical Win]

// Active Players (last 30 days)
Active Players = CALCULATE(
    DISTINCTCOUNT(silver_player_activity[player_id]),
    DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -30, DAY)
)

// Average Daily Theoretical (ADT)
ADT = DIVIDE(
    SUM(silver_player_activity[theoretical_win]),
    DISTINCTCOUNT(silver_player_activity[play_date]),
    0
)
```

### Time Intelligence

```dax
// YTD Revenue
YTD Revenue = TOTALYTD(SUM(gold_daily_gaming[total_wagered]), dim_date[date])

// Same Period Last Year
SPLY Revenue = CALCULATE(
    SUM(gold_daily_gaming[total_wagered]),
    SAMEPERIODLASTYEAR(dim_date[date])
)

// YoY Growth %
YoY Growth = DIVIDE([GGR] - [SPLY Revenue], [SPLY Revenue], 0) * 100

// Rolling 7-Day Average
7-Day Avg Revenue = AVERAGEX(
    DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -7, DAY),
    [GGR]
)
```

---

## 🔒 Compliance Thresholds

| Regulation | Threshold | Trigger |
|------------|-----------|---------|
| **CTR** (Currency Transaction Report) | **$10,000** | Single or aggregated cash transactions in 24 hours |
| **SAR** (Suspicious Activity Report) | **$5,000+** | Pattern of transactions designed to evade CTR |
| **Structuring Alert** | **$8,000-$9,999** | Multiple transactions just below CTR threshold |
| **W-2G (Slots)** | **$1,200** | Single jackpot win |
| **W-2G (Keno)** | **$600** | Single keno win |
| **W-2G (Table Games)** | **$5,000** | Poker tournament win (300:1 odds) |
| **W-2G (Bingo)** | **$1,200** | Single bingo win |

### Compliance Query Examples

```python
# CTR candidates
df.filter(col("amount") >= 10000) \
  .filter(col("transaction_type").isin("CASH_IN", "CHIP_PURCHASE"))

# Structuring detection (24-hour rolling)
from pyspark.sql.window import Window
window_24h = Window.partitionBy("player_id").orderBy("timestamp").rangeBetween(-86400, 0)
df.withColumn("rolling_24h_total", sum("amount").over(window_24h)) \
  .filter((col("rolling_24h_total") >= 8000) & (col("rolling_24h_total") < 10000))

# W-2G qualifying wins
df.filter(
    ((col("game_type") == "SLOT") & (col("win_amount") >= 1200)) |
    ((col("game_type") == "KENO") & (col("win_amount") >= 1500)) |
    ((col("game_type") == "POKER") & (col("win_amount") >= 5000))
)
```

---

## 📁 Table Reference by Layer

### Bronze Tables (Raw)

| Table Name | Description | Key Columns |
|------------|-------------|-------------|
| `bronze_slot_telemetry` | Slot machine events | `machine_id`, `event_type`, `amount`, `timestamp` |
| `bronze_player_profile` | Player master data | `player_id`, `first_name`, `tier_status` |
| `bronze_financial_txn` | Cash/chip transactions | `transaction_id`, `player_id`, `amount`, `type` |
| `bronze_table_games` | Table game activity | `table_id`, `game_type`, `hand_result` |
| `bronze_compliance` | AML/CTR events | `report_type`, `player_id`, `amount` |
| `bronze_security_events` | Access/surveillance logs | `event_type`, `location`, `timestamp` |

### Silver Tables (Cleansed)

| Table Name | Description | Grain |
|------------|-------------|-------|
| `silver_player_activity` | Player gaming sessions | One row per session |
| `silver_slot_spins` | Validated slot events | One row per spin |
| `silver_transactions` | Cleansed financials | One row per transaction |
| `silver_player_360` | Player unified view | One row per player |

### Gold Tables (Aggregations)

| Table Name | Description | Grain |
|------------|-------------|-------|
| `gold_daily_gaming_summary` | Daily KPIs by venue/game | Casino + GameType + Date |
| `gold_player_value` | Player lifetime metrics | One row per player |
| `gold_hourly_floor_status` | Real-time floor metrics | Casino + Hour |
| `gold_compliance_summary` | Regulatory metrics | Date + Report Type |

---

## 🔧 Troubleshooting Commands

### Spark/Notebook Issues

```python
# Check available tables
spark.catalog.listTables("bronze")

# View table schema
spark.read.format("delta").load("Tables/bronze_slot_telemetry").printSchema()

# Check file counts
mssparkutils.fs.ls("Tables/bronze_slot_telemetry")

# Clear cache
spark.catalog.clearCache()

# Check executor memory
spark.sparkContext.getConf().get("spark.executor.memory")
```

### Delta Table Diagnostics

```python
# Check table history
spark.sql("DESCRIBE HISTORY bronze_slot_telemetry LIMIT 10").show()

# Check table details
spark.sql("DESCRIBE DETAIL bronze_slot_telemetry").show()

# Count files (detect small file problem)
spark.sql("DESCRIBE DETAIL bronze_slot_telemetry") \
    .select("numFiles", "sizeInBytes").show()

# Repair corrupt table
spark.sql("FSCK REPAIR TABLE bronze_slot_telemetry")
```

### Performance Optimization

```python
# Optimize table (compact small files)
spark.sql("OPTIMIZE bronze_slot_telemetry")

# Add Z-ORDER for common filters
spark.sql("OPTIMIZE silver_player_activity ZORDER BY (player_id, play_date)")

# Analyze table statistics
spark.sql("ANALYZE TABLE gold_daily_gaming_summary COMPUTE STATISTICS")

# Check partition layout
spark.read.format("delta").load("Tables/silver_transactions").inputFiles()
```

### Connection Issues

```bash
# Test Fabric workspace access
az fabric workspace list --output table

# Check capacity status
az fabric capacity show --capacity-name "cap-casinopoc-dev" --resource-group "rg-fabric-poc"

# View deployment logs
az deployment sub show --name main --query "properties.outputs"
```

---

## 🎯 Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│  MEDALLION LAYERS                                           │
├─────────────────────────────────────────────────────────────┤
│  BRONZE → Raw ingestion, append-only, source tracking       │
│  SILVER → Cleansed, validated, deduplicated, typed          │
│  GOLD   → Aggregated, business KPIs, star schema            │
├─────────────────────────────────────────────────────────────┤
│  COMPLIANCE THRESHOLDS                                      │
├─────────────────────────────────────────────────────────────┤
│  CTR:     $10,000 (cash in 24h)    W-2G Slots:  $1,200     │
│  SAR:     $5,000+ (suspicious)     W-2G Keno:   $600       │
│  Struct:  $8,000-$9,999            W-2G Poker:  $5,000     │
├─────────────────────────────────────────────────────────────┤
│  KEY METRICS                                                │
├─────────────────────────────────────────────────────────────┤
│  GGR = Total Wagered - Total Payouts                        │
│  Hold % = GGR / Total Wagered × 100                         │
│  ADT = Theoretical Win / Days Played                        │
│  Win Variance = Actual GGR - Theoretical Win                │
└─────────────────────────────────────────────────────────────┘
```

---

> 📖 **Full Documentation:** [Quick Start](../quick-start.md) | [Architecture](../architecture.md) | [Tutorials](./index.md)
