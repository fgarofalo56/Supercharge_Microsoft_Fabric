---
hero: assets/heroes/energy-utilities.svg
hero_alt: Agricultural analytics on Fabric
type: feature
---
# Agricultural Analytics

> Leveraging Microsoft Fabric to analyze crop production trends, food safety recall patterns, SNAP benefit distribution, and Census of Agriculture data using publicly available USDA datasets.

---

## Executive Summary

The United States Department of Agriculture (USDA) collects and publishes some of the most extensive agricultural data in the world. The National Agricultural Statistics Service (NASS) conducts the Census of Agriculture every five years and produces weekly, monthly, and annual estimates for hundreds of commodities across every U.S. county. The Food Safety and Inspection Service (FSIS) tracks meat, poultry, and egg product recalls with detailed classification data. The Food and Nutrition Service (FNS) administers the Supplemental Nutrition Assistance Program (SNAP), which served over 42 million Americans in 2023, publishing state-level participation and benefit data. Together these datasets represent the most comprehensive picture of U.S. agricultural production, food safety, and nutrition assistance available to the public.

Despite this wealth of data, cross-cutting analysis remains difficult because each USDA agency maintains its own data systems, schemas, and publication schedules. Microsoft Fabric's unified analytics platform consolidates crop production statistics, food safety recalls, SNAP participation data, and Census of Agriculture trends into a single lakehouse with medallion architecture. This enables:

- **Crop production trend analysis** using NASS QuickStats API data to track yield, acreage, and production for every commodity by state and county — identifying multi-year trends and anomalies
- **Food safety recall pattern detection** analyzing FSIS recall data by reason, severity class, species, and establishment to identify systemic risks in the food supply chain
- **SNAP benefit geographic distribution** mapping participation rates and average benefits per person to identify food insecurity hotspots and correlate with agricultural production regions
- **Census of Agriculture structural analysis** tracking the long-term evolution of U.S. farm size, operator demographics, and production concentration across census years

This use case demonstrates how the Supercharge Microsoft Fabric POC's PySpark notebooks, Delta Lake storage, and Power BI visualizations apply to agricultural analytics using real, publicly available data sources.

---

## Data Sources

### Primary Sources

| Source | Agency | URL | Data Available |
|--------|--------|-----|----------------|
| NASS QuickStats API | USDA-NASS | https://quickstats.nass.usda.gov/api | Crop production, yield, acreage, livestock, prices — 31M+ records across all U.S. commodities |
| FSIS Recall Case Archive | USDA-FSIS | https://www.fsis.usda.gov/recalls | Meat, poultry, and egg product recalls with classification, reason, and pounds recalled |
| SNAP Data Tables | USDA-FNS | https://www.fns.usda.gov/pd/supplemental-nutrition-assistance-program-snap | Monthly state-level participation, benefits issued, average benefit per person |
| Census of Agriculture | USDA-NASS | https://www.nass.usda.gov/AgCensus | Complete census of U.S. farms every 5 years — 2022 census covers 1.9M farms |
| NASS Cropland Data Layer | USDA-NASS | https://nassgeodata.gmu.edu/CropScape | Geospatial crop-specific land cover data at 30m resolution |

### Supporting Sources

| Source | Agency | URL | Use In Analytics |
|--------|--------|-----|------------------|
| NOAA Climate Data | NOAA | https://www.ncei.noaa.gov/cdo-web | Weather and climate conditions for crop yield correlation |
| EPA Watershed Data | EPA | https://www.epa.gov/waterdata | Agricultural runoff and water quality impact analysis |
| SBA Lending Data | SBA | https://data.sba.gov/dataset/7-a-504-foia | Rural small business lending patterns in agricultural regions |
| ERS Food Environment Atlas | USDA-ERS | https://www.ers.usda.gov/data-products/food-environment-atlas | County-level food access, store availability, food assistance |
| ARMS Farm Financial Data | USDA-ERS | https://www.ers.usda.gov/data-products/arms-farm-financial-and-crop-production-practices | Farm income, expenses, and production practices survey |
| FAS Global Trade Data | USDA-FAS | https://apps.fas.usda.gov/gats/default.aspx | U.S. agricultural export/import data for trade analysis |

