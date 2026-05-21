---
hero: assets/heroes/energy-utilities.svg
hero_alt: Natural resources — DOI lands + wildfires
type: feature
---
# Natural Resources Analytics

> Leveraging Microsoft Fabric to unify USGS earthquake monitoring, water resources data, endangered species tracking, and public lands management into a comprehensive natural resources intelligence platform.

---

## Executive Summary

The Department of the Interior (DOI) oversees the stewardship of America's natural resources through six major bureaus: the U.S. Geological Survey (USGS), Bureau of Land Management (BLM), Fish and Wildlife Service (FWS), National Park Service (NPS), Bureau of Safety and Environmental Enforcement (BSEE), and Bureau of Ocean Energy Management (BOEM). Together these agencies manage over 500 million acres of public lands, monitor 1.5 million stream gauges and seismic stations, track 2,700+ listed endangered species, and oversee energy production on federal lands and offshore waters. Each bureau operates independent data systems with different schemas, update frequencies, and access mechanisms, creating significant barriers to integrated analysis.

Microsoft Fabric provides a unified lakehouse platform that consolidates DOI's heterogeneous data streams — real-time earthquake feeds, continuous water monitoring, species occurrence records, park visitation statistics, and land management records — into a single analytical environment. The medallion architecture processes raw API feeds at the Bronze layer, standardizes and enriches records at Silver, and produces decision-ready analytics at Gold. This use case demonstrates how:

- **Seismic pattern analysis** detecting earthquake clustering, foreshock-aftershock sequences, and induced seismicity near energy operations
- **Water resource trend monitoring** tracking streamflow, groundwater levels, and water quality across the National Water Information System (NWIS)
- **Species habitat risk assessment** correlating endangered species occurrence data with land use changes, climate indicators, and contamination records
- **National park visitation analytics** modeling visitor demand, resource strain, and capacity planning across the NPS system

---

## Data Sources

### Primary Sources

| Source | Agency | URL | Data Available |
|--------|--------|-----|----------------|
| USGS Earthquake API (FDSN) | USGS | https://earthquake.usgs.gov/fdsnws/event/1/ | Real-time and historical earthquake catalog (magnitude, depth, location) |
| National Water Information System | USGS | https://waterservices.usgs.gov/rest/IV-Service.html | Real-time and historical streamflow, groundwater, water quality |
| 3D Elevation Program (3DEP) | USGS | https://www.usgs.gov/3d-elevation-program | High-resolution elevation data for terrain and flood analysis |
| ECOS Species Listings | FWS | https://ecos.fws.gov/ecp/services | Endangered/threatened species, critical habitat designations |
| NPS Visitor Statistics | NPS | https://irma.nps.gov/Stats/ | Monthly/annual visitation by park unit |
| NPS Developer API | NPS | https://developer.nps.gov/api/v1/ | Park details, alerts, events, campgrounds, activities |

### Supporting Sources

| Source | Agency | URL | Use In Analytics |
|--------|--------|-----|------------------|
| BLM Public Land Statistics | BLM | https://www.blm.gov/about/data/public-land-statistics | Federal land acreage, grazing permits, mineral leases |
| BSEE Incident Data | BSEE | https://www.bsee.gov/stats-facts/offshore-incident-statistics | Offshore energy safety incidents and inspections |
| BOEM Lease Sale Data | BOEM | https://www.boem.gov/oil-gas-energy/leasing | Offshore oil/gas/renewable energy lease records |
| GAP Analysis Project | USGS | https://www.usgs.gov/programs/gap-analysis-project | Land cover and species habitat distribution models |
| Protected Areas Database | USGS | https://www.usgs.gov/programs/gap-analysis-project/science/pad-us-data-overview | Authoritative inventory of U.S. protected areas |
| NOAA Climate Normals | NOAA | https://www.ncei.noaa.gov/products/land-based-station/us-climate-normals | Climate baselines for resource impact analysis |

