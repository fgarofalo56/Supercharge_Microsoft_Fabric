// =============================================================================
// Example: Private Endpoint for OneLake / ADLS Gen2 storage
// =============================================================================
// Locks down the storage account backing OneLake / Lakehouse data to private
// network access only. ADLS Gen2 surfaces both 'dfs' (hierarchical namespace)
// and 'blob' sub-resources — both are exposed via a single PE.
//
// Prereqs:
//   - Subnet with privateEndpointNetworkPolicies = Disabled
//   - Private DNS Zones for privatelink.dfs.core.windows.net AND
//     privatelink.blob.core.windows.net (typically managed in hub VNet)
//   - Storage account firewall set to "Deny" public network access
//
// Usage:
//   az deployment group create \
//     --resource-group rg-fabricpoc-prod \
//     --template-file ../private-endpoint.bicep \
//     --parameters private-endpoint-onelake.bicepparam
// =============================================================================

using '../private-endpoint.bicep'

param privateEndpointName = 'pe-fabricpoc-onelake-prod'
param location = 'eastus2'

// Subnet ID injected via env var to avoid hardcoding tenant-specific GUIDs
param subnetId = readEnvironmentVariable(
  'PE_SUBNET_ID',
  '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-network-hub/providers/Microsoft.Network/virtualNetworks/vnet-hub-prod/subnets/snet-private-endpoints'
)

// Storage account hosting OneLake / Lakehouse data
param targetResourceId = readEnvironmentVariable(
  'ONELAKE_STORAGE_ID',
  '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-fabricpoc-prod/providers/Microsoft.Storage/storageAccounts/stfabricpocprod'
)

// ADLS Gen2 requires both sub-resources for full Lakehouse functionality
param groupIds = [
  'dfs'
  'blob'
]

// DNS zone IDs from hub VNet — both zones required for OneLake resolution
param privateDnsZoneIds = [
  readEnvironmentVariable(
    'DNS_ZONE_DFS_ID',
    '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-network-hub/providers/Microsoft.Network/privateDnsZones/privatelink.dfs.core.windows.net'
  )
  readEnvironmentVariable(
    'DNS_ZONE_BLOB_ID',
    '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-network-hub/providers/Microsoft.Network/privateDnsZones/privatelink.blob.core.windows.net'
  )
]

param manualConnection = false
param lockResource = false

param tags = {
  Environment: 'prod'
  Workload: 'Fabric-OneLake'
  CostCenter: 'POC'
  DataClassification: 'Confidential'
  ComplianceScope: 'SOC2-CC6.6'
}
