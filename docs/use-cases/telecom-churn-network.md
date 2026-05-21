---
hero: assets/heroes/telecommunications.svg
hero_alt: Telecom churn + network quality analytics
type: feature
---
# Telecom Churn Prediction & Network Quality Analytics

## Use Case Overview

| Attribute | Detail |
|-----------|--------|
| **Industry** | Telecommunications (Regional Wireless Carrier) |
| **Scale** | 3.5M subscribers, 8,000 cell sites, MVNO + postpaid + prepaid |
| **Fabric SKU** | F64 (P1 equivalent) |
| **Estimated Cost** | ~$20,000/month |
| **Primary Compliance** | CPNI (47 CFR 64.2001-2009), GDPR (EU roaming subscribers) |
| **ROI** | 1% churn reduction = ~$12M ARR retained |

---

## Business Context

Regional wireless carriers face relentless competitive pressure from national operators
and MVNOs. Subscriber churn averages 1.5-2.5% monthly, making retention the single
largest lever for revenue protection. Meanwhile, 5G rollout demands precise capacity
planning to maximise capital efficiency.

This use case deploys Microsoft Fabric to unify call detail records (CDRs), network
performance telemetry, subscriber profiles, and billing data into a single analytics
platform. Five interconnected workstreams deliver measurable business value:

1. **Churn Prediction** -- propensity scoring and retention offer optimisation
2. **Network Quality Analytics** -- dropped calls, throughput, latency by cell/sector
3. **Revenue Assurance** -- rating accuracy, unbilled usage, fraud detection
4. **Customer Experience Management** -- NPS drivers, journey analytics
5. **5G Capacity Planning** -- traffic forecasting, small cell placement

---

## Architecture

### High-Level Data Flow

```
+-------------------+     +------------------+     +--------------------+
| CDR / xDR Feeds   |---->| Eventstream      |---->| Eventhouse (KQL)   |
| (voice, data, SMS)|     | (real-time ingest)|     | (real-time network |
+-------------------+     +------------------+     |  KPIs, 15-min agg) |
                                                    +--------------------+
+-------------------+     +------------------+            |
| Subscriber CRM    |---->| Lakehouse Bronze |<-----------+
| (batch daily)     |     |                  |
+-------------------+     +--------+---------+
                                   |
+-------------------+     +--------v---------+
| Network Mgmt      |---->| Lakehouse Silver |
| (PM counters,     |     | (enriched CDRs,  |
|  alarms, config)  |     |  validated subs)  |
+-------------------+     +--------+---------+
                                   |
                          +--------v---------+
                          | Lakehouse Gold   |
                          | - gold_churn_scores
                          | - gold_network_kpis
                          | - gold_revenue_assurance
                          | - gold_cust_experience
                          | - gold_capacity_plan
                          +------------------+
```

### Medallion Tables

| Layer | Table | Description |
|-------|-------|-------------|
| Bronze | `bronze_telecom_cdr` | Raw CDR/xDR records (voice, data, SMS) |
| Bronze | `bronze_telecom_subscribers` | Raw subscriber profiles from CRM |
| Bronze | `bronze_telecom_cell_sites` | Cell site configuration and coordinates |
| Bronze | `bronze_telecom_network_pm` | Performance management counters (15-min) |
| Bronze | `bronze_telecom_alarms` | Network alarms and fault events |
| Silver | `silver_telecom_usage` | Enriched CDRs joined with subscriber + cell site |
| Silver | `silver_telecom_subscriber_360` | Cleansed subscriber with usage aggregates |
| Silver | `silver_telecom_network_quality` | Validated PM counters with derived metrics |
| Gold | `gold_telecom_churn` | Churn propensity scores and feature vectors |
| Gold | `gold_network_kpis` | Network KPIs by cell, sector, hour |
| Gold | `gold_revenue_assurance` | Rating discrepancies and unbilled usage |
| Gold | `gold_cust_experience` | NPS driver analysis and journey scores |
| Gold | `gold_capacity_plan` | 5G traffic forecasts and cell placement recs |

---

## Workstream 1: Churn Prediction

### Problem Statement

Monthly churn of 2.1% costs the carrier ~$100M annually in lost revenue and subscriber
acquisition costs ($350-450 per gross add). Proactive retention campaigns targeting
high-propensity churners can reduce churn by 15-25% when paired with optimised offers.

### Feature Engineering

Features are computed in the Gold layer from Silver aggregates:

