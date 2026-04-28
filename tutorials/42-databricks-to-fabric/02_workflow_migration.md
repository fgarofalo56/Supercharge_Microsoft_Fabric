[Home](../../docs/index.md) > [Tutorials](../) > [42 — Databricks → Fabric](./README.md) > Workflow Migration Reference

# 🔁 Tutorial 42 — Reference: Databricks Workflows → Fabric Pipelines + Spark Job Definitions

> **Last Updated**: 2026-04-27 | **Phase**: 14 (Wave 4) | **Companion to** [Tutorial 42 — Databricks → Fabric](./README.md)
> **Status**: ✅ Final | **Maintainer**: Platform Team

<div align="center">

![Difficulty](https://img.shields.io/badge/Difficulty-Advanced-red?style=for-the-badge)
![Category](https://img.shields.io/badge/Category-Migration_Reference-blue?style=for-the-badge)
![Phase](https://img.shields.io/badge/Phase-14%20Wave%204-green?style=for-the-badge)

</div>

---

## 📖 Overview

This is the deep-dive reference for **Step 5** of [Tutorial 42](./README.md): converting **Databricks Workflows / Jobs** to **Fabric Data Pipelines** and **Spark Job Definitions**. The parent tutorial gives you the high-level activity-mapping table; this doc gives you the canonical translation matrix, cluster/trigger/parameter handling, three worked examples (simple notebook, multi-task DAG, and DLT → Materialized Lake View), DLT-specific guidance, bulk-export tooling, and migration anti-patterns.

Use this reference when:

- You need the **full task-type → activity** map (not just the common ones)
- You're translating **cluster specs, init scripts, or library installs** into Fabric Environments
- You're rewriting **DLT pipelines** as Materialized Lake Views or scheduled notebooks
- You're scripting **bulk export** of Workflow JSON from a large Databricks estate
- You want the **anti-patterns** so you don't lift-and-shift things that should be redesigned

---

## 🧭 Workflow Type Mapping

The first decision is *which* Fabric construct each Databricks workflow becomes. Most jobs map to a Fabric **Pipeline**, but a few map to a **Spark Job Definition**, an **Eventstream**, or a **Materialized Lake View**.

| Databricks Construct | Fabric Equivalent | Notes |
|----------------------|-------------------|-------|
| **Workflow Job (multi-task DAG)** | **Fabric Pipeline** | Tasks → activities; dependencies → activity links |
| **Single-task scheduled notebook** | **Fabric Pipeline** with one Notebook activity, **OR** notebook with native schedule | Use Pipeline if it needs a Variable Library or chained activities; use native schedule for simple repeats |
| **JAR / Wheel / spark-submit job** | **Spark Job Definition (SJD)** | Headless Spark execution; not a Pipeline activity by itself — invoked from a Pipeline if orchestrated |
| **Job cluster (ephemeral)** | **Fabric Spark capacity** (auto-allocated within F-SKU) | No 1:1 cluster object — Fabric autoscales sessions out of CU pool |
| **All-purpose cluster (interactive)** | **Fabric Spark session** (notebook attached to Lakehouse) | For interactive dev only; not a deploy target |
| **Job cluster pools** | No direct equivalent | F-SKU CU pool replaces the warm-pool concept |
| **DLT Pipeline (declarative)** | **Materialized Lake View (MLV)** for SQL DLT, **OR** scheduled notebook chain for Python DLT | See [DLT-Specific Migration](#-dlt-specific-migration) below |
| **Continuous (always-on) job** | **Fabric streaming notebook** + **Eventstream** trigger | Not a Pipeline — re-author against Eventstream/Eventhouse |
| **Webhook-triggered job** | **Pipeline** invoked via REST API + Logic App / Power Automate | Storage event triggers also possible |

> ⚠️ **Gotcha**: Don't reflexively put every Databricks job inside a Pipeline. A heavy production Spark batch (gigabytes of input, a single executable script) is usually a better fit as a **Spark Job Definition**. Pipelines are for **orchestration** of activities; SJDs are for **execution** of code. See [Spark Job Definitions](../../docs/features/spark-environments-job-definitions.md).

---

## 🧩 Task Type Mapping (Canonical Reference)

Every Databricks task type, with the recommended Fabric construct.

| Databricks Task Type | Fabric Equivalent | Notes |
|----------------------|-------------------|-------|
| `notebook_task` | **Notebook** activity | Direct map — re-point notebook reference; widget params → activity parameters |
| `notebook_task` (heavy ETL) | **Spark Job Definition** activity | Convert notebook to `.py` if you want headless execution and faster cold-start |
| `spark_jar_task` | **Spark Job Definition** (Java/Scala) | Repackage JAR; reference from SJD; pass args via SJD command line |
| `spark_python_task` (Python script) | **Spark Job Definition** (Python) **OR** Notebook with `%run` | SJD if it's truly headless; Notebook if you want widget-style params |
| `python_wheel_task` | **Spark Job Definition** + Environment with custom `.whl` | Upload wheel to Environment; reference entry-point in SJD |
| `spark_submit_task` | **Spark Job Definition** | Translate `--conf`, `--py-files`, `--jars` into SJD reference files + Spark properties |
| `sql_task` (DBSQL query) | **Script** (T-SQL) **OR** **Lookup** **OR** **Stored procedure** activity | Lookup if you need return values; Script for fire-and-forget DDL/DML |
| `sql_task` (DBSQL alert) | **Pipeline** + **Web** activity (to alerting system) **OR** **Activator** | Alert logic re-authored as expression on Lookup output |
| `sql_task` (DBSQL dashboard refresh) | Power BI semantic model refresh activity | Dashboards re-authored as Power BI reports |
| `dbt_task` | **Notebook** with `dbt-fabric` adapter **OR** external dbt runner via Web activity | See [dbt Fabric Integration](../../docs/features/dbt-fabric-integration.md) |
| `pipeline_task` (DLT) | **Materialized Lake View** (SQL DLT) **OR** scheduled Notebook chain (Python DLT) | See [DLT-Specific Migration](#-dlt-specific-migration) |
| `for_each_task` | **ForEach** activity | Direct map; iteration over array parameter |
| `condition_task` (If/Else, run-if) | **If Condition**, **Switch**, or **Until** activity | If/Else → If Condition; multi-branch → Switch; loop-with-exit → Until |
| `run_job_task` (sub-job) | **Invoke Pipeline** activity (a.k.a. Execute Pipeline) | Direct map — child pipeline reference |
| Webhook task | **Web** activity | HTTP POST/GET; supports auth via Workspace Identity or Key Vault |
| Custom workflow task (e.g., Airflow operator) | Custom code in **Notebook** activity | Translate operator logic into PySpark/Python |
| Job-completion trigger | **Invoke Pipeline** activity in chain | Chain pipelines instead of triggering on completion |
| File-arrival trigger | **Storage event trigger** on Pipeline (via Logic App + REST) | Native file triggers landing in late 2026; Logic App bridge today |

> 💡 **Tip**: Anything labelled "custom workflow task" in Databricks (where teams have built their own operator framework) should be the **first** thing you redesign — don't port the framework, port the *intent*. A Notebook activity calling a small Python module beats reimplementing the operator runtime.

---

## ☁️ Cluster Configuration Translation

Databricks job-cluster definitions live inside the Job JSON (under `new_cluster`). Fabric does not have explicit cluster objects — instead, Spark sessions are allocated against the F-SKU CU pool, with **Spark properties**, **library lists**, and **resources** declared in a **Fabric Environment**.

| Databricks Cluster Field | Fabric Equivalent | Notes |
|--------------------------|-------------------|-------|
| `spark_version` (e.g., `14.3.x-scala2.12`) | Fabric Spark Runtime (1.3 / 2.0) | Pick the runtime closest to DBR major; see [Spark Runtime Migration](../../docs/best-practices/spark-runtime-migration.md) |
| `node_type_id` (e.g., `Standard_E8s_v3`) | No equivalent — sized by CU | Fabric chooses node sizing from F-SKU; tune via `spark.executor.memory` if needed |
| `driver_node_type_id` | No equivalent | Driver memory tuned via `spark.driver.memory` Spark property |
| `num_workers` (fixed) | No equivalent | Fabric autoscales; control with `spark.dynamicAllocation.maxExecutors` |
| `autoscale.min_workers` / `max_workers` | `spark.dynamicAllocation.minExecutors` / `maxExecutors` | Fabric handles allocation; you set the bounds |
| `spark_conf` (dict) | Environment **Spark properties** | Direct copy with key remapping (`spark.databricks.*` → `spark.microsoft.*` where applicable) |
| `spark_env_vars` | Environment YAML `env:` section | Set via Environment, not per-session |
| `init_scripts` | Environment **Resources** + custom library | Repackage init logic as a `.whl` or `.tar.gz` and upload to Environment |
| `cluster_log_conf` (DBFS log path) | Workspace Monitoring | Logs go to workspace monitoring eventhouse — see [Workspace Monitoring](../../docs/features/workspace-monitoring.md) |
| `aws_attributes` / `azure_attributes` | F-SKU region + Workspace Identity | Identity grants replace IAM role passthrough |
| `instance_pool_id` | No equivalent — F-SKU CU pool | Warm-pool semantics built into capacity |
| `enable_elastic_disk` | Always-on in Fabric | No setting required |
| `runtime_engine: PHOTON` | Fabric Native Execution Engine (NEE) | NEE is the default for V-Order Delta workloads |
| Library install (PyPI) | Environment **Public Libraries** | Add to Environment; Publish required |
| Library install (Maven) | Environment custom JAR upload | Download JAR, upload to Environment |
| Library install (CRAN) | Environment R libraries | R support varies by Fabric Spark runtime — check coverage |
| Cluster policies | Fabric capacity governance + Environment governance | Use workspace roles + Environment publish gates |

For full Environment authoring detail (YAML, library priority, conflict resolution), see [Spark Environments & Job Definitions](../../docs/features/spark-environments-job-definitions.md).

### Example — Cluster Spec → Environment YAML

```yaml
# Databricks job-cluster (excerpt from Job JSON):
# {
#   "new_cluster": {
#     "spark_version": "14.3.x-scala2.12",
#     "node_type_id": "Standard_E8s_v3",
#     "autoscale": {"min_workers": 2, "max_workers": 10},
#     "spark_conf": {
#       "spark.sql.shuffle.partitions": "400",
#       "spark.databricks.delta.optimizeWrite.enabled": "true"
#     },
#     "init_scripts": [{"workspace": {"destination": "/Shared/init/install_geo.sh"}}],
#     "spark_env_vars": {"PYTHONHASHSEED": "0"}
#   }
# }

# Fabric Environment (env-migrated-bronze.yml):
name: env-migrated-bronze
runtime: 1.3
dependencies:
  - geopy==2.4.1
  - h3==3.7.7
  - shapely==2.0.3
custom_libraries:
  - geo_helpers-1.0.0-py3-none-any.whl   # repackaged from init_scripts
spark_properties:
  spark.sql.shuffle.partitions: "400"
  spark.databricks.delta.optimizeWrite.enabled: "true"
  spark.dynamicAllocation.minExecutors: "2"
  spark.dynamicAllocation.maxExecutors: "10"
env:
  PYTHONHASHSEED: "0"
```

---

## ⏰ Trigger / Schedule Translation

| Databricks Trigger | Fabric Equivalent | Notes |
|--------------------|-------------------|-------|
| `schedule` (cron) | **Pipeline schedule trigger** | Same cron syntax; check timezone (`timezone_id`) |
| `continuous` (always-on streaming) | **Eventstream trigger** **OR** scheduled Notebook with `availableNow=True` at high frequency | Re-author against Eventstream — see [Real-Time Intelligence](../../docs/features/real-time-intelligence.md) |
| `file_arrival` trigger | **Storage event trigger** on Pipeline via Logic App + REST API call | Native triggers landing late 2026; Logic App bridge today |
| `job_completion` trigger | **Invoke Pipeline** activity in a parent pipeline | Chain pipelines explicitly instead of relying on event chaining |
| `pause_status: PAUSED` | Disable schedule on Pipeline | Direct toggle in Pipeline portal or REST |
| `max_concurrent_runs` | Pipeline concurrency setting | Fabric default 1; raise if your job is reentrant |
| Retry policy (`max_retries`, `min_retry_interval_millis`) | Activity-level **Retry** + **Retry interval** | Set per activity, not per pipeline |

### Example — Cron Schedule

```json
// Databricks Job schedule:
"schedule": {
  "quartz_cron_expression": "0 0 2 * * ?",
  "timezone_id": "America/Los_Angeles",
  "pause_status": "UNPAUSED"
}
```

```json
// Fabric Pipeline schedule:
{
  "type": "Schedule",
  "frequency": "Day",
  "interval": 1,
  "startTime": "2026-04-27T02:00:00",
  "timeZone": "Pacific Standard Time"
}
```

> 💡 **Tip**: Quartz cron uses 7 fields (with seconds + day-of-week); Fabric uses ISO 8601 frequency/interval **or** simple cron (5 fields). The conversion script translates Quartz → Fabric, but always spot-check edge cases (e.g., `L` for last-day-of-month).

---

## 🔣 Parameter Handling

| Concept | Databricks | Fabric | Migration Notes |
|---------|-----------|--------|-----------------|
| Job-level parameters | `parameters[]` array on Job | Pipeline **parameters** | Direct map; types: string, int, bool, array |
| Task-level parameters | `notebook_task.base_parameters` | **Activity** parameters | Direct map per Notebook activity |
| Default values | `default_value` on parameter | Pipeline parameter `defaultValue` | Direct map |
| Variable substitution | `{{job.parameters.xyz}}` | `@pipeline().parameters.xyz` | Different syntax — script does the rewrite |
| Per-environment values | Per-job override or shell injection | **Variable Library** binding | Promote shared values to a Variable Library |
| Inter-task data passing | `dbutils.jobs.taskValues.get/set(...)` | **Activity output** → expression `@activity('PrevActivity').output.xxx` | Different model — see [Cluster Reuse / Inter-Task Data](#-cluster-reuse--inter-task-data) |
| Dynamic value (date) | `{{start_time.iso_date}}` | `@formatDateTime(utcNow(), 'yyyy-MM-dd')` | Different expression language |
| Run ID | `{{job.run_id}}` | `@pipeline().RunId` | Direct map |

### Variable Library Binding

Promote anything used by ≥ 3 jobs to a Fabric **Variable Library**, with per-stage values (Dev / Test / Prod). See [Wave 7 — Variable Library Setup](../../docs/features/deployment-pipelines.md) for the full pattern.

```json
// Pipeline parameter bound to Variable Library:
{
  "name": "lakehouse_id",
  "type": "string",
  "defaultValue": "@variableLibrary('shared').lakehouse_id"
}
```

> ⚠️ **Gotcha**: Databricks `{{job.parameters.xyz}}` inside notebook code does **nothing** at notebook runtime — it's only resolved by Workflows. In Fabric, the same pattern requires `mssparkutils.notebook.exit()` for return values and parameter cells (tagged `parameters`) for input. The conversion script flags every `{{job.parameters.*}}` reference in notebook cells for rewrite.

---

## 🔄 Cluster Reuse / Inter-Task Data

Databricks workflows reuse a **single cluster** across tasks (cheaper, faster). Fabric autoscales sessions out of a CU pool — there's no "reuse a cluster" knob — but you achieve the same throughput by chaining activities tightly.

### Inter-Task Data Passing

| Pattern | Databricks | Fabric |
|---------|-----------|--------|
| Pass scalar from task A to task B | `dbutils.jobs.taskValues.set("k", v)` then `taskValues.get(taskKey="A", key="k")` | `mssparkutils.notebook.exit(json.dumps({"k": v}))` then `@activity('A').output.exitValue` |
| Share large DataFrame | Cluster-scoped temp view across tasks | Write to a Lakehouse staging table; downstream reads it |
| Share file artifact | DBFS path | OneLake `Files/` path passed as parameter |
| Conditional branch on prior result | `dbutils.jobs.taskValues` + `condition_task` | `If Condition` activity with `@equals(activity('A').output.exitValue, 'OK')` |

### Example — Notebook Returning a Value

```python
# Notebook A (Fabric):
result = compute_something()
mssparkutils.notebook.exit(str(result))   # always cast to str
```

```json
// Pipeline expression in downstream activity:
"@activity('NotebookA').output.exitValue"
```

> ⚠️ **Gotcha**: `notebook.exit()` only supports **string** return. For complex objects, return JSON and parse downstream with `@json(activity('A').output.exitValue)`.

---

## 🧪 Concrete Conversion Examples

Three end-to-end examples covering the most common migration shapes.

### Example 1 — Simple Scheduled Notebook

A daily notebook that runs at 02:00 UTC, reads yesterday's data, writes Bronze.

#### Source — Databricks Job JSON

```json
{
  "name": "daily_bronze_slot_ingest",
  "schedule": {
    "quartz_cron_expression": "0 0 2 * * ?",
    "timezone_id": "UTC",
    "pause_status": "UNPAUSED"
  },
  "tasks": [{
    "task_key": "ingest",
    "notebook_task": {
      "notebook_path": "/Repos/casino/bronze/01_bronze_slot_telemetry",
      "base_parameters": {
        "run_date": "{{start_time.iso_date}}",
        "source_db": "SlotManagement"
      }
    },
    "new_cluster": {
      "spark_version": "14.3.x-scala2.12",
      "node_type_id": "Standard_E8s_v3",
      "autoscale": {"min_workers": 2, "max_workers": 6}
    }
  }]
}
```

#### Target — Fabric Pipeline JSON

```json
{
  "name": "pl_daily_bronze_slot_ingest",
  "properties": {
    "parameters": {
      "run_date": {
        "type": "string",
        "defaultValue": "@formatDateTime(utcNow(), 'yyyy-MM-dd')"
      },
      "source_db": { "type": "string", "defaultValue": "SlotManagement" }
    },
    "activities": [{
      "name": "IngestBronzeSlots",
      "type": "TridentNotebook",
      "typeProperties": {
        "notebookId": "<fabric-notebook-id>",
        "workspaceId": "<workspace-id>",
        "parameters": {
          "run_date":  { "value": "@pipeline().parameters.run_date",  "type": "string" },
          "source_db": { "value": "@pipeline().parameters.source_db", "type": "string" }
        }
      },
      "policy": { "retry": 2, "retryIntervalInSeconds": 300 }
    }]
  },
  "schedule": {
    "frequency": "Day", "interval": 1,
    "startTime": "2026-04-28T02:00:00", "timeZone": "UTC"
  }
}
```

Runtime config (autoscale, spark_version) moves from the cluster spec to the **Environment** attached to the notebook. See [cluster translation](#-cluster-configuration-translation).

---

### Example 2 — Multi-Task DAG with Dependencies

Bronze → Silver → Gold, with Silver fanning out per region (ForEach).

#### Source — Databricks DAG

```
[bronze_load] ── depends_on ──▶ [silver_us, silver_eu, silver_apac] (parallel)
                                       │       │       │
                                       └───┬───┴───────┘
                                           ▼
                                       [gold_kpis]
```

```json
{
  "name": "etl_full",
  "tasks": [
    { "task_key": "bronze_load",
      "notebook_task": { "notebook_path": "/bronze/01_load" } },
    { "task_key": "silver_us",
      "depends_on": [{"task_key": "bronze_load"}],
      "notebook_task": { "notebook_path": "/silver/02_clean",
                         "base_parameters": {"region": "US"} } },
    { "task_key": "silver_eu",
      "depends_on": [{"task_key": "bronze_load"}],
      "notebook_task": { "notebook_path": "/silver/02_clean",
                         "base_parameters": {"region": "EU"} } },
    { "task_key": "silver_apac",
      "depends_on": [{"task_key": "bronze_load"}],
      "notebook_task": { "notebook_path": "/silver/02_clean",
                         "base_parameters": {"region": "APAC"} } },
    { "task_key": "gold_kpis",
      "depends_on": [
        {"task_key": "silver_us"},
        {"task_key": "silver_eu"},
        {"task_key": "silver_apac"}
      ],
      "notebook_task": { "notebook_path": "/gold/03_kpis" } }
  ]
}
```

#### Target — Fabric Pipeline

Replace the three parallel tasks with a single **ForEach** + **Notebook** activity:

```json
{
  "name": "pl_etl_full",
  "activities": [
    {
      "name": "BronzeLoad",
      "type": "TridentNotebook",
      "typeProperties": { "notebookId": "<bronze-nb>" }
    },
    {
      "name": "SilverFanout",
      "type": "ForEach",
      "dependsOn": [{ "activity": "BronzeLoad", "dependencyConditions": ["Succeeded"] }],
      "typeProperties": {
        "items": { "value": "@createArray('US','EU','APAC')", "type": "Expression" },
        "isSequential": false,
        "batchCount": 3,
        "activities": [{
          "name": "SilverClean",
          "type": "TridentNotebook",
          "typeProperties": {
            "notebookId": "<silver-nb>",
            "parameters": {
              "region": { "value": "@item()", "type": "string" }
            }
          }
        }]
      }
    },
    {
      "name": "GoldKpis",
      "type": "TridentNotebook",
      "dependsOn": [{ "activity": "SilverFanout", "dependencyConditions": ["Succeeded"] }],
      "typeProperties": { "notebookId": "<gold-nb>" }
    }
  ]
}
```

Three lessons from this conversion:
- **Replicated tasks → ForEach.** Don't mechanically port three near-identical tasks; collapse them.
- **Parallelism via `batchCount`.** Set `batchCount: 3` to match the Databricks parallel-fan behaviour.
- **Single notebook with a parameter.** The three Databricks notebooks were already parameterised — Fabric ForEach exposes that more directly.

---

### Example 3 — DLT Pipeline → Materialized Lake View

A SQL DLT pipeline that lands a streaming Bronze table and a Silver projection.

#### Source — Databricks DLT (SQL)

```sql
CREATE OR REFRESH STREAMING TABLE bronze_slot_telemetry
COMMENT "Raw slot events from Eventhub"
AS SELECT * FROM cloud_files(
    "abfss://raw@adlsdb01.dfs.core.windows.net/slots/",
    "json",
    map("cloudFiles.schemaLocation", "abfss://raw@adlsdb01.dfs.core.windows.net/_schemas/slots/")
);

CREATE OR REFRESH LIVE TABLE silver_slot_telemetry (
    CONSTRAINT valid_coin EXPECT (coin_in >= 0) ON VIOLATION DROP ROW
)
COMMENT "Cleansed slot telemetry"
AS SELECT
    machine_id,
    CAST(event_time AS TIMESTAMP) AS event_time,
    coin_in,
    coin_out,
    coin_in - coin_out AS net_revenue
FROM LIVE.bronze_slot_telemetry
WHERE event_time IS NOT NULL;
```

#### Target — Fabric Materialized Lake View

The Bronze (autoLoader) leg becomes an **Eventstream** (or **Copy Job CDC**), and the Silver leg becomes an **MLV**:

```sql
-- Silver as Materialized Lake View:
CREATE MATERIALIZED LAKE VIEW lh_silver.silver_slot_telemetry
AS SELECT
    machine_id,
    CAST(event_time AS TIMESTAMP) AS event_time,
    coin_in,
    coin_out,
    coin_in - coin_out AS net_revenue
FROM lh_bronze.bronze_slot_telemetry
WHERE event_time IS NOT NULL
  AND coin_in >= 0;        -- DLT EXPECT enforced as filter (drop semantics)
```

For the **expect** rule (`ON VIOLATION DROP ROW`), the conversion above embeds the predicate directly. For richer rules use a **Great Expectations checkpoint** in the upstream notebook — see [Wave 3 Data Contract Suite](../../docs/best-practices/testing-strategies.md#data-contract-suites).

> ⚠️ **Gotcha**: DLT `ON VIOLATION FAIL` (block-on-bad-data) has no MLV equivalent. Author it as a **GE checkpoint** on the Bronze table that fails the upstream pipeline run. Don't try to encode it as a `CHECK` constraint — Delta `CHECK` aborts the *write*, not the read.

---

## 🌊 DLT-Specific Migration

Because DLT is the most opinionated thing in Databricks Workflows, it's worth its own checklist.

### Decorator / SQL → Fabric Mapping

| DLT Construct | Fabric Equivalent | Notes |
|---------------|-------------------|-------|
| `@dlt.table` (batch) | **Materialized Lake View** (`CREATE MATERIALIZED LAKE VIEW`) | Direct rewrite if the body is SQL |
| `@dlt.view` | **View** (`CREATE VIEW`) | Non-materialised; same as Spark/T-SQL view |
| `@dlt.table` (Python with custom logic) | **Scheduled notebook** with `MERGE INTO` | Manual rewrite required |
| `CREATE OR REFRESH STREAMING TABLE` | **Eventstream → Lakehouse** **OR** **Copy Job CDC** | Use Eventstream for true streaming; Copy Job for incremental batch |
| `cloud_files(...)` (autoLoader) | **Eventstream** with file-arrival source **OR** **Copy Job CDC** with file-arrival trigger | autoLoader's schema-tracking → Copy Job's auto-schema-evolve |
| `@dlt.expect("rule", "predicate")` | **Filter** in MLV body (drop) **OR** **GE checkpoint** (warn/quarantine) | Most direct: encode predicate in MLV WHERE clause |
| `@dlt.expect_or_drop` | Filter in MLV WHERE clause | Direct |
| `@dlt.expect_or_fail` | **GE checkpoint** on upstream table that fails the pipeline | No MLV equivalent for fail-on-violation |
| `@dlt.expect_all_or_drop({...})` | Multiple AND-ed filter predicates in MLV WHERE | Concatenate predicates |
| Apply CHANGES INTO (CDC merge) | **Copy Job CDC** activity **OR** Notebook with `MERGE INTO` | Copy Job is the no-code path; see [Copy Job CDC](../../docs/features/copy-job-cdc.md) |
| DLT pipeline mode = `triggered` | Pipeline schedule | Direct |
| DLT pipeline mode = `continuous` | Eventstream + streaming Notebook (`availableNow=False`) | Re-author |
| DLT `target` (catalog destination) | Lakehouse + schema (`lh_silver.<schema>.<table>`) | Direct |

### autoLoader → Eventstream / Copy Job

```python
# Databricks autoLoader (DLT or notebook):
df = (spark.readStream.format("cloudFiles")
      .option("cloudFiles.format", "json")
      .option("cloudFiles.schemaLocation", "/_schemas/slots/")
      .load("/mnt/raw/slots/"))

# Fabric replacement A — Eventstream (true streaming):
#   Source: ADLS Gen2 file source on /raw/slots/
#   Destination: Lakehouse table lh_bronze.bronze_slot_telemetry
#   Configure schema inference + retention

# Fabric replacement B — Copy Job CDC (incremental batch):
#   Source: ADLS Gen2 folder with file-arrival watermark
#   Destination: Lakehouse table
#   Schedule: every 5/15/60 minutes
```

> 💡 **Tip**: The vast majority of DLT autoLoader pipelines are **batch every N minutes** in disguise — they don't actually need true streaming. A **Copy Job CDC every 5 minutes** is cheaper and simpler than maintaining an always-on Eventstream. Pick the streaming path only when sub-minute latency is a hard requirement.

---

## 🛠️ Migration Tooling

### Bulk Export of Workflow JSON

Databricks REST API (`/api/2.1/jobs/list` and `/api/2.1/jobs/get`) returns the canonical Job definition. The bulk-export script saves every job as a JSON file for batch conversion.

#### PowerShell — `export_databricks_jobs.ps1`

```powershell
param(
    [Parameter(Mandatory)] [string] $DatabricksHost,
    [Parameter(Mandatory)] [string] $DatabricksToken,
    [string] $OutputDir = "./databricks-export/Jobs"
)

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$headers = @{ Authorization = "Bearer $DatabricksToken" }
$page    = $null
$jobs    = @()

do {
    $url = "$DatabricksHost/api/2.1/jobs/list?limit=25"
    if ($page) { $url += "&page_token=$page" }
    $resp = Invoke-RestMethod -Uri $url -Headers $headers
    if ($resp.jobs) { $jobs += $resp.jobs }
    $page = $resp.next_page_token
} while ($page)

foreach ($job in $jobs) {
    $detail = Invoke-RestMethod -Uri "$DatabricksHost/api/2.1/jobs/get?job_id=$($job.job_id)" -Headers $headers
    $safeName = ($detail.settings.name -replace '[^a-zA-Z0-9_-]', '_')
    $detail | ConvertTo-Json -Depth 20 | Set-Content -Path "$OutputDir/$safeName.json"
    Write-Host "Exported: $safeName"
}

Write-Host "Total jobs exported: $($jobs.Count)"
```

#### Python equivalent — `export_databricks_jobs.py`

```python
import argparse, json, os, requests
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", required=True)
    p.add_argument("--token", required=True)
    p.add_argument("--output-dir", default="./databricks-export/Jobs")
    args = p.parse_args()

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    headers = {"Authorization": f"Bearer {args.token}"}
    jobs, page = [], None

    while True:
        url = f"{args.host}/api/2.1/jobs/list?limit=25"
        if page: url += f"&page_token={page}"
        r = requests.get(url, headers=headers).json()
        jobs.extend(r.get("jobs", []))
        page = r.get("next_page_token")
        if not page: break

    for job in jobs:
        d = requests.get(f"{args.host}/api/2.1/jobs/get?job_id={job['job_id']}", headers=headers).json()
        name = "".join(c if c.isalnum() or c in "_-" else "_" for c in d["settings"]["name"])
        Path(args.output_dir, f"{name}.json").write_text(json.dumps(d, indent=2))
        print(f"Exported: {name}")

    print(f"Total: {len(jobs)}")

if __name__ == "__main__":
    main()
```

### Conversion — Scriptable vs Manual

| Aspect | Scriptable | Manual Review |
|--------|-----------|---------------|
| Schedule cron → Fabric schedule | ✅ | — |
| `notebook_task` → Notebook activity | ✅ | Re-point notebook ID |
| `condition_task` (simple If/Else) | ✅ | — |
| `for_each_task` → ForEach | ✅ | — |
| `run_job_task` → Invoke Pipeline | ✅ | — |
| Job parameter → Pipeline parameter | ✅ | — |
| `spark_jar_task` / `spark_python_task` → SJD | ⚠️ partial | Repackage artifact, set entry-point |
| DLT pipeline → MLV | ❌ | Author MLV by hand from DLT SQL |
| Continuous trigger → Eventstream | ❌ | Re-author against Eventstream |
| `dbt_task` → dbt-fabric notebook | ⚠️ partial | Re-point profile; verify adapter coverage |
| Webhook task → Web activity | ✅ | Re-bind auth (Workspace Identity / KV) |
| Job-cluster spec → Environment | ⚠️ partial | Repackage init scripts as `.whl`/`.tar.gz` |
| Custom workflow framework tasks | ❌ | Redesign — don't port the framework |

---

## ⚡ Performance Considerations

| Concern | Databricks | Fabric |
|---------|-----------|--------|
| Cold start for job-cluster | 60-180 sec to provision new cluster | 10-30 sec for Spark session within F-SKU |
| Warm start (cluster pool) | ~30 sec (warm pool) | ~5-10 sec (CU pool already warm) |
| Cost per minute of idle | High (cluster billed even idle) | F-SKU is fixed monthly — idle minutes don't cost extra |
| Cost per active DBU | Variable (tier × DBU) | Smoothed against F-SKU |
| Scale-out latency | 30-90 sec to add workers | 10-30 sec autoscale within session |
| Photon vs NEE | Photon paid surcharge | NEE included; coverage growing |
| Streaming always-on cost | Cluster billed 24×7 | F-SKU absorbs; bound by CU watermark |

> 💡 **Tip**: The fixed-cost F-SKU model means **idle pipelines are free**. In Databricks the temptation was to consolidate jobs onto fewer clusters to save cost; in Fabric, splitting work across more pipelines is fine and improves observability.

---

## 🚫 Anti-Patterns

Don't lift-and-shift these — redesign during migration.

1. **Lift-and-shift "all-purpose cluster" jobs.** All-purpose clusters were cheap for interactive dev, expensive for prod jobs. In Fabric, split: notebooks for dev, Spark Job Definitions for prod batch.
2. **One giant Workflow with 50+ tasks.** Re-architect into smaller Pipelines invoked via **Invoke Pipeline**. Easier to monitor, restart, and version.
3. **Continuous-mode jobs that are really micro-batch.** If the job triggers every minute, it's not streaming — make it a Pipeline schedule or Copy Job CDC at a sane cadence.
4. **DLT pipelines for non-streaming workloads.** Static Bronze→Silver chains belong in MLVs or scheduled notebooks; don't re-create DLT runtime overhead.
5. **`dbutils.jobs.taskValues` for large payloads.** Don't pipe DataFrames through task values; write to a staging Lakehouse table.
6. **Photon-only SQL inside notebooks.** Identify Photon-only functions during assessment and rewrite using portable Spark SQL before migration.
7. **Copying init scripts byte-for-byte.** Init scripts that `apt-get install` system packages don't fit the Environment model. Repackage the *intent* (the libraries you needed) as a `.whl`/`.tar.gz`.
8. **One Variable Library per pipeline.** Use **one shared Variable Library per environment (Dev/Test/Prod)**, not per pipeline. Keeps secrets and connection strings consolidated.
9. **Using Pipeline parameters as feature flags.** If you find yourself toggling logic with a parameter, split into two pipelines or use Deployment Pipeline rules.
10. **Re-creating DLT `expect_or_fail` as Delta `CHECK` constraints.** `CHECK` aborts writes (not what you want); use a **GE checkpoint** that fails the upstream activity.

---

## ✅ Implementation Checklist

Use this as the workflow-migration sub-checklist for Step 5 of [Tutorial 42](./README.md).

- [ ] Bulk-exported all Job JSON via REST API (`export_databricks_jobs.ps1` / `.py`)
- [ ] Categorised every job: Pipeline, SJD, Eventstream, MLV, decommission
- [ ] Identified every `pipeline_task` (DLT) for manual rewrite
- [ ] Identified every `continuous` trigger for Eventstream re-author
- [ ] Mapped every `run_job_task` to Invoke Pipeline activity
- [ ] Mapped every `for_each_task` to ForEach activity
- [ ] Mapped every `condition_task` to If/Switch/Until activity
- [ ] Translated every `new_cluster` spec to a Fabric Environment YAML
- [ ] Repackaged init scripts as custom `.whl`/`.tar.gz`
- [ ] Translated every cron schedule to Fabric Pipeline schedule
- [ ] Translated `dbutils.jobs.taskValues` calls to `mssparkutils.notebook.exit()` + activity outputs
- [ ] Promoted shared parameters (used by ≥3 jobs) to Variable Library
- [ ] Wired retry policy on each activity (was: per-job)
- [ ] Wired storage-event triggers via Logic App (where file-arrival was used)
- [ ] Authored DLT-replacement MLVs and verified row-count parity vs DLT outputs
- [ ] Authored DLT `expect_or_fail` rules as upstream GE checkpoints
- [ ] Verified each converted Pipeline runs end-to-end against test data
- [ ] Disabled (paused) the corresponding Databricks Workflow before Fabric Pipeline goes live
- [ ] Captured pre-migration SLA metrics (duration, cost) and post-migration deltas

---

## 📚 References

### Databricks Documentation
- [Databricks Jobs REST API 2.1](https://docs.databricks.com/api/workspace/jobs)
- [Databricks Workflows overview](https://docs.databricks.com/workflows/index.html)
- [Delta Live Tables — Python and SQL APIs](https://docs.databricks.com/delta-live-tables/python-ref.html)
- [Cluster configuration](https://docs.databricks.com/clusters/configure.html)

### Microsoft Fabric Documentation
- [Fabric Data Pipelines overview](https://learn.microsoft.com/fabric/data-factory/data-factory-overview)
- [Pipeline activities reference](https://learn.microsoft.com/fabric/data-factory/activity-overview)
- [Spark Job Definitions](https://learn.microsoft.com/fabric/data-engineering/create-spark-job-definition)
- [Materialized Lake Views](https://learn.microsoft.com/fabric/data-engineering/materialized-lake-views)
- [Eventstream sources](https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/overview)
- [Copy Job](https://learn.microsoft.com/fabric/data-factory/what-is-copy-job)

### Wave 4 Cross-References
- **[Tutorial 42 — Databricks → Fabric](./README.md)** (parent tutorial — Step 5 anchors here)
- **[Tutorial 41 — Synapse → Fabric](../41-synapse-to-fabric/README.md)** (style anchor; overlapping Pipeline patterns)
- **[Spark Environments & Job Definitions](../../docs/features/spark-environments-job-definitions.md)** (Environment YAML, SJD authoring)
- **[Deployment Pipelines](../../docs/features/deployment-pipelines.md)** (stage promotion + Variable Library)
- **[Pipelines & Data Movement Best Practices](../../docs/best-practices/03_PIPELINES_DATA_MOVEMENT.md)** (ETL/ELT, copy activity tuning)
- **[Materialized Lake Views](../../docs/features/materialized-lake-views.md)** (DLT replacement)
- **[Copy Job CDC](../../docs/features/copy-job-cdc.md)** (autoLoader replacement)
- **[Real-Time Intelligence](../../docs/features/real-time-intelligence.md)** (continuous-trigger replacement)
- **[dbt Fabric Integration](../../docs/features/dbt-fabric-integration.md)** (`dbt_task` migration)
- **[Spark Runtime Migration](../../docs/best-practices/spark-runtime-migration.md)** (DBR → Fabric Spark runtime)
- **[Testing Strategies — Data Contract Suites](../../docs/best-practices/testing-strategies.md)** (GE checkpoints replacing DLT expects)
- **[fabric-cicd Deployment](../../docs/best-practices/fabric-cicd-deployment.md)** (deploying converted Pipelines)
- **[Workspace Monitoring](../../docs/features/workspace-monitoring.md)** (replacement for `cluster_log_conf`)

---

[⬆️ Back to Top](#-tutorial-42--reference-databricks-workflows--fabric-pipelines--spark-job-definitions) | [⬅️ Back to Tutorial 42](./README.md) | [📚 Tutorial Index](../README.md) | [🏠 Home](../../docs/index.md)
