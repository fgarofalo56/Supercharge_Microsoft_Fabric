// =============================================================================
// Cost Allocation Tags Module
// =============================================================================
// This module defines standard cost allocation tags for Azure resources.
// Use these tags consistently across all deployments to enable accurate
// cost tracking, chargeback, and showback in Azure Cost Management.
// =============================================================================

// =============================================================================
// Parameters
// =============================================================================

@description('Cost center code for billing allocation')
param costCenter string

@description('Project name for cost tracking')
param project string = 'fabric-casino-poc'

@description('Environment name (dev, staging, prod)')
@allowed(['dev', 'staging', 'prod', 'demo', 'sandbox'])
param environment string

@description('Owner email or team name responsible for the resources')
param owner string

@description('Department name for organizational cost allocation')
param department string = 'Data Engineering'

@description('Application name for workload identification')
param application string = 'Microsoft Fabric POC'

@description('Business unit for enterprise chargeback')
param businessUnit string = ''

@description('Budget code for financial tracking')
param budgetCode string = ''

@description('Start date for the project (YYYY-MM-DD)')
param startDate string = ''

@description('Expected end date for the project (YYYY-MM-DD)')
param endDate string = ''

@description('Criticality level of the workload')
@allowed(['low', 'medium', 'high', 'critical'])
param criticality string = 'medium'

@description('Whether the resource is managed by automation')
param managedBy string = 'Bicep'

@description('Additional custom tags')
param additionalTags object = {}

// =============================================================================
// Variables
// =============================================================================

// Core cost allocation tags (always applied)
var coreTags = {
  // Financial tracking
  CostCenter: costCenter
  Project: project
  Environment: environment

  // Ownership and accountability
  Owner: owner
  Department: department

  // Workload identification
  Application: application

  // Management metadata
  ManagedBy: managedBy
  Criticality: criticality
}

// Optional financial tags (only if provided)
var financialTags = union(
  !empty(businessUnit) ? { BusinessUnit: businessUnit } : {},
  !empty(budgetCode) ? { BudgetCode: budgetCode } : {}
)

// Optional lifecycle tags (only if provided)
var lifecycleTags = union(
  !empty(startDate) ? { StartDate: startDate } : {},
  !empty(endDate) ? { EndDate: endDate } : {}
)

// Combined tags
var allTags = union(coreTags, financialTags, lifecycleTags, additionalTags)

// =============================================================================
// Outputs
// =============================================================================

@description('Complete set of cost allocation tags to apply to resources')
output tags object = allTags

@description('Core tags only (without optional/custom tags)')
output coreTags object = coreTags

@description('Tag names for documentation')
output tagNames array = [
  'CostCenter'
  'Project'
  'Environment'
  'Owner'
  'Department'
  'Application'
  'ManagedBy'
  'Criticality'
  'BusinessUnit'
  'BudgetCode'
  'StartDate'
  'EndDate'
]

// =============================================================================
// Usage Examples
// =============================================================================
//
// Example 1: Basic usage with core tags
// --------------------------------------
// module costTags 'cost-tags.bicep' = {
//   name: 'cost-tags'
//   params: {
//     costCenter: 'CC-12345'
//     environment: 'dev'
//     owner: 'data-engineering@company.com'
//   }
// }
//
// resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
//   name: 'mystorageaccount'
//   location: location
//   tags: costTags.outputs.tags
//   ...
// }
//
// Example 2: Full enterprise tagging
// -----------------------------------
// module costTags 'cost-tags.bicep' = {
//   name: 'cost-tags'
//   params: {
//     costCenter: 'CC-12345'
//     project: 'fabric-casino-poc'
//     environment: 'prod'
//     owner: 'data-engineering@company.com'
//     department: 'Data Engineering'
//     application: 'Microsoft Fabric POC'
//     businessUnit: 'Gaming Division'
//     budgetCode: 'BUD-2025-POC'
//     startDate: '2025-01-15'
//     endDate: '2025-06-30'
//     criticality: 'high'
//     additionalTags: {
//       Compliance: 'Gaming-Regulations'
//       DataClassification: 'Confidential'
//     }
//   }
// }
//
// Example 3: Using with main.bicep
// ---------------------------------
// // In main.bicep parameters
// param costCenter string
// param owner string
//
// module costTags 'cost-tags.bicep' = {
//   name: 'cost-tags-deployment'
//   params: {
//     costCenter: costCenter
//     environment: environment
//     owner: owner
//   }
// }
//
// var defaultTags = union(tags, costTags.outputs.tags, {
//   DeployedAt: deployedAt
// })
// =============================================================================

