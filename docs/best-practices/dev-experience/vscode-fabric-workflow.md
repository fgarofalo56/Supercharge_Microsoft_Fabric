# VS Code Workflow for Microsoft Fabric Development

![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![Updated](https://img.shields.io/badge/Updated-April_2026-green)
![Category](https://img.shields.io/badge/Category-Developer_Experience-purple)

---

**Last Updated:** `2026-04-27` | **Version:** 1.0.0

---

## Overview

VS Code is the recommended local development environment for this POC. The Microsoft Fabric VS Code extension (GA 2025) provides bidirectional sync between your local repository and Fabric workspaces, enabling a professional software engineering workflow for data engineering artifacts that are traditionally edited only in browser-based UIs.

This guide covers installation, workspace binding, the edit-sync-test-commit loop, and how to get the most out of VS Code when developing notebooks, pipelines, and semantic models for Microsoft Fabric.

### Why VS Code for Fabric?

| Concern | Fabric Web UI | VS Code + Extension |
|---------|---------------|---------------------|
| Source control | Manual export/import | Native Git integration |
| Code review | Not supported | Standard PR workflow |
| Multi-file refactoring | One item at a time | Project-wide find/replace |
| IntelliSense | Basic autocomplete | Full Pylance + type checking |
| Debugging | Print statements only | Breakpoints, step-through |
| Collaboration | Share workspace | Standard Git branching |
| Offline work | Not possible | Full local editing |

---

## Fabric Extension Setup

### Step 1: Install VS Code

Download from [code.visualstudio.com](https://code.visualstudio.com/). Use the **System Installer** on managed machines so updates apply system-wide.

### Step 2: Install the Fabric Extension

Open the Extensions panel (`Ctrl+Shift+X`) and search for **Microsoft Fabric**:

```text
Extension ID: ms-fabric.fabric-vscode
Publisher:    Microsoft
```

Alternatively, install from the command line:

```bash
code --install-extension ms-fabric.fabric-vscode
```

### Step 3: Sign In

1. Open the Command Palette (`Ctrl+Shift+P`).
2. Run **Fabric: Sign In**.
3. Complete the browser-based Azure AD authentication flow.
4. Your tenant and workspaces appear in the Fabric sidebar panel.

> **Tip:** If your organization uses Conditional Access policies, ensure your device is compliant before signing in. The extension uses the same token as `az login`.

### Step 4: Verify Connection

After sign-in, the Fabric panel displays:

```
FABRIC WORKSPACES
  Tenant: Contoso (contoso.onmicrosoft.com)
    Casino-POC-Dev
      Notebooks (18)
      Lakehouses (3)
      Pipelines (5)
      Semantic Models (2)
    Casino-POC-Staging
      ...
```

---

## Workspace Connection

### Binding a Workspace to Your Repository

The Fabric extension maps a **workspace** to a **local folder**. This repo uses the following mapping:

```
E:\Repos\...\Suppercharge_Microsoft_Fabric\
  notebooks/          --> Workspace: Casino-POC-Dev (Notebooks)
  semantic-models/    --> Workspace: Casino-POC-Dev (Semantic Models)
  pipelines/          --> Workspace: Casino-POC-Dev (Pipelines)
```

To bind:

1. Open the Fabric sidebar panel.
2. Right-click your target workspace.
3. Select **Connect to Local Folder**.
4. Choose the repository root.
5. The extension creates a `.fabric/` metadata folder (already in `.gitignore`).

### Multi-Workspace Setup

For environment promotion (Dev/Staging/Prod), bind each workspace to a separate Git branch:

| Branch | Workspace | Purpose |
|--------|-----------|---------|
| `main` | Casino-POC-Dev | Active development |
| `release/staging` | Casino-POC-Staging | Pre-production validation |
| `release/prod` | Casino-POC-Prod | Production |

```bash
# Switch workspace context by switching branches
git checkout main              # Dev workspace
git checkout release/staging   # Staging workspace
```

### Workspace Settings File

The extension stores workspace metadata in `.fabric/settings.json`:

```json
{
  "workspaceId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "workspaceName": "Casino-POC-Dev",
  "tenantId": "11111111-2222-3333-4444-555555555555",
  "itemMappings": {
    "notebooks/bronze/01_bronze_slot_telemetry.py": {
      "itemId": "item-guid-here",
      "itemType": "Notebook"
    }
  }
}
```

> **Important:** The `.fabric/` directory is listed in `.gitignore`. Do not commit workspace-specific bindings to source control.

---

## Syncing Items Between VS Code and Fabric

### Downloading Items from Fabric

Pull the latest version of all items from the connected workspace:

1. Open the Command Palette (`Ctrl+Shift+P`).
2. Run **Fabric: Download All Items**.
3. The extension writes Fabric item definitions to your local folder.

Or download a single item:

```
Fabric Panel > Right-click item > Download to Local
```

### Uploading Local Changes to Fabric

After editing locally, push changes back:

1. **Fabric: Upload All Items** -- syncs everything.
2. **Fabric: Upload Current File** -- syncs only the active editor file.
3. Right-click in the Fabric panel and select **Upload**.

### Selective Sync

For large workspaces, configure which item types to sync in `.fabric/settings.json`:

```json
{
  "syncScope": {
    "includeTypes": ["Notebook", "SemanticModel"],
    "excludePatterns": ["*_archive_*", "*_deprecated_*"]
  }
}
```

### Conflict Resolution

When both local and remote versions have changed:

1. The extension detects the conflict and shows a diff view.
2. Choose **Keep Local**, **Keep Remote**, or **Merge**.
3. For notebook conflicts, prefer **Keep Local** since your local version is under Git control and can be diffed precisely.

---

## Local Editing Workflow

The recommended development loop for this POC:

```
                +-------------------+
                |  Edit in VS Code  |
                +---------+---------+
                          |
                +---------v---------+
                | Run local tests   |
                | (pytest + Spark)  |
                +---------+---------+
                          |
                +---------v---------+
                | Upload to Fabric  |
                | (extension sync)  |
                +---------+---------+
                          |
                +---------v---------+
                | Validate in       |
                | Fabric workspace  |
                +---------+---------+
                          |
                +---------v---------+
                | Commit + Push     |
                | (Git)             |
                +-------------------+
```

### Step-by-Step Example: Editing a Bronze Notebook

```bash
# 1. Pull latest from Git
git pull origin main

# 2. Download latest Fabric state
#    (Command Palette > Fabric: Download All Items)

# 3. Edit the notebook locally
code notebooks/bronze/01_bronze_slot_telemetry.py

# 4. Run local tests
pytest validation/unit_tests/test_generators.py -v

# 5. Upload to Fabric workspace
#    (Command Palette > Fabric: Upload Current File)

# 6. Run the notebook in Fabric to validate against real data

# 7. Commit your changes
git add notebooks/bronze/01_bronze_slot_telemetry.py
git commit -m "fix(bronze): adjust slot telemetry schema for new SAS fields"

# 8. Push and create PR
git push origin feature/slot-schema-update
```

### Notebook Format

This POC uses the **Databricks notebook source** format (`.py` files with `# COMMAND ----------` separators). VS Code treats these as standard Python files, giving full IntelliSense and linting:

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer: Slot Machine Telemetry

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, current_timestamp

# Configuration
SOURCE_PATH = "Files/output/bronze_slot_telemetry.parquet"
TARGET_TABLE = "lh_bronze.bronze_slot_telemetry"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Schema Definition

# COMMAND ----------

schema = StructType([
    StructField("machine_id", StringType(), False),
    StructField("event_type", StringType(), False),
    StructField("amount", DoubleType(), True),
    StructField("timestamp", TimestampType(), False),
])
```

---

## Debugging Notebooks Locally

### Python Cell Debugging

Since notebooks are `.py` files, you can debug them like any Python script:

1. Set breakpoints in the gutter.
2. Press `F5` or use **Run > Start Debugging**.
3. Select the **Python: Current File** configuration.

For PySpark cells, you need a local Spark session. See [local-spark-debugging.md](./local-spark-debugging.md) for full setup.

### launch.json Configuration

Add this to `.vscode/launch.json` for notebook debugging:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Notebook (Local Spark)",
      "type": "debugpy",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "env": {
        "PYSPARK_PYTHON": "${workspaceFolder}/.venv/Scripts/python.exe",
        "FABRIC_POC_HASH_SALT": "local-dev-salt-do-not-use-in-prod",
        "SPARK_LOCAL_IP": "127.0.0.1"
      },
      "justMyCode": true,
      "args": []
    },
    {
      "name": "Debug Generator",
      "type": "debugpy",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "env": {
        "FABRIC_POC_HASH_SALT": "local-dev-salt-do-not-use-in-prod"
      }
    }
  ]
}
```

### Handling Fabric-Specific APIs

Notebook code that references `mssparkutils` or `notebookutils` will fail locally. Use conditional imports:

```python
try:
    from notebookutils import mssparkutils
    IS_FABRIC = True
except ImportError:
    IS_FABRIC = False

# Use IS_FABRIC to gate Fabric-specific calls
if IS_FABRIC:
    mssparkutils.credentials.getSecret("keyvault", "secret-name")
else:
    import os
    secret = os.environ.get("SECRET_NAME", "local-default")
```

---

## Extensions Ecosystem

### Required Extensions

Install these for full Fabric development support:

| Extension | ID | Purpose |
|-----------|----|---------|
| Microsoft Fabric | `ms-fabric.fabric-vscode` | Workspace sync, item management |
| Python | `ms-python.python` | Python language support |
| Pylance | `ms-python.vscode-pylance` | Type checking, IntelliSense |
| Jupyter | `ms-toolsai.jupyter` | Notebook rendering (optional) |
| Bicep | `ms-azuretools.vscode-bicep` | Infrastructure-as-Code |
| Azure Account | `ms-vscode.azure-account` | Azure authentication |

### Recommended Extensions

| Extension | ID | Purpose |
|-----------|----|---------|
| GitLens | `eamodio.gitlens` | Git blame, history, comparison |
| Markdown All in One | `yzhang.markdown-all-in-one` | Documentation editing |
| YAML | `redhat.vscode-yaml` | YAML config editing |
| indent-rainbow | `oderwat.indent-rainbow` | Visual indentation guides |
| Error Lens | `usernamehw.errorlens` | Inline error display |
| Docker | `ms-azuretools.vscode-docker` | Dev container support |

### Install All at Once

```bash
code --install-extension ms-fabric.fabric-vscode \
     --install-extension ms-python.python \
     --install-extension ms-python.vscode-pylance \
     --install-extension ms-azuretools.vscode-bicep \
     --install-extension ms-vscode.azure-account \
     --install-extension eamodio.gitlens \
     --install-extension yzhang.markdown-all-in-one \
     --install-extension redhat.vscode-yaml
```

---

## Settings Configuration

### Workspace Settings (`.vscode/settings.json`)

```json
{
  // ── Python ──────────────────────────────────────────────────
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.autoImportCompletions": true,
  "python.analysis.extraPaths": [
    "${workspaceFolder}/data_generation",
    "${workspaceFolder}/notebooks"
  ],

  // ── Pylance ─────────────────────────────────────────────────
  "python.languageServer": "Pylance",
  "python.analysis.diagnosticSeverityOverrides": {
    "reportMissingImports": "warning",
    "reportMissingModuleSource": "information"
  },

  // ── Formatting ──────────────────────────────────────────────
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "ms-python.python",
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  },

  // ── Files ───────────────────────────────────────────────────
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/node_modules": true,
    ".fabric/": true
  },
  "files.associations": {
    "*.bicep": "bicep",
    "*.bicepparam": "bicep"
  },

  // ── Search ──────────────────────────────────────────────────
  "search.exclude": {
    "**/data_generation/output": true,
    "**/.venv": true,
    "**/temp": true
  },

  // ── Testing ─────────────────────────────────────────────────
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "validation/unit_tests",
    "-v"
  ],

  // ── Bicep ───────────────────────────────────────────────────
  "bicep.experimental.deployPane": true,

  // ── Terminal ────────────────────────────────────────────────
  "terminal.integrated.defaultProfile.windows": "Git Bash",
  "terminal.integrated.env.windows": {
    "FABRIC_POC_HASH_SALT": "local-dev-salt-do-not-use-in-prod"
  }
}
```

### User Settings Recommendations

Add these to your user-level `settings.json` (`Ctrl+,` > Open Settings JSON):

```json
{
  "editor.minimap.enabled": false,
  "editor.bracketPairColorization.enabled": true,
  "editor.guides.bracketPairs": "active",
  "editor.stickyScroll.enabled": true,
  "workbench.editor.wrapTabs": true,
  "git.autofetch": true,
  "git.confirmSync": false,
  "diffEditor.ignoreTrimWhitespace": false
}
```

---

## Keyboard Shortcuts and Productivity

### Essential Shortcuts

| Action | Windows/Linux | Mac |
|--------|---------------|-----|
| Command Palette | `Ctrl+Shift+P` | `Cmd+Shift+P` |
| Quick Open (file) | `Ctrl+P` | `Cmd+P` |
| Go to Symbol | `Ctrl+Shift+O` | `Cmd+Shift+O` |
| Find in Files | `Ctrl+Shift+F` | `Cmd+Shift+F` |
| Toggle Terminal | `` Ctrl+` `` | `` Cmd+` `` |
| Run Python File | `Ctrl+F5` | `Cmd+F5` |
| Debug Python File | `F5` | `F5` |
| Run All Tests | `Ctrl+; A` | `Cmd+; A` |
| Format Document | `Shift+Alt+F` | `Shift+Option+F` |
| Rename Symbol | `F2` | `F2` |
| Toggle Sidebar | `Ctrl+B` | `Cmd+B` |

### Fabric-Specific Shortcuts

Configure these in `keybindings.json` for common Fabric operations:

```json
[
  {
    "key": "ctrl+shift+u",
    "command": "fabric.uploadCurrentItem",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+shift+d",
    "command": "fabric.downloadCurrentItem",
    "when": "editorTextFocus"
  }
]
```

### Multi-Cursor Editing for Notebook Cells

When refactoring across multiple notebook cells:

1. `Ctrl+D` to select next occurrence.
2. `Ctrl+Shift+L` to select all occurrences.
3. `Alt+Click` to place cursors manually.

This is particularly useful when renaming a column across Bronze/Silver/Gold notebooks.

---

## Comparison: VS Code vs Fabric Web UI vs Tabular Editor

| Capability | VS Code + Extension | Fabric Web UI | Tabular Editor |
|------------|---------------------|---------------|----------------|
| **Notebooks** | Full editing, debugging, sync | Native execution, Spark UI | N/A |
| **Semantic Models** | JSON definition editing | Visual model designer | Full DAX, TOM model editing |
| **Pipelines** | JSON definition editing | Visual drag-and-drop | N/A |
| **Lakehouses** | Definition management | Data explorer, SQL endpoint | N/A |
| **Git Integration** | Native Git + PR workflow | Built-in Git sync | External only |
| **IntelliSense** | Full (Pylance, Bicep) | Basic autocomplete | DAX autocomplete |
| **Debugging** | Breakpoints, step-through | Print statements | N/A |
| **Offline Work** | Full local editing | Requires connection | Requires connection |
| **Collaboration** | Git branching + PRs | Workspace sharing | External Git |
| **Bulk Refactoring** | Find/replace across files | One file at a time | One model at a time |
| **Cost** | Free | Included with Fabric | Free (community) |

### When to Use Each Tool

**VS Code + Fabric Extension:**
- Day-to-day notebook and pipeline development
- Code reviews and pull requests
- Refactoring across multiple files
- Local debugging and testing
- Bicep infrastructure editing

**Fabric Web UI:**
- Running notebooks against live data
- Monitoring pipeline executions
- Visual pipeline design
- Lakehouse data exploration
- Spark UI and job monitoring

**Tabular Editor:**
- Complex DAX measure authoring
- Semantic model schema changes
- Calculation group management
- Performance tuning (vertipaq analyzer)

---

## Troubleshooting

### Extension Not Showing Workspaces

```
Problem: Fabric panel shows "No workspaces found"
Cause:   Token expired or wrong tenant
Fix:     Ctrl+Shift+P > "Fabric: Sign Out" > "Fabric: Sign In"
```

### Upload Fails with 403

```
Problem: "Insufficient permissions" when uploading
Cause:   User lacks Contributor role on the workspace
Fix:     Ask workspace admin to assign Contributor or Member role
```

### Notebook Sync Creates Duplicate

```
Problem: Upload creates a new item instead of updating existing
Cause:   Item mapping lost (missing .fabric/settings.json)
Fix:     Delete .fabric/ and rebind workspace
```

### Local Spark Session Fails

```
Problem: "Java not found" when debugging notebooks locally
Cause:   JDK not installed or JAVA_HOME not set
Fix:     See local-spark-debugging.md for JDK setup
```

### Python Import Errors in Notebooks

```
Problem: Pylance reports missing imports for pyspark, mssparkutils
Cause:   Virtual environment missing PySpark
Fix:     pip install pyspark delta-spark in your .venv
         Add stubs for mssparkutils (see notebook-unit-testing.md)
```

---

## References

- [Microsoft Fabric VS Code Extension](https://learn.microsoft.com/fabric/cicd/git-integration/git-get-started)
- [VS Code Python Development](https://code.visualstudio.com/docs/python/python-tutorial)
- [Fabric Git Integration Overview](https://learn.microsoft.com/fabric/cicd/git-integration/intro-to-git-integration)
- [fabric-cicd Python Library](https://pypi.org/project/fabric-cicd/)
- [Tabular Editor Documentation](https://docs.tabulareditor.com/)
- [This POC: fabric-cicd Deployment Guide](../fabric-cicd-deployment.md)
- [This POC: Local Spark Debugging](./local-spark-debugging.md)
- [This POC: Notebook Unit Testing](./notebook-unit-testing.md)
