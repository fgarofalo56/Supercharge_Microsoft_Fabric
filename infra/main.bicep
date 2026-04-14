// =============================================================================
// Microsoft Fabric Casino/Gaming POC - Main Orchestration
// =============================================================================
// This template deploys all infrastructure required for the Fabric POC:
// - Fabric Capacity (F64)
// - Microsoft Purview Account
// - Azure Data Lake Storage Gen2
// - Azure Key Vault
// - Log Analytics Workspace
// - Virtual Network (optional, for private endpoints)
// - Managed Identity
// - Eventstream / Event Hubs (optional, for real-time ingestion)
// - Eventhouse / Azure Data Explorer (optional, for KQL analytics)
// - Power BI Workspace / Embedded Capacity (optional, for BI)
// =============================================================================

targetScope = 'subscription'

// =============================================================================
// Parameters
// =============================================================================

@description('Environment name (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Azure region for deployment')
param location string = 'eastus2'

@description('Project prefix for resource naming (3-10 chars)')
@minLength(3)
@maxLength(10)
param projectPrefix string = 'fabricpoc'

@description('Fabric capacity SKU')
@allowed(['F2', 'F4', 'F8', 'F16', 'F32', 'F64', 'F128', 'F256', 'F512', 'F1024', 'F2048'])
param fabricCapacitySku string = 'F64'

@description('Admin email for Fabric capacity')
param fabricAdminEmail string

@description('Enable private endpoints for enhanced security')
param enablePrivateEndpoints bool = false

@description('Log retention in days')
@minValue(30)
@maxValue(730)
param logRetentionDays int = 90

@description('Tags to apply to all resources')
param tags object = {}

@description('Cost center for billing allocation')
param costCenter string = ''

@description('Owner email or team name')
param owner string = ''

@description('Deployment timestamp (auto-generated)')
param deployedAt string = utcNow()

// --- Real-Time Intelligence (RTI) Parameters ---

@description('Enable Eventstream (Event Hubs) deployment for real-time ingestion')
param enableEventstream bool = false

@description('Enable Eventhouse (Azure Data Explorer) deployment for KQL analytics')
param enableEventhouse bool = false

@description('Enable Power BI Embedded capacity deployment')
param enablePowerBIWorkspace bool = false

@description('Admin members (UPNs) for Power BI workspace')
param powerBIAdminMembers array = []

@description('Eventhouse data retention in days')
@minValue(1)
@maxValue(36500)
param eventhouseRetentionDays int = 365

@description('Eventhouse hot cache period in days')
@minValue(1)
@maxValue(365)
param eventhouseHotCacheDays int = 31

// --- Phase 9: Workspace Identity & Governance Parameters ---

@description('Enable Fabric Workspace Identity (GA 2026) for credential-free authentication')
param enableWorkspaceIdentity bool = false

@description('Fabric data domain for workspace tag governance (e.g., Casino, Federal-USDA)')
param fabricDomain string = ''

@description('Data classification level for workspace tag governance')
@allowed(['Public', 'Internal', 'Confidential', 'HighlyConfidential', ''])
param dataClassification string = ''

@description('Compliance framework applicable to this deployment')
@allowed(['NIGC-MICS', 'HIPAA', 'FedRAMP', 'FISMA', '42CFR-Part2', 'CIPSEA', 'None', ''])
param complianceFramework string = ''

@description('Federal agency code for workspace tag governance (e.g., USDA, SBA, NOAA, EPA, DOI)')
param agencyCode string = ''

// --- Phase 10: Warehouse, SQL Database, Pipeline & Monitoring Parameters ---

@description('Enable Fabric Warehouse configuration deployment')
param enableWarehouse bool = false

@description('Warehouse display name')
param warehouseName string = 'fabric-warehouse'

@description('Enable Fabric SQL Database configuration deployment')
param enableSqlDatabase bool = false

@description('SQL Database display name')
param sqlDatabaseName string = 'fabric-sqldb'

@description('Enable Dynamic Data Masking for SQL Database')
param enableDDM bool = true

@description('Enable Customer-Managed Keys for SQL Database')
param enableSqlDbCMK bool = false

@description('Key Vault key URI for SQL Database CMK')
param sqlDbKeyVaultKeyUri string = ''

