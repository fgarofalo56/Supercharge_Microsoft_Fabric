# Scripts Documentation

Quick start scripts for the Microsoft Fabric Casino/Gaming POC. All scripts are provided in both PowerShell (Windows) and Bash (Linux/macOS) versions.

## Quick Start

```powershell
# Windows (PowerShell)
.\scripts\setup.ps1                    # Set up environment
.\scripts\generate-data.ps1 --quick    # Generate demo data
.\scripts\validate-environment.ps1     # Validate setup
```

```bash
# Linux/macOS (Bash)
./scripts/setup.sh                     # Set up environment
./scripts/generate-data.sh --quick     # Generate demo data
./scripts/validate-environment.sh      # Validate setup
```

---

## Scripts Overview

| Script | Purpose |
|--------|---------|
| `setup.ps1` / `setup.sh` | Complete environment setup |
| `generate-data.ps1` / `generate-data.sh` | Generate synthetic casino data |
| `deploy-infrastructure.ps1` / `deploy-infrastructure.sh` | Deploy Azure infrastructure |
| `validate-environment.ps1` / `validate-environment.sh` | Validate environment setup |
| `cleanup.ps1` / `cleanup.sh` | Cleanup resources and data |

---

## setup.ps1 / setup.sh

**Purpose:** Complete environment setup for the POC.

### What It Does

1. Checks prerequisites (Python 3.10+, Azure CLI, Bicep, Git)
2. Creates Python virtual environment (`.venv`)
3. Installs dependencies from `requirements.txt`
4. Validates Azure CLI login
5. Creates `.env` from `.env.sample` (if needed)
6. Displays next steps

### Usage

```powershell
# Windows
.\scripts\setup.ps1
.\scripts\setup.ps1 -SkipAzureLogin
.\scripts\setup.ps1 -VenvPath "C:\envs\fabric-poc"
```

```bash
# Linux/macOS
./scripts/setup.sh
./scripts/setup.sh --skip-azure-login
./scripts/setup.sh --venv-path /path/to/venv
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-SkipAzureLogin` / `--skip-azure-login` | Skip Azure CLI login validation | `false` |
| `-VenvPath` / `--venv-path` | Custom virtual environment path | `.venv` |

### Prerequisites

- Python 3.10 or later
- Git
- Azure CLI (for deployment)
- Bicep CLI (installed automatically via Azure CLI)

---

## generate-data.ps1 / generate-data.sh

**Purpose:** Generate synthetic casino/gaming data for the POC.

### What It Does

1. Generates data across all casino domains
2. Supports multiple output formats (Parquet, JSON, CSV)
3. Configurable data volumes
4. Provides progress and summary statistics

### Usage

```powershell
# Windows - Quick demo mode
.\scripts\generate-data.ps1 --quick

# Full generation
.\scripts\generate-data.ps1 --all --days 30

# Specific data types
.\scripts\generate-data.ps1 -Slots -SlotCount 100000 -Players -PlayerCount 5000

# Custom output
.\scripts\generate-data.ps1 --all -OutputDir "D:\data" -Format json
```

```bash
# Linux/macOS - Quick demo mode
./scripts/generate-data.sh --quick

# Full generation
./scripts/generate-data.sh --all --days 30

# Specific data types
./scripts/generate-data.sh --slots --slot-count 100000 --players --player-count 5000

# Custom output
./scripts/generate-data.sh --all --output-dir /data/output --format json
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--quick` | Quick demo mode (smaller volumes) | `false` |
| `--all` | Generate all data types | `false` |
| `--days` | Days of historical data | `30` |
| `--slot-count` | Slot machine events | `500,000` |
| `--table-count` | Table game events | `100,000` |
| `--player-count` | Player profiles | `10,000` |
| `--financial-count` | Financial transactions | `50,000` |
| `--security-count` | Security events | `25,000` |
| `--compliance-count` | Compliance filings | `10,000` |
| `--output-dir` | Output directory | `./data/generated` |
| `--format` | Output format: parquet, json, csv | `parquet` |
| `--seed` | Random seed for reproducibility | `42` |
| `--include-pii` | Include unhashed PII (testing only) | `false` |

### Data Type Flags

| Flag | Data Type |
|------|-----------|
| `--slots` | Slot machine telemetry |
| `--tables` | Table game events |
| `--players` | Player profiles |
| `--financial` | Financial transactions |
| `--security` | Security events |
| `--compliance` | Compliance filings |

### Quick Mode Volumes

When using `--quick`, the following reduced volumes are used:

| Data Type | Quick Mode | Full Mode |
|-----------|------------|-----------|
| Days | 7 | 30 |
| Slot Events | 10,000 | 500,000 |
| Table Events | 5,000 | 100,000 |
| Players | 1,000 | 10,000 |
| Financial | 2,000 | 50,000 |
| Security | 500 | 25,000 |
| Compliance | 200 | 10,000 |

---

## deploy-infrastructure.ps1 / deploy-infrastructure.sh

**Purpose:** Deploy Azure infrastructure using Bicep templates.

### What It Does

1. Loads configuration from `.env` file
2. Validates required variables
3. Creates Azure resource group
4. Deploys Bicep templates
5. Saves deployment outputs to `deployment-outputs.json`

### Usage

```powershell
# Windows
.\scripts\deploy-infrastructure.ps1
.\scripts\deploy-infrastructure.ps1 -Environment staging
.\scripts\deploy-infrastructure.ps1 -WhatIf
.\scripts\deploy-infrastructure.ps1 -NoPrompt
```

```bash
# Linux/macOS
./scripts/deploy-infrastructure.sh
./scripts/deploy-infrastructure.sh --environment staging
./scripts/deploy-infrastructure.sh --what-if
./scripts/deploy-infrastructure.sh --no-prompt
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-Environment` / `--environment` | Target: dev, staging, prod | `dev` |
| `-Location` / `--location` | Azure region | From `.env` or `eastus2` |
| `-WhatIf` / `--what-if` | Preview without deploying | `false` |
| `-NoPrompt` / `--no-prompt` | Skip confirmation prompts | `false` |
| `-ParameterFile` / `--parameter-file` | Custom Bicep parameter file | Auto-detected |

### Required .env Variables

```bash
AZURE_SUBSCRIPTION_ID=<your-subscription-id>
PROJECT_PREFIX=fabricpoc
FABRIC_ADMIN_EMAIL=admin@domain.com
```

### Optional .env Variables

```bash
AZURE_LOCATION=eastus2
FABRIC_CAPACITY_SKU=F64
ENABLE_PRIVATE_ENDPOINTS=false
LOG_RETENTION_DAYS=30
```

### Deployment Outputs

After deployment, `deployment-outputs.json` contains:

```json
{
    "deploymentName": "fabric-poc-dev-20250121-123456",
    "resourceGroup": "fabricpoc-dev-rg",
    "environment": "dev",
    "location": "eastus2",
    "timestamp": "2025-01-21T12:34:56Z",
    "outputs": {
        "storageAccountName": "fabricpocdevstorage",
        "fabricCapacityId": "/subscriptions/.../fabricCapacities/...",
        "logAnalyticsWorkspaceId": "..."
    }
}
```

---

## validate-environment.ps1 / validate-environment.sh

**Purpose:** Comprehensive validation of environment setup.

### What It Does

1. Checks all prerequisites
2. Validates configuration files
3. Tests Azure connectivity
4. Verifies Python dependencies
5. Tests generator imports
6. Runs smoke test (data generation)
7. Reports status with visual indicators

### Usage

```powershell
# Windows
.\scripts\validate-environment.ps1
.\scripts\validate-environment.ps1 -Quick
```

```bash
# Linux/macOS
./scripts/validate-environment.sh
./scripts/validate-environment.sh --quick
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-Quick` / `--quick` | Skip smoke tests | `false` |

### Checks Performed

**Prerequisites:**
- Python 3.10+
- Virtual environment
- Git
- Azure CLI
- Bicep

**Configuration:**
- `.env` file exists and configured
- `requirements.txt` exists
- Bicep templates exist
- Data generator exists

**Azure:**
- Azure CLI login status
- Subscription access

**Python:**
- Required packages importable
- Generator classes importable
- Data generation smoke test

### Exit Codes

| Code | Status |
|------|--------|
| `0` | All checks passed (or passed with warnings) |
| `1` | Validation failed |

---

## cleanup.ps1 / cleanup.sh

**Purpose:** Cleanup and teardown POC resources.

### What It Does

1. Deletes Azure resource group (with confirmation)
2. Cleans local generated data
3. Removes Python virtual environment
4. Cleans cache directories

### Usage

```powershell
# Windows
.\scripts\cleanup.ps1 -DeleteData
.\scripts\cleanup.ps1 -DeleteAzure
.\scripts\cleanup.ps1 -DeleteVenv
.\scripts\cleanup.ps1 -All
.\scripts\cleanup.ps1 -All -Force
.\scripts\cleanup.ps1 -DeleteAzure -Environment staging
```