---

## Crop Production Trend Analysis

### Background

The NASS QuickStats API is the primary public interface to USDA's agricultural statistics. It provides access to over 31 million records spanning crop production, livestock inventories, prices received by farmers, and land use statistics. Data is available at national, state, county, and agricultural district levels, with temporal granularity ranging from weekly crop progress reports to annual production summaries. The API uses a structured query model with parameters for commodity, data item, geographic level, and year.

Analyzing crop production trends reveals the effects of agricultural technology adoption (precision agriculture, GMO varieties, irrigation expansion), climate variability, and policy changes (crop insurance subsidies, conservation reserve programs) on U.S. food production capacity. Corn and soybean yields, for example, have increased by roughly 1.5-2% annually over the past 50 years, but year-to-year variability driven by drought and flooding remains significant.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # USDA Crop Production Trend Analysis
# MAGIC Analyze crop yield, acreage, and production trends from NASS QuickStats data.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Load NASS crop production data from bronze layer
df_crops = spark.read.format("delta").load(
    "Tables/bronze_usda_crop_production"
)

# Focus on major field crops at state level
major_crops = ["CORN", "SOYBEANS", "WHEAT", "COTTON", "RICE"]

df_crop_trends = (
    df_crops
    .filter(F.col("commodity_desc").isin(major_crops))
    .filter(F.col("agg_level_desc") == "STATE")
    .filter(F.col("statisticcat_desc") == "YIELD")
    .filter(F.col("unit_desc").contains("BU / ACRE"))
    .filter(F.col("year").between(2000, 2025))
    .withColumn("value_numeric", F.col("value").cast("double"))
    .filter(F.col("value_numeric").isNotNull())
)

# Calculate state-level yield trends with moving averages
window_3yr = Window.partitionBy("state_name", "commodity_desc").orderBy("year").rowsBetween(-2, 0)
window_trend = Window.partitionBy("state_name", "commodity_desc").orderBy("year")

df_yield_analysis = (
    df_crop_trends
    .groupBy("year", "state_name", "commodity_desc")
    .agg(F.avg("value_numeric").alias("avg_yield_bu_acre"))
    .withColumn("moving_avg_3yr", F.round(F.avg("avg_yield_bu_acre").over(window_3yr), 2))
    .withColumn("yield_yoy_change", F.round(
        F.col("avg_yield_bu_acre") - F.lag("avg_yield_bu_acre").over(window_trend), 2
    ))
    .withColumn("yield_yoy_pct", F.round(
        F.col("yield_yoy_change") / F.lag("avg_yield_bu_acre").over(window_trend) * 100, 2
    ))
)

# Identify states with declining yield trends (potential climate stress)
df_declining_yields = (
    df_yield_analysis
    .filter(F.col("year") >= 2020)
    .groupBy("state_name", "commodity_desc")
    .agg(
        F.avg("yield_yoy_pct").alias("avg_annual_yield_change_pct"),
        F.min("avg_yield_bu_acre").alias("min_yield"),
        F.max("avg_yield_bu_acre").alias("max_yield")
    )
    .filter(F.col("avg_annual_yield_change_pct") < 0)
    .orderBy("avg_annual_yield_change_pct")
)

display(df_declining_yields)

