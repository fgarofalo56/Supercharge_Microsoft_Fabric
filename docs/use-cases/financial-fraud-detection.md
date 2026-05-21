---
hero: assets/heroes/financial-services.svg
hero_alt: Real-time fraud detection + AML
type: feature
---
# Financial Services: Real-Time Fraud Detection & Regulatory Compliance

## Executive Summary

This use case demonstrates how a mid-tier commercial bank with **$45 billion in assets under management (AUM)** and **2 million retail accounts** leverages Microsoft Fabric to unify real-time fraud detection, anti-money laundering (AML) monitoring, credit risk scoring, and regulatory reporting into a single analytics platform. The architecture replaces a fragmented legacy stack of batch-oriented SAS models, siloed data warehouses, and manual reconciliation processes with a modern lakehouse that delivers sub-second fraud decisioning and continuous compliance.

### Key Outcomes

| Metric | Before Fabric | After Fabric | Improvement |
|--------|--------------|--------------|-------------|
| Card fraud detection latency | 45 seconds | < 2 seconds | 95% faster |
| False-positive rate | 12% | 3.8% | 68% reduction |
| Annual fraud losses | $18.2M | $8.1M | $10.1M savings |
| AML alert triage time | 4.2 hours | 38 minutes | 85% faster |
| Regulatory report prep | 3 weeks | 2 days | 90% faster |
| Data platform cost | $1.2M/year | $300K/year | 75% reduction |

---

## Industry Context

### The Financial Services Challenge

Financial institutions face a converging set of pressures:

1. **Fraud escalation** - Card-not-present (CNP) fraud grew 30% YoY to $9.49B in US losses (Nilson Report 2025). Real-time authorization decisioning is table stakes.
2. **Regulatory burden** - Banks must comply with BSA/AML (31 CFR 1020), SOX Section 404, PCI DSS v4.0, Basel III capital adequacy, and GLBA privacy requirements simultaneously.
3. **Stress testing mandates** - CCAR and DFAST require banks with >$10B assets to run quarterly macro-economic scenario analyses across the full loan portfolio.
4. **Legacy modernization** - Most mid-tier banks run 15-20 year old SAS/Teradata stacks that cannot support real-time ML scoring or streaming ingestion.

### Regulatory Framework

| Regulation | Citation | Fabric Capability |
|-----------|----------|-------------------|
| Bank Secrecy Act (BSA) | 31 CFR 1020 | Eventstream + KQL for real-time CTR/SAR monitoring |
| SAR Filing | 12 CFR 21.11 (OCC) | Automated suspicious activity detection in Gold layer |
| Currency Transaction Reports | 31 CFR 1010.311 | Aggregation of cash transactions >$10,000 per customer per day |
| PCI DSS v4.0 | Req 3.4, 3.5 | Column-level encryption, tokenized PAN, audit logging |
| SOX Section 404 | 15 USC 7262 | Data lineage via Purview, immutable audit trail in Bronze |
| Basel III | 12 CFR 217 | Credit risk weighted asset calculation in Gold notebooks |
| GLBA (Privacy) | 15 USC 6801 | OneLake security, workspace RBAC, sensitivity labels |
| DFAST / CCAR | 12 CFR 252 | Stress testing data pipelines with scenario parameters |
| FFIEC Guidance | IT Examination Handbook | Monitoring & observability dashboards |
| UDAAP | 12 CFR 1036 | Fair lending analytics in Gold layer |

---

## Architecture

### System Overview

