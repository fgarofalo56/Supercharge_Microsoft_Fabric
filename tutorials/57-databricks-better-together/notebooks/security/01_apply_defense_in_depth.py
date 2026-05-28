# Databricks notebook source
# MAGIC %md
# MAGIC # Tutorial 57 — Defense-in-Depth Automation
# MAGIC
# MAGIC > **Where this runs:** Fabric notebook with workspace-identity / SPN
# MAGIC > permissions for: Graph API (Group.ReadWrite.All), Fabric workspace
# MAGIC > admin, OneLake data access roles, Warehouse SQL admin.
# MAGIC > **What it does:** Idempotently configures every layer of Microsoft's
# MAGIC > defense-in-depth model so the three Power BI reports work for their
# MAGIC > intended personas — and **only** their intended personas.
# MAGIC
# MAGIC ## Layers configured (in order, low to high)
# MAGIC
# MAGIC | # | Layer | API / surface |
# MAGIC |---|---|---|
# MAGIC | 1 | **Entra ID groups** for personas | Microsoft Graph |
# MAGIC | 2 | **Workspace role assignments** | Fabric REST (`/workspaces/{id}/roleAssignments`) |
# MAGIC | 3 | **OneLake security roles** (RLS — GA; CLS — Preview) | Fabric REST (`/items/{id}/dataAccessRoles`) |
# MAGIC | 4 | **Warehouse SQL grants + RLS + DDM** | T-SQL via pyodbc |
# MAGIC | 5 | **Semantic model fixed-identity refresh** | Power BI REST |
# MAGIC | 6 | **RLS mapping table** (powers the dynamic role) | Spark write to Gold |
# MAGIC
# MAGIC ## Source policy
# MAGIC
# MAGIC Every REST call below cites the canonical Microsoft Learn page in a
# MAGIC comment immediately above the request. CLS (column-level security)
# MAGIC is still **Preview** in April 2026 — production users should hold off
# MAGIC on relying on it for compliance until GA.

# COMMAND ----------

import json
import struct
import time

import pandas as pd
import pyodbc
import requests

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Where the persona CSV from the generator is stored. Upload before running.
PERSONAS_PATH = "Files/57-better-together/personas/users.csv"
GROUPS_PATH = "Files/57-better-together/personas/groups.csv"

# Workspace + item identifiers
ctx = notebookutils.runtime.context
WORKSPACE_ID = ctx.currentWorkspaceId
WORKSPACE_NAME = ctx.currentWorkspaceName

GOLD_LAKEHOUSE_NAME = "lh_btfabric_gold"
WAREHOUSE_NAME = "wh_btfabric_gold"      # optional companion warehouse
WAREHOUSE_SERVER = f"<workspace-guid>.datawarehouse.fabric.microsoft.com"

# Tokens — pulled via the notebook's identity (workspace identity is best).
fabric_token = notebookutils.credentials.getToken("https://api.fabric.microsoft.com")
graph_token = notebookutils.credentials.getToken("https://graph.microsoft.com")
pbi_token = notebookutils.credentials.getToken("https://analysis.windows.net/powerbi/api")

fabric_h = {"Authorization": f"Bearer {fabric_token}", "Content-Type": "application/json"}
graph_h = {"Authorization": f"Bearer {graph_token}", "Content-Type": "application/json"}
pbi_h = {"Authorization": f"Bearer {pbi_token}", "Content-Type": "application/json"}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Layer 1 — Entra ID groups (Microsoft Graph)
# MAGIC
# MAGIC Docs:
# MAGIC - [Create group](https://learn.microsoft.com/en-us/graph/api/group-post-groups)
# MAGIC - [Add member](https://learn.microsoft.com/en-us/graph/api/group-post-members)

# COMMAND ----------

groups_df = pd.read_csv(GROUPS_PATH)
users_df = pd.read_csv(PERSONAS_PATH)

# Idempotency: skip groups that already exist (matched by displayName).
existing = requests.get(
    "https://graph.microsoft.com/v1.0/groups?$select=id,displayName&$top=999",
    headers=graph_h,
    timeout=30,
).json()
by_name = {g["displayName"]: g["id"] for g in existing.get("value", [])}

