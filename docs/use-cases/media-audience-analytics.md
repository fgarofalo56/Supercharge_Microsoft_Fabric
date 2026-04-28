# Media & Entertainment: Audience Analytics on Microsoft Fabric

## Executive Summary

| Attribute | Detail |
|-----------|--------|
| **Vertical** | Media & Entertainment (Streaming) |
| **Platform Scale** | 8M subscribers, 50K content titles, 2B playback events/day |
| **Fabric SKU** | F64 (P1 equivalent) |
| **Monthly Cost** | ~$25,000 |
| **Primary ROI** | Churn reduction ($4.2M/yr) + Ad revenue optimization ($1.8M/yr) |
| **Compliance** | COPPA, GDPR, CCPA |
| **Key Workloads** | Eventstream, Eventhouse, Lakehouse, Power BI Direct Lake |

---

## Business Context

A streaming media platform operates a hybrid monetization model with three tiers:

- **Free (AVOD):** Ad-supported, limited catalog access, 2.1M users
- **Basic:** Ad-free, standard quality, 3.4M subscribers at $9.99/mo
- **Premium:** 4K HDR, offline downloads, family profiles, 2.5M subscribers at $15.99/mo

The platform generates approximately 2 billion playback events daily across web, mobile, smart TV, and gaming console clients. Content spans original productions, licensed movies, live sports, and a growing kids library subject to COPPA regulations.

### Key Business Questions

1. Which content titles drive the highest engagement and lowest churn?
2. How do we optimize ad placement in AVOD without degrading watch time?
3. What is the true cost-per-viewing-hour for licensed vs. original content?
4. Which subscriber segments are at risk of churning in the next 30 days?
5. How do viewing patterns differ across age-gated (COPPA) profiles?

---

## Architecture Overview

```
                    Playback Clients (Web/Mobile/TV/Console)
                                    |
                            Event Collector API
                                    |
                        Azure Event Hubs (32 partitions)
                                    |
                    +---------Fabric Eventstream---------+
                    |                                     |
            Eventhouse (KQL DB)                    Lakehouse (Delta)
            Real-time engagement                   Medallion pipeline
            dashboards, alerts                     Bronze -> Silver -> Gold
                    |                                     |
                    +----------Power BI Direct Lake-------+
                                    |
                    Audience Dashboards & Recommendation API
```

### Data Flow

1. **Ingest:** Playback clients emit events (play, pause, seek, stop, heartbeat) via Event Collector API to Azure Event Hubs.
2. **Real-Time Path:** Fabric Eventstream routes events to Eventhouse for sub-second KQL queries powering live engagement dashboards and anomaly detection (e.g., buffering spike alerts).
3. **Batch Path:** Eventstream also lands raw events in the Bronze lakehouse layer as Delta tables partitioned by date.
4. **Silver Layer:** Events are sessionized (30-minute gap = new session), quality-scored, and bot traffic is filtered.
5. **Gold Layer:** Aggregated content performance, user engagement segments, and content affinity matrices feed Power BI and the recommendation engine.

---

## Medallion Architecture

### Bronze: Raw Playback Events

**Table:** `bronze_media_events`

| Column | Type | Description |
|--------|------|-------------|
| event_id | STRING | Unique event identifier (UUID) |
| user_id | STRING | Pseudonymized user identifier |
| content_id | STRING | Content title identifier |
| event_type | STRING | play, pause, seek, stop, heartbeat |
| event_timestamp | TIMESTAMP | Client-side event time (UTC) |
| position_sec | INT | Playback position in seconds |
| device_type | STRING | web, mobile, smart_tv, console |
| bitrate_kbps | INT | Current streaming bitrate |
| plan_tier | STRING | free, basic, premium |
| age_bucket | STRING | child, teen, adult (COPPA routing) |
| region | STRING | ISO 3166-1 region code |
| _ingested_at | TIMESTAMP | Bronze ingestion timestamp |
| _source | STRING | Generator/pipeline identifier |
| _batch_id | STRING | Batch identifier |

