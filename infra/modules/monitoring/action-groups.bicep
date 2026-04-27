// =============================================================================
// Module: action-groups.bicep
// Description: Deploys an Azure Monitor Action Group that routes Fabric
//              platform alerts to email, SMS, voice, webhook (PagerDuty /
//              Opsgenie), Logic App, Microsoft Teams (incoming webhook),
//              Azure Function (ITSM bridge), and Event Hub (SIEM forwarding).
//
// Phase 14 Wave 1 (feature 1.12) - referenced by:
//   - docs/best-practices/operations/observability-stack.md
//   - docs/best-practices/operations/oncall-rotation-handbook.md
//
// Usage:
//   module pagerP1 'modules/monitoring/action-groups.bicep' = {
//     name: 'ag-p1-deployment'
//     params: {
//       actionGroupName: 'agFabP1'             // <= 12 chars
//       displayName: 'Fabric P1 Critical'
//       severityTier: 'P1'
//       emailReceivers: [...]
//       webhookReceivers: [...]
//       teamsWebhookReceivers: [...]
//       tags: defaultTags
//     }
//   }
//
// Owner: fgarofalo56
// =============================================================================

// =============================================================================
// Parameters
// =============================================================================

@description('Short name for the Action Group resource (Azure resource name).')
@minLength(1)
@maxLength(260)
param actionGroupName string

@description('Display name shown on alert notifications and in the Azure Portal.')
@minLength(1)
@maxLength(260)
param displayName string

@description('Azure region for the Action Group. Action Groups are global; "global" is the recommended value and works in all clouds.')
param location string = 'global'

@description('Tags to apply to the Action Group. Merged with module-injected governance tags.')
param tags object = {}

@description('Severity tier driving default routing decisions in observability docs (P1=critical/page, P2=high/email+chat, P3=informational).')
@allowed([
  'P1'
  'P2'
  'P3'
])
param severityTier string

@description('Group short name shown in SMS / voice / push notifications. Azure hard limit is 12 characters; defaults to first 12 chars of actionGroupName.')
@maxLength(12)
param groupShortName string = take(actionGroupName, 12)

@description('Whether the Action Group is enabled. Disable to silence routing without deleting the resource.')
param enabled bool = true

@description('Email receivers. Each item: { name: string, emailAddress: string, useCommonAlertSchema: bool }.')
param emailReceivers array = []

@description('SMS receivers. Each item: { name: string, countryCode: string, phoneNumber: string }.')
param smsReceivers array = []

@description('Voice (phone call) receivers. Each item: { name: string, countryCode: string, phoneNumber: string }.')
param voiceReceivers array = []

@description('Generic webhook receivers (PagerDuty / Opsgenie / custom). Each item: { name: string, serviceUri: string, useCommonAlertSchema: bool, useAadAuth: bool (optional), objectId: string (optional), identifierUri: string (optional), tenantId: string (optional) }.')
param webhookReceivers array = []

@description('Logic App receivers. Each item: { name: string, resourceId: string, callbackUrl: string, useCommonAlertSchema: bool }.')
param logicAppReceivers array = []

@description('Microsoft Teams receivers - implemented as incoming-webhook receivers under the hood. Each item: { name: string, serviceUri: string }.')
param teamsWebhookReceivers array = []

@description('Azure Function receivers (ITSM bridges, ServiceNow connectors, etc.). Each item: { name: string, functionAppResourceId: string, functionName: string, httpTriggerUrl: string, useCommonAlertSchema: bool }.')
param azureFunctionReceivers array = []

@description('Event Hub receivers for SIEM / centralized log forwarding. Each item: { name: string, eventHubNameSpace: string, eventHubName: string, subscriptionId: string, tenantId: string (optional), useCommonAlertSchema: bool }.')
param eventHubReceivers array = []

// =============================================================================
// Variables
// =============================================================================

