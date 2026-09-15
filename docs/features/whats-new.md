---
hero: assets/heroes/features.svg
hero_alt: Fabric feature — What's New — Latest Microsoft Fabric Release Highlights
type: feature
---
# 🆕 What's New in Microsoft Fabric — Release Highlights

<div align="center" markdown>

**Curated, POC-Relevant Snapshot of the Latest Fabric Releases — Grounded in Microsoft Learn**

![Category](https://img.shields.io/badge/Category-Release_Tracking-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-September_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-09-15` | **Version:** 1.0.0

---

## 🎯 Purpose

This page tracks the **latest Microsoft Fabric releases that matter to this POC**, distilled from the official [What's new in Microsoft Fabric](https://learn.microsoft.com/fabric/fundamentals/whats-new) and the [Fabric Updates Blog](https://blog.fabric.microsoft.com/). It is a **point-in-time snapshot** — Microsoft Learn is the live source of truth. Each entry notes whether this repo already covers the capability or links to where it does.

> **Rule of thumb:** Fabric ships fast. Before relying on any entry here, confirm current GA/preview status on Microsoft Learn.

---

## 🗓️ September 2026

| Feature | Status | POC relevance |
|---------|--------|---------------|
| **SQL query editor enhancements** | ✅ GA | Faster results grid, scalable object explorer + IntelliSense, autosave, bulk query management, `.sql` import/export, OneLake analytics + semantic model integration. See [SQL query editor](https://learn.microsoft.com/fabric/data-warehouse/sql-query-editor). |
| **Fabric networking communication policies Admin API** | ✅ GA | Tenant-wide, paginated view of workspace inbound/outbound networking policies. Supports the network-security posture in `docs/best-practices/security/`. See [List Networking Communication Policies](https://learn.microsoft.com/rest/api/fabric/admin/workspaces/list-networking-communication-policies). |
| **ODBC → ADBC driver transition** | ✅ GA | ADBC drivers for supported Power BI/Fabric connectors available for validation before ODBC is disabled. **Action:** validate connectors now. See [Transition from ODBC to ADBC](https://learn.microsoft.com/power-query/transition-to-adbc). |
| **Capacity Operation Events in Real-Time Hub** | 🔵 Preview | Operation-level telemetry for capacity consumption, throttling, workspaces, items. Feeds the capacity-monitoring guidance in `docs/best-practices/`. See [Explore capacity operation events](https://learn.microsoft.com/fabric/real-time-hub/explore-fabric-capacity-operation-events). |
| **Monitor for Fabric Data Warehouse** | 🔵 Preview | Unified active + historical query monitoring, Query Insights, one-click cancel. See [Monitor T-SQL queries](https://learn.microsoft.com/fabric/data-warehouse/monitor). |
| **Fabric Activator integration with warehouse SQL queries** | 🔵 Preview | Define conditions on query results and trigger actions. Extends the RTI alerting patterns in `notebooks/real-time/`. See [Set alerts on warehouse queries](https://learn.microsoft.com/fabric/real-time-intelligence/data-activator/set-alerts-warehouse-sql-query). |

---

## 🗓️ August 2026

| Feature | Status | POC relevance |
|---------|--------|---------------|
| **Activator rules in Eventstream** | ✅ GA | Create/edit/delete/open alert rules without leaving Eventstream. Covered in `docs/features/anomaly-detection-rti.md` and `notebooks/real-time/`. |
| **COPY INTO with workspace identity** | ✅ GA | Warehouse loads approved data from OneLake/ADLS Gen2 using workspace identity — aligns with this repo's Workspace Identity IaC (`infra/modules/security/workspace-identity.bicep`). See [COPY statement](https://learn.microsoft.com/fabric/data-warehouse/ingest-data-copy). |
| **Warehouse CI/CD 2.0** | 🔵 Preview | DacFx-based incremental extraction for Git integration + deployment pipelines. Complements `scripts/fabric-cicd-deploy.py`. See [Source control with Warehouse](https://learn.microsoft.com/fabric/data-warehouse/development-deployment). |
| **Modern Fabric Pipeline canvas** | 🔵 Preview | Improved navigation/layout for large pipelines. See [Pipeline canvas experience](https://learn.microsoft.com/fabric/data-factory/pipeline-canvas-experience). |
| **Git Integration Workspace Relation API** | 🔵 Preview | Automate parent/branched workspace relationships. See [Branch out experience](https://learn.microsoft.com/fabric/cicd/git-integration/branched-workspace). |

---

## 🗓️ July 2026

| Feature | Status | POC relevance |
|---------|--------|---------------|
| **Planning in Fabric IQ** | ✅ GA | Unified no-code planning, reporting, analytics. Covered in `docs/features/fabric-iq-planning.md`. |
| **Fabric IQ conversational analytics** | 🔵 Preview | Ask questions over governed semantic models in Microsoft 365 Copilot Chat. Covered in `docs/features/fabric-iq-conversational-analytics.md`. |
| **Fabric data agent public API** | 🔵 Preview | Manage data agents programmatically from CI/CD, portals, Functions. Covered in `docs/features/data-agent-api.md`. |
| **Resource Instance Rules for OneLake network security** | ✅ GA | Allow specific Azure resource instances to reach OneLake over the public endpoint while Fabric evaluates data permissions. See `docs/features/onelake-security.md`. |
| **OneLake item size reporting** | ✅ GA | Workspace storage report breaking down item/system/soft-deleted data and billing. Supports capacity + cost governance. |
| **fabric-cicd v1.2.0 bulk publish mode** | 🔵 Preview | Publish multiple items in one bulk-import API call. Directly relevant to `scripts/fabric-cicd-deploy.py`. |

---

## 🛡️ Disaster Recovery — Recent Clarifications

The DR guidance this repo captures in `docs/best-practices/fabric-dr-authoritative-answers.md` is current. Two supporting details worth surfacing (now folded into that doc):

- **OneLake soft delete** — OneLake retains deleted files for **7 days** before permanent removal, independent of the DR geo-replication toggle. See [Recover deleted files in OneLake](https://learn.microsoft.com/fabric/onelake/soft-delete).
- **BCDR billing** — enabling DR bills geo-replicated storage as **BCDR Storage** and write operations as **BCDR Operations** (higher CU consumption), visible as separate line items in the Capacity Metrics app. See [OneLake consumption](https://learn.microsoft.com/fabric/onelake/onelake-consumption#disaster-recovery).

---

## 🔗 Sources

- [What's new in Microsoft Fabric](https://learn.microsoft.com/fabric/fundamentals/whats-new) — live release tracker
- [Microsoft Fabric Updates Blog](https://blog.fabric.microsoft.com/) — monthly feature summaries
- [Microsoft Fabric release plan / roadmap](https://learn.microsoft.com/fabric/release-plan/) — upcoming features

---

> 📝 **Document Metadata**
> - **Author**: Documentation Team
> - **Reviewers**: Platform Engineering
> - **Classification**: Internal
> - **Next Review**: 2026-10-15
> - **Maintenance**: Reconcile against Microsoft Learn monthly; this is a snapshot, not the live tracker
