# Weather and Climate Analytics

> Leveraging Microsoft Fabric to analyze severe weather patterns, detect climate anomalies, and correlate meteorological events with cross-domain impacts using NOAA public observation and forecast data.

---

## Executive Summary

The National Oceanic and Atmospheric Administration (NOAA) operates the most comprehensive weather and climate observation network in the world, collecting billions of data points daily from 10,000+ surface stations, 900+ upper-air stations, 160 coastal tide gauges, and hundreds of ocean buoys. The Storm Events Database alone documents over 1.5 million severe weather events since 1950, including property damage estimates, fatalities, and narrative descriptions that are invaluable for pattern recognition and predictive modeling.

Despite this wealth of data, most analysis remains siloed: storm events in one system, climate normals in another, marine observations in a third. Microsoft Fabric unifies these streams through a medallion architecture with Real-Time Intelligence for live weather ingestion, PySpark for historical pattern analysis, and Direct Lake Power BI dashboards for emergency management and policy decision-making. This use case demonstrates how the Supercharge Microsoft Fabric POC applies streaming analytics, Delta Lake time-series optimization, and KQL real-time queries to publicly available NOAA weather and climate data.

- **Storm severity analysis** classifying 1.5M+ events by type, magnitude, economic damage, and fatality impact across 70+ years of records
- **Seasonal pattern detection** using rolling window statistics to identify shifting storm season boundaries and intensifying weather cycles
- **Climate anomaly monitoring** computing departure-from-normal metrics for temperature, precipitation, and sea level against 30-year climate normals
- **Coastal and marine observation** integrating tide gauge and buoy data for sea level trend analysis and coastal hazard early warning

---

## Data Sources

### Primary Sources

| Source | Agency | URL | Data Available |
|--------|--------|-----|----------------|
| Weather API (Forecasts) | NOAA/NWS | https://api.weather.gov | Real-time forecasts, alerts, station observations |
| Storm Events Database | NOAA/NCEI | https://www.ncdc.noaa.gov/stormevents/ | 1.5M+ events: type, magnitude, damage, fatalities, narratives |
| Climate Data Online (CDO) | NOAA/NCEI | https://www.ncei.noaa.gov/cdo-web/ | Historical station data: temp, precip, snow, wind |
| Tides and Currents | NOAA/CO-OPS | https://tidesandcurrents.noaa.gov/api/ | Tide predictions, water levels, sea level trends |
| NDBC Buoy Data | NOAA/NDBC | https://www.ndbc.noaa.gov/data/ | Ocean buoy observations: waves, wind, temperature, pressure |

### Supporting Sources

| Source | Agency | URL | Use In Analytics |
|--------|--------|-----|------------------|
| U.S. Climate Normals | NOAA/NCEI | https://www.ncei.noaa.gov/products/land-based-station/us-climate-normals | 30-year baseline for anomaly detection |
| GHCN-Daily | NOAA/NCEI | https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily | Global daily observations for trend analysis |
| NEXRAD Radar | NOAA/NWS | https://www.ncdc.noaa.gov/nexradinv/ | Radar imagery archive for storm tracking |
| International Best Track (IBTrACS) | NOAA/NCEI | https://www.ncei.noaa.gov/products/international-best-track-archive | Global tropical cyclone track data |
| FEMA Disaster Declarations | FEMA | https://www.fema.gov/api/open/v2/DisasterDeclarations | Federal disaster declarations for damage correlation |
| SHELDUS | CEMHS | https://cemhs.asu.edu/sheldus | County-level hazard loss data |

---

## Storm Severity Analysis

### Background

The NOAA Storm Events Database is the official record of significant weather events in the United States, maintained by the National Centers for Environmental Information (NCEI). Each record includes event type (tornado, hail, flash flood, hurricane, etc.), begin/end dates and locations, magnitude measures (EF scale for tornadoes, hail diameter, wind speed), property and crop damage estimates, and direct/indirect fatalities. The database extends from January 1950 for tornado records, with comprehensive multi-event coverage beginning in 1996.

