#!/bin/bash
# =============================================================================
# Docker Entrypoint Script
# =============================================================================
# Handles different commands and provides proper signal handling
#
# Commands:
#   generate  - Generate batch data (default)
#   stream    - Stream events to Event Hub or stdout
#   validate  - Validate generated data
#   shell     - Start interactive shell
#   help      - Show usage information
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# Signal Handling
# -----------------------------------------------------------------------------
# Trap signals for graceful shutdown
cleanup() {
    echo ""
    echo "Received shutdown signal. Cleaning up..."
    # Kill any background processes
    if [ -n "$PID" ]; then
        kill -TERM "$PID" 2>/dev/null || true
        wait "$PID" 2>/dev/null || true
    fi
    echo "Shutdown complete."
    exit 0
}

trap cleanup SIGTERM SIGINT SIGQUIT

# -----------------------------------------------------------------------------
# Environment Setup
# -----------------------------------------------------------------------------
# Set defaults
OUTPUT_DIR="${DATA_OUTPUT_DIR:-/app/output}"
FORMAT="${DATA_FORMAT:-parquet}"
DAYS="${DATA_DAYS:-30}"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# -----------------------------------------------------------------------------
# Help Function
# -----------------------------------------------------------------------------
show_help() {
    cat << 'EOF'
=============================================================================
Microsoft Fabric Casino/Gaming POC - Data Generator
=============================================================================

USAGE:
    docker run fabric-data-generator <command> [options]

COMMANDS:
    generate    Generate batch data files (default)
    stream      Stream events to Azure Event Hub or stdout
    validate    Validate generated data files
    shell       Start an interactive bash shell
    help        Show this help message

GENERATE COMMAND:
    docker run -v ./output:/app/output fabric-data-generator generate [options]

    Options:
        --all               Generate all data types with default volumes
        --slots N           Generate N slot machine events
        --tables N          Generate N table game events
        --players N         Generate N player profiles
        --financial N       Generate N financial transactions
        --security N        Generate N security events
        --compliance N      Generate N compliance records
        --days N            Days of historical data (default: 30)
        --format FORMAT     Output format: parquet, json, csv (default: parquet)
        --output DIR        Output directory (default: /app/output)
        --seed N            Random seed for reproducibility
        --include-pii       Include unhashed PII (testing only)

    Examples:
        # Generate all data types with defaults
        docker run -v ./output:/app/output fabric-data-generator generate --all

        # Generate specific volumes
        docker run -v ./output:/app/output fabric-data-generator generate \
            --slots 100000 --players 5000 --days 14

        # Quick demo data
        docker run -v ./output:/app/output fabric-data-generator generate \
            --slots 1000 --players 100 --days 7

STREAM COMMAND:
    docker run fabric-data-generator stream [options]

    Options:
        --rate N            Events per second (default: 10)
        --duration N        Duration in seconds (optional, runs indefinitely if not set)
        --max-events N      Maximum events to generate (optional)
        --seed N            Random seed for reproducibility

    Environment Variables (for Azure Event Hub):
        EVENTHUB_CONNECTION_STRING    Event Hub connection string
        EVENTHUB_NAME                 Event Hub name

    Examples:
        # Stream to stdout (local testing)
        docker run fabric-data-generator stream --rate 5 --duration 60

        # Stream to Azure Event Hub
        docker run \
            -e EVENTHUB_CONNECTION_STRING="Endpoint=sb://..." \
            -e EVENTHUB_NAME="slot-telemetry" \
            fabric-data-generator stream --rate 100

VALIDATE COMMAND:
    docker run -v ./output:/app/output:ro fabric-data-generator validate [options]

    Options:
        --input DIR         Input directory to validate (default: /app/output)

ENVIRONMENT VARIABLES:
    DATA_OUTPUT_DIR             Output directory (default: /app/output)
    DATA_FORMAT                 Default output format (default: parquet)
    DATA_DAYS                   Default days of data (default: 30)
    EVENTHUB_CONNECTION_STRING  Azure Event Hub connection string
    EVENTHUB_NAME               Azure Event Hub name

VOLUMES:
    /app/output     Mount point for generated data files

=============================================================================
EOF
}

