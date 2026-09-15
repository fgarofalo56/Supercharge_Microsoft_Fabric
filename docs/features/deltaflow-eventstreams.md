---
hero: assets/heroes/features.svg
hero_alt: Fabric feature — DeltaFlow — Analytics-Ready CDC Streams in Eventstreams
type: feature
---
# 🌊 DeltaFlow — Analytics-Ready CDC Streams in Eventstreams (Preview)

<div align="center" markdown>

**Raw Debezium CDC In, Queryable Tables Out — No JSON Parsing Required**

![Category](https://img.shields.io/badge/Category-Data_Engineering-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-September_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-09-07` | **Version:** 1.0.0

---

## 🎯 Overview

**DeltaFlow** is a capability within Fabric Eventstreams (preview, announced March 2026) that transforms raw **Change Data Capture (CDC)** events from operational databases into **analytics-ready streaming data**. Instead of working with deeply nested Debezium JSON envelopes, you get **tabular rows that closely mirror the source table structure** — enriched with metadata columns describing each change.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Analytics-ready event shape** | CDC events transformed into tabular format reflecting the source table — query directly with KQL, no nested JSON parsing |
| **Automatic schema registration** | Source table schemas autodiscovered and registered with the Fabric Schema Registry |
| **Automatic destination table management** | Routing to a supported destination (e.g., Eventhouse) auto-creates and manages tables matching the source schema |
| **Schema evolution handling** | Source changes (new columns, new tables) are detected automatically — registered schemas and destination tables adjust accordingly |

### Supported CDC Sources

- Azure SQL Database CDC
- Azure SQL Managed Instance CDC
- SQL Server on VM CDC
- PostgreSQL Database CDC

To enable DeltaFlow, choose **"Analytics-ready events & auto-updated schema"** during the schema handling step when setting up a CDC connector as an Eventstream source.

---

## 🏗️ How the Transformation Works

### Before: Raw Debezium Envelope

CDC connectors emit nested JSON — accessing `OrderTotal` requires navigating into the `after` object. Querying directly with KQL or SQL is complex and error-prone.

### After: DeltaFlow Flattened Output

Source columns become top-level columns, plus five metadata columns:

| OrderID | CustomerName | OrderTotal | __dbz_operation | __dbz_timestamp | __dbz_server | __dbz_schema | __dbz_table |
|---------|-------------|-----------|-----------------|-----------------|--------------|--------------|-------------|
| 1001 | Contoso Ltd | 249.99 | Insert | 2026-03-07T00:00:00Z | fabsql | dbo | Orders |

### Operation Types

| Operation | `__dbz_operation` value | When |
|-----------|------------------------|------|
| **Insert** | `Insert` | New row, or initial snapshot of existing rows |
| **Update** | `Pre_Update` + `Post_Update` | **Two rows** per update — before and after state, same timestamp |
| **Delete** | `Delete` | Row deleted — contains last known values |

The Pre/Post_Update pair (similar to Delta Lake change data feed) enables field-level diffs, change tracking, and audit trails.

### Destination Table Mapping

When you route a DeltaFlow-enabled stream to a supported destination such as an Eventhouse, DeltaFlow automatically:

1. **Creates destination tables** matching the source table structure, with columns for each source column plus the five metadata columns
2. **Manages schema evolution** — when source tables change, DeltaFlow detects the changes, updates registered schemas, and adjusts destination tables accordingly

---

## 🏗️ Streaming Patterns

DeltaFlow is the reshaping layer in several published real-time patterns:

- **Customer-intent streaming**: Capture CDC events in Eventstream → reshape with DeltaFlow → enrich micro-batches with AI Functions → publish Business Events → activate responses while the signal is current
- **Row-to-intelligent-action**: CDC source → DeltaFlow → AI functions in a Spark Structured Streaming notebook classify each row by meaning and route actionable items to the right team in seconds

---

## 🎰 Casino/Gaming POC Applications

| Use Case | Application |
|----------|-------------|
| **Player profile changes** | Stream PostgreSQL CDC from the players system into Eventhouse as queryable rows — no Debezium parsing |
| **Cage transaction audit** | Pre/Post_Update pairs give a built-in audit trail of every cage transaction correction |
| **Loyalty tier changes** | Detect tier upgrades/downgrades as they happen and trigger Activator alerts to hosts |
| **Federal case management** | Stream case-status changes from SQL Server into real-time dashboards with automatic schema evolution |

---

## ⚠️ Limitations & Considerations

| Consideration | Detail |
|---------------|--------|
| **Preview status** | No SLA — test before production cutover |
| **Capacity** | Use Eventstreams with at least **F4** capacity units |
| **Source coverage** | Only the four listed CDC connectors support DeltaFlow |
| **Update semantics** | Two rows per update — downstream consumers must handle Pre/Post pairs deliberately |

---

## 🔗 Related Documents

- [Real-Time Intelligence](real-time-intelligence.md) — The parent workload
- [Copy Job CDC](copy-job-cdc.md) — Batch-oriented CDC alternative
- [Mirroring](mirroring.md) — Managed replication alternative (no event stream)
- [Anomaly Detection in RTI](anomaly-detection-rti.md) — Detect anomalies on the streamed data
- [Incremental Refresh & CDC](../best-practices/incremental-refresh-cdc.md) — CDC strategy comparison

---

## 📚 Microsoft Learn References

- [Overview of Microsoft Fabric eventstreams — DeltaFlow](https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/overview#deltaflow-analytics-ready-cdc-streams-preview)
- [DeltaFlow output transformation (preview)](https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/delta-flow-output-transformation)
- [Add Azure SQL Database CDC source](https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/add-source-azure-sql-database-change-data-capture)
- [Add PostgreSQL Database CDC source](https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/add-source-postgresql-database-change-data-capture)

---

> 📝 **Document Metadata**
> - **Author**: Documentation Team
> - **Reviewers**: Real-Time Engineering, Data Engineering
> - **Classification**: Internal
> - **Next Review**: 2026-12-07
