// =============================================================================
// Microsoft Fabric Data Factory Pipeline Module (Metadata-Only)
// =============================================================================
// This module does NOT deploy any Azure resources. Fabric Pipelines are
// workspace-level items without a dedicated ARM resource type.
//
// Purpose:
// - Documents the Pipeline configuration as Bicep parameters
// - Emits outputs consumed by main.bicep and CI/CD pipelines
// - Serves as the IaC "contract" for what the Pipeline looks like
//
// Actual Pipeline items are deployed via:
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

var pipelineConfig = {
  name: pipelineName
  configName: pipelineConfigName
  environment: environment
  capacityId: capacityId
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
  governance: {
    logAnalyticsWorkspaceId: logAnalyticsWorkspaceId
  }
}

// =============================================================================
// OUTPUT-ONLY — No resources deployed
// Actual Fabric Pipeline items are deployed via fabric-cicd library.
// =============================================================================

@description('The pipeline configuration name')
output pipelineName string = pipelineConfigName

@description('Whether the schedule trigger is enabled')
output triggerStatus string = enableScheduleTrigger ? 'Enabled' : 'Disabled'

@description('The full pipeline configuration as JSON')
output configurationJson string = string(pipelineConfig)

@description('Tags that would be applied to pipeline resources')
output appliedTags object = union(tags, {
  FabricComponent: 'Pipeline'
  FabricCapacityId: capacityId
  PipelineName: pipelineName
  ScheduleEnabled: string(enableScheduleTrigger)
})
