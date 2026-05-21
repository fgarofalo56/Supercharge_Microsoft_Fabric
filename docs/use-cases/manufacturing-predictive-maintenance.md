---
hero: assets/heroes/manufacturing.svg
hero_alt: Predictive maintenance + OEE on factory telemetry
type: feature
---
# Manufacturing Predictive Maintenance & OEE Analytics

## Use Case Overview

| Attribute | Detail |
|-----------|--------|
| **Industry** | Discrete Manufacturing |
| **Domain** | Predictive Maintenance, OEE, Quality Analytics |
| **Facility** | 200 CNC machines, 4 production lines, 24/7 operation |
| **Compliance** | IEC 62443 (Industrial Cybersecurity) |
| **Fabric SKU** | F64 (P1 equivalent) |
| **Estimated Cost** | ~$15,000/month |
| **ROI Driver** | Unplanned downtime reduction (avg $250K/hr cost) |

---

## Business Context

Modern discrete manufacturing plants generate massive volumes of sensor telemetry
from CNC machines, hydraulic presses, robotic arms, and conveyor systems. A single
CNC machine can produce 50-100 sensor readings per second across vibration,
temperature, spindle current, coolant pressure, and RPM channels.

**The problem:** Traditional time-based maintenance either replaces parts too early
(wasting capital) or too late (causing unplanned downtime at $250K/hour). Quality
defects traced to process parameter drift are caught only after production,
generating scrap and rework costs.

**The solution:** Microsoft Fabric unifies IoT ingestion, anomaly detection,
predictive modeling, and BI reporting in a single platform. Eventstream captures
sensor data from Azure IoT Hub in real time, Eventhouse runs KQL anomaly detection,
and the medallion lakehouse builds OEE dashboards and maintenance predictions.

### Key Metrics

| Metric | Current State | Target State | Impact |
|--------|--------------|--------------|--------|
| Unplanned downtime | 12% of shift time | < 3% | $4.5M/yr savings |
| OEE | 62% | > 82% | 32% throughput gain |
| Mean Time Between Failure | 380 hrs | > 900 hrs | 2.4x improvement |
| Quality defect rate | 2.8% | < 0.5% | $800K/yr scrap reduction |
| Energy per unit | 4.2 kWh | < 3.1 kWh | 26% energy savings |

---

## Architecture

### High-Level Data Flow

```
IoT Hub (MQTT/OPC-UA)
        |
        v
  Eventstream (real-time ingestion)
        |
        +------> Eventhouse (KQL anomaly detection, 30-sec latency)
        |
        v
  Bronze: bronze_manufacturing_sensors (raw telemetry, append-only)
        |
        v
  Silver: silver_manufacturing_health (1-min aggregations, anomaly flags)
        |
        v
  Gold: gold_manufacturing_oee (OEE per machine/shift)
        gold_maintenance_predictions (predictive scores + schedules)
        |
        v
  Power BI (Direct Lake) -- OEE Dashboard, Maintenance Calendar
        |
        v
  Digital Twin Builder (3D plant model, live sensor overlay)
```

### Component Details

| Component | Purpose | Fabric Item |
|-----------|---------|-------------|
| Azure IoT Hub | Device connectivity, MQTT/AMQP broker | External (Azure) |
| Eventstream | Real-time ingestion from IoT Hub | Eventstream |
| Eventhouse | Sub-minute anomaly detection via KQL | Eventhouse + KQL Queryset |
| Lakehouse | Medallion architecture (Bronze/Silver/Gold) | Lakehouse |
| Notebooks | Spark ETL + ML scoring | Notebook |
| Power BI | OEE dashboards, maintenance calendar | Report (Direct Lake) |
| Digital Twin | 3D facility visualization | Digital Twin Builder |
| Data Activator | Alert on anomaly thresholds | Reflex |

### Medallion Tables

| Layer | Table | Description | Grain |
|-------|-------|-------------|-------|
| Bronze | `bronze_manufacturing_sensors` | Raw sensor readings | Per reading (~100/sec/machine) |
| Silver | `silver_manufacturing_health` | 1-min aggregations + anomaly flags | Per sensor per machine per minute |
| Gold | `gold_manufacturing_oee` | OEE components per shift | Per machine per shift |
| Gold | `gold_maintenance_predictions` | Predictive maintenance scores | Per machine per day |

