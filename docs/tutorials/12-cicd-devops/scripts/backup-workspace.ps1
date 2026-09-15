<#
.SYNOPSIS
    Backup Fabric workspace items before deployment.

.DESCRIPTION
    Creates a backup of workspace items by exporting definitions to JSON.
    Useful for pre-deployment snapshots and disaster recovery.

.PARAMETER WorkspaceId
    The Fabric workspace GUID to backup.

.PARAMETER OutputPath
    Path to save backup files. Default: ./backups

.PARAMETER IncludeItems
    Item types to include in backup.

.EXAMPLE
    .\backup-workspace.ps1 -WorkspaceId "xxx-xxx"

.EXAMPLE
    .\backup-workspace.ps1 -WorkspaceId "xxx-xxx" -OutputPath "C:\backups"

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
    [string]$OutputPath = "./backups",

    [Parameter(Mandatory=$false)]
    [string[]]$IncludeItems = @("Notebook", "DataPipeline", "SemanticModel", "Report", "Lakehouse")
)

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupFolder = Join-Path $OutputPath "backup-$timestamp"

Write-Host "========================================"
Write-Host "  FABRIC WORKSPACE BACKUP"
Write-Host "========================================"
Write-Host "Workspace ID: $WorkspaceId"
Write-Host "Backup Path: $backupFolder"
Write-Host "Timestamp: $timestamp"
Write-Host "========================================"
Write-Host ""

# Create backup directory
New-Item -ItemType Directory -Path $backupFolder -Force | Out-Null
Write-Host "✓ Created backup directory"

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

# Get workspace items
Write-Host ""
Write-Host "Fetching workspace items..."

$itemsUri = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/items"

try {
    $items = Invoke-RestMethod -Uri $itemsUri -Method Get -Headers $headers
    Write-Host "✓ Found $($items.value.Count) items in workspace"
}
catch {
    Write-Error "Failed to get workspace items: $_"
    exit 1
}

# Backup each item
$backedUp = 0
$skipped = 0

Write-Host ""
Write-Host "Backing up items..."

foreach ($item in $items.value) {
    $itemType = $item.type
    $itemName = $item.displayName
    $itemId = $item.id

    # Check if item type should be included
    if ($IncludeItems -notcontains $itemType) {
        $skipped++
        continue
    }

    Write-Host "  Processing: $itemName ($itemType)"

    # Create item type subfolder
    $typeFolder = Join-Path $backupFolder $itemType
    if (-not (Test-Path $typeFolder)) {
        New-Item -ItemType Directory -Path $typeFolder -Force | Out-Null
    }

    # Get item definition
    $definitionUri = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/items/$itemId/getDefinition"

    try {
        # Note: Not all items support getDefinition
        $definition = Invoke-RestMethod -Uri $definitionUri -Method Post -Headers $headers -ErrorAction SilentlyContinue

        if ($definition) {
            $itemFileName = "$itemName.json"
            $itemFilePath = Join-Path $typeFolder $itemFileName

            $definition | ConvertTo-Json -Depth 20 | Out-File -FilePath $itemFilePath -Encoding UTF8
            Write-Host "    ✓ Backed up definition"
            $backedUp++
        }
    }
    catch {
        # Fallback: save item metadata only
        $metadataPath = Join-Path $typeFolder "$itemName.metadata.json"
        $item | ConvertTo-Json -Depth 10 | Out-File -FilePath $metadataPath -Encoding UTF8
        Write-Host "    ⚠ Saved metadata only (definition not available)"
        $backedUp++
    }
}

# Create backup manifest
$manifest = @{
    timestamp = $timestamp
    workspaceId = $WorkspaceId
    totalItems = $items.value.Count
    backedUp = $backedUp
    skipped = $skipped
    includedTypes = $IncludeItems
}

$manifestPath = Join-Path $backupFolder "manifest.json"
$manifest | ConvertTo-Json | Out-File -FilePath $manifestPath -Encoding UTF8

Write-Host ""
Write-Host "========================================"
Write-Host "  BACKUP COMPLETE"
Write-Host "========================================"
Write-Host "Items backed up: $backedUp"
Write-Host "Items skipped: $skipped"
Write-Host "Backup location: $backupFolder"
Write-Host "========================================"