Analyzing 70+ years of storm events reveals shifting severity distributions, geographic migration of storm corridors, and escalating damage costs that inform both emergency management resource allocation and insurance risk modeling.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Storm Severity Analysis
# MAGIC Bronze-to-Silver transformation with severity classification and damage normalization

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Load Bronze storm events
df_storms = spark.read.format("delta").load(
    "abfss://lh_bronze@onelake.dfs.fabric.microsoft.com/Tables/bronze_noaa_storm_events"
)

# --- Normalize Damage Values ---
# NOAA encodes damage as "25K", "1.5M", "500" etc.
def parse_damage_udf(value):
    """Convert NOAA damage notation to numeric."""
    if value is None or value == "":
        return 0.0
    value = str(value).strip().upper()
    multipliers = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
    for suffix, mult in multipliers.items():
        if value.endswith(suffix):
            return float(value[:-1]) * mult
    try:
        return float(value)
    except ValueError:
        return 0.0

parse_damage = F.udf(parse_damage_udf, "double")

df_normalized = df_storms.withColumn(
    "property_damage_amt", parse_damage(F.col("damage_property"))
).withColumn(
    "crop_damage_amt", parse_damage(F.col("damage_crops"))
).withColumn(
    "total_damage_amt",
    F.col("property_damage_amt") + F.col("crop_damage_amt")
).withColumn(
    "total_casualties",
    F.col("deaths_direct") + F.col("deaths_indirect")
    + F.col("injuries_direct") + F.col("injuries_indirect")
)

# --- Severity Classification ---
df_classified = df_normalized.withColumn(
    "severity_tier",
    F.when(
        (F.col("total_damage_amt") > 10_000_000) | (F.col("total_casualties") > 10),
        "CATASTROPHIC"
    ).when(
        (F.col("total_damage_amt") > 1_000_000) | (F.col("total_casualties") > 3),
        "SEVERE"
    ).when(
        (F.col("total_damage_amt") > 100_000) | (F.col("total_casualties") > 0),
        "SIGNIFICANT"
    ).otherwise("MINOR")
)

# --- Decadal Trend Analysis ---
df_trends = df_classified.withColumn(
    "event_year", F.year("begin_date")
).withColumn(
    "decade",
    (F.floor(F.col("event_year") / 10) * 10).cast("int")
)

decade_summary = df_trends.groupBy("decade", "event_type").agg(
    F.count("*").alias("event_count"),
    F.sum("total_damage_amt").alias("total_damage"),
    F.sum("deaths_direct").alias("total_fatalities"),
    F.avg("total_damage_amt").alias("avg_damage_per_event")
).orderBy("decade", F.desc("event_count"))

# Write to Silver
df_classified.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).save("abfss://lh_silver@onelake.dfs.fabric.microsoft.com/Tables/silver_noaa_storm_classified")

decade_summary.write.format("delta").mode("overwrite").save(
    "abfss://lh_gold@onelake.dfs.fabric.microsoft.com/Tables/gold_noaa_storm_decadal_trends"
)

