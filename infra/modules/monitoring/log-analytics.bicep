// =============================================================================
// Log Analytics Workspace Module
// =============================================================================
// Deploys Log Analytics for centralized monitoring
// =============================================================================

@description('Name of the Log Analytics workspace')
param name string

@description('Azure region for deployment')
param location string

@description('Retention period in days. HIPAA/NIGC MICS workloads should configure >= 2190 days (6 yrs).')
@minValue(30)
@maxValue(4383)
param retentionInDays int = 90

@description('When true, disables public network access (for FedRAMP, HIPAA, private-network deployments).')
param enablePrivateEndpoints bool = false

@description('Daily ingestion cap in GB. Set 0 for unlimited.')
@minValue(0)
param dailyQuotaGb int = 10

@description('Tags to apply to resources')
param tags object = {}

// =============================================================================
// Log Analytics Workspace
// =============================================================================

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: retentionInDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    workspaceCapping: dailyQuotaGb > 0 ? {
      dailyQuotaGb: dailyQuotaGb
    } : null
    publicNetworkAccessForIngestion: enablePrivateEndpoints ? 'Disabled' : 'Enabled'
    publicNetworkAccessForQuery: enablePrivateEndpoints ? 'Disabled' : 'Enabled'
  }
}

// =============================================================================
// Data Collection Rules
// =============================================================================

// Performance counters solution
resource performanceSolution 'Microsoft.OperationsManagement/solutions@2015-11-01-preview' = {
  name: 'VMInsights(${logAnalytics.name})'
  location: location
  tags: tags
  plan: {
    name: 'VMInsights(${logAnalytics.name})'
    publisher: 'Microsoft'
    product: 'OMSGallery/VMInsights'
    promotionCode: ''
  }
  properties: {
    workspaceResourceId: logAnalytics.id
  }
}

// =============================================================================
// Outputs (additional)
// =============================================================================
@description('Effective retention in days (echoed for reporting/assertions).')
output retentionInDays int = retentionInDays

// =============================================================================
// Saved Queries for Fabric Monitoring
// =============================================================================

resource fabricActivityQuery 'Microsoft.OperationalInsights/workspaces/savedSearches@2020-08-01' = {
  parent: logAnalytics
  name: 'FabricActivity'
  properties: {
    category: 'Fabric Monitoring'
    displayName: 'Fabric Activity Overview'
    query: '''
// Fabric activity overview
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.FABRIC"
| summarize Count = count() by OperationName, ResultType, bin(TimeGenerated, 1h)
| order by TimeGenerated desc
'''
    version: 2
  }
}

resource storageActivityQuery 'Microsoft.OperationalInsights/workspaces/savedSearches@2020-08-01' = {
  parent: logAnalytics
  name: 'StorageActivity'
  properties: {
    category: 'Fabric Monitoring'
    displayName: 'Storage Operations'
    query: '''
// Storage operations for Fabric data
StorageBlobLogs
| where OperationName in ("PutBlob", "GetBlob", "DeleteBlob")
| summarize Count = count(), TotalBytes = sum(ResponseBodySize) by OperationName, bin(TimeGenerated, 1h)
| order by TimeGenerated desc
'''
    version: 2
  }
}

resource keyVaultAccessQuery 'Microsoft.OperationalInsights/workspaces/savedSearches@2020-08-01' = {
  parent: logAnalytics
  name: 'KeyVaultAccess'
  properties: {
    category: 'Security'
    displayName: 'Key Vault Access Patterns'
    query: '''
// Key Vault access audit
AzureDiagnostics
| where ResourceProvider == "MICROSOFT.KEYVAULT"
| where OperationName has "Secret" or OperationName has "Key"
| summarize Count = count() by OperationName, CallerIPAddress, bin(TimeGenerated, 1h)
| order by TimeGenerated desc
'''
    version: 2
  }
}

// =============================================================================
// Outputs
// =============================================================================

@description('The resource ID of the Log Analytics workspace')
output workspaceId string = logAnalytics.id

@description('The name of the Log Analytics workspace')
output workspaceName string = logAnalytics.name

@description('The customer ID of the Log Analytics workspace')
output workspaceCustomerId string = logAnalytics.properties.customerId
