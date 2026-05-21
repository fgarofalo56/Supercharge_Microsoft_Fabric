---
hero: assets/heroes/healthcare.svg
hero_alt: Tribal health analytics + IHS reporting
type: feature
---
# Tribal Health Analytics

> Leveraging Microsoft Fabric to analyze health disparities, chronic disease burden, and facility utilization across Indian Health Service regions using publicly available federal health data while respecting tribal data sovereignty.

---

## Executive Summary

American Indian and Alaska Native (AI/AN) communities experience persistent health disparities that rank among the most severe of any population group in the United States. Life expectancy for AI/AN individuals is 5.5 years less than the U.S. average, with disproportionately higher rates of diabetes, heart disease, substance use disorders, and suicide. The Indian Health Service (IHS), a federal agency within the Department of Health and Human Services, provides health care to approximately 2.6 million enrolled members of 574 federally recognized tribes across 12 administrative areas. Despite this mandate, IHS has historically operated with per-capita funding roughly 40% below the national average for health expenditures, creating resource allocation challenges that demand data-driven optimization.

Microsoft Fabric enables a unified analytics platform for tribal health intelligence by consolidating publicly available federal health datasets — IHS aggregate statistics, CDC disease surveillance, BRFSS behavioral risk factors, AHRQ hospital utilization, and CMS facility data — into a medallion lakehouse architecture. Critically, this use case operates exclusively on **publicly available, aggregate federal data** and does not access, store, or process tribally controlled health records. All tribal-specific data remains under tribal sovereignty. This approach demonstrates how:

- **Health disparity index calculation** quantifying gaps between AI/AN and national benchmarks across chronic disease, behavioral health, and access-to-care indicators
- **Chronic disease prevalence modeling** using CDC WONDER and BRFSS data to identify regional patterns in diabetes, cardiovascular disease, and substance use disorders
- **IHS facility utilization analysis** benchmarking service delivery against demand using publicly reported IHS workload data
- **Environmental health correlation** linking EPA environmental justice data and USDA food access metrics to health outcomes in AI/AN service areas

---

## Data Sovereignty & Compliance

### Tribal Data Sovereignty

**This use case adheres to the fundamental principle that tribes are sovereign nations with inherent authority over their data.** Tribal data sovereignty — the right of tribal nations to govern the collection, ownership, and application of their data — is recognized by federal policy, tribal law, and research ethics frameworks including the CARE Principles for Indigenous Data Governance (Collective Benefit, Authority to Control, Responsibility, Ethics).

**What this use case DOES:**
- Uses only publicly available, aggregate federal datasets published by IHS, CDC, CMS, and other federal agencies
- Analyzes data at the IHS Area or state level, never at the tribal or individual level
- Demonstrates analytical patterns that tribes could adapt with their own sovereign data
- Respects all data use agreements and terms of service for federal data sources

**What this use case DOES NOT do:**
- Access, store, or process tribally controlled health records or patient-level data
- Use IHS Electronic Health Record (EHR) data, which is subject to tribal consent
- Make claims about specific tribes, communities, or individuals
- Override tribal authority over health data governance

### Regulatory Compliance Framework

| Regulation | Applicability | Implementation |
|------------|---------------|----------------|
| **HIPAA** (45 CFR Parts 160, 164) | All individually identifiable health information | Only aggregate, de-identified federal data used; no PHI |
| **42 CFR Part 2** | Substance use disorder treatment records | No SUD patient records accessed; only aggregate prevalence data from BRFSS |
| **Indian Self-Determination Act** (P.L. 93-638) | Tribal control of health programs | Analysis supports tribal decision-making without usurping tribal authority |
| **CARE Principles** | Indigenous data governance | Aggregate analysis designed to benefit tribal communities |
| **OMB Circular A-130** | Federal data management | Federal datasets used per their published terms of service |
| **FedRAMP** | Cloud security for federal data | Microsoft Fabric available on Azure Government with FedRAMP High |

### Data Classification

All data in this use case is classified as **PUBLIC** or **CONTROLLED UNCLASSIFIED INFORMATION (CUI)** per federal data classification standards. No data classified as Protected Health Information (PHI), Personally Identifiable Information (PII), or tribally restricted information is used.

---

## Data Sources

### Primary Sources

