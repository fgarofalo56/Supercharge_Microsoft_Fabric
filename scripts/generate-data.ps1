#Requires -Version 5.1
<#
.SYNOPSIS
    Generate synthetic casino/gaming data for Microsoft Fabric POC.

.DESCRIPTION
    This script generates synthetic data across all casino domains:
    - Slot machine telemetry
    - Table game events
    - Player profiles
    - Financial transactions
    - Security events
    - Compliance filings

.PARAMETER Days
    Number of days of historical data to generate (default: 30)

.PARAMETER SlotCount
    Number of slot machine events to generate (default: 500000)

.PARAMETER PlayerCount
    Number of player profiles to generate (default: 10000)

.PARAMETER OutputDir
    Output directory for generated data (default: ./data/generated)

.PARAMETER Format
    Output format: parquet, json, csv (default: parquet)

.PARAMETER Quick
    Quick demo mode with smaller data volumes

.PARAMETER All
    Generate all data types

.PARAMETER Slots
    Generate only slot machine data

.PARAMETER Tables
    Generate only table game data

.PARAMETER Players
    Generate only player profile data

.PARAMETER Financial
    Generate only financial transaction data

.PARAMETER Security
    Generate only security event data

.PARAMETER Compliance
    Generate only compliance filing data

.EXAMPLE
    .\generate-data.ps1 --quick
    .\generate-data.ps1 --all --days 30
    .\generate-data.ps1 --slots 100000 --players 5000

.NOTES
    Author: Microsoft Fabric POC Team
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [int]$Days = 30,
    [int]$SlotCount = 500000,
    [int]$TableCount = 100000,
    [int]$PlayerCount = 10000,
    [int]$FinancialCount = 50000,
    [int]$SecurityCount = 25000,
    [int]$ComplianceCount = 10000,
    [string]$OutputDir = "./data/generated",
    [string]$Format = "parquet",
    [int]$Seed = 42,
    [switch]$Quick,
    [switch]$All,
    [switch]$Slots,
    [switch]$Tables,
    [switch]$Players,
    [switch]$Financial,
    [switch]$Security,
    [switch]$Compliance,
    [switch]$IncludePII
)

# =============================================================================
# Configuration
# =============================================================================
$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot
$DataGenPath = Join-Path $ProjectRoot "data_generation"

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

function Write-Progress-Bar {
    param(
        [string]$Activity,
        [int]$PercentComplete
    )
    $barWidth = 40
    $completed = [math]::Floor($barWidth * $PercentComplete / 100)
    $remaining = $barWidth - $completed
    $bar = "[" + ("=" * $completed) + ("." * $remaining) + "]"
    Write-Host "`r$Activity $bar $PercentComplete%" -NoNewline -ForegroundColor Cyan
}

function Format-FileSize {
    param([long]$Size)
    if ($Size -gt 1GB) { return "{0:N2} GB" -f ($Size / 1GB) }
    if ($Size -gt 1MB) { return "{0:N2} MB" -f ($Size / 1MB) }
    if ($Size -gt 1KB) { return "{0:N2} KB" -f ($Size / 1KB) }
    return "$Size bytes"
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
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return "python"
    }
    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        return "python3"
    }

    return $null
}

# =============================================================================
# Main Script
# =============================================================================

Write-Header "Microsoft Fabric Casino/Gaming POC - Data Generation"

# Check if Quick mode
if ($Quick) {
    Write-Info "Quick demo mode enabled - using smaller data volumes"
    $Days = 7
    $SlotCount = 10000
    $TableCount = 5000
    $PlayerCount = 1000
    $FinancialCount = 2000
    $SecurityCount = 500
    $ComplianceCount = 200
    $All = $true
}

# Default to All if no specific type selected
if (-not ($All -or $Slots -or $Tables -or $Players -or $Financial -or $Security -or $Compliance)) {
    Write-Info "No data type specified, defaulting to --All"
    $All = $true
}

