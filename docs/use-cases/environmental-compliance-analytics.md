---
hero: assets/heroes/energy-utilities.svg
hero_alt: Environmental compliance + EPA AQI
type: feature
---
# Environmental Compliance Analytics

> Leveraging Microsoft Fabric to unify EPA air quality monitoring, toxic release tracking, enforcement compliance, and greenhouse gas reporting into a single analytical platform for environmental risk assessment and regulatory intelligence.

---

## Executive Summary

The U.S. Environmental Protection Agency (EPA) manages one of the most complex regulatory data ecosystems in the federal government. Air quality monitoring stations generate millions of hourly observations through the Air Quality System (AQS), while the Toxics Release Inventory (TRI) tracks billions of pounds of chemical releases from over 21,000 facilities annually. Enforcement compliance data in ECHO spans hundreds of thousands of regulated facilities under the Clean Air Act, Clean Water Act, and RCRA, and the Greenhouse Gas Reporting Program (GHGRP) captures emissions from facilities representing roughly 85% of U.S. greenhouse gas output. These datasets are currently siloed across separate EPA systems with incompatible schemas, inconsistent update schedules, and no unified analytical layer.

Microsoft Fabric transforms EPA environmental compliance analysis by providing a lakehouse architecture that unifies these disparate data streams into a single analytical platform. The medallion architecture enables raw ingestion of AQS sensor readings, TRI facility reports, ECHO compliance records, SDWIS water system violations, and GHGRP emissions data at the Bronze layer, cleansing and standardization at the Silver layer, and business-ready KPIs at the Gold layer. This use case demonstrates how:

- **Real-time Air Quality Index (AQI) calculation** from hourly pollutant readings across 4,000+ monitoring stations nationwide
- **Toxic release trend analysis** identifying facilities with increasing chemical discharge patterns over multi-year windows
- **Compliance violation scoring** that aggregates enforcement actions across all EPA programs into a unified facility risk profile
- **Emissions intensity benchmarking** normalizing greenhouse gas output by industry sector, revenue, and production volume

---

## Data Sources

### Primary Sources

| Source | Agency | URL | Data Available |
|--------|--------|-----|----------------|
| Air Quality System (AQS) API | EPA | https://aqs.epa.gov/data/api | Hourly/daily/annual criteria pollutant measurements from 4,000+ stations |
| Toxics Release Inventory (TRI) | EPA | https://enviro.epa.gov/triexplorer | Annual chemical release data from 21,000+ reporting facilities |
| ECHO Enforcement Data | EPA | https://echo.epa.gov | Compliance status, inspections, violations, and enforcement actions |
| Safe Drinking Water (SDWIS) | EPA | https://sdwis.epa.gov | Public water system violations, contaminant monitoring, health advisories |
| Greenhouse Gas Reporting (GHGRP) | EPA | https://ghgdata.epa.gov | Facility-level GHG emissions by gas type, industry, and methodology |

### Supporting Sources

| Source | Agency | URL | Use In Analytics |
|--------|--------|-----|------------------|
| NEI Emissions Inventory | EPA | https://www.epa.gov/air-emissions-inventories | Comprehensive emissions estimates by source category |
| Envirofacts API | EPA | https://enviro.epa.gov | Consolidated EPA facility data and cross-program linkage |
| EJSCREEN | EPA | https://www.epa.gov/ejscreen | Environmental justice demographic and environmental indicators |
| Census TIGER/Line | Census | https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html | Geographic boundary files for spatial analysis |
| NAICS Codes | Census | https://www.census.gov/naics | Industry classification for facility sector analysis |
| Energy Information (EIA) | DOE | https://www.eia.gov/opendata | Energy production and consumption for intensity normalization |

---

## Air Quality Index (AQI) Analytics

### Background