```
+---------------------+     +--------------------+     +-------------------+
|   Card Networks     |     |   Core Banking     |     |   Wire/ACH        |
|   (Visa, MC, etc.)  |     |   (FIS/Fiserv)     |     |   (FedWire/NACHA) |
+--------+------------+     +--------+-----------+     +--------+----------+
         |                           |                          |
         v                           v                          v
+--------+---------------------------+---------------------------+----------+
|                        Azure Event Hub / Eventstream                       |
|                    (Card auth events, wire transfers, ACH)                 |
+--------+---------------------------+---------------------------+----------+
         |                           |                          |
         v                           v                          v
+--------+---------------------------+---------------------------+----------+
|                              EVENTHOUSE                                    |
|   Hot path: velocity checks, geo-anomaly detection, amount spike          |
|   KQL real-time queries with 30-second materialized views                 |
+--------+-----------------------------------------------------------------+
         |
         v
+--------+-----------------------------------------------------------------+
|                          MICROSOFT FABRIC LAKEHOUSE                       |
|                                                                           |
|  +-------------+    +-----------------+    +---------------------------+  |
|  |   BRONZE    |    |     SILVER      |    |          GOLD             |  |
|  |             |    |                 |    |                           |  |
|  | Raw txns    |--->| Enriched txns   |--->| fraud_scores              |  |
|  | Raw accounts|    | Velocity feats  |    | aml_alerts                |  |
|  | Raw wires   |    | Geo-distance    |    | ctr_filings               |  |
|  | Audit log   |    | MCC enrichment  |    | portfolio_risk            |  |
|  +-------------+    +-----------------+    | stress_test_scenarios     |  |
|                                            +---------------------------+  |
+--------------------------------------------------------------------------+
         |
         v
+--------+-----------------------------------------------------------------+
|                           POWER BI (Direct Lake)                          |
|   Fraud Operations Dashboard | AML Case Management | Risk Reporting      |
+-------------------------------------------------------------------------- +
```

### Medallion Architecture Detail

#### Bronze Layer - Raw Ingestion

| Table | Source | Volume | Retention |
|-------|--------|--------|-----------|
| `bronze_financial_transactions` | Card auth events via Eventstream | ~8M txns/day | 7 years (SOX) |
| `bronze_financial_accounts` | Core banking nightly extract | 2M accounts | Current + 1 year |
| `bronze_financial_wires` | FedWire/SWIFT messages | ~50K/day | 5 years (BSA) |
| `bronze_financial_ach` | NACHA batch files | ~500K/day | 5 years |
| `bronze_audit_log` | Fabric audit events | Continuous | 7 years (SOX) |

**Key design decisions:**
- Append-only writes preserve the immutable audit trail required by SOX Section 404
- `input_file_name()` and `_ingested_at` metadata enable full data lineage
- PAN (Primary Account Number) is tokenized at ingestion per PCI DSS Req 3.4
- Raw files retained in OneLake cold tier for regulatory examination requests

#### Silver Layer - Enrichment & Feature Engineering

| Table | Transformations | SLA |
|-------|----------------|-----|
| `silver_financial_enriched` | MCC enrichment, velocity features (1h/24h/7d), geo-distance, dedup | < 5 min from Bronze |
| `silver_financial_accounts_current` | SCD Type 2, risk rating history | Nightly |
| `silver_wire_enriched` | OFAC screening flag, correspondent bank join | < 15 min |

**Velocity features computed:**
- `txn_count_1h` - Transaction count in last 1 hour per card
- `txn_count_24h` - Transaction count in last 24 hours per card
- `txn_count_7d` - Transaction count in last 7 days per card
- `avg_amount_30d` - Rolling 30-day average transaction amount
- `geo_distance_km` - Haversine distance from previous transaction location
- `time_since_last_txn_sec` - Seconds since last transaction

#### Gold Layer - Scoring & Alerts

| Table | Purpose | Refresh |
|-------|---------|---------|
| `gold_fraud_scores` | Per-transaction fraud probability (0-1) | Real-time (Eventstream) + hourly batch |
| `gold_aml_alerts` | CTR filings (>$10K), SAR candidates (structuring) | Hourly |
| `gold_portfolio_risk` | Basel III RWA, PD/LGD/EAD by segment | Daily |
| `gold_stress_scenarios` | CCAR/DFAST scenario outputs | Quarterly |
| `gold_daily_fraud_summary` | Fraud rate, loss amount, top merchants | Hourly |

### Real-Time Fraud Detection Flow

