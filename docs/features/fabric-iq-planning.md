---
hero: assets/heroes/features.svg
hero_alt: Fabric feature — Planning in Fabric IQ — Enterprise Planning and Forecasting
type: feature
---
# 📅 Planning in Fabric IQ — Enterprise Planning and Forecasting

<div align="center" markdown>

**Budgets, Forecasts, and Scenarios on Your Governed Fabric Data — No Separate EPM Tool Required**

![Category](https://img.shields.io/badge/Category-AI_%26_ML-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-September_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-09-07` | **Version:** 1.0.0

---

## 🎯 Overview

Planning in Fabric IQ is an **Enterprise and Corporate Performance Management (EPM/CPM) solution built directly into Microsoft Fabric**. It enables organizations to create, manage, and analyze plans — budgets, forecasts, and scenarios — within the same governed platform used for data, analytics, and AI. Planning reached **General Availability in July 2026** and is available worldwide as part of the Microsoft Fabric SKU, with dedicated billing meters.

Instead of exporting actuals to a separate planning tool or maintaining spreadsheet-based workflows, Planning operates directly on shared semantic models — bringing goals, plans, and actual results together on one data foundation.

### Why Planning in Fabric Matters

| Problem with Traditional EPM | Planning in Fabric IQ |
|------------------------------|----------------------|
| Actuals exported to a separate planning tool | Plans live on the same semantic models as analytics |
| Spreadsheet workflows with no governance | Governed, auditable planning on Fabric data |
| Manual reconciliation between plan and actuals | Shared data foundation — no reconciliation step |
| Separate licensing and infrastructure | Included in the Fabric SKU with dedicated billing meters |

### Core Components

| Component | Purpose |
|-----------|---------|
| **Planning sheets** | Budgeting, forecasting, and scenario modeling in a familiar spreadsheet-like experience with assumptions, inputs, and calculated outcomes |
| **PowerTable sheets** | Structured planning at scale — large dimensional planning models aligned with Fabric data structures and semantic models |
| **Intelligence sheets** | No-code reporting with IBCS formatting, 100+ charts, Gantt charts, annotations, threaded comments, and pixel-perfect exports |
| **Infobridge** | Connects and integrates data across systems, keeping planning data aligned with Fabric workloads and source systems |

---

## 🏗️ Key Capabilities

### Scenario Planning

Scenarios let you create and evaluate alternative versions of a plan without changing the committed **Base** plan:

1. **Create** — Define an alternative scenario (Best Case, Worst Case, Cost Reduction) based on Base
2. **Model** — Apply assumptions via simulation (individual values) or distribution (across rows/columns)
3. **Analyze** — Compare scenarios with scenario variance highlighting
4. **Review** — Assess with stakeholders using threaded comments and @mentions
5. **Finalize** — Lock the scenario to prevent further changes
6. **Apply** — Copy simulated values to Base when ready (native measures remain unchanged)

Scenario data can be persisted to the underlying data source via **Writeback**, with writeback logs for audit. **Scenario security** controls who can access and work with scenario data.

### Statistical Forecasting and Optimization

- Generate statistical forecasts from historical actuals (e.g., 24 months of actuals → rolling forecast)
- Use the **Optimizer** to solve for targets (e.g., adjust a bottom-up sales plan to hit a gross profit target)
- Build rolling forecasts that close months as actuals arrive and extend the horizon

### Measure Models and Row Models

- **Measure Model**: Organize existing semantic model measures into a structured hierarchy (e.g., a P&L)
- **Row Model builder**: Construct a hierarchy from scratch — Net Profit → Gross Profit → Net Revenue → COGS → Operating Expenses — as connected nodes
- **Cube measures**: Allocate values across dimensions automatically and keep multiple sheets in sync

### Writeback to Fabric SQL Database

When you create a Plan item, Fabric automatically provisions a **Fabric SQL database** in your workspace to store plan metadata. Committed forecasts and plan values can be written back to the database for downstream consumption by reports, pipelines, or other workloads.

---

## 🎰 Casino/Gaming POC Applications

| Use Case | Planning Application |
|----------|---------------------|
| **Property budgeting** | Annual budgets per property with scenario modeling for visitation assumptions |
| **Cage and cash operations forecasting** | Forecast cash position requirements by day of week and season |
| **Marketing spend planning** | Plan promotional budgets with Best/Worst case scenarios and variance analysis |
| **Compliance staffing plans** | Headcount planning for compliance teams against CTR/SAR workload forecasts |
| **Federal grant planning** | Multi-year grant budget planning with scenario comparison and writeback |

---

## ⚙️ Prerequisites and Setup

1. **Tenant and capacity settings** — see [Prerequisites for planning in Fabric](https://learn.microsoft.com/fabric/iq/plan/overview-prerequisites)
2. **Data in a Power BI semantic model** with a [connection to your semantic model](https://learn.microsoft.com/fabric/iq/plan/planning-how-to-create-semantic-model-connection)
3. **Semantic model connection owner permissions** and database connections
4. Create via **New item → Plan** in your Fabric workspace — a Fabric SQL database is auto-provisioned for plan metadata

### Limitations

- Planning does **not** support Microsoft Entra B2B guest accounts
- Workspaces that use **private links** are not supported
- See [Known limitations](https://learn.microsoft.com/fabric/iq/plan/overview-limitations) for planning sheet limits

### Billing

Planning is billed through dedicated Fabric billing meters. **PowerTable billing personas** (GA August 2026) provide role-based billing for Planners, Stakeholders, and Viewers — see [Billing and usage for planning in Fabric](https://learn.microsoft.com/fabric/iq/plan/resources/billing-fabric-plan).

---

## 🔗 Related Documents

- [Fabric IQ](fabric-iq.md) — Ontology, graph, and the semantic foundation Planning builds on
- [Fabric IQ Conversational Analytics](fabric-iq-conversational-analytics.md) — Ask questions over planning data in natural language
- [Fabric SQL Database](fabric-sql-database.md) — The auto-provisioned database backing plan metadata and writeback
- [Capacity Planning & Cost Optimization](../best-practices/capacity-planning-cost-optimization.md) — Planning billing meters and capacity impact
- [Scorecards & Metrics](scorecards-metrics.md) — KPI goal tracking that complements plan-vs-actual analysis

---

## 📚 Microsoft Learn References

- [What is planning in Fabric?](https://learn.microsoft.com/fabric/iq/plan/overview)
- [Prerequisites for planning in Fabric](https://learn.microsoft.com/fabric/iq/plan/overview-prerequisites)
- [Scenario planning in Microsoft Fabric](https://learn.microsoft.com/fabric/iq/plan/planning-concept-scenario-planning)
- [What are intelligence sheets in planning?](https://learn.microsoft.com/fabric/iq/plan/intelligence-overview)
- [Create a planning sheet](https://learn.microsoft.com/fabric/iq/plan/planning-how-to-get-started)
- [Billing and usage for planning in Fabric](https://learn.microsoft.com/fabric/iq/plan/resources/billing-fabric-plan)
- [Fabric planning tutorial series](https://learn.microsoft.com/fabric/iq/plan/planning-tutorial/planning/tutorial-0-introduction)

---

> 📝 **Document Metadata**
> - **Author**: Documentation Team
> - **Reviewers**: BI Engineering, Finance, Data Engineering
> - **Classification**: Internal
> - **Next Review**: 2026-12-07
