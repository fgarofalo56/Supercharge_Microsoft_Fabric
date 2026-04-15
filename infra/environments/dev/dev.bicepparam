using '../../main.bicep'

// =============================================================================
// Development Environment Parameters
// =============================================================================
// NOTE: fabricAdminEmail must be sourced from a GitHub Environment secret or
// az deployment override; never commit a real admin email here.

param environment = 'dev'
param location = 'eastus2'
param projectPrefix = 'fabricpoc'

// Smaller SKU for dev to keep costs low (~$250/mo on F2 vs ~$8K/mo on F64)
param fabricCapacitySku = 'F2'

// Admin email must be overridden at deploy time (CI secret or CLI --parameters)
param fabricAdminEmail = readEnvironmentVariable('FABRIC_ADMIN_EMAIL', 'fabric-admin@example.com')

// Dev uses public endpoints for developer accessibility
param enablePrivateEndpoints = false

// Shorter retention for dev
param logRetentionDays = 30

param tags = {
  Environment: 'Development'
  CostCenter: 'POC'
  Owner: readEnvironmentVariable('OWNER_TEAM', 'DataPlatformTeam')
  Project: 'Fabric Casino POC'
}
