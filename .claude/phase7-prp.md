# PRP: Phase 7 - Federal Agencies, Migration Paths, Advanced RTI, Video Analytics & GeoAnalytics

## Executive Summary

Massive expansion of the Microsoft Fabric POC to cover:
- **Federal Agency Data Domains**: USDA, SBA, NOAA, EPA, DOI (replacing Retail/E-commerce)
- **Database Migration Paths**: Teradata→Fabric, Snowflake→Fabric, IBM DB2 as source
- **Advanced Real-Time Intelligence**: Multi-source streaming (SQL, Azure SQL, Cosmos DB, DB2, Oracle, Kafka, IoT)
- **Video/Security Analytics**: Video analysis, people movement, geolocation
- **ArcGIS GeoAnalytics Engine**: Spatial analysis with Esri/Apache Sedona
- **Enhanced Tribal Healthcare**: Complete implementation of stubbed Phase 2
- **Enhanced Federal DOT/FAA**: Complete implementation of stubbed Phase 3

All features use the autonomous coding agent harness for implementation.

---

## 1. New Repository Structure

```
future-expansions/
├── federal-usda/                     # USDA agriculture & food safety
│   ├── README.md                     # Planning doc with open datasets
│   ├── data-domains.md               # USDA data entity specifications
│   └── open-datasets.md              # Dataset catalog with URLs/APIs
├── federal-sba/                      # SBA small business
│   ├── README.md
│   ├── data-domains.md
│   └── open-datasets.md
├── federal-noaa/                     # NOAA weather & ocean
│   ├── README.md
│   ├── data-domains.md
│   └── open-datasets.md
├── federal-epa/                      # EPA environmental
│   ├── README.md
│   ├── data-domains.md
│   └── open-datasets.md
├── federal-doi/                      # DOI land & geological
│   ├── README.md
│   ├── data-domains.md
│   └── open-datasets.md
├── tribal-healthcare/                # (existing, expand)
│   └── README.md
└── federal-dot-faa/                  # (existing, expand)
    └── README.md

tutorials/
├── 24-snowflake-to-fabric/           # Snowflake migration
│   └── README.md
├── 25-ibm-db2-source/                # IBM DB2 as source
│   └── README.md
├── 26-multi-source-streaming/        # Multi-source RTI
│   └── README.md
├── 27-video-security-analytics/      # Video analysis pipeline
│   └── README.md
├── 28-people-movement-analytics/     # People movement & heat maps
│   └── README.md
└── 29-geolocation-analytics/         # Geo/location analytics
    └── README.md

notebooks/
└── streaming/                        # New streaming notebooks
    ├── 01_sql_server_cdc.py
    ├── 02_azure_sql_change_feed.py
    ├── 03_cosmos_db_change_feed.py
    ├── 04_ibm_db2_cdc.py
    ├── 05_oracle_cdc.py
    ├── 06_kafka_connector.py
    ├── 07_iot_hub_ingestion.py
    └── 08_slot_machine_iot_simulator.py

data_generation/
├── generators/
│   ├── federal/                      # Agency-specific generators
│   │   ├── usda_generator.py         # Crop data, food safety, SNAP
│   │   ├── sba_generator.py          # Loan data, disaster assistance
│   │   ├── noaa_generator.py         # Weather obs, storm events
│   │   ├── epa_generator.py          # Air/water quality, TRI
│   │   └── doi_generator.py          # Land use, earthquakes, wildlife
│   ├── analytics/
│   │   ├── video_analytics_generator.py    # Video event metadata
│   │   ├── people_movement_generator.py    # Foot traffic, heat maps
│   │   └── geolocation_generator.py        # GPS, geofence events
│   └── streaming/
│       ├── multi_source_simulator.py       # All-source event simulator
│       └── iot_device_simulator.py         # IoT device fleet simulator
├── schemas/
│   ├── federal/                      # Agency data schemas
│   │   ├── usda_crop_schema.json
│   │   ├── usda_food_safety_schema.json
│   │   ├── sba_loan_schema.json
│   │   ├── noaa_weather_schema.json
│   │   ├── noaa_storm_schema.json
│   │   ├── epa_air_quality_schema.json
│   │   ├── epa_water_quality_schema.json
│   │   ├── doi_earthquake_schema.json
│   │   └── doi_land_use_schema.json
│   ├── streaming/
│   │   ├── cdc_event_schema.json
│   │   ├── iot_telemetry_schema.json
│   │   └── kafka_message_schema.json
│   └── analytics/
│       ├── video_event_schema.json
│       ├── movement_event_schema.json
│       └── geolocation_schema.json
└── config/
    ├── federal_datasets.yaml         # Open dataset registry
    └── streaming_sources.yaml        # Source connector configs

validation/
├── unit_tests/
│   ├── federal/
│   │   ├── test_usda_generator.py
│   │   ├── test_sba_generator.py
│   │   ├── test_noaa_generator.py
│   │   ├── test_epa_generator.py
│   │   └── test_doi_generator.py
│   ├── streaming/
│   │   ├── test_multi_source_simulator.py
│   │   └── test_iot_simulator.py
│   └── analytics/
│       ├── test_video_analytics_generator.py
│       ├── test_people_movement_generator.py
│       └── test_geolocation_generator.py
```