```
Card Swipe/Online Purchase
        |
        v
  Event Hub (< 50ms)
        |
        v
  Eventstream Ingestion
        |
        +---> Eventhouse (KQL)
        |       |
        |       +---> Velocity check (txns in last 1h)
        |       +---> Geo-anomaly (impossible travel)
        |       +---> Amount spike (> 3x avg)
        |       |
        |       v
        |     Risk Score (rules-based, < 200ms)
        |       |
        |       +---> score > 0.85 → DECLINE + alert
        |       +---> score 0.50-0.85 → STEP-UP AUTH
        |       +---> score < 0.50 → APPROVE
        |
        +---> Bronze table (append, async)
                |
                v
          Silver enrichment (batch, 5-min micro-batch)
                |
                v
          Gold fraud_scores (ML model re-score, hourly)
```

---

## Fraud Detection Models

### Rule-Based Scoring (Tier 1 - Real-Time)

These rules execute in KQL against the Eventhouse with sub-second latency:

| Rule | Condition | Score Contribution |
|------|-----------|-------------------|
| Velocity | > 5 txns in 1 hour | +0.25 |
| Geo-anomaly | > 500 km from last txn in < 1 hour | +0.30 |
| Amount spike | Amount > 3x rolling 30-day average | +0.20 |
| High-risk MCC | MCC in gambling, crypto, wire transfer | +0.15 |
| New merchant | First transaction at this merchant | +0.05 |
| Card-not-present | e-commerce without 3DS | +0.10 |
| Cross-border | International transaction on domestic card | +0.10 |
| Time anomaly | Transaction between 2-5 AM local time | +0.05 |

### ML-Based Scoring (Tier 2 - Batch)

The hourly batch job re-scores all transactions using a gradient-boosted model trained on historical fraud labels:

- **Model:** LightGBM classifier trained on 24 months of labeled fraud data
- **Features:** 47 engineered features from Silver layer
- **Performance:** AUC-ROC 0.967, Precision@95%Recall = 0.82
- **Retraining:** Monthly with champion/challenger framework
- **Hosting:** Fabric ML model endpoint via AutoML or custom training

### AML Transaction Monitoring

| Alert Type | Trigger | Regulation |
|-----------|---------|------------|
| CTR Filing | Single cash transaction >= $10,000 | 31 CFR 1010.311 |
| Structuring | Multiple cash txns $8,000-$9,999 within 48h, same customer | 31 CFR 1010.314 |
| Rapid movement | Large deposit followed by immediate wire-out (>80% of deposit) | BSA/AML guidance |
| Round-trip | Funds sent and returned within 72h via different channels | FinCEN advisory |
| High-risk geo | Wire to/from FATF high-risk jurisdiction | 31 CFR 1010.610 |

---

## Compliance Control Mapping

### SOX Section 404 - Internal Controls

| Control Objective | Fabric Implementation |
|------------------|----------------------|
| Data integrity | Bronze append-only Delta tables with time-travel |
| Change management | Fabric CI/CD via fabric-cicd, Git integration |
| Access controls | Workspace RBAC + OneLake security + sensitivity labels |
| Audit trail | Workspace monitoring + Purview lineage |
| Segregation of duties | Separate workspaces for dev/staging/prod |
| Data retention | Delta table retention policies (7-year minimum) |

### PCI DSS v4.0 Compliance

| Requirement | Implementation |
|-------------|---------------|
| Req 3.4 - Render PAN unreadable | Tokenization at ingestion; only card_hash stored |
| Req 3.5 - Protect cryptographic keys | Azure Key Vault with customer-managed keys |
| Req 7.1 - Restrict access | Workspace RBAC, item-level permissions |
| Req 8.3 - MFA | Entra ID Conditional Access |
| Req 10.1 - Audit trails | Fabric audit logs + Purview |
| Req 10.4 - Time synchronization | Azure platform NTP |
| Req 11.3 - Vulnerability scanning | Defender for Cloud integration |
| Req 12.8 - Service provider management | Azure compliance certifications |

### Basel III Capital Adequacy

