# Phase 7 Autonomous Agent Harness - Initialization Script
# Supercharge Microsoft Fabric - Federal Agencies, Migration, RTI, Video Analytics & GeoAnalytics
# Run this script to initialize or resume a Phase 7 autonomous coding session

param(
    [switch]$Resume,
    [switch]$Status,
    [switch]$Reset,
    [int]$Wave = 0
)

$ErrorActionPreference = "Stop"
$HarnessDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Get-Item $HarnessDir).Parent.Parent.FullName

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Phase 7 Autonomous Agent Harness" -ForegroundColor Cyan
Write-Host "Federal Agencies | Migration | RTI | Analytics" -ForegroundColor DarkCyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$ArchonProjectId = "c0f96f03-5095-4704-a167-9a3f5a3e3ed1"
$FeaturesFile = Join-Path $HarnessDir "phase7_features.json"
$ProgressFile = Join-Path $HarnessDir "phase7_progress.txt"
$PromptsDir = Join-Path $HarnessDir "prompts"
$PrpFile = Join-Path (Join-Path $HarnessDir "..") "phase7-prp.md"

function Get-CurrentStatus {
    Write-Host "Phase 7 Harness Status:" -ForegroundColor Yellow
    Write-Host ""

    if (Test-Path $FeaturesFile) {
        $features = Get-Content $FeaturesFile -Raw | ConvertFrom-Json
        Write-Host "  Total Features: $($features.total_features)" -ForegroundColor White
        Write-Host "  Completed:      $($features.completed)" -ForegroundColor Green
        Write-Host "  Passing:        $($features.passing)" -ForegroundColor Green
        Write-Host "  Failing:        $($features.failing)" -ForegroundColor Red
        Write-Host "  Pending:        $($features.pending)" -ForegroundColor Yellow
        Write-Host ""

        # Wave summary
        Write-Host "  Wave Progress:" -ForegroundColor White
        $waveData = @{
            1 = @{ name = "Federal Foundation"; total = 26; completed = 0 }
            2 = @{ name = "Migration & Streaming"; total = 19; completed = 0 }
            3 = @{ name = "Analytics & Visualization"; total = 12; completed = 0 }
            4 = @{ name = "Complete Expansions"; total = 15; completed = 0 }
            5 = @{ name = "Final Regression"; total = 1; completed = 0 }
        }

        foreach ($cat in $features.categories.PSObject.Properties) {
            $waveNum = $cat.Value.wave
            if ($waveData.ContainsKey($waveNum)) {
                $waveData[$waveNum].completed += $cat.Value.completed
            }
        }

        foreach ($w in 1..5) {
            $wd = $waveData[$w]
            $pct = if ($wd.total -gt 0) { [math]::Round(($wd.completed / $wd.total) * 100) } else { 0 }
            $bar = ("=" * [math]::Floor($pct / 5)) + (" " * (20 - [math]::Floor($pct / 5)))
            $color = if ($pct -eq 100) { "Green" } elseif ($pct -gt 0) { "Yellow" } else { "White" }
            Write-Host "    Wave $w [$bar] $pct% - $($wd.name) ($($wd.completed)/$($wd.total))" -ForegroundColor $color
        }

        Write-Host ""

        # Category breakdown
        Write-Host "  Categories:" -ForegroundColor White
        foreach ($cat in $features.categories.PSObject.Properties) {
            $name = $cat.Name
            $total = $cat.Value.total
            $completed = $cat.Value.completed
            $wave = $cat.Value.wave
            $status = if ($completed -eq $total) { "[DONE]" } else { "[$completed/$total]" }
            $color = if ($completed -eq $total) { "Green" } elseif ($completed -gt 0) { "Yellow" } else { "White" }
            Write-Host "    W$wave $($name): $status" -ForegroundColor $color
        }
    } else {
        Write-Host "  Features file not found!" -ForegroundColor Red
    }

    Write-Host ""

    # Check git status
    Write-Host "Git Status:" -ForegroundColor Yellow
    Push-Location $ProjectRoot
    $gitStatus = git status --porcelain 2>$null
    if ($gitStatus) {
        $changedCount = ($gitStatus | Measure-Object).Count
        Write-Host "  $changedCount files with changes" -ForegroundColor Yellow
        $gitStatus | Select-Object -First 10 | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        if ($changedCount -gt 10) {
            Write-Host "    ... and $($changedCount - 10) more" -ForegroundColor Gray
        }
    } else {
        Write-Host "  Working tree clean" -ForegroundColor Green
    }
    Pop-Location
}

