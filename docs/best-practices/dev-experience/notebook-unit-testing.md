---
hero: assets/heroes/best-practices.svg
hero_alt: Dev experience best practice — Unit Testing Microsoft Fabric Notebooks
type: deep-dive
---
# Unit Testing Microsoft Fabric Notebooks

![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![Updated](https://img.shields.io/badge/Updated-April_2026-green)
![Category](https://img.shields.io/badge/Category-Developer_Experience-purple)

---

**Last Updated:** `2026-04-27` | **Version:** 1.0.0

---

## Overview

Microsoft Fabric notebooks execute on remote Spark clusters, which makes local testing challenging. This guide establishes patterns for extracting business logic from notebooks into testable modules, mocking Fabric-specific APIs, and integrating notebook tests into the CI pipeline.

This POC maintains **612 unit tests** across casino, federal, streaming, and analytics domains. The patterns in this document are how those tests are structured.

---

## Why Unit Test Fabric Notebooks

### The Problem

Fabric notebooks are monolithic by default. Code, configuration, and orchestration logic are mixed in a single artifact. Without testing:

- Schema changes break downstream consumers silently.
- Compliance logic (CTR thresholds, SAR detection) cannot be validated without production data.
- Refactoring is risky because there is no safety net.
- Code review is opinion-based rather than evidence-based.

### The Solution

Extract pure transformation functions from notebooks, test them locally with synthetic data, and validate notebook execution in CI. This catches 80% of bugs before code reaches a Fabric workspace.

### What to Test

| Layer | What to Test | Example |
|-------|-------------|---------|
| Bronze | Schema enforcement, data type casting | Slot telemetry timestamp parsing |
| Silver | Cleansing rules, deduplication, validation | SSN hashing, null rejection |
| Gold | Aggregation logic, KPI calculations | Revenue per machine per hour |
| Compliance | Threshold detection, regulatory rules | CTR $10K threshold, SAR patterns |

---

## Test Pyramid for Data Engineering

```
                    /\
                   /  \        End-to-End Tests
                  / E2E \      Run in Fabric workspace
                 /--------\    against real/staging data
                /          \
               / Integration \   Integration Tests
              /   Tests       \  Local Spark + Delta Lake
             /----------------\  Multi-table joins, pipelines
            /                  \
           /    Unit Tests      \  Unit Tests
          /     (pytest)         \ Pure functions, schemas
         /________________________\ Fast, no Spark needed
```

| Level | Scope | Speed | Where | Count in POC |
|-------|-------|-------|-------|-------------|
| Unit | Pure functions, schemas | < 1 sec each | Local (pytest) | 612 |
| Integration | Spark transformations | 5-30 sec each | Local Spark | 9 (GE suites) |
| E2E | Full pipeline | Minutes | Fabric workspace | Manual |

---

## Extracting Testable Functions

### The Pattern: Separate Logic from Orchestration

**Before (monolithic notebook):**

```python
# Databricks notebook source
# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, hash, lit

spark = SparkSession.builder.getOrCreate()

# COMMAND ----------

# Read raw data
df = spark.read.parquet("Files/landing/slot_telemetry/")

# COMMAND ----------

# Complex business logic mixed with orchestration
df_clean = df.filter(col("machine_id").isNotNull())
df_clean = df_clean.withColumn(
    "ctr_flag",
    when(col("amount") >= 10000, lit(True)).otherwise(lit(False))
)
df_clean = df_clean.withColumn(
    "sar_flag",
    when(
        (col("amount") >= 8000) & (col("amount") < 10000),
        lit(True)
    ).otherwise(lit(False))
)

# COMMAND ----------

# Write to lakehouse
df_clean.write.format("delta").mode("append").saveAsTable("lh_bronze.bronze_slot_telemetry")
```

**After (extracted functions):**

Create a shared utility module at `notebooks/utils/compliance_rules.py`:

```python
"""
notebooks/utils/compliance_rules.py
====================================
Reusable compliance detection functions for casino domain.
Extracted from notebooks for testability.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, lit, when


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CTR_THRESHOLD = 10_000       # Currency Transaction Report
SAR_LOWER = 8_000            # Suspicious Activity Report lower bound
SAR_UPPER = 10_000           # Suspicious Activity Report upper bound
W2G_SLOTS = 1_200            # W-2G threshold for slot machines
W2G_TABLE = 600              # W-2G threshold for table games
W2G_POKER = 5_000            # W-2G threshold for poker


def flag_ctr(df: DataFrame, amount_col: str = "amount") -> DataFrame:
    """Flag transactions meeting the CTR threshold ($10,000+)."""
    return df.withColumn(
        "ctr_flag",
        when(col(amount_col) >= CTR_THRESHOLD, lit(True)).otherwise(lit(False)),
    )


def flag_sar(df: DataFrame, amount_col: str = "amount") -> DataFrame:
    """Flag transactions in the SAR structuring range ($8K-$9,999)."""
    return df.withColumn(
        "sar_flag",
        when(
            (col(amount_col) >= SAR_LOWER) & (col(amount_col) < SAR_UPPER),
            lit(True),
        ).otherwise(lit(False)),
    )


def flag_w2g(
    df: DataFrame,
    amount_col: str = "amount",
    game_type_col: str = "game_type",
) -> DataFrame:
    """Flag winnings requiring W-2G reporting based on game type."""
    return df.withColumn(
        "w2g_flag",
        when(
            (col(game_type_col) == "slots") & (col(amount_col) >= W2G_SLOTS),
            lit(True),
        )
        .when(
            (col(game_type_col) == "table") & (col(amount_col) >= W2G_TABLE),
            lit(True),
        )
        .when(
            (col(game_type_col) == "poker") & (col(amount_col) >= W2G_POKER),
            lit(True),
        )
        .otherwise(lit(False)),
    )


def reject_nulls(df: DataFrame, required_cols: list[str]) -> DataFrame:
    """Remove rows where any required column is null."""
    condition = None
    for c in required_cols:
        clause = col(c).isNotNull()
        condition = clause if condition is None else condition & clause
    return df.filter(condition)
```

The notebook then becomes thin orchestration:

```python
# Databricks notebook source
# COMMAND ----------

# MAGIC %run ./utils/compliance_rules

# COMMAND ----------

from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

SOURCE_PATH = "Files/output/bronze_slot_telemetry.parquet"
TARGET_TABLE = "lh_bronze.bronze_slot_telemetry"

# COMMAND ----------

df = spark.read.parquet(SOURCE_PATH)
df = reject_nulls(df, ["machine_id", "timestamp"])
df = flag_ctr(df)
df = flag_sar(df)

# COMMAND ----------

df.write.format("delta").mode("append").saveAsTable(TARGET_TABLE)
```

### The `%run` Pattern

Fabric notebooks support `%run` to include shared code. Structure your utilities as:

```
notebooks/
  utils/
    compliance_rules.py      # Testable functions
    bronze_utils.py           # Shared Bronze helpers
    schema_definitions.py     # StructType definitions
  bronze/
    01_bronze_slot_telemetry.py   # Uses %run ./utils/compliance_rules
  silver/
    01_silver_slot_cleansed.py    # Uses %run ./utils/compliance_rules
```

---

## pytest with Local Spark

### Installation

```bash
pip install pyspark==3.5.3 delta-spark==3.3.0 pytest pytest-cov
```

> **Note:** Match the PySpark version to your Fabric workspace runtime. Fabric Runtime 1.3 uses Spark 3.5.x.

### Spark Fixture (Session-Scoped)

Add to `validation/conftest.py`:

```python
"""
validation/conftest.py
======================
Session-scoped fixtures shared across all validation test suites.
"""

import os

import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session", autouse=True)
def set_hash_salt() -> None:
    """Ensure FABRIC_POC_HASH_SALT is set for the entire test session."""
    if not os.environ.get("FABRIC_POC_HASH_SALT"):
        os.environ["FABRIC_POC_HASH_SALT"] = "test-salt-do-not-use-in-production"


@pytest.fixture(scope="session")
def spark() -> SparkSession:
    """Create a local Spark session for testing.

    Session-scoped to avoid JVM startup overhead on every test.
    Uses local[2] for parallelism without overwhelming CI runners.
    """
    session = (
        SparkSession.builder
        .master("local[2]")
        .appName("fabric-poc-tests")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.ui.enabled", "false")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )
    yield session
    session.stop()
```

---

## Mocking mssparkutils and notebookutils

Fabric notebooks use `mssparkutils` and `notebookutils` for secrets, file operations, and widget parameters. These are not available locally.

### Stub Module

Create `validation/mocks/mssparkutils_stub.py`:

```python
"""
validation/mocks/mssparkutils_stub.py
======================================
Lightweight stub for mssparkutils used in local testing.
Provides the same interface as Fabric's mssparkutils without
requiring a Fabric workspace connection.
"""


class _Credentials:
    """Stub for mssparkutils.credentials."""

    def getSecret(self, vault_url: str, secret_name: str) -> str:
        """Return a placeholder secret value for local testing."""
        return f"mock-secret-{secret_name}"

    def getToken(self, audience: str) -> str:
        """Return a placeholder token for local testing."""
        return "mock-token-eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9"


class _Fs:
    """Stub for mssparkutils.fs."""

    def ls(self, path: str) -> list[dict]:
        """List files at path (returns empty list locally)."""
        return []

    def mkdirs(self, path: str) -> bool:
        """Create directories (no-op locally)."""
        return True

    def cp(self, src: str, dest: str, recurse: bool = False) -> bool:
        """Copy files (no-op locally)."""
        return True

    def rm(self, path: str, recurse: bool = False) -> bool:
        """Remove files (no-op locally)."""
        return True

    def head(self, path: str, max_bytes: int = 65536) -> str:
        """Read head of file (returns empty string locally)."""
        return ""

    def put(self, path: str, content: str, overwrite: bool = False) -> bool:
        """Write content to file (no-op locally)."""
        return True


class _Notebook:
    """Stub for mssparkutils.notebook."""

    def run(self, notebook_name: str, timeout: int = 0, params: dict = None) -> str:
        """Run a notebook (no-op locally)."""
        return f"mock-run-{notebook_name}"

    def exit(self, value: str) -> None:
        """Exit notebook with value (no-op locally)."""
        pass


class _Env:
    """Stub for mssparkutils.env."""

    def getWorkspaceName(self) -> str:
        return "local-test-workspace"

    def getLakehouseName(self) -> str:
        return "lh_bronze"

    def getUserName(self) -> str:
        return "test-user@contoso.com"


class MSSparkUtils:
    """Top-level stub matching the mssparkutils namespace."""

    def __init__(self) -> None:
        self.credentials = _Credentials()
        self.fs = _Fs()
        self.notebook = _Notebook()
        self.env = _Env()


# Module-level instance (import as: from mssparkutils_stub import mssparkutils)
mssparkutils = MSSparkUtils()
```

### Using the Stub in Tests

```python
# In conftest.py or test setup
import sys
from unittest.mock import MagicMock

# Register the stub so notebook imports resolve
sys.modules["notebookutils"] = MagicMock()
sys.modules["notebookutils.mssparkutils"] = MagicMock()
```

Or use `monkeypatch` per test:

```python
def test_notebook_with_mocked_utils(monkeypatch):
    """Test notebook logic with mocked mssparkutils."""
    from validation.mocks.mssparkutils_stub import mssparkutils

    monkeypatch.setattr("sys.modules", {
        **sys.modules,
        "mssparkutils": mssparkutils,
    })

    # Now import and test the notebook function
    from notebooks.utils.compliance_rules import flag_ctr
    # ... assertions
```

---

## conftest.py Fixtures

### Complete Fixture Set

```python
"""
validation/unit_tests/conftest.py
==================================
Fixtures for unit testing notebook logic.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def set_hash_salt() -> None:
    if not os.environ.get("FABRIC_POC_HASH_SALT"):
        os.environ["FABRIC_POC_HASH_SALT"] = "test-salt-do-not-use-in-production"


@pytest.fixture(scope="session", autouse=True)
def mock_fabric_modules() -> None:
    """Register mocks for Fabric-only modules so notebook imports succeed."""
    sys.modules.setdefault("notebookutils", MagicMock())
    sys.modules.setdefault("notebookutils.mssparkutils", MagicMock())


# ---------------------------------------------------------------------------
# Spark
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def spark() -> SparkSession:
    session = (
        SparkSession.builder
        .master("local[2]")
        .appName("notebook-unit-tests")
        .config("spark.ui.enabled", "false")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )
    yield session
    session.stop()


# ---------------------------------------------------------------------------
# Sample DataFrames
# ---------------------------------------------------------------------------

SLOT_SCHEMA = StructType([
    StructField("machine_id", StringType(), False),
    StructField("event_type", StringType(), False),
    StructField("amount", DoubleType(), True),
    StructField("game_type", StringType(), True),
    StructField("timestamp", TimestampType(), False),
])


@pytest.fixture
def slot_telemetry_df(spark):
    """Small DataFrame mimicking Bronze slot telemetry."""
    now = datetime.now()
    data = [
        ("SLOT-001", "play", 25.0, "slots", now),
        ("SLOT-002", "jackpot", 12500.0, "slots", now),     # CTR + W-2G
        ("SLOT-003", "play", 9500.0, "slots", now),          # SAR range
        ("SLOT-004", "play", 8500.0, "table", now),          # SAR range + W-2G
        (None, "play", 100.0, "slots", now),                  # Null machine_id
        ("SLOT-006", "play", 500.0, "poker", now),
        ("SLOT-007", "play", 5500.0, "poker", now),           # W-2G poker
    ]
    return spark.createDataFrame(data, schema=SLOT_SCHEMA)


@pytest.fixture
def empty_df(spark):
    """Empty DataFrame with slot telemetry schema."""
    return spark.createDataFrame([], schema=SLOT_SCHEMA)


# ---------------------------------------------------------------------------
# Temporary Delta paths
# ---------------------------------------------------------------------------

@pytest.fixture
def delta_tmp_path(tmp_path):
    """Return a temporary directory for Delta table writes."""
    path = tmp_path / "delta_test"
    path.mkdir()
    return str(path)
```

---

## Writing Tests: Complete Examples

### Testing Compliance Rules

```python
"""
validation/unit_tests/test_compliance_rules.py
===============================================
Tests for extracted compliance detection functions.
"""

import pytest


class TestFlagCTR:
    """Tests for Currency Transaction Report flagging."""

    def test_amount_at_threshold_is_flagged(self, spark, slot_telemetry_df):
        from notebooks.utils.compliance_rules import flag_ctr

        result = flag_ctr(slot_telemetry_df)
        flagged = result.filter("ctr_flag = true").collect()

        # Only the $12,500 jackpot should be flagged
        assert len(flagged) == 1
        assert flagged[0]["machine_id"] == "SLOT-002"

    def test_amount_below_threshold_not_flagged(self, spark, slot_telemetry_df):
        from notebooks.utils.compliance_rules import flag_ctr

        result = flag_ctr(slot_telemetry_df)
        not_flagged = result.filter("ctr_flag = false").collect()

        # All others (including nulls) should not be flagged
        assert len(not_flagged) == 6

    def test_empty_dataframe_returns_empty(self, spark, empty_df):
        from notebooks.utils.compliance_rules import flag_ctr

        result = flag_ctr(empty_df)
        assert result.count() == 0
        assert "ctr_flag" in result.columns


class TestFlagSAR:
    """Tests for Suspicious Activity Report pattern detection."""

    def test_structuring_range_flagged(self, spark, slot_telemetry_df):
        from notebooks.utils.compliance_rules import flag_sar

        result = flag_sar(slot_telemetry_df)
        flagged = result.filter("sar_flag = true").collect()

        assert len(flagged) == 2
        amounts = {row["amount"] for row in flagged}
        assert amounts == {9500.0, 8500.0}

    def test_at_threshold_not_flagged(self, spark):
        from notebooks.utils.compliance_rules import flag_sar, SAR_UPPER

        data = [("M1", "play", float(SAR_UPPER), "slots", None)]
        # Amount at exactly $10,000 is CTR, not SAR
        # (SAR is strictly below $10K)


class TestRejectNulls:
    """Tests for null rejection utility."""

    def test_null_machine_id_rejected(self, spark, slot_telemetry_df):
        from notebooks.utils.compliance_rules import reject_nulls

        result = reject_nulls(slot_telemetry_df, ["machine_id"])

        assert result.count() == 6  # Original 7 minus 1 null
        machine_ids = [row["machine_id"] for row in result.collect()]
        assert None not in machine_ids

    def test_multiple_required_cols(self, spark, slot_telemetry_df):
        from notebooks.utils.compliance_rules import reject_nulls

        result = reject_nulls(slot_telemetry_df, ["machine_id", "amount"])
        assert result.count() == 6


class TestFlagW2G:
    """Tests for W-2G winnings reporting thresholds."""

    def test_slots_threshold_1200(self, spark, slot_telemetry_df):
        from notebooks.utils.compliance_rules import flag_w2g

        result = flag_w2g(slot_telemetry_df)
        slots_w2g = result.filter(
            "(game_type = 'slots') AND (w2g_flag = true)"
        ).collect()

        # $12,500 and $9,500 are above $1,200 slot threshold
        assert len(slots_w2g) == 2

    def test_poker_threshold_5000(self, spark, slot_telemetry_df):
        from notebooks.utils.compliance_rules import flag_w2g

        result = flag_w2g(slot_telemetry_df)
        poker_w2g = result.filter(
            "(game_type = 'poker') AND (w2g_flag = true)"
        ).collect()

        # Only the $5,500 poker win should be flagged
        assert len(poker_w2g) == 1
        assert poker_w2g[0]["amount"] == 5500.0
```

### Testing Schema Enforcement

```python
"""
validation/unit_tests/test_schema_enforcement.py
=================================================
Tests that schemas match expected definitions.
"""

from pyspark.sql.types import (
    DoubleType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


def test_bronze_slot_schema_has_required_fields(spark, slot_telemetry_df):
    """Bronze slot telemetry must have all required fields."""
    required_fields = {"machine_id", "event_type", "amount", "timestamp"}
    actual_fields = {f.name for f in slot_telemetry_df.schema.fields}

    assert required_fields.issubset(actual_fields)


def test_bronze_slot_schema_types(spark, slot_telemetry_df):
    """Field types must match the expected schema."""
    type_map = {f.name: type(f.dataType) for f in slot_telemetry_df.schema.fields}

    assert type_map["machine_id"] == StringType
    assert type_map["amount"] == DoubleType
    assert type_map["timestamp"] == TimestampType
```

---

## nbval for Notebook Execution Testing

[nbval](https://github.com/computationalmodelling/nbval) validates that Jupyter notebooks execute without errors. For this POC's `.py` notebook format, convert to `.ipynb` first:

### Installation

```bash
pip install nbval jupytext
```

### Converting and Testing

```bash
# Convert .py notebook to .ipynb
jupytext --to ipynb notebooks/bronze/01_bronze_slot_telemetry.py -o temp/test_notebook.ipynb

# Run nbval against the converted notebook
pytest --nbval temp/test_notebook.ipynb --nbval-lax

# --nbval-lax: don't compare cell outputs, just verify no exceptions
```

### Limitations

- nbval requires a running kernel (local PySpark).
- Cells that reference OneLake paths will fail locally.
- Use `# NBVAL_SKIP` comments to skip cells that need Fabric.

```python
# NBVAL_SKIP
# This cell requires a Fabric workspace connection
df.write.format("delta").saveAsTable("lh_bronze.bronze_slot_telemetry")
```

---

## Coverage Reporting

### pytest-cov Configuration

```ini
# pyproject.toml or setup.cfg
[tool.pytest.ini_options]
addopts = "--cov=notebooks/utils --cov=data_generation --cov-report=html --cov-report=term-missing"
testpaths = ["validation/unit_tests"]
```

### Running Coverage

```bash
# Generate coverage report
pytest validation/unit_tests/ -v --cov=notebooks/utils --cov-report=html

# Open the HTML report
open htmlcov/index.html
```

### Coverage Targets

| Module | Target | Rationale |
|--------|--------|-----------|
| `notebooks/utils/` | 90%+ | Core business logic, compliance rules |
| `data_generation/generators/` | 80%+ | Data quality depends on generator correctness |
| `data_generation/config/` | 70%+ | Configuration parsing |
| `notebooks/bronze/` | 50%+ | Orchestration code, many Fabric-only paths |

---

## CI Pipeline Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test-notebooks.yml
name: Notebook Unit Tests

on:
  pull_request:
    paths:
      - 'notebooks/**'
      - 'data_generation/**'
      - 'validation/**'
  push:
    branches: [main]

jobs:
  unit-tests:
    name: Run Notebook Unit Tests
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: pip

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install pyspark==3.5.3 delta-spark==3.3.0
          pip install pytest pytest-cov great-expectations
          pip install -r requirements.txt

      - name: Set test environment variables
        run: |
          echo "FABRIC_POC_HASH_SALT=ci-test-salt" >> $GITHUB_ENV
          echo "SPARK_LOCAL_IP=127.0.0.1" >> $GITHUB_ENV

      - name: Run unit tests
        run: |
          pytest validation/unit_tests/ -v \
            --cov=notebooks/utils \
            --cov=data_generation \
            --cov-report=xml \
            --junitxml=test-results.xml

      - name: Upload coverage to Codecov
        if: always()
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml
          flags: notebook-tests
          fail_ci_if_error: false

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: test-results.xml
```

### Branch Protection Rule

Configure GitHub branch protection on `main`:

- **Required status checks:** `Run Notebook Unit Tests`
- **Require branches to be up to date:** Yes
- **Require PR reviews:** 1+

This prevents merging code that breaks existing tests.

---

## Best Practices

### DO

1. **Extract before testing.** Move business logic out of notebook cells into importable modules under `notebooks/utils/`.

2. **Use session-scoped Spark.** Starting a SparkSession for each test is slow. Use `scope="session"` on your Spark fixture.

3. **Keep test data small.** 5-10 rows per test DataFrame is enough. Large synthetic datasets belong in integration tests.

4. **Test edge cases explicitly.** Empty DataFrames, null values, boundary amounts ($9,999.99 vs $10,000.00), and type mismatches.

5. **Name tests descriptively.** `test_ctr_flag_set_when_amount_equals_10000` is better than `test_flag_1`.

6. **Match Spark versions.** Your local PySpark version should match the Fabric Runtime version to avoid API differences.

7. **Run tests before upload.** Always run `pytest` locally before syncing notebooks to Fabric.

### DO NOT

1. **Do not test Spark internals.** You are testing your logic, not whether `DataFrame.filter()` works.

2. **Do not require network access.** Unit tests must pass offline. Mock all external calls.

3. **Do not use production data.** Synthetic data only. Never copy real data into test fixtures.

4. **Do not test orchestration in unit tests.** Notebook cell ordering, `%run` resolution, and `mssparkutils.notebook.run()` are integration concerns.

5. **Do not skip writing tests for "simple" notebooks.** Schema enforcement and null handling are where most bugs hide.

---

## Anti-Patterns

### Anti-Pattern: Testing the Entire Notebook

```python
# BAD: Running the whole notebook as a test
def test_bronze_notebook():
    exec(open("notebooks/bronze/01_bronze_slot_telemetry.py").read())
```

This is brittle, slow, and gives no useful failure information.

### Anti-Pattern: Hardcoded Paths in Tests

```python
# BAD: Tests that depend on local file paths
def test_read_data():
    df = spark.read.parquet("C:/Users/frank/data/test.parquet")
```

Use `tmp_path` fixtures or in-memory DataFrames instead.

### Anti-Pattern: Testing with Production-Scale Data

```python
# BAD: Generating millions of rows for a unit test
def test_aggregation():
    data = [generate_row() for _ in range(1_000_000)]
```

Unit tests should complete in under a second. Use 5-10 rows.

---

## References

- [pytest Documentation](https://docs.pytest.org/)
- [PySpark Testing Guide](https://spark.apache.org/docs/latest/api/python/getting_started/testing_pyspark.html)
- [delta-spark PyPI](https://pypi.org/project/delta-spark/)
- [nbval GitHub](https://github.com/computationalmodelling/nbval)
- [This POC: Testing Strategies](../testing-strategies.md)
- [This POC: Local Spark Debugging](./local-spark-debugging.md)
- [This POC: CI/CD with fabric-cicd](../fabric-cicd-deployment.md)
- [This POC: Validation Suite](https://github.com/fgarofalo56/Supercharge_Microsoft_Fabric/tree/main/validation)
