// =============================================================================
// Monitoring Alerts & Budgets Module
// =============================================================================
// Deploys Azure Monitor alert rules and budget alerts for Fabric capacity
// and resource cost governance.
//
// Features:
// - Capacity utilization alerts (CU consumption thresholds)
// - Budget alerts for cost management
// - Action groups for notification routing
// - Integration with Log Analytics for custom alert queries
//
// Usage scenarios:
// - Casino: 24/7 burst capacity monitoring with escalation
// - Federal: Shared capacity with per-agency budget tracking
// =============================================================================

// =============================================================================
// Parameters
// =============================================================================

@description('Azure region for deployment')
param location string = resourceGroup().location

@description('Log Analytics workspace ID for alert queries')
param logAnalyticsWorkspaceId string

@description('Enable capacity utilization alerts')
param enableCapacityAlerts bool = true

@description('Capacity utilization threshold (percentage) to trigger alert')
@minValue(50)
@maxValue(100)
param capacityThresholdPercent int = 80

@description('Enable budget alerts for cost management')
param enableBudgetAlerts bool = true

@description('Monthly budget amount in USD')
@minValue(100)
@maxValue(1000000)
param monthlyBudgetAmount int = 10000

@description('Budget alert thresholds (percentages)')
param budgetThresholds array = [
  { threshold: 50, contactEmails: [] }
  { threshold: 75, contactEmails: [] }
  { threshold: 90, contactEmails: [] }
  { threshold: 100, contactEmails: [] }
]

@description('Action group resource ID for alert notifications (optional)')
param alertActionGroupId string = ''

@description('Email addresses for alert notifications')
param alertEmailRecipients array = []

@description('Enable webhook notifications')
param enableWebhook bool = false

@description('Webhook URL for alert notifications')
param webhookUrl string = ''

@description('Fabric capacity resource ID (for metric alerts)')
param fabricCapacityResourceId string = ''

@description('Tags to apply to resources')
param tags object = {}

@description('Alert severity (0=Critical, 1=Error, 2=Warning, 3=Info, 4=Verbose)')
@minValue(0)
@maxValue(4)
param alertSeverity int = 2

@description('Budget start date in yyyy-MM-dd format (defaults to first of current month)')
param budgetStartDate string = ''

@description('Deployment timestamp for budget calculation (auto-generated)')
param deployedAt string = utcNow()

// =============================================================================
// Variables
// =============================================================================

var alertTags = union(tags, {
  FabricComponent: 'Monitoring'
  AlertType: 'CapacityAndBudget'
})

var hasActionGroup = !empty(alertActionGroupId)
var hasEmailRecipients = !empty(alertEmailRecipients)
var hasCapacityResource = !empty(fabricCapacityResourceId)

// Calculate budget start date
var resolvedBudgetStartDate = !empty(budgetStartDate) ? budgetStartDate : '${substring(deployedAt, 0, 7)}-01'

// =============================================================================
// Action Group (notification routing)
// =============================================================================

resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = if (!hasActionGroup && hasEmailRecipients) {
  name: 'ag-fabric-alerts'
  location: 'global'
  tags: alertTags
  properties: {
    groupShortName: 'FabricAlert'
    enabled: true
    emailReceivers: [
      for (email, i) in alertEmailRecipients: {
        name: 'recipient-${i}'
        emailAddress: email
        useCommonAlertSchema: true
      }
    ]
    webhookReceivers: enableWebhook && !empty(webhookUrl) ? [
      {
        name: 'webhook-notification'
        serviceUri: webhookUrl
        useCommonAlertSchema: true
      }
    ] : []
  }
}

// Resolve which action group to use
var resolvedActionGroupId = hasActionGroup ? alertActionGroupId : (hasEmailRecipients ? actionGroup.id : '')

// =============================================================================
// Capacity Utilization Alert (Scheduled Query Rule)
// =============================================================================

resource capacityAlert 'Microsoft.Insights/scheduledQueryRules@2023-03-15-preview' = if (enableCapacityAlerts && !empty(logAnalyticsWorkspaceId)) {
  name: 'alert-fabric-capacity-utilization'
  location: location
  tags: alertTags
  properties: {
    displayName: 'Fabric Capacity Utilization Alert'
    description: 'Fires when Fabric capacity utilization exceeds ${capacityThresholdPercent}%. Review workload distribution and consider scaling or smoothing.'
    severity: alertSeverity
    enabled: true
    evaluationFrequency: 'PT5M'
    windowSize: 'PT15M'
    scopes: [
      logAnalyticsWorkspaceId
    ]
    criteria: {
      allOf: [
        {
          query: '''
            // Fabric Capacity Utilization Query
            // Monitors CU (Capacity Unit) consumption from workspace monitoring tables
            // Adjust table name based on your workspace monitoring configuration
            let threshold = ${capacityThresholdPercent};
            FabricCapacityMetrics_CL
            | where TimeGenerated > ago(15m)
            | summarize AvgUtilization = avg(CapacityUtilizationPercent_d) by bin(TimeGenerated, 5m)
            | where AvgUtilization > threshold
          '''
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 3
            minFailingPeriodsToAlert: 2
          }
        }
      ]
    }
    actions: !empty(resolvedActionGroupId) ? {
      actionGroups: [
        resolvedActionGroupId
      ]
    } : {}
  }
}

