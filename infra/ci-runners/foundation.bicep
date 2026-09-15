targetScope = 'resourceGroup'

@description('Region for the dedicated runner resources.')
param location string = resourceGroup().location

@description('Public IPv4 CIDR allowed to upload the App key; the vault otherwise denies access.')
param operatorIpCidr string

var suffix = uniqueString(resourceGroup().id)
var tags = {
  owner: 'fgarofalo56'
  Project: 'Supercharge_Microsoft_Fabric'
  Purpose: 'GitHub Actions runners'
  ManagedBy: 'Bicep'
  BillingOwner: 'Limitlessdata'
}

resource Registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: 'fabricci${suffix}'
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

resource Vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'fabric-ci-${suffix}'
  location: location
  tags: tags
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    enableSoftDelete: true
    enablePurgeProtection: true
    softDeleteRetentionInDays: 7
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'None'
      defaultAction: 'Deny'
      ipRules: [
        {
          value: operatorIpCidr
        }
      ]
      virtualNetworkRules: []
    }
  }
}

resource Logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'fabric-ci-logs'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    workspaceCapping: {
      dailyQuotaGb: 1
    }
  }
}

resource Environment 'Microsoft.App/managedEnvironments@2025-07-01' = {
  name: 'fabric-ci-environment'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: Logs.properties.customerId
        sharedKey: Logs.listKeys().primarySharedKey
      }
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

resource ImagePullIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'fabric-ci-image-pull'
  location: location
  tags: tags
}

resource RegistryPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(Registry.id, ImagePullIdentity.id, 'AcrPull')
  scope: Registry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: ImagePullIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

output registryName string = Registry.name
output registryServer string = Registry.properties.loginServer
output vaultName string = Vault.name
output environmentId string = Environment.id
output imagePullIdentityId string = ImagePullIdentity.id
