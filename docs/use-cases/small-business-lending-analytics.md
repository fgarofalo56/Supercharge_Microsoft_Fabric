---
hero: assets/heroes/financial-services.svg
hero_alt: SBA lending portfolio analytics
type: feature
---
# Small Business Lending Analytics

> Leveraging Microsoft Fabric to analyze PPP loan distribution, detect lending fraud patterns, and monitor small business capital access using SBA, SAM.gov, and SBIR public data.

---

## Executive Summary

Small business lending is a cornerstone of U.S. economic policy, with the Small Business Administration (SBA) facilitating over $40 billion annually in guaranteed loans through its 7(a), 504, and disaster lending programs. The Paycheck Protection Program (PPP) alone distributed $793 billion across 11.5 million loans during 2020-2021, creating one of the largest publicly available lending datasets in history. Yet despite this scale, fraud detection, lender performance monitoring, and equitable access analysis remain fragmented across disparate systems with limited cross-referencing capability.

Microsoft Fabric provides a unified analytics platform to consolidate SBA lending data, SAM.gov entity registrations, and SBIR/STTR innovation grant records into a single medallion architecture. Real-Time Intelligence enables streaming fraud detection on loan application velocity and structuring patterns, while Direct Lake connectivity delivers sub-second Power BI dashboards for congressional reporting and oversight. This use case demonstrates how the Supercharge Microsoft Fabric POC applies PySpark notebooks, Delta Lake, and KQL analytics to small business lending data from publicly available federal sources.

- **PPP fraud detection** using loan velocity analysis, duplicate entity matching, and structuring pattern recognition across 11.5 million loan records
- **7(a)/504 lending trend analysis** tracking approval rates, default rates, and lender concentration by geography and industry
- **SBIR/STTR innovation grant mapping** correlating R&D investment with small business growth and job creation
- **Lender performance scoring** comparing approval-to-default ratios, processing times, and borrower outcomes across 5,000+ participating lenders

---

## Data Sources

### Primary Sources

| Source | Agency | URL | Data Available |
|--------|--------|-----|----------------|
| PPP FOIA Data | SBA | https://data.sba.gov/dataset/ppp-foia | 11.5M loans: borrower, lender, amount, NAICS, jobs, forgiveness status |
| 7(a) & 504 Loan Data | SBA | https://data.sba.gov/dataset/7-a-504-foia | Active and historical guaranteed loans, approval amounts, charge-off status |
| SBIR/STTR Awards | SBA/NSF | https://www.sbir.gov/api | Innovation grants by agency, topic, award amount, awardee |
| SAM.gov Entity Data | GSA | https://sam.gov/content/entity-information | Business registrations, CAGE codes, NAICS codes, exclusions |
| SBA Disaster Loans | SBA | https://data.sba.gov/dataset/disaster-loan-data-foia | Disaster lending by event, geography, amount |

### Supporting Sources

| Source | Agency | URL | Use In Analytics |
|--------|--------|-----|------------------|
| USAspending Awards | Treasury | https://www.usaspending.gov/download_center/award_data_archive | Federal contract awards to cross-reference SBA borrowers |
| Census CBP Data | Census | https://www.census.gov/programs-surveys/cbp.html | Business establishment counts by geography and NAICS |
| BLS QCEW | DOL | https://www.bls.gov/qcew/ | Employment counts to validate job retention claims |
| FDIC BankFind | FDIC | https://www.fdic.gov/analysis/quarterly-banking-profile | Lender institution profiles and financial health |
| DOJ Fraud Cases | DOJ | https://www.justice.gov/criminal-fraud | PPP fraud prosecution outcomes |
| Federal Reserve SLOOS | Fed | https://www.federalreserve.gov/data/sloos.htm | Senior Loan Officer Survey on lending standards |

---

## PPP Loan Distribution and Fraud Detection

### Background

The Paycheck Protection Program was the largest small business relief effort in U.S. history. The SBA's PPP FOIA dataset contains every loan approved, including borrower name, address, NAICS code, lender, loan amount, jobs reported, and forgiveness status. The Government Accountability Office (GAO) and the SBA Office of Inspector General have identified billions in potentially fraudulent claims, making this dataset a rich target for pattern-based fraud detection.

