---
hero: assets/heroes/features.svg
hero_alt: Fabric feature — ALTER DATABASE SET in Fabric Data Warehouse — Database-Level Configuration
type: feature
---
# ⚙️ ALTER DATABASE SET in Fabric Data Warehouse — Database-Level Configuration

<div align="center" markdown>

**Retention, V-Order, Delta Log Publishing, and Snapshot Timestamps — via T-SQL**

![Category](https://img.shields.io/badge/Category-Data_Engineering-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-September_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-09-12` | **Version:** 1.0.0

---

## 🎯 Overview

Fabric Data Warehouse exposes database-level configuration through the `ALTER DATABASE ... SET` T-SQL statement. These settings control **how far back you can time-travel**, **whether V-Order optimization is applied**, **when Delta Lake logs are published to OneLake**, and **snapshot timestamps** — all scriptable, all auditable, all automatable through your existing T-SQL tooling.

### Supported Settings

| Setting | Values | Purpose | Status |
|---------|--------|---------|--------|
| `TIME_TRAVEL_RETENTION_PERIOD` | `1`–`120` days | How far back time travel, clones, restore points, and snapshots can reach | Preview |
| `VORDER` | `OFF` | Disable V-Order optimization on new Parquet files | GA — **irreversible** |
| `DATA_LAKE_LOG_PUBLISHING` | `PAUSED` / `AUTO` | Pause/resume Delta Lake log publishing to OneLake | GA |
| `TIMESTAMP` (on snapshots) | `CURRENT_TIMESTAMP` or `'YYYY-MM-DDTHH:MM:SS.SS'` | Update a warehouse snapshot's point-in-time | GA |

---

## 🏗️ Usage

### 1. Configure Data Retention (Time Travel Window)

The retention period determines how far back you can run [time travel](https://learn.microsoft.com/fabric/data-warehouse/time-travel) queries, create [table clones](https://learn.microsoft.com/fabric/data-warehouse/clone-table), use [restore points](https://learn.microsoft.com/fabric/data-warehouse/restore-in-place), and create [warehouse snapshots](https://learn.microsoft.com/fabric/data-warehouse/warehouse-snapshot).

```sql
-- Set retention to 15 days
ALTER DATABASE CURRENT
SET TIME_TRAVEL_RETENTION_PERIOD = 15 DAYS;

-- Check the current setting
SELECT
   name,
   time_travel_retention_period_days,
   time_travel_retention_cutoff_date
FROM sys.databases;
```

**Behavior when changing retention:**

- **Increasing** takes effect immediately, but data versions already cleaned up under the shorter period **cannot be recovered**
- **Decreasing** makes older versions eligible for asynchronous background cleanup — and is **irreversible from a data-access perspective**, even if you increase it again afterward
- Only **UTC** is used for retention calculations
- Only workspace **Admins** can modify retention; Member/Contributor/Viewer roles can query the setting
- If decreasing retention would invalidate existing snapshots, the change is **blocked** — advance or delete those snapshots first

### 2. Disable V-Order (Irreversible)

```sql
ALTER DATABASE CURRENT SET VORDER = OFF;

-- Check V-Order state across warehouses
SELECT [name], [is_vorder_enabled] FROM sys.databases;
```

> ⚠️ **Caution**: Disabling V-Order is warehouse-level and **irreversible** — once disabled, it cannot be re-enabled. New Parquet files are written without V-Order optimization. Consider the full performance impact before disabling.

### 3. Pause/Resume Delta Lake Log Publishing

Pausing log publishing holds the published Delta-table versions available to external Delta readers, including Spark and queries executing in Power BI Direct Lake mode. This supports stable Delta reads during bulk loads or saves publishing compute when interoperability isn't needed. It does not freeze queries that access the Warehouse through SQL:

```sql
-- Freeze the external view of warehouse data
ALTER DATABASE CURRENT SET DATA_LAKE_LOG_PUBLISHING = PAUSED;

-- ... run bulk data changes ...

-- Publish all recent changes to other engines
ALTER DATABASE CURRENT SET DATA_LAKE_LOG_PUBLISHING = AUTO;

-- Check publishing state
SELECT [name], [DATA_LAKE_LOG_PUBLISHING_DESC] FROM sys.databases;
```

Warehouse SQL queries are not constrained by the paused Delta-log version. [Direct Lake on SQL can fall back to DirectQuery](https://learn.microsoft.com/fabric/fundamentals/direct-lake-how-it-works#directquery-fallback), which reads current data through SQL rather than the framed Delta version. Pausing publishing alone therefore does not guarantee a frozen Power BI report. Validate the model's storage modes, framing, and fallback behavior. `DirectLakeOnly` prevents fallback but returns errors when Direct Lake cannot serve a query. Direct Lake on OneLake does not support fallback, but other tables in a composite model can use different storage modes.

### 4. Update Snapshot Timestamps

```sql
-- Advance a snapshot to now
ALTER DATABASE [wh_snapshot_monthend]
SET TIMESTAMP = CURRENT_TIMESTAMP;

-- Or to a specific point within the retention window
ALTER DATABASE [wh_snapshot_monthend]
SET TIMESTAMP = '2026-08-31T23:59:59.00';
```

---

## 🎰 Casino/Gaming POC Applications

| Use Case | Setting | Application |
|----------|---------|-------------|
| **Operational lookback** | `TIME_TRAVEL_RETENTION_PERIOD = 90 DAYS` | Illustrative recovery/query window, not an asserted NIGC requirement or substitute for separately governed regulatory records retention |
| **Stable month-end reporting** | `DATA_LAKE_LOG_PUBLISHING = PAUSED` | Hold published Delta versions during reconciliation; validate that report queries do not bypass them through SQL or DirectQuery fallback |
| **Compliance snapshots** | `TIMESTAMP` | Pin audit snapshots to jurisdiction filing deadlines |
| **Cost optimization** | `DATA_LAKE_LOG_PUBLISHING = PAUSED` | Skip log publishing on scratch/ETL warehouses that no other engine reads |

---

## ⚠️ Limitations & Considerations

| Consideration | Detail |
|---------------|--------|
| **Deployment pipelines** | Pipelines use `ScriptDatabaseOptions = false` — `ALTER DATABASE ... SET` statements are **not** propagated through deployments; apply them per-environment as post-deploy steps |
| **Retention preview** | `TIME_TRAVEL_RETENTION_PERIOD` is in preview |
| **V-Order irreversibility** | No path back once disabled |
| **Permissions** | Retention changes require workspace Admin |

---

## 🔗 Related Documents

- [Warehouse ALTER COLUMN](warehouse-alter-column.md) — In-place column type changes (preview)
- [Fabric SQL Database](fabric-sql-database.md) — Operational database with its own configuration surface
- [Disaster Recovery & BCDR](../best-practices/disaster-recovery-bcdr.md) — Retention windows as a DR control
- [Fabric DR Authoritative Answers](../best-practices/fabric-dr-authoritative-answers.md) — Point-in-time recovery guidance
- [Capacity Planning & Cost Optimization](../best-practices/capacity-planning-cost-optimization.md) — Compute cost of log publishing

---

## 📚 Microsoft Learn References

- [How to configure data retention in Fabric Data Warehouse](https://learn.microsoft.com/fabric/data-warehouse/how-to-configure-retention)
- [Data retention in Fabric Data Warehouse (preview)](https://learn.microsoft.com/fabric/data-warehouse/data-retention)
- [Disable V-Order on Warehouse](https://learn.microsoft.com/fabric/data-warehouse/disable-v-order)
- [Delta Lake logs in Warehouse — pause/resume publishing](https://learn.microsoft.com/fabric/data-warehouse/query-delta-lake-logs#pause-delta-lake-log-publishing)
- [Create and manage a warehouse snapshot](https://learn.microsoft.com/fabric/data-warehouse/create-manage-warehouse-snapshot)
- [Deploy a warehouse using pipelines — deployment configurations](https://learn.microsoft.com/fabric/data-warehouse/deploy-pipelines#deployment-configurations)

---

> 📝 **Document Metadata**
> - **Author**: Documentation Team
> - **Reviewers**: Data Engineering, Database Team, Compliance
> - **Classification**: Internal
> - **Next Review**: 2026-12-07
