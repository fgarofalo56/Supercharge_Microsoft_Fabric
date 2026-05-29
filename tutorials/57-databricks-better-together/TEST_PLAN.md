# 🧪 Tutorial 57 — End-to-End Test Plan

> Walk this checklist to validate **both paths** end-to-end:
> (1) the Databricks Better Together tutorial, and
> (2) the Hitchhiker's Guide notebooks.

Each step has **explicit expected output** so you can stop early if
something diverges.

!!! info "Third-party references — publicly sourced, good-faith comparison"
    This page references non-Microsoft products and services. That information is drawn from each vendor's **publicly available documentation** and is offered for honest, good-faith comparison only. This is a personal project written from a Microsoft Fabric and Azure perspective; it does **not** claim expertise in, or authority over, any third-party product, and nothing here is an official statement by, or endorsed by, those vendors. Capabilities, pricing, and features change often — always verify against the vendor's current official documentation. Where a third-party offering is the stronger choice, we say so plainly.

---

## Path 1 — Tutorial 57 happy path

### Phase 0 — Sample data

- [ ] Run `python tutorials/57-databricks-better-together/scripts/generate_sample_data.py`.
- [ ] Expect: `sample-data/57-better-together/retail/*.parquet` (5 files) +
      `sample-data/57-better-together/personas/{users,groups}.csv`.
- [ ] Expect: deterministic output — re-running produces byte-identical files
      (seed=57).

### Phase 1 — Azure scaffolding

- [ ] `az login --use-device-code --tenant <tenant-id>`.
- [ ] `az account set --subscription <sub-id>`.
- [ ] `az deployment sub what-if --location eastus2 \
        --template-file infra/main.bicep \
        --parameters infra/dev.bicepparam`.
- [ ] Expect: planned resources = 1 RG, 1 KV, 1 storage account; **0**
      Databricks workspaces (because `deployDatabricks=false`).
- [ ] If satisfied, `az deployment sub create ...` with the same args.

### Phase 2 — Unity Catalog

- [ ] In Databricks: open `notebooks/setup/00_create_unity_catalog.py` on a
      UC-enabled cluster, run all cells.
- [ ] Expect: `SHOW SCHEMAS IN better_together` lists `retail_raw`,
      `retail_curated`, `retail_secure`.
- [ ] Expect: `SHOW VOLUMES IN better_together.retail_raw` lists `landing`.

### Phase 3 — Load data

- [ ] Upload `sample-data/57-better-together/retail/*.parquet` to
      `/Volumes/better_together/retail_raw/landing/retail/`.
- [ ] Run `notebooks/setup/01_load_sample_data.py`.
- [ ] Expect: five tables in `retail_raw` (`customers`, `products`,
      `orders`, `order_lines`, `returns`).
- [ ] Expect: two views in `retail_secure`
      (`orders_by_region`, `audit_revenue_summary`).
- [ ] As a logged-in user **not in** any `grp-sales-mgr-*`:
      `SELECT COUNT(*) FROM retail_secure.orders_by_region` → 0.

### Phase 4 — Mirroring

- [ ] In Fabric: import `notebooks/mirroring/*.py` into a workspace bound to
      F-SKU capacity.
- [ ] Make sure the Databricks connection ID is stored in Key Vault as
      `fabric-databricks-connection-id`.
- [ ] Run `01_register_full_catalog_mirror.py`.
- [ ] Expect: HTTP 201 or 202; new item `MirrorDBX_FullCatalog` appears in
      the workspace; tables visible under
      `Tables/MirroredAzureDatabricksCatalog/retail_raw/*`.
- [ ] Run `02_register_partial_mirror.py`.
- [ ] Expect: two more items — `MirrorDBX_Inclusion` (only the
      `retail_secure.*` views) and `MirrorDBX_Exclusion` (everything except
      `retail_raw.customers`).
- [ ] Run `03_query_mirror_from_spark.py` → confirm row counts match what
      you saw in Databricks.

### Phase 5 — Gold + semantic model

- [ ] Create `lh_btfabric_gold` lakehouse in the same workspace.
- [ ] Run `notebooks/gold/01_gold_star_schema.py` (attach the gold lakehouse).
- [ ] Expect: six tables in `lh_btfabric_gold` (dim_region, dim_customer,
      dim_product, dim_date, fact_sales, fact_returns).
