# Databricks notebook source
# MAGIC %md
# MAGIC # Tutorial 57 — Gold Layer: Star Schema for Semantic Model
# MAGIC
# MAGIC > **Where this runs:** Fabric notebook attached to `lh_btfabric_gold` (Lakehouse).
# MAGIC > **Inputs:** mirrored Delta tables under `Tables/dbx_mirror.retail_curated.*`
# MAGIC > (whichever Databricks mirror flavor was used in `notebooks/mirroring/`).
# MAGIC > **Outputs:** five Gold tables forming a star schema, plus the
# MAGIC > companion TMDL semantic model in `semantic-model/`.
# MAGIC
# MAGIC ## Star schema layout
# MAGIC
# MAGIC ```
# MAGIC                 dim_region
# MAGIC                     |
# MAGIC dim_customer ---- fact_sales ---- dim_product
# MAGIC                     |
# MAGIC                 dim_date
# MAGIC ```
# MAGIC
# MAGIC `fact_sales` grain = one row per **order line** so we can report on units
# MAGIC sold *and* revenue. Returns are kept as a separate fact at the same grain
# MAGIC for clean subtraction in the semantic model.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

SOURCE_CATALOG = "dbx_mirror.retail_curated"  # adjust if you mirrored differently
GOLD_LAKEHOUSE = "lh_btfabric_gold"

# Fabric: switch the default lakehouse so Tables/ paths resolve.
# In Fabric this is normally done via the lakehouse-attach UI; the line below
# is the notebook-magic equivalent if you want it parameterized.
# notebookutils.lakehouse.set_default(name=GOLD_LAKEHOUSE)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. dim_region — small but canonical

# COMMAND ----------

dim_region = spark.createDataFrame(
    [
        ("US-EAST", "USA", "North America"),
        ("US-WEST", "USA", "North America"),
        ("EMEA", "GBR", "Europe / Middle East / Africa"),
        ("APAC", "JPN", "Asia Pacific"),
    ],
    schema="region_code STRING, country STRING, supercluster STRING",
)
dim_region.write.format("delta").mode("overwrite").saveAsTable(
    f"{GOLD_LAKEHOUSE}.dim_region"
)
print("dim_region rows:", spark.table(f"{GOLD_LAKEHOUSE}.dim_region").count())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. dim_customer — type-1, drops PII columns
# MAGIC
# MAGIC We **do not** carry first/last name or email into the gold layer.
# MAGIC The semantic model is consumed by analysts who don't need PII; the audit
# MAGIC trail for who-is-who stays in `retail_curated`. This is one half of the
# MAGIC "column-level security" story we exercise in the Power BI demo.

# COMMAND ----------

dim_customer = (
    spark.table(f"{SOURCE_CATALOG}.customers")
    .select(
        F.col("customer_id"),
        F.col("region").alias("region_code"),
        F.col("loyalty_tier"),
        F.col("created_at").alias("customer_created_at"),
    )
)
dim_customer.write.format("delta").mode("overwrite").saveAsTable(
    f"{GOLD_LAKEHOUSE}.dim_customer"
)
print("dim_customer rows:", spark.table(f"{GOLD_LAKEHOUSE}.dim_customer").count())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. dim_product

# COMMAND ----------

dim_product = (
    spark.table(f"{SOURCE_CATALOG}.products")
    .select("product_id", "sku", "name", "category", "unit_cost", "unit_price")
)
dim_product.write.format("delta").mode("overwrite").saveAsTable(
    f"{GOLD_LAKEHOUSE}.dim_product"
)
print("dim_product rows:", spark.table(f"{GOLD_LAKEHOUSE}.dim_product").count())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. dim_date — generated, conformed
# MAGIC
# MAGIC Standard practice: dimension on date_key (int yyyymmdd) for tight join
# MAGIC keys in Direct Lake.

# COMMAND ----------

orders_min_max = spark.table(f"{SOURCE_CATALOG}.orders").agg(
    F.min("order_timestamp").alias("min_ts"),
    F.max("order_timestamp").alias("max_ts"),
).collect()[0]

# Bracket the range with full calendar years to make YoY measures behave.
min_year = orders_min_max["min_ts"].year - 1
max_year = orders_min_max["max_ts"].year + 1