---

## Seismic Pattern Analysis

### Background

The USGS Earthquake Hazards Program monitors seismic activity globally through the Advanced National Seismic System (ANSS), publishing earthquake data in near-real-time through the FDSN Web Services API. The earthquake catalog includes magnitude, depth, location, and associated metadata for events dating back decades. Analytical patterns of interest include spatial clustering (identifying seismic swarms), temporal sequences (foreshock-mainshock-aftershock), magnitude-frequency distributions (Gutenberg-Richter law), and induced seismicity correlation with wastewater injection wells.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Silver → Gold: Seismic Cluster Detection
# MAGIC Identifies earthquake clusters using spatiotemporal density analysis
# MAGIC to detect swarm activity and induced seismicity patterns.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window
from math import radians

# Read Silver earthquake data (validated, deduplicated)
df_quakes = spark.read.format("delta").load("Tables/silver_doi_usgs_earthquakes")

# Filter to significant events (M2.5+) in CONUS
df_conus = (
    df_quakes
    .filter(
        (F.col("magnitude") >= 2.5) &
        (F.col("latitude").between(24.5, 49.5)) &
        (F.col("longitude").between(-125.0, -66.5))
    )
    .withColumn("event_date", F.to_date("event_time"))
)

# Spatial binning: 0.5-degree grid cells for cluster detection
df_gridded = (
    df_conus
    .withColumn("lat_bin", F.round(F.col("latitude") * 2) / 2)
    .withColumn("lon_bin", F.round(F.col("longitude") * 2) / 2)
    .withColumn("grid_id", F.concat_ws("_", F.col("lat_bin"), F.col("lon_bin")))
)

# Calculate cluster metrics per grid cell per month
df_clusters = (
    df_gridded
    .withColumn("year_month", F.date_format("event_date", "yyyy-MM"))
    .groupBy("grid_id", "lat_bin", "lon_bin", "year_month")
    .agg(
        F.count("*").alias("event_count"),
        F.max("magnitude").alias("max_magnitude"),
        F.avg("magnitude").alias("avg_magnitude"),
        F.avg("depth_km").alias("avg_depth_km"),
        F.min("event_time").alias("first_event"),
        F.max("event_time").alias("last_event"),
        F.stddev("magnitude").alias("magnitude_stddev"),
    )
)

# Classify cluster type based on depth and frequency patterns
# Shallow induced seismicity: depth < 10km, high frequency, near injection wells
df_classified = (
    df_clusters
    .withColumn(
        "cluster_type",
        F.when(
            (F.col("avg_depth_km") < 10) & (F.col("event_count") > 20),
            "POTENTIAL_INDUCED"
        )
        .when(F.col("event_count") > 50, "SWARM")
        .when(F.col("max_magnitude") >= 5.0, "SIGNIFICANT_SEQUENCE")
        .otherwise("BACKGROUND")
    )
    .withColumn(
        "b_value_proxy",
        F.log10(F.col("event_count")) / F.col("max_magnitude")
    )
)

df_classified.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable("lh_gold.gold_doi_seismic_clusters")

