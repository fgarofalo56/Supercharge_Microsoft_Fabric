# Phase 14 / 15 Reconciliation — Shipped vs. Open

Evidence date: 2026-09-15. Source of truth: local working tree on `main` + deployed Pages site.
Method: each plan deliverable mapped to an existing repo path. "SHIPPED" = the file exists in the tree.

## Headline

The large majority of both phases is **already shipped**. The genuinely-open items are a small, bounded set.

---

## PHASE 14 — One-Stop Shop

### Wave 1 — Operations & SRE Runbooks — SHIPPED
- docs/runbooks/: incident-response-template, capacity-throttling-response, pipeline-failure-triage, auth-failure-playbook, multi-region-failover, tenant-migration-dev-staging-prod, data-quality-incident, disaster-recovery-execution, failed-refresh-triage, cost-spike-investigation, security-incident-response + index. (7 target; 12 present.)
- docs/best-practices/operations/: slo-sli-fabric, oncall-rotation-handbook, change-management, observability-stack. (All 4 present.)
- Bicep monitoring modules (1.12/1.13): NOT VERIFIED this pass — see Open items.

### Wave 2 — MLOps & AI Lifecycle — SHIPPED
- best-practices: mlops-fabric-production, model-monitoring-drift-detection, feature-store-onelake, responsible-ai-framework, llm-cost-tracking. (All 5.)
- features: rag-patterns-deep-dive, prompt-engineering-fabric, eval-harness-llm. (All 3.)
- notebooks/ml/: 04_mlops_model_registry, 05_drift_detection, 06_feature_store_demo, 07_rag_eventhouse_vector, 08_responsible_ai_audit. (All 5.)
- tutorials: 39-mlops-end-to-end, 40-rag-production. (Both present under docs/tutorials/.)

### Wave 3 — Data Management Maturity — SHIPPED
- best-practices/data-management/: master-data-management, data-contracts, data-product-framework, reference-data-versioning, late-arriving-data, scd-patterns, business-glossary-automation. (All 7.)
- notebooks/gold/: 40_mdm_golden_customer, 41_scd_type2_dimension, 42_reference_data_versioned. notebooks/silver/: 40_late_arriving_backfill. (All 4.)
- GE data-contract suite (3.12): NOT VERIFIED this pass — see Open items.

### Wave 4 — Migration Completeness — SHIPPED
- docs/tutorials/: 41-synapse-to-fabric, 42-databricks-to-fabric, 43-redshift-to-fabric, 44-bigquery-to-fabric, 45-onprem-ssas-ssis-ssrs. (All 5; plus extra 55-palantir, 56-informatica, 57-databricks-better-together.)
- data_generation/generators/migration/: synapse_workload_inventory, databricks_workload_inventory. (Both.)
- best-practices/migration-patterns.md present (UPDATE item 4.11 — content depth not re-audited).

### Wave 5 — Security & Compliance Frameworks — SHIPPED
- best-practices/security/: soc2-type2-readiness, iso27001-mapping, gdpr-right-to-deletion, ccpa-privacy-rights, threat-model-stride, zero-trust-blueprint, data-exfiltration-prevention, supply-chain-security, audit-trail-immutability (+ onelake-defense-in-depth). (All 9 + 1.)
- compliance-templates/: soc2-control-matrix, dsar-runbook (+ ctr, sar, w2g, mics). (Both target templates present.)
- notebooks/silver/41_gdpr_cascading_delete present.
- infra/modules/security/private-endpoint.bicep (5.13): NOT VERIFIED this pass — see Open items.

### Wave 6 — Commercial Industry Verticals — SHIPPED (docs/generators/notebooks)
- docs/industries/: healthcare, financial-services, retail-cpg, manufacturing, energy-utilities, telecommunications (+ index). 
- docs/use-cases/: commercial-healthcare-operations, financial-fraud-detection, insurance-claims-analytics, retail-demand-forecasting, manufacturing-predictive-maintenance, energy-grid-analytics, telecom-churn-network, pharma-clinical-trials, media-audience-analytics. (All 9.)
- generators: healthcare, financial, insurance, retail, manufacturing, energy, telecom, pharma, media dirs all present.
- notebooks/gold/: 50_healthcare … 58_media (all 9 gold). tutorials 46–54 all present.

### Wave 7 — Fabric Feature Coverage — SHIPPED
- features: variable-libraries, fabric-unified-admin-monitoring, user-data-functions, apache-airflow-job, spark-job-definitions-deep-dive, notebook-resources-environments, tmdl-power-bi-developer-mode, onelake-shortcuts-s3-gcs-dataverse. (All 8.)
- best-practices: onelake-files-vs-tables, lakehouse-schema-versioning, spark-runtime-breaking-changes-matrix, v-order-tuning-deep-dive, partition-strategy-decision-tree, query-optimization-deep-dive. (All 6.)