function Initialize-Session {
    param([int]$StartWave = 1)

    Write-Host "Initializing Phase 7 coding session (Wave $StartWave)..." -ForegroundColor Yellow
    Write-Host ""

    # Verify prompts exist
    $requiredFiles = @(
        (Join-Path $PromptsDir "phase7_initializer_prompt.md"),
        (Join-Path $PromptsDir "phase7_coding_prompt.md"),
        $FeaturesFile,
        $PrpFile
    )

    foreach ($f in $requiredFiles) {
        if (-not (Test-Path $f)) {
            Write-Host "ERROR: Required file not found: $f" -ForegroundColor Red
            exit 1
        }
    }

    # Add session entry to progress file
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $sessionEntry = @"

================================================================================
## Session: $(Get-Date -Format "yyyy-MM-dd") (Phase 7 Coding - Wave $StartWave)
================================================================================

### Start Time: $timestamp
### Archon Project: $ArchonProjectId
### Starting Wave: $StartWave
### Status: STARTING

### Instructions:
1. Open Claude Code in this repository
2. Read: .claude/harness/prompts/phase7_initializer_prompt.md
3. Read: .claude/phase7-prp.md
4. Read: .claude/harness/phase7_features.json
5. Start with Wave $StartWave, first pending feature
6. Follow coding_prompt.md for implementation workflow

"@

    Add-Content -Path $ProgressFile -Value $sessionEntry

    Write-Host "Session initialized!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Open Claude Code in this repository"
    Write-Host "  2. Read the initializer prompt:"
    Write-Host "     Read: .claude/harness/prompts/phase7_initializer_prompt.md"
    Write-Host "  3. Read the PRP:"
    Write-Host "     Read: .claude/phase7-prp.md"
    Write-Host "  4. Start Wave $StartWave coding"
    Write-Host ""
}

function Reset-Harness {
    Write-Host "Resetting Phase 7 harness to initial state..." -ForegroundColor Yellow

    # Reload original features.json
    if (Test-Path $FeaturesFile) {
        $features = Get-Content $FeaturesFile -Raw | ConvertFrom-Json
        $features.completed = 0
        $features.passing = 0
        $features.failing = 0
        $features.pending = $features.total_features

        foreach ($cat in $features.categories.PSObject.Properties) {
            $cat.Value.completed = 0
            foreach ($item in $cat.Value.items) {
                $item.status = "pending"
            }
        }

        $features | ConvertTo-Json -Depth 10 | Set-Content $FeaturesFile
        Write-Host "Features registry reset." -ForegroundColor Green
    }

    Write-Host "Harness reset complete." -ForegroundColor Green
}

# Main execution
if ($Status) {
    Get-CurrentStatus
} elseif ($Reset) {
    Reset-Harness
} elseif ($Resume) {
    Write-Host "Resuming previous Phase 7 session..." -ForegroundColor Yellow
    Get-CurrentStatus
    Write-Host ""
    Write-Host "To continue, open Claude Code and read:" -ForegroundColor Cyan
    Write-Host "  .claude/harness/prompts/phase7_initializer_prompt.md"
    Write-Host "  .claude/harness/phase7_features.json"
} else {
    Get-CurrentStatus
    Write-Host ""
    $startWave = if ($Wave -gt 0) { $Wave } else { 1 }
    Initialize-Session -StartWave $startWave
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