Common fraud patterns include: applications from businesses with no employees, multiple loans to the same entity or address, loans exceeding payroll-based eligibility, and rapid-fire applications through the same lender within minutes of portal opening.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # PPP Loan Distribution and Fraud Detection
# MAGIC Bronze-to-Silver transformation with fraud indicator scoring

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Load Bronze PPP data
df_ppp = spark.read.format("delta").load(
    "abfss://lh_bronze@onelake.dfs.fabric.microsoft.com/Tables/bronze_sba_ppp_loans"
)

# --- Fraud Indicator 1: Loan Amount Structuring ---
# Loans just below reporting thresholds ($150K boundary for detailed review)
df_structuring = df_ppp.withColumn(
    "structuring_flag",
    F.when(
        (F.col("loan_amount") >= 145000) & (F.col("loan_amount") < 150000), 1
    ).otherwise(0)
)

# --- Fraud Indicator 2: Velocity Analysis ---
# Multiple loans from same address within 24 hours
address_window = Window.partitionBy("borrower_address", "borrower_zip") \
    .orderBy("date_approved") \
    .rangeBetween(-86400, 86400)  # 24-hour window in seconds

df_velocity = df_structuring.withColumn(
    "same_address_loan_count",
    F.count("loan_number").over(address_window)
).withColumn(
    "velocity_flag",
    F.when(F.col("same_address_loan_count") > 2, 1).otherwise(0)
)

# --- Fraud Indicator 3: Jobs-to-Amount Ratio ---
# Flag loans where amount is disproportionate to reported employees
df_scored = df_velocity.withColumn(
    "amount_per_job",
    F.when(F.col("jobs_reported") > 0,
           F.col("loan_amount") / F.col("jobs_reported"))
    .otherwise(F.lit(None))
).withColumn(
    "ratio_flag",
    F.when(F.col("amount_per_job") > 125000, 1).otherwise(0)  # avg salary * 2.5x payroll multiplier
)

# --- Composite Fraud Risk Score ---
df_final = df_scored.withColumn(
    "fraud_risk_score",
    F.col("structuring_flag") + F.col("velocity_flag") + F.col("ratio_flag")
).withColumn(
    "fraud_risk_tier",
    F.when(F.col("fraud_risk_score") >= 3, "HIGH")
    .when(F.col("fraud_risk_score") == 2, "MEDIUM")
    .when(F.col("fraud_risk_score") == 1, "LOW")
    .otherwise("NONE")
)

# Write to Silver
df_final.write.format("delta").mode("overwrite").option(
    "overwriteSchema", "true"
).save("abfss://lh_silver@onelake.dfs.fabric.microsoft.com/Tables/silver_sba_ppp_fraud_scored")

