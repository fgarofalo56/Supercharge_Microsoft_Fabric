# Phase 7 Deep Research Findings Summary
# Compiled from 3 parallel research agents - 2026-03-11

## Critical Discoveries for Implementation

### 1. ArcGIS GeoAnalytics - Pre-Installed in Fabric
- **ArcGIS GeoAnalytics Engine is GA and PRE-INSTALLED in Fabric Spark Runtime 1.3**
- No separate installation required - just needs Esri license via Microsoft Marketplace
- Provides ~20 analysis tools and 160+ SQL functions
- Includes hot spot analysis, spatial joins, movement tracking, buffer operations
- **Apache Sedona** documented as open-source alternative (Apache 2.0 license)
- FindDwellLocations tool available natively for dwell time analysis

### 2. Snowflake Migration - 3 Distinct Paths
- **(a) Snowflake Mirroring**: Near-real-time zero-ETL replication (up to 1,000 tables, free Fabric compute)
- **(b) Fabric Data Pipelines/Copy Job**: Snowflake connector with full load, incremental, CDC, CDC Merge
- **(c) Iceberg table interoperability**: Zero-copy bidirectional access
- Snowpipe equivalent = Eventstreams + Copy Job CDC
- Stored procedures require T-SQL rewrite or dbt conversion

### 3. IBM DB2 - No Native CDC in Eventstreams
- Native DB2 connector in Fabric Data Factory supports z/OS, DB2 for i, and LUW
- **On-premises data gateway is ALWAYS required**
- **No native CDC streaming connector** in Eventstreams
- Real-time CDC path: **Debezium DB2 Connector → Kafka → Fabric Eventstream Kafka source** (LUW only)
- DB2 z/OS requires IBM IIDR or IBM Data Gate as intermediary

### 4. Oracle - GoldenGate has Native OneLake Handler
- Official Microsoft tutorial for **Oracle GoldenGate → Kafka Handler → Eventstream Kafka endpoint**
- OGG Big Data 23c+ has a **native OneLake Event Handler** for direct replication to Fabric Lakehouse
- This is a significant finding for enterprise Oracle customers

### 5. Best Real-Time Streaming Sources (No Auth Required)
1. **USGS Earthquake GeoJSON Feeds** - Updates every 1-5 min, perfect for KQL demos
2. **NWS Weather API (api.weather.gov)** - No key needed, User-Agent header only
3. **NOAA Tides & Currents** - 6-minute intervals, no key
4. **NOAA NDBC Buoy Data** - Hourly, direct HTTP download
5. **USGS Water Services (Instantaneous)** - 15-60 min updates, no key (rate limited)
6. **EPA AirNow** - Hourly AQI (requires free API key)

### 6. Best Batch Datasets for Medallion Architecture
1. **SBA PPP Loan Data** - 11M+ records, rich demographics, direct CSV download
2. **NOAA GHCN-Daily** - Billions of climate observations
3. **EPA TRI** - 35+ years, 21K facilities, annual CSVs
4. **NOAA Storm Events** - 75+ years, 3 related CSV tables/year
5. **USDA QuickStats API** - Millions of agricultural records

### 7. Video Analytics Architecture
- Azure AI Video Indexer with real-time preview (edge via Arc/Kubernetes + NVIDIA GPU)
- Microsoft published official Fabric integration pattern:
  `Blob Storage → ML frame extraction → Custom Vision/Video Indexer → Logic Apps → Fabric DW → Power BI`
- People counting built into Video Indexer
- YOLO + DeepSORT for custom tracking

### 8. IoT Simulator Insights
- Azure IoT Telemetry Simulator (Microsoft official) supports custom templates, scales via Docker/K8s
- SAS protocol (IGT) event codes documented
- Throughput sizing:
  - Small demo: 100 machines → ~1.7M events/day
  - Full casino: 3,000 machines → ~52M events/day

### 9. Eventstream Processing Capabilities
- **5 window types**: Tumbling, Hopping, Sliding, Session, Snapshot
- `Windows()` function supports simultaneous multi-window computation
- CEP via `series_decompose_anomalies()` in KQL
- Sequential pattern matching via KQL `scan` operator
- Late events: `TIMESTAMP BY` watermarks + dual time columns

### 10. Teradata Migration Tools
- **Fabric Migration Assistant** (built-in, AI-powered DACPAC import)
- **dbt adapter** for Fabric allows converting Teradata dbt projects
- Open-source: `microsoft/fabric-migrationfactory` and `microsoft/fabric-migration` on GitHub
- BTEQ → COPY INTO, FastLoad → Data Pipeline, TPT → Copy Job

## Research Reference Documents Created
- `docs/MIGRATION_AND_RTI_RESEARCH.md` - Full migration and RTI findings (~700 lines)
- `future-expansions/video-security-geospatial-iot-research.md` - Video/GeoSpatial/IoT research (~700 lines)

## Impact on Implementation

### Changes to Coding Prompts:
1. Tutorial 24 (Snowflake) should cover all 3 migration paths, not just connector
2. Tutorial 25 (DB2) must emphasize gateway requirement and Debezium bridge for CDC
3. Tutorial 26 (Multi-Source) should highlight no-auth streaming sources for easy demos
4. Tutorial 29 (Geo) should use pre-installed ArcGIS in Fabric Runtime 1.3
5. Streaming notebook 05 (Oracle) should include GoldenGate OneLake Handler path
6. IoT simulator should use Azure IoT Telemetry Simulator template patterns
