using './main.bicep'

// =============================================================================
// Default Parameter Values
// Override these in environment-specific files
// =============================================================================

param environment = 'dev'
param location = 'eastus2'
param projectPrefix = 'fabricpoc'
param fabricCapacitySku = 'F64'
param fabricAdminEmail = 'frgarofa@microsoft.com'
param enablePrivateEndpoints = false
param logRetentionDays = 90

param tags = {
  CostCenter: 'POC'
  Owner: 'DataPlatformTeam'
}
