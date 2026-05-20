# PRP: Phase 14 — One-Stop Shop Completion

> **Vision:** Make this repo the definitive enterprise reference for Microsoft Fabric — covering MLOps, SRE operations, data management maturity, all major migration paths, commercial industry verticals, and complete Fabric feature coverage.

## Summary

Phase 14 closes the highest-impact gaps identified in the Phase 13 audit: thin MLOps lifecycle coverage, empty `docs/runbooks/`, missing data management maturity (MDM, contracts, products), incomplete migration paths (Synapse, Databricks, Redshift, BigQuery), missing commercial industry verticals (Healthcare, Financial Services, Retail, Manufacturing, Energy, Telecom), under-documented Fabric features (Variable Libraries, FUAM, Lakehouse Schemas, OneLake Files-vs-Tables), weak developer experience (no consumer apps, no notebook unit-test pattern), and structural debt (flat best-practices, broken notebook→docs cross-references, thin use cases).

## User Story

**As an** enterprise data architect, ML engineer, SRE, or industry practitioner evaluating or adopting Microsoft Fabric
**I want** a single repository that answers every question I have — from "how do I run an SRE on-call rotation for a Fabric capacity?" to "show me a production fraud detection pattern in Financial Services" to "give me a Synapse → Fabric migration playbook"
**So that** I can build, operate, govern, and scale Fabric workloads at enterprise scale without stitching together fragmented Microsoft Learn articles, vendor blogs, and Stack Overflow answers.

## Problem Statement

The repo is strong on Casino + Federal verticals, medallion architecture, RTI, Direct Lake, and governance. It is materially weak in:

1. **MLOps production discipline** — model registry, drift detection, RAG patterns, LLM cost tracking, responsible AI, feature stores
2. **SRE operations** — `docs/runbooks/` is empty (one README); no SLO/SLI definitions, on-call playbooks, or incident response procedures
3. **Data management maturity** — no MDM, data contracts, data product framework, late-arriving data, reference data versioning
4. **Migration breadth** — Teradata/Snowflake/DB2 covered; Synapse/Databricks/Redshift/BigQuery missing
5. **Security frameworks** — SOC 2 Type II, GDPR right-to-deletion, STRIDE threat model, zero-trust blueprint absent
6. **Commercial verticals** — only Tribal Healthcare exists; no commercial healthcare, finance, retail, manufacturing, energy, telecom
7. **Fabric feature gaps** — Variable Libraries, FUAM, Lakehouse Schemas, OneLake Files-vs-Tables under-documented
8. **Developer experience** — no sample consumer apps (Streamlit/React/Power Apps), no VS Code local dev workflow, no notebook unit-testing pattern
9. **Structural** — flat `best-practices/` directory, blurry feature-vs-best-practice boundaries, 72 notebooks not cross-referenced from docs, thin (<2K word) use cases

## Solution Statement

Deliver Phase 14 across **9 sequential waves**, mirroring the Phase 7 harness pattern (PRP → wave-scoped tasks → harness execution → regression). Each wave produces a coherent slice of value and is independently regression-tested. Total scope: ~85 features across docs, notebooks, sample apps, Bicep, and structural refactors.

## Metadata

| Field | Value |
|-------|-------|
| Type | NEW_CAPABILITY + ENHANCEMENT + REFACTOR |
| Complexity | HIGH |
| Systems Affected | docs/, tutorials/, notebooks/, infra/, scripts/, validation/, sample-apps/ (new), mkdocs.yml |
| Dependencies | MkDocs Material, Bicep, fabric-cicd, pytest, Great Expectations, Streamlit (new), Power BI Desktop, VS Code Fabric extension |
| Estimated Tasks | ~85 features across 9 waves |
| Target Duration | 8-12 weeks (harness-driven) |
| Archon Project ID | `c0f96f03-5095-4704-a167-9a3f5a3e3ed1` |

---

## UX: Before / After

### Before State

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                              BEFORE STATE                                      ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  USER_FLOW: Architect lands on repo → finds excellent medallion + casino +    ║
║             federal content → searches for "Synapse migration" → not found    ║
║             → searches for "incident response" → empty runbooks folder        ║
║             → searches for "fraud detection" → not found → leaves to Bing     ║
║  PAIN_POINT: Repo claims "one-stop shop" but practitioner must leave for      ║
║              MLOps, SRE, commercial verticals, major migrations               ║
║  DATA_FLOW: docs (38 best-practices, 38 features, 10 use-cases) → tutorials   ║
║             (39) → notebooks (72, ~50% unreferenced) → infra (Bicep)          ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

### After State

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                               AFTER STATE                                      ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  USER_FLOW: Architect lands on repo → DECISION_TREES.md routes them to        ║
║             correct domain → finds Synapse migration tutorial → finds         ║
║             SRE runbook → finds fraud detection vertical → finds Streamlit    ║
║             consumer app → ships in week, not quarter                         ║
║  VALUE_ADD: Repo delivers on "one-stop shop" promise. Practitioner stays      ║
║             inside repo for MLOps, ops, verticals, migrations, dev exp.       ║
║  DATA_FLOW: docs (organized by architecture/operations/security/perf) →       ║
║             runbooks (8 playbooks) → tutorials (45+) → notebooks (cross-      ║
║             referenced, +15) → sample-apps (3) → infra (Bicep, +3 modules)    ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## Mandatory Reading

**CRITICAL: Read these files before starting any wave.**