// Normalize webhook receivers - Teams is a webhook in Azure Monitor terms.
// The portal exposes a "Secure webhook" + "Webhook" split; we always emit a
// regular webhook with useCommonAlertSchema=true so adaptive cards can be
// rendered downstream by Logic Apps / Teams workflow connectors.
var teamsAsWebhooks = [for t in teamsWebhookReceivers: {
  name: t.name
  serviceUri: t.serviceUri
  useCommonAlertSchema: true
}]

var allWebhookReceivers = concat(webhookReceivers, teamsAsWebhooks)

// Governance tags merged with caller-supplied tags. Mirrors the
// workspace-identity.bicep pattern (Purpose + Feature tags).
var moduleTags = union(tags, {
  Purpose: 'Fabric Alert Routing'
  SeverityTier: severityTier
  ManagedBy: 'Bicep'
  Module: 'action-groups'
})

// =============================================================================
// Resources
// =============================================================================

@description('Azure Monitor Action Group routing Fabric platform alerts to one or more notification channels.')
resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: actionGroupName
  location: location
  tags: moduleTags
  properties: {
    groupShortName: groupShortName
    enabled: enabled
    emailReceivers: [for e in emailReceivers: {
      name: e.name
      emailAddress: e.emailAddress
      useCommonAlertSchema: contains(e, 'useCommonAlertSchema') ? e.useCommonAlertSchema : true
    }]
    smsReceivers: [for s in smsReceivers: {
      name: s.name
      countryCode: s.countryCode
      phoneNumber: s.phoneNumber
    }]
    voiceReceivers: [for v in voiceReceivers: {
      name: v.name
      countryCode: v.countryCode
      phoneNumber: v.phoneNumber
    }]
    webhookReceivers: [for w in allWebhookReceivers: {
      name: w.name
      serviceUri: w.serviceUri
      useCommonAlertSchema: contains(w, 'useCommonAlertSchema') ? w.useCommonAlertSchema : true
      useAadAuth: contains(w, 'useAadAuth') ? w.useAadAuth : false
      objectId: contains(w, 'objectId') ? w.objectId : ''
      identifierUri: contains(w, 'identifierUri') ? w.identifierUri : ''
      tenantId: contains(w, 'tenantId') ? w.tenantId : ''
    }]
    logicAppReceivers: [for l in logicAppReceivers: {
      name: l.name
      resourceId: l.resourceId
      callbackUrl: l.callbackUrl
      useCommonAlertSchema: contains(l, 'useCommonAlertSchema') ? l.useCommonAlertSchema : true
    }]
    azureFunctionReceivers: [for f in azureFunctionReceivers: {
      name: f.name
      functionAppResourceId: f.functionAppResourceId
      functionName: f.functionName
      httpTriggerUrl: f.httpTriggerUrl
      useCommonAlertSchema: contains(f, 'useCommonAlertSchema') ? f.useCommonAlertSchema : true
    }]
    eventHubReceivers: [for h in eventHubReceivers: {
      name: h.name
      eventHubNameSpace: h.eventHubNameSpace
      eventHubName: h.eventHubName
      subscriptionId: h.subscriptionId
      tenantId: contains(h, 'tenantId') ? h.tenantId : ''
      useCommonAlertSchema: contains(h, 'useCommonAlertSchema') ? h.useCommonAlertSchema : true
    }]
  }
}

// =============================================================================
// Outputs
// =============================================================================

@description('Resource ID of the Action Group. Reference this from metric alerts, scheduled query rules, and budgets.')
output actionGroupId string = actionGroup.id

@description('Name of the Action Group resource.')
output actionGroupName string = actionGroup.name

@description('Group short name surfaced in SMS / voice / mobile push notifications (12-char max).')
output actionGroupShortName string = actionGroup.properties.groupShortName

@description('Severity tier this Action Group is bound to (P1/P2/P3) - matches observability-stack routing matrix.')
output severityTier string = severityTier

@description('Total count of receivers configured across all channels (useful for what-if assertions).')
output receiverCount int = length(emailReceivers) + length(smsReceivers) + length(voiceReceivers) + length(allWebhookReceivers) + length(logicAppReceivers) + length(azureFunctionReceivers) + length(eventHubReceivers)
