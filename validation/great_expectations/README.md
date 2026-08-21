# Great Expectations Data Quality Validation

Comprehensive data quality validation framework for the Microsoft Fabric Casino/Gaming POC using Great Expectations 0.18+.

## Overview

This validation framework ensures data quality across all casino data domains throughout the medallion architecture (Bronze, Silver, Gold layers). It provides:

- **Domain-specific expectation suites** for each data type
- **Checkpoint configurations** for automated validation
- **Data Docs generation** for visual reporting
- **CI/CD integration** support

## Directory Structure

```
great_expectations/
├── great_expectations.yml      # Main configuration file
├── expectations/               # Expectation suite definitions
│   ├── slot_machine_suite.json
│   ├── player_suite.json
│   ├── compliance_suite.json
│   ├── financial_suite.json
│   ├── security_suite.json
│   ├── table_games_suite.json
│   ├── bronze_slot_telemetry_suite.json
│   ├── silver_slot_cleansed_suite.json
│   └── gold_slot_performance_suite.json
├── checkpoints/                # Validation checkpoint configs
│   ├── slot_machine_checkpoint.yml
│   ├── player_checkpoint.yml
│   ├── compliance_checkpoint.yml
│   ├── financial_checkpoint.yml
│   ├── security_checkpoint.yml
│   ├── table_games_checkpoint.yml
│   └── all_domains_checkpoint.yml
├── plugins/                    # Custom expectations (if any)
├── profilers/                  # Data profiler configs
├── uncommitted/                # Local artifacts (gitignored)
│   ├── validations/           # Validation results
│   └── data_docs/             # Generated documentation
└── README.md
```

## Expectation Suites

### 1. Slot Machine Suite (`slot_machine_suite.json`)

Validates slot machine telemetry data from SAS protocol events.

| Expectation | Description |
|-------------|-------------|
| `machine_id` format | Must match `SLOT-XXXX` pattern |
| `event_type` values | Must be in valid SAS event types |
| `coin_in` >= 0 | Non-negative wager amounts |
| `denomination` values | Valid slot denominations (0.01 to 100.00) |
| `jackpot_amount` > 0 | Must be positive when present |
| Natural key uniqueness | `machine_id + event_timestamp + event_type` |

**Usage:**
```bash
great_expectations checkpoint run slot_machine_checkpoint
```

### 2. Player Suite (`player_suite.json`)

Validates player/loyalty member profile data with PII protections.

| Expectation | Description |
|-------------|-------------|
| `player_id` format | Must match `P[digits]` pattern |
| `loyalty_tier` values | Bronze, Silver, Gold, Platinum, Diamond |
| `ssn_hash` length | Must be 64 characters (SHA-256) |
| `email` format | Must contain @ and valid domain |
| Age verification | `date_of_birth` indicates 21+ |
| Unique `player_id` | No duplicate player records |

**Usage:**
```bash
great_expectations checkpoint run player_checkpoint
```

### 3. Compliance Suite (`compliance_suite.json`)

Validates regulatory compliance filings (CTR, SAR, W-2G) for BSA compliance.

| Expectation | Description |
|-------------|-------------|
| `filing_type` values | CTR, SAR, or W2G only |
| CTR threshold | Amount >= $10,000 for CTR filings |
| W2G threshold | Amount >= $600 for W2G filings |
| Required fields | `filing_id`, `filing_type`, `amount`, `transaction_date` |
| `filing_status` values | PENDING, SUBMITTED, ACCEPTED, REJECTED |

**Usage:**
```bash
great_expectations checkpoint run compliance_checkpoint
```

### 4. Financial Suite (`financial_suite.json`)

Validates cage financial transaction data for reconciliation and CTR tracking.

| Expectation | Description |
|-------------|-------------|
| `transaction_id` format | TXN-XXXXXXXX or UUID format |
| `amount` > 0 | Transaction amounts must be positive |
| `ctr_required` flag | Boolean indicating $10,000+ threshold |
| `transaction_type` values | Valid cage transaction types |
| `currency` values | USD, CAD, MXN |
| Unique `transaction_id` | No duplicate transactions |

**Usage:**
```bash
great_expectations checkpoint run financial_checkpoint
```

### 5. Security Suite (`security_suite.json`)

Validates security and surveillance event data for incident tracking.

| Expectation | Description |
|-------------|-------------|
| `event_type` values | 20 valid security event types |
| `severity_level` values | LOW, MEDIUM, HIGH, CRITICAL |
| `location_id` format | Must match `LOC-XXX` pattern |
| Timestamp fields | `event_timestamp`, `response_timestamp`, `resolution_timestamp` |
| `resolution_status` values | PENDING, IN_PROGRESS, RESOLVED, ESCALATED, FALSE_ALARM |

**Usage:**
```bash
great_expectations checkpoint run security_checkpoint
```

### 6. Table Games Suite (`table_games_suite.json`)

Validates table games event data for all game types.

| Expectation | Description |
|-------------|-------------|
| `table_id` format | Must match `TBL-XX-XXX` pattern |
| `game_type` values | BLACKJACK, CRAPS, ROULETTE, BACCARAT, POKER |
| `event_type` values | 14 valid table game event types |
| `bet_amount` > 0 | Positive wager amounts when present |
| `seat_position` range | 1-8 (typical table max) |
| `cards_dealt` format | Rank+suit with hyphen separator |