| Priority | File | Lines | Why Read This |
|----------|------|-------|---------------|
| P0 | `CLAUDE.md` | all | Project conventions, phase status, file naming |
| P0 | `MEMORY.md` | all | Conventions, naming patterns, commit format |
| P0 | `docs/index.md` | all | Doc landing-page pattern to MIRROR |
| P0 | `docs/best-practices/medallion-architecture-deep-dive.md` | all | Best-practice doc style to MIRROR |
| P0 | `docs/features/digital-twin-builder.md` | all | Feature doc style to MIRROR |
| P0 | `docs/use-cases/agricultural-analytics.md` | all | Use-case doc style to MIRROR |
| P0 | `tutorials/30-tribal-healthcare/README.md` | all | Tutorial style to MIRROR (emoji headers, badges, Mermaid) |
| P0 | `notebooks/bronze/01_bronze_slot_telemetry.py` | all | Bronze notebook pattern to MIRROR |
| P0 | `notebooks/silver/01_silver_slot_cleansed.py` | all | Silver notebook pattern to MIRROR |
| P0 | `notebooks/gold/01_gold_slot_performance.py` | all | Gold notebook pattern to MIRROR |
| P1 | `data_generation/generators/base_generator.py` | all | Generator base class to INHERIT |
| P1 | `validation/unit_tests/test_generators.py` | 1-100 | Test pattern to MIRROR |
| P1 | `infra/main.bicep` | all | IaC orchestration entry point |
| P1 | `infra/modules/fabric/fabric-capacity.bicep` | all | Bicep module pattern to MIRROR |
| P1 | `mkdocs.yml` | all | Navigation structure to UPDATE |
| P1 | `validation/phase7_regression_report.md` | all | Regression report format to MIRROR |
| P2 | `.github/workflows/deploy-fabric.yml` | all | CI/CD pattern to extend |
| P2 | `scripts/fabric-cicd-deploy.py` | all | Deployment script pattern |

---

## Patterns to Mirror

### Best-Practice Doc Header
```markdown
# {Title} — {One-Line Subtitle}

> **TL;DR:** {2-sentence summary of what reader will learn}

[![Last Updated](https://img.shields.io/badge/Updated-2026--04--27-blue)]()
[![Phase](https://img.shields.io/badge/Phase-14-green)]()
[![Difficulty](https://img.shields.io/badge/Level-Intermediate-orange)]()

## Table of Contents
{auto-generated TOC}

## Why This Matters
{Concrete pain point with example}

## Reference Architecture
```mermaid
{architecture diagram}
```
```

### Use-Case Doc Skeleton (5-8K words target)
```markdown
# {Industry} — {Use Case Name}

## Business Problem
## Regulatory Context
## Reference Architecture (Mermaid)
## Data Sources & Schemas
## Medallion Implementation
  ### Bronze ingestion
  ### Silver cleansing & validation
  ### Gold business KPIs
## Real-Time Path (if applicable)
## ML / AI Components
## Power BI Semantic Model
## Cost Estimate (CU + Storage)
## ROI Model
## Compliance Mapping
## Production Checklist
## Published References
```

### Tutorial Skeleton
```markdown
# Tutorial {NN}: {Title}

> **What you'll build:** {one sentence}
> **Time:** {N} minutes | **Difficulty:** {level} | **Prereqs:** Tutorial {M}

## Learning Objectives
## Prerequisites
## Architecture
{Mermaid}
## Step 1: ...
## Step 2: ...
## Verification
## Cleanup
## Next Steps
```

### Notebook Header (PySpark)
```python
# Databricks notebook source
# MAGIC %md
# MAGIC # {Title}
# MAGIC
# MAGIC **Layer:** {Bronze|Silver|Gold}
# MAGIC **Domain:** {casino|federal-{agency}|commercial-{vertical}}
# MAGIC **Sources:** {list}
# MAGIC **Outputs:** {list}
# MAGIC **Related Doc:** [{doc title}]({relative path})

# COMMAND ----------
# MAGIC %md ## Configuration
# COMMAND ----------
import sys
from notebookutils import mssparkutils  # NOT dbutils
```

### Generator Pattern
```python
from data_generation.generators.base_generator import BaseGenerator
from typing import Dict, Any

class {Domain}Generator(BaseGenerator):
    """{Industry/Agency} synthetic data generator."""

    def generate_record(self) -> Dict[str, Any]:
        return {...}

    def generate_batch(self, n: int) -> list[Dict[str, Any]]:
        return [self.generate_record() for _ in range(n)]
```

### Bicep Module Header
```bicep
@description('{Module purpose}')
metadata name = '{module-name}'
metadata description = '{What it does}'
metadata owner = 'fgarofalo56'

@description('Resource location')
param location string = resourceGroup().location

@description('Resource tags')
param tags object = {}
```

### Commit Format
```
feat(phase14/wave{N}): {component} — {action}
docs(phase14/wave{N}): {component} — {action}
fix(phase14/wave{N}): {component} — {action}
```

---

## NOT Building (Scope Limits)

- **Production deployments to live Azure** — All new IaC is template-only; user deploys
- **Real customer data ingestion** — Only synthetic generators or open APIs
- **Replacing existing strong content** — Phase 14 is additive; do not rewrite phases 1-13 unless explicitly listed
- **New programming languages** — Stay in Bicep / Python / PySpark / KQL / DAX / TypeScript (Streamlit/React only for sample apps)
- **Mobile apps, native iOS/Android** — Out of scope
- **Non-Fabric Azure services beyond integration points** — No general Azure ML, Synapse, ADF deep-dives unless they're a migration source
- **Multi-cloud beyond migration sources** — No "run Fabric on AWS" content
- **Translating docs to non-English languages** — English only

---

## Wave Plan

### Wave 1 — Operations & SRE Runbooks (P0)

**Goal:** Populate the empty `docs/runbooks/` and add SRE discipline.

