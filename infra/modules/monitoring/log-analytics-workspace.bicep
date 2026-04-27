// =============================================================================
// Module: log-analytics-workspace.bicep
// Description: Deploys an Azure Log Analytics Workspace as the central logging
//              sink for Microsoft Fabric platforms. Supports diagnostic-setting
//              binding (via customerId / workspaceId outputs), workspace-level
//              retention, daily ingestion cap, per-table retention overrides,
//              long-term archive to a linked Storage Account, and customer-
//              managed encryption keys (CMK).
// Owner:       fgarofalo56
// Phase:       Phase 14 Wave 1 (feature 1.13)
// Companion:   action-groups.bicep (alert routing for this workspace)
// References:  docs/best-practices/operations/observability-stack.md
//              docs/runbooks/incident-response-template.md
// =============================================================================

// ---- Parameters ----

@description('Name of the Log Analytics workspace. Must be globally unique within the resource group and 4-63 characters.')
@minLength(4)
@maxLength(63)
param workspaceName string

@description('Azure region for deployment. Defaults to the resource group location.')
param location string = resourceGroup().location

@description('Tags applied to all resources created by this module.')
param tags object = {}

@description('Workspace SKU. PerGB2018 is the standard pay-as-you-go tier; CapacityReservation provides committed-tier discounts.')
@allowed([
  'PerGB2018'
  'CapacityReservation'
  'Free'
  'Standalone'
  'PerNode'
  'Standard'
  'Premium'
])
param sku string = 'PerGB2018'

@description('Capacity reservation level in GB/day. Required only when sku=CapacityReservation.')
@allowed([
  100
  200
  300
  400
  500
  1000
  2000
  5000
])
param capacityReservationLevel int = 100

@description('Workspace-level retention in days. Compliance floors: FedRAMP=1095, HIPAA/NIGC-MICS=2190.')
@minValue(30)
@maxValue(730)
param retentionInDays int = 90

@description('Daily ingestion cap in GB. Use -1 for unlimited (no cap). Recommended: cap non-prod environments to control cost.')
@minValue(-1)
param dailyQuotaGb int = -1

@description('Per-table retention overrides. Each item: { tableName, retentionInDays, totalRetentionInDays }. totalRetentionInDays >= retentionInDays and supports up to 4383 days for archive tier.')
param tableRetentionOverrides array = []

@description('Public network access for ingestion endpoint. Set Disabled when private endpoints are used.')
@allowed([
  'Enabled'
  'Disabled'
])
param publicNetworkAccessForIngestion string = 'Enabled'

@description('Public network access for query endpoint. Set Disabled when private endpoints are used.')
@allowed([
  'Enabled'
  'Disabled'
])
param publicNetworkAccessForQuery string = 'Enabled'

@description('Optional Storage Account resource ID for long-term log archival. When supplied, a linkedStorageAccount of type CustomLogs is created.')
param archiveStorageAccountId string = ''

@description('Optional Key Vault resource ID for customer-managed encryption keys (CMK). All three CMK params must be supplied together.')
param cmkKeyVaultId string = ''

@description('Optional Key Vault key name for CMK. Required when cmkKeyVaultId is provided.')
param cmkKeyName string = ''

@description('Optional Key Vault key version for CMK. Use empty string to bind to the latest version.')
param cmkKeyVersion string = ''

// ---- Variables ----

var enableArchive = !empty(archiveStorageAccountId)
var enableCmk = !empty(cmkKeyVaultId) && !empty(cmkKeyName)

var cmkKeyVaultName = enableCmk ? last(split(cmkKeyVaultId, '/')) : ''
var cmkKeyVaultUri = enableCmk ? 'https://${cmkKeyVaultName}.vault.azure.net' : ''

// =============================================================================
// Resources
// =============================================================================

