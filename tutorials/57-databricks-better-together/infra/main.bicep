// =============================================================================
// Tutorial 57 — Databricks Better Together with Fabric
// Top-level deployment composing Databricks workspace + Key Vault + landing
// zone storage + Fabric workspace identity. Subscription-scope so a new RG can
// be created if needed.
// =============================================================================

targetScope = 'subscription'

// ---- Parameters ----

@description('Azure region for all resources')
param location string = 'eastus2'

@description('Project prefix used for naming (3-10 chars). Lowercase letters and digits only.')
@minLength(3)
@maxLength(10)
param projectPrefix string = 'btfabric'

@description('Deployment environment')
@allowed([
  'dev'
  'staging'
  'prod'
])
param environment string = 'dev'

@description('Resource group name. Created if it does not exist.')
param resourceGroupName string = 'rg-${projectPrefix}-tut57-${environment}'

@description('Tags applied to every resource.')
param tags object = {
  Project: 'Supercharge Microsoft Fabric'
  Tutorial: '57-databricks-better-together'
  ManagedBy: 'Bicep'
}

@description('When true, the Databricks workspace is created with public IP disabled (Private Link required).')
param disablePublicIp bool = false

@description('Optional: existing Log Analytics workspace resource ID for diagnostics. Empty string deploys without diagnostics.')
param logAnalyticsWorkspaceId string = ''

@description('When false (default), the Databricks workspace module is skipped — assume an existing UC-enabled DBW. Set to true to deploy a fresh one.')
param deployDatabricks bool = false

@description('When deployDatabricks=false, the existing Databricks workspace URL is recorded as an output for downstream notebooks. Empty string is allowed.')
param existingDatabricksWorkspaceUrl string = ''

@description('When false (default), no landing-zone storage account is deployed — the tutorial uploads sample data straight to UC volumes. Set to true and supply landingStoragePrincipalId if you want an Azure-side staging area.')
param deployLandingStorage bool = false

@description('Required when deployLandingStorage=true: the principalId of the managed identity / SP that should receive Storage Blob Data Contributor on the landing storage account.')
param landingStoragePrincipalId string = ''

// ---- Resources ----

@description('Resource group containing all tutorial 57 resources.')
resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

@description('Key Vault for tutorial secrets (Databricks PAT, SP client secret).')
module keyVaultModule '../../../infra/modules/security/key-vault.bicep' = {
  name: 'kv-${projectPrefix}-${environment}'
  scope: rg
  params: {
    location: location
    projectPrefix: projectPrefix
    environment: environment
    tags: tags
    logAnalyticsWorkspaceId: logAnalyticsWorkspaceId
  }
}

@description('Landing zone storage account (ADLS Gen2) for staging synthetic data before upload to UC. Only deployed when deployLandingStorage=true AND landingStoragePrincipalId is supplied.')
module storageModule '../../../infra/modules/storage/storage-account.bicep' = if (deployLandingStorage && !empty(landingStoragePrincipalId)) {
  name: 'st-${projectPrefix}-${environment}'
  scope: rg
  params: {
    storageAccountName: 'st${projectPrefix}${environment}${take(uniqueString(rg.id), 4)}'
    location: location
    logAnalyticsWorkspaceId: logAnalyticsWorkspaceId
    managedIdentityPrincipalId: landingStoragePrincipalId
    tags: tags
  }
}

@description('Azure Databricks workspace — Premium SKU for Unity Catalog support. Only deployed when deployDatabricks=true.')
module databricksModule '../../../infra/modules/databricks/databricks-workspace.bicep' = if (deployDatabricks) {
  name: 'dbw-${projectPrefix}-${environment}'
  scope: rg
  params: {
    location: location
    projectPrefix: projectPrefix
    environment: environment
    tags: tags
    disablePublicIp: disablePublicIp
  }
}

// ---- Outputs ----

@description('Tutorial deployment resource group.')
output resourceGroup string = rg.name

@description('Key Vault URI — used by notebooks via `notebookutils.credentials.getSecret`.')
output keyVaultUri string = keyVaultModule.outputs.keyVaultUri

@description('Databricks workspace URL — fresh deploy URL if deployDatabricks=true, otherwise the existing one supplied by parameter.')
output databricksWorkspaceUrl string = databricksModule.?outputs.workspaceUrl ?? existingDatabricksWorkspaceUrl

@description('Databricks workspace resource ID — needed for Fabric mirror item creation REST call. Empty string when using existing.')
output databricksWorkspaceId string = databricksModule.?outputs.workspaceId ?? ''

@description('Landing zone storage account name — empty string when deployLandingStorage=false.')
output landingStorageAccount string = storageModule.?outputs.storageAccountName ?? ''