// =============================================================================
// Tag Policy Recommendations
// =============================================================================
//
// 1. REQUIRED TAGS (enforce with Azure Policy)
//    - CostCenter: For financial chargeback
//    - Environment: For environment-based cost analysis
//    - Owner: For accountability and communication
//
// 2. RECOMMENDED TAGS (encourage with Azure Policy)
//    - Project: For project-level cost aggregation
//    - Application: For workload identification
//    - Department: For organizational rollup
//
// 3. OPTIONAL TAGS (based on organizational needs)
//    - BusinessUnit: For enterprise chargeback
//    - BudgetCode: For detailed financial tracking
//    - StartDate/EndDate: For project lifecycle tracking
//
// 4. AUTOMATED TAGS (set by deployment)
//    - ManagedBy: Identifies deployment method
//    - DeployedAt: Timestamp of deployment
//
// Azure Policy Example (Require CostCenter tag):
// {
//   "if": {
//     "field": "tags['CostCenter']",
//     "exists": "false"
//   },
//   "then": {
//     "effect": "deny"
//   }
// }
// =============================================================================

// =============================================================================
// Cost Management Best Practices
// =============================================================================
//
// 1. TAG CONSISTENCY
//    - Use this module for ALL resource deployments
//    - Avoid manual tag modifications in portal
//    - Implement tag inheritance where possible
//
// 2. COST CENTER NAMING
//    - Use consistent format: CC-XXXXX or department-project
//    - Document cost center mappings
//    - Align with finance systems
//
// 3. ENVIRONMENT NAMING
//    - Standardize: dev, staging, prod
//    - Use for cost allocation rules
//    - Enable environment-based budgets
//
// 4. MONITORING
//    - Set up Cost Management budgets with tag filters
//    - Create cost alerts by CostCenter
//    - Review monthly cost reports by Project
//
// 5. GOVERNANCE
//    - Implement Azure Policy for tag enforcement
//    - Regular tag compliance audits
//    - Document tagging standards
// =============================================================================

// =============================================================================
// Budget Alert Resource (Optional)
// =============================================================================
// Deploy this module at the resource group scope to create a monthly budget
// with percentage-based alerts.  Pass the resource group name and a contact
// email to receive notifications when spending crosses thresholds.
//
// Usage (from main.bicep after the resource group is created):
//
//   module budget 'cost-tags.bicep' = {
//     name: 'budget-deployment'
//     scope: resourceGroup
//     params: {
//       costCenter:      costCenter
//       environment:     environment
//       owner:           owner
//       enableBudget:    true
//       budgetAmount:    10000     // $10,000/month
//       contactEmails:   [ owner ]
//     }
//   }
// =============================================================================

@description('Enable monthly budget alert creation')
param enableBudget bool = false

@description('Monthly budget amount in USD')
param budgetAmount int = 10000

@description('Contact emails for budget alerts')
param contactEmails array = []

@description('Start date for the budget period (YYYY-MM-01). Defaults to current month.')
param budgetStartDate string = '${substring(utcNow(), 0, 7)}-01'

resource monthlyBudget 'Microsoft.Consumption/budgets@2023-11-01' = if (enableBudget && !empty(contactEmails)) {
  name: 'budget-${project}-${environment}'
  properties: {
    category: 'Cost'
    amount: budgetAmount
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: budgetStartDate
    }
    notifications: {
      actual_GreaterThan_50_Percent: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 50
        contactEmails: contactEmails
        thresholdType: 'Actual'
      }
      actual_GreaterThan_80_Percent: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 80
        contactEmails: contactEmails
        thresholdType: 'Actual'
      }
      actual_GreaterThan_100_Percent: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 100
        contactEmails: contactEmails
        thresholdType: 'Actual'
      }
      forecasted_GreaterThan_100_Percent: {
        enabled: true
        operator: 'GreaterThan'
        threshold: 100
        contactEmails: contactEmails
        thresholdType: 'Forecasted'
      }
    }
  }
}
