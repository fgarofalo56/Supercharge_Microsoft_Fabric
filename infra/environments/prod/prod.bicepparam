using '../../main.bicep'

// =============================================================================
// Production Environment Parameters
// =============================================================================

param environment = 'prod'
param location = 'eastus2'
param projectPrefix = 'fabricpoc'

// Full capacity for production
param fabricCapacitySku = 'F64'

// Admin email MUST be overridden at deploy time (CI secret or CLI --parameters).
// The placeholder will fail casino-floor compliance checks at deploy.
param fabricAdminEmail = readEnvironmentVariable('FABRIC_ADMIN_EMAIL', 'fabric-admin@example.com')

// Production uses private endpoints
param enablePrivateEndpoints = true

// Production log retention. Compliance floor takes over when complianceFramework
// is set (NIGC-MICS=1825d, HIPAA=2190d, FedRAMP=1095d).
param logRetentionDays = 730

// Activate compliance controls. Set to your applicable framework.
param complianceFramework = 'NIGC-MICS'

param tags = {
  Environment: 'Production'
  CostCenter: 'Casino-Analytics'
  Owner: readEnvironmentVariable('OWNER_TEAM', 'DataPlatformTeam')
  Project: 'Fabric Casino POC'
}
