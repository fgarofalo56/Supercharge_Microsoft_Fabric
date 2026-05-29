---
hero: assets/heroes/financial-services.svg
hero_alt: Insurance claims analytics + denial prediction
type: feature
---
# Insurance Claims Analytics - P&C Carrier Use Case

!!! info "Third-party references — publicly sourced, good-faith comparison"
    This page references non-Microsoft products and services. That information is drawn from each vendor's **publicly available documentation** and is offered for honest, good-faith comparison only. This is a personal project written from a Microsoft Fabric and Azure perspective; it does **not** claim expertise in, or authority over, any third-party product, and nothing here is an official statement by, or endorsed by, those vendors. Capabilities, pricing, and features change often — always verify against the vendor's current official documentation. Where a third-party offering is the stronger choice, we say so plainly.

## Executive Summary

A mid-market Property & Casualty (P&C) insurance carrier with **$3 billion in gross written premium (GWP)**, approximately **500,000 active policies** across four lines of business, and **120,000 claims per year** deploys Microsoft Fabric to unify claims intake, fraud detection, loss reserving, and statutory reporting into a single lakehouse platform. The solution replaces fragmented legacy systems (AS/400 policy admin, Guidewire ClaimCenter, standalone fraud vendor, Excel-based reserving) with an end-to-end analytics architecture that delivers **ML-driven severity triage at FNOL**, **graph-based fraud ring detection**, **automated loss triangle development**, and **NAIC-compliant statutory data feeds** -- all on a single Fabric F64 capacity.

**Key Outcomes:**
- **$12M annual fraud savings** from network-analysis-based fraud ring detection
- **15% improvement in reserve accuracy** reducing adverse development
- **60% reduction in claims triage time** via ML severity prediction at first notice of loss
- **Automated NAIC statutory reporting** eliminating 200+ hours/quarter of manual preparation

---

## Industry Context

### P&C Insurance Data Landscape

Property & Casualty insurance generates massive, interconnected datasets spanning the full policy lifecycle:

| Data Domain | Volume | Velocity | Variety |
|-------------|--------|----------|---------|
| Policy administration | 500K active policies, 2M endorsements/yr | Daily batch | Structured (ISO/ACORD) |
| Claims (FNOL to closure) | 120K new claims/yr, 45K open at any time | Real-time FNOL, daily batch | Structured + unstructured (adjuster notes, photos) |
| Loss runs & triangles | 10 accident years x 4 LOBs x 50 states | Monthly/quarterly | Structured actuarial |
| Agent/broker channel | 8,000 appointed agents | Daily commissions | Structured |
| Reinsurance | Treaty and facultative placements | Quarterly | Semi-structured |
| Regulatory filings | NAIC Annual/Quarterly statements | Quarterly/annual | Fixed-format statutory |

### Lines of Business

| LOB | GWP | Policy Count | Avg Premium | Claims Frequency |
|-----|-----|-------------|-------------|-----------------|
| Personal Auto | $1.2B | 280,000 | $4,286 | 18% |
| Homeowners | $900M | 120,000 | $7,500 | 8% |
| Commercial Multi-Peril | $600M | 70,000 | $8,571 | 12% |
| Workers' Compensation | $300M | 30,000 | $10,000 | 15% |

### Regulatory Environment

P&C carriers operate under extensive state and federal regulation:

