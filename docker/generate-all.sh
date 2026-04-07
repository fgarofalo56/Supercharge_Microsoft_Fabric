#!/bin/bash
# =============================================================================
# Generate All Data Domains Script
# =============================================================================
# Generates complete dataset across all casino/gaming domains
# Suitable for POC demonstrations and testing
#
# Usage:
#   ./generate-all.sh                    # Default: 30 days, parquet format
#   ./generate-all.sh --days 7           # Quick demo: 7 days
#   ./generate-all.sh --format csv       # CSV output
#   ./generate-all.sh --scale large      # Large dataset
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
OUTPUT_DIR="${DATA_OUTPUT_DIR:-/app/output}"
FORMAT="${DATA_FORMAT:-parquet}"
DAYS="${DATA_DAYS:-30}"
SEED="${DATA_SEED:-42}"
SCALE="medium"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --days|-d)
            DAYS="$2"
            shift 2
            ;;
        --format|-f)
            FORMAT="$2"
            shift 2
            ;;
        --output|-o)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --seed|-s)
            SEED="$2"
            shift 2
            ;;
        --scale)
            SCALE="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --days, -d N       Number of days of data (default: 30)"
            echo "  --format, -f FMT   Output format: parquet, json, csv (default: parquet)"
            echo "  --output, -o DIR   Output directory (default: /app/output)"
            echo "  --seed, -s N       Random seed (default: 42)"
            echo "  --scale SCALE      Data scale: small, medium, large, xlarge (default: medium)"
            echo "  --help, -h         Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# -----------------------------------------------------------------------------
# Scale Configurations
# -----------------------------------------------------------------------------
case $SCALE in
    small|demo)
        SLOTS=10000
        TABLES=5000
        PLAYERS=500
        FINANCIAL=2500
        SECURITY=1000
        COMPLIANCE=500
        ;;
    medium|default)
        SLOTS=100000
        TABLES=50000
        PLAYERS=5000
        FINANCIAL=25000
        SECURITY=10000
        COMPLIANCE=5000
        ;;
    large)
        SLOTS=500000
        TABLES=100000
        PLAYERS=10000
        FINANCIAL=50000
        SECURITY=25000
        COMPLIANCE=10000
        ;;
    xlarge|production)
        SLOTS=2000000
        TABLES=500000
        PLAYERS=50000
        FINANCIAL=250000
        SECURITY=100000
        COMPLIANCE=50000
        ;;
    *)
        echo "Unknown scale: $SCALE"
        echo "Valid options: small, medium, large, xlarge"
        exit 1
        ;;
esac

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
echo "=============================================================================="
echo "Microsoft Fabric Casino/Gaming POC - Complete Data Generation"
echo "=============================================================================="
echo ""
echo "Configuration:"
echo "  Output Directory: $OUTPUT_DIR"
echo "  Output Format:    $FORMAT"
echo "  Historical Days:  $DAYS"
echo "  Random Seed:      $SEED"
echo "  Data Scale:       $SCALE"
echo ""
echo "Data Volumes:"
echo "  Slot Machine Events:     $(printf "%'d" $SLOTS)"
echo "  Table Game Events:       $(printf "%'d" $TABLES)"
echo "  Player Profiles:         $(printf "%'d" $PLAYERS)"
echo "  Financial Transactions:  $(printf "%'d" $FINANCIAL)"
echo "  Security Events:         $(printf "%'d" $SECURITY)"
echo "  Compliance Records:      $(printf "%'d" $COMPLIANCE)"
echo ""
echo "=============================================================================="
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Track start time
START_TIME=$(date +%s)

# -----------------------------------------------------------------------------
# Generate Data
# -----------------------------------------------------------------------------
# Note: In Docker, data_generation is copied as data_generation for valid Python imports
GENERATE_SCRIPT="/app/data_generation/generate.py"

echo "[1/6] Generating Slot Machine Telemetry..."
python "$GENERATE_SCRIPT" \
    --slots $SLOTS \
    --days $DAYS \
    --format $FORMAT \
    --output "$OUTPUT_DIR" \
    --seed $SEED

echo ""
echo "[2/6] Generating Table Game Events..."
python "$GENERATE_SCRIPT" \
    --tables $TABLES \
    --days $DAYS \
    --format $FORMAT \
    --output "$OUTPUT_DIR" \
    --seed $((SEED + 1))

echo ""
echo "[3/6] Generating Player Profiles..."
python "$GENERATE_SCRIPT" \
    --players $PLAYERS \
    --days $DAYS \
    --format $FORMAT \
    --output "$OUTPUT_DIR" \
    --seed $((SEED + 2))

echo ""
echo "[4/6] Generating Financial Transactions..."
python "$GENERATE_SCRIPT" \
    --financial $FINANCIAL \
    --days $DAYS \
    --format $FORMAT \
    --output "$OUTPUT_DIR" \
    --seed $((SEED + 3))

echo ""
echo "[5/6] Generating Security Events..."
python "$GENERATE_SCRIPT" \
    --security $SECURITY \
    --days $DAYS \
    --format $FORMAT \
    --output "$OUTPUT_DIR" \
    --seed $((SEED + 4))

echo ""
echo "[6/6] Generating Compliance Records..."
python "$GENERATE_SCRIPT" \
    --compliance $COMPLIANCE \
    --days $DAYS \
    --format $FORMAT \
    --output "$OUTPUT_DIR" \
    --seed $((SEED + 5))

# Calculate elapsed time
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))
SECONDS=$((ELAPSED % 60))

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo ""
echo "=============================================================================="
echo "GENERATION COMPLETE"
echo "=============================================================================="
echo ""
echo "Output Files:"
ls -lh "$OUTPUT_DIR"/*.${FORMAT} 2>/dev/null || ls -lh "$OUTPUT_DIR"/*
echo ""
echo "Total Size: $(du -sh "$OUTPUT_DIR" | cut -f1)"
echo "Time Elapsed: ${MINUTES}m ${SECONDS}s"
echo ""
echo "Data is ready for upload to Microsoft Fabric!"
echo "=============================================================================="

# Create manifest file
cat > "$OUTPUT_DIR/manifest.json" << EOF
{
  "generated_at": "$(date -Iseconds)",
  "generator_version": "1.0.0",
  "configuration": {
    "days": $DAYS,
    "format": "$FORMAT",
    "seed": $SEED,
    "scale": "$SCALE"
  },
  "volumes": {
    "slot_machine_events": $SLOTS,
    "table_game_events": $TABLES,
    "player_profiles": $PLAYERS,
    "financial_transactions": $FINANCIAL,
    "security_events": $SECURITY,
    "compliance_records": $COMPLIANCE
  },
  "files": [
    "bronze_slot_telemetry.$FORMAT",
    "bronze_table_games.$FORMAT",
    "bronze_player_profile.$FORMAT",
    "bronze_financial_txn.$FORMAT",
    "bronze_security_events.$FORMAT",
    "bronze_compliance.$FORMAT"
  ]
}
EOF

echo "Manifest saved to: $OUTPUT_DIR/manifest.json"