print(f"Storm events classified: {df_classified.count():,}")
print(f"CATASTROPHIC events: {df_classified.filter(F.col('severity_tier') == 'CATASTROPHIC').count():,}")
```

---

## Seasonal Pattern Detection

### Background

Severe weather in the United States follows well-established seasonal patterns: tornado season peaks from April through June in Tornado Alley, hurricane season runs June through November, and winter storms concentrate from December through March. However, climate research indicates these patterns are shifting — tornado activity is migrating eastward from the Great Plains, hurricane rapid intensification is becoming more frequent, and winter storm tracks are changing with the weakening polar vortex. Detecting these shifts in historical data is critical for updating emergency preparedness models and infrastructure resilience planning.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Seasonal Pattern Detection
# MAGIC Rolling window statistics to identify storm season boundary shifts

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Load Silver classified storms
df_storms = spark.read.format("delta").load(
    "abfss://lh_silver@onelake.dfs.fabric.microsoft.com/Tables/silver_noaa_storm_classified"
)

# --- Monthly Event Distribution by Decade ---
df_monthly = df_storms.withColumn(
    "event_year", F.year("begin_date")
).withColumn(
    "event_month", F.month("begin_date")
).withColumn(
    "decade",
    (F.floor(F.col("event_year") / 10) * 10).cast("int")
)

# Focus on key severe weather types
severe_types = ["Tornado", "Hail", "Thunderstorm Wind", "Hurricane", "Flash Flood"]

df_seasonal = df_monthly.filter(
    F.col("event_type").isin(severe_types)
).groupBy("decade", "event_type", "event_month").agg(
    F.count("*").alias("event_count"),
    F.sum("total_damage_amt").alias("total_damage"),
    F.avg("total_damage_amt").alias("avg_damage")
)

# --- Season Boundary Detection ---
# Calculate the month containing the 10th and 90th percentile of events per type/decade
type_decade_window = Window.partitionBy("decade", "event_type").orderBy("event_month")

df_cumulative = df_seasonal.withColumn(
    "cumulative_events",
    F.sum("event_count").over(type_decade_window)
)

total_by_type_decade = df_seasonal.groupBy("decade", "event_type").agg(
    F.sum("event_count").alias("total_events")
)

df_percentile = df_cumulative.join(
    total_by_type_decade, ["decade", "event_type"]
).withColumn(
    "cumulative_pct",
    F.col("cumulative_events") / F.col("total_events")
)

# Season start = first month crossing 10% cumulative, end = first crossing 90%
season_start = df_percentile.filter(
    F.col("cumulative_pct") >= 0.10
).groupBy("decade", "event_type").agg(
    F.min("event_month").alias("season_start_month")
)

season_end = df_percentile.filter(
    F.col("cumulative_pct") >= 0.90
).groupBy("decade", "event_type").agg(
    F.min("event_month").alias("season_end_month")
)

df_season_bounds = season_start.join(
    season_end, ["decade", "event_type"]
).withColumn(
    "season_length_months",
    F.col("season_end_month") - F.col("season_start_month") + 1
).orderBy("event_type", "decade")

# Write Gold
df_season_bounds.write.format("delta").mode("overwrite").save(
    "abfss://lh_gold@onelake.dfs.fabric.microsoft.com/Tables/gold_noaa_season_boundaries"
)

print("Season boundary shifts by decade:")
df_season_bounds.show(30, truncate=False)
```

---

## Climate Anomaly Monitoring

### Background

NOAA publishes 30-year U.S. Climate Normals — baseline averages for temperature, precipitation, snowfall, and other variables computed over rolling 30-year periods (most recently 1991-2020). Comparing current observations against these normals produces anomaly values that are the foundation of climate monitoring. Sustained positive temperature anomalies, precipitation departures, and accelerating sea level rise measured at CO-OPS tide gauges are key indicators tracked by the National Climate Assessment.

The Fabric Eventhouse is ideal for this workload: streaming weather observations arrive via the weather.gov API, are compared against stored normals in real time using KQL, and anomaly alerts trigger through Fabric Activator when thresholds are exceeded.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Climate Anomaly Monitoring
# MAGIC Computing departure-from-normal metrics for temperature and precipitation

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Load observations and normals
df_obs = spark.read.format("delta").load(
    "abfss://lh_silver@onelake.dfs.fabric.microsoft.com/Tables/silver_noaa_daily_observations"
)
df_normals = spark.read.format("delta").load(
    "abfss://lh_silver@onelake.dfs.fabric.microsoft.com/Tables/silver_noaa_climate_normals"
)

# --- Temperature Anomaly ---
# Join daily observations with monthly normals by station and month
df_temp = df_obs.withColumn(
    "obs_month", F.month("observation_date")
).withColumn(
    "obs_year", F.year("observation_date")
)

df_anomaly = df_temp.join(
    df_normals,
    on=[
        df_temp.station_id == df_normals.station_id,
        df_temp.obs_month == df_normals.month
    ],
    how="inner"
).select(
    df_temp.station_id,
    df_temp.station_name,
    df_temp.state,
    df_temp.obs_year,
    df_temp.obs_month,
    df_temp.avg_temp_f,
    df_normals.normal_avg_temp_f,
    df_temp.total_precip_in,
    df_normals.normal_precip_in
)

