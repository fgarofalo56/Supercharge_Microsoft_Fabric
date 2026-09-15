# Semantic Model & Power BI Reports

This folder contains the **Direct Lake** semantic model TMDL and the
configuration plan for the three Power BI reports that demonstrate
progressively stricter security on the same model.

## Files

| File | Purpose |
|---|---|
| `model.tmdl` | Full semantic model: 6 tables, relationships, measures, **3 RLS roles**. Direct Lake on `lh_btfabric_gold`. |

## The three reports (build by hand in Power BI Desktop)

All three reports point at the **same** semantic model and use the
**same** measures (`Revenue`, `Gross Profit`, `Net Revenue`, `AOV`, etc.).
The difference is which **role** users land in via app audience assignment.

| Report | Audience | Role | What they see |
|---|---|---|---|
| **01 — Regional Sales** | `grp-sales-mgr-*` | `RegionalManager` | Only their region's customers / orders / returns. Customer table is visible (they own those relationships). |
| **02 — Finance Performance** | `grp-finance` | `FinanceAnalyst` | All regions, but the `customer_id` column is hidden by OLS. Reports use the `Customers` measure (distinct count) — no row-level PII. |
| **03 — Executive Scorecard** | `grp-exec` | `Executive` | All regions, all columns, all measures. |

## Best practice: separate refresh identity

Direct Lake on a lakehouse refreshes on-demand at query time, but the
companion **Direct Lake on SQL** model (if you build one) does need a
scheduled refresh credential. **Do not** use a personal account for
this — and note: **service principals cannot be RLS/OLS members**
([service-premium-service-principal](https://learn.microsoft.com/en-us/fabric/enterprise/powerbi/service-premium-service-principal)).

✅ Canonical 2026 pattern: configure a **Fixed Identity** on the
semantic model and grant only that identity Read on the lakehouse.

```mermaid
flowchart LR
    SP["SPN<br/>sp-better-together-refresh"] -->|Scheduled refresh| SM[Semantic Model]
    FX["Fixed Identity<br/>(model property)"] -->|Reads| LH[(Lakehouse lh_btfabric_gold)]
    SM -->|Uses| FX
    classDef good fill:#1B5E20,stroke:#fff,color:#fff
    class SP,FX,SM,LH good
```

## How to publish

1. In Power BI Desktop (March 2026+), open this folder via "Open report" →
   browse to a `.pbip` project. Save the project; it will create the
   `definition/` folder that pairs with the TMDL.
2. Publish to your `Better Together` workspace.
3. In the workspace, set the **fixed identity** on the semantic model
   to the SPN `sp-better-together-refresh` (the security automation
   notebook creates this principal).
4. Configure **3 app audiences** matching the table above, and assign
   the Entra security groups created by the persona generator.

## Why dynamic RLS over static roles?

We use one `RegionalManager` role + a `_RLS Mapping` Delta table joined
on `USERPRINCIPALNAME()`, rather than 4 separate `RegionalManagerEMEA`,
`RegionalManagerUSEast` etc. roles. Why:

- The mapping is data, not metadata — it lives in the lakehouse and is
  curated by the security automation notebook. **No model redeploy
  needed** when org changes hit.
- One role to test, one role to audit.
- Survives a Fabric workspace clone — TMDL doesn't reference Entra
  group object IDs, so the model is portable.