# Write to silver layer
df_yield_analysis.write.format("delta").mode("overwrite").saveAsTable(
    "lh_silver.silver_usda_crop_yield_trends"
)
```

---

## Food Safety Recall Pattern Analysis

### Background

The USDA Food Safety and Inspection Service (FSIS) is responsible for the safety of the nation's commercial supply of meat, poultry, and processed egg products. When a product is found to be adulterated or misbranded, FSIS works with the producing establishment to initiate a recall. Recalls are classified into three severity levels: Class I (reasonable probability of serious health consequences or death), Class II (remote probability of adverse health consequences), and Class III (will not cause adverse health consequences). Common recall reasons include undeclared allergens, Listeria monocytogenes contamination, Salmonella contamination, E. coli O157:H7, and foreign material contamination.

Analyzing recall patterns over time reveals systemic weaknesses in the food production system. Undeclared allergens have become the leading cause of food recalls, surpassing pathogen contamination — reflecting both improved allergen testing capabilities and persistent labeling control failures at processing facilities.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # FSIS Food Safety Recall Pattern Detection
# MAGIC Analyze recall frequency, severity, reason, and establishment patterns.

# COMMAND ----------

from pyspark.sql import functions as F

# Load FSIS recall data
df_recalls = spark.read.format("delta").load(
    "Tables/bronze_usda_fsis_recalls"
)

# Parse and enrich recall records
df_recalls_enriched = (
    df_recalls
    .withColumn("recall_date", F.to_date("recall_date_str", "yyyy-MM-dd"))
    .withColumn("recall_year", F.year("recall_date"))
    .withColumn("recall_month", F.month("recall_date"))
    .withColumn("pounds_recalled_num", F.col("pounds_recalled").cast("double"))
    .filter(F.col("recall_year") >= 2015)
)

# Recall trends by reason and classification
df_recall_trends = (
    df_recalls_enriched
    .groupBy("recall_year", "recall_classification", "reason_for_recall")
    .agg(
        F.count("*").alias("recall_count"),
        F.sum("pounds_recalled_num").alias("total_pounds_recalled"),
        F.countDistinct("establishment_name").alias("unique_establishments"),
        F.avg("pounds_recalled_num").alias("avg_pounds_per_recall")
    )
    .orderBy("recall_year", F.desc("recall_count"))
)

# Identify repeat offender establishments
df_repeat_establishments = (
    df_recalls_enriched
    .groupBy("establishment_name", "establishment_number", "state")
    .agg(
        F.count("*").alias("total_recalls"),
        F.sum(F.when(F.col("recall_classification") == "Class I", 1).otherwise(0)).alias("class_i_recalls"),
        F.sum("pounds_recalled_num").alias("total_pounds_recalled"),
        F.min("recall_date").alias("first_recall"),
        F.max("recall_date").alias("latest_recall"),
        F.collect_set("reason_for_recall").alias("recall_reasons")
    )
    .filter(F.col("total_recalls") >= 3)
    .orderBy(F.desc("total_recalls"))
)

# Allergen vs. pathogen recall ratio over time
df_allergen_vs_pathogen = (
    df_recalls_enriched
    .withColumn("recall_category", F.when(
        F.col("reason_for_recall").contains("allergen") | F.col("reason_for_recall").contains("undeclared"),
        "Undeclared Allergen"
    ).when(
        F.col("reason_for_recall").rlike("(?i)salmonella|listeria|e\\.\\s*coli|clostridium"),
        "Pathogen Contamination"
    ).otherwise("Other"))
    .groupBy("recall_year", "recall_category")
    .agg(F.count("*").alias("recall_count"))
)

display(df_allergen_vs_pathogen)

# Write to silver layer
df_recall_trends.write.format("delta").mode("overwrite").saveAsTable(
    "lh_silver.silver_usda_fsis_recall_trends"
)
df_repeat_establishments.write.format("delta").mode("overwrite").saveAsTable(
    "lh_silver.silver_usda_fsis_repeat_establishments"
)
```

---

## SNAP Benefit Distribution Analysis

### Background

The Supplemental Nutrition Assistance Program (SNAP) is the largest federal nutrition assistance program, providing benefits to low-income individuals and families to purchase food. In fiscal year 2023, SNAP served an average of 42.1 million persons per month with total benefits of approximately $113 billion. USDA's Food and Nutrition Service publishes monthly state-level participation counts, total benefits issued, and average benefit per person. This data enables analysis of food insecurity patterns across the country and their relationship to agricultural production, economic conditions, and policy changes.

SNAP participation is highly counter-cyclical — enrollment rises during economic downturns and falls during expansions. The COVID-19 pandemic drove SNAP enrollment from 36 million to over 42 million, accompanied by emergency benefit increases. Analyzing SNAP distribution patterns alongside agricultural production data reveals the paradox of food insecurity in America's most productive farming states.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # SNAP Benefit Distribution Geographic Analysis
# MAGIC Analyze SNAP participation and benefits by state with food insecurity indicators.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Load SNAP participation data
df_snap = spark.read.format("delta").load(
    "Tables/bronze_usda_snap_participation"
)

