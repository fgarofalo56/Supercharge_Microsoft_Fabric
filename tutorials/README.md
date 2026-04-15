# 📖 Tutorials

> 🏠 [Home](../README.md) > 📖 Tutorials

**Last Updated:** `2026-03-11` | **Version:** 2.0.0

---

## 📑 Table of Contents

- [🎯 Overview](#-overview)
- [🗺️ Learning Path](#️-learning-path)
- [📋 Tutorial Index](#-tutorial-index)
- [⏱️ Time Estimates](#️-time-estimates)
- [📋 Prerequisites](#-prerequisites)

---

## 🎯 Overview

This tutorial series of 37 tutorials guides you through implementing a complete Microsoft Fabric data platform for casino/gaming and federal agency analytics. Starting from environment setup through advanced AI/ML, migration, streaming, federal agency POCs, and enterprise best practices, you'll learn industry best practices for medallion architecture, real-time analytics, and data governance.

### What You'll Build

```mermaid
flowchart LR
    subgraph L1["🟢 Foundation"]
        T00[00-Setup]
        T01[01-Bronze]
    end

    subgraph L2["🟡 Core"]
        T02[02-Silver]
        T03[03-Gold]
    end

    subgraph L3["🟠 Advanced"]
        T04[04-Real-Time]
        T05[05-Direct Lake]
    end

    subgraph L4["🔴 Enterprise"]
        T06[06-Pipelines]
        T07[07-Governance]
        T08[08-Mirroring]
        T09[09-AI/ML]
    end

    subgraph L5["🟣 Migration & Integration"]
        T10[10-Teradata]
        T11[11-SAS]
    end

    subgraph L6["🔵 DevOps & Planning"]
        T12[12-CI/CD]
        T13[13-Planning]
    end

    subgraph L7["⚪ Operations & Governance"]
        T14[14-Security]
        T15[15-Cost]
        T16[16-Performance]
        T17[17-Monitoring]
    end

    subgraph L8["🟤 Collaboration & AI"]
        T18[18-Sharing]
        T19[19-Copilot]
    end

    subgraph L9["🟡 Infrastructure & GeoAnalytics"]
        T20[20-Workspace]
        T21[21-GeoAnalytics]
        T22[22-Networking]
        T23[23-Gateways]
    end

    subgraph L10["🟢 Migration & Streaming"]
        T24[24-Snowflake]
        T25[25-DB2]
        T26[26-Streaming]
    end

    subgraph L11["🔴 Analytics & Federal"]
        T27[27-Video]
        T28[28-Movement]
        T29[29-Geo]
        T30[30-Healthcare]
        T31[31-DOT/FAA]
    end

    subgraph L12["🌿 Federal Agency POCs"]
        T32[32-USDA]
        T33[33-SBA]
        T34[34-NOAA]
        T35[35-EPA]
        T36[36-DOI]
    end

    T00 --> T01 --> T02 --> T03 --> T04 --> T05
    T05 --> T06 --> T07 --> T08 --> T09
    T09 --> T10 --> T11
    T11 --> T12 --> T13
    T13 --> T14 --> T15 --> T16 --> T17
    T17 --> T18 --> T19
    T19 --> T20 --> T21 --> T22 --> T23
    T23 --> T24 --> T25 --> T26
    T26 --> T27 --> T28 --> T29 --> T30 --> T31
    T31 --> T32 --> T33 --> T34 --> T35 --> T36
```

---

## 🗺️ Learning Path

### Recommended Order

Complete tutorials in sequence for the best learning experience:

```
╔════════╦════════╦════════╦════════╦════════╦════════╦════════╦════════╦════════╦════════╗
║   00   ║   01   ║   02   ║   03   ║   04   ║   05   ║   06   ║   07   ║   08   ║   09   ║
║ SETUP  ║ BRONZE ║ SILVER ║  GOLD  ║  RT    ║  PBI   ║ PIPES  ║  GOV   ║ MIRROR ║  AI/ML ║
╠════════╬════════╬════════╬════════╬════════╬════════╬════════╬════════╬════════╬════════╣
║   ⭐   ║   ⭐   ║   ⭐   ║   ⭐   ║  ⭐⭐  ║  ⭐⭐  ║  ⭐⭐  ║  ⭐⭐  ║ ⭐⭐⭐ ║ ⭐⭐⭐ ║
╚════════╩════════╩════════╩════════╩════════╩════════╩════════╩════════╩════════╩════════╝

╔════════╦════════╦════════╦════════╦════════╦════════╦════════╦════════╦════════╦════════╗
║   10   ║   11   ║   12   ║   13   ║   14   ║   15   ║   16   ║   17   ║   18   ║   19   ║
║TERADATA║  SAS   ║ CI/CD  ║PLANNING║SECURITY║  COST  ║  PERF  ║MONITOR ║ SHARE  ║COPILOT ║
╠════════╬════════╬════════╬════════╬════════╬════════╬════════╬════════╬════════╬════════╣
║ ⭐⭐⭐ ║  ⭐⭐  ║  ⭐⭐  ║ ⭐⭐⭐ ║ ⭐⭐⭐ ║  ⭐⭐  ║ ⭐⭐⭐ ║  ⭐⭐  ║  ⭐⭐  ║   ⭐   ║
╚════════╩════════╩════════╩════════╩════════╩════════╩════════╩════════╩════════╩════════╝

╔════════╦════════╦════════╦════════╗
║   20   ║   21   ║   22   ║   23   ║
║WKSPACE ║  GEO   ║NETWORK ║GATEWAY ║
╠════════╬════════╬════════╬════════╣
║  ⭐⭐  ║ ⭐⭐⭐ ║ ⭐⭐⭐ ║ ⭐⭐⭐ ║
╚════════╩════════╩════════╩════════╝

╔════════╦════════╦════════╦════════╦════════╦════════╦════════╦════════╗
║   24   ║   25   ║   26   ║   27   ║   28   ║   29   ║   30   ║   31   ║
║SNOWFLK ║  DB2   ║STREAMG ║ VIDEO  ║MOVEMNT║  GEO   ║HEALTH ║DOT/FAA ║
╠════════╬════════╬════════╬════════╬════════╬════════╬════════╬════════╣
║ ⭐⭐⭐ ║ ⭐⭐⭐ ║ ⭐⭐⭐ ║ ⭐⭐⭐ ║ ⭐⭐⭐ ║ ⭐⭐⭐ ║ ⭐⭐⭐ ║ ⭐⭐⭐ ║
╚════════╩════════╩════════╩════════╩════════╩════════╩════════╩════════╝

╔════════╦════════╦════════╦════════╦════════╗
║   32   ║   33   ║   34   ║   35   ║   36   ║
║  USDA  ║  SBA   ║  NOAA  ║  EPA   ║  DOI   ║
╠════════╬════════╬════════╬════════╬════════╣
║  ⭐⭐  ║  ⭐⭐  ║ ⭐⭐⭐ ║ ⭐⭐⭐ ║ ⭐⭐⭐ ║
╚════════╩════════╩════════╩════════╩════════╝
 Beginner ──────────────────────────────────────────────────────────────────────► Advanced
```

---

## 📋 Tutorial Index

| Level | Tutorial | Description | Duration |
|:------|:---------|:------------|:---------|
| 🟢 **Foundation** | | | |
| | [00 - Environment Setup](./00-environment-setup/README.md) | Azure & Fabric workspace provisioning | ~1 hour |
| | [01 - Bronze Layer](./01-bronze-layer/README.md) | Raw data ingestion patterns | ~2 hours |
| 🟡 **Core** | | | |
| | [02 - Silver Layer](./02-silver-layer/README.md) | Data cleansing & validation | ~2 hours |
| | [03 - Gold Layer](./03-gold-layer/README.md) | Business aggregations & KPIs | ~2 hours |
| 🟠 **Advanced** | | | |
| | [04 - Real-Time Analytics](./04-real-time-analytics/README.md) | Eventstreams & Eventhouse | ~3 hours |
| | [05 - Direct Lake & Power BI](./05-direct-lake-powerbi/README.md) | Semantic models & reports | ~2 hours |
| 🔴 **Enterprise** | | | |
| | [06 - Data Pipelines](./06-data-pipelines/README.md) | Orchestration & scheduling | ~2 hours |
| | [07 - Governance & Purview](./07-governance-purview/README.md) | Data catalog & lineage | ~2 hours |
| | [08 - Database Mirroring](./08-database-mirroring/README.md) | SQL Server replication | ~1 hour |
| | [09 - Advanced AI/ML](./09-advanced-ai-ml/README.md) | Machine learning integration | ~3 hours |
| 🟣 **Migration & Integration** | | | |
| | [10 - Teradata Migration](./10-teradata-migration/README.md) | Teradata to Fabric migration & modernization | ~3 hours |
| | [11 - SAS Connectivity](./11-sas-connectivity/README.md) | SAS OLEDB/ODBC connectivity | ~1.5 hours |
| 🔵 **DevOps & Planning** | | | |
| | [12 - CI/CD DevOps](./12-cicd-devops/README.md) | Git integration, pipelines & deployment automation | ~2.5 hours |
| | [13 - Migration Planning](./13-migration-planning/README.md) | 6-month POC to Production enterprise migration | ~4 hours |
| ⚪ **Operations & Governance** | | | |
| | [14 - Security & Networking](./14-security-networking/README.md) | RLS, OLS, Private Link, compliance (PCI-DSS/NIGC) | ~2.5 hours |
| | [15 - Cost Management](./15-cost-optimization/README.md) | Capacity planning, FinOps, pause/resume automation | ~2 hours |
| | [16 - Performance Tuning](./16-performance-tuning/README.md) | V-Order, partitioning, Spark tuning, benchmarking | ~2.5 hours |
| | [17 - Monitoring & Alerting](./17-monitoring-alerting/README.md) | Capacity Metrics, Azure Monitor, KQL diagnostics | ~2 hours |
| 🟤 **Collaboration & AI** | | | |
| | [18 - Data Sharing](./18-data-sharing/README.md) | OneLake shortcuts, cross-workspace, multi-tenant | ~1.5 hours |
| | [19 - Copilot & AI](./19-copilot-ai/README.md) | AI-assisted development across all Fabric workloads | ~1.5 hours |
| 🟡 **Infrastructure & GeoAnalytics** | | | |
| | [20 - Workspace Best Practices](./20-workspace-best-practices/README.md) | Workspace organization, folder structures, environments | ~2.5 hours |
| | [21 - GeoAnalytics & ArcGIS](./21-geoanalytics-arcgis/README.md) | Geospatial analytics, ArcGIS integration, maps | ~3.5 hours |
| | [22 - Networking Connectivity](./22-networking-connectivity/README.md) | Private endpoints, ExpressRoute, VPN, multi-cloud | ~3.5 hours |
| | [23 - SHIR & Data Gateways](./23-shir-data-gateways/README.md) | Self-hosted runtime, on-premises gateways, hybrid | ~2.5 hours |
| 🟢 **Migration & Streaming** | | | |
| | [24 - Snowflake to Fabric](./24-snowflake-to-fabric/README.md) | Snowflake migration, schema mapping, cost comparison | ~3 hours |
| | [25 - IBM DB2 Source](./25-ibm-db2-source/README.md) | DB2 connectivity, CDC, EBCDIC handling | ~3 hours |
| | [26 - Multi-Source Streaming](./26-multi-source-streaming/README.md) | 8 CDC & IoT streaming connectors | ~3 hours |
| 🔴 **Analytics & Federal Expansions** | | | |
| | [27 - Video Security Analytics](./27-video-security-analytics/README.md) | AI video pipeline, YOLO/DeepSORT, edge processing | ~2.5 hours |
| | [28 - People Movement Analytics](./28-people-movement-analytics/README.md) | Foot traffic, queue detection, heat maps | ~2 hours |
| | [29 - Geolocation Analytics](./29-geolocation-analytics/README.md) | H3 spatial indexing, geofencing, proximity | ~2.5 hours |
| | [30 - Tribal Healthcare](./30-tribal-healthcare/README.md) | HIPAA-compliant IHS analytics, PHI masking | ~3 hours |
| | [31 - Federal DOT/FAA](./31-federal-dot-faa/README.md) | FedRAMP aviation analytics, safety dashboards | ~2.5 hours |
| 🌿 **Federal Agency POCs** | | | |
| | [32 - USDA Agriculture](./32-usda-agriculture/README.md) | Crop production & food safety analytics | ~2 hours |
| | [33 - SBA Small Business](./33-sba-small-business/README.md) | PPP/7a/504 loan portfolio analytics | ~2 hours |
| | [34 - NOAA Weather & Climate](./34-noaa-weather-climate/README.md) | Weather, storms, climate trends & real-time | ~2.5 hours |
| | [35 - EPA Environment](./35-epa-environment/README.md) | Air quality, toxic releases, water compliance | ~2.5 hours |
| | [36 - DOI Natural Resources](./36-doi-interior/README.md) | Earthquakes, water, parks, species analytics | ~2.5 hours |

---

## ⏱️ Time Estimates

### By Level

| Level | Tutorials | Total Time |
|:------|:----------|:-----------|
| 🟢 Foundation | 00-01 | ~3 hours |
| 🟡 Core | 02-03 | ~4 hours |
| 🟠 Advanced | 04-05 | ~5 hours |
| 🔴 Enterprise | 06-09 | ~8 hours |
| 🟣 Migration & Integration | 10-11 | ~4.5 hours |
| 🔵 DevOps & Planning | 12-13 | ~6.5 hours |
| ⚪ Operations & Governance | 14-17 | ~9 hours |
| 🟤 Collaboration & AI | 18-19 | ~3 hours |
| 🟡 Infrastructure & GeoAnalytics | 20-23 | ~12 hours |
| 🟢 Migration & Streaming | 24-26 | ~9 hours |
| 🔴 Analytics & Federal Expansions | 27-31 | ~13.5 hours |
| 🌿 Federal Agency POCs | 32-36 | ~11.5 hours |
| **Total** | All 37 | **~89 hours** |

### By Format

| Format | Duration | Best For |
|:-------|:---------|:---------|
| **3-Day Workshop** | 24 hours | Team training, POC kickoff |
| **Self-Paced** | 2-4 weeks | Individual learning |
| **Quick Start** | 4-6 hours | Foundation only (00-03) |

---

## 📋 Prerequisites

Before starting the tutorials, ensure you have:

- [ ] Azure subscription with Fabric enabled
- [ ] Fabric capacity (F64 recommended, F2 minimum)
- [ ] Completed the [Prerequisites Guide](../PREREQUISITES.md)
- [ ] Generated sample data (optional but recommended)

> 💡 **Tip:** Start with [Tutorial 00](./00-environment-setup/README.md) to set up your environment before proceeding.

---

## 📚 Related Documentation

| Document | Description |
|:---------|:------------|
| [🏗️ Architecture](../ARCHITECTURE.md) | System architecture and design |
| [🚀 Deployment Guide](../DEPLOYMENT.md) | Infrastructure deployment |
| [📋 Prerequisites](../PREREQUISITES.md) | Setup requirements |
| [📅 POC Agenda](../poc-agenda/README.md) | 3-Day workshop schedule |
| [📋 Templates](./templates/README.md) | Progress tracker templates |

---

[⬆️ Back to top](#-tutorials) | [🏠 Home](../README.md)

---

> 📖 **Documentation maintained by:** Microsoft Fabric POC Team
> 🔗 **Repository:** [Suppercharge_Microsoft_Fabric](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric)
