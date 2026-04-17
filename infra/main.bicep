// =============================================================================
// Microsoft Fabric POC - Main Orchestration
// =============================================================================
// Deploys: Fabric Capacity, Purview, ADLS Gen2, Key Vault, Log Analytics,
// Managed Identity, (optional) VNet + private endpoints, Eventstream,
// Eventhouse, Power BI capacity, Workspace Identity, and Monitoring alerts.
//
// Compliance frameworks selected via `complianceFramework` actively
// tighten controls (retention, private endpoints, FIPS Key Vault,
// CMK enablement) -- the parameter is NOT just a tag.
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

@description('Admin email for Fabric capacity. Must NOT be a placeholder in prod.')
param fabricAdminEmail string

@description('Enable private endpoints for enhanced security. Forced true for FedRAMP/HIPAA.')
param enablePrivateEndpoints bool = false

@description('Log retention in days. Floor lifted by compliance framework (HIPAA>=2190, NIGC-MICS>=1825, FedRAMP>=1095, PCI-DSS>=365).')
@minValue(30)
@maxValue(4383)
param logRetentionDays int = 90

@description('Tags to apply to all resources')
param tags object = {}

@description('Cost center for billing allocation')
param costCenter string = ''

@description('Owner email or team name')
param owner string = ''

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

// --- Workspace Identity & Governance Parameters ---

@description('Enable Fabric Workspace Identity (GA 2026) for credential-free authentication')
param enableWorkspaceIdentity bool = false

@description('Fabric data domain for workspace tag governance (e.g., Casino, Federal-USDA)')
param fabricDomain string = ''

@description('Data classification level for workspace tag governance')
@allowed(['Public', 'Internal', 'Confidential', 'HighlyConfidential', ''])
param dataClassification string = ''

@description('Compliance framework. Selecting a framework tightens controls; it is NOT merely a tag.')
@allowed(['NIGC-MICS', 'HIPAA', 'FedRAMP', 'FISMA', '42CFR-Part2', 'PCI-DSS', 'CIPSEA', 'None', ''])
param complianceFramework string = ''

@description('Federal agency code for workspace tag governance (e.g., USDA, SBA, NOAA, EPA, DOI)')
param agencyCode string = ''

// --- Monitoring Parameters ---

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
// Compliance-Driven Control Resolution
// =============================================================================
// Selecting a compliance framework raises floors on retention, forces private
// endpoints for networking-sensitive frameworks, and enables FIPS mode on
// Key Vault. Individual parameters act as lower bounds; they can be exceeded
// but not reduced below the framework floor.

var complianceRetentionFloor = complianceFramework == 'HIPAA' ? 2190
  : complianceFramework == 'NIGC-MICS' ? 1825
  : complianceFramework == 'FedRAMP' ? 1095
  : complianceFramework == 'FISMA' ? 1095
  : complianceFramework == '42CFR-Part2' ? 2190
  : complianceFramework == 'PCI-DSS' ? 365
  : 30

var complianceForcesPrivateEndpoints = contains(
  ['HIPAA', 'FedRAMP', 'FISMA', '42CFR-Part2', 'PCI-DSS', 'NIGC-MICS', 'CIPSEA'],
  complianceFramework
)

var complianceRequiresFipsKeyVault = contains(
  ['FedRAMP', 'FISMA', 'PCI-DSS', 'NIGC-MICS', 'CIPSEA'],
  complianceFramework
)

var complianceRequiresCmk = contains(
  ['HIPAA', 'FedRAMP', 'FISMA', '42CFR-Part2', 'PCI-DSS', 'NIGC-MICS', 'CIPSEA'],
  complianceFramework
)

// Resolved effective controls (parameter max'd with compliance floor).
var effectiveRetentionDays = max(logRetentionDays, complianceRetentionFloor)
var effectivePrivateEndpoints = enablePrivateEndpoints || complianceForcesPrivateEndpoints
var effectiveKeyVaultSku = complianceRequiresFipsKeyVault ? 'premium' : 'standard'
var effectiveEnableCmk = complianceRequiresCmk

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

// Cost allocation tags
var costAllocationTags = union(
  !empty(costCenter) ? { CostCenter: costCenter } : {},
  !empty(owner) ? { Owner: owner } : {}
)

// Workspace governance tags (GA 2026)
var workspaceGovernanceTags = union(
  !empty(fabricDomain) ? { FabricDomain: fabricDomain } : {},
  !empty(dataClassification) ? { DataClassification: dataClassification } : {},
  !empty(complianceFramework) ? { ComplianceFramework: complianceFramework } : {},
  !empty(agencyCode) ? { AgencyCode: agencyCode } : {}
)

