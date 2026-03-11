# 📓 Fabric Notebooks

> **[Home](../README.md)** | **[Data Generation](../data-generation/)** | **[Validation](../validation/)** | **[Tutorials](../tutorials/)**

Production-ready notebooks designed for Microsoft Fabric, implementing the medallion architecture for casino/gaming, federal agency, and streaming data.

---

## Overview

```
+------------------+     +------------------+     +------------------+
|   BRONZE LAYER   |     |   SILVER LAYER   |     |    GOLD LAYER    |
+------------------+     +------------------+     +------------------+
| 01_slot_telemetry| --> | 01_slot_cleansed | --> | 01_slot_perf     |
| 02_player_profile| --> | 02_player_master | --> | 02_player_360    |
| 03_financial_txn | --> | 03_table_enriched| --> | 03_compliance    |
| 04_compliance    | --> | 04_financial_rec | --> | 04_table_analytics|
| 05_table_games   | --> | 05_security_enr  | --> | 05_financial_sum |
| 06_security_events| --> | 06_compliance_val| --> | 06_security_dash |
| 07_tribal_health | --> | 07_tribal_health | --> | 07_tribal_360    |
| 08_dot_faa       | --> | 08_dot_faa       | --> | 08_dot_faa_anlyt |
+------------------+     +------------------+     +------------------+
        |                                                 |
        |        +---------------------------------------+
        |        |
+-------v--------v-+                          +----------------+
|   STREAMING (8)  |                          |   MACHINE      |
+------------------+                          |   LEARNING     |
| 01_sql_server_cdc|                          +----------------+
| 02_azure_sql     |                          | Churn Model    |
| 03_cosmos_db     |                          | Fraud Detection|
| 04_ibm_db2_cdc   |                          +----------------+
| 05_oracle_cdc    |
| 06_kafka         |
| 07_iot_hub       |
| 08_slot_iot      |
+------------------+
```

---

## Notebook Inventory

### Bronze Layer Notebooks

Raw data ingestion from landing zone to Bronze tables.

| # | Notebook | Description | Source | Output Table |
|---|----------|-------------|--------|--------------|
| 01 | `bronze_slot_telemetry.py` | Slot machine events ingestion | Parquet | `bronze_slot_telemetry` |
| 02 | `bronze_player_profile.py` | Player demographics with SSN hashing | Parquet | `bronze_player_profile` |
| 03 | `bronze_financial_txn.py` | Cage transactions with CTR flagging | Parquet | `bronze_financial_txn` |
| 04 | `bronze_compliance.py` | Regulatory filings (CTR, SAR, W2G) | Parquet | `bronze_compliance` |
| 05 | `bronze_table_games.py` | Table game transactions | Parquet | `bronze_table_games` |
| 06 | `bronze_security_events.py` | Security/surveillance logs | Parquet | `bronze_security_events` |
| 07 | `07_bronze_tribal_health.py` | IHS tribal health encounters with HIPAA audit | Parquet | `bronze_tribal_health_encounters` |
| 08 | `08_bronze_dot_faa.py` | DOT/FAA multi-domain ingestion (flights, safety, traffic) | Parquet | `bronze_dot_flight_ops` |

### Silver Layer Notebooks

Data cleansing, validation, and enrichment.

| # | Notebook | Description | Key Transformations |
|---|----------|-------------|---------------------|
| 01 | `silver_slot_cleansed.py` | Cleansed slot data | Deduplication, DQ scoring |
| 02 | `silver_player_master.py` | Player master with SCD Type 2 | Slowly changing dimensions |
| 03 | `silver_table_enriched.py` | Enriched table games | Session aggregations, patterns |
| 04 | `silver_financial_reconciled.py` | Reconciled transactions | CTR validation, structuring detection |
| 05 | `silver_security_enriched.py` | Enriched security events | Threat scoring, correlation |
| 06 | `silver_compliance_validated.py` | Validated compliance filings | Threshold validation, deadlines |
| 07 | `07_silver_tribal_health.py` | PHI masking, FHIR R4 mapping, ICD-10 validation | HIPAA compliance, deduplication |
| 08 | `08_silver_dot_faa.py` | IATA validation, delay categorization, carrier standardization | Data quality, cross-source correlation |

