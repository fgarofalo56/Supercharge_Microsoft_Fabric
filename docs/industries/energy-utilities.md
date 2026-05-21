[Home](../index.md) > [Docs](../) > [Industries](./) > Energy & Utilities

![Energy & Utilities — Smart grid, load forecasting on Fabric](../assets/heroes/energy-utilities.svg){ .hero-banner }

# ⚡ Energy & Utilities — Smart Grid Analytics & Renewable Forecasting


<div align="center" markdown>

**Grid-scale analytics, outage prediction, and NERC CIP compliance on Microsoft Fabric**

![Category](https://img.shields.io/badge/Category-Industry_Vertical-teal?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-May_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-05-05` | **Version:** 1.0.0

---

> *"The modern grid generates terabytes of AMI, SCADA, and weather data daily — the utilities that turn that data into real-time decisions will lead the energy transition."*

---

## 📑 Table of Contents

- [Scenario Overview](#-scenario-overview)
- [Regulatory Landscape](#-regulatory-landscape)
- [Data Flow Architecture](#-data-flow-architecture)
- [Why Fabric for Energy and Utilities](#-why-fabric-for-energy-and-utilities)
- [Getting Started](#-getting-started)
- [References](#-references)

---

## 🎯 Scenario Overview

| Scenario | Fabric Pattern | Latency Target | Key Features |
|----------|---------------|----------------|--------------|
| Smart meter (AMI) analytics | Eventstream → Eventhouse + Lakehouse Bronze | < 15 sec | [RTI](../features/real-time-intelligence.md), [Medallion Architecture](../best-practices/medallion-architecture-deep-dive.md) |
| Outage prediction & restoration | Gold feature store + AutoML classification model | 15-min intervals | [AutoML](../features/automl-model-endpoints.md), [Data Activator](../best-practices/alerting-data-activator.md) |
| Renewable generation forecasting | Lakehouse Gold + AutoML time-series model | Hourly | [AutoML](../features/automl-model-endpoints.md), [Semantic Link](../features/semantic-link.md) |
| Grid digital twin | Digital Twin Builder with SCADA binding | < 5 sec | [Digital Twin Builder](../features/digital-twin-builder.md), [RTI](../features/real-time-intelligence.md) |
| Regulatory compliance reporting | Warehouse star schema + Direct Lake | Monthly/Quarterly | [Warehouse Setup](../best-practices/08_WAREHOUSE_SETUP.md), [Direct Lake](../features/direct-lake.md) |
| Vegetation management (wildfire risk) | Lakehouse Gold with geospatial + weather overlays | Daily | [Maps in Fabric](../features/maps-in-fabric.md), [Medallion Architecture](../best-practices/medallion-architecture-deep-dive.md) |

---

## 📋 Regulatory Landscape

| Framework | Applicability | Fabric Controls |
|-----------|--------------|-----------------|
| **NERC CIP** (Critical Infrastructure Protection) | Bulk electric system cyber assets and electronic security perimeters | [Network Security](../best-practices/network-security.md) managed private endpoints, [Outbound Access Protection](../best-practices/outbound-access-protection.md), [RBAC](../best-practices/identity-rbac-patterns.md) |
| **FERC Order 2222** | Distributed energy resource aggregation and market participation | Lakehouse Gold aggregation layer for DER portfolio analytics |
| **EPA Clean Air Act / GHGRP** | Greenhouse gas reporting for fossil generation | [SQL Audit Logs](../best-practices/sql-audit-logs-compliance.md) for emissions data lineage, [Data Governance](../best-practices/data-governance-deep-dive.md) |
| **DOE Cybersecurity Capability Maturity Model (C2M2)** | Cybersecurity practices for energy subsector | [Zero Trust Blueprint](../best-practices/security/zero-trust-blueprint.md), [Monitoring](../best-practices/monitoring-observability.md) |
| **State PUC Reliability Standards** | SAIDI/SAIFI/CAIDI performance metrics | Gold-layer reliability KPIs with Direct Lake dashboards |

---

## 🏗️ Data Flow Architecture

```mermaid
flowchart LR
    subgraph Sources["⚡ Data Sources"]
        AMI["Smart Meters<br/>(AMI Head-End)"]
        SCADA["SCADA / DCS<br/>(OPC UA)"]
        WX["Weather<br/>Services API"]
        GIS["GIS Asset<br/>Registry"]
        MKT["Energy Market<br/>(ISO/RTO Feeds)"]
    end

    subgraph Bronze["🥉 Bronze Layer"]
        B1["Meter Reads<br/>(Eventstream)"]
        B2["SCADA Telemetry<br/>(Eventstream)"]
        B3["Weather Forecasts<br/>(hourly API pull)"]
        B4["Asset Geometry<br/>(GIS export)"]
        B5["Market Prices<br/>(append-only)"]
    end

    subgraph Silver["🥈 Silver Layer"]
        S1["Meter Intervals<br/>(validated, gap-filled)"]
        S2["Grid Telemetry<br/>(downsampled)"]
        S3["Weather Grid<br/>(normalized)"]
        S4["Asset Master<br/>(enriched)"]
    end

    subgraph Gold["🥇 Gold Layer"]
        G1["Load Forecasting<br/>Feature Store"]
        G2["Outage Risk<br/>Scores"]
        G3["Renewable<br/>Generation KPIs"]
        G4["Reliability<br/>(SAIDI/SAIFI)"]
    end

    subgraph BI["📊 Consumption"]
        DTB["Digital Twin<br/>Builder (Grid)"]
        EVH["Eventhouse<br/>(real-time KQL)"]
        DL["Direct Lake<br/>Semantic Model"]
        PBI["Power BI<br/>Dashboards"]
        DA["Data Activator<br/>Outage Alerts"]
    end

    AMI --> B1
    SCADA --> B2
    WX --> B3
    GIS --> B4
    MKT --> B5

    B1 --> S1
    B2 --> S2
    B3 --> S3
    B4 --> S4
    B5 --> S1

    S1 --> G1
    S1 --> G4
    S2 --> G2
    S3 --> G1
    S3 --> G3
    S4 --> G2

    G1 --> DL --> PBI
    G2 --> DL
    G3 --> DL
    G4 --> DL
    B2 --> EVH --> DTB
    G2 --> DA
```

---

## 💡 Why Fabric for Energy and Utilities

**Scale to billions of meter reads without custom infrastructure.** AMI head-end systems generate 96+ interval reads per meter per day. Eventstreams ingest this volume directly into Eventhouse for real-time analytics and Lakehouse Bronze for historical analysis — no Hadoop clusters or custom Kafka consumers required.

**Grid digital twin built on the analytics platform.** Digital Twin Builder models substations, feeders, and distributed energy resources with real-time SCADA binding, enabling operators to visualize grid state in Eventhouse KQL dashboards alongside historical trends.

**Outage prediction with built-in ML.** AutoML trains classification models on weather, vegetation, asset age, and historical outage data, scoring feeder-level risk every 15 minutes and triggering Data Activator alerts for proactive crew dispatch.

**NERC CIP compliance without bolt-on tools.** Managed private endpoints, customer-managed keys, identity-based RBAC, and SQL audit logs provide the access control, encryption, and audit evidence that NERC CIP standards require — all native to Fabric.

**Renewable forecasting at Direct Lake speed.** Wind and solar generation predictions run through AutoML time-series models and surface in Direct Lake Power BI dashboards, giving dispatchers sub-second access to generation-vs-load balance metrics.

---

## 🚀 Getting Started

1. **Ingest AMI and SCADA data** — Configure [Eventstreams](../features/real-time-intelligence.md) to pull meter reads and SCADA telemetry into Eventhouse and Lakehouse Bronze.
2. **Build the medallion Lakehouse** — Follow [Medallion Deep Dive](../best-practices/medallion-architecture-deep-dive.md) for meter, asset, weather, and market data.
3. **Apply NERC CIP controls** — Enable [Network Security](../best-practices/network-security.md) private endpoints, [CMK](../best-practices/customer-managed-keys.md), and [RBAC](../best-practices/identity-rbac-patterns.md) aligned to CIP-004/005/007.
4. **Model the grid** — Use [Digital Twin Builder](../features/digital-twin-builder.md) to create substation and feeder entities with live SCADA binding.
5. **Deploy outage prediction** — Train classification models via [AutoML](../features/automl-model-endpoints.md) and wire [Data Activator](../best-practices/alerting-data-activator.md) for proactive alerts.
6. **Build reliability dashboards** — Create SAIDI/SAIFI/CAIDI reports with [Direct Lake](../features/direct-lake.md) over Gold reliability tables.

---

## 📚 References

| Resource | Link |
|----------|------|
| Real-Time Intelligence | [RTI Guide](../features/real-time-intelligence.md) |
| Digital Twin Builder | [DTB Guide](../features/digital-twin-builder.md) |
| Direct Lake connectivity | [Direct Lake Guide](../features/direct-lake.md) |
| AutoML Model Endpoints | [AutoML Guide](../features/automl-model-endpoints.md) |
| Network Security | [Network Security](../best-practices/network-security.md) |
| Maps in Fabric | [Maps Guide](../features/maps-in-fabric.md) |
| Capacity Planning | [Capacity Guide](../best-practices/capacity-planning-cost-optimization.md) |
| BCDR | [Disaster Recovery](../best-practices/disaster-recovery-bcdr.md) |