The Gold layer computes risk-weighted assets (RWA) for the credit portfolio:

```
RWA = Sum(EAD_i * RiskWeight_i)

Where:
  EAD = Exposure at Default (outstanding balance + undrawn commitments * CCF)
  RiskWeight = f(PD, LGD, maturity) per IRB formula or standardized buckets:
    - Sovereign: 0%
    - Bank: 20-150% (rating-dependent)
    - Corporate: 20-150%
    - Retail mortgage: 35%
    - Other retail: 75%
    - Past due: 150%

CET1 Ratio = CET1 Capital / RWA >= 4.5% (minimum)
Total Capital Ratio = Total Capital / RWA >= 8.0% (minimum)
```

---

## Data Pipeline Implementation

### Prerequisites

| Component | Details |
|-----------|---------|
| Fabric capacity | F64 SKU (~$25,000/month) |
| Event Hub | Standard tier, 32 partitions |
| Azure Key Vault | Premium, HSM-backed for PCI |
| Purview | For governance and lineage |
| Entra ID | Conditional Access policies |

### Notebooks

| Notebook | Layer | Purpose |
|----------|-------|---------|
| `51_financial_transactions.py` | Bronze | Ingest raw card/ACH/wire transactions |
| `51_financial_enriched.py` | Silver | Enrich with velocity features, geo-distance, MCC |
| `51_financial_fraud_scoring.py` | Gold | Fraud scoring, AML alerts, portfolio risk |

### Data Generation

For POC demonstration, synthetic data is generated using the `TransactionGenerator`:

```python
from data_generation.generators.financial.transaction_generator import TransactionGenerator

gen = TransactionGenerator(seed=42, num_customers=10000)
txns = gen.generate(num_records=100000)
gen.to_parquet(txns, "landing/financial/transactions.parquet")
```

The generator produces realistic card transactions with:
- Configurable fraud rate (~0.15% baseline, matching industry averages)
- PCI-compliant: PAN tokenized, only card_hash stored
- Realistic MCC codes, amounts, and merchant names
- Embedded fraud patterns: velocity bursts, geo-anomalies, amount spikes

---

## Cost Model

### Monthly Fabric Costs (F64 SKU)

| Component | CU Consumption | Monthly Cost |
|-----------|---------------|--------------|
| Eventstream ingestion (8M events/day) | ~15% of F64 | $3,750 |
| Eventhouse (hot queries) | ~20% of F64 | $5,000 |
| Lakehouse storage (Delta, 50TB) | OneLake storage | $2,500 |
| Spark notebooks (Bronze/Silver/Gold) | ~25% of F64 | $6,250 |
| Power BI (Direct Lake, 50 users) | ~10% of F64 | $2,500 |
| ML model endpoints | ~10% of F64 | $2,500 |
| Headroom / burst | ~20% of F64 | $2,500 |
| **Total** | **100% F64** | **~$25,000** |

### ROI Analysis

| Category | Annual Value |
|----------|-------------|
| Fraud loss reduction | $10,100,000 |
| Legacy platform decommission | $900,000 |
| Analyst productivity (AML triage) | $450,000 |
| Regulatory reporting automation | $350,000 |
| **Total annual benefit** | **$11,800,000** |
| **Annual Fabric cost** | **$300,000** |
| **Net ROI** | **3,833%** |

---

## Power BI Dashboards

### Fraud Operations Dashboard

**Purpose:** Real-time fraud monitoring for the fraud operations team.

**Visuals:**
- Fraud rate trend (hourly, daily) - line chart
- Fraud by channel (card-present vs. CNP vs. ACH vs. wire) - stacked bar
- Geographic heat map of fraud incidents
- Top 10 merchants by fraud count
- Alert queue with case assignment
- KPI cards: fraud rate %, total losses today, false positive rate

**Connectivity:** Direct Lake to `gold_fraud_scores` and `gold_daily_fraud_summary`

### AML Case Management

**Purpose:** BSA/AML compliance officers review and disposition alerts.