**Volume:** ~2B events/day, ~60B events/month
**Partitioning:** `_bronze_load_date`
**Retention:** 90 days raw, then archive to cold storage

### Silver: Sessionized Viewing

**Table:** `silver_media_sessions`

| Column | Type | Description |
|--------|------|-------------|
| session_id | STRING | Derived session identifier |
| user_id | STRING | Pseudonymized user identifier |
| content_id | STRING | Content title identifier |
| session_start | TIMESTAMP | First event in session |
| session_end | TIMESTAMP | Last event in session |
| watch_duration_sec | INT | Total active viewing time |
| content_duration_sec | INT | Total content duration |
| completion_pct | DOUBLE | watch_duration / content_duration |
| pause_count | INT | Number of pause events |
| seek_count | INT | Number of seek events |
| avg_bitrate_kbps | INT | Average streaming quality |
| quality_score | DOUBLE | Composite QoE metric (0-1) |
| device_type | STRING | Primary device for session |
| plan_tier | STRING | User plan at time of viewing |
| is_binge | BOOLEAN | Part of 3+ consecutive episodes |
| age_bucket | STRING | COPPA age classification |

**Transformations:**
- Sessionization: events grouped by user_id + content_id with 30-minute inactivity gap
- Bot filtering: sessions < 5 seconds or > 24 hours excluded
- Heartbeat deduplication: collapse consecutive heartbeats within 15-second window
- Quality score: weighted combination of bitrate stability, rebuffer ratio, startup time

### Gold: Content Performance

**Table:** `gold_content_performance`

| Column | Type | Description |
|--------|------|-------------|
| content_id | STRING | Content identifier |
| title | STRING | Content title |
| genre | STRING | Primary genre |
| period | DATE | Aggregation period (daily) |
| unique_viewers | BIGINT | Distinct viewers |
| total_watch_hours | DOUBLE | Sum of watch duration |
| avg_completion_pct | DOUBLE | Average completion rate |
| trending_score | DOUBLE | Weighted recency + velocity |
| cost_per_view_hour | DOUBLE | License cost / watch hours |
| is_original | BOOLEAN | Platform original content |

### Gold: User Engagement Segments

**Table:** `gold_user_segments`

| Column | Type | Description |
|--------|------|-------------|
| user_id | STRING | Pseudonymized user identifier |
| segment | STRING | power, casual, at_risk, dormant |
| watch_hours_30d | DOUBLE | Last 30 days viewing |
| sessions_30d | INT | Session count last 30 days |
| genres_watched | INT | Genre diversity |
| avg_completion | DOUBLE | Average completion rate |
| days_since_last | INT | Days since last session |
| churn_probability | DOUBLE | ML-predicted churn risk |
| plan_tier | STRING | Current subscription tier |
| cohort_month | DATE | Signup cohort |

**Segment Definitions:**
- **Power:** 20+ hours/month, 15+ sessions, completion > 70%
- **Casual:** 5-20 hours/month, 5-15 sessions
- **At-Risk:** < 5 hours/month declining, or 14+ days inactive
- **Dormant:** 30+ days since last session

---

## Analytics Use Cases

### 1. Audience Engagement Analytics

**Objective:** Understand viewing behavior to optimize content scheduling and personalization.

**Key Metrics:**
- **Watch Time per Session:** Average and P95 session duration by content genre
- **Completion Rate:** Percentage of content watched to completion (critical for series)
- **Binge Score:** Consecutive episodes watched in a single sitting (3+ = binge)
- **Time-to-First-Play:** Latency from app open to first playback event

**KQL Real-Time Query (Eventhouse):**

```kql
PlaybackEvents
| where EventTimestamp > ago(1h)
| summarize
    ActiveViewers = dcount(UserId),
    AvgBitrateKbps = avg(BitrateKbps),
    BufferingEvents = countif(EventType == "buffering")
  by bin(EventTimestamp, 1m), ContentId
| order by ActiveViewers desc
| take 20
```

**Business Impact:** Content teams use engagement data to greenlight Season 2 renewals. Titles with > 75% completion rate and > 40% binge score receive priority renewal consideration.

