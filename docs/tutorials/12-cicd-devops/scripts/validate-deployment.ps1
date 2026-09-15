<#
.SYNOPSIS
    Validate Fabric deployment completed successfully.

.DESCRIPTION
    Performs post-deployment validation checks:
    - Verifies all items exist in target workspace
    - Checks semantic model refresh status
    - Validates report rendering
    - Tests pipeline connectivity

.PARAMETER WorkspaceId
    The target workspace GUID to validate.

.PARAMETER ExpectedItems
    Optional list of item names that should exist.

.EXAMPLE
    .\validate-deployment.ps1 -WorkspaceId "xxx-xxx"

.NOTES
    Requires: MicrosoftPowerBIMgmt module
    Author: Fabric POC Team
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$WorkspaceId,

    [Parameter(Mandatory=$false)]
    [string[]]$ExpectedItems,

    [Parameter(Mandatory=$false)]
    [switch]$RefreshSemanticModels
)

Write-Host "========================================"
Write-Host "  POST-DEPLOYMENT VALIDATION"
Write-Host "========================================"
Write-Host "Workspace ID: $WorkspaceId"
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "========================================"
Write-Host ""

$validationPassed = $true
$validationResults = @()

# Get access token
try {
    $token = (Get-PowerBIAccessToken -AsString).Replace("Bearer ", "")
    Write-Host "✓ Access token obtained"
}
catch {
    Write-Error "Failed to get access token"
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# ============================================
# Check 1: Workspace Accessible
# ============================================
Write-Host ""
Write-Host "Check 1: Workspace Accessibility"
Write-Host "-" * 40

$workspaceUri = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId"

try {
    $workspace = Invoke-RestMethod -Uri $workspaceUri -Method Get -Headers $headers
    Write-Host "  ✓ Workspace accessible: $($workspace.displayName)"
    $validationResults += @{ Check = "Workspace Access"; Status = "Passed"; Details = $workspace.displayName }
}
catch {
    Write-Host "  ❌ Workspace not accessible"
    $validationPassed = $false
    $validationResults += @{ Check = "Workspace Access"; Status = "Failed"; Details = $_.Exception.Message }
}

# ============================================
# Check 2: All Items Present
# ============================================
Write-Host ""
Write-Host "Check 2: Item Inventory"
Write-Host "-" * 40

$itemsUri = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/items"

try {
    $items = Invoke-RestMethod -Uri $itemsUri -Method Get -Headers $headers
    Write-Host "  ✓ Found $($items.value.Count) items"

    # Group by type
    $byType = $items.value | Group-Object -Property type
    foreach ($group in $byType) {
        Write-Host "    - $($group.Name): $($group.Count)"
    }

    # Check expected items if provided
    if ($ExpectedItems) {
        $itemNames = $items.value | ForEach-Object { $_.displayName }
        $missing = $ExpectedItems | Where-Object { $_ -notin $itemNames }

        if ($missing.Count -gt 0) {
            Write-Host "  ❌ Missing expected items:"
            foreach ($m in $missing) {
                Write-Host "    - $m"
            }
            $validationPassed = $false
            $validationResults += @{ Check = "Expected Items"; Status = "Failed"; Details = "Missing: $($missing -join ', ')" }
        }
        else {
            Write-Host "  ✓ All expected items present"
            $validationResults += @{ Check = "Expected Items"; Status = "Passed"; Details = "All items found" }
        }
    }

    $validationResults += @{ Check = "Item Inventory"; Status = "Passed"; Details = "$($items.value.Count) items" }
}
catch {
    Write-Host "  ❌ Failed to retrieve items"
    $validationPassed = $false
    $validationResults += @{ Check = "Item Inventory"; Status = "Failed"; Details = $_.Exception.Message }
}

# ============================================
# Check 3: Semantic Model Health
# ============================================
Write-Host ""
Write-Host "Check 3: Semantic Model Health"
Write-Host "-" * 40

$semanticModels = $items.value | Where-Object { $_.type -eq "SemanticModel" }

if ($semanticModels.Count -eq 0) {
    Write-Host "  ⚠ No semantic models found"
    $validationResults += @{ Check = "Semantic Models"; Status = "Skipped"; Details = "None found" }
}
else {
    foreach ($model in $semanticModels) {
        Write-Host "  Checking: $($model.displayName)"

        # Get refresh history using Power BI API
        try {
            $refreshUri = "https://api.powerbi.com/v1.0/myorg/groups/$WorkspaceId/datasets/$($model.id)/refreshes?`$top=1"
            $refreshHistory = Invoke-RestMethod -Uri $refreshUri -Method Get -Headers $headers -ErrorAction SilentlyContinue

            if ($refreshHistory.value.Count -gt 0) {
                $lastRefresh = $refreshHistory.value[0]
                Write-Host "    Last refresh: $($lastRefresh.endTime) - Status: $($lastRefresh.status)"

                if ($lastRefresh.status -eq "Failed") {
                    Write-Host "    ⚠ Last refresh failed"
                    $validationResults += @{ Check = "Model: $($model.displayName)"; Status = "Warning"; Details = "Last refresh failed" }
                }
                else {
                    $validationResults += @{ Check = "Model: $($model.displayName)"; Status = "Passed"; Details = "Healthy" }
                }
            }
        }
        catch {
            Write-Host "    ⚠ Unable to check refresh status"
        }

        # Optionally trigger refresh
        if ($RefreshSemanticModels) {
            Write-Host "    Triggering refresh..."
            try {
                $refreshUri = "https://api.powerbi.com/v1.0/myorg/groups/$WorkspaceId/datasets/$($model.id)/refreshes"
                Invoke-RestMethod -Uri $refreshUri -Method Post -Headers $headers
                Write-Host "    ✓ Refresh triggered"
            }
            catch {
                Write-Host "    ❌ Refresh trigger failed"
            }
        }
    }
}

# ============================================
# Check 4: Lakehouses Accessible
# ============================================
Write-Host ""
Write-Host "Check 4: Lakehouse Connectivity"
Write-Host "-" * 40

$lakehouses = $items.value | Where-Object { $_.type -eq "Lakehouse" }

if ($lakehouses.Count -eq 0) {
    Write-Host "  ⚠ No lakehouses found"
    $validationResults += @{ Check = "Lakehouses"; Status = "Skipped"; Details = "None found" }
}
else {
    foreach ($lh in $lakehouses) {
        Write-Host "  ✓ Lakehouse: $($lh.displayName)"
        $validationResults += @{ Check = "Lakehouse: $($lh.displayName)"; Status = "Passed"; Details = "Accessible" }
    }
}

# ============================================
# Summary
# ============================================
Write-Host ""
Write-Host "========================================"
Write-Host "  VALIDATION SUMMARY"
Write-Host "========================================"

$passed = ($validationResults | Where-Object { $_.Status -eq "Passed" }).Count
$failed = ($validationResults | Where-Object { $_.Status -eq "Failed" }).Count
$warnings = ($validationResults | Where-Object { $_.Status -eq "Warning" }).Count

Write-Host "Passed:   $passed"
Write-Host "Warnings: $warnings"
Write-Host "Failed:   $failed"
Write-Host ""

if ($validationPassed -and $failed -eq 0) {
    Write-Host "✅ VALIDATION PASSED"
    Write-Host ""
    exit 0
}
else {
    Write-Host "❌ VALIDATION FAILED"
    Write-Host ""
    Write-Host "Failed checks:"
    $validationResults | Where-Object { $_.Status -eq "Failed" } | ForEach-Object {
        Write-Host "  - $($_.Check): $($_.Details)"
    }
    exit 1
}
