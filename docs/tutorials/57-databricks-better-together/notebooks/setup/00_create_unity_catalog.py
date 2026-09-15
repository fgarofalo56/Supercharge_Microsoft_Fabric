# Databricks notebook source
# MAGIC %md
# MAGIC # Tutorial 57 — Step 1: Create the Unity Catalog Estate
# MAGIC
# MAGIC > **Where this runs:** Azure Databricks (Premium workspace, UC-enabled).
# MAGIC > **Why this exists:** Sets up the source-of-truth catalog/schema/table layout
# MAGIC > that we will subsequently mirror into Fabric. Idempotent — safe to re-run.
# MAGIC
# MAGIC ## What this notebook creates
# MAGIC
# MAGIC | Object | Name | Purpose |
# MAGIC |---|---|---|
# MAGIC | Catalog | `better_together` | Top-level container for the demo. |
# MAGIC | Schema  | `better_together.retail_raw` | Bronze-equivalent landing tables. |
# MAGIC | Schema  | `better_together.retail_curated` | Silver-equivalent cleansed views. |
# MAGIC | Schema  | `better_together.retail_secure` | Region-tagged views for RLS demos. |
# MAGIC | Volume  | `better_together.retail_raw.landing` | Where the synthetic parquet lands before tables are populated. |
# MAGIC
# MAGIC ## Prerequisites
# MAGIC
# MAGIC - The cluster running this notebook **must** have Unity Catalog access (Shared or Single-User mode with UC enabled).
# MAGIC - Your user (or the SP running this) must have `CREATE CATALOG` on the metastore.
# MAGIC   If you only have schema-level rights, change `CATALOG_NAME` to an existing catalog
# MAGIC   you own and the rest of the notebook will work without modification.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

CATALOG_NAME = "better_together"
RAW_SCHEMA = "retail_raw"
CURATED_SCHEMA = "retail_curated"
SECURE_SCHEMA = "retail_secure"
LANDING_VOLUME = "landing"

# Storage root — leave empty to use the metastore default managed location.
# Set this if you need an external location (recommended for production).
STORAGE_ROOT = ""

print(f"Target catalog : {CATALOG_NAME}")
print(f"  raw schema   : {RAW_SCHEMA}")
print(f"  curated      : {CURATED_SCHEMA}")
print(f"  secure       : {SECURE_SCHEMA}")
print(f"  landing vol  : {LANDING_VOLUME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Create the catalog (idempotent)

# COMMAND ----------

storage_clause = f"MANAGED LOCATION '{STORAGE_ROOT}'" if STORAGE_ROOT else ""
spark.sql(
    f"CREATE CATALOG IF NOT EXISTS {CATALOG_NAME} {storage_clause}".strip()
)
spark.sql(f"USE CATALOG {CATALOG_NAME}")
print(f"Catalog ready: {CATALOG_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Create the schemas
# MAGIC
# MAGIC Three schemas mirror the medallion pattern from the rest of this repo:
# MAGIC
# MAGIC - `retail_raw` — append-only landing zone.
# MAGIC - `retail_curated` — cleansed, typed, deduplicated.
# MAGIC - `retail_secure` — region-tagged views used to demonstrate RLS in both
# MAGIC   Databricks **and** Fabric after we mirror.

# COMMAND ----------

for schema in (RAW_SCHEMA, CURATED_SCHEMA, SECURE_SCHEMA):
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG_NAME}.{schema}")
    print(f"  schema ready: {CATALOG_NAME}.{schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Create a Unity Catalog volume for raw parquet drop
# MAGIC
# MAGIC Volumes are the recommended landing area inside UC — they support both
# MAGIC managed and external paths and play nicely with shortcuts when we later
# MAGIC publish from Fabric.

# COMMAND ----------

spark.sql(
    f"CREATE VOLUME IF NOT EXISTS {CATALOG_NAME}.{RAW_SCHEMA}.{LANDING_VOLUME}"
)
landing_path = f"/Volumes/{CATALOG_NAME}/{RAW_SCHEMA}/{LANDING_VOLUME}"
print(f"Landing volume ready at: {landing_path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Persona group placeholders
# MAGIC
# MAGIC The persona groups themselves live in Entra ID — see
# MAGIC `02_register_databricks_mirror.py` and the security automation notebook
# MAGIC for how those are provisioned. Here we just confirm the catalog is ready
# MAGIC to receive grants and emit the names we will use later.

# COMMAND ----------

persona_groups = [
    "grp-sales-mgr-us-east",
    "grp-sales-mgr-us-west",
    "grp-sales-mgr-emea",
    "grp-sales-mgr-apac",
    "grp-finance",
    "grp-exec",
    "grp-audit",
    "grp-data-engineer",
]
print("Personas expected later in the tutorial:")
for g in persona_groups:
    print(f"  - {g}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Confirm what we created

# COMMAND ----------

display(spark.sql(f"SHOW SCHEMAS IN {CATALOG_NAME}"))
display(spark.sql(f"SHOW VOLUMES IN {CATALOG_NAME}.{RAW_SCHEMA}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done
# MAGIC
# MAGIC Continue with `01_load_sample_data.py` to populate the catalog with the
# MAGIC synthetic retail dataset produced by
# MAGIC `scripts/generate_sample_data.py`.

dbutils.notebook.exit("UC estate ready")