---

## 2. Federal Agency Data Domains

### 2.1 USDA (Department of Agriculture)

| Domain | Bronze Table | Silver Table | Gold Table |
|--------|-------------|--------------|------------|
| Crop Production | `bronze_usda_crop_production` | `silver_usda_crop_cleansed` | `gold_usda_crop_analytics` |
| Food Safety | `bronze_usda_food_inspections` | `silver_usda_inspections_enriched` | `gold_usda_food_safety_dashboard` |
| SNAP/Nutrition | `bronze_usda_snap_retailers` | `silver_usda_snap_validated` | `gold_usda_nutrition_metrics` |
| Farm Subsidies | `bronze_usda_farm_payments` | `silver_usda_payments_reconciled` | `gold_usda_subsidy_analysis` |

**Open Datasets:**
- USDA NASS QuickStats API (crop production, livestock, economics)
- FSIS Recall Data (food safety recalls)
- SNAP Retailer Locator (authorized retailer data)
- Farm Service Agency payment data
- National Agricultural Statistics Service Census of Agriculture

**Compliance:** USDA data sharing policies, FOIA, Privacy Act

### 2.2 SBA (Small Business Administration)

| Domain | Bronze Table | Silver Table | Gold Table |
|--------|-------------|--------------|------------|
| PPP Loans | `bronze_sba_ppp_loans` | `silver_sba_ppp_validated` | `gold_sba_ppp_analytics` |
| 7(a) Loans | `bronze_sba_7a_loans` | `silver_sba_7a_enriched` | `gold_sba_lending_dashboard` |
| Disaster Loans | `bronze_sba_disaster_loans` | `silver_sba_disaster_validated` | `gold_sba_disaster_analytics` |
| SBIR/STTR | `bronze_sba_sbir_awards` | `silver_sba_sbir_enriched` | `gold_sba_innovation_metrics` |

**Open Datasets:**
- SBA PPP Loan-Level Data (150K-10M loans, public FOIA release)
- 7(a) and 504 Loan Data
- SBIR/STTR Award Data
- HUBZone Data
- 8(a) Business Development Program data

**Compliance:** FOIA, Privacy Act, Small Business Act reporting

### 2.3 NOAA (National Oceanic and Atmospheric Administration)

| Domain | Bronze Table | Silver Table | Gold Table |
|--------|-------------|--------------|------------|
| Weather Observations | `bronze_noaa_weather_obs` | `silver_noaa_weather_cleansed` | `gold_noaa_weather_analytics` |
| Storm Events | `bronze_noaa_storm_events` | `silver_noaa_storms_enriched` | `gold_noaa_storm_dashboard` |
| Ocean/Tide Data | `bronze_noaa_tide_data` | `silver_noaa_tide_validated` | `gold_noaa_ocean_analytics` |
| Climate Normals | `bronze_noaa_climate_normals` | `silver_noaa_climate_processed` | `gold_noaa_climate_trends` |

**Open Datasets:**
- NOAA Climate Data Online (CDO) API - billions of weather records
- Storm Events Database (1950-present, ~2M records)
- GHCN (Global Historical Climatology Network) Daily
- CO-OPS Tide/Current Data API
- NCEI Integrated Surface Database
- National Buoy Data Center

**Real-Time Capabilities:** NOAA Weather API provides near-real-time observations

### 2.4 EPA (Environmental Protection Agency)