| Feature | Source | Window |
|---------|--------|--------|
| `usage_trend_30d` | CDR daily aggregates | 30-day slope of data usage |
| `voice_minutes_trend` | CDR voice records | 30-day slope of voice minutes |
| `complaint_count_90d` | CRM interactions | Count of complaints in 90 days |
| `tenure_months` | Subscriber profile | Months since activation |
| `contract_remaining_days` | Subscriber profile | Days until contract end |
| `plan_changes_6m` | CRM transactions | Plan changes in 6 months |
| `payment_late_count` | Billing system | Late payments in 12 months |
| `avg_data_usage_gb` | CDR data records | 30-day average daily data |
| `roaming_sessions` | CDR records | International roaming count |
| `dropped_call_rate` | Network PM | Personal dropped call ratio |
| `avg_download_speed` | Network PM | Mean DL throughput experienced |
| `customer_lifetime_value` | Billing | Total revenue to date |
| `device_age_months` | CRM | Months since last device upgrade |
| `overage_charges` | Billing | Out-of-plan usage charges |

### Propensity Scoring

The churn model uses a gradient-boosted tree (LightGBM) trained on 12 months of
historical churn labels. The model outputs a probability score (0.0 - 1.0) per
subscriber, refreshed daily.

**Scoring tiers:**
- **High risk (>0.7):** Immediate retention intervention -- dedicated agent call
- **Medium risk (0.4-0.7):** Targeted offer via SMS/app push (e.g., 20% discount, data bonus)
- **Low risk (<0.4):** Standard engagement programmes

### Retention Offer Optimisation

A contextual bandit model selects the optimal retention offer from a portfolio:

| Offer ID | Description | Cost | Historical Save Rate |
|----------|-------------|------|---------------------|
| RET-01 | 20% discount for 3 months | $15/mo | 38% |
| RET-02 | Free device upgrade (mid-tier) | $200 one-time | 52% |
| RET-03 | Data plan upgrade (free 6 mo) | $10/mo | 41% |
| RET-04 | Loyalty points bonus | $25 equivalent | 22% |
| RET-05 | Free streaming bundle (12 mo) | $8/mo | 35% |

### KQL Real-Time Churn Signals

```kql
// Detect subscribers with sudden usage drop (potential pre-churn signal)
CDR_Stream
| where EventTime > ago(7d)
| summarize DailyDataGB = sum(BytesDown + BytesUp) / 1073741824.0 by SubscriberId, bin(EventTime, 1d)
| summarize AvgRecent = avg(DailyDataGB) by SubscriberId
| join kind=inner (
    CDR_Stream
    | where EventTime between(ago(37d) .. ago(7d))
    | summarize DailyDataGB = sum(BytesDown + BytesUp) / 1073741824.0 by SubscriberId, bin(EventTime, 1d)
    | summarize AvgBaseline = avg(DailyDataGB) by SubscriberId
) on SubscriberId
| where AvgRecent < AvgBaseline * 0.5
| project SubscriberId, AvgBaseline, AvgRecent, DropPct = round((1 - AvgRecent/AvgBaseline) * 100, 1)
| order by DropPct desc
```

---

## Workstream 2: Network Quality Analytics

### Key Performance Indicators

| KPI | Formula | Target |
|-----|---------|--------|
| Dropped Call Rate (DCR) | Dropped calls / Total call attempts | < 1.5% |
| Call Setup Success Rate (CSSR) | Successful setups / Total attempts | > 98.5% |
| Average Throughput (DL) | Total DL bytes / Total DL time | > 25 Mbps (4G), > 100 Mbps (5G) |
| Latency (RTT) | Average round-trip time | < 30ms (4G), < 10ms (5G) |
| RRC Setup Success Rate | Successful RRC / Total RRC attempts | > 99.0% |
| Handover Success Rate | Successful HOs / Total HO attempts | > 97.0% |
| Cell Availability | Uptime / (Uptime + Downtime) | > 99.5% |
| PRB Utilisation | Used PRBs / Total PRBs | Alert > 80% |

### Cell Site Performance Analysis

Network PM counters arrive every 15 minutes from the RAN. The Silver layer aggregates
these into hourly and daily metrics per cell/sector, while the Eventhouse provides
sub-minute visibility for NOC operations.

```kql
// Top 20 worst-performing cells by dropped call rate (last 24h)
NetworkPM
| where Timestamp > ago(24h)
| summarize
    TotalAttempts = sum(CallAttempts),
    DroppedCalls = sum(DroppedCalls),
    AvgDLThroughputMbps = avg(DLThroughputMbps),
    AvgULThroughputMbps = avg(ULThroughputMbps)
    by CellId, Sector
| extend DCR = round(DroppedCalls * 100.0 / TotalAttempts, 2)
| where TotalAttempts > 100
| top 20 by DCR desc
| project CellId, Sector, DCR, TotalAttempts, DroppedCalls, AvgDLThroughputMbps
```

### Sector-Level Heat Maps

