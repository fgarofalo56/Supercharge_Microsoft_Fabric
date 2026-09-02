---
hero: assets/heroes/getting-started.svg
hero_alt: Prerequisites — What you need before deploying
type: quick-start
---
# 📋 Prerequisites Guide

<div align="center" markdown>

# 📋 Prerequisites

**Setup Requirements & Configuration**

![Category](https://img.shields.io/badge/Category-Setup-lightgrey?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-January_2025-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2025-01-21` | **Version:** 1.0.0

---

## 🔀 Deployment Path Selection

Before starting, decide which deployment path suits your needs:

| | **Path B — Quickstart** | **Path A — Production-Aligned** |
|---|---|---|
| **You need** | Fabric capacity + workspace | Azure subscription + Fabric capacity |
| **Deploy Bicep?** | No | Yes (`infra/main.bicep`) |
| **Data flow** | Upload → OneLake directly | Upload → ADLS → OneLake shortcut |
| **Tutorials unlocked** | 00-05 (core medallion) | All tutorials including 06, 07, 14, 17, 22 |
| **Azure cost** | Fabric capacity only | +$1-3/day (Purview, Storage, KV, LAW) |

> **Recommendation:** Start with **Path B** to learn the medallion architecture quickly. Upgrade to **Path A** when you're ready for governance, security, and monitoring tutorials. The upgrade is non-destructive — deploy Bicep, move data, swap notebook source paths.

---

## ☁️ Azure Requirements

### Subscription Access

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **Role** | Contributor | Owner |
| **Scope** | Resource Group | Subscription |
| **Quota** | Sufficient for F64 | 2x capacity |

> 📋 **Prerequisites:** Owner role is recommended for initial setup to configure RBAC and resource providers. If you only have Contributor access, coordinate with your subscription owner for role assignments.

### Resource Provider Registration

Register these providers before deployment:

```bash
# Register required providers
az provider register --namespace Microsoft.Fabric
az provider register --namespace Microsoft.Purview
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.KeyVault
az provider register --namespace Microsoft.Network
az provider register --namespace Microsoft.OperationalInsights
az provider register --namespace Microsoft.ManagedIdentity

# Verify registration (should show "Registered")
az provider list --query "[?namespace=='Microsoft.Fabric'].registrationState" -o tsv
```

### Required Resource Providers

| ☁️ Provider | 📋 Purpose | ✅ Required |
|:------------|:-----------|:-----------:|
| `Microsoft.Fabric` | Fabric capacities and workspaces | **Yes** |
| `Microsoft.Purview` | Data governance and catalog | **Yes** |
| `Microsoft.Storage` | ADLS Gen2 storage | **Yes** |
| `Microsoft.KeyVault` | Secrets management | **Yes** |
| `Microsoft.Network` | VNet and private endpoints | **Yes** |
| `Microsoft.OperationalInsights` | Log Analytics | **Yes** |
| `Microsoft.ManagedIdentity` | Managed identities | **Yes** |

### Microsoft Fabric Requirements

| Requirement | Details |
|-------------|---------|
| **Fabric enabled** | Must be enabled in Microsoft Entra ID tenant |
| **Capacity available** | F64 SKU recommended for POC |
| **Region support** | Check [region availability](https://learn.microsoft.com/fabric/enterprise/region-availability) |

#### Enable Fabric in Tenant

1. Go to [Azure Portal](https://portal.azure.com) > Microsoft Fabric
2. Or [Fabric Admin Portal](https://app.fabric.microsoft.com/admin-portal)
3. Ensure Fabric is enabled for your organization

![Fabric Admin Center](https://learn.microsoft.com/en-us/fabric/admin/media/admin-center/admin-center.png)

*Source: [Microsoft Fabric Admin Center](https://learn.microsoft.com/en-us/fabric/admin/admin-center)*

> ⚠️ **Warning:** Enabling Fabric requires Microsoft Entra ID Global Administrator or Fabric Administrator permissions. Contact your tenant admin if you don't have these roles.

### Quota Verification

```bash
# Check current quota for Fabric capacities
az quota show \
  --scope "/subscriptions/{subscription-id}/providers/Microsoft.Fabric/locations/eastus2" \
  --resource-name "F64"
```

You can also view capacity settings in the Azure portal:

![Fabric Capacity Settings in Azure Portal](https://learn.microsoft.com/en-us/fabric/admin/media/service-admin-portal-capacity-settings/capacity-settings.png)

*Source: [Capacity Settings in Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/admin/service-admin-portal-capacity-settings)*

---

## 💻 Local Development Environment

### Required Tools

| 🛠️ Tool | 📌 Version | ✅ Verify / Install | 📋 Purpose |
|:--------|:-----------|:--------------------|:-----------|
| **Azure CLI** | `2.50+` | `winget install -e --id Microsoft.AzureCLI` | Azure management |
| **Bicep** | `0.22+` | `az bicep install && az bicep upgrade` | Infrastructure as Code |
| **Git** | `2.40+` | `winget install -e --id Git.Git` | Version control |
| **PowerShell** | `7.0+` | `winget install -e --id Microsoft.PowerShell` | Scripting |
| **Python** | `3.10+` | `winget install -e --id Python.Python.3.11` | Data tools |
| **VS Code** | `Latest` | `winget install -e --id Microsoft.VisualStudioCode` | IDE |

<details>
<summary><b>🔍 Click to expand: Optional Tools (Recommended)</b></summary>

### Optional Tools (Recommended)

| 🛠️ Tool | 📌 Version | ✅ Verify / Install | 📋 Purpose |
|:--------|:-----------|:--------------------|:-----------|
| **Docker Desktop** | `Latest` | `winget install -e --id Docker.DockerDesktop` | Container-based data generation |
| **Docker Compose** | `V2+` | Included with Docker Desktop | Multi-service orchestration |

</details>

### Installation Commands

#### Windows (using winget)

```powershell
# Install all required tools
winget install -e --id Microsoft.AzureCLI
winget install -e --id Git.Git
winget install -e --id Microsoft.PowerShell
winget install -e --id Python.Python.3.11
winget install -e --id Microsoft.VisualStudioCode

# Install Bicep via Azure CLI
az bicep install
az bicep upgrade
```

#### macOS (using Homebrew)

```bash
# Install all required tools
brew install azure-cli
brew install git
brew install powershell/tap/powershell
brew install python@3.11

# Install Bicep
az bicep install
az bicep upgrade
```

<details>
<summary><b>🔍 Click to expand: VS Code Extensions</b></summary>

### VS Code Extensions

> 💡 **Pro Tip:** Run all extension installations at once by pasting the entire script block into your terminal.

```bash
# Install recommended extensions
code --install-extension ms-azuretools.vscode-bicep
code --install-extension ms-vscode.azure-account
code --install-extension ms-python.python
code --install-extension ms-toolsai.jupyter
code --install-extension GitHub.copilot
code --install-extension ms-vscode-remote.remote-containers
code --install-extension ms-azuretools.vscode-docker
```

| 🧩 Extension | 🔖 ID | 📋 Purpose |
|:-------------|:------|:-----------|
| **Bicep** | `ms-azuretools.vscode-bicep` | IaC authoring |
| **Azure Account** | `ms-vscode.azure-account` | Azure authentication |
| **Python** | `ms-python.python` | Python development |
| **Jupyter** | `ms-toolsai.jupyter` | Notebook support |
| **GitHub Copilot** | `GitHub.copilot` | AI assistance |
| **Dev Containers** ⭐ | `ms-vscode-remote.remote-containers` | One-click dev environment |
| **Docker** ⭐ | `ms-azuretools.vscode-docker` | Container management |

> 💡 **Pro Tip:** The Dev Containers extension enables one-click development environment setup. Open the repository and click "Reopen in Container" when prompted.

</details>

### Dev Container Setup (Alternative to Local Installation)

If you prefer using Dev Containers, you only need:

1. **Docker Desktop** (with WSL 2 backend on Windows)
2. **VS Code** with Dev Containers extension
3. **Git** (to clone the repository)

All other tools (Python, Azure CLI, Bicep, etc.) are pre-installed in the container.

```bash
# Quick start with Dev Container
git clone https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric.git
code Suppercharge_Microsoft_Fabric
# Then click "Reopen in Container" when prompted
```

**GitHub Codespaces Alternative:**
No local installation required. Click "Code" > "Codespaces" > "Create codespace" on the GitHub repository.

### Python Environment Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate (Windows CMD)
.\.venv\Scripts\activate.bat

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Verify Installation

```bash
# Verify all tools
echo "Azure CLI: $(az --version | head -1)"
echo "Bicep: $(az bicep version)"
echo "Git: $(git --version)"
echo "PowerShell: $(pwsh --version)"
echo "Python: $(python --version)"
```

**Expected Output:**

```
Azure CLI: azure-cli 2.55.0
Bicep: Bicep CLI version 0.24.24
Git: git version 2.43.0
PowerShell: PowerShell 7.4.1
Python: Python 3.11.7
```

---

## 🔑 Microsoft Entra ID Configuration

### Required Permissions

| Permission | Scope | Purpose |
|------------|-------|---------|
| `User.Read` | Delegated | Read user profile |
| `Directory.Read.All` | Application | Read directory data |
| `Fabric.Read.All` | Delegated | Read Fabric resources |

### Service Principal Setup (for CI/CD)

> 📋 **Prerequisites:** You'll need this service principal for GitHub Actions automation. Skip this step if you're only doing manual deployments.

```bash
# Create service principal
az ad sp create-for-rbac \
  --name "sp-fabric-poc-deploy" \
  --role "Contributor" \
  --scopes "/subscriptions/{subscription-id}" \
  --sdk-auth

# Save output for GitHub secrets
```

> ⚠️ **Warning:** Store the service principal credentials securely. Never commit them to source control. Use a password manager or Azure Key Vault.

### Configure OIDC for GitHub Actions

```bash
# Get app registration object ID
APP_ID=$(az ad app list --display-name "sp-fabric-poc-deploy" --query "[0].appId" -o tsv)

# Create federated credential
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "github-actions-main",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:YOUR_ORG/Suppercharge_Microsoft_Fabric:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

---

## 🌐 Network Requirements

### Outbound Connectivity

> 📋 **Prerequisites:** If you're behind a corporate firewall, coordinate with your network team to whitelist these endpoints before deployment.

Ensure these endpoints are accessible from your deployment environment:

| Service | Endpoints | Ports |
|---------|-----------|-------|
| Azure Management | `management.azure.com` | 443 |
| Microsoft Entra ID | `login.microsoftonline.com` | 443 |
| Fabric | `*.fabric.microsoft.com` | 443 |
| Power BI | `*.powerbi.com` | 443 |
| Storage | `*.blob.core.windows.net` | 443 |
| Key Vault | `*.vault.azure.net` | 443 |

### Firewall Rules (if applicable)

```
# Azure services (add to allowlist)
AzureCloud.EastUS2
AzureCloud.WestUS2
```

> ℹ️ **Note:** If using a corporate firewall, work with your network team to whitelist these endpoints.

---

## ✅ Pre-Deployment Checklist

### Azure Subscription

| Task | Status | Notes |
|------|--------|-------|
| Subscription with sufficient quota | ☐ | Check F64 availability |
| Owner or Contributor access | ☐ | Verify role assignment |
| Resource providers registered | ☐ | Run registration commands |
| Fabric enabled in tenant | ☐ | Check admin portal |

### Local Environment

| Task | Status | Notes |
|------|--------|-------|
| Azure CLI installed and logged in | ☐ | `az login` |
| Bicep extension installed | ☐ | `az bicep install` |
| Git configured | ☐ | Clone repository |
| Python environment ready | ☐ | Create virtual environment |

### Configuration Files

| Task | Status | Notes |
|------|--------|-------|
| `.env` file created from `.env.sample` | ☐ | Copy and edit |
| All required values populated | ☐ | No empty required fields |
| Unique names for globally unique resources | ☐ | Purview, Storage |

### Security

| Task | Status | Notes |
|------|--------|-------|
| Service principal created (for CI/CD) | ☐ | Store credentials securely |
| GitHub secrets configured | ☐ | Add to repository |
| Key Vault access policies planned | ☐ | Define who needs access |

---

## 📝 Environment Variables Reference

Create a `.env` file from `.env.sample` with the following values:

### Required Variables

```bash
# Azure Configuration
AZURE_SUBSCRIPTION_ID=        # Your Azure subscription ID
AZURE_TENANT_ID=              # Your Microsoft Entra ID tenant ID
AZURE_LOCATION=eastus2        # Deployment region
ENVIRONMENT=dev               # dev, staging, or prod
PROJECT_PREFIX=fabricpoc      # 3-10 char prefix for naming

# Fabric Settings
FABRIC_CAPACITY_SKU=F64       # Capacity SKU (F2, F4, F16, F32, F64)
FABRIC_ADMIN_EMAIL=           # Admin notification email

# Resource Names (must be globally unique)
PURVIEW_ACCOUNT_NAME=         # Purview account (globally unique)
STORAGE_ACCOUNT_NAME=         # ADLS Gen2 storage (globally unique)
KEY_VAULT_NAME=               # Key Vault (globally unique)
```

### Variable Requirements

| 🔑 Variable | ✅ Required | 📝 Format | 💡 Example |
|:------------|:-----------:|:----------|:-----------|
| `AZURE_SUBSCRIPTION_ID` | **Yes** | GUID | `12345678-1234-1234-1234-123456789012` |
| `AZURE_TENANT_ID` | **Yes** | GUID | `12345678-1234-1234-1234-123456789012` |
| `AZURE_LOCATION` | **Yes** | Region code | `eastus2`, `westus2` |
| `ENVIRONMENT` | **Yes** | String | `dev`, `staging`, `prod` |
| `PROJECT_PREFIX` | **Yes** | 3-10 chars | `fabricpoc` |
| `FABRIC_CAPACITY_SKU` | **Yes** | SKU name | `F2`, `F4`, `F64` |
| `PURVIEW_ACCOUNT_NAME` | **Yes** | Globally unique | `pv-fabricpoc-dev-001` |
| `STORAGE_ACCOUNT_NAME` | **Yes** | Globally unique | `stfabricpocdev001` |

> ⚠️ **Warning:** Storage account names must be globally unique across all of Azure and use only lowercase letters and numbers (no hyphens or special characters).

---

## 🧪 Validation Script

<details>
<summary><b>🔍 Click to expand: Full Validation Script</b></summary>

Save and run this script to verify prerequisites:

```bash
#!/bin/bash
# verify-prerequisites.sh

echo "=== Verifying Prerequisites ==="
echo ""

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not installed"
    exit 1
else
    echo "✅ Azure CLI: $(az --version | head -1)"
fi

# Check login status
if ! az account show &> /dev/null; then
    echo "❌ Not logged into Azure"
    exit 1
else
    echo "✅ Logged into Azure: $(az account show --query name -o tsv)"
fi

# Check Bicep
if ! az bicep version &> /dev/null; then
    echo "❌ Bicep not installed"
    exit 1
else
    echo "✅ Bicep: $(az bicep version)"
fi

# Check Git
if ! command -v git &> /dev/null; then
    echo "❌ Git not installed"
else
    echo "✅ Git: $(git --version)"
fi

# Check Python
if ! command -v python &> /dev/null; then
    echo "❌ Python not installed"
else
    echo "✅ Python: $(python --version)"
fi

# Check Fabric provider
FABRIC_STATE=$(az provider show --namespace Microsoft.Fabric --query registrationState -o tsv 2>/dev/null)
if [ "$FABRIC_STATE" != "Registered" ]; then
    echo "❌ Microsoft.Fabric provider not registered"
else
    echo "✅ Microsoft.Fabric provider registered"
fi

# Check .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found (copy from .env.sample)"
else
    echo "✅ .env file exists"
fi

echo ""
echo "=== Verification Complete ==="
```

### Running the Script

```bash
# Make script executable (Linux/Mac)
chmod +x verify-prerequisites.sh

# Run verification
./verify-prerequisites.sh
```

</details>

---

## 🔧 Troubleshooting

<details>
<summary><b>🔍 Click to expand: Troubleshooting Commands & Solutions</b></summary>

### Azure CLI Login Issues

```bash
# Clear cached credentials
az account clear
az cache purge
az login
```

### Bicep Build Errors

```bash
# Update Bicep to latest
az bicep upgrade

# Clear Bicep cache
rm -rf ~/.bicep
```

### Provider Registration Stuck

```bash
# Force re-registration
az provider unregister --namespace Microsoft.Fabric
az provider register --namespace Microsoft.Fabric

# Check status
az provider show --namespace Microsoft.Fabric --query "registrationState"
```

### Common Error Messages

| ❌ Error | 🔍 Cause | ✅ Solution |
|:---------|:---------|:-----------|
| `AuthorizationFailed` | Insufficient permissions | Request Owner/Contributor role |
| `ResourceProviderNotRegistered` | Provider not enabled | Run registration command |
| `QuotaExceeded` | Insufficient quota | Request quota increase |
| `NameNotAvailable` | Resource name taken | Choose a different name |

</details>

---

## 📚 Next Steps

After completing prerequisites:

| Step | Document | Description |
|------|----------|-------------|
| 1 | [🏗️ Architecture](architecture.md) | Review system design |
| 2 | [🚀 Deployment](deployment.md) | Deploy infrastructure |
| 3 | [Tutorial 00](tutorials/00-environment-setup/README.md) | Hands-on setup |

---

## 📚 Related Documentation

| Document | Description |
|----------|-------------|
| [🏗️ Architecture](architecture.md) | System architecture and design |
| [🚀 Deployment Guide](deployment.md) | Infrastructure deployment |
| [🔐 Security Guide](security.md) | Security controls and compliance |

---

[⬆️ Back to top](#-prerequisites-guide)

---

> 📖 **Documentation maintained by:** Frank Garofalo
> 🔗 **Repository:** [Suppercharge_Microsoft_Fabric](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric)