# Compute departures
df_departures = df_anomaly.withColumn(
    "temp_anomaly_f",
    F.round(F.col("avg_temp_f") - F.col("normal_avg_temp_f"), 2)
).withColumn(
    "precip_anomaly_in",
    F.round(F.col("total_precip_in") - F.col("normal_precip_in"), 2)
).withColumn(
    "precip_pct_normal",
    F.round(F.col("total_precip_in") / F.col("normal_precip_in") * 100, 1)
)

# --- Annual State-Level Anomaly Summary ---
state_annual = df_departures.groupBy("state", "obs_year").agg(
    F.avg("temp_anomaly_f").alias("avg_temp_anomaly"),
    F.avg("precip_anomaly_in").alias("avg_precip_anomaly"),
    F.count("*").alias("observation_count"),
    F.sum(F.when(F.col("temp_anomaly_f") > 3.0, 1).otherwise(0)).alias("extreme_warm_months"),
    F.sum(F.when(F.col("temp_anomaly_f") < -3.0, 1).otherwise(0)).alias("extreme_cold_months")
).withColumn(
    "warming_trend",
    F.when(F.col("avg_temp_anomaly") > 2.0, "SIGNIFICANT_WARMING")
    .when(F.col("avg_temp_anomaly") > 0.5, "MODERATE_WARMING")
    .when(F.col("avg_temp_anomaly") < -0.5, "COOLING")
    .otherwise("NEAR_NORMAL")
)

# --- 10-Year Rolling Trend ---
year_window = Window.partitionBy("state").orderBy("obs_year") \
    .rowsBetween(-9, 0)

state_trend = state_annual.withColumn(
    "rolling_10yr_temp_anomaly",
    F.round(F.avg("avg_temp_anomaly").over(year_window), 2)
)

# Write Gold
state_trend.write.format("delta").mode("overwrite").save(
    "abfss://lh_gold@onelake.dfs.fabric.microsoft.com/Tables/gold_noaa_climate_anomaly_trends"
)

