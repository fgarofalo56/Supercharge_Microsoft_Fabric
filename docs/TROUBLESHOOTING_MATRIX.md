---
hero: assets/heroes/runbooks.svg
hero_alt: Troubleshooting Matrix — Common issues + resolution paths
type: runbook
---
# Troubleshooting Matrix

> **Last Updated**: 2026-04-27 | **Version**: 1.0
> **Status**: Active | **Maintainer**: Engineering Team

A symptom-indexed troubleshooting guide for Microsoft Fabric. Find your symptom, confirm the root cause with diagnostic steps, apply the resolution, and prevent recurrence.

---

## Performance Issues

### Symptom: Spark SQL queries run slowly on large Delta tables

**Likely Cause:** Missing predicate pushdown -- filters are applied after a full table scan instead of being pushed to the file-skipping layer.

**Diagnostic Steps:**
1. Check the Spark UI physical plan: `df.explain(True)` -- look for `PushedFilters` in the scan node.
2. Verify the filter column is used for Z-ordering or partitioning: `DESCRIBE DETAIL table_name`.
3. Check file sizes: `mssparkutils.fs.ls("Tables/table_name/")` -- many small files (< 32 MB) indicate compaction needed.

**Resolution:**
```python
# Optimize with Z-order on frequently filtered columns
spark.sql("OPTIMIZE table_name ZORDER BY (event_date, property_id)")

# Enable V-Order for Direct Lake compatibility
spark.sql("OPTIMIZE table_name USING VORDER")
```

**Prevention:** Include `OPTIMIZE` with ZORDER/VORDER in Gold notebook epilogues. Partition large tables by date.

---

### Symptom: Queries ignore partition pruning -- scanning all partitions

**Likely Cause:** Filter expression uses a transformation on the partition column (e.g., `YEAR(event_date) = 2025` instead of `event_date >= '2025-01-01'`).

**Diagnostic Steps:**
1. Run `df.explain(True)` and check `PartitionFilters` vs `DataFilters`.
2. If `PartitionFilters` is empty, the partition column filter is not being pushed down.

**Resolution:**
```python
# Bad -- prevents partition pruning
df.filter("YEAR(event_date) = 2025")

# Good -- enables partition pruning
df.filter("event_date >= '2025-01-01' AND event_date < '2026-01-01'")
```

**Prevention:** Always filter partition columns with direct comparisons, never wrapped in functions.

---

### Symptom: Broadcast join timeout or OOM on large join

**Likely Cause:** Spark auto-broadcast threshold (default 10 MB) is too high for the available driver memory, or a "small" table grew beyond expectations.

**Diagnostic Steps:**
1. Check broadcast threshold: `spark.conf.get("spark.sql.autoBroadcastJoinThreshold")`.
2. Check dimension table size: `df.count()` and `spark.catalog.currentDatabase()`.
3. Look at Spark UI Stages tab for `BroadcastHashJoin` stages with long GC pauses.

**Resolution:**
```python
# Disable auto-broadcast for this query
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)

# Or explicitly control join strategy
from pyspark.sql.functions import broadcast
result = large_df.join(broadcast(small_df), "key")
```

**Prevention:** Set explicit broadcast thresholds per notebook based on known dimension sizes. For POC-scale data, `10485760` (10 MB) is usually safe.

---

### Symptom: V-Order optimization not improving Direct Lake performance

**Likely Cause:** Table was written without V-Order, or OPTIMIZE was run without the VORDER clause.

**Diagnostic Steps:**
1. Check table properties: `DESCRIBE DETAIL gold_table_name` -- look for `writerVersion`.
2. In Power BI, open Performance Analyzer: check if queries show "DirectQuery fallback."
3. Verify column cardinality is not excessively high (>10M unique values per column).

**Resolution:**
```sql
-- Re-optimize with V-Order
OPTIMIZE gold_slot_performance USING VORDER;

-- For new writes, enable V-Order in writer
spark.conf.set("spark.sql.parquet.vorder.enabled", "true")
```