### Gold Layer Notebooks

Business-ready aggregations and KPIs.

| # | Notebook | Description | Key Metrics |
|---|----------|-------------|-------------|
| 01 | `gold_slot_performance.py` | Slot machine KPIs | Coin-in, Theo, Hold%, variance |
| 02 | `gold_player_360.py` | Player 360 view | LTV, churn risk, tier |
| 03 | `gold_compliance_reporting.py` | Compliance reports | CTR, SAR, W2G counts |
| 04 | `gold_table_analytics.py` | Table games analytics | Drop, Win, Hold% |
| 05 | `gold_financial_summary.py` | Financial summary | Daily P&L, cash flow |
| 06 | `gold_security_dashboard.py` | Security dashboard | Incidents, threats, response |
| 07 | `07_gold_tribal_health_360.py` | Patient 360, population health KPIs | Encounters/year, ED utilization, diabetes prevalence |
| 08 | `08_gold_dot_faa_analytics.py` | Carrier performance, safety analytics | On-time rate, incident trends, airport metrics |

### Real-Time Notebooks

Streaming and real-time analytics.

| Notebook | Description | Technology |
|----------|-------------|------------|
| `realtime_slot_streaming.py` | Eventstream to Lakehouse streaming | Spark Structured Streaming |
| `kql_casino_floor.kql` | KQL queries for Eventhouse monitoring | KQL |

### 🔄 Streaming Notebooks

CDC and IoT streaming connectors for real-time data ingestion.

| # | Notebook | Description | Source | Connector |
|:--|:---------|:------------|:-------|:----------|
| 01 | `01_sql_server_cdc.py` | SQL Server CDC via Debezium | SQL Server | Eventstreams |
| 02 | `02_azure_sql_change_feed.py` | Azure SQL Change Tracking v2 | Azure SQL | Native Change Feed |
| 03 | `03_cosmos_db_change_feed.py` | Cosmos DB change feed processing | Cosmos DB | Change Feed Processor |
| 04 | `04_ibm_db2_cdc.py` | IBM DB2 CDC with EBCDIC handling | DB2 z/OS & LUW | JDBC / ASN Capture |
| 05 | `05_oracle_cdc.py` | Oracle LogMiner CDC | Oracle | LogMiner / GoldenGate |
| 06 | `06_kafka_connector.py` | Multi-topic Kafka with Avro/JSON | Apache Kafka | Kafka Connect |
| 07 | `07_iot_hub_ingestion.py` | Azure IoT Hub device-to-cloud | IoT Hub | Native Connector |
| 08 | `08_slot_machine_iot_simulator.py` | Casino IoT slot machine telemetry | Custom IoT | SAS Protocol |

### Machine Learning Notebooks

Predictive models and AI/ML pipelines.

| Notebook | Description | Model Type | Use Case |
|----------|-------------|------------|----------|
| `ml_player_churn_prediction.py` | Player churn prediction | GBT Classifier | Retention |
| `ml_fraud_detection.py` | Fraud/anomaly detection | Isolation Forest | Security |

---

## Importing Notebooks

### Via Fabric UI

1. Open your Fabric workspace
2. Click **+ New** > **Import notebook**
3. Select the `.py` or `.ipynb` file
4. Click **Upload**

> **Tip:** Import notebooks in layer order: Bronze first, then Silver, then Gold.

### Via Fabric API

```python
import requests

# Upload notebook via API
workspace_id = "your-workspace-id"
token = "your-access-token"

url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/notebooks"
headers = {"Authorization": f"Bearer {token}"}
files = {"file": open("notebook.py", "rb")}

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

---

## Notebook Format

Notebooks use the **Databricks notebook format** with `# COMMAND ----------` separators:

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Notebook Title

