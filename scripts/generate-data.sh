#!/usr/bin/env bash
# =============================================================================
# Microsoft Fabric Casino/Gaming POC - Data Generation (Unix/Mac)
# =============================================================================
#
# SYNOPSIS:
#     Generate synthetic casino/gaming data for Microsoft Fabric POC.
#
# USAGE:
#     ./generate-data.sh [OPTIONS]
#
# OPTIONS:
#     --days N              Days of historical data (default: 30)
#     --slot-count N        Number of slot events (default: 500000)
#     --table-count N       Number of table events (default: 100000)
#     --player-count N      Number of players (default: 10000)
#     --financial-count N   Number of financial txns (default: 50000)
#     --security-count N    Number of security events (default: 25000)
#     --compliance-count N  Number of compliance filings (default: 10000)
#     --output-dir PATH     Output directory (default: ./data/generated)
#     --format FORMAT       Output format: parquet, json, csv (default: parquet)
#     --seed N              Random seed (default: 42)
#     --quick               Quick demo mode with smaller volumes
#     --all                 Generate all data types
#     --slots               Generate slot machine data
#     --tables              Generate table game data
#     --players             Generate player profiles
#     --financial           Generate financial transactions
#     --security            Generate security events
#     --compliance          Generate compliance filings
#     --include-pii         Include unhashed PII (testing only)
#     --help                Show this help message
#
# EXAMPLES:
#     ./generate-data.sh --quick
#     ./generate-data.sh --all --days 30
#     ./generate-data.sh --slots --slot-count 100000 --players --player-count 5000
#
# =============================================================================

set -e

# =============================================================================
# Configuration
# =============================================================================
DAYS=30
SLOT_COUNT=500000
TABLE_COUNT=100000
PLAYER_COUNT=10000
FINANCIAL_COUNT=50000
SECURITY_COUNT=25000
COMPLIANCE_COUNT=10000
OUTPUT_DIR="./data/generated"
FORMAT="parquet"
SEED=42
QUICK=false
INCLUDE_PII=false

# Data type flags
GEN_ALL=false
GEN_SLOTS=false
GEN_TABLES=false
GEN_PLAYERS=false
GEN_FINANCIAL=false
GEN_SECURITY=false
GEN_COMPLIANCE=false

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_GEN_PATH="$PROJECT_ROOT/data_generation"

# =============================================================================
# Color Output
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m'

write_header() {
    echo ""
    echo -e "${CYAN}======================================================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    echo ""
}

write_step() {
    echo -e "${YELLOW}[*] $1${NC}"
}

write_success() {
    echo -e "${GREEN}[+] $1${NC}"
}

write_failure() {
    echo -e "${RED}[-] $1${NC}"
}

write_info() {
    echo -e "${GRAY}    $1${NC}"
}

format_number() {
    printf "%'d" "$1" 2>/dev/null || echo "$1"
}

format_size() {
    local size=$1
    if [ $size -gt 1073741824 ]; then
        echo "$(awk "BEGIN {printf \"%.2f GB\", $size/1073741824}")"
    elif [ $size -gt 1048576 ]; then
        echo "$(awk "BEGIN {printf \"%.2f MB\", $size/1048576}")"
    elif [ $size -gt 1024 ]; then
        echo "$(awk "BEGIN {printf \"%.2f KB\", $size/1024}")"
    else
        echo "$size bytes"
    fi
}

# =============================================================================
# Parse Arguments
# =============================================================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --days)
            DAYS="$2"
            shift 2
            ;;
        --slot-count)
            SLOT_COUNT="$2"
            shift 2
            ;;
        --table-count)
            TABLE_COUNT="$2"
            shift 2
            ;;
        --player-count)
            PLAYER_COUNT="$2"
            shift 2
            ;;
        --financial-count)
            FINANCIAL_COUNT="$2"
            shift 2
            ;;
        --security-count)
            SECURITY_COUNT="$2"
            shift 2
            ;;
        --compliance-count)
            COMPLIANCE_COUNT="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --format)
            FORMAT="$2"
            shift 2
            ;;
        --seed)
            SEED="$2"
            shift 2
            ;;
        --quick)
            QUICK=true
            shift
            ;;
        --all)
            GEN_ALL=true
            shift
            ;;
        --slots)
            GEN_SLOTS=true
            shift
            ;;
        --tables)
            GEN_TABLES=true
            shift
            ;;
        --players)
            GEN_PLAYERS=true
            shift
            ;;
        --financial)
            GEN_FINANCIAL=true
            shift
            ;;
        --security)
            GEN_SECURITY=true
            shift
            ;;
        --compliance)
            GEN_COMPLIANCE=true
            shift
            ;;
        --include-pii)
            INCLUDE_PII=true
            shift
            ;;
        --help|-h)
            head -60 "$0" | grep -E '^#' | sed 's/^# //' | sed 's/^#//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# =============================================================================
# Helper Functions
# =============================================================================
find_python() {
    # Check for venv first
    local venv_paths=(
        "$PROJECT_ROOT/.venv/bin/python"
        "$PROJECT_ROOT/venv/bin/python"
    )

    for path in "${venv_paths[@]}"; do
        if [ -x "$path" ]; then
            echo "$path"
            return 0
        fi
    done

    # Fall back to system Python
    if command -v python3 &>/dev/null; then
        echo "python3"
        return 0
    fi
    if command -v python &>/dev/null; then
        echo "python"
        return 0
    fi

    return 1
}

# =============================================================================
# Main Script
# =============================================================================

write_header "Microsoft Fabric Casino/Gaming POC - Data Generation"