**Prevention:** Set `spark.sql.parquet.vorder.enabled=true` in all Gold notebooks before writing Delta tables.

---

## Capacity and Throttling

### Symptom: Jobs queue indefinitely or fail with "insufficient capacity"

**Likely Cause:** Fabric capacity CU utilization exceeds 100%, triggering throttling. Smoothed utilization over 10 minutes determines throttling severity.

**Diagnostic Steps:**
1. Open Fabric Admin Portal > Capacity settings > Metrics app.
2. Check "CU Utilization %" over the last hour -- sustained >90% triggers throttling.
3. Identify top CU consumers: Metrics app > Top operations by CU.

**Resolution:**
1. **Immediate:** Pause non-critical workloads (dev notebooks, non-urgent pipelines).
2. **Short-term:** Scale up capacity temporarily (F64 to F128) via Azure Portal or Bicep.
3. **Long-term:** Spread workloads across multiple capacities or optimize expensive queries.

```bash
# Scale up via CLI
az fabric capacity update --name "fabric-casino-poc" --sku F128
```

**Prevention:** Configure capacity utilization alerts at 70% and 90% thresholds via `alerts-and-budgets.bicep`. Stagger pipeline schedules to avoid concurrent peaks.

---

### Symptom: Interactive queries slow during scheduled pipeline runs

**Likely Cause:** Background pipeline jobs consume shared CU, leaving insufficient capacity for interactive queries. Fabric uses a single CU pool for all workload types.

**Diagnostic Steps:**
1. Check pipeline run times vs. query slowdown times in Metrics app.
2. Look at concurrent Spark sessions in Workspace Monitoring.

**Resolution:**
1. Schedule heavy pipelines during off-hours (2 AM - 6 AM).
2. Use pipeline concurrency limits to cap parallel notebook activities.
3. Consider separate capacities for interactive (BI) and batch (ETL) workloads.

**Prevention:** Document and enforce pipeline scheduling windows. Use Workspace Monitoring to track CU consumption patterns.

---

## Authentication and Access

### Symptom: Notebook fails with "Forbidden" or "401 Unauthorized" accessing Azure Storage

**Likely Cause:** Service principal or managed identity lacks RBAC role on the storage account, or the token has expired.

**Diagnostic Steps:**
1. Check identity: `mssparkutils.credentials.getToken("storage")` -- if this fails, the identity is not configured.
2. Verify RBAC: Azure Portal > Storage account > Access control > Role assignments.
3. Check if Workspace Identity is enabled: Fabric workspace settings > Identity.

**Resolution:**
```bash
# Assign Storage Blob Data Contributor to the workspace identity
az role assignment create \
  --assignee "<workspace-identity-object-id>" \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<account>"
```

**Prevention:** Use Workspace Identity (deployed via `workspace-identity.bicep`) for credential-free auth. Avoid service principal secrets that expire.

---

### Symptom: Conditional Access policy blocks Fabric service principal

**Likely Cause:** Entra ID Conditional Access policy requires MFA or compliant device, which a service principal cannot satisfy.

**Diagnostic Steps:**
1. Check Entra ID Sign-in logs for the service principal -- look for "Conditional Access failure."
2. Review CA policies: Entra ID > Security > Conditional Access > Policies.

**Resolution:**
1. Exclude the Fabric service principal from the blocking CA policy.
2. Or create a CA policy exception for the "Microsoft Fabric" cloud app.
3. Use Workspace Identity (managed identity) instead of service principal -- MI is typically exempt from CA.

**Prevention:** When planning CA policies, explicitly exclude service principals used for Fabric automation. Document exclusions.

---

### Symptom: Workspace Identity cannot access Key Vault secrets

**Likely Cause:** Key Vault access policy or RBAC does not include the workspace managed identity.

