# Federal Justice Analytics

> End-to-end analytics across the federal criminal justice system — from crime reporting through prosecution, sentencing, and incarceration — using publicly available FBI, DOJ, USSC, and BOP data on Microsoft Fabric.

---

## Executive Summary

The U.S. federal justice system generates vast amounts of structured data at every stage: crime reporting (FBI NIBRS), prosecution (DOJ), sentencing (USSC), and incarceration (BOP). Individually, each dataset tells a partial story. Unified on Microsoft Fabric's lakehouse architecture, these datasets enable a complete pipeline view — from offense to outcome — revealing patterns in enforcement priorities, sentencing consistency, and system-wide trends.

This use case demonstrates how to build that unified view using the Supercharge Microsoft Fabric POC's medallion architecture, PySpark transformations, and Power BI dashboards.

---

## Analytics Domains

### 1. Crime Analytics (FBI NIBRS)

The FBI's National Incident-Based Reporting System (NIBRS) replaced the legacy Summary Reporting System (SRS) as the national standard for crime data collection. NIBRS captures detailed information about each criminal incident including offense type, victim/offender demographics, location, property loss, and arrest data.

**Key Metrics:**
- Offense counts and rates per 100,000 population
- Clearance rates (percentage of offenses resolved by arrest)
- Offense type distribution and year-over-year trends
- Geographic patterns by state, MSA, and agency

#### PySpark: Crime Trend Analysis

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # FBI NIBRS Crime Trend Analysis

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

df_offenses = spark.read.table("lh_silver.fbi_nibrs_offenses")
df_population = spark.read.table("lh_silver.census_population")

# Offense rates per 100K population
df_rates = (
    df_offenses
    .groupBy("state_abbr", "year", "offense_category")
    .agg(F.count("incident_id").alias("offense_count"))
    .join(df_population, on=["state_abbr", "year"])
    .withColumn(
        "rate_per_100k",
        F.round(F.col("offense_count") / F.col("population") * 100000, 2)
    )
)

# Year-over-year change
w = Window.partitionBy("state_abbr", "offense_category").orderBy("year")
df_trends = (
    df_rates
    .withColumn("prior_rate", F.lag("rate_per_100k").over(w))
    .withColumn(
        "yoy_change_pct",
        F.round(
            (F.col("rate_per_100k") - F.col("prior_rate"))
            / F.col("prior_rate") * 100, 2
        )
    )
)

