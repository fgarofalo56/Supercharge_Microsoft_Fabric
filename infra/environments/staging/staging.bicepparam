using '../../main.bicep'

// =============================================================================
// Staging Environment Parameters
// =============================================================================

param environment = 'staging'
param location = 'eastus2'
param projectPrefix = 'fabricpoc'

// Production-like SKU for staging
param fabricCapacitySku = 'F64'

// Admin email for Fabric capacity alerts and notifications
param fabricAdminEmail = 'frgarofa@microsoft.com'

// Staging must test private endpoint code path like production
param enablePrivateEndpoints = true

// Medium retention for staging
param logRetentionDays = 60

param tags = {
  Environment: 'Staging'
  CostCenter: 'POC'
  Owner: 'DataPlatformTeam'
  Project: 'Fabric Casino POC'
}
