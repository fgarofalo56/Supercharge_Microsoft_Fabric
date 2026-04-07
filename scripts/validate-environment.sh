#!/usr/bin/env bash
# =============================================================================
# Microsoft Fabric POC - Environment Validation (Unix/Mac)
# =============================================================================
#
# SYNOPSIS:
#     Validate the Microsoft Fabric POC environment setup.
#
# USAGE:
#     ./validate-environment.sh [OPTIONS]
#
# OPTIONS:
#     --quick      Skip smoke tests, only check prerequisites
#     --verbose    Show detailed output for all checks
#     --help       Show this help message
#
# EXAMPLES:
#     ./validate-environment.sh
#     ./validate-environment.sh --quick
#
# =============================================================================

set -e

# =============================================================================
# Configuration
# =============================================================================
QUICK=false
VERBOSE=false

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_GEN_PATH="$PROJECT_ROOT/data_generation"
ENV_FILE="$PROJECT_ROOT/.env"

MIN_PYTHON_VERSION="3.10"

# Track results
PASSED=0
FAILED=0
WARNINGS=0

# =============================================================================
# Color Output
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m'

# =============================================================================
# Parse Arguments
# =============================================================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            head -30 "$0" | grep -E '^#' | sed 's/^# //' | sed 's/^#//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# =============================================================================
# Helper Functions
# =============================================================================
write_header() {
    echo ""
    echo -e "${CYAN}======================================================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    echo ""
}

write_check() {
    local name="$1"
    local status="$2"
    local message="$3"

    local icon color
    case "$status" in
        PASS) icon="[OK]"; color="${GREEN}" ;;
        FAIL) icon="[X] "; color="${RED}" ;;
        WARN) icon="[!] "; color="${YELLOW}" ;;
        SKIP) icon="[-] "; color="${GRAY}" ;;
        *) icon="[?] "; color="${GRAY}" ;;
    esac

    local line="$icon $name"
    if [ -n "$message" ]; then
        line="$line - $message"
    fi

    echo -e "${color}${line}${NC}"

    case "$status" in
        PASS) ((PASSED++)) ;;
        FAIL) ((FAILED++)) ;;
        WARN) ((WARNINGS++)) ;;
    esac
}

write_subcheck() {
    echo -e "      ${GRAY}$1${NC}"
}

command_exists() {
    command -v "$1" &>/dev/null
}

version_gte() {
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

get_python_version() {
    local cmd=$1
    if command_exists "$cmd"; then
        "$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1
    fi
}

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
    local python_cmds=("python3" "python" "python3.12" "python3.11" "python3.10")
    for cmd in "${python_cmds[@]}"; do
        if command_exists "$cmd"; then
            local version=$(get_python_version "$cmd")
            if [ -n "$version" ] && version_gte "$version" "$MIN_PYTHON_VERSION"; then
                echo "$cmd"
                return 0
            fi
        fi
    done

    return 1
}

# =============================================================================
# Main Script
# =============================================================================

write_header "Microsoft Fabric POC - Environment Validation"

echo -e "${GRAY}Project Root: $PROJECT_ROOT${NC}"
echo -e "${GRAY}Timestamp:    $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""

# =============================================================================
# Section 1: Prerequisites
# =============================================================================
write_header "Prerequisites Check"

# Python
PYTHON_CMD=$(find_python 2>/dev/null || echo "")
if [ -n "$PYTHON_CMD" ]; then
    PYTHON_VERSION=$(get_python_version "$PYTHON_CMD")
    if [ -n "$PYTHON_VERSION" ] && version_gte "$PYTHON_VERSION" "$MIN_PYTHON_VERSION"; then
        write_check "Python" "PASS" "Version $PYTHON_VERSION ($PYTHON_CMD)"
    else
        write_check "Python" "FAIL" "Version $PYTHON_VERSION < $MIN_PYTHON_VERSION required"
    fi
else
    write_check "Python" "FAIL" "Not found"
fi

# Virtual Environment
if [ -d "$PROJECT_ROOT/.venv" ]; then
    write_check "Virtual Environment" "PASS" ".venv exists"
elif [ -d "$PROJECT_ROOT/venv" ]; then
    write_check "Virtual Environment" "PASS" "venv exists"
else
    write_check "Virtual Environment" "WARN" "Not found - run setup.sh"
fi

# Git
if command_exists git; then
    GIT_VERSION=$(git --version | sed 's/git version //')
    write_check "Git" "PASS" "Version $GIT_VERSION"