- **NAIC Model Audit Rule (MAR):** Requires annual audit of financial statements and internal controls over financial reporting. Adopted in all 50 states. Carriers with >$500M in premium must maintain a formal enterprise risk management (ERM) function and file an Own Risk and Solvency Assessment (ORSA). See [NAIC Model Audit Rule](https://content.naic.org/cipr-topics/model-audit-rule).
- **State Department of Insurance (DOI):** Each state DOI requires quarterly and annual statutory financial statements filed via NAIC Financial Data Repository. Rate filings, market conduct exams, and complaint tracking are state-specific.
- **Risk-Based Capital (RBC):** NAIC RBC formula determines minimum capital adequacy. Data quality in loss reserves directly impacts RBC ratios -- reserve deficiencies trigger regulatory action levels.
- **NAIC Statistical Agent Reporting:** Carriers report premium and loss data to statistical agents (ISO, NCCI for workers' comp) for industry-wide ratemaking.
- **Fair Claims Settlement Practices:** Model Unfair Claims Settlement Practices Act requires timely acknowledgment (15 days), investigation, and payment of claims.

---

## Solution Architecture

### Data Flow Overview

```
Policy Admin (AS/400)  ──┐
Guidewire ClaimCenter  ──┤
Agent Portal           ──┤──►  Files/landing/insurance/  ──►  Bronze  ──►  Silver  ──►  Gold
SIU Referrals          ──┤                                      │           │           │
Reinsurance Treaties   ──┘                                      │           │           │
                                                                ▼           ▼           ▼
                                                          bronze_ins_*  silver_ins_*  gold_ins_*
```

### Medallion Architecture

#### Bronze Layer: Raw Ingestion

| Table | Source | Records/Day | Retention |
|-------|--------|-------------|-----------|
| `bronze_insurance_policies` | Policy admin extract | ~2,000 new/endorsed | 7 years |
| `bronze_insurance_claims` | ClaimCenter API | ~330 new FNOL + updates | 10 years |
| `bronze_insurance_adjusters` | HR/adjuster system | ~50 changes/day | 5 years |
| `bronze_insurance_payments` | Claims payments | ~800 transactions/day | 10 years |
| `bronze_insurance_agents` | Agent portal | ~100 changes/day | 7 years |

Raw data is ingested as-is with `_ingested_at` timestamp and `_source_file` metadata. No transformations, no deduplication. Schema is enforced at read time to catch upstream changes early.

#### Silver Layer: Validated & Enriched

| Table | Transformations | Quality Checks |
|-------|----------------|----------------|
| `silver_insurance_claims` | Deduplicated on claim_id, policy-claim linkage validated, loss_type standardized to ISO codes, report_lag calculated, development_age computed | Reserve > 0, valid policy reference, loss_dt <= report_dt, status in valid set |
| `silver_insurance_policies` | Effective/expiry date validation, premium earned calculation, state code standardization | Premium > 0, valid LOB, effective_dt < expiry_dt |

#### Gold Layer: Analytics & Reporting

| Table | Purpose | Grain |
|-------|---------|-------|
| `gold_insurance_loss_triangles` | Actuarial loss development triangles | Accident quarter x development quarter x LOB x state |
| `gold_insurance_fraud_scores` | Fraud probability scores with feature vectors | Per claim |
| `gold_insurance_loss_ratios` | Loss ratio by LOB, state, agent, quarter | Aggregated |
| `gold_insurance_kpis` | Executive dashboard metrics | Daily/monthly |
| `gold_insurance_statutory` | NAIC statutory schedule P data | Annual statement format |

### Claims Intake Triage with ML Severity Prediction

At FNOL, the system predicts claim severity using features available at intake:

**Feature Engineering:**
- `loss_type_encoded`: One-hot encoded ISO loss type
- `report_lag_days`: Days between loss and report (longer lag correlates with higher severity)
- `policy_tenure_months`: How long the policy has been active
- `prior_claims_count`: Number of prior claims on the same policy
- `lob_risk_score`: Historical severity by line of business
- `state_litigation_index`: State-level litigation environment score
- `claimant_age`: Age of claimant (for workers' comp and auto BI)
- `weather_cat_flag`: Whether loss date falls in a CAT-declared event

**Model:** Gradient-boosted classifier (LightGBM) trained on 3 years of closed claims, predicting severity tier (minor / moderate / major / catastrophic). Retrained quarterly. AUC > 0.82 on holdout.

**Triage Actions:**
| Predicted Severity | Action | SLA |
|-------------------|--------|-----|
| Minor (<$5K) | Auto-assign to desk adjuster pool | 30-day closure target |
| Moderate ($5K-$50K) | Assign to experienced adjuster | 60-day investigation |
| Major ($50K-$250K) | Senior adjuster + supervisor review | 90-day management |
| Catastrophic (>$250K) | Major loss unit + reinsurance notice | Immediate escalation |

### Fraud Ring Detection Using Network Analysis

Insurance fraud accounts for an estimated **$80 billion annually** across the U.S. industry (Coalition Against Insurance Fraud). Organized fraud rings -- coordinated groups of claimants, providers, attorneys, and sometimes insiders -- account for a disproportionate share of losses.

**Network Construction:**
- **Nodes:** Claimants, policyholders, agents, medical providers, attorneys, repair shops, adjusters
- **Edges:** Shared address, shared phone, same-day claims, shared provider, attorney referral patterns, policy-claim links

**Detection Signals:**
1. **Community detection:** Louvain algorithm identifies tightly connected clusters
2. **Velocity anomalies:** Multiple claims from the same network within a short window
3. **Provider concentration:** Unusually high referral rates to specific providers
4. **Address overlap:** Multiple claimants sharing the same address across different policies
5. **Staged accident patterns:** Multiple vehicles, similar damage descriptions, specific intersections

**Scoring:** Each claim receives a `fraud_score` (0-100) based on weighted network features. Claims scoring >75 are auto-referred to the Special Investigations Unit (SIU). Historical hit rate on SIU referrals improved from 22% to 58% after network analysis deployment.

### Loss Ratio Analytics

Loss ratio (incurred losses / earned premium) is the fundamental P&C profitability metric. The gold layer computes loss ratios at multiple grains:

- **By LOB:** Identify unprofitable lines for re-underwriting
- **By State:** Geographic profitability for regulatory filings and market strategy
- **By Agent:** Agent-level loss ratios drive commission tiers and appointment decisions
- **By Accident Quarter:** Trend analysis for pricing adequacy
- **Combined Ratio:** Loss ratio + expense ratio for overall underwriting profitability

### Reserving Accuracy (IBNR & Case Reserves)

**Incurred But Not Reported (IBNR)** reserves represent the carrier's estimate of claims that have occurred but have not yet been reported. Accurate IBNR estimation is critical for:
- Financial statement accuracy (NAIC Model Audit Rule)
- Risk-Based Capital adequacy
- Reinsurance recoverable calculations
- Pricing adequacy assessment

**Loss Triangle Development:**
The gold layer builds standard actuarial loss development triangles:

```
                Development Quarter
Accident Qtr    1       2       3       4       5       ...     Ultimate
2024-Q1         $45M    $52M    $55M    $56M    $56.2M          $56.5M
2024-Q2         $48M    $54M    $57M    $58M
2024-Q3         $43M    $50M    $53M
2024-Q4         $47M    $55M
2025-Q1         $50M
```

**Methods Supported:**
- Chain-ladder (weighted average development factors)
- Bornhuetter-Ferguson (blend of expected and actual)
- Cape Cod (weighted B-F variant)

**Reserve Monitoring Dashboard:**
- Actual vs. expected development by accident quarter
- Case reserve adequacy by adjuster (identifies over/under-reserving tendencies)
- Adverse/favorable development alerts when actual exceeds expected by >10%

### Subrogation Recovery Optimization

Subrogation -- recovering claim payments from at-fault third parties -- represents a significant revenue opportunity. The system identifies high-recovery-probability claims using:

- **Liability indicators:** Police reports indicating third-party fault
- **Recovery history:** Historical recovery rates by loss type and state
- **Statute of limitations tracking:** Automated alerts before recovery rights expire
- **Vendor performance:** Recovery rates by subrogation vendor/attorney

**Target:** Improve subrogation recovery rate from 35% to 50% on eligible claims, representing ~$8M additional annual recoveries.

---

## NAIC Compliance & Statutory Reporting

### Model Audit Rule Requirements

The NAIC Model Audit Rule (Model #205) requires carriers to maintain internal controls over financial reporting, including:

1. **Data integrity controls:** Reconciliation between policy admin, claims, and general ledger
2. **Reserve adequacy:** Independent actuarial opinion with data quality attestation
3. **IT general controls:** Change management, access controls, segregation of duties for data systems
4. **Management testing:** Annual testing of key controls with documented evidence

**Fabric Implementation:**
- Delta Lake ACID transactions ensure data integrity across medallion layers
- Row-level security on claims data enforces need-to-know access
- Audit logging via Fabric activity logs provides change trail
- Automated reconciliation notebooks compare bronze totals to source system extracts

### Risk-Based Capital Data Quality

RBC calculations depend on accurate:
- **Net premium earned** by line and state
- **Loss reserves** (case + IBNR) by line and accident year
- **Loss adjustment expense reserves**
- **Reinsurance recoverables**

Data quality issues in any of these inputs can result in:
- Understated RBC ratio triggering Company Action Level (200% threshold)
- Regulatory Action Level (150%) requiring corrective plan
- Authorized Control Level (100%) allowing commissioner to seize the company

The gold layer includes automated data quality checks that flag discrepancies before statutory filing.

### State DOI Requirements

- **Quarterly financial statements:** Schedule P (loss development), Schedule F (reinsurance)
- **Rate filings:** Supporting loss data for rate change justification
- **Market conduct:** Claims handling timeliness metrics per Unfair Claims Settlement Practices Act
- **Complaint tracking:** NAIC Complaint Index data feed

---

## Cost Model

### Fabric F64 Capacity Allocation

| Workload | CU Allocation | Monthly Cost |
|----------|--------------|--------------|
| Bronze ingestion (daily batch + real-time FNOL) | 15% | $2,700 |
| Silver validation & enrichment | 20% | $3,600 |
| Gold aggregation & triangles | 25% | $4,500 |
| ML scoring (severity + fraud) | 15% | $2,700 |
| Power BI Direct Lake dashboards | 15% | $2,700 |
| Ad-hoc actuarial analysis | 10% | $1,800 |
| **Total** | **100%** | **$18,000** |

### ROI Analysis

| Benefit | Annual Value | Confidence |
|---------|-------------|------------|
| Fraud ring detection (incremental SIU recoveries) | $12,000,000 | High |
| Reserve accuracy improvement (reduced adverse development) | $8,000,000 | Medium |
| Subrogation recovery optimization | $8,000,000 | Medium |
| Claims triage efficiency (adjuster FTE savings) | $2,400,000 | High |
| Statutory reporting automation | $500,000 | High |
| **Total Annual Benefit** | **$30,900,000** | |
| **Annual Platform Cost** | **$216,000** | |
| **ROI** | **143:1** | |

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)
- Deploy Fabric F64 capacity
- Establish medallion lakehouse architecture
- Ingest policy and claims data into bronze
- Build silver validation layer

### Phase 2: Analytics (Weeks 5-8)
- Build loss triangle gold tables
- Implement loss ratio analytics by LOB/state/agent
- Create executive claims dashboard
- Deploy severity prediction model (v1)

### Phase 3: Advanced (Weeks 9-12)
- Fraud network graph construction
- SIU referral automation
- Subrogation scoring model
- NAIC statutory data feed automation

### Phase 4: Optimization (Weeks 13-16)
- Model retraining pipeline
- Reserve monitoring alerts
- Agent performance scorecards
- Market conduct compliance reporting

---

## Data Pipeline Notebooks

| Notebook | Layer | Purpose |
|----------|-------|---------|
| `52_insurance_claims.py` | Bronze | Ingest raw claims data with schema enforcement |
| `52_insurance_validated.py` | Silver | Validate, deduplicate, compute report lag & development age |
| `52_insurance_predictions.py` | Gold | Loss triangles, fraud scores, loss ratios, IBNR, KPIs |

---

## Key Metrics & KPIs

| Metric | Definition | Target |
|--------|-----------|--------|
| Loss Ratio | Incurred losses / earned premium | <65% (all lines) |
| Combined Ratio | Loss ratio + expense ratio | <98% |
| Claims Closure Rate | Claims closed / claims opened (rolling 12mo) | >85% |
| Average Days to Close | Mean days from FNOL to closure | <45 days |
| Fraud Detection Rate | SIU confirmed fraud / total SIU referrals | >50% |
| Subrogation Recovery Rate | Recovered / eligible subrogation amount | >45% |
| Reserve Adequacy | (Case reserve + IBNR) / ultimate incurred | 95-105% |
| FNOL Triage Accuracy | Correct severity prediction / total predictions | >80% |
| Statutory Filing Timeliness | Filed on time / total filings | 100% |

---

## References

- [NAIC Model Audit Rule (Model #205)](https://content.naic.org/cipr-topics/model-audit-rule)
- [NAIC Risk-Based Capital](https://content.naic.org/cipr-topics/risk-based-capital)
- [NAIC Own Risk and Solvency Assessment (ORSA)](https://content.naic.org/cipr-topics/own-risk-and-solvency-assessment-orsa)
- [Coalition Against Insurance Fraud - By the Numbers](https://insurancefraud.org/fraud-stats/)
- [NAIC Unfair Claims Settlement Practices Act (Model #900)](https://content.naic.org/sites/default/files/model-law-900.pdf)
- [ISO ClaimSearch](https://www.verisk.com/insurance/products/claimsearch/)
- [Microsoft Fabric Documentation](https://learn.microsoft.com/en-us/fabric/)
- [Delta Lake ACID Transactions](https://docs.delta.io/latest/concurrency-control.html)

---

*This use case is part of the Supercharge Microsoft Fabric POC -- Commercial Verticals expansion.*