The Air Quality Index is the EPA's standardized measure for communicating daily air quality to the public. It translates pollutant concentrations for six criteria pollutants — PM2.5, PM10, Ozone, NO₂, SO₂, and CO — into a 0–500 scale using EPA-defined breakpoint tables. The AQS API provides hourly and daily summary data from monitoring stations operated by state, local, and tribal agencies under federal reference methods.

AQI calculation requires mapping raw pollutant concentrations to breakpoint ranges and applying the linear interpolation formula specified in 40 CFR Part 58, Appendix G. The composite AQI for a location is the maximum AQI across all measured pollutants.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze → Silver: AQI Calculation from AQS Hourly Data
# MAGIC Calculates Air Quality Index from raw pollutant concentrations
# MAGIC using EPA breakpoint tables per 40 CFR Part 58 Appendix G.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, StringType, StructType, StructField

# EPA AQI Breakpoint Table (PM2.5 24-hour, µg/m³)
# Source: https://aqs.epa.gov/aqsweb/documents/codetables/aqi_breakpoints.html
aqi_breakpoints_pm25 = [
    (0.0, 12.0, 0, 50, "Good"),
    (12.1, 35.4, 51, 100, "Moderate"),
    (35.5, 55.4, 101, 150, "Unhealthy for Sensitive Groups"),
    (55.5, 150.4, 151, 200, "Unhealthy"),
    (150.5, 250.4, 201, 300, "Very Unhealthy"),
    (250.5, 500.4, 301, 500, "Hazardous"),
]

breakpoint_schema = StructType([
    StructField("conc_lo", DoubleType()),
    StructField("conc_hi", DoubleType()),
    StructField("aqi_lo", DoubleType()),
    StructField("aqi_hi", DoubleType()),
    StructField("category", StringType()),
])

df_bp = spark.createDataFrame(aqi_breakpoints_pm25, schema=breakpoint_schema)

# COMMAND ----------

# Read Bronze AQS hourly data
df_aqs = spark.read.format("delta").load(
    "Tables/bronze_epa_aqs_hourly"
)

# Calculate AQI using EPA linear interpolation formula:
# AQI = ((AQI_hi - AQI_lo) / (Conc_hi - Conc_lo)) * (Conc - Conc_lo) + AQI_lo
df_aqi = (
    df_aqs
    .filter(F.col("parameter_code") == "88101")  # PM2.5
    .crossJoin(df_bp)
    .filter(
        (F.col("sample_measurement") >= F.col("conc_lo")) &
        (F.col("sample_measurement") <= F.col("conc_hi"))
    )
    .withColumn(
        "aqi_value",
        ((F.col("aqi_hi") - F.col("aqi_lo")) /
         (F.col("conc_hi") - F.col("conc_lo"))) *
        (F.col("sample_measurement") - F.col("conc_lo")) +
        F.col("aqi_lo")
    )
    .withColumn("aqi_value", F.round(F.col("aqi_value")).cast("int"))
    .select(
        "state_code", "county_code", "site_number",
        "date_local", "time_local", "sample_measurement",
        "aqi_value", "category", "latitude", "longitude"
    )
)

# Write to Silver
df_aqi.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable("lh_silver.silver_epa_aqi_calculated")