**Usage:**
```bash
great_expectations checkpoint run table_games_checkpoint
```

## Quick Start

### Prerequisites

```bash
pip install great_expectations>=0.18.0
pip install pyspark  # For Spark execution engine
```

### Running Validations

#### Single Domain Validation

```bash
# Navigate to the great_expectations directory
cd validation/great_expectations

# Run specific checkpoint
great_expectations checkpoint run slot_machine_checkpoint
great_expectations checkpoint run player_checkpoint
great_expectations checkpoint run compliance_checkpoint
great_expectations checkpoint run financial_checkpoint
great_expectations checkpoint run security_checkpoint
great_expectations checkpoint run table_games_checkpoint
```

#### All Domains Validation

```bash
# Run comprehensive validation across all domains
great_expectations checkpoint run all_domains_checkpoint
```

### Viewing Data Docs

After running validations, view the generated reports:

```bash
great_expectations docs build
great_expectations docs open
```

Data Docs will be available at: `uncommitted/data_docs/local_site/index.html`

## Programmatic Usage

### Python Integration

```python
import great_expectations as gx
from great_expectations.core.batch import RuntimeBatchRequest
import pandas as pd

# Get GX context
context = gx.get_context(context_root_dir="validation/great_expectations")

# Load data
df = pd.read_parquet("sample-data/bronze/slot_telemetry.parquet")

# Create batch request
batch_request = RuntimeBatchRequest(
    datasource_name="casino_pandas",
    data_connector_name="runtime_data_connector",
    data_asset_name="slot_data",
    runtime_parameters={"batch_data": df},
    batch_identifiers={"default_identifier_name": "validation_run"},
)

# Run checkpoint with runtime batch
results = context.run_checkpoint(
    checkpoint_name="slot_machine_checkpoint",
    validations=[
        {"batch_request": batch_request, "expectation_suite_name": "slot_machine_suite"}
    ],
)

# Check results
if not results.success:
    print("Validation failed!")
    for result in results.run_results.values():
        print(result)
```

### Microsoft Fabric Notebook Integration

```python
# In Fabric Notebook
import great_expectations as gx
from pyspark.sql import SparkSession

# Get Spark session (already available in Fabric)
spark = SparkSession.builder.getOrCreate()

# Read from Lakehouse
df = spark.read.format("delta").table("bronze.slot_telemetry")

# Get GX context
context = gx.get_context()

# Create validator
validator = context.get_validator(
    datasource_name="casino_delta",
    data_connector_name="runtime_data_connector",
    data_asset_name="slot_telemetry",
    expectation_suite_name="slot_machine_suite",
    batch_identifiers={"table_name": "slot_telemetry", "layer": "bronze"},
    batch_data=df,
)

# Run validation
results = validator.validate()
print(f"Validation passed: {results.success}")
```

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/data-quality.yml
name: Data Quality Validation

on:
  push:
    paths:
      - 'data_generation/**'
      - 'validation/**'
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install great_expectations pandas pyarrow

      - name: Run validations
        working-directory: validation/great_expectations
        run: |
          great_expectations checkpoint run all_domains_checkpoint

      - name: Upload Data Docs
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: data-docs
          path: validation/great_expectations/uncommitted/data_docs/
```

## Compliance Thresholds Reference

| Filing Type | Threshold | Regulation |
|-------------|-----------|------------|
| CTR (Currency Transaction Report) | >= $10,000 | Bank Secrecy Act |
| SAR (Suspicious Activity Report) | Varies | Bank Secrecy Act |
| W-2G (Gambling Winnings) | >= $600 | IRS |
| W-2G Slots | >= $1,200 | IRS |

## Custom Expectations

To add custom expectations, create a Python file in the `plugins/` directory:

```python
# plugins/custom_expectations.py
from great_expectations.expectations.expectation import ColumnMapExpectation


class ExpectColumnValuesToBeValidMachineId(ColumnMapExpectation):
    """Expect column values to be valid casino machine IDs."""

    map_metric = "column_values.match_regex"
    success_keys = ("regex",)
    default_kwarg_values = {"regex": r"^(SLOT|TBL)-[A-Z0-9]{2,4}-[0-9]{3,4}$"}

    library_metadata = {
        "maturity": "experimental",
        "tags": ["casino", "machine_id"],
    }
```

## Troubleshooting

### Common Issues

1. **Spark not available**: Ensure PySpark is installed or use the Pandas execution engine for local testing.

2. **Missing data files**: The checkpoints expect data in `../sample-data/` directory. Generate sample data first.

3. **Checkpoint not found**: Ensure you're running from the `great_expectations/` directory.

4. **Validation always fails**: Check the `mostly` parameter on expectations - it allows for a percentage of failing rows.

### Debug Mode

```bash
# Run with verbose output
great_expectations checkpoint run slot_machine_checkpoint --verbosity DEBUG
```

## Additional Resources

- [Great Expectations Documentation](https://docs.greatexpectations.io/)
- [Expectation Gallery](https://greatexpectations.io/expectations/)
- [Microsoft Fabric Documentation](https://learn.microsoft.com/fabric/)
- [Project Architecture](../../ARCHITECTURE.md)

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01 | Initial validation framework |
| 1.1.0 | 2024-01 | Added all domain suites |
| 1.2.0 | 2024-01 | Added comprehensive checkpoints |
