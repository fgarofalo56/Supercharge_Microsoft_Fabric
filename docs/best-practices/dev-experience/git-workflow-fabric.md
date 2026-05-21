# Git Workflow for Microsoft Fabric Development

![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![Updated](https://img.shields.io/badge/Updated-April_2026-green)
![Category](https://img.shields.io/badge/Category-Developer_Experience-purple)

---

**Last Updated:** `2026-04-27` | **Version:** 1.0.0

---

## Overview

Microsoft Fabric provides built-in Git integration that syncs workspace items (notebooks, pipelines, semantic models) to a Git repository. This guide establishes the branching strategy, PR workflow, and conflict resolution patterns used in this POC.

### Key Principles

1. **Git is the source of truth.** Fabric workspaces are deployment targets, not the authoritative version.
2. **All changes go through PRs.** No direct workspace edits in staging or production.
3. **Automated deployment.** The `fabric-cicd` library deploys items from Git to workspaces.
4. **Test before merge.** Unit tests run in CI; integration testing happens in the dev workspace.

---

## Fabric Git Integration Architecture

```
Developer Machine                    GitHub                        Fabric Service
+-----------------+     push     +----------------+   fabric-cicd  +------------------+
| VS Code         | ----------> | main branch    | ------------> | Casino-POC-Dev   |
| - Edit .py      |             |                |               |   Notebooks      |
| - Run pytest    |    PR       | feature/*      |               |   Lakehouses     |
| - Commit        | ----------> | phase14/*      |               |   Pipelines      |
+-----------------+             +-------+--------+               +------------------+
                                        |
                                        | merge to release/staging
                                        v
                                +----------------+   fabric-cicd  +------------------+
                                | release/staging| ------------> | Casino-POC-Stg   |
                                +-------+--------+               +------------------+
                                        |
                                        | merge to release/prod
                                        v
                                +----------------+   fabric-cicd  +------------------+
                                | release/prod   | ------------> | Casino-POC-Prod  |
                                +----------------+               +------------------+
```

### Sync Direction

| Direction | When | How |
|-----------|------|-----|
| Fabric --> Git | Initial export, one-time migration | Fabric UI: "Connect to Git" |
| Git --> Fabric | Every deployment | `fabric-cicd` via GitHub Actions |
| Local --> Git | Every commit | `git push` |
| Git --> Local | Every pull | `git pull` |

> **Important:** Once Git integration is established, avoid making changes directly in the Fabric workspace. All changes should flow through Git to maintain a single source of truth.

---

## Branch Strategy

### Recommended: Feature Branch + Environment Branches

```
main                          (protected, auto-deploy to Dev)
  |
  +-- feature/slot-schema     (developer feature work)
  +-- feature/sar-detection   (developer feature work)
  +-- phase14/wave8-*         (phase-based feature branches)
  |
  +-- release/staging         (protected, deploy to Staging)
  +-- release/prod            (protected, deploy to Production)
```

### Branch Naming Convention

| Pattern | Purpose | Example |
|---------|---------|---------|
| `feature/<desc>` | New functionality | `feature/add-player-dedup` |
| `fix/<desc>` | Bug fixes | `fix/ctr-threshold-boundary` |
| `phase<N>/wave<N>-<desc>` | Phase-based work | `phase14/wave8-developer-experience` |
| `release/staging` | Staging environment | Long-lived |
| `release/prod` | Production environment | Long-lived |
| `hotfix/<desc>` | Emergency production fix | `hotfix/sar-false-positive` |

### Branch Lifecycle

```bash
# 1. Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/add-player-dedup

# 2. Develop, test, commit
# ... edit files ...
pytest validation/unit_tests/ -v
git add notebooks/silver/02_silver_player_cleansed.py
git commit -m "feat(silver): add deduplication logic for player records"

# 3. Push and create PR
git push -u origin feature/add-player-dedup
gh pr create --title "feat(silver): player deduplication" --body "..."

# 4. After merge, delete feature branch
git checkout main
git pull origin main
git branch -d feature/add-player-dedup
```

### Environment Promotion

```bash
# Promote main --> staging
git checkout release/staging
git merge main
git push origin release/staging
# GitHub Actions deploys to Casino-POC-Stg via fabric-cicd

# Promote staging --> production (after validation)
git checkout release/prod
git merge release/staging
git push origin release/prod
# GitHub Actions deploys to Casino-POC-Prod via fabric-cicd (requires approval)
```

---

## Repository Structure for Fabric Items

### How Fabric Items Map to Files

| Fabric Item | File Format | Repository Path |
|-------------|-------------|-----------------|
| Notebook | `.py` (Databricks source) | `notebooks/<layer>/<name>.py` |
| Semantic Model | `.bim` (JSON) | `semantic-models/<name>/model.bim` |
| Pipeline | `.json` (definition) | `pipelines/<name>/pipeline-content.json` |
| Lakehouse | `.platform` (metadata) | `lakehouses/<name>/.platform` |
| Data Generator | `.py` (Python module) | `data_generation/generators/<name>.py` |
| Bicep Module | `.bicep` | `infra/modules/<category>/<name>.bicep` |

### This POC's Structure

```
Suppercharge_Microsoft_Fabric/
  notebooks/
    bronze/               # 18 Bronze ingestion notebooks
    silver/               # 17 Silver transformation notebooks
    gold/                 # 19 Gold KPI/analytics notebooks
    utils/                # Shared utility modules
    docs/use-cases/       # Applied analytics use cases
  data_generation/
    generators/           # 17 Python data generators
    config/               # YAML configuration
    open_data/            # Federal dataset download scripts
  infra/
    main.bicep            # Root IaC orchestration
    modules/              # Bicep modules
    environments/         # Parameter files per environment
  validation/
    unit_tests/           # 612 unit tests
    great_expectations/   # 9 data quality suites
  scripts/
    fabric-cicd-deploy.py # Deployment script
  .github/workflows/
    deploy-fabric.yml     # CI/CD pipeline
```

### Platform Files

Fabric Git integration creates `.platform` files alongside items. These contain workspace-specific metadata:

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
  "metadata": {
    "type": "Notebook",
    "displayName": "01_bronze_slot_telemetry"
  },
  "config": {
    "version": "2.0",
    "logicalId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
  }
}
```

> **Note:** `.platform` files are workspace-specific. Do not manually edit them. The `fabric-cicd` library handles item ID mapping during deployment.

---

## PR Workflow

### The Complete Flow

```
1. Create Branch    2. Develop Locally   3. Push + PR        4. CI Checks
   git checkout -b     edit .py files       git push             pytest
   feature/xyz         run pytest           gh pr create         bicep build
                       commit                                    lint

5. Code Review      6. Merge             7. Auto-Deploy      8. Validate
   Team reviews        Squash merge         fabric-cicd          Run notebook
   Approve PR          to main              deploys to Dev       in workspace
```

### Creating a Pull Request

```bash
# After committing and pushing your feature branch
gh pr create \
  --title "feat(bronze): add USDA crop ingestion notebook" \
  --body "$(cat <<'EOF'
## Summary
- Added Bronze notebook for USDA crop production data ingestion
- Schema enforcement with 12 validated fields
- Null rejection for required fields (state_code, year, commodity)

## Test Plan
- [x] Unit tests pass locally (pytest)
- [x] Schema validation tests added
- [ ] Manual validation in Dev workspace after merge

## Compliance
- No PII data involved
- Uses public USDA NASS API

## Related
- Phase 14, Wave 8: Developer Experience
EOF
)"
```

### PR Template

Create `.github/PULL_REQUEST_TEMPLATE.md`:

```markdown
## Summary
<!-- 1-3 bullet points describing what changed and why -->

## Type of Change
- [ ] New notebook (Bronze/Silver/Gold)
- [ ] Notebook modification
- [ ] Data generator update
- [ ] Infrastructure (Bicep)
- [ ] Documentation
- [ ] Bug fix
- [ ] Test update

## Test Plan
- [ ] Unit tests pass (`pytest validation/unit_tests/ -v`)
- [ ] New tests added for new logic
- [ ] Manual validation in Dev workspace
- [ ] No regressions in existing tests

## Compliance Checklist
- [ ] No PII in committed code
- [ ] No hardcoded secrets or connection strings
- [ ] FABRIC_POC_HASH_SALT used for PII hashing (not hardcoded salt)
- [ ] Compliance thresholds unchanged (or documented if changed)

## Breaking Changes
<!-- List any breaking changes and migration steps -->
None
```

---

## Conflict Resolution for Fabric Files

### Notebook Conflicts (.py files)

Notebook `.py` files are standard Python with `# COMMAND ----------` cell separators. Git handles these like any Python file:

```bash
# Check for conflicts after merge
git merge main
# If conflicts exist:

# Option 1: Open in VS Code and resolve visually
code notebooks/bronze/01_bronze_slot_telemetry.py

# Option 2: Use VS Code merge editor
# Click "Resolve in Merge Editor" when prompted
```

**Best practices for avoiding notebook conflicts:**

1. Keep notebook cells small and focused.
2. Put shared logic in `notebooks/utils/` modules (conflict-free).
3. Avoid editing the same notebook on multiple branches simultaneously.
4. Use `# COMMAND ----------` separators as natural merge boundaries.

### Pipeline Conflicts (.json files)

Pipeline definitions are JSON files. Conflicts in JSON are harder to resolve:

```bash
# Use jq to format JSON before resolving
cat pipelines/main-pipeline/pipeline-content.json | python -m json.tool > temp/formatted.json
```

**Strategy:** If pipeline conflicts are complex, take the newer version and re-apply your changes manually in the Fabric UI, then re-export.

### Semantic Model Conflicts (.bim files)

Semantic model definitions are large JSON files (`.bim`). Manual conflict resolution is error-prone.

**Strategy:**
1. Take the version from `main` (their changes).
2. Re-apply your measure or table changes using Tabular Editor.
3. Re-export the `.bim` file.

### .platform File Conflicts

`.platform` files should never conflict because they are workspace-specific and listed in `.gitignore`. If they do appear in a conflict:

```bash
# Accept theirs (workspace metadata is regenerated by fabric-cicd)
git checkout --theirs '*.platform'
git add '*.platform'
```

---

## fabric-cicd Deployment Integration

### How Deployment Works

The `deploy-fabric.yml` workflow uses `fabric-cicd` to deploy items:

```yaml
# Simplified from .github/workflows/deploy-fabric.yml
- name: Deploy to Fabric
  run: |
    python scripts/fabric-cicd-deploy.py \
      --workspace-id ${{ secrets.FABRIC_WORKSPACE_ID }} \
      --environment ${{ inputs.target_environment }} \
      --item-type-in-scope Notebook Lakehouse SemanticModel \
      ${{ inputs.dry_run && '--dry-run' || '' }}
```

### Deployment Flow

```
git push to main
  |
  v
GitHub Actions: validate
  - bicep build
  - pytest
  |
  v
GitHub Actions: deploy-dev
  - fabric-cicd (dry-run by default)
  |
  v
Manual dispatch: deploy-staging
  - Requires environment approval
  - fabric-cicd deploys to staging workspace
  |
  v
Manual dispatch: deploy-prod
  - Requires environment approval + wait timer
  - fabric-cicd deploys to production workspace
```

### Scoping Deployments

Not every push needs to deploy every item type. The workflow uses path filters:

```yaml
on:
  push:
    branches: [main]
    paths:
      - 'notebooks/**'
      - 'reports/semantic-model/**'
      - 'reports/report-definitions/**'
```

Only changes to these paths trigger deployment. Infrastructure changes (Bicep), documentation, and tests do not trigger Fabric deployments.

---

## Handling Merge Conflicts in Notebooks

### Common Conflict Scenarios

**Scenario 1: Both branches modify the same cell**

```python
<<<<<<< HEAD
SOURCE_PATH = "Files/output/bronze_slot_telemetry_v2.parquet"
=======
SOURCE_PATH = "Files/output/bronze_slot_telemetry.parquet"
>>>>>>> feature/update-source
```

Resolution: Choose the correct path based on the current data format.

**Scenario 2: One branch adds a cell, another modifies adjacent cells**

```python
# COMMAND ----------

# Cell A (unchanged)

# COMMAND ----------

<<<<<<< HEAD
# Cell B (modified in main)
df = df.withColumn("new_col", lit("v2"))
=======
# Cell B-prime (new cell added in feature branch)
df = df.withColumn("validation_flag", when(col("amount") > 0, True))

# COMMAND ----------

# Cell B (original, unchanged in feature)
>>>>>>> feature/add-validation
```

Resolution: Keep both changes. The new cell from the feature branch and the modification from main are independent.

**Scenario 3: Import block conflicts**

```python
<<<<<<< HEAD
from pyspark.sql.functions import col, current_timestamp, lit, when, hash
=======
from pyspark.sql.functions import col, current_timestamp, input_file_name, lit
>>>>>>> feature/add-source-tracking
```

Resolution: Merge both import lists:

```python
from pyspark.sql.functions import (
    col,
    current_timestamp,
    hash,
    input_file_name,
    lit,
    when,
)
```

### Prevention: Reducing Notebook Conflicts

1. **Extract shared logic.** Functions in `notebooks/utils/` are less likely to conflict than inline notebook code.

2. **One concern per notebook.** Do not mix ingestion and transformation in the same notebook.

3. **Use thin notebooks.** The notebook should be orchestration only. Business logic lives in imported modules.

4. **Coordinate through PRs.** Before starting work on a notebook someone else is editing, communicate in the PR.

---

## .gitignore Patterns

### Fabric-Specific Entries

This POC's `.gitignore` includes these Fabric-relevant patterns:

```gitignore
# Fabric workspace metadata (generated by extension, workspace-specific)
.fabric/

# Fabric binary exports (use .py source format instead)
*.lakehouse
*.warehouse
*.notebook

# Power BI binary files (use .bim or TMDL for source control)
*.pbix
*.pbit

# Generated data (too large for Git)
data_generation/output/
output/
*.parquet
*.csv

# Exception: tracked schema and config CSVs
!**/schemas/*.csv
!**/config/*.csv
!sample-data/**/*.csv
!sample-data/**/*.parquet

# Platform metadata (regenerated by fabric-cicd)
# Note: .platform files ARE tracked if using Fabric Git integration directly.
# They are NOT tracked if using fabric-cicd exclusively.
```

### What to Track vs. Ignore

| Track (commit) | Ignore (gitignore) |
|----------------|--------------------|
| `.py` notebook source | `.ipynb` checkpoint files |
| `.bicep` infrastructure | `.json` ARM compiled output |
| `.bim` semantic models | `.pbix` Power BI binaries |
| `requirements.txt` | `.venv/` virtual environment |
| `.github/workflows/` | `.fabric/` workspace metadata |
| `data_generation/generators/` | `data_generation/output/` |
| `validation/unit_tests/` | `.pytest_cache/`, `htmlcov/` |

---

## Protected Branches and Policies

### Branch Protection Rules

Configure these on GitHub for each protected branch:

**`main` branch:**

```yaml
protection_rules:
  require_pull_request:
    required_reviewers: 1
    dismiss_stale_reviews: true
    require_code_owner_review: false
  require_status_checks:
    strict: true
    contexts:
      - "Run Notebook Unit Tests"
      - "Validate Fabric Items"
  require_linear_history: false
  allow_force_pushes: false
  allow_deletions: false
```

**`release/staging` and `release/prod`:**

```yaml
protection_rules:
  require_pull_request:
    required_reviewers: 2
  require_status_checks:
    strict: true
  restrict_pushes:
    - team: platform-leads
  deployment_branch_policy:
    protected_branches: true
```

### CODEOWNERS

Create `.github/CODEOWNERS`:

```
# Default: platform team reviews everything
*                           @platform-team

# Notebooks: data engineering team
notebooks/                  @data-engineering-team
data_generation/            @data-engineering-team

# Infrastructure: platform team
infra/                      @platform-team
.github/workflows/          @platform-team

# Compliance-sensitive files: require lead review
notebooks/utils/compliance_rules.py  @data-engineering-lead
validation/unit_tests/test_compliance_pipeline.py  @data-engineering-lead
```

---

## Code Review Checklist

### For Notebook PRs

- [ ] **Schema:** Does the notebook enforce a schema (StructType), or does it rely on inference?
- [ ] **Nulls:** Are required columns validated for null values?
- [ ] **Idempotency:** Can the notebook be re-run without creating duplicates?
- [ ] **Paths:** Are file paths using the standard pattern (`Files/output/...`)?
- [ ] **Secrets:** No hardcoded connection strings, passwords, or API keys?
- [ ] **PII:** SSN hashing uses `FABRIC_POC_HASH_SALT` env var, not a hardcoded salt?
- [ ] **Tests:** Unit tests added or updated for new business logic?
- [ ] **Compliance:** CTR/SAR/W-2G thresholds match regulatory requirements?
- [ ] **Documentation:** Markdown cells explain the notebook's purpose and data flow?

### For Bicep PRs

- [ ] **Naming:** Resources follow Azure naming conventions with project prefix?
- [ ] **Parameters:** All configurable values are parameterized (not hardcoded)?
- [ ] **What-if:** `az deployment sub what-if` output reviewed?
- [ ] **Tags:** Resources include required tags (environment, project, owner)?
- [ ] **Security:** No secrets in parameter defaults?

### For Data Generator PRs

- [ ] **Base class:** Generator inherits from `BaseGenerator`?
- [ ] **Type hints:** All functions have type annotations?
- [ ] **PII:** Uses 900-series synthetic SSNs, not Faker?
- [ ] **Determinism:** Random seed can be set for reproducibility?
- [ ] **Tests:** Generator tests added in `validation/unit_tests/`?

---

## Commit Message Convention

This POC follows the Conventional Commits format:

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Types

| Type | When |
|------|------|
| `feat` | New feature (notebook, generator, module) |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code restructuring without behavior change |
| `test` | Adding or updating tests |
| `chore` | Build, CI, or tooling changes |

### Scopes

| Scope | Covers |
|-------|--------|
| `bronze` | Bronze layer notebooks |
| `silver` | Silver layer notebooks |
| `gold` | Gold layer notebooks |
| `infra` | Bicep modules, deployment |
| `generators` | Data generation code |
| `ci` | GitHub Actions workflows |
| `phase<N>/wave<N>` | Phase-specific work |

### Examples

```bash
feat(bronze): add USDA crop production ingestion notebook
fix(silver): correct SSN hashing to use env var salt
docs(best-practices): add dev experience documentation
refactor(generators): extract base validation into BaseGenerator
test(federal): add 54 unit tests for federal agency generators
chore(ci): update actions/checkout to v4
feat(phase14/wave8): add developer experience best practices
```

---

## Multi-Developer Workflow

### Scenario: Two Developers Editing Different Notebooks

This is the simple case. Both developers work on separate feature branches and merge independently:

```bash
# Developer A: working on Bronze notebook
git checkout -b feature/bronze-usda
# edit notebooks/bronze/14_bronze_usda_crop.py

# Developer B: working on Gold notebook
git checkout -b feature/gold-usda-kpi
# edit notebooks/gold/14_gold_usda_performance.py

# No conflicts: both PRs merge cleanly to main
```

### Scenario: Two Developers Editing the Same Notebook

Coordinate through communication and small, focused PRs:

```bash
# Developer A: adds schema enforcement (merge first)
git checkout -b feature/slot-schema
# edit notebooks/bronze/01_bronze_slot_telemetry.py -- cell 3 only
# PR title: "feat(bronze): add schema enforcement to slot telemetry"

# Developer B: adds compliance flags (merge after A)
git checkout -b feature/slot-compliance
# Wait for A's PR to merge
git pull origin main  # Get A's changes
git rebase main       # Rebase onto A's changes
# edit notebooks/bronze/01_bronze_slot_telemetry.py -- cell 5 only
# PR title: "feat(bronze): add CTR/SAR flags to slot telemetry"
```

### Scenario: Hotfix While Feature Work is in Progress

```bash
# Developer has feature work in progress
git stash  # Save current work

# Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/sar-false-positive
# fix, test, commit
git push -u origin hotfix/sar-false-positive
gh pr create --title "fix(compliance): correct SAR detection boundary"

# After hotfix is merged, return to feature work
git checkout feature/my-feature
git stash pop
git rebase main  # Incorporate the hotfix
```

---

## Troubleshooting

### `error: failed to push some refs`

```
Cause:  Remote has changes you don't have locally
Fix:    git pull --rebase origin <branch>
```

### `CONFLICT (content): Merge conflict in notebooks/...`

```
Cause:  Two branches modified the same notebook cell
Fix:    Open in VS Code, use the merge editor, resolve, then:
        git add <file>
        git commit
```

### `fabric-cicd deployment fails after merge`

```
Cause:  Item definition is invalid (broken JSON, missing required fields)
Fix:    Run validation locally:
        python scripts/fabric-cicd-deploy.py --dry-run
```

### PR checks fail but tests pass locally

```
Cause:  Python version or dependency mismatch between local and CI
Fix:    Ensure you're using Python 3.11 and matching pip versions
        Check: python --version && pip freeze | grep pyspark
```

### Large file rejected by GitHub

```
Cause:  Parquet or CSV data files accidentally staged
Fix:    git rm --cached <file>
        Verify .gitignore covers the pattern
```

---

## References

- [Fabric Git Integration](https://learn.microsoft.com/fabric/cicd/git-integration/intro-to-git-integration)
- [fabric-cicd Deployment](https://learn.microsoft.com/fabric/cicd/manage-deployment)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Branch Protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-a-branch-protection-rule/about-protected-branches)
- [This POC: fabric-cicd Deployment Guide](../fabric-cicd-deployment.md)
- [This POC: CI/CD Workflow](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/blob/main/.github/workflows/deploy-fabric.yml)
- [This POC: VS Code Workflow](./vscode-fabric-workflow.md)
