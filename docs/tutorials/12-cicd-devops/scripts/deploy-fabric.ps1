<#
.SYNOPSIS
    Triggers a Fabric Deployment Pipeline deployment.

.DESCRIPTION
    This script triggers a deployment between stages in a Microsoft Fabric Deployment Pipeline.
    It uses the Fabric REST API to initiate the deployment and optionally wait for completion.

.PARAMETER PipelineId
    The deployment pipeline GUID.

.PARAMETER SourceStage
    Source stage name (Development, Test).

.PARAMETER TargetStage
    Target stage name (Test, Production).

.PARAMETER WaitForCompletion
    Wait for deployment to complete. Default: $true

.PARAMETER MaxWaitMinutes
    Maximum time to wait for completion. Default: 30

.EXAMPLE
    .\deploy-fabric.ps1 -PipelineId "xxx-xxx" -SourceStage "Development" -TargetStage "Test"

.EXAMPLE
    .\deploy-fabric.ps1 -PipelineId "xxx-xxx" -SourceStage "Test" -TargetStage "Production" -WaitForCompletion $true

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
    [ValidateSet("Development", "Test")]
    [string]$SourceStage,

    [Parameter(Mandatory=$true)]
    [ValidateSet("Test", "Production")]
    [string]$TargetStage,

    [Parameter(Mandatory=$false)]
    [bool]$WaitForCompletion = $true,

    [Parameter(Mandatory=$false)]
    [int]$MaxWaitMinutes = 30
)

# Stage order mapping
$stageOrder = @{
    "Development" = 0
    "Test" = 1
    "Production" = 2
}

$sourceStageOrder = $stageOrder[$SourceStage]
$targetStageOrder = $stageOrder[$TargetStage]

Write-Host "================================================"
Write-Host "  FABRIC DEPLOYMENT PIPELINE"
Write-Host "================================================"
Write-Host "Pipeline ID: $PipelineId"
Write-Host "Source Stage: $SourceStage (Order: $sourceStageOrder)"
Write-Host "Target Stage: $TargetStage (Order: $targetStageOrder)"
Write-Host "Wait for Completion: $WaitForCompletion"
Write-Host "================================================"
Write-Host ""

# Validate stage order
if ($sourceStageOrder -ge $targetStageOrder) {
    Write-Error "Source stage must be before target stage"
    exit 1
}

# Get access token
try {
    $token = (Get-PowerBIAccessToken -AsString).Replace("Bearer ", "")
    Write-Host "✓ Access token obtained"
}
catch {
    Write-Error "Failed to get access token. Ensure you are authenticated with Connect-PowerBIServiceAccount"
    exit 1
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Build deployment request
$deployRequest = @{
    sourceStageOrder = $sourceStageOrder
    isBackwardDeployment = $false
    newWorkspace = $null
    options = @{
        allowCreateArtifact = $true
        allowOverwriteArtifact = $true
        allowOverwriteTargetArtifactLabel = $true
        allowPurgeData = $false
        allowSkipTilesWithMissingPrerequisites = $true
        allowTakeOver = $true
    }
}

$body = $deployRequest | ConvertTo-Json -Depth 10

# Trigger deployment
$deployUri = "https://api.fabric.microsoft.com/v1/deploymentPipelines/$PipelineId/deploy"

Write-Host "Triggering deployment..."

try {
    $response = Invoke-RestMethod -Uri $deployUri -Method Post -Headers $headers -Body $body
    $operationId = $response.id
    Write-Host "✓ Deployment triggered successfully"
    Write-Host "  Operation ID: $operationId"
}
catch {
    Write-Error "Failed to trigger deployment: $_"
    Write-Error "Response: $($_.ErrorDetails.Message)"
    exit 1
}

# Wait for completion if requested
if ($WaitForCompletion) {
    $waitIntervalSeconds = 30
    $elapsed = 0
    $maxWaitSeconds = $MaxWaitMinutes * 60

    Write-Host ""
    Write-Host "Waiting for deployment to complete..."

    while ($elapsed -lt $maxWaitSeconds) {
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
            Write-Host "================================================"
            Write-Host "  DEPLOYMENT COMPLETED SUCCESSFULLY"
            Write-Host "================================================"
            Write-Host "Duration: $elapsedMinutes minutes"
            exit 0
        }
        elseif ($status.state -eq "Failed") {
            Write-Host ""
            Write-Error "================================================"
            Write-Error "  DEPLOYMENT FAILED"
            Write-Error "================================================"
            if ($status.error) {
                Write-Error "Error Details:"
                Write-Error ($status.error | ConvertTo-Json -Depth 5)
            }
            exit 1
        }
    }

    Write-Error "Deployment timed out after $MaxWaitMinutes minutes"
    exit 1
}

Write-Host ""
Write-Host "Deployment triggered successfully (not waiting for completion)"
exit 0
