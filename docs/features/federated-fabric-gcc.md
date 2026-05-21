# Federated Fabric for GCC — Using Microsoft Fabric in Commercial from Government Cloud

<div align="center" markdown>

**Bridge the GCC Gap — A Practical Guide to Federated Fabric Architecture for Government Customers**

![Category](https://img.shields.io/badge/Category-Government_Cloud-purple?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-April_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-04-29` | **Version:** 1.0.0

---

## Overview

As of April 2026, **Microsoft Fabric is not available in Office 365 GCC, GCC High, or DoD environments**. Microsoft has not published a firm GA date, though industry sources expect Fabric to land in Azure Government by late 2026. This leaves government organizations — state, local, tribal, and federal agencies in GCC — without access to Fabric's unified analytics platform while their commercial counterparts adopt it rapidly.

This document provides a comprehensive guide for GCC customers who want to use Microsoft Fabric in a Commercial tenant today, following a **Federated Fabric** architecture. This approach maintains a government identity boundary in the GCC tenant while running analytics workloads in a Commercial Fabric environment. It covers data classification requirements, cross-cloud identity configuration, step-by-step setup, security controls, gotchas, and a migration path for when Fabric eventually arrives in GCC.

### Who This Is For

| Audience | Relevance |
|----------|-----------|
| **GCC customers (State/Local/Tribal)** | Primary — most common candidates for federated approach |
| **GCC customers (Federal civilian)** | Case-by-case — depends on data sensitivity and ATO requirements |
| **GCC High / DoD customers** | Very limited applicability — CUI/ITAR data cannot move to Commercial |
| **IT architects and security officers** | Architecture decisions, compliance review |
| **Data engineers and analysts** | Implementation and day-to-day operations |

### Key Principle

> **Non-sensitive, publicly releasable, or de-identified data** can be processed in Commercial Fabric. **CUI, PII, PHI, CJIS, ITAR, or export-controlled data** must remain in the GCC (or GCC High/DoD) boundary and cannot be placed in Commercial Fabric.

---

## Current State: Fabric and GCC

### What IS Available in GCC Today

| Service | GCC | GCC High | DoD |
|---------|-----|----------|-----|
| Power BI (via Fabric portal) | Yes | Yes | Yes |
| Power BI Embedded | Yes | Yes | Yes |
| Dataflows Gen1 | Yes | Yes | Limited |
| Paginated Reports | Yes | Yes | Yes |
| Azure Synapse Analytics | Yes (Azure Gov) | Yes (Azure Gov) | Yes (Azure Gov) |
| Azure Data Factory | Yes (Azure Gov) | Yes (Azure Gov) | Yes (Azure Gov) |
| Azure Databricks | Yes (Azure Gov) | Yes (Azure Gov) | Limited |

### What IS NOT Available in GCC

| Service | Status |
|---------|--------|
| Microsoft Fabric (full platform) | Not available |
| OneLake | Not available |
| Lakehouse | Not available |
| Warehouse (Fabric) | Not available |
| Data Engineering (Spark in Fabric) | Not available |
| Data Science (Fabric) | Not available |
| Real-Time Intelligence (Eventstreams, Eventhouse) | Not available |
| Data Activator | Not available |
| Fabric Copilot / Fabric IQ | Not available |
| Direct Lake connectivity | Not available |
| OneLake Shortcuts | Not available |
| External Data Sharing | Not available |
| Fabric Pipelines | Not available |

### Expected Timeline

| Milestone | Expected Date | Source |
|-----------|---------------|--------|
| Fabric GA in Commercial | November 2023 (completed) | Microsoft Ignite 2023 |
| CMK support (Commercial) | 2025 (completed) | Fabric roadmap |
| Private Link / Block Public Access (Commercial) | 2025 (completed) | Fabric roadmap |
| Fabric in Azure Government | Late 2026 (estimated) | Industry analyst reports, Microsoft rep conversations |
| Fabric in GCC High / DoD | Unknown / TBD | No public timeline |

---

## Understanding the Cloud Boundaries

Before designing a federated architecture, it is critical to understand how Microsoft's cloud boundaries work.

### Microsoft Cloud Architecture

```
+-------------------------------------------------------------+
|                    COMMERCIAL CLOUD                           |
|  Azure Commercial  |  Microsoft 365 Commercial  |  Fabric   |
|  (public regions)  |  (global tenant)           |  (GA)     |
+-------------------------------------------------------------+
         |                        |
         | Cross-Cloud B2B       | (not same cloud)
         | (Entra ID)            |
         v                        v
+-------------------------------------------------------------+
|                   AZURE GOVERNMENT                           |
|  Azure Gov         |  Office 365 GCC           |  No Fabric |
|  (USGov regions)   |  FedRAMP Moderate         |            |
+-------------------------------------------------------------+
|  Azure Gov         |  Office 365 GCC High      |  No Fabric |
|  (USGov regions)   |  FedRAMP High / IL4       |            |
+-------------------------------------------------------------+
|  Azure Gov         |  Office 365 DoD           |  No Fabric |
|  (USDoD regions)   |  FedRAMP High / IL5       |            |
+-------------------------------------------------------------+
```

### Key Facts About Cloud Boundaries

1. **GCC runs on Commercial Azure infrastructure** (not Azure Government) but with FedRAMP Moderate-equivalent controls and a compliance boundary enforced at the Microsoft 365 service layer.

2. **GCC High and DoD run on Azure Government infrastructure** with strict data sovereignty, FedRAMP High authorization, and screened US personnel.

3. **Cross-cloud B2B collaboration** (Commercial <-> Azure Government) is supported via Microsoft Entra cross-cloud settings. This enables guest access between tenants in different clouds.

4. **Fabric is a Commercial-only service** as of April 2026. It runs in Azure Commercial regions with Commercial Entra ID authentication.

5. **GCC Entra ID tenants are separate** from Commercial Entra ID tenants. A GCC user's identity lives in the Azure Government cloud instance of Entra ID.

---

## Federated Fabric Architecture

The Federated Fabric pattern uses a **dual-tenant architecture**: the organization maintains its GCC tenant for regulated workloads (email, Teams, SharePoint, Power BI GCC) and establishes a separate Commercial tenant specifically for Fabric analytics workloads on non-sensitive data.

### Architecture Diagram

```
+------------------------------------------+     +------------------------------------------+
|          GCC TENANT                      |     |       COMMERCIAL TENANT                  |
|  (Primary Identity & Collaboration)      |     |  (Analytics / Fabric Workloads)           |
|                                          |     |                                          |
|  +----------------+  +----------------+ |     |  +----------------+  +----------------+  |
|  | Office 365 GCC |  | Power BI GCC   | |     |  | Microsoft      |  | Microsoft      |  |
|  | (Email, Teams, |  | (Regulated BI  | |     |  | Fabric         |  | Entra ID       |  |
|  |  SharePoint)   |  |  dashboards)   | |     |  | (OneLake,      |  | (Commercial)   |  |
|  +----------------+  +----------------+ |     |  |  Lakehouse,    |  +-------+--------+  |
|                                          |     |  |  Warehouse,    |          |           |
|  +----------------+  +----------------+ |     |  |  Spark, RTI,   |          |           |
|  | Azure Gov      |  | Entra ID       | |     |  |  Pipelines)    |          |           |
|  | (Azure Svcs,   |  | (Gov Cloud)    | |     |  +-------+--------+          |           |
|  |  ADLS Gen2,    |  +-------+--------+ |     |          |                    |           |
|  |  Synapse, ADF) |          |           |     |  +-------+--------+          |           |
|  +-------+--------+          |           |     |  | ADLS Gen2      |          |           |
|          |                   |           |     |  | (Commercial)   |          |           |
|          |                   |           |     |  | Landing Zone   |          |           |
|          |                   |           |     |  +-------+--------+          |           |
+----------+-------------------+-----------+     +----------+-------------------+-----------+
           |                   |                            |                    |
           |      Cross-Cloud B2B (Entra)                   |                    |
           |      <----------------------------------->     |                    |
           |                                                |                    |
           |         Data Flow (non-sensitive only)         |                    |
           +--------- De-identified / Public Data --------->+                    |
                      (via ADLS, API, or Export)
```

### Core Principles

1. **Identity lives in GCC** — Users authenticate against their GCC Entra ID. They access the Commercial Fabric tenant as B2B guest users.

2. **Data classification drives placement** — Only non-sensitive, de-identified, or publicly releasable data moves to Commercial Fabric. Regulated data stays in GCC.

3. **Governance is dual-layered** — GCC tenant enforces government compliance policies. Commercial tenant enforces Fabric-specific data governance (Purview, sensitivity labels, workspace access).

4. **Network boundaries are explicit** — Data transfer from GCC/Azure Gov to Commercial is intentional, audited, and controlled via Azure networking or application-layer exports.

5. **Migration-ready** — When Fabric lands in GCC, workloads can be migrated from Commercial to GCC Fabric without redesigning the medallion architecture.

---

## Data Classification: What Can Leave GCC

This is the most critical decision in a Federated Fabric deployment. Getting this wrong creates compliance violations.

### Data Classification Matrix

| Classification | Can Move to Commercial Fabric? | Examples |
|---------------|-------------------------------|----------|
| **Public / Open Data** | YES | Published statistics, press releases, census data, weather data, open datasets |
| **De-identified / Anonymized Data** | YES (with review) | Aggregated metrics, anonymized analytics, trend data without PII |
| **For Official Use Only (FOUO)** | CASE-BY-CASE | Depends on agency policy and data content; often yes if no PII/CUI |
| **Controlled Unclassified Information (CUI)** | NO | Any data marked CUI per NIST SP 800-171 |
| **Personally Identifiable Information (PII)** | NO | SSN, names + addresses, biometric data |
| **Protected Health Information (PHI)** | NO | HIPAA-covered health records |
| **Criminal Justice Information (CJI)** | NO | FBI CJIS data, law enforcement records |
| **ITAR / Export Controlled** | NO | Defense articles, technical data |
| **Tax Return Information (FTI)** | NO | IRS safeguarding requirements |
| **Law Enforcement Sensitive (LES)** | NO | Investigative data |

### Decision Flowchart

```
Start: "Should this data go to Commercial Fabric?"
  |
  +-- Is the data classified as CUI, PII, PHI, CJI, ITAR, FTI, or LES?
  |     |
  |     +-- YES --> STOP. Data MUST stay in GCC/GCC High boundary.
  |     |           Use Power BI GCC or Azure Gov services instead.
  |     |
  |     +-- NO --> Continue
  |
  +-- Is the data publicly available or already published?
  |     |
  |     +-- YES --> PROCEED. Safe for Commercial Fabric.
  |     |
  |     +-- NO --> Continue
  |
  +-- Can the data be de-identified or aggregated before transfer?
  |     |
  |     +-- YES --> De-identify FIRST, then proceed to Commercial.
  |     |           Document the de-identification process.
  |     |
  |     +-- NO --> Continue
  |
  +-- Does your agency ATO or ISSO allow this data outside the GCC boundary?
        |
        +-- YES --> PROCEED with documented approval.
        |
        +-- NO --> STOP. Data stays in GCC.
```

---

## Prerequisites and Requirements

### Organizational Prerequisites

| Requirement | Detail |
|-------------|--------|
| **Data classification review** | Complete review of all datasets intended for Commercial Fabric. Document classification for each. |
| **ISSO / Security Officer approval** | Written authorization to process non-sensitive data in Commercial cloud |
| **ATO consideration** | If applicable, update System Security Plan (SSP) to document the Commercial tenant boundary |
| **Licensing budget** | Separate Microsoft 365 and Fabric capacity licenses for the Commercial tenant |
| **Entra admin access** | Security Administrator role in BOTH GCC and Commercial tenants |
| **Fabric admin access** | Fabric Administrator role in the Commercial tenant |
| **Network connectivity** | Ability to transfer data between Azure Gov and Azure Commercial (or equivalent) |

### Technical Prerequisites

| Component | Required | Notes |
|-----------|----------|-------|
| **Commercial Entra ID tenant** | Yes | Separate tenant from GCC |
| **Fabric capacity (F SKU)** | Yes | F64 minimum recommended for production |
| **Azure subscription (Commercial)** | Yes | For ADLS Gen2 landing zone, Private Link, networking |
| **Azure subscription (Gov)** | Conditional | If using ADLS Gen2 bridge pattern |
| **Conditional Access policies** | Yes | MFA enforcement for cross-cloud guests |
| **Microsoft Purview** | Recommended | Data governance in Commercial tenant |
| **VPN or ExpressRoute** | Optional | For Private Link scenarios |

### Licensing Requirements

| License | Where | Purpose |
|---------|-------|---------|
| Office 365 GCC (E3/E5) | GCC Tenant | Primary identity and collaboration |
| Power BI Pro/Premium Per User | GCC Tenant | Regulated BI workloads |
| Microsoft 365 E3/E5 (Commercial) | Commercial Tenant | Identity foundation for Fabric |
| Microsoft Fabric F64+ | Commercial Tenant | Fabric capacity |
| Entra ID P1/P2 | Both Tenants | Cross-cloud B2B, Conditional Access |
| Microsoft Purview | Commercial Tenant | Data governance (recommended) |

> **Cost consideration:** You will pay for licensing in both tenants. GCC licensing cannot be applied to Commercial services and vice versa. Budget for dual licensing early.

---

## Step-by-Step: Setting Up Federated Fabric

### Phase 1: Establish a Commercial Tenant

**Goal:** Create or identify a Commercial Entra ID tenant to host Fabric workloads.

**Step 1.1 — Create a Commercial Entra ID Tenant**

If your organization does not already have a Commercial Microsoft 365 tenant:

1. Navigate to [https://admin.microsoft.com](https://admin.microsoft.com)
2. Sign up for a Microsoft 365 Business or Enterprise trial
3. Use a domain distinct from your GCC tenant (e.g., `agencyanalytics.onmicrosoft.com`)
4. Complete tenant creation and verify your custom domain

If your organization already has a Commercial tenant (common for organizations that migrated to GCC from Commercial), you can reuse it.

**Step 1.2 — Assign Licensing**

1. Purchase Microsoft 365 E3 or E5 licenses for the Commercial tenant
2. Purchase Microsoft Fabric capacity (F64 recommended for production, F2 for testing)
3. Assign licenses to admin accounts that will configure Fabric

**Step 1.3 — Configure Tenant Security Baseline**

In the Commercial tenant:

```
1. Enable Security Defaults or configure Conditional Access
2. Enforce MFA for all users (especially admins and guest users)
3. Configure Entra ID Protection (P2) for risk-based policies
4. Set up audit logging and diagnostic settings
5. Configure admin consent workflow for applications
```

---

### Phase 2: Configure Cross-Cloud B2B in Entra ID

**Goal:** Enable GCC users to access the Commercial Fabric tenant as B2B guest users.

**Step 2.1 — Enable Cross-Cloud Settings (Commercial Tenant)**

1. Sign in to [https://entra.microsoft.com](https://entra.microsoft.com) with a **Security Administrator** account in the Commercial tenant
2. Navigate to **Entra ID** > **External Identities** > **Cross-tenant access settings**
3. Select **Microsoft cloud settings**
4. Check the box for **Microsoft Azure Government**
5. Save

**Step 2.2 — Add the GCC Tenant to Organizational Settings (Commercial Tenant)**

1. In Cross-tenant access settings, select **Organizational settings**
2. Click **Add organization**
3. Enter the **Tenant ID** of your GCC tenant (domain name lookup does not work cross-cloud)
4. Select the organization and click **Add**
5. Configure inbound access settings:
   - B2B collaboration: **Allow** (for specific users/groups or all)
   - Applications: Specify Fabric-related apps or allow all
6. Configure outbound access: Typically restrict or block (your Commercial users don't need to access GCC resources)

> **Finding your GCC Tenant ID:** In the GCC tenant's Entra admin center, go to **Entra ID** > **Overview**. The Tenant ID is displayed on the overview page.

**Step 2.3 — Enable Cross-Cloud Settings (GCC Tenant)**

1. Sign in to the Entra admin center for the GCC tenant
2. Navigate to **Entra ID** > **External Identities** > **Cross-tenant access settings**
3. Select **Microsoft cloud settings**
4. Check the box for **Microsoft Azure Commercial**
5. Save

**Step 2.4 — Add the Commercial Tenant to Organizational Settings (GCC Tenant)**

1. In Cross-tenant access settings, select **Organizational settings**
2. Click **Add organization**
3. Enter the **Tenant ID** of your Commercial tenant
4. Configure outbound access settings:
   - B2B collaboration: **Allow** (for the specific users/groups who need Fabric access)
   - Applications: Allow Microsoft Fabric app ID or all
5. Configure inbound access: Typically restrict (Commercial users don't need to access GCC resources)

**Step 2.5 — Invite GCC Users to Commercial Tenant**

1. In the Commercial tenant, go to **Entra ID** > **Users** > **New user** > **Invite external user**
2. Enter the GCC user's **UPN** (email as sign-in is not supported cross-cloud)
3. The user receives an invitation and redeems it using their GCC credentials
4. Assign the user to appropriate Fabric workspace roles

**Step 2.6 — Configure Conditional Access for Guests (Commercial Tenant)**

Create a Conditional Access policy in the Commercial tenant:

```
Policy Name: "Require MFA for Cross-Cloud Guests - Fabric"
Users: Guest and External Users → B2B collaboration guest users
Cloud Apps: Microsoft Fabric, Power BI Service
Grant: Require MFA
Session: Sign-in frequency = 4 hours (recommended)
```

Optionally, configure trust settings to accept MFA claims from the GCC tenant (reduces double-MFA prompts):

1. In Cross-tenant access settings > Organizational settings
2. Select your GCC tenant's entry
3. Edit **Trust settings**
4. Check **Trust multi-factor authentication from Microsoft Entra tenants**

---

### Phase 3: Provision Fabric Capacity and Workspaces

**Goal:** Set up the Fabric environment in the Commercial tenant.

**Step 3.1 — Purchase and Configure Fabric Capacity**

1. In the Azure portal (Commercial), create a **Microsoft Fabric** capacity:
   - Resource group: `rg-fabric-gov-analytics`
   - Region: `East US` or `East US 2` (closest to Azure Gov regions)
   - SKU: F64 (production) or F2 (testing/POC)
   - Administrator: Assign your Commercial admin account

2. In the Fabric Admin Portal ([https://app.fabric.microsoft.com](https://app.fabric.microsoft.com)):
   - Navigate to **Admin portal** > **Capacity settings**
   - Verify the capacity appears and is active

**Step 3.2 — Create Workspaces**

Create workspaces following a governance structure:

```
Workspace Naming Convention:
  ws-gov-[agency]-[environment]-[domain]

Examples:
  ws-gov-analytics-prod-public-data
  ws-gov-analytics-dev-sandbox
  ws-gov-analytics-prod-open-data
  ws-gov-analytics-prod-performance-metrics
```

For each workspace:
1. Navigate to Fabric portal > **Workspaces** > **New workspace**
2. Name the workspace following the convention above
3. Assign to the Fabric capacity
4. Set workspace access:
   - **Admin**: Fabric admins (Commercial accounts)
   - **Member**: GCC guest users who need to create/edit content
   - **Contributor**: GCC guest users who need to run notebooks/queries
   - **Viewer**: GCC guest users who only consume reports

**Step 3.3 — Enable Guest Access in Fabric Tenant Settings**

In the Fabric Admin Portal:

1. Go to **Tenant settings**
2. Enable **Guest users can access Microsoft Fabric** — set to Enabled
3. Enable **Users can invite guest users to collaborate through item sharing and permissions** — set to Enabled (restrict to security group of authorized inviters)
4. Configure **External data sharing** settings if needed

**Step 3.4 — Create Lakehouses and Warehouses**

In each workspace, create the core Fabric items:

1. **Lakehouse** for raw/bronze data: `lh_gov_bronze`
2. **Lakehouse** for transformed/silver data: `lh_gov_silver`
3. **Lakehouse** for gold/aggregated data: `lh_gov_gold`
4. **Warehouse** for SQL-based analytics (optional): `wh_gov_analytics`

---

### Phase 4: Bridge Data from GCC to Commercial Fabric

**Goal:** Move non-sensitive data from GCC environment to Commercial Fabric.

This is the most architecturally significant phase. Choose one of the following patterns based on your requirements.

#### Option A: ADLS Gen2 Bridge Pattern (Recommended)

This uses an Azure Data Lake Storage Gen2 account in Azure Commercial as a landing zone.

**Step 4A.1 — Create ADLS Gen2 Landing Zone**

In Azure Commercial subscription:

```bash
# Create resource group
az group create \
  --name rg-gov-data-landing \
  --location eastus2

# Create storage account with hierarchical namespace (ADLS Gen2)
az storage account create \
  --name stgovdatalanding \
  --resource-group rg-gov-data-landing \
  --location eastus2 \
  --sku Standard_LRS \
  --kind StorageV2 \
  --hns true \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false

# Create containers
az storage fs create \
  --name landing-bronze \
  --account-name stgovdatalanding

az storage fs create \
  --name landing-silver \
  --account-name stgovdatalanding
```

**Step 4A.2 — Export Data from GCC/Azure Gov**

In Azure Government, use Azure Data Factory or Synapse Pipelines to export non-sensitive data:

```json
{
  "name": "ExportToCommercialLanding",
  "type": "Copy",
  "source": {
    "type": "AzureDataLakeStore",
    "description": "Source: ADLS Gen2 in Azure Gov"
  },
  "sink": {
    "type": "AzureDataLakeStore",
    "description": "Sink: ADLS Gen2 in Azure Commercial",
    "connectionString": "https://stgovdatalanding.dfs.core.windows.net"
  },
  "note": "Use service principal or SAS token for cross-cloud auth"
}
```

Cross-cloud considerations:
- Azure Data Factory in Azure Gov CAN connect to Azure Commercial storage using service principal or SAS token
- Network traffic goes over Microsoft backbone if using service endpoints
- Consider ExpressRoute or VPN for additional network security

**Step 4A.3 — Create OneLake Shortcut to ADLS Gen2**

In Fabric Lakehouse (`lh_gov_bronze`):

1. Open the Lakehouse in Fabric portal
2. In Explorer, right-click **Files** or **Tables** > **New shortcut**
3. Select **Azure Data Lake Storage Gen2**
4. Enter connection details:
   - URL: `https://stgovdatalanding.dfs.core.windows.net`
   - Authentication: Service principal or SAS token (organizational account does not work cross-tenant)
   - Container: `landing-bronze`
5. The data now appears in your Lakehouse without copying

#### Option B: API / File Export Pattern

For smaller datasets or agencies without Azure Gov subscriptions:

**Step 4B.1 — Export Data as Files**

```python
# Example: Export de-identified data to Parquet files
import pandas as pd
from azure.storage.filedatalake import DataLakeServiceClient

# Read from GCC data source
df = pd.read_sql("SELECT * FROM public_metrics WHERE classification = 'PUBLIC'",
                  connection_string)

# De-identify if needed
df = df.drop(columns=['ssn', 'name', 'address'])  # Remove PII columns

# Write to Parquet
df.to_parquet('public_metrics_deidentified.parquet', index=False)

# Upload to Commercial ADLS Gen2
service_client = DataLakeServiceClient(
    account_url="https://stgovdatalanding.dfs.core.windows.net",
    credential=sas_token
)
file_system_client = service_client.get_file_system_client("landing-bronze")
file_client = file_system_client.get_file_client("public_metrics/data.parquet")

with open('public_metrics_deidentified.parquet', 'rb') as f:
    file_client.upload_data(f, overwrite=True)
```

#### Option C: Fabric Pipeline Ingestion

If the data source is accessible from Commercial Azure (e.g., a public API, open data source):

1. In Fabric workspace, create a **Data Pipeline**
2. Add a **Copy Data** activity
3. Configure source as HTTP or REST connector pointing to the public data API
4. Configure sink as the Fabric Lakehouse
5. Schedule the pipeline

---

### Phase 5: Configure External Data Sharing

**Goal:** If bi-directional data access is needed between tenants.

Fabric External Data Sharing allows data in one Fabric tenant to be accessed from another tenant via OneLake shortcuts. This is relevant if:
- The Commercial Fabric tenant needs to share processed analytics back with users who remain in the GCC tenant (consuming via a different Commercial tenant)
- Multiple agencies in separate Commercial tenants need to share data

**Step 5.1 — Enable External Data Sharing (Admin Portal)**

In the Commercial tenant's Fabric Admin Portal:

1. Go to **Tenant settings**
2. Under **Export and sharing settings**:
   - Enable **External data sharing** — specify which users can create shares
   - Enable **Users can accept external data shares** — specify which users can accept

**Step 5.2 — Create an External Data Share**

1. In a workspace, find the Lakehouse or Warehouse with data to share
2. Right-click > **External data share**
3. Select the tables or folders to share
4. Enter the email address of the recipient (must be in a different Fabric tenant)
5. The recipient gets a link, accepts it, and chooses a lakehouse for the shortcut

> **Important:** External data sharing uses Fabric-to-Fabric authentication, NOT Entra B2B. The recipient gets read-only access via a OneLake shortcut. Governance policies from the source tenant do NOT flow to the consumer tenant.

---

### Phase 6: Set Up Governance and Monitoring

**Step 6.1 — Data Governance**

In the Commercial tenant:

1. **Microsoft Purview Information Protection:**
   - Create sensitivity labels: `Public`, `Internal`, `Government-NonSensitive`
   - Apply default labels to Fabric items
   - Configure auto-labeling policies

2. **Purview Data Loss Prevention:**
   - Create DLP policies that prevent sharing of labeled content outside the tenant
   - Monitor for accidental inclusion of sensitive data patterns (SSN regex, etc.)

3. **Data access policies:**
   - Use workspace roles for coarse-grained access
   - Use OneLake Security (folder-level, RLS, CLS) for fine-grained access

**Step 6.2 — Audit Logging**

1. Enable **Unified Audit Log** in the Commercial tenant
2. Configure Fabric **workspace monitoring** to capture:
   - Who accessed what data
   - Query execution logs
   - Data export events
3. Export audit logs to a SIEM (Sentinel, Splunk) for monitoring
4. Set up alerts for anomalous access patterns

**Step 6.3 — Compliance Reporting**

Create a compliance dashboard that tracks:
- Data inventory in Commercial Fabric (all items, their classification)
- Guest user activity (last sign-in, actions performed)
- Data transfer volume from GCC to Commercial
- Policy violations and DLP alerts

---

## Architecture Patterns

### Pattern A: Full Commercial Tenant for Analytics

**Best for:** State/local agencies with mostly public or non-sensitive data.

```
GCC Tenant                    Commercial Tenant
+-----------------+           +-----------------------+
| Email, Teams,   |           | Microsoft Fabric      |
| SharePoint,     |  B2B      | (all analytics)       |
| Power BI GCC    | <-------> |                       |
| (regulated BI)  |  Guest    | OneLake               |
+-----------------+  Access   | Lakehouse (medallion) |
                              | Warehouse             |
                              | Notebooks             |
                              | Power BI (public BI)  |
                              +-----------------------+
```

**Pros:** Full Fabric feature access, simplest architecture, single analytics platform.
**Cons:** Dual licensing cost, all data must be non-sensitive, no Fabric-GCC integration.

---

### Pattern B: ADLS Gen2 Bridge (Hybrid)

**Best for:** Agencies with mixed data sensitivity, existing Azure Gov investments.

```
Azure Gov                    Azure Commercial
+-----------------+          +-----------------------+
| ADLS Gen2       |  Export  | ADLS Gen2             |
| (all data)      | -------> | (landing zone)        |
|                 | (non-    |         |              |
| Synapse / ADF   |  sens.)  |    Shortcut           |
| (regulated ETL) |          |         v              |
+-----------------+          | Microsoft Fabric      |
                             | Lakehouse / Warehouse |
GCC Tenant                   +-----------------------+
+-----------------+          Commercial Tenant
| Power BI GCC    |  B2B     +-----------------------+
| (sensitive BI)  | <------> | Power BI (Fabric)     |
+-----------------+  Guest   | (public analytics BI) |
                              +-----------------------+
```

**Pros:** Retains Azure Gov for sensitive processing, incremental adoption, clear data boundary.
**Cons:** More complex, requires cross-cloud networking, dual Azure subscriptions.

---

### Pattern C: Export-and-Load with Data Pipelines

**Best for:** Agencies with limited Azure Gov footprint, small to medium data volumes.

```
GCC Environment              Commercial Tenant
+-----------------+          +-----------------------+
| Source Systems   |  Export  | Fabric Pipelines      |
| (databases,     | -------> | (Copy Data activity)  |
|  files, APIs)   | (files,  |         |              |
+-----------------+  APIs)   |         v              |
                             | Lakehouse (Bronze)    |
                             | Notebooks (Silver)    |
                             | Warehouse (Gold)      |
                             | Power BI Reports      |
                             +-----------------------+
```

**Pros:** No Azure Gov dependency, Fabric handles all ETL, simpler networking.
**Cons:** Manual export step, latency, not suitable for real-time, file-based only.

---

## Security and Compliance Deep Dive

### Compliance Framework Mapping

| Framework | Applicability to Federated Fabric | Notes |
|-----------|-----------------------------------|-------|
| **FedRAMP Moderate** | GCC tenant maintains FedRAMP Moderate. Commercial tenant is NOT FedRAMP authorized for government data. | Only non-regulated data goes to Commercial. |
| **FedRAMP High** | Not applicable to Commercial Fabric. | If you need FedRAMP High, wait for Fabric in Azure Gov or use Synapse in Azure Gov. |
| **NIST SP 800-171** | Does not apply to data in Commercial Fabric (CUI stays in GCC). | Ensure CUI never reaches Commercial. |
| **CMMC Level 2** | Same as NIST 800-171 — CUI stays in GCC. | Commercial Fabric can be used for non-CUI analytics. |
| **CJIS** | CJIS data cannot go to Commercial. | Use Power BI GCC or Azure Gov Synapse for CJIS workloads. |
| **HIPAA** | PHI cannot go to Commercial without BAA and additional controls. | De-identified data per HIPAA Safe Harbor may be permissible. |
| **StateRAMP** | Varies by state. | Check your state's requirements; many align with FedRAMP Moderate. |

### Security Controls Checklist

```
[ ] Data classification completed for all datasets
[ ] ISSO/Security Officer written approval obtained
[ ] Conditional Access policies enforced (MFA for guests)
[ ] Cross-cloud B2B configured with least-privilege access
[ ] Sensitivity labels applied to all Fabric items
[ ] DLP policies active (SSN patterns, credit card numbers, etc.)
[ ] Audit logging enabled in both tenants
[ ] Network security configured (Private Link if required)
[ ] Guest user lifecycle management (expiration, access reviews)
[ ] Incident response plan updated to cover Commercial tenant
[ ] Data transfer procedures documented and reviewed
[ ] Quarterly access reviews scheduled
```

### Identity Security

| Control | Implementation |
|---------|---------------|
| **MFA** | Required for all guest users via Conditional Access |
| **Conditional Access** | Location-based, device-compliance, risk-based policies |
| **Session management** | Sign-in frequency ≤ 8 hours, persistent browser sessions disabled |
| **Access reviews** | Quarterly review of guest users in Commercial tenant |
| **Just-in-time access** | Consider PIM for admin roles in Commercial tenant |
| **Named accounts** | Every GCC user accessing Fabric has a named guest account — no shared accounts |

---

## Networking and Connectivity

### Option 1: Public Internet (Simplest)

- GCC users access Commercial Fabric via browser over the internet
- ADLS Gen2 data transfer uses public endpoints with SAS tokens
- Acceptable for non-sensitive data with strong authentication

### Option 2: Private Link (More Secure)

- Enable **Azure Private Link** for Fabric in the Commercial tenant
- Create Private Endpoints in a Commercial Azure VNet
- Connect to GCC networks via VPN or ExpressRoute (cross-cloud peering requires specific configuration)
- Block public internet access to Fabric via tenant settings

> **Limitation:** Fabric Private Link does not support cross-tenant scenarios. If GCC users access Fabric as guests, they use the Commercial tenant's Private Link endpoint, which requires network connectivity to the Commercial VNet.

### Option 3: Workspace-Level Private Links (Cross-Tenant)

Fabric supports workspace-level Private Link services for cross-tenant secure connectivity:

1. In the Commercial tenant: Create a Private Link service for the Fabric workspace
2. In the GCC Azure Gov subscription: Create a Private Endpoint connecting to the Commercial workspace's Private Link service
3. Configure DNS for proper name resolution

> **Note:** This is the most complex networking option and requires coordination between both Azure subscriptions.

---

## Licensing and Cost Considerations

### Monthly Cost Estimate (Example)

| Item | SKU | Estimated Monthly Cost |
|------|-----|----------------------|
| Fabric Capacity (Production) | F64 | ~$5,000/month |
| Fabric Capacity (Dev/Test) | F2 | ~$260/month |
| Microsoft 365 E3 (Commercial, per user) | E3 | ~$36/user/month |
| Entra ID P2 (per user) | P2 | ~$9/user/month |
| ADLS Gen2 Storage | LRS | ~$0.02/GB/month |
| Azure Private Link (if used) | Standard | ~$8/endpoint/month |

### Cost Optimization Tips

1. **Pause Fabric capacity** during non-business hours (nights/weekends) to reduce costs by 60%+
2. **Use F2 for dev/test** — F64 is only needed for production workloads
3. **Minimize Commercial M365 licenses** — only assign to users who need admin access. Guest users (B2B) from GCC don't need Commercial M365 licenses for Fabric access if the capacity has sufficient CUs.
4. **Right-size capacity** — Start with F64 and scale based on actual CU utilization via the Capacity Metrics app

---

## Best Practices

### Data Management

1. **Classify before you move.** Never transfer data to Commercial without documented classification review. When in doubt, keep it in GCC.

2. **De-identify at source.** Run de-identification in the GCC boundary (Azure Gov or GCC services) before any data crosses to Commercial. Never de-identify after the data is in Commercial.

3. **Use medallion architecture in Fabric.** Bronze (raw de-identified), Silver (cleansed), Gold (aggregated). This mirrors what you will build when Fabric comes to GCC.

4. **Automate data classification checks.** In your Fabric pipelines, add validation steps that scan for PII patterns (SSN, email, phone) and halt the pipeline if detected.

5. **Document every data flow.** Maintain a data flow diagram showing exactly what data moves between GCC and Commercial, how, and why.

### Identity and Access

6. **Use security groups for guest management.** Create an "Analytics-Fabric-Users" security group in GCC Entra ID. Add/remove users from the group rather than managing individual guest invitations.

7. **Enforce named accounts only.** No shared accounts, no service accounts accessing Fabric interactively.

8. **Set guest user expiration.** Configure B2B guest users to expire every 90 days with renewal requiring manager approval.

9. **Separate admin identities.** Fabric admins should have dedicated admin accounts, not their daily-use GCC accounts.

### Architecture

10. **Design for migration.** When Fabric arrives in GCC, you want to migrate workloads without redesigning. Use the same workspace names, lakehouse structure, and notebook code you would in GCC Fabric.

11. **Keep regulated workloads in Power BI GCC.** Dashboards over sensitive data stay in GCC Power BI. Use Commercial Fabric only for non-sensitive analytics.

12. **Use OneLake shortcuts over data copying.** Shortcuts to ADLS Gen2 landing zones avoid data duplication and keep a single source of truth.

13. **Tag everything.** Use Fabric workspace descriptions, item descriptions, and sensitivity labels to clearly mark data provenance (e.g., "Source: GCC De-identified Export 2026-04").

### Operations

14. **Monitor guest activity weekly.** Review sign-in logs for unusual access patterns.

15. **Test cross-cloud access quarterly.** Verify that B2B collaboration works correctly — cross-cloud settings can break during Entra ID updates.

16. **Maintain a runbook.** Document the exact steps for: inviting new users, revoking access, transferring new datasets, handling incidents.

---

## Gotchas and Common Pitfalls

### Identity Gotchas

| Gotcha | Impact | Mitigation |
|--------|--------|------------|
| **Domain name lookup doesn't work cross-cloud** | Cannot find GCC tenants by domain name in Commercial Entra. Must use Tenant ID. | Always use Tenant ID when configuring cross-cloud settings. |
| **Email as sign-in not supported cross-cloud** | GCC users must be invited by UPN, not email alias. | Use the full UPN format: `user@agency.gcc.onmicrosoft.com`. |
| **B2B Direct Connect not supported cross-cloud** | Only B2B Collaboration (guest accounts) works. No shared channels or direct connect. | Design around guest access model only. |
| **Double MFA prompts** | Users prompted for MFA in both GCC and Commercial tenants. | Configure MFA trust in cross-tenant access settings. |
| **Guest user consent prompts** | First-time access to Fabric may require admin consent for the Fabric app. | Pre-consent the Fabric app for guest users via enterprise applications. |

### Data Gotchas

| Gotcha | Impact | Mitigation |
|--------|--------|------------|
| **Sensitivity labels don't flow cross-tenant** | Labels applied in GCC don't appear in Commercial, and vice versa. | Apply labels independently in each tenant. |
| **DLP policies are tenant-scoped** | GCC DLP won't scan Commercial Fabric data. | Create separate DLP policies in the Commercial tenant. |
| **Purview governance is per-tenant** | No unified governance view across GCC + Commercial. | Accept dual governance or use a third-party tool. |
| **OneLake shortcuts to ADLS Gen2 cross-tenant require service principal** | Organizational account and workspace identity don't work cross-tenant for ADLS shortcuts. | Use service principal or SAS token authentication. |
| **External data sharing is Fabric-to-Fabric, not Fabric-to-GCC** | External data sharing requires Fabric in both tenants. Since GCC doesn't have Fabric, this only works between two Commercial tenants. | Use ADLS Gen2 bridge or file export for GCC return data flows. |

### Networking Gotchas

| Gotcha | Impact | Mitigation |
|--------|--------|------------|
| **Private Link doesn't support cross-tenant** | Tenant-level Private Link is single-tenant only. | Use workspace-level Private Link services for cross-tenant, or accept public access with strong auth. |
| **Cross-cloud shortcuts don't work over Private Link** | Shortcuts referencing data from another tenant can't use Private Link. | Use OneLake data sharing without Private Link for cross-tenant access. |
| **Azure Gov regions are separate from Commercial regions** | Cannot peer VNets between Azure Gov and Azure Commercial natively. | Use VPN gateway-to-gateway or ExpressRoute with Global Reach for cross-cloud connectivity. |

### Licensing Gotchas

| Gotcha | Impact | Mitigation |
|--------|--------|------------|
| **GCC licenses are NOT valid in Commercial** | A Power BI Pro GCC license doesn't grant any access in Commercial Fabric. | Purchase separate Commercial licenses. |
| **Guest users consume Fabric CU, not per-user licenses** | B2B guests from GCC use the Fabric capacity (CUs) when running queries/notebooks. They don't need a separate Power BI Pro license in Commercial IF the workspace is on Fabric capacity. | Monitor CU consumption. |
| **F SKU vs P SKU transition** | P SKUs are being deprecated. New purchases must be F SKU. | Use F64 or higher for production. |

---

## Frequently Asked Questions

**Q: Can GCC High or DoD customers use this federated approach?**
A: Technically yes for non-CUI data, but practically very limited. GCC High and DoD exist specifically because the data requires sovereign boundary protection. Most data in these environments is CUI or higher and cannot move to Commercial. Consult your ISSO before considering this approach.

**Q: Is this approach officially supported by Microsoft?**
A: Microsoft supports cross-cloud B2B collaboration between Azure Government and Azure Commercial tenants. Microsoft supports guest user access to Fabric. However, there is no Microsoft-published reference architecture specifically for "Federated Fabric for GCC." This is an architectural pattern assembled from supported building blocks.

**Q: What happens when Fabric comes to GCC?**
A: You migrate your Fabric workloads from the Commercial tenant to the GCC Fabric instance. If you followed the medallion architecture and naming conventions recommended in this guide, migration involves re-creating workspaces in GCC Fabric, moving notebooks/pipelines, and repointing data sources. OneLake data can be migrated via Fabric's migration tools or by re-ingesting from source.

**Q: Can I use Fabric Copilot / AI features from GCC?**
A: Fabric Copilot is available in Commercial Fabric. GCC guest users accessing Commercial Fabric can use Copilot features, but the AI processing happens in Commercial Azure (not Azure Government). If your organization's AI policy prohibits government users from using Commercial AI services, disable Copilot for guest users via tenant settings.

**Q: How do I handle data that's borderline (not clearly CUI but also not public)?**
A: When in doubt, keep it in GCC. The cost of a compliance violation far exceeds the cost of delayed analytics. Work with your data governance team and ISSO to establish clear classification criteria before proceeding.

**Q: Can I use Power BI in GCC to connect to Fabric in Commercial via DirectQuery?**
A: No. Power BI GCC cannot connect to Commercial Fabric via DirectQuery or Live Connection. These are separate service instances in different clouds. You can export data or reports from Commercial Fabric and import them into Power BI GCC, but there is no live cross-cloud connection.

---

## When Fabric Comes to GCC: Migration Path

When Microsoft releases Fabric for GCC, plan the following migration:

### Pre-Migration Checklist

```
[ ] Inventory all workspaces, lakehouses, warehouses, and notebooks in Commercial Fabric
[ ] Document all data pipelines and their schedules
[ ] Export all notebook code to source control (Git integration)
[ ] Document all workspace permissions and roles
[ ] List all OneLake shortcuts and their targets
[ ] Capture all Power BI reports and semantic models
```

### Migration Steps

1. **Provision Fabric capacity in GCC** (new F SKU in Azure Gov)
2. **Re-create workspaces** in GCC Fabric with same naming convention
3. **Re-create lakehouses and warehouses** in GCC workspaces
4. **Import notebooks** from source control (Git)
5. **Reconfigure data pipelines** to point to GCC/Azure Gov data sources (no more cross-cloud bridge needed)
6. **Migrate Power BI reports** using PBIX export/import or XMLA
7. **Update user access** — users are now native GCC users, not B2B guests
8. **Validate data integrity** — run comparison queries between Commercial and GCC
9. **Decommission Commercial Fabric** — revoke guest access, remove data, cancel capacity

### What Will Be Easier Post-Migration

- No dual licensing
- No cross-cloud B2B complexity
- Native Entra ID integration (no guest accounts)
- FedRAMP-authorized boundary for all data
- Unified governance with GCC Purview
- Potentially: Direct Lake connections to GCC Power BI

---

## Casino POC: Federated Pattern Example

For the Supercharge Microsoft Fabric POC, here is how the federated pattern applies to the casino/gaming domain:

### Casino Data Classification

| Dataset | Classification | Fabric Location |
|---------|---------------|-----------------|
| Slot machine telemetry (aggregated hourly) | Non-sensitive (no PII) | Commercial Fabric |
| Player loyalty data (with PII) | Sensitive (PII) | GCC Power BI / Azure Gov |
| Table game performance metrics | Non-sensitive (no PII) | Commercial Fabric |
| Currency Transaction Reports (CTR) | Regulated (FinCEN) | GCC / Azure Gov ONLY |
| Suspicious Activity Reports (SAR) | Regulated (FinCEN) | GCC / Azure Gov ONLY |
| W-2G tax data | Regulated (IRS) | GCC / Azure Gov ONLY |
| Hotel occupancy rates | Non-sensitive | Commercial Fabric |
| F&B revenue metrics | Non-sensitive | Commercial Fabric |
| Player demographics (de-identified) | Non-sensitive after de-ID | Commercial Fabric |

### Medallion in Federated Casino POC

```
Azure Gov / GCC Boundary              Commercial Fabric
+----------------------------+        +----------------------------+
| Source Systems              |        | lh_gov_bronze              |
| (Gaming systems, POS, CRM) |        |   slot_telemetry_hourly/   |
|            |                |        |   table_performance/       |
|            v                |        |   hotel_occupancy/         |
| De-identification Pipeline  | -----> |   fb_revenue/              |
| (Azure Data Factory in Gov) |        +----------------------------+
|            |                |        | lh_gov_silver              |
|            v                |        |   slot_cleansed/           |
| ADLS Gen2 (Azure Gov)      |        |   table_validated/         |
| - Raw regulated data       |        +----------------------------+
| - CTR/SAR data             |        | lh_gov_gold                |
| - PII player data          |        |   slot_performance_kpi/    |
+----------------------------+        |   casino_floor_metrics/    |
                                      |   revenue_dashboard/       |
                                      +----------------------------+
```

---

## Federal Agency Considerations

### USDA

Open agricultural data (crop production, food safety inspections) is publicly available and an excellent candidate for Commercial Fabric analytics. USDA National Agricultural Statistics Service (NASS) data can be ingested directly via public APIs.

### SBA

Loan program statistics and disaster loan summaries are public. Individually identifiable loan applicant data is PII and must stay in GCC.

### NOAA

Weather, climate, and ocean data is overwhelmingly public and ideal for Fabric analytics (Real-Time Intelligence, Eventstreams for weather feeds).

### EPA

Environmental monitoring data, facility emissions reports (TRI), and air quality data are public. Enforcement action details involving ongoing investigations may be LES.

### DOI

Land management data, geological survey data, and natural resource statistics are largely public. Tribal trust data and certain land records may have restrictions.

### DOJ

Published crime statistics (UCR/NIBRS) are public. Active investigation data, CJIS data, and witness/victim information are absolutely restricted to GCC High or DoD boundaries.

---

## References

### Microsoft Documentation

| Resource | URL |
|----------|-----|
| Enable B2B collaboration across Microsoft clouds | [learn.microsoft.com/entra/external-id/cross-cloud-settings](https://learn.microsoft.com/entra/external-id/cross-cloud-settings) |
| Cross-tenant access overview | [learn.microsoft.com/entra/external-id/cross-tenant-access-overview](https://learn.microsoft.com/entra/external-id/cross-tenant-access-overview) |
| Entra B2B in government and national clouds | [learn.microsoft.com/entra/external-id/b2b-government-national-clouds](https://learn.microsoft.com/entra/external-id/b2b-government-national-clouds) |
| Power BI for US Government customers | [learn.microsoft.com/fabric/enterprise/powerbi/service-government-us-overview](https://learn.microsoft.com/fabric/enterprise/powerbi/service-government-us-overview) |
| External data sharing in Microsoft Fabric | [learn.microsoft.com/fabric/governance/external-data-sharing-overview](https://learn.microsoft.com/fabric/governance/external-data-sharing-overview) |
| Fabric cross-tenant workspace Private Link | [learn.microsoft.com/fabric/security/security-cross-tenant-communication](https://learn.microsoft.com/fabric/security/security-cross-tenant-communication) |
| Private links for Fabric tenants | [learn.microsoft.com/fabric/security/security-private-links-overview](https://learn.microsoft.com/fabric/security/security-private-links-overview) |
| Configure cross-tenant access settings | [learn.microsoft.com/entra/external-id/cross-tenant-access-settings-b2b-collaboration](https://learn.microsoft.com/entra/external-id/cross-tenant-access-settings-b2b-collaboration) |
| OneLake shortcuts | [learn.microsoft.com/fabric/onelake/onelake-shortcuts](https://learn.microsoft.com/fabric/onelake/onelake-shortcuts) |
| ADLS Gen2 shortcuts in Fabric | [learn.microsoft.com/fabric/onelake/create-adls-shortcut](https://learn.microsoft.com/fabric/onelake/create-adls-shortcut) |
| Fabric tenant settings | [learn.microsoft.com/fabric/admin/tenant-settings-index](https://learn.microsoft.com/fabric/admin/tenant-settings-index) |

### Community and Industry Sources

| Resource | URL |
|----------|-----|
| Fabric GCC availability discussion | [community.fabric.microsoft.com — When will Fabric be available for GCC](https://community.fabric.microsoft.com/t5/Fabric-platform/When-will-Fabric-be-available-for-GCC/td-p/4398348) |
| Fabric CMKs: Gov Cloud Readiness (Daymark) | [daymarksi.com — CMK Gov Cloud Readiness](https://www.daymarksi.com/cole-tramps-microsoft-insights/microsoft-fabric-cmks-a-game-changer-for-gov-cloud-readiness) |
| GCC High B2B Implementation Guide (Summit 7) | [summit7.us — B2B Collaboration in GCC High](https://www.summit7.us/blog/implementing-b2b-collaboration-in-gcc-high-going-slow-to-go-fast) |
| Cross-Cloud Collaboration Setup (Agile IT) | [agileit.com — GCC High Cross-Cloud Collaboration](https://agileit.com/news/commercial-office-365-gcc-high-cross-cloud-collaboration/) |
| Understanding Compliance Between Clouds (Microsoft Tech Community) | [techcommunity.microsoft.com — Compliance Between Clouds](https://techcommunity.microsoft.com/blog/publicsectorblog/understanding-compliance-between-commercial-government-dod--secret-offerings---j/4225436) |
| Fabric Multi-Tenant Architecture (Microsoft FastTrack) | [techcommunity.microsoft.com — Multi-Tenant Architecture](https://techcommunity.microsoft.com/blog/fasttrackforazureblog/microsoft-fabric---multi-tenant-architecture/4119429) |
| Cross-Cloud Collaboration Overview (AvePoint) | [avepoint.com — Cross-Cloud Collaboration for Government](https://www.avepoint.com/blog/microsoft-365/cross-cloud-collaboration-gov) |

### Compliance Frameworks

| Framework | Reference |
|-----------|-----------|
| FedRAMP | [fedramp.gov](https://www.fedramp.gov/) |
| NIST SP 800-171 | [csrc.nist.gov](https://csrc.nist.gov/publications/detail/sp/800-171/rev-2/final) |
| CMMC 2.0 | [dodcio.defense.gov/CMMC](https://dodcio.defense.gov/CMMC/) |
| CJIS Security Policy | [fbi.gov/cjis](https://www.fbi.gov/services/cjis/cjis-security-policy-resource-center) |

---

> **Disclaimer:** This document provides an architectural pattern for using Microsoft Fabric in Commercial cloud from a GCC environment. It does not constitute legal or compliance advice. Organizations must consult with their Information System Security Officer (ISSO), legal counsel, and compliance teams before implementing any cross-cloud data architecture. Data classification decisions and compliance determinations are the responsibility of the implementing organization.

---

*Last updated: 2026-04-29 | Supercharge Microsoft Fabric POC*