// DeployedAt intentionally omitted from resource tags so that every deployment
// doesn't produce a diff in what-if. Use the deployment name for traceability.
var defaultTags = union(tags, costAllocationTags, workspaceGovernanceTags, {
  Environment: environment
  Project: 'Microsoft Fabric POC'
  Application: 'fabric-casino-poc'
  ManagedBy: 'Bicep'
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
    retentionInDays: effectiveRetentionDays
    enablePrivateEndpoints: effectivePrivateEndpoints
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
    enablePrivateEndpoints: effectivePrivateEndpoints
    keyVaultSku: effectiveKeyVaultSku
    provisionStorageCmkKey: effectiveEnableCmk
    tags: defaultTags
  }
}

// =============================================================================
// Networking Module (deployed when any control requires private networking)
// =============================================================================

module networking 'modules/networking/vnet.bicep' = if (effectivePrivateEndpoints) {
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
    enablePrivateEndpoint: effectivePrivateEndpoints
    privateEndpointSubnetId: effectivePrivateEndpoints ? networking!.outputs.privateEndpointSubnetId : ''
    enableCmk: effectiveEnableCmk
    keyVaultKeyUri: effectiveEnableCmk ? security.outputs.storageCmkKeyUri : ''
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
    enablePrivateEndpoint: effectivePrivateEndpoints
    privateEndpointSubnetId: effectivePrivateEndpoints ? networking!.outputs.privateEndpointSubnetId : ''
    tags: defaultTags
  }
}

// =============================================================================
// Eventstream Module (Real-Time Ingestion - Optional)
// =============================================================================

module eventstream 'modules/fabric/fabric-eventstream.bicep' = if (enableEventstream) {
  name: 'eventstream-deployment'
  scope: resourceGroup
  params: {
    eventStreamName: eventStreamName
    fabricCapacityId: fabric.outputs.capacityId
    location: location
    logAnalyticsWorkspaceId: monitoring.outputs.workspaceId
    enablePrivateEndpoint: effectivePrivateEndpoints
    privateEndpointSubnetId: effectivePrivateEndpoints ? networking!.outputs.privateEndpointSubnetId : ''
    tags: defaultTags
  }
}

// =============================================================================
// Eventhouse Module (KQL Real-Time Analytics - Optional)
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
    enablePrivateEndpoint: effectivePrivateEndpoints
    privateEndpointSubnetId: effectivePrivateEndpoints ? networking!.outputs.privateEndpointSubnetId : ''
    enableDoubleEncryption: complianceRequiresFipsKeyVault
    tags: defaultTags
  }
}

// =============================================================================
// Power BI Workspace Module (BI & Direct Lake - Optional)
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
// Workspace Identity (GA 2026: credential-free authentication)
// =============================================================================

module workspaceIdentity 'modules/security/workspace-identity.bicep' = if (enableWorkspaceIdentity) {
  name: 'workspace-identity-deployment'
  scope: resourceGroup
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
// Monitoring Alerts & Budgets Module (Optional)
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
// Resource Locks (prevent accidental deletion of critical resources)
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

// Real-Time Intelligence outputs (conditional)
output eventStreamId string = enableEventstream ? eventstream!.outputs.eventStreamId : ''
output eventStreamEndpoint string = enableEventstream ? eventstream!.outputs.eventStreamEndpoint : ''

output eventHouseId string = enableEventhouse ? eventhouse!.outputs.eventHouseId : ''
output kqlEndpoint string = enableEventhouse ? eventhouse!.outputs.kqlEndpoint : ''
output eventHouseDatabaseIds array = enableEventhouse ? eventhouse!.outputs.databaseIds : []

output powerBICapacityId string = enablePowerBIWorkspace ? powerBIWorkspace!.outputs.workspaceId : ''
output powerBIPortalUrl string = enablePowerBIWorkspace ? powerBIWorkspace!.outputs.powerBiPortalUrl : ''

// Workspace Identity outputs (conditional)
output workspaceIdentityId string = enableWorkspaceIdentity ? workspaceIdentity!.outputs.identityId : ''
output workspaceIdentityPrincipalId string = enableWorkspaceIdentity ? workspaceIdentity!.outputs.principalId : ''
output workspaceIdentityClientId string = enableWorkspaceIdentity ? workspaceIdentity!.outputs.clientId : ''

// Resolved compliance controls (for assertion / traceability)
output appliedTags object = defaultTags
output effectiveRetentionDays int = effectiveRetentionDays
output effectivePrivateEndpoints bool = effectivePrivateEndpoints
output effectiveKeyVaultSku string = effectiveKeyVaultSku
output effectiveEnableCmk bool = effectiveEnableCmk

// Monitoring alert outputs (conditional)
output monitoringActionGroupId string = enableMonitoringAlerts ? monitoringAlerts!.outputs.actionGroupId : ''
output monitoringBudgetId string = enableMonitoringAlerts ? monitoringAlerts!.outputs.budgetId : ''
