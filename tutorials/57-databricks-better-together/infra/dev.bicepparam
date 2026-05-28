// =============================================================================
// Tutorial 57 — dev environment parameters
// Run with:
//   az deployment sub create --location eastus2 \
//     --template-file main.bicep --parameters dev.bicepparam
// =============================================================================

using './main.bicep'

param location = 'eastus2'
param projectPrefix = 'btfabric'
param environment = 'dev'
param resourceGroupName = 'rg-btfabric-tut57-dev'
param disablePublicIp = false
param logAnalyticsWorkspaceId = ''
// Use an existing UC-enabled Databricks workspace (recommended).
// Flip to true only if you want to provision a brand-new one.
param deployDatabricks = false
param existingDatabricksWorkspaceUrl = 'https://adb-<workspace-id>.<n>.azuredatabricks.net'
// Landing storage is also optional — keep false unless you actually need an
// Azure-side staging area for the parquet sample data (you can upload
// directly into a UC volume in Databricks instead).
param deployLandingStorage = false
param landingStoragePrincipalId = ''
param tags = {
  Project: 'Supercharge Microsoft Fabric'
  Tutorial: '57-databricks-better-together'
  ManagedBy: 'Bicep'
  Environment: 'dev'
  CostCenter: 'tutorial'
}
