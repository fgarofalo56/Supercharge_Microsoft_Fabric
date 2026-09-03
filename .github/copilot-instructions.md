# GitHub Copilot Instructions for Supercharge Microsoft Fabric

> **Purpose**: Ground GitHub Copilot (chat, inline, and coding agent) on THIS repository — its structure, conventions, commands, and research workflow.
> **Companion**: `CLAUDE.md` holds the full phase history and extended context. This file is the operational quick-reference; keep them consistent.

---

## Project Overview

**Name:** Supercharge Microsoft Fabric — Casino/Gaming Industry POC + Federal Expansions
**Type:** Infrastructure + Documentation + Data Engineering
**Primary Stack:** Bicep, Python, PySpark, KQL, DAX
**Target Platform:** Microsoft Fabric (F64 SKU)
**Repository:** https://github.com/fgarofalo56/Supercharge_Microsoft_Fabric

### Key Technologies

- **Infrastructure:** Azure Bicep, ARM Templates, GitHub Actions
- **Data Processing:** PySpark, Python, Delta Lake
- **Real-Time:** Eventstreams, Eventhouse, KQL
- **BI:** Power BI, Direct Lake, DAX
- **Governance:** Microsoft Purview
- **Testing:** pytest (431 unit tests), Great Expectations (9 suites)
- **Fabric Features Covered:** Fabric IQ, Real-Time Intelligence, AI Copilot, Data Mesh, Digital Twin Builder, Data Agents, OneLake Security, Iceberg Interop, Mirroring, Direct Lake, SQL Database, GraphQL, Semantic Link, OneLake Catalog, AutoML, Translytical Task Flows, MCP, Workspace Monitoring, Copy Job CDC

---

## Repository Structure

```text
Supercharge_Microsoft_Fabric/
├── infra/                  # Bicep IaC modules and deployments
│   ├── main.bicep          # Root orchestration (Workspace Identity, Tags, CMK)
│   ├── modules/            # fabric-capacity, workspace-identity, warehouse, sql-database, pipeline, alerts-and-budgets, storage-account
│   └── environments/       # dev/test/prod .bicepparam files
├── docs/                   # Architecture, deployment, best practices, feature docs
│   ├── best-practices/     # Error handling, alerting, performance, governance, CI/CD, CMK, OAP, capacity, BCDR, testing, RBAC, network, medallion, migration, observability, multi-tenant, sharing, CDC
│   └── features/           # 55 feature docs (Fabric IQ, RTI, Copilot, Data Mesh, DTB, Data Agents, OneLake Security, Mirroring, Direct Lake, SQL DB, GraphQL, Semantic Link, Catalog, AutoML, Translytical, MCP, Monitoring, Copy Job, Iceberg, dbt, MLV, Vector DB)
├── tutorials/              # 58 step-by-step tutorials (00-57)
├── poc-agenda/             # 3-day workshop materials
├── data_generation/        # 17 Python data generators (casino, federal, streaming, analytics)
│   ├── generators/         # base_generator.py + domain generators
│   ├── open_data/          # Real federal dataset download scripts (USDA, SBA, NOAA, EPA, DOI, DOJ)
│   └── config/             # federal_datasets.yaml — real public API definitions
├── notebooks/              # 58+ Fabric-importable notebooks
│   ├── bronze/             # 18 Bronze ingestion notebooks (casino + 6 federal agencies + shortcuts)
│   ├── silver/             # 17 Silver transformation notebooks
│   ├── gold/               # 19 Gold KPI/analytics notebooks (+ digital twin, AI functions)
│   └── ml/                 # ML notebooks (AutoML, RAG/vector search)
├── scripts/                # Deployment scripts (fabric-cicd-deploy.py)
├── validation/             # 431 unit tests + 9 Great Expectations suites
│   ├── unit_tests/         # test_generators.py, federal/, streaming/, analytics/, notebook/
│   └── great_expectations/ # Data quality checkpoints
├── tests/                  # Additional test suites
├── .github/                # Copilot config, agents, chatmodes, prompts, workflows, ISSUE_TEMPLATE
└── mkdocs.yml              # Documentation site configuration
```

---

## Critical Rules

### Rule 1: Native Task Management

Use the session's native task tracking for in-session work and `gh issue` for anything cross-session. Do not invent a parallel tracking system.

### Rule 2: Research First — Microsoft Docs MCP

**Before implementing or changing anything that touches a Microsoft Fabric or Azure capability, query the Microsoft Docs MCP server** (`microsoft.docs.mcp`, configured in `.vscode/mcp.json`):

1. Use `microsoft_docs_search` to find the current official guidance for the feature (Fabric APIs, SKU behavior, security defaults, GA status).
2. Use `microsoft_docs_fetch` on the most relevant page when you need full procedures, prerequisites, or troubleshooting detail.
3. Use `microsoft_code_sample_search` when generating Microsoft/Azure-related code — prefer the latest official snippets over memory.
4. Cross-reference what you find against this repo's `docs/features/` and `docs/best-practices/` — if the official docs have moved on from what this repo says, flag it (see Rule 3).

**Why:** Fabric ships fast. Feature docs here are point-in-time snapshots; Learn is the live source of truth.

### Rule 3: Log Missing Features and Gaps

When you hit a **missing capability, documentation gap, or feature this POC doesn't cover yet**, offer to log it — don't silently work around it:

1. **Offer first**: "This repo doesn't cover X. Want me to file an issue to track it?"
2. **File with the template**: use the `feature_request.md` / `documentation-request.md` templates in `.github/ISSUE_TEMPLATE/` (via `gh issue create`), or invoke the `/log-missing-feature` prompt.
3. **Label correctly**: `enhancement` for new capabilities, `documentation` for doc gaps.
4. **Link the evidence**: include the Microsoft Learn URL (from Rule 2 research) and the repo path where the gap was found.