# Load state population estimates for per-capita analysis
df_population = spark.read.format("delta").load(
    "Tables/bronze_census_state_population"
)

# Monthly SNAP analysis by state
df_snap_analysis = (
    df_snap
    .filter(F.col("fiscal_year") >= 2018)
    .withColumn("avg_persons_num", F.col("avg_participation_persons").cast("double"))
    .withColumn("total_benefits_num", F.col("total_benefits_issued").cast("double"))
    .withColumn("avg_benefit_per_person",
        F.round(F.col("total_benefits_num") / F.col("avg_persons_num"), 2)
    )
)

# State-level annual aggregation with per-capita participation rate
df_state_snap = (
    df_snap_analysis
    .groupBy("fiscal_year", "state_name")
    .agg(
        F.avg("avg_persons_num").alias("avg_monthly_participants"),
        F.sum("total_benefits_num").alias("annual_benefits_issued"),
        F.avg("avg_benefit_per_person").alias("avg_monthly_benefit_per_person")
    )
    .join(
        df_population.select("year", "state_name", "population"),
        (F.col("fiscal_year") == F.col("year")) & (df_snap_analysis["state_name"] == df_population["state_name"]),
        "left"
    )
    .withColumn("participation_rate_pct",
        F.round(F.col("avg_monthly_participants") / F.col("population") * 100, 2)
    )
)

# Identify food insecurity hotspots (high participation rate states)
df_food_insecurity = (
    df_state_snap
    .filter(F.col("fiscal_year") == 2023)
    .orderBy(F.desc("participation_rate_pct"))
)

# Trend analysis — participation change since pre-pandemic baseline
window_trend = Window.partitionBy("state_name").orderBy("fiscal_year")
df_snap_trends = (
    df_state_snap
    .withColumn("participation_change_pct", F.round(
        (F.col("avg_monthly_participants") - F.first("avg_monthly_participants").over(
            Window.partitionBy("state_name").orderBy("fiscal_year").rowsBetween(Window.unboundedPreceding, Window.unboundedPreceding)
        )) / F.first("avg_monthly_participants").over(
            Window.partitionBy("state_name").orderBy("fiscal_year").rowsBetween(Window.unboundedPreceding, Window.unboundedPreceding)
        ) * 100, 2
    ))
)

display(df_food_insecurity)

