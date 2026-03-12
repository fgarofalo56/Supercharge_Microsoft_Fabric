// =============================================================================
// Microsoft Fabric Eventhouse Module
// =============================================================================
// Deploys real-time analytics infrastructure for Fabric RTI.
// Since Microsoft Fabric Eventhouse is a workspace-level KQL artifact without
// a dedicated ARM resource type, this module provisions an Azure Data Explorer
// (Kusto) cluster that mirrors the Eventhouse analytical capability. The ADX
// cluster serves as the backing compute for KQL queries, hot cache, and
// retention policies equivalent to a Fabric Eventhouse configuration.
// =============================================================================

// =============================================================================
// Parameters
// =============================================================================

@description('Name of the Eventhouse / Azure Data Explorer cluster')
param eventHouseName string

@description('Resource ID of the Fabric capacity to associate with')
param fabricCapacityId string

@description('Azure region for deployment')
param location string

@description('Database names to create within the Eventhouse')
param databaseNames array = [
  'CasinoFloorMonitoring'
  'PlayerAnalytics'
  'ComplianceRealTime'
  'SlotTelemetry'
]

@description('Default data retention period in days')
@minValue(1)
@maxValue(36500)
param retentionDays int = 365

@description('Hot cache period in days for frequently queried data')
@minValue(1)
@maxValue(365)
param hotCacheDays int = 31

@description('Azure Data Explorer cluster SKU name')
@allowed([
  'Dev(No SLA)_Standard_E2a_v4'
  'Standard_E2ads_v5'
  'Standard_E4ads_v5'
  'Standard_E8ads_v5'
  'Standard_E16ads_v5'
])
param clusterSkuName string = 'Standard_E2ads_v5'

@description('Number of instances in the cluster')
@minValue(2)
@maxValue(20)
param clusterCapacity int = 2

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string = ''

@description('Principal ID of managed identity for RBAC')
param managedIdentityPrincipalId string = ''

@description('Enable streaming ingestion for low-latency data')
param enableStreamingIngestion bool = true

@description('Enable private endpoint for the cluster')
param enablePrivateEndpoint bool = false

@description('Subnet ID for private endpoint')
param privateEndpointSubnetId string = ''

@description('Tags to apply to resources')
param tags object = {}

// =============================================================================
// Variables
// =============================================================================

var eventhouseTags = union(tags, {
  FabricComponent: 'Eventhouse'
  FabricCapacityId: fabricCapacityId
})

// Kusto Database Admin role definition ID
var kustoDatabaseAdminRoleId = 'Admin'

// =============================================================================
// Azure Data Explorer Cluster (Fabric Eventhouse backing resource)
// =============================================================================

resource adxCluster 'Microsoft.Kusto/clusters@2024-04-13' = {
  name: eventHouseName
  location: location
  tags: eventhouseTags
  sku: {
    name: clusterSkuName
    tier: 'Standard'
    capacity: clusterCapacity
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    enableStreamingIngest: enableStreamingIngestion
    enablePurge: true
    enableAutoStop: true
    enableDiskEncryption: true
    enableDoubleEncryption: false
    publicNetworkAccess: enablePrivateEndpoint ? 'Disabled' : 'Enabled'
    publicIPType: 'IPv4'
    trustedExternalTenants: []
    optimizedAutoscale: {
      version: 1
      isEnabled: true
      minimum: clusterCapacity
      maximum: clusterCapacity * 2
    }
  }
}

// =============================================================================
// KQL Databases (one per analytical domain)
// =============================================================================

resource databases 'Microsoft.Kusto/clusters/databases@2024-04-13' = [
  for dbName in databaseNames: {
    parent: adxCluster
    name: dbName
    location: location
    kind: 'ReadWrite'
    properties: {
      softDeletePeriod: 'P${retentionDays}D'
      hotCachePeriod: 'P${hotCacheDays}D'
    }
  }
]

// =============================================================================
// Ingestion Mapping Scripts (Casino domain KQL tables)
// =============================================================================
// These scripts create the target tables and ingestion mappings in the first
// database (CasinoFloorMonitoring) for Eventstream-to-Eventhouse routing.
// =============================================================================

