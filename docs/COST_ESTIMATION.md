# 💰 Azure Cost Estimation Guide

> 🏠 [Home](index.md) > 📚 [Docs](./) > 💰 Cost Estimation

<div align="center">

# 💰 Cost Estimation

**Budget Planning & Cost Analysis**

![Category](https://img.shields.io/badge/Category-Finance-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-January_2025-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2025-01-21` | **Version:** 1.0.0

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Detailed Cost Breakdown](#detailed-cost-breakdown)
  - [Microsoft Fabric Capacity](#microsoft-fabric-capacity)
  - [Azure Storage (ADLS Gen2)](#azure-storage-adls-gen2)
  - [Microsoft Purview](#microsoft-purview)
  - [Azure Key Vault](#azure-key-vault)
  - [Log Analytics](#log-analytics)
  - [Networking (Private Endpoints)](#networking-private-endpoints)
- [Cost Scenarios](#cost-scenarios)
  - [Scenario 1: POC Demo (3 Days)](#scenario-1-poc-demo-3-days)
  - [Scenario 2: Development (1 Month)](#scenario-2-development-1-month)
  - [Scenario 3: Production Pilot (1 Month)](#scenario-3-production-pilot-1-month)
- [Cost Optimization Strategies](#cost-optimization-strategies)
- [Azure Pricing Calculator](#azure-pricing-calculator)
- [Cost Monitoring](#cost-monitoring)

---

## Executive Summary

This document provides comprehensive cost estimates for the Microsoft Fabric Casino/Gaming POC across different environments and usage patterns.

### Total Estimated Monthly Cost by Environment

| 🏢 Environment | 📊 Fabric SKU | ⏰ Hours/Day | 💰 Monthly Estimate | 📝 Notes |
|:---------------|:-------------|:------------|:-------------------|:---------|
| **Development** | `F4` | 8 hrs (weekdays) | **$450 - $650** | Pause outside business hours |
| **Staging** | `F16` | 12 hrs (weekdays) | **$1,800 - $2,500** | Extended testing hours |
| **Production POC** | `F64` | 24/7 | **$9,500 - $12,500** | Full capacity, always-on |
| **Production Pilot** | `F64 Reserved` | 24/7 | **$6,500 - $9,000** | 1-year reserved capacity |

### Cost Distribution (Production POC)

| 🧩 Component | 💵 Monthly Cost | 📊 % of Total |
|:-------------|:---------------|:--------------|
| **Fabric Capacity (F64)** | ~$8,500 | 75-80% |
| **ADLS Gen2 Storage** | ~$500 | 4-5% |
| **Microsoft Purview** | ~$800 | 7-8% |
| **Log Analytics** | ~$300 | 2-3% |
| **Key Vault** | ~$10 | <1% |
| **Networking** | ~$200 | 1-2% |

> **Note:** All prices are estimates in USD based on East US 2 region. Actual costs may vary based on usage patterns, region, and Azure pricing updates. Refer to the [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/) for current rates.

---

## Detailed Cost Breakdown

### Microsoft Fabric Capacity

Microsoft Fabric capacity is the primary cost driver for this POC. Fabric uses Capacity Units (CUs) for billing, with different SKUs providing different amounts of compute power.

![Fabric Capacity Settings](https://learn.microsoft.com/en-us/fabric/admin/media/service-admin-portal-capacity-settings/capacity-settings.png)

*Source: [Capacity Settings in Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/admin/service-admin-portal-capacity-settings)*

#### Fabric SKU Pricing Matrix

| 📊 SKU | ⚡ CUs | 🖥️ vCores | 🧠 Memory | 💰 Monthly (24/7) | 💵 Monthly (8hr/day) | ⏱️ Hourly |
|:-------|:------|:---------|:----------|:-----------------|:-------------------|:----------|
| `F2` | 2 | 2 | 16 GB | ~$265 | ~$88 | `$0.36` |
| `F4` | 4 | 4 | 32 GB | ~$530 | ~$176 | `$0.73` |
| `F8` | 8 | 8 | 64 GB | ~$1,060 | ~$353 | `$1.45` |
| `F16` | 16 | 16 | 128 GB | ~$2,120 | ~$706 | `$2.90` |
| `F32` | 32 | 32 | 256 GB | ~$4,240 | ~$1,413 | `$5.80` |
| **`F64`** ⭐ | **64** | **64** | **512 GB** | **~$8,480** | **~$2,827** | **`$11.60`** |
| `F128` | 128 | 128 | 1024 GB | ~$16,960 | ~$5,653 | `$23.20` |
| `F256` | 256 | 256 | 2048 GB | ~$33,920 | ~$11,307 | `$46.40` |
| `F512` | 512 | 512 | 4096 GB | ~$67,840 | ~$22,613 | `$92.80` |

> **POC Configuration:** The default POC uses **F64** for sufficient parallel processing of casino gaming workloads. Development environments can use F4 or F8.

#### Capacity Cost Optimization Options

| 💡 Option | 💰 Savings | 📋 Requirements |
|:----------|:----------|:---------------|
| **Pause/Resume Scheduling** | Up to 67% | Pause capacity during off-hours |
| **1-Year Reserved Capacity** | ~25-30% | Commit to 1-year usage |
| **3-Year Reserved Capacity** | ~35-40% | Commit to 3-year usage |
| **Dev/Test Subscriptions** | Varies | Azure Dev/Test offer pricing |

##### Pause/Resume Cost Impact (F64)

| ⏰ Schedule | 🕐 Active Hours/Month | 💵 Monthly Cost | 📉 Savings vs 24/7 |
|:-----------|:---------------------|:---------------|:-------------------|
| 24/7 | 730 | ~$8,480 | — |
| 12 hrs/day (all days) | 365 | ~$4,240 | **50%** |
| 8 hrs/day (weekdays only) | 176 | ~$2,042 | **76%** ⭐ |
| 8 hrs/day (all days) | 243 | ~$2,820 | **67%** |
| On-demand (as needed) | Variable | Variable | Up to **90%** |

---

### Azure Storage (ADLS Gen2)

Azure Data Lake Storage Gen2 costs consist of storage capacity, transactions, and data transfer.

#### Storage Pricing (Hot Tier, Standard_LRS)

| 📦 Component | 💲 Rate | 💰 POC Estimate (500 GB) |
|:-------------|:-------|:------------------------|
| **Data Storage** | `$0.0208`/GB/month | ~$10.40/month |
| **Write Operations** (per 10K) | `$0.065` | ~$50/month |
| **Read Operations** (per 10K) | `$0.0052` | ~$15/month |
| **Iterative Read** (per 10K) | `$0.0208` | ~$10/month |
| **Other Operations** | Varies | ~$5/month |

#### Storage Tiers Comparison

| 🗄️ Tier | 💲 Storage/GB | 📋 Best For | ✅ POC Recommendation |
|:--------|:-------------|:-----------|:---------------------|
| **Hot** 🔥 | `$0.0208` | Active data, frequent access | Bronze, Silver layers |
| **Cool** ❄️ | `$0.0115` | Infrequent access (30+ days) | Archived raw data |
| **Archive** 🧊 | `$0.00208` | Rarely accessed | Compliance archives |

#### Estimated Storage Volumes by Layer

| 🏛️ Layer | 📊 Estimated Size | 📈 Growth Rate | 💰 Monthly Cost |
|:---------|:-----------------|:--------------|:---------------|
| **Bronze** 🥉 | 200 GB | 50 GB/week | ~$4.16 |
| **Silver** 🥈 | 100 GB | 25 GB/week | ~$2.08 |
| **Gold** 🥇 | 50 GB | 10 GB/week | ~$1.04 |
| **Landing** 📥 | 150 GB | Variable | ~$3.12 |
| **Total** | **500 GB** | — | **~$10.40 + transactions** |

#### Transaction Cost Estimates (POC Workload)

| Workload | Monthly Operations | Monthly Cost |
|----------|-------------------|--------------|
| Bronze Ingestion | ~50M writes | ~$325 |
| Silver Transformation | ~20M read/write | ~$75 |
| Gold Aggregation | ~5M read/write | ~$20 |
| Power BI Queries | ~10M reads | ~$50 |
| **Total Transactions** | - | **~$470** |

> **Total ADLS Gen2 Estimate:** ~$500/month for POC workload (500 GB storage + transactions)

---

### Microsoft Purview

Microsoft Purview provides data governance, catalog, and lineage capabilities.

#### Purview Pricing Components

| 🧩 Component | 💲 Rate | 💰 POC Estimate |
|:-------------|:-------|:---------------|
| **Data Map Capacity Units** | `$0.42`/CU/hour | ~$300/month (1 CU baseline) |
| **Data Map Overages** | `$0.42`/CU/hour | ~$100/month |
| **Scanning (Standard)** | Included in CU | Included |
| **Scanning (Advanced)** | `$0.21`/vCore/hour | ~$150/month |
| **Classification** | `$0.000003`/record | ~$50/month |
| **Lineage** | Included | Included |

#### Purview Scanning Cost Estimates

| 📂 Data Source | 📊 Records/Tables | 🔄 Scan Frequency | 💰 Monthly Cost |
|:---------------|:-----------------|:-----------------|:---------------|
| **ADLS Gen2 Bronze** | ~50 tables | Daily | ~$50 |
| **ADLS Gen2 Silver** | ~30 tables | Daily | ~$30 |
| **ADLS Gen2 Gold** | ~20 tables | Daily | ~$20 |
| **Fabric Lakehouse** | ~100 items | Weekly | ~$100 |
| **Total Scanning** | — | — | **~$200** |

> **Total Purview Estimate:** ~$600-$800/month for POC governance workload

---

### Azure Key Vault

Key Vault costs are minimal for typical POC usage.

#### Key Vault Pricing

| 🔑 Operation Type | 💲 Rate | 💰 POC Estimate |
|:------------------|:-------|:---------------|
| **Secrets Operations** | `$0.03`/10K transactions | ~$3/month |
| **Key Operations (RSA 2048)** | `$0.03`/10K operations | ~$2/month |
| **Certificate Operations** | `$0.03`/10K operations | ~$1/month |
| **Storage (per secret)** | Included | Included |

> **Total Key Vault Estimate:** ~$5-$10/month

---

### Log Analytics

Log Analytics charges based on data ingestion volume and retention period.

#### Log Analytics Pricing

| 📊 Component | 💲 Rate | 💰 POC Estimate |
|:-------------|:-------|:---------------|
| **Data Ingestion** | `$2.30`/GB | ~$230/month (100 GB) |
| **Data Retention (0-31 days)** | Included | Included |
| **Data Retention (31-90 days)** | `$0.10`/GB/month | ~$60/month |
| **Data Retention (90+ days)** | `$0.20`/GB/month | As needed |
| **Interactive Queries** | Included | Included |
| **Basic Logs (optional)** | `$0.50`/GB ingestion | Alternative for high-volume |

#### Estimated Log Volumes

| 📋 Log Source | 📊 Daily Volume | 📈 Monthly Volume | 💰 Monthly Cost |
|:--------------|:---------------|:-----------------|:---------------|
| **Fabric Activity** | ~1 GB | ~30 GB | ~$69 |
| **Storage Diagnostics** | ~1.5 GB | ~45 GB | ~$103 |
| **Key Vault Audit** | ~0.2 GB | ~6 GB | ~$14 |
| **Purview Activity** | ~0.3 GB | ~9 GB | ~$21 |
| **Total** | **~3 GB/day** | **~90 GB** | **~$207** |

> **Total Log Analytics Estimate:** ~$250-$350/month (including extended retention)

---

### Networking (Private Endpoints)

Private endpoints are optional but recommended for production security.

#### Private Endpoint Pricing

| 🔒 Component | 💲 Rate | 💰 POC Estimate (if enabled) |
|:-------------|:-------|:---------------------------|
| **Private Endpoint (per endpoint)** | `$0.01`/hour | ~$7.30/month each |
| **Data Processing (inbound)** | `$0.01`/GB | ~$10/month |
| **Data Processing (outbound)** | `$0.01`/GB | ~$10/month |

#### Private Endpoints Required

| 🔗 Service | 🔢 Endpoints | 💰 Monthly Cost |
|:-----------|:------------|:---------------|
| **ADLS Gen2** (DFS + Blob) | 2 | ~$14.60 |
| **Key Vault** | 1 | ~$7.30 |
| **Purview** (Account + Portal + Ingestion) | 3 | ~$21.90 |
| **Total** | **6** | **~$43.80 + data processing** |

> **Total Networking Estimate:** ~$100-$200/month (with private endpoints enabled)

---

## Cost Scenarios

### Scenario 1: POC Demo (3 Days)

Short-term demonstration for customer or stakeholder presentation.

| 🧩 Component | ⚙️ Configuration | 💰 Cost |
|:-------------|:----------------|:-------|
| **Fabric Capacity** | F64, 24 hrs x 3 days | ~$835 |
| **ADLS Gen2** | 50 GB storage + transactions | ~$30 |
| **Purview** | Basic scanning (3 days pro-rated) | ~$80 |
| **Key Vault** | Minimal operations | ~$1 |
| **Log Analytics** | 10 GB ingestion | ~$25 |
| **Networking** | Public endpoints | $0 |

| 💵 **Total 3-Day Demo** | | **~$970** |
|:------------------------|:---------|:----------|

**Cost Optimization Tips:**
- Create capacity just before demo, delete immediately after
- Use sample datasets (pre-generated)
- Disable verbose logging during demo

---

### Scenario 2: Development (1 Month)

Development environment with business hours usage.

| 🧩 Component | ⚙️ Configuration | 💰 Cost |
|:-------------|:----------------|:-------|
| **Fabric Capacity** | F4, 8 hrs/day weekdays (176 hrs) | ~$130 |
| **ADLS Gen2** | 50 GB storage + moderate transactions | ~$100 |
| **Purview** | Weekly scanning only | ~$200 |
| **Key Vault** | Standard operations | ~$5 |
| **Log Analytics** | 30 GB ingestion, 90-day retention | ~$100 |
| **Networking** | Public endpoints | $0 |

| 💵 **Total Development (1 Month)** | | **~$535** |
|:-----------------------------------|:---------|:----------|

**Cost Optimization Tips:**
- Use Azure DevTest subscription pricing if available
- Implement pause/resume automation (see [infra/scripts/pause-resume.ps1])
- Reduce Purview scan frequency to weekly
- Use Basic Logs tier for high-volume diagnostics

---

### Scenario 3: Production Pilot (1 Month)

Full production-like environment for pilot program.

| 🧩 Component | ⚙️ Configuration | 💰 Cost |
|:-------------|:----------------|:-------|
| **Fabric Capacity** | F64, 24/7 | ~$8,480 |
| **ADLS Gen2** | 500 GB storage + high transactions | ~$500 |
| **Purview** | Daily scanning, full governance | ~$800 |
| **Key Vault** | Full operations | ~$10 |
| **Log Analytics** | 100 GB ingestion, 90-day retention | ~$350 |
| **Networking** | Private endpoints enabled | ~$200 |

| 💵 **Total Production Pilot (1 Month)** | | **~$10,340** |
|:----------------------------------------|:---------|:-------------|

**Cost Optimization Tips:**
- Consider 1-year reserved capacity (~$6,000/month for Fabric)
- Implement lifecycle policies for storage (move cold data to Cool tier)
- Use commitment tiers for Log Analytics if available
- Review Purview scanning frequency based on data change rate

---

## Cost Optimization Strategies

### 1. Fabric Capacity Management

#### Pause/Resume Scheduling

Implement automated pause/resume using Azure Automation:

```powershell
# Example: Pause capacity at 6 PM, Resume at 8 AM (weekdays)
# See: infra/scripts/capacity-scheduler.ps1

# Potential savings: 50-76% on Fabric costs
```

**Recommended Schedules:**

| 🏢 Environment | ⏰ Schedule | 📉 Savings |
|:---------------|:-----------|:----------|
| **Dev** | 8 AM - 6 PM weekdays | **76%** |
| **Staging** | 7 AM - 10 PM weekdays | **57%** |
| **Production** | 24/7 (no pause) | Use reserved |

#### Reserved Capacity

| 📋 Commitment | 💰 Discount | ⏱️ Break-even |
|:-------------|:-----------|:-------------|
| Pay-as-you-go | 0% | Flexible |
| 1-year reserved | ~25-30% | ~9 months |
| 3-year reserved | ~35-40% | ~24 months |

### 2. Storage Optimization

#### Lifecycle Management Policies

```json
{
  "rules": [
    {
      "name": "MoveToCool",
      "enabled": true,
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "prefixMatch": ["bronze/archive/"]
        },
        "actions": {
          "baseBlob": {
            "tierToCool": { "daysAfterModificationGreaterThan": 30 }
          }
        }
      }
    }
  ]
}
```

**Potential Savings:** 40-50% on archived data storage

### 3. Log Analytics Optimization

| 💡 Strategy | ⚙️ Implementation | 📉 Savings |
|:------------|:-----------------|:----------|
| **Basic Logs** | Use for high-volume, low-query logs | 70% on ingestion |
| **Data Collection Rules** | Filter unnecessary logs at source | 30-50% on volume |
| **Commitment Tiers** | Pre-purchase ingestion capacity | 15-25% |
| **Archive to Storage** | Export to cheaper storage tier | 80% for cold data |

### 4. Purview Optimization

- Schedule scans during off-peak hours
- Use incremental scanning where supported
- Limit classification to sensitive data columns only
- Batch lineage extraction operations

### 5. Azure Advisor Recommendations

Enable Azure Advisor for automated cost recommendations:
- Right-sizing suggestions
- Unused resource identification
- Reserved instance opportunities
- Anomaly detection

---

## Azure Pricing Calculator

Use the Azure Pricing Calculator for accurate, up-to-date estimates.

### Pre-configured Calculator Links

| Scenario | Link |
|----------|------|
| **POC Demo (3 Days)** | [Configure in Calculator](https://azure.microsoft.com/pricing/calculator/?service=fabric) |
| **Development** | [Configure in Calculator](https://azure.microsoft.com/pricing/calculator/?service=fabric) |
| **Production Pilot** | [Configure in Calculator](https://azure.microsoft.com/pricing/calculator/?service=fabric) |

> **Tip:** Use the Azure Pricing Calculator to get accurate, region-specific pricing. The capacity settings shown below help you understand what you are configuring:

![Fabric Capacity Settings](https://learn.microsoft.com/en-us/fabric/admin/media/service-admin-portal-capacity-settings/capacity-settings.png)

*Source: [Capacity Settings in Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/admin/service-admin-portal-capacity-settings)*

### Components to Configure

1. **Microsoft Fabric**
   - SKU: F64 (or appropriate)
   - Region: East US 2
   - Hours per month: Based on schedule

2. **Storage Account**
   - Type: Data Lake Storage Gen2
   - Tier: Hot
   - Capacity: 500 GB
   - Redundancy: LRS

3. **Azure Purview**
   - Data Map Capacity Units
   - Scanning hours

4. **Log Analytics**
   - Data ingestion (GB/month)
   - Retention period

5. **Key Vault**
   - Secrets/keys count
   - Operations per month

6. **Private Endpoints** (if applicable)
   - Number of endpoints
   - Data processed

---

## Cost Monitoring

### Azure Cost Management Setup

1. **Create Budgets**
   ```
   Budget Name: FabricPOC-Monthly
   Amount: $12,000
   Alert thresholds: 50%, 75%, 90%, 100%
   ```

2. **Cost Alerts**
   - Configure email notifications
   - Set up action groups for automated responses

3. **Cost Analysis Views**
   - Group by: Resource Group, Service, Tag
   - Filter by: CostCenter tag

### Recommended Tags for Cost Allocation

```bicep
// See: infra/cost-tags.bicep
tags: {
  CostCenter: 'gaming-poc'
  Project: 'fabric-casino-poc'
  Environment: 'dev|staging|prod'
  Owner: 'data-engineering-team'
}
```

### Monthly Review Checklist

- [ ] Review Fabric capacity utilization (target: 60-80%)
- [ ] Check for idle/unused resources
- [ ] Validate log retention policies
- [ ] Review storage growth trends
- [ ] Evaluate reserved capacity eligibility
- [ ] Check Azure Advisor recommendations
- [ ] Update forecasts based on actual usage

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [Architecture Guide](ARCHITECTURE.md) | System architecture and components |
| [Deployment Guide](DEPLOYMENT.md) | Infrastructure deployment instructions |
| [Prerequisites](PREREQUISITES.md) | Setup requirements |
| [Cost Tags Module](../infra/cost-tags.bicep) | Bicep module for cost allocation |

---

## Disclaimer

> **Important:** All cost estimates in this document are approximations based on Azure pricing as of January 2025. Actual costs may vary based on:
> - Azure region selected
> - Actual resource utilization
> - Data volumes and transaction patterns
> - Azure pricing changes
> - Exchange rate fluctuations (for non-USD billing)
>
> Always verify current pricing using the [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/) and monitor actual costs through [Azure Cost Management](https://portal.azure.com/#blade/Microsoft_Azure_CostManagement/Menu/overview).

---

[Back to top](#azure-cost-estimation-guide)

---

> **Documentation maintained by:** Microsoft Fabric POC Team
> **Repository:** [Supercharge_Microsoft_Fabric](https://github.com/fgarofalo56/Supercharge_Microsoft_Fabric)
