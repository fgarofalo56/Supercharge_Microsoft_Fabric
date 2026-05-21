---
hero: assets/heroes/reference.svg
hero_alt: "Reference — Glossary, FAQ, cheat sheets, style guide, and the data dictionary"
type: reference
---
# 💬 Frequently Asked Questions (FAQ)

> **Last Updated**: 2026-04-27 | **Version**: 3.0
> **Status**: ✅ Final | **Maintainer**: Documentation Team

<div align="center" markdown>

![Category](https://img.shields.io/badge/Category-Reference-purple?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-April_2026-blue?style=for-the-badge)

</div>

---

!!! tip "Looking for answers to specific operational questions?"
    See **[Field Questions](FIELD_QUESTIONS.md)** for detailed answers to scenarios
    that come up in real customer engagements: Power BI mashup errors with VNet
    sources, creating views on mirrored Databricks tables, Unity Catalog →
    Fabric permission inheritance, Direct Lake on multi-source semantic
    models, SharePoint → Fabric Pipeline triggers, Fabric SQL Database
    ingestion patterns, and DataFlow Gen2 + gateway → Lakehouse issues.

## 🎯 General Questions

### What is this POC?

This is a **production-ready proof-of-concept environment** for Microsoft Fabric, purpose-built for the casino and gaming industry. It demonstrates:

- ✅ Complete medallion architecture (Bronze/Silver/Gold)
- ✅ Real-time slot machine telemetry
- ✅ Player 360 analytics
- ✅ Regulatory compliance (NIGC MICS, FinCEN BSA)
- ✅ Direct Lake Power BI dashboards
- ✅ Data governance with Microsoft Purview

**Key Value:** Provides a working reference implementation that can be customized for your specific casino operations.

---

### Who is this POC for?

<details>
<summary>👥 Click to see target audience</summary>

| Audience | Use Case |
|----------|----------|
| 🏗️ **Data Architects** | Evaluate Fabric for enterprise data platforms |
| 💻 **Data Engineers** | Learn medallion architecture patterns |
| 📊 **BI Developers** | Build Direct Lake Power BI solutions |
| 🎰 **Gaming Industry** | Implement analytics for casino operations |
| 🏛️ **Solution Architects** | Design cloud-native analytics platforms |
| 🎓 **Students/Learners** | Hands-on experience with Microsoft Fabric |

</details>

---

### What data domains are covered?

<details>
<summary>🎲 Click to see data domains</summary>

| Domain | Icon | Description |
|--------|------|-------------|
| **Slot Machines** | 🎰 | Telemetry, meter readings, jackpots, performance |
| **Table Games** | 🎲 | Hand results, chip tracking, dealer analytics |
| **Player/Loyalty** | 👤 | Profiles, rewards, Player 360 insights |
| **Financial/Cage** | 💰 | Transactions, fills, credits, cash management |
| **Security** | 🔒 | Surveillance, access control, incident tracking |
| **Compliance** | 📋 | CTR/SAR reporting, W-2G forms, regulatory filings |

</details>

---

### How long does it take to complete the full POC?

**3-Day Workshop Format:**
- **Day 1** (8 hours): Medallion foundation (Bronze + Silver)
- **Day 2** (8 hours): Gold layer + Real-time analytics
- **Day 3** (8 hours): Power BI + Governance

**Self-Paced Learning:** 2-4 weeks (2-3 hours per week)

See the [3-Day POC Agenda](poc-agenda/README.md) for detailed schedules.

---

### Can I use this for non-gaming industries?

**Yes!** While this POC is casino-focused, the architecture patterns apply to many industries:

| Industry | Adaptations |
|----------|-------------|
| 🏥 Healthcare | Patient analytics, HIPAA compliance |
| 🏛️ Federal Government | DOT/FAA datasets, FedRAMP compliance |
| 🛒 Retail/E-commerce | Customer 360, supply chain optimization |
| 🏦 Financial Services | Transaction monitoring, fraud detection |

See the tutorial modules (14–37) for vertical-specific examples.

---

## 📋 Prerequisites & Setup

### What Azure resources do I need?

<details>
<summary>☁️ Click to see requirements</summary>

**Required:**
- ✅ Azure subscription (Owner or Contributor access)
- ✅ Microsoft Fabric capacity (F64 recommended for POC)
- ✅ Resource providers registered (see below)

**Optional:**
- Microsoft Purview account (for governance features)
- Azure Key Vault (for secrets management)
- Private endpoints (for production security)

**Resource Providers to Register:**
```bash
az provider register --namespace Microsoft.Fabric
az provider register --namespace Microsoft.Purview
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.KeyVault
```

See [Prerequisites Guide](PREREQUISITES.md) for complete details.

</details>

---

### What is the minimum Fabric capacity SKU?

| SKU | Use Case | Monthly Cost (24/7) |
|-----|----------|---------------------|
| **F2** | Minimal testing | ~$265 |
| **F4** | Development (recommended minimum) | ~$530 |
| **F64** | **POC recommended** | ~$8,480 |

**Why F64 for POC?**
- Sufficient compute for parallel data processing
- Can handle real-time streaming workloads
- Supports multiple concurrent users

**Can I start smaller?** Yes, but expect slower performance with F2/F4. Good for learning tutorials but not representative of production performance.

See [Cost Estimation Guide](COST_ESTIMATION.md) for detailed pricing.

---

### Do I need to install anything locally?

**Quick Answer:** No, if using Dev Container or Codespaces.

**Local Installation Option:**

| Tool | Version | Required? |
|------|---------|-----------|
| Azure CLI | 2.50+ | Yes |
| Bicep | 0.22+ | Yes |
| Git | 2.40+ | Yes |
| PowerShell | 7.0+ | Yes |
| Python | 3.10+ | For data generation |
| Docker | Latest | For containerized generators |

**Easiest Setup:** Use GitHub Codespaces (zero installation) or VS Code Dev Container.

See [Prerequisites - Dev Container Setup](PREREQUISITES.md#dev-container-setup-alternative-to-local-installation).

---

### How do I enable Fabric in my tenant?

<details>
<summary>🔑 Click to see steps</summary>

**Requirements:**
- Microsoft Entra ID Global Administrator OR Fabric Administrator role

**Steps:**
1. Navigate to [Microsoft Fabric Admin Portal](https://app.fabric.microsoft.com/admin-portal)
2. Select **Tenant settings**
3. Under **Microsoft Fabric**, enable:
   - ✅ Users can create Fabric items
   - ✅ Users can use OneLake
4. (Optional) Restrict to specific security groups
5. Click **Apply**

**Verification:**
1. Go to [app.fabric.microsoft.com](https://app.fabric.microsoft.com)
2. You should see the Fabric home page
3. Click **+ New** - you should see Lakehouse, Warehouse, etc.

**Troubleshooting:** If Fabric options don't appear, contact your Microsoft Entra ID admin to verify tenant settings.

</details>

---

### What permissions do I need?

<details>
<summary>🔐 Click to see permission requirements</summary>

**Azure Subscription:**
- Minimum: **Contributor** role
- Recommended: **Owner** role (for initial setup)

**Fabric Workspace:**
- **Admin**: Full control (workspace owners)
- **Member**: Can create and edit items (data engineers)
- **Contributor**: Can create/edit but not share (developers)
- **Viewer**: Read-only (business users)

**Why Owner for Setup?**
- Configure RBAC and resource providers
- Create service principals for CI/CD
- Set up managed identities

After initial setup, Contributor is sufficient for day-to-day operations.

</details>

---

## 🚀 Deployment Questions

### What are the deployment options?

| Method | Best For | Time to Deploy |
|--------|----------|----------------|
| 🐳 **Docker Quick Start** | Generate sample data, test generators | ~5 minutes |
| ☁️ **Azure Bicep** | Full infrastructure deployment | ~30 minutes |
| 📜 **PowerShell Scripts** | Automated CI/CD workflows | ~30 minutes |
| 🔄 **GitHub Actions** | Continuous deployment pipelines | One-time setup |

See [Deployment Guide](DEPLOYMENT.md) for detailed instructions.

---

### How do I deploy to Azure?

<details>
<summary>📜 Click to see quick deployment steps</summary>

**Prerequisites:**
- Azure CLI logged in
- Bicep extension installed
- `.env` file configured

**Quick Deployment:**

```bash
# 1. Login to Azure
az login
az account set --subscription "<your-subscription-id>"

# 2. Deploy infrastructure
az deployment sub create \
  --location eastus2 \
  --template-file infra/main.bicep \
  --parameters infra/environments/dev/dev.bicepparam

# 3. Verify deployment
./scripts/verify-deployment.sh
```

**Deployment Time:** ~30 minutes for complete infrastructure.

**What Gets Deployed:**
- Fabric capacity
- Purview account
- ADLS Gen2 storage
- Key Vault
- Log Analytics workspace
- Network security groups

</details>

---

### Common deployment errors?

<details>
<summary>⚠️ Click to see common issues and fixes</summary>

#### Error: `Microsoft.Fabric/capacities resource provider not registered`

**Fix:**
```bash
az provider register --namespace Microsoft.Fabric
az provider show --namespace Microsoft.Fabric --query "registrationState"
```
Wait for "Registered" status (can take 5-10 minutes).

---

#### Error: `AuthorizationFailed`

**Cause:** Insufficient permissions

**Fix:** Ensure you have Owner or Contributor role:
```bash
az role assignment list --assignee "$(az ad signed-in-user show --query id -o tsv)"
```

---

#### Error: `SKU F64 not available in region`

**Cause:** Capacity not available in selected region

**Fix:** Check [Fabric capacity availability](https://learn.microsoft.com/fabric/enterprise/region-availability) and choose supported region.

---

#### Error: `Purview account name already exists`

**Cause:** Purview names are globally unique

**Fix:** Choose a different name in `.env` file:
```bash
PURVIEW_ACCOUNT_NAME=pv-fabricpoc-<your-unique-id>
```

</details>

---

### How do I verify deployment succeeded?

<details>
<summary>✅ Click to see verification steps</summary>

**Automated Verification:**
```bash
./scripts/verify-deployment.sh
```

**Manual Verification Checklist:**
- [ ] Fabric capacity shows in Azure Portal
- [ ] Fabric capacity shows in [Fabric Admin Portal](https://app.fabric.microsoft.com/admin-portal)
- [ ] Purview account accessible
- [ ] Storage account has ADLS Gen2 enabled
- [ ] Key Vault accessible
- [ ] Log Analytics receiving logs

**Quick Portal Check:**
```bash
# List deployed resources
az resource list --resource-group "rg-fabric-poc-dev" --output table
```

</details>

---

### How do I delete everything?

**⚠️ Warning:** This is irreversible. Ensure you have backups.

```bash
# Delete resource group (removes all resources)
az group delete --name "rg-fabric-poc-dev" --yes --no-wait

# Remove lock first if resources are locked
az lock delete --name "CanNotDelete" --resource-group "rg-fabric-poc-dev"
```

See [Deployment Guide - Cleanup](DEPLOYMENT.md#️-cleanup) for details.

---

## 🎲 Data Generation

### How do I generate sample data?

<details>
<summary>🎰 Click to see data generation options</summary>

**Option 1: Docker (Easiest)**
```bash
# Quick demo dataset (7 days, small)
docker-compose run --rm demo-generator

# Full dataset (30 days, production-like)
docker-compose run --rm data-generator

# Custom parameters
docker-compose run --rm data-generator --slots 100000 --players 5000 --days 14
```

**Option 2: Local Python**
```bash
# Install dependencies
pip install -r requirements.txt

# Generate all data
python data_generation/generate.py --all --days 30

# Generate specific domains
python data_generation/generate.py --slots 50000 --players 2000
```

**Option 3: Use Pre-Generated Samples**
```bash
# Sample data is already in the repository
ls sample-data/bronze/

# 10,000 slot events, 500 players, etc.
```

Output location: `./output` directory

See [Data Generation Guide](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/blob/main/data_generation/README.md) for complete documentation.

</details>

---

### What data volumes are generated by default?

| Data Type | Records | Size | Bronze Table |
|-----------|---------|------|--------------|
| Slot Events | 500,000 | ~500 MB | `bronze_slot_telemetry` |
| Table Games | 100,000 | ~100 MB | `bronze_table_games` |
| Players | 10,000 | ~10 MB | `bronze_player_profile` |
| Financial | 50,000 | ~50 MB | `bronze_financial_txn` |
| Security | 25,000 | ~25 MB | `bronze_security_events` |
| Compliance | 10,000 | ~10 MB | `bronze_compliance` |
| **Total** | **~700,000** | **~700 MB** | |

**Customization:**
```bash
# Scale up for larger POCs
docker-compose run --rm data-generator --all --days 90

# Scale down for quick testing
docker-compose run --rm demo-generator  # 7 days, smaller volumes
```

---

### Is the generated data realistic?

**Yes!** The data generators include:

✅ **Realistic distributions** based on industry patterns
✅ **Referential integrity** (Player IDs match across tables)
✅ **Compliance logic** (CTR $10K threshold, W-2G $1,200)
✅ **Time-series patterns** (hourly/daily seasonality)
✅ **PII protection** (hashed SSN, masked credit cards)

**Example realistic patterns:**
- Slot machine hold percentage: 8-12%
- Player loyalty tiers: Bronze (60%), Silver (30%), Gold (8%), Platinum (2%)
- Peak gaming hours: 7pm-2am (weekends higher)
- CTR generation: ~0.5% of transactions

See [Data Generation - Data Quality Features](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/blob/main/data_generation/README.md#data-quality-features).

---

### How do I customize the generated data?

<details>
<summary>🔧 Click to see customization options</summary>

**Command Line Options:**
```bash
# Adjust volumes
--slots 1000000        # 1 million slot events
--players 50000        # 50,000 player profiles
--days 90              # 90 days of history

# Adjust format
--format csv           # Output as CSV instead of Parquet
--format json          # Output as JSON

# Control randomness
--seed 12345           # Use specific seed for reproducibility
```

**Programmatic Customization:**
```python
from generators import SlotMachineGenerator

# Custom generator configuration
generator = SlotMachineGenerator(
    num_machines=1000,
    denominations=[0.01, 0.25, 0.50, 1.00, 5.00],
    hold_pct_mean=0.10,  # 10% hold
    seed=42
)

df = generator.generate(100000)
```

**Configuration Files:**
Edit `data_generation/config/` YAML files for domain-specific customization.

</details>

---

### How do I stream data to Event Hub?

<details>
<summary>⚡ Click to see streaming setup</summary>

**Prerequisites:**
- Azure Event Hub created
- Connection string obtained

**Docker Streaming:**
```bash
EVENTHUB_CONNECTION_STRING="Endpoint=sb://..." \
EVENTHUB_NAME="slot-telemetry" \
STREAMING_RATE=10 \
docker-compose up streaming-generator
```

**Python Streaming:**
```python
from generators import SlotMachineGenerator
from streaming import EventHubStreamer

# Configure streamer
streamer = EventHubStreamer(
    connection_string=os.getenv("EVENTHUB_CONNECTION_STRING"),
    eventhub_name="slot-telemetry"
)

# Stream events
generator = SlotMachineGenerator()
for event in generator.generate_stream(events_per_second=10):
    streamer.send(event)
```

**Parameters:**
- `STREAMING_RATE`: Events per second (default: 10)
- `BATCH_SIZE`: Events per batch (default: 100)

See [Tutorial 04: Real-Time Analytics](tutorials/04-real-time-analytics/README.md).

</details>

---

## 📖 Tutorial Questions

### What's the learning path?

```mermaid
graph LR
    T00[00-Setup] --> T01[01-Bronze]
    T01 --> T02[02-Silver]
    T02 --> T03[03-Gold]
    T03 --> T04[04-Real-Time]
    T04 --> T05[05-Power BI]
    T05 --> T06[06-Pipelines]
    T06 --> T07[07-Governance]
    T07 --> T08[08-Mirroring]
    T08 --> T09[09-AI/ML]
```

**Recommended Path:**
1. **🟢 Foundation** (00-01): Environment setup, Bronze layer
2. **🟡 Core** (02-03): Silver and Gold layers
3. **🟠 Advanced** (04-05): Real-time analytics, Power BI
4. **🔴 Enterprise** (06-09): Pipelines, governance, AI/ML

See [Tutorials README](tutorials/index.md) for complete learning path.

---

### Can I skip tutorials?

**Not Recommended.** Each tutorial builds on the previous one:

| Tutorial | Can Skip? | Notes |
|----------|-----------|-------|
| 00-Setup | ❌ No | Creates workspace and Lakehouses |
| 01-Bronze | ❌ No | Required for Silver layer |
| 02-Silver | ❌ No | Required for Gold layer |
| 03-Gold | ❌ No | Required for Power BI |
| 04-Real-Time | ✅ Yes | Optional for basic POC |
| 05-Power BI | ⚠️ Partial | Can use pre-built reports |
| 06-Pipelines | ✅ Yes | Optional for manual workflows |
| 07-Governance | ✅ Yes | Optional for POC |
| 08-Mirroring | ✅ Yes | Optional feature |
| 09-AI/ML | ✅ Yes | Advanced feature |

**Minimum POC:** Complete tutorials 00-03 + 05 (Power BI).

---

### Tutorial 00: Environment setup issues?

<details>
<summary>⚠️ Common setup problems</summary>

#### Issue: Can't create workspace

**Cause:** Fabric not enabled in tenant

**Fix:** Ask Microsoft Entra ID admin to enable Fabric tenant settings.

---

#### Issue: Capacity appears paused

**Cause:** Auto-pause enabled or manually paused

**Fix:**
1. Go to [Fabric Admin Portal](https://app.fabric.microsoft.com/admin-portal)
2. Navigate to **Capacity settings**
3. Click **Resume** on your capacity

---

#### Issue: Can't create Lakehouse

**Cause:** Insufficient workspace permissions

**Fix:** Ensure you have Member or Admin role in the workspace.

</details>

---

### Tutorial 01: Bronze layer issues?

<details>
<summary>⚠️ Common Bronze layer problems</summary>

#### Issue: Data not loading into Lakehouse

**Cause:** File path or format issues

**Fix:**
```python
# Check file path
display(dbutils.fs.ls("Files/bronze/"))

# Verify Parquet format
df = spark.read.format("parquet").load("Files/bronze/slot_telemetry.parquet")
display(df.limit(10))
```

---

#### Issue: Schema mismatch errors

**Cause:** Generated data doesn't match expected schema

**Fix:** Use `mergeSchema` option:
```python
df = spark.read.format("parquet") \
    .option("mergeSchema", "true") \
    .load("Files/bronze/")
```

---

#### Issue: Large files causing timeouts

**Cause:** File too large for single operation

**Fix:** Process in batches or use streaming read.

</details>

---

### Tutorial 05: Direct Lake not working?

<details>
<summary>⚠️ Common Direct Lake problems</summary>

#### Issue: Semantic model falls back to DirectQuery

**Cause:** Delta table not V-Order optimized or too complex

**Fix:**
```sql
-- Optimize Delta table for Direct Lake
OPTIMIZE gold_slot_performance
USING (VORDER);
```

---

#### Issue: "Not supported in Direct Lake mode" error

**Cause:** Using unsupported DAX features

**Supported in Direct Lake:**
- ✅ Most DAX functions
- ✅ Calculated columns
- ✅ Measures
- ✅ Row-level security

**Not Supported:**
- ❌ Calculated tables
- ❌ Some complex M queries
- ❌ Composite models with Import

**Fix:** Simplify DAX or move calculation to Gold layer.

---

#### Issue: Performance is slow

**Cause:** Query complexity or missing optimization

**Fix:**
1. Run `OPTIMIZE` on Delta tables
2. Ensure table partitioning
3. Check Fabric capacity is active
4. Review DAX query performance in Performance Analyzer

</details>

---

## 📊 Power BI & Reporting

### What is Direct Lake mode?

**Direct Lake** is a revolutionary data connectivity mode that combines the best of Import and DirectQuery:

| Mode | Speed | Freshness | Data Duplication |
|------|-------|-----------|------------------|
| Import | ⚡ Fast | ❌ Stale (requires refresh) | Yes |
| DirectQuery | 🐌 Slow | ✅ Fresh | No |
| **Direct Lake** | ⚡ **Fast** | ✅ **Fresh** | **No** |

**How it works:**
- Queries execute directly against Delta tables in OneLake
- Uses V-Order optimization for sub-second performance
- No data import or scheduled refresh required
- Automatic fallback to DirectQuery if needed

See [Tutorial 05: Direct Lake & Power BI](tutorials/05-direct-lake-powerbi/README.md).

---

### Do I need a Power BI license?

<details>
<summary>💳 Click to see licensing requirements</summary>

**To Create Content:**
- Power BI Pro OR
- Power BI Premium Per User (PPU)

**To Consume Content:**
- Power BI Free (if content is in Premium/Fabric capacity)
- Power BI Pro (if not in Premium capacity)

**Fabric Capacity Advantage:**
Users with free licenses can view reports published to Fabric capacity workspaces.

**POC Recommendation:**
- Get Power BI Pro trial (60 days free)
- Or use Fabric capacity with free license for viewers

</details>

---

### How often does Direct Lake refresh?

**Answer:** It doesn't! That's the beauty of Direct Lake.

**Traditional Import Mode:**
- Requires scheduled refresh (e.g., every 8 hours)
- Data is stale between refreshes
- Consumes refresh capacity

**Direct Lake:**
- ✅ Always queries the latest data
- ✅ No refresh schedule needed
- ✅ Updates appear immediately when Delta tables update

**Exception:** If you have calculated tables or composite models, those components might need refresh.

---

### What reports are included?

| Report | Description | Key Visuals |
|--------|-------------|-------------|
| 🎰 **Casino Executive Dashboard** | High-level KPIs | Revenue trends, floor performance, player metrics |
| 🎲 **Slot Performance Analysis** | Machine-level analytics | Hold %, utilization, jackpot frequency |
| 👤 **Player 360 View** | Customer analytics | Segments, lifetime value, visit patterns |
| 📋 **Compliance Monitoring** | Regulatory reporting | CTR/SAR status, W-2G tracking, audit trails |
| ⚡ **Real-Time Floor Monitor** | Live casino status | Machine status, alerts, occupancy |

**Location:** `reports/report-definitions/`

See [Reports README](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/blob/main/reports/README.md) for import instructions.

---

### Can I customize the reports?

**Absolutely!** The reports are provided as starting templates.

**Customization Options:**
1. **Edit in Power BI Desktop:**
   - Open `.pbip` files
   - Modify visuals, add pages
   - Adjust DAX measures

2. **Create New Reports:**
   - Connect to existing semantic model
   - Build custom visuals
   - Apply your branding

3. **Add Custom DAX:**
   ```dax
   // Example: Average Daily Theo per Player
   Avg Daily Theo = 
   DIVIDE(
       SUM(gold_player_360[total_theo]),
       DISTINCTCOUNT(gold_player_360[player_id])
   )
   ```

**Best Practice:** Copy template first, then customize.

---

### How do I implement Row-Level Security (RLS)?

<details>
<summary>🔒 Click to see RLS implementation</summary>

**Use Case:** Users should only see data for their casino property.

**Step 1: Create Role in Semantic Model**
1. Open semantic model in Power BI Desktop
2. Go to **Modeling** > **Manage roles**
3. Create role: `PropertyFilter`
4. Add DAX filter:

```dax
[PropertyID] = LOOKUPVALUE(
    UserPropertyMapping[PropertyID],
    UserPropertyMapping[UserEmail],
    USERPRINCIPALNAME()
)
```

**Step 2: Test Role**
1. Click **Modeling** > **View as**
2. Select role and test user
3. Verify data is filtered correctly

**Step 3: Assign Users**
1. Publish report to Fabric workspace
2. Go to semantic model security settings
3. Add users/groups to roles

**Row-Level Security Patterns:**
- Filter by region: `[Region] = "West"`
- Filter by user email: `USERPRINCIPALNAME()`
- Dynamic filtering from lookup table

See [Security Guide - Row-Level Security](SECURITY.md#row-level-security-rls) for complete examples.

</details>

---

## 🔐 Security & Compliance

### What compliance frameworks are covered?

<details>
<summary>📋 Click to see compliance coverage</summary>

| Framework | Description | Implementation |
|-----------|-------------|----------------|
| 🎰 **NIGC MICS** | Minimum Internal Control Standards | Meter accuracy validation, drop count verification |
| 💰 **FinCEN BSA** | Bank Secrecy Act | CTR/SAR reporting, $10K threshold detection |
| 💳 **PCI-DSS** | Payment Card Industry | Card number masking, access controls |
| 🏛️ **State Gaming** | Jurisdiction Requirements | Configurable audit trails, retention policies |

**Compliance Features:**
- Automated CTR generation (>= $10,000)
- SAR pattern detection (structuring)
- W-2G auto-generation ($1,200 slots, $600 keno)
- 5-year data retention policies

See [Security Guide - Compliance Requirements](SECURITY.md#-compliance-requirements).

</details>

---

### How is PII protected?

<details>
<summary>🔐 Click to see PII handling</summary>

**Default PII Protection:**

| PII Type | Method | Example |
|----------|--------|---------|
| SSN | Hashed (SHA-256) + Masked | `XXX-XX-1234` |
| Names | First initial only | `J*** S***` |
| Credit Cards | Masked last 4 digits | `****-****-****-1234` |
| Phone | Partial mask | `(***) ***-4567` |
| Email | Domain only | `j***@example.com` |

**Bronze Layer:** Raw PII hashed/masked on ingestion
**Silver Layer:** Only hashed values, no raw PII
**Gold Layer:** No PII, only aggregated/anonymized data

**Sample Data:** All provided sample data has PII pre-masked.

**Testing Only:** Use `--include-pii` flag for development (never in production).

See [Security Guide - PII Handling](SECURITY.md#pii-handling).

</details>

---

### How are secrets managed?

**Never commit secrets to Git!** This repository has multiple protections:

✅ **`.gitignore`**: Blocks common secret files
✅ **Pre-commit hook**: Scans for high-risk patterns
✅ **`.env.sample`**: Provides template without secrets
✅ **Sample data**: All PII masked

**Best Practices:**
1. Use `.env` files locally (gitignored)
2. Store production secrets in Azure Key Vault
3. Use managed identities for Azure authentication
4. Enable the pre-commit hook:
   ```bash
   git config core.hooksPath .githooks
   ```

**If you accidentally commit a secret:**
1. Assume it's compromised - rotate immediately
2. Remove from Git history with BFG Repo-Cleaner
3. Report per your security policy

See [Security Guide - Repository Security](SECURITY.md#-repository-security).

---

### What network security options are available?

<details>
<summary>🌐 Click to see network security</summary>

**Private Endpoint Support:**
- Azure Storage (ADLS Gen2)
- Key Vault
- Microsoft Purview
- Log Analytics

**Network Security Groups (NSG):**
- Restrict inbound/outbound traffic
- Segment subnets by function
- Deny-by-default rules

**Fabric Network Isolation:**
- Connect Fabric workspace to VNet (Preview)
- Private endpoints for OneLake
- Firewall rules for managed endpoints

**Configuration:**
Edit `infra/modules/network.bicep` to enable private endpoints.

See [Security Guide - Network Security](SECURITY.md#-network-security).

</details>

---

## 🔧 Troubleshooting

### Notebook fails with "Capacity not available"

**Cause:** Fabric capacity is paused or inactive.

**Fix:**
1. Go to [Fabric Admin Portal](https://app.fabric.microsoft.com/admin-portal)
2. Navigate to **Capacity settings**
3. Ensure capacity status is **Active**
4. If paused, click **Resume**

**Prevention:** Disable auto-pause for POC demos.

---

### "Cannot connect to Lakehouse" error

<details>
<summary>🔍 Click to see debugging steps</summary>

**Check 1: Lakehouse exists**
```python
# In notebook
%run ./_notebook_config

# Should show lakehouse tables
display(spark.catalog.listTables())
```

**Check 2: Workspace permissions**
- Verify you have Member or Admin role
- Check workspace settings > Users & permissions

**Check 3: Lakehouse attached to notebook**
1. Open notebook
2. Click **Add Lakehouse** in left pane
3. Select existing Lakehouse
4. Click **Add**

**Check 4: Capacity active**
Ensure Fabric capacity is not paused.

</details>

---

### Delta table "file not found" errors

**Cause:** Delta transaction log corruption or incomplete writes.

**Fix:**
```python
# Repair Delta table
from delta.tables import DeltaTable

DeltaTable.forPath(spark, "Tables/bronze_slot_telemetry").generate("symlink_format_manifest")

# Or vacuum old files
DeltaTable.forPath(spark, "Tables/bronze_slot_telemetry").vacuum()
```

**Prevention:** Use proper DataFrame writes with checkpoints.

---

### Power BI reports show "Unable to connect"

<details>
<summary>🔍 Click to see connection debugging</summary>

**Check 1: Semantic model exists**
1. Go to workspace
2. Verify semantic model is published
3. Click semantic model > Settings
4. Check data source credentials

**Check 2: Direct Lake requirements**
- Gold tables must be Delta format
- Tables must be in OneLake
- Workspace must be on Fabric capacity

**Check 3: Permissions**
- User must have Build permission on semantic model
- Or Viewer permission for read-only

**Check 4: Refresh semantic model**
1. Open semantic model
2. Click **Refresh now**
3. Check refresh history for errors

</details>

---

### Data generator produces "invalid schema" warnings

**Cause:** Schema mismatch between generator and expected Bronze schema.

**Fix:**
```bash
# Update to latest generator code
git pull origin main

# Or specify schema version
python generate.py --all --schema-version 1.1
```

**Workaround:** Use `mergeSchema` when reading:
```python
df = spark.read.format("parquet") \
    .option("mergeSchema", "true") \
    .load("Files/bronze/")
```

---

### "Out of memory" errors during data processing

<details>
<summary>💾 Click to see memory optimization</summary>

**Cause:** Processing too much data at once or inefficient code.

**Fix 1: Process in batches**
```python
# Bad: Load entire dataset
df = spark.read.format("delta").load("Tables/bronze_slot_telemetry")

# Good: Filter first
df = spark.read.format("delta").load("Tables/bronze_slot_telemetry") \
    .filter("event_date >= '2024-01-01'")
```

**Fix 2: Repartition data**
```python
df.repartition(10).write.format("delta").save("Tables/silver_slot_clean")
```

**Fix 3: Increase capacity**
- Use larger Fabric SKU temporarily
- Or reduce data volume for POC

**Fix 4: Optimize DataFrame operations**
- Use `select()` to limit columns early
- Avoid `collect()` on large datasets
- Use `coalesce()` instead of `repartition()` when reducing partitions

</details>

---

## 💰 Cost & Licensing

### What will this POC cost me?

**Quick Estimates:**

| Scenario | Duration | Capacity | Estimated Cost |
|----------|----------|----------|----------------|
| 🧪 **POC Demo** | 3 days | F64 (24 hrs/day) | **$35-50** |
| 🔧 **Development** | 1 month | F4 (8 hrs/day, weekdays) | **$175-265** |
| 🏭 **Production Pilot** | 1 month | F64 (24/7) | **$8,500-9,500** |

**Cost Breakdown (1-month F64 24/7):**
- Fabric Capacity: ~$8,500 (80%)
- ADLS Gen2 Storage: ~$500 (5%)
- Purview: ~$800 (8%)
- Other services: ~$700 (7%)

**Major Cost Driver:** Fabric capacity (75-80% of total cost).

See [Cost Estimation Guide](COST_ESTIMATION.md) for detailed scenarios.

---

### How can I reduce costs?

<details>
<summary>💡 Click to see cost optimization strategies</summary>

**Strategy 1: Pause/Resume Capacity**
```bash
# Pause capacity when not in use
az fabric capacity pause --name "fabric-casino-poc"

# Resume when needed
az fabric capacity resume --name "fabric-casino-poc"
```
**Savings:** Up to 76% for development environments (8 hrs/day vs 24/7)

---

**Strategy 2: Use Smaller SKU for Dev**
- Development: F4 ($530/month 24/7) or F2 ($265/month 24/7)
- Staging: F16 ($2,120/month 24/7)
- Production only: F64 ($8,480/month 24/7)

**Savings:** 93% for dev environments (F4 vs F64)

---

**Strategy 3: Reserved Capacity**
- 1-year commitment: Save 25-30%
- 3-year commitment: Save 35-40%

**Example:** F64 reserved 1-year: ~$6,000-7,000/month (vs $8,500)

---

**Strategy 4: Storage Lifecycle Policies**
```bash
# Move cold data to Cool tier after 30 days
az storage blob lifecycle-management set \
  --policy @lifecycle-policy.json \
  --account-name $STORAGE_ACCOUNT_NAME
```
**Savings:** 50% on storage costs for archival data

---

**Strategy 5: Schedule-Based Automation**
```powershell
# Automated pause/resume schedule
# Run via Azure Automation or GitHub Actions
Start-FabricCapacity -Time "08:00" -Days "Mon-Fri"
Stop-FabricCapacity -Time "18:00" -Days "Mon-Fri"
```

---

See [Cost Estimation - Optimization Strategies](COST_ESTIMATION.md#cost-optimization-strategies).

</details>

---

### Do I need to pay for Power BI separately?

**Short Answer:** Maybe, depends on your usage.

**Licensing Options:**

| Scenario | License Required | Cost |
|----------|------------------|------|
| Create reports/semantic models | Power BI Pro or PPU | $10-20/user/month |
| View reports (Fabric capacity) | Free license | $0 |
| View reports (non-Fabric) | Power BI Pro | $10/user/month |
| Enterprise distribution | Premium capacity or Fabric | Capacity cost |

**POC Recommendation:**
1. Use Power BI Pro trial (60 days free)
2. Publish to Fabric workspace
3. Viewers can use free licenses

**Note:** Fabric capacity is already included in your F64 cost estimate - it provides Power BI Premium features.

---

### What about Azure free tier/credits?

**Azure Free Tier:**
- ❌ Microsoft Fabric not included in free tier
- ✅ Some supporting services (Storage, Key Vault) have free allowances

**Azure Credits:**
- ✅ Can use Fabric with Azure credits (students, startups)
- ✅ Visual Studio subscriptions include monthly credits

**Free Trials:**
- Power BI Pro: 60-day trial
- Fabric capacity: Trial available via Microsoft
- Azure subscription: $200 credit for 30 days (new customers)

**POC on a Budget:**
- Use F2 capacity ($265/month or ~$9/day)
- Pause when not in use
- Limit to 3-day POC demo ($27-35 total)

---

## 🐳 Docker & Dev Containers

### What's the difference between Docker and Dev Container?

| Feature | Docker | Dev Container |
|---------|--------|---------------|
| **Purpose** | Run data generators | Full development environment |
| **Requires** | Docker Desktop only | Docker + VS Code |
| **What's Inside** | Python + generators | Python + Azure CLI + Bicep + extensions |
| **Use Case** | Generate data quickly | Complete coding environment |
| **Persistent** | No | Yes (VS Code workspace) |

**Docker:** Run generators, validate data, stream to Event Hub
**Dev Container:** Complete development setup with all tools pre-installed

---

### How do I use Docker for data generation?

```bash
# Quick demo (7 days, small dataset)
docker-compose run --rm demo-generator

# Full dataset (30 days, production-like volumes)
docker-compose run --rm data-generator

# Custom parameters
docker-compose run --rm data-generator --all --days 14 --format csv

# Specific data domains
docker-compose run --rm data-generator --slots 100000 --players 5000
```

Output: `./output` directory

See [Docker Support](index.md#-docker-support) in main README.

---

### How do I use Dev Containers?

**Option 1: VS Code Local**
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Install [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
3. Open repository in VS Code
4. Click "Reopen in Container" when prompted

**Option 2: GitHub Codespaces (Zero Installation)**
1. Go to repository on GitHub
2. Click **Code** > **Codespaces** tab
3. Click **Create codespace on main**
4. Wait ~2 minutes for environment to build

**What You Get:**
- ✅ Python 3.11 with all dependencies
- ✅ Azure CLI + Bicep
- ✅ PowerShell 7
- ✅ Git configured
- ✅ All VS Code extensions pre-installed

---

### Docker commands are failing?

<details>
<summary>🔧 Click to see Docker troubleshooting</summary>

**Issue: `docker-compose: command not found`**

**Cause:** Docker Compose not installed or using wrong command

**Fix:**
```bash
# Docker Compose V2 (preferred)
docker compose run --rm data-generator

# Docker Compose V1 (legacy)
docker-compose run --rm data-generator
```

---

**Issue: `Cannot connect to Docker daemon`**

**Cause:** Docker Desktop not running

**Fix:** Start Docker Desktop application

---

**Issue: `Port 8080 already in use`**

**Cause:** Another service using the port

**Fix:**
```bash
# Change port in docker-compose.yml
ports:
  - "8081:8080"  # Use 8081 instead

# Or stop conflicting service
docker ps  # Find conflicting container
docker stop <container-id>
```

---

**Issue: `Image build fails`**

**Cause:** Network issues or missing dependencies

**Fix:**
```bash
# Rebuild without cache
docker-compose build --no-cache data-generator

# Or pull latest image
docker-compose pull
```

</details>

---

## 🏗️ Architecture Deep Dive

### Why Lakehouse instead of Warehouse for this POC?

The POC chose Lakehouse as the primary store for three reasons: (1) the diverse data formats across 9 industry verticals (Parquet, CSV, JSON) favor schema-on-read flexibility; (2) the PySpark-first notebook workflow aligns naturally with Lakehouse's Spark engine; and (3) Direct Lake mode provides zero-copy Power BI connectivity without Import refresh schedules. Warehouse is the better choice for T-SQL-heavy teams or migrations from Synapse Dedicated SQL Pool.

See: [DECISION_TREES.md](DECISION_TREES.md#1-lakehouse-vs-warehouse-vs-sql-database) | [Lakehouse/Warehouse/SQL DB Decision Guide](best-practices/lakehouse-warehouse-sqldb-decision-guide.md)

---

### What goes in each medallion layer?

| Layer | Content | Schema | Retention |
|-------|---------|--------|-----------|
| **Bronze** | Raw ingested data, append-only, minimal transformation | Schema-on-read, source schema preserved | Full history |
| **Silver** | Cleansed, deduplicated, validated, enriched data | Schema-on-write, enforced constraints | Full history |
| **Gold** | Business aggregations, KPIs, star schema fact/dim tables | Star schema, V-Order optimized for Direct Lake | Rolling window or full |

The key principle: Bronze is append-only (never modify source records), Silver deduplicates and validates (MERGE upserts), Gold aggregates for consumption (overwrite on refresh).

See: [Medallion Architecture Deep Dive](best-practices/medallion-architecture-deep-dive.md)

---

### How should I design workspaces?

The recommended pattern for this POC is a **per-environment** workspace layout:

| Workspace | Purpose | Capacity |
|-----------|---------|----------|
| `ws-fabric-poc-dev` | Development, notebook authoring | F4 (dev) |
| `ws-fabric-poc-staging` | Integration testing, UAT | F16 (staging) |
| `ws-fabric-poc-prod` | Production workloads | F64 (prod) |

Each workspace contains three Lakehouses (`lh_bronze`, `lh_silver`, `lh_gold`), one Warehouse (for T-SQL consumers), and one Eventhouse (for real-time). For multi-tenant scenarios, see [Multi-Tenant Workspace Architecture](best-practices/multi-tenant-workspace-architecture.md).

See: [Workspace Naming](best-practices/01_WORKSPACES_NAMING.md)

---

### When should I use shortcuts vs. copying data?

Use **shortcuts** when you want to query data in-place without storage duplication (e.g., referencing ADLS Gen2 landing zones or cross-workspace tables). Use **copy** (pipeline Copy Activity) when you need to transform data during ingestion, the source requires a data gateway, or you want full control over the data lifecycle in OneLake. Shortcuts are free (no storage cost); copies consume storage.

See: [DECISION_TREES.md](DECISION_TREES.md#5-mirroring-vs-shortcuts-vs-pipeline-copy) | [Shortcut Transformations Notebook](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/blob/main/notebooks/bronze/17_bronze_shortcut_transformations.py)

---

### What is Workspace Identity and when do I need it?

Workspace Identity is a managed identity scoped to a Fabric workspace. It enables credential-free authentication to Azure resources (Storage, Key Vault, Purview) from notebooks and pipelines -- no service principal secrets to rotate. Use it whenever your notebooks access Azure resources. The POC deploys it via `infra/modules/security/workspace-identity.bicep`.

See: [OneLake Security](features/onelake-security.md) | [Workspace Identity Module](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/blob/main/infra/modules/security/workspace-identity.bicep)

---

## ⚡ Performance Tuning

### What is V-Order and do I need it?

V-Order is a write-time optimization for Parquet files that dramatically improves Direct Lake query performance. It reorders data within row groups for optimal column compression and scan efficiency. You need it on every Gold table that feeds a Power BI semantic model via Direct Lake. Enable it with:

```python
spark.conf.set("spark.sql.parquet.vorder.enabled", "true")
```

Or apply retroactively: `OPTIMIZE gold_table_name USING VORDER`.

See: [Direct Lake](features/direct-lake.md) | [Performance & Parallelism](best-practices/performance-parallelism.md)

---

### How should I partition large tables?

Partition by the most common filter column (typically a date column). For this POC, Bronze and Silver tables partition by `event_date` for efficient time-range queries. Rules of thumb:

- **Partition size target:** 256 MB - 1 GB per partition
- **Do not over-partition:** Avoid partitioning by high-cardinality columns (player_id) -- too many small files
- **Combine with Z-Order:** `OPTIMIZE table ZORDER BY (property_id)` within each partition for multi-column filtering

See: [Performance & Parallelism](best-practices/performance-parallelism.md) | [Medallion Deep Dive](best-practices/medallion-architecture-deep-dive.md)

---

### What Spark settings should I tune first?

For POC-scale data (~700K-1M records per table), the most impactful settings are:

| Setting | POC Value | Default | Why |
|---------|-----------|---------|-----|
| `spark.sql.shuffle.partitions` | 8 | 200 | POC data is small; 200 partitions creates too many tiny files |
| `spark.sql.parquet.vorder.enabled` | true | false | Required for Direct Lake performance |
| `spark.sql.autoBroadcastJoinThreshold` | 10485760 | 10485760 | 10 MB is fine for POC dimension tables |
| `spark.sql.adaptive.enabled` | true | true | AQE auto-tunes at runtime |

See: [CHEAT_SHEETS.md](CHEAT_SHEETS.md#spark-configuration-for-fabric) | [Spark Notebooks Best Practices](best-practices/05_SPARK_NOTEBOOKS.md)

---

### How do I prevent Direct Lake fallback to DirectQuery?

Direct Lake falls back to DirectQuery when: (1) the model contains calculated tables; (2) column cardinality exceeds guardrails; (3) the query uses unsupported DAX patterns. To prevent fallback:

1. Move all calculated tables into Gold notebooks (materialize as Delta tables)
2. Pre-aggregate high-cardinality columns in Gold layer
3. Monitor fallback using Power BI Performance Analyzer
4. Keep Gold tables V-Order optimized

See: [Direct Lake](features/direct-lake.md) | [CHEAT_SHEETS.md](CHEAT_SHEETS.md#direct-lake-specific)

---

## 🤖 MLOps & AI

### What ML models does this POC include?

The POC includes three ML notebooks:

| Notebook | Model | Purpose | Algorithm |
|----------|-------|---------|-----------|
| `01_ml_player_churn_prediction.py` | Player Churn | Predict player attrition risk | Gradient Boosted Trees |
| `02_ml_fraud_detection.py` | Fraud Detection | Identify anomalous transactions | Isolation Forest |
| `03_ml_automl_weather_forecasting.py` | Weather Forecast | Predict weather patterns (NOAA data) | AutoML |

All models use MLflow for experiment tracking and model registry.

See: [ML Notebooks](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/blob/main/notebooks/ml/) | [AutoML Model Endpoints](features/automl-model-endpoints.md)

---

### How does model versioning work in Fabric?

Fabric uses MLflow's model registry natively. Models are logged during training with `mlflow.log_model()`, registered in the workspace model registry, and versioned automatically. Fabric's ML model item provides a UI for version comparison, stage transitions (Staging/Production), and deployment to endpoints.

See: [AutoML Model Endpoints](features/automl-model-endpoints.md)

---

### Can I use AI Functions in notebooks?

Yes. Fabric AI Functions (`ai_summarize`, `ai_classify`, `ai_translate`, etc.) are available in Spark SQL for inline LLM-powered transformations. The POC demonstrates compliance-aware usage in `17_gold_ai_functions_compliance.py`, including token cost estimation and PII guardrails.

See: [AI Copilot Configuration](features/ai-copilot-configuration.md) | [AI Functions Notebook](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/blob/main/notebooks/gold/17_gold_ai_functions_compliance.py)

---

### What about Data Agents?

Data Agents are autonomous AI-powered analytics assistants that can answer natural language questions about your data. They run inside Fabric workspaces with governed access to Lakehouses and Warehouses. The POC documents configuration patterns but does not deploy a live agent (requires tenant admin enablement).

See: [Data Agents](features/data-agents.md) | [Fabric IQ](features/fabric-iq.md)

---

## 🔄 Migrations

### How do I migrate from Synapse Analytics?

The migration path depends on your current Synapse component:

| Synapse Component | Fabric Equivalent | Migration Approach |
|---|---|---|
| Dedicated SQL Pool | Warehouse | T-SQL compatible; CTAS scripts transfer directly |
| Serverless SQL Pool | Lakehouse SQL endpoint | Repoint external tables to OneLake |
| Spark Pool | Fabric Spark | Notebooks largely compatible; update `dbutils` to `mssparkutils` |
| Pipelines | Fabric Pipelines | JSON-compatible with minor activity type changes |
| Data Explorer | Eventhouse | KQL fully compatible; export/import databases |

See: [Migration Patterns](best-practices/migration-patterns.md) | [Tutorial 13: Migration Planning](tutorials/13-migration-planning/README.md)

---

### How do I migrate from Databricks?

Key differences to address:

1. **Runtime:** Replace `dbutils` with `mssparkutils` (file system, credentials, notebook orchestration)
2. **Unity Catalog:** Map to Fabric OneLake + Purview for governance
3. **Delta Lake:** Fully compatible -- Delta tables work as-is in OneLake
4. **MLflow:** Supported natively in Fabric
5. **Notebook format:** Databricks notebook source format imports directly

The POC notebooks already use the Databricks notebook format with `# COMMAND ----------` separators. Phase 11 remediation ensured all `dbutils` references were replaced with `mssparkutils`.

See: [Migration Patterns](best-practices/migration-patterns.md)

---

### How do I migrate from Snowflake?

Use Fabric Mirroring for continuous replication from Snowflake into OneLake (Delta format). This provides near-real-time sync without building custom ETL. Alternatively, use Snowflake's `COPY INTO` to export to ADLS Gen2, then create Lakehouse shortcuts to the exported data.

See: [Mirroring](features/mirroring.md) | [Tutorial 24: Snowflake to Fabric](tutorials/24-snowflake-to-fabric/README.md)

---

### What about Teradata and IBM DB2?

Both are covered in the POC:

- **Teradata:** Tutorial 10 covers TPT export patterns and migration planning
- **IBM DB2:** Streaming notebook `04_ibm_db2_cdc.py` demonstrates CDC from DB2 z/OS and LUW with EBCDIC handling

For both, the typical pattern is: set up an on-premises Data Gateway, configure a pipeline Copy Activity, and land data in the Bronze Lakehouse.

See: [Tutorial 10: Teradata Migration](tutorials/10-teradata-migration/README.md) | [IBM DB2 CDC Notebook](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/blob/main/notebooks/streaming/04_ibm_db2_cdc.py)

---

## 🛠️ Dev Experience

### Can I develop notebooks locally?

Yes, but with caveats. Notebooks use the Databricks notebook format (`.py` files with `# COMMAND ----------` separators) and can be edited in any IDE. However, `mssparkutils` and `spark` are only available inside Fabric. The POC includes a `_get_arg` shim at the top of every notebook so code can run in both Fabric and local pytest:

```python
try:
    from notebookutils import mssparkutils
except ImportError:
    mssparkutils = None
```

The 612 unit tests in `validation/unit_tests/` validate notebook logic locally without a Fabric session.

See: [Testing Strategies](best-practices/testing-strategies.md)

---

### How does Git integration work with Fabric?

Fabric workspaces can connect to Azure DevOps or GitHub repos. Each Fabric item (notebook, pipeline, semantic model) is serialized as a JSON/YAML/Python file and synced bi-directionally. Best practice: establish a one-way flow (edit in IDE, push to Git, sync to Fabric) to avoid merge conflicts.

See: [Git Integration](features/git-integration.md) | [fabric-cicd Deployment](best-practices/fabric-cicd-deployment.md)

---

### What CI/CD tool should I use?

The POC uses two complementary approaches:

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **GitHub Actions** | Bicep IaC deployment, testing | `.github/workflows/deploy-fabric.yml` |
| **fabric-cicd** (Python) | Fabric item deployment (notebooks, pipelines) | `scripts/fabric-cicd-deploy.py` |

`fabric-cicd` is the Microsoft-recommended tool for deploying Fabric workspace items. It handles notebook uploads, pipeline definitions, and semantic model refreshes.

See: [fabric-cicd Deployment](best-practices/fabric-cicd-deployment.md) | [Tutorial 12: CI/CD DevOps](tutorials/12-cicd-devops/README.md)

---

### How do I run tests?

```bash
# All 612 unit tests
pytest validation/unit_tests/ -v

# By category
pytest validation/unit_tests/test_generators.py -v      # Casino (30 tests)
pytest validation/unit_tests/federal/ -v                 # Federal (54 tests)
pytest validation/unit_tests/streaming/ -v               # Streaming (20 tests)
pytest validation/unit_tests/analytics/ -v               # Analytics (30 tests)

# Data quality (Great Expectations)
great_expectations checkpoint run bronze_checkpoint
```

See: [Testing Strategies](best-practices/testing-strategies.md)

---

## 📜 Compliance Frameworks

### What compliance frameworks does this POC address?

| Framework | Domain | POC Implementation |
|-----------|--------|-------------------|
| **NIGC MICS** | Casino/Gaming | Meter accuracy validation, drop count verification, audit trails |
| **FinCEN BSA** | Casino/Financial | CTR (>$10K), SAR (structuring detection), W-2G auto-generation |
| **HIPAA** | Tribal Healthcare | PHI masking, audit logging, 42 CFR Part 2 substance abuse protections |
| **FedRAMP** | Federal (DOT/FAA) | Encryption at rest (CMK), private endpoints, audit logging |
| **SOX** | Financial | Immutable audit trails, access controls, data retention |
| **GDPR** | General | Data subject access rights, right to erasure (Delta DELETE) |
| **CCPA** | California | Consumer data inventory, opt-out mechanisms |
| **PCI-DSS** | Payment | Card number masking, Key Vault (HSM-backed) for card data |

See: [Security](SECURITY.md) | [SQL Audit Logs](best-practices/sql-audit-logs-compliance.md) | [CMK](best-practices/customer-managed-keys.md)

---

### How are CTR and SAR reports generated?

**Currency Transaction Reports (CTR):** Any cash transaction >= $10,000 triggers automatic CTR flagging in the Bronze compliance notebook (`04_bronze_compliance.py`). The Silver layer validates amounts and deadlines. The Gold layer (`03_gold_compliance_reporting.py`) produces FinCEN-ready reports.

**Suspicious Activity Reports (SAR):** The Silver layer detects structuring patterns -- multiple transactions between $8,000-$9,999 by the same individual within 24 hours. The fraud detection ML model (`02_ml_fraud_detection.py`) provides additional anomaly scoring.

See: [Compliance Reporting Notebook](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/blob/main/notebooks/gold/03_gold_compliance_reporting.py)

---

### How is HIPAA compliance handled?

Tribal Healthcare notebooks implement HIPAA safeguards:

1. **PHI Masking:** Silver layer (`07_silver_tribal_health.py`) masks protected health information
2. **Audit Logging:** Every data access is logged with user ID, timestamp, and data accessed
3. **FHIR R4 Mapping:** Data mapped to standardized FHIR R4 format for interoperability
4. **42 CFR Part 2:** Substance abuse treatment records have additional access restrictions
5. **Retention:** Log Analytics configured for >= 6 years (HIPAA requirement) via `log-analytics.bicep`

See: [Tribal Health Analytics](use-cases/tribal-health-analytics.md) | [Tutorial 30: Tribal Healthcare](tutorials/30-tribal-healthcare/README.md)

---

### What encryption options are available?

| Layer | Mechanism | Configuration |
|-------|-----------|---------------|
| **At Rest (default)** | Microsoft-managed keys (MMK) | Automatic, no config needed |
| **At Rest (enhanced)** | Customer-managed keys (CMK) | `infra/modules/storage/storage-account.bicep` with `enableCmk=true` |
| **In Transit** | TLS 1.2+ | Automatic for all Fabric endpoints |
| **Key Storage** | Azure Key Vault (HSM-backed for PCI-DSS) | `infra/modules/security/security.bicep` with `skuName='premium'` |
| **PII Fields** | Application-level hashing (SHA-256) | Implemented in Bronze notebooks (SSN, card numbers) |

See: [Customer-Managed Keys](best-practices/customer-managed-keys.md) | [Network Security](best-practices/network-security.md)

---

## 📚 Additional Resources

### Where can I learn more about Microsoft Fabric?

**Official Documentation:**
- [Microsoft Fabric Documentation](https://learn.microsoft.com/fabric/)
- [Fabric Architecture Center](https://learn.microsoft.com/fabric/get-started/architecture)
- [Fabric Pricing](https://azure.microsoft.com/pricing/details/microsoft-fabric/)

**Community Resources:**
- [Microsoft Fabric Blog](https://blog.fabric.microsoft.com/)
- [Microsoft Fabric Community](https://community.fabric.microsoft.com/)
- [Power BI Community](https://community.powerbi.com/)

**Training:**
- [Microsoft Learn: Fabric Learning Path](https://learn.microsoft.com/training/browse/?products=fabric)
- [Data Engineering with Fabric](https://learn.microsoft.com/training/paths/get-started-fabric/)

---

### Where do I report issues or contribute?

**GitHub Repository:**
- 🐛 **Report bugs**: [Open an issue](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/issues)
- 💡 **Feature requests**: [Start a discussion](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/discussions)
- 🔧 **Pull requests**: See [Contributing Guide](CONTRIBUTING.md)

**Before Opening an Issue:**
1. Check existing issues for duplicates
2. Review FAQ (this document)
3. Include reproduction steps
4. Provide error messages and logs

---

### How do I stay updated?

**Watch the Repository:**
- Click **Watch** on GitHub
- Choose notification preferences

**Release Notes:**
- Check [CHANGELOG.md](CHANGELOG.md) for version history
- Subscribe to releases on GitHub

**Social Media:**
- Follow Microsoft Fabric on Twitter
- Join the LinkedIn Fabric community

---

## 🎯 Quick Reference

### Essential Links

| Resource | Link |
|----------|------|
| 🏠 **Main README** | [README.md](index.md) |
| 🏗️ **Architecture** | [ARCHITECTURE.md](ARCHITECTURE.md) |
| 🚀 **Deployment** | [DEPLOYMENT.md](DEPLOYMENT.md) |
| 📋 **Prerequisites** | [PREREQUISITES.md](PREREQUISITES.md) |
| 🔐 **Security** | [SECURITY.md](SECURITY.md) |
| 💰 **Cost Estimation** | [COST_ESTIMATION.md](COST_ESTIMATION.md) |
| 📖 **Tutorials** | [tutorials/](tutorials/index.md) |
| 🎲 **Data Generation** | [data_generation/](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/tree/main/data_generation) |
| 📊 **Reports** | [reports/](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/tree/main/reports) |
| 📅 **POC Agenda** | [poc-agenda/](poc-agenda/README.md) |

---

### Command Cheat Sheet

```bash
# Deployment
az deployment sub create --location eastus2 --template-file infra/main.bicep --parameters infra/environments/dev/dev.bicepparam

# Data Generation
docker-compose run --rm data-generator --all --days 30

# Verify
./scripts/verify-deployment.sh

# Cleanup
az group delete --name "rg-fabric-poc-dev" --yes
```

---

### Support

**Need help?** Try these resources in order:

1. 📖 Check this FAQ
2. 🔍 Search [existing issues](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/issues)
3. 💬 Ask in [GitHub Discussions](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/discussions)
4. 🐛 [Open a new issue](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/issues/new)

---

[⬆️ Back to top](#-frequently-asked-questions-faq)

---

> 📖 **Documentation maintained by:** Microsoft Fabric POC Team
> 🔗 **Repository:** [Suppercharge_Microsoft_Fabric](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric)
> 🔄 **Last Updated:** 2025-01-21
