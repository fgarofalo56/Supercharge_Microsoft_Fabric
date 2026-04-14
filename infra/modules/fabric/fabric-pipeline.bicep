// =============================================================================
// Microsoft Fabric Data Factory Pipeline Module
// =============================================================================
// Deploys configuration for Fabric Data Factory pipelines (orchestration).
//
// Since Fabric pipelines are workspace-level items without dedicated ARM
// resource types, this module provisions metadata, tagging, and supporting
// infrastructure (scheduling via Logic Apps or Azure Functions).
//
// Key features supported:
// - Pipeline orchestration metadata
// - Schedule trigger configuration
// - Monitoring integration
// - CI/CD via fabric-cicd library
//
// The actual Pipeline items are created via:
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

@description('Pipeline display name')
param pipelineName string = 'fabric-pipeline'

@description('Resource ID of the Fabric capacity to associate with')
param capacityId string = ''

@description('Enable schedule trigger for automated execution')
param enableScheduleTrigger bool = false

@description('Schedule frequency for the trigger')
@allowed(['Minute', 'Hour', 'Day', 'Week', 'Month'])
param scheduleFrequency string = 'Day'

@description('Schedule interval (e.g., 1 = every 1 day, 15 = every 15 minutes)')
@minValue(1)
@maxValue(1440)
param scheduleInterval int = 1

@description('Schedule start time (ISO 8601)')
param scheduleStartTime string = ''

@description('Pipeline activities list (for documentation/tagging)')
param activities array = []

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string = ''

@description('Enable retry on failure')
param enableRetryOnFailure bool = true

@description('Maximum retry attempts')
@minValue(0)
@maxValue(10)
param maxRetryAttempts int = 3

@description('Retry interval in seconds')
@minValue(10)
@maxValue(3600)
param retryIntervalSeconds int = 30

// =============================================================================
// Variables
// =============================================================================

var pipelineConfigName = '${projectPrefix}-pipe-${environment}'

var pipelineTags = union(tags, {
  FabricComponent: 'Pipeline'
  FabricCapacityId: capacityId
  PipelineName: pipelineName
  ScheduleEnabled: string(enableScheduleTrigger)
  ScheduleFrequency: enableScheduleTrigger ? '${scheduleInterval} ${scheduleFrequency}' : 'Manual'
  RetryEnabled: string(enableRetryOnFailure)
})

// Pipeline configuration for downstream automation
var pipelineConfig = {
  name: pipelineName
  environment: environment
  schedule: {
    enabled: enableScheduleTrigger
    frequency: scheduleFrequency
    interval: scheduleInterval
    startTime: scheduleStartTime
  }
  retry: {
    enabled: enableRetryOnFailure
    maxAttempts: maxRetryAttempts
    intervalSeconds: retryIntervalSeconds
  }
  activities: activities
}

// =============================================================================
// Pipeline Configuration Metadata
// =============================================================================

resource pipelineMetadata 'Microsoft.Resources/deploymentScripts@2023-08-01' = {
  name: 'pipe-config-${pipelineConfigName}'
  location: location
  tags: pipelineTags
  kind: 'AzurePowerShell'
  properties: {
    azPowerShellVersion: '9.7'
    retentionInterval: 'P1D'
    scriptContent: '''
      $config = @{
        pipelineName = $env:PIPELINE_NAME
        environment = $env:ENVIRONMENT
        scheduleEnabled = $env:SCHEDULE_ENABLED
        scheduleFrequency = $env:SCHEDULE_FREQUENCY
        scheduleInterval = $env:SCHEDULE_INTERVAL
        retryEnabled = $env:RETRY_ENABLED
        maxRetry = $env:MAX_RETRY
        timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
      }
      $DeploymentScriptOutputs = @{
        configuration = ($config | ConvertTo-Json -Compress)
      }
    '''
    environmentVariables: [
      { name: 'PIPELINE_NAME', value: pipelineName }
      { name: 'ENVIRONMENT', value: environment }
      { name: 'SCHEDULE_ENABLED', value: string(enableScheduleTrigger) }
      { name: 'SCHEDULE_FREQUENCY', value: scheduleFrequency }
      { name: 'SCHEDULE_INTERVAL', value: string(scheduleInterval) }
      { name: 'RETRY_ENABLED', value: string(enableRetryOnFailure) }
      { name: 'MAX_RETRY', value: string(maxRetryAttempts) }
    ]
    timeout: 'PT5M'
    cleanupPreference: 'OnSuccess'
  }
}

// =============================================================================
// Outputs
// =============================================================================

@description('The pipeline configuration name')
output pipelineName string = pipelineConfigName

@description('The pipeline configuration as JSON')
output pipelineConfiguration string = string(pipelineConfig)

@description('Whether the schedule trigger is enabled')
output triggerStatus string = enableScheduleTrigger ? 'Enabled' : 'Disabled'

@description('The deployment script resource ID')
output metadataResourceId string = pipelineMetadata.id

@description('Tags applied to pipeline resources')
output appliedTags object = pipelineTags
