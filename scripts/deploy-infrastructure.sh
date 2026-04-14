#!/usr/bin/env bash
# =============================================================================
# Microsoft Fabric POC - Infrastructure Deployment (Unix/Mac)
# =============================================================================
#
# SYNOPSIS:
#     Deploy Microsoft Fabric POC infrastructure to Azure.
#
# USAGE:
#     ./deploy-infrastructure.sh [OPTIONS]
#
# OPTIONS:
#     --environment ENV     Target environment: dev, staging, prod (default: dev)
#     --location REGION     Azure region (default: from .env or eastus2)
#     --what-if             Preview deployment without making changes
#     --no-prompt           Skip confirmation prompts
#     --parameter-file FILE Path to Bicep parameter file
#     --help                Show this help message
#
# EXAMPLES:
#     ./deploy-infrastructure.sh
#     ./deploy-infrastructure.sh --environment staging
#     ./deploy-infrastructure.sh --what-if
#     ./deploy-infrastructure.sh --no-prompt
#
# =============================================================================

set -e

# =============================================================================
# Configuration
# =============================================================================
ENVIRONMENT="dev"
LOCATION=""
WHAT_IF=false
NO_PROMPT=false
PARAMETER_FILE=""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INFRA_PATH="$PROJECT_ROOT/infra"
ENV_FILE="$PROJECT_ROOT/.env"
OUTPUT_FILE="$PROJECT_ROOT/deployment-outputs.json"

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

# =============================================================================
# Parse Arguments
# =============================================================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --environment)
            ENVIRONMENT="$2"
            if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
                echo "Invalid environment: $ENVIRONMENT"
                echo "Valid options: dev, staging, prod"
                exit 1
            fi
            shift 2
            ;;
        --location)
            LOCATION="$2"
            shift 2
            ;;
        --what-if)
            WHAT_IF=true
            shift
            ;;
        --no-prompt)
            NO_PROMPT=true
            shift
            ;;
        --parameter-file)
            PARAMETER_FILE="$2"
            shift 2
            ;;
        --help|-h)
            head -40 "$0" | grep -E '^#' | sed 's/^# //' | sed 's/^#//'
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
load_env_file() {
    local file="$1"
    if [ -f "$file" ]; then
        while IFS= read -r line || [[ -n "$line" ]]; do
            # Skip comments and empty lines
            [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
            # Export the variable
            if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]]; then
                # Remove quotes from value
                local key="${line%%=*}"
                local value="${line#*=}"
                value="${value%\"}"
                value="${value#\"}"
                value="${value%\'}"
                value="${value#\'}"
                export "$key=$value"
            fi
        done < "$file"
    fi
}

get_env_var() {
    local var_name="$1"
    local default="$2"
    local value="${!var_name}"
    if [ -z "$value" ] || [[ "$value" =~ ^\<.*\>$ ]]; then
        echo "$default"
    else
        echo "$value"
    fi
}

is_var_set() {
    local var_name="$1"
    local value="${!var_name}"
    if [ -z "$value" ] || [[ "$value" =~ ^\<.*\>$ ]]; then
        return 1
    fi
    return 0
}

# =============================================================================
# Main Script
# =============================================================================

write_header "Microsoft Fabric POC - Infrastructure Deployment"

write_info "Project Root: $PROJECT_ROOT"
write_info "Environment:  $ENVIRONMENT"
echo ""

# =============================================================================
# Step 1: Load Environment Configuration
# =============================================================================
write_header "Step 1: Loading Configuration"

if [ ! -f "$ENV_FILE" ]; then
    write_failure ".env file not found at $ENV_FILE"
    write_info "Copy .env.sample to .env and configure your values"
    write_info "Run: cp .env.sample .env"
    exit 1
fi

write_step "Loading .env file..."
load_env_file "$ENV_FILE"
write_success "Environment variables loaded"

# =============================================================================
# Step 2: Validate Required Variables
# =============================================================================
write_header "Step 2: Validating Configuration"

MISSING_VARS=()
REQUIRED_VARS=("AZURE_SUBSCRIPTION_ID" "PROJECT_PREFIX" "FABRIC_ADMIN_EMAIL")

for var in "${REQUIRED_VARS[@]}"; do
    if ! is_var_set "$var"; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    write_failure "Missing or invalid required variables:"
    for var in "${MISSING_VARS[@]}"; do
        write_info "  - $var"
    done
    echo ""
    write_info "Please configure these in your .env file"
    exit 1