| Source | Agency | URL | Data Available |
|--------|--------|-----|----------------|
| IHS Fact Sheets & Statistics | IHS/HHS | https://www.ihs.gov/newsroom/factsheets/ | Aggregate IHS service population, funding, workload statistics |
| CDC WONDER | CDC | https://wonder.cdc.gov | Mortality data, natality, population estimates by race/ethnicity |
| BRFSS Annual Survey | CDC | https://www.cdc.gov/brfss/ | Behavioral risk factors, chronic disease prevalence by demographics |
| HCUP Statistical Briefs | AHRQ | https://hcup-us.ahrq.gov | Hospital utilization, costs, and outcomes data |
| CMS Provider Data | CMS | https://data.cms.gov | Medicare/Medicaid provider enrollment, quality measures |

### Supporting Sources

| Source | Agency | URL | Use In Analytics |
|--------|--------|-----|------------------|
| EJSCREEN | EPA | https://www.epa.gov/ejscreen | Environmental justice indicators for AI/AN areas |
| Food Access Research Atlas | USDA | https://www.ers.usda.gov/data-products/food-access-research-atlas/ | Food desert identification in tribal service areas |
| SDOH Data | HHS | https://health.gov/healthypeople | Social determinants of health framework and benchmarks |
| Area Health Resource Files | HRSA | https://data.hrsa.gov/topics/health-workforce/ahrf | Health workforce availability by county |
| National Vital Statistics | NCHS | https://www.cdc.gov/nchs/nvss/ | Birth and death registration statistics |
| SAMHSA NSDUH | SAMHSA | https://www.samhsa.gov/data/nsduh | Substance use and mental health prevalence data |

---

## Health Disparity Index Calculation

### Background

Health disparities between AI/AN populations and the general U.S. population are documented across virtually every health indicator tracked by the federal government. The IHS reports that AI/AN individuals die at higher rates than other Americans from chronic liver disease (368% higher), diabetes (177% higher), assault/homicide (82% higher), and intentional self-harm/suicide (60% higher). Quantifying these disparities as a composite index enables prioritized resource allocation and intervention targeting.

The Health Disparity Index (HDI) calculated here uses publicly available CDC WONDER mortality data and BRFSS prevalence data, comparing AI/AN age-adjusted rates to national benchmarks across multiple health domains.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Silver → Gold: Health Disparity Index Calculation
# MAGIC Calculates composite health disparity indices comparing AI/AN
# MAGIC age-adjusted rates to national benchmarks using CDC public data.
# MAGIC
# MAGIC **DATA NOTE:** This analysis uses ONLY publicly available aggregate
# MAGIC federal data. No tribal-specific or patient-level data is accessed.

# COMMAND ----------

from pyspark.sql import functions as F

# Read Silver CDC WONDER mortality data (age-adjusted rates)
df_mortality = spark.read.format("delta").load(
    "Tables/silver_tribal_cdc_mortality_rates"
)

# Read Silver BRFSS prevalence data
df_brfss = spark.read.format("delta").load(
    "Tables/silver_tribal_brfss_prevalence"
)

# Define health disparity domains and national benchmarks
# Source: CDC WONDER, age-adjusted rates per 100,000 (2020-2022)
national_benchmarks = {
    "all_cause_mortality": 835.4,
    "diabetes_mortality": 25.4,
    "chronic_liver_disease": 12.8,
    "heart_disease_mortality": 173.8,
    "suicide_mortality": 14.0,
    "unintentional_injury": 57.6,
}

# Calculate disparity ratios (AI/AN rate / national rate)
for condition, benchmark in national_benchmarks.items():
    df_mortality = df_mortality.withColumn(
        f"{condition}_disparity_ratio",
        F.when(
            F.col("race_ethnicity") == "American Indian or Alaska Native",
            F.col(f"{condition}_rate") / F.lit(benchmark)
        )
    )

# Aggregate to IHS Area level
disparity_cols = [f"{c}_disparity_ratio" for c in national_benchmarks.keys()]