### 2. Content Recommendation Engine

**Objective:** Improve content discovery using collaborative filtering enhanced with content-based features.

**Approach:**
- **Collaborative Filtering:** User-content interaction matrix factorized via ALS (Alternating Least Squares) in PySpark MLlib
- **Content-Based Features:** Genre, cast, director, release year, content rating, duration
- **Hybrid Score:** 0.7 * collaborative + 0.3 * content-based, with COPPA-safe filtering for child profiles

**Content Affinity Matrix:**

```python
# Gold layer: user-genre affinity for recommendation input
affinity = sessions_df.groupBy("user_id", "genre") \
    .agg(
        F.sum("watch_duration_sec").alias("total_watch_sec"),
        F.avg("completion_pct").alias("avg_completion"),
        F.count("session_id").alias("session_count")
    ) \
    .withColumn("affinity_score",
        F.col("total_watch_sec") * 0.4 +
        F.col("avg_completion") * 100 * 0.4 +
        F.col("session_count") * 0.2
    )
```

**COPPA Constraint:** Child profiles (age_bucket = "child") only receive recommendations from the kids catalog. No cross-profile recommendation leakage.

### 3. Ad Monetization Optimization (AVOD Tier)

**Objective:** Maximize ad revenue for free-tier users without degrading engagement.

**Key Metrics:**
- **Impression Yield:** Ad impressions per content hour viewed
- **Fill Rate:** Percentage of ad slots filled by demand partners
- **CPM (Cost per Mille):** Revenue per 1,000 ad impressions
- **Ad-Induced Drop-Off:** Percentage of users who stop viewing during/after an ad break

**Optimization Strategy:**
- Dynamic ad load: reduce ad frequency for users showing engagement decline
- Contextual targeting: match ad categories to content genre (no behavioral tracking for COPPA profiles)
- A/B test ad pod lengths: 15s vs 30s vs 60s pre-roll impact on completion rates

**Gold Metrics:**

| Metric | Target | Current |
|--------|--------|---------|
| Impression Yield | 12/hr | 10.3/hr |
| Fill Rate | 95% | 91% |
| Average CPM | $18.00 | $15.40 |
| Ad Drop-Off Rate | < 8% | 11.2% |

### 4. Content Acquisition ROI

**Objective:** Evaluate whether licensed content justifies its acquisition cost.

**Key Metrics:**
- **Cost per Viewing Hour (CPVH):** Total license cost / total viewing hours
- **Catalog Utilization:** Percentage of catalog titles viewed at least once in 30 days
- **Marginal Viewer Contribution:** Incremental subscribers attributed to a title

**Benchmarks:**

| Content Type | Avg CPVH | Catalog Utilization |
|-------------|----------|---------------------|
| Originals | $0.42 | 89% |
| Licensed Movies | $0.78 | 62% |
| Licensed Series | $0.55 | 71% |
| Live Sports | $1.20 | 95% |

### 5. Subscriber Lifecycle Management

**Objective:** Reduce churn through proactive engagement interventions.

**Lifecycle Stages:**
1. **Trial (Day 1-7):** Onboarding optimization, content sampling breadth
2. **Activation (Day 8-30):** Habit formation, push notification cadence tuning
3. **Engagement (Month 2-12):** Content personalization, feature adoption
4. **Decay (Declining usage):** Win-back campaigns, plan downgrade offers
5. **Churn (Cancellation):** Exit survey analysis, re-acquisition targeting

**Churn Prediction Features:**
- Watch hours trend (7d, 14d, 30d rolling)
- Session frequency decline rate
- Genre diversity contraction
- Device usage pattern changes
- Payment failure history
- Support ticket sentiment

**Intervention Triggers:**

| Signal | Action | Expected Lift |
|--------|--------|---------------|
| 50% watch time decline over 14d | Personalized email with curated picks | +12% retention |
| No session in 10 days | Push notification with new release | +8% reactivation |
| Payment failure | Proactive support outreach | +22% save rate |
| Trial day 3, < 2 sessions | In-app content spotlight | +15% trial conversion |

