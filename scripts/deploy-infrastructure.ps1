#Requires -Version 5.1
<#
.SYNOPSIS
    Deploy Microsoft Fabric POC infrastructure to Azure.

.DESCRIPTION
    This script deploys all Azure infrastructure for the Casino/Gaming POC:
    - Loads configuration from .env file
    - Validates required variables
    - Deploys Bicep templates
    - Outputs resource URLs and connection info
    - Saves deployment outputs to JSON

.PARAMETER Environment
    Target environment: dev, staging, prod (default: dev)

.PARAMETER Location
    Azure region for deployment (default: from .env or eastus2)

.PARAMETER WhatIf
    Preview deployment without making changes

.PARAMETER NoPrompt
    Skip confirmation prompts

.PARAMETER ParameterFile
    Path to Bicep parameter file (overrides .env)

.EXAMPLE
    .\deploy-infrastructure.ps1
    .\deploy-infrastructure.ps1 -Environment staging
    .\deploy-infrastructure.ps1 -WhatIf
    .\deploy-infrastructure.ps1 -NoPrompt

.NOTES
    Author: Microsoft Fabric POC Team
    Version: 1.0.0
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment = "dev",
    [string]$Location = "",
    [switch]$NoPrompt,
    [string]$ParameterFile = ""
)

# =============================================================================
# Configuration
# =============================================================================
$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot
$InfraPath = Join-Path $ProjectRoot "infra"
$EnvFile = Join-Path $ProjectRoot ".env"
$OutputFile = Join-Path $ProjectRoot "deployment-outputs.json"

# =============================================================================
# Helper Functions
# =============================================================================

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "=" * 70 -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "=" * 70 -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host "[*] $Message" -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Message)
    Write-Host "[+] $Message" -ForegroundColor Green
}

function Write-Failure {
    param([string]$Message)
    Write-Host "[-] $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "    $Message" -ForegroundColor Gray
}

function Load-EnvFile {
    param([string]$Path)

    $envVars = @{}

    if (Test-Path $Path) {
        Get-Content $Path | ForEach-Object {
            $line = $_.Trim()
            # Skip comments and empty lines
            if ($line -and -not $line.StartsWith("#")) {
                $parts = $line -split "=", 2
                if ($parts.Count -eq 2) {
                    $key = $parts[0].Trim()
                    $value = $parts[1].Trim()
                    # Remove surrounding quotes
                    $value = $value -replace '^["'']|["'']$', ''
                    $envVars[$key] = $value
                }
            }
        }
    }

    return $envVars
}

function Test-RequiredVariables {
    param(
        [hashtable]$EnvVars,
        [string[]]$Required
    )

    $missing = @()
    foreach ($var in $Required) {
        if (-not $EnvVars.ContainsKey($var) -or [string]::IsNullOrWhiteSpace($EnvVars[$var]) -or $EnvVars[$var] -match "^<.*>$") {
            $missing += $var
        }
    }

    return $missing
}

# =============================================================================
# Main Script
# =============================================================================

Write-Header "Microsoft Fabric POC - Infrastructure Deployment"

Write-Info "Project Root: $ProjectRoot"
Write-Info "Environment:  $Environment"
Write-Host ""

# =============================================================================
# Step 1: Load Environment Configuration
# =============================================================================
Write-Header "Step 1: Loading Configuration"

if (-not (Test-Path $EnvFile)) {
    Write-Failure ".env file not found at $EnvFile"
    Write-Info "Copy .env.sample to .env and configure your values"
    Write-Info "Run: copy .env.sample .env"
    exit 1
}

Write-Step "Loading .env file..."
$envVars = Load-EnvFile $EnvFile
Write-Success "Loaded $($envVars.Count) environment variables"

# =============================================================================
# Step 2: Validate Required Variables
# =============================================================================
Write-Header "Step 2: Validating Configuration"

$requiredVars = @(
    "AZURE_SUBSCRIPTION_ID",
    "PROJECT_PREFIX",
    "FABRIC_ADMIN_EMAIL"
)

$missingVars = Test-RequiredVariables $envVars $requiredVars

if ($missingVars.Count -gt 0) {
    Write-Failure "Missing or invalid required variables:"
    foreach ($var in $missingVars) {
        Write-Info "  - $var"
    }
    Write-Host ""
    Write-Info "Please configure these in your .env file"
    exit 1
}

Write-Success "All required variables configured"

