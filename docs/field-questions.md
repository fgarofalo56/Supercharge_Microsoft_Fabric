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

**Last Updated:** `2026-09-15` | **Version:** 1.1.0

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

Source: [Direct Lake security integration](https://learn.microsoft.com/fabric/fundamentals/direct-lake-security-integration) · [Service principals for Fabric](https://learn.microsoft.com/fabric/enterprise/powerbi/service-premium-service-principal) · [Workspace identity](best-practices/network-security.md#workspace-level-network-isolation).

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

## 6. Fabric Disaster Recovery — Enterprise DR Strategy for a Regional Outage

> **Scenario.** A customer has adopted Fabric as their **Enterprise Data Platform**
> and is designing their DR strategy. After reviewing multiple Microsoft articles
> they are confused by apparently conflicting guidance, and want a definitive
> Microsoft position: what is actually available after a Microsoft-led regional
> failover, what the customer must rebuild themselves, whether DR can be tested,
> what happens on failback, and how to weigh cost against business risk. Primary
> region in this engagement: **Australia East**.

This section answers each concern in Q&A form. The full, source-cited treatment
lives in [Fabric DR — Authoritative Answers](best-practices/fabric-dr-authoritative-answers.md);
operational steps are in the [Multi-Region Failover](runbooks/multi-region-failover.md)
and [Disaster Recovery Execution](runbooks/disaster-recovery-execution.md) runbooks.

### 6.1 The documentation seems to conflict — which statement is right?

**Both are true; they describe different layers.** The apparent contradiction
resolves once you separate *data* from *service*:

- **"Services become operational after Microsoft-led recovery"** — refers to the
  **Fabric platform and portal** being restored by Microsoft so you can sign in
  and read data. Microsoft fails the *service* over.
- **"Replicated data is read-only and customers must rebuild capacities,
  workspaces, and artifacts"** — refers to **your workloads**. Geo-replicated
  OneLake *data* survives, but the *compute and item definitions* (capacity,
  workspaces, pipelines, notebooks, semantic models) are **not** automatically
  recreated in the secondary region. That rebuild is the customer's job.

So: Microsoft restores the **platform and your data**; you restore the
**running workloads** on top of it. Source: [Reliability in Microsoft Fabric](https://learn.microsoft.com/fabric/security/reliability-fabric).

### 6.2 What exactly is available after a Microsoft regional failover?

Assuming the DR capacity setting was **on** and the primary region has an
Azure-paired secondary where Fabric is supported:

| Component | State after Microsoft-led failover |
|-----------|-----------------------------------|
| **Fabric portal** | Read-only. You can browse workspaces and items; write operations (create/modify) are paused. |
| **Power BI reports** | **Viewable** (read). **Refresh, publish, and metadata edits are not supported.** |
| **OneLake data (Lakehouse/Warehouse)** | **Readable and writable via OneLake APIs / tools** (ADLS Gen2 API, Storage Explorer, OneLake File Explorer) through the global endpoint. The items themselves don't *open* in the portal, but the data is accessible. |
| **Pipelines / Dataflow Gen2 / Eventstream** | Cannot open or run. Protect their output by landing it in a lakehouse/warehouse (a supported DR destination). |
| **Notebooks** | Cannot open; **code content is not saved** across the disaster. Keep notebooks in Git. |
| **Spark Job Definitions** | Cannot open; code files accessible via OneLake; metadata/config saved. |
| **ML Models / Experiments** | Cannot open; code and run metadata **not saved**. |
| **KQL Database / Queryset** | **Not accessible after failover** — data is stored outside OneLake and needs a separate DR approach. |

**Direct answers to the customer's sub-questions:** reports are *accessible but
not refreshable*; pipelines *cannot run*; workspaces are *visible but not
usable for write operations*; replicated OneLake data is *fully readable and
writable via APIs* — but the *workloads* on top of it are not operational until
you rebuild them.

### 6.3 What recovery activities must the customer perform?

If you need workloads running again (not just data readable), the customer owns
the rebuild. The general plan:

1. **Create a new Fabric capacity** in a region outside the primary geo (high
   demand during an incident makes a different geo more likely to have compute).
2. **Create workspaces** on that capacity — **same names** as before (required
   for recovery scripts to resolve item references).
3. **Recreate items with the same names** as the ones being recovered.
4. **Restore each item** per the [experience-specific DR guidance](https://learn.microsoft.com/fabric/security/experience-specific-guidance).

**Can Git-integrated artifacts simply be redeployed from Azure DevOps?**
**Yes — this is the recommended pattern.** If your items (notebooks, pipelines,
semantic models, reports, warehouse definitions) are under Git integration, you
redeploy them into the new workspaces from source control rather than
rebuilding by hand. This project's own `scripts/fabric-cicd-deploy.py` does
exactly this. **Data is the exception** — Git holds *definitions*, not table
contents; data comes from the geo-replicated OneLake copy (or your own backup
for anything stored outside OneLake).

### 6.4 Can DR be tested before a real outage?

**Partially.** A Microsoft-declared regional failover **cannot be self-triggered**
— only Microsoft declares it. But you *can* validate everything you control:

- **Drill your own recovery runbook**: provision a second capacity, redeploy
  from Git, reconnect data, and measure how long it takes. This tests Option B
  (scripted recovery) end-to-end without touching production.
- **Validate data accessibility**: confirm you can read OneLake data via the
  ADLS Gen2 API / Storage Explorer from outside the portal.
- **Game-day the decision logic**: rehearse the "declare / communicate / cut
  over" process with leadership so the human steps are not first-time-under-pressure.

What you **cannot** test is Microsoft's actual failover of the platform itself.
For that you rely on Microsoft's SLA and the published reliability guidance —
there is no customer-invoked "failover drill" button.

### 6.5 What happens on failback when Australia East returns?

This is the area with the **least public Microsoft documentation** — be careful
not to over-promise. What we can say:

- Geo-replication is **asynchronous and one-directional** during the outage:
  primary → secondary. There is **no documented automatic "sync back"** of
  changes made in the secondary region to the primary once it recovers.
- **Data written to the secondary region during an extended outage is a
  potential gap.** If you run workloads in the secondary for weeks, that new
  data does not automatically flow back to Australia East.
- **Customer responsibilities on failback** (working assumption, pending
  Microsoft confirmation): plan a **controlled cutback** — quiesce writes in
  the secondary, copy/migrate any delta data back, redeploy/repoint workloads
  to the primary capacity, and validate before resuming normal operations.

Treat failback as a **planned migration you design and test**, not an automatic
platform event. Escalate to Microsoft for a written failback statement for this
customer's specific topology before committing an RTO/RPO to leadership.

### 6.6 How do we weigh cost versus business risk across the three options?

| | **A. Microsoft-managed geo-replication only** | **B. Scripted recovery automation** | **C. Active-active, two regions** |
|---|---|---|---|
| **What it is** | Rely on OneLake geo-replication + manual rebuild-on-incident | Pre-built, tested Git-redeploy + capacity scripts, triggered on demand | Two live capacities running concurrently, workload split or mirrored |
| **Cost** | Lowest compute, **but DR adds BCDR Storage + higher write CU** | Low-moderate — engineering time; one capacity most of the time | Highest — second capacity continuously + sync tooling |
| **Operational complexity** | Low day-to-day; high *during* an incident | Moderate — scripts need maintenance + drills | High — ongoing dual-region ops, consistency, conflict handling |
| **Achievable RTO** | Slow — bounded by an undrilled manual rebuild | Faster — bounded by measured script execution | Fastest — near-zero if truly active-active |
| **Achievable RPO** | Bounded by async replication lag (not zero, not tunable) | Same as A — automation speeds rebuild, not replication | Smallest, *if* inter-region sync is near-real-time (verify per store) |
| **When it fits** | Low-criticality, cost-sensitive, hours-to-a-day tolerance | **Most production enterprise workloads** — best leverage-per-dollar | Near-zero downtime tolerance justifying a second live capacity |

!!! tip "Where most enterprises land"
    **Option B** is the practical middle ground: cost close to A, but it converts
    A's "unbounded manual rebuild" risk into a measured, drillable, improvable
    process. This project's `fabric-cicd` pipeline is exactly this pattern —
    Git as source of truth, scripted redeploy on demand.

!!! warning "DR is not free"
    Enabling the DR capacity setting bills **BCDR Storage** plus **higher write
    CU consumption** (per-tier rates in the Capacity Metrics app). Factor this
    into the Option A/B/C cost comparison — DR-on costs more than DR-off even
    on a single capacity. See [OneLake consumption](https://learn.microsoft.com/fabric/onelake/onelake-consumption#disaster-recovery).

### 6.7 Where are the public SLA and compliance documents, and how do we raise a request with Microsoft?

Much of what the customer wants confirmed is already published. Start with the
public sources below; for anything not covered there, use the support-request
process at the end.

#### Service-level agreement (SLA)

- **[Service Level Agreements for Online Services](https://www.microsoft.com/licensing/docs/view/Service-Level-Agreements-SLA-for-Online-Services)**
  — the authoritative, downloadable SLA document that includes Microsoft Fabric.
  This is the contractual availability commitment.
- **[How to read a service-level agreement (SLA)](https://learn.microsoft.com/azure/reliability/concept-service-level-agreements)**
  — how to interpret an SLA correctly: what it does and doesn't guarantee, how
  availability is defined and measured, and the conditions/exclusions that shape
  coverage. Important context before treating any uptime figure as a DR guarantee.
- **Component SLAs differ.** For example, the [Data Factory pipeline SLA in Fabric](https://learn.microsoft.com/fabric/data-factory/data-factory-overview)
  is equivalent to Azure Data Factory (99.9% of operations processed; activity
  runs initiate within four minutes of schedule 99.9% of the time). Check the
  per-workload SLA rather than assuming one figure covers all of Fabric.
- **Support responsiveness is separate from the service SLA.** Microsoft commits
  to an *initial response time* for support requests but [does not provide an SLA
  for support-request *resolution*](https://learn.microsoft.com/power-bi/support/service-support-options).

#### Compliance and audit documentation

- **[Standards compliance in Microsoft Fabric](https://learn.microsoft.com/fabric/governance/standards-compliance)**
  — Fabric's adherence to compliance standards and the governing terms (Microsoft
  Online Services Terms, Data Protection Addendum).
- **[Microsoft compliance offerings](https://learn.microsoft.com/compliance/regulatory/offering-home)**
  — the full catalog of certifications/attestations (ISO 27001/27017/27018/27701,
  HIPAA, SOC, FedRAMP, etc.) grouped by global / US-government / industry /
  regional scope.
- **[Service Trust Portal](https://servicetrust.microsoft.com/)** — where you
  download the actual audit reports, certificates, and assessment documents
  (ISO, SOC, PCI, FedRAMP, and regional/industry offerings). Requires sign-in
  with an Azure subscription or trial.
- **[Microsoft Trust Center](https://www.microsoft.com/trustcenter)** — the
  primary entry point for Fabric compliance information.

#### How to raise a request with Microsoft

For anything **not** answered by the public documents above, the supported
channel is a Microsoft support request:

1. **Azure portal → Help + support → Create a support request.** Step-by-step:
   [Create an Azure support request](https://learn.microsoft.com/azure/azure-portal/supportability/how-to-create-azure-support-request).
2. **Fabric-specific support options and scope** (what's break-fix vs. advisory,
   preview-feature support, outage/SIE handling):
   [Fabric and Power BI support overview](https://learn.microsoft.com/power-bi/support/service-support-options).
3. **Initial response times by support plan and severity:**
   [Support scope and responsiveness](https://azure.microsoft.com/support/plans/response/).
4. **During an active outage**, check the [Fabric Support page](https://support.fabric.microsoft.com/support)
   and Microsoft 365 Service Health / Message center first, then contact support
   if no active incident is listed.

> Non-public confirmations (for example, customer-specific architecture reviews
> or contractual commitments beyond the published SLA) are handled through your
> Microsoft account team or a support request — there is no public self-service
> form for those.

---

## 📚 Related Documentation

- [Fabric DR — Authoritative Answers](best-practices/fabric-dr-authoritative-answers.md) — full source-cited DR treatment
- [Disaster Recovery & BCDR](best-practices/disaster-recovery-bcdr.md) — BCDR patterns
- [Multi-Region Failover runbook](runbooks/multi-region-failover.md) — operational failover steps
- [Disaster Recovery Execution runbook](runbooks/disaster-recovery-execution.md) — DR execution steps
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
*[fgarofalo56/Supercharge_Microsoft_Fabric/issues](https://github.com/fgarofalo56/Supercharge_Microsoft_Fabric/issues)*
*and tag it `field-question`.*
