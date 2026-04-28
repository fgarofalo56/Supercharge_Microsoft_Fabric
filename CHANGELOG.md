# 📋 Changelog

> **Last Updated:** 2026-04-27 | **Version:** 3.0.0 | **Status:** Active

<div align="center">

![Changelog](https://img.shields.io/badge/📋_Changelog-Keep_a_Changelog-blue?style=for-the-badge)
![SemVer](https://img.shields.io/badge/🔢_Versioning-SemVer_2.0-green?style=for-the-badge)
![Phase](https://img.shields.io/badge/🎯_Phase-14_Complete-purple?style=for-the-badge)

</div>

---

## 📑 Table of Contents

- [🔮 Unreleased](#-unreleased)
- [🏷️ 3.0.0 — Phase 14: One-Stop Shop Completion](#️-300---2026-04-27)
- [🏷️ 2.2.0 — Phase 12: Documentation Gap Remediation](#️-220---2026-04-21)
- [🏷️ 2.1.0 — Phase 11: Audit Remediation](#️-210---2026-04-15)
- [🏷️ 2.0.0 — Phases 9 & 10: Fabric Modernization](#️-200---2026-04-13)
- [🏷️ 1.2.0 — Tutorials & Docs Site](#️-120---2025-01-28)
- [🏷️ 1.1.0 — Docker & Power BI](#️-110---2025-01-21)
- [🏷️ 1.0.0 — Initial Release](#️-100---2025-01-21)
- [📊 Version History Summary](#-version-history-summary)

---

All notable changes to the Microsoft Fabric Casino/Gaming POC will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 🔮 [Unreleased]

Nothing currently unreleased.

---

## 🏷️ [3.0.0] — 2026-04-27

### Phase 14: One-Stop Shop Completion — 119 Features, 9 Waves

Major release transforming the POC into a comprehensive Microsoft Fabric enterprise reference.

#### Wave 1 — Operations & SRE (PR #53)

**Added:**
- 7 operational runbooks: incident response, capacity throttling, pipeline failure triage, auth failure playbook, multi-region failover, tenant migration, data quality incident
- 4 operations best-practice docs: SLO/SLI definitions, on-call rotation handbook, change management (RFC/CAB), observability stack
- 2 Bicep modules: Action Groups (7 receiver types), Log Analytics Workspace (table-level retention, CMK, archive)

#### Wave 2 — MLOps & AI Lifecycle (PR #54)

**Added:**
- 8 MLOps/AI docs: MLOps production guide, drift detection (PSI/KS/Wasserstein), feature store, responsible AI framework, LLM cost tracking, RAG patterns, prompt engineering, eval harness
- 5 ML notebooks: model registry (MLflow champion/challenger), drift detection, feature store demo, RAG with Eventhouse vectors, responsible AI audit
- 2 tutorials: end-to-end MLOps (Tutorial 39), production RAG (Tutorial 40)

#### Wave 3 — Data Management (PR #55)

**Added:**
- 7 data management docs: MDM (4 topologies), data contracts (YAML + GE), data product framework, reference data versioning, late-arriving data, SCD patterns (all 6 types), business glossary automation
- 4 notebooks: MDM golden customer, SCD Type 2 dimension, reference data versioned, late-arriving backfill
- 1 Great Expectations suite: data contract enforcement

#### Wave 4 — Migration (PR #56)

**Added:**
- 5 migration tutorials: Synapse → Fabric, Databricks → Fabric, Redshift → Fabric, BigQuery → Fabric, on-prem SSAS/SSIS/SSRS
- 2 assessment/conversion notebooks: Synapse workload assessment (3-mode CLI), schema conversion (28 type mappings)
- 2 migration data generators: Synapse workload inventory, Databricks workload inventory
- Updated `migration-patterns.md` with 5 new source sub-sections

#### Wave 5 — Security & Compliance (PR #57)

**Added:**
- 9 security docs: SOC 2 Type II readiness, ISO 27001 Annex A mapping, GDPR right-to-deletion, CCPA privacy rights, STRIDE threat model, zero-trust blueprint, data exfiltration prevention, supply chain security, audit trail immutability
- 2 compliance templates: SOC 2 control matrix (47 criteria), DSAR runbook (7-phase lifecycle)
- 1 notebook: GDPR cascading delete (4 modes, hash-chain audit)
- 1 Bicep module: private endpoint with DNS + lock

#### Wave 6 — Commercial Industry Verticals (PR #58)

**Added:**
- 9 industry verticals, each with use-case doc + data generator + bronze/silver/gold notebooks + tutorial + unit tests:
  - Healthcare (HIPAA/HITRUST) — readmission risk, claims denial analytics
  - Financial Services (SOX/PCI-DSS/Basel III) — real-time fraud detection, AML
  - Insurance (NAIC) — loss triangles, fraud ring detection
  - Retail/CPG (PCI-DSS) — demand forecasting, Customer 360
  - Manufacturing/IoT (IEC 62443) — predictive maintenance, OEE
  - Energy/Utilities (NERC CIP) — smart meter analytics, grid reliability
  - Telecom (CPNI/GDPR) — churn prediction, network quality
  - Pharma/Life Sciences (21 CFR Part 11/GxP) — clinical trials, safety signals
  - Media/Entertainment (COPPA/GDPR) — audience analytics, recommendations
- 133 new unit tests (431 total), 0 regressions

#### Wave 7 — Feature Coverage Completion (PR #64)

**Added:**
- 8 feature docs: Variable Libraries, FUAM, User Data Functions, Apache Airflow Job, Spark Job Definitions, Notebook Resources & Environments, TMDL/Developer Mode, OneLake Shortcuts (S3/GCS/Dataverse)
- 6 best-practice docs: OneLake Files vs Tables, Lakehouse Schema Versioning, Spark Runtime Breaking Changes Matrix, V-Order Tuning, Partition Strategy Decision Tree, Query Optimization Deep Dive
- 1 notebook: Variable Library parameterized pipeline demo

#### Wave 8 — Developer Experience (PR #65)

**Added:**
- 4 sample applications: Streamlit dashboard (SQL endpoint), React+GraphQL (Apollo/MSAL), Power Apps canvas consumer, Logic App orchestrator
- 5 developer docs: VS Code workflow, notebook unit testing, local Spark debugging, Git workflow for Fabric, devcontainer setup
- Bronze pattern unit test (PySpark)
- Updated `.devcontainer/devcontainer.json`

#### Wave 9 — Structural Refactor

**Added:**
- Decision Trees guide (Mermaid flowcharts for 7 key decisions)
- Troubleshooting Matrix (symptom-indexed, 10+ categories)
- Cheat Sheets (PySpark, KQL, T-SQL, DAX quick reference)
- FAQ expansion (25+ entries, 8 categories)
- Notebooks cross-reference README
- Bicep modules README
- Phase 14 regression report (119 features, 431 tests, 0 regressions)
- CHANGELOG update (this entry)

---

#### DOJ Department of Justice (8th Federal Domain)
- **doj_generator.py** — DOJGenerator with 4 domains: crime_stats (FBI NIBRS), federal_cases (USSC), antitrust (mergers/cartels), drug_enforcement (DEA)
- **test_doj_generator.py** — 29 unit tests covering all 4 domains, HHI logic, sentencing ranges
- **doj_download.py** — Open data download module for FBI CDE API, USSC, antitrust filings, HSR, DEA
- **18_bronze_doj.py** — Bronze ingestion for 4 DOJ tables with schema enforcement
- **18_silver_doj.py** — Silver transformations with NIBRS validation, HHI classification, DQ scoring
- **19_gold_doj_analytics.py** — Gold analytics: crime trends, sentencing analytics, antitrust metrics, drug enforcement
- **4 GE suites** — Great Expectations for crime_stats, federal_cases, antitrust, drug_enforcement
- **Tutorial 38** — DOJ Justice Analytics step-by-step guide
- **doj_justice_report.json** — Power BI report template (4 pages: Crime, Sentencing, Antitrust, DEA)
- **federal_datasets.yaml** — Added DOJ agency block with 8 public datasets (FBI CDE, USSC, Antitrust, HSR, DEA, BOP, BJS, Vera)

#### Use Cases Section
- **docs/use-cases/README.md** — Use cases index page
- **docs/use-cases/antitrust-analytics.md** — HHI concentration analysis, 2023 Merger Guidelines, cartel detection, cross-domain analysis
- **docs/use-cases/federal-justice-analytics.md** — Crime analytics, sentencing disparity, prosecution pipeline, drug enforcement
- **docs/use-cases/references/README.md** — Curated published DOJ/FBI/USSC/DEA resources with URLs

### Changed
- **README.md** — Added DOJ to federal domain listing, bumped tutorial count to 38
- **CLAUDE.md** — Updated domain listing with DOJ
- **__init__.py** — Added DOJGenerator export
- **conftest.py** — Added doj_generator fixture

### Planned
- Additional Power BI report templates
- Enhanced compliance reporting

---

## 🏷️ [2.2.0] - 2026-04-21

### Added — Phase 12: Documentation Gap Remediation

#### Feature Documentation (13 new docs)
- **docs/features/dataflow-gen2.md** — Power Query M transformations, query folding, staging, scheduling
- **docs/features/data-activator.md** — Rule-based alerting, objects, properties, triggers
- **docs/features/deployment-pipelines.md** — Native ALM, stage promotion, deployment rules
- **docs/features/spark-environments-job-definitions.md** — Library management, Spark Job Definitions
- **docs/features/git-integration.md** — Azure DevOps/GitHub sync, branch-per-workspace
- **docs/features/real-time-hub.md** — Event catalog, data streams, derived streams
- **docs/features/paginated-reports.md** — RDL authoring, pixel-perfect reports, subscriptions
- **docs/features/scorecards-metrics.md** — KPI tracking, status rules, automated check-ins
- **docs/features/composite-models.md** — Mixed Import + DirectQuery + Direct Lake
- **docs/features/cross-database-queries.md** — Three-part naming across Lakehouse/Warehouse/SQL DB
- **docs/features/fabric-rest-apis.md** — Core/Admin/Item APIs, authentication, LRO polling
- **docs/features/vnet-data-gateway.md** — Managed gateway in customer VNet, Bicep setup
- **docs/features/workspace-ip-firewall.md** — IP rules, trusted service bypass, surge protection

#### Best Practices (5 new guides)
- **docs/best-practices/etl-elt-comparison-guide.md** — Side-by-side comparison of all 5 ETL methods with code
- **docs/best-practices/power-bi-best-practices.md** — DAX optimization, semantic model design, Direct Lake tuning
- **docs/best-practices/lakehouse-warehouse-sqldb-decision-guide.md** — Feature comparison matrix, hybrid patterns
- **docs/best-practices/finops-cost-governance.md** — FinOps framework, chargeback, pause/resume automation
- **docs/best-practices/data-modeling-star-schema.md** — Dimensional modeling, SCD Type 1/2/3, Direct Lake

### Changed — Phase 12
- **mkdocs.yml** — Added Features nav section (35 docs), expanded Best Practices (37 docs), added tutorials 24-36
- **docs/best-practices/README.md** — Added Phase 12 documentation gap remediation section
- **CHANGELOG.md** — Added [2.2.0] section

---

## 🏷️ [2.1.0] - 2026-04-15

### Added
- `bronze_utils.py` shared helper for common notebook patterns
- `FABRIC_POC_HASH_SALT` env var documented in `.env.sample` (required for PII generation)
- `CHECKPOINT_PATH_BASE` env var documented in `.env.sample` (OneLake checkpoint path)

### Changed
- CLAUDE.md: Phase Status updated to Phase 11 Complete (Audit Remediation, 2026-04-15)
- 65 notebooks: `dbutils` replaced with `mssparkutils`; `/tmp` paths replaced with OneLake checkpoint paths; `lh_bronze.*` namespace applied consistently
- Compliance framework parameter wired to enforce real controls (CMK, private endpoints, retention)
- SSN generation: replaced Faker SSN with deterministic 900-series synthetic; salt now requires `FABRIC_POC_HASH_SALT` env var
- Tutorial 15 progress tracker: corrected links for tutorials 17–19 to actual dir names
- Tutorial 19: removed false "FINAL TUTORIAL" / "Series Complete!" markers; now links to Tutorial 20
- Tutorial 36: removed dead Tutorial 37 links; series terminus now points back to Tutorials Index

### Fixed
- All 74 `../index.md` broken links in `tutorials/**/README.md` replaced with `../README.md`
- 39 occurrences of `Supercharge_Microsoft_Fabric` (single 'p') corrected to `Suppercharge_Microsoft_Fabric`
- CI workflow: fixed GitHub Actions action versions and deploy-fabric conditional logic
- README.md and other docs: removed all `future-expansions/` links (directory deleted)
- README.md: removed "Production-Ready" self-certification language and empty Acknowledgments section

### Removed
- `future-expansions/` directory and all references to it
- Dead-weight metadata-only Bicep stub modules

---

## 🏷️ [2.0.0] - 2026-04-13

### Added — Phase 9: New Fabric Experience Modernization

#### Feature Documentation (7 new docs)
- **docs/features/digital-twin-builder.md** — IoT digital twin modeling and simulation
- **docs/features/data-agents.md** — Autonomous AI agents for data workflows
- **docs/features/onelake-security.md** — Workspace identity, managed VNet, trusted access
- **docs/features/onelake-iceberg-interop.md** — Apache Iceberg read/write for cross-platform analytics
- **docs/features/dbt-fabric-integration.md** — dbt Core/Cloud with Fabric SQL & Spark
- **docs/features/materialized-lake-views.md** — Pre-computed views for Direct Lake performance
- **docs/features/eventhouse-vector-database.md** — Vector search in KQL for AI/RAG workloads

#### Best Practices (5 new guides)
- **docs/best-practices/fabric-cicd-deployment.md** — fabric-cicd Python library, GitHub Actions, environment promotion
- **docs/best-practices/sql-audit-logs-compliance.md** — SQL analytics endpoint audit logs
- **docs/best-practices/outbound-access-protection.md** — Data exfiltration prevention
- **docs/best-practices/customer-managed-keys.md** — BYOK encryption key management
- **docs/best-practices/spark-runtime-migration.md** — Runtime 2.0 migration guide

#### Infrastructure
- **infra/modules/security/workspace-identity.bicep** — Workspace Identity (GA 2026) module
- **scripts/fabric-cicd-deploy.py** — fabric-cicd deployment script
- **.github/workflows/deploy-fabric.yml** — 4-stage CI/CD pipeline

#### Notebooks (3 new notebooks)
- **notebooks/gold/17_gold_digital_twin_demo.py** — Digital twin demo notebook
- **notebooks/bronze/17_bronze_shortcut_transformations.py** — Shortcut transformations
- **notebooks/gold/17_gold_ai_functions_compliance.py** — AI Functions compliance notebook

### Changed — Phase 9
- **infra/main.bicep** — Added Workspace Identity module, workspace governance tags, CMK support
- **infra/modules/storage/storage-account.bicep** — Added CMK configuration parameters
- **docs/features/fabric-iq.md** — Added Ontology, Plan, and Graph layers
- **docs/features/real-time-intelligence.md** — Added Business Events, Maps, SQL Operator
- **docs/best-practices/data-governance-deep-dive.md** — Added default domain sensitivity labels
- **notebooks/bronze/01_bronze_slot_telemetry.py** — Added Lakehouse Schema section
- **notebooks/silver/01_silver_slot_cleansed.py** — Added Lakehouse Schema section
- **notebooks/gold/01_gold_slot_performance.py** — Added Lakehouse Schema section

### Added — Phase 10: Full Fabric Landscape Coverage

#### Feature Documentation (11 new docs)
- **docs/features/mirroring.md** — Near-real-time DB replication (Oracle, SAP, BigQuery, MySQL)
- **docs/features/direct-lake.md** — Power BI reads Delta directly from OneLake
- **docs/features/fabric-sql-database.md** — OLTP workload with auto-replication to OneLake
- **docs/features/api-for-graphql.md** — GraphQL API layer over Fabric data items
- **docs/features/semantic-link.md** — SemPy library bridging notebooks and semantic models
- **docs/features/onelake-catalog.md** — Unified data discovery and governance hub
- **docs/features/automl-model-endpoints.md** — Automated ML training and REST model deployment
- **docs/features/translytical-task-flows.md** — Write-back from Power BI reports to Lakehouse
- **docs/features/fabric-mcp.md** — Model Context Protocol for AI agent interaction
- **docs/features/workspace-monitoring.md** — Queryable system tables for activity tracking
- **docs/features/copy-job-cdc.md** — Low-code continuous ingestion with change data capture

#### Best Practices (11 new guides)
- **docs/best-practices/capacity-planning-cost-optimization.md** — SKU selection, CU cost model
- **docs/best-practices/disaster-recovery-bcdr.md** — RTO/RPO targets, failover procedures
- **docs/best-practices/testing-strategies.md** — Testing pyramid, unit/integration/DQ testing
- **docs/best-practices/network-security.md** — Private endpoints, managed VNet, IP firewall
- **docs/best-practices/identity-rbac-patterns.md** — Workspace roles, item permissions, RLS/CLS/OLS
- **docs/best-practices/medallion-architecture-deep-dive.md** — SCD patterns, table maintenance
- **docs/best-practices/monitoring-observability.md** — Capacity monitoring, dashboards, alerting
- **docs/best-practices/migration-patterns.md** — Source-specific migration and validation
- **docs/best-practices/multi-tenant-workspace-architecture.md** — Topology and isolation patterns
- **docs/best-practices/data-sharing-federation.md** — Shortcuts, data sharing, federation
- **docs/best-practices/incremental-refresh-cdc.md** — Delta MERGE, watermark management

#### Infrastructure (4 new Bicep modules)
- **infra/modules/fabric/fabric-warehouse.bicep** — Fabric Warehouse configuration metadata
- **infra/modules/fabric/fabric-sql-database.bicep** — SQL Database with DDM & CMK
- **infra/modules/fabric/fabric-pipeline.bicep** — Data Factory Pipeline with scheduling
- **infra/modules/monitoring/alerts-and-budgets.bicep** — Capacity alerts & budget management

#### Notebooks (1 new notebook)
- **notebooks/ml/03_ml_automl_weather_forecasting.py** — AutoML weather forecasting demo

### Changed — Phase 10
- **infra/main.bicep** — Added Warehouse, SQL Database, Pipeline, and Alerts modules with conditional flags
- **docs/index.md** — Added Feature Documentation section with 22 feature docs
- **docs/best-practices/README.md** — Added Phase 9 and Phase 10 best practices sections
- **README.md** — Updated Phase badge to 10, added Phase 9-10 section, updated test count
- **CLAUDE.md** — Updated phase status to Phase 10 Complete
- **CHANGELOG.md** — Added [2.0.0] section

---

## 🏷️ [1.2.0] - 2025-01-28

### Added

#### New Tutorials
- **Tutorial 12: CI/CD & DevOps** - Git integration, deployment pipelines, automation scripts
- **Tutorial 13: Migration Planning** - 6-month enterprise migration guide, POC to production

#### Notebook Documentation
- **notebooks/bronze/README.md** - Raw ingestion layer documentation
- **notebooks/silver/README.md** - Data cleansing layer documentation
- **notebooks/gold/README.md** - Business aggregation layer documentation
- **notebooks/real-time/README.md** - Streaming analytics documentation
- **notebooks/ml/README.md** - Machine learning documentation

#### Quick Reference Documents
- **docs/QUICK_START.md** - 5-minute getting started guide
- **tutorials/CHEAT_SHEET.md** - Printable PySpark/KQL/DAX reference card

#### MkDocs Documentation Site
- **mkdocs.yml** - Material theme with dark/light toggle, search, Mermaid support
- **.github/workflows/docs.yml** - GitHub Actions for auto-deploy to GitHub Pages
- **docs/stylesheets/extra.css** - Custom styling for documentation site

#### Infrastructure Documentation
- **infra/README.md** - Comprehensive Bicep deployment guide with Mermaid diagrams

### Changed
- Reorganized repository structure (moved review files to docs/archive/)
- Updated tutorials/README.md to include all 14 tutorials
- Enhanced main README.md with new documentation links

### Fixed
- Fixed 10 broken icons8.com image links (replaced with emoji)
- Fixed GitHub badge URLs (corrected username)
- Fixed markdown rendering issues in docs/STYLE_GUIDE.md
- Fixed broken image reference in tutorials/08-database-mirroring

---

## 🏷️ [1.1.0] - 2025-01-21

### Added

#### Docker Support
- **Dockerfile** - Multi-stage build for data generator container
- **docker-compose.yml** - Multi-service orchestration with four services:
  - `data-generator` - Full dataset generation (30 days)
  - `demo-generator` - Quick demo dataset (7 days, smaller volumes)
  - `streaming-generator` - Real-time streaming to Azure Event Hub
  - `data-validator` - Data quality validation
- Docker environment variables for configuration
- Volume mounts for data persistence

#### Dev Container
- **.devcontainer/** - VS Code Dev Container configuration
  - Pre-installed Python 3.11, Azure CLI, Bicep, Git, PowerShell
  - Recommended VS Code extensions auto-install
  - GitHub Codespaces support
- One-click development environment setup

#### Power BI Templates
- **reports/** - Power BI report templates and semantic model definitions
  - `report-definitions/` - Report .pbip files
  - `semantic-model/tables/` - Table definitions for Direct Lake
  - `semantic-model/measures/` - DAX measure definitions
- Report templates for:
  - Casino Executive Dashboard
  - Slot Performance Analysis
  - Player 360 View
  - Compliance Monitoring
  - Real-Time Floor Monitor

#### Cost Estimation
- **docs/COST_ESTIMATION.md** - Comprehensive Azure cost guide
  - Detailed Fabric capacity pricing matrix
  - Environment-specific cost scenarios (POC, Dev, Production)
  - Cost optimization strategies
  - Pause/resume scheduling guidance
  - Reserved capacity recommendations

#### Sample Data
- **sample-data/** - Pre-generated datasets for quick exploration
  - `bronze/` - Bronze layer sample data files
  - `schemas/` - Schema definitions and documentation
- Sample datasets:
  - Slot Telemetry (10,000 records, 7 days)
  - Player Profiles (500 records)
  - Table Games (2,000 records)
  - Financial Transactions (1,000 records)

#### Automation Scripts
- **scripts/** - PowerShell automation scripts
  - `deploy.ps1` - Infrastructure deployment automation
  - `generate-data.ps1` - Data generation wrapper (local/Docker)
  - `validate.ps1` - Validation test runner

#### VS Code Configuration
- **.vscode/** - Workspace settings
  - `settings.json` - Workspace preferences
  - `extensions.json` - Recommended extensions
  - `launch.json` - Debug configurations

### Changed

#### Documentation Updates
- **README.md** - Major updates:
  - Added Docker and Dev Container badges
  - New navigation sections for Docker, Dev Container, Power BI, Cost Estimation, Sample Data
  - Updated Quick Start with three deployment options (Docker, Dev Container, Azure)
  - Expanded Repository Structure with new directories
- **docs/DEPLOYMENT.md** - Added:
  - Docker Deployment section
  - Script-Based Deployment section
  - Cost optimization quick reference
- **docs/PREREQUISITES.md** - Added:
  - Docker Desktop as optional tool
  - Dev Containers extension
  - Dev Container quick start guide
- **data_generation/README.md** - Added:
  - Docker quick start (primary option)
  - Sample data usage guide
  - Docker reference section
- **validation/README.md** - Added:
  - Docker validation option
  - Script-based validation
  - Docker-based CI/CD workflow
  - Dev Container testing guide

### Fixed
- Updated .gitignore for new directories and files

---

## 🏷️ [1.0.0] - 2025-01-21

### Added

#### Core Infrastructure
- **infra/** - Bicep Infrastructure as Code
  - `main.bicep` - Root orchestration template
  - `modules/` - Reusable Bicep modules (Fabric, Purview, Storage, Key Vault)
  - `environments/` - Dev, Staging, Production parameter files
- Microsoft Fabric capacity deployment
- Microsoft Purview data governance integration
- Azure Data Lake Storage Gen2 (ADLS Gen2)
- Azure Key Vault for secrets management
- Log Analytics workspace

#### Documentation
- **docs/** - Comprehensive documentation suite
  - `ARCHITECTURE.md` - System architecture and design patterns
  - `DEPLOYMENT.md` - Step-by-step deployment guide
  - `PREREQUISITES.md` - Setup requirements
  - `SECURITY.md` - Security controls and compliance
  - `diagrams/` - Architecture diagrams

#### Tutorials
- **tutorials/** - 10 step-by-step tutorials
  - 00-environment-setup
  - 01-bronze-layer
  - 02-silver-layer
  - 03-gold-layer
  - 04-real-time-analytics
  - 05-direct-lake-powerbi
  - 06-data-pipelines
  - 07-governance-purview
  - 08-database-mirroring
  - 09-advanced-ai-ml

#### Data Generation
- **data_generation/** - Synthetic data generators
  - Slot Machine telemetry generator
  - Table Game transaction generator
  - Player Profile generator
  - Financial Transaction generator
  - Security Event generator
  - Compliance Filing generator (CTR, SAR, W-2G)
- PII protection (hashing, masking)
- Referential integrity across datasets
- Configurable volumes and date ranges

#### Validation Framework
- **validation/** - Testing and data quality
  - `great_expectations/` - Data quality validation suites
  - `unit_tests/` - Generator unit tests
  - `integration_tests/` - End-to-end pipeline tests
  - `deployment_tests/` - Infrastructure validation
- Domain-specific expectation suites:
  - Slot Machine, Player, Compliance, Financial, Security, Table Games

#### Notebooks
- **notebooks/** - Fabric-importable notebooks
  - Bronze layer ingestion
  - Silver layer transformations
  - Gold layer aggregations
  - Real-time analytics examples

#### POC Agenda
- **poc-agenda/** - 3-Day workshop materials
  - Day 1: Foundation (Bronze/Silver)
  - Day 2: Transformation (Gold/Real-Time)
  - Day 3: Intelligence (Power BI/Purview)

#### CI/CD
- **.github/workflows/** - GitHub Actions workflows
  - Infrastructure deployment
  - Validation tests
  - Code quality checks

### Security
- Environment variable management (.env.sample)
- PII handling patterns
- Compliance framework support (NIGC MICS, FinCEN BSA, PCI-DSS)

---

## 📊 Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 1.1.0 | 2025-01-21 | Docker, Dev Container, Power BI templates, Cost estimation, Sample data |
| 1.0.0 | 2025-01-21 | Initial release with full POC capabilities |

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

[⬆️ Back to Top](#-changelog) | [📚 Docs](docs/index.md) | [🏠 Main README](README.md)

</div>
