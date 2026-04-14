// =============================================================================
// Microsoft Fabric Warehouse Module (Metadata-Only)
// =============================================================================
// This module does NOT deploy any Azure resources. Fabric Warehouse is a
// workspace-level item without a dedicated ARM resource type.
//
// Purpose:
// - Documents the Warehouse configuration as Bicep parameters
// - Emits outputs consumed by main.bicep and CI/CD pipelines
// - Serves as the IaC "contract" for what the Warehouse looks like
//
// Actual Warehouse items are deployed via:
// - fabric-cicd Python library  (scripts/fabric-cicd-deploy.py)
// - Fabric REST API
// - Fabric portal UI
// =============================================================================

// =============================================================================
// Parameters (kept for documentation / contract purposes)
// =============================================================================

@description('Azure region (unused — no resources deployed)')
param location string

@description('Project prefix for resource naming')
@minLength(3)
@maxLength(10)
param projectPrefix string

@description('Environment name')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Tags (passed through to outputs)')
param tags object = {}

@description('Warehouse display name')
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

var warehouseConfig = {
  name: warehouseName
  configName: warehouseConfigName
  environment: environment
  capacityId: capacityId
  settings: {
    resultCaching: enableResultCaching
    statisticsAutoCreation: enableStatisticsAutoCreation
  }
  endpoints: {
    sqlEndpoint: '${warehouseConfigName}.datawarehouse.fabric.microsoft.com'
  }
  governance: {
    logAnalyticsWorkspaceId: logAnalyticsWorkspaceId
    managedIdentityPrincipalId: managedIdentityPrincipalId
    privateEndpoint: enablePrivateEndpoint
    privateEndpointSubnetId: privateEndpointSubnetId
  }
}

// =============================================================================
// OUTPUT-ONLY — No resources deployed
// Actual Fabric Warehouse items are deployed via fabric-cicd library.
// =============================================================================

@description('The warehouse configuration name')
output warehouseName string = warehouseConfigName

@description('The expected SQL endpoint for the warehouse')
output sqlEndpoint string = warehouseConfig.endpoints.sqlEndpoint

@description('The full warehouse configuration as JSON')
output configurationJson string = string(warehouseConfig)

@description('Tags that would be applied to warehouse resources')
output appliedTags object = union(tags, {
  FabricComponent: 'Warehouse'
  FabricCapacityId: capacityId
  WarehouseName: warehouseName
})