# COMMAND ----------

# Python code cell
df = spark.read.parquet("path")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Section Header

# COMMAND ----------

# More code
df.show()
```

---

## Environment Configuration

### Prerequisites

Notebooks expect the following:

| Requirement | Description |
|-------------|-------------|
| Default Lakehouse | Must be attached to notebook |
| Spark Session | Available as `spark` variable |
| Delta Lake | Support enabled (default in Fabric) |

### Setting Default Lakehouse

1. Open notebook in Fabric
2. Click **Lakehouse** in left panel
3. Select your Lakehouse (e.g., `lh_bronze`)
4. Click **Pin** to set as default

### Lakehouse References

| Lakehouse | Purpose | Layer |
|-----------|---------|-------|
| `lh_bronze` | Raw ingested data | Bronze |
| `lh_silver` | Cleansed/enriched data | Silver |
| `lh_gold` | Business-ready aggregations | Gold |

---

## Best Practices

### Parameterization

Use widgets for configurable values:

```python
# Configuration cell
dbutils.widgets.text("source_path", "Files/data/")
dbutils.widgets.text("batch_date", "2024-01-01")

source_path = dbutils.widgets.get("source_path")
batch_date = dbutils.widgets.get("batch_date")
```

### Error Handling

Wrap operations in try-except:

```python
try:
    df.write.saveAsTable(table_name)
    print(f"Success: Wrote {df.count()} records")
except Exception as e:
    print(f"Error: {e}")
    raise
```

### Logging

Include progress logging:

```python
from datetime import datetime

print(f"[{datetime.now()}] Starting ingestion...")
print(f"[{datetime.now()}] Read {df.count()} records")
print(f"[{datetime.now()}] Wrote to {table_name}")
```

---

## Dependencies

Notebooks use standard Fabric libraries (no additional packages required):

| Library | Version | Purpose |
|---------|---------|---------|
| PySpark | 3.4+ | Data processing |
| Delta Lake | 2.4+ | Table format |
| pandas | 2.0+ | Small dataset operations |
| matplotlib | 3.7+ | Visualization |
| seaborn | 0.12+ | Statistical visualization |
| MLflow | 2.0+ | ML experiment tracking |

---

## Execution Order

### Initial Load (One-Time)

```
1. Bronze Notebooks (can run in parallel)
   |-- 01_bronze_slot_telemetry.py
   |-- 02_bronze_player_profile.py
   |-- 03_bronze_financial_txn.py
   |-- 04_bronze_compliance.py
   |-- 05_bronze_table_games.py
   |-- 06_bronze_security_events.py
   |-- 07_bronze_tribal_health.py
   +-- 08_bronze_dot_faa.py

2. Silver Notebooks (run after Bronze, in order)
   |-- 01_silver_slot_cleansed.py
   |-- 02_silver_player_master.py
   |-- 03_silver_table_enriched.py
   |-- 04_silver_financial_reconciled.py
   |-- 05_silver_security_enriched.py
   |-- 06_silver_compliance_validated.py
   |-- 07_silver_tribal_health.py
   +-- 08_silver_dot_faa.py

3. Gold Notebooks (run after Silver)
   |-- 01_gold_slot_performance.py
   |-- 02_gold_player_360.py
   |-- 03_gold_compliance_reporting.py
   |-- 04_gold_table_analytics.py
   |-- 05_gold_financial_summary.py
   |-- 06_gold_security_dashboard.py
   |-- 07_gold_tribal_health_360.py
   +-- 08_gold_dot_faa_analytics.py

4. Streaming Notebooks (independent of medallion)
   |-- 01_sql_server_cdc.py
   |-- 02_azure_sql_change_feed.py
   |-- 03_cosmos_db_change_feed.py
   |-- 04_ibm_db2_cdc.py
   |-- 05_oracle_cdc.py
   |-- 06_kafka_connector.py
   |-- 07_iot_hub_ingestion.py
   +-- 08_slot_machine_iot_simulator.py
