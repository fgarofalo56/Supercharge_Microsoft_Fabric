# 🎲 Data Generation

> **[Home](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/blob/main/README.md)** | **[Tutorials](../tutorials/)** | **[Notebooks](../notebooks/)** | **[Validation](../validation/)**

Synthetic data generators for casino/gaming, federal agencies, streaming CDC, and analytics scenarios in the Microsoft Fabric POC.

---

!!! info "Third-party references — publicly sourced, good-faith comparison"
    This page references non-Microsoft products and services (for example, IBM DB2 and Oracle as simulated CDC source systems). That information is drawn from each vendor's **publicly available documentation** and is offered for honest, good-faith comparison only. This is a personal project written from a Microsoft Fabric and Azure perspective; it does **not** claim expertise in, or authority over, any third-party product, and nothing here is an official statement by, or endorsed by, those vendors. Capabilities, pricing, and features change often — always verify against the vendor's current official documentation. Where a third-party offering is the stronger choice, we say so plainly.

---

## Overview

```
+------------------+     +------------------+     +------------------+
|  Configuration   |     |    Generators    |     |     Output       |
+------------------+     +------------------+     +------------------+
|  - Date range    | --> | Casino (6)       | --> | Parquet (default)|
|  - Volume        |     | Federal (7)      |     | CSV              |
|  - Seed          |     | Streaming (3)    |     | JSON             |
|  - PII handling  |     | Analytics (3)    |     |                  |
|                  |     |                  |     | Bronze Layer     |
|                  |     | 16 generators    |     | Ready            |
+------------------+     +------------------+     +------------------+
```

---

## Quick Start

### Option 1: Docker (Recommended)

The fastest way to generate data without installing dependencies.

```bash
# Generate demo dataset (quick, small)
docker-compose run --rm demo-generator

# Generate full dataset (30 days, all domains)
docker-compose run --rm data-generator

# Generate with custom parameters
docker-compose run --rm data-generator --all --days 14 --format parquet

# Stream events to Azure Event Hub
EVENTHUB_CONNECTION_STRING="your-connection" docker-compose up streaming-generator
```

Output will be in the `./output` directory.

### Option 2: Local Python

```bash
# Install dependencies
pip install -r ../requirements.txt

# Generate all data with default volumes
python generate.py --all --days 30

# Generate specific data types
python generate.py --slots 100000 --players 5000

# Output to different format
python generate.py --all --format csv --output ./csv_output
```

### Option 3: Use Sample Data

Pre-generated sample datasets are available for quick exploration:

```bash
# View available sample data
ls ../sample-data/bronze/

# Copy sample data to output
cp -r ../sample-data/bronze/* ./output/
```

