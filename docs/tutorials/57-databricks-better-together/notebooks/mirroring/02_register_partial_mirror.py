# Databricks notebook source
# MAGIC %md
# MAGIC # Tutorial 57 — Mirror Patterns B & C: Partial Catalog (inclusion / exclusion)
# MAGIC
# MAGIC > **Where this runs:** Fabric notebook.
# MAGIC > **Source of truth:**
# MAGIC > [Mirrored Azure Databricks Unity Catalog item definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/mirrored-azuredatabricks-unitycatalog-definition).
# MAGIC
# MAGIC The mirror item supports a `partialCatalog` block with **exactly one of**:
# MAGIC
# MAGIC - `inclusionList` — only the schemas/tables listed are mirrored.
# MAGIC - `exclusionList` — everything **except** the listed schemas/tables
# MAGIC   is mirrored.
# MAGIC
# MAGIC The two demos here use **the same catalog** as notebook 01 so you can
# MAGIC create three mirror items in the same workspace and compare them
# MAGIC side-by-side.

# COMMAND ----------

import json
import time
from typing import Any

import requests

WORKSPACE_ID = notebookutils.runtime.context.currentWorkspaceId
CONNECTION_ID = notebookutils.credentials.getSecret(
    "https://kv-btfabric-dev.vault.azure.net/",
    "fabric-databricks-connection-id",
)
DATABRICKS_WORKSPACE_URL = "https://adb-<workspace-id>.<n>.azuredatabricks.net"
DATABRICKS_CATALOG = "better_together"

token = notebookutils.credentials.getToken("https://api.fabric.microsoft.com")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
api_url = (
    f"https://api.fabric.microsoft.com/v1/workspaces/"
    f"{WORKSPACE_ID}/mirroredAzureDatabricksCatalogs"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Helper — build & POST a mirrored-catalog definition

# COMMAND ----------

def create_mirror(display_name: str, partial_catalog: dict[str, Any]) -> str:
    definition = {
        "displayName": display_name,
        "definition": {
            "parts": [
                {
                    "path": "mirroring.json",
                    "payload": {
                        "source": {
                            "type": "AzureDatabricks",
                            "azureDatabricks": {
                                "workspaceUrl": DATABRICKS_WORKSPACE_URL,
                                "catalogName": DATABRICKS_CATALOG,
                            },
                        },
                        "connection": {"connectionId": CONNECTION_ID},
                        "mirroringConfiguration": {
                            "automaticSync": True,
                            "partialCatalog": partial_catalog,
                        },
                    },
                    "payloadType": "InlineJson",
                }
            ]
        },
    }
    r = requests.post(api_url, headers=headers, data=json.dumps(definition), timeout=60)
    print(f"[{display_name}] HTTP {r.status_code}")
    if r.status_code == 202:
        op_url = r.headers["Location"]
        while True:
            poll = requests.get(op_url, headers=headers, timeout=30).json()
            if poll.get("status") in {"Succeeded", "Failed"}:
                break
            time.sleep(5)
        result = poll
    else:
        r.raise_for_status()
        result = r.json()
    item_id = result.get("id") or result.get("itemId")
    print(f"[{display_name}] item id={item_id}")
    return item_id

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pattern B — Inclusion list
# MAGIC
# MAGIC Only mirror the **secure views**. This is the recommended posture when
# MAGIC the source catalog also holds tables you specifically do NOT want
# MAGIC visible in Fabric (e.g., raw staging tables, dev sandboxes, vendor
# MAGIC PII you've not yet masked).

# COMMAND ----------

include_id = create_mirror(
    "MirrorDBX_Inclusion",
    {
        "inclusionList": {
            "schemas": [
                {
                    "name": "retail_secure",
                    "tables": [
                        {"name": "orders_by_region"},
                        {"name": "audit_revenue_summary"},
                    ],
                }
            ]
        }
    },
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pattern C — Exclusion list
# MAGIC
# MAGIC Mirror everything **except** `retail_raw.customers` (which holds PII
# MAGIC the Fabric workspace shouldn't see — e.g., the email column we
# MAGIC deliberately stripped from the Gold dim_customer).

# COMMAND ----------

exclude_id = create_mirror(
    "MirrorDBX_Exclusion",
    {
        "exclusionList": {
            "schemas": [
                {
                    "name": "retail_raw",
                    "tables": [{"name": "customers"}],
                }
            ]
        }
    },
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## When to choose which
# MAGIC
# MAGIC | Posture | Use |
# MAGIC |---|---|
# MAGIC | **Full** | Greenfield demo, dev workspaces, "expose all the things". |
# MAGIC | **Inclusion** | Default-deny security posture — easier to reason about ("I know exactly what's in the mirror"). |
# MAGIC | **Exclusion** | When the source catalog is mostly safe and you have a small number of carve-outs. |
# MAGIC
# MAGIC 🚩 **Caveat from MS Learn:** Once a schema/table is added to either
# MAGIC list, you **cannot** rename it (see
# MAGIC [limitations](https://learn.microsoft.com/en-us/fabric/mirroring/azure-databricks-limitations)).

notebookutils.notebook.exit(
    f"inclusion={include_id}|exclusion={exclude_id}"
)