Gold-layer aggregates feed Power BI Direct Lake reports with geospatial heat maps.
NOC analysts can drill from regional view down to individual cell-sector performance,
overlaid with subscriber density and terrain data.

---

## Workstream 3: Revenue Assurance

### Rating Accuracy

CDRs are re-rated in the Silver layer against the subscriber's plan terms. Discrepancies
between the switch-rated amount and the re-rated amount flag potential revenue leakage:

| Check | Description | Threshold |
|-------|-------------|-----------|
| Duration mismatch | CDR duration vs billing duration | > 5 seconds |
| Data volume mismatch | CDR bytes vs rated bytes | > 1% variance |
| Zero-rated anomalies | Free usage not matching plan rules | Any unexpected |
| Cross-network rating | Interconnect charges vs contract rates | > $0.001/min |
| Roaming re-rating | Visited network charges vs retail rate | > 5% variance |

### Unbilled Usage Detection

```sql
-- Identify CDRs with no matching billing record (potential revenue leakage)
SELECT
    c.cdr_id,
    c.subscriber_id,
    c.call_type,
    c.duration_sec,
    c.start_dt,
    c.rated_amount
FROM silver_telecom_usage c
LEFT JOIN billing_rated_events b
    ON c.cdr_id = b.cdr_id
WHERE b.cdr_id IS NULL
    AND c.start_dt >= DATEADD(day, -7, GETDATE())
    AND c.duration_sec > 0
ORDER BY c.rated_amount DESC
```

### Fraud Detection Patterns

| Pattern | Indicator | Action |
|---------|-----------|--------|
| SIM box fraud | High call volume from single IMEI, many IMSIs | Block IMEI, investigate |
| Subscription fraud | New subscriber, immediate high international usage | Real-time block |
| Wangiri fraud | Short-duration calls to premium-rate numbers | Pattern alerting |
| IRSF | International revenue share fraud, call forwarding chains | Interconnect monitoring |
| PBX hacking | Abnormal after-hours call volumes from business accounts | Usage cap alerting |

---

## Workstream 4: Customer Experience Management

### NPS Driver Analysis

Net Promoter Score surveys are correlated with operational data to identify causal
drivers of satisfaction and detraction:

| Driver | Data Source | Impact on NPS |
|--------|-----------|---------------|
| Network quality at home | CDR + cell site mapping | High (r=0.68) |
| Billing accuracy | Revenue assurance output | Medium (r=0.45) |
| Store/contact centre wait time | CRM interactions | Medium (r=0.41) |
| Data speed consistency | PM counter variability | High (r=0.62) |
| Plan value perception | Competitive benchmarking | Medium (r=0.39) |
| Device performance | Device diagnostics | Low (r=0.28) |

### Journey Analytics

Customer journey stages are tracked through interaction events:

1. **Awareness** -- Marketing campaign exposure and response
2. **Acquisition** -- Store visit, online signup, activation
3. **Onboarding** -- First 30 days usage patterns, setup calls
4. **Usage** -- Steady-state consumption, plan utilisation
5. **Service** -- Support interactions, complaints, escalations
6. **Renewal** -- Contract renewal decision, upgrade, churn

Each stage has associated health metrics that feed the churn model.

---

## Workstream 5: 5G Capacity Planning

### Traffic Forecasting

Time-series forecasting (Prophet/ARIMA) on per-cell traffic volumes predicts when
cells will reach capacity thresholds. The model accounts for:

- Seasonal patterns (time of day, day of week, holidays)
- Growth trends (subscriber additions, data usage growth)
- Event-driven spikes (concerts, sports, emergencies)
- Technology migration (4G to 5G traffic shift)

### Small Cell Placement Optimisation

Gold-layer analysis combines:

- Traffic density maps (from CDR geolocation)
- Coverage gap analysis (from drive test data)
- Building footprints and zoning data
- Fibre availability for backhaul
- Revenue density (ARPU by location)

Output is a prioritised list of candidate small cell locations with projected ROI.

### Capacity KPIs

| Metric | Formula | Planning Trigger |
|--------|---------|-----------------|
| PRB utilisation | Used PRBs / Available PRBs | > 70% sustained |
| User throughput ratio | Achieved / Advertised speed | < 50% at busy hour |
| Connection density | Active users / Cell capacity | > 80% of design limit |
| Traffic growth rate | Month-over-month volume change | > 15% monthly |
| Spectral efficiency | Throughput / Bandwidth | Below technology floor |

---

## CPNI Compliance

### Regulatory Framework

Customer Proprietary Network Information (CPNI) is protected under 47 CFR 64.2001-2009
(FCC regulations). Carriers must safeguard subscriber data including:

- Call detail records (numbers called, call duration, time of day)
- Service configuration (plan type, features subscribed)
- Usage data (data consumption, roaming patterns)

### Fabric Implementation

