# Transportation Safety Analytics

> Leveraging Microsoft Fabric to analyze aviation incident patterns, airline on-time performance, and surface transportation crash data using publicly available DOT, FAA, NTSB, and NHTSA datasets.

---

## Executive Summary

Transportation safety oversight in the United States spans multiple agencies under the Department of Transportation umbrella. The Federal Aviation Administration (FAA) oversees aviation safety and airspace management, the National Transportation Safety Board (NTSB) investigates accidents across all transportation modes, the Bureau of Transportation Statistics (BTS) tracks airline operational performance, and the National Highway Traffic Safety Administration (NHTSA) maintains the most comprehensive motor vehicle crash fatality database in the world. Each agency publishes rich, publicly available datasets — yet cross-agency analysis remains rare because these systems were never designed to interoperate.

Microsoft Fabric's unified analytics platform eliminates this fragmentation by bringing aviation incident reports, airline delay data, crash fatality statistics, and weather observations into a single lakehouse with medallion architecture. The result is a transportation safety intelligence layer that enables:

- **Aviation incident trend analysis** correlating NASA ASRS voluntary reports with NTSB accident investigations to identify emerging risk patterns before they become fatal events
- **Airline operational reliability scoring** using BTS on-time performance data to rank carriers, routes, and airports by delay severity and cancellation rates
- **Surface transportation crash analytics** leveraging NHTSA FARS data to model fatality risk by geography, time of day, vehicle type, and contributing factors
- **Cross-modal safety correlation** linking aviation weather delays to surface crash spikes during the same storm systems, enabling coordinated safety response

This use case demonstrates how the Supercharge Microsoft Fabric POC's PySpark notebooks, Delta Lake storage, and Power BI visualizations apply to transportation safety analytics using real, publicly available data sources.

---

## Data Sources

### Primary Sources

| Source | Agency | URL | Data Available |
|--------|--------|-----|----------------|
| Aviation Safety Reporting System (ASRS) | NASA/FAA | https://asrs.arc.nasa.gov | Voluntary confidential incident reports from pilots, controllers, mechanics — 1.9M+ reports since 1976 |
| Airline On-Time Performance | BTS | https://transtats.bts.gov/Tables.asp?QO_VQ=EFD | Flight-level delay, cancellation, and diversion data for all U.S. carriers — 12M+ records/year |
| Fatality Analysis Reporting System (FARS) | NHTSA | https://crashstats.nhtsa.dot.gov/Api/Public/ViewApis | Census of all fatal motor vehicle crashes in the U.S. since 1975 — 30K-40K fatalities/year |
| NTSB Aviation Accident Database | NTSB | https://data.ntsb.gov/avdata | Investigated aviation accidents and incidents with probable cause determinations |
| FAA Accident & Incident Data | FAA | https://www.asias.faa.gov/pls/apex/f?p=100:1 | FAA-reported accidents, incidents, and enforcement actions |

### Supporting Sources

| Source | Agency | URL | Use In Analytics |
|--------|--------|-----|------------------|
| NOAA Integrated Surface Data | NOAA | https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database | Weather conditions at incident time/location for causal correlation |
| FAA Operations Network (OPSNET) | FAA | https://aspm.faa.gov/opsnet/sys/main.asp | Airport operations counts, delay causes by facility |
| BTS National Transportation Statistics | BTS | https://www.bts.gov/topics/national-transportation-statistics | Historical trend data across all modes |
| FHWA Highway Statistics | FHWA | https://www.fhwa.dot.gov/policyinformation/statistics.cfm | Vehicle miles traveled, road infrastructure context |
| EPA Air Quality System | EPA | https://aqs.epa.gov/aqsweb/airdata/download_files.html | Airport-area air quality for emissions analysis |
| GIS Transportation Data | BTS | https://data-usdot.opendata.arcgis.com | Geospatial layers for airports, roads, transit systems |

---

## Aviation Incident Trend Analysis

### Background

The NASA Aviation Safety Reporting System (ASRS) is the world's largest voluntary confidential safety reporting program. Pilots, air traffic controllers, flight attendants, and maintenance technicians submit reports describing safety-related events without fear of enforcement action. This dataset is uniquely valuable because it captures near-miss events and systemic hazards that never appear in accident databases. The ASRS database contains over 1.9 million reports since 1976, categorized by event type, contributing factors, aircraft type, and flight phase.

