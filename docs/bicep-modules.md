# Bicep Modules

Auto-generated documentation for Bicep modules.

## analytics

### powerbi-workspace.bicep

**Parameters:**
- @description('Name of the Power BI Embedded capacity (acts as Fabric workspace backing resource)')
- param workspaceName string
- @description('Resource ID of the Fabric capacity to associate with')
- param fabricCapacityId string
- @description('Azure region for deployment')
- param location string
- @description('Admin members (UPNs) for workspace administration')
- param adminMembers array = []
- @description('Power BI Embedded SKU for the workspace capacity')
- param skuName string = 'A4'
- @description('Log Analytics workspace ID for diagnostics')
- param logAnalyticsWorkspaceId string = ''
- @description('Tags to apply to resources')
- param tags object = {}
- @description('The resource ID of the Power BI Embedded capacity')
- @description('The name of the Power BI Embedded capacity')
- @description('The provisioning state of the capacity')
- @description('The workspace admin members configured')
- @description('Power BI portal entry point. Navigate here to assign a workspace to this capacity.')

## databricks

### databricks-workspace.bicep

**Parameters:**
- @description('Azure region for the Databricks workspace')
- param location string
- @description('Project prefix used for resource naming (3-10 chars)')
- param projectPrefix string
- @description('Deployment environment')
- param environment string
- @description('Tags to apply to resources')
- param tags object = {}
- @description('Optional VNet integration — when supplied, the workspace is injected into the supplied VNet using "VNet injection" (Customer-managed VNet).')
- param vnetId string = ''
- @description('Public subnet name inside the supplied VNet (used only when vnetId is set).')
- param publicSubnetName string = 'snet-databricks-public'
- @description('Private subnet name inside the supplied VNet (used only when vnetId is set).')
- param privateSubnetName string = 'snet-databricks-private'
- @description('When true, public network access to the control plane is disabled (requires private link).')
- param disablePublicIp bool = false
- @description('Azure Databricks workspace — Premium SKU (required for Unity Catalog).')
- @description('Workspace resource ID — use with the Databricks REST API and Fabric mirror registration.')
- @description('Workspace URL (use for Databricks CLI configuration).')
- @description('Workspace name.')
- @description('Managed resource group created by Databricks (contains DBFS storage, compute, etc.).')

## fabric

### fabric-capacity.bicep

**Parameters:**
- @description('Name of the Fabric capacity')
- param capacityName string
- @description('Azure region for deployment')
- param location string
- @description('Fabric capacity SKU')
- param skuName string = 'F64'
- @description('Admin email address for the capacity')
- param adminEmail string
- @description('Tags to apply to resources')
- param tags object = {}
- @description('The name of the Fabric capacity')
- @description('The resource ID of the Fabric capacity')
- @description('The SKU of the Fabric capacity')
- @description('The provisioning state of the capacity')

### fabric-eventhouse.bicep