print(f"State-year anomaly records: {state_trend.count():,}")
```

---

## Implementation in Fabric

### Table Inventory

| Layer | Table | Source | Description |
|-------|-------|--------|-------------|
| Bronze | `bronze_noaa_storm_events` | NCEI Storm Events | Raw storm event records (1.5M+ rows) |
| Bronze | `bronze_noaa_daily_observations` | CDO/GHCN-Daily | Raw daily weather station observations |
| Bronze | `bronze_noaa_climate_normals` | NCEI Climate Normals | 30-year baseline averages (1991-2020) |
| Bronze | `bronze_noaa_tide_observations` | CO-OPS API | Raw tide gauge water level readings |
| Bronze | `bronze_noaa_buoy_observations` | NDBC | Raw ocean buoy measurements |
| Silver | `silver_noaa_storm_classified` | Storm Bronze | Classified events with severity tier and normalized damage |
| Silver | `silver_noaa_daily_observations` | CDO Bronze | Validated daily obs with QC flags applied |
| Silver | `silver_noaa_climate_normals` | Normals Bronze | Station-month normals with metadata |
| Silver | `silver_noaa_tide_validated` | Tide Bronze | Validated water levels with datum corrections |
| Gold | `gold_noaa_storm_decadal_trends` | Silver Storms | Event counts, damage, fatalities by decade and type |
| Gold | `gold_noaa_season_boundaries` | Silver Storms | Season start/end month by event type and decade |
| Gold | `gold_noaa_climate_anomaly_trends` | Silver Obs + Normals | State annual anomalies with 10-year rolling trend |
| Gold | `gold_noaa_sea_level_trends` | Silver Tides | Annual mean sea level and rate of change by station |
| Gold | `gold_noaa_coastal_hazard_index` | Silver Tides + Storms | Composite coastal risk score combining storm surge and sea level |

### Notebook Sequence

1. `01_bronze_noaa_storm_ingest.py` - Ingest NCEI Storm Events CSV bulk download into Delta Bronze
2. `02_bronze_noaa_cdo_ingest.py` - Pull Climate Data Online observations via CDO API into Bronze
3. `03_bronze_noaa_normals_ingest.py` - Load 30-year Climate Normals reference data into Bronze
4. `04_bronze_noaa_tides_ingest.py` - Stream CO-OPS tide gauge data via API into Bronze
5. `05_bronze_noaa_buoy_ingest.py` - Ingest NDBC buoy observations into Bronze
6. `06_silver_storm_classification.py` - Normalize damage, classify severity, validate coordinates
7. `07_silver_observation_validation.py` - Apply QC flags, remove erroneous readings, standardize units
8. `08_gold_storm_decadal_trends.py` - Aggregate storm events by decade and type
9. `09_gold_season_boundaries.py` - Detect season start/end shifts using cumulative percentile analysis
10. `10_gold_climate_anomaly.py` - Compute temperature and precipitation departures from normals
11. `11_gold_sea_level_trends.py` - Calculate annual mean sea level and linear trend by tide station
12. `12_gold_coastal_hazard_index.py` - Build composite coastal risk score

---

## Power BI Visualizations

### Recommended Visuals

| Page | Visual Type | Data | Purpose |
|------|-------------|------|---------|
| Storm Overview | Filled Map | `gold_noaa_storm_decadal_trends` | Geographic density of severe weather events by state |
| Storm Overview | Stacked Area | `gold_noaa_storm_decadal_trends` | Event count trends by type across decades |
| Storm Detail | Scatter Plot | `silver_noaa_storm_classified` | Individual events: damage vs. casualties with severity color |
| Storm Detail | Decomposition Tree | `silver_noaa_storm_classified` | Drill from type -> state -> county -> severity |
| Season Shifts | Heatmap Matrix | `gold_noaa_season_boundaries` | Month × event type × decade showing season migration |
| Season Shifts | Line Chart | `gold_noaa_season_boundaries` | Season length trends per event type over decades |
| Climate Anomaly | Diverging Bar | `gold_noaa_climate_anomaly_trends` | Temperature anomaly by state (red warm, blue cool) |
| Climate Anomaly | Small Multiples | `gold_noaa_climate_anomaly_trends` | 10-year rolling anomaly sparklines for each state |
| Coastal Risk | Map + Gauges | `gold_noaa_sea_level_trends` | Tide stations with sea level trend rate indicators |

### DAX Measures

```dax
// Total Damage (Inflation-Adjusted to Current Year)
Adjusted Storm Damage =
SUMX(
    'silver_noaa_storm_classified',
    'silver_noaa_storm_classified'[total_damage_amt]
        * LOOKUPVALUE(
            'dim_cpi_adjustment'[adjustment_factor],
            'dim_cpi_adjustment'[year],
            YEAR('silver_noaa_storm_classified'[begin_date])
        )
)
```

```dax
// Temperature Anomaly Trend (Rolling 10-Year Average)
Avg 10yr Temp Anomaly =
AVERAGEX(
    FILTER(
        'gold_noaa_climate_anomaly_trends',
        'gold_noaa_climate_anomaly_trends'[obs_year]
            >= MAX('gold_noaa_climate_anomaly_trends'[obs_year]) - 9
    ),
    'gold_noaa_climate_anomaly_trends'[avg_temp_anomaly]
)
```

```dax
// Catastrophic Event Frequency (Events per Decade)
Catastrophic Rate Per Decade =
VAR _CatCount =
    CALCULATE(
        COUNTROWS('silver_noaa_storm_classified'),
        'silver_noaa_storm_classified'[severity_tier] = "CATASTROPHIC"
    )
VAR _YearSpan =
    DATEDIFF(
        MIN('silver_noaa_storm_classified'[begin_date]),
        MAX('silver_noaa_storm_classified'[begin_date]),
        YEAR
    )