dim_date = (
    spark.sql(
        f"SELECT sequence(to_date('{min_year}-01-01'), to_date('{max_year}-12-31'), interval 1 day) AS dates"
    )
    .withColumn("date", F.explode("dates"))
    .drop("dates")
    .select(
        (F.year("date") * 10000 + F.month("date") * 100 + F.dayofmonth("date")).alias("date_key"),
        F.col("date"),
        F.year("date").alias("year"),
        F.quarter("date").alias("quarter"),
        F.month("date").alias("month"),
        F.date_format("date", "MMMM").alias("month_name"),
        F.dayofmonth("date").alias("day_of_month"),
        F.dayofweek("date").alias("day_of_week"),
        F.date_format("date", "EEEE").alias("day_name"),
        F.weekofyear("date").alias("iso_week"),
    )
)
dim_date.write.format("delta").mode("overwrite").saveAsTable(
    f"{GOLD_LAKEHOUSE}.dim_date"
)
print("dim_date rows:", spark.table(f"{GOLD_LAKEHOUSE}.dim_date").count())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. fact_sales — order-line grain

# COMMAND ----------

orders = spark.table(f"{SOURCE_CATALOG}.orders")
lines = spark.table(f"{SOURCE_CATALOG}.order_lines")
products = spark.table(f"{SOURCE_CATALOG}.products").select(
    "product_id", "unit_cost"
)

fact_sales = (
    lines
    .join(orders, "order_id")
    .join(products, "product_id")
    .select(
        F.col("order_line_id"),
        F.col("order_id"),
        F.col("customer_id"),
        F.col("product_id"),
        F.col("region").alias("region_code"),
        (
            F.year("order_timestamp") * 10000
            + F.month("order_timestamp") * 100
            + F.dayofmonth("order_timestamp")
        ).alias("date_key"),
        F.col("quantity"),
        F.col("unit_price"),
        F.col("line_total").alias("revenue"),
        (F.col("quantity") * F.col("unit_cost")).alias("cost"),
        (F.col("line_total") - F.col("quantity") * F.col("unit_cost")).alias("gross_profit"),
    )
)
fact_sales.write.format("delta").mode("overwrite").saveAsTable(
    f"{GOLD_LAKEHOUSE}.fact_sales"
)
print("fact_sales rows:", spark.table(f"{GOLD_LAKEHOUSE}.fact_sales").count())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. fact_returns — same grain as fact_sales

# COMMAND ----------

returns_src = spark.table(f"{SOURCE_CATALOG}.returns")
lines_for_returns = spark.table(f"{SOURCE_CATALOG}.order_lines").select(
    "order_id", "product_id", "quantity", "unit_price", "line_total"
)

fact_returns = (
    returns_src
    .join(lines_for_returns, "order_id")
    .select(
        F.col("return_id"),
        F.col("order_id"),
        F.col("customer_id"),
        F.col("product_id"),
        F.col("region").alias("region_code"),
        (
            F.year("return_timestamp") * 10000
            + F.month("return_timestamp") * 100
            + F.dayofmonth("return_timestamp")
        ).alias("date_key"),
        F.col("quantity"),
        F.col("line_total").alias("refund_amount"),
        F.col("reason"),
    )
)
fact_returns.write.format("delta").mode("overwrite").saveAsTable(
    f"{GOLD_LAKEHOUSE}.fact_returns"
)
print("fact_returns rows:", spark.table(f"{GOLD_LAKEHOUSE}.fact_returns").count())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Sanity-check the joins (so Direct Lake doesn't surprise us later)

# COMMAND ----------

# Customer keys present on fact but missing on dim?
missing_customers = (
    spark.table(f"{GOLD_LAKEHOUSE}.fact_sales")
    .select("customer_id")
    .distinct()
    .join(
        spark.table(f"{GOLD_LAKEHOUSE}.dim_customer").select("customer_id"),
        "customer_id",
        "left_anti",
    )
    .count()
)
assert missing_customers == 0, (
    f"Star schema integrity: {missing_customers} customer_ids in fact_sales "
    f"have no dim_customer row. Did the mirror sync all customers?"
)
print("OK — fact_sales → dim_customer integrity holds.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done
# MAGIC
# MAGIC Gold star schema is ready. The next step is publishing the semantic model
# MAGIC defined in `semantic-model/btfabric_demo.tmdl/`, which references these
# MAGIC five tables and applies the RLS roles + measures.

print("Gold star schema complete:")
for t in ["dim_region", "dim_customer", "dim_product", "dim_date", "fact_sales", "fact_returns"]:
    print(f"  {GOLD_LAKEHOUSE}.{t}: {spark.table(f'{GOLD_LAKEHOUSE}.{t}').count():>7,} rows")