print(f"AQI records calculated: {df_aqi.count()}")
```

---

## Toxic Release Inventory (TRI) Facility Analysis

### Background

The Toxics Release Inventory is a publicly available dataset mandated by the Emergency Planning and Community Right-to-Know Act (EPCRA) Section 313. Facilities in covered industry sectors (manufacturing, mining, electric utilities, and others) that manufacture, process, or otherwise use listed toxic chemicals above reporting thresholds must file annual TRI reports. The dataset captures on-site releases to air, water, and land, as well as off-site transfers for disposal, treatment, and recycling.

TRI analysis enables identification of facilities with increasing release trends, high-risk chemical usage patterns, and potential environmental justice concerns when overlaid with demographic data from EJSCREEN.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Silver → Gold: TRI Facility Release Trend Analysis
# MAGIC Identifies facilities with increasing toxic release patterns
# MAGIC over rolling 5-year windows for regulatory priority targeting.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Read Silver TRI data (cleansed, deduplicated)
df_tri = spark.read.format("delta").load("Tables/silver_epa_tri_releases")

# Calculate facility-level annual release totals
df_facility_annual = (
    df_tri
    .groupBy("trifid", "facility_name", "state", "county",
             "naics_code", "reporting_year", "latitude", "longitude")
    .agg(
        F.sum("total_releases_lbs").alias("total_releases_lbs"),
        F.sum("fugitive_air_lbs").alias("fugitive_air_lbs"),
        F.sum("stack_air_lbs").alias("stack_air_lbs"),
        F.sum("water_discharge_lbs").alias("water_discharge_lbs"),
        F.sum("land_disposal_lbs").alias("land_disposal_lbs"),
        F.countDistinct("chemical_name").alias("distinct_chemicals"),
        F.collect_set("chemical_name").alias("chemicals_reported"),
    )
)

# Calculate 5-year rolling trend using linear regression slope
year_window = Window.partitionBy("trifid").orderBy("reporting_year")

df_trend = (
    df_facility_annual
    .withColumn("year_rank", F.row_number().over(year_window))
    .withColumn("releases_prev_year", F.lag("total_releases_lbs").over(year_window))
    .withColumn(
        "yoy_change_pct",
        F.when(
            F.col("releases_prev_year") > 0,
            ((F.col("total_releases_lbs") - F.col("releases_prev_year"))
             / F.col("releases_prev_year") * 100)
        ).otherwise(None)
    )
)

# Identify facilities with consistently increasing releases (3+ consecutive years)
increasing_window = Window.partitionBy("trifid").orderBy("reporting_year").rowsBetween(-2, 0)

df_flagged = (
    df_trend
    .withColumn("increasing_flag", F.when(F.col("yoy_change_pct") > 0, 1).otherwise(0))
    .withColumn("consecutive_increases", F.sum("increasing_flag").over(increasing_window))
    .withColumn(
        "risk_tier",
        F.when(F.col("consecutive_increases") >= 3, "HIGH")
        .when(F.col("consecutive_increases") == 2, "MEDIUM")
        .otherwise("LOW")
    )
)

# Write Gold aggregation
df_flagged.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable("lh_gold.gold_epa_tri_facility_trends")

high_risk = df_flagged.filter(F.col("risk_tier") == "HIGH").select("trifid").distinct().count()
print(f"High-risk facilities (3+ consecutive years increasing): {high_risk}")
```

---

## Enforcement Compliance Violation Scoring

### Background

The EPA's Enforcement and Compliance History Online (ECHO) system integrates compliance data from the Clean Air Act (CAA), Clean Water Act (CWA), Resource Conservation and Recovery Act (RCRA), and Safe Drinking Water Act (SDWA). Each regulated facility has compliance status indicators, inspection histories, and enforcement action records. Synthesizing these across programs into a unified compliance risk score enables prioritized resource allocation for inspectors and enforcement attorneys.

The composite scoring model weights violation severity, recency, frequency, and responsiveness to produce a 0–100 risk score per facility.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Gold: Multi-Program Compliance Risk Scoring
# MAGIC Calculates a composite 0-100 compliance risk score per facility
# MAGIC across CAA, CWA, RCRA, and SDWA enforcement programs.

# COMMAND ----------

from pyspark.sql import functions as F

# Read Silver ECHO compliance data
df_echo = spark.read.format("delta").load("Tables/silver_epa_echo_compliance")

# Define severity weights by violation type
severity_weights = {
    "HPV": 10.0,   # High Priority Violation (CAA)
    "SNC": 10.0,   # Significant Non-Compliance (CWA)
    "SNY": 8.0,    # Significant Non-Complier (RCRA)
    "SV":  6.0,    # Serious Violator (SDWA)
    "V":   3.0,    # Violation
    "N":   0.0,    # No Violation
}