**Diagnostic Steps:**
1. Identify the MI object ID: Fabric workspace settings > Identity > Object ID.
2. Check Key Vault access: Azure Portal > Key Vault > Access policies (or RBAC).
3. Test: `mssparkutils.credentials.getSecret("vault-name", "secret-name")`.

**Resolution:**
```bash
# If using RBAC model
az role assignment create \
  --assignee "<mi-object-id>" \
  --role "Key Vault Secrets User" \
  --scope "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/<vault>"

# If using access policy model
az keyvault set-policy --name "<vault>" --object-id "<mi-object-id>" --secret-permissions get list
```

**Prevention:** The `workspace-identity.bicep` module includes optional `enableKeyVaultAccess` parameter that auto-assigns the role.

---

## Ingestion and Streaming

### Symptom: Eventstream shows increasing consumer lag / backpressure

**Likely Cause:** Downstream processing (Lakehouse write or Eventhouse ingestion) is slower than the event production rate.

**Diagnostic Steps:**
1. Check Eventstream metrics: Consumer group lag (offset difference).
2. Check Eventhouse ingestion metrics: Pending ingestion count, batch duration.
3. Check if Spark Structured Streaming checkpoints are corrupted: `mssparkutils.fs.ls("checkpoint_path/")`.

**Resolution:**
1. **Scale consumer:** Increase Eventstream consumer group partition count.
2. **Optimize writes:** Batch Lakehouse writes with larger trigger intervals.
3. **Eventhouse:** Increase ingestion batch size or enable streaming ingestion.

```python
# Increase micro-batch interval to reduce write pressure
df.writeStream \
  .trigger(processingTime="30 seconds") \
  .format("delta") \
  .start("Tables/bronze_slot_telemetry")
```

**Prevention:** Size Eventstream partitions to match expected peak throughput. Monitor consumer lag with alerts.

---

### Symptom: Streaming notebook checkpoint corruption after restart

**Likely Cause:** Checkpoint directory contains partial metadata from an unclean shutdown, or the checkpoint was written to `/tmp` (ephemeral) instead of OneLake.

**Diagnostic Steps:**
1. Check checkpoint location: `mssparkutils.fs.ls("checkpoint_path/")`.
2. Look for `metadata` and `offsets` directories.
3. If checkpoint is in `/tmp` or `dbfs:/tmp`, it was lost on session restart.

**Resolution:**
```python
# Reset checkpoint by deleting and restarting from earliest
mssparkutils.fs.rm("Tables/.checkpoints/slot_streaming", True)

# Use OneLake path for durable checkpoints (not /tmp)
checkpoint_path = "abfss://workspace@onelake.dfs.fabric.microsoft.com/lakehouse/Tables/.checkpoints/slot_streaming"
```

**Prevention:** All POC notebooks use OneLake checkpoint paths (Phase 11 remediation). Never use `/tmp` for streaming checkpoints.

---

### Symptom: Schema drift causes ingestion failures or silent null columns

**Likely Cause:** Source system added/renamed columns. Delta Lake's default mode rejects schema changes.

**Diagnostic Steps:**
1. Compare source schema with Delta table schema: `spark.read.parquet("source").schema` vs `spark.table("target").schema`.
2. Check for null columns that should have data.

**Resolution:**
```python
# Allow schema evolution on write
df.write.format("delta") \
  .option("mergeSchema", "true") \
  .mode("append") \
  .saveAsTable("bronze_slot_telemetry")
```

**Prevention:** Use `mergeSchema` in Bronze notebooks (schema-on-read). Enforce strict schemas in Silver notebooks for data quality.

---

## Refresh Failures

### Symptom: Direct Lake semantic model falls back to DirectQuery mode

**Likely Cause:** Delta table exceeds Direct Lake guardrails (row count, column count, or table count per model), or table contains unsupported data types.

