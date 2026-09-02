---
hero: assets/heroes/compliance.svg
hero_alt: Compliance template — MICS Compliance Template
type: compliance
---
# 🏛️ MICS Compliance Template

> **Last Updated**: 2026-04-15 | **Version**: 2.0
> **Status**: ✅ Final | **Maintainer**: Documentation Team

<div align="center" markdown>

![Category](https://img.shields.io/badge/Category-Compliance-red)
![Status](https://img.shields.io/badge/Status-Final-green)
![Authority](https://img.shields.io/badge/Authority-NIGC-blue)

</div>

---

## 📖 Overview

This template provides guidance for implementing and reporting on National Indian Gaming Commission (NIGC) Minimum Internal Control Standards (MICS) requirements using the Casino Analytics platform.

---

## 📜 Regulatory Framework

| Requirement | Details |
|-------------|---------|
| **Authority** | National Indian Gaming Commission (NIGC) |
| **Regulation** | 25 CFR Part 542 |
| **Applicability** | Class II and Class III gaming operations |
| **Audit Frequency** | Annual (minimum) |

---

## 📑 MICS Categories

### Part 542 - Minimum Internal Control Standards

| Section | Category | Key Requirements |
|---------|----------|------------------|
| 542.12 | Bingo | Card tracking, prize payout, cash handling |
| 542.13 | Card Games | Drop/count, fills/credits, surveillance |
| 542.14 | Pull Tabs | Inventory, sales, prize redemption |
| 542.18 | Table Games | Drop, count, fills, credits, markers |
| 542.19 | Gaming Machines | Meter readings, drops, hopper fills |
| 542.21 | Drop/Count | Procedures, dual control, documentation |
| 542.22 | Cage/Credit | Accountability, reconciliation |
| 542.31 | Surveillance | Camera coverage, recording retention |

---

## 🎰 Gaming Machine Controls (542.19)

### Required Data Points

| Data Element | Source Table | Column | Frequency |
|--------------|--------------|--------|-----------|
| Coin-in meter | silver_slot_telemetry | total_coin_in | Daily |
| Coin-out meter | silver_slot_telemetry | total_coin_out | Daily |
| Jackpot meter | silver_slot_telemetry | jackpot_amount | Per event |
| Games played | silver_slot_telemetry | total_spins | Daily |
| Door access | bronze_machine_events | door_open_event | Per event |
| Error codes | bronze_machine_events | error_code | Per event |

### Daily Machine Reconciliation Query

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import *

spark = SparkSession.builder.getOrCreate()

def daily_machine_reconciliation(report_date: str):
    """
    Generate daily machine reconciliation report per MICS 542.19.

    Compares:
    - Opening meters vs closing meters
    - Calculated vs reported hold
    - Documented fills and jackpots
    """

    # Get meter readings
    df_meters = spark.table("bronze_machine_meters") \
        .filter(to_date("reading_timestamp") == report_date)

    # Get activity from telemetry
    df_activity = spark.table("silver_slot_telemetry") \
        .filter(to_date("event_timestamp") == report_date) \
        .groupBy("machine_id") \
        .agg(
            sum("bet_amount").alias("calculated_coin_in"),
            sum("win_amount").alias("calculated_coin_out"),
            count("*").alias("total_events"),
            sum(when(col("event_type") == "JACKPOT", col("win_amount")).otherwise(0)).alias("jackpot_total")
        )

    # Get physical counts
    df_drops = spark.table("bronze_drop_counts") \
        .filter(to_date("count_timestamp") == report_date) \
        .select("machine_id", "physical_drop_amount")

    # Reconciliation
    df_reconciliation = df_meters.alias("m") \
        .join(df_activity.alias("a"), "machine_id", "left") \
        .join(df_drops.alias("d"), "machine_id", "left") \
        .select(
            col("m.machine_id"),
            col("m.opening_coin_in").alias("meter_opening_coin_in"),
            col("m.closing_coin_in").alias("meter_closing_coin_in"),
            (col("m.closing_coin_in") - col("m.opening_coin_in")).alias("meter_coin_in_diff"),
            col("a.calculated_coin_in"),
            col("a.calculated_coin_out"),
            col("d.physical_drop_amount"),
            # Variance calculations
            (col("a.calculated_coin_in") - (col("m.closing_coin_in") - col("m.opening_coin_in"))).alias("coin_in_variance"),
            # Hold percentage
            ((col("a.calculated_coin_in") - col("a.calculated_coin_out")) / col("a.calculated_coin_in") * 100).alias("actual_hold_pct"),
            col("m.theoretical_hold_pct"),
            # Variance flag
            when(
                abs(col("a.calculated_coin_in") - (col("m.closing_coin_in") - col("m.opening_coin_in"))) > 100,
                "VARIANCE_ALERT"
            ).otherwise("OK").alias("status")
        )

    return df_reconciliation

# Generate report
reconciliation = daily_machine_reconciliation("2024-01-15")
reconciliation.show()

# Flag variances for review
variances = reconciliation.filter(col("status") == "VARIANCE_ALERT")
print(f"Machines with variances: {variances.count()}")
```

### SQL - Machine Meter Verification

```sql
-- MICS 542.19 - Daily machine meter verification
WITH meter_readings AS (
    SELECT
        machine_id,
        MAX(CASE WHEN reading_type = 'OPEN' THEN coin_in_meter END) as opening_meter,
        MAX(CASE WHEN reading_type = 'CLOSE' THEN coin_in_meter END) as closing_meter,
        MAX(CASE WHEN reading_type = 'OPEN' THEN coin_out_meter END) as opening_out,
        MAX(CASE WHEN reading_type = 'CLOSE' THEN coin_out_meter END) as closing_out
    FROM bronze_machine_meters
    WHERE reading_date = CURRENT_DATE - 1
    GROUP BY machine_id
),
calculated_activity AS (
    SELECT
        machine_id,
        SUM(bet_amount) as calc_coin_in,
        SUM(win_amount) as calc_coin_out,
        COUNT(*) as total_spins
    FROM silver_slot_telemetry
    WHERE CAST(event_timestamp AS DATE) = CURRENT_DATE - 1
      AND event_type = 'SPIN'
    GROUP BY machine_id
)
SELECT
    m.machine_id,
    m.closing_meter - m.opening_meter as meter_coin_in,
    a.calc_coin_in,
    (m.closing_meter - m.opening_meter) - a.calc_coin_in as variance,
    CASE
        WHEN ABS((m.closing_meter - m.opening_meter) - a.calc_coin_in) > 100 THEN 'INVESTIGATE'
        WHEN ABS((m.closing_meter - m.opening_meter) - a.calc_coin_in) > 10 THEN 'REVIEW'
        ELSE 'OK'
    END as status
FROM meter_readings m
LEFT JOIN calculated_activity a ON m.machine_id = a.machine_id
ORDER BY ABS(variance) DESC;
```

---

## 📦 Drop and Count Procedures (542.21)

### Drop Schedule Tracking

```python
def verify_drop_compliance(report_date: str):
    """
    Verify drop and count procedures per MICS 542.21.

    Checks:
    - All scheduled drops completed
    - Dual signature on count sheets
    - Variance within tolerance
    """

    # Scheduled drops
    df_schedule = spark.table("bronze_drop_schedule") \
        .filter(col("scheduled_date") == report_date)

    # Actual drops
    df_actual = spark.table("bronze_drop_counts") \
        .filter(to_date("count_timestamp") == report_date)

    # Compare
    df_compliance = df_schedule.alias("s") \
        .join(df_actual.alias("a"),
              (col("s.machine_id") == col("a.machine_id")) &
              (col("s.drop_type") == col("a.drop_type")),
              "left") \
        .select(
            col("s.machine_id"),
            col("s.drop_type"),
            col("s.scheduled_time"),
            col("a.count_timestamp").alias("actual_time"),
            col("a.counter_1_id"),
            col("a.counter_2_id"),
            col("a.physical_count"),
            col("a.system_expected"),
            (col("a.physical_count") - col("a.system_expected")).alias("variance"),
            # Compliance checks
            when(col("a.count_timestamp").isNull(), "MISSED_DROP")
                .when(col("a.counter_2_id").isNull(), "MISSING_DUAL_CONTROL")
                .when(abs(col("a.physical_count") - col("a.system_expected")) > 50, "VARIANCE")
                .otherwise("COMPLIANT").alias("compliance_status")
        )

    return df_compliance
```

---

## 📹 Surveillance Requirements (542.31)

### Camera Coverage Verification

| Area | Minimum Coverage | Recording Retention |
|------|------------------|---------------------|
| Gaming machines | All machines visible | 7 days minimum |
| Table games | All tables, drop boxes | 7 days minimum |
| Count room | Full room coverage | 7 days minimum |
| Cage | All windows, vault | 7 days minimum |
| Entrances/Exits | All points | 7 days minimum |

### Surveillance Log Query

```sql
-- Verify surveillance coverage per MICS 542.31
SELECT
    camera_zone,
    COUNT(DISTINCT camera_id) as camera_count,
    MIN(last_recording_check) as oldest_check,
    SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) as active_cameras,
    SUM(CASE WHEN status = 'OFFLINE' THEN 1 ELSE 0 END) as offline_cameras,
    SUM(CASE WHEN recording_available = FALSE THEN 1 ELSE 0 END) as missing_recordings
FROM surveillance_camera_status
WHERE check_date = CURRENT_DATE
GROUP BY camera_zone
HAVING SUM(CASE WHEN status = 'OFFLINE' THEN 1 ELSE 0 END) > 0
    OR SUM(CASE WHEN recording_available = FALSE THEN 1 ELSE 0 END) > 0;
```

---

## 📊 Audit Reports

### Monthly MICS Compliance Summary

```python
def generate_mics_compliance_report(report_month: str):
    """
    Generate monthly MICS compliance summary for audit.
    """

    report = {
        "report_period": report_month,
        "generated_at": datetime.now().isoformat(),
        "sections": {}
    }

    # Section 542.19 - Gaming Machines
    machine_compliance = spark.sql(f"""
        SELECT
            COUNT(DISTINCT machine_id) as total_machines,
            SUM(CASE WHEN daily_reconciled = TRUE THEN 1 ELSE 0 END) as reconciled_days,
            AVG(ABS(variance_pct)) as avg_variance_pct,
            MAX(ABS(variance_pct)) as max_variance_pct
        FROM gold.machine_daily_compliance
        WHERE report_month = '{report_month}'
    """).collect()[0]

    report["sections"]["542.19_gaming_machines"] = {
        "total_machines": machine_compliance.total_machines,
        "reconciliation_rate": machine_compliance.reconciled_days / 30 * 100,
        "avg_variance": machine_compliance.avg_variance_pct,
        "status": "COMPLIANT" if machine_compliance.avg_variance_pct < 0.5 else "REVIEW"
    }

    # Section 542.21 - Drop/Count
    drop_compliance = spark.sql(f"""
        SELECT
            COUNT(*) as total_drops,
            SUM(CASE WHEN dual_control = TRUE THEN 1 ELSE 0 END) as dual_control_count,
            SUM(CASE WHEN variance_within_tolerance = TRUE THEN 1 ELSE 0 END) as within_tolerance
        FROM gold.drop_count_compliance
        WHERE report_month = '{report_month}'
    """).collect()[0]

    report["sections"]["542.21_drop_count"] = {
        "total_drops": drop_compliance.total_drops,
        "dual_control_rate": drop_compliance.dual_control_count / drop_compliance.total_drops * 100,
        "tolerance_rate": drop_compliance.within_tolerance / drop_compliance.total_drops * 100,
        "status": "COMPLIANT" if drop_compliance.dual_control_count == drop_compliance.total_drops else "NON-COMPLIANT"
    }

    # Section 542.31 - Surveillance
    surveillance_compliance = spark.sql(f"""
        SELECT
            AVG(uptime_pct) as avg_uptime,
            MIN(retention_days) as min_retention,
            SUM(CASE WHEN coverage_complete = TRUE THEN 1 ELSE 0 END) as full_coverage_days
        FROM gold.surveillance_compliance
        WHERE report_month = '{report_month}'
    """).collect()[0]

    report["sections"]["542.31_surveillance"] = {
        "avg_uptime": surveillance_compliance.avg_uptime,
        "min_retention_days": surveillance_compliance.min_retention,
        "full_coverage_rate": surveillance_compliance.full_coverage_days / 30 * 100,
        "status": "COMPLIANT" if surveillance_compliance.min_retention >= 7 else "NON-COMPLIANT"
    }

    return report
```

---

## ⚠️ Variance Thresholds

| Category | Warning | Alert | Investigation |
|----------|---------|-------|---------------|
| Machine meters | 0.1% | 0.5% | 1.0% |
| Drop counts | $10 | $50 | $100 |
| Table fills | $100 | $500 | $1,000 |
| Credit transactions | Any | Any | Any |

---

## 📂 Documentation Requirements

### Required Records

| Record Type | Retention | Format |
|-------------|-----------|--------|
| Machine meter readings | 5 years | Digital + Paper backup |
| Drop/count worksheets | 5 years | Digital + Paper backup |
| Variance reports | 5 years | Digital |
| Surveillance logs | 7 days video / 1 year logs | Digital |
| Audit reports | 5 years | Digital + Paper |

---

## ✅ Audit Preparation Checklist

- [ ] All meter readings documented and reconciled
- [ ] Drop schedules complete with dual signatures
- [ ] Variances investigated and documented
- [ ] Surveillance recordings verified (7-day minimum)
- [ ] Employee access logs reviewed
- [ ] Jackpot documentation complete
- [ ] Fill/credit slips balanced
- [ ] Key control logs current
- [ ] Training records updated

---

## 📞 Contact

**Gaming Commission Liaison:** gaming-compliance@casino.com
**Internal Audit:** internal-audit@casino.com
**NIGC Contact:** https://www.nigc.gov

---

---

## 🔗 Related Documents

| Document | Description |
|----------|-------------|
| [Compliance Templates Overview](./README.md) | Index of all compliance templates |
| [CTR Template](./ctr-template.md) | Currency Transaction Report template |
| [SAR Template](./sar-template.md) | Suspicious Activity Report template |
| [W-2G Template](./w2g-template.md) | Gambling winnings tax reporting |
| [Data Dictionary](../data-dictionary/README.md) | Table schemas and field definitions |

---

[⬆️ Back to Top](#-mics-compliance-template) | [📚 Parent](./) | [🏠 Home](../index.md)
