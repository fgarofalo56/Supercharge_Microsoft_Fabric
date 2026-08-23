# Claude Code - Microsoft Fabric POC Project

## Project Overview

**Name:** Supercharge Microsoft Fabric - Casino/Gaming Industry POC + Federal Expansions
**Type:** Infrastructure + Documentation + Data Engineering
**Primary Stack:** Bicep, Python, PySpark, KQL, DAX
**Target Platform:** Microsoft Fabric (F64 SKU)
**Phase Status:** Phase 15 Complete (Layout, Visual Impact & CSA-in-a-Box, 2026-05-05)

## Key Technologies

- **Infrastructure:** Azure Bicep, ARM Templates, GitHub Actions
- **Data Processing:** PySpark, Python, Delta Lake
- **Real-Time:** Eventstreams, Eventhouse, KQL
- **BI:** Power BI, Direct Lake, DAX
- **Governance:** Microsoft Purview
- **Testing:** pytest, Great Expectations
- **New Features:** Fabric IQ, Real-Time Intelligence, AI Copilot, Data Mesh, Digital Twin Builder, Data Agents, OneLake Security, Iceberg Interop, Mirroring, Direct Lake, SQL Database, GraphQL, Semantic Link, OneLake Catalog, AutoML, Translytical, MCP, Workspace Monitoring, Copy Job CDC

## Directory Structure

```
infra/              - Bicep IaC modules and deployments
docs/               - Architecture, deployment, best practices, feature docs
  best-practices/   - Error handling, alerting, performance, governance, CI/CD, CMK, OAP, capacity, BCDR, testing, RBAC, network, medallion, migration, observability, multi-tenant, sharing, CDC
  features/         - 50 feature docs: Fabric IQ, RTI, Copilot, Data Mesh, DTB, Data Agents, OneLake Security, Mirroring, Direct Lake, SQL DB, GraphQL, Semantic Link, Catalog, AutoML, Translytical, MCP, Monitoring, Copy Job, Iceberg, dbt, MLV, Vector DB
tutorials/          - 58 step-by-step tutorials (00-57)
poc-agenda/         - 3-day workshop materials
data_generation/    - 17 Python data generators (casino, federal, streaming, analytics)
  open_data/        - Real federal dataset download scripts (USDA, SBA, NOAA, EPA, DOI, DOJ)
notebooks/          - 58+ Fabric-importable notebooks (medallion + streaming + federal + AI)
  bronze/           - 18 Bronze ingestion notebooks (casino + 6 federal agencies + shortcuts)
  silver/           - 17 Silver transformation notebooks
  gold/             - 19 Gold KPI/analytics notebooks (+ digital twin, AI functions)
  docs/use-cases/   - Applied analytics use cases with published references
scripts/            - Deployment scripts (fabric-cicd)
validation/         - 431 unit tests + 9 Great Expectations suites
```

## Coding Conventions

### Bicep
- Use camelCase for parameter names
- Use PascalCase for resource symbolic names
- Always include description decorators
- Use modules for reusability
- Follow Azure naming conventions with project prefix

### Python (Data Generators)
- Use snake_case for functions and variables
- Use PascalCase for classes
- Include type hints
- Use dataclasses or Pydantic for schemas
- Follow PEP 8

### PySpark (Notebooks)
- Use Delta Lake format for all tables
- Include schema enforcement
- Document transformations with markdown cells
- Use parameterized cells for configuration

### KQL
- Use PascalCase for function names
- Include comments for complex queries
- Optimize for performance (limit early, filter first)

## Common Patterns

### Medallion Architecture
- **Bronze:** Raw ingestion, append-only, minimal transformation
- **Silver:** Cleansed, validated, schema-enforced, deduped
- **Gold:** Business aggregations, KPIs, star schema

### Data Quality
- Schema validation at ingestion
- Null/completeness checks
- Referential integrity verification
- Business rule validation

### Compliance Data
- CTR threshold: $10,000
- SAR patterns: Multiple transactions $8K-$9.9K
- W-2G threshold: $1,200 (slots), $600 (keno), $5,000 (poker)
- PII: Hash SSN, mask card numbers

## Important Files

| File | Purpose |
|------|---------|
| `infra/main.bicep` | Root IaC orchestration (+ Workspace Identity, Tags) |
| `infra/modules/fabric/fabric-capacity.bicep` | Fabric F64 deployment |
| `infra/modules/security/workspace-identity.bicep` | Workspace Identity (GA 2026) |
| `data_generation/generators/base_generator.py` | Generator base class |
| `notebooks/bronze/01_bronze_slot_telemetry.py` | Primary Bronze pattern |
| `scripts/fabric-cicd-deploy.py` | fabric-cicd deployment script |
| `.github/workflows/deploy-fabric.yml` | CI/CD pipeline for Fabric items |