induced = df_classified.filter(F.col("cluster_type") == "POTENTIAL_INDUCED").count()
print(f"Potential induced seismicity clusters: {induced}")
```

---

## Water Resource Trend Monitoring

### Background

The USGS National Water Information System (NWIS) is the nation's principal repository for water data, serving real-time and historical measurements from approximately 1.5 million monitoring sites. Instantaneous values for streamflow (discharge), gage height, water temperature, specific conductance, and dissolved oxygen are published at 15-minute intervals. This data underpins flood forecasting, drought monitoring, water rights adjudication, and ecological flow management. Long-term trend analysis reveals the impacts of climate change, urbanization, and water use on the nation's freshwater resources.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Silver → Gold: NWIS Streamflow Trend Analysis
# MAGIC Calculates long-term streamflow trends using Mann-Kendall
# MAGIC trend detection and Sen's slope estimation for drought/flood monitoring.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Read Silver NWIS daily streamflow data
df_flow = spark.read.format("delta").load("Tables/silver_doi_nwis_streamflow")

# Calculate annual statistics per monitoring site
df_annual = (
    df_flow
    .withColumn("water_year", 
        F.when(F.month("measurement_date") >= 10, F.year("measurement_date") + 1)
        .otherwise(F.year("measurement_date"))
    )
    .groupBy("site_number", "site_name", "state", "huc8_code",
             "latitude", "longitude", "water_year")
    .agg(
        F.avg("discharge_cfs").alias("mean_annual_flow_cfs"),
        F.min("discharge_cfs").alias("min_flow_7day_cfs"),
        F.max("discharge_cfs").alias("peak_flow_cfs"),
        F.percentile_approx("discharge_cfs", 0.1).alias("flow_10th_pct"),
        F.percentile_approx("discharge_cfs", 0.9).alias("flow_90th_pct"),
        F.count("*").alias("observation_count"),
    )
)

# Calculate departure from long-term mean
site_window = Window.partitionBy("site_number")
annual_window = Window.partitionBy("site_number").orderBy("water_year")

df_trends = (
    df_annual
    .withColumn("long_term_mean", F.avg("mean_annual_flow_cfs").over(site_window))
    .withColumn("long_term_stddev", F.stddev("mean_annual_flow_cfs").over(site_window))
    .withColumn(
        "flow_anomaly_pct",
        (F.col("mean_annual_flow_cfs") - F.col("long_term_mean"))
        / F.col("long_term_mean") * 100
    )
    .withColumn(
        "standardized_anomaly",
        (F.col("mean_annual_flow_cfs") - F.col("long_term_mean"))
        / F.col("long_term_stddev")
    )
    .withColumn(
        "drought_flag",
        F.when(F.col("standardized_anomaly") < -1.5, "SEVERE_DROUGHT")
        .when(F.col("standardized_anomaly") < -1.0, "MODERATE_DROUGHT")
        .when(F.col("standardized_anomaly") > 1.5, "FLOOD_RISK")
        .otherwise("NORMAL")
    )
    .withColumn("flow_prev_year", F.lag("mean_annual_flow_cfs").over(annual_window))
    .withColumn(
        "yoy_change_pct",
        F.when(F.col("flow_prev_year") > 0,
            (F.col("mean_annual_flow_cfs") - F.col("flow_prev_year"))
            / F.col("flow_prev_year") * 100
        )
    )
)

df_trends.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable("lh_gold.gold_doi_streamflow_trends")

drought = df_trends.filter(F.col("drought_flag") == "SEVERE_DROUGHT").count()
print(f"Site-years in severe drought: {drought}")
```

---

## Species Habitat Risk Assessment

### Background

The U.S. Fish and Wildlife Service (FWS) administers the Endangered Species Act (ESA), maintaining the official list of threatened and endangered species through the Environmental Conservation Online System (ECOS). As of 2024, over 1,680 U.S. species are listed under the ESA, with designated critical habitats spanning millions of acres of federal, state, and private lands. Species status assessments require integration of occurrence data, habitat condition, threat factors (land use change, climate shifts, contamination), and recovery plan progress. The ECOS web services API provides programmatic access to species listings, critical habitat boundaries, and recovery plan information.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Gold: Endangered Species Habitat Risk Assessment
# MAGIC Correlates species occurrence with land use change, climate
# MAGIC indicators, and contamination data for habitat risk scoring.

# COMMAND ----------

from pyspark.sql import functions as F

# Read Silver species and habitat data
df_species = spark.read.format("delta").load("Tables/silver_doi_fws_species_listings")
df_habitat = spark.read.format("delta").load("Tables/silver_doi_fws_critical_habitat")
df_land_cover = spark.read.format("delta").load("Tables/silver_doi_usgs_land_cover")