created: dict[str, str] = {}
for _, g in groups_df.iterrows():
    name = g["group_name"]
    if name in by_name:
        created[name] = by_name[name]
        continue
    body = {
        "displayName": name,
        "description": g["description"],
        "mailEnabled": False,
        "mailNickname": name.replace(" ", "-"),
        "securityEnabled": True,
    }
    r = requests.post(
        "https://graph.microsoft.com/v1.0/groups",
        headers=graph_h,
        data=json.dumps(body),
        timeout=30,
    )
    if r.status_code == 201:
        created[name] = r.json()["id"]
        print(f"  created group: {name}")
    else:
        print(f"  WARN  failed group {name}: {r.status_code} {r.text[:200]}")

print(f"Group inventory: {len(created)} groups available.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Layer 2 — Fabric workspace role assignments
# MAGIC
# MAGIC Docs: [add-workspace-role-assignment](https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/add-workspace-role-assignment).
# MAGIC Cap: 1000 principals per workspace; groups count as 1.

# COMMAND ----------

ROLE_FOR_GROUP = {
    "grp-data-engineer": "Contributor",
    "grp-exec": "Viewer",
    "grp-finance": "Viewer",
    "grp-audit": "Viewer",
    # Regional managers — Viewer only; RLS/OLS does the heavy lifting downstream.
    "grp-sales-mgr-us-east": "Viewer",
    "grp-sales-mgr-us-west": "Viewer",
    "grp-sales-mgr-emea":    "Viewer",
    "grp-sales-mgr-apac":    "Viewer",
}

assign_url = (
    f"https://api.fabric.microsoft.com/v1/workspaces/"
    f"{WORKSPACE_ID}/roleAssignments"
)
for group_name, role in ROLE_FOR_GROUP.items():
    group_id = created.get(group_name)
    if not group_id:
        print(f"  skip {group_name} — not in created map")
        continue
    body = {
        "principal": {"id": group_id, "type": "Group"},
        "role": role,
    }
    r = requests.post(assign_url, headers=fabric_h, data=json.dumps(body), timeout=30)
    if r.status_code in (200, 201):
        print(f"  {group_name:<30} -> {role}")
    elif r.status_code == 409:
        print(f"  {group_name:<30} already assigned")
    else:
        print(f"  WARN  {group_name}: {r.status_code} {r.text[:200]}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Layer 3 — OneLake security roles on the Gold lakehouse
# MAGIC
# MAGIC Docs: [data-access-control-model](https://learn.microsoft.com/en-us/fabric/onelake/security/data-access-control-model),
# MAGIC [create-or-update-data-access-roles](https://learn.microsoft.com/en-us/rest/api/fabric/core/onelake-data-access-security/create-or-update-data-access-roles).
# MAGIC
# MAGIC ⚠️ **CLS is still Preview** as of April 2026. We define it here for
# MAGIC demonstration but the production posture should layer it behind a
# MAGIC feature flag until MS marks it GA.

# COMMAND ----------

# Look up the lakehouse item id
items = requests.get(
    f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/items?type=Lakehouse",
    headers=fabric_h,
    timeout=30,
).json()
gold_id = next(
    (it["id"] for it in items.get("value", []) if it["displayName"] == GOLD_LAKEHOUSE_NAME),
    None,
)
assert gold_id, f"Gold lakehouse '{GOLD_LAKEHOUSE_NAME}' not found in workspace."

def build_member(group_id: str) -> dict:
    return {
        "fabricItemMembers": [
            {
                "itemAccess": ["ReadAll"],
                "sourcePath": f"{WORKSPACE_ID}/{gold_id}",
            }
        ],
        "microsoftEntraMembers": [{"objectId": group_id, "tenantId": ctx.currentWorkspaceTenantId}],
    }

roles_payload = {
    "value": [
        # Finance — read everything, but customer_id column is denied (CLS).
        {
            "name": "FinanceReader",
            "decisionRules": [
                {
                    "effect": "Permit",
                    "permission": [
                        {"attributeName": "Path",   "attributeValueIncludedIn": ["*"]},
                        {"attributeName": "Action", "attributeValueIncludedIn": ["Read"]},
                    ],
                    "constraints": {
                        "columns": [
                            {
                                "tablePath": "/Tables/dim_customer",
                                "columnNames": ["customer_id"],
                                "columnEffect": "Deny",       # PREVIEW (CLS)
                                "columnAction": ["Read"],
                            }
                        ],
                    },
                }
            ],
            "members": build_member(created.get("grp-finance", "")),
        },
        # Regional managers — one role per region with a row filter.
        *[
            {
                "name": f"RegionalReader_{region}",
                "decisionRules": [
                    {
                        "effect": "Permit",
                        "permission": [
                            {"attributeName": "Path",   "attributeValueIncludedIn": ["*"]},
                            {"attributeName": "Action", "attributeValueIncludedIn": ["Read"]},
                        ],
                        "constraints": {
                            "rows": [
                                {
                                    "tablePath": "/Tables/fact_sales",
                                    "value": f"select * from fact_sales where region_code = '{region}'",
                                },
                                {
                                    "tablePath": "/Tables/fact_returns",
                                    "value": f"select * from fact_returns where region_code = '{region}'",
                                },
                            ],
                        },
                    }
                ],
                "members": build_member(created.get(f"grp-sales-mgr-{region.lower()}", "")),
            }
            for region in ["US-EAST", "US-WEST", "EMEA", "APAC"]
        ],
        # Executive — full ReadAll, no constraints.
        {
            "name": "ExecutiveReader",
            "decisionRules": [
                {
                    "effect": "Permit",
                    "permission": [
                        {"attributeName": "Path",   "attributeValueIncludedIn": ["*"]},
                        {"attributeName": "Action", "attributeValueIncludedIn": ["Read"]},
                    ],
                }
            ],
            "members": build_member(created.get("grp-exec", "")),
        },
    ]
}

put_url = (
    f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/"
    f"items/{gold_id}/dataAccessRoles"
)
r = requests.put(put_url, headers=fabric_h, data=json.dumps(roles_payload), timeout=60)
print(f"OneLake data access roles: HTTP {r.status_code}")
if r.status_code >= 400:
    print(r.text[:600])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Layer 4 — Warehouse T-SQL: RLS + DDM
# MAGIC
# MAGIC Docs:
# MAGIC - [tutorial-row-level-security](https://learn.microsoft.com/en-us/fabric/data-warehouse/tutorial-row-level-security)
# MAGIC - [dynamic-data-masking](https://learn.microsoft.com/en-us/fabric/data-warehouse/dynamic-data-masking)
# MAGIC
# MAGIC ⚠️ **Direct Lake caveat:** Power BI Direct Lake on a Warehouse with
# MAGIC RLS/CLS in place **falls back to DirectQuery**. If you want full
# MAGIC Direct Lake performance, prefer OneLake security RLS (Layer 3) over
# MAGIC Warehouse RLS.

# COMMAND ----------

def warehouse_conn():
    token_bytes = pbi_token.encode("utf-16-le")
    token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
    SQL_COPT_SS_ACCESS_TOKEN = 1256
    conn_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server={WAREHOUSE_SERVER},1433;"
        f"Database={WAREHOUSE_NAME};"
        "Encrypt=yes;TrustServerCertificate=no;"
    )
    return pyodbc.connect(conn_str, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})