| # | File | Action | Description |
|---|------|--------|-------------|
| 1.1 | `docs/runbooks/incident-response-template.md` | CREATE | Severity matrix, comms tree, blameless postmortem template |
| 1.2 | `docs/runbooks/capacity-throttling-response.md` | CREATE | Detect (CU usage > 90%), mitigate (scale, pause), prevent (autoscale, queues) |
| 1.3 | `docs/runbooks/pipeline-failure-triage.md` | CREATE | Symptom→cause matrix, retry/replay, alert wiring |
| 1.4 | `docs/runbooks/auth-failure-playbook.md` | CREATE | Workspace Identity, Service Principal, Managed Identity failure modes |
| 1.5 | `docs/runbooks/multi-region-failover.md` | CREATE | OneLake geo-redundancy, capacity failover, RTO/RPO targets |
| 1.6 | `docs/runbooks/tenant-migration-dev-staging-prod.md` | CREATE | Workspace promotion via Deployment Pipelines + fabric-cicd |
| 1.7 | `docs/runbooks/data-quality-incident.md` | CREATE | GE failure → quarantine → root cause → backfill |
| 1.8 | `docs/best-practices/operations/slo-sli-fabric.md` | CREATE | Latency p99, success rate, freshness SLOs with concrete thresholds |
| 1.9 | `docs/best-practices/operations/oncall-rotation-handbook.md` | CREATE | Rotation cadence, escalation, paging integration (Action Groups) |
| 1.10 | `docs/best-practices/operations/change-management.md` | CREATE | RFC template, freeze windows, rollback playbooks |
| 1.11 | `docs/best-practices/operations/observability-stack.md` | CREATE | Log Analytics + Workspace Monitoring + Action Groups + Grafana |
| 1.12 | `infra/modules/monitoring/action-groups.bicep` | CREATE | Pager/email/Teams alert routing |
| 1.13 | `infra/modules/monitoring/log-analytics-workspace.bicep` | CREATE | Workspace + diagnostic settings + retention |

**Wave 1 Acceptance:**
- `docs/runbooks/` contains 7 playbooks + index
- Each runbook: trigger conditions, steps, verification, rollback, on-call escalation
- All runbooks linked from `docs/best-practices/monitoring-observability.md`
- Bicep modules deployable, validated by `az bicep build`

---

### Wave 2 — MLOps & AI Lifecycle Maturity (P0)

**Goal:** Production-grade ML and AI lifecycle. Today's Copilot/Agents/AutoML docs are demo-grade.

| # | File | Action | Description |
|---|------|--------|-------------|
| 2.1 | `docs/best-practices/mlops-fabric-production.md` | CREATE | Model registry (MLflow), experiment tracking, batch+online inference, canary, A/B |
| 2.2 | `docs/best-practices/model-monitoring-drift-detection.md` | CREATE | Statistical drift, concept drift, performance degradation, alert wiring |
| 2.3 | `docs/best-practices/feature-store-onelake.md` | CREATE | Versioned features, point-in-time joins, online/offline serving |
| 2.4 | `docs/best-practices/responsible-ai-framework.md` | CREATE | SHAP/LIME, fairness metrics (demographic parity, equal opportunity), bias remediation |
| 2.5 | `docs/best-practices/llm-cost-tracking.md` | CREATE | Token budgets, rate limiting, fallback model strategy, cost attribution |
| 2.6 | `docs/features/rag-patterns-deep-dive.md` | CREATE | Chunking strategies, retrieval evaluation (recall@k, MRR), hybrid search, reranking |
| 2.7 | `docs/features/prompt-engineering-fabric.md` | CREATE | System prompts, few-shot, chain-of-thought, structured outputs in Fabric notebooks |
| 2.8 | `docs/features/eval-harness-llm.md` | CREATE | Promptfoo / DeepEval / custom eval harness on Fabric |
| 2.9 | `notebooks/ml/04_mlops_model_registry.py` | CREATE | MLflow registry + Fabric ML endpoints + champion/challenger |
| 2.10 | `notebooks/ml/05_drift_detection.py` | CREATE | KS test, PSI, performance drift on Casino slot revenue model |
| 2.11 | `notebooks/ml/06_feature_store_demo.py` | CREATE | OneLake-backed feature table + point-in-time correctness |
| 2.12 | `notebooks/ml/07_rag_eventhouse_vector.py` | CREATE | Eventhouse vector + retrieval + reranking + eval |
| 2.13 | `notebooks/ml/08_responsible_ai_audit.py` | CREATE | SHAP + fairness audit on lending model |
| 2.14 | `tutorials/39-mlops-end-to-end/README.md` | CREATE | Multi-step tutorial: train → register → deploy → monitor → retrain |
| 2.15 | `tutorials/40-rag-production/README.md` | CREATE | RAG with Eventhouse vector + Data Agents + eval harness |

**Wave 2 Acceptance:**
- 5 best-practice docs covering MLOps, drift, feature store, responsible AI, LLM cost
- 3 feature docs covering RAG, prompt engineering, eval harness
- 5 ML notebooks with end-to-end runnable examples
- 2 multi-step tutorials
- All cross-linked from `docs/features/data-agents.md`, `docs/features/automl-model-endpoints.md`, `docs/features/fabric-iq.md`

---

### Wave 3 — Data Management Maturity (P0)

**Goal:** Data-as-product thinking, MDM, contracts, late-arriving data.

| # | File | Action | Description |
|---|------|--------|-------------|
| 3.1 | `docs/best-practices/data-management/master-data-management.md` | CREATE | MDM topology (registry/coexistence/hub), match-merge, golden record |
| 3.2 | `docs/best-practices/data-management/data-contracts.md` | CREATE | Schema contracts, breaking-change policy, GE enforcement at boundaries |
| 3.3 | `docs/best-practices/data-management/data-product-framework.md` | CREATE | Product = Lakehouse + SLA + owner + discoverability + deprecation |
| 3.4 | `docs/best-practices/data-management/reference-data-versioning.md` | CREATE | Lookup tables with effective dating, distribution, consumption |
| 3.5 | `docs/best-practices/data-management/late-arriving-data.md` | CREATE | Backfills, corrections, watermarks, idempotency |
| 3.6 | `docs/best-practices/data-management/scd-patterns.md` | CREATE | SCD Type 1/2/3/6 in Delta Lake with MERGE patterns |
| 3.7 | `docs/best-practices/data-management/business-glossary-automation.md` | CREATE | Purview term sync, schema-to-glossary linkage |
| 3.8 | `notebooks/gold/40_mdm_golden_customer.py` | CREATE | Match-merge with fuzzy + deterministic rules |
| 3.9 | `notebooks/gold/41_scd_type2_dimension.py` | CREATE | SCD2 MERGE with effective_from/to + current_flag |
| 3.10 | `notebooks/gold/42_reference_data_versioned.py` | CREATE | Versioned reference table + temporal queries |
| 3.11 | `notebooks/silver/40_late_arriving_backfill.py` | CREATE | Watermarked backfill with idempotent MERGE |
| 3.12 | `validation/great_expectations/data_contract_suite.py` | CREATE | GE expectation suite enforcing data contract |

