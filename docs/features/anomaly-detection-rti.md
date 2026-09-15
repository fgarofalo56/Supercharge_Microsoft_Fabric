---
hero: assets/heroes/features.svg
hero_alt: Fabric feature — Anomaly Detection in Real-Time Intelligence — No-Code Outlier Detection
type: feature
---
# 📉 Anomaly Detection in Real-Time Intelligence (Preview)

<div align="center" markdown>

**Automatic Outlier Detection on Live Eventhouse Data — No Data Science Expertise Required**

![Category](https://img.shields.io/badge/Category-AI_%26_ML-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-September_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-09-07` | **Version:** 1.0.0

---

## 🎯 Overview

The **Anomaly Detector** in Real-Time Intelligence automatically identifies unusual patterns and outliers in streaming or time-series data. Detection runs **natively against live Eventhouse tables and incoming streaming data** — no copying or exporting — supporting both real-time detection and evaluation over historical windows.

Unlike static threshold-based alerts, the anomaly detector **adapts to historical trends and seasonality**, making it effective at identifying subtle or context-sensitive issues: system failures, fraud, performance degradation, or other critical events. When an anomaly is detected, it can trigger downstream actions through **Activator** — alerts, dashboard updates, or automated workflows — and anomaly events can be consumed by **Fabric data agents** for automated reasoning.

### Built-In Models

| Model | Algorithm | Best For |
|-------|-----------|----------|
| **Signal Watcher** | SR (TSB-AD) | Subtle shifts to sharp spikes |
| **Signal Watcher (Seasonal)** | SR + seasonality | Signals with regular cycles |
| **Signal Watcher (Enhanced Seasonal)** | SR + complex seasonality | Multiple overlapping seasonal patterns |
| **Histogram Sentinel** | HBOS | Distribution-based anomalies at scale |
| **Pattern Proximity** | KNN | Local pattern shifts |
| **Core Pattern Finder** | PCA | Subtle, hidden anomalies in complex data |
| **Change Spike Detector** | MS-developed | Sharp, local changes |
| **Rolling Change Tracker** | MS-developed | Gradual trend shifts |

The system **recommends models** based on your data's characteristics — you can switch between recommendations and tune confidence levels (low/medium/high) to balance detection sensitivity against false positives.

---

## 🏗️ Setup

Three entry points:

1. **From an Eventhouse table** — select the table, then **Create Anomaly Detector** in the toolbar
2. **From Real-Time hub** — find the table, select **Anomaly detection**, then **Create detector**
3. **From the Create pane** — **Create → Real-Time Intelligence → Anomaly detection**, then select your data source

After analysis, you can:

- **Save** the detector to preserve the configuration
- **Publish** detected anomalies to the Real-Time Hub for **continuous monitoring** of incoming live data — without duplicating the dataset
- **Set alerts** via Activator, or connect anomaly events to **data agents**
- **Open in a Fabric notebook** for advanced exploration with KQL, SQL, Python, or Spark
- **Query results via the SQL endpoint** of the Eventhouse for downstream BI

### Prerequisites

1. Workspace with a Fabric-enabled capacity; **Admin, Contributor, or Member** role
2. An **Eventhouse** with a KQL database
3. **Python plugin enabled** on the Eventhouse (Python 3.11.7 DL plugin) — the detector can auto-enable it, but enabling can take **up to one hour**
4. The **"Detect anomalies in Real-Time Intelligence (Preview)"** tenant switch enabled in the Admin portal
5. **Sufficient historical data** — daily data needs a few months; per-second data may need only days

### Required Table Schema

The input table must have a **numeric value column**, a **datetime column**, and a **string column** — otherwise anomaly detection is disabled.

---

## 🎰 Casino/Gaming POC Applications

| Use Case | Application |
|----------|-------------|
| **Slot floor monitoring** | Detect machines with anomalous hold percentages or coin-in patterns in near real time |
| **Fraud detection** | Flag unusual player betting patterns that static thresholds miss (seasonality-aware) |
| **Cage operations** | Detect anomalous cash flow variances by shift and window |
| **AML pattern detection** | Surface structuring patterns (multiple $8K–$9.9K transactions) as anomalies for SAR review |
| **Federal program integrity** | Detect anomalous grant disbursement patterns across agencies |

---

## ⚠️ Limitations, Concurrency & Billing

| Consideration | Detail |
|---------------|--------|
| **Single model per detector** | Each anomaly detector supports only one model configuration |
| **Concurrency limit** | Eventhouse supports up to **8 concurrent queries** per Eventhouse — excess queries are retried but not queued and may silently fail; let each query complete before starting another |
| **Reanalysis impact** | Reanalyzing with new data updates the model used by **existing monitoring rules** — downstream actions may be affected |
| **Preview** | No SLA; billing started **December 2025** |

### Billing

Anomaly Detector uses one dedicated meter — **"Anomaly Detector Queries Capacity Usage CU"** (operation: *Anomaly Detection Run Queries*). Billing is tied to **query execution**, not data volume:

- **Interactive analysis** accrues CUs per query when you run detection or switch models
- **Continuous monitoring** accrues CUs per monitoring query — check frequency directly drives cost

Monitor consumption in the **Microsoft Fabric Capacity Metrics app**.

---

## 🔗 Related Documents

- [Real-Time Intelligence](real-time-intelligence.md) — The parent workload (Eventhouse, Eventstreams, Activator)
- [Data Activator](data-activator.md) — Alerting and actions on detected anomalies
- [DeltaFlow CDC Streams](deltaflow-eventstreams.md) — Streaming CDC data that anomaly detection can monitor
- [Eventhouse Vector Database](eventhouse-vector-database.md) — Complementary ML capability on the same engine
- [Capacity Planning & Cost Optimization](../best-practices/capacity-planning-cost-optimization.md) — CU consumption management

---

## 📚 Microsoft Learn References

- [Anomaly detection in Real-Time Intelligence (Preview)](https://learn.microsoft.com/fabric/real-time-intelligence/anomaly-detection)
- [Specifications of anomaly detection models in Fabric (Preview)](https://learn.microsoft.com/fabric/real-time-intelligence/anomaly-detection-models)
- [Anomaly detector capacity usage and billing](https://learn.microsoft.com/fabric/real-time-intelligence/anomaly-detection-billing)
- [Multivariate anomaly detection overview](https://learn.microsoft.com/fabric/real-time-intelligence/multivariate-anomaly-overview)
- [Set alerts on anomaly detection events](https://learn.microsoft.com/fabric/real-time-hub/set-alerts-anomaly-detection)

---

> 📝 **Document Metadata**
> - **Author**: Documentation Team
> - **Reviewers**: Real-Time Engineering, Data Science, Compliance
> - **Classification**: Internal
> - **Next Review**: 2026-12-07