@description('Enable Fabric Data Factory Pipeline configuration deployment')
param enablePipeline bool = false

@description('Pipeline display name')
param pipelineName string = 'fabric-pipeline'

@description('Enable schedule trigger for pipeline')
param enablePipelineSchedule bool = false

@description('Pipeline schedule frequency')
@allowed(['Minute', 'Hour', 'Day', 'Week', 'Month'])
param pipelineScheduleFrequency string = 'Day'

@description('Enable monitoring alerts and budget tracking')
param enableMonitoringAlerts bool = false

@description('Monthly budget amount in USD for cost alerts')
@minValue(100)
@maxValue(1000000)
param monthlyBudgetAmount int = 10000

@description('Capacity utilization threshold percentage for alerts')
@minValue(50)
@maxValue(100)
param capacityAlertThreshold int = 80

@description('Email addresses for alert notifications')
param alertEmailRecipients array = []

// =============================================================================
// Variables
// =============================================================================

var resourceGroupName = 'rg-${projectPrefix}-${environment}'
var fabricCapacityName = 'fabric${projectPrefix}${environment}'
var purviewAccountName = 'pview${projectPrefix}${environment}'
var storageAccountName = 'st${projectPrefix}${environment}'
var keyVaultName = 'kv-${projectPrefix}-${environment}'
var logAnalyticsName = 'log-${projectPrefix}-${environment}'
var managedIdentityName = 'id-${projectPrefix}-${environment}'
var vnetName = 'vnet-${projectPrefix}-${environment}'
var eventStreamName = 'evtns-${projectPrefix}-${environment}'
var eventHouseName = 'adx${projectPrefix}${environment}'
var powerBICapacityName = 'pbi${projectPrefix}${environment}'

// Cost allocation tags (using cost-tags module pattern)
var costAllocationTags = union(
  !empty(costCenter) ? { CostCenter: costCenter } : {},
  !empty(owner) ? { Owner: owner } : {}
)

// Phase 9: Workspace governance tags (GA 2026)
var workspaceGovernanceTags = union(
  !empty(fabricDomain) ? { FabricDomain: fabricDomain } : {},
  !empty(dataClassification) ? { DataClassification: dataClassification } : {},
  !empty(complianceFramework) ? { ComplianceFramework: complianceFramework } : {},
  !empty(agencyCode) ? { AgencyCode: agencyCode } : {}
)

var defaultTags = union(tags, costAllocationTags, workspaceGovernanceTags, {
  Environment: environment
  Project: 'Microsoft Fabric POC'
  Application: 'fabric-casino-poc'
  ManagedBy: 'Bicep'
  DeployedAt: deployedAt
})

// =============================================================================
// Resource Group
// =============================================================================

resource resourceGroup 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: resourceGroupName
  location: location
  tags: defaultTags
}

// =============================================================================
// Monitoring Module
// =============================================================================

module monitoring 'modules/monitoring/log-analytics.bicep' = {
  name: 'monitoring-deployment'
  scope: resourceGroup
  params: {
    name: logAnalyticsName
    location: location
    retentionInDays: logRetentionDays
    tags: defaultTags
  }
}

// =============================================================================
// Security Module (Key Vault & Managed Identity)
// =============================================================================

module security 'modules/security/security.bicep' = {
  name: 'security-deployment'
  scope: resourceGroup
  params: {
    keyVaultName: keyVaultName
    managedIdentityName: managedIdentityName
    location: location
    logAnalyticsWorkspaceId: monitoring.outputs.workspaceId
    enablePrivateEndpoints: enablePrivateEndpoints
    tags: defaultTags
  }
}

// =============================================================================
// Networking Module (Optional)
// =============================================================================

module networking 'modules/networking/vnet.bicep' = if (enablePrivateEndpoints) {
  name: 'networking-deployment'
  scope: resourceGroup
  params: {
    vnetName: vnetName
    location: location
    tags: defaultTags
  }
}

// =============================================================================
// Storage Module (ADLS Gen2)
// =============================================================================

