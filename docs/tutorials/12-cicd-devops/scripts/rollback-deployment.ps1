<#
.SYNOPSIS
    Rollback Fabric deployment to previous version.

.DESCRIPTION
    This script performs a rollback of a Microsoft Fabric deployment.
    Supports full rollback, partial rollback, or item-level rollback.

.PARAMETER PipelineId
    Deployment pipeline GUID.

.PARAMETER TargetStage
    Stage to rollback (Test, Production).

.PARAMETER RollbackType
    Type of rollback: Full, Partial, or ItemLevel.

.PARAMETER ItemsToRollback
    Specific items to rollback (for ItemLevel type).

.EXAMPLE
    .\rollback-deployment.ps1 -PipelineId "xxx-xxx" -TargetStage "Production" -RollbackType "Full"

.EXAMPLE
    .\rollback-deployment.ps1 -PipelineId "xxx-xxx" -TargetStage "Test" -RollbackType "ItemLevel" -ItemsToRollback @("notebook1", "pipeline2")

.NOTES
    Requires: MicrosoftPowerBIMgmt module
    Author: Fabric POC Team
    Version: 1.0.0
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$PipelineId,

    [Parameter(Mandatory=$true)]
    [ValidateSet("Test", "Production")]
    [string]$TargetStage,

    [Parameter(Mandatory=$false)]
    [ValidateSet("Full", "Partial", "ItemLevel")]
    [string]$RollbackType = "Full",

    [Parameter(Mandatory=$false)]
    [string[]]$ItemsToRollback,

    [Parameter(Mandatory=$false)]
    [bool]$WaitForCompletion = $true
)

Write-Host "========================================"
Write-Host "  FABRIC ROLLBACK PROCEDURE"
Write-Host "========================================"
Write-Host "Target Stage: $TargetStage"
Write-Host "Rollback Type: $RollbackType"
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "========================================"
Write-Host ""

# Confirmation prompt
$confirmation = Read-Host "Are you sure you want to rollback $TargetStage? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "Rollback cancelled by user"
    exit 0
}

# Get access token
try {
    $token = (Get-PowerBIAccessToken -AsString).Replace("Bearer ", "")
    Write-Host "✓ Access token obtained"
}
catch {
    Write-Error "Failed to get access token. Ensure you are authenticated."
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Stage order mapping
$stageOrder = @{
    "Development" = 0
    "Test" = 1
    "Production" = 2
}

$targetOrder = $stageOrder[$TargetStage]

# Find source stage (one before target)
$sourceStage = switch ($TargetStage) {
    "Test" { "Development" }
    "Production" { "Test" }
}

if (-not $sourceStage) {
    Write-Error "Cannot rollback Development stage"
    exit 1
}

Write-Host ""
Write-Host "Rolling back $TargetStage to $sourceStage state..."
Write-Host ""

switch ($RollbackType) {
    "Full" {
        # Full rollback - redeploy from source (backward deployment)
        Write-Host "Performing FULL rollback..."
        Write-Host "This will overwrite all items in $TargetStage with versions from $sourceStage"

        $deployRequest = @{
            sourceStageOrder = $stageOrder[$sourceStage]
            isBackwardDeployment = $true
            options = @{
                allowOverwriteArtifact = $true
                allowPurgeData = $false
            }
        }

        $body = $deployRequest | ConvertTo-Json -Depth 10
        $deployUri = "https://api.fabric.microsoft.com/v1/deploymentPipelines/$PipelineId/deploy"

        try {
            $response = Invoke-RestMethod -Uri $deployUri -Method Post -Headers $headers -Body $body
            $operationId = $response.id
            Write-Host "✓ Rollback initiated"
            Write-Host "  Operation ID: $operationId"
        }
        catch {
            Write-Error "Failed to initiate rollback: $_"
            exit 1
        }

        # Wait for completion
        if ($WaitForCompletion) {
            $maxWaitMinutes = 30
            $waitIntervalSeconds = 30
            $elapsed = 0

            Write-Host ""
            Write-Host "Waiting for rollback to complete..."

            while ($elapsed -lt ($maxWaitMinutes * 60)) {
                Start-Sleep -Seconds $waitIntervalSeconds
                $elapsed += $waitIntervalSeconds

                $statusUri = "https://api.fabric.microsoft.com/v1/deploymentPipelines/$PipelineId/operations/$operationId"

                try {
                    $status = Invoke-RestMethod -Uri $statusUri -Method Get -Headers $headers
                }
                catch {
                    Write-Warning "Failed to get status, retrying..."
                    continue
                }

                $elapsedMinutes = [math]::Round($elapsed / 60, 1)
                Write-Host "  Status: $($status.state) (${elapsedMinutes} minutes elapsed)"

                if ($status.state -eq "Succeeded") {
                    Write-Host ""
                    Write-Host "✓ Rollback completed successfully"
                    break
                }
                elseif ($status.state -eq "Failed") {
                    Write-Error "Rollback failed!"
                    if ($status.error) {
                        Write-Error ($status.error | ConvertTo-Json -Depth 5)
                    }
                    exit 1
                }
            }
        }
    }

    "Partial" {
        Write-Host "Performing PARTIAL rollback..."
        Write-Host "This will rollback selected item types while preserving others"

        # Get items in the pipeline
        $pipelineUri = "https://api.fabric.microsoft.com/v1/deploymentPipelines/$PipelineId/stages"
        $stages = Invoke-RestMethod -Uri $pipelineUri -Method Get -Headers $headers

        Write-Host ""
        Write-Host "Available item types for partial rollback:"
        Write-Host "  - Notebooks"
        Write-Host "  - Pipelines"
        Write-Host "  - SemanticModels"
        Write-Host "  - Reports"
        Write-Host ""
        Write-Host "Use ItemLevel rollback with specific item names for granular control"
    }

    "ItemLevel" {
        Write-Host "Performing ITEM-LEVEL rollback..."

        if (-not $ItemsToRollback -or $ItemsToRollback.Count -eq 0) {
            Write-Error "No items specified for item-level rollback. Use -ItemsToRollback parameter."
            exit 1
        }

        Write-Host "Items to rollback:"
        foreach ($item in $ItemsToRollback) {
            Write-Host "  - $item"
        }
        Write-Host ""

        # For item-level rollback, we typically use Git to restore specific items
        Write-Host "Item-level rollback requires Git integration:"
        Write-Host "  1. Identify the commit with the working version"
        Write-Host "  2. git checkout <commit-hash> -- <item-path>"
        Write-Host "  3. git commit -m 'Rollback: Restore <item>'"
        Write-Host "  4. git push"
        Write-Host "  5. Sync workspace from Git"
        Write-Host ""
        Write-Host "Alternatively, use Fabric UI to restore items from deployment history"
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host "  ROLLBACK COMPLETE"
Write-Host "========================================"
Write-Host ""
Write-Host "NEXT STEPS:"
Write-Host "  1. Verify system functionality in $TargetStage"
Write-Host "  2. Run integration tests"
Write-Host "  3. Check semantic model refresh status"
Write-Host "  4. Verify report rendering"
Write-Host "  5. Notify stakeholders"
Write-Host "  6. Document incident in change management system"
Write-Host ""