print(f"PPP loans scored: {df_final.count():,}")
print(f"HIGH risk: {df_final.filter(F.col('fraud_risk_tier') == 'HIGH').count():,}")
```

---

## 7(a) and 504 Lending Trend Analysis

### Background

The SBA 7(a) program is the agency's primary general-purpose loan guarantee, supporting up to $5 million per loan for working capital, equipment, and real estate. The 504 program provides long-term fixed-rate financing for major assets. Together they represent the steady-state backbone of SBA lending. Key analytical dimensions include approval rates by lender type (bank vs. CDFI vs. credit union), geographic distribution relative to business density, industry concentration by NAICS code, and charge-off (default) patterns over loan life.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # 7(a)/504 Lending Trend Analysis
# MAGIC Gold-layer aggregations for lender performance and geographic access

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Load Silver 7(a)/504 data
df_loans = spark.read.format("delta").load(
    "abfss://lh_silver@onelake.dfs.fabric.microsoft.com/Tables/silver_sba_7a504_loans"
)

# --- Lender Concentration Index ---
# Calculate HHI by state to detect lending monopolies
lender_state = df_loans.groupBy("borrower_state", "lender_name").agg(
    F.sum("gross_approval").alias("total_approved"),
    F.count("*").alias("loan_count")
)

state_totals = lender_state.groupBy("borrower_state").agg(
    F.sum("total_approved").alias("state_total")
)

df_hhi = lender_state.join(state_totals, "borrower_state").withColumn(
    "market_share_pct",
    (F.col("total_approved") / F.col("state_total")) * 100
).withColumn(
    "share_squared",
    F.pow(F.col("market_share_pct"), 2)
)

state_hhi = df_hhi.groupBy("borrower_state").agg(
    F.sum("share_squared").alias("lending_hhi"),
    F.countDistinct("lender_name").alias("active_lenders"),
    F.sum("total_approved").alias("total_volume")
).withColumn(
    "concentration_tier",
    F.when(F.col("lending_hhi") > 2500, "HIGHLY_CONCENTRATED")
    .when(F.col("lending_hhi") > 1500, "MODERATELY_CONCENTRATED")
    .otherwise("COMPETITIVE")
)

# --- Charge-Off Analysis by Vintage ---
df_chargeoff = df_loans.withColumn(
    "approval_year", F.year("approval_date")
).groupBy("approval_year", "program").agg(
    F.count("*").alias("total_loans"),
    F.sum(F.when(F.col("loan_status") == "CHGOFF", 1).otherwise(0)).alias("charged_off"),
    F.sum("gross_approval").alias("total_approved"),
    F.sum(F.when(F.col("loan_status") == "CHGOFF", F.col("gross_charge_off_amount"))
          .otherwise(0)).alias("total_chargeoff_amount")
).withColumn(
    "chargeoff_rate",
    F.round(F.col("charged_off") / F.col("total_loans") * 100, 2)
).withColumn(
    "loss_severity",
    F.round(F.col("total_chargeoff_amount") / F.col("total_approved") * 100, 2)
)

# Write Gold tables
state_hhi.write.format("delta").mode("overwrite").save(
    "abfss://lh_gold@onelake.dfs.fabric.microsoft.com/Tables/gold_sba_lending_concentration"
)
df_chargeoff.write.format("delta").mode("overwrite").save(
    "abfss://lh_gold@onelake.dfs.fabric.microsoft.com/Tables/gold_sba_chargeoff_vintage"
)

print(f"States analyzed: {state_hhi.count()}")
print(f"Vintage cohorts: {df_chargeoff.count()}")
```

---

## SBIR/STTR Innovation Grant Analysis

### Background

The Small Business Innovation Research (SBIR) and Small Business Technology Transfer (STTR) programs represent $4+ billion in annual federal R&D investment directed to small businesses. Eleven federal agencies participate, with the Department of Defense, NIH, NSF, and DOE as the largest funders. The sbir.gov API provides structured award data including topic areas, award phases (Phase I feasibility, Phase II development, Phase III commercialization), and awardee details. Analyzing these grants alongside SBA lending data reveals whether innovation investment correlates with subsequent capital access and business growth.

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # SBIR/STTR Innovation Grant Analytics
# MAGIC Correlating R&D grants with lending outcomes and job creation

# COMMAND ----------

from pyspark.sql import functions as F

# Load SBIR awards and SBA lending data
df_sbir = spark.read.format("delta").load(
    "abfss://lh_silver@onelake.dfs.fabric.microsoft.com/Tables/silver_sba_sbir_awards"
)
df_loans = spark.read.format("delta").load(
    "abfss://lh_silver@onelake.dfs.fabric.microsoft.com/Tables/silver_sba_7a504_loans"
)

# --- SBIR Award Distribution by Agency and Phase ---
agency_phase = df_sbir.groupBy("agency", "phase").agg(
    F.count("*").alias("award_count"),
    F.sum("award_amount").alias("total_funding"),
    F.avg("award_amount").alias("avg_award"),
    F.countDistinct("company_name").alias("unique_awardees")
).withColumn(
    "commercialization_ratio",
    F.when(F.col("phase") == "Phase III",
           F.col("award_count")).otherwise(0)
)

# --- Innovation-to-Lending Pipeline ---
# Match SBIR awardees to SBA loan recipients by fuzzy name + zip
df_sbir_entities = df_sbir.select(
    F.upper(F.trim("company_name")).alias("entity_name"),
    F.col("zip").alias("entity_zip"),
    F.col("award_amount").alias("sbir_total"),
    F.col("phase").alias("sbir_phase"),
    F.col("award_year")
).distinct()

df_loan_entities = df_loans.select(
    F.upper(F.trim("borrower_name")).alias("entity_name"),
    F.col("borrower_zip").alias("entity_zip"),
    F.col("gross_approval").alias("loan_amount"),
    F.year("approval_date").alias("loan_year")
).distinct()