# Species-level habitat risk assessment
df_risk = (
    df_species
    .join(df_habitat, on="species_code", how="left")
    .join(df_land_cover, on=["state_fips", "county_fips"], how="left")
    .withColumn(
        "habitat_loss_risk",
        F.when(F.col("developed_land_pct_change") > 5.0, "HIGH")
        .when(F.col("developed_land_pct_change") > 2.0, "MODERATE")
        .otherwise("LOW")
    )
    .withColumn(
        "climate_vulnerability",
        F.when(F.col("temp_anomaly_c") > 2.0, "HIGH")
        .when(F.col("temp_anomaly_c") > 1.0, "MODERATE")
        .otherwise("LOW")
    )
    .withColumn(
        "contamination_exposure",
        F.when(F.col("tri_facilities_in_habitat") > 5, "HIGH")
        .when(F.col("tri_facilities_in_habitat") > 0, "MODERATE")
        .otherwise("LOW")
    )
)

# Calculate composite habitat risk score (0-100)
risk_map = {"HIGH": 3, "MODERATE": 2, "LOW": 1}

df_scored = (
    df_risk
    .withColumn("habitat_score",
        F.when(F.col("habitat_loss_risk") == "HIGH", 3)
        .when(F.col("habitat_loss_risk") == "MODERATE", 2).otherwise(1))
    .withColumn("climate_score",
        F.when(F.col("climate_vulnerability") == "HIGH", 3)
        .when(F.col("climate_vulnerability") == "MODERATE", 2).otherwise(1))
    .withColumn("contam_score",
        F.when(F.col("contamination_exposure") == "HIGH", 3)
        .when(F.col("contamination_exposure") == "MODERATE", 2).otherwise(1))
    .withColumn(
        "composite_risk_score",
        F.round(
            (F.col("habitat_score") * 0.4 +
             F.col("climate_score") * 0.35 +
             F.col("contam_score") * 0.25) / 3 * 100
        ).cast("int")
    )
    .withColumn(
        "recovery_priority",
        F.when(F.col("composite_risk_score") >= 80, "CRITICAL")
        .when(F.col("composite_risk_score") >= 60, "HIGH")
        .when(F.col("composite_risk_score") >= 40, "MODERATE")
        .otherwise("STABLE")
    )
)

df_scored.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable("lh_gold.gold_doi_species_habitat_risk")

