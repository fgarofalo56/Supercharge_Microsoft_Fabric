# My Existing Azure Resources

> Personal reference sheet. Fill in the IDs for your existing Azure resources so every tutorial can pull from one place instead of hunting through multiple portals.

> ⚠️ **Do not commit real secrets** (connection strings, access keys, SAS tokens) to this file. Store those in the listed Key Vault and reference them by secret name only.

**Last updated:** _YYYY-MM-DD_

---

## Fabric Workspace

| Field | Value |
|---|---|
| Fabric tenant (Entra ID) | d1fc0498-f208-4b49-8376-beb9293acdf6 |
| Fabric capacity name | fabriccaplimitlessdatadev |
| Fabric capacity resource ID | `/subscriptions/363ef5d1-0e77-4594-a530-f51af23dbf8c/resourceGroups/fabric-dev/providers/Microsoft.Fabric/capacities/fabriccaplimitlessdatadev` |
| Fabric capacity SKU | F64 |
| Workspace name | casino-fabric-poc |
| Workspace ID | `7899f58d-d19f-4e9d-8370-b88621aad31e` |
| Workspace region | eastus2 |
| lh_bronze ID | `2ab24ff1-5b33-4dd5-907c-9f0d4668dd8e` |
| lh_silver ID | `5f65ac64-9309-4507-a768-bcd8fb2168f1` |
| lh_gold ID | `8fa85e0d-d57d-42f2-9830-da2e014f9762` |

---

## ADLS Gen2 Storage Account

Used by: Tutorial 00 Step 4 (shortcut), Tutorial 06 (pipelines), Tutorial 22 (networking).

| Field | Value |
|---|---|
| Subscription ID | 363ef5d1-0e77-4594-a530-f51af23dbf8c |
| Subscription name | FedCiv ATU FFL - DLZ |
| Resource group |rg-dlz-dev-storage-eastus2 |
| Storage account name | rg-dlz-dev-storage-eastus2 |
| DFS endpoint | `rg-dlz-dev-storage-eastus2.dfs.core.windows.net` |
| Blob endpoint | `rg-dlz-dev-storage-eastus2.blob.core.windows.net` |
| Primary container(s) | landing, bronze, silver, gold |
| Access method | Managed Identity / SAS / Account Key (pick one) |
| Firewall | Public / Private endpoint / VNet-restricted |

**ABFSS path template for OneLake shortcuts:**

```
abfss://<container>@<storage>.dfs.core.windows.net/<path>
```

---

## Microsoft Purview

Used by: Tutorial 07 (governance, catalog, lineage).

| Field | Value |
|---|---|
| Subscription ID | e093f4fd-5047-4ee4-968d-a56942c665f3 |
| Resource group | rg-dmlz-dev-governance-eastus |
| Purview account name | dmlz-dev-purview-eastus |
| Atlas endpoint | `https://dmlz-dev-purview-eastus.purview.azure.com` |
| Scan endpoint | `https://dmlz-dev-purview-eastus.scan.purview.azure.com` |
| Managed Resource Group | managed-rg-dmlz-dev-purview-eastus (auto-created) |
| Public access | Enabled |

---

## Azure Key Vault

Used by: Tutorial 08 (mirroring), 11 (SAS), 12 (CI/CD), 14 (security).

| Field | Value |
|---|---|
| Subscription ID | e093f4fd-5047-4ee4-968d-a56942c665f3 |
| Resource group | rg-dmlz-dev-governance-eastus |
| Vault name | dmlzvault |
| Vault URI | `https://dmlzvault.vault.azure.net/` |
| Access model | RBAC  |
| Soft delete | Enabled (should be) |
| Purge protection | Disabled |

**Secret name conventions (suggested — fill in what you use):**

| Purpose | Secret name |
|---|---|
| SQL Server connection string | `sql-casino-connstr` |
| Snowflake password | `snowflake-password` |
| Event Hub SAS key | `eventhub-sas-key` |
| Service principal secret | `sp-fabric-poc-secret` |

---

## Log Analytics Workspace

Used by: Tutorial 14 (security audit logs), 17 (monitoring + diagnostics).

| Field | Value |
|---|---|
| Subscription ID | a60a2fdd-c133-4845-9beb-31f470bf3ef5 |
| Resource group | rg-alz-dev-logging |
| Workspace name | alz-dev-dataObservability-logAnalyticsWorkspace |
| Workspace ID (GUID) | 896be601-ef0c-4255-a42b-f6d5a551e7f4 |
| Workspace resource ID | `/subscriptions/a60a2fdd-c133-4845-9beb-31f470bf3ef5/resourceGroups/rg-alz-dev-logging/providers/Microsoft.OperationalInsights/workspaces/alz-dev-dataObservability-logAnalyticsWorkspace` |
| Region | eastus2 |
| Retention days | 30 |

---

## User-Assigned Managed Identity