- [ ] Expect: the assert at the end of the notebook passes ("OK — fact_sales
      → dim_customer integrity holds").
- [ ] In Power BI Desktop: open the `semantic-model/` folder as a `.pbip`
      project; publish to the workspace.

### Phase 6 — Defense-in-depth automation

- [ ] Upload `sample-data/57-better-together/personas/*.csv` to
      `Files/57-better-together/personas/` in the gold lakehouse.
- [ ] Run `notebooks/security/01_apply_defense_in_depth.py`.
- [ ] Expect: ~13 Entra groups created (or reused), workspace role assignments
      logged, OneLake data access roles PUT returns 200, `rls_user_region_map`
      Delta table populated with ~8 rows.
- [ ] Manual step: set the **Fixed Identity** on the published semantic model.

### Phase 7 — Power BI persona testing

For each of the three reports, log in as one of the synthetic-user UPNs (or
use **View as → Other user**) and verify the row counts below match.

| Persona | Report | Expected `fact_sales` row count |
|---|---|---|
| `grp-sales-mgr-us-east` user | Regional Sales | only US-EAST rows |
| `grp-sales-mgr-emea` user | Regional Sales | only EMEA rows |
| `grp-finance` user | Finance Performance | all rows, `customer_id` not visible |
| `grp-exec` user | Executive Scorecard | all rows, all columns |
| `grp-audit` user | (any) | aggregate views only |

---

## Path 2 — Hitchhiker's Guide validation

Each Hitchhiker's notebook is a flat list of recipes. The validation goal is
**syntax correctness + runnability on a clean workspace**, not exhaustive
output comparison.

- [ ] Import all 7 `notebooks/hitchhikers-guide/*.py` files into a Fabric
      workspace.
- [ ] Open `00_index.py` → run the "Pre-flight" cells. Expect: a workspace
      name, a notebook ID, a Spark version printed.

For each subsequent notebook, run the cells that don't require external
infrastructure (sections marked with `🔗` link to Learn but the snippet
itself is self-contained):

| Notebook | Cells to run | Skip cells that |
|---|---|---|
| `01_connectivity.py` | A (ADLS mount), N (Fabric REST `/workspaces`) | hit Snowflake / on-prem / mirror items unless those exist in your environment |
| `02_lakehouse_warehouse_ops.py` | All A, B, D, F, G | I (Warehouse from Spark) unless you have a Warehouse |
| `03_security_identity.py` | F, G, H, I — token & secret cells | A (PUT data access roles) unless you have a target lakehouse |
| `04_admin_governance.py` | A (boilerplate), I (tenant settings read) | C, F, G unless you have a fresh workspace to mutate |
| `05_automation_utilities.py` | All — every cell is pure utility | none |
| `06_troubleshooting.py` | All self-diagnostic cells | none |

Expected: every executed cell returns without an unhandled exception.

---

## Path 3 — Static validation (run from the host)

These checks run from your dev machine and don't touch Fabric/Databricks at all.

```bash
# 1. Generators produce identical output across runs (determinism)
python tutorials/57-databricks-better-together/scripts/generate_sample_data.py
md5sum sample-data/57-better-together/retail/*.parquet  > /tmp/run1.md5
rm -rf sample-data/57-better-together
python tutorials/57-databricks-better-together/scripts/generate_sample_data.py
md5sum sample-data/57-better-together/retail/*.parquet  > /tmp/run2.md5
diff /tmp/run1.md5 /tmp/run2.md5   # expect empty diff

# 2. Bicep static build
az bicep build --file infra/modules/databricks/databricks-workspace.bicep
az bicep build --file infra/modules/security/key-vault.bicep
az bicep build --file tutorials/57-databricks-better-together/infra/main.bicep
# expect: warnings about a new Bicep release only; no errors

# 3. Notebook Python syntax check (parses every .py as Python, ignoring magics)
python -m py_compile \
  tutorials/57-databricks-better-together/notebooks/setup/00_create_unity_catalog.py \
  tutorials/57-databricks-better-together/notebooks/setup/01_load_sample_data.py \
  tutorials/57-databricks-better-together/notebooks/mirroring/*.py \
  tutorials/57-databricks-better-together/notebooks/gold/*.py \
  tutorials/57-databricks-better-together/notebooks/security/*.py \
  notebooks/hitchhikers-guide/*.py
# expect: silent (0 exit)

# 4. Existing test suite still passes
pytest validation/unit_tests/ -q
# expect: same count as before this PR; no regressions

# 5. Docs site builds without broken links
mkdocs build --strict
# expect: 0 warnings, 0 errors
```

---

## Acceptance criteria

This tutorial is **accepted** when:

- All Path 3 static checks pass.
- At least one persona per role (Regional Manager, Finance, Exec) has been
  validated via "View as" in Power BI with the expected row filtering.
- The defense-in-depth doc cross-links resolve from
  `mkdocs build --strict`.
- The PR has no merge conflicts with `main`.
