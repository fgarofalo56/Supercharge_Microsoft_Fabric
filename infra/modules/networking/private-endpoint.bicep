// =============================================================================
// Shared Private Endpoint Module
// =============================================================================
// Reusable module that creates a private endpoint with Private DNS Zone(s),
// VNet link(s), and a DNS Zone Group for automatic DNS registration.
//
// Usage example (from a calling module):
//   module pe '../../networking/private-endpoint.bicep' = if (enablePrivateEndpoint) {
//     name: 'pe-myService'
//     params: {
//       name:                  'pe-myService'
//       location:              location
//       tags:                  tags
//       subnetId:              privateEndpointSubnetId
//       privateLinkServiceId:  myService.id
//       groupIds:              ['vault']
//       dnsZoneNames:          ['privatelink.vaultcore.azure.net']
//     }
//   }
//
// NOTE: For production deployments, Private DNS Zones should be centrally
// managed in a hub VNet and linked to spoke VNets. This POC deploys them
// inline for simplicity.
// See: https://learn.microsoft.com/azure/private-link/private-endpoint-dns
// =============================================================================

// =============================================================================
// Parameters
// =============================================================================

@description('Name of the private endpoint resource')
param name string

@description('Azure region for deployment')
param location string

@description('Tags to apply to all resources')
param tags object = {}

@description('Resource ID of the subnet where the private endpoint NIC will be placed')
param subnetId string

@description('Resource ID of the service to connect to via Private Link')
param privateLinkServiceId string

@description('Private Link sub-resource group IDs (e.g., [\'vault\'], [\'account\'], [\'cluster\'], [\'namespace\'], [\'dfs\'])')
param groupIds array

@description('Private DNS zone names to create and link (e.g., [\'privatelink.vaultcore.azure.net\'])')
param dnsZoneNames array

// =============================================================================
// Variables
// =============================================================================

// Extract VNet ID from subnet ID for DNS zone VNet links
var vnetId = substring(subnetId, 0, lastIndexOf(subnetId, '/subnets/'))

// =============================================================================
// Private Endpoint
// =============================================================================

resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-05-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    subnet: {
      id: subnetId
    }
    privateLinkServiceConnections: [
      {
        name: '${name}-connection'
        properties: {
          privateLinkServiceId: privateLinkServiceId
          groupIds: groupIds
        }
      }
    ]
  }
}

// =============================================================================
// Private DNS Zones (one per dnsZoneName)
// =============================================================================

resource privateDnsZones 'Microsoft.Network/privateDnsZones@2020-06-01' = [
  for zoneName in dnsZoneNames: {
    name: zoneName
    location: 'global'
    tags: tags
  }
]

// =============================================================================
// VNet Links (one per DNS zone)
// =============================================================================

resource vnetLinks 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = [
  for (zoneName, i) in dnsZoneNames: {
    parent: privateDnsZones[i]
    name: 'link-${name}-${i}'
    location: 'global'
    tags: tags
    properties: {
      registrationEnabled: false
      virtualNetwork: {
        id: vnetId
      }
    }
  }
]

// =============================================================================
// DNS Zone Group (auto-registers A records on the PE)
// =============================================================================

resource dnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-05-01' = {
  parent: privateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      for (zoneName, i) in dnsZoneNames: {
        name: replace(zoneName, '.', '-')
        properties: {
          privateDnsZoneId: privateDnsZones[i].id
        }
      }
    ]
  }
}

// =============================================================================
// Outputs
// =============================================================================

@description('The resource ID of the private endpoint')
output privateEndpointId string = privateEndpoint.id

@description('The resource IDs of the created Private DNS Zones')
output dnsZoneIds array = [for (zoneName, i) in dnsZoneNames: privateDnsZones[i].id]