**Wave 3 Acceptance:**
- 7 best-practice docs in new `docs/best-practices/data-management/` subdir
- 4 production-ready notebooks with synthetic data
- 1 GE suite enforcing data contract
- All docs link from `docs/best-practices/data-governance-deep-dive.md`

---

### Wave 4 — Migration Completeness (P1)

**Goal:** Cover the three biggest real-world migration paths.

| # | File | Action | Description |
|---|------|--------|-------------|
| 4.1 | `tutorials/41-synapse-to-fabric/README.md` | CREATE | Dedicated SQL pool → Warehouse, Spark pool → Fabric Spark, ADLS Gen2 → OneLake |
| 4.2 | `tutorials/41-synapse-to-fabric/01_assessment.py` | CREATE | Workload inventory script, complexity scoring |
| 4.3 | `tutorials/41-synapse-to-fabric/02_schema_conversion.py` | CREATE | T-SQL → Fabric Warehouse T-SQL diff |
| 4.4 | `tutorials/41-synapse-to-fabric/03_pipeline_migration.md` | CREATE | Synapse Pipelines → Fabric Data Pipelines |
| 4.5 | `tutorials/42-databricks-to-fabric/README.md` | CREATE | Workspace, Delta tables, Unity Catalog, MLflow |
| 4.6 | `tutorials/42-databricks-to-fabric/01_delta_compatibility.py` | CREATE | Iceberg vs Delta, V-Order, MLflow registry sync |
| 4.7 | `tutorials/42-databricks-to-fabric/02_workflow_migration.md` | CREATE | Databricks Jobs → Fabric Pipelines + Spark Job Definitions |
| 4.8 | `tutorials/43-redshift-to-fabric/README.md` | CREATE | UNLOAD → OneLake, dist/sort keys → V-Order, RA3 → CU mapping |
| 4.9 | `tutorials/44-bigquery-to-fabric/README.md` | CREATE | BigQuery export → OneLake, partitioning/clustering → Delta partitioning |
| 4.10 | `tutorials/45-onprem-ssas-ssis-ssrs/README.md` | CREATE | SSAS Tabular → Power BI semantic, SSIS → Pipelines, SSRS → Paginated |
| 4.11 | `docs/best-practices/migration-patterns.md` | UPDATE | Add Synapse, Databricks, Redshift, BigQuery, SSAS sections |
| 4.12 | `data_generation/generators/migration/synapse_workload_inventory.py` | CREATE | Synthetic Synapse workload metadata for assessment demo |
| 4.13 | `data_generation/generators/migration/databricks_workload_inventory.py` | CREATE | Synthetic Databricks workload metadata |

**Wave 4 Acceptance:**
- 5 new migration tutorials (Synapse, Databricks, Redshift, BigQuery, SSAS/SSIS/SSRS)
- 2 assessment generators
- `migration-patterns.md` updated with all 5 sources
- Each tutorial has assessment → schema conversion → workflow migration → validation

---

### Wave 5 — Security & Compliance Frameworks (P1)

**Goal:** Auditor-facing compliance frameworks beyond what's already covered.

| # | File | Action | Description |
|---|------|--------|-------------|
| 5.1 | `docs/best-practices/security/soc2-type2-readiness.md` | CREATE | AICPA Trust Services Criteria → Fabric controls mapping |
| 5.2 | `docs/best-practices/security/iso27001-mapping.md` | CREATE | Annex A controls → Fabric implementation |
| 5.3 | `docs/best-practices/security/gdpr-right-to-deletion.md` | CREATE | DSAR workflow, cascading deletes across medallion + Eventhouse + Power BI |
| 5.4 | `docs/best-practices/security/ccpa-privacy-rights.md` | CREATE | California-specific deletion + opt-out workflows |
| 5.5 | `docs/best-practices/security/threat-model-stride.md` | CREATE | STRIDE per-component for reference architecture |
| 5.6 | `docs/best-practices/security/zero-trust-blueprint.md` | CREATE | Conditional Access + device compliance + Workspace Identity + Private Endpoints |
| 5.7 | `docs/best-practices/security/data-exfiltration-prevention.md` | CREATE | OAP, COPY INTO restrictions, egress monitoring, DLP integration |
| 5.8 | `docs/best-practices/security/supply-chain-security.md` | CREATE | Notebook vetting, pip pinning, environment files, Iceberg shortcut review |
| 5.9 | `docs/best-practices/security/audit-trail-immutability.md` | CREATE | Log Analytics retention, immutable storage, tamper-evident workflows |
| 5.10 | `docs/compliance-templates/soc2-control-matrix.xlsx-template.md` | CREATE | Template that maps each SOC 2 CC criterion to Fabric evidence |
| 5.11 | `docs/compliance-templates/dsar-runbook.md` | CREATE | Step-by-step DSAR fulfillment runbook |
| 5.12 | `notebooks/silver/41_gdpr_cascading_delete.py` | CREATE | DSAR cascading delete across Bronze/Silver/Gold |
| 5.13 | `infra/modules/security/private-endpoint.bicep` | CREATE | Private Endpoint module for OneLake/Fabric |

