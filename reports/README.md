# Power BI Reports & Semantic Model

> **[Home](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/blob/main/README.md)** > **Reports**

**Last Updated:** `2025-01-21` | **Version:** 1.0.0

---

## Overview

This directory contains the complete Power BI reporting infrastructure for the Microsoft Fabric Casino/Gaming POC. It includes:

- **Semantic Model Definitions** (TMDL format) for Direct Lake connectivity
- **DAX Measure Libraries** organized by business domain
- **Report Layout Definitions** in JSON format
- **Setup and Configuration Guides**

---

## Directory Structure

```
reports/
├── README.md                          # This file
├── setup-guide.md                     # Step-by-step setup instructions
├── dax-measures.md                    # Complete DAX reference
├── semantic-model/
│   ├── model.tmdl                     # Model metadata and configuration
│   └── tables/
│       ├── dim_date.tmdl             # Date dimension
│       ├── dim_time.tmdl             # Time dimension
│       ├── dim_machine.tmdl          # Slot machine dimension
│       ├── dim_player.tmdl           # Player dimension
│       ├── dim_table.tmdl            # Table games dimension
│       ├── fact_slot_performance.tmdl # Slot performance facts
│       ├── fact_table_performance.tmdl # Table games facts
│       ├── fact_player_activity.tmdl  # Player 360 facts
│       └── fact_compliance.tmdl       # Compliance facts
│   └── measures/
│       ├── _casino_kpis.tmdl         # Core casino metrics
│       ├── _player_analytics.tmdl    # Player metrics
│       ├── _compliance_metrics.tmdl  # Compliance metrics
│       └── _time_intelligence.tmdl   # Time calculations
└── report-definitions/
    ├── casino-executive-dashboard.json  # Executive summary report
    ├── slot-floor-operations.json       # Slot operations report
    └── compliance-monitoring.json       # Compliance report
```

---

## Reports Overview

### 1. Casino Executive Dashboard

**Purpose:** High-level KPIs and trends for casino executives

| Visual | Description |
|--------|-------------|
| KPI Cards | Net Win, Hold %, Active Players, Total Games |
| Trend Chart | Daily revenue with 7-day moving average |
| Zone Performance | Comparative bar chart by casino zone |
| Top Machines | Top 10 performers by net win |
| Compliance Summary | CTR/SAR/W-2G filing counts |
| Player Distribution | Loyalty tier breakdown |

**Screenshot Placeholder:**

> 📸 **Screenshot**: Executive Dashboard showing KPI cards, revenue trends, and player distribution
> 
> _To add: Capture the main dashboard view from Power BI Service after publishing_

**Key Filters:**
- Date Range (default: Last 30 days)
- Property/Location
- Zone
- Denomination

---

### 2. Slot Floor Operations

**Purpose:** Operational insights for floor managers

| Visual | Description |
|--------|-------------|
| Machine Matrix | Performance by Zone x Denomination |
| Utilization Heatmap | Machine activity by hour |
| Hold Variance Analysis | Scatter plot of actual vs theoretical |
| Jackpot Tracking | Recent jackpots with amounts |
| Alert Indicators | Machines requiring attention |
| Manufacturer Comparison | Performance by machine manufacturer |

**Screenshot Placeholder:**

> 📸 **Screenshot**: Slot Operations dashboard with floor map and performance metrics
> 
> _To add: Capture the slot operations view showing machine status and KPIs_

**Key Filters:**
- Date Range
- Zone
- Denomination
- Manufacturer
- Machine Type
- Performance Status

---

### 3. Compliance Monitoring

**Purpose:** Regulatory compliance tracking and audit support

| Visual | Description |
|--------|-------------|
| Filing Status Cards | Pending, Submitted, Overdue counts |
| Daily Filing Trend | CTR/SAR/W-2G filing volumes |
| Threshold Alerts | Transactions approaching thresholds |
| Structuring Detection | Potential structuring indicators |
| Deadline Calendar | Upcoming filing deadlines |
| Audit Trail | Recent compliance activities |

**Screenshot Placeholder:**

> 📸 **Screenshot**: Compliance Monitoring dashboard with filing status and deadline tracking
> 
> _To add: Capture the compliance view showing CTR/SAR/W-2G metrics_

**Key Filters:**
- Date Range
- Filing Type (CTR, SAR, W-2G)
- Filing Status
- Amount Threshold

---

## Data Source Configuration

### Direct Lake Connection

The semantic model uses Direct Lake mode for optimal performance:

```
OneLake (lh_gold lakehouse)
    └── Delta Tables
         ├── gold_slot_performance
         ├── gold_table_analytics
         ├── gold_player_360
         ├── gold_financial_summary
         ├── gold_compliance_reporting
         └── gold_security_dashboard
```

### Connection String Format

```
Data Source=powerbi://api.powerbi.com/v1.0/myorg/[workspace-name];
Initial Catalog=[lakehouse-name];
DirectLakeConnection=True
```