**Parameters:**
- @description('Name of the Eventhouse / Azure Data Explorer cluster')
- param eventHouseName string
- @description('Resource ID of the Fabric capacity to associate with')
- param fabricCapacityId string
- @description('Azure region for deployment')
- param location string
- @description('Database names to create within the Eventhouse')
- param databaseNames array = [
- @description('Default data retention period in days')
- param retentionDays int = 365
- @description('Hot cache period in days for frequently queried data')
- param hotCacheDays int = 31
- @description('Azure Data Explorer cluster SKU name')
- param clusterSkuName string = 'Standard_E2ads_v5'
- @description('Number of instances in the cluster')
- param clusterCapacity int = 2
- @description('Log Analytics workspace ID for diagnostics')
- param logAnalyticsWorkspaceId string = ''
- @description('Principal ID of managed identity for RBAC')
- param managedIdentityPrincipalId string = ''
- @description('Enable streaming ingestion for low-latency data')
- param enableStreamingIngestion bool = true
- @description('Enable private endpoint for the cluster')
- param enablePrivateEndpoint bool = false
- @description('Subnet ID for private endpoint')
- param privateEndpointSubnetId string = ''
- @description('Enable the destructive Purge operation. Disabled by default; enable only for environments where hard-delete is explicitly required for DSAR or retention enforcement.')
- param enablePurge bool = false
- @description('When true, turns on double encryption (FIPS 140-2 Level 2 equivalent) for the ADX cluster.')
- param enableDoubleEncryption bool = false
- @description('Principal type for the managed identity. "ServicePrincipal" is correct for both user-assigned and system-assigned MIs.')
- param managedIdentityPrincipalType string = 'ServicePrincipal'
- @description('Tags to apply to resources')
- param tags object = {}
- @description('Enable automatic cluster stop after inactivity. Disable for production workloads.')
- param enableAutoStop bool = false
- @description('The resource ID of the Azure Data Explorer cluster (Eventhouse backing resource)')
- @description('The KQL query endpoint URI')
- @description('The KQL data ingestion endpoint URI')
- @description('The name of the ADX cluster')
- @description('The resource IDs of all created databases')
- @description('The database names created within the Eventhouse')
- @description('The principal ID of the cluster system-assigned identity')

### fabric-eventstream.bicep

**Parameters:**
- @description('Name of the Eventstream / Event Hubs namespace')
- param eventStreamName string
- @description('Resource ID of the Fabric capacity to associate with')
- param fabricCapacityId string
- @description('Azure region for deployment')
- param location string
- @description('Consumer groups to create for downstream processing')
- param consumerGroups array = [
- @description('Input source configurations for the Eventstream. Each entry defines a hub (topic) name and its partition count.')
- param inputSources array = [
- @description('Routing rules mapping input sources to destinations (for documentation/tagging purposes)')
- param routingRules object = {
- @description('Log Analytics workspace ID for diagnostics')
- param logAnalyticsWorkspaceId string = ''
- @description('Enable private endpoint for the Event Hubs namespace')
- param enablePrivateEndpoint bool = false
- @description('Subnet ID for private endpoint')
- param privateEndpointSubnetId string = ''
- @description('Tags to apply to resources')
- param tags object = {}
- @description('Disable local (key-based) authentication, enforcing AAD-only. Default: true for security.')
- param disableLocalAuth bool = true
- @description('The resource ID of the Event Hubs namespace (Eventstream backing resource)')
- @description('The fully qualified namespace endpoint for Eventstream connectivity')
- @description('The name of the Event Hubs namespace')
- @description('The names of all created Event Hubs (input sources)')

## governance

### purview.bicep

**Parameters:**
- @description('Name of the Purview account')
- param purviewAccountName string
- @description('Azure region for deployment')
- param location string
- @description('Principal ID of the managed identity for RBAC')
- param managedIdentityPrincipalId string
- @description('Log Analytics workspace ID for diagnostics')
- param logAnalyticsWorkspaceId string
- @description('Enable private endpoint')
- param enablePrivateEndpoint bool = false
- @description('Subnet ID for private endpoint')
- param privateEndpointSubnetId string = ''
- @description('Tags to apply to resources')
- param tags object = {}
- @description('The name of the Purview account')
- @description('The resource ID of the Purview account')
- @description('The Purview account endpoint')
- @description('The principal ID of the Purview managed identity')

## monitoring

### action-groups.bicep

**Parameters:**
- @description('Short name for the Action Group resource (Azure resource name).')
- param actionGroupName string
- @description('Display name shown on alert notifications and in the Azure Portal.')
- param displayName string
- @description('Azure region for the Action Group. Action Groups are global; "global" is the recommended value and works in all clouds.')
- param location string = 'global'
- @description('Tags to apply to the Action Group. Merged with module-injected governance tags.')
- param tags object = {}
- @description('Severity tier driving default routing decisions in observability docs (P1=critical/page, P2=high/email+chat, P3=informational).')
- param severityTier string
- @description('Group short name shown in SMS / voice / push notifications. Azure hard limit is 12 characters; defaults to first 12 chars of actionGroupName.')
- param groupShortName string = take(actionGroupName, 12)
- @description('Whether the Action Group is enabled. Disable to silence routing without deleting the resource.')
- param enabled bool = true
- @description('Email receivers. Each item: { name: string, emailAddress: string, useCommonAlertSchema: bool }.')
- param emailReceivers array = []
- @description('SMS receivers. Each item: { name: string, countryCode: string, phoneNumber: string }.')
- param smsReceivers array = []
- @description('Voice (phone call) receivers. Each item: { name: string, countryCode: string, phoneNumber: string }.')
- param voiceReceivers array = []
- @description('Generic webhook receivers (PagerDuty / Opsgenie / custom). Each item: { name: string, serviceUri: string, useCommonAlertSchema: bool, useAadAuth: bool (optional), objectId: string (optional), identifierUri: string (optional), tenantId: string (optional) }.')
- param webhookReceivers array = []
- @description('Logic App receivers. Each item: { name: string, resourceId: string, callbackUrl: string, useCommonAlertSchema: bool }.')
- param logicAppReceivers array = []
- @description('Microsoft Teams receivers - implemented as incoming-webhook receivers under the hood. Each item: { name: string, serviceUri: string }.')
- param teamsWebhookReceivers array = []
- @description('Azure Function receivers (ITSM bridges, ServiceNow connectors, etc.). Each item: { name: string, functionAppResourceId: string, functionName: string, httpTriggerUrl: string, useCommonAlertSchema: bool }.')
- param azureFunctionReceivers array = []
- @description('Event Hub receivers for SIEM / centralized log forwarding. Each item: { name: string, eventHubNameSpace: string, eventHubName: string, subscriptionId: string, tenantId: string (optional), useCommonAlertSchema: bool }.')
- param eventHubReceivers array = []
- @description('Azure Monitor Action Group routing Fabric platform alerts to one or more notification channels.')
- @description('Resource ID of the Action Group. Reference this from metric alerts, scheduled query rules, and budgets.')
- @description('Name of the Action Group resource.')
- @description('Group short name surfaced in SMS / voice / mobile push notifications (12-char max).')
- @description('Severity tier this Action Group is bound to (P1/P2/P3) - matches observability-stack routing matrix.')
- @description('Total count of receivers configured across all channels (useful for what-if assertions).')

### alerts-and-budgets.bicep

**Parameters:**
- @description('Azure region for deployment')
- param location string = resourceGroup().location
- @description('Log Analytics workspace ID for alert queries')
- param logAnalyticsWorkspaceId string
- @description('Enable capacity utilization alerts')
- param enableCapacityAlerts bool = true
- @description('Capacity utilization threshold (percentage) to trigger alert')
- param capacityThresholdPercent int = 80
- @description('Enable budget alerts for cost management')
- param enableBudgetAlerts bool = true
- @description('Monthly budget amount in USD')
- param monthlyBudgetAmount int = 10000
- @description('Budget alert thresholds (percentages)')
- param budgetThresholds array = [
- @description('Action group resource ID for alert notifications (optional)')
- param alertActionGroupId string = ''
- @description('Email addresses for alert notifications')
- param alertEmailRecipients array = []
- @description('Enable webhook notifications')
- param enableWebhook bool = false
- @description('Webhook URL for alert notifications')
- param webhookUrl string = ''
- @description('Fabric capacity resource ID (for metric alerts)')
- param fabricCapacityResourceId string = ''
- @description('Tags to apply to resources')
- param tags object = {}
- @description('Alert severity (0=Critical, 1=Error, 2=Warning, 3=Info, 4=Verbose)')
- param alertSeverity int = 2
- @description('Budget start date in yyyy-MM-dd format (defaults to first of current month)')
- param budgetStartDate string = ''
- @description('Deployment timestamp for budget calculation (auto-generated)')
- param deployedAt string = utcNow()
- @description('The action group resource ID')
- @description('The capacity alert rule resource ID')
- @description('The throttling alert rule resource ID')
- @description('The budget resource ID')
- @description('The long-running job alert resource ID')
- @description('Tags applied to monitoring resources')

### log-analytics-workspace.bicep

**Parameters:**
- @description('Name of the Log Analytics workspace. Must be globally unique within the resource group and 4-63 characters.')
- param workspaceName string
- @description('Azure region for deployment. Defaults to the resource group location.')
- param location string = resourceGroup().location
- @description('Tags applied to all resources created by this module.')
- param tags object = {}
- @description('Workspace SKU. PerGB2018 is the standard pay-as-you-go tier; CapacityReservation provides committed-tier discounts.')
- param sku string = 'PerGB2018'
- @description('Capacity reservation level in GB/day. Required only when sku=CapacityReservation.')
- param capacityReservationLevel int = 100
- @description('Workspace-level retention in days. Compliance floors: FedRAMP=1095, HIPAA/NIGC-MICS=2190.')
- param retentionInDays int = 90
- @description('Daily ingestion cap in GB. Use -1 for unlimited (no cap). Recommended: cap non-prod environments to control cost.')
- param dailyQuotaGb int = -1
- @description('Per-table retention overrides. Each item: { tableName, retentionInDays, totalRetentionInDays }. totalRetentionInDays >= retentionInDays and supports up to 4383 days for archive tier.')
- param tableRetentionOverrides array = []
- @description('Public network access for ingestion endpoint. Set Disabled when private endpoints are used.')
- param publicNetworkAccessForIngestion string = 'Enabled'
- @description('Public network access for query endpoint. Set Disabled when private endpoints are used.')
- param publicNetworkAccessForQuery string = 'Enabled'
- @description('Optional Storage Account resource ID for long-term log archival. When supplied, a linkedStorageAccount of type CustomLogs is created.')
- param archiveStorageAccountId string = ''
- @description('Optional Key Vault resource ID for customer-managed encryption keys (CMK). All three CMK params must be supplied together.')
- param cmkKeyVaultId string = ''
- @description('Optional Key Vault key name for CMK. Required when cmkKeyVaultId is provided.')
- param cmkKeyName string = ''
- @description('Optional Key Vault key version for CMK. Use empty string to bind to the latest version.')
- param cmkKeyVersion string = ''
- @description('Central Log Analytics workspace for Fabric diagnostic settings, alerts, and runbook KQL.')
- @description('Per-table retention/archive overrides for tables that need different policies than the workspace default (e.g., AuditLogs, SigninLogs, AzureDiagnostics).')
- @description('Linked Storage Account for long-term log archival (NIGC-MICS / HIPAA / FedRAMP retention floors).')
- @description('Customer-managed key binding for the workspace. Requires the workspace identity to have Key Vault Crypto User on the supplied vault.')
- @description('Resource ID of the Log Analytics workspace. Bind to diagnosticSettings.workspaceId.')
- @description('Name of the Log Analytics workspace.')
- @description('Customer ID (workspace GUID) used by agents and diagnostic-setting bindings.')
- @description('Effective workspace retention in days (echoed for assertions).')
- @description('Number of per-table retention overrides applied.')
- @description('True when long-term archive storage is linked.')
- @description('True when customer-managed key encryption is bound.')

### log-analytics.bicep

**Parameters:**
- @description('Name of the Log Analytics workspace')
- param name string
- @description('Azure region for deployment')
- param location string
- @description('Retention period in days. HIPAA/NIGC MICS workloads should configure >= 2190 days (6 yrs).')
- param retentionInDays int = 90
- @description('When true, disables public network access (for FedRAMP, HIPAA, private-network deployments).')
- param enablePrivateEndpoints bool = false
- @description('Daily ingestion cap in GB. Set 0 for unlimited.')
- param dailyQuotaGb int = 10
- @description('Tags to apply to resources')
- param tags object = {}
- @description('Effective retention in days (echoed for reporting/assertions).')
- @description('The resource ID of the Log Analytics workspace')
- @description('The name of the Log Analytics workspace')
- @description('The customer ID of the Log Analytics workspace')

## networking

### private-endpoint.bicep

**Parameters:**
- @description('Name of the private endpoint resource')
- param name string
- @description('Azure region for deployment')
- param location string
- @description('Tags to apply to all resources')
- param tags object = {}
- @description('Resource ID of the subnet where the private endpoint NIC will be placed')
- param subnetId string
- @description('Resource ID of the service to connect to via Private Link')
- param privateLinkServiceId string
- @description('Private Link sub-resource group IDs (e.g., [\'vault\'], [\'account\'], [\'cluster\'], [\'namespace\'], [\'dfs\'])')
- param groupIds array
- @description('Private DNS zone names to create and link (e.g., [\'privatelink.vaultcore.azure.net\'])')
- param dnsZoneNames array
- @description('The resource ID of the private endpoint')
- @description('The resource IDs of the created Private DNS Zones')

### vnet.bicep

**Parameters:**
- @description('Name of the Virtual Network')
- param vnetName string
- @description('Azure region for deployment')
- param location string
- @description('Address space for the VNet')
- param addressSpace string = '10.0.0.0/16'
- @description('Tags to apply to resources')
- param tags object = {}
- @description('The resource ID of the VNet')
- @description('The name of the VNet')
- @description('The Fabric subnet ID')
- @description('The Private Endpoint subnet ID')
- @description('The Management subnet ID')

## security

### key-vault.bicep

**Parameters:**
- @description('Azure region for the Key Vault')
- param location string
- @description('Project prefix used for naming (3-10 chars)')
- param projectPrefix string
- @description('Deployment environment')
- param environment string
- @description('Tags to apply')
- param tags object = {}
- @description('Tenant ID — defaults to the subscription tenant.')
- param tenantId string = subscription().tenantId
- @description('Enable purge protection (cannot be disabled once enabled).')
- param enablePurgeProtection bool = true
- @description('Soft-delete retention in days (7-90).')
- param softDeleteRetentionDays int = 90
- @description('Disable public network access (requires private endpoint).')
- param disablePublicAccess bool = false
- @description('Optional Log Analytics workspace ID for diagnostics. Empty string skips diag setup.')
- param logAnalyticsWorkspaceId string = ''
- @description('Azure Key Vault with RBAC authorization.')
- @description('Diagnostic settings — only deployed when logAnalyticsWorkspaceId is supplied.')
- @description('Key Vault resource ID.')
- @description('Key Vault name.')
- @description('Key Vault DNS URI.')

### private-endpoint.bicep

**Parameters:**
- @description('Name of the private endpoint resource (1-80 chars, alphanumerics/hyphens)')
- param privateEndpointName string
- @description('Azure region for the private endpoint (must match subnet region)')
- param location string = resourceGroup().location
- @description('Tags to apply to the private endpoint')
- param tags object = {}
- @description('Resource ID of the subnet that will host the PE NIC. Subnet MUST have privateEndpointNetworkPolicies = Disabled.')
- param subnetId string
- @description('Resource ID of the target Azure resource being privately exposed (Key Vault, Storage, SQL, Event Hub, Purview, etc.)')
- param targetResourceId string
- @description('Sub-resource group IDs for the target service (e.g., ["vault"], ["sql"], ["dfs","blob"], ["namespace"], ["account"]). See Microsoft docs: https://learn.microsoft.com/azure/private-link/private-endpoint-overview#private-link-resource')
- param groupIds array
- @description('Optional request message displayed to the target resource owner during manual approval')
- param requestMessage string = ''
- @description('When false (default), uses auto-approved privateLinkServiceConnections (same tenant). When true, uses manualPrivateLinkServiceConnections for cross-tenant scenarios requiring owner approval.')
- param manualConnection bool = false
- @description('Optional list of Private DNS Zone resource IDs for DNS integration. When non-empty, a privateDnsZoneGroup is created so A-records resolve through the zone. For production, reference centrally managed zones from the hub VNet.')
- param privateDnsZoneIds array = []
- @description('Name of the privateDnsZoneGroup child resource')
- param privateDnsZoneGroupName string = 'default'
- @description('Optional override for the auto-generated network interface name. When empty, Azure assigns a default NIC name.')
- param customNetworkInterfaceName string = ''
- @description('Optional list of custom DNS A-record configurations. Each entry: { fqdn: string, ipAddresses: [string] }. Used when consuming services need pinned A-records (rare).')
- param customDnsConfigs array = []
- @description('Optional list of Application Security Group resource IDs to attach to the PE NIC. Enables ASG-based NSG rules instead of IP/CIDR rules.')
- param applicationSecurityGroupIds array = []
- @description('Apply a CanNotDelete lock to the private endpoint (recommended for prod). Lock is scoped to the PE only; NIC and DNS zone group are protected by the parent.')
- param lockResource bool = false
- @description('Private Endpoint exposing the target resource into the supplied subnet')
- @description('Private DNS Zone Group — registers A-records on the PE NIC against the supplied zones')
- @description('Optional CanNotDelete lock on the private endpoint to prevent accidental teardown')
- @description('Resource ID of the private endpoint')
- @description('Name of the private endpoint')
- @description('Resource ID of the network interface created for the private endpoint')
- @description('Private IP addresses assigned to the private endpoint NIC. Sourced from the auto-generated customDnsConfigs which Azure populates post-deployment.')
- @description('Resource ID of the Private DNS Zone Group (empty when DNS integration is not configured)')

### resource-locks.bicep

**Parameters:**
- @description('Name of the Key Vault resource to lock')
- param keyVaultName string
- @description('Name of the Storage Account resource to lock')
- param storageAccountName string
- @description('Name of the Fabric Capacity resource to lock')
- param fabricCapacityName string
- @description('Name of the Log Analytics Workspace resource to lock')
- param logAnalyticsName string
- @description('Name of the Purview Account resource to lock')
- param purviewAccountName string

### security.bicep

**Parameters:**
- @description('Name of the Key Vault')
- param keyVaultName string
- @description('Name of the Managed Identity')
- param managedIdentityName string
- @description('Azure region for deployment')
- param location string
- @description('Log Analytics workspace ID for diagnostics')
- param logAnalyticsWorkspaceId string
- @description('Tags to apply to resources')
- param tags object = {}
- @description('Enable private endpoints - restricts public network access when true')
- param enablePrivateEndpoints bool = false
- @description('Subnet ID for private endpoint')
- param privateEndpointSubnetId string = ''
- @description('Key Vault SKU. `premium` is required for HSM-backed keys (FedRAMP, PCI-DSS).')
- param keyVaultSku string = 'standard'
- @description('When true, provisions a CMK key inside this Key Vault for storage encryption and outputs its key URI.')
- param provisionStorageCmkKey bool = false
- @description('The name of the Key Vault')
- @description('The resource ID of the Key Vault')
- @description('The URI of the Key Vault')
- @description('The resource ID of the Managed Identity')
- @description('The principal ID of the Managed Identity')
- @description('The client ID of the Managed Identity')
- @description('Unversioned key URI for the storage CMK key (empty when not provisioned).')

### workspace-identity.bicep

**Parameters:**
- @description('Azure region for the managed identity resource')
- param location string
- @description('Project prefix for resource naming (3-10 characters)')
- param projectPrefix string
- @description('Deployment environment')
- param environment string
- @description('Tags to apply to resources')
- param tags object = {}
- @description('Enable Key Vault Secrets User role assignment for the workspace identity')
- param enableKeyVaultAccess bool = true
- @description('Key Vault resource ID for role assignment (required when enableKeyVaultAccess is true)')
- param keyVaultId string = ''
- @description('Enable Storage Blob Data Contributor role assignment')
- param enableStorageAccess bool = true
- @description('Storage account resource ID for role assignment (required when enableStorageAccess is true)')
- param storageAccountId string = ''
- @description('Enable Purview Data Curator role assignment')
- param enablePurviewAccess bool = false
- @description('Purview account resource ID for role assignment (required when enablePurviewAccess is true)')
- param purviewAccountId string = ''
- @description('User-assigned managed identity for Fabric workspace')
- @description('Key Vault Secrets User role for workspace identity')
- @description('Storage Blob Data Contributor role for workspace identity')
- @description('Purview Data Curator role for workspace identity')
- @description('Resource ID of the workspace managed identity')
- @description('Principal ID (Object ID) of the workspace managed identity')
- @description('Client ID of the workspace managed identity')
- @description('Name of the workspace managed identity')

## storage

### storage-account.bicep

**Parameters:**
- @description('Name of the storage account')
- param storageAccountName string
- @description('Azure region for deployment')
- param location string
- @description('Log Analytics workspace ID for diagnostics')
- param logAnalyticsWorkspaceId string
- @description('Principal ID of the managed identity for RBAC')
- param managedIdentityPrincipalId string
- @description('Enable private endpoint')
- param enablePrivateEndpoint bool = false
- @description('Subnet ID for private endpoint')
- param privateEndpointSubnetId string = ''
- @description('Tags to apply to resources')
- param tags object = {}
- @description('Enable Customer-Managed Keys for storage encryption')
- param enableCmk bool = false
- @description('Key Vault key URI for CMK encryption (required when enableCmk is true). Format: https://<vault>.vault.azure.net/keys/<keyname>[/<version>]')
- param keyVaultKeyUri string = ''
- @description('User-assigned managed identity resource ID for Key Vault access (required when enableCmk is true)')
- param keyVaultIdentityId string = ''
- @description('The name of the storage account')
- @description('The resource ID of the storage account')
- @description('The DFS endpoint for ADLS Gen2')
- @description('The blob endpoint')

