---
hero: assets/heroes/best-practices.svg
hero_alt: Best practice — Query Optimization Deep Dive
---

# 🚀 Query Optimization Deep Dive

<div align="center" markdown>

**Maximize Spark SQL and PySpark Performance on Microsoft Fabric**

![Category](https://img.shields.io/badge/Category-Performance_Tuning-orange?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-April_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-04-27` | **Version:** 1.0.0

---

## 🎯 Overview

Query optimization on Microsoft Fabric involves tuning Apache Spark's execution engine to minimize data shuffling, leverage data skipping, and use efficient join strategies. Unlike traditional databases, Spark is a distributed compute engine where poor query design can lead to orders-of-magnitude performance differences. This guide covers the critical optimization techniques with real PySpark/SQL code examples and before/after performance comparisons.

### Optimization Impact Hierarchy

| Technique | Typical Improvement | Effort | When to Apply |
|-----------|:------------------:|:------:|---------------|
| Predicate pushdown (filter early) | 5-100x | Low | Every query |
| Broadcast join (small tables) | 3-20x | Low | Joins with dim tables < 100 MB |
| Partition pruning | 5-50x | Low | Partitioned tables |
| AQE auto-tuning | 1.5-5x | None | ON by default |
| ZORDER / data skipping | 2-10x | Medium | Frequent filter patterns |
| Shuffle partition tuning | 1.5-3x | Medium | Shuffle-heavy queries |
| Caching | 2-10x | Medium | Iterative processing |
| Skew handling | 2-20x | High | Skewed data distributions |
| Statistics collection | 1.5-3x | Low | After major data loads |

---

## 🔍 Predicate Pushdown

### Concept

Predicate pushdown moves filter conditions as close to the data source as possible, reducing the amount of data read from storage. With Delta Lake and V-Order, pushdown leverages min/max statistics and partition pruning to skip entire files and partitions.

### Filter Early, Filter Often

```python
# ❌ WRONG: Filter after join (reads ALL data first)
df_telemetry = spark.table("bronze.slot_telemetry")  # 500 GB
df_machines = spark.table("silver.machine_master")     # 50 MB
df_joined = df_telemetry.join(df_machines, "machine_id")
df_result = df_joined.filter(col("gaming_date") == "2026-04-27")  # Filter AFTER join
# Reads 500 GB, joins, THEN filters

# ✅ CORRECT: Filter before join (reads only 1 day)
df_telemetry = spark.table("bronze.slot_telemetry") \
    .filter(col("gaming_date") == "2026-04-27")  # Filter BEFORE join — reads ~1.4 GB
df_machines = spark.table("silver.machine_master")
df_result = df_telemetry.join(df_machines, "machine_id")
# Reads 1.4 GB, joins 1.4 GB × 50 MB
```

### Column Pruning

```python
# ❌ WRONG: Select all columns
df = spark.table("silver.player_transactions")  # 30 columns
df_agg = df.groupBy("player_id").agg(sum("amount").alias("total"))
# Reads all 30 columns from storage

# ✅ CORRECT: Select only needed columns
df = spark.table("silver.player_transactions") \
    .select("player_id", "amount")  # Only 2 columns
df_agg = df.groupBy("player_id").agg(sum("amount").alias("total"))
# Reads only 2 columns — columnar Parquet skips the rest
```

### Verifying Predicate Pushdown

```python
# Check if pushdown is happening
df = spark.table("bronze.slot_telemetry") \
    .filter(col("gaming_date") == "2026-04-27") \
    .filter(col("coin_in") > 100)

df.explain(True)
# Look for:
# PushedFilters: [IsNotNull(gaming_date), EqualTo(gaming_date, 2026-04-27), GreaterThan(coin_in, 100)]
# PartitionFilters: [isnotnull(gaming_date), (gaming_date = 2026-04-27)]
```

### Delta-Specific Pushdown

```sql
-- Delta data skipping uses file-level min/max statistics
-- This query skips files where coin_in max < 10000
SELECT player_id, SUM(coin_in) as total
FROM silver.player_transactions
WHERE coin_in > 10000
  AND transaction_date = '2026-04-27'
GROUP BY player_id;

-- Data skipping is automatic for the first 32 columns
-- For tables with > 32 columns, put frequently filtered columns first in schema
```

---

## 📡 Broadcast Joins

### When to Broadcast

Broadcast joins send the entire small table to every executor, avoiding an expensive shuffle of the large table. This is the single most impactful join optimization.

```python
from pyspark.sql.functions import broadcast

# Dimension table: 50 MB (well under 100 MB threshold)
df_machines = spark.table("gold.dim_machine")  # 500 rows, 50 MB

# Fact table: 500 million rows
df_telemetry = spark.table("silver.slot_telemetry_cleansed") \
    .filter(col("gaming_date") >= "2026-04-01")

# ✅ Broadcast the small dimension table
df_result = df_telemetry.join(
    broadcast(df_machines),
    "machine_id"
)
# Avoids shuffling 500M rows — only 50 MB is broadcast to each executor
```

### Broadcast Threshold Configuration

```python
# Default broadcast threshold: 10 MB (conservative)
spark.conf.get("spark.sql.autoBroadcastJoinThreshold")  # "10485760" (10 MB)

# Increase for larger dimension tables (up to ~100 MB is safe)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "104857600")  # 100 MB

# Disable broadcast entirely (for debugging)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")
```

### Broadcast Decision Matrix

| Small Table Size | Executor Memory | Broadcast? | Notes |
|:----------------:|:--------------:|:----------:|-------|
| < 10 MB | Any | **Auto** | Spark broadcasts automatically |
| 10-100 MB | >= 4 GB | **Manual** | Use `broadcast()` hint |
| 100-500 MB | >= 8 GB | **Careful** | Test with `broadcast()`, monitor memory |
| > 500 MB | Any | **No** | Sort-merge join is safer |

### Verifying Broadcast Join

```python
# Check the physical plan for BroadcastHashJoin
df_result = df_telemetry.join(broadcast(df_machines), "machine_id")
df_result.explain()
# Look for: BroadcastHashJoin [machine_id], [machine_id], Inner, BuildRight
# NOT: SortMergeJoin or ShuffledHashJoin
```

---

## ⚡ Adaptive Query Execution

### What AQE Does

Adaptive Query Execution (AQE) is ON by default in Fabric and dynamically optimizes queries at runtime based on actual data statistics gathered during execution.

| AQE Feature | What It Does | Default |
|-------------|-------------|:-------:|
| **Coalesce shuffle partitions** | Reduces empty/small partitions after shuffle | ON |
| **Convert sort-merge to broadcast** | Switches join strategy if one side is small | ON |
| **Optimize skew joins** | Splits skewed partitions for balanced processing | ON |
| **Dynamic partition pruning** | Prunes partitions based on join results | ON |

### AQE Configuration

```python
# AQE is ON by default in Fabric — verify:
spark.conf.get("spark.sql.adaptive.enabled")  # "true"
spark.conf.get("spark.sql.adaptive.coalescePartitions.enabled")  # "true"
spark.conf.get("spark.sql.adaptive.skewJoin.enabled")  # "true"

# Fine-tune coalescing behavior
spark.conf.set("spark.sql.adaptive.coalescePartitions.minPartitionSize", "67108864")  # 64 MB min
spark.conf.set("spark.sql.adaptive.advisoryPartitionSizeInBytes", "134217728")  # 128 MB target

# Skew join threshold
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "268435456")  # 256 MB
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionFactor", "5")  # 5x median = skewed
```

### AQE in Action

```python
# Without AQE: Fixed 200 shuffle partitions, many are empty
# With AQE: Partitions automatically coalesced based on data size

# Example: Aggregation with uneven data distribution
df = spark.table("silver.player_transactions") \
    .filter(col("transaction_date") >= "2026-04-01") \
    .groupBy("player_id") \
    .agg(
        sum("amount").alias("total_amount"),
        count("*").alias("transaction_count")
    )

# AQE observes that 150 of 200 shuffle partitions are tiny
# and automatically coalesces them into ~30 well-sized partitions
df.explain(True)
# Look for: AdaptiveSparkPlan (isFinalPlan=true)
#           CustomShuffleReader with coalesced partitions
```

---

## 🔀 Shuffle Partition Tuning

### Understanding Shuffles

A shuffle occurs whenever Spark needs to redistribute data across executors (joins, group-by, repartition). Each shuffle creates `spark.sql.shuffle.partitions` output files (default: 200).

### When to Change Default

```python
# Default: 200 partitions
# Problem: 200 partitions for a 10 MB dataset = 200 files of 50 KB each (too many)
# Problem: 200 partitions for a 500 GB dataset = 200 files of 2.5 GB each (too few)

# For small datasets (< 1 GB):
spark.conf.set("spark.sql.shuffle.partitions", "20")

# For medium datasets (1-100 GB):
spark.conf.set("spark.sql.shuffle.partitions", "200")  # Default is fine

# For large datasets (100 GB - 1 TB):
spark.conf.set("spark.sql.shuffle.partitions", "1000")

# For very large datasets (> 1 TB):
spark.conf.set("spark.sql.shuffle.partitions", "4000")

# Better: Let AQE handle it automatically (Runtime 1.3+)
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.shuffle.partitions", "auto")
```

### Diagnosing Shuffle Issues

```python
# Check shuffle write/read in Spark UI
# Symptoms of too many partitions:
# - Hundreds of tasks completing in < 1 second
# - Scheduler overhead dominates execution time
# - Many tasks with < 1 MB input

# Symptoms of too few partitions:
# - Few tasks running for minutes each
# - Executor OOM errors
# - Uneven task completion times (some fast, some very slow)

# Programmatic check
def estimate_shuffle_partitions(df, target_partition_mb: int = 128):
    """Estimate optimal shuffle partition count."""
    # Approximate the data size
    row_count = df.count()
    sample_size = min(10000, row_count)
    sample = df.limit(sample_size).toPandas()
    avg_row_bytes = sample.memory_usage(deep=True).sum() / sample_size
    total_mb = (row_count * avg_row_bytes) / (1024 ** 2)

    optimal_partitions = max(1, int(total_mb / target_partition_mb))
    print(f"Estimated data size: {total_mb:,.0f} MB")
    print(f"Recommended shuffle partitions: {optimal_partitions}")
    return optimal_partitions
```

---

## 💾 Caching Strategies

### Cache vs Persist vs Delta Caching

| Strategy | Storage | Scope | Best For |
|----------|---------|-------|----------|
| `cache()` / `persist(MEMORY_ONLY)` | Executor memory | Single notebook | Iterative processing |
| `persist(MEMORY_AND_DISK)` | Memory + spill to disk | Single notebook | Large datasets, iterative |
| `persist(DISK_ONLY)` | Executor disk | Single notebook | Very large intermediate results |
| **Delta caching** | SSD cache on nodes | Cross-notebook | Repeated reads of same table |
| **Temp table** | Delta table in lakehouse | Cross-notebook | Reusable intermediate results |

### When to Cache

```python
# ✅ GOOD: DataFrame used multiple times in same notebook
df_transactions = spark.table("silver.player_transactions") \
    .filter(col("transaction_date") >= "2026-04-01") \
    .cache()  # Cache because we'll use it 3 times below

# Usage 1: Total by player
totals = df_transactions.groupBy("player_id").agg(sum("amount"))

# Usage 2: Count by type
counts = df_transactions.groupBy("transaction_type").count()

# Usage 3: Compliance check
suspicious = df_transactions.filter(
    (col("amount") >= 8000) & (col("amount") <= 9900)
)

# Clean up when done
df_transactions.unpersist()
```

```python
# ❌ WRONG: Caching a DataFrame used only once
df = spark.table("gold.slot_performance_daily").cache()  # Wasteful
result = df.filter(col("gaming_date") == "2026-04-27").collect()
# Cache fills memory for no benefit — the data is read once
```

### Delta Caching (Fabric-Managed)

```python
# Delta caching is automatic in Fabric for frequently accessed tables
# It caches Parquet file contents on local SSD

# Force-cache a table for repeated cross-notebook access:
spark.sql("CACHE TABLE gold.dim_machine")

# Check cache status
spark.catalog.isCached("gold.dim_machine")  # True

# Clear specific cache
spark.sql("UNCACHE TABLE gold.dim_machine")

# Clear all caches
spark.catalog.clearCache()
```

### Caching Decision Matrix

| Scenario | Cache? | Strategy |
|----------|:------:|----------|
| Used once in notebook | No | Read directly |
| Used 2-3 times, < 1 GB | **Yes** | `.cache()` (MEMORY_ONLY) |
| Used 2-3 times, 1-10 GB | **Yes** | `.persist(MEMORY_AND_DISK)` |
| Used 2-3 times, > 10 GB | Maybe | `.persist(DISK_ONLY)` or temp table |
| Cross-notebook reuse | **Yes** | `CACHE TABLE` or temp Delta table |
| Streaming micro-batch | No | Streaming handles its own state |

---

## ⚖️ Skew Handling

### Detecting Skew

```python
from pyspark.sql import functions as F

def detect_join_skew(df, join_column: str, threshold_factor: float = 10.0):
    """Detect data skew in a join column."""
    stats = df.groupBy(join_column).count() \
        .agg(
            F.avg("count").alias("avg_count"),
            F.max("count").alias("max_count"),
            F.min("count").alias("min_count"),
            F.percentile_approx("count", 0.5).alias("median_count"),
            F.percentile_approx("count", 0.99).alias("p99_count"),
            F.count("*").alias("distinct_keys"),
        ).collect()[0]

    skew_ratio = stats.max_count / stats.avg_count
    print(f"Column: {join_column}")
    print(f"  Distinct keys: {stats.distinct_keys:,}")
    print(f"  Min/Avg/Median/P99/Max count: {stats.min_count:,} / {stats.avg_count:,.0f} / {stats.median_count:,} / {stats.p99_count:,} / {stats.max_count:,}")
    print(f"  Skew ratio (max/avg): {skew_ratio:.1f}x")

    if skew_ratio > threshold_factor:
        print(f"  🔴 SKEWED: Ratio {skew_ratio:.0f}x exceeds threshold {threshold_factor}x")
        # Show top skewed keys
        top_keys = df.groupBy(join_column).count() \
            .orderBy(F.desc("count")).limit(10).collect()
        print(f"  Top 10 hot keys:")
        for row in top_keys:
            print(f"    {row[join_column]}: {row['count']:,} rows")
        return True
    else:
        print(f"  ✅ Skew is within acceptable range")
        return False

# Usage
detect_join_skew(spark.table("silver.player_transactions"), "player_id")
```

### Salting for Skew Mitigation

```python
from pyspark.sql.functions import concat, lit, rand, floor as spark_floor

# Problem: Player "VIP-001" has 10M transactions, others have ~1K
# Join is bottlenecked on the single partition processing VIP-001

SALT_BUCKETS = 20

# Step 1: Salt the skewed (large) table
df_transactions_salted = spark.table("silver.player_transactions") \
    .withColumn("salt", (rand() * SALT_BUCKETS).cast("int")) \
    .withColumn("salted_player_id", concat(col("player_id"), lit("_"), col("salt")))

# Step 2: Explode the small table to match all salt values
from pyspark.sql.functions import explode, array

salt_values = [lit(i) for i in range(SALT_BUCKETS)]
df_players_exploded = spark.table("gold.dim_player") \
    .withColumn("salt", explode(array(*salt_values))) \
    .withColumn("salted_player_id", concat(col("player_id"), lit("_"), col("salt")))

# Step 3: Join on salted key
df_result = df_transactions_salted.join(
    df_players_exploded,
    "salted_player_id"
).drop("salt", "salted_player_id")
# VIP-001's 10M rows are now spread across 20 partitions
```

### AQE Skew Join (Preferred in Runtime 1.3+)

```python
# AQE handles skew automatically when enabled
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "268435456")  # 256 MB
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionFactor", "5")

# Just write the normal join — AQE detects and splits skewed partitions
df_result = df_transactions.join(df_players, "player_id")
# AQE detects VIP-001 partition is 5x larger than median
# and automatically splits it into smaller sub-partitions
```

---

## 🪣 Bucketing vs Partitioning

### When Bucketing Helps

Bucketing pre-sorts data into a fixed number of files by hash of a column. This eliminates shuffles for joins and aggregations on the bucketed column.

```python
# Create a bucketed table (useful for repeated joins on player_id)
df = spark.table("silver.player_transactions")
df.write.format("delta") \
    .bucketBy(256, "player_id") \
    .sortBy("player_id", "transaction_date") \
    .mode("overwrite") \
    .saveAsTable("silver.player_transactions_bucketed")

# Joining two tables bucketed on the same column = no shuffle
df_trans = spark.table("silver.player_transactions_bucketed")
df_profile = spark.table("silver.player_profile_bucketed")  # Also bucketed by player_id, 256 buckets
df_joined = df_trans.join(df_profile, "player_id")
# Sort-merge join with NO exchange (shuffle) — both sides already co-partitioned
```

### Bucketing vs Partitioning Comparison

| Feature | Partitioning | Bucketing |
|---------|:------------:|:---------:|
| **Mechanism** | Directory per value | Fixed number of files by hash |
| **Best for** | Filter queries (WHERE) | Join queries (JOIN ON) |
| **Cardinality** | Low (< 1,000 values) | Any (fixed bucket count) |
| **Pruning** | Partition pruning (directories) | Bucket pruning (files) |
| **Shuffle elimination** | No | Yes (when both sides bucketed) |
| **Maintenance** | OPTIMIZE per partition | Rebucket on major changes |
| **Fabric compatibility** | Full | Full (Delta tables) |

---

## 📊 Statistics Collection

### Why Statistics Matter

Spark's Cost-Based Optimizer (CBO) uses table and column statistics to choose optimal join orders, join strategies, and filter selectivity estimates. Without statistics, Spark makes conservative estimates that often lead to suboptimal plans.

### Collecting Statistics

```sql
-- Collect table-level statistics (row count, size)
ANALYZE TABLE silver.player_transactions COMPUTE STATISTICS;

-- Collect column-level statistics (min, max, distinct count, nulls, avg length)
ANALYZE TABLE silver.player_transactions
COMPUTE STATISTICS FOR COLUMNS player_id, amount, transaction_date, transaction_type;

-- Collect for all columns (more expensive but most accurate)
ANALYZE TABLE silver.player_transactions
COMPUTE STATISTICS FOR ALL COLUMNS;

-- Verify statistics are available
DESCRIBE EXTENDED silver.player_transactions;
-- Look for "Statistics" row showing numRows and sizeInBytes
```

### When to Collect Statistics

```python
# After major data loads
def post_load_statistics(table_name: str, key_columns: list = None):
    """Collect statistics after a significant data load."""
    # Table-level statistics
    spark.sql(f"ANALYZE TABLE {table_name} COMPUTE STATISTICS")

    # Column-level statistics for key columns
    if key_columns:
        cols_str = ", ".join(key_columns)
        spark.sql(f"ANALYZE TABLE {table_name} COMPUTE STATISTICS FOR COLUMNS {cols_str}")

    print(f"Statistics collected for {table_name}")

# Usage after daily load
post_load_statistics(
    "silver.player_transactions",
    ["player_id", "amount", "transaction_date", "transaction_type"]
)
```

### Statistics-Driven Optimization

```python
# Without statistics: Spark assumes both tables are large → sort-merge join
# With statistics: Spark knows dim_machine is 50 MB → broadcast join

# Scenario: Before statistics
spark.sql("ANALYZE TABLE gold.dim_machine COMPUTE STATISTICS")
spark.sql("ANALYZE TABLE silver.slot_telemetry_cleansed COMPUTE STATISTICS")

# Now Spark CBO chooses broadcast join automatically
df = spark.sql("""
    SELECT t.gaming_date, m.manufacturer, SUM(t.coin_in) as revenue
    FROM silver.slot_telemetry_cleansed t
    JOIN gold.dim_machine m ON t.machine_id = m.machine_id
    WHERE t.gaming_date >= '2026-04-01'
    GROUP BY t.gaming_date, m.manufacturer
""")
# CBO chooses BroadcastHashJoin because it knows dim_machine is small
```

---

## 🔥 Photon Engine in Fabric

### What Photon Does

Photon is a vectorized query engine written in C++ that accelerates Spark SQL operations. In Fabric, Photon is available on certain capacity SKUs and can dramatically speed up scan-heavy and aggregation-heavy workloads.

### Photon-Optimized Patterns

```python
# Photon excels at:
# 1. Large scans with filters
# 2. Aggregations (SUM, COUNT, AVG, MIN, MAX)
# 3. Hash joins
# 4. Data shuffles

# Query that benefits heavily from Photon
df = spark.sql("""
    SELECT
        gaming_date,
        floor_zone,
        machine_type,
        COUNT(*) as event_count,
        SUM(coin_in) as total_coin_in,
        SUM(coin_out) as total_coin_out,
        AVG(theoretical_hold_pct) as avg_hold,
        MIN(coin_in) as min_bet,
        MAX(coin_in) as max_bet
    FROM silver.slot_telemetry_cleansed
    WHERE gaming_date BETWEEN '2026-04-01' AND '2026-04-27'
    GROUP BY gaming_date, floor_zone, machine_type
""")
# Photon vectorizes the scan, filter, and aggregation
# Typically 2-5x faster than standard Spark for this pattern
```

### Checking Photon Usage

```python
# Verify Photon is being used in the query plan
df.explain(True)
# Look for: ColumnarToRow / RowToColumnar transitions
# Photon operations appear as native columnar operations

# Photon is NOT used for:
# - UDFs (Python or Scala)
# - Complex data types (arrays, maps, structs) in some operations
# - Non-SQL operations (RDD API)
```

---

## 📈 Query Plan Analysis

### Reading EXPLAIN Output

```python
# Three levels of EXPLAIN detail
df = spark.table("silver.player_transactions") \
    .filter(col("transaction_date") == "2026-04-27") \
    .groupBy("player_id") \
    .agg(sum("amount").alias("total"))

# Level 1: Simple plan
df.explain()  # Shows physical plan only

# Level 2: Extended plan
df.explain(True)  # Shows parsed, analyzed, optimized, and physical plans

# Level 3: Formatted plan (most readable)
df.explain("formatted")  # Shows plan with stats
```

### Key Metrics to Check

```python
# After running a query, check Spark UI for:
metrics_checklist = {
    "Scan": {
        "files_read": "Should be << total files (data skipping)",
        "data_size_read": "Should be << total table size (pruning working)",
        "rows_output": "Should match expected filtered count",
    },
    "Exchange (Shuffle)": {
        "shuffle_write": "Large shuffle = potential optimization opportunity",
        "shuffle_records": "High count = check if broadcast join possible",
    },
    "Join": {
        "type": "BroadcastHashJoin (best) > ShuffledHashJoin > SortMergeJoin (worst for small tables)",
        "build_side": "Smaller table should be build side",
    },
    "Aggregate": {
        "spill_size": "Non-zero = increase executor memory or partitions",
    },
}
```

### Before/After Optimization Example

```python
import time

def benchmark_query(name: str, query_fn, iterations: int = 3) -> float:
    """Benchmark a query function."""
    times = []
    for _ in range(iterations):
        spark.catalog.clearCache()
        start = time.time()
        query_fn().collect()
        times.append(time.time() - start)
    avg = sum(times) / len(times)
    print(f"{name}: avg={avg:.2f}s (min={min(times):.2f}s, max={max(times):.2f}s)")
    return avg

# Before: Naive query
def query_naive():
    return spark.sql("""
        SELECT t.player_id, m.floor_zone, SUM(t.coin_in) as total
        FROM bronze.slot_telemetry t
        JOIN silver.machine_master m ON t.machine_id = m.machine_id
        WHERE t.gaming_date = '2026-04-27'
        GROUP BY t.player_id, m.floor_zone
    """)

# After: Optimized query
def query_optimized():
    return spark.sql("""
        SELECT /*+ BROADCAST(m) */
            t.player_id, m.floor_zone, SUM(t.coin_in) as total
        FROM bronze.slot_telemetry t
        JOIN silver.machine_master m ON t.machine_id = m.machine_id
        WHERE t.gaming_date = '2026-04-27'
        GROUP BY t.player_id, m.floor_zone
    """)

before = benchmark_query("Before (naive)", query_naive)
after = benchmark_query("After (broadcast hint)", query_optimized)
print(f"Improvement: {((before - after) / before * 100):.0f}%")
```

---

## 🎰 Casino Query Optimization

### Slot Performance Dashboard Query

```python
# Optimized query for casino floor management dashboard
# Uses: broadcast join, predicate pushdown, partition pruning

spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "104857600")

df_dashboard = spark.sql("""
    SELECT /*+ BROADCAST(dm), BROADCAST(dz) */
        t.gaming_date,
        dz.zone_name,
        dm.manufacturer,
        dm.denomination,
        COUNT(DISTINCT t.machine_id) as active_machines,
        SUM(t.coin_in) as total_coin_in,
        SUM(t.coin_out) as total_coin_out,
        (SUM(t.coin_in) - SUM(t.coin_out)) / NULLIF(SUM(t.coin_in), 0) * 100 as hold_pct,
        SUM(t.games_played) as total_games
    FROM silver.slot_telemetry_cleansed t
    JOIN gold.dim_machine dm ON t.machine_id = dm.machine_id
    JOIN gold.dim_floor_zone dz ON t.floor_zone = dz.zone_id
    WHERE t.gaming_date >= current_date() - INTERVAL 7 DAYS
    GROUP BY t.gaming_date, dz.zone_name, dm.manufacturer, dm.denomination
    ORDER BY t.gaming_date DESC, total_coin_in DESC
""")
```

### Compliance Structuring Detection

```python
# Optimized: Find potential structuring (multiple transactions just under $10K)
df_structuring = spark.sql("""
    SELECT
        player_id,
        transaction_date,
        COUNT(*) as txn_count,
        SUM(amount) as daily_total,
        MAX(amount) as max_single,
        COLLECT_LIST(amount) as amounts
    FROM silver.player_transactions
    WHERE transaction_date >= current_date() - INTERVAL 30 DAYS
      AND amount BETWEEN 8000 AND 9900
    GROUP BY player_id, transaction_date
    HAVING COUNT(*) >= 2 AND SUM(amount) >= 10000
    ORDER BY daily_total DESC
""")
# Predicate pushdown on date + amount range
# Partition pruning on transaction_date
# HAVING filter reduces output before ORDER BY
```

---

## 🏛️ Federal Query Optimization

### NOAA Weather Analysis

```python
# Optimized: Cross-station weather anomaly detection
spark.conf.set("spark.sql.shuffle.partitions", "100")

df_anomalies = spark.sql("""
    SELECT /*+ BROADCAST(s) */
        o.station_id,
        s.station_name,
        s.state,
        o.observation_date,
        o.temperature_max,
        o.temperature_min,
        AVG(o.temperature_max) OVER (
            PARTITION BY o.station_id
            ORDER BY o.observation_date
            ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
        ) as rolling_avg_max,
        o.temperature_max - AVG(o.temperature_max) OVER (
            PARTITION BY o.station_id
            ORDER BY o.observation_date
            ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING
        ) as deviation
    FROM silver.noaa_weather_observations o
    JOIN gold.dim_station s ON o.station_id = s.station_id
    WHERE o.observation_date >= '2026-01-01'
""")

# Filter for significant anomalies (> 3 std deviations)
df_significant = df_anomalies.filter(abs(col("deviation")) > 15)
```

---

## 🚫 Anti-Patterns

### Anti-Pattern 1: UDFs Instead of Built-in Functions

```python
# ❌ WRONG: Python UDF (forces row-at-a-time processing, no Photon)
from pyspark.sql.functions import udf
from pyspark.sql.types import DoubleType

@udf(DoubleType())
def calculate_hold_pct(coin_in, coin_out):
    if coin_in == 0:
        return 0.0
    return (coin_in - coin_out) / coin_in * 100

df = df.withColumn("hold_pct", calculate_hold_pct(col("coin_in"), col("coin_out")))

# ✅ CORRECT: Built-in functions (vectorized, Photon-compatible)
df = df.withColumn("hold_pct",
    when(col("coin_in") == 0, lit(0.0))
    .otherwise((col("coin_in") - col("coin_out")) / col("coin_in") * 100)
)
```

### Anti-Pattern 2: Collecting Large Results to Driver

```python
# ❌ WRONG: Collecting millions of rows to driver
all_data = spark.table("silver.player_transactions").collect()  # OOM risk!

# ✅ CORRECT: Process in Spark, collect only aggregated results
summary = spark.table("silver.player_transactions") \
    .groupBy("transaction_type") \
    .agg(count("*"), sum("amount")) \
    .collect()  # Small result set
```

### Anti-Pattern 3: Repeated Reads Without Caching

```python
# ❌ WRONG: Reading the same table 5 times
for zone in ["VIP", "HIGH_LIMIT", "MAIN_FLOOR", "PENNY", "TABLE_GAMES"]:
    df = spark.table("silver.slot_telemetry_cleansed") \
        .filter(col("floor_zone") == zone) \
        .agg(sum("coin_in"))
    # Reads entire table from storage 5 times

# ✅ CORRECT: Read once, cache, process
df = spark.table("silver.slot_telemetry_cleansed").cache()
for zone in ["VIP", "HIGH_LIMIT", "MAIN_FLOOR", "PENNY", "TABLE_GAMES"]:
    result = df.filter(col("floor_zone") == zone).agg(sum("coin_in"))
df.unpersist()
```

### Anti-Pattern 4: Ignoring Explain Plans

```python
# ❌ WRONG: Running queries without checking the plan
result = df_large.join(df_small, "key").collect()
# Might be doing SortMergeJoin when BroadcastHashJoin is optimal

# ✅ CORRECT: Check plan before running expensive queries
df_result = df_large.join(df_small, "key")
df_result.explain()
# Verify: BroadcastHashJoin, no unnecessary Exchange, partition pruning active
df_result.collect()
```

---

## 📚 References

- [Spark SQL Performance Tuning](https://spark.apache.org/docs/latest/sql-performance-tuning.html)
- [Adaptive Query Execution](https://spark.apache.org/docs/latest/sql-performance-tuning.html#adaptive-query-execution)
- [Fabric Spark Optimization](https://learn.microsoft.com/en-us/fabric/data-engineering/spark-job-concurrency-and-queueing)
- [Delta Lake Optimization](https://docs.delta.io/latest/optimizations-oss.html)
- [Broadcast Joins](https://spark.apache.org/docs/latest/sql-performance-tuning.html#broadcast-hint-for-sql-queries)
- [V-Order Tuning Deep Dive](v-order-tuning-deep-dive.md)
- [Partition Strategy Decision Tree](partition-strategy-decision-tree.md)

---

> **Next:** [V-Order Tuning Deep Dive](v-order-tuning-deep-dive.md) | [Partition Strategy Decision Tree](partition-strategy-decision-tree.md)
