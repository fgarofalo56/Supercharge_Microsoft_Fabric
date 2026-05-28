# Fabric notebook source
# MAGIC %md
# MAGIC # 🧭 Hitchhiker's Guide — 01: Connectivity
# MAGIC
# MAGIC > Everything that goes "how do I connect Fabric to ___?". Each section
# MAGIC > is independent. **Look up the section you need; ignore the rest.**
# MAGIC
# MAGIC | Section | Source / target |
# MAGIC |---|---|
# MAGIC | A | ADLS Gen2 |
# MAGIC | B | Amazon S3 |
# MAGIC | C | Google Cloud Storage |
# MAGIC | D | On-prem SQL Server (gateway) |
# MAGIC | E | Snowflake |
# MAGIC | F | Synapse Serverless SQL |
# MAGIC | G | Databricks Delta tables |
# MAGIC | H | Fabric Warehouse (T-SQL endpoint) |
# MAGIC | I | Fabric SQL Database |
# MAGIC | J | Lakehouse SQL endpoint |
# MAGIC | K | Eventhouse / KQL DB |
# MAGIC | L | GraphQL endpoint |
# MAGIC | M | Power BI semantic model (Semantic Link / sempy) |
# MAGIC | N | Fabric REST API |
# MAGIC | O | Cosmos DB mirror |
# MAGIC | P | PostgreSQL / MySQL mirror |

# COMMAND ----------

# MAGIC %md
# MAGIC ## A — ADLS Gen2
# MAGIC
# MAGIC ✅ **Best: workspace identity (no creds)** — give the workspace
# MAGIC identity Storage Blob Data Reader/Contributor on the account, then
# MAGIC just mount.

# COMMAND ----------

notebookutils.fs.mount(
    "abfss://mycontainer@mystorageaccount.dfs.core.windows.net",
    "/mydata",
)
notebookutils.fs.ls("/mydata")
# 🔗 https://learn.microsoft.com/en-us/fabric/data-engineering/notebookutils/notebookutils-file-system

# COMMAND ----------

# MAGIC %md
# MAGIC **Account key via Key Vault:**

# COMMAND ----------

account_key = notebookutils.credentials.getSecret(
    "https://myvault.vault.azure.net/", "storage-account-key"
)
notebookutils.fs.mount(
    "abfss://mycontainer@myaccount.dfs.core.windows.net",
    "/mydata",
    {"accountKey": account_key},
)

# COMMAND ----------

# MAGIC %md
# MAGIC **OAuth (no mount) — direct PySpark read:**

# COMMAND ----------

acct, tenant, client_id, client_secret = "myacct", "<tenant-id>", "<sp-id>", "<sp-secret>"
spark.conf.set(f"fs.azure.account.auth.type.{acct}.dfs.core.windows.net", "OAuth")
spark.conf.set(
    f"fs.azure.account.oauth.provider.type.{acct}.dfs.core.windows.net",
    "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
)
spark.conf.set(f"fs.azure.account.oauth2.client.id.{acct}.dfs.core.windows.net", client_id)
spark.conf.set(f"fs.azure.account.oauth2.client.secret.{acct}.dfs.core.windows.net", client_secret)
spark.conf.set(
    f"fs.azure.account.oauth2.client.endpoint.{acct}.dfs.core.windows.net",
    f"https://login.microsoftonline.com/{tenant}/oauth2/token",
)
df = spark.read.format("delta").load(f"abfss://c@{acct}.dfs.core.windows.net/path")

# COMMAND ----------

# MAGIC %md
# MAGIC ## B — Amazon S3
# MAGIC
# MAGIC Recommended: an **OneLake shortcut** registered via REST.

# COMMAND ----------

import json, requests
token = notebookutils.credentials.getToken("https://api.fabric.microsoft.com")
hdr = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
ws  = notebookutils.runtime.context.currentWorkspaceId
lh  = "<lakehouseId>"
body = {
  "path": "Files/landingZone",
  "name": "PartnerS3",
  "target": {
    "amazonS3": {
      "location": "https://my-bucket.s3.us-west-2.amazonaws.com",
      "subpath": "/data/orders",
      "connectionId": "<connection-id>",
    }
  },
}
r = requests.post(
  f"https://api.fabric.microsoft.com/v1/workspaces/{ws}/items/{lh}/shortcuts",
  headers=hdr, data=json.dumps(body), timeout=30,
)
print(r.status_code, r.text[:400])
# 🔗 https://learn.microsoft.com/en-us/fabric/onelake/create-s3-shortcut

# COMMAND ----------

# MAGIC %md
# MAGIC ## C — Google Cloud Storage

# COMMAND ----------

