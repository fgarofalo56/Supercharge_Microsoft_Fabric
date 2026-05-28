# Fabric notebook source
# MAGIC %md
# MAGIC # 🧭 Hitchhiker's Guide — 03: Security & Identity
# MAGIC
# MAGIC ## Sections
# MAGIC
# MAGIC | # | Topic |
# MAGIC |---|---|
# MAGIC | A | OneLake security role: RLS + CLS via REST |
# MAGIC | B | Warehouse RLS |
# MAGIC | C | Warehouse CLS |
# MAGIC | D | Warehouse DDM (Dynamic Data Masking) |
# MAGIC | E | Semantic model RLS via DAX role |
# MAGIC | F | Workspace identity token from notebook |
# MAGIC | G | Service principal token via MSAL |
# MAGIC | H | Key Vault: get / put secret |
# MAGIC | I | "Who am I?" — current user + workspace identity |

# COMMAND ----------

# MAGIC %md
# MAGIC ## A — OneLake security role (RLS GA, CLS Preview)
# MAGIC
# MAGIC `PUT /v1/workspaces/{ws}/items/{item}/dataAccessRoles`
# MAGIC
# MAGIC 🔗 [create-or-update-data-access-roles](https://learn.microsoft.com/en-us/rest/api/fabric/core/onelake-data-access-security/create-or-update-data-access-roles)

# COMMAND ----------

import json, requests
token = notebookutils.credentials.getToken("https://api.fabric.microsoft.com")
hdr = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
ws = notebookutils.runtime.context.currentWorkspaceId
item = "<lakehouseId>"

body = {
  "value": [{
    "name": "FinanceReader",
    "decisionRules": [{
      "effect": "Permit",
      "permission": [
        {"attributeName": "Path",   "attributeValueIncludedIn": ["*"]},
        {"attributeName": "Action", "attributeValueIncludedIn": ["Read"]}
      ],
      "constraints": {
        "rows": [{
          "tablePath": "/Tables/fact_sales",
          "value": "select * from fact_sales where region_code = 'EMEA'"
        }],
        "columns": [{
          "tablePath": "/Tables/dim_customer",
          "columnNames": ["customer_id"],
          "columnEffect": "Deny",     # ⚠️ PREVIEW (CLS)
          "columnAction": ["Read"]
        }]
      }
    }],
    "members": {
      "microsoftEntraMembers": [{
        "objectId": "<group-or-user-id>",
        "tenantId": "<tenant-id>"
      }]
    }
  }]
}
r = requests.put(
  f"https://api.fabric.microsoft.com/v1/workspaces/{ws}/items/{item}/dataAccessRoles",
  headers=hdr, data=json.dumps(body), timeout=60,
)
print(r.status_code, r.text[:400])

# COMMAND ----------

# MAGIC %md
# MAGIC ## B — Warehouse RLS
# MAGIC
# MAGIC 🔗 [tutorial-row-level-security](https://learn.microsoft.com/en-us/fabric/data-warehouse/tutorial-row-level-security)

# COMMAND ----------

# Run via pyodbc or Fabric SQL Editor
sql = """
CREATE FUNCTION Security.fn_securitypredicate(@SalesRep AS sysname)
RETURNS TABLE WITH SCHEMABINDING AS
RETURN SELECT 1 AS fn_securitypredicate_result
       WHERE @SalesRep = USER_NAME() OR USER_NAME() = 'manager@contoso.com';

CREATE SECURITY POLICY SalesFilter
ADD FILTER PREDICATE Security.fn_securitypredicate(SalesRep) ON dbo.Sales
WITH (STATE = ON);
"""

# COMMAND ----------

# MAGIC %md
# MAGIC ## C — Warehouse CLS

# COMMAND ----------

sql = """
GRANT SELECT ON dbo.Membership(MemberID, FirstName, LastName) TO Marketing;
"""

# COMMAND ----------

# MAGIC %md
# MAGIC ## D — Warehouse DDM (Dynamic Data Masking)
# MAGIC
# MAGIC 🔗 [dynamic-data-masking](https://learn.microsoft.com/en-us/fabric/data-warehouse/dynamic-data-masking)

# COMMAND ----------

sql = """
ALTER TABLE dbo.EmployeeData
ALTER COLUMN [email] ADD MASKED WITH (FUNCTION = 'email()');

ALTER TABLE dbo.EmployeeData
ALTER COLUMN [ssn]   ADD MASKED WITH (FUNCTION = 'partial(0,"XXX-XX-",4)');

GRANT UNMASK ON dbo.EmployeeData TO [auditor@contoso.com];
"""

# COMMAND ----------

# MAGIC %md
# MAGIC ## E — Semantic model RLS via DAX
# MAGIC
# MAGIC In Power BI Desktop → Modeling → Manage Roles, or via TMDL `role` block:
# MAGIC
# MAGIC ```dax
# MAGIC -- Static
# MAGIC [Region] = "West"
# MAGIC
# MAGIC -- Dynamic (USERPRINCIPALNAME-driven)
# MAGIC [Region] IN
# MAGIC   SELECTCOLUMNS(
# MAGIC     FILTER('UserRegionMap', 'UserRegionMap'[upn] = USERPRINCIPALNAME()),
# MAGIC     "r", 'UserRegionMap'[region]
# MAGIC   )
# MAGIC ```
# MAGIC
# MAGIC ⚠️ RLS only restricts **Viewers**. Admin/Member/Contributor bypass.

# COMMAND ----------

# MAGIC %md
# MAGIC ## F — Workspace identity token from notebook

# COMMAND ----------

storage_token = notebookutils.credentials.getToken("https://storage.azure.com/")
# Token represents the workspace identity when run unattended (pipeline/SP).

# COMMAND ----------

# MAGIC %md
# MAGIC ## G — Service principal via MSAL (full Fabric scope)
# MAGIC
# MAGIC Use this when notebookutils' scoped tokens are insufficient (e.g.,
# MAGIC admin APIs from a pipeline-triggered run).

# COMMAND ----------

from msal import ConfidentialClientApplication
client_id     = "<sp-app-id>"
tenant_id     = "<tenant-id>"
client_secret = notebookutils.credentials.getSecret("https://kv.vault.azure.net/", "sp-secret")

app = ConfidentialClientApplication(
    client_id,
    authority=f"https://login.microsoftonline.com/{tenant_id}",
    client_credential=client_secret,
)
res = app.acquire_token_for_client(scopes=["https://api.fabric.microsoft.com/.default"])
fabric_full_scope_token = res["access_token"]

# COMMAND ----------

# MAGIC %md
# MAGIC ## H — Key Vault: get / put

# COMMAND ----------

api_key = notebookutils.credentials.getSecret("https://myvault.vault.azure.net/", "openai-key")
notebookutils.credentials.putSecret("https://myvault.vault.azure.net/", "demo-key", "value")

# COMMAND ----------

# MAGIC %md
# MAGIC ## I — Who am I?

# COMMAND ----------

ctx = notebookutils.runtime.context
print("workspace:", ctx.currentWorkspaceName, ctx.currentWorkspaceId)
# Inside Spark, the executing identity:
print(spark.sql("SELECT current_user() AS me").collect()[0]["me"])