# Calculate component scores
df_scored = (
    df_echo
    .withColumn(
        "severity_score",
        F.when(F.col("compliance_status") == "HPV", 10.0)
        .when(F.col("compliance_status") == "SNC", 10.0)
        .when(F.col("compliance_status") == "SNY", 8.0)
        .when(F.col("compliance_status") == "SV", 6.0)
        .when(F.col("compliance_status") == "V", 3.0)
        .otherwise(0.0)
    )
    .withColumn(
        "recency_weight",
        F.when(F.datediff(F.current_date(), F.col("violation_date")) <= 365, 1.0)
        .when(F.datediff(F.current_date(), F.col("violation_date")) <= 730, 0.7)
        .when(F.datediff(F.current_date(), F.col("violation_date")) <= 1095, 0.4)
        .otherwise(0.2)
    )
    .withColumn("weighted_severity", F.col("severity_score") * F.col("recency_weight"))
)

# Aggregate to facility level
df_facility_risk = (
    df_scored
    .groupBy("registry_id", "facility_name", "state", "city",
             "zip_code", "latitude", "longitude")
    .agg(
        F.sum("weighted_severity").alias("raw_risk_score"),
        F.count("*").alias("total_violations"),
        F.countDistinct("program_code").alias("programs_violated"),
        F.max("violation_date").alias("most_recent_violation"),
        F.sum(F.when(F.col("compliance_status").isin("HPV", "SNC"), 1).otherwise(0))
            .alias("high_priority_count"),
    )
    .withColumn(
        "composite_risk_score",
        F.least(
            F.lit(100),
            F.round(
                F.col("raw_risk_score") +
                (F.col("programs_violated") * 5) +
                (F.col("high_priority_count") * 3)
            )
        ).cast("int")
    )
    .withColumn(
        "risk_category",
        F.when(F.col("composite_risk_score") >= 75, "CRITICAL")
        .when(F.col("composite_risk_score") >= 50, "HIGH")
        .when(F.col("composite_risk_score") >= 25, "MODERATE")
        .otherwise("LOW")
    )
)

df_facility_risk.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable("lh_gold.gold_epa_facility_risk_scores")