Used by: Tutorial 14 (RBAC), 22 (networking auth), 23 (gateways).

| Field | Value |
|---|---|
| Subscription ID | e093f4fd-5047-4ee4-968d-a56942c665f3 |
| Resource group | rg-dmlz-dev-governance-eastus |
| Identity name | admla-umi-dev |
| Client ID | b52d68ef-0b7d-418d-a749-ad5d8bcf9b8d |
| Principal ID (Object ID) | cf8ed72e-6643-485f-8ddb-6db3af9f42a2 |
| Resource ID | `/subscriptions/e093f4fd-5047-4ee4-968d-a56942c665f3/resourcegroups/rg-dmlz-dev-governance-eastus/providers/Microsoft.ManagedIdentity/userAssignedIdentities/admla-umi-dev` |

**Assigned roles (document for each target resource):**

| On resource | Role |
|---|---|
| ADLS storage account | Storage Blob Data Contributor |
| Key Vault | Key Vault Secrets User |
| Purview | Purview Data Reader / Curator |
| Log Analytics | Log Analytics Contributor |

---

## Event Hub Namespace + Event Hubs

Used by: Tutorial 04 (real-time analytics), 26 (multi-source streaming).

| Field | Value |
|---|---|
| Subscription ID | 363ef5d1-0e77-4594-a530-f51af23dbf8c |
| Resource group | rg-dlz-streaming-dev |
| Namespace name | dlz-streaming-dev |
| Namespace FQDN | `dlz-streaming-dev.servicebus.windows.net` |
| Pricing tier | Standard |
| Throughput units / PUs | 1 |

### Event Hubs within the namespace

| Event Hub name | Purpose | Partitions | Retention (hrs) | Consumer groups |
|---|---|---|---|---|
| _slot-telemetry_ | Slot machine events | 4 | 24 | `$Default`, `fabric-eventstream` |
| _player-activity_ | Player loyalty / cage | 2 | 24 | `$Default` |
| _compliance_ | CTR/SAR/W-2G filings | 2 | 168 | `$Default` |

> Connection strings live in Key Vault — reference by secret name, not value.

---

## Optional — Additional Azure Resources

Fill these in if/when relevant to your tutorials.

### VNet + Subnets (Tutorial 22)

| Field | Value |
|---|---|
| Subscription | _sub-guid_ |
| Resource group | _rg-name_ |
| VNet name | _vnet-xxxxxxx_ |
| Address space | _10.0.0.0/16_ |
| PE subnet name | _snet-pe_ |
| PE subnet range | _10.0.1.0/24_ |

### Source Systems (Tutorial 08 Mirroring, 10 Teradata, 24 Snowflake, 25 DB2)

| System | Hostname / Endpoint | Port | Auth | Secret in KV |
|---|---|---|---|---|
| SQL Server | _server.database.windows.net_ | 1433 | Entra ID / SQL | `sql-server-connstr` |
| Snowflake | _account.snowflakecomputing.com_ | 443 | Key pair / Password | `snowflake-password` |
| Teradata | _tdhost.example.com_ | 1025 | LDAP | `teradata-password` |

---

## Cross-Subscription RBAC Checklist

Since your resources span 3 subscriptions, verify the Fabric workspace identity (or your user account) has these roles before you hit Tutorial X:

- [ ] ADLS storage account → **Storage Blob Data Contributor**
- [ ] Key Vault → **Key Vault Secrets User** (or Secrets Officer if you need to write)
- [ ] Purview → **Purview Data Curator** (workspace level) + **Reader** (subscription level)
- [ ] Log Analytics → **Log Analytics Contributor**
- [ ] Event Hub namespace → **Azure Event Hubs Data Receiver** (for Fabric Eventstream) + **Data Sender** (if publishing)

## Tutorial Resource Map

Quick lookup — which resources each tutorial needs from above:

| Tutorial | Resources Needed |
|---|---|
| 04 Real-Time | Event Hub namespace + Fabric workspace (Eventstream, Eventhouse) |
| 05 Direct Lake + PBI | lh_gold only |
| 06 Data Pipelines | ADLS (optional shortcut) + Fabric pipelines |
| 07 Governance | Purview + ADLS + lh_* |
| 08 Mirroring | Source DB (SQL/Cosmos/Snowflake) + Key Vault |
| 11 SAS | Key Vault (for SAS connection strings) |
| 12 CI/CD | Service principal + GitHub secrets + Key Vault |
| 14 Security | Key Vault + MI + Log Analytics |
| 17 Monitoring | Log Analytics + Fabric Capacity Metrics |
| 22 Networking | VNet + Private endpoints |
| 23 Gateways | On-prem SHIR + Key Vault |

---

> 🔒 **Reminder:** This file lives in the repo. **Fill in names and resource IDs** (non-sensitive), but **never paste secrets, keys, or connection strings** here. Those belong in Key Vault and referenced by secret name only.