**Diagnostic Steps:**
1. Check model properties in Power BI: Settings > Semantic model > Direct Lake behavior.
2. Query the model DMV: `SELECT * FROM $SYSTEM.DISCOVER_STORAGE_TABLE_COLUMNS` for column stats.
3. Check for calculated tables (not supported in Direct Lake).

**Resolution:**
1. Reduce table cardinality by pre-aggregating in Gold notebooks.
2. Remove calculated tables -- move logic to Gold layer.
3. Split large models into multiple semantic models.

**Prevention:** Design Gold tables to stay within Direct Lake guardrails. See [Direct Lake](features/direct-lake.md) for current limits.

---

### Symptom: Incremental refresh fails with "token expired" error

**Likely Cause:** OAuth token used for incremental refresh expired during a long-running refresh operation (>1 hour).

**Diagnostic Steps:**
1. Check refresh history in Fabric workspace: Semantic model > Refresh history.
2. Look for error message containing "AADSTS700082" or "token expired."

**Resolution:**
1. Use Workspace Identity for authentication (no token expiry).
2. Reduce incremental refresh partition size to shorten individual refresh time.
3. If using service principal, extend token lifetime in Entra ID app registration.

**Prevention:** Migrate from SP-based auth to Workspace Identity. Configure incremental refresh with smaller partitions.

---

## Pipeline Failures

### Symptom: Pipeline times out waiting for notebook activity

**Likely Cause:** Spark session startup is slow (cold start), or the notebook itself takes longer than the activity timeout.

**Diagnostic Steps:**
1. Check pipeline run details: Activity runs > Duration vs. Timeout setting.
2. Check Spark session startup time in Monitoring Hub.
3. Verify the notebook runs successfully when executed standalone.

**Resolution:**
1. Increase activity timeout (default 12 hours, increase if needed).
2. Enable Spark session reuse across notebook activities in the same pipeline.
3. Optimize notebook to reduce runtime (filter early, select fewer columns).

```json
{
  "type": "SparkNotebook",
  "timeout": "02:00:00",
  "retryPolicy": {
    "count": 2,
    "intervalInSeconds": 60
  }
}
```

**Prevention:** Set realistic timeouts per activity. Monitor pipeline durations weekly for drift.

---

### Symptom: Pipeline fails after credential rotation

**Likely Cause:** Pipeline connection or linked service references an expired secret or rotated key.

**Diagnostic Steps:**
1. Check pipeline error: "InvalidConnectionCredential" or "SecretNotFound."
2. Verify Key Vault secret version: `az keyvault secret show --name "secret-name" --vault-name "vault"`.
3. Check if connection uses a specific secret version (pinned) vs. latest.

**Resolution:**
1. Update the connection in Fabric to use the new credential.
2. If using Key Vault references, ensure connection uses "latest" version, not a pinned version URI.
3. Re-authenticate data source connections in Fabric workspace settings.

**Prevention:** Use Workspace Identity (no credentials to rotate). If using Key Vault, always reference the latest secret version.

---

## Notebook Failures

### Symptom: "OutOfMemoryError: Java heap space" in notebook

**Likely Cause:** Driver OOM from `collect()`, `toPandas()`, or `display()` on a large DataFrame, or too many cached DataFrames.

**Diagnostic Steps:**
1. Check Spark UI > Executors > Memory usage.
2. Search notebook for `collect()`, `toPandas()`, or `display()` calls on unfiltered DataFrames.
3. Check cached DataFrames: `spark.catalog.clearCache()`.

**Resolution:**
```python
# Bad: pulls entire table to driver
pdf = spark.table("bronze_slot_telemetry").toPandas()

# Good: filter and limit first
pdf = spark.table("bronze_slot_telemetry") \
    .filter("event_date = '2025-01-01'") \
    .limit(100000) \
    .toPandas()

# Clear cache if needed
spark.catalog.clearCache()
```

**Prevention:** Never call `collect()` or `toPandas()` without filtering and limiting first. Use `display(df.limit(1000))` for preview.

---