resource slotTelemetryTable 'Microsoft.Kusto/clusters/databases/scripts@2024-04-13' = {
  parent: databases[0]
  name: 'createSlotTelemetryTable'
  properties: {
    scriptContent: '''
      .create-merge table SlotTelemetry (
        Timestamp: datetime,
        MachineId: string,
        CasinoFloor: string,
        Zone: string,
        EventType: string,
        CoinIn: decimal,
        CoinOut: decimal,
        Jackpot: decimal,
        GameType: string,
        Denomination: decimal,
        SessionId: string,
        PlayerId: string
      )

      .create-merge table SlotTelemetry ingestion json mapping 'SlotTelemetryMapping'
      ```
      [
        {"column": "Timestamp", "path": "$.timestamp", "datatype": "datetime"},
        {"column": "MachineId", "path": "$.machine_id", "datatype": "string"},
        {"column": "CasinoFloor", "path": "$.casino_floor", "datatype": "string"},
        {"column": "Zone", "path": "$.zone", "datatype": "string"},
        {"column": "EventType", "path": "$.event_type", "datatype": "string"},
        {"column": "CoinIn", "path": "$.coin_in", "datatype": "decimal"},
        {"column": "CoinOut", "path": "$.coin_out", "datatype": "decimal"},
        {"column": "Jackpot", "path": "$.jackpot", "datatype": "decimal"},
        {"column": "GameType", "path": "$.game_type", "datatype": "string"},
        {"column": "Denomination", "path": "$.denomination", "datatype": "decimal"},
        {"column": "SessionId", "path": "$.session_id", "datatype": "string"},
        {"column": "PlayerId", "path": "$.player_id", "datatype": "string"}
      ]
      ```

      .alter table SlotTelemetry policy streamingingestion enable
    '''
    continueOnErrors: false
  }
}

resource complianceAlertTable 'Microsoft.Kusto/clusters/databases/scripts@2024-04-13' = {
  parent: databases[0]
  name: 'createComplianceAlertTable'
  properties: {
    scriptContent: '''
      .create-merge table ComplianceAlerts (
        Timestamp: datetime,
        AlertType: string,
        Severity: string,
        PlayerId: string,
        TransactionId: string,
        Amount: decimal,
        ThresholdType: string,
        ThresholdValue: decimal,
        Description: string,
        Status: string
      )

      .create-merge table ComplianceAlerts ingestion json mapping 'ComplianceAlertMapping'
      ```
      [
        {"column": "Timestamp", "path": "$.timestamp", "datatype": "datetime"},
        {"column": "AlertType", "path": "$.alert_type", "datatype": "string"},
        {"column": "Severity", "path": "$.severity", "datatype": "string"},
        {"column": "PlayerId", "path": "$.player_id", "datatype": "string"},
        {"column": "TransactionId", "path": "$.transaction_id", "datatype": "string"},
        {"column": "Amount", "path": "$.amount", "datatype": "decimal"},
        {"column": "ThresholdType", "path": "$.threshold_type", "datatype": "string"},
        {"column": "ThresholdValue", "path": "$.threshold_value", "datatype": "decimal"},
        {"column": "Description", "path": "$.description", "datatype": "string"},
        {"column": "Status", "path": "$.status", "datatype": "string"}
      ]
      ```

      .alter table ComplianceAlerts policy streamingingestion enable
    '''
    continueOnErrors: false
  }
}

// =============================================================================
// RBAC - Managed Identity Database Admin
// =============================================================================

resource databasePrincipal 'Microsoft.Kusto/clusters/databases/principalAssignments@2024-04-13' = [
  for (dbName, i) in databaseNames: if (!empty(managedIdentityPrincipalId)) {
    parent: databases[i]
    name: guid(adxCluster.id, dbName, managedIdentityPrincipalId)
    properties: {
      principalId: managedIdentityPrincipalId
      role: kustoDatabaseAdminRoleId
      tenantId: subscription().tenantId
      principalType: 'App'
    }
  }
]

// =============================================================================
// Diagnostic Settings
// =============================================================================

resource adxDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(logAnalyticsWorkspaceId)) {
  name: 'eventhouse-diagnostics'
  scope: adxCluster
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
// Private Endpoint (Optional)
// =============================================================================

resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-05-01' = if (enablePrivateEndpoint) {
  name: 'pe-${eventHouseName}'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'eventhouse-connection'
        properties: {
          privateLinkServiceId: adxCluster.id
          groupIds: [
            'cluster'
          ]
        }
      }
    ]
  }
}

// =============================================================================
// Outputs
// =============================================================================

@description('The resource ID of the Azure Data Explorer cluster (Eventhouse backing resource)')
output eventHouseId string = adxCluster.id

@description('The KQL query endpoint URI')
output kqlEndpoint string = adxCluster.properties.uri

@description('The KQL data ingestion endpoint URI')
output kqlIngestionEndpoint string = adxCluster.properties.dataIngestionUri

@description('The name of the ADX cluster')
output eventHouseName string = adxCluster.name

@description('The resource IDs of all created databases')
output databaseIds array = [for (dbName, i) in databaseNames: databases[i].id]

@description('The database names created within the Eventhouse')
output databaseNamesOutput array = databaseNames

@description('The principal ID of the cluster system-assigned identity')
output clusterPrincipalId string = adxCluster.identity.principalId