# Write to gold layer
df_state_snap.write.format("delta").mode("overwrite").saveAsTable(
    "lh_gold.gold_usda_snap_state_analysis"
)
```

---

## Implementation in Fabric

### Table Inventory

| Layer | Table | Source | Description |
|-------|-------|--------|-------------|
| Bronze | `bronze_usda_crop_production` | NASS QuickStats | Raw crop production, yield, acreage, and price data by commodity/state/county |
| Bronze | `bronze_usda_fsis_recalls` | FSIS | Raw food safety recall records with classification, reason, pounds recalled |
| Bronze | `bronze_usda_snap_participation` | FNS | Monthly state-level SNAP participation and benefit data |
| Bronze | `bronze_usda_census_of_agriculture` | NASS | Census of Agriculture farm counts, acreage, operator demographics |
| Bronze | `bronze_usda_cropland_data_layer` | NASS | Geospatial crop-specific land cover classifications |
| Bronze | `bronze_census_state_population` | Census Bureau | State population estimates for per-capita calculations |
| Silver | `silver_usda_crop_yield_trends` | NASS | Aggregated yield trends with moving averages and YoY change by state/crop |
| Silver | `silver_usda_fsis_recall_trends` | FSIS | Recall counts and pounds recalled by year, classification, and reason |
| Silver | `silver_usda_fsis_repeat_establishments` | FSIS | Establishments with 3+ recalls — repeat offender tracking |
| Silver | `silver_usda_snap_state_monthly` | FNS | Cleansed monthly SNAP data with derived per-person benefit metrics |
| Silver | `silver_usda_census_farm_structure` | NASS | Census data normalized for cross-year comparison of farm structure |
| Gold | `gold_usda_snap_state_analysis` | FNS | Annual state-level SNAP analysis with participation rates and trends |
| Gold | `gold_usda_crop_production_dashboard` | NASS | Executive crop production KPIs by commodity, state, and year |
| Gold | `gold_usda_food_safety_scorecard` | FSIS | Establishment-level food safety risk scoring and trend metrics |
| Gold | `gold_usda_farm_structure_evolution` | NASS | Census-to-census farm size, operator, and production concentration trends |
| Gold | `gold_usda_weather_crop_correlation` | Multi | Cross-domain weather impact on crop yields |

### Notebook Sequence

1. `01_bronze_usda_crop_production.py` — Ingest NASS QuickStats crop production data via API
2. `02_bronze_usda_fsis_recalls.py` — Ingest FSIS recall case archive data
3. `03_bronze_usda_snap_participation.py` — Ingest FNS SNAP monthly state-level data
4. `04_bronze_usda_census_agriculture.py` — Ingest Census of Agriculture summary data
5. `05_silver_usda_crop_yield_trends.py` — Calculate yield trends, moving averages, anomaly detection
6. `06_silver_usda_fsis_recall_patterns.py` — Aggregate recall patterns, identify repeat establishments
7. `07_silver_usda_snap_enrichment.py` — Join SNAP with population, calculate per-capita rates
8. `08_silver_usda_census_normalization.py` — Normalize census data across years for trend analysis
9. `09_gold_usda_crop_dashboard.py` — Executive crop production KPIs and state rankings
10. `10_gold_usda_food_safety_scorecard.py` — Establishment risk scores and recall severity trends
11. `11_gold_usda_snap_analysis.py` — State-level food insecurity analysis with participation trends
12. `12_gold_usda_weather_crop_correlation.py` — Cross-domain weather impact on crop yields

---

## Power BI Visualizations

### Recommended Visuals

| Page | Visual Type | Data | Purpose |
|------|-------------|------|---------|
| Crop Production Overview | Line chart (multi-series) | Yield trends by commodity over 20 years | Track long-term productivity gains by crop |
| Crop Production Overview | Choropleth map | Corn yield by state (latest year) | Geographic distribution of crop productivity |
| Food Safety Dashboard | Stacked bar chart | Recalls by year and classification | Trend in recall severity over time |
| Food Safety Dashboard | Treemap | Recall reasons by frequency | Identify dominant recall categories |
| Food Safety Dashboard | Table (conditional formatting) | Repeat offender establishments | Highlight high-risk facilities |
| SNAP Analysis | Filled map | Participation rate by state | Geographic food insecurity patterns |
| SNAP Analysis | Combo chart (bar + line) | Participation vs. unemployment rate | Demonstrate SNAP counter-cyclicality |
| Farm Structure | Grouped bar chart | Farm count by size class across census years | Consolidation trend visualization |
| Cross-Domain | Scatter plot | Crop yield anomaly vs. weather deviation | Weather-crop yield relationship |

### DAX Measures

```dax
// Average Yield Trend — 3-year moving average for smoothed crop productivity
Avg Yield 3yr Moving =
VAR _current_year = SELECTEDVALUE('silver_usda_crop_yield_trends'[year])
VAR _commodity = SELECTEDVALUE('silver_usda_crop_yield_trends'[commodity_desc])
VAR _state = SELECTEDVALUE('silver_usda_crop_yield_trends'[state_name])
RETURN
    CALCULATE(
        AVERAGE('silver_usda_crop_yield_trends'[avg_yield_bu_acre]),
        FILTER(
            ALL('silver_usda_crop_yield_trends'),
            'silver_usda_crop_yield_trends'[commodity_desc] = _commodity
            && 'silver_usda_crop_yield_trends'[state_name] = _state
            && 'silver_usda_crop_yield_trends'[year] >= _current_year - 2
            && 'silver_usda_crop_yield_trends'[year] <= _current_year
        )
    )
```

```dax
// SNAP Participation Rate — percentage of state population receiving SNAP benefits
SNAP Participation Rate =
DIVIDE(
    SUM('gold_usda_snap_state_analysis'[avg_monthly_participants]),
    SUM('gold_usda_snap_state_analysis'[population]),
    0
)
```

```dax
// Recall Severity Index — weighted score emphasizing Class I recalls
Recall Severity Index =
VAR _class_i = CALCULATE(COUNTROWS('silver_usda_fsis_recall_trends'),
    'silver_usda_fsis_recall_trends'[recall_classification] = "Class I")