critical = df_facility_risk.filter(F.col("risk_category") == "CRITICAL").count()
print(f"Critical-risk facilities: {critical}")
```

---

## Implementation in Fabric

### Table Inventory

| Layer | Table | Source | Description |
|-------|-------|--------|-------------|
| Bronze | `bronze_epa_aqs_hourly` | AQS API | Raw hourly criteria pollutant measurements |
| Bronze | `bronze_epa_aqs_monitors` | AQS API | Monitor station metadata and location |
| Bronze | `bronze_epa_tri_releases` | TRI Explorer | Raw annual toxic release reports |
| Bronze | `bronze_epa_echo_compliance` | ECHO | Raw compliance and enforcement records |
| Bronze | `bronze_epa_sdwis_violations` | SDWIS | Raw drinking water violations |
| Bronze | `bronze_epa_ghgrp_emissions` | GHGRP | Raw facility greenhouse gas reports |
| Silver | `silver_epa_aqi_calculated` | AQS Bronze | Calculated AQI with categories and coordinates |
| Silver | `silver_epa_tri_releases` | TRI Bronze | Cleansed, deduplicated facility releases |
| Silver | `silver_epa_echo_compliance` | ECHO Bronze | Standardized multi-program compliance records |
| Silver | `silver_epa_sdwis_violations` | SDWIS Bronze | Validated water system violation records |
| Silver | `silver_epa_ghgrp_normalized` | GHGRP Bronze | Emissions normalized by industry sector |
| Gold | `gold_epa_aqi_daily_summary` | AQI Silver | Daily AQI summaries by county with trends |
| Gold | `gold_epa_tri_facility_trends` | TRI Silver | Multi-year facility release trends with risk tiers |
| Gold | `gold_epa_facility_risk_scores` | ECHO Silver | Composite compliance risk scores 0–100 |
| Gold | `gold_epa_emissions_intensity` | GHGRP Silver | Emissions intensity by sector and facility |
| Gold | `gold_epa_environmental_justice` | All Silver | Environmental burden index by census tract |

### Notebook Sequence

1. `01_bronze_epa_aqs_ingest.py` — Ingest hourly AQS data via API pagination
2. `02_bronze_epa_tri_ingest.py` — Ingest TRI annual release files
3. `03_bronze_epa_echo_ingest.py` — Ingest ECHO compliance and enforcement records
4. `04_bronze_epa_sdwis_ingest.py` — Ingest SDWIS water system violations
5. `05_bronze_epa_ghgrp_ingest.py` — Ingest GHGRP facility emissions
6. `06_silver_epa_aqi_calculation.py` — Calculate AQI from raw measurements
7. `07_silver_epa_tri_cleansing.py` — Deduplicate and standardize TRI records
8. `08_silver_epa_echo_standardize.py` — Normalize multi-program compliance data
9. `09_silver_epa_sdwis_validate.py` — Validate and enrich water system records
10. `10_silver_epa_ghgrp_normalize.py` — Normalize emissions by sector and methodology
11. `11_gold_epa_aqi_summary.py` — Daily and annual AQI summaries by county
12. `12_gold_epa_tri_trends.py` — Facility release trend analysis with risk tiers
13. `13_gold_epa_risk_scoring.py` — Composite multi-program compliance risk scores
14. `14_gold_epa_emissions_intensity.py` — Emissions intensity benchmarking
15. `15_gold_epa_environmental_justice.py` — Environmental burden index by census tract

---

## Power BI Visualizations

### Recommended Visuals

| Page | Visual Type | Data | Purpose |
|------|-------------|------|---------|
| Air Quality Overview | Azure Map with heat layer | `gold_epa_aqi_daily_summary` | Geographic AQI distribution with color-coded severity |
| Air Quality Trends | Line chart + slicer | `gold_epa_aqi_daily_summary` | Multi-year AQI trends by county with pollutant filter |
| TRI Facility Dashboard | Scatter plot (bubble) | `gold_epa_tri_facility_trends` | Release volume vs. chemical count by risk tier |
| TRI Chemical Trends | Stacked area chart | `gold_epa_tri_facility_trends` | Annual release trends by media type (air/water/land) |
| Compliance Risk Map | Filled map with drill-through | `gold_epa_facility_risk_scores` | Facility risk scores by state with drill-through to detail |
| Compliance Scorecard | KPI cards + table | `gold_epa_facility_risk_scores` | Summary metrics: critical/high/moderate counts |
| Emissions Intensity | Clustered bar chart | `gold_epa_emissions_intensity` | Sector benchmarking of emissions per unit output |
| Environmental Justice | Choropleth map | `gold_epa_environmental_justice` | Census tract environmental burden index overlay |

### DAX Measures

```dax
// Weighted Average AQI by County (population-weighted)
Weighted Avg AQI =
VAR _Total =
    SUMX(
        gold_epa_aqi_daily_summary,
        gold_epa_aqi_daily_summary[aqi_value]
        * RELATED(dim_county[population])
    )
VAR _Pop = SUMX(gold_epa_aqi_daily_summary, RELATED(dim_county[population]))
RETURN
    DIVIDE(_Total, _Pop, BLANK())
```

```dax
// Facilities in Significant Non-Compliance (SNC Rate)
SNC Rate =
VAR _SNC =
    CALCULATE(
        COUNTROWS(gold_epa_facility_risk_scores),
        gold_epa_facility_risk_scores[high_priority_count] > 0
    )
VAR _Total = COUNTROWS(gold_epa_facility_risk_scores)
RETURN
    DIVIDE(_SNC, _Total, 0)
