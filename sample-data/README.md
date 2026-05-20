# Sample Data for Microsoft Fabric Casino/Gaming POC

This directory contains pre-generated sample datasets for demonstrating and exploring the Microsoft Fabric Casino/Gaming POC without needing to run the full data generation pipeline.

## Quick Start

The sample data is ready to use immediately. Simply load the CSV files from the `bronze/` directory into your preferred tool (Excel, Power BI, Fabric notebooks, etc.).

```python
# Example: Load in Python
import pandas as pd

slot_data = pd.read_csv("bronze/slot_telemetry_sample.csv")
player_data = pd.read_csv("bronze/player_profile_sample.csv")
```

## Directory Structure

```
sample-data/
├── README.md                    # This file
├── generate_samples.py          # Script to regenerate sample data
├── bronze/                      # Pre-generated sample CSV/Parquet files
│   ├── slot_telemetry_sample.csv
│   ├── player_profile_sample.csv
│   ├── table_games_sample.csv
│   ├── financial_transactions_sample.csv
│   ├── security_events_sample.csv
│   └── compliance_filings_sample.csv
└── schemas/                     # JSON schema definitions (symlink)
```

## Sample Datasets

### 1. Slot Machine Telemetry (`slot_telemetry_sample.csv`)

**Records:** 90 rows (pre-generated) / 500 rows (with generator)
**Description:** Slot machine events following SAS protocol patterns

| Column | Type | Description |
|--------|------|-------------|
| event_id | string | Unique event identifier |
| machine_id | string | Machine ID (SLOT-0001 format) |
| asset_number | string | Asset tracking number |
| location_id | string | Floor location |
| zone | string | Casino zone (North, VIP, High Limit, etc.) |
| event_type | string | GAME_PLAY, JACKPOT, METER_UPDATE, BILL_IN, etc. |
| event_timestamp | datetime | ISO 8601 timestamp |
| denomination | float | Machine denomination ($0.01-$100.00) |
| coin_in | float | Amount wagered |
| coin_out | float | Amount paid out |
| jackpot_amount | float | Jackpot amount (if applicable) |
| games_played | int | Number of games in session |
| player_id | string | Player ID (if carded play) |
| session_id | string | Session identifier |
| machine_type | string | Video Slots, Mechanical Reels, etc. |
| manufacturer | string | IGT, Aristocrat, Konami, etc. |

**Key Features for Demo:**
- Includes 5+ jackpot events for payout analysis
- Mix of carded and uncarded play
- Various denominations and machine types
- Error/tilt events for maintenance analysis

---

### 2. Player Profiles (`player_profile_sample.csv`)

**Records:** 25 rows (pre-generated) / 100 rows (with generator)
**Description:** Loyalty program member profiles with masked PII

| Column | Type | Description |
|--------|------|-------------|
| player_id | string | Unique player identifier |
| loyalty_number | string | Loyalty card number |
| first_name | string | Masked first name (J***) |
| last_name | string | Masked last name (S***) |
| email | string | Hashed email address |
| phone | string | Masked phone (***-***-1234) |
| date_of_birth | date | DOB (21+ verified) |
| ssn_hash | string | SHA-256 hash of SSN |
| ssn_masked | string | XXX-XX-1234 format |
| city | string | City |
| state | string | State abbreviation |
| loyalty_tier | string | Bronze, Silver, Gold, Platinum, Diamond |
| points_balance | int | Current point balance |
| lifetime_points | int | Total lifetime points |
| enrollment_date | date | Program enrollment date |
| last_visit_date | date | Most recent visit |
| total_theo | float | Lifetime theoretical win |
| preferred_game | string | Favorite game type |
| vip_flag | bool | VIP status indicator |
| self_excluded | bool | Responsible gaming flag |

**Key Features for Demo:**
- Realistic tier distribution (40% Bronze, 30% Silver, etc.)
- VIP and Diamond tier players for high-value analysis
- PII properly masked for compliance demonstration
- Self-exclusion flags for responsible gaming

---

### 3. Table Games (`table_games_sample.csv`)

**Records:** 40 rows (pre-generated) / 200 rows (with generator)
**Description:** Table game transactions and player ratings

| Column | Type | Description |
|--------|------|-------------|
| event_id | string | Unique event identifier |
| table_id | string | Table identifier |
| game_type | string | Blackjack, Craps, Roulette, etc. |
| table_number | int | Physical table number |
| zone | string | Pit location |
| event_type | string | BUY_IN, CASH_OUT, RATING_START, etc. |
| event_timestamp | datetime | Transaction timestamp |
| player_id | string | Player ID (if rated) |
| dealer_id | string | Dealer employee ID |
| shift | string | Day, Swing, Grave |
| amount | float | Transaction amount |
| min_bet | float | Table minimum |
| max_bet | float | Table maximum |
| average_bet | float | Player average bet |
| hands_played | int | Hands in rating period |
| hours_played | float | Duration of play |
| theoretical_win | float | Calculated theo |
| marker_number | string | Marker reference (if credit) |

