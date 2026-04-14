// =============================================================================
// Microsoft Fabric SQL Database Module
// =============================================================================
// Deploys configuration for Fabric SQL Database (GA Feb 2026) -- an OLTP
// workload inside Fabric with auto-replication to OneLake as Delta tables.
//
// Since Fabric SQL Database is a workspace-level item without a dedicated ARM
// resource type, this module provisions metadata and tagging for governance,
// along with supporting Azure infrastructure (Key Vault for CMK, diagnostics).
//
// Key features supported:
// - Dynamic Data Masking (DDM) -- GA
// - Customer-Managed Keys (CMK) -- GA
// - Auto-replication to OneLake (always-on)
// - Data virtualization via SQL endpoint
//
// The actual SQL Database item is created via:
// - Fabric portal / workspace UI
// - fabric-cicd Python library (CI/CD pipeline)
// - Fabric REST API (programmatic creation)
// =============================================================================

// =============================================================================
// Parameters
// =============================================================================

@description('Azure region for deployment')
param location string

@description('Project prefix for resource naming')
@minLength(3)
@maxLength(10)
param projectPrefix string

@description('Environment name')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Tags to apply to resources')
param tags object = {}

@description('SQL Database display name')
param databaseName string = 'fabric-sqldb'

@description('Resource ID of the Fabric capacity to associate with')
param capacityId string = ''

@description('Enable Dynamic Data Masking (DDM) configuration tracking')
param enableDDM bool = true

@description('Enable Customer-Managed Keys (CMK) for encryption at rest')
param enableCMK bool = false

@description('Key Vault key URI for CMK (required when enableCMK = true)')
param keyVaultKeyUri string = ''

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string = ''

@description('Managed Identity principal ID for RBAC assignments')
param managedIdentityPrincipalId string = ''

@description('Enable auto-replication to OneLake (always true for Fabric SQL DB)')
param enableOneLakeReplication bool = true

@description('Data virtualization mode')
@allowed(['ReadOnly', 'ReadWrite', 'Disabled'])
param dataVirtualizationMode string = 'ReadOnly'

// =============================================================================
// Variables
// =============================================================================

var sqlDbConfigName = '${projectPrefix}-sqldb-${environment}'

var sqlDbTags = union(tags, {
  FabricComponent: 'SQLDatabase'
  FabricCapacityId: capacityId
  DatabaseName: databaseName
  DDMEnabled: string(enableDDM)
  CMKEnabled: string(enableCMK)
  OneLakeReplication: string(enableOneLakeReplication)
  DataVirtualization: dataVirtualizationMode
})

// SQL Database configuration for downstream automation
var sqlDbConfig = {
  name: databaseName
  environment: environment
  features: {
    dynamicDataMasking: enableDDM
    customerManagedKeys: enableCMK
    oneLakeReplication: enableOneLakeReplication
    dataVirtualization: dataVirtualizationMode
  }
  endpoints: {
    tdsEndpoint: '${sqlDbConfigName}.database.fabric.microsoft.com'
    oneLakePath: 'Tables/${databaseName}'
  }
}

// =============================================================================
// SQL Database Configuration Metadata
// =============================================================================

resource sqlDbMetadata 'Microsoft.Resources/deploymentScripts@2023-08-01' = {
  name: 'sqldb-config-${sqlDbConfigName}'
  location: location
  tags: sqlDbTags
  kind: 'AzurePowerShell'
  properties: {
    azPowerShellVersion: '9.7'
    retentionInterval: 'P1D'
    scriptContent: '''
      $config = @{
        databaseName = $env:DATABASE_NAME
        environment = $env:ENVIRONMENT
        ddmEnabled = $env:DDM_ENABLED
        cmkEnabled = $env:CMK_ENABLED
        oneLakeReplication = $env:ONELAKE_REPLICATION
        dataVirtualization = $env:DATA_VIRTUALIZATION
        timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
      }
      $DeploymentScriptOutputs = @{
        configuration = ($config | ConvertTo-Json -Compress)
      }
    '''
    environmentVariables: [
      { name: 'DATABASE_NAME', value: databaseName }
      { name: 'ENVIRONMENT', value: environment }
      { name: 'DDM_ENABLED', value: string(enableDDM) }
      { name: 'CMK_ENABLED', value: string(enableCMK) }
      { name: 'ONELAKE_REPLICATION', value: string(enableOneLakeReplication) }
      { name: 'DATA_VIRTUALIZATION', value: dataVirtualizationMode }
    ]
    timeout: 'PT5M'
    cleanupPreference: 'OnSuccess'
  }
}

// =============================================================================
// CMK Key Vault Access Policy (conditional)
// =============================================================================
// When CMK is enabled, the Fabric workspace identity needs access to the
// Key Vault key used for encryption. This is documented here for reference;
// the actual Key Vault access policy is managed in the security module.
// =============================================================================

// =============================================================================
// Outputs
// =============================================================================

@description('The SQL Database configuration name')
output databaseName string = sqlDbConfigName

@description('The expected TDS endpoint for SQL connectivity')
output tdsEndpoint string = sqlDbConfig.endpoints.tdsEndpoint

@description('Whether OneLake auto-replication is enabled')
output oneLakeReplicationEnabled bool = enableOneLakeReplication

@description('The SQL Database configuration as JSON')
output sqlDbConfiguration string = string(sqlDbConfig)

@description('The deployment script resource ID')
output metadataResourceId string = sqlDbMetadata.id

@description('Tags applied to SQL Database resources')
output appliedTags object = sqlDbTags
