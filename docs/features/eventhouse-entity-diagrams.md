---
hero: assets/heroes/features.svg
hero_alt: Fabric feature — Eventhouse Entity Diagrams — Visual KQL Database Lineage
type: feature
---
# 🕸️ Eventhouse Entity Diagrams — Visual KQL Database Lineage

<div align="center" markdown>

**Visually Explore Relationships and Data Flow Across Your KQL Database**

![Category](https://img.shields.io/badge/Category-Real--Time_%26_Streaming-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Preview-orange?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-August_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-08-22` | **Version:** 1.0.0

---

## 🎯 Overview

**Entity diagrams** in Real-Time Intelligence render the lineage and relationships of KQL database items as an interactive graph. Instead of reconstructing data flow from memory or documentation, you can see — at a glance — how tables, materialized views, functions, external tables, and data connections relate, from source to destination.

The diagram simplifies database management: track dependencies before changing a schema, spot orphaned entities, understand ingestion paths, and take action directly from the visual.

!!! info "Preview feature"
    Entity diagrams are in [preview](https://learn.microsoft.com/fabric/fundamentals/preview). Behavior and availability may change before GA.

### What the Diagram Shows

| Element | Representation |
|---------|----------------|
| **Tables** | Nodes with row/ingestion context |
| **Materialized views** | Nodes linked to their source tables |
| **Functions** | Nodes linked to the tables/views they reference |
| **External tables** | Nodes representing OneLake/external sources |
| **Data connections** | Edges showing ingestion flow (Eventstream, SDKs, Kafka, Logstash, data flows) |
| **Update policies** | Edges showing table-to-table transformation chains |

---

## 🏗️ How It Works

```mermaid
flowchart LR
    subgraph Sources["📥 Sources"]
        ES["Eventstream"]
        KAFKA["Kafka"]
        SDK["SDKs / Logstash"]
    end

    subgraph KQLDB["🗄️ KQL Database"]
        RAW["raw_slot_telemetry<br/>(table)"]
        CLEAN["slot_telemetry_clean<br/>(table + update policy)"]
        AGG["slot_perf_hourly<br/>(materialized view)"]
        FN["GetMachineHealth()<br/>(function)"]
    end

    ES --> RAW
    KAFKA --> RAW
    SDK --> RAW
    RAW -->|"update policy"| CLEAN
    CLEAN --> AGG
    CLEAN --> FN

    style RAW fill:#2E86C1,stroke:#1B4F72,color:#fff
    style CLEAN fill:#148F77,stroke:#0B5345,color:#fff
    style AGG fill:#E67E22,stroke:#CA6F1E,color:#fff
```

The entity diagram renders exactly this shape from your live database metadata — no manual diagramming.

---

## 🔑 Prerequisites & Permissions

| Requirement | Detail |
|-------------|--------|
| **Workspace** | Fabric-enabled capacity with a KQL database |
| **View diagram** | Database **view** permissions |
| **Ingestion details** | Database **Admin** or **Monitor** role to see per-entity ingestion stats (see [KQL role-based access control](https://learn.microsoft.com/fabric/real-time-intelligence/manage-database-permissions)) |

---

## 🎰 Casino POC Use Cases

1. **Pre-change impact analysis** — before altering `raw_slot_telemetry`'s schema, open the entity diagram to see every downstream update policy, materialized view, and function that depends on it.
2. **Onboarding** — new engineers explore the real-time estate visually instead of reading KQL management commands.
3. **Orphan detection** — spot tables with no ingestion edges (stale connections) or views whose sources were dropped.
4. **Ingestion health** — with Admin/Monitor permissions, per-entity ingestion details surface which connections are flowing and which have stalled — complementing [Workspace Monitoring](workspace-monitoring.md).

For workspace-level lineage across *all* Fabric item types (not just KQL entities), see [Lineage](https://learn.microsoft.com/fabric/governance/lineage) in the governance docs — the two views are complementary.

---

## ⚠️ Considerations

| Consideration | Detail |
|---------------|--------|
| **Preview** | Not yet covered by production SLAs; validate before relying on it operationally |
| **KQL scope** | Shows entities within one KQL database — cross-database and cross-item lineage lives in workspace lineage |
| **Permissions-gated detail** | Ingestion stats require elevated database roles; viewers see structure only |

---

## 🔗 Related Documents

- [Real-Time Intelligence](real-time-intelligence.md) — Eventstreams, Eventhouse, KQL, and business events
- [Eventhouse Vector Database](eventhouse-vector-database.md) — Vector storage and search in Eventhouse
- [Workspace Monitoring](workspace-monitoring.md) — Activity, capacity, and item performance monitoring
- [Data Activator](data-activator.md) — Trigger actions on real-time conditions
- [Monitoring & Observability](../best-practices/monitoring-observability.md) — End-to-end observability patterns

---

> 📝 **Document Metadata**
> - **Author**: Documentation Team
> - **Reviewers**: Real-Time Engineering
> - **Classification**: Internal
> - **Next Review**: 2026-11-22