Analyzing ASRS report trends over time reveals shifts in the aviation safety landscape — from the rise of runway incursion reports in the 2000s to the recent increase in unmanned aircraft system (UAS) encounter reports.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Aviation Incident Trend Analysis
# MAGIC Analyze ASRS incident reports by category, severity, and temporal patterns.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Load ASRS incident data from bronze layer
df_asrs = spark.read.format("delta").load(
    "Tables/bronze_dot_asrs_incidents"
)

# Parse report date and extract temporal features
df_asrs_enriched = (
    df_asrs
    .withColumn("report_date", F.to_date("report_date_str", "yyyy-MM-dd"))
    .withColumn("report_year", F.year("report_date"))
    .withColumn("report_month", F.month("report_date"))
    .withColumn("report_quarter", F.quarter("report_date"))
    .filter(F.col("report_year") >= 2015)
)

# Aggregate incident counts by category and year
df_incident_trends = (
    df_asrs_enriched
    .groupBy("report_year", "event_type", "contributing_factor_primary")
    .agg(
        F.count("*").alias("incident_count"),
        F.countDistinct("report_id").alias("unique_reports"),
        F.countDistinct("aircraft_type").alias("aircraft_types_involved")
    )
    .orderBy("report_year", F.desc("incident_count"))
)

# Calculate year-over-year change using window functions
window_yoy = Window.partitionBy("event_type").orderBy("report_year")
df_incident_trends = df_incident_trends.withColumn(
    "yoy_change_pct",
    F.round(
        (F.col("incident_count") - F.lag("incident_count").over(window_yoy))
        / F.lag("incident_count").over(window_yoy) * 100, 2
    )
)

# Identify top emerging risk categories (fastest-growing incident types)
df_emerging_risks = (
    df_incident_trends
    .filter(F.col("report_year") == 2024)
    .filter(F.col("yoy_change_pct") > 10)
    .orderBy(F.desc("yoy_change_pct"))
    .limit(10)
)

display(df_emerging_risks)

# Write to silver layer
df_incident_trends.write.format("delta").mode("overwrite").saveAsTable(
    "lh_silver.silver_dot_asrs_incident_trends"
)
```

---

## Airline On-Time Performance Analysis

### Background

The Bureau of Transportation Statistics (BTS) collects on-time performance data from all U.S. air carriers with at least one percent of total domestic scheduled passenger revenue. This dataset covers every domestic flight operated by reporting carriers — approximately 12 million flight records per year. Each record includes scheduled and actual departure/arrival times, delay causes (carrier, weather, NAS, security, late aircraft), cancellation reasons, and diversion indicators.

This data enables granular analysis of airline reliability, airport congestion patterns, and the cascading effects of delays through hub-and-spoke networks. The five FAA-defined delay categories allow attribution of delay minutes to specific root causes.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Airline Delay Pattern Analysis
# MAGIC Analyze BTS on-time performance by carrier, airport, and delay cause.

# COMMAND ----------

from pyspark.sql import functions as F

# Load BTS on-time performance data
df_flights = spark.read.format("delta").load(
    "Tables/bronze_dot_bts_ontime_performance"
)

# Calculate delay metrics per carrier per month
df_carrier_performance = (
    df_flights
    .filter(F.col("year") >= 2020)
    .groupBy("year", "month", "reporting_airline", "reporting_airline_name")
    .agg(
        F.count("*").alias("total_flights"),
        F.sum(F.when(F.col("dep_del15") == 1, 1).otherwise(0)).alias("delayed_flights"),
        F.sum(F.when(F.col("cancelled") == 1, 1).otherwise(0)).alias("cancelled_flights"),
        F.sum(F.when(F.col("diverted") == 1, 1).otherwise(0)).alias("diverted_flights"),
        F.avg("arr_delay_minutes").alias("avg_arrival_delay_min"),
        F.sum("carrier_delay").alias("total_carrier_delay_min"),
        F.sum("weather_delay").alias("total_weather_delay_min"),
        F.sum("nas_delay").alias("total_nas_delay_min"),
        F.sum("security_delay").alias("total_security_delay_min"),
        F.sum("late_aircraft_delay").alias("total_late_aircraft_delay_min")
    )
)

# Compute on-time performance rate and reliability score
df_carrier_performance = (
    df_carrier_performance
    .withColumn(
        "on_time_pct",
        F.round((F.col("total_flights") - F.col("delayed_flights") - F.col("cancelled_flights"))
                / F.col("total_flights") * 100, 2)
    )
    .withColumn(
        "cancellation_rate_pct",
        F.round(F.col("cancelled_flights") / F.col("total_flights") * 100, 2)
    )
    .withColumn(
        "reliability_score",
        F.round(
            F.col("on_time_pct") * 0.6
            + (100 - F.col("cancellation_rate_pct")) * 0.3
            + F.least(F.lit(100), F.lit(100) - F.col("avg_arrival_delay_min")) * 0.1,
            2
        )
    )
)

# Airport congestion analysis — top 30 busiest airports
df_airport_delays = (
    df_flights
    .filter(F.col("year") == 2024)
    .groupBy("origin", "origin_city_name")
    .agg(
        F.count("*").alias("departures"),
        F.avg("dep_delay_minutes").alias("avg_dep_delay"),
        F.percentile_approx("dep_delay_minutes", 0.95).alias("p95_dep_delay"),
        F.sum(F.when(F.col("cancelled") == 1, 1).otherwise(0)).alias("cancellations")
    )
    .orderBy(F.desc("departures"))
    .limit(30)
)

display(df_airport_delays)

# Write to silver layer
df_carrier_performance.write.format("delta").mode("overwrite").saveAsTable(
    "lh_silver.silver_dot_carrier_performance"
)
```