| Requirement | Implementation |
|-------------|---------------|
| **Access control** | Workspace-level RBAC; CPNI tables restricted to authorised roles |
| **Opt-in/opt-out** | `subscriber.cpni_consent` flag enforced in Silver queries |
| **Audit logging** | SQL audit logs enabled on all lakehouses; retained 5 years |
| **Data minimisation** | PII columns (phone number, IMSI) hashed in Silver; raw only in Bronze with restricted access |
| **Breach notification** | Eventhouse alert on bulk CPNI access patterns |
| **Third-party sharing** | CPNI fields excluded from data sharing endpoints; GraphQL resolvers enforce consent check |
| **Annual certification** | Automated compliance report from audit logs |

### Row-Level Security for CPNI

```sql
-- RLS policy: restrict CDR access to subscriber's own account or authorised roles
CREATE FUNCTION dbo.fn_cpni_filter(@subscriber_id VARCHAR(50))
RETURNS TABLE
WITH SCHEMABINDING
AS
RETURN
    SELECT 1 AS result
    WHERE
        IS_MEMBER('CPNIAuthorisedAnalysts') = 1
        OR @subscriber_id = SESSION_CONTEXT(N'subscriber_id')
```

### GDPR Considerations (EU Roaming)

For subscribers roaming on EU partner networks, additional GDPR requirements apply:

| Requirement | Implementation |
|-------------|---------------|
| Right to erasure | Soft-delete with 30-day purge pipeline |
| Data portability | Export API in JSON/CSV via Data Agent |
| Consent management | Granular consent flags per processing purpose |
| Data residency | EU roaming CDRs processed in EU Fabric capacity |
| DPO notification | Automated alert on cross-border data movement |

---

## Cost Analysis

### Fabric Consumption Breakdown

| Component | CU Estimate | Monthly Cost |
|-----------|-------------|-------------|
| Eventstream (CDR ingest ~50K events/sec) | 8 CU | $3,200 |
| Eventhouse (real-time KQL queries) | 6 CU | $2,400 |
| Lakehouse (medallion processing) | 16 CU | $6,400 |
| Spark notebooks (ML training, daily) | 8 CU | $3,200 |
| Power BI Direct Lake (50 concurrent users) | 4 CU | $1,600 |
| OneLake storage (5 TB compressed Delta) | -- | $1,200 |
| Purview governance | 2 CU | $800 |
| **Total** | **44 CU** | **~$18,800** |

### ROI Model

| Metric | Value |
|--------|-------|
| Total subscribers | 3,500,000 |
| ARPU (average) | $58/month |
| Annual revenue | $2.44B |
| Current monthly churn | 2.1% |
| Post-analytics churn | 1.8% (conservative) |
| Churn reduction | 0.3% (absolute) |
| Retained subscribers/month | 10,500 |
| Annual retained revenue | ~$12.0M |
| Fabric annual cost | ~$226K |
| **Net ROI** | **~53x** |

Additional value from network quality improvements (reduced truck rolls, optimised
CapEx), revenue assurance (plugging leakage), and improved NPS (reduced acquisition
cost) is not included in this conservative estimate.

---

## Power BI Reports

### Dashboard Suite

1. **Churn Command Centre** -- Real-time churn risk heatmap, retention campaign tracker,
   offer conversion rates, subscriber-level drill-through
2. **Network Operations** -- Cell site health map, DCR/CSSR trends, PRB utilisation
   gauges, alarm correlation timeline
3. **Revenue Assurance** -- Rating discrepancy waterfall, unbilled usage tracker,
   fraud alert queue with investigation workflow
4. **Customer Experience** -- NPS trend by segment, journey stage health, complaint
   resolution SLA tracking
5. **Capacity Planning** -- Traffic forecast charts, cell congestion predictions,
   CapEx planning scenarios

All reports use Direct Lake mode for sub-second query performance on the Gold layer.

---

## References

| Source | URL |
|--------|-----|
| FCC CPNI Rules (47 CFR 64) | https://www.ecfr.gov/current/title-47/chapter-I/subchapter-B/part-64/subpart-U |
| 3GPP TS 32.298 (CDR format) | https://www.3gpp.org/specifications/32-series |
| TM Forum Revenue Assurance (GB941) | https://www.tmforum.org/resources/standard/gb941-revenue-assurance-guidebook/ |
| Microsoft Fabric Eventstream | https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/overview |
| Microsoft Fabric Eventhouse | https://learn.microsoft.com/fabric/real-time-intelligence/eventhouse |
| GSMA 5G Implementation Guidelines | https://www.gsma.com/futurenetworks/technology/5g/ |
| Ofcom Quality of Service (UK ref) | https://www.ofcom.org.uk/research-and-data/telecoms-research |