fi

write_success "All required variables configured"

# Display configuration
FABRIC_SKU=$(get_env_var "FABRIC_CAPACITY_SKU" "F64")
if [ -z "$LOCATION" ]; then
    LOCATION=$(get_env_var "AZURE_LOCATION" "eastus2")
fi

write_step "Deployment Configuration:"
write_info "Subscription:    $AZURE_SUBSCRIPTION_ID"
write_info "Project Prefix:  $PROJECT_PREFIX"
write_info "Admin Email:     $FABRIC_ADMIN_EMAIL"
write_info "Fabric SKU:      $FABRIC_SKU"
write_info "Location:        $LOCATION"

# =============================================================================
# Step 3: Validate Azure CLI Login
# =============================================================================
write_header "Step 3: Validating Azure Connection"

write_step "Checking Azure CLI login..."

if ! az account show &>/dev/null; then
    write_failure "Not logged in to Azure CLI"
    write_info "Run 'az login' to authenticate"
    exit 1
fi

CURRENT_USER=$(az account show --query 'user.name' -o tsv)
CURRENT_SUB=$(az account show --query 'name' -o tsv)
CURRENT_SUB_ID=$(az account show --query 'id' -o tsv)

write_success "Logged in as: $CURRENT_USER"
write_info "Current subscription: $CURRENT_SUB"

# Check if correct subscription
if [ "$CURRENT_SUB_ID" != "$AZURE_SUBSCRIPTION_ID" ]; then
    write_step "Switching to configured subscription..."
    if ! az account set --subscription "$AZURE_SUBSCRIPTION_ID"; then
        write_failure "Failed to set subscription"
        exit 1
    fi
    write_success "Subscription set to: $AZURE_SUBSCRIPTION_ID"
fi

# =============================================================================
# Step 4: Prepare Deployment
# =============================================================================
write_header "Step 4: Preparing Deployment"

# Determine parameter file
if [ -n "$PARAMETER_FILE" ] && [ -f "$PARAMETER_FILE" ]; then
    BICEP_PARAMS="$PARAMETER_FILE"
    write_info "Using parameter file: $PARAMETER_FILE"
else
    # Check for environment-specific parameter file
    ENV_PARAM_FILE="$INFRA_PATH/environments/$ENVIRONMENT/$ENVIRONMENT.bicepparam"
    if [ -f "$ENV_PARAM_FILE" ]; then
        BICEP_PARAMS="$ENV_PARAM_FILE"
        write_info "Using environment params: $ENV_PARAM_FILE"
    else
        # Use default parameter file
        BICEP_PARAMS="$INFRA_PATH/main.bicepparam"
        write_info "Using default params: $BICEP_PARAMS"
    fi
fi

# Check Bicep files exist
MAIN_BICEP="$INFRA_PATH/main.bicep"
if [ ! -f "$MAIN_BICEP" ]; then
    write_failure "main.bicep not found at $MAIN_BICEP"
    exit 1
fi

# Resource group name
RESOURCE_GROUP="${PROJECT_PREFIX}-${ENVIRONMENT}-rg"
write_info "Resource Group: $RESOURCE_GROUP"

# =============================================================================
# Step 5: Confirm Deployment
# =============================================================================
if [ "$NO_PROMPT" = false ] && [ "$WHAT_IF" = false ]; then
    write_header "Deployment Summary"
    echo -e "${YELLOW}The following resources will be deployed:${NC}"
    echo ""
    write_info "Resource Group:     $RESOURCE_GROUP"
    write_info "Location:           $LOCATION"
    write_info "Environment:        $ENVIRONMENT"
    write_info "Fabric Capacity:    $FABRIC_SKU"
    write_info "Private Endpoints:  $(get_env_var 'ENABLE_PRIVATE_ENDPOINTS' 'false')"
    echo ""

    read -p "Do you want to proceed with deployment? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        write_info "Deployment cancelled"
        exit 0
    fi
fi

# =============================================================================
# Step 6: Create Resource Group
# =============================================================================
write_header "Step 6: Creating Resource Group"

write_step "Creating resource group: $RESOURCE_GROUP"