VAR _class_ii = CALCULATE(COUNTROWS('silver_usda_fsis_recall_trends'),
    'silver_usda_fsis_recall_trends'[recall_classification] = "Class II")
VAR _class_iii = CALCULATE(COUNTROWS('silver_usda_fsis_recall_trends'),
    'silver_usda_fsis_recall_trends'[recall_classification] = "Class III")
RETURN
    _class_i * 3 + _class_ii * 2 + _class_iii * 1
```

```dax
// Allergen Recall Proportion — share of total recalls caused by undeclared allergens
Allergen Recall Proportion =
DIVIDE(
    CALCULATE(
        COUNTROWS('silver_usda_fsis_recall_trends'),
        CONTAINSSTRING('silver_usda_fsis_recall_trends'[reason_for_recall], "allergen")
    ),
    COUNTROWS('silver_usda_fsis_recall_trends'),
    0
)
```

---

## Cross-Domain Analysis

### Hypothesis 1: Agricultural Runoff Correlates with Downstream Water Quality Degradation (USDA x EPA)

Counties with the highest fertilizer application rates (derived from NASS crop production intensity) may show elevated nitrate and phosphorus levels in EPA water quality monitoring data. By joining NASS county-level crop acreage data with EPA STORET water quality measurements from downstream monitoring stations, we can quantify the correlation between agricultural intensity and waterway impairment.

```python
# Cross-domain: USDA × EPA agricultural runoff analysis
df_crop_acreage = spark.read.format("delta").load("Tables/bronze_usda_crop_production")
df_water_quality = spark.read.format("delta").load("Tables/bronze_epa_water_quality")

# Calculate agricultural intensity per county (acres planted / total land area)
df_ag_intensity = (
    df_crop_acreage
    .filter(F.col("statisticcat_desc") == "AREA PLANTED")
    .filter(F.col("agg_level_desc") == "COUNTY")
    .groupBy("year", "state_name", "county_name", "state_fips_code", "county_code")
    .agg(F.sum("value_numeric").alias("total_acres_planted"))
)

# Join with EPA water quality for downstream nitrate measurements
df_runoff_correlation = (
    df_ag_intensity
    .join(
        df_water_quality
        .filter(F.col("parameter_name") == "Nitrate")
        .groupBy("year", "county_name", "state_name")
        .agg(F.avg("result_value").alias("avg_nitrate_mg_l")),
        on=["year", "state_name", "county_name"],
        how="inner"
    )
)

correlation = df_runoff_correlation.stat.corr("total_acres_planted", "avg_nitrate_mg_l")
print(f"Agricultural Intensity-Nitrate Correlation: {correlation:.4f}")
```

### Hypothesis 2: Weather Anomalies Predict Crop Yield Shortfalls (USDA x NOAA)

Drought conditions (measured by NOAA's Palmer Drought Severity Index) and excessive precipitation events during critical growing season windows should show strong negative correlation with crop yields. By joining NASS yield data with NOAA climate division data on state/year, we can build predictive models for yield shortfalls and quantify the yield impact per unit of drought severity.

```python
# Cross-domain: USDA × NOAA weather-crop yield correlation
df_yields = spark.read.format("delta").load("Tables/silver_usda_crop_yield_trends")
df_drought = spark.read.format("delta").load("Tables/bronze_noaa_drought_index")

# Join crop yields with growing season (Apr-Sep) drought severity
df_weather_yield = (
    df_yields
    .filter(F.col("commodity_desc") == "CORN")
    .join(
        df_drought
        .filter(F.col("month").between(4, 9))
        .groupBy("year", "state_name")
        .agg(F.avg("pdsi").alias("growing_season_avg_pdsi")),
        on=["year", "state_name"],
        how="inner"
    )
)