RETURN
    DIVIDE(_CatCount, DIVIDE(_YearSpan, 10, 1), 0)
```

```dax
// Season Length Change vs Baseline
Season Shift From Baseline =
VAR _CurrentLength =
    SELECTEDVALUE('gold_noaa_season_boundaries'[season_length_months])
VAR _BaselineLength =
    CALCULATE(
        AVERAGE('gold_noaa_season_boundaries'[season_length_months]),
        'gold_noaa_season_boundaries'[decade] = 1970
    )
RETURN
    _CurrentLength - _BaselineLength
```

---

## Cross-Domain Analysis

### Hypothesis 1: NOAA Severe Weather x DOT/FAA Aviation Disruption

**Hypothesis:** Counties with increasing tornado and thunderstorm frequency (NOAA Storm Events) correlate with rising flight cancellation and delay rates at nearby airports, enabling predictive scheduling models.

```sql
-- Weather impact on aviation operations
SELECT
    n.state,
    n.event_type,
    n.event_year,
    n.event_count AS severe_weather_events,
    f.total_delays,
    f.total_cancellations,
    f.avg_delay_minutes,
    CORR(n.event_count, f.total_cancellations)
        OVER (PARTITION BY n.state) AS weather_cancellation_correlation
FROM gold_noaa_storm_decadal_trends n
JOIN gold_dot_faa_airport_performance f
    ON n.state = f.state
    AND n.event_year = f.year
WHERE n.event_type IN ('Tornado', 'Thunderstorm Wind', 'Hail', 'Hurricane')
ORDER BY weather_cancellation_correlation DESC
```

### Hypothesis 2: NOAA Climate Anomaly x USDA Crop Yield Impact

**Hypothesis:** States with sustained temperature anomalies exceeding +2F and precipitation departures below 75% of normal show statistically significant crop yield reductions in the following growing season, validating climate-agricultural linkage models.

```python
# Cross-domain: Climate anomaly impact on crop production
df_climate = spark.read.format("delta").load(
    "abfss://lh_gold@onelake.dfs.fabric.microsoft.com/Tables/gold_noaa_climate_anomaly_trends"
)
df_crops = spark.read.format("delta").load(
    "abfss://lh_gold@onelake.dfs.fabric.microsoft.com/Tables/gold_usda_crop_production"
)

# Join climate anomalies with crop yields (lagged 1 year for growing season impact)
df_impact = df_climate.join(
    df_crops,
    on=[
        df_climate.state == df_crops.state_alpha,
        df_climate.obs_year == df_crops.year - 1  # Prior year climate affects next harvest
    ],
    how="inner"
).select(
    df_climate.state,
    df_climate.obs_year.alias("climate_year"),
    "avg_temp_anomaly",
    "avg_precip_anomaly",
    "warming_trend",
    "commodity_desc",
    "yield_per_acre",
    "production_value"
)

# Identify climate-stressed crop outcomes
df_stressed = df_impact.filter(
    (F.col("avg_temp_anomaly") > 2.0) | (F.col("avg_precip_anomaly") < -1.5)
).withColumn(
    "climate_stress_type",
    F.when(
        (F.col("avg_temp_anomaly") > 2.0) & (F.col("avg_precip_anomaly") < -1.5),
        "HOT_DRY"
    ).when(F.col("avg_temp_anomaly") > 2.0, "HOT")
    .otherwise("DRY")
)