df_hdi = (
    df_mortality
    .filter(F.col("race_ethnicity") == "American Indian or Alaska Native")
    .groupBy("ihs_area", "state", "reporting_year")
    .agg(
        *[F.avg(c).alias(c) for c in disparity_cols],
        F.count("*").alias("data_points"),
    )
    .withColumn(
        "composite_hdi",
        F.round(
            (F.col("all_cause_mortality_disparity_ratio") * 0.25 +
             F.col("diabetes_mortality_disparity_ratio") * 0.20 +
             F.col("heart_disease_mortality_disparity_ratio") * 0.15 +
             F.col("chronic_liver_disease_disparity_ratio") * 0.15 +
             F.col("suicide_mortality_disparity_ratio") * 0.15 +
             F.col("unintentional_injury_disparity_ratio") * 0.10),
            3
        )
    )
    .withColumn(
        "disparity_level",
        F.when(F.col("composite_hdi") >= 2.0, "SEVERE")
        .when(F.col("composite_hdi") >= 1.5, "SIGNIFICANT")
        .when(F.col("composite_hdi") >= 1.2, "MODERATE")
        .otherwise("NEAR_PARITY")
    )
)

df_hdi.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable("lh_gold.gold_tribal_health_disparity_index")

severe = df_hdi.filter(F.col("disparity_level") == "SEVERE").count()
print(f"IHS Area-years with SEVERE health disparities: {severe}")
```

---

## Chronic Disease Prevalence Modeling

### Background

Diabetes affects AI/AN adults at 2.3 times the rate of non-Hispanic white adults, making it the most significant chronic disease disparity in Indian Country. The Behavioral Risk Factor Surveillance System (BRFSS), administered by the CDC, provides state-level prevalence estimates for diabetes, cardiovascular disease, obesity, smoking, and other chronic conditions by race and ethnicity. While BRFSS sample sizes for AI/AN populations are small in many states (requiring multi-year aggregation), the data enables regional pattern identification that supports IHS resource planning.

This analysis models chronic disease prevalence trends across IHS service areas, identifying regions with accelerating disease burden that may require expanded screening, treatment, and prevention programs.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Gold: Chronic Disease Prevalence Trends by IHS Area
# MAGIC Models multi-year chronic disease prevalence using BRFSS data
# MAGIC to identify accelerating disease burden in AI/AN service areas.
# MAGIC
# MAGIC **DATA NOTE:** BRFSS provides aggregate prevalence estimates.
# MAGIC No individual-level or tribal-specific records are accessed.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Read Silver BRFSS prevalence data (AI/AN filtered, multi-year pooled)
df_brfss = spark.read.format("delta").load(
    "Tables/silver_tribal_brfss_prevalence"
)

# Focus on key chronic conditions
conditions = [
    "diabetes_prevalence_pct",
    "heart_disease_prevalence_pct",
    "obesity_prevalence_pct",
    "smoking_prevalence_pct",
    "heavy_drinking_prevalence_pct",
    "no_health_insurance_pct",
]

# Calculate 3-year rolling averages to smooth small sample effects
area_window = Window.partitionBy("ihs_area", "condition").orderBy("survey_year")
rolling_window = Window.partitionBy("ihs_area", "condition").orderBy("survey_year").rowsBetween(-2, 0)

# Unpivot conditions for trend analysis
df_unpivoted = df_brfss.selectExpr(
    "ihs_area", "state", "survey_year",
    "stack(6, "
    "'diabetes', diabetes_prevalence_pct, "
    "'heart_disease', heart_disease_prevalence_pct, "
    "'obesity', obesity_prevalence_pct, "
    "'smoking', smoking_prevalence_pct, "
    "'heavy_drinking', heavy_drinking_prevalence_pct, "
    "'uninsured', no_health_insurance_pct"
    ") as (condition, prevalence_pct)"
)

df_trends = (
    df_unpivoted
    .withColumn("rolling_avg_3yr", F.avg("prevalence_pct").over(rolling_window))
    .withColumn("prev_year_avg", F.lag("rolling_avg_3yr").over(area_window))
    .withColumn(
        "trend_direction",
        F.when(F.col("rolling_avg_3yr") > F.col("prev_year_avg") * 1.02, "INCREASING")
        .when(F.col("rolling_avg_3yr") < F.col("prev_year_avg") * 0.98, "DECREASING")
        .otherwise("STABLE")
    )
    .withColumn(
        "acceleration_flag",
        F.when(
            (F.col("trend_direction") == "INCREASING") &
            (F.col("prevalence_pct") > F.col("rolling_avg_3yr")),
            "ACCELERATING"
        ).otherwise("NORMAL")
    )
)

df_trends.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable("lh_gold.gold_tribal_chronic_disease_trends")

accelerating = df_trends.filter(F.col("acceleration_flag") == "ACCELERATING").count()
print(f"Condition-area-years with accelerating prevalence: {accelerating}")
```