# Exact match on normalized name + zip
df_pipeline = df_sbir_entities.join(
    df_loan_entities,
    on=["entity_name", "entity_zip"],
    how="inner"
).filter(
    F.col("loan_year") >= F.col("award_year")  # Loan came after SBIR award
).withColumn(
    "years_to_lending",
    F.col("loan_year") - F.col("award_year")
)

pipeline_stats = df_pipeline.groupBy("sbir_phase").agg(
    F.count("*").alias("matched_entities"),
    F.avg("years_to_lending").alias("avg_years_to_loan"),
    F.avg("loan_amount").alias("avg_subsequent_loan"),
    F.avg("sbir_total").alias("avg_sbir_award")
)

# Write Gold
pipeline_stats.write.format("delta").mode("overwrite").save(
    "abfss://lh_gold@onelake.dfs.fabric.microsoft.com/Tables/gold_sba_sbir_lending_pipeline"
)

print(f"SBIR awardees matched to SBA loans: {df_pipeline.count():,}")
```

---

## Implementation in Fabric

### Table Inventory

| Layer | Table | Source | Description |
|-------|-------|--------|-------------|
| Bronze | `bronze_sba_ppp_loans` | PPP FOIA | Raw PPP loan records (11.5M rows) |
| Bronze | `bronze_sba_7a504_loans` | 7(a)/504 FOIA | Raw SBA guaranteed loan records |
| Bronze | `bronze_sba_sbir_awards` | sbir.gov API | Raw SBIR/STTR award records |
| Bronze | `bronze_sba_disaster_loans` | Disaster FOIA | Raw disaster loan records |
| Bronze | `bronze_sam_entities` | SAM.gov | Business entity registrations and exclusions |
| Silver | `silver_sba_ppp_fraud_scored` | PPP Bronze | Cleansed PPP loans with fraud risk scoring |
| Silver | `silver_sba_7a504_loans` | 7(a)/504 Bronze | Validated loans with lender enrichment |
| Silver | `silver_sba_sbir_awards` | SBIR Bronze | Normalized awards with phase classification |
| Silver | `silver_sam_entity_validated` | SAM Bronze | Deduplicated entities with NAICS mapping |
| Gold | `gold_sba_lending_concentration` | Silver 7(a)/504 | HHI by state, lender market share |
| Gold | `gold_sba_chargeoff_vintage` | Silver 7(a)/504 | Default rates by approval year cohort |
| Gold | `gold_sba_sbir_lending_pipeline` | Silver SBIR + 7(a) | Innovation-to-capital access correlation |
| Gold | `gold_sba_ppp_fraud_summary` | Silver PPP | Fraud risk aggregations by lender, state, industry |
| Gold | `gold_sba_lender_scorecard` | Silver 7(a)/504 + PPP | Lender performance composite scores |

### Notebook Sequence

1. `01_bronze_sba_ppp_ingest.py` - Ingest PPP FOIA CSV/Parquet into Delta Bronze
2. `02_bronze_sba_7a504_ingest.py` - Ingest 7(a)/504 loan data into Delta Bronze
3. `03_bronze_sba_sbir_ingest.py` - Pull SBIR awards from sbir.gov API into Bronze
4. `04_bronze_sam_entity_ingest.py` - Ingest SAM.gov entity extracts into Bronze
5. `05_silver_ppp_fraud_scoring.py` - Cleanse PPP data and apply fraud indicator scoring
6. `06_silver_7a504_validation.py` - Validate and enrich 7(a)/504 loan records
7. `07_silver_sbir_normalization.py` - Normalize SBIR awards with phase and agency mapping
8. `08_gold_lending_concentration.py` - Calculate HHI and lender market share by state
9. `09_gold_chargeoff_analysis.py` - Compute vintage cohort charge-off rates
10. `10_gold_sbir_lending_pipeline.py` - Correlate SBIR awardees with subsequent SBA loans
11. `11_gold_lender_scorecard.py` - Build composite lender performance scores

---

## Power BI Visualizations

### Recommended Visuals

| Page | Visual Type | Data | Purpose |
|------|-------------|------|---------|
| PPP Overview | Filled Map | `gold_sba_ppp_fraud_summary` | Loan distribution and fraud density by state |
| PPP Overview | Stacked Bar | `silver_sba_ppp_fraud_scored` | Fraud risk tier distribution by NAICS sector |
| PPP Fraud Drill | Scatter Plot | `silver_sba_ppp_fraud_scored` | Loan amount vs. jobs reported with risk tier color |
| PPP Fraud Drill | Table | `silver_sba_ppp_fraud_scored` | Top HIGH-risk loans with detail columns |
| Lending Trends | Line Chart | `gold_sba_chargeoff_vintage` | Charge-off rates by vintage year and program |
| Lending Trends | Clustered Bar | `gold_sba_lending_concentration` | Top/bottom 10 states by lending HHI |
| Lender Scorecard | KPI Cards + Table | `gold_sba_lender_scorecard` | Top lenders ranked by composite performance score |
| Innovation Pipeline | Sankey Diagram | `gold_sba_sbir_lending_pipeline` | SBIR Phase I -> Phase II -> SBA Loan flow |
| Innovation Pipeline | Treemap | `gold_sba_sbir_lending_pipeline` | SBIR funding by agency and technology area |

### DAX Measures

```dax
// PPP Fraud Rate by Lender
PPP Fraud Rate =
VAR _HighRisk =
    CALCULATE(
        COUNTROWS('silver_sba_ppp_fraud_scored'),
        'silver_sba_ppp_fraud_scored'[fraud_risk_tier] = "HIGH"
    )