else
    write_check "Git" "FAIL" "Not found"
fi

# Azure CLI
if command_exists az; then
    AZ_VERSION=$(az version --query '"azure-cli"' -o tsv 2>/dev/null)
    write_check "Azure CLI" "PASS" "Version $AZ_VERSION"
else
    write_check "Azure CLI" "FAIL" "Not found"
fi

# Bicep
if command_exists az; then
    BICEP_VERSION=$(az bicep version 2>/dev/null)
    if [ -n "$BICEP_VERSION" ]; then
        BICEP_VER=$(echo "$BICEP_VERSION" | sed 's/Bicep CLI version //')
        write_check "Bicep" "PASS" "Version $BICEP_VER"
    else
        write_check "Bicep" "WARN" "Not installed - run 'az bicep install'"
    fi
else
    write_check "Bicep" "SKIP" "Azure CLI required"
fi

# =============================================================================
# Section 2: Configuration Files
# =============================================================================
write_header "Configuration Files"

# .env file
if [ -f "$ENV_FILE" ]; then
    PLACEHOLDERS=$(grep -c '<.*>' "$ENV_FILE" 2>/dev/null || echo 0)
    if [ "$PLACEHOLDERS" -gt 0 ]; then
        write_check ".env file" "WARN" "Found $PLACEHOLDERS unconfigured placeholders"
    else
        write_check ".env file" "PASS" "Exists and configured"
    fi
else
    write_check ".env file" "WARN" "Not found - copy from .env.sample"
fi

# requirements.txt
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    write_check "requirements.txt" "PASS" "Exists"
else
    write_check "requirements.txt" "FAIL" "Not found"
fi

# Infrastructure files
if [ -f "$PROJECT_ROOT/infra/main.bicep" ]; then
    write_check "Bicep templates" "PASS" "infra/main.bicep exists"
else
    write_check "Bicep templates" "WARN" "infra/main.bicep not found"
fi

# Data generation
if [ -f "$DATA_GEN_PATH/generate.py" ]; then
    write_check "Data generator" "PASS" "generate.py exists"
else
    write_check "Data generator" "FAIL" "generate.py not found"
fi

# =============================================================================
# Section 3: Azure Connectivity
# =============================================================================
write_header "Azure Connectivity"

if command_exists az; then
    if az account show &>/dev/null; then
        USER_NAME=$(az account show --query 'user.name' -o tsv)
        SUB_NAME=$(az account show --query 'name' -o tsv)
        TENANT_ID=$(az account show --query 'tenantId' -o tsv)

        write_check "Azure Login" "PASS" "Logged in as $USER_NAME"
        write_subcheck "Subscription: $SUB_NAME"
        write_subcheck "Tenant: ${TENANT_ID:0:8}..."

        # Check subscription access
        SUB_COUNT=$(az account list --query "length(@)" -o tsv 2>/dev/null)
        write_check "Subscriptions" "PASS" "$SUB_COUNT accessible"
    else
        write_check "Azure Login" "WARN" "Not logged in - run 'az login'"
    fi
else
    write_check "Azure Login" "SKIP" "Azure CLI not installed"
fi

# =============================================================================
# Section 4: Python Dependencies
# =============================================================================
if [ "$QUICK" = false ] && [ -n "$PYTHON_CMD" ]; then
    write_header "Python Dependencies"

    REQUIRED_PACKAGES=(
        "pandas"
        "numpy"
        "pyarrow"
        "faker"
        "tqdm"
        "pydantic"
        "azure-identity:azure.identity"
        "azure-storage-blob:azure.storage.blob"
    )

    for pkg in "${REQUIRED_PACKAGES[@]}"; do
        # Handle package:module format
        if [[ "$pkg" == *":"* ]]; then
            PKG_NAME="${pkg%%:*}"
            MODULE_NAME="${pkg##*:}"
        else
            PKG_NAME="$pkg"
            MODULE_NAME="${pkg//-/_}"
        fi

        if $PYTHON_CMD -c "import $MODULE_NAME" &>/dev/null; then
            write_check "$PKG_NAME" "PASS" "Importable"
        else
            write_check "$PKG_NAME" "FAIL" "Not installed"
        fi
    done
fi