```

```dax
// Year-over-Year TRI Release Change
TRI YoY Change % =
VAR _Current =
    CALCULATE(
        SUM(gold_epa_tri_facility_trends[total_releases_lbs]),
        gold_epa_tri_facility_trends[reporting_year]
            = MAX(gold_epa_tri_facility_trends[reporting_year])
    )
VAR _Prior =
    CALCULATE(
        SUM(gold_epa_tri_facility_trends[total_releases_lbs]),
        gold_epa_tri_facility_trends[reporting_year]
            = MAX(gold_epa_tri_facility_trends[reporting_year]) - 1
    )
RETURN
    DIVIDE(_Current - _Prior, _Prior, BLANK())
```

```dax
// Emissions Intensity (metric tons CO2e per $M revenue)
Emissions Intensity =
DIVIDE(
    SUM(gold_epa_emissions_intensity[total_co2e_mt]),
    DIVIDE(SUM(gold_epa_emissions_intensity[facility_revenue]), 1000000, 1),
    BLANK()
)
```

---

## Cross-Domain Analysis

### Hypothesis 1: EPA × USDA — Agricultural Runoff and Water Quality

Agricultural operations are a leading source of nonpoint source water pollution. Correlating USDA crop production data (fertilizer application rates, livestock density) with EPA water quality violations from SDWIS and Clean Water Act enforcement in ECHO can identify agricultural regions where farming intensity predicts downstream water quality degradation.

```python
# Cross-domain: USDA crop intensity vs. EPA water violations by county
df_cross_ag = (
    df_usda_crop_production
    .join(df_epa_water_violations, on=["state_fips", "county_fips"])
    .groupBy("state", "county", "reporting_year")
    .agg(
        F.sum("total_fertilizer_tons").alias("fertilizer_intensity"),
        F.sum("livestock_head_count").alias("livestock_density"),
        F.count("violation_id").alias("water_violations"),
        F.avg("nitrate_concentration_mg_l").alias("avg_nitrate_level"),
    )
    .withColumn(
        "runoff_risk_score",
        (F.col("fertilizer_intensity") * 0.4) +
        (F.col("livestock_density") * 0.3) +
        (F.col("water_violations") * 0.3)
    )
)
```

### Hypothesis 2: EPA × DOI — Contamination on Federal Public Lands

The Department of the Interior manages over 500 million acres of public lands. EPA Superfund sites, TRI facilities, and abandoned mine lands on or adjacent to DOI-managed properties create environmental remediation obligations that span both agencies. Overlaying EPA facility data with DOI land boundary data from BLM and NPS identifies contamination hotspots on federal lands requiring interagency coordination.

```python
# Cross-domain: EPA contaminated facilities on DOI-managed lands
from pyspark.sql import functions as F

df_cross_lands = (
    df_epa_tri_facilities
    .join(
        df_doi_land_boundaries,
        (F.col("tri.latitude").between(F.col("land.lat_min"), F.col("land.lat_max"))) &
        (F.col("tri.longitude").between(F.col("land.lon_min"), F.col("land.lon_max")))
    )
    .groupBy("land_unit_name", "managing_bureau", "state")
    .agg(
        F.count("trifid").alias("tri_facilities_on_land"),
        F.sum("total_releases_lbs").alias("total_releases_on_land"),
        F.countDistinct("chemical_name").alias("distinct_chemicals"),
    )
    .orderBy(F.col("total_releases_on_land").desc())
)
```

### Hypothesis 3: EPA × DOJ — Environmental Crime Prosecution Outcomes

EPA enforcement referrals to the DOJ for criminal prosecution represent the most severe environmental violations. Linking EPA referral data from ECHO with DOJ case outcomes and USSC sentencing data reveals patterns in prosecution success rates, sentencing severity, and the deterrent effect of criminal enforcement on future facility compliance.

```sql
-- Cross-domain: EPA enforcement referrals to DOJ prosecution outcomes
SELECT
    e.facility_name,
    e.state,
    e.referral_date,
    j.case_number,
    j.disposition,
    j.sentence_months,
    j.fine_amount,
    post_compliance.composite_risk_score AS post_prosecution_risk
