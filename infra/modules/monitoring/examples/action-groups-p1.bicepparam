// =============================================================================
// Example: P1 Critical Action Group
// =============================================================================
// Demonstrates how to call infra/modules/monitoring/action-groups.bicep for a
// P1 (page-the-on-call) routing group. Pages PagerDuty, posts to Teams, and
// calls + SMSs the on-call rotation. Pair with high-severity metric alerts
// (capacity exhaustion, ingestion failure, security incident).
//
// Deploy:
//   az deployment group create \
//     --resource-group rg-fabricpoc-prod \
//     --template-file ../action-groups.bicep \
//     --parameters action-groups-p1.bicepparam
// =============================================================================

using '../action-groups.bicep'

param actionGroupName = 'ag-fab-p1-prod'
param displayName = 'Fabric Platform - P1 Critical'
param severityTier = 'P1'
param groupShortName = 'FabP1'
param enabled = true

param tags = {
  Environment: 'prod'
  Project: 'Microsoft Fabric POC'
  CostCenter: 'PlatformOps'
  Owner: 'fgarofalo56'
}

param emailReceivers = [
  {
    name: 'oncall-primary'
    emailAddress: readEnvironmentVariable('ONCALL_PRIMARY_EMAIL', 'oncall-primary@example.com')
    useCommonAlertSchema: true
  }
  {
    name: 'oncall-secondary'
    emailAddress: readEnvironmentVariable('ONCALL_SECONDARY_EMAIL', 'oncall-secondary@example.com')
    useCommonAlertSchema: true
  }
]

param smsReceivers = [
  {
    name: 'oncall-sms'
    countryCode: '1'
    phoneNumber: readEnvironmentVariable('ONCALL_SMS_NUMBER', '5555550100')
  }
]

param voiceReceivers = [
  {
    name: 'oncall-voice'
    countryCode: '1'
    phoneNumber: readEnvironmentVariable('ONCALL_VOICE_NUMBER', '5555550100')
  }
]

param webhookReceivers = [
  {
    name: 'pagerduty-fabric-p1'
    serviceUri: readEnvironmentVariable('PAGERDUTY_INTEGRATION_URL', 'https://events.pagerduty.com/integration/REPLACE/enqueue')
    useCommonAlertSchema: true
  }
  {
    name: 'opsgenie-fabric-p1'
    serviceUri: readEnvironmentVariable('OPSGENIE_INTEGRATION_URL', 'https://api.opsgenie.com/v1/json/azure?apiKey=REPLACE')
    useCommonAlertSchema: true
  }
]

param teamsWebhookReceivers = [
  {
    name: 'teams-fabric-incidents'
    serviceUri: readEnvironmentVariable('TEAMS_WEBHOOK_URL', 'https://example.webhook.office.com/webhookb2/REPLACE')
  }
]

param logicAppReceivers = []
param azureFunctionReceivers = []
param eventHubReceivers = []