**Wave 5 Acceptance:**
- 9 best-practice docs in new `docs/best-practices/security/` subdir
- 2 compliance templates
- 1 DSAR cascading delete notebook
- 1 new Bicep module
- STRIDE threat model includes data flow diagram with trust boundaries

---

### Wave 6 — Commercial Industry Verticals (P1)

**Goal:** Move beyond Casino + Federal into commercial enterprise verticals.

For each vertical, deliver: 1 use-case doc (5-8K words), 1 generator, 3 medallion notebooks (Bronze/Silver/Gold), 1 tutorial.

| # | Vertical | Use Case | Files |
|---|----------|----------|-------|
| 6.1 | Healthcare (Commercial) | Hospital operations + claims | `docs/use-cases/commercial-healthcare-operations.md`, `data_generation/generators/healthcare/hospital_operations_generator.py`, `notebooks/{bronze,silver,gold}/50_healthcare_*.py`, `tutorials/46-commercial-healthcare/README.md` |
| 6.2 | Financial Services | Fraud detection + AML | `docs/use-cases/financial-fraud-detection.md`, `data_generation/generators/financial/transaction_generator.py`, `notebooks/{bronze,silver,gold}/51_financial_*.py`, `tutorials/47-financial-services/README.md` |
| 6.3 | Insurance | Claims prediction + underwriting | `docs/use-cases/insurance-claims-analytics.md`, `data_generation/generators/insurance/claims_generator.py`, `notebooks/{bronze,silver,gold}/52_insurance_*.py`, `tutorials/48-insurance/README.md` |
| 6.4 | Retail/CPG | Demand forecasting + promotion effectiveness | `docs/use-cases/retail-demand-forecasting.md`, `data_generation/generators/retail/sales_generator.py`, `notebooks/{bronze,silver,gold}/53_retail_*.py`, `tutorials/49-retail-cpg/README.md` |
| 6.5 | Manufacturing/IoT | Predictive maintenance + OEE | `docs/use-cases/manufacturing-predictive-maintenance.md`, `data_generation/generators/manufacturing/sensor_generator.py`, `notebooks/{bronze,silver,gold}/54_manufacturing_*.py`, `tutorials/50-manufacturing-iot/README.md` |
| 6.6 | Energy/Utilities | Smart meter + grid analytics | `docs/use-cases/energy-grid-analytics.md`, `data_generation/generators/energy/meter_generator.py`, `notebooks/{bronze,silver,gold}/55_energy_*.py`, `tutorials/51-energy-utilities/README.md` |
| 6.7 | Telecom | Churn + network analytics | `docs/use-cases/telecom-churn-network.md`, `data_generation/generators/telecom/cdr_generator.py`, `notebooks/{bronze,silver,gold}/56_telecom_*.py`, `tutorials/52-telecom/README.md` |
| 6.8 | Pharma/Life Sciences | Clinical trial analytics | `docs/use-cases/pharma-clinical-trials.md`, `data_generation/generators/pharma/trial_generator.py`, `notebooks/{bronze,silver,gold}/57_pharma_*.py`, `tutorials/53-pharma/README.md` |
| 6.9 | Media/Entertainment | Audience + content recommendation | `docs/use-cases/media-audience-analytics.md`, `data_generation/generators/media/event_generator.py`, `notebooks/{bronze,silver,gold}/58_media_*.py`, `tutorials/54-media/README.md` |

**Per-vertical compliance mapping:**
- Healthcare → HIPAA + HITRUST
- Financial Services → SOX + PCI-DSS + Basel III + GLBA
- Insurance → NAIC Model Audit Rule
- Retail → PCI-DSS
- Manufacturing → IEC 62443 (OT security)
- Energy → NERC CIP
- Telecom → CPNI + GDPR
- Pharma → 21 CFR Part 11 + GxP
- Media → COPPA + GDPR

**Wave 6 Acceptance:**
- 9 use-case docs (5K+ words each)
- 9 generators inheriting from BaseGenerator with unit tests
- 27 notebooks (3 per vertical × 9 verticals)
- 9 tutorials with architecture, step-by-step, verification, ROI
- Each vertical has a corresponding compliance section

---

### Wave 7 — Fabric Feature Coverage Completion (P2)

**Goal:** Close remaining feature documentation gaps.

| # | File | Action | Description |
|---|------|--------|-------------|
| 7.1 | `docs/features/variable-libraries.md` | CREATE | Parameterized pipelines, env-specific values, secrets binding |
| 7.2 | `docs/features/fabric-unified-admin-monitoring.md` | CREATE | FUAM tenant-wide observability, capacity utilization dashboards |
| 7.3 | `docs/features/user-data-functions.md` | CREATE | Serverless C#/Python functions in Fabric |
| 7.4 | `docs/features/apache-airflow-job.md` | CREATE | Managed Airflow in Fabric, when-to-use vs Pipelines |
| 7.5 | `docs/features/spark-job-definitions-deep-dive.md` | CREATE | SJD vs notebooks, Java/Scala/Python/R, environment files |
| 7.6 | `docs/features/notebook-resources-environments.md` | CREATE | Resource files, %run, environment YAML, library management |
| 7.7 | `docs/features/tmdl-power-bi-developer-mode.md` | CREATE | TMDL semantic model authoring, source control |
| 7.8 | `docs/features/onelake-shortcuts-s3-gcs-dataverse.md` | CREATE | Multi-cloud shortcut patterns, auth, refresh, cost |
| 7.9 | `docs/best-practices/onelake-files-vs-tables.md` | CREATE | Decision matrix: when Files, when Tables, perf trade-offs |
| 7.10 | `docs/best-practices/lakehouse-schema-versioning.md` | CREATE | Schema evolution, breaking changes, dual-write, deprecation |
| 7.11 | `docs/best-practices/spark-runtime-breaking-changes-matrix.md` | CREATE | Library-by-library 1.2 → 1.3 → 2.0 breaking changes |
| 7.12 | `docs/best-practices/v-order-tuning-deep-dive.md` | CREATE | When V-Order helps, when it hurts, OPTIMIZE strategy |
| 7.13 | `docs/best-practices/partition-strategy-decision-tree.md` | CREATE | Cardinality, query patterns, compaction, partition pruning |
| 7.14 | `docs/best-practices/query-optimization-deep-dive.md` | CREATE | Predicate pushdown, broadcast joins, AQE, shuffle tuning |
| 7.15 | `notebooks/bronze/19_variable_library_demo.py` | CREATE | Pipeline parameterized via Variable Library |

