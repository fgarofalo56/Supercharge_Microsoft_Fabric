#!/bin/bash
# ==============================================================================
# Post-Create Script for Microsoft Fabric Casino/Gaming POC Dev Container
# ==============================================================================
# This script runs after the container is created to finalize the environment.
# ==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print banner
echo -e "${CYAN}"
echo "=============================================================="
echo "    Microsoft Fabric Casino/Gaming POC - Dev Container Setup  "
echo "=============================================================="
echo -e "${NC}"

# Function to print status messages
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ==============================================================================
# 1. Verify Python Environment
# ==============================================================================
print_status "Verifying Python environment..."

PYTHON_VERSION=$(python --version 2>&1)
print_success "Python version: $PYTHON_VERSION"

# Upgrade pip
pip install --upgrade pip --quiet
print_success "pip upgraded to latest version"

# ==============================================================================
# 2. Install Python Dependencies
# ==============================================================================
print_status "Installing Python dependencies..."

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    print_success "Core dependencies installed"
else
    print_warning "requirements.txt not found"
fi

if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt --quiet
    print_success "Development dependencies installed"
else
    print_warning "requirements-dev.txt not found"
fi

# ==============================================================================
# 3. Set Up Pre-commit Hooks (if pre-commit is installed)
# ==============================================================================
print_status "Setting up pre-commit hooks..."

if command -v pre-commit &> /dev/null; then
    if [ -f ".pre-commit-config.yaml" ]; then
        pre-commit install --install-hooks
        print_success "Pre-commit hooks installed"
    else
        print_warning ".pre-commit-config.yaml not found, skipping pre-commit setup"
    fi
else
    print_warning "pre-commit not installed, skipping hook setup"
fi

# ==============================================================================
# 4. Configure Git
# ==============================================================================
print_status "Configuring Git..."

# Set up git config (these can be overridden by user's global config)
git config --local core.autocrlf input
git config --local core.eol lf
git config --local pull.rebase false

# Configure nbstripout for Jupyter notebooks (removes outputs before commit)
if command -v nbstripout &> /dev/null; then
    nbstripout --install --attributes .gitattributes 2>/dev/null || true
    print_success "nbstripout configured for notebook cleaning"
else
    print_warning "nbstripout not available"
fi

print_success "Git configured"

# ==============================================================================
# 5. Verify Azure CLI
# ==============================================================================
print_status "Verifying Azure CLI installation..."

if command -v az &> /dev/null; then
    AZ_VERSION=$(az version --query '"azure-cli"' -o tsv 2>/dev/null || echo "unknown")
    print_success "Azure CLI version: $AZ_VERSION"

    # Check Bicep
    if az bicep version &> /dev/null; then
        BICEP_VERSION=$(az bicep version 2>&1 | grep -oP 'v\d+\.\d+\.\d+' | head -1 || echo "installed")
        print_success "Bicep version: $BICEP_VERSION"
    else
        print_status "Installing Bicep..."
        az bicep install
        print_success "Bicep installed"
    fi
else
    print_warning "Azure CLI not found (will be installed via features)"
fi

# ==============================================================================
# 6. Create Project Directories
# ==============================================================================
print_status "Creating project directories..."

mkdir -p temp
mkdir -p .data/raw
mkdir -p .data/processed
mkdir -p .logs

print_success "Project directories created"

# ==============================================================================
# 7. Set Up Environment File
# ==============================================================================
print_status "Checking environment configuration..."

if [ ! -f ".env" ] && [ -f ".env.sample" ]; then
    print_status "Creating .env from .env.sample..."
    cp .env.sample .env
    print_success ".env file created from sample"
    print_warning "Please update .env with your actual configuration values"
elif [ -f ".env" ]; then
    print_success ".env file already exists"
else
    print_warning "No .env.sample found, skipping environment setup"
fi

# ==============================================================================
# 8. Verify Jupyter Setup
# ==============================================================================
print_status "Verifying Jupyter setup..."

if command -v jupyter &> /dev/null; then
    print_success "Jupyter is available"

    # Install IPython kernel
    python -m ipykernel install --user --name fabric-casino-poc --display-name "Fabric Casino POC (Python 3.11)" 2>/dev/null || true
    print_success "IPython kernel installed"
else
    print_warning "Jupyter not found"
fi

# ==============================================================================
# 9. Run Initial Validation
# ==============================================================================
print_status "Running quick validation..."

# Test Python imports
python -c "
import sys
try:
    import pandas
    import numpy
    import faker
    import azure.identity
    import pydantic
    print('Core packages imported successfully')
except ImportError as e:
    print(f'Import error: {e}')
    sys.exit(1)
"
print_success "Core Python packages validated"

# ==============================================================================
# 10. Display Welcome Message
# ==============================================================================
echo ""
echo -e "${GREEN}=============================================================="
echo "         Dev Container Setup Complete!"
echo "==============================================================${NC}"
echo ""
echo -e "${CYAN}Quick Start Commands:${NC}"
echo ""
echo "  Data Generation:"
echo "    python data_generation/generate.py --help"
echo "    python data_generation/generate.py --type slot_events --records 1000"
echo ""
echo "  Testing:"
echo "    pytest validation/ -v                    # Run all tests"
echo "    pytest validation/unit_tests/ -v         # Run unit tests"
echo "    pytest validation/deployment_tests/ -v   # Run deployment tests"
echo ""
echo "  Azure & Infrastructure:"
echo "    az login --use-device-code              # Login to Azure"
echo "    az bicep build --file infra/main.bicep  # Validate Bicep"
echo ""
echo "  Jupyter Notebooks:"
echo "    jupyter lab --no-browser --port 8888    # Start Jupyter Lab"
echo ""
echo -e "${CYAN}Useful Aliases:${NC}"
echo "    generate     - Run data generator"
echo "    validate     - Run pytest validation"
echo "    bicep-lint   - Validate Bicep templates"
echo "    cddata       - Navigate to data_generation/"
echo "    cdinfra      - Navigate to infra/"
echo "    cdnotebooks  - Navigate to notebooks/"
echo ""
echo -e "${YELLOW}Notes:${NC}"
echo "  - Update .env with your Azure configuration before deployment"
echo "  - Run 'az login' to authenticate with Azure"
echo "  - Check README.md for detailed documentation"
echo ""
echo -e "${GREEN}Happy coding!${NC}"
echo ""

# ==============================================================================
# 11. Install pre-commit hooks (idempotent; errors are non-fatal)
# ==============================================================================
git config --local core.hooksPath .githooks 2>/dev/null || true
pre-commit install --install-hooks 2>/dev/null || true