df_trends.write.format("delta").mode("overwrite").saveAsTable(
    "lh_gold.crime_rate_trends"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Clearance Rate Analysis

# COMMAND ----------

df_clearance = (
    df_offenses
    .groupBy("state_abbr", "year", "offense_category")
    .agg(
        F.count("incident_id").alias("total_offenses"),
        F.sum(
            F.when(F.col("cleared_flag") == True, 1).otherwise(0)
        ).alias("cleared_count")
    )
    .withColumn(
        "clearance_rate",
        F.round(F.col("cleared_count") / F.col("total_offenses") * 100, 2)
    )
)

df_clearance.write.format("delta").mode("overwrite").saveAsTable(
    "lh_gold.crime_clearance_rates"
)
```

---

### 2. Prosecution Pipeline

The federal prosecution pipeline tracks cases from arrest through final disposition. By joining FBI arrest data, DOJ case management data, and USSC sentencing records, we can measure pipeline throughput and identify bottlenecks.

**Pipeline Stages:**

```
Arrest (FBI/Agency)
  └── Referral to U.S. Attorney
        ├── Declined (no prosecution)
        └── Filed
              ├── Dismissed
              └── Adjudicated
                    ├── Guilty Plea (~90% of convictions)
                    ├── Trial Conviction
                    └── Acquittal
                          └── Sentencing (USSC)
                                └── BOP Custody / Probation
```

#### PySpark: Prosecution Funnel

```python
# COMMAND ----------

# MAGIC %md
# MAGIC # Federal Prosecution Pipeline Funnel

# COMMAND ----------

from pyspark.sql import functions as F

df_cases = spark.read.table("lh_silver.doj_federal_cases")

# Funnel metrics by fiscal year and district
df_funnel = (
    df_cases
    .groupBy("fiscal_year", "district")
    .agg(
        F.count("case_id").alias("total_referrals"),
        F.sum(F.when(F.col("status") == "Declined", 1).otherwise(0)).alias("declined"),
        F.sum(F.when(F.col("status") == "Filed", 1).otherwise(0)).alias("filed"),
        F.sum(F.when(F.col("status") == "Dismissed", 1).otherwise(0)).alias("dismissed"),
        F.sum(F.when(F.col("disposition") == "Guilty Plea", 1).otherwise(0)).alias("guilty_plea"),
        F.sum(F.when(F.col("disposition") == "Trial Conviction", 1).otherwise(0)).alias("trial_conviction"),
        F.sum(F.when(F.col("disposition") == "Acquittal", 1).otherwise(0)).alias("acquittal"),
    )
    .withColumn(
        "conviction_rate",
        F.round(
            (F.col("guilty_plea") + F.col("trial_conviction"))
            / (F.col("guilty_plea") + F.col("trial_conviction") + F.col("acquittal"))
            * 100, 2
        )
    )
    .withColumn(
        "declination_rate",
        F.round(F.col("declined") / F.col("total_referrals") * 100, 2)
    )
)

df_funnel.write.format("delta").mode("overwrite").saveAsTable(
    "lh_gold.prosecution_pipeline_funnel"
)
```

---

### 3. Sentencing Disparity Analysis

The U.S. Sentencing Commission publishes detailed data on federal sentencing outcomes. Analyzing this data reveals patterns in sentencing consistency — or disparity — across districts, demographics, and offense types.

**Key Dimensions:**
- **Geographic:** Sentencing variation by federal judicial district
- **Offense type:** Drug trafficking, fraud, immigration, firearms, etc.
- **Departure patterns:** Within-guideline vs. above/below guideline sentences
- **Demographic factors:** Analysis of outcomes across different populations

#### PySpark: Sentencing Disparity

```python
# COMMAND ----------

# MAGIC %md
# MAGIC # Sentencing Disparity Analysis (USSC Data)

# COMMAND ----------

from pyspark.sql import functions as F

df_sentences = spark.read.table("lh_silver.ussc_individual_sentences")

# District-level sentencing variation for drug offenses
df_district_variation = (
    df_sentences
    .filter(F.col("primary_offense_category") == "Drug Trafficking")
    .groupBy("district", "fiscal_year")
    .agg(
        F.count("case_id").alias("case_count"),
        F.avg("prison_months").alias("avg_prison_months"),
        F.percentile_approx("prison_months", 0.5).alias("median_prison_months"),
        F.stddev("prison_months").alias("stddev_prison_months"),
        F.avg("guideline_min_months").alias("avg_guideline_min"),
        # Departure analysis
        F.sum(F.when(F.col("departure_type") == "Below", 1).otherwise(0)).alias("below_guideline"),
        F.sum(F.when(F.col("departure_type") == "Within", 1).otherwise(0)).alias("within_guideline"),
        F.sum(F.when(F.col("departure_type") == "Above", 1).otherwise(0)).alias("above_guideline"),
    )
    .withColumn(
        "below_guideline_rate",
        F.round(F.col("below_guideline") / F.col("case_count") * 100, 2)
    )
    .withColumn(
        "sentence_to_guideline_ratio",
        F.round(F.col("avg_prison_months") / F.col("avg_guideline_min"), 2)
    )
)

df_district_variation.write.format("delta").mode("overwrite").saveAsTable(
    "lh_gold.sentencing_disparity_by_district"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Departure Rate Trends

# COMMAND ----------

df_departure_trends = (
    df_sentences
    .groupBy("fiscal_year", "primary_offense_category", "departure_type")
    .agg(F.count("case_id").alias("case_count"))
    .withColumn(
        "total_in_category",
        F.sum("case_count").over(
            Window.partitionBy("fiscal_year", "primary_offense_category")
        )
    )
    .withColumn(
        "departure_pct",
        F.round(F.col("case_count") / F.col("total_in_category") * 100, 2)
    )
)

df_departure_trends.write.format("delta").mode("overwrite").saveAsTable(
    "lh_gold.sentencing_departure_trends"
)
```

---

### 4. Drug Enforcement Trends

DEA seizure data and USSC drug sentencing data together reveal trends in federal drug enforcement — what substances are being targeted, where seizures are concentrated, and how sentences have shifted over time.

**Key Metrics:**
- Seizure volumes by drug type and region
- Estimated street values
- Sentencing trends by drug category
- Mandatory minimum application rates

#### PySpark: Drug Enforcement Analysis

```python
# COMMAND ----------

# MAGIC %md
# MAGIC # Drug Enforcement Trends

# COMMAND ----------

from pyspark.sql import functions as F

df_seizures = spark.read.table("lh_silver.dea_drug_seizures")

# Seizure trends by drug type
df_seizure_trends = (
    df_seizures
    .groupBy("fiscal_year", "drug_category", "region")
    .agg(
        F.count("seizure_id").alias("seizure_count"),
        F.sum("quantity_kg").alias("total_quantity_kg"),
        F.sum("estimated_value_usd").alias("total_street_value"),
        F.avg("quantity_kg").alias("avg_seizure_size_kg")
    )
    .orderBy("fiscal_year", "drug_category")
)

df_seizure_trends.write.format("delta").mode("overwrite").saveAsTable(
    "lh_gold.drug_seizure_trends"
)

# COMMAND ----------

# Drug sentencing: mandatory minimum usage
df_drug_sentences = spark.read.table("lh_silver.ussc_individual_sentences").filter(
    F.col("primary_offense_category") == "Drug Trafficking"
)

df_mandatory_min = (
    df_drug_sentences
    .groupBy("fiscal_year", "drug_type")
    .agg(
        F.count("case_id").alias("total_cases"),
        F.sum(
            F.when(F.col("mandatory_minimum_applied") == True, 1).otherwise(0)
        ).alias("mandatory_min_count"),
        F.avg("prison_months").alias("avg_sentence_months")
    )
    .withColumn(
        "mandatory_min_rate",
        F.round(F.col("mandatory_min_count") / F.col("total_cases") * 100, 2)
    )
)

df_mandatory_min.write.format("delta").mode("overwrite").saveAsTable(
    "lh_gold.drug_mandatory_minimum_trends"
)
```

---

## Implementation in Fabric

### Table Inventory

| Layer | Table | Source | Description |
|-------|-------|--------|-------------|
| Bronze | `bronze_fbi_nibrs_incidents` | FBI CDE API | Raw incident records |
| Bronze | `bronze_fbi_nibrs_offenses` | FBI CDE API | Raw offense detail records |
| Bronze | `bronze_doj_federal_cases` | DOJ Open Data | Raw federal case records |
| Bronze | `bronze_ussc_sentences` | USSC Data Files | Raw individual sentencing records |
| Bronze | `bronze_bop_population` | BOP Statistics | Raw inmate population snapshots |
| Bronze | `bronze_dea_seizures` | DEA Reports | Raw drug seizure records |
| Silver | `silver_fbi_nibrs_offenses` | Cleansed, validated, enriched with geo codes |
| Silver | `silver_doj_federal_cases` | Standardized case records with pipeline stage |
| Silver | `silver_ussc_individual_sentences` | Validated sentencing with guideline ranges |
| Silver | `silver_bop_inmate_demographics` | Cleansed inmate demographics and facility data |
| Silver | `silver_dea_drug_seizures` | Standardized seizure records with categories |
| Gold | `gold_crime_rate_trends` | Offense rates per 100K with YoY change |
| Gold | `gold_crime_clearance_rates` | Clearance rates by state and category |
| Gold | `gold_prosecution_pipeline_funnel` | Pipeline metrics by district and year |
| Gold | `gold_sentencing_disparity_by_district` | District-level sentencing variation |
| Gold | `gold_sentencing_departure_trends` | Guideline departure rates over time |
| Gold | `gold_drug_seizure_trends` | Seizure volumes by type and region |
| Gold | `gold_drug_mandatory_minimum_trends` | Mandatory minimum application rates |

### Notebook Sequence

```
01_bronze_fbi_nibrs_ingest.py         → Ingest FBI NIBRS incident/offense data
02_bronze_doj_cases_ingest.py         → Ingest DOJ federal case data
03_bronze_ussc_sentences_ingest.py    → Ingest USSC sentencing files
04_bronze_bop_population_ingest.py    → Ingest BOP population statistics
05_bronze_dea_seizures_ingest.py      → Ingest DEA seizure data
06_silver_crime_cleanse.py            → Cleanse and validate NIBRS data
07_silver_cases_cleanse.py            → Standardize DOJ case records
08_silver_sentences_cleanse.py        → Validate sentencing data
09_gold_crime_analytics.py            → Crime rates and clearance analysis
10_gold_prosecution_funnel.py         → Prosecution pipeline metrics
11_gold_sentencing_disparity.py       → Sentencing variation analysis
12_gold_drug_enforcement.py           → Drug seizure and sentencing trends
```

---

## Power BI Visualizations

| Visual | Type | Data Source | Purpose |
|--------|------|-------------|---------|
| **Crime Rate Map** | Filled map | `gold_crime_rate_trends` | Geographic distribution of offense rates by state |
| **Clearance Rate Comparison** | Clustered bar | `gold_crime_clearance_rates` | Clearance rates by offense category |
| **Prosecution Funnel** | Funnel chart | `gold_prosecution_pipeline_funnel` | Referral → Filed → Convicted flow |
| **Conviction Rate by District** | Bar chart | `gold_prosecution_pipeline_funnel` | District comparison of conviction rates |
| **Sentencing Box Plot** | Box & whisker | `gold_sentencing_disparity_by_district` | Sentence distribution by district |
| **Departure Rate Trend** | Stacked area | `gold_sentencing_departure_trends` | Below/Within/Above guideline over time |
| **Drug Seizure Treemap** | Treemap | `gold_drug_seizure_trends` | Seizure volume by drug type and region |
| **Mandatory Minimum Trend** | Line chart | `gold_drug_mandatory_minimum_trends` | Mandatory minimum rate over time by drug type |

### DAX Measures

```dax
// Conviction Rate
Conviction Rate =
DIVIDE(
    CALCULATE(
        COUNTROWS('ProsecutionFunnel'),
        'ProsecutionFunnel'[Disposition] IN {"Guilty Plea", "Trial Conviction"}
    ),
    CALCULATE(
        COUNTROWS('ProsecutionFunnel'),
        'ProsecutionFunnel'[Disposition] IN {"Guilty Plea", "Trial Conviction", "Acquittal"}
    ),
    0
)

// Sentence-to-Guideline Ratio
Sentence to Guideline Ratio =
DIVIDE(
    AVERAGE('Sentences'[PrisonMonths]),
    AVERAGE('Sentences'[GuidelineMinMonths]),
    0
)

// Below-Guideline Departure Rate
Below Guideline Rate =
DIVIDE(
    CALCULATE(COUNTROWS('Sentences'), 'Sentences'[DepartureType] = "Below"),
    COUNTROWS('Sentences'),
    0
)
```

---

## Published References

### Primary Data Sources

- **FBI Crime Data Explorer (CDE)** — NIBRS data, offense statistics, law enforcement data
  https://cde.ucr.cjis.gov

- **DOJ Open Data Portal** — Federal case data, grants, and agency statistics
  https://www.justice.gov/open/open-data

- **U.S. Sentencing Commission Research** — Individual sentencing datafiles, annual reports, guideline manuals
  https://www.ussc.gov/research

- **Bureau of Justice Statistics (BJS)** — Victimization, corrections, courts, law enforcement statistics
  https://bjs.ojp.gov

- **Bureau of Prisons (BOP) Statistics** — Inmate population, demographics, facility data
  https://www.bop.gov/about/statistics/

- **DEA Data and Statistics** — Drug seizure data, national threat assessments
  https://www.dea.gov/data-and-statistics

### Research & Academic Sources

- **ICPSR National Archive of Criminal Justice Data (NACJD)**
  https://www.icpsr.umich.edu/web/pages/NACJD/index.html

- **Vera Institute of Justice — Incarceration Trends**
  https://github.com/vera-institute/incarceration-trends

- **DOJ Antitrust Case Filings** (for white-collar crime cross-reference)
  https://www.justice.gov/atr/antitrust-case-filings

---

## Microsoft Published Resources

The following Microsoft-published white papers and reference architectures support building federal justice analytics on Azure and Microsoft Fabric:

- **Azure for Government — Justice & Public Safety** — Azure Government capabilities for law enforcement and justice agencies
  https://learn.microsoft.com/en-us/azure/azure-government/documentation-government-overview-jps

- **The Future of Public Safety and Justice** — Microsoft e-book on digital transformation in public safety
  https://info.microsoft.com/ww-landing-the-future-of-public-safety-and-justice.html

- **Microsoft Fabric Security White Paper** — Data protection and governance for sensitive criminal justice data
  https://learn.microsoft.com/en-us/fabric/security/white-paper-landing-page

- **Medallion Lakehouse Architecture in Fabric** — Official guidance for the Bronze/Silver/Gold pattern
  https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture

- **Real-Time Fraud Detection with Azure Stream Analytics** — Applicable pattern for real-time crime alert systems
  https://learn.microsoft.com/en-us/azure/stream-analytics/stream-analytics-real-time-fraud-detection

- **Azure Synapse Analytics Security White Paper** — Security architecture patterns for analytics workloads
  https://learn.microsoft.com/en-us/azure/synapse-analytics/guidance/security-white-paper-introduction

- **Cloud-Scale Analytics (Cloud Adoption Framework)** — Enterprise data governance and data mesh patterns
  https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/scenarios/cloud-scale-analytics/

---

## Related Documentation

- [Antitrust Analytics](antitrust-analytics.md)
- [Use Cases Index](index.md)
- [Published References Catalog](references/README.md)
- [Medallion Architecture Deep Dive](../best-practices/medallion-architecture-deep-dive.md)

---

*Last Updated: 2026-04-23*