# Quantify yield impact per unit PDSI change
correlation = df_weather_yield.stat.corr("growing_season_avg_pdsi", "avg_yield_bu_acre")
print(f"PDSI-Corn Yield Correlation: {correlation:.4f}")
```

### Hypothesis 3: SNAP Participation Inversely Correlates with Small Business Lending in Rural Counties (USDA x SBA)

Rural counties with higher SNAP participation rates may show lower SBA loan approval rates and volumes, reflecting broader economic distress that simultaneously drives food assistance demand and constrains small business access to capital. By joining SNAP participation data with SBA 7(a) and 504 loan data by county, we can test whether food insecurity and small business credit access are structurally linked.

---

## Microsoft Published Resources

| Resource | URL | Relevance |
|----------|-----|-----------|
| Azure for Government Documentation | https://learn.microsoft.com/en-us/azure/azure-government/documentation-government-overview-wwps | FedRAMP and government compliance requirements for processing USDA data |
| Medallion Architecture in Fabric | https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture | Bronze/Silver/Gold layering pattern applied to agricultural data pipelines |
| Microsoft Fabric Security White Paper | https://learn.microsoft.com/en-us/fabric/security/security-overview | Data protection framework for PII in SNAP benefit recipient analysis |
| Power BI Best Practices for Large Datasets | https://learn.microsoft.com/en-us/power-bi/guidance/star-schema | Star schema design for agricultural production dimension modeling |
| Cloud-Scale Analytics with Microsoft Fabric | https://learn.microsoft.com/en-us/fabric/get-started/microsoft-fabric-overview | Architecture guidance for building enterprise-scale agricultural analytics |
| Data Warehouse in Microsoft Fabric | https://learn.microsoft.com/en-us/fabric/data-warehouse/data-warehousing | Warehouse patterns for high-volume NASS QuickStats data (31M+ records) |

---

## Published References

| Reference | URL | Description |
|-----------|-----|-------------|
| NASS QuickStats API Documentation | https://quickstats.nass.usda.gov/api | API specification for querying USDA crop, livestock, and economic statistics |
| NASS QuickStats Web Interface | https://quickstats.nass.usda.gov | Interactive query tool for all NASS statistical data |
| FSIS Recalls and Public Health Alerts | https://www.fsis.usda.gov/recalls | Complete archive of USDA meat, poultry, and egg product recalls |
| SNAP Data Tables | https://www.fns.usda.gov/pd/supplemental-nutrition-assistance-program-snap | Monthly national and state-level SNAP participation and benefit data |
| 2022 Census of Agriculture | https://www.nass.usda.gov/AgCensus | Complete census of 1.9M U.S. farms — demographics, production, economics |
| NASS CropScape Cropland Data Layer | https://nassgeodata.gmu.edu/CropScape | Geospatial crop-type classification imagery at 30m resolution |
| ERS Food Environment Atlas | https://www.ers.usda.gov/data-products/food-environment-atlas | County-level food access, food assistance, and health indicators |
| USDA Open Data Catalog | https://www.usda.gov/content/usda-open-data-catalog | Centralized catalog of all USDA publicly available datasets |

---

## Related Documentation

- [Federal Justice Analytics](federal-justice-analytics.md) — DOJ enforcement analytics patterns
- [Antitrust Analytics](antitrust-analytics.md) — DOJ market concentration and enforcement analysis
- [Transportation Safety Analytics](transportation-safety-analytics.md) — DOT/FAA safety analytics for cross-domain weather correlation
- [NOAA Weather Notebooks](https://github.com/fgarofalo56/Supercharge_Microsoft_Fabric/blob/main/notebooks/bronze/12_bronze_noaa_storm_events.py) — Weather data for crop yield correlation
- [EPA Air Quality Notebooks](https://github.com/fgarofalo56/Supercharge_Microsoft_Fabric/blob/main/notebooks/bronze/14_bronze_epa_air_quality.py) — Environmental data for runoff analysis
- [SBA Lending Notebooks](https://github.com/fgarofalo56/Supercharge_Microsoft_Fabric/blob/main/notebooks/bronze/11_bronze_sba_loan_data.py) — Small business lending data for rural economy analysis
- [Medallion Architecture Deep Dive](../best-practices/medallion-architecture-deep-dive.md) — Bronze/Silver/Gold layering patterns
- [Data Sharing and Federation](../best-practices/data-sharing-federation.md) — Cross-agency data sharing patterns

---

*Last Updated: 2026-04-23*