---

## IHS Facility Utilization Analysis

### Background

The Indian Health Service operates 24 hospitals, 50 health centers, and 28 health stations directly, with an additional 605 facilities operated by tribes and tribal organizations under the Indian Self-Determination and Education Assistance Act (P.L. 93-638). IHS publishes aggregate workload data including outpatient visits, inpatient days, dental visits, and community health contacts through its annual reports and fact sheets. Benchmarking these workload metrics against service population creates utilization rates that reveal where demand exceeds capacity, informing facility expansion and workforce recruitment priorities.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Gold: IHS Facility Utilization Benchmarking
# MAGIC Calculates facility utilization rates and identifies capacity
# MAGIC gaps using publicly available IHS workload statistics.
# MAGIC
# MAGIC **DATA NOTE:** Uses only aggregate IHS published workload data.
# MAGIC No facility-specific patient data or tribal records accessed.

# COMMAND ----------

from pyspark.sql import functions as F

# Read Silver IHS workload data (from published IHS fact sheets)
df_ihs = spark.read.format("delta").load(
    "Tables/silver_tribal_ihs_workload"
)

# Read HRSA health workforce data for provider supply context
df_hrsa = spark.read.format("delta").load(
    "Tables/silver_tribal_hrsa_workforce"
)

# Calculate utilization metrics per IHS Area
df_utilization = (
    df_ihs
    .groupBy("ihs_area", "fiscal_year")
    .agg(
        F.sum("user_population").alias("total_users"),
        F.sum("outpatient_visits").alias("total_op_visits"),
        F.sum("inpatient_days").alias("total_ip_days"),
        F.sum("dental_visits").alias("total_dental_visits"),
        F.sum("community_health_contacts").alias("total_ch_contacts"),
        F.sum("er_visits").alias("total_er_visits"),
        F.countDistinct("facility_id").alias("facility_count"),
    )
    .withColumn(
        "op_visits_per_user",
        F.round(F.col("total_op_visits") / F.col("total_users"), 2)
    )
    .withColumn(
        "dental_visits_per_user",
        F.round(F.col("total_dental_visits") / F.col("total_users"), 3)
    )
    .withColumn(
        "er_rate_per_1000",
        F.round(F.col("total_er_visits") / F.col("total_users") * 1000, 1)
    )
)

# Benchmark against national averages (AHRQ MEPS data)
# National avg outpatient visits: ~4.0/person/year
# National avg dental visits: ~0.44/person/year
# National avg ER visits: ~429 per 1,000
df_benchmarked = (
    df_utilization
    .withColumn("op_benchmark_ratio",
        F.round(F.col("op_visits_per_user") / 4.0, 2))
    .withColumn("dental_benchmark_ratio",
        F.round(F.col("dental_visits_per_user") / 0.44, 2))
    .withColumn("er_benchmark_ratio",
        F.round(F.col("er_rate_per_1000") / 429, 2))
    .withColumn(
        "capacity_assessment",
        F.when(
            (F.col("op_benchmark_ratio") < 0.7) &
            (F.col("er_benchmark_ratio") > 1.3),
            "CAPACITY_GAP"  # Low outpatient + high ER = access problem
        )
        .when(F.col("op_benchmark_ratio") < 0.7, "UNDERSERVED")
        .when(F.col("er_benchmark_ratio") > 1.5, "ER_OVERRELIANCE")
        .otherwise("ADEQUATE")
    )
)

df_benchmarked.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).saveAsTable("lh_gold.gold_tribal_facility_utilization")

