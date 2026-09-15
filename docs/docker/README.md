# Docker Configuration for Microsoft Fabric Data Generator

This directory contains Docker configuration for running the Casino/Gaming POC data generators in a containerized environment.

## Quick Start

### Build the Image

```bash
# From repository root
docker build -t fabric-data-generator .

# Or use docker-compose
docker-compose build
```

### Generate Demo Data (Quick)

```bash
# Generate small dataset for quick testing
docker run --rm -v ./output:/app/output fabric-data-generator generate \
    --slots 1000 --players 100 --days 7

# Or use the demo service
docker-compose run --rm demo-generator
```

### Generate Full Dataset

```bash
# Generate complete dataset with defaults
docker run --rm -v ./output:/app/output fabric-data-generator generate --all

# Generate with custom parameters
docker run --rm -v ./output:/app/output fabric-data-generator generate \
    --all --days 30 --format parquet

# Or use docker-compose
docker-compose run --rm data-generator
```

## Commands

The container supports several commands:

| Command    | Description                                    |
| ---------- | ---------------------------------------------- |
| `generate` | Generate batch data files (default)            |
| `stream`   | Stream events to Azure Event Hub or stdout     |
| `validate` | Validate generated data files                  |
| `shell`    | Start an interactive bash shell                |
| `help`     | Show detailed usage information                |

### Generate Command

Generate batch data for Microsoft Fabric bronze layer:

```bash
# Generate all data types with default volumes
docker run --rm -v ./output:/app/output fabric-data-generator generate --all

# Generate specific data types
docker run --rm -v ./output:/app/output fabric-data-generator generate \
    --slots 100000 \
    --tables 50000 \
    --players 5000

# Generate with specific time range
docker run --rm -v ./output:/app/output fabric-data-generator generate \
    --all --days 14

# Generate in different format
docker run --rm -v ./output:/app/output fabric-data-generator generate \
    --all --format csv
```

**Options:**
- `--all`: Generate all data types with default volumes
- `--slots N`: Generate N slot machine events
- `--tables N`: Generate N table game events
- `--players N`: Generate N player profiles
- `--financial N`: Generate N financial transactions
- `--security N`: Generate N security events
- `--compliance N`: Generate N compliance records
- `--days N`: Days of historical data (default: 30)
- `--format FORMAT`: Output format: parquet, json, csv (default: parquet)
- `--seed N`: Random seed for reproducibility
- `--include-pii`: Include unhashed PII (testing only)

### Stream Command

Stream real-time events for testing Fabric Real-Time Intelligence:

```bash
# Stream to stdout (local testing)
docker run --rm fabric-data-generator stream --rate 5 --duration 60

# Stream to Azure Event Hub
docker run --rm \
    -e EVENTHUB_CONNECTION_STRING="Endpoint=sb://your-namespace.servicebus.windows.net/;SharedAccessKeyName=..." \
    -e EVENTHUB_NAME="slot-telemetry" \
    fabric-data-generator stream --rate 100

# Using docker-compose
export EVENTHUB_CONNECTION_STRING="your-connection-string"
export EVENTHUB_NAME="slot-telemetry"
docker-compose up streaming-generator
```

**Options:**
- `--rate N`: Events per second (default: 10)
- `--duration N`: Duration in seconds (optional)
- `--max-events N`: Maximum events to generate (optional)
- `--seed N`: Random seed for reproducibility

### Validate Command

Validate generated data files:

```bash
# Validate data in output directory
docker run --rm -v ./output:/app/output:ro fabric-data-generator validate

# Validate specific directory
docker run --rm -v /path/to/data:/data:ro fabric-data-generator validate --input /data
```

## Docker Compose Services

The `docker-compose.yml` provides several pre-configured services:

### data-generator

Full data generation service:

```bash
# Generate all data
docker-compose run --rm data-generator

# Pass custom options
docker-compose run --rm data-generator generate --slots 500000 --days 60
```

### streaming-generator

Long-running streaming service:

```bash
# Start streaming (runs in background)
docker-compose up -d streaming-generator

# View logs
docker-compose logs -f streaming-generator

# Stop streaming
docker-compose stop streaming-generator
```

### demo-generator

Quick demo data generation:

```bash
# Generate small dataset for demos
docker-compose run --rm demo-generator
```

### data-validator

Validate generated data:

```bash
# Run validation
docker-compose run --rm data-validator
```

## Environment Variables

| Variable                     | Default       | Description                           |
| ---------------------------- | ------------- | ------------------------------------- |
| `DATA_OUTPUT_DIR`            | `/app/output` | Output directory for generated data   |
| `DATA_FORMAT`                | `parquet`     | Default output format                 |
| `DATA_DAYS`                  | `30`          | Default days of historical data       |
| `EVENTHUB_CONNECTION_STRING` | (empty)       | Azure Event Hub connection string     |
| `EVENTHUB_NAME`              | (empty)       | Azure Event Hub name                  |
| `STREAMING_RATE`             | `10`          | Events per second for streaming       |
| `STREAMING_DURATION`         | `3600`        | Streaming duration in seconds         |

### Using .env File

Create a `.env` file in the repository root:

```bash
# Data generation settings
DATA_FORMAT=parquet
DATA_DAYS=30

# Azure Event Hub (for streaming)
EVENTHUB_CONNECTION_STRING=Endpoint=sb://your-namespace.servicebus.windows.net/;SharedAccessKeyName=...
EVENTHUB_NAME=slot-telemetry
STREAMING_RATE=100
```

## Volume Mounts

### Output Data

Mount a local directory to access generated data:

```bash
docker run -v ./output:/app/output fabric-data-generator generate --all
```

The generated files will be available at `./output/`:
- `bronze_slot_telemetry.parquet`
- `bronze_table_games.parquet`
- `bronze_player_profile.parquet`
- `bronze_financial_txn.parquet`
- `bronze_security_events.parquet`
- `bronze_compliance.parquet`
- `manifest.json` (metadata about the generation)

### Read-Only Validation

For validation, mount as read-only:

```bash
docker run -v ./output:/app/output:ro fabric-data-generator validate
```

## Resource Requirements

### Batch Generation

| Scale   | Records    | Memory | CPU  | Time    |
| ------- | ---------- | ------ | ---- | ------- |
| Small   | ~20K       | 1 GB   | 1    | ~30s    |
| Medium  | ~200K      | 2 GB   | 2    | ~2min   |
| Large   | ~700K      | 4 GB   | 4    | ~5min   |
| XLarge  | ~3M        | 8 GB   | 4    | ~15min  |

### Streaming

- Memory: 512 MB - 2 GB depending on rate
- CPU: 0.5 - 2 cores depending on rate

## Examples

### Scenario 1: POC Demo Preparation

Generate small dataset for a quick demo:

```bash
# Build image
docker build -t fabric-data-generator .

# Generate demo data
docker run --rm -v ./output:/app/output fabric-data-generator generate \
    --slots 5000 \
    --tables 2000 \
    --players 500 \
    --financial 1000 \
    --security 500 \
    --compliance 200 \
    --days 7 \
    --format parquet
```

### Scenario 2: Full POC Dataset

Generate complete dataset for thorough testing:

```bash
# Use docker-compose with defaults
docker-compose run --rm data-generator

# Or specify large dataset
docker run --rm -v ./output:/app/output fabric-data-generator generate \
    --all --days 90
```

### Scenario 3: Real-Time Testing

Test Fabric Real-Time Intelligence with streaming data:

```bash
# Local testing (stdout)
docker run --rm fabric-data-generator stream --rate 10 --duration 300

# With Azure Event Hub
docker run --rm \
    -e EVENTHUB_CONNECTION_STRING="$EVENTHUB_CONNECTION_STRING" \
    -e EVENTHUB_NAME="slot-telemetry" \
    fabric-data-generator stream --rate 100 --duration 3600
```

### Scenario 4: CI/CD Pipeline

Generate and validate data in a pipeline:

```bash
# Generate data
docker run --rm -v ./ci-output:/app/output fabric-data-generator generate \
    --all --seed 42 --days 7

# Validate output
docker run --rm -v ./ci-output:/app/output:ro fabric-data-generator validate
```

### Scenario 5: Custom Scale Dataset

Use the generate-all script with scale options:

```bash
# Enter container and run generate-all script
docker run --rm -v ./output:/app/output fabric-data-generator shell
./generate-all.sh --scale large --days 30 --format parquet
```

## Troubleshooting

### Image Build Issues

```bash
# Clean build (no cache)
docker build --no-cache -t fabric-data-generator .

# Check build logs
docker build -t fabric-data-generator . 2>&1 | tee build.log
```

### Memory Issues

If generation fails with memory errors:

```bash
# Increase container memory
docker run --rm --memory=8g -v ./output:/app/output fabric-data-generator generate --all

# Or generate in smaller batches
docker run --rm -v ./output:/app/output fabric-data-generator generate --slots 100000
docker run --rm -v ./output:/app/output fabric-data-generator generate --tables 50000
```

### Permission Issues

If output files have incorrect permissions:

```bash
# Run with current user
docker run --rm --user $(id -u):$(id -g) -v ./output:/app/output fabric-data-generator generate --all
```

### Event Hub Connection Issues

```bash
# Test Event Hub connectivity
docker run --rm \
    -e EVENTHUB_CONNECTION_STRING="$EVENTHUB_CONNECTION_STRING" \
    -e EVENTHUB_NAME="slot-telemetry" \
    fabric-data-generator stream --rate 1 --max-events 5
```

## Security Considerations

1. **Non-root User**: The container runs as a non-root user (`appuser`) for security
2. **No Secrets in Image**: Never bake credentials into the image; use environment variables
3. **Read-only Mounts**: Use `:ro` suffix for validation to prevent modifications
4. **Resource Limits**: Set appropriate memory/CPU limits to prevent resource exhaustion

## Integration with Microsoft Fabric

After generating data, upload to Fabric:

1. **Manual Upload**: Use Fabric Lakehouse UI to upload parquet files
2. **Azure Storage**: Copy to ADLS Gen2 and connect to Fabric
3. **Pipeline**: Use Fabric Data Pipelines to ingest from mounted storage

```bash
# Example: Copy to Azure Storage
az storage blob upload-batch \
    --account-name $STORAGE_ACCOUNT \
    --destination bronze \
    --source ./output \
    --pattern "*.parquet"
```
