#Requires -Version 5.1
<#
.SYNOPSIS
    Validate the Microsoft Fabric POC environment setup.

.DESCRIPTION
    This script performs comprehensive validation:
    - Check all prerequisites (Python, Azure CLI, Bicep, Git)
    - Validate Azure connectivity
    - Test generator imports
    - Run quick smoke test
    - Report status with checkmarks

.PARAMETER Quick
    Skip smoke tests, only check prerequisites

.PARAMETER Verbose
    Show detailed output for all checks

.EXAMPLE
    .\validate-environment.ps1
    .\validate-environment.ps1 -Quick
    .\validate-environment.ps1 -Verbose

.NOTES
    Author: Microsoft Fabric POC Team
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [switch]$Quick
)

# =============================================================================
# Configuration
# =============================================================================
$ErrorActionPreference = "Continue"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot
$DataGenPath = Join-Path $ProjectRoot "data_generation"
$EnvFile = Join-Path $ProjectRoot ".env"

$MinPythonVersion = [Version]"3.10.0"

# Track results
$Results = @{
    Passed = 0
    Failed = 0
    Warnings = 0
    Checks = @()
}

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

function Write-Check {
    param(
        [string]$Name,
        [string]$Status,  # "PASS", "FAIL", "WARN", "SKIP"
        [string]$Message = ""
    )

    $icon = switch ($Status) {
        "PASS" { "[OK]"; $color = "Green" }
        "FAIL" { "[X] "; $color = "Red" }
        "WARN" { "[!] "; $color = "Yellow" }
        "SKIP" { "[-] "; $color = "Gray" }
        default { "[?] "; $color = "Gray" }
    }

    $checkLine = "$icon $Name"
    if ($Message) {
        $checkLine += " - $Message"
    }

    Write-Host $checkLine -ForegroundColor $color

    # Track result
    switch ($Status) {
        "PASS" { $script:Results.Passed++ }
        "FAIL" { $script:Results.Failed++ }
        "WARN" { $script:Results.Warnings++ }
    }

    $script:Results.Checks += @{
        Name = $Name
        Status = $Status
        Message = $Message
    }
}

function Write-SubCheck {
    param(
        [string]$Message
    )
    Write-Host "      $Message" -ForegroundColor Gray
}

