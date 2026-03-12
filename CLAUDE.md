# Claude Code - Microsoft Fabric POC Project

## Project Overview

**Name:** Supercharge Microsoft Fabric - Casino/Gaming Industry POC + Federal Expansions
**Type:** Infrastructure + Documentation + Data Engineering
**Primary Stack:** Bicep, Python, PySpark, KQL, DAX
**Target Platform:** Microsoft Fabric (F64 SKU)
**Phase Status:** Phase 7 Complete (71 features, 134 tests, 5 waves)

## Key Technologies

- **Infrastructure:** Azure Bicep, ARM Templates, GitHub Actions
- **Data Processing:** PySpark, Python, Delta Lake
- **Real-Time:** Eventstreams, Eventhouse, KQL
- **BI:** Power BI, Direct Lake, DAX
- **Governance:** Microsoft Purview
- **Testing:** pytest, Great Expectations

## Directory Structure

```
infra/              - Bicep IaC modules and deployments
docs/               - Architecture and deployment documentation
tutorials/          - 32 step-by-step tutorials (00-31)
poc-agenda/         - 3-day workshop materials
data-generation/    - 16 Python data generators (casino, federal, streaming, analytics)
notebooks/          - 35 Fabric-importable notebooks (medallion + streaming)
validation/         - 134 unit tests + Great Expectations data quality
future-expansions/  - Federal agency & industry expansion documentation
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
| `infra/main.bicep` | Root IaC orchestration |
| `infra/modules/fabric/fabric-capacity.bicep` | Fabric F64 deployment |
| `data-generation/generators/base_generator.py` | Generator base class |
| `notebooks/bronze/01_bronze_slot_telemetry.ipynb` | Primary Bronze pattern |

## Testing Commands

```bash
# Validate Bicep
az bicep build --file infra/main.bicep

# Run all 134 unit tests
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

## Context Notes

- Target SKU is F64 (P1 equivalent) for POC
- Casino domain uses NIGC MICS compliance standards
- Real-time focuses on casino floor monitoring
- Direct Lake is the primary BI connectivity method
- Purview provides governance and lineage
- Phase 7 adds HIPAA (Tribal Healthcare), FedRAMP (DOT/FAA), 42 CFR Part 2 compliance
- All federal datasets use real, publicly available APIs documented in `data-generation/config/federal_datasets.yaml`

## Archon Project ID

`c0f96f03-5095-4704-a167-9a3f5a3e3ed1`

Use this ID to track tasks and store project documentation in Archon.