---

## Sensor Architecture

### Sensor Types per Machine

| Sensor | Unit | Normal Range | Warning | Critical |
|--------|------|-------------|---------|----------|
| Vibration | mm/s | 0.5 - 4.5 | 4.5 - 7.0 | > 7.0 |
| Temperature | C | 20 - 65 | 65 - 85 | > 85 |
| Spindle Current | A | 5 - 45 | 45 - 55 | > 55 |
| Coolant Pressure | bar | 3.0 - 8.0 | 2.0 - 3.0 or 8.0 - 10.0 | < 2.0 or > 10.0 |
| Spindle RPM | rpm | 500 - 12000 | N/A (setpoint-dependent) | Deviation > 5% |

### Machine Types

| Type | Count | Sensors/Machine | Readings/sec | Daily Volume |
|------|-------|-----------------|-------------|--------------|
| CNC Mill | 120 | 5 | 10 | 51.8M |
| Hydraulic Press | 30 | 5 | 5 | 6.5M |
| Robotic Arm | 30 | 5 | 20 | 25.9M |
| Conveyor | 20 | 3 | 2 | 1.7M |
| **Total** | **200** | — | — | **~86M/day** |

### Degradation Patterns

Predictive maintenance relies on detecting gradual degradation before catastrophic
failure. The data generator models realistic failure modes:

1. **Bearing Wear (CNC):** Vibration increases linearly 0.02 mm/s per day over
   30-60 days, then exponentially in final 5 days before seizure.
2. **Thermal Degradation:** Temperature baseline drifts +0.5C/week when coolant
   system degrades.
3. **Current Draw Increase:** Worn tooling causes 2-5% current increase per week.
4. **Pressure Loss:** Hydraulic seal degradation shows slow pressure drop.

---

## Real-Time Anomaly Detection (Eventhouse)

### KQL Anomaly Query

```kql
// Detect vibration anomalies using series decomposition
let lookback = 1h;
SensorTelemetry
| where timestamp > ago(lookback)
| where sensor_type == "vibration"
| summarize avg_vibration = avg(value) by machine_id, bin(timestamp, 1m)
| order by machine_id, timestamp asc
| summarize ts = make_list(timestamp), vals = make_list(avg_vibration) by machine_id
| extend anomalies = series_decompose_anomalies(vals, 1.5)
| mv-expand ts to typeof(datetime), vals to typeof(double), anomalies to typeof(int)
| where anomalies == 1
| project machine_id, timestamp = ts, vibration = vals, anomaly_score = anomalies
```

### KQL OEE Real-Time View

```kql
// Real-time OEE calculation per production line
let shift_start = bin(now(), 8h);
MachineEvents
| where timestamp > shift_start
| summarize
    planned_time = 480,  // 8-hour shift in minutes
    run_time = countif(state == "running"),
    total_parts = sum(parts_produced),
    good_parts = sum(good_parts),
    ideal_cycle = avg(ideal_cycle_time_sec)
    by production_line
| extend
    availability = toreal(run_time) / planned_time,
    performance = (toreal(total_parts) * ideal_cycle / 60) / run_time,
    quality = toreal(good_parts) / total_parts
| extend oee = availability * performance * quality
| project production_line, availability, performance, quality, oee
```

---

## OEE Calculation

**OEE = Availability x Performance x Quality**

### Component Definitions

| Component | Formula | Inputs |
|-----------|---------|--------|
| **Availability** | Run Time / Planned Production Time | Downtime events, shift schedule |
| **Performance** | (Ideal Cycle Time x Total Parts) / Run Time | Parts count, cycle time standard |
| **Quality** | Good Parts / Total Parts | Defect count, rework count |

### OEE Benchmarks

| Level | OEE | Interpretation |
|-------|-----|----------------|
| World-class | >= 85% | Top-quartile discrete manufacturing |
| Good | 70-84% | Room for improvement, competitive |
| Average | 55-69% | Typical, significant loss opportunity |
| Poor | < 55% | Major losses in availability/performance/quality |

---

## Quality Defect Prediction

Process parameters correlate with downstream quality defects. The gold layer
computes feature vectors from silver aggregations and scores them against a
trained model:

| Feature | Source | Correlation to Defects |
|---------|--------|----------------------|
| Vibration stddev (1-min) | silver_manufacturing_health | 0.72 |
| Temperature max delta | silver_manufacturing_health | 0.65 |
| Current coefficient of variation | silver_manufacturing_health | 0.58 |
| RPM deviation from setpoint | silver_manufacturing_health | 0.61 |
| Time since last maintenance | work_orders | 0.54 |

When the composite defect probability exceeds 0.7, the system triggers a
Data Activator alert to the quality team and recommends parameter adjustment.

---

## Energy Optimization

Energy consumption per unit produced is tracked at the machine and line level:

```
Energy per Unit = Total kWh consumed / Good Parts Produced
```

The gold layer aggregates energy consumption from current and voltage sensors,
correlates with production output, and identifies:

- **Idle energy waste:** Machines consuming power during unplanned stops
- **Peak demand spikes:** Suboptimal scheduling causing demand charges
- **Efficiency degradation:** Worn tooling requiring more energy per cut

### Optimization Strategies

1. **Load balancing:** Distribute jobs to minimize peak demand across lines
2. **Idle shutdown:** Auto-standby after 10 minutes of no production
3. **Tool change scheduling:** Replace tools before energy efficiency drops >15%

---

## Digital Twin Integration

This use case integrates with the Digital Twin Builder feature documented in
[docs/features/digital-twin-builder.md](../features/digital-twin-builder.md).

### Twin Model Structure

```
Manufacturing Plant (root)
  +-- Production Line 1
  |     +-- CNC-001 (live sensors: vibration, temp, current, pressure, rpm)
  |     +-- CNC-002
  |     +-- ...
  +-- Production Line 2
  |     +-- Press-001
  |     +-- Robot-001
  +-- Utility Systems
        +-- Coolant System
        +-- Compressed Air
        +-- Electrical Distribution
```

### Twin Capabilities

| Capability | Description |
|------------|-------------|
| Live sensor overlay | Real-time values displayed on 3D machine models |
| Heatmap visualization | Temperature/vibration intensity across plant floor |
| What-if simulation | Model impact of taking machine offline for maintenance |
| Historical playback | Replay sensor data around failure events |

---

## IEC 62443 Compliance

IEC 62443 defines cybersecurity requirements for Industrial Automation and Control
Systems (IACS). This architecture enforces the following controls:

### Network Segmentation (Zones & Conduits)

```
Zone 0: Safety Systems (isolated, air-gapped)
Zone 1: OT Network (PLCs, sensors, SCADA)
         |
    [Industrial DMZ - Conduit]
         |
Zone 2: IT Network (IoT Hub, Fabric, BI)
         |
Zone 3: Enterprise / Internet
```

| Control | Implementation |
|---------|---------------|
| **Zone separation** | OT and IT on separate VLANs with firewall rules |
| **Conduit security** | Industrial DMZ hosts IoT Edge gateway; no direct OT-to-cloud |
| **Protocol restriction** | Only MQTT/OPC-UA from OT to DMZ; AMQP from DMZ to IoT Hub |
| **Authentication** | X.509 certificates per device; no shared keys |
| **Data diode** | Sensor data flows one-way (OT -> IT); no commands from cloud to OT |

### Secure Ingestion Path

```
Sensor --> PLC --> OPC-UA Server --> IoT Edge (DMZ) --> IoT Hub --> Eventstream
                                         |
                                   [TLS 1.2+, X.509]
```

### Security Levels

| SL | Zone | Description |
|----|------|-------------|
| SL 1 | Zone 1 (OT) | Protection against casual violation |
| SL 2 | DMZ | Protection against intentional violation with low resources |
| SL 3 | Zone 2 (IT/Fabric) | Protection against intentional violation with moderate resources |

### Fabric-Specific Controls

| Control | Fabric Feature |
|---------|---------------|
| Data encryption at rest | OneLake encryption (Microsoft-managed or CMK) |
| Data encryption in transit | TLS 1.2+ enforced |
| Access control | Workspace roles + row-level security |
| Audit logging | SQL Audit Logs, Workspace Monitoring |
| Network isolation | Private endpoints + Outbound Access Protection |
| Sensitivity labels | Auto-applied to manufacturing data (Confidential) |

---