### Wave 8 — Developer Experience — MOSTLY SHIPPED
- best-practices/dev-experience/: vscode-fabric-workflow, notebook-unit-testing, local-spark-debugging, git-workflow-fabric, devcontainer-setup. (All 5.)
- docs/sample-apps/: streamlit-fabric-consumer, react-graphql-consumer, power-apps-canvas-consumer, logic-app-orchestrator. (All 4 — but under docs/, plan specified repo-root sample-apps/.)
- validation/unit_tests/notebook/test_bronze_pattern.py present.

### Wave 9 — Structural Refactor & Cross-References — PARTIAL
- best-practices/ reorganized into subdirs (operations/, security/, data-management/, dev-experience/): DONE.
- Top-level nav docs: decision-trees.md, troubleshooting-matrix.md, cheat-sheets.md, faq.md: ALL EXIST.
- OPEN: (9.8) use-case expansion to 5K+ words — currently 1,684–3,833 words; none reach 5K. (9.14) notebook 'Related Doc:' header backfill across all notebooks — not verified. (9.15) zero-broken-link validation run — not verified. (9.16) phase14 regression report — not found.

---

## PHASE 15 — Layout, Visual & CSA-in-a-Box Content

- WI1 nav-restructure: navigation.expand REMOVED; navigation.tabs + navigation.indexes present. SHIPPED.
- WI2 visual-foundation: docs/assets/heroes/ + diagrams/ + icons/ + images/ present (hero SVGs incl. decisions.svg, compliance-*.svg). SHIPPED.
- WI3 copilot-chat-enhance: docs/javascripts/copilot-chat.js + docs/stylesheets/copilot-chat.css present. SHIPPED (feature depth not re-audited).
- WI4 role-quickstarts: docs/quickstarts/ bi-developer, data-engineer, data-scientist, platform-admin, security-admin. SHIPPED (all 5).
- WI5 decision-trees: docs/decision-trees.md (503 lines, Mermaid). SHIPPED.
- WI6 industry-pages: docs/industries/ 6 verticals. SHIPPED.
- WI7 compliance-frameworks: docs/compliance/ fedramp, gdpr, hipaa, nist-800-53, pci-dss, soc2. SHIPPED (all 6).
- WI8 research-whitepapers: docs/research/ ai-readiness-assessment, data-mesh-maturity-model, enterprise-data-platform-comparison. SHIPPED (3).
- WI9 operational-runbooks: docs/runbooks/ 12 playbooks. SHIPPED.
- WI10 reference-architecture: docs/reference-architecture/ hybrid-cloud, large-enterprise-multi-domain, real-time-analytics, small-medium-enterprise. SHIPPED (4).

---

## CONFIRMED-SHIPPED (verified this pass, previously 'unverified')

- Bicep monitoring modules (1.12/1.13): infra/modules/monitoring/action-groups.bicep + log-analytics-workspace.bicep BOTH EXIST. SHIPPED.
- Bicep security module (5.13): infra/modules/security/private-endpoint.bicep EXISTS. SHIPPED.
- GE data-contract suite (3.12): validation/great_expectations/data_contract_suite.py EXISTS. SHIPPED.
- Phase-14 regression report (9.16): validation/phase14_regression_report.md + docs/validation/phase14_regression_report.md EXIST. SHIPPED.
- sample-apps (Wave 8): all 4 exist under docs/sample-apps/ (streamlit, react-graphql, power-apps, logic-app). SHIPPED — at docs/ path rather than repo-root; cosmetic path difference only.

## GENUINELY OPEN (the real residual backlog — confirmed by evidence)

1. **Use-case depth (P14 9.8)** — 19 use-case docs currently 1,684–3,833 words; plan target 5K+ each. None reach 5K. CONTENT WORK (~19 docs to expand). This is the one substantial content gap.
2. **Notebook 'Related Doc:' header backfill (P14 9.14)** — only 3 of 117 notebooks contain a 'Related Doc' marker; 10 reference a docs/ path. ~107 notebooks lack the cross-reference header. MECHANICAL.
3. **Zero-broken-link validation (P14 9.15)** — no link-checker configured in mkdocs.yml/pyproject (no mkdocs-linkcheck/lychee). VERIFICATION TOOLING absent; a full link audit has not been evidenced.

## Issues
- **#142 (campaign meta)** — THIS reconciliation is its first pilot deliverable. Recommend: post this matrix, then close #142 with the 3 open items above either (a) spun into a focused follow-up issue or (b) explicitly accepted as deferred. The campaign's broad 'inventory + reconcile' goal is met by this document.
- **#105 (repo rename)** — owner-executed GitHub setting (rename + redirect verification + CSA-in-a-Box notification). Cannot be closed by code; deferred by owner decision 2026-05. Recommend: keep open, or close as 'won't do for now' with the prepped 5-step sequence retained for when the owner chooses to execute.