**Key Features for Demo:**
- Multiple game types with realistic distributions
- Buy-in and cash-out transactions
- Player rating data for host assignments
- Marker/credit transactions

---

### 4. Financial Transactions (`financial_transactions_sample.csv`)

**Records:** 30 rows (pre-generated) / 200 rows (with generator)
**Description:** Cage and cashier transactions

| Column | Type | Description |
|--------|------|-------------|
| transaction_id | string | Unique transaction ID |
| transaction_type | string | CASH_IN, CHIP_REDEMPTION, MARKER_ISSUE, etc. |
| transaction_timestamp | datetime | Transaction time |
| cage_location | string | Cage window location |
| cashier_id | string | Cashier employee ID |
| supervisor_id | string | Supervisor (for large txns) |
| player_id | string | Customer player ID |
| amount | float | Transaction amount |
| currency | string | Currency code (USD) |
| payment_method | string | Cash, Check, Wire, Chip |
| ctr_required | bool | CTR threshold flag ($10,000+) |
| ctr_filed | bool | CTR filing status |
| ctr_reference | string | FinCEN reference number |
| suspicious_activity_flag | bool | SAR review flag |
| shift | string | Day, Swing, Grave |
| business_date | date | Gaming day |

**Key Features for Demo:**
- 10+ transactions above CTR threshold ($10,000)
- Suspicious activity flags for AML review
- Wire transfers and marker transactions
- Check cashing with ID verification

---

### 5. Security Events (`security_events_sample.csv`)

**Records:** 30 rows (pre-generated) / 150 rows (with generator)
**Description:** Security and surveillance event log

| Column | Type | Description |
|--------|------|-------------|
| event_id | string | Unique event identifier |
| event_type | string | BADGE_SWIPE, CAMERA_ALERT, INCIDENT_REPORT, etc. |
| event_timestamp | datetime | Event timestamp |
| zone | string | Physical location |
| location_detail | string | Specific location |
| security_level | string | Public, Employee, Restricted, High Security |
| severity_level | string | LOW, MEDIUM, HIGH, CRITICAL |
| employee_id | string | Employee (for badge events) |
| badge_number | string | Badge ID |
| camera_id | string | Camera identifier |
| access_granted | bool | Access result |
| access_denied_reason | string | Denial reason |
| incident_number | string | Incident reference |
| incident_category | string | Theft, Medical, Disturbance, etc. |
| responding_officer_id | string | Security officer |
| resolution_status | string | Open, Investigating, Resolved |

**Key Features for Demo:**
- Access control events (granted/denied)
- Camera alerts and surveillance events
- Incident reports with categories
- Exclusion check events

---

### 6. Compliance Filings (`compliance_filings_sample.csv`)

**Records:** 20 rows (pre-generated) / 50 rows (with generator)
**Description:** Regulatory compliance filings (CTR, SAR, W-2G)

| Column | Type | Description |
|--------|------|-------------|
| filing_id | string | Unique filing identifier |
| filing_type | string | CTR, SAR, W2G |
| filing_timestamp | datetime | Filing creation time |
| filing_date | date | Actual filing date |
| due_date | date | Regulatory due date |
| status | string | Draft, Pending Review, Filed |
| player_id | string | Subject player ID |
| player_name_hash | string | Hashed player name |
| ssn_hash | string | Hashed SSN |
| ssn_masked | string | Masked SSN |
| transaction_date | date | Related transaction date |
| amount | float | Transaction/jackpot amount |
| game_type | string | Game type (for W-2G) |
| jackpot_amount | float | Jackpot amount (W-2G) |
| withholding_amount | float | Tax withholding |
| sar_category | string | SAR category (if SAR) |
| sar_narrative | string | SAR description |
| fincen_reference | string | FinCEN reference |
| irs_reference | string | IRS reference (W-2G) |
| compliance_officer_id | string | Responsible officer |

**Key Features for Demo:**
- Mix of CTR, SAR, and W-2G filings
- CTR filings above $10,000 threshold
- SAR filings with structuring patterns
- W-2G jackpot tax reporting

---

## Data Characteristics

### Referential Integrity

All sample datasets use consistent `player_id` values, allowing you to join across datasets:

```sql
-- Example: Join player profiles with slot activity
SELECT
    p.loyalty_tier,
    p.player_id,
    SUM(s.coin_in) as total_wagered,
    COUNT(DISTINCT s.session_id) as sessions
FROM player_profile_sample p
JOIN slot_telemetry_sample s ON p.player_id = s.player_id
GROUP BY p.loyalty_tier, p.player_id
```

### Date Range

All sample data is generated for **January 2024** (2024-01-01 to 2024-01-31).

### Reproducibility

Sample data was generated with **seed 42** for reproducibility. Running `generate_samples.py` with the same parameters will produce identical output.

### Edge Cases Included

The sample data intentionally includes edge cases for testing:

- **Jackpots**: At least 5 jackpot events in slot data
- **CTR Threshold**: 10+ transactions >= $10,000
- **Suspicious Activity**: Flagged transactions for SAR review
- **High-Value Players**: Diamond/Platinum tier members
- **Security Incidents**: Critical and high-severity events
- **Self-Exclusion**: Players with responsible gaming flags

---

## Regenerating Sample Data

To regenerate the sample data with different parameters:

```bash
# Install dependencies (if not already installed)
pip install -r ../requirements.txt

# Generate with defaults (seed=42, CSV format)
python generate_samples.py

# Generate with custom seed
python generate_samples.py --seed 123

# Generate larger datasets
python generate_samples.py --slots 2000 --players 500

# Generate both CSV and Parquet
python generate_samples.py --format both

# Generate to custom location
python generate_samples.py --output ./my-data

# Full customization
python generate_samples.py \
    --seed 42 \
    --slots 1000 \
    --players 200 \
    --tables 400 \
    --financial 400 \
    --security 300 \
    --compliance 100 \
    --start-date 2024-06-01 \
    --end-date 2024-06-30 \
    --format both
```

### Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--seed` | 42 | Random seed for reproducibility |
| `--format` | csv | Output format: csv, parquet, or both |
| `--output` | ./ | Output directory |
| `--slots` | 500 | Number of slot telemetry records |
| `--players` | 100 | Number of player profiles |
| `--tables` | 200 | Number of table game records |
| `--financial` | 200 | Number of financial transactions |
| `--security` | 150 | Number of security events |
| `--compliance` | 50 | Number of compliance filings |
| `--start-date` | 2024-01-01 | Start of date range |
| `--end-date` | 2024-01-31 | End of date range |

---

## Using with Microsoft Fabric

### Upload to Lakehouse

1. Open your Fabric workspace
2. Navigate to your Lakehouse
3. Click "Get data" > "Upload files"
4. Select the CSV files from `bronze/`
5. Files will be available as Delta tables

### Load in Notebook

```python
# Fabric Spark notebook
from pyspark.sql import SparkSession

# Read uploaded files
slot_df = spark.read.format("csv")\
    .option("header", "true")\
    .option("inferSchema", "true")\
    .load("Files/sample-data/bronze/slot_telemetry_sample.csv")

# Or if converted to Delta
slot_df = spark.read.format("delta").load("Tables/slot_telemetry")
```

### Power BI Connection

1. Open Power BI Desktop
2. Get Data > Text/CSV
3. Navigate to CSV files
4. Transform and load as needed

---

## File Sizes

The pre-generated samples are smaller representative datasets for quick demos:

| File | Rows | Approx Size (CSV) |
|------|------|-------------------|
| slot_telemetry_sample.csv | 90 | ~21 KB |
| player_profile_sample.csv | 25 | ~10 KB |
| table_games_sample.csv | 40 | ~8 KB |
| financial_transactions_sample.csv | 30 | ~7 KB |
| security_events_sample.csv | 30 | ~7 KB |
| compliance_filings_sample.csv | 20 | ~9 KB |
| **Total** | **235** | **~62 KB** |

For larger datasets, use the generator script:

```bash
# Generate full-size samples (recommended for POC demos)
python generate_samples.py --slots 500 --players 100 --tables 200 \
    --financial 200 --security 150 --compliance 50 --format both
```

---

## Schema Reference

JSON schema definitions are available in the `../data_generation/schemas/` directory:

- `slot_telemetry_schema.json`
- `player_profile_schema.json`
- `table_games_schema.json`
- `financial_transaction_schema.json`
- `security_events_schema.json`
- `compliance_filing_schema.json`

These schemas can be used for data validation in Fabric pipelines or Great Expectations.

---

## Questions?

For issues with sample data generation, check:

1. Python dependencies are installed (`pip install -r requirements.txt`)
2. Running from the correct directory
3. Sufficient disk space for output

For POC-related questions, see the main [README](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/blob/main/README.md) or [CONTRIBUTING](../CONTRIBUTING.md) guide.