```bash
# Linux/macOS
./scripts/cleanup.sh --delete-data
./scripts/cleanup.sh --delete-azure
./scripts/cleanup.sh --delete-venv
./scripts/cleanup.sh --all
./scripts/cleanup.sh --all --force
./scripts/cleanup.sh --delete-azure --environment staging
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-DeleteData` / `--delete-data` | Delete generated data | `false` |
| `-DeleteAzure` / `--delete-azure` | Delete Azure resource group | `false` |
| `-DeleteVenv` / `--delete-venv` | Delete virtual environment | `false` |
| `-All` / `--all` | Delete everything | `false` |
| `-Force` / `--force` | Skip confirmation prompts | `false` |
| `-Environment` / `--environment` | Target environment for Azure | `dev` |

### Safety Features

- **Confirmation prompts:** All destructive actions require confirmation
- **Azure deletion:** Requires typing the resource group name
- **Force mode:** Bypasses all prompts (use with caution)
- **Selective cleanup:** Delete only what you need

---

## Typical Workflows

### Initial Setup

```powershell
# 1. Setup environment
.\scripts\setup.ps1

# 2. Validate setup
.\scripts\validate-environment.ps1

# 3. Generate test data
.\scripts\generate-data.ps1 --quick
```

### Full POC Deployment

```powershell
# 1. Setup environment
.\scripts\setup.ps1

# 2. Configure .env file
code .env

# 3. Generate full dataset
.\scripts\generate-data.ps1 --all --days 30

# 4. Deploy infrastructure
.\scripts\deploy-infrastructure.ps1

# 5. Validate everything
.\scripts\validate-environment.ps1
```

### Cleanup After POC

```powershell
# Delete everything
.\scripts\cleanup.ps1 -All

# Or selectively
.\scripts\cleanup.ps1 -DeleteData
.\scripts\cleanup.ps1 -DeleteAzure
```

### Re-deploy to Different Environment

```powershell
# Deploy to staging
.\scripts\deploy-infrastructure.ps1 -Environment staging

# Later, cleanup staging
.\scripts\cleanup.ps1 -DeleteAzure -Environment staging
```

---

## Troubleshooting

### "Python not found"

1. Install Python 3.10+ from https://www.python.org/downloads/
2. Ensure Python is in your PATH
3. Run `setup.ps1` / `setup.sh` to create virtual environment

### "Azure CLI not logged in"

```bash
az login
az account set --subscription <subscription-id>
```

### "Bicep not installed"

```bash
az bicep install
```

### "Module import failed"

1. Ensure virtual environment is activated
2. Run `pip install -r requirements.txt`
3. Check for conflicting package versions

### "Deployment failed"

1. Check `.env` configuration
2. Verify Azure subscription access
3. Run with `--what-if` to preview changes
4. Check Azure Portal for detailed error messages

### "Permission denied" (Linux/macOS)

```bash
chmod +x scripts/*.sh
```

---

## Environment Variables Reference

The scripts use these environment variables from `.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_SUBSCRIPTION_ID` | Yes | Azure subscription ID |
| `PROJECT_PREFIX` | Yes | Prefix for resource names |
| `FABRIC_ADMIN_EMAIL` | Yes | Admin email for notifications |
| `AZURE_TENANT_ID` | No | Azure tenant ID |
| `AZURE_LOCATION` | No | Azure region (default: eastus2) |
| `FABRIC_CAPACITY_SKU` | No | Fabric capacity SKU (default: F64) |
| `ENABLE_PRIVATE_ENDPOINTS` | No | Enable private endpoints |
| `LOG_RETENTION_DAYS` | No | Log retention period |
| `DATA_GENERATION_DAYS` | No | Default data generation days |
| `SLOT_MACHINE_COUNT` | No | Number of slot machines |
| `PLAYER_COUNT` | No | Number of players |

---

## Cross-Platform Considerations

### Line Endings

If you encounter issues running bash scripts on Windows or vice versa:

```bash
# Convert to Unix line endings
dos2unix scripts/*.sh

# Convert to Windows line endings
unix2dos scripts/*.ps1
```

### Execution Policy (Windows)

If PowerShell scripts are blocked:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Permissions (Linux/macOS)

Make scripts executable:

```bash
chmod +x scripts/*.sh
```

---

## Contributing

When modifying scripts:

1. Update both `.ps1` and `.sh` versions
2. Test on all target platforms
3. Update this README with any new parameters
4. Follow existing code style and patterns