gaps = df_benchmarked.filter(F.col("capacity_assessment") == "CAPACITY_GAP").count()
print(f"IHS Area-years with capacity gaps: {gaps}")
```

---

## Implementation in Fabric

### Table Inventory

| Layer | Table | Source | Description |
|-------|-------|--------|-------------|
| Bronze | `bronze_tribal_cdc_mortality` | CDC WONDER | Raw age-adjusted mortality rates by race/ethnicity |
| Bronze | `bronze_tribal_brfss_raw` | CDC BRFSS | Raw behavioral risk factor survey results |
| Bronze | `bronze_tribal_ihs_workload` | IHS Fact Sheets | Raw IHS service area workload statistics |
| Bronze | `bronze_tribal_cms_providers` | CMS Data | Raw provider enrollment and quality measures |
| Bronze | `bronze_tribal_hrsa_workforce` | HRSA AHRF | Raw health workforce availability by county |
| Bronze | `bronze_tribal_ejscreen` | EPA EJSCREEN | Raw environmental justice indicators |
| Bronze | `bronze_tribal_food_access` | USDA ERS | Raw food access research atlas data |
| Silver | `silver_tribal_cdc_mortality_rates` | CDC Bronze | Validated, race/ethnicity-filtered mortality rates |
| Silver | `silver_tribal_brfss_prevalence` | BRFSS Bronze | Multi-year pooled prevalence estimates for AI/AN |
| Silver | `silver_tribal_ihs_workload` | IHS Bronze | Standardized facility workload metrics |
| Silver | `silver_tribal_hrsa_workforce` | HRSA Bronze | Validated workforce supply by IHS Area |
| Silver | `silver_tribal_environmental_health` | EJSCREEN Bronze | Environmental burden indicators for AI/AN areas |
| Gold | `gold_tribal_health_disparity_index` | Mortality Silver | Composite health disparity index by IHS Area |
| Gold | `gold_tribal_chronic_disease_trends` | BRFSS Silver | Multi-year chronic disease prevalence trends |
| Gold | `gold_tribal_facility_utilization` | IHS Workload Silver | Facility utilization benchmarks and capacity gaps |
| Gold | `gold_tribal_sdoh_composite` | All Silver | Social determinants of health composite scores |

### Notebook Sequence

1. `01_bronze_tribal_cdc_mortality_ingest.py` — Ingest CDC WONDER mortality data
2. `02_bronze_tribal_brfss_ingest.py` — Ingest BRFSS survey prevalence data
3. `03_bronze_tribal_ihs_workload_ingest.py` — Ingest IHS published workload statistics
4. `04_bronze_tribal_cms_providers_ingest.py` — Ingest CMS provider enrollment data
5. `05_bronze_tribal_hrsa_workforce_ingest.py` — Ingest HRSA workforce data
6. `06_bronze_tribal_ejscreen_ingest.py` — Ingest EPA EJSCREEN for AI/AN areas
7. `07_bronze_tribal_food_access_ingest.py` — Ingest USDA food access atlas
8. `08_silver_tribal_mortality_validate.py` — Validate and filter mortality rates
9. `09_silver_tribal_brfss_pool.py` — Multi-year pooling for AI/AN sample adequacy
10. `10_silver_tribal_ihs_standardize.py` — Standardize IHS workload across areas
11. `11_silver_tribal_environmental.py` — Calculate environmental burden indicators
12. `12_gold_tribal_disparity_index.py` — Composite health disparity index
13. `13_gold_tribal_chronic_disease.py` — Chronic disease prevalence trend analysis
14. `14_gold_tribal_utilization.py` — Facility utilization benchmarking
15. `15_gold_tribal_sdoh_composite.py` — Social determinants composite scoring

---

## Power BI Visualizations

### Recommended Visuals

| Page | Visual Type | Data | Purpose |
|------|-------------|------|---------|
| Disparity Overview | KPI cards + radar chart | `gold_tribal_health_disparity_index` | Composite HDI with domain-level breakdown |
| Disparity Map | Filled map (IHS Areas) | `gold_tribal_health_disparity_index` | Geographic distribution of health disparities |
| Chronic Disease Trends | Multi-line chart + slicer | `gold_tribal_chronic_disease_trends` | Prevalence trends by condition and IHS Area |
| Disease Comparison | Grouped bar chart | `gold_tribal_chronic_disease_trends` | AI/AN vs. national prevalence side-by-side |
| Facility Utilization | Bullet chart | `gold_tribal_facility_utilization` | Actual vs. benchmark utilization rates |
| Capacity Gaps | Table with conditional formatting | `gold_tribal_facility_utilization` | Areas with capacity gaps highlighted |
| Social Determinants | Decomposition tree | `gold_tribal_sdoh_composite` | SDOH factor contribution to health outcomes |
| Environmental Health | Scatter plot | `gold_tribal_sdoh_composite` | Environmental burden vs. health disparity correlation |

### DAX Measures

```dax
// Composite Health Disparity Index (weighted average)
Health Disparity Index =
AVERAGE(gold_tribal_health_disparity_index[composite_hdi])
```

```dax
// Disparity Gap (AI/AN rate minus national rate, per 100K)
Mortality Disparity Gap =
VAR _AIAN_Rate =
    CALCULATE(
        AVERAGE(gold_tribal_health_disparity_index[all_cause_mortality_disparity_ratio]),
        ALLSELECTED()
    )
