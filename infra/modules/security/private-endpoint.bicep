// =============================================================================
// Module: private-endpoint.bicep
// Description: Production-grade Private Endpoint module for locking down
//              Fabric / OneLake / supporting Azure resources (Key Vault,
//              Storage, SQL, Purview, Event Hub) to private network access.
//              Supports auto-approved (same-tenant) and manual (cross-tenant)
//              connections, optional Private DNS Zone Group integration,
//              Application Security Group binding, custom DNS records, and
//              CanNotDelete locks.
//
//              Referenced by:
//              - Zero-Trust blueprint (docs/best-practices/security/zero-trust-blueprint.md)
//              - Network Security best practices (docs/best-practices/network-security.md)
//              - SOC 2 controls (CC6.1 / CC6.6 — logical access + boundary protection)
//
//              NOTE: The target subnet MUST have
//              `privateEndpointNetworkPolicies = Disabled`. Private DNS Zones
//              should be centrally managed in a hub VNet for production; pass
//              their resource IDs via `privateDnsZoneIds`.
//
// Owner: fgarofalo56
// =============================================================================

// =============================================================================
// Parameters
// =============================================================================

@description('Name of the private endpoint resource (1-80 chars, alphanumerics/hyphens)')
@minLength(2)
@maxLength(80)
param privateEndpointName string

@description('Azure region for the private endpoint (must match subnet region)')
param location string = resourceGroup().location

@description('Tags to apply to the private endpoint')
param tags object = {}

@description('Resource ID of the subnet that will host the PE NIC. Subnet MUST have privateEndpointNetworkPolicies = Disabled.')
param subnetId string

@description('Resource ID of the target Azure resource being privately exposed (Key Vault, Storage, SQL, Event Hub, Purview, etc.)')
param targetResourceId string

@description('Sub-resource group IDs for the target service (e.g., ["vault"], ["sql"], ["dfs","blob"], ["namespace"], ["account"]). See Microsoft docs: https://learn.microsoft.com/azure/private-link/private-endpoint-overview#private-link-resource')
param groupIds array

@description('Optional request message displayed to the target resource owner during manual approval')
@maxLength(140)
param requestMessage string = ''

@description('When false (default), uses auto-approved privateLinkServiceConnections (same tenant). When true, uses manualPrivateLinkServiceConnections for cross-tenant scenarios requiring owner approval.')
param manualConnection bool = false

@description('Optional list of Private DNS Zone resource IDs for DNS integration. When non-empty, a privateDnsZoneGroup is created so A-records resolve through the zone. For production, reference centrally managed zones from the hub VNet.')
param privateDnsZoneIds array = []

@description('Name of the privateDnsZoneGroup child resource')
@minLength(1)
@maxLength(80)
param privateDnsZoneGroupName string = 'default'

@description('Optional override for the auto-generated network interface name. When empty, Azure assigns a default NIC name.')
param customNetworkInterfaceName string = ''

@description('Optional list of custom DNS A-record configurations. Each entry: { fqdn: string, ipAddresses: [string] }. Used when consuming services need pinned A-records (rare).')
param customDnsConfigs array = []

@description('Optional list of Application Security Group resource IDs to attach to the PE NIC. Enables ASG-based NSG rules instead of IP/CIDR rules.')
param applicationSecurityGroupIds array = []

@description('Apply a CanNotDelete lock to the private endpoint (recommended for prod). Lock is scoped to the PE only; NIC and DNS zone group are protected by the parent.')
param lockResource bool = false

// =============================================================================
// Variables
// =============================================================================

var connectionName = '${privateEndpointName}-conn'

// Governance tag merge — matches workspace-identity.bicep / log-analytics
// pattern. Provides consistent module-of-origin attribution.
var mergedTags = union(tags, {
  Module: 'private-endpoint'
  ManagedBy: 'Bicep'
  Purpose: 'PrivateLink-NetworkIsolation'
  ZeroTrustControl: 'BoundaryProtection'
})

var hasDnsZones = !empty(privateDnsZoneIds)
var hasAsgs = !empty(applicationSecurityGroupIds)
var hasCustomDns = !empty(customDnsConfigs)
var hasCustomNicName = !empty(customNetworkInterfaceName)

var asgReferences = [for asgId in applicationSecurityGroupIds: {
  id: asgId
}]

var connectionProperties = {
  privateLinkServiceId: targetResourceId
  groupIds: groupIds
  requestMessage: empty(requestMessage) ? null : requestMessage
}

// =============================================================================
// Resources
// =============================================================================

@description('Private Endpoint exposing the target resource into the supplied subnet')
resource PrivateEndpoint 'Microsoft.Network/privateEndpoints@2024-01-01' = {
  name: privateEndpointName
  location: location
  tags: mergedTags
  properties: {
    subnet: {
      id: subnetId
    }
    customNetworkInterfaceName: hasCustomNicName ? customNetworkInterfaceName : null
    applicationSecurityGroups: hasAsgs ? asgReferences : null
    customDnsConfigs: hasCustomDns ? customDnsConfigs : null
    privateLinkServiceConnections: manualConnection ? [] : [
      {
        name: connectionName
        properties: connectionProperties
      }
    ]
    manualPrivateLinkServiceConnections: manualConnection ? [
      {
        name: connectionName
        properties: connectionProperties
      }
    ] : []
  }
}

@description('Private DNS Zone Group — registers A-records on the PE NIC against the supplied zones')
resource PrivateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2024-01-01' = if (hasDnsZones) {
  parent: PrivateEndpoint
  name: privateDnsZoneGroupName
  properties: {
    privateDnsZoneConfigs: [for (zoneId, i) in privateDnsZoneIds: {
      name: 'config-${i}'
      properties: {
        privateDnsZoneId: zoneId
      }
    }]
  }
}

@description('Optional CanNotDelete lock on the private endpoint to prevent accidental teardown')
resource PrivateEndpointLock 'Microsoft.Authorization/locks@2020-05-01' = if (lockResource) {
  scope: PrivateEndpoint
  name: 'lock-${privateEndpointName}'
  properties: {
    level: 'CanNotDelete'
    notes: 'Private endpoint provides network isolation. Removing this resource may expose the target service to public network paths.'
  }
}

// =============================================================================
// Outputs
// =============================================================================

@description('Resource ID of the private endpoint')
output privateEndpointId string = PrivateEndpoint.id

@description('Name of the private endpoint')
output privateEndpointName string = PrivateEndpoint.name

@description('Resource ID of the network interface created for the private endpoint')
output nicId string = PrivateEndpoint.properties.networkInterfaces[0].id

@description('Private IP addresses assigned to the private endpoint NIC. Sourced from the auto-generated customDnsConfigs which Azure populates post-deployment.')
output privateIPAddresses array = PrivateEndpoint.properties.customDnsConfigs

@description('Resource ID of the Private DNS Zone Group (empty when DNS integration is not configured)')
output dnsZoneGroupId string = hasDnsZones ? PrivateDnsZoneGroup.id : ''