**Wave 7 Acceptance:**
- 8 new feature docs
- 6 new best-practice docs
- 1 demo notebook
- All linked from `docs/index.md` and `mkdocs.yml`

---

### Wave 8 — Developer Experience (P2)

**Goal:** Make the repo a great place to develop, not just read about Fabric.

| # | File | Action | Description |
|---|------|--------|-------------|
| 8.1 | `sample-apps/streamlit-fabric-consumer/app.py` | CREATE | Streamlit app querying Fabric SQL endpoint with charts |
| 8.2 | `sample-apps/streamlit-fabric-consumer/requirements.txt` | CREATE | Pinned deps |
| 8.3 | `sample-apps/streamlit-fabric-consumer/README.md` | CREATE | Setup, auth (Service Principal), run, deploy to Container Apps |
| 8.4 | `sample-apps/react-graphql-consumer/` | CREATE | React + Apollo querying Fabric API for GraphQL |
| 8.5 | `sample-apps/power-apps-canvas-consumer/README.md` | CREATE | Canvas app pattern, Translytical Task Flow integration |
| 8.6 | `sample-apps/logic-app-orchestrator/README.md` | CREATE | Logic App calling Fabric Pipelines via REST |
| 8.7 | `docs/best-practices/dev-experience/vscode-fabric-workflow.md` | CREATE | VS Code Fabric extension, sync, local edit, debug |
| 8.8 | `docs/best-practices/dev-experience/notebook-unit-testing.md` | CREATE | pytest + nbval + %run patterns + CI examples |
| 8.9 | `docs/best-practices/dev-experience/local-spark-debugging.md` | CREATE | PySpark local install, mocking mssparkutils, fixture patterns |
| 8.10 | `docs/best-practices/dev-experience/git-workflow-fabric.md` | CREATE | Branch strategy, conflict resolution for `.platform`/`.notebook-content` |
| 8.11 | `docs/best-practices/dev-experience/devcontainer-setup.md` | CREATE | Dev container with Bicep + PySpark + Fabric CLI |
| 8.12 | `validation/unit_tests/notebook/test_bronze_pattern.py` | CREATE | Unit test pattern for Bronze notebooks using local Spark |
| 8.13 | `.devcontainer/devcontainer.json` | CREATE/UPDATE | Reproducible dev environment |

**Wave 8 Acceptance:**
- 4 sample consumer apps (Streamlit working end-to-end, React/Power Apps/Logic App documented)
- 5 dev-experience best-practice docs
- 1 working notebook unit test
- Reproducible devcontainer

---

### Wave 9 — Structural Refactor & Cross-References (Critical UX)

**Goal:** Fix flat structure, broken cross-references, thin use cases, blurry feature/BP boundaries.

| # | Task | Action | Description |
|---|------|--------|-------------|
| 9.1 | Reorganize `docs/best-practices/` | REFACTOR | Move existing docs into subdirs: `architecture/`, `operations/`, `security/`, `performance/`, `data-management/`, `dev-experience/`. Add 301-style index redirects in old location. |
| 9.2 | `docs/DECISION_TREES.md` | CREATE | Master decision matrix: Lakehouse vs Warehouse vs SQL DB, RTI vs batch, Direct Lake vs Import, Notebooks vs SJD vs Pipelines, Mirroring vs Shortcut vs Pipeline |
| 9.3 | `docs/TROUBLESHOOTING_MATRIX.md` | CREATE | Symptom-indexed: slow query, capacity throttle, auth failure, ingestion lag, Power BI refresh failure |
| 9.4 | `docs/CHEAT_SHEETS.md` | CREATE | PySpark+Fabric API cheat sheet, KQL essentials, T-SQL Fabric quirks, DAX patterns |
| 9.5 | `docs/FAQ.md` | UPDATE | Add 25+ new entries: query perf, MLOps, migrations, security, dev experience |
| 9.6 | `notebooks/README.md` | CREATE | Cross-reference index: each notebook → tutorial → feature doc |
| 9.7 | `infra/modules/README.md` | CREATE | Bicep module index, parameter reference, feature mapping |
| 9.8 | `docs/use-cases/*.md` | EXPAND | Bring all 10 existing use-case docs to 5K+ words with arch diagrams, cost models, ROI |
| 9.9 | `mkdocs.yml` | UPDATE | New nav structure with subdirectories, add all Wave 1-8 docs |
| 9.10 | `docs/index.md` | UPDATE | Update landing page with Phase 14 deliverables, new decision-tree links |
| 9.11 | `README.md` | UPDATE | Repo-root README updated with Phase 14 summary, new directory layout |
| 9.12 | `CHANGELOG.md` | UPDATE | Phase 14 entries per wave |
| 9.13 | `CLAUDE.md` | UPDATE | Phase 14 status, new directory conventions |
| 9.14 | Notebook header backfill | UPDATE | All 72 existing notebooks → add `Related Doc:` link in header |
| 9.15 | Validation: link checker | RUN | `mkdocs-linkcheck` or equivalent; zero broken internal links |
| 9.16 | `validation/phase14_regression_report.md` | CREATE | Final regression report covering all 9 waves |

**Wave 9 Acceptance:**
- `docs/best-practices/` reorganized into 6 subdirs without breaking external links (use redirects)
- 4 new top-level navigation docs (DECISION_TREES, TROUBLESHOOTING_MATRIX, CHEAT_SHEETS, expanded FAQ)
- All 72 existing notebooks have `Related Doc:` cross-reference
- All 10 existing use-cases expanded to 5K+ words
- mkdocs builds with zero broken links
- Final regression report