See [Sample Data](#sample-data) section for details.

---

## Data Generators

| Generator | Output Table | Description | Key Fields |
|-----------|--------------|-------------|------------|
| `SlotMachineGenerator` | `bronze_slot_telemetry` | Slot machine events, meters, jackpots | `machine_id`, `coin_in`, `coin_out`, `jackpot_amount` |
| `TableGameGenerator` | `bronze_table_games` | Table game transactions, ratings | `table_id`, `game_type`, `bet_amount`, `result` |
| `PlayerGenerator` | `bronze_player_profile` | Player demographics, loyalty | `player_id`, `loyalty_tier`, `ssn_hash` |
| `FinancialGenerator` | `bronze_financial_txn` | Cage transactions, markers | `txn_id`, `amount`, `ctr_flag` |
| `SecurityGenerator` | `bronze_security_events` | Access control, surveillance | `event_id`, `location`, `threat_level` |
| `ComplianceGenerator` | `bronze_compliance` | CTR, SAR, W-2G filings | `filing_type`, `amount`, `status` |

### 🏛️ Federal Agency Generators

| Generator | Output Table | Description | Key Fields |
|-----------|--------------|-------------|------------|
| `USDAGenerator` | `bronze_usda_crop_production` | Crop yields, food safety recalls | `commodity`, `yield_per_acre`, `recall_class` |
| `SBAGenerator` | `bronze_sba_loans` | PPP, 7(a), disaster, SBIR loans | `program_type`, `loan_amount`, `naics_code` |
| `NOAAGenerator` | `bronze_noaa_weather` | Weather observations, storm events | `station_id`, `parameter`, `event_type` |
| `EPAGenerator` | `bronze_epa_air_quality` | Air quality (AQI), water quality (MCL) | `aqi_value`, `pollutant`, `mcl_violation` |
| `DOIGenerator` | `bronze_doi_earthquakes` | Earthquakes, land use management | `magnitude`, `depth_km`, `managing_agency` |
| `TribalHealthcareGenerator` | `bronze_tribal_health` | IHS encounters, pharmacy, lab | `icd10_code`, `tribal_affiliation`, `encounter_type` |
| `DOTFAAGenerator` | `bronze_dot_flight_ops` | Flight operations, safety incidents | `carrier_code`, `delay_minutes`, `incident_type` |

### 🔄 Streaming Generators

| Generator | Output Table | Description | Key Fields |
|-----------|--------------|-------------|------------|
| `MultiSourceSimulator` | CDC events | 5 CDC sources (SQL Server, Azure SQL, Cosmos DB, DB2, Oracle) | `source_type`, `operation`, `before_image` |
| `IoTDeviceSimulator` | IoT telemetry | 7 device types (slot, roulette, HVAC, camera, elevator, etc.) | `device_type`, `telemetry`, `protocol` |
| `EventHubProducer` | Event Hub | Real-time event streaming to Azure Event Hub | `event_hub_name`, `connection_string` |

### 📊 Analytics Generators

| Generator | Output Table | Description | Key Fields |
|-----------|--------------|-------------|------------|
| `VideoAnalyticsGenerator` | `bronze_video_events` | 50 cameras, 8 event types, YOLO/DeepSORT | `camera_id`, `event_type`, `confidence_score` |
| `PeopleMovementGenerator` | `bronze_movement_events` | 30 zones, 6 sensor types, queue detection | `sensor_id`, `person_count`, `dwell_time_seconds` |
| `GeolocationGenerator` | `bronze_geolocation` | 200 devices, H3 indexing, geofencing | `device_id`, `h3_index`, `geofence_event` |

> [!NOTE]
> All generators inherit from `BaseGenerator` and support `seed` for reproducibility, `generate_record()` for single records, and `generate_batch(count)` for bulk generation.

---

## Default Volumes

When using `--all`, the following volumes are generated:

| Data Type | Records | Est. Size | Bronze Table |
|-----------|---------|-----------|--------------|
| Slot Events | 500,000 | ~500 MB | `bronze_slot_telemetry` |
| Table Games | 100,000 | ~100 MB | `bronze_table_games` |
| Players | 10,000 | ~10 MB | `bronze_player_profile` |
| Financial | 50,000 | ~50 MB | `bronze_financial_txn` |
| Security | 25,000 | ~25 MB | `bronze_security_events` |
| Compliance | 10,000 | ~10 MB | `bronze_compliance` |
| **Total** | **~700,000** | **~700 MB** | |

> **Note:** Volumes can be scaled up or down using command line options.

---

## Command Line Options

```
usage: generate.py [-h] [--output OUTPUT] [--format {parquet,json,csv}]
                   [--days DAYS] [--seed SEED] [--all]
                   [--slots SLOTS] [--tables TABLES] [--players PLAYERS]
                   [--financial FINANCIAL] [--security SECURITY]
                   [--compliance COMPLIANCE] [--include-pii]

Options:
  --output, -o     Output directory (default: ./output)
  --format, -f     Output format: parquet, json, csv (default: parquet)
  --days, -d       Days of historical data (default: 30)
  --seed, -s       Random seed for reproducibility (default: 42)
  --all, -a        Generate all data types
  --slots          Number of slot machine events
  --tables         Number of table game events
  --players        Number of player profiles
  --financial      Number of financial transactions
  --security       Number of security events
  --compliance     Number of compliance records
  --include-pii    Include raw PII (testing only)
```

---

## Using Generators Programmatically

```python
from generators import SlotMachineGenerator, PlayerGenerator
from datetime import datetime, timedelta

# Configure date range
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

# Generate slot machine data
slot_gen = SlotMachineGenerator(
    num_machines=500,
    seed=42,
    start_date=start_date,
    end_date=end_date,
)

# Generate 10,000 events
df = slot_gen.generate(10000)

# Save to parquet
slot_gen.to_parquet(df, "output/slot_events.parquet")

# Generate in batches (memory efficient)
for batch in slot_gen.generate_batches(100000, batch_size=10000):
    process_batch(batch)
```

---

## Sample Output Preview

### Slot Machine Events

```json
{
  "event_id": "evt_a1b2c3d4",
  "machine_id": "SM-0042",
  "asset_number": "A-12345",
  "event_type": "PLAY",
  "event_timestamp": "2024-01-15T14:32:18Z",
  "denomination": 0.25,
  "coin_in": 100.00,
  "coin_out": 85.50,
  "games_played": 400,
  "theoretical_hold": 8.5,
  "actual_hold": 14.5,
  "player_id": "PLY-98765"
}
```

### Player Profile

```json
{
  "player_id": "PLY-98765",
  "loyalty_number": "GOLD-2024-00123",
  "first_name": "J***",
  "last_name": "S***",
  "ssn_hash": "sha256:a1b2c3...",
  "ssn_masked": "XXX-XX-1234",
  "loyalty_tier": "Gold",
  "points_balance": 15420,
  "total_theo": 12500.00,
  "vip_flag": true
}
```

---

## Data Quality Features

All generators include:

| Feature | Description |
|---------|-------------|
| **Consistent Schemas** | Matching Delta Lake table definitions |
| **Referential Integrity** | Player IDs, Machine IDs cross-reference correctly |
| **Realistic Distributions** | Based on industry patterns and statistics |
| **Compliance Logic** | CTR $10K threshold, W-2G $1,200 threshold |
| **PII Protection** | Hashing, masking enabled by default |
| **Reproducibility** | Seed-based generation for consistent results |

---

## PII Handling

> **Warning:** By default, PII is protected. Use `--include-pii` only for testing/development.

| PII Type | Default Handling | Example Output |
|----------|------------------|----------------|
| SSN | Hashed + Masked | `XXX-XX-1234` |
| Names | First initial only | `J*** S***` |
| Addresses | Hashed | `sha256:abc123...` |
| Card Numbers | Masked | `****-****-****-1234` |
| Phone | Partial mask | `(***) ***-4567` |
| Email | Domain only | `j***@example.com` |

---

## Compliance Data

The compliance generator includes realistic patterns for regulatory filings:

### CTR (Currency Transaction Reports)

| Field | Value |
|-------|-------|
| Threshold | >= $10,000 |
| Filing Deadline | 15 days |
| Includes | Cash-in/cash-out breakdown |

### SAR (Suspicious Activity Reports)

| Field | Value |
|-------|-------|
| Triggers | Pattern detection (structuring) |
| Categories | Multiple (layering, structuring, etc.) |
| Filing Deadline | 30 days |
| Includes | Narrative generation |

### W-2G (Gambling Winnings)

| Game Type | Threshold |
|-----------|-----------|
| Slots | >= $1,200 |
| Keno | >= $1,500 |
| Poker Tournaments | >= $5,000 |
| Table Games | >= $600 (300:1 odds) |

---

## Output Schemas

### Slot Machine Events

```
event_id, machine_id, asset_number, location_id, zone,
event_type, event_timestamp, denomination, coin_in, coin_out,
jackpot_amount, games_played, theoretical_hold, actual_hold,
player_id, session_id, machine_type, manufacturer, game_theme,
error_code, error_message, _ingested_at, _source, _batch_id
```

### Player Profiles

```
player_id, loyalty_number, first_name, last_name, email,
phone, date_of_birth, ssn_hash, ssn_masked, address_line1,
city, state, zip_code, country, loyalty_tier, points_balance,
lifetime_points, tier_credits, enrollment_date, last_visit_date,
total_visits, total_theo, total_actual_win_loss, average_daily_theo,
preferred_game, communication_preference, marketing_opt_in,
marketing_channel, host_assigned, vip_flag, self_excluded,
account_status, _ingested_at, _source, _batch_id
```

> **Tip:** See individual generator docstrings for complete schema documentation.

---

## Directory Structure

```
data_generation/
├── 📁 generators/
│   ├── __init__.py
│   ├── base_generator.py              # Base class for all generators
│   ├── slot_machine.py                # 🎰 Slot telemetry
│   ├── table_game.py                  # 🎲 Table games
│   ├── player.py                      # 👤 Player profiles
│   ├── financial.py                   # 💰 Financial transactions
│   ├── security.py                    # 🔒 Security events
│   ├── compliance.py                  # 📋 Compliance filings
│   ├── 📁 federal/                    # 🏛️ Federal agency generators
│   │   ├── usda_generator.py          # USDA agriculture
│   │   ├── sba_generator.py           # SBA small business
│   │   ├── noaa_generator.py          # NOAA weather
│   │   ├── epa_generator.py           # EPA environment
│   │   ├── doi_generator.py           # DOI interior
│   │   ├── tribal_healthcare_generator.py  # IHS healthcare
│   │   └── dot_faa_generator.py       # DOT/FAA aviation
│   ├── 📁 streaming/                  # 🔄 Streaming simulators
│   │   ├── multi_source_simulator.py  # CDC from 5 sources
│   │   ├── iot_device_simulator.py    # IoT device fleet
│   │   └── event_hub_producer.py      # Event Hub streaming
│   └── 📁 analytics/                  # 📊 Analytics generators
│       ├── video_analytics_generator.py    # Video security
│       ├── people_movement_generator.py    # Foot traffic
│       └── geolocation_generator.py        # Geolocation/H3
├── 📁 schemas/                        # JSON Schema definitions
│   ├── slot_telemetry_schema.json     # Casino schemas (5)
│   ├── 📁 federal/                    # Federal schemas (11)
│   ├── 📁 streaming/                  # Streaming schemas (3)
│   └── 📁 analytics/                  # Analytics schemas (3)
├── 📁 config/                         # Configuration files
│   ├── generator_config.yaml
│   ├── federal_datasets.yaml          # Federal open dataset catalog
│   └── streaming_sources.yaml         # Streaming source config
├── 📁 output/                         # Default output directory
├── generate.py                        # Main CLI entry point
└── README.md
```

---

## Sample Data

Pre-generated sample datasets are available for quick exploration without running generators.

### Available Sample Datasets

| Dataset | Records | Format | Location |
|---------|---------|--------|----------|
| Slot Telemetry | 10,000 | CSV/Parquet | `../sample-data/bronze/slot_telemetry_sample.*` |
| Player Profiles | 500 | CSV/Parquet | `../sample-data/bronze/player_profiles_sample.*` |
| Table Games | 2,000 | CSV/Parquet | `../sample-data/bronze/table_games_sample.*` |
| Financial | 1,000 | CSV/Parquet | `../sample-data/bronze/financial_sample.*` |

### Using Sample Data

```python
import pandas as pd

# Load sample slot data
df = pd.read_parquet("../sample-data/bronze/slot_telemetry_sample.parquet")
print(f"Records: {len(df)}")
print(df.head())

# Or use CSV
df = pd.read_csv("../sample-data/bronze/slot_telemetry_sample.csv")
```

### Schema Definitions

Schema definitions are available in `../sample-data/schemas/` describing:
- Column names and data types
- Business descriptions
- Valid value ranges
- PII handling requirements

---

## Docker Reference

### Docker Compose Services

| Service | Command | Description |
|---------|---------|-------------|
| `data-generator` | `docker-compose run --rm data-generator` | Full 30-day dataset |
| `demo-generator` | `docker-compose run --rm demo-generator` | Quick demo dataset |
| `streaming-generator` | `docker-compose up streaming-generator` | Event Hub streaming |
| `data-validator` | `docker-compose run --rm data-validator` | Validate output |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_FORMAT` | `parquet` | Output format (parquet, csv, json) |
| `DATA_DAYS` | `30` | Days of historical data |
| `DATA_OUTPUT_DIR` | `/app/output` | Output directory |
| `EVENTHUB_CONNECTION_STRING` | - | Azure Event Hub connection |
| `EVENTHUB_NAME` | `slot-telemetry` | Event Hub name |
| `STREAMING_RATE` | `10` | Events per second |

### Building the Docker Image

```bash
# Build from project root
docker-compose build data-generator

# Build with specific tag
docker build -t fabric-data-generator:v1.1.0 .

# Run without docker-compose
docker run -v ./output:/app/output fabric-data-generator --all --days 7
```

---

## 📑 JSON Schemas

All generators have matching JSON Schema (draft-07) definitions:

| Category | Schemas | Total Properties |
|----------|---------|-----------------|
| Casino/Gaming | 5 | 85 |
| Federal Agencies | 11 | 297 |
| Streaming | 3 | 62 |
| Analytics | 3 | 68 |
| **Total** | **22** | **512** |

Schema files are in `schemas/` with subdirectories for each category.

---

## Related Resources

| Resource | Description |
|----------|-------------|
| [Bronze Layer Tutorial](../tutorials/01-bronze-layer/README.md) | How to ingest generated data |
| [Validation Tests](../validation/README.md) | Data quality testing |
| [Notebooks](../notebooks/README.md) | Fabric notebooks for processing |
| [Sample Data](../sample-data/) | Pre-generated datasets |
| [Docker Compose](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/blob/main/docker-compose.yml) | Container orchestration |

---

<div align="center" markdown>

**[Back to Top](#slot_machine-data_generation)** | **[Main README](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/blob/main/README.md)**

</div>
