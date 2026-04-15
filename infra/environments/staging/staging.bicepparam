using '../../main.bicep'

// =============================================================================
// Staging Environment Parameters
// =============================================================================

param environment = 'staging'
param location = 'eastus2'
param projectPrefix = 'fabricpoc'

// Production-like SKU for staging
param fabricCapacitySku = 'F64'

// Admin email must be overridden at deploy time (CI secret or CLI --parameters)
param fabricAdminEmail = readEnvironmentVariable('FABRIC_ADMIN_EMAIL', 'fabric-admin@example.com')

// Staging exercises the private-endpoint code path like production
param enablePrivateEndpoints = true

// Medium retention for staging
param logRetentionDays = 60

param tags = {
  Environment: 'Staging'
  CostCenter: 'POC'
  Owner: readEnvironmentVariable('OWNER_TEAM', 'DataPlatformTeam')
  Project: 'Fabric Casino POC'
}