## Testing Commands

```bash
# Validate Bicep
az bicep build --file infra/main.bicep

# Run all 431 unit tests
pytest validation/unit_tests/ -v

# Run by category
pytest validation/unit_tests/test_generators.py -v      # Casino (30 tests)
pytest validation/unit_tests/federal/ -v                 # Federal (54 tests)
pytest validation/unit_tests/streaming/ -v               # Streaming (20 tests)
pytest validation/unit_tests/analytics/ -v               # Analytics (30 tests)

# Run data quality tests
great_expectations checkpoint run bronze_checkpoint
```

## Deployment Commands

```bash
# What-if analysis
az deployment sub what-if --location eastus2 \
  --template-file infra/main.bicep \
  --parameters infra/environments/dev/dev.bicepparam

# Deploy
az deployment sub create --location eastus2 \
  --template-file infra/main.bicep \
  --parameters infra/environments/dev/dev.bicepparam
```

## Phase 7 Completion (2026-03-11)

Phase 7 delivered 71 features across 5 waves with zero regressions:

| Wave | Scope | Features | Tests |
|------|-------|----------|-------|
| Wave 1 | Federal Agencies (USDA, SBA, NOAA, EPA, DOI) | 26 | 54 |
| Wave 2 | Migration & Streaming | 19 | 20 |
| Wave 3 | Video, Movement, Geolocation Analytics | 12 | 30 |
| Wave 4 | Tribal Healthcare + DOT/FAA | 15 | — |
| Wave 5 | Final Regression | 1 | 134 (full) |

## Phase 8 Progress (2026-03-12)

Phase 8 expands all 5 federal agencies (USDA, SBA, NOAA, EPA, DOI) to full POC parity with Casino/Gaming:

| Wave | Scope | Status |
|------|-------|--------|
| Wave 1 | Federal POC Parity (5 agencies x Bronze/Silver/Gold + tutorials) | Complete |
| Wave 2 | Best Practices (error handling, alerting, performance, governance) | Complete |
| Wave 3 | New Features (Fabric IQ, RTI, Copilot, Data Mesh) | Complete |
| Wave 4 | Open data download framework + documentation updates | Complete |

## Phase 9 Completion (2026-04-13)

Phase 9 modernizes the POC for the new Microsoft Fabric experience (July 2025 - April 2026 GA wave):

| Item | Feature | Type | Status |
|------|---------|------|--------|
| 1 | Digital Twin Builder | Doc + Notebook | Complete |
| 2 | Data Agents | Doc | Complete |
| 3 | Fabric IQ Update (Ontology/Plan/Graph) | Doc Update | Complete |
| 4 | RTI Update (Business Events, Maps, SQL Operator) | Doc Update | Complete |
| 5 | OneLake Security | Doc | Complete |
| 6 | Workspace Identity | Bicep Module | Complete |
| 7 | Lakehouse Schemas | Notebook Updates (Bronze/Silver/Gold) | Complete |
| 8 | Shortcut Transformations | Notebook | Complete |
| 9 | fabric-cicd CI/CD | Workflow + Script + Doc | Complete |
| 10 | SQL Audit Logs Compliance | Doc | Complete |
| 11 | Workspace Tags | Bicep Update | Complete |
| 12 | Default Domain Sensitivity Labels | Doc Update | Complete |
| 13 | Outbound Access Protection | Doc | Complete |
| 14 | Customer-Managed Keys | Bicep Update + Doc | Complete |
| 15 | Iceberg Interoperability | Doc | Complete |
| 16 | dbt Integration | Doc | Complete |
| 17 | AI Functions Compliance | Notebook | Complete |
| 18 | Materialized Lake Views | Doc | Complete |
| 19 | Spark Runtime 2.0 Migration | Doc | Complete |
| 20 | Vector Database in Eventhouse | Doc | Complete |

### Phase 9 New Files (18 files, ~12,000+ lines)

**Feature Docs:** digital-twin-builder.md, data-agents.md, onelake-security.md, onelake-iceberg-interop.md, dbt-fabric-integration.md, materialized-lake-views.md, eventhouse-vector-database.md
**Best Practice Docs:** sql-audit-logs-compliance.md, outbound-access-protection.md, customer-managed-keys.md, spark-runtime-migration.md, fabric-cicd-deployment.md
**Notebooks:** 17_gold_digital_twin_demo.py, 17_bronze_shortcut_transformations.py, 17_gold_ai_functions_compliance.py
**Infrastructure:** workspace-identity.bicep, deploy-fabric.yml, fabric-cicd-deploy.py
**Modified Files:** main.bicep, fabric-iq.md, real-time-intelligence.md, data-governance-deep-dive.md, storage-account.bicep, 01_bronze_slot_telemetry.py, 01_silver_slot_cleansed.py, 01_gold_slot_performance.py