---

## Compliance Framework

### COPPA (Children's Online Privacy Protection Act)

The platform serves a kids content library requiring COPPA compliance for users under 13.

**Requirements Implemented:**

1. **Age-Gated Profiles:** Each account designates child profiles during setup. Child profiles are tagged with `age_bucket = "child"` at the event level.

2. **Parental Consent:** Verifiable parental consent (VPC) is obtained before creating child profiles. Consent records are stored separately with audit trail.

3. **Data Minimization:** Child profile events collect only:
   - Content interaction (play/pause/stop) -- no seek granularity
   - Device type (category only, no device fingerprint)
   - No geolocation, no behavioral advertising identifiers

4. **No Behavioral Advertising:** AVOD ads shown to child profiles use contextual targeting only (genre-based). No user-level tracking or cross-session profiling.

5. **Data Retention:** Child profile event data is retained for a maximum of 30 days (vs. 90 days for adult profiles).

6. **Parental Access:** Parents can request full export or deletion of child profile data via self-service portal.

**Implementation in Medallion:**

```
Bronze: age_bucket field populated from profile metadata
Silver: COPPA filter applied -- child sessions excluded from behavioral models
Gold:   Child engagement metrics aggregated at content level only (no user-level)
        Recommendations use content-based filtering only (no collaborative)
```

### GDPR (General Data Protection Regulation)

**Requirements Implemented:**

1. **Consent Management:** Users provide granular consent for:
   - Essential (playback functionality) -- always required
   - Analytics (engagement measurement) -- opt-in
   - Personalization (recommendations) -- opt-in
   - Advertising (behavioral ads for AVOD) -- opt-in

2. **Right to Erasure (Article 17):** Deletion request triggers:
   - Immediate: Remove user from active recommendation models
   - 24 hours: Purge user_id from Silver/Gold aggregations
   - 72 hours: Delete all Bronze event records matching user_id
   - Confirmation: Erasure completion notification to user

3. **Data Portability (Article 20):** Users can export their viewing history, preferences, and profile data in machine-readable JSON format.

4. **Purpose Limitation:** Event data collected for playback functionality is not repurposed for advertising without explicit consent upgrade.

5. **Pseudonymization:** All user identifiers in the lakehouse are pseudonymized. The mapping table (user_id <-> PII) is stored in a separate, access-controlled system outside Fabric.

**GDPR Erasure Pipeline:**

```python
# Triggered by erasure request via API
def process_erasure(user_id: str):
    """Delete user data across all medallion layers."""
    # 1. Gold: Remove from segments and affinity tables
    spark.sql(f"DELETE FROM gold_user_segments WHERE user_id = '{user_id}'")

    # 2. Silver: Remove sessionized data
    spark.sql(f"DELETE FROM silver_media_sessions WHERE user_id = '{user_id}'")

    # 3. Bronze: Remove raw events (partitioned scan)
    spark.sql(f"DELETE FROM bronze_media_events WHERE user_id = '{user_id}'")

    # 4. Eventhouse: KQL purge
    # .purge table PlaybackEvents records where UserId == user_id

    # 5. Audit log
    log_erasure_completion(user_id, datetime.utcnow())
```

---

## Cost Model

### Monthly Fabric Consumption (~$25,000/month on F64)

| Workload | CU Allocation | Monthly Cost | Notes |
|----------|---------------|--------------|-------|
| Eventstream | 25% | $6,250 | 2B events/day ingestion |
| Eventhouse (KQL) | 20% | $5,000 | Real-time dashboards, 7-day hot cache |
| Lakehouse (Spark) | 30% | $7,500 | Medallion ETL, daily batch |
| Power BI Direct Lake | 15% | $3,750 | 50+ dashboards, 200 users |
| OneLake Storage | 10% | $2,500 | ~15 TB Delta + archive |

### ROI Analysis