module storage 'modules/storage/storage-account.bicep' = {
  name: 'storage-deployment'
  scope: resourceGroup
  params: {
    storageAccountName: storageAccountName
    location: location
    logAnalyticsWorkspaceId: monitoring.outputs.workspaceId
    managedIdentityPrincipalId: security.outputs.managedIdentityPrincipalId
    enablePrivateEndpoint: enablePrivateEndpoints
    privateEndpointSubnetId: enablePrivateEndpoints ? networking.outputs.privateEndpointSubnetId : ''
    tags: defaultTags
  }
}

// =============================================================================
// Fabric Capacity Module
// =============================================================================

module fabric 'modules/fabric/fabric-capacity.bicep' = {
  name: 'fabric-deployment'
  scope: resourceGroup
  params: {
    capacityName: fabricCapacityName
    location: location
    skuName: fabricCapacitySku
    adminEmail: fabricAdminEmail
    tags: defaultTags
  }
}

// =============================================================================
// Governance Module (Purview)
// =============================================================================

module governance 'modules/governance/purview.bicep' = {
  name: 'governance-deployment'
  scope: resourceGroup
  params: {
    purviewAccountName: purviewAccountName
    location: location
    managedIdentityPrincipalId: security.outputs.managedIdentityPrincipalId
    logAnalyticsWorkspaceId: monitoring.outputs.workspaceId
    enablePrivateEndpoint: enablePrivateEndpoints
    privateEndpointSubnetId: enablePrivateEndpoints ? networking.outputs.privateEndpointSubnetId : ''
    tags: defaultTags
  }
}

// =============================================================================
// Eventstream Module (Real-Time Ingestion - Optional)
// =============================================================================
// Deploys Event Hubs namespace as the backing resource for Fabric Eventstream.
// Enable by setting enableEventstream = true in your parameter file.
// =============================================================================

module eventstream 'modules/fabric/fabric-eventstream.bicep' = if (enableEventstream) {
  name: 'eventstream-deployment'
  scope: resourceGroup
  params: {
    eventStreamName: eventStreamName
    fabricCapacityId: fabric.outputs.capacityId
    location: location
    logAnalyticsWorkspaceId: monitoring.outputs.workspaceId
    enablePrivateEndpoint: enablePrivateEndpoints
    privateEndpointSubnetId: enablePrivateEndpoints ? networking.outputs.privateEndpointSubnetId : ''
    tags: defaultTags
  }
}

// =============================================================================
// Eventhouse Module (KQL Real-Time Analytics - Optional)
// =============================================================================
// Deploys Azure Data Explorer cluster as the backing resource for Fabric
// Eventhouse with KQL databases, ingestion mappings, and retention policies.
// Enable by setting enableEventhouse = true in your parameter file.
// =============================================================================

module eventhouse 'modules/fabric/fabric-eventhouse.bicep' = if (enableEventhouse) {
  name: 'eventhouse-deployment'
  scope: resourceGroup
  params: {
    eventHouseName: eventHouseName
    fabricCapacityId: fabric.outputs.capacityId
    location: location
    retentionDays: eventhouseRetentionDays
    hotCacheDays: eventhouseHotCacheDays
    logAnalyticsWorkspaceId: monitoring.outputs.workspaceId
    managedIdentityPrincipalId: security.outputs.managedIdentityPrincipalId
    enablePrivateEndpoint: enablePrivateEndpoints
    privateEndpointSubnetId: enablePrivateEndpoints ? networking.outputs.privateEndpointSubnetId : ''
    tags: defaultTags
  }
}

// =============================================================================
// Power BI Workspace Module (BI & Direct Lake - Optional)
// =============================================================================
// Deploys Power BI Embedded capacity for Fabric workspace analytics.
// Enable by setting enablePowerBIWorkspace = true in your parameter file.
// =============================================================================

module powerBIWorkspace 'modules/analytics/powerbi-workspace.bicep' = if (enablePowerBIWorkspace) {
  name: 'powerbi-workspace-deployment'
  scope: resourceGroup
  params: {
    workspaceName: powerBICapacityName
    fabricCapacityId: fabric.outputs.capacityId
    location: location
    adminMembers: powerBIAdminMembers
    logAnalyticsWorkspaceId: monitoring.outputs.workspaceId
    tags: defaultTags
  }
}

// =============================================================================
// Workspace Identity (Phase 9 - GA 2026: Credential-free authentication)
// =============================================================================