@description('Central Log Analytics workspace for Fabric diagnostic settings, alerts, and runbook KQL.')
resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: workspaceName
  location: location
  tags: tags
  properties: {
    sku: sku == 'CapacityReservation' ? {
      name: sku
      capacityReservationLevel: capacityReservationLevel
    } : {
      name: sku
    }
    retentionInDays: retentionInDays
    workspaceCapping: dailyQuotaGb >= 0 ? {
      dailyQuotaGb: dailyQuotaGb
    } : null
    publicNetworkAccessForIngestion: publicNetworkAccessForIngestion
    publicNetworkAccessForQuery: publicNetworkAccessForQuery
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
      disableLocalAuth: false
    }
  }
}

// ---- Per-table retention overrides -----------------------------------------
// Loop over the supplied array to apply table-level retention. totalRetentionInDays
// extends data into the archive tier (cheaper, slower) beyond the hot retention.
@description('Per-table retention/archive overrides for tables that need different policies than the workspace default (e.g., AuditLogs, SigninLogs, AzureDiagnostics).')
resource tableOverrides 'Microsoft.OperationalInsights/workspaces/tables@2022-10-01' = [for table in tableRetentionOverrides: {
  parent: workspace
  name: table.tableName
  properties: {
    retentionInDays: table.retentionInDays
    totalRetentionInDays: table.totalRetentionInDays
  }
}]

// ---- Long-term archive storage linkage -------------------------------------
// linkedStorageAccount of type CustomLogs allows the workspace to spill aged
// logs into low-cost blob storage for compliance retention windows.
@description('Linked Storage Account for long-term log archival (NIGC-MICS / HIPAA / FedRAMP retention floors).')
resource archiveLink 'Microsoft.OperationalInsights/workspaces/linkedStorageAccounts@2020-08-01' = if (enableArchive) {
  parent: workspace
  name: 'CustomLogs'
  properties: {
    storageAccountIds: [
      archiveStorageAccountId
    ]
  }
}

// ---- Customer-managed encryption keys --------------------------------------
// Workspace CMK is configured via the cluster resource for dedicated clusters,
// but for non-cluster workspaces CMK is set on the workspace itself via the
// linkedServices resource type. We model the most common case: per-workspace
// CMK for a Premium tier workspace.
@description('Customer-managed key binding for the workspace. Requires the workspace identity to have Key Vault Crypto User on the supplied vault.')
resource cmkBinding 'Microsoft.OperationalInsights/workspaces/linkedServices@2020-08-01' = if (enableCmk) {
  parent: workspace
  name: 'Cluster'
  properties: {
    resourceId: cmkKeyVaultId
    writeAccessResourceId: empty(cmkKeyVersion) ? '${cmkKeyVaultUri}/keys/${cmkKeyName}' : '${cmkKeyVaultUri}/keys/${cmkKeyName}/${cmkKeyVersion}'
  }
}

// =============================================================================
// Outputs
// =============================================================================

@description('Resource ID of the Log Analytics workspace. Bind to diagnosticSettings.workspaceId.')
output workspaceId string = workspace.id

@description('Name of the Log Analytics workspace.')
output workspaceName string = workspace.name

@description('Customer ID (workspace GUID) used by agents and diagnostic-setting bindings.')
output customerId string = workspace.properties.customerId

@description('Effective workspace retention in days (echoed for assertions).')
output effectiveRetentionInDays int = workspace.properties.retentionInDays

@description('Number of per-table retention overrides applied.')
output tableOverrideCount int = length(tableRetentionOverrides)

@description('True when long-term archive storage is linked.')
output archiveEnabled bool = enableArchive

@description('True when customer-managed key encryption is bound.')
output cmkEnabled bool = enableCmk

// SECURITY NOTE: primarySharedKey is intentionally NOT output. Consumers should
// authenticate to Log Analytics using Azure RBAC (Monitoring Reader / Log
// Analytics Reader) rather than the workspace shared key. If a shared key is
// required (legacy MMA agents), retrieve it on demand via:
//   az monitor log-analytics workspace get-shared-keys -g <rg> -n <workspaceName>