---

## Files to Change (Summary)

| Category | Count | Action |
|----------|-------|--------|
| New best-practice docs | ~32 | CREATE |
| New feature docs | ~11 | CREATE |
| New use-case docs | ~9 | CREATE (commercial verticals) |
| Expanded use-case docs | 10 | UPDATE |
| New runbooks | 7 | CREATE |
| New tutorials | ~14 | CREATE |
| New notebooks | ~50 | CREATE |
| Updated notebooks | 72 | UPDATE (cross-ref headers only) |
| New generators | ~10 | CREATE |
| New Bicep modules | 4 | CREATE |
| New sample apps | 4 | CREATE |
| New compliance templates | 2 | CREATE |
| Structural refactor | — | REFACTOR `docs/best-practices/` into subdirs |
| Index/README updates | ~8 | UPDATE |

**Total artifacts: ~225 files created or modified**

---

## Validation Commands

### Level 1: STATIC_ANALYSIS

```bash
# Bicep
az bicep build --file infra/main.bicep
az bicep build --file infra/modules/monitoring/action-groups.bicep
az bicep build --file infra/modules/monitoring/log-analytics-workspace.bicep
az bicep build --file infra/modules/security/private-endpoint.bicep

# Python
ruff check data_generation/ validation/ scripts/ sample-apps/
mypy data_generation/ --ignore-missing-imports

# MkDocs build (catches broken nav, missing files)
mkdocs build --strict
```

**EXPECT:** Exit 0, no errors

### Level 2: UNIT_TESTS

```bash
# Existing 612 tests must still pass (no regressions)
pytest validation/unit_tests/ -v

# New Wave 6 vertical generator tests
pytest validation/unit_tests/healthcare/ -v
pytest validation/unit_tests/financial/ -v
pytest validation/unit_tests/insurance/ -v
pytest validation/unit_tests/retail/ -v
pytest validation/unit_tests/manufacturing/ -v
pytest validation/unit_tests/energy/ -v
pytest validation/unit_tests/telecom/ -v
pytest validation/unit_tests/pharma/ -v
pytest validation/unit_tests/media/ -v

# Wave 8 notebook unit tests
pytest validation/unit_tests/notebook/ -v
```

**EXPECT:** All tests pass. Phase 14 adds ~150 new tests on top of existing 612 (target: 760+ tests).

### Level 3: FULL_SUITE + DATA QUALITY

```bash
# Full pytest
pytest validation/ -v --tb=short

# Great Expectations
great_expectations checkpoint run bronze_checkpoint
great_expectations checkpoint run silver_checkpoint
great_expectations checkpoint run gold_checkpoint
great_expectations checkpoint run data_contract_checkpoint  # New in Wave 3

# Link checking
mkdocs build --strict
# (or use external linkcheck tool if mkdocs-strict insufficient)

# Bicep what-if (no live deploy)
az deployment sub what-if --location eastus2 \
  --template-file infra/main.bicep \
  --parameters infra/environments/dev/dev.bicepparam
```

**EXPECT:** All tests pass, GE suites pass, no broken links, Bicep what-if shows expected resources only.

---

## Testing Strategy

### Unit Tests to Write

| Test File | Test Cases | Validates |
|-----------|------------|-----------|
| `validation/unit_tests/healthcare/test_hospital_generator.py` | record shape, batch size, HIPAA-safe fields | Wave 6.1 |
| `validation/unit_tests/financial/test_transaction_generator.py` | fraud injection rate, schema, PCI scrubbing | Wave 6.2 |
| `validation/unit_tests/insurance/test_claims_generator.py` | claim distribution, denial rate, PII handling | Wave 6.3 |
| `validation/unit_tests/retail/test_sales_generator.py` | seasonality, promotion uplift, returns | Wave 6.4 |
| `validation/unit_tests/manufacturing/test_sensor_generator.py` | failure injection, OEE components | Wave 6.5 |
| `validation/unit_tests/energy/test_meter_generator.py` | interval data, anomaly injection | Wave 6.6 |
| `validation/unit_tests/telecom/test_cdr_generator.py` | call duration distribution, churn signal | Wave 6.7 |
| `validation/unit_tests/pharma/test_trial_generator.py` | enrollment, AE rate, blinding | Wave 6.8 |
| `validation/unit_tests/media/test_event_generator.py` | session, watch time, recommendation events | Wave 6.9 |
| `validation/unit_tests/notebook/test_bronze_pattern.py` | local Spark mock, mssparkutils mock | Wave 8 |
| `validation/unit_tests/migration/test_synapse_inventory.py` | workload classification | Wave 4 |
| `validation/unit_tests/migration/test_databricks_inventory.py` | workload classification | Wave 4 |

### Edge Cases Checklist (per wave)

- [ ] Empty input data
- [ ] Schema mismatch on ingest
- [ ] Late-arriving records (Wave 3)
- [ ] Drift detection thresholds (Wave 2)
- [ ] DSAR cascade misses one layer (Wave 5)
- [ ] Capacity throttling mid-pipeline (Wave 1)
- [ ] Auth token expiry mid-job (Wave 1)
- [ ] Cross-region failover during write (Wave 1)
- [ ] Vertical-specific compliance edge cases (Wave 6)

---

## Acceptance Criteria

- [ ] All 9 waves completed
- [ ] ~225 artifacts created or modified
- [ ] All Level 1-3 validation commands pass with exit 0
- [ ] 612 existing tests still pass (zero regressions)
- [ ] ~150 new tests added (target: 760+ total)
- [ ] All new docs follow header/style patterns from Mandatory Reading
- [ ] All Mermaid diagrams render in MkDocs Material
- [ ] mkdocs.yml navigation updated for all new docs
- [ ] No broken internal links (mkdocs --strict)
- [ ] Each new use-case doc ≥ 5K words
- [ ] Each runbook has trigger / steps / verification / rollback / escalation sections
- [ ] All 72 existing notebooks have `Related Doc:` cross-reference
- [ ] Phase 14 regression report committed
- [ ] CHANGELOG.md, README.md, CLAUDE.md updated
- [ ] Sample apps have working end-to-end demos (at minimum Streamlit)