---

## Surface Transportation Crash Analytics

### Background

The Fatality Analysis Reporting System (FARS) is a nationwide census of all police-reported fatal motor vehicle crashes in the United States. Maintained by NHTSA since 1975, FARS contains data on over 1.8 million fatal crashes and 2 million fatalities. Every record includes crash circumstances (time, location, weather, road type), vehicle information (make, model, year, damage), and person-level data (age, sex, restraint use, alcohol involvement, injury severity).

FARS data reveals critical patterns: rural roads account for a disproportionate share of fatalities despite lower traffic volumes, alcohol-impaired driving fatalities spike on weekends and holidays, and pedestrian/cyclist fatalities have been rising steadily since 2009. Combining FARS with highway vehicle miles traveled (VMT) data from FHWA yields fatality rates that normalize for exposure.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # NHTSA FARS Crash Fatality Analytics
# MAGIC Analyze fatal crash patterns by geography, time, and contributing factors.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Load FARS accident-level data
df_crashes = spark.read.format("delta").load(
    "Tables/bronze_dot_fars_accidents"
)

# Load FARS person-level data for impairment and restraint analysis
df_persons = spark.read.format("delta").load(
    "Tables/bronze_dot_fars_persons"
)

# Crash severity and temporal analysis
df_crash_analysis = (
    df_crashes
    .filter(F.col("year") >= 2018)
    .withColumn("crash_hour", F.col("hour").cast("int"))
    .withColumn("is_weekend", F.when(
        F.dayofweek("crash_date").isin(1, 7), True
    ).otherwise(False))
    .withColumn("is_nighttime", F.when(
        (F.col("crash_hour") >= 20) | (F.col("crash_hour") <= 5), True
    ).otherwise(False))
    .groupBy("year", "state_name", "is_weekend", "is_nighttime")
    .agg(
        F.count("*").alias("fatal_crashes"),
        F.sum("fatals").alias("total_fatalities"),
        F.sum(F.when(F.col("drunk_dr") > 0, 1).otherwise(0)).alias("alcohol_involved_crashes"),
        F.avg("fatals").alias("avg_fatalities_per_crash")
    )
)

# Impairment analysis from person-level data
df_impairment = (
    df_persons
    .filter(F.col("year") >= 2018)
    .filter(F.col("per_typ") == 1)  # Drivers only
    .groupBy("year", "state_name")
    .agg(
        F.count("*").alias("total_drivers_in_fatal_crashes"),
        F.sum(F.when(F.col("drinking") == 1, 1).otherwise(0)).alias("drinking_drivers"),
        F.sum(F.when(F.col("drugs") == 1, 1).otherwise(0)).alias("drug_positive_drivers"),
        F.sum(F.when(F.col("rest_use").isin(0, 7, 8), 1).otherwise(0)).alias("unrestrained_drivers")
    )
    .withColumn(
        "impaired_driving_pct",
        F.round(F.col("drinking_drivers") / F.col("total_drivers_in_fatal_crashes") * 100, 2)
    )
)

# Fatality rate per 100M VMT by state (requires FHWA VMT join)
df_fatality_rates = (
    df_crash_analysis
    .groupBy("year", "state_name")
    .agg(F.sum("total_fatalities").alias("annual_fatalities"))
)

