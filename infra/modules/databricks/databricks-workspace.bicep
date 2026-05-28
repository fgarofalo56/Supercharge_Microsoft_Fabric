// =============================================================================
// Module: databricks-workspace.bicep
// Description: Azure Databricks workspace (Premium SKU) for the
//              "Databricks Better Together with Fabric" tutorial.
//              Premium is required for Unity Catalog support, table ACLs,
//              and credential passthrough — all of which the tutorial demos.
//              Unity Catalog metastore creation itself is an account-level
//              operation that lives outside Bicep — see the tutorial README
//              for the post-deploy step.
// =============================================================================

// ---- Parameters ----

@description('Azure region for the Databricks workspace')
param location string

@description('Project prefix used for resource naming (3-10 chars)')
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

@description('Optional VNet integration — when supplied, the workspace is injected into the supplied VNet using "VNet injection" (Customer-managed VNet).')
param vnetId string = ''

@description('Public subnet name inside the supplied VNet (used only when vnetId is set).')
param publicSubnetName string = 'snet-databricks-public'

@description('Private subnet name inside the supplied VNet (used only when vnetId is set).')
param privateSubnetName string = 'snet-databricks-private'

@description('When true, public network access to the control plane is disabled (requires private link).')
param disablePublicIp bool = false

// ---- Variables ----

var workspaceName = 'dbw-${projectPrefix}-${environment}'
var managedResourceGroupName = 'rg-dbw-${projectPrefix}-${environment}-managed'
var managedResourceGroupId = '${subscription().id}/resourceGroups/${managedResourceGroupName}'

var useCustomVnet = !empty(vnetId)

// =============================================================================
// Resources
// =============================================================================

@description('Azure Databricks workspace — Premium SKU (required for Unity Catalog).')
resource databricksWorkspace 'Microsoft.Databricks/workspaces@2024-05-01' = {
  name: workspaceName
  location: location
  tags: union(tags, {
    Purpose: 'Better Together with Fabric'
    Tutorial: '57-databricks-better-together'
  })
  sku: {
    name: 'premium'
  }
  properties: {
    managedResourceGroupId: managedResourceGroupId
    parameters: union(
      {
        enableNoPublicIp: {
          value: disablePublicIp
        }
      },
      useCustomVnet ? {
        customVirtualNetworkId: {
          value: vnetId
        }
        customPublicSubnetName: {
          value: publicSubnetName
        }
        customPrivateSubnetName: {
          value: privateSubnetName
        }
      } : {}
    )
  }
}

// =============================================================================
// Outputs
// =============================================================================

@description('Workspace resource ID — use with the Databricks REST API and Fabric mirror registration.')
output workspaceId string = databricksWorkspace.id

@description('Workspace URL (use for Databricks CLI configuration).')
output workspaceUrl string = 'https://${databricksWorkspace.properties.workspaceUrl}'

@description('Workspace name.')
output workspaceName string = databricksWorkspace.name

@description('Managed resource group created by Databricks (contains DBFS storage, compute, etc.).')
output managedResourceGroup string = managedResourceGroupName
