# Local PySpark Debugging for Fabric Development

![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![Updated](https://img.shields.io/badge/Updated-April_2026-green)
![Category](https://img.shields.io/badge/Category-Developer_Experience-purple)

---

**Last Updated:** `2026-04-27` | **Version:** 1.0.0

---

## Overview

Fabric notebooks run on remote Spark clusters, which means every test cycle requires uploading code, waiting for cluster startup, and reading logs from the Fabric UI. For iterative development, this is too slow.

Local PySpark debugging lets you set breakpoints, inspect DataFrames, and step through transformation logic on your own machine. The tradeoff is that you lose access to OneLake, Fabric APIs, and Workspace Identity, but for the 80% of code that is pure Spark transformations, local debugging is dramatically faster.

### Speed Comparison

| Operation | Fabric Workspace | Local PySpark |
|-----------|------------------|---------------|
| Cluster startup | 30-120 seconds | 0 (already running) |
| Run a cell | 2-5 seconds | < 1 second |
| Set a breakpoint | Not possible | Native VS Code |
| Inspect a DataFrame | `display()` in browser | Variables panel |
| Full test suite (612 tests) | N/A | ~45 seconds |

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11 or 3.12 | Match Fabric Runtime |
| Java JDK | 11 or 17 | Required by Spark |
| PySpark | 3.5.3 | Match Fabric Runtime 1.3 |
| delta-spark | 3.3.0 | Delta Lake for local reads/writes |
| VS Code | Latest | With Python + Debugpy extensions |

---

## Local PySpark Installation

### Step 1: Create Virtual Environment

```bash
cd E:/Repos/GitHub/MyDemoRepos/Suppercharge_Microsoft_Fabric

# Create venv
python -m venv .venv

# Activate (Windows - Git Bash)
source .venv/Scripts/activate

# Activate (Windows - PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Linux/macOS)
source .venv/bin/activate
```

### Step 2: Install Packages

```bash
pip install --upgrade pip

# Core Spark packages (match Fabric Runtime 1.3)
pip install pyspark==3.5.3
pip install delta-spark==3.3.0

# Testing
pip install pytest pytest-cov great-expectations

# Development utilities
pip install ipython pandas pyarrow

# Data generators (this POC)
pip install faker numpy python-dateutil pyyaml requests

# Optional: notebook conversion
pip install jupytext nbval
```

### Step 3: Verify Installation

```python
# verify_spark.py
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .master("local[2]")
    .appName("verify")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config(
        "spark.sql.catalog.spark_catalog",
        "org.apache.spark.sql.delta.catalog.DeltaCatalog",
    )
    .getOrCreate()
)

df = spark.range(10)
df.show()
print(f"Spark version: {spark.version}")
print(f"Python: {spark.sparkContext.pythonVer}")
spark.stop()
print("Local Spark is working.")
```

```bash
python verify_spark.py
```

---

## Java and JDK Setup

PySpark requires a JDK. Fabric Runtime 1.3 uses Java 11.

### Windows

1. Download [Microsoft OpenJDK 17](https://learn.microsoft.com/java/openjdk/download) (or Adoptium JDK 11/17).

2. Install to a path without spaces (e.g., `C:\java\jdk-17`).

3. Set environment variables:

```powershell
# PowerShell (run as administrator)
[System.Environment]::SetEnvironmentVariable("JAVA_HOME", "C:\java\jdk-17", "User")
[System.Environment]::SetEnvironmentVariable(
    "Path",
    "$env:Path;C:\java\jdk-17\bin",
    "User"
)
```

Or in Git Bash (add to `~/.bashrc`):

```bash
export JAVA_HOME="/c/java/jdk-17"
export PATH="$JAVA_HOME/bin:$PATH"
```

4. Verify:

```bash
java -version
# openjdk version "17.0.x" ...
```

### Linux / macOS

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install openjdk-17-jdk-headless

# macOS (Homebrew)
brew install openjdk@17

# Set JAVA_HOME
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
```

### Common Java Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `JAVA_HOME is not set` | Missing env var | Set `JAVA_HOME` as above |
| `Could not find or load main class` | Wrong JDK version | Use JDK 11 or 17, not JRE |
| `UnsupportedClassVersionError` | JDK too old | Upgrade to JDK 11+ |
| `Access denied` on Windows | Path has spaces | Move JDK to a path without spaces |

---

## Mocking mssparkutils

Fabric notebooks import `mssparkutils` for credential access, file operations, and notebook orchestration. This module is not installable via pip.

### Strategy 1: Conditional Import (Recommended)

Add this pattern to notebooks that need both local and Fabric execution:

```python
import os

try:
    from notebookutils import mssparkutils  # noqa: F401
    IS_FABRIC = True
except ImportError:
    IS_FABRIC = False


def get_secret(vault_url: str, secret_name: str) -> str:
    """Retrieve a secret from Key Vault (Fabric) or env var (local)."""
    if IS_FABRIC:
        return mssparkutils.credentials.getSecret(vault_url, secret_name)
    value = os.environ.get(secret_name.upper().replace("-", "_"))
    if value is None:
        raise ValueError(
            f"Secret '{secret_name}' not found. "
            f"Set env var {secret_name.upper().replace('-', '_')} for local dev."
        )
    return value


def get_source_path(fabric_path: str, local_path: str) -> str:
    """Return the appropriate path based on execution environment."""
    if IS_FABRIC:
        return fabric_path
    return local_path
```

### Strategy 2: conftest.py Mock Registration

For tests, register a mock before any notebook code is imported:

```python
# validation/conftest.py
import sys
from unittest.mock import MagicMock

# Register mssparkutils mock before any test imports notebook code
mock_mssparkutils = MagicMock()
mock_mssparkutils.credentials.getSecret.return_value = "mock-secret"
mock_mssparkutils.env.getWorkspaceName.return_value = "test-workspace"
mock_mssparkutils.env.getLakehouseName.return_value = "lh_bronze"

sys.modules["notebookutils"] = MagicMock()
sys.modules["notebookutils.mssparkutils"] = mock_mssparkutils
```

### Strategy 3: Full Stub Module

For comprehensive local development, use the full stub from [notebook-unit-testing.md](./notebook-unit-testing.md#mocking-mssparkutils-and-notebookutils).

---

## Creating Local Test Fixtures

### Generating Sample Parquet Files

Use the POC's data generators to create local test data:

```python
"""
scripts/create_local_fixtures.py
=================================
Generate small sample datasets for local Spark debugging.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_generation.generators.slot_telemetry_generator import SlotTelemetryGenerator
from data_generation.generators.player_generator import PlayerGenerator


def create_fixtures(output_dir: str = "temp/fixtures") -> None:
    """Generate small sample datasets for local debugging."""
    os.makedirs(output_dir, exist_ok=True)

    # Slot telemetry: 100 records
    slot_gen = SlotTelemetryGenerator()
    slot_data = slot_gen.generate_batch(100)
    slot_gen.save_parquet(slot_data, f"{output_dir}/slot_telemetry.parquet")
    print(f"Created {output_dir}/slot_telemetry.parquet (100 records)")

    # Players: 50 records
    player_gen = PlayerGenerator()
    player_data = player_gen.generate_batch(50)
    player_gen.save_parquet(player_data, f"{output_dir}/players.parquet")
    print(f"Created {output_dir}/players.parquet (50 records)")


if __name__ == "__main__":
    create_fixtures()
```

### Creating In-Memory Test DataFrames

For unit tests, prefer in-memory DataFrames over file fixtures:

```python
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    DoubleType, StringType, StructField, StructType, TimestampType,
)

spark = SparkSession.builder.master("local[2]").getOrCreate()

# Minimal test DataFrame
schema = StructType([
    StructField("machine_id", StringType(), False),
    StructField("amount", DoubleType(), True),
    StructField("timestamp", TimestampType(), False),
])

data = [
    ("SLOT-001", 25.0, datetime(2026, 1, 1, 10, 0)),
    ("SLOT-002", 12500.0, datetime(2026, 1, 1, 10, 5)),
    ("SLOT-003", 9500.0, datetime(2026, 1, 1, 10, 10)),
]

df = spark.createDataFrame(data, schema=schema)
df.show()
```

### Creating Local Delta Tables

```python
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .master("local[2]")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config(
        "spark.sql.catalog.spark_catalog",
        "org.apache.spark.sql.delta.catalog.DeltaCatalog",
    )
    .getOrCreate()
)

# Write Delta table locally
df.write.format("delta").mode("overwrite").save("temp/delta/slot_telemetry")

# Read it back
df_read = spark.read.format("delta").load("temp/delta/slot_telemetry")
df_read.show()

# Time travel
df_v0 = spark.read.format("delta").option("versionAsOf", 0).load("temp/delta/slot_telemetry")
```

---

## VS Code Debugger Configuration

### launch.json

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug: Current Notebook",
      "type": "debugpy",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": true,
      "env": {
        "PYSPARK_PYTHON": "${workspaceFolder}/.venv/Scripts/python.exe",
        "JAVA_HOME": "C:/java/jdk-17",
        "SPARK_LOCAL_IP": "127.0.0.1",
        "FABRIC_POC_HASH_SALT": "local-dev-salt-do-not-use-in-prod",
        "PYDEVD_WARN_SLOW_RESOLVE_TIMEOUT": "5"
      }
    },
    {
      "name": "Debug: pytest (current file)",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-v", "-s"],
      "console": "integratedTerminal",
      "justMyCode": true,
      "env": {
        "FABRIC_POC_HASH_SALT": "local-dev-salt-do-not-use-in-prod"
      }
    },
    {
      "name": "Debug: pytest (all unit tests)",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": ["validation/unit_tests/", "-v", "--tb=short"],
      "console": "integratedTerminal",
      "justMyCode": true,
      "env": {
        "FABRIC_POC_HASH_SALT": "local-dev-salt-do-not-use-in-prod"
      }
    },
    {
      "name": "Debug: Data Generator",
      "type": "debugpy",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "env": {
        "FABRIC_POC_HASH_SALT": "local-dev-salt-do-not-use-in-prod"
      }
    }
  ]
}
```

### Setting Breakpoints in Notebooks

Since this POC's notebooks are `.py` files, breakpoints work natively:

1. Open `notebooks/bronze/01_bronze_slot_telemetry.py`.
2. Click the gutter to the left of a line number to set a breakpoint.
3. Press `F5` and select "Debug: Current Notebook".
4. Execution stops at the breakpoint.
5. Use the Variables panel to inspect DataFrames.

### Debugging Tips

**Inspect DataFrame contents at a breakpoint:**

In the Debug Console (`Ctrl+Shift+Y`), type:

```python
df.show(5, truncate=False)
df.printSchema()
df.count()
df.describe().show()
```

**Conditional breakpoints:**

Right-click a breakpoint > Edit Breakpoint > Condition:

```python
df.count() > 100
```

**Logpoints (no-pause breakpoints):**

Right-click a breakpoint > Edit Breakpoint > Log Message:

```
Row count at this step: {df.count()}
```

---

## Local Delta Lake Operations

### Read/Write Delta Tables

```python
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .master("local[2]")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config(
        "spark.sql.catalog.spark_catalog",
        "org.apache.spark.sql.delta.catalog.DeltaCatalog",
    )
    .getOrCreate()
)

# ── Write ──────────────────────────────────────────────────────
df.write.format("delta").mode("overwrite").save("temp/delta/bronze_slots")

# ── Read ───────────────────────────────────────────────────────
df = spark.read.format("delta").load("temp/delta/bronze_slots")

# ── Append ─────────────────────────────────────────────────────
new_data.write.format("delta").mode("append").save("temp/delta/bronze_slots")

# ── Merge (upsert) ────────────────────────────────────────────
from delta.tables import DeltaTable

target = DeltaTable.forPath(spark, "temp/delta/silver_players")
target.alias("t").merge(
    source=updates.alias("s"),
    condition="t.player_id = s.player_id",
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()

# ── Time travel ────────────────────────────────────────────────
df_v0 = (
    spark.read.format("delta")
    .option("versionAsOf", 0)
    .load("temp/delta/bronze_slots")
)

# ── History ────────────────────────────────────────────────────
delta_table = DeltaTable.forPath(spark, "temp/delta/bronze_slots")
delta_table.history().show(truncate=False)

# ── Schema evolution ──────────────────────────────────────────
df_new_cols.write.format("delta").mode("append") \
    .option("mergeSchema", "true") \
    .save("temp/delta/bronze_slots")
```

### Simulating the Medallion Architecture Locally

```python
# Bronze: raw ingestion
raw_df = spark.read.parquet("temp/fixtures/slot_telemetry.parquet")
raw_df.write.format("delta").mode("overwrite").save("temp/delta/bronze/slot_telemetry")

# Silver: cleansed
bronze_df = spark.read.format("delta").load("temp/delta/bronze/slot_telemetry")
silver_df = (
    bronze_df
    .filter(col("machine_id").isNotNull())
    .dropDuplicates(["machine_id", "timestamp"])
    .withColumn("ingested_at", current_timestamp())
)
silver_df.write.format("delta").mode("overwrite").save("temp/delta/silver/slot_telemetry")

# Gold: aggregated
silver_df = spark.read.format("delta").load("temp/delta/silver/slot_telemetry")
gold_df = (
    silver_df
    .groupBy("machine_id")
    .agg(
        sum("amount").alias("total_amount"),
        count("*").alias("event_count"),
        avg("amount").alias("avg_amount"),
    )
)
gold_df.write.format("delta").mode("overwrite").save("temp/delta/gold/slot_performance")
```

---

## Limitations and Workarounds

### What Does NOT Work Locally

| Feature | Why | Workaround |
|---------|-----|------------|
| OneLake paths | `abfss://` requires Fabric auth | Use local file paths |
| `mssparkutils` | Fabric-only SDK | Mock or conditional import |
| Workspace Identity | Fabric managed identity | Use `DefaultAzureCredential` |
| Eventstreams | Fabric Real-Time Intelligence | Use local Kafka (Docker) |
| Lakehouse SQL Endpoint | Fabric service | Use local Delta + Spark SQL |
| Direct Lake | Power BI integration | Not testable locally |
| `display()` function | Fabric notebook rendering | Use `df.show()` or `df.toPandas()` |
| `%run` magic | Fabric notebook orchestration | Use Python imports |

### Path Mapping

Create a helper to map Fabric paths to local paths:

```python
"""notebooks/utils/path_resolver.py"""

import os

# Detect execution environment
IS_FABRIC = "FABRIC_RUNTIME_VERSION" in os.environ


def resolve_path(fabric_path: str, local_path: str) -> str:
    """Return the appropriate path for the current environment."""
    return fabric_path if IS_FABRIC else local_path


# Usage in notebooks:
source = resolve_path(
    fabric_path="Files/output/bronze_slot_telemetry.parquet",
    local_path="temp/fixtures/slot_telemetry.parquet",
)
```

---

## DuckDB for Quick SQL Validation

For quick SQL validation without starting a Spark JVM, use DuckDB:

```bash
pip install duckdb
```

```python
import duckdb

# Read Parquet directly
result = duckdb.sql("""
    SELECT machine_id, COUNT(*) as event_count, SUM(amount) as total
    FROM 'temp/fixtures/slot_telemetry.parquet'
    GROUP BY machine_id
    ORDER BY total DESC
    LIMIT 10
""")
result.show()

# Read Delta tables (DuckDB 0.10+)
result = duckdb.sql("""
    SELECT * FROM delta_scan('temp/delta/bronze/slot_telemetry')
    WHERE amount >= 10000
""")
result.show()

# Validate SQL logic before porting to Spark
ctr_check = duckdb.sql("""
    SELECT
        machine_id,
        amount,
        CASE WHEN amount >= 10000 THEN TRUE ELSE FALSE END AS ctr_flag
    FROM 'temp/fixtures/slot_telemetry.parquet'
    WHERE amount >= 8000
    ORDER BY amount DESC
""")
ctr_check.show()
```

DuckDB is ideal for:
- Quick schema inspection of Parquet/Delta files.
- Validating SQL logic before writing PySpark.
- Ad-hoc data exploration without JVM overhead.

---

## Docker Compose for Local Spark

For teams that want a standardized local environment:

### docker-compose.yml

```yaml
# docker-compose.spark.yml
# Local Spark + Delta Lake development environment
version: "3.9"

services:
  spark:
    image: bitnami/spark:3.5.3
    container_name: fabric-poc-spark
    environment:
      - SPARK_MODE=master
      - SPARK_MASTER_HOST=spark
      - SPARK_CONF_spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension
      - SPARK_CONF_spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog
    ports:
      - "7077:7077"   # Spark master
      - "8080:8080"   # Spark UI
      - "4040:4040"   # Application UI
    volumes:
      - ./notebooks:/opt/notebooks
      - ./temp/delta:/opt/delta
      - ./temp/fixtures:/opt/fixtures

  spark-worker:
    image: bitnami/spark:3.5.3
    container_name: fabric-poc-worker
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark:7077
      - SPARK_WORKER_MEMORY=4G
      - SPARK_WORKER_CORES=2
    depends_on:
      - spark

  minio:
    image: minio/minio:latest
    container_name: fabric-poc-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: fabricadmin
      MINIO_ROOT_PASSWORD: fabricpassword123
    ports:
      - "9000:9000"   # S3 API
      - "9001:9001"   # Console
    volumes:
      - minio-data:/data

volumes:
  minio-data:
```

### Using MinIO as a Local OneLake Substitute

MinIO provides an S3-compatible API that can simulate OneLake for local testing:

```python
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .master("local[2]")
    .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:9000")
    .config("spark.hadoop.fs.s3a.access.key", "fabricadmin")
    .config("spark.hadoop.fs.s3a.secret.key", "fabricpassword123")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .getOrCreate()
)

# Write to MinIO (simulating OneLake write)
df.write.format("delta").mode("overwrite").save("s3a://lakehouse/bronze/slot_telemetry")

# Read from MinIO
df = spark.read.format("delta").load("s3a://lakehouse/bronze/slot_telemetry")
```

Start the stack:

```bash
docker compose -f docker-compose.spark.yml up -d
```

---

## Debugging Workflow Examples

### Example 1: Debugging a Schema Mismatch

```
Symptom: Silver notebook fails with "cannot resolve column 'event_timestamp'"
```

1. Generate test data locally:

```bash
python scripts/create_local_fixtures.py
```

2. Open the Silver notebook and set a breakpoint after the read:

```python
df = spark.read.format("delta").load("temp/delta/bronze/slot_telemetry")
# <-- breakpoint here
```

3. Press `F5`. At the breakpoint, inspect the schema:

```python
# Debug Console
df.printSchema()
# Output shows column is named 'timestamp', not 'event_timestamp'
```

4. Fix the column reference and re-run.

### Example 2: Debugging a Compliance Rule

```
Symptom: CTR flag is not being set for $10,000 transactions
```

1. Create a targeted test DataFrame:

```python
test_data = [
    ("M1", 9999.99),   # Below threshold
    ("M2", 10000.00),   # At threshold (should flag)
    ("M3", 10000.01),   # Above threshold (should flag)
]
```

2. Step through `flag_ctr()` and inspect the `when` condition evaluation.

3. Discover: the condition uses `>` instead of `>=`. Fix and re-test.

### Example 3: Debugging a Delta Merge

```
Symptom: Upsert is creating duplicates instead of updating
```

1. Create source and target Delta tables locally.
2. Set a breakpoint after the merge.
3. Inspect the target table to see if the merge condition matched.
4. Common cause: join key data types differ (string vs. int).

---

## Performance Tips

### Speed Up Local Spark

```python
spark = (
    SparkSession.builder
    .master("local[2]")            # Use 2 cores, not local[*]
    .config("spark.ui.enabled", "false")          # Skip Spark UI
    .config("spark.driver.memory", "2g")          # Limit memory
    .config("spark.sql.shuffle.partitions", "2")  # Fewer partitions
    .config("spark.default.parallelism", "2")
    .config("spark.sql.adaptive.enabled", "true")
    .getOrCreate()
)
```

### Avoid Common Performance Traps

| Trap | Impact | Fix |
|------|--------|-----|
| `local[*]` on 16-core machine | OOM, slow startup | Use `local[2]` |
| Spark UI enabled | 200ms+ overhead per action | Set `spark.ui.enabled=false` |
| 200 shuffle partitions (default) | Slow for small data | Set to 2 for tests |
| Re-creating SparkSession per test | 3-5 sec per test | Use session-scoped fixture |
| Large test datasets | Minutes per test | Use 5-10 row fixtures |

---

## Troubleshooting

### `py4j.protocol.Py4JJavaError: An error occurred while calling`

```
Cause:  Java/PySpark version mismatch or missing JDK
Fix:    Verify JAVA_HOME points to JDK 11 or 17
        java -version should show 11.x or 17.x
```

### `ModuleNotFoundError: No module named 'delta'`

```
Cause:  delta-spark not installed
Fix:    pip install delta-spark==3.3.0
```

### `AnalysisException: Path does not exist`

```
Cause:  Fabric path (Files/...) used locally
Fix:    Use path_resolver.py or local paths in debug mode
```

### `Spark driver memory exceeded`

```
Cause:  Test data too large for local[*]
Fix:    Use local[2] and limit test data to < 1000 rows
```

### `WinError 5: Access is denied` (Windows)

```
Cause:  Temp directory locked by another process
Fix:    Close other Spark sessions / restart VS Code terminal
        Use a unique temp directory per test session
```

### `delta.exceptions.DeltaConcurrentModificationException`

```
Cause:  Two processes writing to the same Delta table
Fix:    Use separate temp directories per test (tmp_path fixture)
```

---

## References

- [PySpark Installation Guide](https://spark.apache.org/docs/latest/api/python/getting_started/install.html)
- [Delta Lake Quickstart](https://docs.delta.io/latest/quick-start.html)
- [VS Code Python Debugging](https://code.visualstudio.com/docs/python/debugging)
- [DuckDB Delta Lake Support](https://duckdb.org/docs/extensions/delta.html)
- [Fabric Runtime 1.3 Release Notes](https://learn.microsoft.com/fabric/data-engineering/runtime-1-3)
- [This POC: Notebook Unit Testing](./notebook-unit-testing.md)
- [This POC: VS Code Workflow](./vscode-fabric-workflow.md)
- [This POC: Dev Container Setup](./devcontainer-setup.md)
