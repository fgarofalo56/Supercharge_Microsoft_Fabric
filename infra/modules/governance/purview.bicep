// =============================================================================
// Microsoft Purview Module
// =============================================================================
// Deploys a Microsoft Purview account for data governance
// =============================================================================

@description('Name of the Purview account')
param purviewAccountName string

@description('Azure region for deployment')
param location string

@description('Principal ID of the managed identity for RBAC')
param managedIdentityPrincipalId string

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string

@description('Enable private endpoint')
param enablePrivateEndpoint bool = false

@description('Subnet ID for private endpoint')
param privateEndpointSubnetId string = ''

@description('Tags to apply to resources')
param tags object = {}

// =============================================================================
// Purview Account
// =============================================================================

resource purviewAccount 'Microsoft.Purview/accounts@2023-05-01-preview' = {
  name: purviewAccountName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publicNetworkAccess: enablePrivateEndpoint ? 'Disabled' : 'Enabled'
    managedResourceGroupName: 'mrg-${purviewAccountName}'
  }
}

// =============================================================================
// Diagnostic Settings
// =============================================================================

resource purviewDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'purview-diagnostics'
  scope: purviewAccount
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
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
// Role Assignment - Data Curator for Managed Identity
// =============================================================================

var purviewDataCuratorRoleId = 'af8bf84c-4de3-462a-b576-41e6c7478f52' // Purview Data Curator

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(purviewAccount.id, managedIdentityPrincipalId, purviewDataCuratorRoleId)
  scope: purviewAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', purviewDataCuratorRoleId)
    principalId: managedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// =============================================================================
// Private Endpoint (Optional)
// =============================================================================

module purviewPrivateEndpoint '../networking/private-endpoint.bicep' = if (enablePrivateEndpoint) {
  name: 'pe-${purviewAccountName}'
  params: {
    name: 'pe-${purviewAccountName}'
    location: location
    tags: tags
    subnetId: privateEndpointSubnetId
    privateLinkServiceId: purviewAccount.id
    groupIds: [
      'account'
    ]
    dnsZoneNames: [
      'privatelink.purview.azure.com'
    ]
  }
}

// =============================================================================
// Outputs
// =============================================================================

@description('The name of the Purview account')
output purviewAccountName string = purviewAccount.name

@description('The resource ID of the Purview account')
output purviewAccountId string = purviewAccount.id

@description('The Purview account endpoint')
output purviewEndpoint string = purviewAccount.properties.endpoints.catalog

@description('The principal ID of the Purview managed identity')
output purviewPrincipalId string = purviewAccount.identity.principalId