```

### Incremental Processing

| Layer | Strategy | Frequency |
|-------|----------|-----------|
| Bronze | Append new data | Hourly |
| Silver | Process incremental batches | Hourly |
| Gold | Refresh aggregations | Daily |

### Real-Time

- `realtime_slot_streaming.py` - Runs continuously
- KQL queries - On-demand via Eventhouse

---

## Testing Notebooks

Before running in production:

- [ ] Verify source paths exist
- [ ] Check Lakehouse connections
- [ ] Run with small data subset
- [ ] Validate row counts and schemas
- [ ] Check data quality scores
- [ ] Review execution logs

---

## Troubleshooting

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| Table not found | Lakehouse not pinned | Ensure Lakehouse is pinned and previous layer completed |
| Permission denied | Role assignment | Check workspace role assignments |
| Timeout | Large data volume | Increase cluster size or reduce data volume |
| Schema mismatch | Column changes | Use `overwriteSchema` option or fix source data |
| Memory error | Large dataset | Use partitioning or process in batches |
| Job failed | Various | Check Spark UI for detailed error logs |

---

## Directory Structure

```
notebooks/
├── 📁 bronze/                   # Bronze layer ingestion (8 notebooks)
│   ├── 01_bronze_slot_telemetry.py
│   ├── 02_bronze_player_profile.py
│   ├── 03_bronze_financial_txn.py
│   ├── 04_bronze_compliance.py
│   ├── 05_bronze_table_games.py
│   ├── 06_bronze_security_events.py
│   ├── 07_bronze_tribal_health.py       # 🏥 HIPAA-compliant
│   └── 08_bronze_dot_faa.py             # ✈️ Multi-domain
├── 📁 silver/                   # Silver layer transformation (7 notebooks)
│   ├── 01_silver_slot_cleansed.py
│   ├── 02_silver_player_master.py
│   ├── 03_silver_table_enriched.py
│   ├── 04_silver_financial_reconciled.py
│   ├── 05_silver_security_enriched.py
│   ├── 06_silver_compliance_validated.py
│   ├── 07_silver_tribal_health.py       # PHI masking, FHIR
│   └── 08_silver_dot_faa.py             # IATA validation
├── 📁 gold/                     # Gold layer aggregation (8 notebooks)
│   ├── 01_gold_slot_performance.py
│   ├── 02_gold_player_360.py
│   ├── 03_gold_compliance_reporting.py
│   ├── 04_gold_table_analytics.py
│   ├── 05_gold_financial_summary.py
│   ├── 06_gold_security_dashboard.py
│   ├── 07_gold_tribal_health_360.py     # Patient 360
│   └── 08_gold_dot_faa_analytics.py     # Carrier performance
├── 📁 streaming/                # 🔄 Streaming notebooks (8)
│   ├── 01_sql_server_cdc.py
│   ├── 02_azure_sql_change_feed.py
│   ├── 03_cosmos_db_change_feed.py
│   ├── 04_ibm_db2_cdc.py
│   ├── 05_oracle_cdc.py
│   ├── 06_kafka_connector.py
│   ├── 07_iot_hub_ingestion.py
│   └── 08_slot_machine_iot_simulator.py
├── 📁 real-time/                # Real-time analytics
│   └── 01_realtime_slot_streaming.py
├── 📁 ml/                       # Machine learning
│   ├── 01_ml_player_churn_prediction.py
│   └── 02_ml_fraud_detection.py
└── README.md
```

---

## Related Resources

| Resource | Description |
|----------|-------------|
| [Tutorials](../tutorials/README.md) | Step-by-step implementation guides |
| [Data Generation](../data-generation/README.md) | Generate test data for notebooks |
| [Validation](../validation/README.md) | Test notebook outputs |
| [Fabric Documentation](https://learn.microsoft.com/fabric/) | Official Microsoft Fabric docs |

---

<div align="center">

**[Back to Top](#notebook-fabric-notebooks)** | **[Main README](../README.md)**

</div>