critical = df_scored.filter(F.col("recovery_priority") == "CRITICAL").count()
print(f"Species with CRITICAL habitat risk: {critical}")
```

---

## Implementation in Fabric

### Table Inventory

| Layer | Table | Source | Description |
|-------|-------|--------|-------------|
| Bronze | `bronze_doi_usgs_earthquakes` | USGS FDSN API | Raw earthquake event catalog |
| Bronze | `bronze_doi_nwis_streamflow` | NWIS API | Raw instantaneous streamflow values |
| Bronze | `bronze_doi_nwis_groundwater` | NWIS API | Raw groundwater level measurements |
| Bronze | `bronze_doi_fws_species_listings` | ECOS API | Raw ESA species listing data |
| Bronze | `bronze_doi_fws_critical_habitat` | ECOS API | Raw critical habitat designations |
| Bronze | `bronze_doi_nps_visitation` | NPS IRMA | Raw monthly park visitation counts |
| Bronze | `bronze_doi_blm_land_stats` | BLM | Raw public land management statistics |
| Bronze | `bronze_doi_usgs_land_cover` | GAP/NLCD | Raw land cover classification data |
| Silver | `silver_doi_usgs_earthquakes` | USGS Bronze | Validated, deduplicated earthquake catalog |
| Silver | `silver_doi_nwis_streamflow` | NWIS Bronze | Quality-controlled daily streamflow records |
| Silver | `silver_doi_fws_species_listings` | FWS Bronze | Standardized species listings with taxonomy |
| Silver | `silver_doi_fws_critical_habitat` | FWS Bronze | Georeferenced critical habitat boundaries |
| Silver | `silver_doi_nps_visitation` | NPS Bronze | Validated park visitation with seasonality |
| Silver | `silver_doi_usgs_land_cover` | Land Cover Bronze | Land use change calculations by county |
| Gold | `gold_doi_seismic_clusters` | Earthquake Silver | Spatiotemporal seismic clusters with classification |
| Gold | `gold_doi_streamflow_trends` | Streamflow Silver | Annual flow trends with drought/flood flags |
| Gold | `gold_doi_species_habitat_risk` | Species + Habitat Silver | Composite habitat risk scores per species |
| Gold | `gold_doi_park_demand_forecast` | Visitation Silver | Park visitation forecasts and capacity metrics |

### Notebook Sequence

1. `01_bronze_doi_earthquakes_ingest.py` — Ingest USGS FDSN earthquake catalog via API
2. `02_bronze_doi_nwis_ingest.py` — Ingest NWIS streamflow and groundwater data
3. `03_bronze_doi_species_ingest.py` — Ingest FWS ECOS species listings and habitats
4. `04_bronze_doi_nps_visitation_ingest.py` — Ingest NPS IRMA visitation statistics
5. `05_bronze_doi_land_cover_ingest.py` — Ingest USGS land cover classification data
6. `06_silver_doi_earthquake_validation.py` — Validate and deduplicate earthquake records
7. `07_silver_doi_nwis_qc.py` — Quality control and daily aggregation of streamflow
8. `08_silver_doi_species_standardize.py` — Standardize species taxonomy and habitat geometry
9. `09_silver_doi_nps_validate.py` — Validate and enrich visitation records
10. `10_silver_doi_land_cover_change.py` — Calculate land use change metrics
11. `11_gold_doi_seismic_clusters.py` — Spatiotemporal cluster detection and classification
12. `12_gold_doi_streamflow_trends.py` — Long-term flow trend analysis with anomaly flags
13. `13_gold_doi_species_risk.py` — Composite habitat risk scoring
14. `14_gold_doi_park_demand.py` — Visitation forecasting and capacity planning

---

## Power BI Visualizations

### Recommended Visuals

| Page | Visual Type | Data | Purpose |
|------|-------------|------|---------|
| Seismic Overview | Azure Map with point clusters | `gold_doi_seismic_clusters` | Real-time earthquake map with magnitude-scaled markers |
| Seismic Trends | Line + bar combo | `gold_doi_seismic_clusters` | Monthly event counts and maximum magnitudes over time |
| Water Resources | Shape map (HUC8) | `gold_doi_streamflow_trends` | Watershed-level drought/flood status with color coding |
| Streamflow Detail | Sparklines + KPI cards | `gold_doi_streamflow_trends` | Site-level flow anomalies with trend indicators |
| Species Dashboard | Matrix heatmap | `gold_doi_species_habitat_risk` | Species risk scores by state and threat category |
| Species Map | Azure Map with polygons | `gold_doi_species_habitat_risk` | Critical habitat boundaries with risk overlay |
| Park Visitation | Decomposition tree | `gold_doi_park_demand_forecast` | Visitation drivers by park, season, and year |
| Capacity Planning | Gauge + table | `gold_doi_park_demand_forecast` | Current utilization vs. capacity with forecasts |

### DAX Measures

```dax
// Seismic Event Rate (events per month, trailing 12 months)
Seismic Event Rate =
VAR _Months = 12
VAR _EndDate = MAX(gold_doi_seismic_clusters[year_month])
VAR _Events =
    CALCULATE(
        SUM(gold_doi_seismic_clusters[event_count]),
        DATESINPERIOD(
            dim_date[Date],
            _EndDate,
            -_Months,
            MONTH
        )
    )