RETURN
    (_AIAN_Rate - 1) * 835.4  // National benchmark per 100K
```

```dax
// ER Overreliance Indicator
ER Overreliance Score =
VAR _ERRatio = AVERAGE(gold_tribal_facility_utilization[er_benchmark_ratio])
VAR _OPRatio = AVERAGE(gold_tribal_facility_utilization[op_benchmark_ratio])
RETURN
    DIVIDE(_ERRatio, _OPRatio, BLANK())
    // Values > 1.5 indicate ER substituting for primary care
```

```dax
// Chronic Disease Acceleration Flag Count
Accelerating Conditions =
CALCULATE(
    DISTINCTCOUNT(gold_tribal_chronic_disease_trends[condition]),
    gold_tribal_chronic_disease_trends[acceleration_flag] = "ACCELERATING"
)
```

---

## Cross-Domain Analysis

### Hypothesis 1: Tribal Health × USDA — Food Access and Diabetes Prevalence

Food deserts — areas with limited access to affordable, nutritious food — disproportionately overlap with tribal lands. The USDA Food Access Research Atlas identifies low-access census tracts, and correlating these with BRFSS diabetes prevalence data in AI/AN populations can quantify the relationship between food access and the diabetes epidemic in Indian Country, supporting arguments for expanded nutrition programs and food sovereignty initiatives.

```python
# Cross-domain: USDA food access vs. diabetes prevalence in AI/AN areas
df_cross_food = (
    df_usda_food_access
    .filter(F.col("tract_overlaps_tribal_area") == True)
    .join(df_tribal_chronic_disease, on=["state", "county_fips"])
    .filter(F.col("condition") == "diabetes")
    .groupBy("ihs_area", "state")
    .agg(
        F.avg("low_access_pct").alias("avg_food_desert_pct"),
        F.avg("prevalence_pct").alias("avg_diabetes_prevalence"),
        F.count("*").alias("tracts_analyzed"),
    )
    .withColumn(
        "food_diabetes_correlation",
        F.corr("avg_food_desert_pct", "avg_diabetes_prevalence")
            .over(Window.partitionBy(F.lit(1)))
    )
)
```

### Hypothesis 2: Tribal Health × EPA — Environmental Justice and Health Outcomes

EPA's EJSCREEN environmental justice screening tool identifies communities with disproportionate environmental burdens. AI/AN communities near Superfund sites, TRI facilities, and areas with poor air or water quality may experience elevated rates of cancer, respiratory disease, and developmental health conditions. Correlating EPA environmental indicators with tribal health disparities strengthens the evidence base for environmental remediation prioritization.

```python
# Cross-domain: EPA environmental burden vs. tribal health disparities
df_cross_ej = (
    df_epa_ejscreen
    .filter(F.col("pct_aian") > 0.10)  # Tracts with >10% AI/AN population
    .join(df_tribal_health_disparity, on=["state_fips", "county_fips"])
    .select(
        "state", "county", "ihs_area",
        "pm25_score", "ozone_score", "lead_paint_score",
        "superfund_proximity_score", "rmp_proximity_score",
        "composite_hdi", "disparity_level",
    )
    .withColumn(
        "environmental_health_risk",
        F.when(
            (F.col("superfund_proximity_score") > 80) &
            (F.col("composite_hdi") >= 1.5),
            "HIGH_RISK_OVERLAP"
        ).otherwise("STANDARD")
    )
)
```

### Hypothesis 3: Tribal Health × DOI — Federal Trust Lands and Health Infrastructure

The Department of the Interior holds approximately 56 million acres in trust for tribal nations. The geographic distribution and remoteness of trust lands directly affects health care access — many IHS and tribal facilities serve populations spread across vast, rural geographies. Correlating DOI trust land data with IHS facility locations and HRSA health workforce data identifies service deserts where the combination of geography, workforce shortage, and population need is most acute.

```sql
-- Cross-domain: DOI trust land remoteness vs. health access
SELECT
    t.ihs_area,
    t.state,
    l.trust_land_acres,
    l.avg_distance_to_nearest_hospital_miles,
    w.primary_care_physicians_per_100k,
    u.op_visits_per_user,
    u.er_rate_per_1000,
    u.capacity_assessment,
    h.composite_hdi