# -----------------------------------------------------------------------------
# Generate Command
# -----------------------------------------------------------------------------
run_generate() {
    echo "=============================================="
    echo "Microsoft Fabric Data Generator - Batch Mode"
    echo "=============================================="
    echo "Output Directory: $OUTPUT_DIR"
    echo "Default Format: $FORMAT"
    echo "Default Days: $DAYS"
    echo "=============================================="
    echo ""

    # Build command with defaults if not overridden
    # Note: In Docker, data_generation is copied as data_generation for valid Python imports
    CMD="python /app/data_generation/generate.py"

    # Pass all arguments to the generator
    if [ $# -eq 0 ]; then
        # No arguments - show generator help
        $CMD --help
    else
        # Add default output if not specified
        if [[ ! "$*" =~ "--output" ]] && [[ ! "$*" =~ "-o" ]]; then
            CMD="$CMD --output $OUTPUT_DIR"
        fi

        # Add default format if not specified
        if [[ ! "$*" =~ "--format" ]] && [[ ! "$*" =~ "-f" ]]; then
            CMD="$CMD --format $FORMAT"
        fi

        exec $CMD "$@"
    fi
}

# -----------------------------------------------------------------------------
# Stream Command
# -----------------------------------------------------------------------------
run_stream() {
    echo "=============================================="
    echo "Microsoft Fabric Data Generator - Stream Mode"
    echo "=============================================="

    if [ -n "$EVENTHUB_CONNECTION_STRING" ]; then
        echo "Target: Azure Event Hub ($EVENTHUB_NAME)"
    else
        echo "Target: stdout (no Event Hub configured)"
    fi
    echo "=============================================="
    echo ""

    # Note: In Docker, data_generation is copied as data_generation for valid Python imports
    CMD="python /app/data_generation/generators/streaming/event_hub_producer.py"

    # Add Event Hub config from environment if present
    if [ -n "$EVENTHUB_CONNECTION_STRING" ]; then
        CMD="$CMD --connection-string \"$EVENTHUB_CONNECTION_STRING\""
    fi

    if [ -n "$EVENTHUB_NAME" ]; then
        CMD="$CMD --eventhub-name \"$EVENTHUB_NAME\""
    fi

    # Execute with remaining arguments
    exec $CMD "$@" &
    PID=$!
    wait $PID
}

# -----------------------------------------------------------------------------
# Validate Command
# -----------------------------------------------------------------------------
run_validate() {
    echo "=============================================="
    echo "Microsoft Fabric Data Validator"
    echo "=============================================="

    INPUT_DIR="${1:-$OUTPUT_DIR}"
    echo "Validating data in: $INPUT_DIR"
    echo "=============================================="
    echo ""

    # Check if data exists
    if [ ! -d "$INPUT_DIR" ] || [ -z "$(ls -A $INPUT_DIR 2>/dev/null)" ]; then
        echo "ERROR: No data files found in $INPUT_DIR"
        echo "Generate data first with: docker run -v ./output:/app/output fabric-data-generator generate --all"
        exit 1
    fi

    # List files to validate
    echo "Files found:"
    ls -la "$INPUT_DIR"
    echo ""

    # Run validation (if validation script exists)
    if [ -f "/app/validation/great_expectations/validate_data.py" ]; then
        exec python /app/validation/great_expectations/validate_data.py --input "$INPUT_DIR"
    else
        # Basic validation - check file readability
        echo "Running basic validation..."
        python << PYEOF
import sys
from pathlib import Path
import pyarrow.parquet as pq
import pandas as pd

input_dir = Path("$INPUT_DIR")
errors = []
validated = 0

for f in input_dir.glob("*.parquet"):
    try:
        df = pq.read_table(f).to_pandas()
        print(f"OK: {f.name} - {len(df):,} records, {len(df.columns)} columns")
        validated += 1
    except Exception as e:
        errors.append(f"{f.name}: {e}")

for f in input_dir.glob("*.csv"):
    try:
        df = pd.read_csv(f)
        print(f"OK: {f.name} - {len(df):,} records, {len(df.columns)} columns")
        validated += 1
    except Exception as e:
        errors.append(f"{f.name}: {e}")

print(f"\nValidated {validated} files")

if errors:
    print(f"\n{len(errors)} errors found:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("All files valid!")
    sys.exit(0)
PYEOF
    fi
}

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
case "${1:-help}" in
    generate)
        shift
        run_generate "$@"
        ;;
    stream)
        shift
        run_stream "$@"
        ;;
    validate)
        shift
        run_validate "$@"
        ;;
    shell|bash|sh)
        exec /bin/bash
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        # If first arg looks like an option, assume generate command
        if [[ "$1" == --* ]] || [[ "$1" == -* ]]; then
            run_generate "$@"
        else
            echo "Unknown command: $1"
            echo "Run with 'help' to see available commands"
            exit 1
        fi
        ;;
esac
