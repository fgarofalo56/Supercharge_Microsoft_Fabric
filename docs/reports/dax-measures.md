# DAX Measures Reference

> **[Home](https://github.com/fgarofalo56/Supercharge_Microsoft_Fabric/blob/main/README.md)** > **[Reports](README.md)** > **DAX Measures**

**Last Updated:** `2025-01-21` | **Version:** 1.0.0

---

## Overview

This document contains all DAX measures for the Casino Analytics semantic model, organized by business domain. Copy these measures into your semantic model or use as reference for creating measures.

---

## Table of Contents

1. [Core Casino KPIs](#core-casino-kpis)
2. [Slot Performance](#slot-performance)
3. [Table Games](#table-games)
4. [Player Analytics](#player-analytics)
5. [Compliance Metrics](#compliance-metrics)
6. [Financial Metrics](#financial-metrics)
7. [Time Intelligence](#time-intelligence)
8. [Conditional Formatting](#conditional-formatting)
9. [Utility Measures](#utility-measures)

---

## Core Casino KPIs

### Revenue Measures

```dax
// Total Coin In - Total amount wagered across all slots
Total Coin In =
SUM(gold_slot_performance[total_coin_in])

// Total Coin Out - Total payouts to players
Total Coin Out =
SUM(gold_slot_performance[total_coin_out])

// Net Win - Casino revenue from gaming operations
Net Win =
[Total Coin In] - [Total Coin Out]

// Hold Percentage - Percentage of wagers retained by casino
Hold % =
DIVIDE([Net Win], [Total Coin In], 0) * 100

// Hold % Formatted - For display with symbol
Hold % Display =
FORMAT([Hold %], "0.00") & "%"
```

### Theoretical Metrics

```dax
// Theoretical Win - Expected revenue based on house edge
Theoretical Win =
SUMX(
    gold_slot_performance,
    gold_slot_performance[total_coin_in] *
    COALESCE(gold_slot_performance[_theoretical_hold_used], 0.08)
)

// Theoretical Win (Fixed Rate) - Using standard 8% hold
Theo Win 8pct =
[Total Coin In] * 0.08

// Hold Variance - Actual vs expected performance
Hold Variance =
[Net Win] - [Theoretical Win]

// Hold Variance Percentage
Hold Variance % =
DIVIDE([Hold Variance], [Theoretical Win], 0) * 100

// Variance Status - Performance indicator
Variance Status =
SWITCH(
    TRUE(),
    [Hold Variance %] > 20, "Outperforming",
    [Hold Variance %] > 5, "Above Expected",
    [Hold Variance %] >= -5, "Normal",
    [Hold Variance %] >= -20, "Below Expected",
    "Underperforming"
)
```

### Volume Metrics

```dax
// Total Games Played
Total Games =
SUM(gold_slot_performance[total_games])

// Total Events (Transactions)
Total Events =
SUM(gold_slot_performance[total_events])

// Total Sessions
Total Sessions =
SUM(gold_slot_performance[unique_sessions])

// Unique Players
Unique Players =
SUM(gold_slot_performance[unique_players])
```

---

## Slot Performance

### Machine Productivity

```dax
// Win Per Unit Per Day (WPUPD)
WPUPD =
DIVIDE(
    [Net Win],
    DISTINCTCOUNT(gold_slot_performance[machine_id]),
    0
)

// Coin In Per Machine
Coin In Per Machine =
DIVIDE(
    [Total Coin In],
    DISTINCTCOUNT(gold_slot_performance[machine_id]),
    0
)

// Games Per Machine
Games Per Machine =
DIVIDE(
    [Total Games],
    DISTINCTCOUNT(gold_slot_performance[machine_id]),
    0
)

// Average Bet Size
Avg Bet =
DIVIDE([Total Coin In], [Total Games], 0)

// Games Per Player (Engagement)
Games Per Player =
DIVIDE([Total Games], [Unique Players], 0)
```

### Jackpot Metrics

```dax
// Total Jackpot Payouts
Total Jackpots =
SUM(gold_slot_performance[jackpot_payouts])

// Jackpot Count
Jackpot Count =
SUM(gold_slot_performance[jackpot_count])

// Average Jackpot Amount
Avg Jackpot =
DIVIDE([Total Jackpots], [Jackpot Count], 0)

// Jackpot Ratio (% of Coin In)
Jackpot Ratio =
DIVIDE([Total Jackpots], [Total Coin In], 0) * 100
```

### Machine Performance Analysis

```dax
// Active Machines
Active Machines =
DISTINCTCOUNT(gold_slot_performance[machine_id])

// High Performing Machines
High Performers =
CALCULATE(
    DISTINCTCOUNT(gold_slot_performance[machine_id]),
    gold_slot_performance[performance_status] = "HIGH_PERFORMER"
)

// Underperforming Machines
Underperformers =
CALCULATE(
    DISTINCTCOUNT(gold_slot_performance[machine_id]),
    gold_slot_performance[performance_status] = "UNDERPERFORMER"
)

// Low Activity Machines
Low Activity Machines =
CALCULATE(
    DISTINCTCOUNT(gold_slot_performance[machine_id]),
    gold_slot_performance[performance_status] = "LOW_ACTIVITY"
)

// Performance Distribution
Performance Distribution =
DIVIDE(
    [High Performers],
    [Active Machines],
    0
) * 100
```

### Zone Analysis

```dax
// Net Win by Zone - Use with zone context
Zone Net Win =
CALCULATE([Net Win])

// Zone Contribution %
Zone Contribution % =
DIVIDE(
    [Net Win],
    CALCULATE([Net Win], ALL(gold_slot_performance[zone])),
    0
) * 100

// Zone Rank
Zone Rank =
RANKX(
    ALL(gold_slot_performance[zone]),
    [Net Win],
    ,
    DESC,
    Dense
)
```

---

## Table Games

### Drop and Win

```dax
// Total Drop (Buy-ins)
Total Drop =
SUM(gold_table_analytics[total_drop])

// Total Payouts
Table Payouts =
SUM(gold_table_analytics[total_payouts])

// Table Win
Table Win =
SUM(gold_table_analytics[table_win])

// Table Hold %
Table Hold % =
DIVIDE([Table Win], [Total Drop], 0) * 100
```

### Table Performance

```dax
// Active Tables
Active Tables =
SUM(gold_table_analytics[active_tables])

// Total Hands
Total Hands =
SUM(gold_table_analytics[total_hands])

// Hands Per Table
Hands Per Table =
DIVIDE([Total Hands], [Active Tables], 0)

// Drop Per Player
Drop Per Player =
SUM(gold_table_analytics[drop_per_player])

// Expected Hold %
Expected Table Hold % =
AVERAGE(gold_table_analytics[expected_hold_pct])

// Table Hold Variance
Table Hold Variance =
[Table Hold %] - [Expected Table Hold %]
```

### Game Type Analysis

```dax
// Blackjack Win
Blackjack Win =
CALCULATE(
    [Table Win],
    gold_table_analytics[game_type] = "BLACKJACK"
)

// Roulette Win
Roulette Win =
CALCULATE(
    [Table Win],
    gold_table_analytics[game_type] = "ROULETTE"
)

// Baccarat Win
Baccarat Win =
CALCULATE(
    [Table Win],
    gold_table_analytics[game_type] = "BACCARAT"
)

// Craps Win
Craps Win =
CALCULATE(
    [Table Win],
    gold_table_analytics[game_type] = "CRAPS"
)
```

---

## Player Analytics

### Player Counts

```dax
// Total Players
Total Players =
COUNTROWS(gold_player_360)

// VIP Players
VIP Players =
CALCULATE(
    COUNTROWS(gold_player_360),
    gold_player_360[vip_flag] = TRUE
)

// VIP Percentage
VIP % =
DIVIDE([VIP Players], [Total Players], 0) * 100

// Active Players (30 days)
Active Players 30D =
CALCULATE(
    COUNTROWS(gold_player_360),
    gold_player_360[days_since_visit] <= 30
)

// Active Players (7 days)
Active Players 7D =
CALCULATE(
    COUNTROWS(gold_player_360),
    gold_player_360[days_since_visit] <= 7
)

// Inactive Players (90+ days)
Inactive Players =
CALCULATE(
    COUNTROWS(gold_player_360),
    gold_player_360[days_since_visit] > 90
)
```

### Player Value

```dax
// Average Player Value Score
Avg Player Value =
AVERAGE(gold_player_360[player_value_score])

// Total Player Theo
Total Player Theo =
SUM(gold_player_360[total_theo_win])

// Avg Player Theo
Avg Player Theo =
AVERAGE(gold_player_360[total_theo_win])

// Player Lifetime Value (Estimated)
Total Player LTV =
SUMX(
    gold_player_360,
    gold_player_360[total_theo_win] *
    DIVIDE(365, COALESCE(gold_player_360[account_age_days], 1), 0) * 3
)
```

### Churn Analysis

```dax
// High Churn Risk Count
High Churn Risk =
CALCULATE(
    COUNTROWS(gold_player_360),
    gold_player_360[churn_risk] = "High"
)

// Medium-High Churn Risk
Medium High Churn =
CALCULATE(
    COUNTROWS(gold_player_360),
    gold_player_360[churn_risk] = "Medium-High"
)

// At-Risk Player Theo
At Risk Theo =
CALCULATE(
    SUM(gold_player_360[total_theo_win]),
    gold_player_360[churn_risk] IN {"High", "Medium-High"}
)

// Average Churn Risk Score
Avg Churn Score =
AVERAGE(gold_player_360[churn_risk_score])

// Churn Risk Distribution (for tooltip)
Churn Distribution =
VAR TotalPlayers = [Total Players]
VAR HighRisk = [High Churn Risk]
RETURN
"High Risk: " & HighRisk & " (" & FORMAT(DIVIDE(HighRisk, TotalPlayers, 0), "0.0%") & ")"
```

### Tier Analysis

```dax
// Diamond Players
Diamond Players =
CALCULATE(
    COUNTROWS(gold_player_360),
    gold_player_360[loyalty_tier] = "Diamond"
)

// Platinum Players
Platinum Players =
CALCULATE(
    COUNTROWS(gold_player_360),
    gold_player_360[loyalty_tier] = "Platinum"
)

// Gold Players
Gold Players =
CALCULATE(
    COUNTROWS(gold_player_360),
    gold_player_360[loyalty_tier] = "Gold"
)

// Silver Players
Silver Players =
CALCULATE(
    COUNTROWS(gold_player_360),
    gold_player_360[loyalty_tier] = "Silver"
)

// Bronze Players
Bronze Players =
CALCULATE(
    COUNTROWS(gold_player_360),
    gold_player_360[loyalty_tier] = "Bronze"
)

// Tier Theo Value
Tier Theo =
SUMX(
    VALUES(gold_player_360[loyalty_tier]),
    CALCULATE(SUM(gold_player_360[total_theo_win]))
)
```

### Player Engagement

```dax
// Average Days Since Visit
Avg Days Since Visit =
AVERAGE(gold_player_360[days_since_visit])

// Average Visit Frequency
Avg Visits =
AVERAGE(gold_player_360[total_visits])

// Slot vs Table Preference
Slot Preference % =
DIVIDE(
    CALCULATE(
        COUNTROWS(gold_player_360),
        gold_player_360[preferred_game_type] = "Slots"
    ),
    [Total Players],
    0
) * 100
```

---

## Compliance Metrics

### Filing Counts

```dax
// CTR (Currency Transaction Report) Count
CTR Count =
SUM(gold_compliance_reporting[ctr_count])

// SAR (Suspicious Activity Report) Count
SAR Count =
SUM(gold_compliance_reporting[sar_count])

// W-2G (Jackpot Tax Form) Count
W2G Count =
SUM(gold_compliance_reporting[w2g_count])

// Total Regulatory Filings
Total Filings =
[CTR Count] + [SAR Count] + [W2G Count]
```

### Filing Amounts

```dax
// CTR Total Amount
CTR Amount =
SUM(gold_compliance_reporting[ctr_total_amount])

// SAR Total Amount
SAR Amount =
SUM(gold_compliance_reporting[sar_total_amount])

// W2G Total Amount
W2G Amount =
SUM(gold_compliance_reporting[w2g_total_amount])

// Total Filing Amount
Total Filing Amount =
COALESCE([CTR Amount], 0) +
COALESCE([SAR Amount], 0) +
COALESCE([W2G Amount], 0)
```

### Filing Status

```dax
// Pending Filings
Pending Filings =
SUM(gold_compliance_reporting[pending_filings])

// Submitted Filings
Submitted Filings =
SUM(gold_compliance_reporting[submitted_filings])

// Filing Completion Rate
Filing Rate % =
DIVIDE(
    [Submitted Filings],
    [Submitted Filings] + [Pending Filings],
    1
) * 100
```

### Structuring Detection

```dax
// Structuring Suspects
Structuring Suspects =
SUM(gold_compliance_reporting[structuring_suspect_count])

// Structuring Amount
Structuring Amount =
SUM(gold_compliance_reporting[structuring_suspect_amount])

// Potential CTR (Unfiled)
Potential CTR Count =
SUM(gold_compliance_reporting[potential_ctr_count])

// Potential CTR Amount
Potential CTR Amount =
SUM(gold_compliance_reporting[potential_ctr_amount])
```

### Compliance Health

```dax
// Compliance Score (0-100)
Compliance Score =
VAR Pending = [Pending Filings]
VAR Structuring = [Structuring Suspects]
VAR TotalFilings = [Total Filings]
RETURN
SWITCH(
    TRUE(),
    Pending = 0 && Structuring = 0, 100,
    Structuring > 0, 60,
    Pending > 10, 70,
    Pending > 5, 80,
    90
)

// Compliance Status
Compliance Status =
SWITCH(
    TRUE(),
    [Compliance Score] >= 90, "Compliant",
    [Compliance Score] >= 70, "Attention Needed",
    "At Risk"
)

// Daily Filing Rate
Daily Filing Rate =
DIVIDE(
    [Total Filings],
    DISTINCTCOUNT(gold_compliance_reporting[report_date]),
    0
)
```

---

## Financial Metrics

### Transaction Volume

```dax
// Total Financial Transactions
Total Transactions =
SUM(gold_financial_summary[total_transactions])

// Unique Customers
Financial Customers =
SUM(gold_financial_summary[unique_customers])

// Total Volume
Total Volume =
SUM(gold_financial_summary[total_volume])

// Average Transaction
Avg Transaction =
DIVIDE([Total Volume], [Total Transactions], 0)
```

### Cash Flow

```dax
// Total Buy-Ins
Total Buy Ins =
SUM(gold_financial_summary[total_buy_ins])

// Total Cash Outs
Total Cash Outs =
SUM(gold_financial_summary[total_cash_outs])

// Net Cash Flow
Net Cash Flow =
[Total Buy Ins] - [Total Cash Outs]

// Total Markers
Total Markers =
SUM(gold_financial_summary[total_markers])

// Total Check Cashing
Total Check Cashing =
SUM(gold_financial_summary[total_check_cashing])
```

### Customer Metrics

```dax
// Average Customer Spend
Avg Customer Spend =
DIVIDE([Total Buy Ins], [Financial Customers], 0)

// CTR Filing Rate (Financial)
CTR Filing Rate =
AVERAGE(gold_financial_summary[ctr_filing_rate])
```

---

## Time Intelligence

### Month-to-Date

```dax
// Coin In MTD
Coin In MTD =
TOTALMTD([Total Coin In], dim_date[Date])

// Net Win MTD
Net Win MTD =
TOTALMTD([Net Win], dim_date[Date])

// Games MTD
Games MTD =
TOTALMTD([Total Games], dim_date[Date])
```

### Year-to-Date

```dax
// Coin In YTD
Coin In YTD =
TOTALYTD([Total Coin In], dim_date[Date])

// Net Win YTD
Net Win YTD =
TOTALYTD([Net Win], dim_date[Date])

// CTR Count YTD
CTR YTD =
TOTALYTD([CTR Count], dim_date[Date])
```

### Prior Period Comparison

```dax
// Net Win Previous Month
Net Win PM =
CALCULATE(
    [Net Win],
    DATEADD(dim_date[Date], -1, MONTH)
)

// Net Win Previous Year
Net Win PY =
CALCULATE(
    [Net Win],
    DATEADD(dim_date[Date], -1, YEAR)
)

// Net Win Growth MoM
Net Win MoM Growth % =
DIVIDE(
    [Net Win] - [Net Win PM],
    ABS([Net Win PM]),
    0
) * 100

// Net Win Growth YoY
Net Win YoY Growth % =
DIVIDE(
    [Net Win] - [Net Win PY],
    ABS([Net Win PY]),
    0
) * 100
```

### Rolling Averages

```dax
// 7-Day Rolling Average Coin In
Coin In 7D Avg =
AVERAGEX(
    DATESINPERIOD(dim_date[Date], MAX(dim_date[Date]), -7, DAY),
    [Total Coin In]
)

// 7-Day Rolling Average Net Win
Net Win 7D Avg =
AVERAGEX(
    DATESINPERIOD(dim_date[Date], MAX(dim_date[Date]), -7, DAY),
    [Net Win]
)

// 30-Day Rolling Average Net Win
Net Win 30D Avg =
AVERAGEX(
    DATESINPERIOD(dim_date[Date], MAX(dim_date[Date]), -30, DAY),
    [Net Win]
)
```

### Period Calculations

```dax
// Days in Selection
Days Selected =
DISTINCTCOUNT(dim_date[Date])

// First Date in Context
First Date =
MIN(dim_date[Date])

// Last Date in Context
Last Date =
MAX(dim_date[Date])
```

---

## Conditional Formatting

### Color Scales

```dax
// Hold Variance Color
Hold Variance Color =
SWITCH(
    TRUE(),
    [Hold Variance %] > 10, "#107C10",  // Green
    [Hold Variance %] > 0, "#498205",   // Light Green
    [Hold Variance %] >= -10, "#FFB900", // Yellow
    "#D13438"                            // Red
)

// Churn Risk Color
Churn Risk Color =
SWITCH(
    SELECTEDVALUE(gold_player_360[churn_risk]),
    "Active", "#107C10",
    "Low", "#498205",
    "Medium", "#FFB900",
    "Medium-High", "#F7630C",
    "High", "#D13438",
    "#605E5C"
)

// Compliance Status Color
Compliance Color =
SWITCH(
    [Compliance Status],
    "Compliant", "#107C10",
    "Attention Needed", "#FFB900",
    "At Risk", "#D13438",
    "#605E5C"
)
```

### Icon Sets

```dax
// Trend Icon
Trend Icon =
VAR Growth = [Net Win MoM Growth %]
RETURN
SWITCH(
    TRUE(),
    Growth > 5, UNICHAR(9650),   -- Up arrow
    Growth < -5, UNICHAR(9660),  -- Down arrow
    UNICHAR(9644)                -- Dash
)

// Status Icon
Performance Icon =
VAR Status = [Variance Status]
RETURN
SWITCH(
    Status,
    "Outperforming", UNICHAR(9733),  -- Star
    "Above Expected", UNICHAR(9650), -- Up
    "Normal", UNICHAR(9679),         -- Circle
    "Below Expected", UNICHAR(9660), -- Down
    UNICHAR(9888)                    -- Warning
)
```

---

## Utility Measures

### Formatting Helpers

```dax
// Currency Format
Currency Display =
VAR Value = [Net Win]
RETURN
IF(
    Value >= 1000000,
    FORMAT(Value / 1000000, "$#,##0.0") & "M",
    IF(
        Value >= 1000,
        FORMAT(Value / 1000, "$#,##0.0") & "K",
        FORMAT(Value, "$#,##0")
    )
)

// Percentage with Sign
Growth Display =
VAR Growth = [Net Win MoM Growth %]
RETURN
IF(
    Growth > 0,
    "+" & FORMAT(Growth, "0.0") & "%",
    FORMAT(Growth, "0.0") & "%"
)

// Blank if Zero
Net Win Safe =
IF([Net Win] = 0, BLANK(), [Net Win])
```

### Debug / Testing

```dax
// Row Count for Testing
_Row Count =
COUNTROWS(gold_slot_performance)

// Current Filter Context
_Filter Context =
CONCATENATEX(
    FILTERS(gold_slot_performance[zone]),
    gold_slot_performance[zone],
    ", "
)

// Last Refresh Time
_Last Refresh =
MAX(gold_slot_performance[_gold_timestamp])
```

---

## Usage Notes

### Measure Organization

Organize measures in folders by category:
- **Casino KPIs** - Core revenue metrics
- **Slot Performance** - Machine-level analysis
- **Table Games** - Table game metrics
- **Player Analytics** - Player behavior
- **Compliance** - Regulatory metrics
- **Time Intelligence** - Period calculations
- **Formatting** - Display helpers

### Performance Tips

1. Use `DIVIDE()` instead of `/` to handle division by zero
2. Avoid `CALCULATE(CALCULATE(...))` nesting
3. Use variables for repeated calculations
4. Filter early with `CALCULATETABLE`
5. Avoid `ALL()` on large tables without filters

### Direct Lake Considerations

1. Keep measures simple for Direct Lake optimization
2. Avoid iterators on large tables when possible
3. Use pre-aggregated Gold layer data
4. Test for fallback to DirectQuery mode

---

> **Questions?** Open an issue in the GitHub repository.
