# Research: Video/Security Analytics, ArcGIS Integration, and IoT Simulation for Microsoft Fabric

**Research Date:** 2026-03-11
**Scope:** Video analytics pipelines, people movement analytics, geolocation analytics, ArcGIS integration, open geospatial datasets, and mocked IoT/slot machine event stream creation
**Target Platform:** Microsoft Fabric (F64 SKU) - Casino/Gaming Industry POC

---

## Part 1: Video/Security Analytics in Microsoft Fabric

### 1. Video Analytics Pipeline

#### 1.1 Azure AI Video Indexer (Primary Microsoft Service)

**Official Documentation:**
- Overview: https://learn.microsoft.com/azure/azure-video-indexer/video-indexer-overview
- Real-Time Analysis (Preview): https://learn.microsoft.com/azure/azure-video-indexer/live-analysis
- REST API: https://learn.microsoft.com/rest/api/videoindexer/
- Logic Apps Integration: https://learn.microsoft.com/azure/azure-video-indexer/logic-apps-connector-arm-accounts

**Key Capabilities:**
- People and vehicle detection with bounding boxes and real-time counting
- Custom insights using open vocabulary (OV) technology -- define custom object detection without coding or training
- Object tracking with unique IDs (tracked via visual embeddings, not biometrics)
- Event summaries for up to 6-hour segments of recorded footage
- Anomaly detection with "Focus on" prompts for specific event types (e.g., "violent behavior")
- Real-time streaming analysis via Azure AI Video Indexer enabled by Arc (Kubernetes-based edge deployment)

**Real-Time Analysis Hardware Requirements:**
- Minimum: 1 VM with 32 cores, 64 GB RAM, 200 GB storage (CPU only) or 1 VM with 16 cores, 64 GB RAM + NVIDIA A2 GPU
- GPU support: NVIDIA A2, A10, V100, A100, H100
- Camera capacity per GPU: A100 supports up to 16 cameras (insights only), H100 up to 16 cameras
- Preview period: No extra cost for real-time video analysis

**Limitations to Consider:**
- Only static cameras supported (no PTZ)
- Frame rate must be 28-32 FPS
- Minimum detection size: 35x35 pixels
- Fisheye lenses not supported
- Maximum 10 people per frame recommended for optimal accuracy