RG_EXISTS=$(az group exists --name "$RESOURCE_GROUP")
if [ "$RG_EXISTS" = "true" ]; then
    write_info "Resource group already exists"
else
    az group create \
        --name "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --tags Environment="$ENVIRONMENT" Project="$PROJECT_PREFIX" \
        --output none

    write_success "Resource group created"
fi

# =============================================================================
# Step 7: Deploy Bicep Template
# =============================================================================
write_header "Step 7: Deploying Infrastructure"

DEPLOYMENT_NAME="fabric-poc-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"

write_step "Starting deployment: $DEPLOYMENT_NAME"
write_info "This may take 10-20 minutes..."
echo ""

# Build deployment command
DEPLOY_CMD=(
    az deployment sub create
    --resource-group "$RESOURCE_GROUP"
    --template-file "$MAIN_BICEP"
    --parameters "$BICEP_PARAMS"
    --parameters "environment=$ENVIRONMENT"
    --parameters "location=$LOCATION"
    --parameters "projectPrefix=$PROJECT_PREFIX"
    --parameters "fabricAdminEmail=$FABRIC_ADMIN_EMAIL"
    --name "$DEPLOYMENT_NAME"
    --output json
)

# Add optional parameters
if is_var_set "FABRIC_CAPACITY_SKU"; then
    DEPLOY_CMD+=(--parameters "fabricCapacitySku=$FABRIC_CAPACITY_SKU")
fi
if is_var_set "ENABLE_PRIVATE_ENDPOINTS"; then
    DEPLOY_CMD+=(--parameters "enablePrivateEndpoints=$ENABLE_PRIVATE_ENDPOINTS")
fi
if is_var_set "LOG_RETENTION_DAYS"; then
    DEPLOY_CMD+=(--parameters "logRetentionDays=$LOG_RETENTION_DAYS")
fi

# What-If mode
if [ "$WHAT_IF" = true ]; then
    write_info "Running in What-If mode..."
    DEPLOY_CMD+=(--what-if)
fi

# Run deployment
START_TIME=$(date +%s)

if ! "${DEPLOY_CMD[@]}"; then
    write_failure "Deployment failed"
    exit 1
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

if [ "$WHAT_IF" = false ]; then
    write_success "Deployment completed in $(printf '%02d:%02d' $((DURATION/60)) $((DURATION%60)))"
fi

# =============================================================================
# Step 8: Retrieve and Save Outputs
# =============================================================================
if [ "$WHAT_IF" = false ]; then
    write_header "Step 8: Retrieving Deployment Outputs"

    write_step "Fetching deployment outputs..."

    OUTPUTS=$(az deployment sub show \
        --name "$DEPLOYMENT_NAME" \
        --query "properties.outputs" \
        --output json 2>/dev/null)

    if [ -n "$OUTPUTS" ] && [ "$OUTPUTS" != "null" ]; then
        # Create output JSON
        cat > "$OUTPUT_FILE" << EOF
{
    "deploymentName": "$DEPLOYMENT_NAME",
    "resourceGroup": "$RESOURCE_GROUP",
    "environment": "$ENVIRONMENT",
    "location": "$LOCATION",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "outputs": $OUTPUTS
}
EOF
        write_success "Outputs saved to: $OUTPUT_FILE"

        # Display key outputs
        write_header "Deployment Outputs"
        echo "$OUTPUTS" | jq -r 'to_entries[] | "    \(.key): \(.value.value)"' 2>/dev/null || \
            write_info "Install jq to view formatted outputs"

    else
        write_info "No outputs to retrieve"
    fi

    # =============================================================================
    # Summary
    # =============================================================================
    write_header "Deployment Complete!"

    write_success "Infrastructure deployed successfully"
    echo ""
    echo -e "${YELLOW}Key Information:${NC}"
    write_info "Resource Group:   $RESOURCE_GROUP"
    write_info "Deployment Name:  $DEPLOYMENT_NAME"
    write_info "Outputs File:     $OUTPUT_FILE"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  1. Review deployment outputs in $OUTPUT_FILE"
    echo "  2. Configure Microsoft Fabric workspace"
    echo "  3. Upload generated data to storage"
    echo "  4. Run notebooks in Microsoft Fabric"
    echo ""

else
    write_header "What-If Complete"
    write_info "Review the changes above"
    write_info "Remove --what-if to perform actual deployment"
fi
