# Changelog

All notable changes to the Microsoft Fabric Casino/Gaming POC will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Additional Power BI report templates
- Azure Data Factory pipeline integration
- Enhanced compliance reporting

---

## [1.2.0] - 2025-01-28

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

## [1.1.0] - 2025-01-21

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

## [1.0.0] - 2025-01-21

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

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 1.1.0 | 2025-01-21 | Docker, Dev Container, Power BI templates, Cost estimation, Sample data |
| 1.0.0 | 2025-01-21 | Initial release with full POC capabilities |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.