### Rule 4: Medallion Architecture Discipline

- **Bronze:** raw ingestion, append-only, minimal transformation, schema enforcement, metadata columns (`batch_id`, ingestion timestamp)
- **Silver:** cleansed, validated, deduplicated, schema-enforced
- **Gold:** business aggregations, KPIs, star schema
- All tables are **Delta Lake**. Notebooks use `mssparkutils` (never `dbutils`) and OneLake paths (never `/tmp`).

### Rule 5: Compliance Constants Are Not Suggestions

- CTR threshold: **$10,000**
- SAR pattern: multiple transactions **$8,000–$9,900**
- W-2G thresholds: **$1,200** (slots), **$600** (keno), **$5,000** (poker)
- PII: hash SSNs (salt from `FABRIC_POC_HASH_SALT` env var — never hardcode), mask card numbers
- Frameworks in scope: NIGC MICS (casino), HIPAA (Tribal Healthcare), FedRAMP (DOT/FAA), 42 CFR Part 2

---

## Coding Conventions

### Bicep

- camelCase for parameter names; PascalCase for resource symbolic names
- Always include `@description` decorators
- Use modules for reusability; follow Azure naming conventions with project prefix
- Validate with `az bicep build --file infra/main.bicep` before committing

### Python (Data Generators)

- snake_case functions/variables, PascalCase classes
- Type hints required; dataclasses or Pydantic for schemas; PEP 8
- Generators extend `data_generation/generators/base_generator.py`
- Lint/format with `uv run ruff check` and `uv run ruff format`

### PySpark (Notebooks)

- Delta Lake for all tables; schema enforcement on write
- Markdown cells documenting each transformation
- Parameterized cells for configuration
- `mssparkutils`, OneLake checkpoint paths, `lh_bronze.*` namespace conventions

### KQL

- PascalCase function names; comment complex queries
- Optimize: limit early, filter first

---

## Common Commands

```bash
# Validate Bicep
az bicep build --file infra/main.bicep

# Run all 431 unit tests
pytest validation/unit_tests/ -v

# Run by category
pytest validation/unit_tests/test_generators.py -v   # Casino (30 tests)
pytest validation/unit_tests/federal/ -v             # Federal (54 tests)
pytest validation/unit_tests/streaming/ -v           # Streaming (20 tests)
pytest validation/unit_tests/analytics/ -v           # Analytics (30 tests)

# Data quality
great_expectations checkpoint run bronze_checkpoint

# What-if deployment analysis
az deployment sub what-if --location eastus2 \
  --template-file infra/main.bicep \
  --parameters infra/environments/dev/dev.bicepparam

# Deploy
az deployment sub create --location eastus2 \
  --template-file infra/main.bicep \
  --parameters infra/environments/dev/dev.bicepparam

# Fabric item CI/CD
python scripts/fabric-cicd-deploy.py
```

---

## Important Files

| File | Purpose |
|------|---------|
| `infra/main.bicep` | Root IaC orchestration (Workspace Identity, Tags, CMK) |
| `infra/modules/fabric/fabric-capacity.bicep` | Fabric F64 deployment |
| `infra/modules/security/workspace-identity.bicep` | Workspace Identity |
| `data_generation/generators/base_generator.py` | Generator base class |
| `data_generation/config/federal_datasets.yaml` | Real federal public API definitions |
| `notebooks/bronze/01_bronze_slot_telemetry.py` | Primary Bronze pattern |
| `scripts/fabric-cicd-deploy.py` | fabric-cicd deployment script |
| `.github/workflows/deploy-fabric.yml` | CI/CD pipeline for Fabric items |
| `CLAUDE.md` | Full phase history and extended project context |
| `.vscode/mcp.json` | MCP server configuration (incl. `microsoft.docs.mcp`) |

---

## Common Patterns and Gotchas

1. **Federal datasets are dual-mode**: each agency (USDA, SBA, NOAA, EPA, DOI, DOJ) supports BOTH synthetic generation AND real open-data downloads — check `federal_datasets.yaml` before writing a new fetcher.
2. **Direct Lake is the primary BI connectivity method** — don't default to Import mode in examples.
3. **Target SKU is F64** (P1 equivalent) — capacity guidance assumes this tier.
4. **PII salt must come from `FABRIC_POC_HASH_SALT`** — a missing env var should fail loudly, not fall back to a default.
5. **Notebooks are Fabric-importable** — no local-only paths, no `dbutils`, no `/tmp` checkpoints.
6. **Don't create duplicate docs** — check `docs/features/` and `docs/best-practices/` before writing new documentation; update the existing doc instead.

---

## Issue Reporting

Templates live in `.github/ISSUE_TEMPLATE/`:

- **Feature Request** (`feature_request.md`) — new capabilities, missing Fabric features
- **Documentation Request** (`documentation-request.md`) — doc gaps, corrections, new guides
- **Bug Report** (`bug_report.md`) — broken generators, failing notebooks, bad Bicep

Prefer filing via `gh issue create` with the matching template body, or use the `/log-missing-feature` prompt.

---

## Resources

- [Microsoft Fabric Documentation](https://learn.microsoft.com/en-us/fabric/)
- [Microsoft Fabric Roadmap](https://learn.microsoft.com/en-us/fabric/release-plan/)
- [Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/)
- [Delta Lake Documentation](https://docs.delta.io/)
- Internal: `docs/index.md`, `docs/quick-start.md`, `docs/troubleshooting-matrix.md`, `CONTRIBUTING.md`