display(df_crash_analysis.orderBy("year", F.desc("total_fatalities")))

# Write to gold layer
df_crash_analysis.write.format("delta").mode("overwrite").saveAsTable(
    "lh_gold.gold_dot_crash_fatality_analysis"
)
df_impairment.write.format("delta").mode("overwrite").saveAsTable(
    "lh_gold.gold_dot_driver_impairment_analysis"
)
```

---

## Implementation in Fabric

### Table Inventory

| Layer | Table | Source | Description |
|-------|-------|--------|-------------|
| Bronze | `bronze_dot_asrs_incidents` | ASRS | Raw aviation safety reports with narrative text, event types, contributing factors |
| Bronze | `bronze_dot_bts_ontime_performance` | BTS | Flight-level on-time, delay cause, cancellation, and diversion records |
| Bronze | `bronze_dot_fars_accidents` | NHTSA | Accident-level fatal crash records with location, time, conditions |
| Bronze | `bronze_dot_fars_persons` | NHTSA | Person-level records (drivers, passengers, pedestrians) for each fatal crash |
| Bronze | `bronze_dot_fars_vehicles` | NHTSA | Vehicle-level records with make, model, damage, maneuver |
| Bronze | `bronze_dot_ntsb_aviation_accidents` | NTSB | Investigated aviation accident records with probable cause |
| Bronze | `bronze_noaa_weather_observations` | NOAA | Hourly weather observations for correlation with incidents |
| Silver | `silver_dot_asrs_incident_trends` | ASRS | Aggregated incident trends by category, year, contributing factor |
| Silver | `silver_dot_carrier_performance` | BTS | Monthly carrier performance metrics with reliability scores |
| Silver | `silver_dot_airport_delay_metrics` | BTS | Airport-level delay statistics with percentile distributions |
| Silver | `silver_dot_fars_crash_enriched` | NHTSA | Cleansed crash records joined with person/vehicle data, geocoded |
| Silver | `silver_dot_ntsb_accidents_enriched` | NTSB | Accident records joined with weather and airport data |
| Gold | `gold_dot_crash_fatality_analysis` | NHTSA | Fatality analysis by state, time period, impairment factors |
| Gold | `gold_dot_driver_impairment_analysis` | NHTSA | Driver impairment rates by state and year |
| Gold | `gold_dot_carrier_reliability_scorecard` | BTS | Carrier reliability rankings with composite scoring |
| Gold | `gold_dot_aviation_safety_dashboard` | ASRS/NTSB | Combined aviation safety metrics for executive reporting |
| Gold | `gold_dot_weather_safety_correlation` | Multi | Cross-domain weather impact on aviation and surface safety |

### Notebook Sequence

1. `01_bronze_dot_asrs_incidents.py` — Ingest ASRS incident report data with schema enforcement
2. `02_bronze_dot_bts_ontime.py` — Ingest BTS airline on-time performance monthly files
3. `03_bronze_dot_fars_accidents.py` — Ingest NHTSA FARS accident, person, and vehicle files
4. `04_bronze_dot_ntsb_aviation.py` — Ingest NTSB aviation accident database records
5. `05_silver_dot_asrs_trends.py` — Aggregate ASRS incidents by category with YoY change
6. `06_silver_dot_carrier_performance.py` — Calculate carrier reliability scores and delay attribution
7. `07_silver_dot_fars_enrichment.py` — Join crash/person/vehicle tables, geocode, cleanse
8. `08_gold_dot_crash_fatality_analysis.py` — State-level fatality analysis with impairment metrics
9. `09_gold_dot_carrier_scorecard.py` — Carrier reliability rankings and route-level analysis
10. `10_gold_dot_aviation_safety_dashboard.py` — Combined aviation safety KPIs for executive layer
11. `11_gold_dot_weather_safety_correlation.py` — Cross-domain weather impact analysis

---

## Power BI Visualizations

### Recommended Visuals

| Page | Visual Type | Data | Purpose |
|------|-------------|------|---------|
| Aviation Safety Overview | Line chart + bar overlay | ASRS incident trends by year/category | Identify rising incident categories |
| Aviation Safety Overview | Treemap | Incident counts by contributing factor | Show relative frequency of safety factors |
| Airline Performance | Heatmap matrix | Carrier × month on-time percentage | Compare carrier reliability seasonally |
| Airline Performance | Scatter plot | Avg delay vs. cancellation rate by carrier | Identify worst-performing carriers |
| Airport Operations | Map (filled) | Airport delay severity by location | Geographic congestion patterns |
| Airport Operations | Waterfall chart | Delay minutes by cause category | Attribution of delay root causes |
| Highway Safety | Choropleth map | Fatality rate per 100M VMT by state | Identify high-risk states |
| Highway Safety | Line chart (dual axis) | Fatalities + impairment rate over time | Track safety improvement trends |
| Cross-Modal Analysis | Combo chart | Weather events vs. aviation delays vs. crash spikes | Correlate weather impact across modes |

### DAX Measures

```dax
// On-Time Performance Rate — percentage of flights arriving within 15 minutes of schedule
On-Time Performance Rate =
DIVIDE(
    CALCULATE(
        COUNTROWS('silver_dot_carrier_performance'),
        'silver_dot_carrier_performance'[on_time_pct] >= 85
    ),
    COUNTROWS('silver_dot_carrier_performance'),
    0
)
```

```dax
// Fatality Rate per 100 Million VMT — normalized crash severity metric
Fatality Rate per 100M VMT =
VAR _fatalities = SUM('gold_dot_crash_fatality_analysis'[total_fatalities])
VAR _vmt_hundreds_millions = DIVIDE(SUM('dim_state_vmt'[vehicle_miles_traveled]), 100000000, 1)
RETURN
    DIVIDE(_fatalities, _vmt_hundreds_millions, 0)