# Quick mode adjustments
if [ "$QUICK" = true ]; then
    write_info "Quick demo mode enabled - using smaller data volumes"
    DAYS=7
    SLOT_COUNT=10000
    TABLE_COUNT=5000
    PLAYER_COUNT=1000
    FINANCIAL_COUNT=2000
    SECURITY_COUNT=500
    COMPLIANCE_COUNT=200
    GEN_ALL=true
fi

# Default to All if no specific type selected
if [ "$GEN_ALL" = false ] && [ "$GEN_SLOTS" = false ] && [ "$GEN_TABLES" = false ] && \
   [ "$GEN_PLAYERS" = false ] && [ "$GEN_FINANCIAL" = false ] && \
   [ "$GEN_SECURITY" = false ] && [ "$GEN_COMPLIANCE" = false ]; then
    write_info "No data type specified, defaulting to --all"
    GEN_ALL=true
fi

# Display configuration
write_step "Configuration:"
write_info "Days:        $DAYS"
write_info "Output:      $OUTPUT_DIR"
write_info "Format:      $FORMAT"
write_info "Seed:        $SEED"
if [ "$QUICK" = true ]; then
    write_info "Mode:        Quick Demo"
fi
echo ""

# Find Python
PYTHON_CMD=$(find_python)
if [ -z "$PYTHON_CMD" ]; then
    write_failure "Python not found. Run setup.sh first."
    exit 1
fi
write_info "Using Python: $PYTHON_CMD"

# Verify data_generation module
if [ ! -f "$DATA_GEN_PATH/generate.py" ]; then
    write_failure "data_generation/generate.py not found"
    exit 1
fi

# Build command arguments
ARGS=(
    "$DATA_GEN_PATH/generate.py"
    "--output" "$OUTPUT_DIR"
    "--format" "$FORMAT"
    "--days" "$DAYS"
    "--seed" "$SEED"
)

if [ "$GEN_ALL" = true ]; then
    ARGS+=("--all")
else
    if [ "$GEN_SLOTS" = true ]; then ARGS+=("--slots" "$SLOT_COUNT"); fi
    if [ "$GEN_TABLES" = true ]; then ARGS+=("--tables" "$TABLE_COUNT"); fi
    if [ "$GEN_PLAYERS" = true ]; then ARGS+=("--players" "$PLAYER_COUNT"); fi
    if [ "$GEN_FINANCIAL" = true ]; then ARGS+=("--financial" "$FINANCIAL_COUNT"); fi
    if [ "$GEN_SECURITY" = true ]; then ARGS+=("--security" "$SECURITY_COUNT"); fi
    if [ "$GEN_COMPLIANCE" = true ]; then ARGS+=("--compliance" "$COMPLIANCE_COUNT"); fi
fi

if [ "$INCLUDE_PII" = true ]; then
    ARGS+=("--include-pii")
    write_info "Warning: Including unhashed PII (for testing only)"
fi

# Show what will be generated
write_header "Data Generation Plan"
if [ "$GEN_ALL" = true ] || [ "$GEN_SLOTS" = true ]; then
    write_info "Slot Machine Events: $(format_number $SLOT_COUNT)"
fi
if [ "$GEN_ALL" = true ] || [ "$GEN_TABLES" = true ]; then
    write_info "Table Game Events:   $(format_number $TABLE_COUNT)"
fi
if [ "$GEN_ALL" = true ] || [ "$GEN_PLAYERS" = true ]; then
    write_info "Player Profiles:     $(format_number $PLAYER_COUNT)"
fi
if [ "$GEN_ALL" = true ] || [ "$GEN_FINANCIAL" = true ]; then
    write_info "Financial Txns:      $(format_number $FINANCIAL_COUNT)"
fi
if [ "$GEN_ALL" = true ] || [ "$GEN_SECURITY" = true ]; then
    write_info "Security Events:     $(format_number $SECURITY_COUNT)"
fi
if [ "$GEN_ALL" = true ] || [ "$GEN_COMPLIANCE" = true ]; then
    write_info "Compliance Filings:  $(format_number $COMPLIANCE_COUNT)"
fi

# Create output directory
if [ ! -d "$OUTPUT_DIR" ]; then
    write_step "Creating output directory: $OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
fi

# Run generation
write_header "Generating Data"

START_TIME=$(date +%s)

cd "$PROJECT_ROOT"

write_step "Starting data generation..."
echo ""

# Run the Python generator
if ! $PYTHON_CMD "${ARGS[@]}"; then
    write_failure "Data generation failed"
    exit 1
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# =============================================================================
# Summary
# =============================================================================
write_header "Generation Complete!"

# List generated files
write_step "Generated Files:"
TOTAL_SIZE=0

if [ -d "$OUTPUT_DIR" ]; then
    for file in "$OUTPUT_DIR"/*; do
        if [ -f "$file" ]; then
            size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
            TOTAL_SIZE=$((TOTAL_SIZE + size))
            filename=$(basename "$file")
            printf "    %-35s %s\n" "$filename" "$(format_size $size)"
        fi
    done
fi

echo ""
write_info "Total Size: $(format_size $TOTAL_SIZE)"
write_info "Duration:   $(printf '%02d:%02d' $((DURATION/60)) $((DURATION%60)))"
write_info "Location:   $(cd "$OUTPUT_DIR" && pwd)"

echo ""
write_success "Data generation completed successfully!"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Review generated data in $OUTPUT_DIR"
echo -e "  2. Upload to Azure Storage: ${CYAN}az storage blob upload-batch ...${NC}"
echo "  3. Or use in Microsoft Fabric notebooks"
echo ""