# =============================================================================
# Section 5: Generator Import Test
# =============================================================================
if [ "$QUICK" = false ] && [ -n "$PYTHON_CMD" ]; then
    write_header "Generator Import Test"

    GENERATORS=(
        "SlotMachineGenerator"
        "TableGameGenerator"
        "PlayerGenerator"
        "FinancialGenerator"
        "SecurityGenerator"
        "ComplianceGenerator"
    )

    cd "$PROJECT_ROOT"

    for gen in "${GENERATORS[@]}"; do
        if $PYTHON_CMD -c "
import sys
sys.path.insert(0, 'data_generation')
from generators import $gen
print('OK')
" 2>/dev/null | grep -q "OK"; then
            write_check "$gen" "PASS" "Import successful"
        else
            write_check "$gen" "FAIL" "Import failed"
        fi
    done
fi

# =============================================================================
# Section 6: Smoke Test
# =============================================================================
if [ "$QUICK" = false ] && [ -n "$PYTHON_CMD" ]; then
    write_header "Smoke Test"

    echo -e "${GRAY}Running quick data generation test...${NC}"

    cd "$PROJECT_ROOT"

    SMOKE_RESULT=$($PYTHON_CMD << 'EOF' 2>&1
import sys
sys.path.insert(0, 'data_generation')
from generators import SlotMachineGenerator

try:
    gen = SlotMachineGenerator(seed=42, num_machines=10)
    df = gen.generate(100, show_progress=False)

    if len(df) == 100:
        print(f"SUCCESS: Generated {len(df)} records")
        print(f"Columns: {len(df.columns)}")
        print(f"Memory: {df.memory_usage(deep=True).sum() / 1024:.1f} KB")
    else:
        print(f"ERROR: Expected 100 records, got {len(df)}")
        sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
EOF
)

    if echo "$SMOKE_RESULT" | grep -q "SUCCESS"; then
        SUCCESS_LINE=$(echo "$SMOKE_RESULT" | grep "SUCCESS")
        COLS_LINE=$(echo "$SMOKE_RESULT" | grep "Columns")
        MEM_LINE=$(echo "$SMOKE_RESULT" | grep "Memory")

        write_check "Data Generation" "PASS" "$SUCCESS_LINE"
        write_subcheck "$COLS_LINE"
        write_subcheck "$MEM_LINE"
    else
        write_check "Data Generation" "FAIL" "$SMOKE_RESULT"
    fi
fi

# =============================================================================
# Summary
# =============================================================================
write_header "Validation Summary"

TOTAL=$((PASSED + FAILED + WARNINGS))

echo "Total Checks: $TOTAL"
echo ""

# Status bars
PASS_WIDTH=$((PASSED * 40 / TOTAL))
FAIL_WIDTH=$((FAILED * 40 / TOTAL))
WARN_WIDTH=$((WARNINGS * 40 / TOTAL))

[ $PASS_WIDTH -lt 1 ] && [ $PASSED -gt 0 ] && PASS_WIDTH=1
[ $FAIL_WIDTH -lt 0 ] && FAIL_WIDTH=0
[ $WARN_WIDTH -lt 0 ] && WARN_WIDTH=0

PASS_BAR=$(printf '=%.0s' $(seq 1 $PASS_WIDTH) 2>/dev/null || echo "=")
FAIL_BAR=$(printf '=%.0s' $(seq 1 $FAIL_WIDTH) 2>/dev/null || echo "")
WARN_BAR=$(printf '=%.0s' $(seq 1 $WARN_WIDTH) 2>/dev/null || echo "")

printf "  Passed:   %3d " "$PASSED"
echo -e "${GREEN}$PASS_BAR${NC}"

printf "  Failed:   %3d " "$FAILED"
echo -e "${RED}$FAIL_BAR${NC}"

printf "  Warnings: %3d " "$WARNINGS"
echo -e "${YELLOW}$WARN_BAR${NC}"

echo ""

# Overall status
if [ $FAILED -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -n "Status: "
        echo -e "${GREEN}ALL CHECKS PASSED${NC}"
        echo ""
        echo -e "${GREEN}Your environment is ready for the Microsoft Fabric POC!${NC}"
    else
        echo -n "Status: "
        echo -e "${YELLOW}PASSED WITH WARNINGS${NC}"
        echo ""
        echo -e "${YELLOW}Environment is functional but review warnings above.${NC}"
    fi
    exit 0
else
    echo -n "Status: "
    echo -e "${RED}VALIDATION FAILED${NC}"
    echo ""
    echo -e "${RED}Please fix the failed checks before proceeding.${NC}"
    echo -e "${YELLOW}Run ./scripts/setup.sh to set up the environment.${NC}"
    exit 1
fi