body = {
  "path": "Files/landingZone",
  "name": "PartnerGCS",
  "target": {
    "type": "GoogleCloudStorage",
    "googleCloudStorage": {
      "connectionId": "<connection-id>",
      "location": "https://gcs-mybucket.storage.googleapis.com",
      "subpath": "/orders",
    },
  },
}
# Same POST URL as section B.
# 🔗 https://learn.microsoft.com/en-us/fabric/onelake/create-gcs-shortcut

# COMMAND ----------

# MAGIC %md
# MAGIC ## D — On-prem SQL Server
# MAGIC
# MAGIC - Install the **On-premises data gateway** (Enterprise, v3000.214.2+).
# MAGIC - Create a Fabric cloud connection of type SQL Server, choose the gateway.
# MAGIC - For private VNet sources, use a **virtual network data gateway** or
# MAGIC   **MPE → Private Link Service → ExpressRoute/VPN**.
# MAGIC - For continuous CDC, use **SQL Server mirroring**.
# MAGIC
# MAGIC 🔗 [connect-to-on-premise-sources-using-managed-private-endpoints](https://learn.microsoft.com/en-us/fabric/security/connect-to-on-premise-sources-using-managed-private-endpoints)
# MAGIC 🔗 [sql-server-tutorial](https://learn.microsoft.com/en-us/fabric/mirroring/sql-server-tutorial)

# COMMAND ----------

# MAGIC %md
# MAGIC ## E — Snowflake
# MAGIC
# MAGIC Three ways:
# MAGIC 1. **Mirror** (recommended — CDC into OneLake Delta).
# MAGIC 2. **Spark connector** in a notebook for ad-hoc reads.
# MAGIC 3. **Snowflake-managed Iceberg DB item** when Snowflake owns Iceberg.
# MAGIC
# MAGIC 🔗 [mirroring/snowflake](https://learn.microsoft.com/en-us/fabric/mirroring/snowflake),
# MAGIC [create-snowflake-database-item](https://learn.microsoft.com/en-us/fabric/onelake/snowflake/create-snowflake-database-item)

# COMMAND ----------

sf_secret = notebookutils.credentials.getSecret("https://myvault.vault.azure.net/", "snowflake-pwd")
sfopts = {
  "sfURL": "myacct.snowflakecomputing.com",
  "sfUser": "FABRIC_READER",
  "sfPassword": sf_secret,
  "sfDatabase": "ANALYTICS",
  "sfSchema": "PUBLIC",
  "sfWarehouse": "COMPUTE_WH",
}
df = (spark.read.format("snowflake").options(**sfopts).option("dbtable", "DIM_CUSTOMER").load())

# COMMAND ----------

# MAGIC %md
# MAGIC ## F — Synapse Serverless SQL pool
# MAGIC
# MAGIC No first-party mirror. Best pattern: **shortcut to the underlying ADLS
# MAGIC parquet** that Synapse Serverless reads, and skip Synapse at query time.

# COMMAND ----------

# MAGIC %md
# MAGIC ## G — Databricks Delta tables
# MAGIC
# MAGIC | Source posture | Best pattern |
# MAGIC |---|---|
# MAGIC | UC-governed table | **Mirrored Databricks Catalog** |
# MAGIC | Non-UC ADLS-managed Delta | OneLake **ADLS Gen2 shortcut** |
# MAGIC | Ad-hoc Databricks job reading OneLake | **Direct ABFS from Databricks** with OAuth |
# MAGIC
# MAGIC 🔗 [azure-databricks](https://learn.microsoft.com/en-us/fabric/mirroring/azure-databricks),
# MAGIC [onelake-azure-databricks](https://learn.microsoft.com/en-us/fabric/onelake/onelake-azure-databricks)
# MAGIC
# MAGIC See tutorial 57 for end-to-end examples of all three.

# COMMAND ----------

# MAGIC %md
# MAGIC ## H — Fabric Warehouse from a notebook (T-SQL endpoint)

# COMMAND ----------

import struct, pyodbc

token_bytes = notebookutils.credentials.getToken(
    "https://analysis.windows.net/powerbi/api"
).encode("utf-16-le")
token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
SQL_COPT_SS_ACCESS_TOKEN = 1256