**Visuals:**
- CTR filing queue (>$10K transactions)
- Structuring pattern alerts with transaction timeline
- Customer risk profile with account history
- SAR narrative auto-generation data
- Alert aging and SLA compliance

**Connectivity:** Direct Lake to `gold_aml_alerts`

### Executive Risk Dashboard

**Purpose:** CRO and board-level risk reporting.

**Visuals:**
- Basel III capital ratios (CET1, Tier 1, Total Capital)
- RWA by portfolio segment
- Credit quality migration matrix
- Stress test scenario comparison (baseline/adverse/severely adverse)
- Trend analysis of key risk indicators

**Connectivity:** Direct Lake to `gold_portfolio_risk` and `gold_stress_scenarios`

---

## Security & Access Control

### Workspace Architecture

```
Financial Services Workspaces
├── fin-dev          (developers - full access)
├── fin-staging      (CI/CD validation - automated)
├── fin-prod-ingest  (data engineers - contributor)
├── fin-prod-analytics (analysts - viewer + build)
└── fin-prod-compliance (BSA/AML officers - viewer)
```

### Data Classification

| Data Element | Sensitivity Label | Access |
|-------------|-------------------|--------|
| Card PAN (raw) | **Never stored** | N/A |
| Card hash | Confidential | Data engineers only |
| Transaction amounts | Internal | Analytics team |
| Customer PII | Highly Confidential | Compliance + need-to-know |
| Fraud scores | Confidential | Fraud ops + analytics |
| AML alerts | Highly Confidential | BSA officers only |
| Aggregate KPIs | Internal | All authorized users |

### Encryption

- **At rest:** Microsoft-managed keys (default) or customer-managed keys via Key Vault
- **In transit:** TLS 1.2+ enforced
- **Column-level:** PAN tokenized before entering Fabric; SSN hashed with HMAC-SHA-256
- **Key rotation:** Automatic 90-day rotation via Key Vault policy

---

## Deployment Guide

### Step 1: Infrastructure

```bash
az deployment sub create --location eastus2 \
  --template-file infra/main.bicep \
  --parameters infra/environments/prod/prod.bicepparam \
  --parameters enableCompliance=true enableCMK=true
```

### Step 2: Data Generation (POC Only)

```bash
cd data_generation
python -m generators.financial.transaction_generator \
  --records 1000000 --output landing/financial/
```

### Step 3: Notebook Execution Order

1. `notebooks/bronze/51_financial_transactions.py`
2. `notebooks/silver/51_financial_enriched.py`
3. `notebooks/gold/51_financial_fraud_scoring.py`

### Step 4: Power BI

1. Create semantic model over Gold tables using Direct Lake
2. Import dashboard templates from `poc-agenda/dashboards/`
3. Configure row-level security for compliance roles

---

## References

- [31 CFR 1020 - BSA Rules for Banks](https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1020)
- [12 CFR 21 - OCC Suspicious Activity Reports](https://www.ecfr.gov/current/title-12/chapter-I/part-21)
- [PCI DSS v4.0](https://www.pcisecuritystandards.org/document_library/)
- [12 CFR 217 - Basel III Capital Rules](https://www.ecfr.gov/current/title-12/chapter-II/subchapter-A/part-217)
- [15 USC 7262 - SOX Section 404](https://www.law.cornell.edu/uscode/text/15/7262)
- [15 USC 6801 - GLBA Privacy](https://www.law.cornell.edu/uscode/text/15/6801)
- [12 CFR 252 - DFAST/CCAR](https://www.ecfr.gov/current/title-12/chapter-II/subchapter-A/part-252)
- [FinCEN BSA/AML Manual](https://www.fincen.gov/resources/statutes-and-regulations)
- [Nilson Report - Card Fraud Statistics](https://nilsonreport.com/)
- [Microsoft Fabric Documentation](https://learn.microsoft.com/en-us/fabric/)

---

*Last Updated: 2026-04-27*
*Phase: 14 - Wave 6 (Commercial Verticals)*
*Industry: Financial Services - Commercial Banking*