**Integration with Fabric:**
Microsoft published an official architecture pattern: "Automate video analysis by using Azure Machine Learning and Azure Vision in Foundry Tools" (https://learn.microsoft.com/azure/architecture/ai-ml/architecture/analyze-video-computer-vision-machine-learning). Two architecture options exist:

**Architecture Option A: Custom Vision + Frame Extraction**
1. Video files uploaded to Blob Storage
2. Azure ML pipeline extracts frames using FFmpeg
3. Frames stored in Data Lake Storage
4. Logic Apps calls Custom Vision or Computer Vision API for analysis
5. JSON results parsed and stored in Microsoft Fabric Data Warehouse
6. Power BI visualizes results

**Architecture Option B: Video Indexer (Recommended for common objects)**
1. Video files uploaded to Blob Storage
2. Logic Apps monitors and triggers Video Indexer API
3. Video Indexer indexes content, runs natural language searches
4. JSON results parsed by Logic Apps
5. Results stored in Fabric SQL database
6. Power BI visualizes results

**Important:** Azure Custom Vision is being retired (support until 9/25/2028). Microsoft recommends migrating to Azure ML AutoML for custom model training or using Foundry Models for generative AI-based solutions.

#### 1.2 Computer Vision Models for Security Camera Feeds

**Azure AI Services Options:**
- **Azure Vision in Foundry Tools**: Basic OCR, image analysis, motion detection
- **Azure AI Custom Vision**: Specific object detection (weapons, anomalies) -- retiring, migrate to AutoML
- **Azure AI Face**: Face detection, liveness check, identity verification (Limited Access features require registration)
- **Azure OpenAI (GPT-4o/4V)**: Broad image analysis using multimodal models
- **Azure Content Understanding**: Custom classification workflows for unstructured data (public preview)

**Open-Source Computer Vision Stack:**

| Tool | Purpose | GitHub | License |
|------|---------|--------|---------|
| YOLO (v8/v11/v12) | Real-time object detection | https://github.com/ultralytics/ultralytics | AGPL-3.0 |
| OpenCV | Image/video processing library | https://github.com/opencv/opencv | Apache 2.0 |
| DeepSORT | Multi-object tracking with deep features | https://github.com/nwojke/deep_sort | GPL-2.0 |
| ByteTrack | High-performance multi-object tracking | https://github.com/ifzhang/ByteTrack | MIT |
| Ultralytics Trackers | Built-in ByteTrack/BoTSORT in YOLO | https://docs.ultralytics.com/modes/track/ | AGPL-3.0 |

**YOLO + DeepSORT Pipeline for Casino Security:**
- YOLO detects objects (people, suspicious items) in each frame
- DeepSORT assigns persistent IDs and tracks objects across frames
- Combination enables: people counting, trajectory tracking, dwell time measurement
- Example open-source project: https://github.com/brijeshhere/OpenCV_YOLO11_DeepSort_Customer_time_Store (real-time customer tracking with dwell time using YOLO v11m + DeepSort)

#### 1.3 Architecture: Camera to Fabric Lakehouse

**Recommended End-to-End Architecture:**
```
Security Cameras (RTSP/HTTP)
    |
    v
Azure IoT Edge (edge inference with YOLO/Custom Vision containers)
    |
    v
Azure IoT Hub (receives inference results + metadata)
    |
    v
Fabric Eventstream (Azure IoT Hub source connector)
    |
    v
Fabric Eventhouse / KQL Database (real-time analytics)
    |                    |
    v                    v
Fabric Lakehouse     Real-Time Dashboard
(Delta Lake)         (KQL-based)
    |
    v
Power BI Reports
```

**Azure IoT Edge Role:**
- Runs containerized AI models (YOLO, Custom Vision ONNX exports) at the edge
- Reduces bandwidth by sending only inference results (not raw video)
- Supports GPU-accelerated inference on edge devices
- Documentation: https://learn.microsoft.com/azure/iot-edge/about-iot-edge

**Fabric Integration Points:**
- Eventstreams natively support Azure IoT Hub as a source (JSON, Avro, CSV formats)
- Real-Time hub provides centralized discovery of all streaming data
- Eventhouse provides KQL-based real-time analytics on streaming events
- Lakehouse stores Delta Lake tables for historical analysis

#### 1.4 Sample Video Datasets for Demos

| Dataset | Description | Size | URL |
|---------|-------------|------|-----|
| **UCF-Crime** | 1,900 real-world surveillance videos with 13 anomaly categories (fighting, robbery, shoplifting, etc.) | ~128 hours | https://www.crcv.ucf.edu/projects/real-world/ |
| **VIRAT** | Surveillance video dataset with activity annotations (events in parking lots, buildings) | Multiple scenes | https://www.crcv.ucf.edu/research/data-sets/virat/ |
| **ShanghaiTech Campus** | 13 scenes with 130 abnormal events (wrong direction walking, loitering, bicycling) | 437 videos | https://svip-lab.github.io/dataset/campus_dataset.html |
| **UCF-Crime-DVS** | Event-based version using Dynamic Vision Sensors for anomaly detection | Novel DVS format | https://arxiv.org/html/2503.12905v1 |
| **TinyVIRAT** | Low-resolution action recognition from surveillance cameras | Reduced resolution | https://www.crcv.ucf.edu/research/projects/tinyvirat-low-resolution-video-action-recognition/ |
| **UCA (UCF Crime Annotation)** | Detailed annotations on UCF-Crime dataset | Annotations layer | https://www.kaggle.com/datasets/vigneshwar472/ucaucf-crime-annotation-dataset |
| **MOT17** | Multi-object tracking benchmark with pedestrian tracking | Multiple sequences | https://motchallenge.net/data/MOT17/ |
| **COCO** | Common Objects in Context -- general object detection/segmentation | 330K images | https://cocodataset.org/ |

**Recommended for Casino POC:**
- UCF-Crime for anomaly detection demos (contains real surveillance footage with labeled anomalies)
- ShanghaiTech for indoor movement pattern analysis
- VIRAT for parking lot / building entrance monitoring scenarios
- COCO for general object detection model benchmarking

#### 1.5 Storing Video Analytics Metadata in Delta Lake

**Recommended Delta Lake Table Schemas:**

**Table: video_detection_events (Bronze)**
```
- event_id: STRING (UUID)
- camera_id: STRING
- timestamp: TIMESTAMP
- frame_number: LONG
- detection_type: STRING (person, vehicle, weapon, bag, etc.)
- confidence_score: DOUBLE
- bounding_box_x: INT
- bounding_box_y: INT
- bounding_box_width: INT
- bounding_box_height: INT
- tracking_id: STRING (DeepSORT/ByteTrack assigned ID)
- raw_inference_json: STRING (full model output)
- ingestion_timestamp: TIMESTAMP
```

**Table: video_tracking_summary (Silver)**
```
- tracking_id: STRING
- camera_id: STRING
- object_type: STRING
- first_seen: TIMESTAMP
- last_seen: TIMESTAMP
- dwell_time_seconds: INT
- trajectory_points: ARRAY<STRUCT<x: INT, y: INT, timestamp: TIMESTAMP>>
- zone_visited: ARRAY<STRING>
- average_confidence: DOUBLE
```

**Table: video_anomaly_alerts (Gold)**
```
- alert_id: STRING
- camera_id: STRING
- alert_type: STRING (weapon_detected, abandoned_bag, loitering, unusual_crowd, etc.)
- severity: STRING (low, medium, high, critical)
- timestamp: TIMESTAMP
- description: STRING
- related_tracking_ids: ARRAY<STRING>
- acknowledged: BOOLEAN
- acknowledged_by: STRING
- acknowledged_at: TIMESTAMP
```

---

### 2. People Movement Analytics

#### 2.1 Foot Traffic Analysis Patterns

**Computer Vision Approaches:**
- **People counting**: YOLO + line-crossing detection (count people crossing a virtual line)
- **Occupancy monitoring**: Frame-by-frame person count in defined zones
- **Directional flow**: Optical flow analysis combined with object tracking

**Commercial Solutions with CV Technology:**
- V-Count Ultima AI: 3D active stereo vision, up to 99.9% counting accuracy, works in zero-light conditions
- FootfallCam: Specializes in retail analytics with zone-based tracking
- Milesight People Counters: IoT-based with heat map generation

**Azure AI Video Indexer Real-Time Analysis** provides built-in people counting and tracking for live camera streams (Preview). It can monitor checkout line lengths in real time for staffing optimization.

#### 2.2 Heat Map Generation from Movement Data

**Approaches:**
1. **Video-based heat maps**: Aggregate detection coordinates over time to create density maps
   - Overlay bounding box centers on floor plan
   - Use kernel density estimation (KDE) for smooth gradients
   - Warmer colors = higher activity

2. **Sensor-based heat maps**: Wi-Fi/BLE probe request data
   - Track device MAC addresses (anonymized) across access points
   - Triangulate positions using RSSI values
   - Generate heat maps from aggregated position data

3. **ArcGIS GeoAnalytics in Fabric**: FindHotSpots tool provides statistically significant spatial clustering analysis

**Data Model for Heat Maps:**
```
- zone_id: STRING
- time_window: TIMESTAMP (e.g., 15-min intervals)
- person_count: INT
- avg_dwell_time_seconds: DOUBLE
- entry_count: INT
- exit_count: INT
- density_score: DOUBLE
```

#### 2.3 Dwell Time Analytics

**Implementation Approaches:**
1. **Camera-based**: Track objects via DeepSORT/ByteTrack, calculate time between first_seen and last_seen in a zone
2. **BLE Beacon-based**: Detect when a beacon (worn by patron or in phone) enters/exits a zone
3. **Wi-Fi probe-based**: Monitor device association/disassociation with access points

**ArcGIS GeoAnalytics FindDwellLocations Tool:**
- Natively available in Fabric Spark via `geoanalytics_fabric.tools.FindDwellLocations`
- Analyzes GPS/tracking data to find locations where entities stayed for a specified duration
- Documentation: https://developers.arcgis.com/geoanalytics-fabric/tools/find-dwell-locations/

#### 2.4 Queue Detection and Wait Time Estimation

**Approaches:**
1. **CV-based queue detection**: YOLO detects people, clustering algorithms identify queue formations, count people in queue zones
2. **Serpentine queue modeling**: Define queue geometry, count people within geometry boundaries
3. **Wait time estimation**: (queue_length / service_rate) using historical throughput data

**Azure Video Indexer** supports real-time people counting in queue zones for retail scenarios.

#### 2.5 Casino Floor Movement Patterns (High-Value Player Tracking)

**Architecture for Casino Use Case:**
- Deploy cameras at entry/exit points, gaming floor zones, high-limit areas
- Use tracking (non-biometric, visual embedding-based) to follow patron journeys
- Correlate with loyalty card swipe data from slot machines/tables
- Generate patron journey maps and dwell-time analysis per gaming zone

**Compliance Considerations:**
- Must comply with gaming commission regulations on surveillance
- Player tracking must use non-biometric methods (position/appearance embeddings, not facial recognition)
- High-value player tracking often correlates with player card data rather than visual surveillance

#### 2.6 Wi-Fi/Bluetooth Beacon Triangulation Data

**Wi-Fi Based Indoor Positioning:**
- Passive monitoring of Wi-Fi probe requests from patron devices
- RSSI (Received Signal Strength Indicator) triangulation across multiple access points
- Accuracy: +/- 3-5 meters indoors
- Privacy: Must anonymize/hash MAC addresses

**Bluetooth Low Energy (BLE) Beacon Positioning:**
- BLE beacons placed throughout the casino floor
- Accuracy: +/- 1-3 meters
- Approaches: proximity detection (which beacon is closest) or trilateration (3+ beacons)
- Battery-powered beacons last 2-5 years
- Supported protocols: iBeacon (Apple), Eddystone (Google)

**Integration with Fabric:**
- Beacon/Wi-Fi data flows via Azure IoT Hub or Event Hubs
- Fabric Eventstream ingests positioning events
- KQL queries analyze movement patterns in real time
- ArcGIS GeoAnalytics in Fabric for spatial analysis of movement tracks

**Data Generation Approaches for Demo:**
- Generate synthetic Wi-Fi probe events with randomized MAC hashes, RSSI values, and AP identifiers
- Simulate BLE beacon detection events with beacon IDs, proximity zones, and timestamps
- Model realistic casino floor layouts with gaming zones, restaurants, hotel lobbies

---

### 3. Geolocation Analytics

#### 3.1 GPS/Coordinate Data Processing in PySpark

**Native PySpark Geospatial Functions:**
- PySpark includes ST geospatial functions (available in Databricks and Fabric Runtime)
- Functions include: `st_point()`, `st_distance()`, `st_contains()`, `st_intersects()`, `st_buffer()`
- Reference: https://learn.microsoft.com/azure/databricks/pyspark/reference/functions/#st-geospatial-functions

**Haversine Distance Calculation in PySpark:**
- Use `asin`, `cos`, `sin`, `sqrt`, `toRadians` from `pyspark.sql.functions`
- Applies great-circle distance formula for lat/lon coordinate pairs

**ArcGIS GeoAnalytics for Fabric:**
- 160+ spatial SQL functions available directly in Fabric Spark notebooks
- `ST_Distance()`, `ST_DWithin()`, `ST_Contains()`, `ST_Intersects()`, `ST_Buffer()`, `ST_Union()`
- Automatic spatial indexing for optimized joins
- Developer docs: https://developers.arcgis.com/geoanalytics-fabric/sql-functions/

#### 3.2 Geofencing Implementation

**Approaches in Fabric:**
1. **ArcGIS GeoAnalytics**: Use `ST_Contains()` to check if a point is within a polygon (geofence)
2. **Custom PySpark UDF**: Define polygon boundaries, use point-in-polygon algorithm
3. **Fabric Activator**: Set up alerts when geofence events are detected in real-time streams
4. **Azure Maps Geofencing API**: REST API for geofence enter/exit events (can feed into Eventstreams)

**Casino Geofencing Use Cases:**
- Property boundary monitoring
- Gaming floor zone boundaries (slots, table games, high-limit, sportsbook)
- Restricted area alerts (back-of-house, cash cage proximity)
- Marketing zone triggers (proximity to restaurants, shows, promotions)

#### 3.3 H3 Hexagonal Indexing for Spatial Analytics

**Overview:**
- H3 is Uber's open-source hierarchical hexagonal geospatial indexing system
- Converts lat/lon coordinates to hexagonal cell indexes at 16 resolution levels
- Hexagons provide uniform adjacency (6 neighbors each), better than square grids for spatial analysis
- GitHub: https://github.com/uber/h3
- Documentation: https://h3geo.org/

**PySpark Integration:**
- `h3-pyspark` library: https://pypi.org/project/h3-pyspark/
  - Provides PySpark UDFs for H3 operations
  - Functions: `geo_to_h3()`, `h3_to_geo()`, `h3_to_geo_boundary()`, `k_ring()`, `hex_ring()`
  - Install: `pip install h3-pyspark`
- Amazon's `h3-indexer`: https://github.com/amazon-science/h3-indexer
  - Open-source package for indexing geospatial data using PySpark + Apache Sedona + H3

**Casino Use Cases for H3:**
- Aggregate player activity by hexagonal zones on casino floor
- Create consistent spatial bins for heat map generation
- Efficient spatial joins between player location data and property zones
- Resolution 11 (~24m edge) or 12 (~9m edge) recommended for indoor casino floor analysis

#### 3.4 Integration with Mapping Services

**ArcGIS for Power BI:**
- Built-in Power BI visual for mapping
- Supports geocoding, clustering, drive-time analysis
- Available with ArcGIS for Power BI subscription
- Documentation: https://doc.arcgis.com/en/microsoft-365/latest/power-bi/get-started-with-arcgis-for-power-bi.htm

**ArcGIS Maps Workload for Fabric (Preview):**
- Announced November 2025 at Ignite
- Visualize, analyze, and share geospatial insights with OneLake integration
- Spark-based processing, Power BI embedding, smart mapping features
- Create maps directly within Fabric: https://learn.microsoft.com/fabric/real-time-intelligence/map/create-map

**Azure Maps:**
- REST APIs for geocoding, routing, rendering, traffic, weather
- Can feed data into Fabric via Eventstreams or Data Factory

---

## Part 2: ArcGIS Integration with Microsoft Fabric

### 4. ArcGIS GeoAnalytics for Microsoft Fabric

#### 4.1 Official Documentation and Status

**Status:** Generally Available (GA)
**Documentation:**
- Microsoft Learn: https://learn.microsoft.com/fabric/data-engineering/spark-arcgis-geoanalytics
- Esri Developer Docs: https://developers.arcgis.com/geoanalytics-fabric/
- Esri Community: https://community.esri.com/t5/arcgis-geoanalytics-for-microsoft-fabric/ct-p/arcgis-geoanalytics-for-microsoft-fabric
- Microsoft Marketplace: https://marketplace.microsoft.com/en-us/product/saas/esri.arcgis-fabric

**Key Facts:**
- Pre-installed in Fabric Spark Runtime 1.3 (no separate installation needed)
- Enabled by tenant admin in Settings > Admin Portal > Tenant settings > "ArcGIS GeoAnalytics for Fabric Runtime"
- Can also be enabled/disabled at capacity level

#### 4.2 Capabilities

**160+ Spatial SQL Functions** including:
- Geometry creation: `ST_Point()`, `ST_Polygon()`, `ST_GeomFromGeoJSON()`, `ST_GeomFromText()`
- Spatial relationships: `ST_Contains()`, `ST_Intersects()`, `ST_Within()`, `ST_Crosses()`
- Measurements: `ST_Distance()`, `ST_Area()`, `ST_Length()`, `ST_DWithin()`
- Transformations: `ST_Buffer()`, `ST_Union()`, `ST_Intersection()`, `ST_Difference()`
- Format conversions: `ST_AsText()`, `ST_AsBinary()`, `ST_AsGeoJSON()`

**~20 Analysis Tools:**
| Tool | Description |
|------|-------------|
| FindHotSpots | Statistically significant spatial clusters |
| FindPointClusters | Spatial outlier detection |
| AggregatePoints | Aggregate point data into areas |
| NearestNeighbors | Find closest features |
| GroupByProximity | Group features by spatial proximity |
| FindDwellLocations | Identify stops in tracking data |
| CalculateMotionStatistics | Speed, acceleration from GPS tracks |
| DetectIncidents | Anomaly detection in spatial data |
| FindSimilarLocations | Location similarity analysis |
| SpatialJoin | Enrich data based on spatial relationships |
| Overlay | Combine spatial layers |
| Clip | Extract features within boundaries |
| Buffer | Create proximity zones |

**Track Functions (TRK_):**
- Trajectory reconstruction and analysis
- Split-by-distance, dwell identification, speed calculations
- Co-traveler detection
- Documentation: https://developers.arcgis.com/geoanalytics-fabric/trk-functions/

#### 4.3 Installation and Configuration

**No separate installation required.** The library is natively integrated into Fabric Spark runtime. To use it:

1. Tenant admin enables in Settings > Admin Portal > "ArcGIS GeoAnalytics for Fabric Runtime"
2. In a Fabric Spark notebook, import and authorize:
```python
# Authorization with API key (example from docs)
from geoanalytics_fabric import GeoAnalytics
GeoAnalytics.auth(username="your_username", password="your_password")
# OR
GeoAnalytics.auth(api_key="your_api_key")
```
3. Start using spatial functions and tools in Spark SQL or PySpark

**Important Considerations:**
- Requires valid Esri license (bring your own license model)
- When writing to Delta, geometries are converted to well-known binary (WKB) format
- When reading Delta tables, use `ST_GeomFromBinary()` to convert WKB back to geometry
- Not supported when Outbound Access Protection is enabled (requires calls to Esri services)

#### 4.4 ArcGIS Living Atlas Datasets

The ArcGIS Living Atlas of the World (https://livingatlas.arcgis.com/) provides curated geospatial datasets that can be read directly into Fabric Spark DataFrames:

```python
# Example: Read US States boundaries
myFS = "https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/USA_States_Generalized_Boundaries/FeatureServer/0"
df = spark.read.format('feature-service').load(myFS)
```

**Relevant Living Atlas Layers:**
- US States and County boundaries
- US Census demographics (ACS data)
- Points of interest
- Transportation networks
- Land use/land cover
- Natural hazards

#### 4.5 Licensing Requirements for POC/Demo

**Current Status:**
- GA licensing requires a paid Esri subscription through Microsoft Marketplace
- Subscription available at: https://marketplace.microsoft.com/en-us/product/saas/esri.arcgis-fabric
- Renewal options: manual or auto-renewal every 30 days
- Contact Esri for POC/trial licensing: they offer flexible pricing and may provide evaluation licenses

**For POC without ArcGIS License, consider:**
- Apache Sedona (open-source alternative -- see section 4.6)
- Native PySpark spatial functions
- H3 library for hexagonal indexing

#### 4.6 Alternative: Apache Sedona (Open-Source)

**Overview:**
- Apache Sedona (formerly GeoSpark) is an open-source distributed geospatial computing engine
- Extends Apache Spark with spatial data types, indexes, and operations
- GitHub: https://github.com/apache/sedona
- Documentation: https://sedona.apache.org/
- License: Apache 2.0

**Key Capabilities:**
- Spatial RDD (Resilient Distributed Datasets) and DataFrame APIs
- Spatial SQL support: ST_Point, ST_Contains, ST_Distance, ST_Buffer, etc.
- Spatial indexing: R-Tree and Quad-Tree
- Supports: Shapefile, GeoJSON, GeoParquet, WKT, WKB formats
- APIs in: Java, Scala, Python (PySedona), R
- Works with Delta Lake and Delta tables

**Comparison with ArcGIS GeoAnalytics:**

| Feature | ArcGIS GeoAnalytics | Apache Sedona |
|---------|-------------------|---------------|
| License | Commercial (Esri) | Open Source (Apache 2.0) |
| Installation | Pre-installed in Fabric | Requires manual install in Fabric |
| Functions | 160+ | ~100+ |
| Spatial indexing | Automatic | Manual (R-Tree/Quad-Tree) |
| Track analysis | Built-in TRK functions | Custom implementation |
| Visualization | Built-in plotting | Requires additional libraries |
| Support | Esri + Microsoft | Community |
| Living Atlas | Direct access | No direct access |
| Fabric integration | Native | Requires library management |

**Using Sedona in Fabric:**
- Install via `%pip install apache-sedona` in notebook or via Spark environment configuration
- May require additional JAR files for full functionality
- Reference: https://sedona.apache.org/latest/ and https://delta.io/blog/apache-sedona/

---

### 5. Open Geospatial Datasets

#### 5.1 OpenStreetMap Data

**Source:** https://www.openstreetmap.org/
**Download:** https://download.geofabrik.de/ (daily extracts by region)
**Formats:** Shapefile (.shp), GeoPackage (.gpkg), OSM PBF (.pbf), GeoJSON
**License:** Open Database License (ODbL) -- free with attribution

**Available Layers:** Buildings, landuse, natural features, places, railways, roads, waterways
**Casino Relevance:** Hotel/casino building footprints, road networks, points of interest near properties

#### 5.2 US Census TIGER/Line Shapefiles

**Source:** https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
**2024 Files Technical Documentation:** https://www2.census.gov/geo/pdfs/maps-data/data/tiger/tgrshp2024/TGRSHP2024_TechDoc.pdf
**Data.gov Catalog:** https://catalog.data.gov/dataset/tiger-line-shapefile-current-nation-u-s-state-and-equivalent-entities
**License:** Public domain (US Government)

**Available Layers:**
- State, county, tract, block group, block boundaries
- Roads, railroads, hydrography
- Congressional districts, school districts
- ZIP code tabulation areas (ZCTAs)
- Metropolitan statistical areas

**Casino Relevance:** Property boundary context, census demographics for patron analysis, drive-time analysis base data

#### 5.3 Natural Earth Data

**Source:** https://www.naturalearthdata.com/
**Scales:** 1:10m, 1:50m, 1:110m
**License:** Public domain
**Formats:** Shapefile, GeoPackage, SQLite

**Available Layers:**
- Cultural: countries, states/provinces, populated places, roads, railroads, airports, ports, urban areas
- Physical: coastlines, land, ocean, lakes, rivers, glaciated areas, reefs
- Raster: Natural Earth I (satellite-derived)

**Casino Relevance:** Good for context/basemaps, international casino property mapping, overview-level analysis

#### 5.4 USGS Elevation/Terrain Data

**Source:** https://www.usgs.gov/the-national-map-data-delivery
**Download Tool:** https://apps.nationalmap.gov/datasets/
**EarthExplorer:** https://earthexplorer.usgs.gov/ (search under "Digital Elevation")

**Available Datasets:**
| Dataset | Resolution | Coverage |
|---------|-----------|----------|
| 3DEP 1-meter DEM | 1m | US (partial) |
| 3DEP 1/3 arc-second | ~10m | US (complete) |
| SRTM 1 arc-second | ~30m | Global (56S-60N) |
| GMTED2010 | ~250m-1km | Global |

**License:** Public domain (US Government)
**Casino Relevance:** Terrain context for property mapping, flood risk assessment, 3D visualization

#### 5.5 Casino/Gaming Property Locations

**No single authoritative open dataset exists.** Approaches for obtaining casino location data:

1. **OpenStreetMap**: Query for amenity=casino or leisure=casino
   - Geofabrik extracts can be filtered
   - Overpass API for targeted queries

2. **Nevada Gaming Control Board**: Public license records with addresses (requires geocoding)
   - https://gaming.nv.gov/

3. **State gaming commission websites**: Most states publish licensed facility lists
   - New Jersey: https://www.nj.gov/oag/ge/
   - Mississippi: https://www.msgamingcommission.com/
   - Pennsylvania: https://gamingcontrolboard.pa.gov/

4. **ArcGIS Living Atlas**: Search for hospitality/entertainment layers

5. **Google Places API / Foursquare**: POI databases with casino category filters (commercial, rate-limited)

6. **Data generation approach**: For POC, create a synthetic casino property dataset with:
   - Las Vegas Strip properties (coordinates readily available)
   - Atlantic City boardwalk casinos
   - Major tribal casinos across US

#### 5.6 Public Transit Data (GTFS)

**Overview:** General Transit Feed Specification (GTFS) is the standard format for public transit schedules and geographic data.

**Sources:**
- **Transitland**: https://www.transit.land/ (aggregator of 2,500+ GTFS feeds worldwide)
- **OpenMobilityData**: https://transitfeeds.com/ (searchable GTFS feed directory)
- **MobilityData**: https://mobilitydatabase.org/ (curated directory)

**GTFS Data Contains:**
- stops.txt: Stop locations with lat/lon
- routes.txt: Transit routes
- trips.txt: Trip schedules
- shapes.txt: Route geometries
- stop_times.txt: Arrival/departure times

**Casino Relevance:**
- Analyze patron accessibility via public transit
- Model transportation options for casino properties
- Integrate with spatial analysis for service area mapping

---

## Part 3: Mocked IoT/Slot Machine Event Stream Creator

### 6. IoT Simulation Patterns

#### 6.1 Azure IoT Telemetry Simulator (Recommended for Scale Testing)

**Official Microsoft Tool:**
- GitHub: https://github.com/Azure-Samples/Iot-Telemetry-Simulator
- Docs: https://learn.microsoft.com/en-us/samples/azure-samples/iot-telemetry-simulator/azure-iot-device-telemetry-simulator/

**Key Features:**
- Supports Azure IoT Hub, Event Hubs, and Kafka
- Uses multiplexed AMQP connections (~995 devices per connection)
- Customizable telemetry templates with dynamic variables
- Variable types: random integers/doubles, sequential counters, timestamps, UUIDs, discrete value selection, random strings
- Deployment: Docker container, Azure Container Instances, Kubernetes (Helm chart)
- Scale: Thousands of simulated devices across multiple instances

**Template System Example:**
```json
{
  "Variables": [
    {"name": "coin_in", "random": true, "min": 0, "max": 500},
    {"name": "coin_out", "random": true, "min": 0, "max": 2000},
    {"name": "machine_state", "values": ["idle", "playing", "bonus", "payout", "error"]}
  ],
  "Template": "{\"device_id\": \"$.DeviceId\", \"timestamp\": \"$.Time\", \"coin_in\": $.coin_in, \"coin_out\": $.coin_out, \"state\": \"$.machine_state\"}"
}
```

#### 6.2 Azure CLI Device Simulation

**Quick testing with Azure CLI:**
```bash
az iot device simulate \
  --device-id slot-machine-001 \
  --hub-name MyIoTHub \
  --da '{"coin_in": 25, "coin_out": 0, "game_type": "slots", "denomination": 0.25}' \
  --mc 1000 \
  --mi 1
```
- `--mc`: Message count
- `--mi`: Message interval (seconds)
- Documentation: https://learn.microsoft.com/cli/azure/iot/device?view=azure-cli-latest

#### 6.3 Python Azure IoT Device SDK

**For custom event generators:**
- SDK: `pip install azure-iot-device`
- GitHub: https://github.com/Azure/azure-iot-sdk-python
- Samples: https://github.com/Azure-Samples/azure-iot-samples-python

**Key SDK Features:**
- MQTT and AMQP protocol support
- Device provisioning via DPS
- Twin properties (desired/reported)
- Direct method invocation
- File upload capability
- Connection string or X.509 certificate authentication

#### 6.4 SAS (Slot Accounting System) Protocol Simulation

**About SAS Protocol:**
- Developed by IGT (International Game Technology)
- De facto standard for casino floor communications
- Latest version: SAS 6.03 (managed by Gaming Standards Association)
- Purpose: Automate slot machine meter reporting, event logging, player tracking, bonusing, ticketing (TITO), cashless gaming (AFT)
- Reference: https://support.igt.com/apps/sas-protocol.aspx

**SAS Protocol Key Functions:**
- ROM signature verification
- Meter reading (coin-in, coin-out, jackpot, games played)
- Real-time events (door open, power on/off, reel tilt, printer jam)
- Progressive broadcast (progressive jackpot amounts)
- Tournament operations
- TITO (Ticket-In/Ticket-Out) transactions
- AFT (Advanced Funds Transfer) for cashless gaming
- Multi-denomination support

**Open-Source SAS Implementation:**
- GitHub: https://github.com/thomas-pythonas/saspy (Python SAS protocol implementation for ARM architecture)
- Contains SAS protocol frame structures and command implementations

**SAS Event Types for Simulation:**
| Event Code | Description | Frequency |
|------------|-------------|-----------|
| 0x11 | Slot door opened | Rare |
| 0x12 | Slot door closed | Rare |
| 0x17 | AC power applied | Rare |
| 0x18 | AC power lost | Rare |
| 0x51 | Handpay pending | ~1/5000 games |
| 0x52 | Handpay reset | ~1/5000 games |
| 0x7E | Game started | Every 4-8 seconds |
| 0x7F | Game ended | Every 4-8 seconds |
| 0x71 | Ticket printed | ~1/50 sessions |
| 0x72 | Ticket inserted | ~1/session |

#### 6.5 Event Schema Design for Gaming Floor IoT

**Recommended Event Schema for Slot Machine Telemetry:**

```json
{
  "event_id": "uuid-v4",
  "machine_id": "SM-FL02-A042",
  "asset_number": "12345",
  "location": {
    "casino_id": "CASINO-001",
    "floor": "main",
    "zone": "high_limit_slots",
    "section": "A",
    "position": 42,
    "coordinates": {"lat": 36.1162, "lon": -115.1745}
  },
  "timestamp": "2026-03-11T14:23:45.123Z",
  "event_type": "game_play",
  "game_data": {
    "game_id": "BUFFALO_GOLD",
    "game_type": "video_slots",
    "denomination": 0.01,
    "lines_played": 50,
    "bet_per_line": 5,
    "total_bet": 250,
    "total_win": 0,
    "credits_before": 5000,
    "credits_after": 4750
  },
  "meters": {
    "coin_in": 1250000,
    "coin_out": 1187500,
    "jackpot": 50000,
    "games_played": 45230,
    "games_won": 13569,
    "door_count": 12,
    "power_reset_count": 2
  },
  "machine_status": {
    "state": "playing",
    "door_open": false,
    "printer_ok": true,
    "bill_acceptor_ok": true,
    "communication_ok": true,
    "firmware_version": "4.2.1",
    "last_maintenance": "2026-03-01T08:00:00Z"
  },
  "player": {
    "card_inserted": true,
    "player_id": "PLY-HASH-A1B2C3",
    "tier": "gold",
    "session_start": "2026-03-11T14:00:00Z",
    "session_coin_in": 5000,
    "session_coin_out": 4750
  }
}
```

**Supporting Event Types:**

| Event Type | Description | Fields |
|-----------|-------------|--------|
| `game_play` | Individual game round | bet, win, game_id, denomination |
| `meter_report` | Periodic meter snapshot | coin_in, coin_out, games_played, jackpot |
| `machine_alert` | Status change alert | alert_type, severity, description |
| `player_session` | Player card in/out | player_id, tier, session_start/end |
| `financial_event` | Bill insert, ticket print/redeem | amount, type, ticket_number |
| `jackpot_event` | Jackpot hit | amount, type (hand-pay/ticket), game_id |
| `maintenance_event` | Door open, power cycle, error | event_code, technician_id |

#### 6.6 Throughput Considerations (50-500 Events/Second)

**Sizing for Casino Floor Simulation:**
- Typical casino: 2,000-4,000 slot machines
- Average game duration: 4-8 seconds per spin
- Events per machine: ~0.2 events/second (game play) + periodic meters
- Total throughput at 3,000 machines: ~600-750 events/second at peak

**Azure IoT Hub Tiers for Gaming IoT:**
| Tier | Messages/Day | Burst Rate | Recommended For |
|------|-------------|------------|----------------|
| S1 | 400,000 | 100 msg/sec | Small casino (<500 machines) |
| S2 | 6,000,000 | 120 msg/sec | Medium casino (<2000 machines) |
| S3 | 300,000,000 | 6,000 msg/sec | Large casino or multi-property |

**Alternative: Direct Event Hub Ingestion:**
- Event Hubs supports 1 MB/sec per throughput unit (TU)
- Auto-inflate to 20 TUs
- Fabric Eventstreams can directly consume from Event Hubs
- More cost-effective for high-throughput scenarios without device management

**Fabric Eventstream Throughput:**
- Supports Azure IoT Hub, Azure Event Hubs, Apache Kafka as sources
- Event processing capabilities for filtering, transformation, windowed aggregations
- Routes to Eventhouse (KQL Database), Lakehouse (Delta Lake), or both

#### 6.7 MQTT Simulator Tools

**Open-Source MQTT Simulators:**

| Tool | Description | URL |
|------|-------------|-----|
| mqtt-simulator (Python) | Lightweight, JSON-config based | https://github.com/DamascenoRafael/mqtt-simulator |
| Bevywise IoT Simulator | Python-extensible with custom algorithms | https://www.bevywise.com/iot-simulator/ |
| MIMIC MQTT Simulator | Scalable, customizable, commercial | https://www.gambitcomm.com/site/mqttsimulator.php |
| mqttgen.py | Simple Python MQTT generator script | GitHub Gist |

**Azure IoT Hub MQTT Support:**
- IoT Hub supports MQTT v3.1.1 natively
- Devices can publish to `devices/{device_id}/messages/events/`
- Fabric Eventstreams support MQTT v3.1/v3.1.1 sources directly (preview)
- Azure IoT Operations (preview) supports MQTT-to-Fabric routing

#### 6.8 Recommended Implementation Approach for POC

**Architecture for Slot Machine Event Stream Demo:**
```
Custom Python Generator (gaming events)
    |
    +--> Azure IoT Hub (device simulation via SDK)
    |        |
    |        v
    |    Fabric Eventstream (IoT Hub source)
    |        |
    |        +--> Eventhouse/KQL DB (real-time dashboards)
    |        |
    |        +--> Lakehouse (Delta Lake for historical analysis)
    |
    +--> Event Hub (alternative: direct high-throughput ingestion)
             |
             v
         Fabric Eventstream (Event Hub source)
```

**Tool Selection:**
1. **For quick demos**: Azure CLI `az iot device simulate` with custom JSON payloads
2. **For scale testing**: Azure IoT Telemetry Simulator (Docker) with custom templates
3. **For realistic simulation**: Custom Python generator using `azure-iot-device` SDK
   - Model game durations with Poisson distribution (avg 5 sec between spins)
   - Model win/loss with configurable RTP (Return to Player, typically 88-96%)
   - Generate correlated events (game play -> meter update -> player session update)
   - Include realistic error/maintenance events at configurable frequencies
4. **For MQTT testing**: mqtt-simulator with Fabric Eventstream MQTT source

**Data Volume Estimates for POC:**
| Scenario | Machines | Events/Hour | Events/Day | Storage/Day (est.) |
|----------|----------|-------------|------------|-------------------|
| Small demo | 100 | 72,000 | 1.7M | ~500 MB |
| Medium POC | 1,000 | 720,000 | 17M | ~5 GB |
| Full casino | 3,000 | 2,160,000 | 52M | ~15 GB |

---

## Cross-Cutting Integration Notes

### Combining Video Analytics + Geospatial + IoT in Fabric

**Unified Casino Floor Intelligence Architecture:**
```
Layer 1: Data Sources
  - Security cameras -> Azure IoT Edge -> Video Analytics metadata
  - Slot machines -> IoT Hub -> Game/meter events
  - BLE beacons -> IoT Hub -> Patron location events
  - Wi-Fi probes -> IoT Hub -> Device proximity events

Layer 2: Ingestion (Fabric)
  - Eventstreams (IoT Hub + Event Hub sources)
  - Real-Time Hub (centralized streaming discovery)

Layer 3: Real-Time Analytics (Fabric)
  - Eventhouse / KQL Database
  - Real-Time Dashboards
  - Fabric Activator (alerts: jackpots, security events, equipment failures)

Layer 4: Historical Analytics (Fabric)
  - Lakehouse (Delta Lake)
  - ArcGIS GeoAnalytics (spatial analysis in Spark notebooks)
  - Machine Learning (anomaly detection, predictive maintenance)

Layer 5: Visualization
  - Power BI with ArcGIS for Power BI (spatial dashboards)
  - Real-Time Dashboards (KQL-based)
  - Custom web apps (embedded Power BI / Azure Maps)
```

### Key Fabric Features Used Across All Scenarios

| Feature | Video Analytics | Movement Analytics | IoT/Gaming |
|---------|----------------|-------------------|-------------|
| Eventstream | Video metadata ingestion | Location events | Machine telemetry |
| Eventhouse | Real-time anomaly detection | Real-time tracking | Real-time floor status |
| Lakehouse | Historical analysis | Heat map generation | Trend analysis |
| ArcGIS GeoAnalytics | Camera coverage analysis | Spatial clustering | Floor layout optimization |
| Power BI | Security dashboards | Movement heat maps | Gaming floor KPIs |
| Activator | Security alerts | Geofence triggers | Jackpot/error alerts |
| Data Factory | Batch video processing | Data enrichment | Historical data loads |

---

## References and Links Summary

### Microsoft Documentation
- Fabric Eventstream Overview: https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/overview
- Fabric Real-Time Hub: https://learn.microsoft.com/fabric/real-time-hub/real-time-hub-overview
- Fabric Eventhouse: https://learn.microsoft.com/fabric/real-time-intelligence/eventhouse
- Fabric + IoT Hub: https://learn.microsoft.com/fabric/real-time-hub/add-source-azure-iot-hub
- ArcGIS GeoAnalytics for Fabric: https://learn.microsoft.com/fabric/data-engineering/spark-arcgis-geoanalytics
- Video Analysis Architecture: https://learn.microsoft.com/azure/architecture/ai-ml/architecture/analyze-video-computer-vision-machine-learning
- Azure Video Indexer Real-Time: https://learn.microsoft.com/azure/azure-video-indexer/live-analysis
- Azure IoT Edge: https://learn.microsoft.com/azure/iot-edge/about-iot-edge
- IoT Edge + Custom Vision: https://learn.microsoft.com/azure/iot-edge/tutorial-deploy-custom-vision
- Footfall Detection Pattern: https://learn.microsoft.com/azure-stack/user/pattern-retail-footfall-detection
- Real-Time Intelligence Tutorial: https://learn.microsoft.com/fabric/real-time-intelligence/tutorial-introduction

### Open-Source Tools
- YOLO (Ultralytics): https://github.com/ultralytics/ultralytics
- DeepSORT: https://github.com/nwojke/deep_sort
- ByteTrack: https://github.com/ifzhang/ByteTrack
- OpenCV: https://github.com/opencv/opencv
- Apache Sedona: https://github.com/apache/sedona
- H3 Hexagonal Index: https://github.com/uber/h3
- h3-pyspark: https://pypi.org/project/h3-pyspark/
- Azure IoT Telemetry Simulator: https://github.com/Azure-Samples/Iot-Telemetry-Simulator
- SAS Protocol (Python): https://github.com/thomas-pythonas/saspy
- MQTT Simulator: https://github.com/DamascenoRafael/mqtt-simulator

### Datasets
- UCF-Crime: https://www.crcv.ucf.edu/projects/real-world/
- VIRAT: https://www.crcv.ucf.edu/research/data-sets/virat/
- ShanghaiTech: https://svip-lab.github.io/dataset/campus_dataset.html
- OpenStreetMap: https://download.geofabrik.de/
- TIGER/Line: https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
- Natural Earth: https://www.naturalearthdata.com/
- USGS Elevation: https://apps.nationalmap.gov/datasets/
- ArcGIS Living Atlas: https://livingatlas.arcgis.com/
- GTFS Transit Feeds: https://www.transit.land/
- COCO Dataset: https://cocodataset.org/

### Esri/ArcGIS
- ArcGIS GeoAnalytics Developer Docs: https://developers.arcgis.com/geoanalytics-fabric/
- ArcGIS GeoAnalytics Marketplace: https://marketplace.microsoft.com/en-us/product/saas/esri.arcgis-fabric
- ArcGIS Living Atlas: https://livingatlas.arcgis.com/
- ArcGIS for Power BI: https://doc.arcgis.com/en/microsoft-365/latest/power-bi/get-started-with-arcgis-for-power-bi.htm
