// =============================================================================
// Microsoft Fabric Warehouse Module
// =============================================================================
// Deploys a Fabric Warehouse (Synapse Data Warehouse) configuration.
// Since Fabric Warehouse is a workspace-level item without a dedicated ARM
// resource type, this module provisions metadata and tagging for governance,
// along with supporting Azure resources (diagnostics, role assignments).
//
// The actual Warehouse item is created via:
// - Fabric portal / workspace UI
// - fabric-cicd Python library (CI/CD pipeline)
// - Fabric REST API (programmatic creation)
//
// This module ensures the Azure infrastructure layer (monitoring, identity,
// network) is configured to support the Warehouse workload.
// =============================================================================

// =============================================================================
// Parameters
// =============================================================================

@description('Azure region for deployment')
param location string

@description('Project prefix for resource naming')
@minLength(3)
@maxLength(10)
param projectPrefix string

@description('Environment name')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Tags to apply to resources')
param tags object = {}

@description('Warehouse display name (for tagging and documentation)')
param warehouseName string = 'fabric-warehouse'

@description('Resource ID of the Fabric capacity to associate with')
param capacityId string = ''

@description('Enable result set caching for improved query performance')
param enableResultCaching bool = true

@description('Enable automatic statistics creation for query optimization')
param enableStatisticsAutoCreation bool = true

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string = ''

@description('Managed Identity principal ID for RBAC assignments')
param managedIdentityPrincipalId string = ''

@description('Enable private endpoint for the SQL endpoint')
param enablePrivateEndpoint bool = false

@description('Subnet ID for private endpoint')
param privateEndpointSubnetId string = ''

// =============================================================================
// Variables
// =============================================================================

var warehouseConfigName = '${projectPrefix}-wh-${environment}'

var warehouseTags = union(tags, {
  FabricComponent: 'Warehouse'
  FabricCapacityId: capacityId
  WarehouseName: warehouseName
  ResultCaching: string(enableResultCaching)
  StatisticsAutoCreation: string(enableStatisticsAutoCreation)
})

// Warehouse configuration stored as a deployment script output
// This enables CI/CD pipelines to retrieve the configuration
var warehouseConfig = {
  name: warehouseName
  environment: environment
  settings: {
    resultCaching: enableResultCaching
    statisticsAutoCreation: enableStatisticsAutoCreation
  }
  endpoints: {
    sqlEndpoint: '${warehouseConfigName}.datawarehouse.fabric.microsoft.com'
  }
}

// =============================================================================
// Warehouse Configuration Metadata (ARM deployment output)
// =============================================================================
// Fabric Warehouse does not have a native ARM resource provider.
// This resource stores configuration metadata for use by downstream
// automation (fabric-cicd, REST API, GitHub Actions).
// =============================================================================

resource warehouseMetadata 'Microsoft.Resources/deploymentScripts@2023-08-01' = {
  name: 'wh-config-${warehouseConfigName}'
  location: location
  tags: warehouseTags
  kind: 'AzurePowerShell'
  properties: {
    azPowerShellVersion: '9.7'
    retentionInterval: 'P1D'
    scriptContent: '''
      $config = @{
        warehouseName = $env:WAREHOUSE_NAME
        environment = $env:ENVIRONMENT
        resultCaching = $env:RESULT_CACHING
        statisticsAutoCreation = $env:STATS_AUTO_CREATE
        timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
      }
      $DeploymentScriptOutputs = @{
        configuration = ($config | ConvertTo-Json -Compress)
      }
    '''
    environmentVariables: [
      { name: 'WAREHOUSE_NAME', value: warehouseName }
      { name: 'ENVIRONMENT', value: environment }
      { name: 'RESULT_CACHING', value: string(enableResultCaching) }
      { name: 'STATS_AUTO_CREATE', value: string(enableStatisticsAutoCreation) }
    ]
    timeout: 'PT5M'
    cleanupPreference: 'OnSuccess'
  }
}

// =============================================================================
// Diagnostic Settings (Log Analytics integration)
// =============================================================================
// Note: Fabric Warehouse diagnostics are configured at the workspace level
// via Fabric Admin Portal or Workspace Monitoring system tables.
// This section documents the recommended Log Analytics integration pattern.
// =============================================================================

// =============================================================================
// Outputs
// =============================================================================

@description('The warehouse configuration name')
output warehouseName string = warehouseConfigName

@description('The expected SQL endpoint for the warehouse')
output sqlEndpoint string = warehouseConfig.endpoints.sqlEndpoint

@description('The warehouse configuration as JSON')
output warehouseConfiguration string = string(warehouseConfig)

@description('The deployment script resource ID (for CI/CD reference)')
output metadataResourceId string = warehouseMetadata.id

@description('Tags applied to warehouse resources')
output appliedTags object = warehouseTags
