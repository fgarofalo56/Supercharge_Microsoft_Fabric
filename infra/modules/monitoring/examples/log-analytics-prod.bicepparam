// =============================================================================
// Example: Production Log Analytics Workspace
// =============================================================================
// Reference deployment for the central Fabric logging sink. Demonstrates:
//   - 90-day workspace retention (table overrides extend audit tables to 7y)
//   - 100 GB/day ingestion cap (cost control)
//   - Long-term archive to a dedicated immutable storage account
//   - Customer-managed encryption keys (CMK) bound from Key Vault
//   - Public ingestion/query disabled (private endpoints required)
//
// Usage:
//   az deployment group create \
//     --resource-group rg-fabricpoc-prod \
//     --template-file ../log-analytics-workspace.bicep \
//     --parameters log-analytics-prod.bicepparam
// =============================================================================

using '../log-analytics-workspace.bicep'

param workspaceName = 'log-fabricpoc-prod-eus2'
param location = 'eastus2'

param sku = 'PerGB2018'

// 90-day hot retention; table-level overrides extend audit/security tables
// to compliance floors below.
param retentionInDays = 90

// Cap daily ingestion at 100 GB to bound monthly cost. Alerts fire when the
// cap is reached so operations can investigate noisy sources.
param dailyQuotaGb = 100

// Per-table retention overrides for compliance:
//   - AuditLogs / SigninLogs:     2y hot,  7y archive  (HIPAA / NIGC-MICS)
//   - AzureDiagnostics:           90d hot, 1y archive  (general operations)
//   - StorageBlobLogs:            30d hot, 90d archive (high-volume signal)
param tableRetentionOverrides = [
  {
    tableName: 'AuditLogs'
    retentionInDays: 730
    totalRetentionInDays: 2555
  }
  {
    tableName: 'SigninLogs'
    retentionInDays: 730
    totalRetentionInDays: 2555
  }
  {
    tableName: 'AzureDiagnostics'
    retentionInDays: 90
    totalRetentionInDays: 365
  }
  {
    tableName: 'StorageBlobLogs'
    retentionInDays: 30
    totalRetentionInDays: 90
  }
]

// Production: ingestion + query are private only
param publicNetworkAccessForIngestion = 'Disabled'
param publicNetworkAccessForQuery = 'Disabled'

// Long-term archive (immutable WORM storage account in the platform RG)
param archiveStorageAccountId = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-fabricpoc-prod/providers/Microsoft.Storage/storageAccounts/stfabricpocprodlogs'

// Customer-managed encryption key
param cmkKeyVaultId = '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-fabricpoc-prod/providers/Microsoft.KeyVault/vaults/kv-fabricpoc-prod'
param cmkKeyName = 'log-analytics-cmk'
param cmkKeyVersion = ''

param tags = {
  Environment: 'Production'
  CostCenter: 'Casino-Analytics'
  Owner: 'fgarofalo56'
  Project: 'Fabric Casino POC'
  Workload: 'Observability'
  ComplianceFramework: 'NIGC-MICS'
}