VAR _Total =
    COUNTROWS('silver_sba_ppp_fraud_scored')
RETURN
    DIVIDE(_HighRisk, _Total, 0)
```

```dax
// Weighted Charge-Off Severity
Weighted Chargeoff Severity =
SUMX(
    'gold_sba_chargeoff_vintage',
    'gold_sba_chargeoff_vintage'[total_chargeoff_amount]
        / 'gold_sba_chargeoff_vintage'[total_approved]
        * 'gold_sba_chargeoff_vintage'[total_loans]
) / SUM('gold_sba_chargeoff_vintage'[total_loans])
```

```dax
// Lending HHI Classification
HHI Classification =
VAR _HHI = SELECTEDVALUE('gold_sba_lending_concentration'[lending_hhi])
RETURN
    SWITCH(
        TRUE(),
        _HHI > 2500, "Highly Concentrated",
        _HHI > 1500, "Moderately Concentrated",
        "Competitive"
    )
```

```dax
// SBIR-to-Loan Conversion Rate
SBIR Loan Conversion =
VAR _SBIRAwardees =
    DISTINCTCOUNT('silver_sba_sbir_awards'[company_name])
VAR _MatchedToLoans =
    DISTINCTCOUNT('gold_sba_sbir_lending_pipeline'[entity_name])
RETURN
    DIVIDE(_MatchedToLoans, _SBIRAwardees, 0)
```

---

## Cross-Domain Analysis

### Hypothesis 1: SBA Lending Concentration x DOJ Antitrust Market HHI

**Hypothesis:** States with high market concentration (DOJ antitrust HHI > 2,500) in key industries show correspondingly concentrated SBA lending, suggesting that monopolistic markets also restrict small business capital access.

```sql
-- Cross-reference SBA lending HHI with DOJ market concentration
SELECT
    sba.borrower_state,
    sba.lending_hhi,
    sba.concentration_tier AS lending_concentration,
    doj.industry_hhi,
    doj.concentration_tier AS market_concentration,
    CASE
        WHEN sba.lending_hhi > 2500 AND doj.industry_hhi > 2500
        THEN 'DUAL_CONCENTRATED'
        ELSE 'DIVERGENT'
    END AS concentration_alignment
FROM gold_sba_lending_concentration sba
JOIN gold_doj_market_hhi doj
    ON sba.borrower_state = doj.state
WHERE sba.lending_hhi > 1500 OR doj.industry_hhi > 1500
ORDER BY sba.lending_hhi DESC
```

### Hypothesis 2: SBA Rural Lending x USDA Agricultural Economics

**Hypothesis:** Counties with high USDA crop production value but low SBA 7(a) loan volume represent underserved agricultural communities where small businesses lack capital access despite strong economic fundamentals.

```python
# Cross-domain: SBA lending deserts in high-value agricultural counties
df_usda = spark.read.format("delta").load(
    "abfss://lh_gold@onelake.dfs.fabric.microsoft.com/Tables/gold_usda_crop_production"
)
df_sba = spark.read.format("delta").load(
    "abfss://lh_gold@onelake.dfs.fabric.microsoft.com/Tables/gold_sba_lending_concentration"
)

