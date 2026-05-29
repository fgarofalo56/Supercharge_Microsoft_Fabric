---
hero: assets/heroes/reference.svg
hero_alt: Reference — My Resources
type: reference
---
# Resource Inventory Template

> Per-deployment reference sheet. Fill in your **own** Azure resource IDs locally so every tutorial pulls from one place instead of hunting through multiple portals.

!!! note "Third-party references — publicly sourced, good-faith comparison"
    This page references non-Microsoft products and services. That information is drawn from each vendor's **publicly available documentation** and is offered for honest, good-faith comparison only. This is a personal project written from a Microsoft Fabric and Azure perspective; it does **not** claim expertise in, or authority over, any third-party product, and nothing here is an official statement by, or endorsed by, those vendors. Capabilities, pricing, and features change often — always verify against the vendor's current official documentation. Where a third-party offering is the stronger choice, we say so plainly.

!!! warning "Do not commit real values to this file"
    The template below uses placeholders only. **Keep your real GUIDs, tenant IDs, subscription IDs, resource names, and managed-identity object IDs out of this file before committing.** Connection strings, access keys, SAS tokens, and any other secrets belong in Key Vault and should be referenced by **secret name only** from your notebooks and pipelines.

**Last updated:** _YYYY-MM-DD_

---

## Fabric Workspace

| Field | Value |
|---|---|
| Fabric tenant (Entra ID) | `<tenant-guid>` |
| Fabric capacity name | `<fabric-capacity-name>` |
| Fabric capacity resource ID | `/subscriptions/<sub-guid>/resourceGroups/<rg>/providers/Microsoft.Fabric/capacities/<name>` |
| Fabric capacity SKU | F64 |
| Workspace name | `<workspace-name>` |
| Workspace ID | `<workspace-guid>` |
| Workspace region | eastus2 |
| `lh_bronze` ID | `<lakehouse-guid>` |
| `lh_silver` ID | `<lakehouse-guid>` |
| `lh_gold` ID | `<lakehouse-guid>` |

---

## ADLS Gen2 Storage Account

Used by: Tutorial 00 Step 4 (shortcut), Tutorial 06 (pipelines), Tutorial 22 (networking).

| Field | Value |
|---|---|
| Subscription ID | `<sub-guid>` |
| Subscription name | `<sub-name>` |
| Resource group | `<rg-name>` |
| Storage account name | `<storage-account-name>` |
| DFS endpoint | `<storage>.dfs.core.windows.net` |
| Blob endpoint | `<storage>.blob.core.windows.net` |
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
| Subscription ID | `<sub-guid>` |
| Resource group | `<rg-name>` |
| Purview account name | `<purview-account>` |
| Atlas endpoint | `https://<purview-account>.purview.azure.com` |
| Scan endpoint | `https://<purview-account>.scan.purview.azure.com` |
| Managed Resource Group | `managed-rg-<purview-account>` (auto-created) |
| Public access | Enabled |

---

## Azure Key Vault

Used by: Tutorial 08 (mirroring), 11 (SAS), 12 (CI/CD), 14 (security).

| Field | Value |
|---|---|
| Subscription ID | `<sub-guid>` |
| Resource group | `<rg-name>` |
| Vault name | `<vault-name>` |
| Vault URI | `https://<vault-name>.vault.azure.net/` |
| Access model | RBAC |
| Soft delete | Enabled (should be) |
| Purge protection | Enabled |

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
| Subscription ID | `<sub-guid>` |
| Resource group | `<rg-name>` |
| Workspace name | `<log-analytics-name>` |
| Workspace ID (GUID) | `<workspace-guid>` |
| Workspace resource ID | `/subscriptions/<sub-guid>/resourceGroups/<rg>/providers/Microsoft.OperationalInsights/workspaces/<name>` |
| Region | eastus2 |
| Retention days | 30 |

---

## User-Assigned Managed Identity

Used by: Tutorial 14 (RBAC), 22 (networking auth), 23 (gateways).

| Field | Value |
|---|---|
| Subscription ID | `<sub-guid>` |
| Resource group | `<rg-name>` |
| Identity name | `<umi-name>` |
| Client ID | `<client-guid>` |
| Principal ID (Object ID) | `<object-guid>` |
| Resource ID | `/subscriptions/<sub-guid>/resourceGroups/<rg>/providers/Microsoft.ManagedIdentity/userAssignedIdentities/<name>` |

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
| Subscription ID | `<sub-guid>` |
| Resource group | `<rg-name>` |
| Namespace name | `<eh-namespace>` |
| Namespace FQDN | `<eh-namespace>.servicebus.windows.net` |
| Pricing tier | Standard |
| Throughput units / PUs | 1 |

### Event Hubs within the namespace

| Event Hub name | Purpose | Partitions | Retention (hrs) | Consumer groups |
|---|---|---|---|---|
| `slot-telemetry` | Slot machine events | 4 | 24 | `$Default`, `fabric-eventstream` |
| `player-activity` | Player loyalty / cage | 2 | 24 | `$Default` |
| `compliance` | CTR/SAR/W-2G filings | 2 | 168 | `$Default` |

> Connection strings live in Key Vault — reference by secret name, not value.

---

## Optional — Additional Azure Resources

Fill these in if/when relevant to your tutorials.

### VNet + Subnets (Tutorial 22)

| Field | Value |
|---|---|
| Subscription | `<sub-guid>` |
| Resource group | `<rg-name>` |
| VNet name | `<vnet-name>` |
| Address space | `10.0.0.0/16` |
| PE subnet name | `snet-pe` |
| PE subnet range | `10.0.1.0/24` |

### Source Systems (Tutorial 08 Mirroring, 10 Teradata, 24 Snowflake, 25 DB2)

| System | Hostname / Endpoint | Port | Auth | Secret in KV |
|---|---|---|---|---|
| SQL Server | `<server>.database.windows.net` | 1433 | Entra ID / SQL | `sql-server-connstr` |
| Snowflake | `<account>.snowflakecomputing.com` | 443 | Key pair / Password | `snowflake-password` |
| Teradata | `<tdhost>` | 1025 | LDAP | `teradata-password` |

---

## Cross-Subscription RBAC Checklist

If your resources span multiple subscriptions, verify the Fabric workspace identity (or your user account) has these roles before you start any tutorial that crosses a subscription boundary:

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
| 05 Direct Lake + PBI | `lh_gold` only |
| 06 Data Pipelines | ADLS (optional shortcut) + Fabric pipelines |
| 07 Governance | Purview + ADLS + `lh_*` |
| 08 Mirroring | Source DB (SQL / Cosmos / Snowflake) + Key Vault |
| 11 SAS | Key Vault (for SAS connection strings) |
| 12 CI/CD | Service principal + GitHub secrets + Key Vault |
| 14 Security | Key Vault + MI + Log Analytics |
| 17 Monitoring | Log Analytics + Fabric Capacity Metrics |
| 22 Networking | VNet + Private endpoints |
| 23 Gateways | On-prem SHIR + Key Vault |

---

!!! danger "Reminder"
    This file lives in the repo. **Fill in placeholder values with your own resources locally**, but **never paste real tenant GUIDs, subscription IDs, managed-identity object IDs, customer names, secrets, keys, or connection strings** here when committing back to a public branch. Those belong in Key Vault (or a private fork) and should be referenced by secret name only.
