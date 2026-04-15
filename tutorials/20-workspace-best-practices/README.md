# Tutorial 20: Workspace Organization Best Practices

> **Home > Tutorials > Workspace Best Practices**

---

## Overview

This hands-on tutorial guides you through implementing workspace organization patterns in Microsoft Fabric. You'll learn to structure workspaces for different team sizes, implement environment separation strategies, and apply governance best practices.

![Microsoft Fabric Workspace](https://learn.microsoft.com/en-us/fabric/get-started/media/workspaces/fabric-workspace-items.png)

*Source: [Workspaces in Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/get-started/workspaces)*

**Duration:** 2-3 hours
**Level:** Intermediate
**Prerequisites:**
- Fabric workspace admin access
- Understanding of medallion architecture
- Completed tutorials 00-03

---

## Learning Objectives

By the end of this tutorial, you will be able to:

- Choose the right workspace pattern for your organization
- Implement environment separation (Dev/Test/Staging/Prod)
- Configure folder structures within lakehouses
- Apply naming conventions and governance policies
- Set up security boundaries and RBAC

---

## Decision Framework: Workspace Patterns

### Pattern Selection Criteria

| Factor | Single Workspace | Layer-Based | Domain + Environment |
|--------|------------------|-------------|----------------------|
| Team Size | 1-5 | 5-15 | 15+ |
| Domains | Single | Single | Multiple |
| Compliance | Low | Medium | High |
| Governance | Minimal | Moderate | Enterprise |
| Cost Mgmt | Simple | Per-layer | Per-domain |

---

## Lab 1: Single Workspace Pattern

**Best for:** Small teams, POCs, learning environments

### Step 1.1: Create Unified Workspace

```
Workspace Name: Casino-POC-Unified
```

1. Navigate to **Power BI Service** > **Workspaces**
2. Click **New workspace**
3. Configure:
   - **Name:** `Casino-POC-Unified`
   - **License mode:** Fabric capacity
   - **Capacity:** Select your F64 capacity

### Step 1.2: Create Medallion Lakehouses

Create three lakehouses within the same workspace:

```
Lakehouse 1: lh_bronze
Lakehouse 2: lh_silver
Lakehouse 3: lh_gold
```

For each lakehouse:
1. Click **+ New** > **Lakehouse**
2. Name according to pattern above
3. Click **Create**

### Step 1.3: Configure Folder Structure (Bronze)

In `lh_bronze`, create this folder hierarchy:

```
Files/
├── raw/
│   ├── slot_telemetry/
│   │   ├── year=2024/
│   │   │   └── month=01/
│   ├── player_profiles/
│   ├── financial_transactions/
│   ├── table_games/
│   └── compliance/
├── schemas/
│   └── avro/
├── landing/
│   └── staging/
└── archive/
    └── processed/
```

**Create folders using notebook:**

```python
# Create Bronze folder structure
folders = [
    "Files/raw/slot_telemetry/year=2024/month=01",
    "Files/raw/player_profiles",
    "Files/raw/financial_transactions",
    "Files/raw/table_games",
    "Files/raw/compliance",
    "Files/schemas/avro",
    "Files/landing/staging",
    "Files/archive/processed"
]

for folder in folders:
    dbutils.fs.mkdirs(f"abfss://{lakehouse_name}@onelake.dfs.fabric.microsoft.com/{folder}")
    print(f"Created: {folder}")
```

### Step 1.4: Configure Folder Structure (Silver)

In `lh_silver`, create:

```
Files/
├── validated/
│   ├── slot_telemetry/
│   ├── player_master/      # SCD Type 2
│   └── transactions/
├── business_rules/
│   └── rule_definitions/
├── data_quality/
│   └── reports/
└── staging/
    └── temp/
```

### Step 1.5: Configure Folder Structure (Gold)

In `lh_gold`, create:

```
Files/
├── dimensions/
│   ├── dim_player/
│   ├── dim_machine/
│   ├── dim_location/
│   └── dim_date/
├── facts/
│   ├── fact_slot_play/
│   ├── fact_transactions/
│   └── fact_compliance/
├── aggregations/
│   ├── daily/
│   ├── weekly/
│   └── monthly/
└── semantic/
    └── exports/
```

### Step 1.6: Verify Structure

Run verification notebook:

```python
# Verify all structures exist
def verify_structure(lakehouse_name: str, expected_folders: list) -> dict:
    """Verify folder structure exists."""
    results = {"success": [], "missing": []}

    for folder in expected_folders:
        path = f"abfss://{lakehouse_name}@onelake.dfs.fabric.microsoft.com/{folder}"
        try:
            dbutils.fs.ls(path)
            results["success"].append(folder)
        except:
            results["missing"].append(folder)

    return results

# Run verification
bronze_folders = ["Files/raw", "Files/schemas", "Files/landing", "Files/archive"]
results = verify_structure("lh_bronze", bronze_folders)
print(f"Bronze verification: {len(results['success'])} OK, {len(results['missing'])} missing")
```

---

## Lab 2: Layer-Based Workspace Pattern

**Best for:** Medium teams, department-level implementations

### Step 2.1: Create Layer Workspaces

Create separate workspaces for each medallion layer:

```
Workspace 1: Casino-Bronze-Layer
Workspace 2: Casino-Silver-Layer
Workspace 3: Casino-Gold-Layer
Workspace 4: Casino-Orchestration
```

### Step 2.2: Configure Bronze Workspace

1. Create workspace `Casino-Bronze-Layer`
2. Create single lakehouse: `lh_bronze`
3. Add data pipelines for ingestion
4. Create notebooks for raw processing

**Workspace contents:**

| Item Type | Name | Purpose |
|-----------|------|---------|
| Lakehouse | lh_bronze | Raw data storage |
| Pipeline | pl_ingest_slots | Slot telemetry ingestion |
| Pipeline | pl_ingest_players | Player profile ingestion |
| Notebook | nb_bronze_quality_check | Data validation |

### Step 2.3: Configure Silver Workspace

1. Create workspace `Casino-Silver-Layer`
2. Create lakehouse: `lh_silver`
3. Add transformation notebooks
4. Configure data quality checks

**Workspace contents:**

| Item Type | Name | Purpose |
|-----------|------|---------|
| Lakehouse | lh_silver | Cleansed data |
| Notebook | nb_silver_transform_slots | Slot data transformation |
| Notebook | nb_silver_scd_players | Player SCD Type 2 |
| Dataflow Gen2 | df_silver_dedup | Deduplication flows |

### Step 2.4: Configure Gold Workspace

1. Create workspace `Casino-Gold-Layer`
2. Create lakehouse: `lh_gold`
3. Create semantic model
4. Add Power BI reports

**Workspace contents:**

| Item Type | Name | Purpose |
|-----------|------|---------|
| Lakehouse | lh_gold | Business layer |
| Semantic Model | sm_casino_analytics | Direct Lake model |
| Report | rpt_executive_dashboard | Executive metrics |
| Report | rpt_operations | Floor operations |

### Step 2.5: Configure Cross-Workspace Shortcuts

Create shortcuts to enable cross-workspace data access:

**In Silver workspace (accessing Bronze):**

```python
# Create shortcut to Bronze lakehouse
# Navigate to: lh_silver > Shortcuts > New Shortcut
# Source: Microsoft OneLake
# Target: Casino-Bronze-Layer/lh_bronze/Tables/*
```

**In Gold workspace (accessing Silver):**

```python
# Create shortcut to Silver lakehouse
# Navigate to: lh_gold > Shortcuts > New Shortcut
# Source: Microsoft OneLake
# Target: Casino-Silver-Layer/lh_silver/Tables/*
```

### Step 2.6: Set Up Orchestration Workspace

Create orchestration workspace for cross-layer pipelines:

```python
# Master pipeline pattern
# Workspace: Casino-Orchestration
# Pipeline: pl_medallion_master

# Pipeline activities:
# 1. Execute Pipeline: pl_ingest_slots (Bronze workspace)
# 2. Wait for completion
# 3. Execute Pipeline: pl_transform_slots (Silver workspace)
# 4. Wait for completion
# 5. Execute Pipeline: pl_aggregate_slots (Gold workspace)
```

---

## Lab 3: Domain + Environment Matrix Pattern

**Best for:** Enterprise, multi-team, compliance-heavy environments

### Step 3.1: Define Domain Structure

For a large casino operation:

```
Domains:
├── Gaming Operations (slot, table games)
├── Player Services (profiles, loyalty)
├── Financial (transactions, compliance)
└── Marketing (campaigns, promotions)
```

### Step 3.2: Create Environment Matrix

Create workspace matrix:

| Domain | Dev | Test | Staging | Prod |
|--------|-----|------|---------|------|
| Gaming | Gaming-Dev | Gaming-Test | Gaming-Staging | Gaming-Prod |
| Player | Player-Dev | Player-Test | Player-Staging | Player-Prod |
| Financial | Financial-Dev | Financial-Test | Financial-Staging | Financial-Prod |
| Marketing | Marketing-Dev | Marketing-Test | Marketing-Staging | Marketing-Prod |

### Step 3.3: Create Gaming Domain Workspaces

```powershell
# Using Fabric REST API
$domains = @("Gaming", "Player", "Financial", "Marketing")
$environments = @("Dev", "Test", "Staging", "Prod")

foreach ($domain in $domains) {
    foreach ($env in $environments) {
        $workspaceName = "$domain-$env"
        # Create workspace via API
        Write-Host "Creating workspace: $workspaceName"
    }
}
```

**Manual creation for Gaming domain:**

1. **Gaming-Dev:** Development and experimentation
2. **Gaming-Test:** Integration testing
3. **Gaming-Staging:** Pre-production validation
4. **Gaming-Prod:** Production workloads

### Step 3.4: Configure Each Environment

**Development Environment (Gaming-Dev):**

```yaml
Capacity: F2 (minimal)
Purpose: Experimentation
Data: Sample/synthetic
Security: Relaxed
Git: Feature branches
```

**Test Environment (Gaming-Test):**

```yaml
Capacity: F4
Purpose: Integration testing
Data: Subset of production (anonymized)
Security: Standard
Git: Develop branch
```

**Staging Environment (Gaming-Staging):**

```yaml
Capacity: F16
Purpose: UAT, Performance testing
Data: Production-like volume (anonymized)
Security: Production-like
Git: Release branches
```

**Production Environment (Gaming-Prod):**

```yaml
Capacity: F64
Purpose: Live operations
Data: Full production
Security: Strict
Git: Main branch only
```

### Step 3.5: Configure RBAC Per Environment

**Development RBAC:**

| Role | Workspace Role | Permissions |
|------|----------------|-------------|
| Data Engineer | Contributor | Full access |
| Data Scientist | Contributor | Full access |
| Analyst | Viewer | Read-only |

**Production RBAC:**

| Role | Workspace Role | Permissions |
|------|----------------|-------------|
| Platform Admin | Admin | Full management |
| Senior Engineer | Contributor | Deploy via CI/CD |
| Data Engineer | Viewer | Read-only |
| Analyst | Viewer | Reports only |

### Step 3.6: Set Up Deployment Pipeline

Configure Fabric deployment pipelines:

```
Gaming-Dev → Gaming-Test → Gaming-Staging → Gaming-Prod
```

1. Navigate to **Deployment pipelines**
2. Create new pipeline: `Gaming-Deployment`
3. Assign workspaces to stages
4. Configure deployment rules

**Deployment rules:**

```json
{
  "dataSourceRules": [
    {
      "ruleName": "Update connection strings",
      "condition": "itemType = Lakehouse",
      "action": "Replace connection"
    }
  ],
  "parameterRules": [
    {
      "ruleName": "Environment variable",
      "parameterName": "environment",
      "values": {
        "Development": "dev",
        "Test": "test",
        "Staging": "staging",
        "Production": "prod"
      }
    }
  ]
}
```

---

## Lab 4: Naming Conventions

### Standard Naming Patterns

| Item Type | Pattern | Example |
|-----------|---------|---------|
| Workspace | `{Domain}-{Environment}` | `Gaming-Prod` |
| Lakehouse | `lh_{layer}` | `lh_bronze` |
| Table | `{layer}_{entity}` | `bronze_slot_telemetry` |
| Pipeline | `pl_{action}_{entity}` | `pl_ingest_slots` |
| Dataflow | `df_{action}_{entity}` | `df_transform_players` |
| Notebook | `nb_{layer}_{purpose}` | `nb_silver_scd` |
| Semantic Model | `sm_{domain}` | `sm_gaming_analytics` |
| Report | `rpt_{audience}_{topic}` | `rpt_exec_revenue` |

### Create Naming Validation Notebook

```python
import re
from typing import Optional

def validate_name(item_type: str, name: str) -> dict:
    """Validate item name against naming conventions."""
    patterns = {
        "lakehouse": r"^lh_(bronze|silver|gold)(_\w+)?$",
        "table": r"^(bronze|silver|gold)_[a-z_]+$",
        "pipeline": r"^pl_[a-z]+_[a-z_]+$",
        "dataflow": r"^df_[a-z]+_[a-z_]+$",
        "notebook": r"^nb_[a-z]+_[a-z_]+$",
        "semantic_model": r"^sm_[a-z_]+$",
        "report": r"^rpt_[a-z]+_[a-z_]+$"
    }

    pattern = patterns.get(item_type)
    if not pattern:
        return {"valid": False, "error": f"Unknown item type: {item_type}"}

    if re.match(pattern, name):
        return {"valid": True, "name": name}
    else:
        return {"valid": False, "error": f"Name '{name}' doesn't match pattern '{pattern}'"}

# Test validations
test_cases = [
    ("lakehouse", "lh_bronze"),
    ("lakehouse", "LH_Bronze"),  # Invalid - uppercase
    ("table", "bronze_slot_telemetry"),
    ("table", "SlotTelemetry"),  # Invalid - no prefix
    ("pipeline", "pl_ingest_slots"),
    ("notebook", "nb_silver_transform"),
]

for item_type, name in test_cases:
    result = validate_name(item_type, name)
    status = "" if result["valid"] else ""
    print(f"{status} {item_type}: {name}")
```

---

## Lab 5: Governance Policies

### Step 5.1: Configure Workspace Settings

For each production workspace, enable:

1. **OneLake data access:** Configure carefully
2. **Git integration:** Main branch only
3. **Dataset settings:** Certified datasets only
4. **Export settings:** Restrict as needed

### Step 5.2: Create Data Certification Process

```markdown
## Data Certification Workflow

1. **Request Certification**
   - Data owner submits certification request
   - Includes data quality report

2. **Review Process**
   - Data steward reviews
   - Validates quality metrics
   - Checks compliance requirements

3. **Approval**
   - Data steward approves/rejects
   - Certified badge applied

4. **Ongoing Monitoring**
   - Automated quality checks
   - Re-certification on major changes
```

### Step 5.3: Implement Tagging Strategy

```python
# Tag structure for compliance
tags = {
    "classification": ["public", "internal", "confidential", "restricted"],
    "pii_level": ["none", "low", "medium", "high"],
    "retention": ["30d", "90d", "1y", "7y", "permanent"],
    "domain": ["gaming", "player", "financial", "marketing"],
    "compliance": ["pci-dss", "nigc", "gdpr", "sox"]
}

# Apply tags to tables via Purview
# See Tutorial 07: Governance & Purview
```

---

## Summary Checklist

### Single Workspace Pattern
- [ ] Created unified workspace
- [ ] Created Bronze/Silver/Gold lakehouses
- [ ] Configured folder structures
- [ ] Verified structure

### Layer-Based Pattern
- [ ] Created layer workspaces
- [ ] Configured shortcuts
- [ ] Set up orchestration workspace
- [ ] Tested cross-workspace pipelines

### Domain + Environment Pattern
- [ ] Created workspace matrix
- [ ] Configured per-environment settings
- [ ] Set up RBAC
- [ ] Created deployment pipelines

### Governance
- [ ] Applied naming conventions
- [ ] Created validation notebook
- [ ] Configured certification process
- [ ] Implemented tagging strategy

---

## Additional Resources

- [Best Practices Documentation](../BEST_PRACTICES.md)
- [Microsoft Fabric Workspace Documentation](https://learn.microsoft.com/en-us/fabric/get-started/workspaces)
- [Deployment Pipelines](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/intro-to-deployment-pipelines)

---

## 🧭 Navigation

| Previous | Up | Next |
|----------|-----|------|
| [⬅️ 19-Copilot & AI](../19-copilot-ai/README.md) | [📖 Tutorials Index](../README.md) | [21-GeoAnalytics & ArcGIS](../21-geoanalytics-arcgis/README.md) ➡️ |

---

> 💬 **Questions or issues?** Open an issue in the [GitHub repository](https://github.com/frgarofa/Suppercharge_Microsoft_Fabric/issues).