# Display configuration
Write-Step "Deployment Configuration:"
Write-Info "Subscription:    $($envVars['AZURE_SUBSCRIPTION_ID'])"
Write-Info "Project Prefix:  $($envVars['PROJECT_PREFIX'])"
Write-Info "Admin Email:     $($envVars['FABRIC_ADMIN_EMAIL'])"
Write-Info "Fabric SKU:      $($envVars.GetValueOrDefault('FABRIC_CAPACITY_SKU', 'F64'))"

if ($Location) {
    Write-Info "Location:        $Location (override)"
} else {
    $Location = $envVars.GetValueOrDefault('AZURE_LOCATION', 'eastus2')
    Write-Info "Location:        $Location"
}

# =============================================================================
# Step 3: Validate Azure CLI Login
# =============================================================================
Write-Header "Step 3: Validating Azure Connection"

Write-Step "Checking Azure CLI login..."
$account = az account show 2>$null | ConvertFrom-Json

if (-not $account) {
    Write-Failure "Not logged in to Azure CLI"
    Write-Info "Run 'az login' to authenticate"
    exit 1
}

Write-Success "Logged in as: $($account.user.name)"
Write-Info "Current subscription: $($account.name)"

# Check if correct subscription
if ($account.id -ne $envVars['AZURE_SUBSCRIPTION_ID']) {
    Write-Step "Switching to configured subscription..."
    az account set --subscription $envVars['AZURE_SUBSCRIPTION_ID']
    if ($LASTEXITCODE -ne 0) {
        Write-Failure "Failed to set subscription"
        exit 1
    }
    Write-Success "Subscription set to: $($envVars['AZURE_SUBSCRIPTION_ID'])"
}

# =============================================================================
# Step 4: Prepare Deployment
# =============================================================================
Write-Header "Step 4: Preparing Deployment"

# Determine parameter file
if ($ParameterFile -and (Test-Path $ParameterFile)) {
    $bicepParams = $ParameterFile
    Write-Info "Using parameter file: $ParameterFile"
} else {
    # Check for environment-specific parameter file
    $envParamFile = Join-Path $InfraPath "environments\$Environment\$Environment.bicepparam"
    if (Test-Path $envParamFile) {
        $bicepParams = $envParamFile
        Write-Info "Using environment params: $envParamFile"
    } else {
        # Use default parameter file
        $bicepParams = Join-Path $InfraPath "main.bicepparam"
        Write-Info "Using default params: $bicepParams"
    }
}

# Check Bicep files exist
$mainBicep = Join-Path $InfraPath "main.bicep"
if (-not (Test-Path $mainBicep)) {
    Write-Failure "main.bicep not found at $mainBicep"
    exit 1
}

# Resource group name
$resourceGroupName = "rg-$($envVars['PROJECT_PREFIX'])-$Environment"
Write-Info "Resource Group: $resourceGroupName"

# =============================================================================
# Step 5: Confirm Deployment
# =============================================================================
if (-not $NoPrompt -and -not $WhatIfPreference) {
    Write-Header "Deployment Summary"
    Write-Host "The following resources will be deployed:" -ForegroundColor Yellow
    Write-Host ""
    Write-Info "Resource Group:     $resourceGroupName"
    Write-Info "Location:           $Location"
    Write-Info "Environment:        $Environment"
    Write-Info "Fabric Capacity:    $($envVars.GetValueOrDefault('FABRIC_CAPACITY_SKU', 'F64'))"
    Write-Info "Private Endpoints:  $($envVars.GetValueOrDefault('ENABLE_PRIVATE_ENDPOINTS', 'false'))"
    Write-Host ""

    $response = Read-Host "Do you want to proceed with deployment? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Info "Deployment cancelled"
        exit 0
    }
}

# =============================================================================
# Step 6: Create Resource Group
# =============================================================================
Write-Header "Step 6: Creating Resource Group"

Write-Step "Creating resource group: $resourceGroupName"

