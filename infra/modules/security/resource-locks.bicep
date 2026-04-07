// =============================================================================
// Resource Locks Module
// =============================================================================
// Deploys CanNotDelete locks on critical infrastructure resources.
// This module runs at resource-group scope so that locks are correctly scoped.
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
// Resource Locks
// =============================================================================

resource keyVaultLock 'Microsoft.Authorization/locks@2020-05-01' = {
  name: 'lock-${keyVaultName}'
  properties: {
    level: 'CanNotDelete'
    notes: 'Critical resource: Key Vault contains secrets for Fabric POC. Protected from accidental deletion.'
  }
}

resource storageLock 'Microsoft.Authorization/locks@2020-05-01' = {
  name: 'lock-${storageAccountName}'
  properties: {
    level: 'CanNotDelete'
    notes: 'Critical resource: ADLS Gen2 storage for Fabric Lakehouse data. Protected from accidental deletion.'
  }
}

resource fabricLock 'Microsoft.Authorization/locks@2020-05-01' = {
  name: 'lock-${fabricCapacityName}'
  properties: {
    level: 'CanNotDelete'
    notes: 'Critical resource: Fabric F64 capacity. Protected from accidental deletion.'
  }
}

resource logAnalyticsLock 'Microsoft.Authorization/locks@2020-05-01' = {
  name: 'lock-${logAnalyticsName}'
  properties: {
    level: 'CanNotDelete'
    notes: 'Critical resource: Log Analytics workspace for monitoring. Protected from accidental deletion.'
  }
}

resource purviewLock 'Microsoft.Authorization/locks@2020-05-01' = {
  name: 'lock-${purviewAccountName}'
  properties: {
    level: 'CanNotDelete'
    notes: 'Critical resource: Purview governance account. Protected from accidental deletion.'
  }
}