try:
    cn = warehouse_conn()
except Exception as e:
    print(f"Warehouse not reachable — skipping T-SQL layer ({e})")
    cn = None

if cn is not None:
    cur = cn.cursor()
    cur.execute("""
    IF SCHEMA_ID('Security') IS NULL EXEC('CREATE SCHEMA Security');

    CREATE OR ALTER FUNCTION Security.fn_region_predicate(@region AS NVARCHAR(20))
      RETURNS TABLE WITH SCHEMABINDING AS
      RETURN SELECT 1 AS predicate_result
        WHERE
          IS_ROLEMEMBER('exec') = 1
          OR IS_ROLEMEMBER('finance') = 1
          OR (IS_ROLEMEMBER('sales-mgr-us-east') = 1 AND @region = 'US-EAST')
          OR (IS_ROLEMEMBER('sales-mgr-us-west') = 1 AND @region = 'US-WEST')
          OR (IS_ROLEMEMBER('sales-mgr-emea')    = 1 AND @region = 'EMEA')
          OR (IS_ROLEMEMBER('sales-mgr-apac')    = 1 AND @region = 'APAC');

    IF NOT EXISTS (SELECT 1 FROM sys.security_policies WHERE name = 'FactSalesRLS')
      CREATE SECURITY POLICY FactSalesRLS
        ADD FILTER PREDICATE Security.fn_region_predicate(region_code)
        ON dbo.fact_sales
      WITH (STATE = ON);

    -- DDM on dim_customer.customer_id when query path goes via Warehouse.
    IF NOT EXISTS (
      SELECT 1 FROM sys.masked_columns
      WHERE object_id = OBJECT_ID('dbo.dim_customer') AND name = 'customer_id'
    )
      ALTER TABLE dbo.dim_customer
        ALTER COLUMN customer_id ADD MASKED WITH (FUNCTION = 'partial(2, "***", 0)');
    """)
    cn.commit()
    cn.close()
    print("Warehouse RLS + DDM applied.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Layer 5 — Semantic model: Fixed Identity for refresh
# MAGIC
# MAGIC SPNs cannot be RLS/OLS members, so the canonical Direct Lake refresh
# MAGIC pattern is **Fixed Identity** — a real user account whose only purpose
# MAGIC is refreshing the model. We register the credential here and the
# MAGIC model owner sets `fixedIdentity` in Power BI service.
# MAGIC
# MAGIC Docs: [service-premium-service-principal](https://learn.microsoft.com/en-us/fabric/enterprise/powerbi/service-premium-service-principal).

# COMMAND ----------

print(
    "Manual step (or extend with Power BI REST):\n"
    "  1. In Power BI Service, open the semantic model settings.\n"
    "  2. Under 'Direct Lake fallback' & 'Refresh', set Fixed Identity to a\n"
    "     dedicated user account (NOT the SP, NOT a regional manager).\n"
    "  3. Grant that user 'ReadAll' on the gold lakehouse via OneLake roles.\n"
    "Reason: SPNs cannot be members of RLS/OLS roles."
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Layer 6 — RLS mapping table (powers the dynamic semantic-model role)
# MAGIC
# MAGIC The semantic model's `RegionalManager` role looks up `USERPRINCIPALNAME()`
# MAGIC in the gold lakehouse table `rls_user_region_map`. We materialize that
# MAGIC table here from the persona CSV.

# COMMAND ----------

mapping_pdf = users_df[users_df["region"] != "ALL"][["upn", "region"]].rename(
    columns={"region": "region_code"}
)
mapping_df = spark.createDataFrame(mapping_pdf)
mapping_df.write.format("delta").mode("overwrite").saveAsTable(
    f"{GOLD_LAKEHOUSE_NAME}.rls_user_region_map"
)
print(f"rls_user_region_map populated: {mapping_df.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done — verify with the regression cell below
# MAGIC
# MAGIC Run this cell as different personas (use **View as** in Power BI, or
# MAGIC sign into the SQL endpoint as the persona) and confirm the row counts
# MAGIC match expectations:
# MAGIC
# MAGIC | Persona | Expected `fact_sales` rows |
# MAGIC |---|---|
# MAGIC | Exec | all rows |
# MAGIC | Finance | all rows (but `customer_id` masked / hidden) |
# MAGIC | sales-mgr-us-east | only US-EAST |
# MAGIC | sales-mgr-emea | only EMEA |
# MAGIC | audit | aggregate views only (no row data) |

display(
    spark.sql(
        f"SELECT region_code, COUNT(*) FROM {GOLD_LAKEHOUSE_NAME}.fact_sales "
        f"GROUP BY region_code"
    )
)

notebookutils.notebook.exit("defense-in-depth applied")
