// =============================================================================
// Security Module (Key Vault & Managed Identity)
// =============================================================================
// Deploys Key Vault and User-Assigned Managed Identity
// =============================================================================

@description('Name of the Key Vault')
param keyVaultName string

@description('Name of the Managed Identity')
param managedIdentityName string

@description('Azure region for deployment')
param location string

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string

@description('Tags to apply to resources')
param tags object = {}

@description('Enable private endpoints - restricts public network access when true')
param enablePrivateEndpoints bool = false

@description('Subnet ID for private endpoint')
param privateEndpointSubnetId string = ''

@description('Key Vault SKU. `premium` is required for HSM-backed keys (FedRAMP, PCI-DSS).')
@allowed([
  'standard'
  'premium'
])
param keyVaultSku string = 'standard'

@description('When true, provisions a CMK key inside this Key Vault for storage encryption and outputs its key URI.')
param provisionStorageCmkKey bool = false

// =============================================================================
// Managed Identity
// =============================================================================

resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: managedIdentityName
  location: location
  tags: tags
}

// =============================================================================
// Key Vault
// =============================================================================

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: keyVaultSku
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    // Restrict public access when private endpoints are enabled
    publicNetworkAccess: enablePrivateEndpoints ? 'Disabled' : 'Enabled'
    networkAcls: {
      defaultAction: enablePrivateEndpoints ? 'Deny' : 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// =============================================================================
// CMK key for storage encryption (provisioned when compliance requires CMK)
// =============================================================================

resource storageCmkKey 'Microsoft.KeyVault/vaults/keys@2023-07-01' = if (provisionStorageCmkKey) {
  parent: keyVault
  name: 'cmk-storage-${uniqueString(resourceGroup().id)}'
  properties: {
    kty: keyVaultSku == 'premium' ? 'RSA-HSM' : 'RSA'
    keySize: 2048
    keyOps: [
      'wrapKey'
      'unwrapKey'
    ]
    attributes: {
      enabled: true
      exportable: false
    }
    rotationPolicy: {
      attributes: {
        expiryTime: 'P2Y'
      }
      lifetimeActions: [
        {
          trigger: {
            timeBeforeExpiry: 'P60D'
          }
          action: {
            type: 'Rotate'
          }
        }
        {
          trigger: {
            timeBeforeExpiry: 'P30D'
          }
          action: {
            type: 'Notify'
          }
        }
      ]
    }
  }
}

// =============================================================================
// Key Vault Secrets User Role for Managed Identity
// =============================================================================

var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

resource keyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, managedIdentity.id, keyVaultSecretsUserRoleId)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// =============================================================================
// Key Vault Crypto User Role for Managed Identity (CMK wrap/unwrap)
// =============================================================================

var keyVaultCryptoUserRoleId = '12338af0-0e69-4776-bea7-57586841c05f'

resource keyVaultCryptoRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, managedIdentity.id, keyVaultCryptoUserRoleId)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultCryptoUserRoleId)
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// =============================================================================
// Diagnostic Settings
// =============================================================================

resource keyVaultDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'keyvault-diagnostics'
  scope: keyVault
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        categoryGroup: 'audit'
        enabled: true
      }
      {
        categoryGroup: 'allLogs'
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
// Private Endpoint (Optional)
// =============================================================================

module keyVaultPrivateEndpoint '../networking/private-endpoint.bicep' = if (enablePrivateEndpoints) {
  name: 'pe-${keyVaultName}'
  params: {
    name: 'pe-${keyVaultName}'
    location: location
    tags: tags
    subnetId: privateEndpointSubnetId
    privateLinkServiceId: keyVault.id
    groupIds: [
      'vault'
    ]
    dnsZoneNames: [
      'privatelink.vaultcore.azure.net'
    ]
  }
}

// =============================================================================
// Outputs
// =============================================================================

@description('The name of the Key Vault')
output keyVaultName string = keyVault.name

@description('The resource ID of the Key Vault')
output keyVaultId string = keyVault.id

@description('The URI of the Key Vault')
output keyVaultUri string = keyVault.properties.vaultUri

@description('The resource ID of the Managed Identity')
output managedIdentityId string = managedIdentity.id

@description('The principal ID of the Managed Identity')
output managedIdentityPrincipalId string = managedIdentity.properties.principalId

@description('The client ID of the Managed Identity')
output managedIdentityClientId string = managedIdentity.properties.clientId

@description('Unversioned key URI for the storage CMK key (empty when not provisioned).')
output storageCmkKeyUri string = provisionStorageCmkKey ? storageCmkKey.properties.keyUri : ''