### Symptom: Library version conflict between notebooks

**Likely Cause:** One notebook installs a package with `%pip install` that conflicts with another notebook's dependency in the same Spark session.

**Diagnostic Steps:**
1. Check installed packages: `%pip list`.
2. Look for version mismatch errors in the stack trace.
3. Check if session pooling is sharing sessions across notebooks.

**Resolution:**
1. Use Spark Environments to manage consistent library versions workspace-wide.
2. Pin specific versions in `%pip install`: `%pip install pandas==2.1.0`.
3. Restart session between conflicting notebooks: `mssparkutils.session.stop()`.

**Prevention:** Define library dependencies in a Spark Environment rather than inline `%pip install`. See [Spark Environments](features/spark-environments-job-definitions.md).

---

### Symptom: `mssparkutils` command fails with "module not found"

**Likely Cause:** Running outside of Fabric (local development, pytest) where `mssparkutils` is not available.

**Diagnostic Steps:**
1. Check execution environment: `import mssparkutils` -- if `ModuleNotFoundError`, you are outside Fabric.
2. Check if the `_get_arg` helper shim is present at the top of the notebook.

**Resolution:**
```python
# Use the POC's standard shim pattern (present in all notebooks since Phase 11)
try:
    from notebookutils import mssparkutils
except ImportError:
    mssparkutils = None

def _get_arg(name, default=None):
    try:
        return mssparkutils.notebook.getArgument(name)
    except Exception:
        return default
```

**Prevention:** All POC notebooks include the `_get_arg` shim. For new notebooks, copy the pattern from `notebooks/utils/bronze_utils.py`.

---

## Data Quality Issues

### Symptom: Duplicate records in Silver/Gold tables after re-run

**Likely Cause:** Notebook uses `append` mode without deduplication, and the same batch was processed twice.

**Diagnostic Steps:**
1. Count duplicates: `df.groupBy("primary_key").count().filter("count > 1").count()`.
2. Check if notebook uses `mode("append")` without `MERGE`.
3. Check pipeline retry history for duplicate runs.

**Resolution:**
```python
# Use MERGE (upsert) instead of append for idempotent writes
from delta.tables import DeltaTable

target = DeltaTable.forName(spark, "silver_slot_cleansed")
target.alias("t").merge(
    source_df.alias("s"),
    "t.event_id = s.event_id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
```

**Prevention:** Use MERGE/upsert in Silver and Gold notebooks. Design Bronze as append-only with deduplication deferred to Silver.

---

### Symptom: Null values proliferating through the medallion pipeline

**Likely Cause:** Source data has unexpected nulls, and schema enforcement in Silver is not catching them.

**Diagnostic Steps:**
1. Profile nulls: `df.select([count(when(col(c).isNull(), c)).alias(c) for c in df.columns]).show()`.
2. Check Bronze notebook for null handling.
3. Check Silver notebook for NOT NULL constraints.

**Resolution:**
```python
# Add null checks in Silver layer
from pyspark.sql.functions import col, when, lit

df = df.withColumn("amount",
    when(col("amount").isNull(), lit(0.0)).otherwise(col("amount"))
)

# Enforce NOT NULL via Delta constraints
spark.sql("ALTER TABLE silver_financial ADD CONSTRAINT amount_not_null CHECK (amount IS NOT NULL)")
```

**Prevention:** Add Great Expectations data quality checks between layers. See `validation/` for existing suites.

---

## Deployment Failures

### Symptom: `fabric-cicd` deployment fails with "item not found"

**Likely Cause:** The fabric-cicd tool cannot find the Fabric item (notebook, pipeline) in the target workspace, or the workspace ID is incorrect.

**Diagnostic Steps:**
1. Verify workspace ID: Fabric Portal > Workspace settings > Workspace ID.
2. Check fabric-cicd config file for correct workspace mapping.
3. Verify service principal has Contributor role on the workspace.