## Cost Analysis

### Monthly Fabric Costs (~$15,000)

| Component | Cost | Notes |
|-----------|------|-------|
| F64 Capacity (Fabric) | $8,200 | Shared across all workloads |
| Eventhouse (hot storage) | $2,800 | 30-day retention, ~86M records/day |
| OneLake storage | $1,500 | Delta tables, ~2.5 TB/month growth |
| Power BI Premium | $1,200 | Included in F64 |
| Data Activator | $800 | Alert rules for anomaly triggers |
| IoT Hub (S2) | $500 | External Azure cost |
| **Total** | **~$15,000** | |

### ROI Calculation

| Benefit | Annual Value |
|---------|-------------|
| Unplanned downtime reduction (12% -> 3%) | $4,500,000 |
| Quality defect reduction (2.8% -> 0.5%) | $800,000 |
| Energy optimization (26% reduction) | $350,000 |
| Maintenance parts savings (predictive vs preventive) | $200,000 |
| **Total annual benefit** | **$5,850,000** |
| **Annual Fabric + Azure cost** | **$186,000** |
| **Net ROI** | **31:1** |

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

- Deploy IoT Hub and configure device provisioning (X.509)
- Set up Eventstream ingestion from IoT Hub
- Create bronze notebook (`54_manufacturing_sensors.py`)
- Deploy Eventhouse with 30-day retention

### Phase 2: Analytics (Weeks 3-4)

- Build silver aggregation notebook (`54_manufacturing_aggregated.py`)
- Implement KQL anomaly detection queries
- Create gold OEE notebook (`54_manufacturing_oee.py`)
- Build Power BI OEE dashboard (Direct Lake)

### Phase 3: Intelligence (Weeks 5-6)

- Train predictive maintenance model (survival analysis)
- Implement quality defect prediction scoring
- Configure Data Activator alerts
- Deploy Digital Twin with live sensor overlay

### Phase 4: Optimization (Weeks 7-8)

- Energy optimization reporting
- Maintenance calendar integration
- Stakeholder training
- Production go-live

---

## Notebooks

| Notebook | Layer | Purpose |
|----------|-------|---------|
| `54_manufacturing_sensors.py` | Bronze | Raw sensor ingestion |
| `54_manufacturing_aggregated.py` | Silver | 1-min aggregation + anomaly flags |
| `54_manufacturing_oee.py` | Gold | OEE + maintenance predictions |

---

## Data Generator

The synthetic data generator (`data_generation/generators/manufacturing/sensor_generator.py`)
produces realistic sensor telemetry with configurable degradation patterns.

```python
from data_generation.generators.manufacturing.sensor_generator import ManufacturingSensorGenerator

gen = ManufacturingSensorGenerator(seed=42, num_machines=200)
sensors_df = gen.generate(num_records=10000)
```

---

## References

- [Digital Twin Builder](../features/digital-twin-builder.md)
- [Real-Time Intelligence](../features/real-time-intelligence.md)
- [Eventhouse Vector Database](../features/eventhouse-vector-database.md)
- [Network Security Best Practices](../best-practices/network-security.md)
- [Monitoring & Observability](../best-practices/monitoring-observability.md)
- [IEC 62443 Standard](https://www.iec.ch/cyber-security)
- [Azure IoT Hub Documentation](https://learn.microsoft.com/azure/iot-hub/)
- [OEE Foundation](https://www.oee.com/)

---

## Glossary

| Term | Definition |
|------|-----------|
| **OEE** | Overall Equipment Effectiveness -- composite metric of availability, performance, quality |
| **MTBF** | Mean Time Between Failures |
| **MTTR** | Mean Time To Repair |
| **OPC-UA** | Open Platform Communications Unified Architecture -- industrial interoperability standard |
| **MQTT** | Message Queuing Telemetry Transport -- lightweight IoT messaging protocol |
| **PLC** | Programmable Logic Controller |
| **SCADA** | Supervisory Control and Data Acquisition |
| **OT** | Operational Technology (factory floor systems) |
| **IT** | Information Technology (enterprise systems) |
| **DMZ** | Demilitarized Zone (network buffer between OT and IT) |
| **IEC 62443** | International standard for industrial cybersecurity |
| **CNC** | Computer Numerical Control (precision machining) |
