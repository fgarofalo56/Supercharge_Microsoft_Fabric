// =============================================================================
// Microsoft Fabric SQL Database Module (Metadata-Only)
// =============================================================================
// This module does NOT deploy any Azure resources. Fabric SQL Database is a
// workspace-level item without a dedicated ARM resource type.
//
// Purpose:
// - Documents the SQL Database configuration as Bicep parameters
// - Emits outputs consumed by main.bicep and CI/CD pipelines
// - Serves as the IaC "contract" for what the SQL Database looks like
//
// Key features documented:
// - Dynamic Data Masking (DDM) — GA
// - Customer-Managed Keys (CMK) — GA
// - Auto-replication to OneLake (always-on)
// - Data virtualization via SQL endpoint
//
// Actual SQL Database items are deployed via:
// - fabric-cicd Python library  (scripts/fabric-cicd-deploy.py)
// - Fabric REST API
// - Fabric portal UI
// =============================================================================

// =============================================================================
// Parameters (kept for documentation / contract purposes)
// =============================================================================

@description('Azure region (unused — no resources deployed)')
param location string

@description('Project prefix for resource naming')
@minLength(3)
@maxLength(10)
param projectPrefix string

@description('Environment name')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

@description('Tags (passed through to outputs)')
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

var sqlDbConfig = {
  name: databaseName
  configName: sqlDbConfigName
  environment: environment
  capacityId: capacityId
  features: {
    dynamicDataMasking: enableDDM
    customerManagedKeys: enableCMK
    keyVaultKeyUri: enableCMK ? keyVaultKeyUri : ''
    oneLakeReplication: enableOneLakeReplication
    dataVirtualization: dataVirtualizationMode
  }
  endpoints: {
    tdsEndpoint: '${sqlDbConfigName}.database.fabric.microsoft.com'
    oneLakePath: 'Tables/${databaseName}'
  }
  governance: {
    logAnalyticsWorkspaceId: logAnalyticsWorkspaceId
    managedIdentityPrincipalId: managedIdentityPrincipalId
  }
}

// =============================================================================
// OUTPUT-ONLY — No resources deployed
// Actual Fabric SQL Database items are deployed via fabric-cicd library.
// =============================================================================

@description('The SQL Database configuration name')
output databaseName string = sqlDbConfigName

@description('The expected TDS endpoint for SQL connectivity')
output tdsEndpoint string = sqlDbConfig.endpoints.tdsEndpoint

@description('Whether OneLake auto-replication is enabled')
output oneLakeReplicationEnabled bool = enableOneLakeReplication

@description('The full SQL Database configuration as JSON')
output configurationJson string = string(sqlDbConfig)

@description('Tags that would be applied to SQL Database resources')
output appliedTags object = union(tags, {
  FabricComponent: 'SQLDatabase'
  FabricCapacityId: capacityId
  DatabaseName: databaseName
  DDMEnabled: string(enableDDM)
  CMKEnabled: string(enableCMK)
})
