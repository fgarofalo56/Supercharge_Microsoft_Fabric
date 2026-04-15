# Operational Runbooks

> **Home > Documentation > Runbooks**

---

## Overview

This directory contains operational runbooks for the Casino Analytics platform. Each runbook provides step-by-step instructions for common operational tasks and incident response.

---

## Runbook Index

| Category | Runbook | Description |
|----------|---------|-------------|
| **Incidents** | [Data Pipeline Failure](#data-pipeline-failure) | Handle failed data pipelines |
| **Incidents** | [Capacity Alert](#capacity-alert) | Respond to capacity utilization alerts |
| **Incidents** | [Data Quality Alert](#data-quality-alert) | Investigate data quality issues |
| **Incidents** | [Real-Time Ingestion Lag](#real-time-ingestion-lag) | Address Eventstream delays |
| **Maintenance** | [Capacity Pause/Resume](#capacity-pauseresume) | Scheduled capacity management |
| **Maintenance** | [Delta Table Optimization](#delta-table-optimization) | Table maintenance procedures |
| **Deployment** | [Semantic Model Refresh](#semantic-model-refresh) | Refresh Power BI models |
| **Deployment** | [Notebook Deployment](#notebook-deployment) | Deploy notebook changes |

---

## Incident Runbooks

### Data Pipeline Failure

**Severity:** High
**SLA:** Resolve within 4 hours

#### Symptoms
- Pipeline shows "Failed" status in Fabric
- Data not appearing in target tables
- Alerts from monitoring system

#### Diagnostic Steps

1. **Identify Failed Pipeline**
   ```
   Navigate to: Fabric Portal → Workspace → Data Factory → Monitor
   Filter: Status = Failed, Last 24 hours
   ```

2. **Check Error Details**
   - Click on failed pipeline run
   - Expand activity details
   - Copy error message

3. **Common Error Patterns**

   | Error | Likely Cause | Solution |
   |-------|--------------|----------|
   | `SourceNotFound` | Source file missing | Check source system, verify file exists |
   | `InvalidSchema` | Schema mismatch | Compare schemas, enable schema evolution |
   | `QuotaExceeded` | Capacity limits | Scale capacity or optimize query |
   | `AuthenticationFailed` | Credentials expired | Refresh connection credentials |
   | `Timeout` | Long-running query | Optimize query, increase timeout |

4. **Resolution Steps**

   **For Source Errors:**
   ```python
   # Verify source connectivity
   df = spark.read.format("parquet").load("source_path")
   df.printSchema()
   ```

   **For Schema Errors:**
   ```python
   # Enable schema evolution
   spark.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "true")
   ```

   **For Timeout Errors:**
   ```python
   # Increase timeout in pipeline settings
   # Or partition data for smaller batches
   ```

5. **Rerun Pipeline**
   - Click "Rerun" on failed activity
   - Monitor progress
   - Verify data in target table

#### Post-Incident
- [ ] Document root cause
- [ ] Update alerting if needed
- [ ] Create ticket for permanent fix

---

### Capacity Alert

**Severity:** Medium to High
**SLA:** Respond within 30 minutes

#### Symptoms
- CPU utilization > 90%
- Memory utilization > 85%
- Query timeouts
- Slow report loading

#### Diagnostic Steps

1. **Check Capacity Metrics**
   ```
   Navigate to: admin.powerbi.com → Capacity settings → Select capacity
   View: CPU, Memory, Queuing metrics
   ```

2. **Identify Heavy Workloads**
   ```kql
   // In Capacity Metrics app
   FabricCapacityUsage
   | where TimeGenerated > ago(1h)
   | summarize AvgCPU = avg(CPUPercent) by WorkspaceName, ItemName
   | order by AvgCPU desc
   | take 10
   ```

3. **Resolution Options**

   **Option A: Scale Up (Immediate)**
   ```bash
   # Scale from F64 to F128
   az rest --method patch \
     --url "https://management.azure.com/.../capacities/fabric-casino" \
     --body '{"sku": {"name": "F128"}}'
   ```

   **Option B: Kill Heavy Queries**
   ```
   Navigate to: Workspace → Lakehouse → SQL endpoint
   Identify long-running queries and terminate
   ```

   **Option C: Redistribute Workloads**
   - Move non-critical workspaces to different capacity
   - Reschedule batch jobs to off-peak hours

4. **Monitor Recovery**
   - Watch capacity metrics for 15 minutes
   - Verify user experience improved

#### Post-Incident
- [ ] Review query optimization opportunities
- [ ] Consider permanent capacity increase
- [ ] Update scheduling for heavy jobs

---

### Data Quality Alert

**Severity:** Medium
**SLA:** Investigate within 2 hours

#### Symptoms
- Quality score dropped below threshold
- Business users report incorrect data
- Automated quality checks failed

#### Diagnostic Steps

1. **Identify Affected Tables**
   ```python
   # Check quality metrics
   df_quality = spark.sql("""
       SELECT table_name, quality_score, check_timestamp
       FROM quality_metrics
       WHERE quality_score < 0.95
       ORDER BY check_timestamp DESC
   """)
   df_quality.show()
   ```

2. **Investigate Specific Issues**
   ```python
   # Check for nulls
   df = spark.table("silver_slot_telemetry")
   null_counts = df.select([
       sum(col(c).isNull().cast("int")).alias(c)
       for c in df.columns
   ])
   null_counts.show()

   # Check for duplicates
   dup_count = df.groupBy("event_id").count().filter("count > 1").count()
   print(f"Duplicate records: {dup_count}")
   ```

3. **Trace to Source**
   - Check Bronze layer for raw data issues
   - Review recent source system changes
   - Verify transformation logic

4. **Resolution**
   ```python
   # Reprocess affected partitions
   affected_dates = ["2024-01-15", "2024-01-16"]

   for date in affected_dates:
       # Re-run Silver transformation
       mssparkutils.notebook.run("01_silver_slot_cleansing",
                           timeout_seconds=3600,
                           arguments={"process_date": date})
   ```

#### Post-Incident
- [ ] Update data quality rules if needed
- [ ] Notify downstream consumers
- [ ] Document source system issue

---

### Real-Time Ingestion Lag

**Severity:** High (for real-time dashboards)
**SLA:** Resolve within 15 minutes

#### Symptoms
- Real-time dashboard showing stale data
- Eventstream showing backlog
- Alerts for ingestion delay

#### Diagnostic Steps

1. **Check Eventstream Health**
   ```
   Navigate to: Workspace → Real-Time Intelligence → Eventstream
   View: Input/Output metrics, Error count
   ```

2. **Check Eventhouse Ingestion**
   ```kql
   .show ingestion failures
   | where FailedOn > ago(1h)
   | summarize count() by Table, FailureKind
   ```

3. **Common Issues**

   | Issue | Indicator | Solution |
   |-------|-----------|----------|
   | Source backup | High input rate | Check Event Hub |
   | Schema mismatch | Ingestion failures | Update schema |
   | Capacity limit | Throttling | Scale Eventhouse |
   | Network issue | Connection errors | Check connectivity |

4. **Resolution**

   **For Schema Issues:**
   ```kql
   // Update table schema
   .alter table SlotTelemetry
   (EventId: string, MachineId: string, ...)
   ```

   **For Capacity Issues:**
   ```
   Scale Eventhouse: Settings → Scale → Increase CU
   ```

   **For Source Backup:**
   ```bash
   # Check Event Hub metrics
   az eventhubs eventhub show \
     --name slot-telemetry \
     --namespace-name eh-casino \
     --resource-group rg-casino
   ```

#### Post-Incident
- [ ] Verify real-time dashboards updated
- [ ] Check for data gaps
- [ ] Backfill if needed

---

## Maintenance Runbooks

### Capacity Pause/Resume

**Schedule:** Nightly (if applicable)

#### Pause Capacity (Cost Savings)

```powershell
# Pause capacity at 11 PM
$capacityId = "your-capacity-id"

# Check no active jobs
$activeJobs = Get-FabricCapacityActiveJobs -CapacityId $capacityId
if ($activeJobs.Count -eq 0) {
    Suspend-FabricCapacity -CapacityId $capacityId
    Write-Host "Capacity paused successfully"
} else {
    Write-Warning "Active jobs found, skipping pause"
}
```

#### Resume Capacity

```powershell
# Resume capacity at 6 AM
$capacityId = "your-capacity-id"

Resume-FabricCapacity -CapacityId $capacityId

# Wait for capacity to be ready
Start-Sleep -Seconds 60

# Verify capacity is running
$status = Get-FabricCapacityStatus -CapacityId $capacityId
Write-Host "Capacity status: $($status.State)"
```

---

### Delta Table Optimization

**Schedule:** Weekly (Sunday 2 AM)

```python
# Delta table maintenance notebook

tables_to_optimize = [
    "bronze_slot_telemetry",
    "silver_slot_telemetry",
    "gold.fact_daily_slot_performance"
]

for table in tables_to_optimize:
    print(f"Optimizing {table}...")

    # Compact small files
    spark.sql(f"OPTIMIZE {table}")

    # Remove old versions (beyond retention)
    spark.sql(f"VACUUM {table} RETAIN 168 HOURS")  # 7 days

    # Analyze table statistics
    spark.sql(f"ANALYZE TABLE {table} COMPUTE STATISTICS")

    print(f"Completed {table}")
```

---

### Semantic Model Refresh

**Schedule:** Daily or on-demand

1. **Manual Refresh**
   ```
   Navigate to: Workspace → Semantic Model → Refresh now
   ```

2. **Scripted Refresh**
   ```powershell
   # Refresh via REST API
   $workspaceId = "workspace-guid"
   $datasetId = "dataset-guid"

   Invoke-PowerBIRestMethod -Method Post `
     -Url "groups/$workspaceId/datasets/$datasetId/refreshes"
   ```

3. **Verify Refresh**
   ```powershell
   # Check refresh history
   $refreshes = Invoke-PowerBIRestMethod -Method Get `
     -Url "groups/$workspaceId/datasets/$datasetId/refreshes"

   $refreshes.value | Select-Object -First 5 |
     Format-Table status, startTime, endTime
   ```

---

### Notebook Deployment

**Process:** Deploy notebook changes from development to production

1. **Export from Development**
   ```
   Navigate to: Dev Workspace → Notebook → Download .ipynb
   ```

2. **Review Changes**
   - Compare with existing production notebook
   - Validate all parameters
   - Check for hardcoded values

3. **Import to Production**
   ```
   Navigate to: Prod Workspace → Import → Upload .ipynb
   ```

4. **Test Execution**
   - Run with limited data
   - Verify output correctness
   - Check performance

5. **Update Pipeline References**
   - If notebook is in pipeline, verify activity references
   - Test pipeline end-to-end

---

## Escalation Matrix

| Severity | Response Time | Escalation After | Contact |
|----------|---------------|------------------|---------|
| Critical | 15 min | 30 min | VP Engineering |
| High | 30 min | 2 hours | Platform Lead |
| Medium | 2 hours | 8 hours | Team Lead |
| Low | 24 hours | 48 hours | Ticket queue |

---

## Quick Reference

### Useful Commands

```bash
# Check capacity status
az rest --method get --url "https://api.fabric.microsoft.com/v1/capacities/{id}"

# List workspace items
az rest --method get --url "https://api.fabric.microsoft.com/v1/workspaces/{id}/items"

# Get pipeline runs
az rest --method get --url "https://api.fabric.microsoft.com/v1/workspaces/{id}/pipelines/{pipelineId}/runs"
```

### Key URLs

| Resource | URL |
|----------|-----|
| Fabric Portal | https://app.fabric.microsoft.com |
| Power BI Admin | https://admin.powerbi.com |
| Azure Portal | https://portal.azure.com |
| Status Page | https://status.fabric.microsoft.com |

---

[Back to Documentation](../index.md)