conn_str = (
    "Driver={ODBC Driver 18 for SQL Server};"
    f"Server=<workspace>-<dataworkspace-id>.datawarehouse.fabric.microsoft.com,1433;"
    f"Database=<warehouse>;"
    "Encrypt=yes;TrustServerCertificate=no;"
)
cn = pyodbc.connect(conn_str, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
# Or the Spark connector:
df = spark.read.synapsesql("warehouse.dbo.dim_customer")
# 🔗 https://learn.microsoft.com/en-us/fabric/data-engineering/spark-data-warehouse-connector

# COMMAND ----------

# MAGIC %md
# MAGIC ## I — Fabric SQL Database

# COMMAND ----------

conn_str = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=<workspace-guid>.database.fabric.microsoft.com,1433;"
    "Database=<db>;"
    "Encrypt=yes;TrustServerCertificate=no;"
    "Authentication=ActiveDirectoryDefault;"
)
# After `az login` (locally) or in a notebook with workspace identity,
# ActiveDirectoryDefault reuses cached credentials. ODBC 18+ required.
# 🔗 https://learn.microsoft.com/en-us/fabric/database/sql/connect-jupyter-notebook

# COMMAND ----------

# MAGIC %md
# MAGIC ## J — Lakehouse SQL endpoint
# MAGIC
# MAGIC Same pyodbc pattern as H/I. Get the server name from the SQL analytics
# MAGIC endpoint property on the lakehouse item.

# COMMAND ----------

# MAGIC %md
# MAGIC ## K — Eventhouse / KQL DB

# COMMAND ----------

kusto_token = notebookutils.credentials.getToken("kusto")
df = (
    spark.read
    .format("com.microsoft.kusto.spark.synapse.datasource")
    .option("accessToken", kusto_token)
    .option("kustoCluster", "https://<cluster-uri>.kusto.fabric.microsoft.com")
    .option("kustoDatabase", "<db>")
    .option("kustoQuery", "T | take 10")
    .load()
)
# Or read directly from OneLake-availability path:
df = spark.read.format("delta").load(
    "abfss://<ws-guid>@onelake.dfs.fabric.microsoft.com/<eh-guid>/Tables/MyTable"
)
# 🔗 https://learn.microsoft.com/en-us/fabric/real-time-intelligence/spark-connector
# 🔗 https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-house-onelake-availability

# COMMAND ----------

# MAGIC %md
# MAGIC ## L — GraphQL endpoint

# COMMAND ----------

import requests
token = notebookutils.credentials.getToken("https://analysis.windows.net/powerbi/api")
endpoint = "https://<graphql>.graphql.fabric.microsoft.com/v1/workspaces/<ws>/graphqlapis/<api>/graphql"
query = "{ products(first: 5) { items { productId name listPrice } } }"
r = requests.post(endpoint, headers={"Authorization": f"Bearer {token}"}, json={"query": query})
r.json()
# 🔗 https://learn.microsoft.com/en-us/fabric/data-engineering/connect-apps-api-graphql

# COMMAND ----------

# MAGIC %md
# MAGIC ## M — Power BI semantic model via Semantic Link (sempy)

# COMMAND ----------

import sempy.fabric as fabric
fabric.list_datasets()
fabric.list_tables("Customer Profitability Sample")
fabric.list_measures("Customer Profitability Sample")
df = fabric.read_table("Customer Profitability Sample", "Customer")
# 🔗 https://learn.microsoft.com/en-us/fabric/data-science/read-write-power-bi-python

# COMMAND ----------

# MAGIC %md
# MAGIC ## N — Fabric REST API

# COMMAND ----------

token = notebookutils.credentials.getToken("https://api.fabric.microsoft.com")
r = requests.get(
    "https://api.fabric.microsoft.com/v1/workspaces",
    headers={"Authorization": f"Bearer {token}"},
)
r.json()
# Item-management scopes for Data Factory pipelines:
#   Workspace.ReadWrite.All, Item.ReadWrite.All

# COMMAND ----------

# MAGIC %md
# MAGIC ## O — Cosmos DB via mirror
# MAGIC
# MAGIC Provision a mirrored Cosmos DB item from the Fabric portal — data
# MAGIC lands as Delta in OneLake. Background replication is **free**; query
# MAGIC the OneLake Delta projection in Spark or Direct Lake (avoid hitting
# MAGIC Cosmos directly, which still charges RU).
# MAGIC
# MAGIC 🔗 [azure-cosmos-db](https://learn.microsoft.com/en-us/fabric/mirroring/azure-cosmos-db)

# COMMAND ----------

# MAGIC %md
# MAGIC ## P — PostgreSQL / MySQL mirror
# MAGIC
# MAGIC - **Azure Database for PostgreSQL** → native mirror item.
# MAGIC - **Azure Database for MySQL** → native mirror item.
# MAGIC - **On-prem or generic PG/MySQL** → on-prem data gateway + Copy Job CDC,
# MAGIC   or write your own **Open Mirroring** producer.
# MAGIC
# MAGIC 🔗 [PostgreSQL mirroring](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-fabric-mirroring),
# MAGIC [MySQL mirroring](https://learn.microsoft.com/en-us/azure/mysql/integration/fabric-mirroring-mysql)