function Test-CommandExists {
    param([string]$Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Get-PythonVersion {
    param([string]$PythonCmd)
    try {
        $output = & $PythonCmd --version 2>&1
        if ($output -match "Python (\d+\.\d+\.\d+)") {
            return [Version]$Matches[1]
        }
    } catch {}
    return $null
}

function Get-VenvPython {
    $venvPaths = @(
        (Join-Path $ProjectRoot ".venv\Scripts\python.exe"),
        (Join-Path $ProjectRoot "venv\Scripts\python.exe"),
        (Join-Path $ProjectRoot ".venv\bin\python"),
        (Join-Path $ProjectRoot "venv\bin\python")
    )

    foreach ($path in $venvPaths) {
        if (Test-Path $path) {
            return $path
        }
    }

    # Fall back to system Python
    foreach ($cmd in @("python", "python3", "py")) {
        if (Test-CommandExists $cmd) {
            return $cmd
        }
    }

    return $null
}

# =============================================================================
# Main Script
# =============================================================================

Write-Header "Microsoft Fabric POC - Environment Validation"

Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray
Write-Host "Timestamp:    $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

# =============================================================================
# Section 1: Prerequisites
# =============================================================================
Write-Header "Prerequisites Check"

# Python
$PythonCmd = Get-VenvPython
if ($PythonCmd) {
    $version = Get-PythonVersion $PythonCmd
    if ($version -and $version -ge $MinPythonVersion) {
        Write-Check "Python" "PASS" "Version $version ($PythonCmd)"
    } else {
        Write-Check "Python" "FAIL" "Version $version < $MinPythonVersion required"
    }
} else {
    Write-Check "Python" "FAIL" "Not found"
}

# Virtual Environment
$venvPath = Join-Path $ProjectRoot ".venv"
if (Test-Path $venvPath) {
    Write-Check "Virtual Environment" "PASS" ".venv exists"
} else {
    $venvPath = Join-Path $ProjectRoot "venv"
    if (Test-Path $venvPath) {
        Write-Check "Virtual Environment" "PASS" "venv exists"
    } else {
        Write-Check "Virtual Environment" "WARN" "Not found - run setup.ps1"
    }
}

# Git
if (Test-CommandExists "git") {
    $gitVersion = (git --version) -replace "git version ", ""
    Write-Check "Git" "PASS" "Version $gitVersion"
} else {
    Write-Check "Git" "FAIL" "Not found"
}

# Azure CLI
if (Test-CommandExists "az") {
    $azVersion = az version --query '\"azure-cli\"' -o tsv 2>$null
    Write-Check "Azure CLI" "PASS" "Version $azVersion"
} else {
    Write-Check "Azure CLI" "FAIL" "Not found"
}

# Bicep
if (Test-CommandExists "az") {
    $bicepVersion = az bicep version 2>$null
    if ($bicepVersion) {
        $bicepVer = $bicepVersion -replace "Bicep CLI version ", ""
        Write-Check "Bicep" "PASS" "Version $bicepVer"
    } else {
        Write-Check "Bicep" "WARN" "Not installed - run 'az bicep install'"
    }
} else {
    Write-Check "Bicep" "SKIP" "Azure CLI required"
}

# =============================================================================
# Section 2: Configuration Files
# =============================================================================
Write-Header "Configuration Files"

# .env file
if (Test-Path $EnvFile) {
    $envContent = Get-Content $EnvFile -Raw
    $placeholders = ($envContent | Select-String "<.*>" -AllMatches).Matches.Count
    if ($placeholders -gt 0) {
        Write-Check ".env file" "WARN" "Found $placeholders unconfigured placeholders"
    } else {
        Write-Check ".env file" "PASS" "Exists and configured"
    }
} else {
    Write-Check ".env file" "WARN" "Not found - copy from .env.sample"
}

# requirements.txt
$reqFile = Join-Path $ProjectRoot "requirements.txt"
if (Test-Path $reqFile) {
    Write-Check "requirements.txt" "PASS" "Exists"
} else {
    Write-Check "requirements.txt" "FAIL" "Not found"
}

# Infrastructure files
$mainBicep = Join-Path $ProjectRoot "infra\main.bicep"
if (Test-Path $mainBicep) {
    Write-Check "Bicep templates" "PASS" "infra/main.bicep exists"
} else {
    Write-Check "Bicep templates" "WARN" "infra/main.bicep not found"
}

# Data generation
$genPy = Join-Path $DataGenPath "generate.py"
if (Test-Path $genPy) {
    Write-Check "Data generator" "PASS" "generate.py exists"
} else {
    Write-Check "Data generator" "FAIL" "generate.py not found"
}

# =============================================================================
# Section 3: Azure Connectivity
# =============================================================================
Write-Header "Azure Connectivity"

if (Test-CommandExists "az") {
    $account = az account show 2>$null | ConvertFrom-Json
    if ($account) {
        Write-Check "Azure Login" "PASS" "Logged in as $($account.user.name)"
        Write-SubCheck "Subscription: $($account.name)"
        Write-SubCheck "Tenant: $($account.tenantId.Substring(0,8))..."

        # Check subscription access
        $subscriptions = az account list --query "[].id" -o tsv 2>$null
        $subCount = ($subscriptions -split "`n" | Where-Object { $_ }).Count
        Write-Check "Subscriptions" "PASS" "$subCount accessible"
    } else {
        Write-Check "Azure Login" "WARN" "Not logged in - run 'az login'"
    }
} else {
    Write-Check "Azure Login" "SKIP" "Azure CLI not installed"
}

# =============================================================================
# Section 4: Python Dependencies
# =============================================================================
if (-not $Quick -and $PythonCmd) {
    Write-Header "Python Dependencies"

    $requiredPackages = @(
        "pandas",
        "numpy",
        "pyarrow",
        "faker",
        "tqdm",
        "pydantic",
        "azure-identity",
        "azure-storage-blob"
    )

    foreach ($package in $requiredPackages) {
        try {
            $result = & $PythonCmd -c "import $($package -replace '-','_'); print('OK')" 2>&1
            if ($result -eq "OK") {
                Write-Check $package "PASS" "Importable"
            } else {
                Write-Check $package "FAIL" "Import error"
            }
        } catch {
            Write-Check $package "FAIL" "Not installed"
        }
    }
}

# =============================================================================
# Section 5: Generator Import Test
# =============================================================================
if (-not $Quick -and $PythonCmd) {
    Write-Header "Generator Import Test"

    $generators = @(
        "SlotMachineGenerator",
        "TableGameGenerator",
        "PlayerGenerator",
        "FinancialGenerator",
        "SecurityGenerator",
        "ComplianceGenerator"
    )

    # Test imports
    Push-Location $ProjectRoot
    foreach ($gen in $generators) {
        try {
            $code = @"
import sys
sys.path.insert(0, 'data_generation')
from generators import $gen
print('OK')
"@
            $result = $code | & $PythonCmd 2>&1
            if ($result -like "*OK*") {
                Write-Check $gen "PASS" "Import successful"
            } else {
                Write-Check $gen "FAIL" "Import failed"
            }
        } catch {
            Write-Check $gen "FAIL" "Import error: $_"
        }
    }
    Pop-Location
}

# =============================================================================
# Section 6: Smoke Test
# =============================================================================
if (-not $Quick -and $PythonCmd) {
    Write-Header "Smoke Test"

    Write-Host "Running quick data generation test..." -ForegroundColor Gray

    Push-Location $ProjectRoot

    $smokeTestCode = @"
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
"@

    try {
        $result = $smokeTestCode | & $PythonCmd 2>&1
        if ($result -like "*SUCCESS*") {
            Write-Check "Data Generation" "PASS" ($result | Select-String "SUCCESS" | ForEach-Object { $_.Line })
            Write-SubCheck ($result | Select-String "Columns" | ForEach-Object { $_.Line })
            Write-SubCheck ($result | Select-String "Memory" | ForEach-Object { $_.Line })
        } else {
            Write-Check "Data Generation" "FAIL" $result
        }
    } catch {
        Write-Check "Data Generation" "FAIL" "Error: $_"
    }

    Pop-Location
}

# =============================================================================
# Summary
# =============================================================================
Write-Header "Validation Summary"

$totalChecks = $Results.Passed + $Results.Failed + $Results.Warnings

Write-Host "Total Checks: $totalChecks" -ForegroundColor White
Write-Host ""

# Status bar
$passBar = "=" * [math]::Max(1, [int]($Results.Passed / $totalChecks * 40))
$failBar = "=" * [math]::Max(0, [int]($Results.Failed / $totalChecks * 40))
$warnBar = "=" * [math]::Max(0, [int]($Results.Warnings / $totalChecks * 40))

Write-Host "  Passed:   $($Results.Passed.ToString().PadLeft(3)) " -NoNewline
Write-Host $passBar -ForegroundColor Green

Write-Host "  Failed:   $($Results.Failed.ToString().PadLeft(3)) " -NoNewline
Write-Host $failBar -ForegroundColor Red

Write-Host "  Warnings: $($Results.Warnings.ToString().PadLeft(3)) " -NoNewline
Write-Host $warnBar -ForegroundColor Yellow

Write-Host ""

# Overall status
if ($Results.Failed -eq 0) {
    if ($Results.Warnings -eq 0) {
        Write-Host "Status: " -NoNewline
        Write-Host "ALL CHECKS PASSED" -ForegroundColor Green
        Write-Host ""
        Write-Host "Your environment is ready for the Microsoft Fabric POC!" -ForegroundColor Green
    } else {
        Write-Host "Status: " -NoNewline
        Write-Host "PASSED WITH WARNINGS" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Environment is functional but review warnings above." -ForegroundColor Yellow
    }
    exit 0
} else {
    Write-Host "Status: " -NoNewline
    Write-Host "VALIDATION FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please fix the failed checks before proceeding." -ForegroundColor Red
    Write-Host "Run .\scripts\setup.ps1 to set up the environment." -ForegroundColor Yellow
    exit 1
}
