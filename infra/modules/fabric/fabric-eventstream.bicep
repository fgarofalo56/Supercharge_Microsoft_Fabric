// =============================================================================
// Microsoft Fabric Eventstream Module
// =============================================================================
// Deploys real-time event ingestion infrastructure for Fabric RTI.
// Since Microsoft Fabric Eventstream is a workspace-level artifact without a
// dedicated ARM resource type, this module provisions the underlying Azure
// Event Hubs namespace that powers Eventstream ingestion. The Event Hubs
// namespace integrates with Fabric Eventstream as a custom input source.
// =============================================================================

// =============================================================================
// Parameters
// =============================================================================

@description('Name of the Eventstream / Event Hubs namespace')
param eventStreamName string

@description('Resource ID of the Fabric capacity to associate with')
param fabricCapacityId string

@description('Azure region for deployment')
param location string

@description('Consumer groups to create for downstream processing')
param consumerGroups array = [
  'bronze-ingestion'
  'silver-transform'
  'monitoring'
]

@description('Input source configurations for the Eventstream. Each entry defines a hub (topic) name and its partition count.')
param inputSources array = [
  {
    name: 'slot-telemetry'
    partitionCount: 8
    messageRetentionInDays: 3
  }
  {
    name: 'table-events'
    partitionCount: 4
    messageRetentionInDays: 3
  }
  {
    name: 'player-activity'
    partitionCount: 4
    messageRetentionInDays: 3
  }
  {
    name: 'compliance-events'
    partitionCount: 2
    messageRetentionInDays: 7
  }
]

@description('Routing rules mapping input sources to destinations (for documentation/tagging purposes)')
param routingRules object = {
  slotTelemetry: 'bronze_slot_telemetry'
  tableEvents: 'bronze_table_events'
  playerActivity: 'bronze_player_activity'
  complianceEvents: 'bronze_compliance_events'
}

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string = ''

@description('Enable private endpoint for the Event Hubs namespace')
param enablePrivateEndpoint bool = false

@description('Subnet ID for private endpoint')
param privateEndpointSubnetId string = ''

@description('Tags to apply to resources')
param tags object = {}

// =============================================================================
// Variables
// =============================================================================

// Merge routing rules into tags for operational traceability
var routingTags = {
  FabricComponent: 'Eventstream'
  FabricCapacityId: fabricCapacityId
  RoutingRules: string(routingRules)
}
var mergedTags = union(tags, routingTags)

// =============================================================================
// Event Hubs Namespace (Fabric Eventstream backing resource)
// =============================================================================

resource eventHubNamespace 'Microsoft.EventHub/namespaces@2024-01-01' = {
  name: eventStreamName
  location: location
  tags: mergedTags
  sku: {
    name: 'Standard'
    tier: 'Standard'
    capacity: 2
  }
  properties: {
    isAutoInflateEnabled: true
    maximumThroughputUnits: 10
    kafkaEnabled: true
    publicNetworkAccess: enablePrivateEndpoint ? 'Disabled' : 'Enabled'
    minimumTlsVersion: '1.2'
    zoneRedundant: true
    disableLocalAuth: false
  }
}

// =============================================================================
// Event Hubs (one per input source / Eventstream topic)
// =============================================================================

resource eventHubs 'Microsoft.EventHub/namespaces/eventhubs@2024-01-01' = [
  for source in inputSources: {
    parent: eventHubNamespace
    name: source.name
    properties: {
      partitionCount: source.partitionCount
      messageRetentionInDays: source.messageRetentionInDays
      status: 'Active'
    }
  }
]

// =============================================================================
// Consumer Groups (applied to each Event Hub)
// =============================================================================

resource consumerGroupResources 'Microsoft.EventHub/namespaces/eventhubs/consumergroups@2024-01-01' = [
  for pair in flatten([
    for (source, sourceIdx) in inputSources: [
      for group in consumerGroups: {
        hubName: source.name
        groupName: group
        sourceIndex: sourceIdx
      }
    ]
  ]): {
    parent: eventHubs[pair.sourceIndex]
    name: pair.groupName
    properties: {
      userMetadata: 'Fabric Eventstream consumer group for ${pair.groupName} processing'
    }
  }
]

// =============================================================================
// Authorization Rules
// =============================================================================

resource sendListenRule 'Microsoft.EventHub/namespaces/authorizationRules@2024-01-01' = {
  parent: eventHubNamespace
  name: 'fabric-eventstream-rule'
  properties: {
    rights: [
      'Send'
      'Listen'
      'Manage'
    ]
  }
}

resource listenOnlyRule 'Microsoft.EventHub/namespaces/authorizationRules@2024-01-01' = {
  parent: eventHubNamespace
  name: 'fabric-readonly-rule'
  properties: {
    rights: [
      'Listen'
    ]
  }
}

// =============================================================================
// Diagnostic Settings
// =============================================================================

resource eventHubDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(logAnalyticsWorkspaceId)) {
  name: 'eventstream-diagnostics'
  scope: eventHubNamespace
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
  name: 'pe-${eventStreamName}'
  location: location
  tags: tags
  properties: {
    subnet: {
      id: privateEndpointSubnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'eventstream-connection'
        properties: {
          privateLinkServiceId: eventHubNamespace.id
          groupIds: [
            'namespace'
          ]
        }
      }
    ]
  }
}

// =============================================================================
// Outputs
// =============================================================================

@description('The resource ID of the Event Hubs namespace (Eventstream backing resource)')
output eventStreamId string = eventHubNamespace.id

@description('The fully qualified namespace endpoint for Eventstream connectivity')
output eventStreamEndpoint string = eventHubNamespace.properties.serviceBusEndpoint

@description('The name of the Event Hubs namespace')
output eventStreamName string = eventHubNamespace.name

@description('The primary connection string for Send/Listen/Manage access')
output eventStreamConnectionString string = sendListenRule.listKeys().primaryConnectionString

@description('The read-only connection string for Listen access')
output eventStreamReadOnlyConnectionString string = listenOnlyRule.listKeys().primaryConnectionString

@description('The names of all created Event Hubs (input sources)')
output eventHubNames array = [for (source, i) in inputSources: eventHubs[i].name]
