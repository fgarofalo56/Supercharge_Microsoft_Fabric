// =============================================================================
// Module: workspace-identity.bicep
// Description: Deploys a user-assigned managed identity for Fabric workspace
//              identity scenarios. Enables credential-free authentication to
//              Azure resources (Key Vault, Storage, Purview) from Fabric workspaces.
//              Supports the Workspace Identity (GA, 2026) pattern.
// =============================================================================

// ---- Parameters ----

@description('Azure region for the managed identity resource')
param location string

@description('Project prefix for resource naming (3-10 characters)')
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

@description('Tags to apply to resources')
param tags object = {}

@description('Enable Key Vault Secrets User role assignment for the workspace identity')
param enableKeyVaultAccess bool = true

@description('Key Vault resource ID for role assignment (required when enableKeyVaultAccess is true)')
param keyVaultId string = ''

@description('Enable Storage Blob Data Contributor role assignment')
param enableStorageAccess bool = true

@description('Storage account resource ID for role assignment (required when enableStorageAccess is true)')
param storageAccountId string = ''

@description('Enable Purview Data Curator role assignment')
param enablePurviewAccess bool = false

@description('Purview account resource ID for role assignment (required when enablePurviewAccess is true)')
param purviewAccountId string = ''

// ---- Variables ----

var identityName = 'id-fabric-ws-${projectPrefix}-${environment}'

// Well-known role definition IDs
var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'
var storageBlobDataContributorRoleId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
var purviewDataCuratorRoleId = 'af8bf84c-4de3-462a-b576-41e6c7478f52'

// =============================================================================
// Resources
// =============================================================================

@description('User-assigned managed identity for Fabric workspace')
resource workspaceIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
  tags: union(tags, {
    Purpose: 'Fabric Workspace Identity'
    FabricFeature: 'WorkspaceIdentity-GA-2026'
  })
}

// ---- Role Assignments ----

@description('Key Vault Secrets User role for workspace identity')
resource kvRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableKeyVaultAccess && !empty(keyVaultId)) {
  name: guid(keyVaultId, workspaceIdentity.id, keyVaultSecretsUserRoleId)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
    principalId: workspaceIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

@description('Storage Blob Data Contributor role for workspace identity')
resource storageRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableStorageAccess && !empty(storageAccountId)) {
  name: guid(storageAccountId, workspaceIdentity.id, storageBlobDataContributorRoleId)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataContributorRoleId)
    principalId: workspaceIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

@description('Purview Data Curator role for workspace identity')
resource purviewRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enablePurviewAccess && !empty(purviewAccountId)) {
  name: guid(purviewAccountId, workspaceIdentity.id, purviewDataCuratorRoleId)
  scope: purviewAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', purviewDataCuratorRoleId)
    principalId: workspaceIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// ---- Existing Resource References ----
// All target resources are expected to live in the same resource group as the
// workspace identity (enforced by main.bicep orchestration). Role assignments
// must target the same scope as this module, so we reference by name only.
// Cross-RG deployments are not supported; pass resource IDs only for resources
// co-located in the same resource group.

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = if (enableKeyVaultAccess && !empty(keyVaultId)) {
  name: last(split(keyVaultId, '/'))
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = if (enableStorageAccess && !empty(storageAccountId)) {
  name: last(split(storageAccountId, '/'))
}

resource purviewAccount 'Microsoft.Purview/accounts@2023-05-01-preview' existing = if (enablePurviewAccess && !empty(purviewAccountId)) {
  name: last(split(purviewAccountId, '/'))
}

// =============================================================================
// Outputs
// =============================================================================

@description('Resource ID of the workspace managed identity')
output identityId string = workspaceIdentity.id

@description('Principal ID (Object ID) of the workspace managed identity')
output principalId string = workspaceIdentity.properties.principalId

@description('Client ID of the workspace managed identity')
output clientId string = workspaceIdentity.properties.clientId

@description('Name of the workspace managed identity')
output identityName string = workspaceIdentity.name