## Phase 10 Completion (2026-04-13)

Phase 10 achieves full Fabric landscape coverage — every major feature and enterprise best practice documented:

| Category | Items | Type | Status |
|----------|-------|------|--------|
| Feature Docs (11) | Mirroring, Direct Lake, SQL Database, GraphQL, Semantic Link, OneLake Catalog, AutoML, Translytical, MCP, Workspace Monitoring, Copy Job CDC | Docs | Complete |
| Best Practices (11) | Capacity Planning, BCDR, Testing, Network Security, RBAC, Medallion Deep Dive, Observability, Migration, Multi-Tenant, Data Sharing, Incremental CDC | Docs | Complete |
| Bicep Modules (4) | Warehouse, SQL Database, Pipeline, Alerts & Budgets | IaC | Complete |
| Notebooks (1) | AutoML Weather Forecasting | Notebook | Complete |
| Root Updates (6) | index.md, README.md, CHANGELOG.md, CLAUDE.md, best-practices/README.md, cross-references | Updates | Complete |

### Phase 10 New Files (27 files, ~21,000+ lines)

**Feature Docs:** mirroring.md, direct-lake.md, fabric-sql-database.md, api-for-graphql.md, semantic-link.md, onelake-catalog.md, automl-model-endpoints.md, translytical-task-flows.md, fabric-mcp.md, workspace-monitoring.md, copy-job-cdc.md
**Best Practice Docs:** capacity-planning-cost-optimization.md, disaster-recovery-bcdr.md, testing-strategies.md, network-security.md, identity-rbac-patterns.md, medallion-architecture-deep-dive.md, monitoring-observability.md, migration-patterns.md, multi-tenant-workspace-architecture.md, data-sharing-federation.md, incremental-refresh-cdc.md
**Bicep Modules:** fabric-warehouse.bicep, fabric-sql-database.bicep, fabric-pipeline.bicep, alerts-and-budgets.bicep
**Notebooks:** 03_ml_automl_weather_forecasting.py
**Modified Files:** main.bicep, index.md, README.md, CHANGELOG.md, CLAUDE.md, best-practices/README.md

## Context Notes

- Target SKU is F64 (P1 equivalent) for POC
- Casino domain uses NIGC MICS compliance standards
- Real-time focuses on casino floor monitoring
- Direct Lake is the primary BI connectivity method
- Purview provides governance and lineage
- Phase 7 adds HIPAA (Tribal Healthcare), FedRAMP (DOT/FAA), 42 CFR Part 2 compliance
- Phase 8 adds full medallion notebooks, tutorials, open data scripts, and GE suites for all federal agencies
- Phase 9 adds new Fabric experience features: Digital Twin Builder, Data Agents, OneLake Security, Workspace Identity, Lakehouse Schemas, Shortcut Transformations, Iceberg Interop, fabric-cicd CI/CD, CMK, OAP, SQL Audit Logs, Workspace Tags, dbt Integration, AI Functions, Materialized Views, Vector DB, Spark Runtime 2.0
- Phase 10 adds full landscape coverage: Mirroring, Direct Lake, SQL Database, GraphQL, Semantic Link, OneLake Catalog, AutoML, Translytical, MCP, Workspace Monitoring, Copy Job CDC + 11 enterprise best practices + 4 Bicep modules
- Phase 11 is audit remediation only — no new features; see Phase 11 section below
- All federal datasets use real, publicly available APIs documented in `data_generation/config/federal_datasets.yaml`
- Each agency supports BOTH synthetic data generation AND real open data downloads

## Phase 11 Completion (2026-04-15)

Phase 11 is a pure audit remediation — no new features, only correctness fixes:

| Area | Change |
|------|--------|
| Dead directories | Removed `future-expansions/` references throughout docs |
| CI workflow | Fixed GitHub Actions action versions; fixed deploy-fabric conditional logic |
| Compliance framework | Wired compliance parameter to enforce real controls (CMK, private endpoints, retention) |
| PII generation | Fixed SSN salt to require env var (`FABRIC_POC_HASH_SALT`); replaced Faker SSN with 900-series synthetic |
| Bicep modules | Deleted metadata-only stub modules |
| Notebooks (65) | Bulk-fixed for Fabric compatibility: `dbutils` → `mssparkutils`, `/tmp` → OneLake checkpoints, `lh_bronze.*` namespace |
| Utilities | Added `bronze_utils.py` shared helper |
| Test suite | Restored full suite to 431 passing tests |
| Documentation | Fixed broken tutorial nav links, Tutorial 19/36 false terminals, Tutorial 15 progress tracker, clone URL typos |

## Archon Project ID

`c0f96f03-5095-4704-a167-9a3f5a3e3ed1`

Use this ID to track tasks and store project documentation in Archon.