df_rural_gap = df_usda.join(
    df_sba,
    df_usda.state_alpha == df_sba.borrower_state,
    "left"
).withColumn(
    "lending_gap_score",
    F.col("crop_value_millions") / F.coalesce(F.col("total_volume"), F.lit(1))
).filter(
    F.col("lending_gap_score") > 2.0  # High ag value, low lending
).orderBy(F.desc("lending_gap_score"))

df_rural_gap.select(
    "state_alpha", "crop_value_millions", "total_volume",
    "active_lenders", "lending_gap_score"
).show(20)
```

### Hypothesis 3: PPP Fraud Density x BOP Incarceration Rates

**Hypothesis:** Metropolitan areas with higher federal incarceration rates for financial crimes (BOP data) subsequently show higher PPP fraud risk scores, suggesting geographic clustering of financial fraud expertise.

```sql
-- PPP fraud density vs federal financial crime incarceration
SELECT
    ppp.borrower_state,
    ppp.fraud_high_count,
    ppp.fraud_rate_pct,
    bop.financial_crime_inmates,
    bop.financial_crime_rate_per_100k,
    CORR(ppp.fraud_rate_pct, bop.financial_crime_rate_per_100k)
        OVER () AS correlation_coefficient
FROM gold_sba_ppp_fraud_summary ppp
JOIN gold_bop_incarceration_by_offense bop
    ON ppp.borrower_state = bop.state
ORDER BY ppp.fraud_rate_pct DESC
```

---

## Microsoft Published Resources

| Resource | URL | Relevance |
|----------|-----|-----------|
| Real-Time Fraud Detection with Stream Analytics | https://learn.microsoft.com/azure/stream-analytics/stream-analytics-real-time-fraud-detection | Architecture pattern for streaming fraud indicator scoring |
| Microsoft Fabric Security White Paper | https://learn.microsoft.com/fabric/security/security-overview | Row-level security for lender-specific views, workspace permissions |
| Cloud-Scale Analytics with Microsoft Fabric | https://learn.microsoft.com/fabric/get-started/microsoft-fabric-overview | Unified analytics platform for consolidating SBA data sources |
| Power BI Embedded Analytics | https://learn.microsoft.com/power-bi/developer/embedded/embedded-analytics-power-bi | Embedding lending dashboards in congressional reporting portals |
| Delta Lake in Microsoft Fabric | https://learn.microsoft.com/fabric/data-engineering/lakehouse-and-delta-tables | Time-travel and versioning for audit trail on fraud scoring changes |
| Microsoft Purview Data Governance | https://learn.microsoft.com/purview/purview-overview | Data lineage and classification for PII in lending records |

---

## Published References

| Reference | Source | URL |
|-----------|--------|-----|
| PPP FOIA Full Dataset | SBA | https://data.sba.gov/dataset/ppp-foia |
| 7(a) and 504 Loan Data | SBA | https://data.sba.gov/dataset/7-a-504-foia |
| SBIR Award Data API | SBA | https://www.sbir.gov/api |
| SAM.gov Entity Information | GSA | https://sam.gov/content/entity-information |
| PPP Fraud Oversight Reports | SBA OIG | https://www.sba.gov/about-sba/oversight-advocacy/office-inspector-general |
| GAO PPP Fraud Reports | GAO | https://www.gao.gov/products/gao-22-105051 |
| SBA Lending Statistics | SBA | https://www.sba.gov/about-sba/sba-performance/open-government/digital-sba/open-data/open-data-sources |

---

## Related Documentation

- [Antitrust Analytics](antitrust-analytics.md) - DOJ market concentration analysis (cross-domain with SBA lending HHI)
- [Federal Justice Analytics](federal-justice-analytics.md) - DOJ/BOP data for fraud prosecution correlation
- [Best Practices: Medallion Architecture](../best-practices/medallion-architecture-deep-dive.md) - Bronze/Silver/Gold patterns used in lending pipelines
- [Best Practices: Real-Time Intelligence](../features/real-time-intelligence.md) - Streaming fraud detection architecture
- [Best Practices: Data Sharing & Federation](../best-practices/data-sharing-federation.md) - Cross-agency data federation patterns
- [Tutorial 25: SBA Bronze Ingestion](../tutorials/33-sba-small-business/README.md) - Step-by-step SBA data loading

---

*Last Updated: 2026-04-23*