| Domain | Bronze Table | Silver Table | Gold Table |
|--------|-------------|--------------|------------|
| Air Quality | `bronze_epa_air_quality` | `silver_epa_aqi_validated` | `gold_epa_air_dashboard` |
| Water Quality | `bronze_epa_water_quality` | `silver_epa_water_enriched` | `gold_epa_water_dashboard` |
| Toxic Releases | `bronze_epa_tri_releases` | `silver_epa_tri_analyzed` | `gold_epa_toxics_analytics` |
| Superfund Sites | `bronze_epa_superfund` | `silver_epa_superfund_enriched` | `gold_epa_cleanup_dashboard` |

**Open Datasets:**
- AirNow API (real-time AQI for 2,000+ monitoring stations)
- TRI Explorer (Toxic Release Inventory - 4M+ records)
- ECHO (Enforcement & Compliance History Online)
- Safe Drinking Water Information System (SDWIS)
- Superfund/CERCLIS site data
- Greenhouse Gas Reporting Program (GHGRP)

**Real-Time Capabilities:** AirNow API provides hourly AQI updates

### 2.5 DOI (Department of the Interior)

| Domain | Bronze Table | Silver Table | Gold Table |
|--------|-------------|--------------|------------|
| Earthquakes | `bronze_doi_earthquakes` | `silver_doi_seismic_enriched` | `gold_doi_earthquake_dashboard` |
| Water Resources | `bronze_doi_water_data` | `silver_doi_hydro_validated` | `gold_doi_water_analytics` |
| Wildlife/Species | `bronze_doi_species_data` | `silver_doi_species_enriched` | `gold_doi_biodiversity_dashboard` |
| Land Use | `bronze_doi_land_parcels` | `silver_doi_land_classified` | `gold_doi_land_analytics` |

**Open Datasets:**
- USGS Earthquake Hazards API (real-time, global earthquake catalog)
- USGS National Water Information System (NWIS) - streamflow, groundwater
- FWS ECOS (Environmental Conservation Online System) - species data
- BLM Public Land Statistics
- NPS Visitor Use Statistics
- USGS National Map / The National Map APIs

**Real-Time Capabilities:** USGS Earthquake API provides real-time seismic data (GeoJSON)

---

## 3. Migration Path Specifications

### 3.1 Teradata to Microsoft Fabric (Enhance Tutorial 10)
- Schema/DDL conversion patterns (Teradata SQL → Spark SQL)
- BTEQ/FastLoad → Data Pipeline equivalents
- Data type mapping reference table
- Workload migration assessment tool
- Performance benchmarking framework
- Migration scripts and templates

### 3.2 Snowflake to Microsoft Fabric (New Tutorial 24)
- Snowflake connector configuration
- Snowpipe → Eventstreams migration
- Stored procedure → Notebook conversion
- UDF → Spark UDF migration
- Data sharing alternatives (Snowflake → ADLS → OneLake)
- Cost comparison worksheet
- Architecture mapping (Snowflake concepts → Fabric concepts)

### 3.3 IBM DB2 as Source (New Tutorial 25)
- On-premises Data Gateway setup for DB2
- DB2 for z/OS vs DB2 LUW connector differences
- JDBC connection patterns
- CDC (Change Data Capture) from DB2
- Bulk load patterns for initial migration
- Incremental sync patterns
- Data type mapping (DB2 → Delta Lake)

---

## 4. Advanced RTI & Streaming Specifications

### 4.1 Multi-Source Streaming Architecture

```
Sources                    Ingestion           Processing          Storage
┌──────────┐
│ SQL Svr  │──CDC──┐
│ (on-prem)│       │
└──────────┘       │    ┌─────────────┐    ┌──────────────┐    ┌───────────┐
┌──────────┐       ├───>│             │    │              │    │           │
│ Azure SQL│──CDC──┤    │ Eventstream │───>│ Eventhouse   │───>│ Lakehouse │
│          │       │    │ (Hub)       │    │ (KQL DB)     │    │ (Delta)   │
└──────────┘       │    │             │    │              │    │           │
┌──────────┐       │    └─────────────┘    └──────────────┘    └───────────┘
│ Cosmos DB│──CF───┤           │
│          │       │           │
└──────────┘       │    ┌──────┴──────┐
┌──────────┐       │    │ Real-Time   │
│ IBM DB2  │──CDC──┤    │ Dashboard   │
│          │       │    └─────────────┘
└──────────┘       │
┌──────────┐       │
│ Oracle   │──CDC──┤
│          │       │
└──────────┘       │
┌──────────┐       │
│ Kafka    │───────┤
│ Cluster  │       │
└──────────┘       │
┌──────────┐       │
│ IoT Hub  │───────┤
│ Devices  │       │
└──────────┘       │
┌──────────┐       │
│ Slot Sim │───────┘
│ (Custom) │
└──────────┘
```

