# Power BI Semantic Model Setup Guide

> **[Home](https://github.com/fgarofalo56/Supercharge_Microsoft_Fabric/blob/main/README.md)** > **[Reports](README.md)** > **Setup Guide**

**Last Updated:** `2025-01-21` | **Version:** 1.0.0

---

## Prerequisites

Before starting, ensure you have:

- [ ] Microsoft Fabric workspace with at least Contributor access
- [ ] Gold layer tables populated in `lh_gold` lakehouse
- [ ] Power BI Pro or Premium Per User license
- [ ] Power BI Desktop (optional, for local development)

### Required Gold Tables

| Table | Purpose | Required |
|-------|---------|----------|
| `gold_slot_performance` | Slot machine KPIs | Yes |
| `gold_table_analytics` | Table games KPIs | Yes |
| `gold_player_360` | Player analytics | Yes |
| `gold_financial_summary` | Financial metrics | Yes |
| `gold_compliance_reporting` | Compliance tracking | Yes |
| `gold_security_dashboard` | Security events | Optional |

---

## Step 1: Create the Semantic Model

### Option A: Via Lakehouse UI (Recommended)

1. **Navigate to Lakehouse**
   - Open Microsoft Fabric portal
   - Go to your workspace (e.g., `casino-fabric-poc`)
   - Open `lh_gold` lakehouse

2. **Create New Semantic Model**
   - Click **New semantic model** button
   - Enter name: `Casino Analytics Model`
   - Verify storage mode shows **Direct Lake**

3. **Select Tables**

   Check the following tables:
   - [x] `gold_slot_performance`
   - [x] `gold_table_analytics`
   - [x] `gold_player_360`
   - [x] `gold_financial_summary`
   - [x] `gold_compliance_reporting`
   - [x] `gold_security_dashboard` (if available)

4. **Create Model**
   - Click **Create**
   - Wait for model to provision (1-2 minutes)

### Option B: Via Power BI Desktop

1. **Open Power BI Desktop**

2. **Connect to OneLake**
   - Get Data > Microsoft Fabric
   - Select **Lakehouse**
   - Choose workspace and `lh_gold` lakehouse
   - Select **DirectLake** mode

3. **Import Tables**
   - Select required Gold tables
   - Click **Load**

4. **Publish to Fabric**
   - File > Publish > Publish to Power BI
   - Select target workspace

---

## Step 2: Create Dimension Tables

The Gold layer contains denormalized facts. For optimal analysis, create dimension tables.

### Create dim_date Table

In the semantic model:

1. Click **New table**
2. Enter DAX expression:

```dax
dim_date =
VAR MinDate = DATE(2024, 1, 1)
VAR MaxDate = DATE(2025, 12, 31)
RETURN
ADDCOLUMNS(
    CALENDAR(MinDate, MaxDate),
    "date_key", INT(FORMAT([Date], "YYYYMMDD")),
    "Year", YEAR([Date]),
    "Quarter", "Q" & QUARTER([Date]),
    "Month", MONTH([Date]),
    "Month Name", FORMAT([Date], "MMMM"),
    "Month Short", FORMAT([Date], "MMM"),
    "Week", WEEKNUM([Date]),
    "Day", DAY([Date]),
    "Day Name", FORMAT([Date], "dddd"),
    "Day Short", FORMAT([Date], "ddd"),
    "Day of Week", WEEKDAY([Date]),
    "Is Weekend", IF(WEEKDAY([Date]) IN {1, 7}, TRUE, FALSE),
    "Is Holiday", FALSE, -- Update with actual holidays
    "Fiscal Year", IF(MONTH([Date]) >= 10, YEAR([Date]) + 1, YEAR([Date])),
    "Fiscal Quarter", "FQ" & SWITCH(TRUE(),
        MONTH([Date]) IN {10,11,12}, 1,
        MONTH([Date]) IN {1,2,3}, 2,
        MONTH([Date]) IN {4,5,6}, 3,
        4
    )
)
```

### Create dim_time Table (Optional)

For hourly analysis:

```dax
dim_time =
VAR Hours = GENERATESERIES(0, 23, 1)
VAR Minutes = {0, 15, 30, 45}
RETURN
ADDCOLUMNS(
    CROSSJOIN(Hours, Minutes),
    "time_key", [Value] * 100 + [Value1],
    "Hour", [Value],
    "Minute", [Value1],
    "Hour Label", FORMAT(TIME([Value], [Value1], 0), "hh:mm AM/PM"),
    "Hour24", FORMAT(TIME([Value], [Value1], 0), "HH:mm"),
    "Shift", SWITCH(TRUE(),
        [Value] >= 6 && [Value] < 14, "Day",
        [Value] >= 14 && [Value] < 22, "Swing",
        "Grave"
    ),
    "Is Peak Hour", [Value] IN {18, 19, 20, 21, 22}
)
```

---

## Step 3: Configure Relationships

### Open Model View

1. Click on semantic model name
2. Select **Model view** (diagram icon)

### Create Relationships

Create the following relationships by dragging fields:

| From Table | From Column | To Table | To Column | Cardinality | Direction |
|------------|-------------|----------|-----------|-------------|-----------|
| `dim_date` | `Date` | `gold_slot_performance` | `business_date` | Many-to-One | Single |
| `dim_date` | `Date` | `gold_table_analytics` | `event_date` | Many-to-One | Single |
| `dim_date` | `Date` | `gold_compliance_reporting` | `report_date` | Many-to-One | Single |
| `dim_date` | `Date` | `gold_financial_summary` | `report_date` | Many-to-One | Single |

### Relationship Settings

For each relationship:

1. Double-click the relationship line
2. Configure:
   - **Cardinality:** Many-to-One (or as specified)
   - **Cross-filter direction:** Single
   - **Make this relationship active:** Yes
   - **Assume referential integrity:** Yes (for Direct Lake performance)

### Inactive Relationships

Create inactive relationships for role-playing dimensions:

```
dim_date --> gold_player_360[first_visit] (inactive)
dim_date --> gold_player_360[last_visit] (inactive)
```

---

## Step 4: Add DAX Measures

### Create Measures Table

1. Click **New measure**
2. Enter: `_Measures = ""`
3. This creates a placeholder measures table

### Add Core Casino KPIs

Copy measures from `dax-measures.md` or add individually:

#### Revenue Measures

```dax
Total Coin In = SUM(gold_slot_performance[total_coin_in])

Total Coin Out = SUM(gold_slot_performance[total_coin_out])

Net Win = [Total Coin In] - [Total Coin Out]

Hold % =
DIVIDE([Net Win], [Total Coin In], 0) * 100

Theoretical Win =
SUMX(
    gold_slot_performance,
    gold_slot_performance[total_coin_in] * 0.08
)

Hold Variance = [Net Win] - [Theoretical Win]

Hold Variance % =
DIVIDE([Hold Variance], [Theoretical Win], 0) * 100
```

#### Player Measures

```dax
Total Players = COUNTROWS(gold_player_360)

VIP Players =
CALCULATE(
    COUNTROWS(gold_player_360),
    gold_player_360[vip_flag] = TRUE
)

Active Players 30D =
CALCULATE(
    COUNTROWS(gold_player_360),
    gold_player_360[days_since_visit] <= 30
)

High Churn Risk =
CALCULATE(
    COUNTROWS(gold_player_360),
    gold_player_360[churn_risk] = "High"
)

Avg Player Value Score =
AVERAGE(gold_player_360[player_value_score])

Total Player Theo =
SUM(gold_player_360[total_theo_win])
```

#### Compliance Measures

```dax
CTR Count = SUM(gold_compliance_reporting[ctr_count])

SAR Count = SUM(gold_compliance_reporting[sar_count])

W2G Count = SUM(gold_compliance_reporting[w2g_count])

Total Filings = [CTR Count] + [SAR Count] + [W2G Count]

CTR Total Amount = SUM(gold_compliance_reporting[ctr_total_amount])

Pending Filings = SUM(gold_compliance_reporting[pending_filings])
```

---

## Step 5: Create Reports

### Method 1: From Semantic Model

1. Open semantic model
2. Click **Create report**
3. Design report using visuals

### Method 2: Import Report Definitions

1. Open report definition JSON file
2. Use as visual specification guide
3. Manually recreate visuals in Power BI

### Executive Dashboard Layout

```
+----------------------------------------------------------+
| Casino Executive Dashboard              [Date Slicer]     |
+------------+------------+------------+------------+-------+
|  Net Win   |  Hold %    | Players    |  Games     | Zone  |
|  $2.5M     |   8.2%     |  12,450    |  1.2M      |[List] |
+------------+------------+------------+------------+-------+
|                    Net Win Trend (Line Chart)             |
|         X: Date  Y: Net Win  Line: Zone                  |
+---------------------------+-------------------------------+
|   Zone Performance        |        Top 10 Machines        |
|   (Horizontal Bar)        |   (Table with conditional)    |
+---------------------------+-------------------------------+
|   Compliance Summary      |   Player Tier Distribution    |
|   (Multi-row Card)        |   (Donut Chart)               |
+---------------------------+-------------------------------+
```

### Adding Visuals

#### KPI Cards

1. Add **Card** visual
2. Fields: Select measure (e.g., `[Net Win]`)
3. Format:
   - Display units: Auto
   - Decimal places: 2
   - Font size: 24pt
   - Data label: On

#### Line Chart (Trend)

1. Add **Line Chart** visual
2. X-axis: `dim_date[Date]`
3. Y-axis: `[Net Win]`
4. Legend: `gold_slot_performance[zone]` (optional)
5. Format:
   - X-axis: Date hierarchy (Month > Day)
   - Y-axis: Start at 0
   - Data labels: Off

#### Bar Chart (Zone Performance)

1. Add **Clustered Bar Chart** visual
2. Y-axis: `gold_slot_performance[zone]`
3. X-axis: `[Net Win]`
4. Sort: Descending by X-axis
5. Format:
   - Data colors: By zone
   - Data labels: On

#### Table (Top Machines)

1. Add **Table** visual
2. Columns:
   - `gold_slot_performance[machine_id]`
   - `gold_slot_performance[zone]`
   - `[Net Win]`
   - `[Hold %]`
   - `[Total Games]`
3. Filters:
   - Top N: Top 10 by `[Net Win]`
4. Format:
   - Conditional formatting on Hold %

---

## Step 6: Configure Row-Level Security

### Create Security Role

1. In semantic model, click **Manage roles**
2. Click **Create**
3. Name: `ZoneAccess`

### Define Filter Expression

```dax
// Zone-based security
[Zone] = LOOKUPVALUE(
    SecurityTable[Zone],
    SecurityTable[UserEmail],
    USERPRINCIPALNAME()
)
```

### Alternative: Direct Zone Assignment

```dax
// Simpler approach for POC
gold_slot_performance[zone] IN {"High Limit", "Main Floor"}
```

### Test Security

1. Click **View as role**
2. Select `ZoneAccess`
3. Verify data filtering works

---

## Step 7: Publish and Share

### Publish Report

1. In Power BI Desktop: **File > Publish**
2. Select workspace: `casino-fabric-poc`
3. Click **Publish**

### Configure Workspace Access

1. Open workspace settings
2. Add users/groups with appropriate roles:
   - **Viewer:** Read-only access to reports
   - **Contributor:** Edit reports and models
   - **Admin:** Full workspace management

### Create App (Optional)

1. Click **Create app**
2. Configure app settings
3. Add reports to app
4. Publish to organization

---

## Step 8: Set Up Scheduled Delivery

### Email Subscriptions

1. Open report
2. Click **Subscribe**
3. Configure:
   - Schedule: Daily at 7:00 AM
   - Recipients: Distribution list
   - Format: Full report or specific pages

### Data-Driven Alerts

1. On KPI card, click **...**
2. Select **Manage alerts**
3. Configure threshold alerts

---

## Verification Checklist

- [ ] Semantic model created with Direct Lake mode
- [ ] All Gold tables imported
- [ ] Dimension tables created (dim_date)
- [ ] Relationships configured correctly
- [ ] All DAX measures calculating properly
- [ ] Reports created and formatted
- [ ] RLS configured and tested
- [ ] Published to workspace
- [ ] Users have appropriate access

---

## Troubleshooting

### Issue: Data Not Refreshing

**Symptoms:** Report shows stale data

**Solutions:**
1. Check that Gold layer notebooks completed
2. Verify Direct Lake mode is active (not fallback)
3. Check lakehouse permissions

### Issue: Slow Performance

**Symptoms:** Reports load slowly

**Solutions:**
1. Add filters to reduce data scanned
2. Simplify complex measures
3. Check Gold table partitioning
4. Reduce visuals per page

### Issue: Relationship Errors

**Symptoms:** Measures return incorrect values

**Solutions:**
1. Verify relationship cardinality
2. Check for ambiguous paths
3. Use USERELATIONSHIP for inactive relationships

### Issue: DirectLake Fallback

**Symptoms:** Queries fall back to DirectQuery

**Solutions:**
1. Simplify calculated columns
2. Avoid unsupported DAX functions
3. Reduce table row counts
4. Check Fabric capacity

---

## Next Steps

1. Review [DAX Measures Reference](dax-measures.md)
2. Customize report definitions in `report-definitions/`
3. Create additional reports as needed
4. Set up monitoring and alerts

---

> **Questions?** Open an issue in the GitHub repository.