**Resolution:**
1. Update workspace ID in `fabric-cicd` configuration.
2. Ensure all referenced items exist in the target workspace.
3. Run with `--verbose` flag for detailed error output.

**Prevention:** Validate workspace IDs in CI/CD pipeline configuration. Use `fabric-cicd` dry-run mode before actual deployment.

See: [fabric-cicd Deployment](best-practices/fabric-cicd-deployment.md)

---

### Symptom: Git sync fails with merge conflicts

**Likely Cause:** Both Fabric UI edits and Git-side edits modified the same item, creating a conflict that auto-merge cannot resolve.

**Diagnostic Steps:**
1. Check Git sync status in Fabric workspace: Source control > Status.
2. Look for "Conflict" status on specific items.
3. Check the Git branch for recent commits that touch the same files.

**Resolution:**
1. Export the Fabric workspace version of conflicting items.
2. Resolve conflicts in Git (prefer the version with intended changes).
3. Re-sync from Git to workspace.

**Prevention:** Establish a one-way flow: edit in Git (VS Code/IDE), sync to Fabric. Avoid editing items directly in Fabric UI when Git integration is enabled.

See: [Git Integration](features/git-integration.md) | [CI/CD Best Practices](best-practices/fabric-cicd-deployment.md)

---

### Symptom: Bicep deployment fails with "ResourceProviderNotRegistered"

**Likely Cause:** The Azure subscription does not have the required resource provider registered.

**Diagnostic Steps:**
```bash
az provider show --namespace Microsoft.Fabric --query "registrationState"
az provider show --namespace Microsoft.Purview --query "registrationState"
```

**Resolution:**
```bash
az provider register --namespace Microsoft.Fabric
az provider register --namespace Microsoft.Purview
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.KeyVault
# Wait 5-10 minutes for registration to complete
```

**Prevention:** Include resource provider registration as the first step in CI/CD pipelines. The `deploy-fabric.yml` workflow handles this automatically.

---

## Cost Surprises

### Symptom: Unexpected CU spike during off-hours

**Likely Cause:** A scheduled pipeline or streaming notebook continued running outside business hours, or a long-running Spark session was left open.

**Diagnostic Steps:**
1. Check Metrics app: CU utilization timeline -- identify the spike window.
2. Check Monitoring Hub: Active Spark sessions and pipeline runs during the spike.
3. Check streaming notebooks: `01_realtime_slot_streaming.py` runs continuously by design.

**Resolution:**
1. Cancel orphaned Spark sessions in Monitoring Hub.
2. Add timeout to pipeline activities.
3. Schedule capacity pause/resume for non-production environments.

```bash
# Pause capacity during off-hours
az fabric capacity pause --name "fabric-casino-poc-dev"
```

**Prevention:** Use `alerts-and-budgets.bicep` to set CU alerts at 70% and 90%. Implement automated capacity pause/resume schedules for dev/test.

---

### Symptom: OneLake storage costs growing faster than expected

**Likely Cause:** Delta Lake time travel retains old file versions indefinitely unless VACUUM is run. Each overwrite doubles storage until old files are cleaned.

**Diagnostic Steps:**
1. Check table storage: `DESCRIBE DETAIL table_name` -- compare `sizeInBytes` vs. expected.
2. Check file count: `mssparkutils.fs.ls("Tables/table_name/")` -- many `part-*.parquet` files indicate accumulated versions.
3. Check VACUUM history: `DESCRIBE HISTORY table_name`.

**Resolution:**
```python
# Vacuum old files (retain 7 days of time travel)
spark.sql("VACUUM table_name RETAIN 168 HOURS")

# For all tables
for table in spark.catalog.listTables():
    spark.sql(f"VACUUM {table.name} RETAIN 168 HOURS")
```

**Prevention:** Schedule weekly VACUUM jobs for all tables. Set `delta.deletedFileRetentionDuration` to match your recovery SLA.

---

### Symptom: Cross-region data egress charges appearing