$rgExists = az group exists --name $resourceGroupName
if ($rgExists -eq "true") {
    Write-Info "Resource group already exists"
} else {
    az group create `
        --name $resourceGroupName `
        --location $Location `
        --tags Environment=$Environment Project=$($envVars['PROJECT_PREFIX']) | Out-Null

    if ($LASTEXITCODE -ne 0) {
        Write-Failure "Failed to create resource group"
        exit 1
    }
    Write-Success "Resource group created"
}

# =============================================================================
# Step 7: Deploy Bicep Template
# =============================================================================
Write-Header "Step 7: Deploying Infrastructure"

$deploymentName = "fabric-poc-$Environment-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

Write-Step "Starting deployment: $deploymentName"
Write-Info "This may take 10-20 minutes..."
Write-Host ""

# Build deployment command
$deployArgs = @(
    "deployment", "sub", "create",
    "--location", $Location,
    "--template-file", $mainBicep,
    "--parameters", $bicepParams,
    "--parameters", "environment=$Environment",
    "--parameters", "location=$Location",
    "--parameters", "projectPrefix=$($envVars['PROJECT_PREFIX'])",
    "--parameters", "fabricAdminEmail=$($envVars['FABRIC_ADMIN_EMAIL'])",
    "--name", $deploymentName,
    "--output", "json"
)

# Add optional parameters
if ($envVars.ContainsKey('FABRIC_CAPACITY_SKU')) {
    $deployArgs += @("--parameters", "fabricCapacitySku=$($envVars['FABRIC_CAPACITY_SKU'])")
}
if ($envVars.ContainsKey('ENABLE_PRIVATE_ENDPOINTS')) {
    $deployArgs += @("--parameters", "enablePrivateEndpoints=$($envVars['ENABLE_PRIVATE_ENDPOINTS'])")
}
if ($envVars.ContainsKey('LOG_RETENTION_DAYS')) {
    $deployArgs += @("--parameters", "logRetentionDays=$($envVars['LOG_RETENTION_DAYS'])")
}

# What-If mode
if ($WhatIfPreference) {
    Write-Info "Running in What-If mode..."
    $deployArgs += "--what-if"
}

# Run deployment
$startTime = Get-Date

try {
    $result = az @deployArgs 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Failure "Deployment failed"
        Write-Host $result -ForegroundColor Red
        exit 1
    }

    $endTime = Get-Date
    $duration = $endTime - $startTime

    if (-not $WhatIfPreference) {
        Write-Success "Deployment completed in $($duration.ToString('mm\:ss'))"
    }

} catch {
    Write-Failure "Deployment error: $_"
    exit 1
}

# =============================================================================
# Step 8: Retrieve and Save Outputs
# =============================================================================
if (-not $WhatIfPreference) {
    Write-Header "Step 8: Retrieving Deployment Outputs"

    Write-Step "Fetching deployment outputs..."

    $outputs = az deployment sub show `
        --name $deploymentName `
        --query "properties.outputs" `
        --output json 2>$null | ConvertFrom-Json

    if ($outputs) {
        # Build outputs object
        $outputData = @{
            deploymentName = $deploymentName
            resourceGroup = $resourceGroupName
            environment = $Environment
            location = $Location
            timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
            outputs = @{}
        }

        # Process outputs
        $outputs.PSObject.Properties | ForEach-Object {
            $outputData.outputs[$_.Name] = $_.Value.value
        }

        # Save to file
        $outputData | ConvertTo-Json -Depth 10 | Set-Content $OutputFile
        Write-Success "Outputs saved to: $OutputFile"

        # Display key outputs
        Write-Header "Deployment Outputs"

        if ($outputData.outputs.Count -gt 0) {
            foreach ($key in $outputData.outputs.Keys) {
                $value = $outputData.outputs[$key]
                if ($value -is [string] -and $value.Length -lt 80) {
                    Write-Info "$($key.PadRight(30)) $value"
                } else {
                    Write-Info "$($key.PadRight(30)) [see $OutputFile]"
                }
            }
        } else {
            Write-Info "No outputs returned from deployment"
        }

    } else {
        Write-Info "No outputs to retrieve"
    }

    # =============================================================================
    # Summary
    # =============================================================================
    Write-Header "Deployment Complete!"

    Write-Success "Infrastructure deployed successfully"
    Write-Host ""
    Write-Host "Key Information:" -ForegroundColor Yellow
    Write-Info "Resource Group:   $resourceGroupName"
    Write-Info "Deployment Name:  $deploymentName"
    Write-Info "Outputs File:     $OutputFile"
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Review deployment outputs in $OutputFile"
    Write-Host "  2. Configure Microsoft Fabric workspace"
    Write-Host "  3. Upload generated data to storage"
    Write-Host "  4. Run notebooks in Microsoft Fabric"
    Write-Host ""

} else {
    Write-Header "What-If Complete"
    Write-Info "Review the changes above"
    Write-Info "Remove -WhatIf to perform actual deployment"
}