```

```dax
// Alcohol Involvement Rate — percentage of fatal crashes involving impaired drivers
Alcohol Involvement Rate =
DIVIDE(
    SUM('gold_dot_crash_fatality_analysis'[alcohol_involved_crashes]),
    SUM('gold_dot_crash_fatality_analysis'[fatal_crashes]),
    0
)
```

```dax
// Carrier Reliability Score — weighted composite of on-time, cancellation, and delay
Carrier Reliability Score =
VAR _ontime = AVERAGE('silver_dot_carrier_performance'[on_time_pct])
VAR _cancel = AVERAGE('silver_dot_carrier_performance'[cancellation_rate_pct])
VAR _delay = AVERAGE('silver_dot_carrier_performance'[avg_arrival_delay_min])
RETURN
    ROUND(
        _ontime * 0.6 + (100 - _cancel) * 0.3 + MIN(100, 100 - _delay) * 0.1,
        2
    )
```

---

## Cross-Domain Analysis

### Hypothesis 1: Weather Events Drive Correlated Aviation and Highway Safety Degradation

Severe weather systems simultaneously impact aviation operations (delays, diversions) and highway safety (increased crash fatality rates). By joining NOAA weather event data with BTS delay records and FARS crash data on date and geography, we can quantify the amplification effect of weather on multi-modal transportation risk.

```python
# Cross-domain: DOT × NOAA weather impact correlation
df_weather_events = spark.read.format("delta").load("Tables/bronze_noaa_storm_events")
df_flight_delays = spark.read.format("delta").load("Tables/silver_dot_carrier_performance")
df_fatal_crashes = spark.read.format("delta").load("Tables/gold_dot_crash_fatality_analysis")

# Join on date and state to correlate weather severity with safety outcomes
df_weather_safety = (
    df_weather_events
    .filter(F.col("event_type").isin("Winter Storm", "Thunderstorm", "Fog", "Ice Storm"))
    .groupBy("year", "month", "state")
    .agg(
        F.count("*").alias("severe_weather_events"),
        F.sum("deaths_direct").alias("weather_direct_deaths")
    )
    .join(
        df_fatal_crashes.groupBy("year", "state_name")
        .agg(F.sum("total_fatalities").alias("highway_fatalities")),
        (F.col("year") == F.col("year")) & (F.col("state") == F.col("state_name")),
        "inner"
    )
)

# Calculate correlation coefficient
correlation = df_weather_safety.stat.corr("severe_weather_events", "highway_fatalities")
print(f"Weather-Highway Fatality Correlation: {correlation:.4f}")
```

### Hypothesis 2: Transportation Emissions Correlate with Airport-Area Air Quality Degradation

Airports with higher operations volumes contribute to localized air quality issues. By joining FAA OPSNET airport operations counts with EPA Air Quality System (AQS) monitoring data for monitors near major airports, we can assess whether aviation activity correlates with elevated PM2.5, NOx, and ozone levels.

```python
# Cross-domain: DOT × EPA airport emissions impact
df_airport_ops = spark.read.format("delta").load("Tables/bronze_dot_faa_opsnet")
df_air_quality = spark.read.format("delta").load("Tables/bronze_epa_air_quality")