module workspaceIdentity 'modules/security/workspace-identity.bicep' = if (enableWorkspaceIdentity) {
  name: 'workspace-identity-deployment'
  scope: resourceGroup
  dependsOn: [security, storage, governance]
  params: {
    location: location
    projectPrefix: projectPrefix
    environment: environment
    tags: defaultTags
    enableKeyVaultAccess: true
    keyVaultId: security.outputs.keyVaultId
    enableStorageAccess: true
    storageAccountId: storage.outputs.storageAccountId
    enablePurviewAccess: true
    purviewAccountId: governance.outputs.purviewAccountId
  }
}

// =============================================================================
// Fabric Warehouse Module (Phase 10 - Optional)
// =============================================================================
// Deploys configuration metadata for Fabric Warehouse (Synapse Data Warehouse).
// Enable by setting enableWarehouse = true in your parameter file.
// =============================================================================

module warehouse 'modules/fabric/fabric-warehouse.bicep' = if (enableWarehouse) {
  name: 'warehouse-deployment'
  scope: resourceGroup
  params: {
    location: location
    projectPrefix: projectPrefix
    environment: environment
    warehouseName: warehouseName
    capacityId: fabric.outputs.capacityId
    logAnalyticsWorkspaceId: monitoring.outputs.workspaceId
    managedIdentityPrincipalId: security.outputs.managedIdentityPrincipalId
    tags: defaultTags
  }
}

// =============================================================================
// Fabric SQL Database Module (Phase 10 - Optional)
// =============================================================================
// Deploys configuration metadata for Fabric SQL Database (OLTP + OneLake).
// Enable by setting enableSqlDatabase = true in your parameter file.
// =============================================================================

module sqlDatabase 'modules/fabric/fabric-sql-database.bicep' = if (enableSqlDatabase) {
  name: 'sql-database-deployment'
  scope: resourceGroup
  params: {
    location: location
    projectPrefix: projectPrefix
    environment: environment
    databaseName: sqlDatabaseName
    capacityId: fabric.outputs.capacityId
    enableDDM: enableDDM
    enableCMK: enableSqlDbCMK
    keyVaultKeyUri: sqlDbKeyVaultKeyUri
    logAnalyticsWorkspaceId: monitoring.outputs.workspaceId
    managedIdentityPrincipalId: security.outputs.managedIdentityPrincipalId
    tags: defaultTags
  }
}

// =============================================================================
// Fabric Data Factory Pipeline Module (Phase 10 - Optional)
// =============================================================================
// Deploys configuration metadata for Fabric Data Factory pipelines.
// Enable by setting enablePipeline = true in your parameter file.
// =============================================================================

module pipeline 'modules/fabric/fabric-pipeline.bicep' = if (enablePipeline) {
  name: 'pipeline-deployment'
  scope: resourceGroup
  params: {
    location: location
    projectPrefix: projectPrefix
    environment: environment
    pipelineName: pipelineName
    capacityId: fabric.outputs.capacityId
    enableScheduleTrigger: enablePipelineSchedule
    scheduleFrequency: pipelineScheduleFrequency
    logAnalyticsWorkspaceId: monitoring.outputs.workspaceId
    tags: defaultTags
  }
}

// =============================================================================
// Monitoring Alerts & Budgets Module (Phase 10 - Optional)
// =============================================================================
// Deploys capacity utilization alerts and budget tracking.
// Enable by setting enableMonitoringAlerts = true in your parameter file.
// =============================================================================

module monitoringAlerts 'modules/monitoring/alerts-and-budgets.bicep' = if (enableMonitoringAlerts) {
  name: 'monitoring-alerts-deployment'
  scope: resourceGroup
  params: {
    location: location
    logAnalyticsWorkspaceId: monitoring.outputs.workspaceId
    enableCapacityAlerts: true
    capacityThresholdPercent: capacityAlertThreshold
    enableBudgetAlerts: true
    monthlyBudgetAmount: monthlyBudgetAmount
    alertEmailRecipients: alertEmailRecipients
    fabricCapacityResourceId: fabric.outputs.capacityId
    tags: defaultTags
  }
}

// =============================================================================
// Resource Locks (Prevent accidental deletion of critical resources)
// =============================================================================