### 4.2 Streaming Notebook Specifications

| # | Notebook | Source | Pattern | Key Features |
|---|----------|--------|---------|--------------|
| 01 | `sql_server_cdc.py` | SQL Server (on-prem) | CDC via Debezium/SHIR | Schema evolution handling |
| 02 | `azure_sql_change_feed.py` | Azure SQL Database | Native Change Feed | Low-latency cloud CDC |
| 03 | `cosmos_db_change_feed.py` | Cosmos DB | Change Feed Processor | Multi-partition processing |
| 04 | `ibm_db2_cdc.py` | IBM DB2 | JDBC + CDC tables | Legacy mainframe integration |
| 05 | `oracle_cdc.py` | Oracle | LogMiner/GoldenGate | Enterprise DB streaming |
| 06 | `kafka_connector.py` | Apache Kafka | Kafka Connect + Eventstreams | Topic-based ingestion |
| 07 | `iot_hub_ingestion.py` | Azure IoT Hub | Device-to-cloud messages | Telemetry routing |
| 08 | `slot_machine_iot_simulator.py` | Custom IoT Sim | SAS protocol simulation | 50-500 events/sec |

### 4.3 Event Processing Patterns
- Windowed aggregations (tumbling, hopping, sliding) in KQL
- Complex Event Processing (CEP) for multi-event correlation
- Late-arriving event handling with watermarks
- Event deduplication strategies
- Multi-source event correlation (join streams from different sources)
- Dead letter queues for failed events

---

## 5. Video/Security Analytics Specifications

### 5.1 Video Analytics Pipeline

```
Camera Feed → Azure IoT Edge → AI Model → Metadata → Fabric Lakehouse
                  │                │              │
                  │          ┌─────┴─────┐   ┌───┴────┐
                  │          │ YOLO/      │   │ Delta  │
                  │          │ DeepSORT   │   │ Lake   │
                  │          │ OpenCV     │   │ Tables │
                  │          └───────────┘   └────────┘
```

| Domain | Bronze Table | Silver Table | Gold Table |
|--------|-------------|--------------|------------|
| Video Events | `bronze_video_events` | `silver_video_enriched` | `gold_video_dashboard` |
| Object Detection | `bronze_detections` | `silver_detections_classified` | `gold_detection_analytics` |
| People Tracking | `bronze_person_tracks` | `silver_tracks_correlated` | `gold_movement_patterns` |

**Sample Datasets:**
- UCF Crime Dataset (video classification training)
- VIRAT Video Dataset (surveillance video activities)
- MOT Challenge (multi-object tracking benchmarks)
- Synthetic video metadata generation (for demo without actual video)

### 5.2 People Movement Analytics
- Foot traffic counting and trending
- Heat map generation from coordinate data
- Dwell time analysis by zone
- Queue detection and wait time estimation
- Casino floor movement patterns (high-value player tracking)
- Wi-Fi/BLE beacon triangulation simulation

### 5.3 Geolocation Analytics & ArcGIS
- GPS coordinate processing in PySpark
- H3 hexagonal spatial indexing
- Geofencing with point-in-polygon
- Distance and proximity calculations
- Spatial joins and overlay analysis
- ArcGIS GeoAnalytics Engine for Spark (or Apache Sedona as OSS alternative)
- Integration with ArcGIS Living Atlas
- US Census TIGER/Line shapefiles
- OpenStreetMap data processing

---

## 6. Feature Inventory (Autonomous Harness)

### Category Breakdown