**Likely Cause:** Fabric capacity is in a different region than the source data (ADLS, Azure SQL), causing cross-region reads.

**Diagnostic Steps:**
1. Check Fabric capacity region: Azure Portal > Fabric capacity > Location.
2. Check source data region: Storage account / Azure SQL > Location.
3. Compare -- if different, cross-region egress is expected.

**Resolution:**
1. Move Fabric capacity to the same region as the data source.
2. Or copy data to a storage account in the same region as the capacity.

**Prevention:** Deploy all resources in the same Azure region. The POC uses `eastus2` for all resources via `infra/main.bicep`.

---

## Quick Lookup Index

| Symptom Keyword | Section |
|---|---|
| Slow query, scan | [Predicate Pushdown](#symptom-spark-sql-queries-run-slowly-on-large-delta-tables) |
| Partition | [Partition Pruning](#symptom-queries-ignore-partition-pruning----scanning-all-partitions) |
| Broadcast, OOM join | [Broadcast Join](#symptom-broadcast-join-timeout-or-oom-on-large-join) |
| V-Order, Direct Lake slow | [V-Order](#symptom-v-order-optimization-not-improving-direct-lake-performance) |
| Throttling, queue | [CU Throttling](#symptom-jobs-queue-indefinitely-or-fail-with-insufficient-capacity) |
| 401, Forbidden, auth | [Auth Failures](#symptom-notebook-fails-with-forbidden-or-401-unauthorized-accessing-azure-storage) |
| Conditional Access | [CA Policy](#symptom-conditional-access-policy-blocks-fabric-service-principal) |
| Key Vault, secrets | [Key Vault Access](#symptom-workspace-identity-cannot-access-key-vault-secrets) |
| Lag, backpressure | [Eventstream Lag](#symptom-eventstream-shows-increasing-consumer-lag--backpressure) |
| Checkpoint | [Checkpoint Corruption](#symptom-streaming-notebook-checkpoint-corruption-after-restart) |
| Schema drift | [Schema Drift](#symptom-schema-drift-causes-ingestion-failures-or-silent-null-columns) |
| Fallback, DirectQuery | [Direct Lake Fallback](#symptom-direct-lake-semantic-model-falls-back-to-directquery-mode) |
| Token expired | [Incremental Refresh](#symptom-incremental-refresh-fails-with-token-expired-error) |
| Timeout, pipeline | [Pipeline Timeout](#symptom-pipeline-times-out-waiting-for-notebook-activity) |
| Credential rotation | [Credential Rotation](#symptom-pipeline-fails-after-credential-rotation) |
| Heap, memory | [OOM](#symptom-outofmemoryerror-java-heap-space-in-notebook) |
| Library conflict | [Library Conflict](#symptom-library-version-conflict-between-notebooks) |
| mssparkutils | [mssparkutils Missing](#symptom-mssparkutils-command-fails-with-module-not-found) |
| Duplicates | [Duplicate Records](#symptom-duplicate-records-in-silvergold-tables-after-re-run) |
| Nulls | [Null Proliferation](#symptom-null-values-proliferating-through-the-medallion-pipeline) |
| fabric-cicd | [Deployment](#symptom-fabric-cicd-deployment-fails-with-item-not-found) |
| Git conflict | [Git Sync](#symptom-git-sync-fails-with-merge-conflicts) |
| ResourceProvider | [Bicep Deploy](#symptom-bicep-deployment-fails-with-resourceprovidernotregistered) |
| CU spike | [Cost Spike](#symptom-unexpected-cu-spike-during-off-hours) |
| Storage growth | [Storage Costs](#symptom-onelake-storage-costs-growing-faster-than-expected) |
| Egress, cross-region | [Egress Charges](#symptom-cross-region-data-egress-charges-appearing) |

---

[Back to Docs](index.md) | [FAQ](FAQ.md) | [Decision Trees](DECISION_TREES.md)
