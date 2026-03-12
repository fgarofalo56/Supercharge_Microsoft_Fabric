// =============================================================================
// Power BI / Fabric Workspace Module
// =============================================================================
// Deploys a Power BI Dedicated capacity and workspace configuration for
// Fabric analytics. Since Power BI workspaces are managed through the
// Power BI REST API (not ARM), this module provisions the Power BI Embedded
// capacity that backs Fabric workspaces and configures it for Direct Lake
// connectivity and workspace assignment.
//
// NOTE: Workspace creation, membership, and content deployment should be
// performed via the Power BI REST API or Fabric REST API post-deployment.
// This module handles the ARM-deployable infrastructure components.
// =============================================================================

// =============================================================================
// Parameters
// =============================================================================

@description('Name of the Power BI Embedded capacity (acts as Fabric workspace backing resource)')
param workspaceName string

@description('Resource ID of the Fabric capacity to associate with')
param fabricCapacityId string

@description('Azure region for deployment')
param location string

@description('Admin members (UPNs) for workspace administration')
param adminMembers array = []

@description('Power BI Embedded SKU for the workspace capacity')
@allowed([
  'A1'
  'A2'
  'A4'
  'A5'
  'A6'
])
param skuName string = 'A4'

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string = ''

@description('Tags to apply to resources')
param tags object = {}

// =============================================================================
// Variables
// =============================================================================

var workspaceTags = union(tags, {
  FabricComponent: 'Workspace'
  FabricCapacityId: fabricCapacityId
  AdminMembers: join(adminMembers, ';')
  DirectLake: 'Enabled'
})

// =============================================================================
// Power BI Embedded Capacity (Fabric Workspace backing resource)
// =============================================================================

resource pbiCapacity 'Microsoft.PowerBIDedicated/capacities@2024-01-01' = {
  name: workspaceName
  location: location
  tags: workspaceTags
  sku: {
    name: skuName
    tier: 'PBIE_Azure'
  }
  properties: {
    administration: {
      members: adminMembers
    }
    mode: 'Gen2'
  }
}

// =============================================================================
// Diagnostic Settings
// =============================================================================

resource pbiDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(logAnalyticsWorkspaceId)) {
  name: 'powerbi-workspace-diagnostics'
  scope: pbiCapacity
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
// Outputs
// =============================================================================

@description('The resource ID of the Power BI Embedded capacity')
output workspaceId string = pbiCapacity.id

@description('The name of the Power BI Embedded capacity')
output workspaceName string = pbiCapacity.name

@description('The provisioning state of the capacity')
output provisioningState string = pbiCapacity.properties.provisioningState

@description('The workspace admin members configured')
output adminMembersConfigured array = adminMembers

// NOTE: The actual workspace URL is generated when the workspace is created
// via the Power BI REST API. Use the Fabric capacity ID to assign a workspace
// to this capacity:
//   POST https://api.powerbi.com/v1.0/myorg/groups
//   POST https://api.powerbi.com/v1.0/myorg/groups/{groupId}/AssignToCapacity
//   Body: { "capacityId": "<output.workspaceId>" }
@description('The workspace URL placeholder - actual URL is generated via Power BI REST API after workspace creation')
output workspaceUrl string = 'https://app.powerbi.com/groups/${pbiCapacity.name}'