df_stressed.groupBy("climate_stress_type", "commodity_desc").agg(
    F.avg("yield_per_acre").alias("avg_stressed_yield"),
    F.count("*").alias("sample_size")
).orderBy("commodity_desc", "climate_stress_type").show(30)
```

### Hypothesis 3: NOAA Coastal Storm Surge x DOI Coastal Land Management

**Hypothesis:** DOI-managed coastal lands (national wildlife refuges, national seashores) experiencing accelerating sea level rise (>3mm/year at nearby tide gauges) and increasing storm surge frequency face compounding habitat loss that should prioritize managed retreat strategies.

```sql
-- Coastal risk: Sea level trends at DOI-managed coastal sites
SELECT
    t.station_name,
    t.state,
    t.sea_level_trend_mm_yr,
    t.trend_confidence_interval,
    s.storm_surge_events_last_decade,
    s.max_surge_ft,
    d.site_name AS doi_managed_site,
    d.site_type,
    d.acreage,
    CASE
        WHEN t.sea_level_trend_mm_yr > 5.0 AND s.storm_surge_events_last_decade > 10
        THEN 'CRITICAL_RISK'
        WHEN t.sea_level_trend_mm_yr > 3.0 OR s.storm_surge_events_last_decade > 5
        THEN 'ELEVATED_RISK'
        ELSE 'MONITOR'
    END AS coastal_risk_tier
FROM gold_noaa_sea_level_trends t
JOIN gold_noaa_storm_surge_summary s
    ON t.state = s.state
JOIN gold_doi_managed_lands d
    ON t.state = d.state
    AND d.site_type IN ('National Wildlife Refuge', 'National Seashore')
ORDER BY t.sea_level_trend_mm_yr DESC
```

---

## Microsoft Published Resources

| Resource | URL | Relevance |
|----------|-----|-----------|
| Real-Time Intelligence in Microsoft Fabric | https://learn.microsoft.com/fabric/real-time-intelligence/overview | Streaming weather observation ingestion and KQL anomaly detection |
| Medallion Architecture in Fabric | https://learn.microsoft.com/fabric/onelake/onelake-medallion-lakehouse-architecture | Bronze/Silver/Gold pattern for weather data pipeline |
| Azure IoT Hub Reference Architecture | https://learn.microsoft.com/azure/architecture/reference-architectures/iot | Sensor data ingestion pattern applicable to weather stations |
| Stream Analytics Windowing Functions | https://learn.microsoft.com/azure/stream-analytics/stream-analytics-window-functions | Tumbling/sliding windows for seasonal pattern detection |
| Power BI Map Visualizations | https://learn.microsoft.com/power-bi/visuals/power-bi-map-tips-and-tricks | Geographic storm density and climate anomaly mapping |
| Microsoft Fabric Activator | https://learn.microsoft.com/fabric/real-time-intelligence/data-activator/activator-introduction | Alert triggering when anomaly thresholds are exceeded |

---

## Published References

| Reference | Source | URL |
|-----------|--------|-----|
| Storm Events Database | NOAA/NCEI | https://www.ncdc.noaa.gov/stormevents/ |
| Climate Data Online | NOAA/NCEI | https://www.ncei.noaa.gov/cdo-web/ |
| U.S. Climate Normals (1991-2020) | NOAA/NCEI | https://www.ncei.noaa.gov/products/land-based-station/us-climate-normals |
| CO-OPS Tides and Currents API | NOAA | https://tidesandcurrents.noaa.gov/api/ |
| NDBC Observation Data | NOAA | https://www.ndbc.noaa.gov/data/ |
| Weather.gov API Documentation | NWS | https://www.weather.gov/documentation/services-web-api |
| Sea Level Trends | NOAA/CO-OPS | https://tidesandcurrents.noaa.gov/sltrends/ |

---

## Related Documentation

- [Antitrust Analytics](antitrust-analytics.md) - DOJ market concentration (cross-reference with weather-driven economic disruption)
- [Federal Justice Analytics](federal-justice-analytics.md) - Federal enforcement patterns
- [Best Practices: Real-Time Intelligence](../features/real-time-intelligence.md) - Streaming architecture for weather observation ingestion
- [Best Practices: Medallion Architecture](../best-practices/medallion-architecture-deep-dive.md) - Bronze/Silver/Gold patterns for time-series weather data
- [Best Practices: Monitoring & Observability](../best-practices/monitoring-observability.md) - Alerting on climate anomaly thresholds
- [Tutorial 27: NOAA Bronze Ingestion](../../tutorials/27-noaa-bronze-ingestion.md) - Step-by-step NOAA data loading

---

*Last Updated: 2026-04-23*
