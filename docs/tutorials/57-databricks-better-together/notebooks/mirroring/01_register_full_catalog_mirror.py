# Databricks notebook source
# MAGIC %md
# MAGIC # Tutorial 57 — Mirror Pattern A: Full Databricks Catalog
# MAGIC
# MAGIC > **Where this runs:** **Fabric** notebook (not Databricks). Uses the
# MAGIC > Fabric REST API to provision a "Mirrored Azure Databricks Catalog"
# MAGIC > item that exposes every schema and every table from the Databricks
# MAGIC > UC catalog `better_together` as OneLake shortcuts.
# MAGIC > **Source of truth:** Microsoft Learn —
# MAGIC > [Mirrored Azure Databricks Unity Catalog item definition](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/mirrored-azuredatabricks-unitycatalog-definition)
# MAGIC > and [azure-databricks-tutorial](https://learn.microsoft.com/en-us/fabric/mirroring/azure-databricks-tutorial).
# MAGIC
# MAGIC ## What "Databricks mirroring" actually is in 2026
# MAGIC
# MAGIC Despite the name, Databricks mirroring in Fabric is **zero-copy**:
# MAGIC OneLake gets shortcuts to the Databricks-managed Delta files; nothing
# MAGIC is replicated. Background compute is free; only your reads against the
# MAGIC mirrored catalog consume CU. Source: [overview](https://learn.microsoft.com/en-us/fabric/mirroring/overview).
# MAGIC
# MAGIC There are **three configuration shapes** for the same item type — this
# MAGIC notebook covers shape #1 (full). See notebook 02 for inclusion and
# MAGIC exclusion lists, and 03 for how to query the result.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Prerequisites
# MAGIC
# MAGIC 1. The Databricks UC catalog `better_together` exists and is populated
# MAGIC    (run `notebooks/setup/00_create_unity_catalog.py` and
# MAGIC    `notebooks/setup/01_load_sample_data.py` first).
# MAGIC 2. On the Databricks metastore: **external data access is enabled** and
# MAGIC    the **SP we use here has `EXTERNAL USE SCHEMA`** on every schema
# MAGIC    we want to mirror.
# MAGIC    See [azure-databricks-security](https://learn.microsoft.com/en-us/fabric/mirroring/azure-databricks-security).
# MAGIC 3. The Fabric workspace identity has been registered as a trusted
# MAGIC    principal on the Databricks-managed ADLS account (this is the
# MAGIC    "trusted workspace access" pattern — required when ADLS is firewalled).

# COMMAND ----------

import json
import time

import requests

# Resolves to the workspace this notebook is running in.
WORKSPACE_ID = notebookutils.runtime.context.currentWorkspaceId

# An existing Fabric connection ID for the Databricks SPN. Create this once
# via the Fabric portal (New connection -> Azure Databricks) and store its ID
# in Key Vault, or read it back from a connection-management automation.
CONNECTION_ID = notebookutils.credentials.getSecret(
    "https://kv-btfabric-dev.vault.azure.net/",
    "fabric-databricks-connection-id",
)

DATABRICKS_WORKSPACE_URL = "https://adb-<workspace-id>.<n>.azuredatabricks.net"
DATABRICKS_CATALOG = "better_together"
ITEM_NAME = "MirrorDBX_FullCatalog"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Build the item definition (full catalog)
# MAGIC
# MAGIC In the **full** shape, `partialCatalog` is omitted entirely.
# MAGIC `automaticSync = true` propagates schema changes (table adds/drops,
# MAGIC column adds) without manual intervention.

# COMMAND ----------

definition = {
    "displayName": ITEM_NAME,
    "description": "Tutorial 57 — full mirror of better_together UC catalog.",
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
                        # No `partialCatalog` -> full catalog mirror.
                    },
                },
                "payloadType": "InlineJson",
            }
        ]
    },
}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Acquire a Fabric API token (uses the notebook's user / SP identity)

# COMMAND ----------

token = notebookutils.credentials.getToken("https://api.fabric.microsoft.com")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create the mirrored item
# MAGIC
# MAGIC Endpoint: `POST /v1/workspaces/{workspaceId}/mirroredAzureDatabricksCatalogs`
# MAGIC
# MAGIC Source: [item definition spec](https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/mirrored-azuredatabricks-unitycatalog-definition).

# COMMAND ----------

url = (
    f"https://api.fabric.microsoft.com/v1/workspaces/"
    f"{WORKSPACE_ID}/mirroredAzureDatabricksCatalogs"
)
resp = requests.post(url, headers=headers, data=json.dumps(definition), timeout=60)
print(f"HTTP {resp.status_code}")
print(resp.text[:2000])
resp.raise_for_status()

# Long-running operation pattern — poll the Location header until 200.
if resp.status_code == 202:
    op_url = resp.headers["Location"]
    print(f"Polling operation: {op_url}")
    while True:
        poll = requests.get(op_url, headers=headers, timeout=30)
        status = poll.json().get("status")
        print(f"  status={status}")
        if status in {"Succeeded", "Failed"}:
            break
        time.sleep(5)
    poll.raise_for_status()
    result = poll.json()
else:
    result = resp.json()

item_id = result.get("id") or result.get("itemId")
print(f"Created mirrored item id: {item_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validate
# MAGIC
# MAGIC The item is now visible at `Files/MirroredAzureDatabricksCatalog/...`
# MAGIC under the mirror item, and tables appear with the catalog's schema
# MAGIC structure preserved. Background sync is **already running** — schema
# MAGIC changes will appear within seconds; data is queried live via shortcut
# MAGIC so there's no replication delay.

# COMMAND ----------

# Confirm by listing items of this type
items_url = (
    f"https://api.fabric.microsoft.com/v1/workspaces/{WORKSPACE_ID}/items"
    f"?type=MirroredAzureDatabricksCatalog"
)
items = requests.get(items_url, headers=headers, timeout=30).json()
for it in items.get("value", []):
    print(f"  {it['displayName']:<30} id={it['id']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Heads-up — what UC RLS does NOT carry over
# MAGIC
# MAGIC > UC row filters / column masks defined on the Databricks side are
# MAGIC > **not** enforced through the mirror. You must re-author security in
# MAGIC > Fabric using **OneLake security** (RLS GA, CLS Preview April 2026)
# MAGIC > or via the SQL endpoint in **User identity mode**. See
# MAGIC > `../security/01_apply_onelake_security.py` and the defense-in-depth
# MAGIC > doc at `docs/best-practices/security/onelake-defense-in-depth.md`.

notebookutils.notebook.exit(f"mirror_item_id={item_id}")