RETURN
    DIVIDE(_Events, _Months, 0)
```

```dax
// Streamflow Drought Severity Index
Drought Severity Index =
VAR _SevereCount =
    CALCULATE(
        COUNTROWS(gold_doi_streamflow_trends),
        gold_doi_streamflow_trends[drought_flag] = "SEVERE_DROUGHT"
    )
VAR _ModCount =
    CALCULATE(
        COUNTROWS(gold_doi_streamflow_trends),
        gold_doi_streamflow_trends[drought_flag] = "MODERATE_DROUGHT"
    )
VAR _Total = COUNTROWS(gold_doi_streamflow_trends)
RETURN
    DIVIDE(_SevereCount * 2 + _ModCount, _Total, 0)
```

```dax
// Species at Critical Risk (% of listed species)
Critical Species Rate =
DIVIDE(
    CALCULATE(
        DISTINCTCOUNT(gold_doi_species_habitat_risk[species_code]),
        gold_doi_species_habitat_risk[recovery_priority] = "CRITICAL"
    ),
    DISTINCTCOUNT(gold_doi_species_habitat_risk[species_code]),
    0
)
```

```dax
// Park Utilization Rate (actual vs. capacity)
Park Utilization % =
DIVIDE(
    SUM(gold_doi_park_demand_forecast[actual_visitors]),
    SUM(gold_doi_park_demand_forecast[carrying_capacity]),
    BLANK()
)
```

---

## Cross-Domain Analysis

### Hypothesis 1: DOI × NOAA — Climate Impact on Water Resources

NOAA climate data (temperature normals, precipitation trends, drought indices) directly predicts changes in USGS streamflow patterns. Correlating NOAA's Palmer Drought Severity Index (PDSI) and precipitation anomalies with NWIS streamflow departures quantifies how climate variability translates to water availability in specific watersheds, enabling proactive drought management.

```python
# Cross-domain: NOAA climate indicators vs. USGS streamflow
df_cross_climate = (
    df_noaa_climate_normals
    .join(df_doi_streamflow_trends, on=["state", "huc8_code", "water_year"])
    .select(
        "state", "huc8_code", "water_year",
        "precip_anomaly_pct", "temp_anomaly_c", "pdsi_value",
        "flow_anomaly_pct", "drought_flag",
    )
    .withColumn(
        "climate_flow_correlation",
        F.corr("precip_anomaly_pct", "flow_anomaly_pct")
            .over(Window.partitionBy("huc8_code"))
    )
)
```

### Hypothesis 2: DOI × EPA — Contamination on Public Lands

EPA TRI facility releases and Superfund sites located on or adjacent to DOI-managed lands create ecological risks to species habitat and water resources. Joining EPA facility data with DOI land boundaries and FWS critical habitat designations identifies protected areas with the highest contamination exposure, enabling prioritized remediation coordination between DOI and EPA.

```python
# Cross-domain: EPA contamination within DOI critical habitat
df_cross_contam = (
    df_epa_tri_facilities
    .join(
        df_doi_critical_habitat,
        (F.col("tri.latitude").between(
            F.col("habitat.bbox_south"), F.col("habitat.bbox_north"))) &
        (F.col("tri.longitude").between(
            F.col("habitat.bbox_west"), F.col("habitat.bbox_east")))
    )
    .groupBy("species_code", "common_name", "listing_status")
    .agg(
        F.count("trifid").alias("tri_facilities_in_habitat"),
        F.sum("total_releases_lbs").alias("total_releases_in_habitat"),
        F.countDistinct("chemical_name").alias("distinct_contaminants"),
    )
    .orderBy(F.col("total_releases_in_habitat").desc())
)
```

### Hypothesis 3: DOI × USDA — Agricultural Land Use and Species Impact

USDA crop production data reveals where agricultural intensification encroaches on wildlife habitat. Correlating USDA county-level agricultural land use with FWS species occurrence data and USGS land cover change metrics identifies regions where farming expansion most threatens endangered species, informing Farm Bill conservation program targeting.

```sql
-- Cross-domain: USDA agricultural intensity vs. species habitat loss
SELECT
    s.common_name,
    s.listing_status,
    l.state,
    l.county,
    a.total_cropland_acres,
    a.cropland_change_pct_5yr,
    l.developed_land_pct_change,
    s.composite_risk_score,
    s.recovery_priority
