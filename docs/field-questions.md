---
hero: assets/heroes/reference.svg
hero_alt: "Reference — Field Questions: Real customer scenarios answered"
type: reference
---
# 🛠️ Field Questions — Real Customer Scenarios

<div align="center" markdown>

**Detailed answers to questions raised by customers evaluating Fabric for production**

![Category](https://img.shields.io/badge/Category-Field_Guide-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Living-orange?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-May_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-05-21` | **Version:** 1.0.0

This page collects detailed answers to specific questions raised during enterprise
Fabric adoption — scenarios that the standard product docs don't address directly
but that come up repeatedly in field engagements. Each topic links back to the
authoritative Microsoft Learn citation.

!!! info "Third-party references — publicly sourced, good-faith comparison"
    This page references non-Microsoft products and services. That information is drawn from each vendor's **publicly available documentation** and is offered for honest, good-faith comparison only. This is a personal project written from a Microsoft Fabric and Azure perspective; it does **not** claim expertise in, or authority over, any third-party product, and nothing here is an official statement by, or endorsed by, those vendors. Capabilities, pricing, and features change often — always verify against the vendor's current official documentation. Where a third-party offering is the stronger choice, we say so plainly.

---

## 1. Power BI Mashup Errors with Mixed VNet + Cloud Sources

> **Scenario.** Combining data from Azure Databricks (on a corporate VNet) with cloud
> data sources such as SharePoint Lists causes the Power BI semantic model refresh
> to fail. The mashup engine appears to be routing the cloud source through the VNet.

### Why this happens

This is the Power Query **Formula.Firewall** ("privacy levels which cannot be used
together") error. Power Query partitions every data source by privacy level and
refuses to evaluate a single mashup that joins partitions it can't isolate.

In the Power BI Service the constraint is stricter still: if **any** source in a
semantic model requires a gateway (VNet data gateway in your case), the service
forces the cloud source through the same gateway too — and a single semantic
model can use only one gateway connection. SharePoint List → Databricks-on-VNet
hits this directly.

To make the cross-source mashup work without changing architecture, you must:

1. Set both sources to **Organizational** privacy level (Service and Desktop), AND
2. Define the cloud source on the same VNet data gateway, AND
3. Enable **"Allow user's cloud data sources to refresh through this gateway cluster"** on the gateway.

Source: [Data refresh — Accessing on-premises and cloud sources in the same source query](https://learn.microsoft.com/power-bi/connect-data/refresh-data#review-data-infrastructure-dependencies) · [Merge or append on-premises and cloud data sources](https://learn.microsoft.com/power-bi/connect-data/service-gateway-mashup-on-premises-cloud).

### Does mirroring Databricks via VNet to Fabric eliminate the mashup issue?

**Yes — in practice.** Once Azure Databricks is mirrored into a Fabric workspace
(through a VNet data gateway), Power BI no longer reads Databricks as a "VNet
source" inside the semantic model. The model reads the mirrored Delta tables
from **OneLake via Direct Lake** — which is a Fabric/OneLake source, not a VNet
source. SharePoint can then be joined as a normal cloud source without
triggering the firewall.

Mirroring for Azure Databricks specifically uses a **VNet data gateway** (not
Fabric's managed private endpoints — those are a separate path for Spark
egress). For Databricks behind a private endpoint, follow the dedicated
mirroring + private-endpoint guide.

Source: [Connect to Azure Databricks workspaces behind a private endpoint](https://learn.microsoft.com/fabric/mirroring/azure-databricks-private-endpoint) · [Mirroring Azure Databricks Unity Catalog — Direct Lake](https://learn.microsoft.com/fabric/mirroring/azure-databricks).

### Does the Fabric workspace need its own Fabric VNet if the Databricks connection is already VNet-private?

**No — not for mirroring.** Mirroring uses the VNet data gateway path. Fabric's
**managed VNet + managed private endpoints** are required only for **Fabric Data
Engineering (Spark) workloads** that need to egress to private resources directly
from the workspace.

If your only private source in this workspace is Databricks → ADLS via mirroring
+ VNet gateway, you do **not** need to assign a managed VNet to the workspace.
You **would** need it if a notebook in the same workspace later needs to reach
the same Databricks/ADLS privately (independent of mirroring).

Source: [Managed private endpoints overview — limitations](https://learn.microsoft.com/fabric/security/security-managed-private-endpoints-overview#limitations-and-considerations).

### Recommended pattern

```
[Azure Databricks (corporate VNet)]
        │
        │  Mirroring via VNet data gateway
        ▼
[Fabric workspace · Mirrored DB item]
        │
        │  Direct Lake (OneLake)
        ▼
[Power BI semantic model]
        ▲
        │  Cloud source — no gateway needed
[SharePoint List / cloud data]
```

The semantic model now combines two **OneLake/Fabric-native** sources from its
own perspective, so the Formula.Firewall path is irrelevant.

---

## 2. Creating Views on Mirrored Databricks Tables

> **Scenario.** EDW group uses a two-step Databricks pattern: a `Cleaned` catalog
> of tables, plus a `Replicas` catalog of Views that filter `current_record = true`
> and that Analytics consumes. Can the View pattern carry over to Fabric mirroring?

### Can you create SQL Views on mirrored Databricks tables?

**Yes.** Every mirrored Azure Databricks item gets an auto-generated **SQL
Analytics Endpoint** that supports T-SQL `CREATE VIEW`, inline TVFs, stored
procedures, and security policies over the Delta tables.

The endpoint label "read-only" refers to **data manipulation** (no INSERT /
UPDATE / DELETE on the mirrored tables themselves). Metadata DDL for **views,
TVFs, stored procedures, and permissions is explicitly supported** — and is
documented consistently across every mirroring source (Azure SQL, SQL Server,
PostgreSQL, Oracle, Open Mirroring, Databricks).

So your `Replicas` view pattern translates one-for-one. Create:

```sql
CREATE VIEW Replicas.Customer AS
SELECT * FROM Cleaned.Customer WHERE current_record = true;
```

Source: [Mirroring Azure Databricks — Built-in analytics experiences](https://learn.microsoft.com/fabric/mirroring/azure-databricks#what-analytics-experiences-are-built-in) · [Explore data in your mirrored database](https://learn.microsoft.com/fabric/mirroring/explore) · [SQL analytics endpoint limitations](https://learn.microsoft.com/fabric/data-warehouse/limitations#limitations-of-the-sql-analytics-endpoint).

### Where does the transformation belong?

In order of recommendation:

| Option | Pros | Cons |
|---|---|---|
| **(A) View on the mirror's SQL analytics endpoint** | Zero extra storage, no second copy, Direct Lake / SQL consumers see filtered data, fastest to deploy | View executes at query time; complex multi-table joins can degrade Direct Lake to DirectQuery fallback |
| **(B) View in a Fabric Warehouse** using three-part naming `MirroredDB.schema.table` | Full DDL/DML, more performant for complex joins, security policies + RLS, materializable | Workspace-scoped — Warehouse and mirror must live in the same Fabric workspace |
| **(C) Notebook materialization to a Lakehouse table** | Best perf for very heavy aggregations / window functions | Second copy of data, extra orchestration, no longer "live" |
| **(D) Push back to Databricks as a filtered table** | Keeps single source of truth in Databricks | Couples semantic layer to upstream platform; loses the "mirror once, transform downstream" benefit |

For the `current_record = true` use case specifically, **option (A) is the right
default** — it's a simple `WHERE` clause, no perf penalty, and it lets you stop
maintaining the `Replicas` catalog in Databricks.

Source: [Query the warehouse or SQL analytics endpoint — Write a cross-database query](https://learn.microsoft.com/fabric/data-warehouse/query-warehouse#write-a-cross-database-query) · [Develop and deploy cross-warehouse dependencies](https://learn.microsoft.com/fabric/data-warehouse/cross-warehouse-development-database-projects#pattern-1-direct-cross-warehouse-references-via-database-references).

### Should you convert mirrored Databricks tables into Lakehouse tables?

**Usually no.** The mirror is incremental and continuously updated. Materializing
into a Lakehouse means:

- You now own a refresh schedule (Fabric Pipeline / Notebook) to keep it fresh.
- You lose the near-real-time guarantee of the mirror.
- You double your storage cost for the same logical dataset.

Only do this if (a) you need very heavy aggregations that hurt Direct Lake at
query time, (b) you need to **mutate** the data (e.g., apply additional
filtering, deduplication, or business logic that views can't express cleanly),
or (c) you need to blend with other Lakehouse-resident data and prefer a
unified storage location.

---

## 3. Lakehouse Security and Permissions for Mirrored Databricks

> **Scenario.** Customer uses Databricks table-level scripting as a workaround for
> the lack of "grant all except" functionality. They want to know how the
> permission model changes once Databricks is mirrored to Fabric.

### Are Unity Catalog permissions inherited when mirroring to Fabric?

**No.** Unity Catalog grants are **not** carried over. Microsoft documents this
explicitly: *"Unity Catalog policies and permissions aren't mirrored in Fabric.
... You need to use Fabric's permission model to set access control on objects
in Fabric."*

A single connection credential is used to mirror Unity Catalog. Once the data
is in Fabric, downstream consumers query through that connection — Unity
Catalog row/column/ABAC policies do **not** apply to Fabric reads.

A preview pattern called **OneLake Security mapping** lets you sync an Entra
group via Databricks Automatic Identity Management, grant it UC privileges,
and then assign the *same* Entra group a OneLake Data Access Role in Fabric.
That is a **parallel re-grant**, not inheritance.

Source: [Secure Fabric mirrored databases from Azure Databricks](https://learn.microsoft.com/fabric/mirroring/azure-databricks-security) · [Tutorial: Enable OneLake Security](https://learn.microsoft.com/fabric/mirroring/azure-databricks-tutorial#enable-onelake-security-on-the-mirrored-databricks-item).

### Three control planes to keep distinct

| Control plane | Scope | How managed | Inherits from UC? |
|---|---|---|---|
| **Fabric workspace roles** | Workspace-wide (Admin / Member / Contributor / Viewer) | Fabric portal · Entra groups | No |
| **Item permissions / Share** | Per mirrored database item (Read · ReadData · ReadAll · Write) | Share dialog · Entra groups | No |
| **SQL endpoint T-SQL** | Schema / object / column / row inside the SQL analytics endpoint | `GRANT` / `DENY` / `CREATE SECURITY POLICY` | No (re-apply) |

A user needs (**workspace role OR item Read**) **AND** sufficient SQL grants to
return rows. Unity Catalog is a fourth, fully separate control plane that does
not flow through.

### Does the endpoint support standard T-SQL grant/deny patterns?

**Yes.** The SQL analytics endpoint over a mirrored database supports the standard
SQL Server securable hierarchy via `GRANT` / `REVOKE` / `DENY`, plus RLS and CLS:

```sql
-- Grant whole schema
GRANT SELECT ON SCHEMA::abc TO [Analytics-Readers];
-- Deny a specific object
DENY  SELECT ON OBJECT::dbo.xyz_pii TO [Analytics-Readers];
-- Column-level
GRANT SELECT ON dbo.customer (id, name, region) TO [Analytics-Readers];
-- Row-level via security policy
CREATE SECURITY POLICY rls.region_filter
  ADD FILTER PREDICATE rls.fn_region([region]) ON dbo.customer
  WITH (STATE = ON);
```

Caveats:

- `CREATE USER` isn't invoked explicitly — the user is created the first time
  you `GRANT` / `DENY` against it.
- The user must additionally have **Read** on the item (or a workspace role) to
  connect.
- RLS / CLS apply to T-SQL queries. Direct Lake **falls back to DirectQuery** to
  honor RLS, so plan for the perf delta.
- Grants must be re-applied on the SQL analytics endpoint even if defined on
  the source — they do not migrate via deployment pipelines.

Source: [SQL granular permissions in Fabric](https://learn.microsoft.com/fabric/data-warehouse/sql-granular-permissions) · [Row-level security in Fabric](https://learn.microsoft.com/fabric/data-warehouse/row-level-security).

### Are Entra ID groups supported?

**Yes — at every layer.**

- **Workspace roles**: Microsoft 365 groups, security groups, and distribution
  lists are all accepted. Nested groups are honored.
- **Item permissions / Share**: Entra groups accepted; permission propagation
  can lag up to two hours.
- **SQL endpoint T-SQL**: `GRANT` / `DENY` accept Entra groups directly:
  ```sql
  GRANT SELECT ON SCHEMA::sales TO [Sales-Analysts];   -- Entra group
  ```

Source: [Roles in workspaces in Microsoft Fabric](https://learn.microsoft.com/fabric/fundamentals/roles-workspaces) · [Fabric Data Warehouse security](https://learn.microsoft.com/fabric/data-warehouse/security).

### Which group owns the mirrored Databricks workspace — EDW or Analytics?

**EDW (data platform team).** Microsoft's adoption guidance calls the mirrored
database a "data product"; ownership goes to whoever owns the upstream
source. The Analytics team gets a **separate consumption workspace** (Power
BI semantic models, reports, paginated reports).

Use **Fabric Domains** to group both workspaces under a single business
domain so the Analytics team gets discoverability without ownership.

Important caveat: shared recipients access using the **item owner's
identity** in delegated mode — if the EDW owner is removed from the
workspace, downstream Analytics consumers lose access. Set the owner to a
**service principal or Workspace Identity**, not an individual.

Source: [Fabric adoption roadmap — Content ownership and management](https://learn.microsoft.com/power-bi/guidance/fabric-adoption-roadmap-content-ownership-and-management) · [Domains best practices](https://learn.microsoft.com/fabric/governance/domains-best-practices) · [Share warehouse — manage permissions](https://learn.microsoft.com/fabric/data-warehouse/share-warehouse-manage-permissions).

### How does UAT work when only PROD is mirrored?

Microsoft's recommended pattern is **mirror once, share everywhere** — but
that doesn't mean "only mirror PROD." For Fabric-side validation:

1. Upstream Databricks maintains separate UAT and PROD Unity Catalogs (the
   real data isolation lives upstream).
2. In Fabric, mirror **each** Databricks environment once into a dedicated
   mirroring workspace (`mirror-databricks-uat`, `mirror-databricks-prod`).
3. Downstream consumer Fabric workspaces (semantic models, reports) are
   promoted UAT → PROD via Deployment Pipelines, with Data Source rules
   re-pointing them at the appropriate mirror.

Mirroring is **excluded from Deployment Pipeline content promotion** (only
the item definition is captured in Git; the SQL endpoint and views are not).
You must manually start the mirror after deploying to a new environment.

If you mirror **only PROD**, your UAT consumers can't validate the same
query path (SQL endpoint behavior, RLS, view definitions, semantic-model
framing) that PROD will use — explicitly mirror UAT too if your release gate
requires it.

Source: [CI/CD for mirrored databases in Fabric](https://learn.microsoft.com/fabric/mirroring/mirrored-database-cicd) · [Fabric deployment patterns](https://learn.microsoft.com/azure/architecture/data-guide/technology-choices/fabric-deployment-patterns).

---

## 4. Fabric Workspace Setup for Analytics on Mirrored Databricks

> **Scenario.** Analytics group wants to maintain its own Lakehouse to blend
> Databricks data with non-core systems, then use Direct Lake for reporting.

### What can / can't you do against a mirrored Databricks database?

| Capability | Status | Notes |
|---|---|---|
| Query mirrored tables via T-SQL on the SQL analytics endpoint | ✅ Read-only | No INSERT / UPDATE / DELETE / MERGE on mirrored tables |
| `CREATE VIEW` / inline TVFs / stored procedures | ✅ Supported | See Topic 2 |
| `GRANT` / `DENY` / RLS / CLS | ✅ Supported | See Topic 3 |
| Save / share queries in SQL editor | ✅ Supported | Saved queries persist; SSMS + mssql VS Code extension supported |
| Cross-database queries (`MirrorDB.schema.table` in a Warehouse) | ✅ Supported | Same workspace only |
| PySpark notebook **read** via FQN `workspace.mirrorDB.schema.table` | ✅ Supported | Requires schema-enabled lakehouse attached, or no lakehouse |
| PySpark notebook **write** back to mirror | ❌ Not supported | Mirror is read-only; write to a Lakehouse instead |
| Direct Lake on SQL endpoint | ✅ GA | Fallback to DirectQuery on RLS / views / capacity guardrails |
| Direct Lake on OneLake (composite-capable) | ✅ GA | No DirectQuery fallback; supports composite models |

Source: [Limitations: Fabric mirrored databases from Azure Databricks](https://learn.microsoft.com/fabric/mirroring/azure-databricks-limitations) · [Query mirrored databases in Spark notebooks](https://learn.microsoft.com/fabric/data-engineering/query-mirrored-database-spark-notebooks).

### Can a single semantic model combine Direct Lake against both a mirror and a Lakehouse?

**Yes — but only with Direct Lake on OneLake.**

| Mode | Composite Direct Lake (mirror + lakehouse) | Notes |
|---|---|---|
| **Direct Lake on SQL** | ❌ No | Single data source only |
| **Direct Lake on OneLake** | ✅ Yes | Mix tables from lakehouses, warehouses, SQL DBs, mirrored DBs; can also add Import-mode tables from any Power Query connector |

Direct Lake on OneLake reads Delta files directly from OneLake (the mirror
lands in OneLake), bypassing the SQL endpoint for data load. For the Analytics
team's use case — blending Databricks-mirrored tables with non-core sources —
**Direct Lake on OneLake is the right model**.

Source: [Direct Lake overview — Comparison of storage modes](https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview#comparison-of-storage-modes) · [Direct Lake on Power BI Desktop](https://learn.microsoft.com/fabric/fundamentals/direct-lake-power-bi-desktop).

### Do customers typically run Warehouse / Lakehouse and Reports in separate workspaces?

**Yes — this is Microsoft's documented "data workspace vs reporting workspace"
pattern**, often layered under a Fabric Domain. The Power BI implementation
planning guide recommends separating:

- **Data workspace** — lakehouses, warehouses, SQL DBs, pipelines, dataflows,
  semantic models (the data product)
- **Reporting workspace** — reports, dashboards, metrics (the consumption layer)

For multi-medallion teams, this can further split into *Bronze workspace*,
*Silver/Gold workspace*, and *Reports workspace* per data product, with
**OneLake shortcuts** as the cross-workspace glue.

Source: [Power BI implementation planning — Workspace-level planning](https://learn.microsoft.com/power-bi/guidance/powerbi-implementation-planning-workspaces-workspace-level-planning) · [Fabric deployment patterns](https://learn.microsoft.com/azure/architecture/data-guide/technology-choices/fabric-deployment-patterns).

### Can a report's semantic model in Workspace A query a mirrored Databricks in Workspace B?

**Yes — this is the standard Direct Lake pattern.**

Hard constraints:

- **Region**: model and source must live in the **same region**. Workaround:
  create a Lakehouse in the model's region and shortcut to the cross-region
  source.
- **Permissions** the binding identity (see service-account section below)
  must have:
  - **Read** on the mirrored DB item in Workspace B
  - **ReadData** (Direct Lake on SQL) or **ReadAll** / OneLake Security role
    (Direct Lake on OneLake)
- **Semantic-model owner** must also have read access — framing is checked
  against the owner, not the runtime user.
- If **Workspace Outbound Access Protection** (preview) is enabled, you must
  add explicit exception rules (SQL FQDN or OneLake URL).

Source: [Direct Lake security integration](https://learn.microsoft.com/fabric/fundamentals/direct-lake-security-integration) · [Workspace outbound access protection for semantic models](https://learn.microsoft.com/fabric/security/workspace-outbound-access-protection-semantic-models).

### Does this require a service account?

**Either SSO or a fixed identity works — but a fixed identity is the recommended
pattern for cross-workspace and embedded scenarios.**

| Auth mode | When to use | Caveat |
|---|---|---|
| **SSO (default)** | Interactive reports where every consumer has source access | Consumers must have Read + ReadData on the mirror; breaks for embed and for users without source grants |
| **Service Principal** | XMLA refresh, automation, deployment pipelines | Workspace SPN must be enabled at tenant + capacity; **SPN profiles are NOT supported** for Direct Lake |
| **Workspace Identity** | Cross-workspace Direct Lake, isolated consumer workspaces | GA in April 2026 wave; recommended over individual SPNs for new builds |

For the Analytics team's scenario (their own workspace consuming the EDW
team's mirror), the recommended pattern is:

1. EDW team creates a **Workspace Identity** for the mirror workspace.
2. Workspace Identity is granted **Read + ReadData** on the mirror.
3. Analytics team's semantic model is bound to a connection using **SSO
   disabled, fixed identity = Workspace Identity**.
4. Report consumers need only **Read** on the semantic model, not the mirror.

Source: [Direct Lake security integration](https://learn.microsoft.com/fabric/fundamentals/direct-lake-security-integration) · [Service principals for Fabric](https://learn.microsoft.com/fabric/enterprise/powerbi/service-premium-service-principal) · [Workspace identity](best-practices/network-security.md#workspace-identity).

---

## 5. SharePoint, Fabric SQL Database, and DataFlow Gen2

### SharePoint Shortcut + automatic DataFlow Gen2 / Pipeline trigger

> **Scenario.** Files land in a Lakehouse via OneLake Shortcut to a SharePoint
> Document Library. Want: user uploads file → DataFlow processes it → output
> as clean CSV / XLSX returned to user.

**OneLake events do NOT fire on shortcut targets.** The OneLake event grid
(`Microsoft.Fabric.OneLake.FileCreated`) only fires when files are written to
**OneLake-native storage** (Files/Tables in a Lakehouse). Shortcuts are
pointers — the file is still written to the SharePoint store, so no OneLake
event is emitted.

**Supported alternatives, in order of preference:**

1. **Power Automate SharePoint trigger → Fabric Pipeline REST API**.
   *"When a file is created (properties only)"* SharePoint trigger →
   HTTP action calling
   `POST /v1/workspaces/{ws}/items/{pipelineId}/jobs/instances?jobType=Pipeline`
   with a file-path parameter. This is the **canonical Microsoft pattern**.
2. **Scheduled Fabric Pipeline** that scans the shortcut folder via
   `Get Metadata` → `ForEach` → parameterized `Copy` / `Dataflow`. Simplest
   fallback; latency = the schedule interval.
3. **Activator + OneLake events** is viable only if you first **copy** the
   file from the SharePoint shortcut into a native OneLake folder — which
   then emits FileCreated events.

For the **self-service file processing pattern**:

```
[User uploads file to SharePoint]
         │
         │  Power Automate SharePoint trigger
         ▼
[Power Automate flow]
         │
         │  HTTP POST → Fabric Pipeline REST API (runOnDemand)
         ▼
[Fabric Pipeline: Copy + Dataflow Gen2 transformation]
         │
         │  Output as CSV/XLSX
         ▼
[SharePoint Document Library or OneDrive — via SharePoint connector "Create file"]
```

Caveats:

- SharePoint triggers in Power Automate do **not fire on subfolders** — create
  multiple flows or use the parent library.
- Power Automate's per-flow license matters at volume (Pay-as-you-go vs
  per-user plans).

Source: [OneLake events](https://learn.microsoft.com/fabric/real-time-hub/explore-fabric-onelake-events) · [Build event-driven data pipelines](https://learn.microsoft.com/fabric/real-time-hub/tutorial-build-event-driven-data-pipelines) · [SharePoint connector triggers in Power Automate](https://learn.microsoft.com/sharepoint/dev/business-apps/power-automate/sharepoint-connector-actions-triggers) · [Fabric Pipeline REST API](https://learn.microsoft.com/fabric/data-factory/pipeline-rest-api-capabilities).

### Fabric SQL Database — ingestion best practices

Fabric SQL Database (distinct from Fabric Data Warehouse) has a **narrower
ingestion surface** than Azure SQL DB. Defaults:

- **Connection**: TDS over **TCP port 1433** only. Open this on your gateway
  / firewall.
- **Authentication**: **Microsoft Entra ID only** — no SQL logins, no Windows
  auth. Use a service principal for automation.
- **Recovery model**: Full only. No minimal logging in bulk import.
- **CDC**: Not available — use Fabric **Mirroring** to OneLake instead
  (auto-enabled for Fabric SQL DB).
- **Encryption**: System-managed TDE only. **Customer-managed keys (CMK) are
  not supported.**

**Recommended ingestion patterns**:

| Pattern | Supported? | Notes |
|---|---|---|
| `OPENROWSET(BULK ...)` from OneLake / ADLS / S3 / GCS via shortcuts | ✅ Yes (preview) | The primary bulk-load path |
| Fabric Pipeline Copy activity (via TDS) | ✅ Yes | Use this for orchestrated loads |
| DataFlow Gen2 to Fabric SQL DB destination | ✅ Yes | Schema-on-write; see destination guidance |
| Pre-stage 100 MB – 1 GB files for parallelism | ✅ Recommended | Inherits Warehouse file-size guidance |

Source: [Fabric SQL Database limitations](https://learn.microsoft.com/fabric/database/sql/limitations) · [Data virtualization in Fabric SQL Database (OPENROWSET)](https://learn.microsoft.com/fabric/database/sql/data-virtualization).

### Ingestion patterns that are NOT supported in Fabric SQL Database

| Pattern | Status | Replacement |
|---|---|---|
| Native `BULK INSERT` from file path | ❌ Not supported | Use `OPENROWSET(BULK)` from OneLake |
| Legacy `OPENROWSET` (non-BULK) | ❌ Not supported | Only the BULK function is supported |
| `COPY INTO` (T-SQL statement) | ❌ Not supported | This is **Warehouse-only**; do not confuse |
| SQL Server transactional / snapshot / merge replication | ❌ Not supported | Use Mirroring (replaces CDC + replication) |
| CDC (Change Data Capture) | ❌ Not supported | Mirroring is auto-enabled for Fabric SQL DB |
| MS DTC / distributed transactions | ❌ Not supported | Re-architect to local transactions |
| `BACKUP` / `RESTORE` | ❌ Not supported | System-managed backups only |
| Customer-managed keys / TDE custom | ❌ Not supported | System-managed TDE only |
| SSIS direct write (OLE DB destination) | ⚠️ Works through TDS but **not optimized**; no minimal logging | Prefer Fabric Pipeline / DataFlow Gen2 |
| Linked servers (as source) | ❌ Not supported | Linked-server **target** is allowed |

For ODBC bulk-load drivers, the most common errors are caused by:

1. **TDS version mismatch** — Fabric SQL DB requires modern TDS (8.0+). Older
   drivers will negotiate down and fail. Update the driver to **ODBC Driver 18
   for SQL Server** (17.x is too old for some scenarios).
2. **Port 1433 blocked** — verify outbound 1433 on the gateway / proxy / corporate
   firewall.
3. **SQL login fallback** — ODBC drivers default to SQL auth; force `Authentication=ActiveDirectoryServicePrincipal` or `ActiveDirectoryInteractive` in the connection string.

Source: [Fabric SQL Database limitations](https://learn.microsoft.com/fabric/database/sql/limitations) · [OPENROWSET BULK in Fabric SQL DB](https://learn.microsoft.com/sql/t-sql/functions/openrowset-bulk-transact-sql?view=fabric-sqldb).

### DataFlow Gen2 unable to select a Lakehouse destination when reading via Power BI gateway

This is a **documented limitation**, not a bug.

**Root cause**: DataFlow Gen2 staging uses **TDS over TCP 1433** to read from
its internal staging Lakehouse. On-prem gateways and corporate proxies
frequently:

- Block outbound 1433 (only allow HTTPS/443).
- Only proxy generic HTTP/TLS (not TDS).

When a gateway-bound dataflow has **multiple queries that reference each
other**, the second query can't read staged results from the staging
Lakehouse over 1433 → `WriteToDatabaseTableFrom_*` error.

Additional constraints:

- **Gateway version**: minimum **3000.270 (May 2025)** for incremental refresh
  + Lakehouse destination; **3000.290+** for "Navigate using full hierarchy"
  schema support.
- Lakehouse destination does **not** support spaces or special characters in
  column / table names, and does not support `Duration` or `Binary` columns.

**Documented workarounds** (in order of robustness):

1. **Open outbound TCP 1433** from the gateway server to Fabric SQL endpoints.
   The proxy must support TDS, not just HTTP.
2. **Single-query design** — write directly to Lakehouse, do not reference
   staged queries. Disable Fast Copy.
3. **Stage to ADLS Gen2 first**: a Fabric Pipeline `Copy` activity reads from
   the gateway → writes to ADLS Gen2, then a **cloud-only** DataFlow Gen2 or
   Pipeline loads ADLS Gen2 → Lakehouse. This is the most robust enterprise
   pattern when the gateway environment can't open TCP 1433.
4. **Upgrade the gateway** to at least 3000.270.

Source: [Gateway considerations for DataFlow Gen2 destinations](https://learn.microsoft.com/fabric/data-factory/gateway-considerations-output-destinations) · [DataFlow Gen2 limitations](https://learn.microsoft.com/fabric/data-factory/data-factory-limitations#data-factory-dataflow-gen2-limitations) · [DataFlow Gen2 incremental refresh limitations](https://learn.microsoft.com/fabric/data-factory/dataflow-gen2-incremental-refresh#limitations) · [Lakehouse connector for DataFlow Gen2](https://learn.microsoft.com/fabric/data-factory/connector-lakehouse-overview).

---

## 📚 Related Documentation

- [Mirroring](features/mirroring.md) — Fabric Mirroring end-to-end
- [Direct Lake](features/direct-lake.md) — connectivity, guardrails, fallback
- [Network Security](best-practices/network-security.md) — VNet, private endpoints, managed VNet
- [Fabric SQL Database](features/fabric-sql-database.md) — overview + best practices
- [DataFlow Gen2](features/dataflow-gen2.md) — destinations, refresh, gateway
- [Identity & RBAC Patterns](best-practices/identity-rbac-patterns.md) — workspace roles, item permissions, Entra ID groups
- [Multi-Tenant Workspace Architecture](best-practices/multi-tenant-workspace-architecture.md) — production vs UAT, cross-workspace patterns
- [Outbound Access Protection](best-practices/outbound-access-protection.md) — workspace egress controls

---

*If you have a scenario not covered here, file an issue at*
*[fgarofalo56/Suppercharge_Microsoft_Fabric/issues](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/issues)*
*and tag it `field-question`.*