# Display configuration
Write-Step "Configuration:"
Write-Info "Days:        $Days"
Write-Info "Output:      $OutputDir"
Write-Info "Format:      $Format"
Write-Info "Seed:        $Seed"
if ($Quick) {
    Write-Info "Mode:        Quick Demo"
}
Write-Host ""

# Find Python
$PythonCmd = Get-VenvPython
if (-not $PythonCmd) {
    Write-Failure "Python not found. Run setup.ps1 first."
    exit 1
}
Write-Info "Using Python: $PythonCmd"

# Verify data_generation module
if (-not (Test-Path (Join-Path $DataGenPath "generate.py"))) {
    Write-Failure "data_generation/generate.py not found"
    exit 1
}

# Build command arguments
$Args = @(
    (Join-Path $DataGenPath "generate.py"),
    "--output", $OutputDir,
    "--format", $Format,
    "--days", $Days,
    "--seed", $Seed
)

if ($All) {
    $Args += "--all"
} else {
    if ($Slots) { $Args += @("--slots", $SlotCount) }
    if ($Tables) { $Args += @("--tables", $TableCount) }
    if ($Players) { $Args += @("--players", $PlayerCount) }
    if ($Financial) { $Args += @("--financial", $FinancialCount) }
    if ($Security) { $Args += @("--security", $SecurityCount) }
    if ($Compliance) { $Args += @("--compliance", $ComplianceCount) }
}

if ($IncludePII) {
    $Args += "--include-pii"
    Write-Info "Warning: Including unhashed PII (for testing only)"
}

# Show what will be generated
Write-Header "Data Generation Plan"
if ($All -or $Slots) { Write-Info "Slot Machine Events: $('{0:N0}' -f $SlotCount)" }
if ($All -or $Tables) { Write-Info "Table Game Events:   $('{0:N0}' -f $TableCount)" }
if ($All -or $Players) { Write-Info "Player Profiles:     $('{0:N0}' -f $PlayerCount)" }
if ($All -or $Financial) { Write-Info "Financial Txns:      $('{0:N0}' -f $FinancialCount)" }
if ($All -or $Security) { Write-Info "Security Events:     $('{0:N0}' -f $SecurityCount)" }
if ($All -or $Compliance) { Write-Info "Compliance Filings:  $('{0:N0}' -f $ComplianceCount)" }

# Create output directory
if (-not (Test-Path $OutputDir)) {
    Write-Step "Creating output directory: $OutputDir"
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

# Run generation
Write-Header "Generating Data"

$startTime = Get-Date

try {
    # Change to project root for proper imports
    Push-Location $ProjectRoot

    Write-Step "Starting data generation..."
    Write-Host ""

    # Run the Python generator
    & $PythonCmd $Args

    if ($LASTEXITCODE -ne 0) {
        Write-Failure "Data generation failed with exit code $LASTEXITCODE"
        Pop-Location
        exit 1
    }

    Pop-Location
} catch {
    Write-Failure "Error during data generation: $_"
    Pop-Location
    exit 1
}

$endTime = Get-Date
$duration = $endTime - $startTime

# =============================================================================
# Summary
# =============================================================================
Write-Header "Generation Complete!"

# List generated files
Write-Step "Generated Files:"
$files = Get-ChildItem -Path $OutputDir -File -ErrorAction SilentlyContinue
$totalSize = 0

foreach ($file in $files) {
    $size = Format-FileSize $file.Length
    $totalSize += $file.Length
    Write-Info "$($file.Name.PadRight(35)) $size"
}

Write-Host ""
Write-Info "Total Size: $(Format-FileSize $totalSize)"
Write-Info "Duration:   $($duration.ToString('mm\:ss'))"
Write-Info "Location:   $(Resolve-Path $OutputDir)"

Write-Host ""
Write-Success "Data generation completed successfully!"
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Review generated data in $OutputDir"
Write-Host "  2. Upload to Azure Storage: " -NoNewline
Write-Host "az storage blob upload-batch ..." -ForegroundColor Cyan
Write-Host "  3. Or use in Microsoft Fabric notebooks"
Write-Host ""
