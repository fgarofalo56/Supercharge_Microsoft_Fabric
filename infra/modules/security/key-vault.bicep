// =============================================================================
// Module: key-vault.bicep
// Description: Azure Key Vault with RBAC-only authorization (no access policies).
//              Used by tutorial 57 to store the Databricks PAT, service
//              principal client secret, and connection strings consumed by
//              the security automation notebooks.
//              RBAC-only is the 2026 best practice — access policies are
//              deprecated for new vaults.
// =============================================================================

// ---- Parameters ----

@description('Azure region for the Key Vault')
param location string

@description('Project prefix used for naming (3-10 chars)')
@minLength(3)
@maxLength(10)
param projectPrefix string

@description('Deployment environment')
@allowed([
  'dev'
  'staging'
  'prod'
])
param environment string

@description('Tags to apply')
param tags object = {}

@description('Tenant ID — defaults to the subscription tenant.')
param tenantId string = subscription().tenantId

@description('Enable purge protection (cannot be disabled once enabled).')
param enablePurgeProtection bool = true

@description('Soft-delete retention in days (7-90).')
@minValue(7)
@maxValue(90)
param softDeleteRetentionDays int = 90

@description('Disable public network access (requires private endpoint).')
param disablePublicAccess bool = false

@description('Optional Log Analytics workspace ID for diagnostics. Empty string skips diag setup.')
param logAnalyticsWorkspaceId string = ''

// ---- Variables ----

// Key Vault names: 3-24 chars, alphanumeric + hyphen, globally unique
// We append a 4-char hash of the resource group + subscription so re-deploys
// in different RGs of the same sub don't collide.
var nameSuffix = substring(uniqueString(resourceGroup().id, subscription().subscriptionId), 0, 4)
var keyVaultName = 'kv-${projectPrefix}-${environment}-${nameSuffix}'

// =============================================================================
// Resources
// =============================================================================

@description('Azure Key Vault with RBAC authorization.')
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: union(tags, {
    Purpose: 'Tutorial 57 secrets store'
  })
  properties: {
    tenantId: tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: softDeleteRetentionDays
    enablePurgeProtection: enablePurgeProtection ? true : null
    publicNetworkAccess: disablePublicAccess ? 'Disabled' : 'Enabled'
    networkAcls: disablePublicAccess ? {
      bypass: 'AzureServices'
      defaultAction: 'Deny'
    } : {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }
}

@description('Diagnostic settings — only deployed when logAnalyticsWorkspaceId is supplied.')
resource diag 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(logAnalyticsWorkspaceId)) {
  name: 'diag-${keyVaultName}'
  scope: keyVault
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        categoryGroup: 'audit'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

// =============================================================================
// Outputs
// =============================================================================

@description('Key Vault resource ID.')
output keyVaultId string = keyVault.id

@description('Key Vault name.')
output keyVaultName string = keyVault.name

@description('Key Vault DNS URI.')
output keyVaultUri string = keyVault.properties.vaultUri
