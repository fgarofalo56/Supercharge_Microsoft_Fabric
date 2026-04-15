using './main.bicep'

// =============================================================================
// Default parameter values. Environment-specific files override these.
// =============================================================================

param environment = 'dev'
param location = 'eastus2'
param projectPrefix = 'fabricpoc'
param fabricCapacitySku = 'F64'

// Admin email must be provided via the FABRIC_ADMIN_EMAIL environment variable
// (set from a CI/CD secret or local .env). The placeholder fails any real
// deployment check.
param fabricAdminEmail = readEnvironmentVariable('FABRIC_ADMIN_EMAIL', 'fabric-admin@example.com')

param enablePrivateEndpoints = false
param logRetentionDays = 90

param tags = {
  CostCenter: 'POC'
  Owner: readEnvironmentVariable('OWNER_TEAM', 'DataPlatformTeam')
}