| Category | Feature Count | Description |
|----------|--------------|-------------|
| Federal Agency READMEs | 5 | Planning docs for USDA, SBA, NOAA, EPA, DOI |
| Federal Data Generators | 5 | Python generators for agency data |
| Federal JSON Schemas | 9 | Data schemas for agency domains |
| Federal Unit Tests | 5 | Tests for agency generators |
| Open Dataset Configs | 1 | Dataset registry YAML |
| Migration Tutorials | 2 | Snowflake, DB2 tutorials |
| Migration Enhancement | 1 | Enhance existing Teradata tutorial |
| Streaming Notebooks | 8 | Multi-source CDC/streaming notebooks |
| Streaming Schemas | 3 | CDC, IoT, Kafka schemas |
| Streaming Generator | 2 | Multi-source + IoT simulators |
| Streaming Tests | 2 | Tests for streaming generators |
| Streaming Tutorial | 1 | Multi-source RTI tutorial |
| Video Analytics | 3 | Tutorial + generator + schema |
| People Movement | 3 | Tutorial + generator + schema |
| Geolocation | 3 | Tutorial + generator + schema |
| Analytics Tests | 3 | Tests for analytics generators |
| Tribal Healthcare Expansion | 7 | Complete stubbed Phase 2 |
| DOT/FAA Expansion | 7 | Complete stubbed Phase 3 |
| Future Expansions README | 1 | Updated main README |
| Streaming Source Config | 1 | Source connector YAML |
| **TOTAL** | **71** | |

---

## 7. Open Dataset Registry

### Real-Time Capable Datasets
| Agency | Dataset | API | Format | Update Freq |
|--------|---------|-----|--------|-------------|
| NOAA | Weather Observations | weather.gov API | JSON | Hourly |
| EPA | AirNow AQI | AirNow API | JSON | Hourly |
| USGS | Earthquakes | earthquake.usgs.gov | GeoJSON | Real-time |
| USGS | Water Data | waterservices.usgs.gov | JSON/CSV | 15-min |

### Bulk Download Datasets
| Agency | Dataset | URL | Format | Size |
|--------|---------|-----|--------|------|
| USDA | NASS QuickStats | quickstats.nass.usda.gov | CSV/API | ~50GB total |
| SBA | PPP Loan Data | data.sba.gov | CSV | ~10GB |
| NOAA | Storm Events | ncdc.noaa.gov/stormevents | CSV | ~2GB |
| EPA | TRI Data | epa.gov/tri | CSV | ~5GB |
| DOI | USGS National Map | nationalmap.gov | GeoJSON/SHP | Varies |
| Census | TIGER/Line | census.gov/geo | SHP | ~50GB |

---

## 8. Implementation Priority

### Wave 1: Foundation (Federal Agencies)
1. Federal agency README planning docs (5 files)
2. Open dataset registry YAML
3. Federal data generators (5 generators)
4. Federal JSON schemas (9 schemas)
5. Federal unit tests (5 test files)

### Wave 2: Migration & Streaming
6. Snowflake migration tutorial
7. IBM DB2 source tutorial
8. Teradata tutorial enhancement
9. Streaming notebooks (8 notebooks)
10. Multi-source streaming tutorial
11. Streaming generators (2 generators)
12. Streaming schemas (3 schemas)
13. Streaming tests (2 test files)
14. Source connector config YAML

### Wave 3: Analytics & Visualization
15. Video security analytics tutorial + generator + schema
16. People movement analytics tutorial + generator + schema
17. Geolocation analytics tutorial + generator + schema
18. Analytics unit tests (3 test files)

### Wave 4: Complete Expansions
19. Tribal healthcare full implementation (7 files)
20. Federal DOT/FAA full implementation (7 files)
21. Updated future-expansions README

### Wave 5: Final Regression
22. Cross-feature integration testing
23. Documentation completeness review
24. End-to-end demo walkthrough verification

---

## 9. Compliance & Governance

### Federal Data Governance
- **FOIA**: All datasets used are publicly available
- **Privacy Act**: No PII in federal datasets (or properly anonymized)
- **FedRAMP**: Architecture supports GCC/GCC-High deployment
- **FISMA**: Security controls documentation
- **NIST 800-53**: Control mapping for federal systems

### Data Quality Standards
- Schema validation at ingestion (all bronze tables)
- Completeness checks (null percentage thresholds)
- Referential integrity (cross-domain joins)
- Freshness monitoring (data arrival SLAs)
- Business rule validation (domain-specific)

---

*Generated: 2026-03-11*
*Version: 1.0.0*
*Status: PLANNING - READY FOR HARNESS EXECUTION*
