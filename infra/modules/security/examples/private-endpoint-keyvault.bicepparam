// =============================================================================
// Example: Private Endpoint for Azure Key Vault
// =============================================================================
// Locks down the Key Vault holding workload secrets to private network access
// only. Includes a CanNotDelete lock to prevent accidental teardown — secrets
// store is treated as Tier-0 infrastructure.
//
// Prereqs:
//   - Subnet with privateEndpointNetworkPolicies = Disabled
//   - Private DNS Zone for privatelink.vaultcore.azure.net
//   - Key Vault with publicNetworkAccess = Disabled
//
// Usage:
//   az deployment group create \
//     --resource-group rg-fabricpoc-prod \
//     --template-file ../private-endpoint.bicep \
//     --parameters private-endpoint-keyvault.bicepparam
// =============================================================================

using '../private-endpoint.bicep'

param privateEndpointName = 'pe-fabricpoc-kv-prod'
param location = 'eastus2'

param subnetId = readEnvironmentVariable(
  'PE_SUBNET_ID',
  '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-network-hub/providers/Microsoft.Network/virtualNetworks/vnet-hub-prod/subnets/snet-private-endpoints'
)

param targetResourceId = readEnvironmentVariable(
  'KEYVAULT_ID',
  '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-fabricpoc-prod/providers/Microsoft.KeyVault/vaults/kv-fabricpoc-prod'
)

// Key Vault exposes a single 'vault' sub-resource
param groupIds = [
  'vault'
]

param privateDnsZoneIds = [
  readEnvironmentVariable(
    'DNS_ZONE_KV_ID',
    '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg-network-hub/providers/Microsoft.Network/privateDnsZones/privatelink.vaultcore.azure.net'
  )
]

param manualConnection = false

// Tier-0 secrets — protect from accidental deletion
param lockResource = true

param tags = {
  Environment: 'prod'
  Workload: 'Fabric-Secrets'
  CostCenter: 'POC'
  DataClassification: 'Restricted'
  ComplianceScope: 'SOC2-CC6.1'
  Tier: 'Tier-0'
}