| Revenue Driver | Annual Impact |
|----------------|---------------|
| Churn reduction (1.5pp improvement) | $4,200,000 |
| Ad revenue optimization (+18% CPM) | $1,800,000 |
| Content acquisition savings (CPVH) | $900,000 |
| Trial conversion improvement (+3pp) | $600,000 |
| **Total Annual Benefit** | **$7,500,000** |
| **Annual Fabric Cost** | **$300,000** |
| **ROI** | **25:1** |

---

## Real-Time Intelligence

### Eventhouse KQL Queries

**Live Concurrent Viewers:**

```kql
PlaybackEvents
| where EventTimestamp > ago(5m)
| where EventType in ("play", "heartbeat")
| summarize ConcurrentViewers = dcount(UserId) by bin(EventTimestamp, 1m)
| render timechart
```

**Content Trending Detection:**

```kql
PlaybackEvents
| where EventTimestamp > ago(1h)
| summarize Viewers = dcount(UserId) by ContentId
| join kind=inner (
    PlaybackEvents
    | where EventTimestamp between (ago(2h) .. ago(1h))
    | summarize PrevViewers = dcount(UserId) by ContentId
) on ContentId
| extend TrendPct = round((Viewers - PrevViewers) * 100.0 / PrevViewers, 1)
| where TrendPct > 50
| order by TrendPct desc
```

**Quality of Experience Alert:**

```kql
PlaybackEvents
| where EventTimestamp > ago(10m)
| where EventType == "buffering"
| summarize BufferEvents = count(), AffectedUsers = dcount(UserId) by Region
| where BufferEvents > 1000
| order by BufferEvents desc
```

---

## Power BI Dashboards

### Dashboard 1: Content Command Center

**Purpose:** Real-time content performance for programming executives.

**Visuals:**
- Live concurrent viewer count (card with sparkline)
- Top 20 trending titles (bar chart, hourly refresh)
- Completion rate heatmap by genre x day-of-week
- New release first-48-hour trajectory vs. benchmark

### Dashboard 2: Subscriber Health

**Purpose:** Lifecycle management for growth and retention teams.

**Visuals:**
- Subscriber funnel: Trial -> Active -> At-Risk -> Churned
- Cohort retention curves (month-over-month)
- Engagement segment distribution (power/casual/at-risk/dormant)
- Churn prediction risk scores with intervention recommendations

### Dashboard 3: Ad Revenue Operations

**Purpose:** AVOD monetization for ad sales and ad ops teams.

**Visuals:**
- Impression yield and fill rate trends
- CPM by genre and daypart
- Ad-induced drop-off by ad pod length
- Revenue forecast vs. actual (daily)

---

## Implementation Checklist

- [ ] Deploy Eventstream with Event Hub source (32 partitions)
- [ ] Configure Eventhouse KQL database with 7-day retention
- [ ] Create Bronze notebook: `58_media_events.py`
- [ ] Create Silver notebook: `58_media_sessions.py`
- [ ] Create Gold notebook: `58_media_recommendations.py`
- [ ] Configure COPPA age-gate filtering in Silver pipeline
- [ ] Implement GDPR erasure pipeline with audit logging
- [ ] Build Power BI Direct Lake semantic model
- [ ] Deploy Content Command Center dashboard
- [ ] Deploy Subscriber Health dashboard
- [ ] Deploy Ad Revenue Operations dashboard
- [ ] Set up KQL alerting for QoE degradation
- [ ] Configure OneLake data retention policies (30d child, 90d adult)
- [ ] Validate COPPA data minimization in child profile events
- [ ] Load test: 2B events/day sustained throughput

---

## References

- [Microsoft Fabric Eventstream Documentation](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/event-streams/overview)
- [Eventhouse KQL Best Practices](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/eventhouse)
- [COPPA Rule (16 CFR Part 312)](https://www.ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa)
- [GDPR Article 17 - Right to Erasure](https://gdpr-info.eu/art-17-gdpr/)
- [Direct Lake Mode in Power BI](https://learn.microsoft.com/en-us/power-bi/enterprise/directlake-overview)
- [Delta Lake Deletion Vectors](https://docs.delta.io/latest/delta-deletion-vectors.html)
