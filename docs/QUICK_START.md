# ⚡ Quick Start Guide

> 🏠 [Home](index.md) > 📚 [Docs](./) > ⚡ Quick Start

**Get your Microsoft Fabric Casino Analytics POC running in 5 minutes.**

---

## ✅ What You Need

| Requirement | Details |
|------------|---------|
| **Azure Subscription** | With Contributor access |
| **Fabric Capacity** | F64 SKU (or F2 for testing) |
| **Fabric Enabled** | In your Azure AD tenant |
| **Tools** | Azure CLI + Bicep installed |

> 💡 **No Fabric capacity yet?** Use a [Fabric trial](https://learn.microsoft.com/fabric/get-started/fabric-trial) to get started free.

---

## 🚀 5 Steps to Running

### Step 1: Clone & Configure

```bash
# Clone the repository
git clone https://github.com/YOUR_ORG/Supercharge_Microsoft_Fabric.git
cd Supercharge_Microsoft_Fabric

# Copy environment template
cp .env.sample .env

# Edit with your values
code .env
```

**Required `.env` values:**
```bash
AZURE_SUBSCRIPTION_ID=<your-subscription-id>
AZURE_TENANT_ID=<your-tenant-id>
AZURE_LOCATION=eastus2
FABRIC_CAPACITY_SKU=F64
PROJECT_PREFIX=casinopoc
```

---

### Step 2: Login & Register Providers

```bash
# Login to Azure
az login

# Register required providers (one-time)
az provider register --namespace Microsoft.Fabric
az provider register --namespace Microsoft.Purview
az provider register --namespace Microsoft.Storage
```

---

### Step 3: Deploy Infrastructure

```bash
# Validate the deployment
az deployment sub what-if \
  --location eastus2 \
  --template-file infra/main.bicep \
  --parameters infra/environments/dev/dev.bicepparam

# Deploy (takes ~10 minutes)
az deployment sub create \
  --location eastus2 \
  --template-file infra/main.bicep \
  --parameters infra/environments/dev/dev.bicepparam
```

---

### Step 4: Generate Sample Data

```bash
# Install Python dependencies
pip install -r requirements.txt

# Generate 1 hour of casino data
python data-generation/run_generators.py --duration 1h

# Or use Docker
docker-compose up data-generator
```

---

### Step 5: Run Your First Notebook

1. Open [Microsoft Fabric](https://app.fabric.microsoft.com)
2. Navigate to your workspace: `ws-casinopoc-dev`
3. Import notebook: `notebooks/bronze/01_bronze_slot_telemetry.py`
4. Click **Run All**

![Fabric Workspace Settings](https://learn.microsoft.com/en-us/fabric/fundamentals/media/workspaces/workspace-settings-cog.png)

*Source: [Microsoft Fabric Workspaces Documentation](https://learn.microsoft.com/en-us/fabric/fundamentals/workspaces)*

---

## ✔️ Verify Success

### Create Your Lakehouse

Before running notebooks, create a Lakehouse in your workspace:

1. In your workspace, click **+ New** > **Lakehouse**
2. Name it `lh_bronze_casino`
3. Click **Create**

![Creating a New Warehouse in Fabric](https://learn.microsoft.com/en-us/fabric/data-warehouse/media/create-warehouse/new-warehouse.png)

*Source: [Create a Warehouse in Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/data-warehouse/create-warehouse)*

### Check Bronze Layer Created

```python
# Run in Fabric notebook
df = spark.read.format("delta").load("Tables/bronze_slot_telemetry")
display(df.limit(10))
```

**Expected Output:**
| machine_id | casino_id | event_type | amount | timestamp |
|------------|-----------|------------|--------|-----------|
| SLOT-001 | VENUE-A | SPIN | 2.50 | 2025-01-22T10:00:00 |
| SLOT-001 | VENUE-A | WIN | 15.00 | 2025-01-22T10:00:05 |

### Verify Tables Exist

```sql
-- Run in Fabric SQL endpoint
SHOW TABLES IN bronze;
```

**Expected:** `bronze_slot_telemetry`, `bronze_player_profile`, `bronze_financial_txn`

---

## 📍 Where to Go Next

| Task | Tutorial |
|------|----------|
| **Build Silver Layer** | [02-silver-layer](tutorials/02-silver-layer/) |
| **Create Gold Aggregations** | [03-gold-layer](tutorials/03-gold-layer/) |
| **Set Up Real-Time** | [04-real-time-analytics](tutorials/04-real-time-analytics/) |
| **Connect Power BI** | [05-direct-lake-powerbi](tutorials/05-direct-lake-powerbi/) |

### Quick Commands Reference

```bash
# View deployment status
az deployment sub show --name main --query properties.provisioningState

# Check Fabric workspace
az fabric workspace list --output table

# Tail data generator logs
docker-compose logs -f data-generator
```

---

## ❓ Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| **Deployment fails** | Check quota: `az quota show --scope /subscriptions/{id}/providers/Microsoft.Fabric/locations/eastus2 --resource-name F64` |
| **No tables appear** | Wait 2-3 minutes after notebook run; refresh Lakehouse |
| **Permission denied** | Verify Fabric workspace access in Fabric portal |
| **Notebook timeout** | Increase capacity SKU or reduce data volume |

---

> 📚 **Full Documentation:** [Prerequisites](PREREQUISITES.md) | [Architecture](ARCHITECTURE.md) | [Deployment](DEPLOYMENT.md)

---

**Total Time:** ~10-15 minutes (mostly deployment wait time)
