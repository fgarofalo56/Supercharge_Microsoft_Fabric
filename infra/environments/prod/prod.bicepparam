using '../../main.bicep'

// =============================================================================
// Production Environment Parameters
// =============================================================================

param environment = 'prod'
param location = 'eastus2'
param projectPrefix = 'fabricpoc'

// Full capacity for production
param fabricCapacitySku = 'F64'

// Admin email for critical Fabric capacity alerts and notifications
param fabricAdminEmail = 'frgarofa@microsoft.com'

// Production should use private endpoints
param enablePrivateEndpoints = true

// Full retention for production
param logRetentionDays = 90

param tags = {
  Environment: 'Production'
  CostCenter: 'Casino-Analytics'
  Owner: 'DataPlatformTeam'
  Project: 'Fabric Casino POC'
  Compliance: 'NIGC-MICS'
}