---

## Completion Checklist

- [ ] Wave 1 (Operations & SRE) complete + validated
- [ ] Wave 2 (MLOps & AI) complete + validated
- [ ] Wave 3 (Data Management) complete + validated
- [ ] Wave 4 (Migration) complete + validated
- [ ] Wave 5 (Security & Compliance) complete + validated
- [ ] Wave 6 (Commercial Verticals) complete + validated
- [ ] Wave 7 (Feature Coverage) complete + validated
- [ ] Wave 8 (Developer Experience) complete + validated
- [ ] Wave 9 (Structural Refactor) complete + validated
- [ ] Final regression report: `validation/phase14_regression_report.md`
- [ ] mkdocs builds clean
- [ ] PR created and merged to main

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Scope creep — verticals expand to 15+ | HIGH | HIGH | Hard cap at 9 commercial verticals in Wave 6; defer rest to Phase 15 |
| Use-case expansion to 5K+ words takes longer than tutorial creation | MED | MED | Use a fixed template (see Patterns to Mirror); mandate sections rather than freeform |
| Restructure of `best-practices/` breaks external links/SEO | MED | MED | Add 301-redirect markdown stubs in old paths; update only after redirects in place |
| Sample apps require Service Principal / live Fabric to demo | HIGH | LOW | Provide mock-mode + recorded GIFs for those without Fabric access |
| MLOps notebooks require MLflow + ML Endpoints which may be in preview | MED | MED | Pin to GA features only; mark preview features clearly with banner |
| 50 new notebooks risk inconsistent style | HIGH | MED | Enforce notebook header template; add CI lint for header presence |
| Compliance docs (SOC 2, GDPR) drift out of date with regulatory changes | LOW | MED | Add `Last Reviewed:` date; commit to quarterly review |
| Migration tutorials require source systems we don't have access to | HIGH | LOW | Use synthetic inventories + documented patterns; mark as "pattern guide" not "live demo" |
| Vertical compliance mappings could be wrong (HIPAA, PCI, etc.) | MED | HIGH | Cite Microsoft published references; mark "verify with your compliance team" |
| Wave 9 refactor causes harness or CI confusion | MED | MED | Refactor LAST after all content waves complete; single-commit refactor; CI run before merge |

---

## Notes

### Execution Strategy

**Recommended approach: Use the Phase 7 harness pattern.**

1. **Initializer pass:** Generate `phase14_features.json` from this PRP (one feature per row in wave tables)
2. **Per-wave coding sessions:** Run harness for each wave; allow ~1-2 weeks per wave depending on parallelism
3. **Per-wave regression:** Run Level 1 + Level 2 validation after each wave completes
4. **Final wave (Wave 9):** Structural refactor MUST be last, after all content waves
5. **Final regression:** Run Level 3 full suite + GE + mkdocs strict
6. **PR strategy:** One PR per wave to keep review-able size; final integration PR for Wave 9 refactor

### Archon Setup

Create wave-level Archon tasks under project `c0f96f03-5095-4704-a167-9a3f5a3e3ed1`:

- Wave 1 task_order: 95
- Wave 2 task_order: 90
- Wave 3 task_order: 85
- Wave 4 task_order: 80
- Wave 5 task_order: 75
- Wave 6 task_order: 70
- Wave 7 task_order: 65
- Wave 8 task_order: 60
- Wave 9 task_order: 50 (must run last)

### Key Design Decisions

1. **Why "data-management" as a separate subdir** (not under best-practices flat): The existing flat directory is at 32+ files; semantic grouping is the only way to make it navigable.

2. **Why expand existing use-cases vs create new ones first**: Existing use-cases set the bar at 1-2K words. New 5-8K verticals would create inconsistency unless existing ones are brought up. Wave 9 enforces parity.

3. **Why sample apps in `sample-apps/` (new top-level)**: Keeps consumer code separate from platform code. Distinct deploy target (Container Apps vs Fabric).

4. **Why compliance is split between Wave 5 (frameworks) and Wave 6 (per-vertical)**: Frameworks are horizontal (SOC 2 applies to all); vertical compliance is industry-specific (HIPAA only for healthcare).

5. **Why MLOps before commercial verticals**: Several verticals (Financial fraud, Manufacturing predictive maintenance, Insurance claims) build on MLOps patterns — wave order matters.

6. **Why structural refactor last**: Refactoring file paths mid-flight would break in-flight harness sessions. Single-shot refactor at end is safest.

### Future Phases (out of Phase 14 scope)

- **Phase 15:** Additional verticals (gov-state-local, education, agriculture, hospitality, real-estate)
- **Phase 16:** Advanced patterns (event-driven architectures, multi-tenant SaaS on Fabric, edge analytics)
- **Phase 17:** Internationalization (docs translation, multi-region deployment patterns)
- **Phase 18:** Video content (recorded walkthroughs of every tutorial)

### Success Metrics

- Repository delivers on "one-stop shop" promise: practitioner can answer 90%+ of questions without leaving the repo
- 760+ passing tests
- Zero broken internal links
- All sample apps demoable in <15 min from clone
- Each wave delivers reviewable, mergeable value independently
- Phase 14 regression report shows zero regressions

---

**PRP Author:** Claude Code (Opus 4.7)
**Date:** 2026-04-27
**Status:** READY FOR HARNESS INITIALIZATION
**Estimated Calendar Time:** 8-12 weeks
**Estimated Files:** ~225 created or modified
**Prerequisites:** Phase 13 complete, harness configured, Archon project active