FROM gold_doi_species_habitat_risk s
JOIN silver_doi_usgs_land_cover l
    ON s.state_fips = l.state_fips AND s.county_fips = l.county_fips
JOIN gold_usda_crop_production a
    ON l.state_fips = a.state_fips AND l.county_fips = a.county_fips
WHERE s.recovery_priority IN ('CRITICAL', 'HIGH')
    AND a.cropland_change_pct_5yr > 3.0
ORDER BY s.composite_risk_score DESC
```

---

## Microsoft Published Resources

| Resource | URL | Relevance |
|----------|-----|-----------|
| Azure Maps Documentation | https://learn.microsoft.com/en-us/azure/azure-maps/about-azure-maps | Geospatial visualization for earthquake, habitat, and park mapping |
| Azure IoT Reference Architecture | https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/iot | Real-time sensor ingestion for USGS streamflow and seismic monitoring |
| Microsoft Fabric Security White Paper | https://learn.microsoft.com/en-us/fabric/security/white-paper-landing-page | Data protection for sensitive species location and land management data |
| Cloud-Scale Analytics with Microsoft Fabric | https://learn.microsoft.com/en-us/azure/architecture/solution-ideas/articles/analytics-end-to-end | End-to-end analytics architecture for multi-bureau DOI data |
| Power BI Embedded Analytics | https://learn.microsoft.com/en-us/power-bi/developer/embedded/embedding | Embedding DOI dashboards into public-facing portals and field apps |
| Azure Synapse Analytics for Government | https://learn.microsoft.com/en-us/azure/architecture/industries/government | Government cloud analytics patterns for DOI workloads |

---

## Published References

| Reference | URL | Description |
|-----------|-----|-------------|
| USGS Earthquake Hazards API | https://earthquake.usgs.gov/fdsnws/event/1/ | FDSN event web service for earthquake data access |
| NWIS Web Services | https://waterservices.usgs.gov | REST API for real-time and historical water data |
| ECOS Species Profile API | https://ecos.fws.gov/ecp/services | Programmatic access to ESA species listings |
| NPS Developer API | https://developer.nps.gov/api/v1/ | Park information, alerts, and visitor resources |
| NPS Visitor Statistics | https://irma.nps.gov/Stats/ | Official NPS visitation reporting system |
| USGS 3DEP Data | https://www.usgs.gov/3d-elevation-program | National elevation and terrain data program |
| Protected Areas Database (PAD-US) | https://www.usgs.gov/programs/gap-analysis-project/science/pad-us-data-overview | Authoritative U.S. protected areas inventory |

---

## Related Documentation

- [Environmental Compliance Analytics](environmental-compliance-analytics.md) — EPA contamination data for public lands overlay
- [Tribal Health Analytics](tribal-health-analytics.md) — DOI trust lands and tribal environmental health
- [Federal Justice Analytics](federal-justice-analytics.md) — Environmental crime prosecution on federal lands
- [Antitrust Analytics](antitrust-analytics.md) — Energy market concentration on federal leases
- [Real-Time Intelligence](../features/real-time-intelligence.md) — Eventstream patterns for USGS real-time feeds
- [Medallion Architecture Deep Dive](../best-practices/medallion-architecture-deep-dive.md) — Bronze/Silver/Gold for geospatial data
- [Data Governance Deep Dive](../best-practices/data-governance-deep-dive.md) — Purview lineage for DOI data pipelines

---

*Last Updated: 2026-04-23*