### Required Permissions

| Permission | Scope | Purpose |
|------------|-------|---------|
| Viewer | Lakehouse | Read Gold layer tables |
| Contributor | Semantic Model | Modify measures/relationships |
| Admin | Workspace | Manage report deployment |

---

## Key Metrics Reference

### Slot Performance Metrics

| Metric | Definition | Business Use |
|--------|------------|--------------|
| **Coin In** | Total amount wagered | Volume indicator |
| **Coin Out** | Total payouts to players | Payout tracking |
| **Net Win** | Coin In - Coin Out | Revenue metric |
| **Hold %** | Net Win / Coin In | Profitability indicator |
| **Theo Win** | Coin In x House Edge | Expected revenue |
| **Hold Variance** | Net Win - Theo Win | Performance vs expected |
| **WPUPD** | Win Per Unit Per Day | Machine productivity |

### Player Metrics

| Metric | Definition | Business Use |
|--------|------------|--------------|
| **Player Value Score** | Composite scoring (0-1000) | Player ranking |
| **Theo Win** | Expected player contribution | Marketing ROI |
| **Churn Risk Score** | Likelihood to leave (0-100) | Retention targeting |
| **Days Since Visit** | Recency indicator | Engagement tracking |
| **Total Visits** | Visit frequency | Loyalty indicator |

### Compliance Metrics

| Metric | Definition | Business Use |
|--------|------------|--------------|
| **CTR Count** | Cash Transaction Reports filed | Regulatory compliance |
| **SAR Count** | Suspicious Activity Reports | Risk management |
| **W-2G Count** | Jackpot tax forms | Tax compliance |
| **Filing Rate** | Filings per required threshold | Compliance health |
| **Pending Filings** | Not yet submitted | Workload indicator |

---

## How to Import into Fabric

### Method 1: Via Lakehouse UI

1. Open `lh_gold` lakehouse in Fabric
2. Click **New semantic model**
3. Select all Gold layer tables
4. Configure relationships per `setup-guide.md`
5. Add measures from `dax-measures.md`

### Method 2: Via TMDL Import

1. Export semantic model as TMDL from an existing model
2. Replace table/measure definitions with files from this directory
3. Import modified TMDL to Fabric workspace

### Method 3: Via Power BI Desktop

1. Connect to OneLake with Direct Lake mode
2. Import tables from `lh_gold`
3. Create relationships and measures
4. Publish to Fabric workspace

See `setup-guide.md` for detailed step-by-step instructions.

---

## Report Distribution

### Scheduled Delivery

| Report | Audience | Frequency | Format |
|--------|----------|-----------|--------|
| Executive Dashboard | C-Suite | Daily 7 AM | Email embed |
| Slot Operations | Floor Managers | Real-time | Dashboard |
| Compliance | Compliance Team | Daily 8 AM | PDF |

### Row-Level Security

RLS is configured for zone-based access:

```dax
// Users see only their assigned zones
[Zone Filter] =
    gold_slot_performance[zone] IN VALUES(SecurityTable[UserZone])
```

---

## Performance Optimization

### Pre-Aggregation

Gold layer tables are pre-aggregated for optimal Direct Lake performance:
- Daily grain for historical analysis
- Hourly grain for operational dashboards
- Optimized with Z-ORDER on frequently filtered columns

### Best Practices

1. **Limit columns** - Only include needed fields in semantic model
2. **Use measures** - Avoid calculated columns for complex logic
3. **Filter early** - Apply filters at data source level
4. **Limit visuals** - Maximum 6-8 visuals per report page

---

## Maintenance

### Monthly Tasks

- [ ] Review measure performance
- [ ] Validate data quality scores
- [ ] Update threshold parameters
- [ ] Archive old report versions

### Quarterly Tasks

- [ ] Review with business stakeholders
- [ ] Add new measures as needed
- [ ] Update documentation
- [ ] Performance benchmark

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Fallback to DirectQuery | Complex DAX or large table | Simplify measures, add filters |
| Stale data | Delta table not refreshed | Check pipeline status |
| Missing relationships | New tables added | Update semantic model |
| Slow visuals | Too much data scanned | Add filters, pre-aggregate |

### Support

- **Technical:** Review `troubleshooting` section in setup guide
- **Business:** Contact casino analytics team
- **Fabric:** Microsoft Fabric documentation

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [Setup Guide](setup-guide.md) | Step-by-step setup instructions |
| [DAX Measures](dax-measures.md) | Complete measure reference |
| [Architecture](../ARCHITECTURE.md) | System architecture |
| [Gold Layer Tutorial](../tutorials/03-gold-layer/README.md) | Gold table creation |
| [Direct Lake Tutorial](../tutorials/05-direct-lake-powerbi/README.md) | Direct Lake setup |

---

> **Documentation maintained by:** Microsoft Fabric POC Team
> **Repository:** [Suppercharge_Microsoft_Fabric](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric)
