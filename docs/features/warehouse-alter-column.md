---
hero: assets/heroes/features.svg
hero_alt: Fabric feature — ALTER COLUMN in Fabric Data Warehouse — In-Place Schema Evolution
type: feature
---
# 🔧 ALTER COLUMN in Fabric Data Warehouse — In-Place Schema Evolution (Preview)

<div align="center" markdown>

**In-Place Schema Evolution for Supported Conversions**

![Category](https://img.shields.io/badge/Category-Data_Engineering-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-September_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-09-12` | **Version:** 1.0.0

> **Validation scope:** Reviewed against Microsoft Learn. SQL examples have not been executed against a Fabric capacity; confirm the specific source-to-target conversion before use.

---

## 🎯 Overview

`ALTER TABLE ... ALTER COLUMN` is **in preview** for Fabric Data Warehouse, closing one of the most painful gaps in warehouse schema evolution. Previously, changing a column's data type required a CTAS rebuild — create a new table, copy data, drop the old one, rename. Now you can alter columns in place, and the operation can run inside an **explicit user-defined transaction** alongside other supported DDL.

### The Full ALTER TABLE Surface in Fabric Warehouse

| Operation | Status |
|-----------|--------|
| `ADD` nullable columns | ✅ GA |
| `DROP COLUMN` | ✅ GA (May 2025) |
| `sp_rename COLUMN` | ✅ GA (May 2025) |
| **`ALTER COLUMN`** | 🔶 **Preview** |
| `ADD`/`DROP` `PRIMARY KEY`, `UNIQUE`, `FOREIGN KEY` constraints | ✅ Only with `NOT ENFORCED` |
| `ALTER TABLE` on distributed temp tables | ✅ Supported |
| All other `ALTER TABLE` operations | ❌ Blocked |

---

## 🏗️ Usage

```sql
-- Alter a column's data type in place (preview)
ALTER TABLE dbo.fact_slot_play
ALTER COLUMN wager_amount DECIMAL(18,2);
```

### Transactional Schema Changes

Supported `ALTER TABLE` statements — including ALTER COLUMN — can run inside an explicit transaction, so multi-step schema changes are atomic:

```sql
BEGIN TRAN;
ALTER TABLE dbo.dim_player ADD loyalty_tier VARCHAR(20) NULL;
ALTER TABLE dbo.dim_player ALTER COLUMN player_name VARCHAR(200);
ALTER TABLE dbo.dim_player DROP COLUMN legacy_notes;
COMMIT;
-- If any statement fails, all schema changes roll back
```

---

## ⚠️ Warehouse-Specific Validation

Use the **Warehouse in Fabric** section of the ALTER TABLE reference, not the general SQL Server restrictions or conversion examples. Preview availability does not establish that every pair of supported storage types can be converted in place.

[Warehouse persisted data types](https://learn.microsoft.com/fabric/data-warehouse/data-types) exclude `text`, `ntext`, `image`, `nvarchar`, and `xml`. SQL Server examples converting those legacy columns are not Warehouse in-place migration recipes. Map source data to supported Warehouse types during ingestion instead.

Before applying a change:

1. Confirm the exact source type, target type, nullability, and dependencies against Warehouse-specific guidance.
2. Test representative values and downstream queries in a development warehouse.
3. Validate transaction failure behavior and preserve a recovery plan before production migration.

The examples above illustrate syntax, not a verified conversion matrix.

---

## 🎰 Casino/Gaming POC Applications

| Use Case | Application |
|----------|-------------|
| **Wager precision widening** | Assess `DECIMAL(12,2)` → `DECIMAL(18,2)` for high-limit play; verify conversion support before choosing an in-place migration |
| **Regulatory field expansion** | Widen `player_name` or address columns when jurisdiction reporting requirements change |
| **Federal schema alignment** | Validate revised data dictionary types against supported conversions and test preservation of historical values |
| **Bronze-to-silver type promotion** | Use validated casts in Silver transformations; do not assume arbitrary `VARCHAR`-to-numeric in-place conversion is supported |

---

## ⚠️ Limitations & Considerations

| Consideration | Detail |
|---------------|--------|
| **Preview status** | No SLA — validate in dev before relying on it in production pipelines |
| **Statistics and dependencies** | Verify Warehouse-specific behavior and query plans; do not infer statistics behavior from the SQL Server section of the reference |
| **Git integration limits** | There are [limitations adding constraints or columns via Git Integration](https://learn.microsoft.com/fabric/data-warehouse/git-integration#limitations-in-git-integration) — review before combining |
| **dbt-fabric adapter** | Microsoft Learn describes CTAS-based adapter implementations for some DDL; pin the adapter and test its generated SQL rather than assuming native preview support |
| **Mirrored sources** | `ALTER COLUMN` on a *source* table is not supported for some mirroring configurations (e.g., SQL Managed Instance) — check per-source limitations |

---

## 🔗 Related Documents

- [Warehouse ALTER DATABASE SET](warehouse-alter-database-set.md) — Database-level settings (retention, V-Order, Delta log publishing)
- [Fabric SQL Database](fabric-sql-database.md) — The OLTP sibling with full DDL support
- [dbt Integration](dbt-fabric-integration.md) — How the dbt-fabric adapter handles schema changes
- [Cross-Database Queries](cross-database-queries.md) — Query patterns across warehouse and lakehouse
- [Migration Patterns](../best-practices/migration-patterns.md) — Synapse-to-Fabric schema evolution strategies

---

## 📚 Microsoft Learn References

- [T-SQL surface area in Fabric Data Warehouse](https://learn.microsoft.com/fabric/data-warehouse/tsql-surface-area)
- [ALTER TABLE (Transact-SQL) — Fabric Data Warehouse syntax](https://learn.microsoft.com/sql/t-sql/statements/alter-table-transact-sql?view=fabric&preserve-view=true#syntax-for-warehouse-in-fabric)
- [Transactions in Fabric Data Warehouse](https://learn.microsoft.com/fabric/data-warehouse/transactions)
- [Table constraints in Warehouse](https://learn.microsoft.com/fabric/data-warehouse/table-constraints)

---

> 📝 **Document Metadata**
> - **Author**: Documentation Team
> - **Reviewers**: Data Engineering, Database Team
> - **Classification**: Internal
> - **Next Review**: 2026-12-07
