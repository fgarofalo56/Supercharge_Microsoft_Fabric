# Databricks notebook source
# MAGIC %md
# MAGIC # Tutorial 57 — Step 2: Load Sample Data into Unity Catalog
# MAGIC
# MAGIC > **Where this runs:** Azure Databricks (same UC-enabled cluster as step 1).
# MAGIC > **Inputs:** parquet files in the landing volume from
# MAGIC > `scripts/generate_sample_data.py`.
# MAGIC > **Outputs:** five Delta tables in `better_together.retail_raw` plus
# MAGIC > region-tagged views in `better_together.retail_secure`.
# MAGIC
# MAGIC ## What this notebook does
# MAGIC
# MAGIC 1. Reads the five parquet files dropped into the UC volume.
# MAGIC 2. Writes Delta tables in `retail_raw` (overwrite mode — idempotent).
# MAGIC 3. Adds dynamic-view definitions in `retail_secure` that filter by region
# MAGIC    using `current_user()` / `is_account_group_member()` so the SAME view
# MAGIC    returns different rows per persona.

# COMMAND ----------

CATALOG_NAME = "better_together"
RAW_SCHEMA = "retail_raw"
SECURE_SCHEMA = "retail_secure"
LANDING_VOLUME = "landing"
LANDING_PATH = f"/Volumes/{CATALOG_NAME}/{RAW_SCHEMA}/{LANDING_VOLUME}"

TABLES = ["customers", "products", "orders", "order_lines", "returns"]

print(f"Reading from : {LANDING_PATH}")
print(f"Writing to   : {CATALOG_NAME}.{RAW_SCHEMA}.<table>")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Sanity-check that the parquet files are present
# MAGIC
# MAGIC If this fails, run the host-side script first:
# MAGIC
# MAGIC ```bash
# MAGIC python tutorials/57-databricks-better-together/scripts/generate_sample_data.py
# MAGIC databricks fs cp -r sample-data/57-better-together/retail \
# MAGIC   dbfs:/Volumes/better_together/retail_raw/landing/retail
# MAGIC ```

# COMMAND ----------

available = {
    f.name.rstrip("/")
    for f in dbutils.fs.ls(f"{LANDING_PATH}/retail")
}
missing = [t for t in TABLES if f"{t}.parquet" not in available]
if missing:
    raise FileNotFoundError(
        f"Missing parquet files in landing volume: {missing}. "
        f"Did you run generate_sample_data.py and upload the output?"
    )
print(f"Files present: {sorted(available)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Load each parquet into Delta in `retail_raw`
# MAGIC
# MAGIC PyArrow writes nanosecond timestamps by default, which Spark/Delta
# MAGIC cannot ingest (`Illegal Parquet type: INT64 (TIMESTAMP(NANOS,false))`).
# MAGIC The generator script now coerces to microseconds at write time, but we
# MAGIC keep a defensive read-side cast here so older parquet drops still load.

# COMMAND ----------

import pyarrow as pa
import pyarrow.parquet as pq

for table in TABLES:
    source = f"{LANDING_PATH}/retail/{table}.parquet"
    target = f"{CATALOG_NAME}.{RAW_SCHEMA}.{table}"

    arrow_tbl = pq.read_table(source)
    new_fields = []
    needs_cast = False
    for fld in arrow_tbl.schema:
        if pa.types.is_timestamp(fld.type) and fld.type.unit == "ns":
            new_fields.append(fld.with_type(pa.timestamp("us")))
            needs_cast = True
        else:
            new_fields.append(fld)
    if needs_cast:
        arrow_tbl = arrow_tbl.cast(pa.schema(new_fields))

    df = spark.createDataFrame(arrow_tbl.to_pandas())
    df.write.format("delta").mode("overwrite").saveAsTable(target)

    count = spark.table(target).count()
    print(f"  {target:<48} {count:>7,} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Create region-tagged dynamic views for the RLS demo
# MAGIC
# MAGIC The view filters by the persona-group convention from
# MAGIC `01_create_unity_catalog.py`. A user in `grp-sales-mgr-us-east` will
# MAGIC see only `US-EAST` orders; `grp-finance` and `grp-exec` see everything;
# MAGIC `grp-audit` sees aggregated revenue only.
# MAGIC
# MAGIC > 💡 We use `is_account_group_member(...)` which is the UC-canonical way
# MAGIC > to do RLS at the view level. Microsoft Learn calls this a "dynamic view"
# MAGIC > — same behavior survives the Fabric mirror via shortcut.

# COMMAND ----------

spark.sql(f"USE CATALOG {CATALOG_NAME}")

spark.sql(f"""
CREATE OR REPLACE VIEW {SECURE_SCHEMA}.orders_by_region AS
SELECT *
FROM {RAW_SCHEMA}.orders
WHERE
  is_account_group_member('grp-exec')
  OR is_account_group_member('grp-finance')
  OR (is_account_group_member('grp-sales-mgr-us-east') AND region = 'US-EAST')
  OR (is_account_group_member('grp-sales-mgr-us-west') AND region = 'US-WEST')
  OR (is_account_group_member('grp-sales-mgr-emea')    AND region = 'EMEA')
  OR (is_account_group_member('grp-sales-mgr-apac')    AND region = 'APAC')
""")

spark.sql(f"""
CREATE OR REPLACE VIEW {SECURE_SCHEMA}.audit_revenue_summary AS
SELECT
  region,
  date_trunc('month', order_timestamp) AS month,
  count(*) AS orders,
  sum(order_total) AS revenue
FROM {RAW_SCHEMA}.orders
GROUP BY region, date_trunc('month', order_timestamp)
""")

print("Views created:")
display(spark.sql(f"SHOW VIEWS IN {CATALOG_NAME}.{SECURE_SCHEMA}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done
# MAGIC
# MAGIC Continue with `02_register_databricks_mirror.py` which registers this
# MAGIC catalog as a mirrored source inside the Fabric workspace.

dbutils.notebook.exit("Sample data loaded; secure views created")