// =============================================================================
// Throttling / Overload Alert
// =============================================================================

resource throttlingAlert 'Microsoft.Insights/scheduledQueryRules@2023-03-15-preview' = if (enableCapacityAlerts && !empty(logAnalyticsWorkspaceId)) {
  name: 'alert-fabric-capacity-throttling'
  location: location
  tags: alertTags
  properties: {
    displayName: 'Fabric Capacity Throttling Alert'
    description: 'Fires when Fabric capacity is throttling requests due to overload. Immediate action required: scale up or reduce concurrent workloads.'
    severity: 1 // Error severity for throttling
    enabled: true
    evaluationFrequency: 'PT5M'
    windowSize: 'PT5M'
    scopes: [
      logAnalyticsWorkspaceId
    ]
    criteria: {
      allOf: [
        {
          query: '''
            // Fabric Capacity Throttling Detection
            FabricCapacityMetrics_CL
            | where TimeGenerated > ago(5m)
            | where ThrottlingState_s == "Active" or CapacityUtilizationPercent_d >= 100
            | summarize ThrottleEvents = count() by bin(TimeGenerated, 1m)
            | where ThrottleEvents > 0
          '''
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    actions: !empty(resolvedActionGroupId) ? {
      actionGroups: [
        resolvedActionGroupId
      ]
    } : {}
  }
}

// =============================================================================
// Budget Alert (Consumption Budget)
// =============================================================================

resource budget 'Microsoft.Consumption/budgets@2023-11-01' = if (enableBudgetAlerts) {
  name: 'budget-fabric-monthly'
  properties: {
    category: 'Cost'
    amount: monthlyBudgetAmount
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: resolvedBudgetStartDate
    }
    notifications: {
      notification50: {
        enabled: length(budgetThresholds) > 0
        operator: 'GreaterThanOrEqualTo'
        threshold: 50
        contactEmails: hasEmailRecipients ? alertEmailRecipients : []
        thresholdType: 'Actual'
      }
      notification75: {
        enabled: length(budgetThresholds) > 1
        operator: 'GreaterThanOrEqualTo'
        threshold: 75
        contactEmails: hasEmailRecipients ? alertEmailRecipients : []
        thresholdType: 'Actual'
      }
      notification90: {
        enabled: length(budgetThresholds) > 2
        operator: 'GreaterThanOrEqualTo'
        threshold: 90
        contactEmails: hasEmailRecipients ? alertEmailRecipients : []
        thresholdType: 'Actual'
      }
      notification100: {
        enabled: length(budgetThresholds) > 3
        operator: 'GreaterThanOrEqualTo'
        threshold: 100
        contactEmails: hasEmailRecipients ? alertEmailRecipients : []
        thresholdType: 'Forecasted'
      }
    }
  }
}

// =============================================================================
// Long-Running Job Alert
// =============================================================================

resource longRunningJobAlert 'Microsoft.Insights/scheduledQueryRules@2023-03-15-preview' = if (enableCapacityAlerts && !empty(logAnalyticsWorkspaceId)) {
  name: 'alert-fabric-long-running-jobs'
  location: location
  tags: alertTags
  properties: {
    displayName: 'Fabric Long-Running Job Alert'
    description: 'Fires when Spark or SQL jobs exceed 2 hours. Investigate for inefficient queries or data skew.'
    severity: 3 // Info severity
    enabled: true
    evaluationFrequency: 'PT15M'
    windowSize: 'PT30M'
    scopes: [
      logAnalyticsWorkspaceId
    ]
    criteria: {
      allOf: [
        {
          query: '''
            // Long-running Fabric job detection
            FabricJobMetrics_CL
            | where TimeGenerated > ago(30m)
            | where Status_s == "Running"
            | where DurationMinutes_d > 120
            | project JobName_s, ItemType_s, DurationMinutes_d, WorkspaceName_s
          '''
          timeAggregation: 'Count'
          operator: 'GreaterThan'
          threshold: 0
          failingPeriods: {
            numberOfEvaluationPeriods: 2
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    actions: !empty(resolvedActionGroupId) ? {
      actionGroups: [
        resolvedActionGroupId
      ]
    } : {}
  }
}

// =============================================================================
// Outputs
// =============================================================================

@description('The action group resource ID')
output actionGroupId string = !hasActionGroup && hasEmailRecipients ? actionGroup.id : alertActionGroupId

@description('The capacity alert rule resource ID')
output capacityAlertRuleId string = enableCapacityAlerts && !empty(logAnalyticsWorkspaceId) ? capacityAlert.id : ''

@description('The throttling alert rule resource ID')
output throttlingAlertRuleId string = enableCapacityAlerts && !empty(logAnalyticsWorkspaceId) ? throttlingAlert.id : ''

@description('The budget resource ID')
output budgetId string = enableBudgetAlerts ? budget.id : ''

@description('The long-running job alert resource ID')
output longRunningJobAlertId string = enableCapacityAlerts && !empty(logAnalyticsWorkspaceId) ? longRunningJobAlert.id : ''

@description('Tags applied to monitoring resources')
output appliedTags object = alertTags
