# Databricks notebook source
# MAGIC %md
# MAGIC # Tutorial 57 — Query the Databricks Mirror from a Fabric Notebook
# MAGIC
# MAGIC > **Where this runs:** Fabric Spark notebook.
# MAGIC > Once the catalog mirror from notebook 01/02 exists, mirrored tables
# MAGIC > are reachable from Spark, the SQL endpoint, and Power BI Direct Lake
# MAGIC > — **without any data movement**.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. From Spark — via the mirror's SQL Analytics Endpoint
# MAGIC
# MAGIC Each mirrored catalog item gets an auto-provisioned SQL analytics
# MAGIC endpoint. The Spark Data Warehouse connector is the canonical way to
# MAGIC query it ([spark-data-warehouse-connector](https://learn.microsoft.com/en-us/fabric/data-engineering/spark-data-warehouse-connector)).

# COMMAND ----------

# Replace with the mirror item display name from notebook 01
MIRROR_ITEM = "MirrorDBX_FullCatalog"

# Two-level naming: <itemName>.<schemaName>.<tableName>
sales = spark.read.synapsesql(f"{MIRROR_ITEM}.retail_raw.orders")
sales.printSchema()
print(f"order count: {sales.count():,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. From Spark — via direct OneLake ABFS path
# MAGIC
# MAGIC Mirrored items live at the canonical OneLake URI pattern
# MAGIC ([onelake-access-api](https://learn.microsoft.com/en-us/fabric/onelake/onelake-access-api)):
# MAGIC
# MAGIC ```
# MAGIC abfss://<workspace>@onelake.dfs.fabric.microsoft.com/
# MAGIC   <mirrorItem>.MirroredAzureDatabricksCatalog/Tables/<schema>/<table>
# MAGIC ```

# COMMAND ----------

ctx = notebookutils.runtime.context
workspace_name = ctx.currentWorkspaceName

abfss_path = (
    f"abfss://{workspace_name}@onelake.dfs.fabric.microsoft.com/"
    f"{MIRROR_ITEM}.MirroredAzureDatabricksCatalog/Tables/retail_raw/orders"
)
df = spark.read.format("delta").load(abfss_path)
df.show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. From T-SQL — via the SQL analytics endpoint
# MAGIC
# MAGIC From a Fabric Warehouse or any pyodbc client, the mirror is just
# MAGIC another schema. Three-part naming `[<mirrorItem>].[<schema>].[<table>]`.

# COMMAND ----------

# MAGIC %%sql
# MAGIC -- This cell uses the inline SQL magic available in Fabric SQL notebooks.
# MAGIC SELECT TOP 10 region, COUNT(*) AS orders, SUM(order_total) AS revenue
# MAGIC FROM [MirrorDBX_FullCatalog].[retail_raw].[orders]
# MAGIC GROUP BY region;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. From sempy (Semantic Link) — for a Power BI-style API
# MAGIC
# MAGIC Once a Direct Lake semantic model is published over the gold layer,
# MAGIC sempy gives you a one-liner read against it
# MAGIC ([read-write-power-bi-python](https://learn.microsoft.com/en-us/fabric/data-science/read-write-power-bi-python)).

# COMMAND ----------

import sempy.fabric as fabric

print("Datasets in this workspace:")
print(fabric.list_datasets())

# COMMAND ----------

# MAGIC %md
# MAGIC ## Latency sanity check
# MAGIC
# MAGIC Because the mirror is **shortcut-backed**, data changes in the
# MAGIC Databricks source are visible in Fabric **instantly** — there is no
# MAGIC replication delay (the data was never replicated). Schema changes
# MAGIC propagate within seconds via `automaticSync`. See
# MAGIC [overview](https://learn.microsoft.com/en-us/fabric/mirroring/azure-databricks).

notebookutils.notebook.exit("queried_mirror_ok")
