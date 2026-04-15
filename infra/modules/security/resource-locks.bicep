// =============================================================================
// Resource Locks Module
// =============================================================================
// Deploys CanNotDelete locks on critical infrastructure resources.
// Each lock is scoped to the named resource via `scope:` on an existing ref
// so the lock applies to the resource, not the enclosing resource group.
// =============================================================================

@description('Name of the Key Vault resource to lock')
param keyVaultName string

@description('Name of the Storage Account resource to lock')
param storageAccountName string

@description('Name of the Fabric Capacity resource to lock')
param fabricCapacityName string

@description('Name of the Log Analytics Workspace resource to lock')
param logAnalyticsName string

@description('Name of the Purview Account resource to lock')
param purviewAccountName string

// =============================================================================
// Existing resource references (lock targets)
// =============================================================================

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultName
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource fabricCapacity 'Microsoft.Fabric/capacities@2023-11-01' existing = {
  name: fabricCapacityName
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: logAnalyticsName
}

resource purviewAccount 'Microsoft.Purview/accounts@2023-05-01-preview' existing = {
  name: purviewAccountName
}

// =============================================================================
// Resource Locks (scoped to each resource)
// =============================================================================

resource keyVaultLock 'Microsoft.Authorization/locks@2020-05-01' = {
  scope: keyVault
  name: 'lock-${keyVaultName}'
  properties: {
    level: 'CanNotDelete'
    notes: 'Key Vault holds workload secrets. Protected from accidental deletion.'
  }
}

resource storageLock 'Microsoft.Authorization/locks@2020-05-01' = {
  scope: storageAccount
  name: 'lock-${storageAccountName}'
  properties: {
    level: 'CanNotDelete'
    notes: 'ADLS Gen2 storage for Fabric Lakehouse data. Protected from accidental deletion.'
  }
}

resource fabricLock 'Microsoft.Authorization/locks@2020-05-01' = {
  scope: fabricCapacity
  name: 'lock-${fabricCapacityName}'
  properties: {
    level: 'CanNotDelete'
    notes: 'Fabric capacity. Protected from accidental deletion.'
  }
}

resource logAnalyticsLock 'Microsoft.Authorization/locks@2020-05-01' = {
  scope: logAnalytics
  name: 'lock-${logAnalyticsName}'
  properties: {
    level: 'CanNotDelete'
    notes: 'Log Analytics workspace for diagnostics/audit. Protected from accidental deletion.'
  }
}

resource purviewLock 'Microsoft.Authorization/locks@2020-05-01' = {
  scope: purviewAccount
  name: 'lock-${purviewAccountName}'
  properties: {
    level: 'CanNotDelete'
    notes: 'Purview governance account. Protected from accidental deletion.'
  }
}