# Join airport operations with nearby air quality monitors
df_airport_emissions = (
    df_airport_ops
    .groupBy("year", "facility_id", "facility_name")
    .agg(F.sum("total_operations").alias("annual_operations"))
    .join(
        df_air_quality
        .filter(F.col("parameter_name") == "PM2.5 - Local Conditions")
        .groupBy("year", "county_name", "state_name")
        .agg(F.avg("arithmetic_mean").alias("avg_pm25")),
        on="year",
        how="inner"
    )
)
```

### Hypothesis 3: Airline Delay Cascades Impact Regional Economic Activity

Chronic airline delays at hub airports may correlate with reduced business travel efficiency and measurable economic effects. By joining BTS delay data with SBA lending activity and BEA regional GDP data, we can explore whether markets served by unreliable air service show different economic indicators.

---

## Microsoft Published Resources

| Resource | URL | Relevance |
|----------|-----|-----------|
| Azure IoT Reference Architecture | https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/iot | Reference pattern for real-time transportation telemetry ingestion via Fabric Eventstreams |
| Microsoft Fabric Security White Paper | https://learn.microsoft.com/en-us/fabric/security/security-overview | Security framework for handling PII in crash victim data and confidential ASRS reports |
| Cloud-Scale Analytics with Microsoft Fabric | https://learn.microsoft.com/en-us/fabric/get-started/microsoft-fabric-overview | Architecture guidance for building enterprise-scale transportation analytics |
| Power BI Embedded Analytics White Paper | https://learn.microsoft.com/en-us/power-bi/developer/embedded/embedded-analytics-power-bi | Embedding transportation safety dashboards in agency portals and public-facing sites |
| Medallion Architecture in Fabric | https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture | Best practice for Bronze/Silver/Gold layering of transportation safety data |
| Azure for Government Documentation | https://learn.microsoft.com/en-us/azure/azure-government/documentation-government-overview-wwps | FedRAMP compliance requirements for DOT/FAA data processing in government cloud |

---

## Published References

| Reference | URL | Description |
|-----------|-----|-------------|
| NASA ASRS Database Online | https://asrs.arc.nasa.gov/search/database.html | Searchable database of 1.9M+ voluntary aviation safety reports |
| BTS Airline On-Time Statistics | https://transtats.bts.gov/OT_Delay/OT_DelayCause1.asp | Monthly reporting of flight delays by cause for all U.S. carriers |
| NHTSA FARS Encyclopedia | https://www-fars.nhtsa.dot.gov/Main/index.aspx | Interactive query tool for fatal crash data 1994-present |
| NHTSA FARS API | https://crashstats.nhtsa.dot.gov/Api/Public/ViewApis | RESTful API access to FARS data products |
| NTSB Aviation Accident Database | https://data.ntsb.gov/avdata | Downloadable aviation accident investigation data |
| BTS TranStats | https://transtats.bts.gov | Portal for all Bureau of Transportation Statistics datasets |
| FAA ASIAS (Aviation Safety Information Analysis and Sharing) | https://www.asias.faa.gov | FAA's safety data integration and analysis system |
| FHWA Highway Statistics Series | https://www.fhwa.dot.gov/policyinformation/statistics.cfm | Annual vehicle miles traveled and road infrastructure data |

---

## Related Documentation

- [Federal Justice Analytics](federal-justice-analytics.md) — DOJ law enforcement analytics patterns
- [Antitrust Analytics](antitrust-analytics.md) — DOJ market concentration and enforcement analysis
- [NOAA Weather Notebooks](../../notebooks/bronze/12_bronze_noaa_storm_events.py) — Weather data ingestion for cross-domain correlation
- [EPA Air Quality Notebooks](../../notebooks/bronze/14_bronze_epa_air_quality.py) — Air quality data for emissions analysis
- [Medallion Architecture Deep Dive](../best-practices/medallion-architecture-deep-dive.md) — Bronze/Silver/Gold layering patterns
- [Real-Time Intelligence](../features/real-time-intelligence.md) — Eventstream patterns for streaming transportation telemetry
- [Network Security Best Practices](../best-practices/network-security.md) — Securing PII in crash victim data

---

*Last Updated: 2026-04-23*
