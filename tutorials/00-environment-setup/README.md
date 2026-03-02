# Tutorial 00: Environment Setup

> **🏠 [Home](../../index.md)** > **📖 [Tutorials](../index.md)** > **⚙️ Environment Setup**

---

<div align="center">

![Difficulty](https://img.shields.io/badge/⭐_Difficulty-Beginner-brightgreen?style=for-the-badge)
![Duration](https://img.shields.io/badge/⏱️_Duration-45--60_mins-blue?style=for-the-badge)
![Prerequisites](https://img.shields.io/badge/📋_Prerequisites-Azure_Subscription-orange?style=for-the-badge)

</div>

---

## 🎓 Tutorial 00: Environment Setup

| | |
|---|---|
| **Difficulty** | ⭐ Beginner |
| **Time** | ⏱️ 30-45 minutes |
| **Prerequisites** | Azure subscription with Fabric enabled |

---

### 📍 Progress Tracker

<div align="center">

<table>
<thead>
<tr>
<th align="center" width="10%">Tutorial</th>
<th align="left" width="45%">Name</th>
<th align="center" width="15%">Status</th>
<th align="center" width="15%">Duration</th>
<th align="center" width="15%">Difficulty</th>
</tr>
</thead>
<tbody>
<tr style="background-color: #e8f5e9;">
<td align="center"><strong>00</strong></td>
<td><strong>👉 <a href="../00-environment-setup/README.md">Environment Setup</a></strong></td>
<td align="center"><img src="https://img.shields.io/badge/●-CURRENT-blue?style=flat-square" alt="Current"></td>
<td align="center">45-60 min</td>
<td align="center">⭐ Beginner</td>
</tr>
<tr>
<td align="center">01</td>
<td><a href="../01-bronze-layer/README.md">🥉 Bronze Layer</a></td>
<td align="center"><img src="https://img.shields.io/badge/○-TODO-lightgrey?style=flat-square" alt="Todo"></td>
<td align="center">60-90 min</td>
<td align="center">⭐ Beginner</td>
</tr>
<tr>
<td align="center">02</td>
<td><a href="../02-silver-layer/README.md">🥈 Silver Layer</a></td>
<td align="center"><img src="https://img.shields.io/badge/○-TODO-lightgrey?style=flat-square" alt="Todo"></td>
<td align="center">60-90 min</td>
<td align="center">⭐⭐ Intermediate</td>
</tr>
<tr>
<td align="center">03</td>
<td><a href="../03-gold-layer/README.md">🥇 Gold Layer</a></td>
<td align="center"><img src="https://img.shields.io/badge/○-TODO-lightgrey?style=flat-square" alt="Todo"></td>
<td align="center">90-120 min</td>
<td align="center">⭐⭐ Intermediate</td>
</tr>
<tr>
<td align="center">04</td>
<td><a href="../04-real-time-analytics/README.md">⚡ Real-Time Analytics</a></td>
<td align="center"><img src="https://img.shields.io/badge/○-TODO-lightgrey?style=flat-square" alt="Todo"></td>
<td align="center">90-120 min</td>
<td align="center">⭐⭐⭐ Advanced</td>
</tr>
<tr>
<td align="center">05</td>
<td><a href="../05-direct-lake-powerbi/README.md">📊 Direct Lake & Power BI</a></td>
<td align="center"><img src="https://img.shields.io/badge/○-TODO-lightgrey?style=flat-square" alt="Todo"></td>
<td align="center">60-90 min</td>
<td align="center">⭐⭐ Intermediate</td>
</tr>
<tr>
<td align="center">06</td>
<td><a href="../06-data-pipelines/README.md">🔄 Data Pipelines</a></td>
<td align="center"><img src="https://img.shields.io/badge/○-TODO-lightgrey?style=flat-square" alt="Todo"></td>
<td align="center">60-90 min</td>
<td align="center">⭐⭐ Intermediate</td>
</tr>
<tr>
<td align="center">07</td>
<td><a href="../07-governance-purview/README.md">🛡️ Governance & Purview</a></td>
<td align="center"><img src="https://img.shields.io/badge/○-TODO-lightgrey?style=flat-square" alt="Todo"></td>
<td align="center">60-90 min</td>
<td align="center">⭐⭐ Intermediate</td>
</tr>
<tr>
<td align="center">08</td>
<td><a href="../08-database-mirroring/README.md">🔄 Database Mirroring</a></td>
<td align="center"><img src="https://img.shields.io/badge/○-TODO-lightgrey?style=flat-square" alt="Todo"></td>
<td align="center">60-90 min</td>
<td align="center">⭐⭐ Intermediate</td>
</tr>
<tr>
<td align="center">09</td>
<td><a href="../09-advanced-ai-ml/README.md">🤖 Advanced AI/ML</a></td>
<td align="center"><img src="https://img.shields.io/badge/○-TODO-lightgrey?style=flat-square" alt="Todo"></td>
<td align="center">90-120 min</td>
<td align="center">⭐⭐⭐ Advanced</td>
</tr>
</tbody>
</table>

<p><em>💡 Tip: Click any tutorial name to jump directly to it</em></p>

</div>

---

| Navigation | |
|---|---|
| **Previous** | N/A - This is the first tutorial |
| **Next** | [01-Bronze Layer](../01-bronze-layer/README.md) ➡️ |

---

## 📖 Overview

This tutorial guides you through setting up your Microsoft Fabric environment for the Casino/Gaming POC. You will create the foundational workspace and Lakehouse infrastructure needed for the medallion architecture.

```mermaid
graph LR
    subgraph "What We're Building"
        A[Azure Subscription] --> B[Fabric Workspace]
        B --> C[🥉 lh_bronze]
        B --> D[🥈 lh_silver]
        B --> E[🥇 lh_gold]
    end
```

---

## 🎯 Learning Objectives

By the end of this tutorial, you will be able to:

- [ ] Understand Microsoft Fabric workspace structure
- [ ] Create and configure a Fabric workspace
- [ ] Create Lakehouses for the medallion architecture
- [ ] Connect to Azure Data Lake Storage
- [ ] Configure workspace settings and access

---

## 📋 Prerequisites

Before starting, ensure you have:

- [ ] Azure subscription with Fabric enabled
- [ ] Fabric capacity (F64 recommended, F2 minimum for POC)
- [ ] Azure CLI installed locally (optional)
- [ ] Access to Fabric portal (app.fabric.microsoft.com)

> 📋 **Prerequisites:** If you don't have a Fabric capacity, you can start a free trial at [app.fabric.microsoft.com](https://app.fabric.microsoft.com). Trial capacity provides 60 days of limited compute units.

---

## 🛠️ Step 1: Access Microsoft Fabric

1. Navigate to [Microsoft Fabric](https://app.fabric.microsoft.com)
2. Sign in with your Azure AD / Entra ID account
3. Verify you see the Fabric home page

### Verify Capacity Access

1. Click on **Settings** (gear icon) in the top right
2. Select **Admin portal** (if you have admin access)
3. Navigate to **Capacity settings**
4. Confirm your Fabric capacity is available and running

![Fabric Workspace Contact List](https://learn.microsoft.com/en-us/fabric/get-started/media/create-workspaces/fabric-contact-list.png)

*Source: [Create workspaces in Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/get-started/create-workspaces)*

> ⚠️ **Warning:** If your capacity is paused, notebooks and data processing will not work. Ensure the capacity is in "Active" state before proceeding. Resume can take 2-3 minutes.

---

## 🛠️ Step 2: Create Workspace

### Create a New Workspace

1. In the left navigation, click **Workspaces**
2. Click **+ New workspace**
3. Configure the workspace:

   | Setting | Value |
   |---------|-------|
   | Name | `casino-fabric-poc` |
   | Description | Casino/Gaming Fabric POC - Medallion Architecture |
   | License mode | Fabric capacity |
   | Capacity | Select your Fabric capacity |

4. Click **Apply**

![Pin Workspace to Favorites](https://learn.microsoft.com/en-us/fabric/get-started/media/create-workspaces/pin-workspace.png)

*Tip: Pin your workspace for quick access. Source: [Create workspaces in Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/get-started/create-workspaces)*

### Configure Workspace Settings

1. Open workspace settings (three dots > Settings)
2. Configure the following:

   **General:**
   - Contact list: Add team members
   - Default storage format: Delta

   **Premium/Fabric:**
   - License mode: Fabric capacity
   - Default storage format: Delta/Parquet

> 💡 **Pro Tip:** Using Delta format enables time travel, ACID transactions, and schema evolution - all critical features for our medallion architecture. Always choose Delta over Parquet for production workloads.

---

## 🛠️ Step 3: Create Lakehouses

We'll create three Lakehouses for the medallion architecture.

![Microsoft Fabric Lakehouse Overview](https://learn.microsoft.com/en-us/fabric/data-engineering/media/lakehouse-overview/lakehouse-overview.gif)

*Source: [What is a Lakehouse in Microsoft Fabric?](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-overview)*

```mermaid
graph TB
    subgraph "Medallion Architecture"
        direction LR
        B[🥉 lh_bronze<br/>Raw Data] --> S[🥈 lh_silver<br/>Cleansed Data]
        S --> G[🥇 lh_gold<br/>Business Ready]
    end
```

### 🥉 Bronze Lakehouse (Raw Data)

![Lakehouse Card on Data Engineering Homepage](https://learn.microsoft.com/en-us/fabric/data-engineering/media/create-lakehouse/lakehouse-card.png)

*Create a new Lakehouse from the Data Engineering homepage. Source: [Create a Lakehouse](https://learn.microsoft.com/en-us/fabric/data-engineering/create-lakehouse)*

1. In your workspace, click **+ New** > **Lakehouse**
2. Name: `lh_bronze`
3. Click **Create**

### 🥈 Silver Lakehouse (Cleansed Data)

1. Click **+ New** > **Lakehouse**
2. Name: `lh_silver`
3. Click **Create**

### 🥇 Gold Lakehouse (Business Ready)

1. Click **+ New** > **Lakehouse**
2. Name: `lh_gold`
3. Click **Create**

### Verify Lakehouses

Your workspace should now contain:

```
casino-fabric-poc/
├── 🥉 lh_bronze
├── 🥈 lh_silver
└── 🥇 lh_gold
```

---

## 🛠️ Step 4: Connect to External Storage (Optional)

If you deployed the ADLS Gen2 storage account via Bicep, connect it as a shortcut.

### Create OneLake Shortcut to ADLS

![New Shortcut in Lake View](https://learn.microsoft.com/en-us/fabric/onelake/media/create-onelake-shortcut/new-shortcut-lake-view.png)

*Right-click to create a new shortcut from the Lake view. Source: [Create an ADLS shortcut](https://learn.microsoft.com/en-us/fabric/onelake/create-adls-shortcut)*

1. Open `lh_bronze`
2. In the **Explorer** pane, right-click on **Files**
3. Select **New shortcut**
4. Choose **Azure Data Lake Storage Gen2**
5. Enter connection details:

   | Setting | Value |
   |---------|-------|
   | URL | Your ADLS DFS endpoint |
   | Connection | Create new |
   | Authentication | Organizational account |

6. Browse to the `landing` container
7. Name the shortcut: `landing_zone`
8. Click **Create**

![Shortcut Connection Details](https://learn.microsoft.com/en-us/fabric/onelake/media/create-adls-shortcut/shortcut-details.png)

*Configure connection details for the ADLS shortcut. Source: [Create an ADLS shortcut](https://learn.microsoft.com/en-us/fabric/onelake/create-adls-shortcut)*

![Browse Storage Account](https://learn.microsoft.com/en-us/fabric/onelake/media/create-adls-shortcut/shortcut-browse.png)

*Browse and select the target folder in your storage account. Source: [Create an ADLS shortcut](https://learn.microsoft.com/en-us/fabric/onelake/create-adls-shortcut)*

> 💡 **Pro Tip:** Shortcuts allow you to access external data without copying it, reducing storage costs and keeping data in sync. Use shortcuts for large archives or shared data sources.

---

## 🛠️ Step 5: Configure Workspace Access

### Add Team Members

1. Open workspace settings
2. Navigate to **Access**
3. Add users with appropriate roles:

   | Role | Who | Permissions |
   |------|-----|-------------|
   | Admin | Workspace owners | Full control |
   | Member | Data engineers | Edit all items |
   | Contributor | Developers | Create/edit |
   | Viewer | Business users | Read only |

> ⚠️ **Warning:** Be careful when assigning Admin roles. Admins can delete the workspace and all its contents.

---

## 🛠️ Step 6: Install Local Tools (Optional)

For local development and data generation, install these tools:

### Required Tools

| Tool | Purpose | Installation |
|------|---------|--------------|
| Python 3.10+ | Data generation scripts | [python.org](https://python.org) |
| VS Code | Code editor | [code.visualstudio.com](https://code.visualstudio.com) |
| Azure CLI | Azure management | [docs.microsoft.com](https://docs.microsoft.com/cli/azure/install-azure-cli) |

### Python Environment Setup

> 💡 **Pro Tip:** Use a virtual environment to isolate project dependencies and avoid conflicts with system Python packages.

![Fabric Notebook Interface](https://learn.microsoft.com/en-us/fabric/data-engineering/media/how-to-use-notebook/switch-mode.png)

*The Fabric notebook interface with mode switching options. Source: [How to use notebooks](https://learn.microsoft.com/en-us/fabric/data-engineering/how-to-use-notebook)*

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies (if requirements.txt exists)
pip install -r requirements.txt
```

---

## ✅ Step 7: Verify Setup

### Run Verification Checks

1. **Workspace accessible:** Can see all three Lakehouses
2. **Capacity assigned:** Workspace shows "Premium" or "Fabric" badge
3. **Shortcuts working:** Can browse landing zone (if configured)
4. **Permissions correct:** Team members can access

### Create a Test Table

![New Notebook Menu Options](https://learn.microsoft.com/en-us/fabric/data-engineering/media/how-to-use-notebook/new-menu-notebook-options.png)

*Create a new notebook from the workspace. Source: [How to use notebooks](https://learn.microsoft.com/en-us/fabric/data-engineering/how-to-use-notebook)*

1. Open `lh_bronze`
2. Click **Open notebook** > **New notebook**
3. Run this test code:

```python
# Test Lakehouse connectivity
from pyspark.sql import SparkSession

# Create test data
data = [("test", 1), ("data", 2)]
df = spark.createDataFrame(data, ["name", "value"])

# Write to Bronze Lakehouse
df.write.format("delta").mode("overwrite").save("Tables/test_connection")

print("✅ Success! Lakehouse is configured correctly.")
```

> 💡 **Pro Tip:** First-time notebook execution can take 2-3 minutes while Fabric provisions a Spark cluster. Subsequent runs will be faster.

4. Verify the `test_connection` table appears in the Tables folder
5. Delete the test table when done:

```python
# Clean up test table
spark.sql("DROP TABLE IF EXISTS test_connection")
print("✅ Test table cleaned up.")
```

---

## ✅ Validation Checklist

Before moving to the next tutorial, verify:

- [ ] **Workspace Created** - `casino-fabric-poc` workspace exists and is accessible
- [ ] **Capacity Assigned** - Fabric capacity is active and assigned to workspace
- [ ] **Bronze Lakehouse** - `lh_bronze` created successfully
- [ ] **Silver Lakehouse** - `lh_silver` created successfully
- [ ] **Gold Lakehouse** - `lh_gold` created successfully
- [ ] **Shortcut Configuration** - ADLS shortcut accessible (if configured)
- [ ] **Test Notebook Runs** - Successfully executed test notebook without errors
- [ ] **Table Operations Work** - Created and deleted test table successfully

<details>
<summary>🔍 How to verify each item</summary>

### Workspace Created
```powershell
# Navigate to app.fabric.microsoft.com
# Verify workspace appears in left navigation
```

### Capacity Assigned
1. Click Settings (gear icon) > Admin portal
2. Go to Capacity settings
3. Verify capacity status = "Active"

### Lakehouses Created
```python
# In any notebook, run:
spark.sql("SHOW DATABASES").show()
# Should list: lh_bronze, lh_silver, lh_gold
```

### Test Notebook Runs
```python
# Run this verification cell:
from pyspark.sql import SparkSession

# Create test data
data = [("environment", "ready"), ("setup", "complete")]
df = spark.createDataFrame(data, ["key", "value"])

# Write to Bronze
df.write.format("delta").mode("overwrite").save("Tables/env_test")

# Read back
df_check = spark.read.format("delta").load("Tables/env_test")
print(f"✅ Environment test passed: {df_check.count()} records")

# Cleanup
spark.sql("DROP TABLE IF EXISTS env_test")
```

### Capacity Check
```bash
# Check capacity CU usage in Fabric portal:
# Settings > Admin portal > Capacity settings > Usage
# Verify CUs available and not at 100%
```

</details>

---

## 🔧 Troubleshooting

### Workspace Creation Fails

| Issue | Solution |
|-------|----------|
| "Fabric not enabled" | Contact your tenant admin to enable Fabric |
| "No capacity available" | Start a trial or provision a capacity |
| "Permission denied" | Ensure your account has workspace creation rights |

### Shortcut Connection Fails

| Issue | Solution |
|-------|----------|
| "Cannot connect" | Verify ADLS account exists and is accessible |
| "Firewall blocked" | Check firewall/private endpoint settings |
| "Access denied" | Ensure you have Storage Blob Data Reader role |

### Notebook Won't Run

| Issue | Solution |
|-------|----------|
| "Capacity not available" | Verify capacity is running (not paused) |
| "Spark pool error" | Wait 2-3 minutes for first-time Spark startup |
| "Out of memory" | Reduce data size or upgrade capacity |

> 💡 **Pro Tip:** If Spark startup fails repeatedly, try detaching and reattaching the Lakehouse to the notebook. This forces a fresh cluster provisioning.

---

## 🎉 Summary

Congratulations! You have successfully:

- ✅ Created a Microsoft Fabric workspace for the Casino POC
- ✅ Set up the medallion architecture with Bronze, Silver, and Gold Lakehouses
- ✅ Configured external storage connectivity (optional)
- ✅ Verified the environment is ready for data ingestion

Your environment is now ready to start building the data platform!

---

## ➡️ Next Steps

Continue to **[Tutorial 01: Bronze Layer](../01-bronze-layer/README.md)** to start ingesting raw data into the Bronze layer.

---

## 📚 Resources

- [Microsoft Fabric Documentation](https://learn.microsoft.com/fabric/)
- [Lakehouse Overview](https://learn.microsoft.com/fabric/data-engineering/lakehouse-overview)
- [Workspace Management](https://learn.microsoft.com/fabric/get-started/workspaces)
- [OneLake Shortcuts](https://learn.microsoft.com/fabric/onelake/onelake-shortcuts)

---

## 🧭 Navigation

| Previous | Up | Next |
|----------|-----|------|
| N/A | [📖 Tutorials Index](../index.md) | [01-Bronze Layer](../01-bronze-layer/README.md) ➡️ |

---

> 💬 **Questions or issues?** Open an issue in the [GitHub repository](https://github.com/frgarofa/Suppercharge_Microsoft_Fabric/issues).