FROM gold_tribal_facility_utilization u
JOIN gold_tribal_health_disparity_index h
    ON u.ihs_area = h.ihs_area AND u.fiscal_year = h.reporting_year
JOIN silver_doi_trust_lands l
    ON u.ihs_area = l.ihs_area
JOIN silver_tribal_hrsa_workforce w
    ON u.ihs_area = w.ihs_area
WHERE u.capacity_assessment IN ('CAPACITY_GAP', 'UNDERSERVED')
ORDER BY h.composite_hdi DESC
```

---

## Microsoft Published Resources

| Resource | URL | Relevance |
|----------|-----|-----------|
| Azure Health Data Services | https://learn.microsoft.com/en-us/azure/health-data-services/ | FHIR-compliant health data platform for interoperability |
| HIPAA Compliance on Azure | https://learn.microsoft.com/en-us/azure/compliance/offerings/offering-hipaa-us | HIPAA implementation guidance for health data workloads |
| Microsoft Fabric Security White Paper | https://learn.microsoft.com/en-us/fabric/security/white-paper-landing-page | Data protection for sensitive health analytics |
| Cloud-Scale Analytics with Microsoft Fabric | https://learn.microsoft.com/en-us/azure/architecture/solution-ideas/articles/analytics-end-to-end | End-to-end analytics architecture for health data |
| Power BI for Healthcare | https://learn.microsoft.com/en-us/power-bi/guidance/whitepaper-powerbi-enterprise-deployment | Enterprise BI deployment for health system dashboards |
| Azure Government Compliance | https://learn.microsoft.com/en-us/azure/azure-government/documentation-government-overview-itar | Government cloud compliance for federal health data |

---

## Published References

| Reference | URL | Description |
|-----------|-----|-------------|
| IHS Fact Sheets | https://www.ihs.gov/newsroom/factsheets/ | Official IHS statistics on service population and health outcomes |
| IHS Disparities Report | https://www.ihs.gov/newsroom/factsheets/disparities/ | IHS-published health disparity data for AI/AN populations |
| CDC WONDER Documentation | https://wonder.cdc.gov/wonder/help/main.html | Mortality and population data query system documentation |
| BRFSS Annual Survey Data | https://www.cdc.gov/brfss/annual_data/annual_data.htm | Behavioral Risk Factor Surveillance System methodology |
| AHRQ HCUP Overview | https://hcup-us.ahrq.gov/overview.jsp | Healthcare Cost and Utilization Project data overview |
| CMS Data Portal | https://data.cms.gov | Centers for Medicare & Medicaid Services open data |
| CARE Principles for Indigenous Data | https://www.gida-global.org/care | CARE Principles for Indigenous Data Governance |
| Tribal Self-Governance | https://www.tribalselfgov.org | Resources on tribal self-determination in health care |

---

## Related Documentation

- [Environmental Compliance Analytics](environmental-compliance-analytics.md) — EPA environmental justice data for tribal lands overlay
- [Natural Resources Analytics](natural-resources-analytics.md) — DOI trust land management and resource data
- [Federal Justice Analytics](federal-justice-analytics.md) — Federal enforcement patterns affecting tribal communities
- [Data Governance Deep Dive](../best-practices/data-governance-deep-dive.md) — Purview governance for sensitive health data
- [Network Security](../best-practices/network-security.md) — Network isolation for health data workloads
- [Identity & RBAC Patterns](../best-practices/identity-rbac-patterns.md) — Row-level security for multi-agency access
- [OneLake Security](../features/onelake-security.md) — Data protection patterns for compliance-sensitive workloads

---

*Last Updated: 2026-04-23*
