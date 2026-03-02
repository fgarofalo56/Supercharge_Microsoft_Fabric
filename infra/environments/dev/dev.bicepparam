using '../../main.bicep'

// =============================================================================
// Development Environment Parameters
// =============================================================================

param environment = 'dev'
param location = 'eastus2'
param projectPrefix = 'fabricpoc'

// Use smaller SKU for dev to reduce costs
param fabricCapacitySku = 'F64'

// Admin email for Fabric capacity alerts and notifications
param fabricAdminEmail = 'frgarofa@microsoft.com'

// Dev environment uses public endpoints
param enablePrivateEndpoints = false

// Shorter retention for dev
param logRetentionDays = 30

param tags = {
  Environment: 'Development'
  CostCenter: 'POC'
  Owner: 'DataPlatformTeam'
  Project: 'Fabric Casino POC'
}