FROM gold_epa_facility_risk_scores e
JOIN gold_doj_criminal_cases j
    ON e.registry_id = j.epa_registry_id
LEFT JOIN gold_epa_facility_risk_scores post_compliance
    ON e.registry_id = post_compliance.registry_id
    AND post_compliance.assessment_year = YEAR(j.disposition_date) + 1
WHERE j.division = 'ENRD'  -- Environment and Natural Resources Division
ORDER BY j.fine_amount DESC
```

---

## Microsoft Published Resources

| Resource | URL | Relevance |
|----------|-----|-----------|
| Microsoft Cloud for Sustainability | https://learn.microsoft.com/en-us/industry/sustainability/overview | Sustainability data modeling patterns applicable to EPA emissions analytics |
| Azure Well-Architected Framework – Security | https://learn.microsoft.com/en-us/azure/well-architected/security/ | Security patterns for protecting sensitive environmental enforcement data |
| Cloud-Scale Analytics with Microsoft Fabric | https://learn.microsoft.com/en-us/azure/architecture/solution-ideas/articles/analytics-end-to-end | End-to-end analytics architecture reference for multi-source environmental data |
| Power BI Deployment and Governance White Paper | https://learn.microsoft.com/en-us/power-bi/guidance/whitepaper-powerbi-enterprise-deployment | Enterprise BI deployment patterns for multi-agency dashboards |
| Azure IoT Reference Architecture | https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/iot | IoT sensor ingestion patterns applicable to AQS real-time monitoring |
| Microsoft Fabric Security White Paper | https://learn.microsoft.com/en-us/fabric/security/white-paper-landing-page | Data protection for sensitive enforcement and compliance data |

---

## Published References

| Reference | URL | Description |
|-----------|-----|-------------|
| EPA AQS API Documentation | https://aqs.epa.gov/aqsweb/documents/data_api.html | Complete API reference for Air Quality System data access |
| TRI National Analysis | https://www.epa.gov/trinationalanalysis | EPA's annual analysis of TRI trends and findings |
| ECHO Data Downloads | https://echo.epa.gov/tools/data-downloads | Bulk compliance and enforcement data files |
| EJSCREEN Technical Documentation | https://www.epa.gov/ejscreen/technical-information-about-ejscreen | Methodology for environmental justice screening |
| GHGRP Data Publication | https://www.epa.gov/ghgreporting/data-sets | Greenhouse Gas Reporting Program public datasets |
| EPA AQI Breakpoint Tables | https://aqs.epa.gov/aqsweb/documents/codetables/aqi_breakpoints.html | Official AQI calculation breakpoints and methodology |
| 40 CFR Part 58 Appendix G | https://www.ecfr.gov/current/title-40/chapter-I/subchapter-C/part-58/appendix-Appendix%20G%20to%20Part%2058 | Federal regulation defining AQI uniform index |

---

## Related Documentation

- [Federal Justice Analytics](federal-justice-analytics.md) — DOJ enforcement data for environmental crime prosecution analysis
- [Antitrust Analytics](antitrust-analytics.md) — Cross-reference for corporate environmental violation patterns
- [Natural Resources Analytics](natural-resources-analytics.md) — DOI land management and contamination overlay
- [Tribal Health Analytics](tribal-health-analytics.md) — Environmental justice and health disparities on tribal lands
- [Data Governance Deep Dive](../best-practices/data-governance-deep-dive.md) — Purview lineage for EPA data pipelines
- [Real-Time Intelligence](../features/real-time-intelligence.md) — Eventstream patterns for AQS sensor data ingestion
- [Medallion Architecture Deep Dive](../best-practices/medallion-architecture-deep-dive.md) — Bronze/Silver/Gold patterns for environmental data

---

*Last Updated: 2026-04-23*
