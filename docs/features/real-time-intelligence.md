---
hero: assets/heroes/features.svg
hero_alt: Fabric feature — Real-Time Intelligence (RTI) Comprehensive Guide
type: feature
---
# ⚡ Real-Time Intelligence (RTI) Comprehensive Guide


<div align="center" markdown>

**Streaming Analytics at Scale with Microsoft Fabric**

![Category](https://img.shields.io/badge/Category-Real_Time_Analytics-orange?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-April_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-04-13` | **Version:** 2.0.0

---

## 🎯 Overview

Real-Time Intelligence (RTI) in Microsoft Fabric provides a complete streaming analytics platform that enables organizations to ingest, process, analyze, and act on data in motion. RTI brings together four key components -- Eventstreams, Eventhouse, Real-Time Dashboards, and Data Activator -- into a unified experience within the Fabric workspace.

### Why RTI Matters

| Challenge | RTI Solution |
|-----------|-------------|
| Delayed insights from batch processing | Sub-second ingestion with continuous processing |
| Multiple disconnected streaming tools | Unified platform within Fabric workspace |
| Complex stream processing code | No-code/low-code transformations in Eventstreams |
| Static dashboards refreshed hourly | Auto-refreshing dashboards with live KQL queries |
| Manual alert configuration | Data Activator triggers actions automatically |
| Hot/warm/cold data management | Integrated caching policies in Eventhouse |

### RTI in the Fabric Ecosystem

```mermaid
flowchart TB
    subgraph Sources["📡 Event Sources"]
        EH["Azure Event Hub"]
        KF["Apache Kafka"]
        CA["Custom App"]
        IoT["Azure IoT Hub"]
        CDC["CDC Streams"]
    end

    subgraph RTI["⚡ Real-Time Intelligence"]
        ES["📥 Eventstreams<br/>Ingestion & Transform"]
        EVH["🏠 Eventhouse<br/>KQL Database"]
        RTD["📊 Real-Time Dashboards<br/>Live Visualization"]
        DA["🔔 Data Activator<br/>Automated Actions"]
    end

    subgraph Fabric["🔷 Fabric Workloads"]
        LH["🏠 Lakehouse<br/>Delta Tables"]
        WH["🏢 Warehouse"]
        PBI["📊 Power BI"]
        NB["📓 Notebooks"]
    end

    Sources --> ES
    ES --> EVH
    ES --> LH
    EVH --> RTD
    EVH --> DA
    EVH --> PBI
    EVH --> NB
    LH --> WH
    LH --> PBI

    style RTI fill:#E67E22,stroke:#CA6F1E,color:#fff
    style Sources fill:#2E86C1,stroke:#1A5276,color:#fff
    style Fabric fill:#6C3483,stroke:#4A235A,color:#fff
```

---

## 🏗️ RTI Components

### Component Overview

| Component | Purpose | Key Capabilities |
|-----------|---------|-----------------|
| **Eventstreams** | Event ingestion and in-flight transformation | Source connectors, no-code transforms, multi-destination routing |
| **Eventhouse** | High-performance analytical store (KQL DB) | Time-series optimization, hot cache, materialized views, update policies |
| **Real-Time Dashboards** | Live visualization of streaming data | Auto-refresh tiles, KQL-driven visuals, parameters, drill-through |
| **Data Activator** | Automated actions triggered by data conditions | Threshold alerts, pattern detection, Power Automate integration |

### Component Interaction

```mermaid
sequenceDiagram
    participant S as Event Source
    participant ES as Eventstream
    participant EH as Eventhouse (KQL DB)
    participant MV as Materialized View
    participant RTD as Real-Time Dashboard
    participant DA as Data Activator
    participant PA as Power Automate

    S->>ES: Stream events
    ES->>ES: Filter, transform, enrich
    ES->>EH: Ingest to table
    EH->>MV: Update policy triggers
    MV->>RTD: Query for visualization
    MV->>DA: Monitor for conditions
    DA->>PA: Trigger action
    PA->>PA: Send email/Teams/webhook

    Note over ES,EH: Sub-second latency
    Note over MV,RTD: Auto-refresh (30s default)
```

---

## 📐 Architecture Patterns

### Pattern 1: Hot Path Only (Eventhouse)

Best for operational monitoring where only recent data matters. All events flow through Eventstream directly to Eventhouse for real-time querying.

```mermaid
flowchart LR
    subgraph Sources["📡 Sources"]
        S1["Slot Telemetry"]
        S2["Player Card Swipes"]
        S3["Compliance Alerts"]
    end

    subgraph Processing["⚡ Processing"]
        ES["Eventstream"]
        EH["Eventhouse<br/>KQL Database"]
    end

    subgraph Output["📊 Output"]
        RTD["Real-Time Dashboard"]
        DA["Data Activator<br/>Alerts"]
    end

    Sources --> ES --> EH --> Output

    style Processing fill:#E67E22,stroke:#CA6F1E,color:#fff
```

**When to Use:**
- Casino floor monitoring (last 24-72 hours)
- Live weather observation feeds
- Real-time AQI monitoring
- Flight delay tracking

**Retention Configuration:**
```kql
// Set hot cache to 3 days, total retention to 30 days
.alter table SlotTelemetry policy caching
    hot = 3d

.alter table SlotTelemetry policy retention
    softdelete = 30d
    recoverability = enabled
```

### Pattern 2: Warm Path (Lakehouse Delta)

Best for batch analytics where streaming data needs to be combined with historical data in the medallion architecture.

```mermaid
flowchart LR
    subgraph Sources["📡 Sources"]
        S1["NOAA Observations"]
        S2["EPA Sensor Data"]
        S3["DOI Seismic Data"]
    end

    subgraph Processing["⚡ Processing"]
        ES["Eventstream"]
        LH["Lakehouse<br/>Bronze Delta Tables"]
    end

    subgraph Medallion["🥇 Medallion"]
        SV["Silver<br/>Cleansed"]
        GD["Gold<br/>Aggregated"]
        PBI["Power BI<br/>Direct Lake"]
    end

    Sources --> ES --> LH --> SV --> GD --> PBI

    style Processing fill:#2E86C1,stroke:#1A5276,color:#fff
    style Medallion fill:#27AE60,stroke:#1E8449,color:#fff
```

**When to Use:**
- Historical trend analysis on streaming data
- Data that feeds into medallion architecture
- Batch ML model training on recent events
- Compliance reporting (requires full history)

### Pattern 3: Lambda (Hot + Warm Hybrid)

The recommended pattern for most production workloads. Eventstream splits events to both Eventhouse (hot) and Lakehouse (warm), providing real-time dashboards alongside historical batch analytics.

```mermaid
flowchart TB
    subgraph Sources["📡 Event Sources"]
        S1["Slot Machine<br/>Telemetry"]
        S2["Player Card<br/>Events"]
        S3["Compliance<br/>Triggers"]
    end

    subgraph Ingestion["📥 Eventstream"]
        ES["Eventstream<br/>Filter + Enrich"]
    end

    subgraph HotPath["🔴 Hot Path (Real-Time)"]
        EH["Eventhouse"]
        RTD["Real-Time<br/>Dashboard"]
        DA["Data Activator<br/>Alerts"]
    end

    subgraph WarmPath["🔵 Warm Path (Batch)"]
        LH["Lakehouse<br/>Bronze"]
        SV["Silver<br/>Cleansed"]
        GD["Gold<br/>Aggregated"]
        PBI["Power BI<br/>Direct Lake"]
    end

    Sources --> ES
    ES -->|"Real-time copy"| EH
    ES -->|"Batch landing"| LH
    EH --> RTD
    EH --> DA
    LH --> SV --> GD --> PBI

    style HotPath fill:#E74C3C,stroke:#C0392B,color:#fff
    style WarmPath fill:#2E86C1,stroke:#1A5276,color:#fff
    style Ingestion fill:#E67E22,stroke:#CA6F1E,color:#fff
```

**When to Use:**
- Casino floor operations (real-time alerts + historical reporting)
- NOAA storm tracking (live radar + climate trend analysis)
- EPA monitoring (real-time AQI + compliance reporting)
- DOT/FAA (live flight tracking + delay pattern analysis)

> 💡 **Tip**: The Lambda pattern is the default recommendation for this project. It provides the best balance of real-time responsiveness and historical depth.

### Pattern 4: Kappa (Stream-Only)

All processing happens on the stream. Suitable when there is no need for a separate batch layer and all analytics can be derived from the event stream.

```mermaid
flowchart LR
    S["📡 Source"] --> ES["Eventstream<br/>Transform"]
    ES --> EH["Eventhouse"]
    EH --> MV["Materialized<br/>Views"]
    MV --> RTD["Real-Time<br/>Dashboard"]
    MV --> DA["Activator"]

    style ES fill:#E67E22,stroke:#CA6F1E,color:#fff
```

**When to Use:**
- IoT sensor monitoring where only recent data matters
- Real-time anomaly detection without historical context
- Simple event counting and aggregation

---

## 📥 Eventstream Setup

### Source Connectors

| Source Type | Connector | Auth Method | Use Case |
|------------|-----------|-------------|----------|
| **Azure Event Hub** | Native | Connection string / Managed Identity | Primary for Azure-native sources |
| **Apache Kafka** | Kafka protocol | SASL/SSL | Third-party streaming platforms |
| **Custom App** | REST API / SDK | API key / OAuth | Application-level event producers |
| **Azure IoT Hub** | Native | Device connection string | IoT device telemetry |
| **Sample Data** | Built-in | None | Development and testing |
| **Azure Blob Storage** | Native | Account key / MI | File-based event replay |
| **CDC (Fabric Mirroring)** | Database CDC | Connection config | Change data capture from databases |

### Creating an Eventstream

#### Step 1: Create the Eventstream Item

```
Workspace → + New → Eventstream
  Name: es-slot-telemetry
  Description: Real-time slot machine telemetry events from casino floor
```

#### Step 2: Add a Source

For Azure Event Hub source:

```json
{
    "source_type": "AzureEventHub",
    "connection": {
        "event_hub_namespace": "eh-casino-telemetry",
        "event_hub_name": "slot-events",
        "consumer_group": "$Default",
        "authentication": "managed_identity"
    },
    "serialization": {
        "type": "JSON",
        "encoding": "UTF-8"
    }
}
```

For a Custom App source (used by data generators):

```python
# Python data generator sending to Eventstream custom app endpoint
from azure.eventhub import EventHubProducerClient, EventData
import json

connection_str = "Endpoint=sb://es-slot-telemetry.servicebus.windows.net/..."
producer = EventHubProducerClient.from_connection_string(connection_str)

event = EventData(json.dumps({
    "machine_id": "SL-4421",
    "event_type": "spin",
    "denomination": 0.25,
    "wager": 2.50,
    "payout": 0.00,
    "timestamp": "2026-03-12T14:30:00Z",
    "floor_location": "Floor 2, Section A3"
}))

batch = producer.create_batch()
batch.add(event)
producer.send_batch(batch)
```

### Eventstream Transformations

Eventstreams support no-code in-flight transformations:

| Transform | Description | Example |
|-----------|-------------|---------|
| **Filter** | Remove events that don't match criteria | Filter out "heartbeat" events, keep only "spin" and "error" |
| **Manage Fields** | Select, rename, or remove fields | Remove raw_payload, rename ts to timestamp |
| **Aggregate** | Windowed aggregations (tumbling, hopping, session) | Count spins per machine per 5-minute window |
| **Group By** | Group events by key columns | Group by machine_id and floor_location |
| **Union** | Combine multiple streams | Merge slot and table game events |
| **Expand** | Flatten nested JSON arrays | Expand multi-line transaction details |
| **Join** | Join two streams on a key | Enrich telemetry with machine master data |

#### Tumbling Window Aggregation Example

```
Eventstream Canvas:
  [Source: Event Hub]
    → [Filter: event_type IN ('spin', 'jackpot', 'error')]
    → [Aggregate: Tumbling Window 5min]
        GroupBy: machine_id, floor_location
        Aggregations:
          - COUNT(*) AS event_count
          - SUM(wager) AS total_wager
          - SUM(payout) AS total_payout
          - COUNT(CASE WHEN event_type='error' THEN 1 END) AS error_count
    → [Destination: Eventhouse table "SlotTelemetry5min"]
    → [Destination: Lakehouse table "bronze_slot_telemetry"]
```

### Multi-Destination Routing

A single Eventstream can route events to multiple destinations simultaneously:

```mermaid
flowchart TB
    SRC["📡 Event Hub<br/>slot-events"]

    subgraph ES["📥 Eventstream"]
        F1["Filter:<br/>event_type = 'spin'"]
        F2["Filter:<br/>event_type = 'error'"]
        F3["Filter:<br/>event_type = 'jackpot'"]
        AGG["Aggregate:<br/>5min tumbling"]
    end

    SRC --> ES

    F1 --> AGG
    AGG -->|"Hot path"| EH1["Eventhouse:<br/>SlotTelemetry5min"]
    F2 -->|"Alert path"| DA["Data Activator:<br/>Error Alerts"]
    F3 -->|"Compliance"| EH2["Eventhouse:<br/>JackpotEvents"]
    F1 -->|"Warm path"| LH["Lakehouse:<br/>bronze_slot_telemetry"]

    style ES fill:#E67E22,stroke:#CA6F1E,color:#fff
```

---

## 🏠 Eventhouse Configuration

### Database Creation

An Eventhouse contains one or more KQL databases. Each database is an independent container for tables, functions, materialized views, and policies.

```
Workspace → + New → Eventhouse
  Name: evh-casino-operations
  Description: Real-time analytics for casino floor operations

  Databases:
  ├── db-slot-telemetry      (Slot machine events and aggregations)
  ├── db-compliance-alerts    (CTR, SAR, W-2G real-time monitoring)
  └── db-player-tracking      (Player card swipe and session events)
```

### Table Schemas and Ingestion Mappings

#### Table Creation

```kql
// Create the raw telemetry ingestion table
.create table SlotTelemetryRaw (
    MachineId: string,
    EventType: string,
    Denomination: real,
    Wager: real,
    Payout: real,
    Timestamp: datetime,
    FloorLocation: string,
    GameTitle: string,
    SessionId: string,
    ErrorCode: string,
    RawPayload: dynamic
)

// Create the 5-minute aggregation table
.create table SlotTelemetry5min (
    MachineId: string,
    FloorLocation: string,
    WindowStart: datetime,
    WindowEnd: datetime,
    SpinCount: long,
    TotalWager: real,
    TotalPayout: real,
    HoldAmount: real,
    HoldPct: real,
    ErrorCount: long,
    JackpotCount: long
)
```

#### Ingestion Mapping

```kql
// JSON ingestion mapping for Event Hub data
.create table SlotTelemetryRaw ingestion json mapping 'SlotTelemetryMapping'
    '[{"column":"MachineId","path":"$.machine_id","datatype":"string"},'
    '{"column":"EventType","path":"$.event_type","datatype":"string"},'
    '{"column":"Denomination","path":"$.denomination","datatype":"real"},'
    '{"column":"Wager","path":"$.wager","datatype":"real"},'
    '{"column":"Payout","path":"$.payout","datatype":"real"},'
    '{"column":"Timestamp","path":"$.timestamp","datatype":"datetime"},'
    '{"column":"FloorLocation","path":"$.floor_location","datatype":"string"},'
    '{"column":"GameTitle","path":"$.game_title","datatype":"string"},'
    '{"column":"SessionId","path":"$.session_id","datatype":"string"},'
    '{"column":"ErrorCode","path":"$.error_code","datatype":"string"},'
    '{"column":"RawPayload","path":"$","datatype":"dynamic"}]'
```

### Retention and Caching Policies

Eventhouse uses a two-tier storage model:

| Tier | Storage | Performance | Cost |
|------|---------|-------------|------|
| **Hot Cache** | SSD (in-memory) | Sub-second query response | Higher CU consumption |
| **Cold Storage** | OneLake (Azure Blob) | Seconds to minutes query response | Lower cost, included in capacity |

```kql
// Configure hot cache: keep last 7 days in fast storage
.alter table SlotTelemetryRaw policy caching
    hot = 7d

// Configure total retention: keep 90 days, allow recovery
.alter table SlotTelemetryRaw policy retention
    softdelete = 90d
    recoverability = enabled

// For compliance tables, keep longer
.alter table ComplianceAlerts policy caching
    hot = 30d

.alter table ComplianceAlerts policy retention
    softdelete = 7y
    recoverability = enabled
```

> ⚠️ **Warning**: Compliance data (CTR, SAR, W-2G) must be retained per regulatory requirements. NIGC MICS requires 5-year minimum retention for gaming records. Configure retention policies accordingly.

### Materialized Views

Materialized views pre-compute aggregations for faster dashboard queries:

```kql
// Hourly slot performance materialized view
.create materialized-view with (backfill=true)
    SlotPerformanceHourly on table SlotTelemetryRaw
{
    SlotTelemetryRaw
    | where EventType == "spin"
    | summarize
        SpinCount = count(),
        TotalWager = sum(Wager),
        TotalPayout = sum(Payout),
        HoldAmount = sum(Wager) - sum(Payout),
        AvgWager = avg(Wager)
        by MachineId, FloorLocation, bin(Timestamp, 1h)
}

// Daily compliance summary materialized view
.create materialized-view with (backfill=true)
    ComplianceDailySummary on table ComplianceAlerts
{
    ComplianceAlerts
    | summarize
        CTRCount = countif(AlertType == "CTR"),
        SARCount = countif(AlertType == "SAR"),
        W2GCount = countif(AlertType == "W2G"),
        TotalAlerts = count()
        by bin(Timestamp, 1d)
}
```

### Update Policies

Update policies automatically transform data as it arrives, creating derived tables from raw ingestion:

```kql
// Create derived table for error analysis
.create table SlotErrors (
    MachineId: string,
    ErrorCode: string,
    ErrorTimestamp: datetime,
    FloorLocation: string,
    GameTitle: string,
    TimeSinceLastError: timespan
)

// Update policy: extract errors from raw telemetry on ingestion
.alter table SlotErrors policy update
@'[{"IsEnabled": true, "Source": "SlotTelemetryRaw", "Query": "SlotTelemetryRaw | where EventType == \"error\" | project MachineId, ErrorCode, ErrorTimestamp=Timestamp, FloorLocation, GameTitle, TimeSinceLastError=timespan(null)", "IsTransactional": true}]'
```

---

## 🔍 KQL Query Patterns

### Time-Series Analysis

```kql
// Slot revenue time-series with 1-hour bins over the last 7 days
SlotTelemetryRaw
| where Timestamp > ago(7d) and EventType == "spin"
| summarize
    Revenue = sum(Wager) - sum(Payout),
    SpinCount = count()
    by bin(Timestamp, 1h)
| render timechart
    with (title="Hourly Slot Revenue", xtitle="Time", ytitle="Revenue ($)")
```

```kql
// Seasonal decomposition of daily revenue
let daily_revenue = SlotTelemetryRaw
| where EventType == "spin"
| summarize Revenue = sum(Wager) - sum(Payout) by bin(Timestamp, 1d)
| project Timestamp, Revenue;
daily_revenue
| make-series Revenue = sum(Revenue) on Timestamp step 1d
| extend (anomalies, score, baseline) = series_decompose_anomalies(Revenue)
| render anomalychart
    with (title="Revenue Anomaly Detection", anomalycolumns=anomalies)
```

### Anomaly Detection

```kql
// Detect anomalous error rates per machine using series_decompose_anomalies()
let error_rates = SlotTelemetryRaw
| where Timestamp > ago(7d)
| summarize
    TotalEvents = count(),
    Errors = countif(EventType == "error")
    by MachineId, bin(Timestamp, 1h)
| extend ErrorRate = round(todouble(Errors) / TotalEvents * 100, 2);
error_rates
| make-series ErrorRate = avg(ErrorRate) on Timestamp step 1h by MachineId
| extend (anomalies, score, baseline) = series_decompose_anomalies(ErrorRate, 1.5)
| mv-expand Timestamp to typeof(datetime),
            ErrorRate to typeof(double),
            anomalies to typeof(int),
            score to typeof(double),
            baseline to typeof(double)
| where anomalies != 0
| project MachineId, Timestamp, ErrorRate, anomalies, score
| order by score desc
```

### Geospatial Queries

```kql
// Find all earthquake events within 100km of a given point (DOI use case)
let center_lat = 47.6062;  // Seattle
let center_lon = -122.3321;
let radius_km = 100;
EarthquakeEvents
| where Timestamp > ago(30d)
| where geo_distance_point_to_point(Longitude, Latitude, center_lon, center_lat) < radius_km * 1000
| project EventId, Magnitude, Depth, Latitude, Longitude,
          Distance_km = round(geo_distance_point_to_point(Longitude, Latitude, center_lon, center_lat) / 1000, 1),
          Timestamp
| order by Magnitude desc
```

```kql
// Check if facilities are within EPA monitoring zones using geo_point_in_polygon()
let monitoring_zone = dynamic({
    "type": "Polygon",
    "coordinates": [[[-122.5, 47.4], [-122.5, 47.8], [-122.1, 47.8], [-122.1, 47.4], [-122.5, 47.4]]]
});
EPAFacilities
| where geo_point_in_polygon(Longitude, Latitude, monitoring_zone)
| summarize FacilityCount = count(), TotalReleases = sum(ReleaseAmount) by ChemicalName
| order by TotalReleases desc
```

### Pattern Matching with Scan Operator

```kql
// Detect structuring patterns: multiple transactions just below CTR threshold
// Pattern: 3+ transactions of $8,000-$9,999 from same player within 24 hours
PlayerTransactions
| where Timestamp > ago(24h)
| where Amount between (8000.0 .. 9999.99)
| order by PlayerId asc, Timestamp asc
| partition by PlayerId
    (
        scan with_match_id = mid
            declare (step1: bool = false, step2: bool = false, step3: bool = false)
            with
            (
                step step1: true;
                step step2: step1 == true and Timestamp - step1.Timestamp < 24h;
                step step3: step2 == true and Timestamp - step1.Timestamp < 24h;
            )
        | where step3 == true
    )
| summarize
    TransactionCount = count(),
    TotalAmount = sum(Amount),
    TimeSpan = max(Timestamp) - min(Timestamp)
    by PlayerId, mid
| where TransactionCount >= 3
| order by TotalAmount desc
```

### Advanced Aggregation Patterns

```kql
// Moving average of slot performance (7-day window)
SlotPerformanceHourly
| where Timestamp > ago(30d)
| summarize DailyRevenue = sum(HoldAmount) by bin(Timestamp, 1d)
| order by Timestamp asc
| extend MovingAvg7d = series_fir(pack_array(DailyRevenue), repeat(1, 7), true, false)
| project Timestamp, DailyRevenue, MovingAvg7d

// Percentile analysis of player session durations
PlayerSessions
| where Timestamp > ago(30d)
| summarize
    p50 = percentile(SessionDuration, 50),
    p75 = percentile(SessionDuration, 75),
    p90 = percentile(SessionDuration, 90),
    p99 = percentile(SessionDuration, 99),
    AvgDuration = avg(SessionDuration)
    by bin(Timestamp, 1d)
| render timechart
```

---

## 📊 Real-Time Dashboards

### Dashboard Architecture

Real-Time Dashboards in Fabric are purpose-built for live KQL-powered visualizations. Unlike Power BI reports that query semantic models, RTI dashboards query Eventhouse (KQL databases) directly.

```mermaid
flowchart TB
    subgraph Dashboard["📊 Real-Time Dashboard"]
        T1["🎰 Floor Overview<br/>Tile: Map"]
        T2["📈 Revenue Trend<br/>Tile: Time Chart"]
        T3["⚠️ Active Alerts<br/>Tile: Table"]
        T4["🎯 KPIs<br/>Tile: Stat Cards"]
        T5["🔄 Error Rate<br/>Tile: Anomaly Chart"]
        P1["🎛️ Parameters<br/>Floor, TimeRange, Denom"]
    end

    subgraph Eventhouse["🏠 Eventhouse"]
        DB1["db-slot-telemetry"]
        MV1["SlotPerformanceHourly"]
        MV2["ComplianceDailySummary"]
    end

    P1 -.->|"Filter"| T1 & T2 & T3 & T4 & T5
    T1 & T2 & T3 & T4 & T5 -->|"KQL Query"| Eventhouse

    style Dashboard fill:#F4D03F,stroke:#D4AC0D,color:#000
    style Eventhouse fill:#E67E22,stroke:#CA6F1E,color:#fff
```

### Tile Types and Configuration

| Tile Type | Best For | Refresh Rate | KQL Output |
|-----------|----------|-------------|------------|
| **Time Chart** | Trends over time | 30s | `render timechart` |
| **Bar Chart** | Comparisons across categories | 30s | `render barchart` |
| **Pie Chart** | Proportions and distributions | 60s | `render piechart` |
| **Stat Card** | Single KPI values | 10s | Single row, single column |
| **Table** | Detailed records | 30s | Tabular output |
| **Map** | Geospatial data | 60s | Requires lat/long columns |
| **Anomaly Chart** | Outlier detection | 60s | `render anomalychart` |
| **Multi-Stat** | Multiple KPIs in one tile | 30s | Single row, multiple columns |

### Auto-Refresh Settings

```
Dashboard Settings → Auto Refresh
  ├── Minimum refresh interval: 10 seconds
  ├── Default refresh interval: 30 seconds
  ├── Maximum data age: configurable per tile
  └── Pause auto-refresh when tab is inactive: recommended
```

> 💡 **Tip**: Set critical alert tiles (compliance, errors) to 10-second refresh and informational tiles (trends, summaries) to 60-second refresh to balance performance with freshness.

### Parameter-Driven Dashboards

Parameters allow users to filter dashboard data interactively:

```kql
// Define parameter usage in tile query
// Parameter: FloorLocation (dropdown, multi-select)
// Parameter: TimeRange (time range picker)
// Parameter: MinWager (free text, decimal)

SlotPerformanceHourly
| where FloorLocation in ({FloorLocation})
| where Timestamp between ({TimeRange})
| where TotalWager >= {MinWager}
| summarize
    TotalRevenue = sum(HoldAmount),
    AvgHoldPct = avg(HoldAmount / TotalWager) * 100,
    TotalSpins = sum(SpinCount)
    by MachineId, FloorLocation
| order by TotalRevenue desc
```

### Casino Floor Dashboard Layout

> **Dashboard:** 🎰 Casino Floor Operations — Real-Time
> **Parameters:** Floor · Time window · Denomination

**Top-row KPI cards:**

| Revenue | Machines | Active Players | Alerts |
|---|---|---|---|
| **$1.2M** ↑ 4.2% | **1,247** Online | **892** | **3 Active** · ⚠ CTR: 1 |

**Visualizations (in order, top to bottom):**

1. 📈 **Hourly Revenue Trend** — time-series line chart of last 24h with anomaly markers
2. 🗺️ **Floor Heat Map** *(left)* — color-coded by revenue; click a machine for detail
3. ⚠️ **Active Compliance Alerts** *(right)* — CTR · SAR · W-2G table sorted by severity
4. 🔄 **Machine Error Rate** — anomaly chart of last 7 days with detection bands

---

## 🔔 Data Activator

Data Activator (formerly Reflex) monitors streaming data for conditions and automatically triggers actions when thresholds are met.

### Alert Configuration

| Alert Type | Condition | Action |
|-----------|-----------|--------|
| **CTR Threshold** | Transaction amount >= $10,000 | Email compliance team + log to audit table |
| **SAR Pattern** | 3+ transactions $8K-$9.9K from same player in 24h | Alert compliance officer + flag in system |
| **Machine Error Spike** | Error rate > 10% for 15+ minutes | Email floor tech + page on-call engineer |
| **Revenue Anomaly** | Hourly revenue deviates >3 sigma from baseline | Alert floor manager |
| **Jackpot Event** | Payout > $1,200 (W-2G threshold) | Notify cage operations + auto-generate W-2G |

### Setting Up Data Activator

```mermaid
flowchart LR
    subgraph Source["📡 Data Source"]
        EH["Eventhouse Query"]
    end

    subgraph Activator["🔔 Data Activator"]
        MON["Monitor<br/>Condition"]
        ACT["Action<br/>Trigger"]
    end

    subgraph Actions["🎯 Actions"]
        EM["📧 Email Alert"]
        TM["💬 Teams Message"]
        PA["⚡ Power Automate"]
        WH["🔗 Webhook"]
    end

    Source --> MON -->|"Condition Met"| ACT --> Actions

    style Activator fill:#C0392B,stroke:#922B21,color:#fff
```

### Example: CTR Compliance Alert

```json
{
    "activator_name": "CTR Threshold Alert",
    "source": {
        "type": "eventhouse",
        "database": "db-compliance-alerts",
        "query": "PlayerTransactions | where Amount >= 10000 | where Timestamp > ago(5m)"
    },
    "condition": {
        "type": "row_count",
        "operator": "greater_than",
        "value": 0
    },
    "actions": [
        {
            "type": "email",
            "recipients": ["compliance-team@casino.com"],
            "subject": "CTR Alert: Transaction >= $10,000",
            "body": "Player {PlayerId} - Transaction of ${Amount} at {Timestamp}"
        },
        {
            "type": "power_automate",
            "flow_id": "ctr-processing-flow",
            "parameters": {
                "player_id": "{PlayerId}",
                "amount": "{Amount}",
                "timestamp": "{Timestamp}"
            }
        }
    ]
}
```

---

## 🏛️ Domain Use Cases

### 🎰 Casino: Slot Telemetry and Compliance

```mermaid
flowchart TB
    subgraph Casino["🎰 Casino Floor"]
        SM["Slot Machines<br/>SAS Protocol"]
        TG["Table Games<br/>RFID Chips"]
        PC["Player Cards<br/>Loyalty System"]
    end

    subgraph ES["📥 Eventstreams"]
        ES1["es-slot-telemetry"]
        ES2["es-table-games"]
        ES3["es-player-events"]
    end

    subgraph EVH["🏠 evh-casino-operations"]
        DB1["db-slot-telemetry"]
        DB2["db-compliance"]
        DB3["db-player-tracking"]
    end

    subgraph Alerts["🔔 Data Activator"]
        A1["CTR Alert<br/>>= $10,000"]
        A2["SAR Pattern<br/>Structuring"]
        A3["W-2G Trigger<br/>>= $1,200"]
        A4["Error Spike<br/>>10% rate"]
    end

    Casino --> ES --> EVH --> Alerts

    style Casino fill:#6C3483,stroke:#4A235A,color:#fff
    style EVH fill:#E67E22,stroke:#CA6F1E,color:#fff
    style Alerts fill:#C0392B,stroke:#922B21,color:#fff
```

**Key Real-Time Queries:**

```kql
// Live floor utilization by section
SlotTelemetryRaw
| where Timestamp > ago(15m)
| where EventType == "spin"
| summarize ActiveMachines = dcount(MachineId) by FloorLocation
| join kind=leftouter (
    MachineInventory | summarize TotalMachines = count() by FloorLocation
) on FloorLocation
| extend UtilizationPct = round(todouble(ActiveMachines) / TotalMachines * 100, 1)
| order by UtilizationPct desc
```

### 🌀 NOAA: Live Weather and Storm Tracking

```mermaid
flowchart LR
    subgraph Sources["🌀 NOAA Sources"]
        OBS["Weather<br/>Observations"]
        ALR["Storm<br/>Alerts"]
        RAD["Radar<br/>Data"]
    end

    subgraph Processing["⚡ RTI"]
        ES["Eventstream"]
        EH["Eventhouse<br/>db-weather"]
    end

    subgraph Output["📊 Dashboards"]
        WM["Weather<br/>Map"]
        ST["Storm<br/>Tracker"]
        HI["Historical<br/>Comparison"]
    end

    Sources --> Processing --> Output

    style Processing fill:#E67E22,stroke:#CA6F1E,color:#fff
```

**Key Real-Time Queries:**

```kql
// Track active severe weather alerts by state
NOAAAlerts
| where Timestamp > ago(1h) and Status == "Active"
| where Severity in ("Extreme", "Severe")
| summarize AlertCount = count(), AlertTypes = make_set(EventType) by State, Severity
| order by Severity asc, AlertCount desc

// Detect temperature anomalies at observation stations
let station_history = NOAAObservations
| where Timestamp between (ago(365d) .. ago(1d))
| summarize AvgTemp = avg(Temperature), StdTemp = stdev(Temperature) by StationId, bin(Timestamp, 1d);
NOAAObservations
| where Timestamp > ago(1h)
| join kind=inner station_history on StationId
| extend ZScore = (Temperature - AvgTemp) / StdTemp
| where abs(ZScore) > 3
| project StationId, Temperature, AvgTemp, ZScore, Timestamp
```

### 🌊 EPA: Real-Time AQI Monitoring

**Key Real-Time Queries:**

```kql
// Real-time Air Quality Index across monitoring stations
EPASensorData
| where Timestamp > ago(1h)
| where Pollutant == "PM2.5"
| summarize AvgConcentration = avg(Concentration) by StationId, City, State
| extend AQI_Category = case(
    AvgConcentration <= 12, "Good",
    AvgConcentration <= 35.4, "Moderate",
    AvgConcentration <= 55.4, "Unhealthy for Sensitive Groups",
    AvgConcentration <= 150.4, "Unhealthy",
    AvgConcentration <= 250.4, "Very Unhealthy",
    "Hazardous")
| extend AQI_Color = case(
    AQI_Category == "Good", "Green",
    AQI_Category == "Moderate", "Yellow",
    AQI_Category == "Unhealthy for Sensitive Groups", "Orange",
    AQI_Category == "Unhealthy", "Red",
    AQI_Category == "Very Unhealthy", "Purple",
    "Maroon")
| order by AvgConcentration desc
```

### 🏔️ DOI: Earthquake Event Streaming

**Key Real-Time Queries:**

```kql
// Real-time earthquake monitoring with cascading event detection
EarthquakeEvents
| where Timestamp > ago(24h)
| order by Timestamp desc
| extend
    TimeSincePrevious = prev(Timestamp) - Timestamp,
    DistanceFromPrevious = geo_distance_point_to_point(
        Longitude, Latitude,
        prev(Longitude), prev(Latitude)) / 1000
| where Magnitude >= 3.0
| project Timestamp, Magnitude, Depth, Latitude, Longitude,
          Region, TimeSincePrevious, DistanceFromPrevious
```

### ✈️ DOT/FAA: Flight Delay Tracking

**Key Real-Time Queries:**

```kql
// Real-time flight delay status by airport
FlightEvents
| where Timestamp > ago(2h)
| where EventType == "departure" or EventType == "arrival"
| extend DelayMinutes = datetime_diff('minute', ActualTime, ScheduledTime)
| summarize
    TotalFlights = count(),
    DelayedFlights = countif(DelayMinutes > 15),
    AvgDelay = avg(DelayMinutes),
    MaxDelay = max(DelayMinutes)
    by Airport, EventType
| extend OnTimePct = round(todouble(TotalFlights - DelayedFlights) / TotalFlights * 100, 1)
| order by AvgDelay desc
```

---

## ⚡ Performance Tuning

### Ingestion Throughput

| Factor | Recommendation | Impact |
|--------|---------------|--------|
| **Batch Size** | 1,000-10,000 events per batch | Larger batches = higher throughput, more latency |
| **Batch Interval** | 10-30 seconds for near-real-time | Shorter interval = lower latency, more overhead |
| **Compression** | Enable gzip for Event Hub payloads | 60-80% reduction in network traffic |
| **Partitioning** | Partition by high-cardinality key (machine_id) | Enables parallel ingestion |
| **Ingestion Mapping** | Pre-define JSON mappings | Eliminates runtime schema inference |

### Query Optimization

| Technique | Description | Example |
|-----------|-------------|---------|
| **Filter Early** | Push time and category filters to the top of query | `where Timestamp > ago(1h)` first |
| **Use Materialized Views** | Pre-aggregate common patterns | `SlotPerformanceHourly` instead of raw table |
| **Limit Columns** | Project only needed columns | `project MachineId, Revenue` not `*` |
| **Avoid Cross-Joins** | Use lookup instead of join for small tables | `lookup MachineInfo on MachineId` |
| **Partition Hints** | Use shuffle hint for large aggregations | `summarize hint.shufflekey=MachineId` |
| **Stored Functions** | Encapsulate complex logic in functions | `.create function GetFloorRevenue(...)` |

### Cache Sizing Guidelines

| Workload | Hot Cache Size | Rationale |
|----------|---------------|-----------|
| Casino Floor Monitoring | 3-7 days | Operational dashboards focus on current week |
| Compliance Alerts | 30 days | Regulatory review typically covers last 30 days |
| NOAA Observations | 7-14 days | Weather trends and storm tracking |
| EPA Sensor Data | 7 days | AQI monitoring focuses on recent trends |
| DOI Earthquake Events | 30 days | Aftershock monitoring requires extended window |
| DOT/FAA Flight Data | 3 days | Delay analysis focuses on recent patterns |

```kql
// Monitor cache utilization
.show database db-slot-telemetry extents
| summarize
    HotExtents = countif(MaxCreatedOn > ago(7d)),
    ColdExtents = countif(MaxCreatedOn <= ago(7d)),
    HotSizeGB = sumif(OriginalSize, MaxCreatedOn > ago(7d)) / 1GB,
    ColdSizeGB = sumif(OriginalSize, MaxCreatedOn <= ago(7d)) / 1GB
```

---

## 💰 Cost Management

### Understanding RTI Cost Drivers

| Cost Driver | Description | Optimization |
|------------|-------------|-------------|
| **Ingestion CU** | Compute for parsing and storing events | Batch events, use efficient serialization |
| **Query CU** | Compute for executing KQL queries | Optimize queries, use materialized views |
| **Cache Storage** | Hot SSD storage for fast queries | Right-size cache duration per table |
| **Dashboard Refresh** | Each tile refresh consumes query CU | Increase refresh interval for non-critical tiles |
| **Data Activator** | Monitoring queries run continuously | Simplify conditions, extend check intervals |

### Cost Optimization Strategies

```mermaid
flowchart TB
    subgraph Strategies["💰 Cost Optimization"]
        S1["📦 Batch Ingestion<br/>Group events before send"]
        S2["🔍 Materialized Views<br/>Pre-compute aggregations"]
        S3["⏰ Cache Tuning<br/>Right-size hot periods"]
        S4["🔄 Dashboard Intervals<br/>30-60s vs 10s"]
        S5["📊 Query Optimization<br/>Filter early, project few"]
        S6["🗑️ Retention Policies<br/>Auto-purge old data"]
    end

    S1 --> |"30-50% less CU"| CU["Reduced CU Usage"]
    S2 --> |"60-80% faster"| CU
    S3 --> |"20-40% less storage"| CU
    S4 --> |"50-70% less queries"| CU
    S5 --> |"Variable savings"| CU
    S6 --> |"Controlled growth"| CU

    style Strategies fill:#27AE60,stroke:#1E8449,color:#fff
```

### Monitoring CU Consumption

```kql
// Monitor capacity usage for RTI workloads
.show capacity usage
| where StartTime > ago(7d)
| summarize
    IngestionCU = sumif(CU, WorkloadType == "Ingestion"),
    QueryCU = sumif(CU, WorkloadType == "Query"),
    MaterializedViewCU = sumif(CU, WorkloadType == "MaterializedView")
    by bin(StartTime, 1h)
| render timechart
    with (title="RTI CU Consumption by Workload Type")
```

### Cost Estimation by Domain

| Domain | Events/Day | Hot Cache | Est. Monthly CU |
|--------|-----------|-----------|-----------------|
| Casino Slot Telemetry | 5M | 7 days | 15-20% of F64 |
| Casino Compliance | 50K | 30 days | 2-5% of F64 |
| NOAA Observations | 2M | 14 days | 8-12% of F64 |
| EPA Sensor Data | 500K | 7 days | 3-5% of F64 |
| DOI Earthquake Events | 100K | 30 days | 1-2% of F64 |
| DOT/FAA Flight Data | 1M | 3 days | 5-8% of F64 |

> 📝 **Note**: Percentages are approximate for an F64 capacity. Actual consumption depends on query complexity, dashboard refresh rates, and data volumes. Monitor with the capacity metrics app.

---

## 📡 Business Events

Business Events (Preview, 2026) introduce a new paradigm for event-driven architectures in RTI. Unlike traditional Eventstream sources that originate from external systems, Business Events are generated from within Fabric itself -- from notebooks, User Data Functions, or pipeline activities.

### How Business Events Work

```mermaid
flowchart LR
    subgraph Generators["📝 Event Generators"]
        NB["Fabric Notebook"]
        UDF["User Data Function"]
        PA["Pipeline Activity"]
    end

    subgraph Hub["📡 Real-Time Hub"]
        BE["Business Events"]
    end

    subgraph Consumers["🎯 Consumers"]
        ACT["Data Activator"]
        ES["Eventstream"]
        PBI["Power BI Dashboard"]
        PWA["Power Automate"]
    end

    Generators -->|"Publish"| Hub -->|"Subscribe"| Consumers

    style Hub fill:#E67E22,stroke:#CA6F1E,color:#fff
    style Generators fill:#6C3483,stroke:#4A235A,color:#fff
```

### Business Event Use Cases

| Domain | Event | Trigger | Action |
|--------|-------|---------|--------|
| **Casino** | Revenue threshold crossed | Gold notebook aggregation | Alert floor manager via Teams |
| **Casino** | Compliance filing generated | CTR/SAR pipeline completion | Notify compliance officer |
| **USDA** | Crop yield anomaly detected | ML model prediction | Trigger investigation workflow |
| **NOAA** | Severe weather threshold | Weather data processing | Activate emergency protocol |
| **EPA** | Violation score exceeded | Water quality analysis | Generate enforcement alert |

### Publishing Business Events from Notebooks

```python
# Publish a business event from a Fabric notebook
from notebookutils import mssparkutils

event_payload = {
    "eventType": "ComplianceAlert",
    "source": "gold_compliance_pipeline",
    "data": {
        "player_id": "P-12345",
        "alert_type": "SAR_PATTERN",
        "total_amount": 28500.00,
        "transaction_count": 3,
        "time_window_hours": 4
    }
}

mssparkutils.notification.publishBusinessEvent(
    event_name="casino-compliance-alert",
    payload=event_payload
)
```

> 📝 **Note**: Business Events integrate with the Real-Time Hub, making them discoverable and subscribable by any authorized consumer in the Fabric tenant.

---

## 🔮 Anomaly Detection

Anomaly Detection (Preview) provides a no-code interface for detecting outliers and unusual patterns in streaming data. Previously, anomaly detection required writing KQL queries using `series_decompose_anomalies()` -- the new feature automates model selection and configuration.

### No-Code Anomaly Detection Setup

| Step | Action | Details |
|------|--------|---------|
| 1 | Select data source | Choose Eventhouse table or materialized view |
| 2 | Configure metric | Select numeric column to monitor (e.g., revenue, error_rate) |
| 3 | Set granularity | Time bucket for analysis (1 min, 5 min, 1 hour) |
| 4 | Choose sensitivity | Low (fewer alerts), Medium, High (more alerts) |
| 5 | Configure alerts | Email, Teams, Power Automate, or Data Activator trigger |

### Anomaly Detection for Casino Operations

```
Monitor: Slot machine revenue per hour
Metric: sum(HoldAmount) per FloorLocation
Granularity: 1 hour
Sensitivity: Medium
Alert: Teams notification to floor manager when anomaly detected

Monitor: Player transaction patterns
Metric: count() per PlayerId where Amount > 5000
Granularity: 15 minutes
Sensitivity: High
Alert: Email compliance team + Data Activator trigger
```

### Anomaly Detection for Federal Agencies

| Agency | Metric | Granularity | Sensitivity | Alert Action |
|--------|--------|-------------|-------------|-------------|
| NOAA | Temperature deviation from historical average | 1 hour | Medium | Dashboard highlight |
| EPA | PM2.5 concentration spike | 30 min | High | Email regional office |
| DOI | Earthquake event frequency | 1 hour | Low | Map overlay |
| DOT/FAA | Flight delay rate deviation | 15 min | Medium | Operations dashboard |

> 💡 **Tip**: Use no-code anomaly detection for straightforward metrics. For complex multi-variate analysis (e.g., CTR structuring patterns), continue using the KQL `series_decompose_anomalies()` and `scan` operator approaches documented in the KQL Query Patterns section above.

---

## 🗺️ Fabric Maps

Fabric Maps (GA, March 2026) provides native geospatial visualization directly within Real-Time Intelligence. This replaces the need for custom mapping solutions or external GIS tools for many scenarios.

### Capabilities

| Feature | Description |
|---------|-------------|
| **Real-Time Location Tracking** | Visualize live entity positions (vehicles, assets, people) |
| **Historical Path Analysis** | Replay movement patterns over time |
| **Geofencing Visualization** | Display defined geographic boundaries with event triggers |
| **Heat Maps** | Density visualization for concentration analysis |
| **Cluster Rendering** | Automatic grouping of nearby points at zoom levels |
| **KQL-Powered** | Data sourced from Eventhouse via KQL queries |

### Casino Floor Mapping

```kql
// Feed Fabric Maps with real-time slot machine utilization by location
SlotTelemetryRaw
| where Timestamp > ago(15m)
| join kind=inner MachineLocations on MachineId
| summarize
    ActiveSpins = count(),
    Revenue = sum(Wager) - sum(Payout)
    by MachineId, Latitude, Longitude, ZoneName
| extend MarkerSize = case(
    Revenue > 1000, "large",
    Revenue > 500, "medium",
    "small")
```

### Federal Agency Map Use Cases

| Agency | Map Application | Data Source | Update Frequency |
|--------|----------------|-------------|-----------------|
| **NOAA** | Live weather station network | NOAAObservations table | 5 min |
| **EPA** | AQI monitoring station map | EPASensorData table | 30 min |
| **DOI** | Earthquake event map (last 24h) | EarthquakeEvents table | Real-time |
| **DOT/FAA** | Airport delay status map | FlightEvents table | 15 min |
| **USDA** | Crop condition by county | AgricultureData table | Daily |

> 📝 **Note**: Fabric Maps integrates directly with Data Activator for geofence-triggered alerts (e.g., alert when an asset leaves a defined zone or when AQI exceeds thresholds in a monitored area).

---

## 💻 Eventstream SQL Operator

The Eventstream SQL Operator (GA, March 2026) enables SQL-based stream processing directly within Eventstreams. This is a significant enhancement over the previous no-code transformation approach, providing familiar SQL syntax for complex real-time transformations.

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **SQL Syntax** | Standard SQL for stream transformations |
| **Multiple Destinations** | Route transformed data to multiple outputs from single SQL operator |
| **Event Ordering** | Configurable event ordering policies |
| **Late Event Handling** | Define rules for late-arriving events |
| **Windowing** | Tumbling, hopping, sliding, and session windows |
| **Joins** | Stream-to-stream and stream-to-reference joins |

### SQL Operator Examples

```sql
-- Casino: Real-time revenue aggregation with tumbling window
SELECT
    FloorLocation,
    TUMBLE_START(EventTime, INTERVAL '5' MINUTE) AS WindowStart,
    COUNT(*) AS SpinCount,
    SUM(Wager) AS TotalWager,
    SUM(Payout) AS TotalPayout,
    SUM(Wager) - SUM(Payout) AS NetRevenue,
    AVG(CAST(Wager AS FLOAT)) AS AvgWager
FROM SlotEvents
GROUP BY
    FloorLocation,
    TUMBLE(EventTime, INTERVAL '5' MINUTE)

-- Casino: Detect high-value transactions in real-time
SELECT
    PlayerId,
    TransactionId,
    Amount,
    TransactionType,
    EventTime,
    CASE
        WHEN Amount >= 10000 THEN 'CTR_REQUIRED'
        WHEN Amount BETWEEN 8000 AND 9999.99 THEN 'SAR_REVIEW'
        ELSE 'NORMAL'
    END AS ComplianceFlag
FROM PlayerTransactionStream
WHERE Amount >= 5000

-- Federal: NOAA weather alert aggregation with session window
SELECT
    State,
    SESSION_START(EventTime, INTERVAL '30' MINUTE) AS AlertSessionStart,
    COUNT(*) AS AlertCount,
    MAX(Severity) AS MaxSeverity,
    COLLECT(DISTINCT EventType) AS AlertTypes
FROM NOAAAlertStream
WHERE Severity IN ('Extreme', 'Severe')
GROUP BY
    State,
    SESSION(EventTime, INTERVAL '30' MINUTE)
```

### SQL Operator vs No-Code Transformations

| Criteria | No-Code | SQL Operator |
|----------|---------|-------------|
| **Learning Curve** | Low | Medium (SQL knowledge) |
| **Complexity** | Simple transforms only | Complex joins, windows, aggregations |
| **Multi-destination** | Limited | Full support |
| **Late Events** | Basic | Configurable policies |
| **Use When** | Simple field mapping, filtering | Complex analytics, compliance logic |

> 💡 **Tip**: For this POC, use the SQL Operator for compliance-critical stream processing (CTR detection, SAR pattern aggregation) where precise windowing and ordering matter. Use no-code transforms for simpler routing and field mapping.

---

## 📋 Schema Registry

The Schema Registry (Preview) enables contract-based event schema definition and validation for real-time pipelines. This ensures type-safe, reliable data flow through Eventstreams.

### Schema Registry Concepts

| Concept | Description |
|---------|-------------|
| **Schema Set** | Collection of related schemas (e.g., all casino event types) |
| **Schema Version** | Versioned schema definition with compatibility rules |
| **Compatibility Mode** | Forward, backward, or full compatibility enforcement |
| **Validation** | Automatic validation of incoming events against registered schemas |

### Casino Event Schemas

```json
{
    "schemaSet": "casino-events",
    "schemas": [
        {
            "name": "SlotTelemetryEvent",
            "version": 1,
            "fields": [
                {"name": "MachineId", "type": "string", "required": true},
                {"name": "EventType", "type": "string", "required": true, "allowed": ["spin", "payout", "error", "maintenance"]},
                {"name": "Wager", "type": "decimal", "required": false},
                {"name": "Payout", "type": "decimal", "required": false},
                {"name": "Timestamp", "type": "datetime", "required": true}
            ]
        },
        {
            "name": "PlayerTransactionEvent",
            "version": 1,
            "fields": [
                {"name": "PlayerId", "type": "string", "required": true},
                {"name": "Amount", "type": "decimal", "required": true},
                {"name": "TransactionType", "type": "string", "required": true},
                {"name": "Timestamp", "type": "datetime", "required": true}
            ]
        }
    ]
}
```

### Confluent Schema Registry Support

Eventstream also supports decoding data from Confluent Schema Registry topics, enabling seamless migration from Kafka-native streaming architectures. This is relevant for organizations migrating from Confluent Cloud or on-premises Kafka deployments.

---

## 🔺 DeltaFlow Transformation

DeltaFlow (Preview) transforms raw Change Data Capture (CDC) events into flattened, analytics-ready format. This is particularly valuable for mirroring and CDC streaming scenarios.

### How DeltaFlow Works

```mermaid
flowchart LR
    subgraph Input["📥 CDC Events"]
        CDC["Debezium/CDC<br/>Insert, Update, Delete<br/>Before/After images"]
    end

    subgraph Transform["🔺 DeltaFlow"]
        FLAT["Flatten CDC envelope"]
        META["Add metadata columns"]
        TAB["Produce tabular rows"]
    end

    subgraph Output["📤 Analytics-Ready"]
        DT["Delta Table<br/>Standard row format<br/>_operation, _timestamp"]
    end

    Input --> Transform --> Output

    style Transform fill:#E67E22,stroke:#CA6F1E,color:#fff
```

### DeltaFlow Output Columns

| Column | Description |
|--------|-------------|
| `_operation` | Type of change: INSERT, UPDATE, DELETE |
| `_timestamp` | When the change occurred |
| `_source_table` | Original source table name |
| `_transaction_id` | Source transaction identifier |
| All source columns | Flattened from the CDC `after` image |

> 📝 **Note**: DeltaFlow complements the existing CDC streaming notebooks in this POC (e.g., `01_sql_server_cdc.py`, `05_oracle_cdc.py`). It provides a no-code alternative for simple CDC flattening, while the notebook approach remains better for complex transformation logic.

---

## 🏭 Digital Twin Builder

Digital Twin Builder (Preview) is a new Real-Time Intelligence item for creating data-driven, real-time representations of physical entities. It enables organizations to model physical environments as digital entities with real-time data bindings.

For comprehensive documentation, see the dedicated [Digital Twin Builder Guide](digital-twin-builder.md).

### Quick Overview

| Aspect | Details |
|--------|---------|
| **What** | Real-time digital representations of physical entities |
| **Where** | New item type within RTI workload |
| **Data Source** | Eventhouse tables and materialized views |
| **Entity Types** | Custom-defined (machines, zones, facilities, sensors) |
| **Properties** | Static (metadata) and dynamic (real-time telemetry) |
| **Relationships** | Parent-child, monitors, contains, serves |

### Casino Floor Twin Example

```
Casino
  └── Floor (Floor 1, Floor 2)
        └── Zone (High Limit, Penny Slots, Table Games)
              └── Machine (SM-001, SM-002, ...)
                    Properties: utilization, revenue/hr, error_rate, temperature
```

### Federal Facility Twin Example

```
USDA Regional Office
  └── Warehouse (Storage Facility A)
        └── Storage Unit (Cold Storage 1)
              └── Sensor (Temp-001, Humidity-001)
                    Properties: temperature, humidity, inventory_count
```

---

## 🤖 MCP for Real-Time Intelligence

Model Context Protocol (MCP) support for RTI (Preview) enables AI agents and applications to interact directly with Eventhouse and Data Activator through standardized MCP interfaces.

### MCP Remote Servers

| Server | Capabilities |
|--------|-------------|
| **Eventhouse MCP** | Execute KQL queries, browse databases, list tables, get schema information |
| **Activator MCP** | Create/modify alert rules, check alert status, manage triggers |

### AI Agent Integration Pattern

```mermaid
flowchart LR
    subgraph Agent["🤖 AI Agent"]
        LLM["Language Model"]
        MCP_C["MCP Client"]
    end

    subgraph RTI["⚡ RTI MCP Servers"]
        EH_MCP["Eventhouse<br/>MCP Server"]
        ACT_MCP["Activator<br/>MCP Server"]
    end

    subgraph Data["📊 RTI Data"]
        KQL_DB["KQL Databases"]
        ALERTS["Alert Rules"]
    end

    Agent -->|"MCP Protocol"| RTI --> Data

    style RTI fill:#E67E22,stroke:#CA6F1E,color:#fff
    style Agent fill:#6C3483,stroke:#4A235A,color:#fff
```

### Use Cases

| Scenario | MCP Action | Example |
|----------|-----------|---------|
| Natural language KQL | Agent translates question to KQL, executes via MCP | "What's the slot revenue for Floor 2 in the last hour?" |
| Alert management | Agent creates/modifies Activator rules via MCP | "Set up an alert when Floor 3 utilization drops below 20%" |
| Incident investigation | Agent queries multiple tables to correlate events | "Why did Machine SM-1042 go offline at 3:15 PM?" |

> 📝 **Note**: MCP for RTI connects directly with [Fabric Data Agents](data-agents.md), enabling agents to answer questions about real-time operational data.

---

## 🔌 New Connectors (2025-2026)

Several new Eventstream connectors have been added since the original release:

| Connector | Status | Description |
|-----------|--------|-------------|
| **Cribl Stream** (Preview) | New | Receive data from diverse telemetry and log sources through Cribl Stream. Supports Syslog, Datadog Agent, Splunk, OpenTelemetry, and edge-based sources. |
| **Solace PubSub+** (Preview) | New | Connect Fabric Eventstream with Solace PubSub+ event brokers for enterprise messaging integration. |
| **Confluent Schema Registry** (Preview) | New | Decode data from Confluent Schema Registry topics for Avro/Protobuf/JSON Schema encoded data. |
| **Azure Monitor** (Preview) | New | Route VM telemetry via Azure Monitor Agent and Data Collection Rules directly to Eventhouse. |
| **Private Network Streaming** (Preview) | New | Azure VNet bridge for on-premises/private cloud sources via VPN, ExpressRoute, or private endpoints. |
| **Azure Blob Storage Shortcut** (Preview) | New | Create shortcuts to Azure Blob Storage for direct data access. |

### Connector Architecture Updates

```mermaid
flowchart TB
    subgraph NewSources["🆕 New Sources (2025-2026)"]
        CR["Cribl Stream<br/>Syslog, Splunk, OTEL"]
        SO["Solace PubSub+"]
        AZ["Azure Monitor<br/>VM Telemetry"]
        PN["Private Network<br/>VPN/ExpressRoute"]
    end

    subgraph ExistingSources["📡 Existing Sources"]
        EH["Azure Event Hub"]
        KF["Apache Kafka"]
        IO["IoT Hub"]
        DB["CDC Sources"]
    end

    subgraph Eventstream["📥 Eventstream"]
        SR["Schema Registry<br/>(Optional)"]
        SQL["SQL Operator<br/>(GA)"]
        NC["No-Code Transform"]
    end

    NewSources --> Eventstream
    ExistingSources --> Eventstream

    style NewSources fill:#27AE60,stroke:#1E8449,color:#fff
    style Eventstream fill:#E67E22,stroke:#CA6F1E,color:#fff
```

> 💡 **Tip**: The Private Network Streaming connector is particularly relevant for federal agencies with on-premises data sources that cannot be exposed to the public internet. Use VNet data gateways with ExpressRoute for secure, high-throughput streaming from agency data centers.

---

## 📚 References

| Resource | URL |
|----------|-----|
| Real-Time Intelligence Overview | https://learn.microsoft.com/fabric/real-time-intelligence/overview |
| Eventstream Documentation | https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/overview |
| Eventhouse Documentation | https://learn.microsoft.com/fabric/real-time-intelligence/eventhouse |
| KQL Reference | https://learn.microsoft.com/kusto/query/ |
| Real-Time Dashboards | https://learn.microsoft.com/fabric/real-time-intelligence/dashboard-real-time-create |
| Data Activator | https://learn.microsoft.com/fabric/real-time-intelligence/data-activator/data-activator-introduction |
| Materialized Views | https://learn.microsoft.com/kusto/management/materialized-views/materialized-view-overview |
| Caching Policy | https://learn.microsoft.com/kusto/management/cache-policy |

---

## 🔗 Related Documents

- [Fabric IQ](fabric-iq.md) -- Natural language querying for RTI data
- [AI Copilot Configuration](ai-copilot-configuration.md) -- KQL Copilot for Eventhouse
- [Data Mesh Enterprise Patterns](data-mesh-enterprise-patterns.md) -- Cross-domain RTI architecture
- [Digital Twin Builder](digital-twin-builder.md) -- Entity modeling with real-time data bindings
- [Data Agents](data-agents.md) -- AI agents powered by RTI data via MCP
- [OneLake Security](onelake-security.md) -- Fine-grained security for RTI data in OneLake
- [Eventhouse Vector Database](eventhouse-vector-database.md) -- Vector search and AI embeddings in Eventhouse
- [Copy Job CDC](copy-job-cdc.md) -- Change data capture for continuous ingestion into RTI
- [Workspace Monitoring](workspace-monitoring.md) -- System tables for monitoring RTI workloads
- [Mirroring](mirroring.md) -- Near-real-time DB replication as alternative to streaming
- [Direct Lake](direct-lake.md) -- Direct Lake semantic models over RTI-landed data
- [Architecture](../ARCHITECTURE.md) -- System architecture overview
- [Migration & RTI Research](../MIGRATION_AND_RTI_RESEARCH.md) -- Migration paths and RTI research notes

---

> 📝 **Document Metadata**
> - **Author**: Documentation Team
> - **Reviewers**: Data Engineering, Streaming Team, Compliance
> - **Classification**: Internal
> - **Next Review**: 2026-06-12