module resourceLocks 'modules/security/resource-locks.bicep' = {
  name: 'resource-locks-deployment'
  scope: resourceGroup
  dependsOn: [security, storage, fabric, monitoring, governance]
  params: {
    keyVaultName: keyVaultName
    storageAccountName: storageAccountName
    fabricCapacityName: fabricCapacityName
    logAnalyticsName: logAnalyticsName
    purviewAccountName: purviewAccountName
  }
}

// =============================================================================
// Outputs
// =============================================================================

output resourceGroupName string = resourceGroup.name
output resourceGroupId string = resourceGroup.id

output fabricCapacityName string = fabric.outputs.capacityName
output fabricCapacityId string = fabric.outputs.capacityId

output purviewAccountName string = governance.outputs.purviewAccountName
output purviewEndpoint string = governance.outputs.purviewEndpoint

output storageAccountName string = storage.outputs.storageAccountName
output storageAccountId string = storage.outputs.storageAccountId
output adlsEndpoint string = storage.outputs.dfsEndpoint

output keyVaultName string = security.outputs.keyVaultName
output keyVaultUri string = security.outputs.keyVaultUri

output logAnalyticsWorkspaceId string = monitoring.outputs.workspaceId
output logAnalyticsWorkspaceName string = monitoring.outputs.workspaceName

output managedIdentityId string = security.outputs.managedIdentityId
output managedIdentityPrincipalId string = security.outputs.managedIdentityPrincipalId
output managedIdentityClientId string = security.outputs.managedIdentityClientId

// --- Real-Time Intelligence Outputs (conditional) ---

output eventStreamId string = enableEventstream ? eventstream.outputs.eventStreamId : ''
output eventStreamEndpoint string = enableEventstream ? eventstream.outputs.eventStreamEndpoint : ''

output eventHouseId string = enableEventhouse ? eventhouse.outputs.eventHouseId : ''
output kqlEndpoint string = enableEventhouse ? eventhouse.outputs.kqlEndpoint : ''
output eventHouseDatabaseIds array = enableEventhouse ? eventhouse.outputs.databaseIds : []

output powerBIWorkspaceId string = enablePowerBIWorkspace ? powerBIWorkspace.outputs.workspaceId : ''
output powerBIWorkspaceUrl string = enablePowerBIWorkspace ? powerBIWorkspace.outputs.workspaceUrl : ''

// --- Phase 9: Workspace Identity Outputs (conditional) ---

output workspaceIdentityId string = enableWorkspaceIdentity ? workspaceIdentity.outputs.identityId : ''
output workspaceIdentityPrincipalId string = enableWorkspaceIdentity ? workspaceIdentity.outputs.principalId : ''
output workspaceIdentityClientId string = enableWorkspaceIdentity ? workspaceIdentity.outputs.clientId : ''

// Cost tracking reference
output appliedTags object = defaultTags

// --- Phase 10: Warehouse, SQL Database, Pipeline & Monitoring Outputs ---

output warehouseName string = enableWarehouse ? warehouse.outputs.warehouseName : ''
output warehouseSqlEndpoint string = enableWarehouse ? warehouse.outputs.sqlEndpoint : ''

output sqlDatabaseEndpoint string = enableSqlDatabase ? sqlDatabase.outputs.tdsEndpoint : ''
output sqlDatabaseOneLakeEnabled bool = enableSqlDatabase ? sqlDatabase.outputs.oneLakeReplicationEnabled : false

output fabricPipelineName string = enablePipeline ? pipeline.outputs.pipelineName : ''
output fabricPipelineTriggerStatus string = enablePipeline ? pipeline.outputs.triggerStatus : ''

output monitoringActionGroupId string = enableMonitoringAlerts ? monitoringAlerts.outputs.actionGroupId : ''
output monitoringBudgetId string = enableMonitoringAlerts ? monitoringAlerts.outputs.budgetId : ''

// =============================================================================
// Cost Documentation Reference
// =============================================================================
// For detailed cost estimates and optimization strategies, see:
// - docs/COST_ESTIMATION.md - Comprehensive cost guide
// - docs/diagrams/cost-breakdown.md - Visual cost breakdowns
// - infra/cost-tags.bicep - Reusable cost allocation tags module
// =============================================================================
