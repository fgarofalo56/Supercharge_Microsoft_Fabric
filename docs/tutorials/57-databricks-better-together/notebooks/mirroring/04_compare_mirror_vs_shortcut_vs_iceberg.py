# Databricks notebook source
# MAGIC %md
# MAGIC # Tutorial 57 — Mirror vs Shortcut vs Iceberg vs Open Mirroring
# MAGIC
# MAGIC > A side-by-side reference notebook. Every snippet below is the
# MAGIC > **canonical 2026 syntax** from Microsoft Learn. The point of this
# MAGIC > notebook is decision support — match a real scenario to the right
# MAGIC > integration pattern.
# MAGIC
# MAGIC ## Decision matrix
# MAGIC
# MAGIC | If your source is… | Use… | Why |
# MAGIC |---|---|---|
# MAGIC | A **Unity Catalog catalog** on Databricks | Mirrored Databricks Catalog (full / inclusion / exclusion — notebook 01-02) | Zero-copy via shortcuts; schema sync automatic. |
# MAGIC | A **Databricks-managed Delta table NOT in UC** | OneLake **ADLS Gen2 shortcut** to the underlying ABFSS path | Mirror item requires UC. |
# MAGIC | **Snowflake-managed Iceberg** tables | **OneLake Iceberg shortcut** | Bidirectional virtual Delta/Iceberg metadata is auto-generated. |
# MAGIC | A **Snowflake regular table** | Native Snowflake mirror item | CDC + Delta projection in OneLake. |
# MAGIC | **S3 / GCS / non-UC ADLS** with Delta or parquet files | OneLake shortcut (S3 / GCS / ADLS variant) | No replication needed. |
# MAGIC | A DB Microsoft does NOT mirror natively (DB2, Oracle, SaaS) | **Open Mirroring** producer | You push parquet files; Fabric materializes Delta. |
# MAGIC | Azure SQL DB / SQL Server / Cosmos / PostgreSQL / MySQL / Fabric SQL DB | Native first-party mirror item | CDC-driven, free background compute. |

# COMMAND ----------

# MAGIC %md
# MAGIC ## Reference snippets (read-only — these don't all run together)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Pattern 1 — Mirrored Databricks Catalog (see notebook 01)
# MAGIC
# MAGIC ```python
# MAGIC POST /v1/workspaces/{ws}/mirroredAzureDatabricksCatalogs
# MAGIC # body: source + connection + (optional) partialCatalog
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ### Pattern 2 — OneLake S3 shortcut

# COMMAND ----------

s3_shortcut = {
    "path": "Files/landingZone",
    "name": "PartnerS3",
    "target": {
        "amazonS3": {
            "location": "https://my-bucket.s3.us-west-2.amazonaws.com",
            "subpath": "/data/orders",
            "connectionId": "<your S3 connection id>",
        }
    },
}
# POST /v1/workspaces/{ws}/items/{lakehouseId}/shortcuts
# see https://learn.microsoft.com/en-us/rest/api/fabric/core/onelake-shortcuts/create-shortcut

# COMMAND ----------

# MAGIC %md
# MAGIC ### Pattern 3 — OneLake GCS shortcut

# COMMAND ----------

gcs_shortcut = {
    "path": "Files/landingZone",
    "name": "PartnerGCS",
    "target": {
        "type": "GoogleCloudStorage",
        "googleCloudStorage": {
            "connectionId": "<your GCS connection id>",
            "location": "https://gcs-mybucket.storage.googleapis.com",
            "subpath": "/orders",
        },
    },
}

# COMMAND ----------

# MAGIC %md
# MAGIC ### Pattern 4 — OneLake Iceberg shortcut (Snowflake)
# MAGIC
# MAGIC See [onelake-iceberg-snowflake](https://learn.microsoft.com/en-us/fabric/onelake/onelake-iceberg-snowflake).
# MAGIC The shortcut targets the Snowflake-managed Iceberg metadata.
# MAGIC Fabric auto-generates a virtual Delta view; Power BI Direct Lake
# MAGIC consumes it like any Delta table.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Pattern 5 — Open Mirroring producer
# MAGIC
# MAGIC ```text
# MAGIC POST /v1/workspaces/{ws}/mirroredDatabases
# MAGIC ```
# MAGIC Then land files in the per-table landing zone:
# MAGIC
# MAGIC ```text
# MAGIC Files/LandingZone/<schema>.<table>/
# MAGIC   00000000000000000001.parquet
# MAGIC   00000000000000000002.parquet
# MAGIC   _partnerEvents.json   # declares row keys
# MAGIC ```
# MAGIC
# MAGIC Required: 20-digit zero-padded, strictly monotonic file names; a
# MAGIC `__rowMarker__` column encodes insert/update/delete. See
# MAGIC [open-mirroring-landing-zone-format](https://learn.microsoft.com/en-us/fabric/mirroring/open-mirroring-landing-zone-format).

# COMMAND ----------

# MAGIC %md
# MAGIC ### Pattern 6 — Direct ABFS from Databricks to OneLake
# MAGIC
# MAGIC Used when you want a Databricks job to read or write OneLake without a
# MAGIC mirror item. Configure the Spark session with OAuth, then read like
# MAGIC any abfss path. See [onelake-azure-databricks](https://learn.microsoft.com/en-us/fabric/onelake/onelake-azure-databricks).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cost & CU summary
# MAGIC
# MAGIC | Pattern | Storage charge | Read CU | Background CU |
# MAGIC |---|---|---|---|
# MAGIC | Mirror (Databricks) | Free (shortcuts only) | Yes (Spark / SQL / Direct Lake) | **Free** |
# MAGIC | Mirror (SQL / Cosmos / Snowflake / PG / MySQL) | Up to free entitlement (1 TB per CU) | Yes | **Free** |
# MAGIC | Open Mirroring | Same as Delta storage in OneLake | Yes | **Free for replication** |
# MAGIC | OneLake shortcut | Free | Yes | n/a |
# MAGIC | Direct ABFS from DBX | Same as Delta in OneLake | Yes (read/write through Fabric) | n/a |
# MAGIC
# MAGIC Source: [mirroring/overview](https://learn.microsoft.com/en-us/fabric/mirroring/overview).

notebookutils.notebook.exit("ok")
