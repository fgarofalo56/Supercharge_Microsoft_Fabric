# Antitrust Analytics

> Leveraging Microsoft Fabric to analyze market concentration, merger activity, and cartel detection patterns using publicly available DOJ, FTC, and federal enforcement data.

---

## Executive Summary

Antitrust enforcement is among the most data-intensive functions in federal law enforcement. The Department of Justice Antitrust Division and the Federal Trade Commission collectively review thousands of merger filings annually under the Hart-Scott-Rodino (HSR) Act, investigate price-fixing conspiracies, and monitor market concentration across every sector of the U.S. economy.

Historically, this analysis has been fragmented across agency systems, spreadsheets, and ad-hoc tools. A unified analytics platform on Microsoft Fabric enables:

- **Real-time market concentration monitoring** using the Herfindahl-Hirschman Index (HHI)
- **Merger review pipeline tracking** from HSR filing through final disposition
- **Cartel detection pattern recognition** across bid-rigging, price-fixing, and market allocation schemes
- **Cross-agency correlation** linking antitrust outcomes to small business lending (SBA), environmental compliance (EPA), and economic indicators

This use case demonstrates how the Supercharge Microsoft Fabric POC's medallion architecture, PySpark notebooks, and Power BI visualizations apply to antitrust analytics using real, publicly available data sources.

---

## Data Sources

### Primary Sources

| Source | Agency | URL | Data Available |
|--------|--------|-----|----------------|
| Antitrust Case Filings | DOJ | https://www.justice.gov/atr/antitrust-case-filings | Civil and criminal case index, filing dates, outcomes |
| HSR Filing Data | FTC/DOJ | https://catalog.data.gov | Premerger notification statistics, filing volumes |
| 2023 Merger Guidelines | FTC/DOJ | https://www.justice.gov/atr/2023-merger-guidelines | Current HHI thresholds and analytical framework |
| Competition Cases | FTC | https://www.ftc.gov/legal-library/browse/cases-proceedings | Enforcement actions, consent orders, merger challenges |
| Open Data Portal | DOJ | https://www.justice.gov/open/open-data | Cross-division datasets |

### Supporting Sources

| Source | Agency | URL | Use In Analytics |
|--------|--------|-----|------------------|
| FBI Crime Data Explorer | FBI | https://cde.ucr.cjis.gov | White-collar crime overlay |
| USSC Research | USSC | https://www.ussc.gov/research | Antitrust sentencing outcomes |
| BJS Statistics | DOJ | https://bjs.ojp.gov | Federal prosecution pipeline |
| USAspending | Treasury | https://www.usaspending.gov | Government contract concentration |
| SBA Lending Data | SBA | https://data.sba.gov | Small business lending by market |
| SEC EDGAR | SEC | https://www.sec.gov/edgar | Public company filings, M&A disclosures |

---

## HHI Market Concentration Analysis

### Background

The Herfindahl-Hirschman Index (HHI) is the standard measure of market concentration used by the DOJ and FTC in merger review. It is calculated as the sum of the squares of market share percentages for all firms in a market.

```
HHI = Σ (market_share_i)²
```

Where `market_share_i` is the percentage market share of firm `i`.

### 2023 DOJ/FTC Merger Guidelines Thresholds

The revised Merger Guidelines published in December 2023 establish the following HHI thresholds:

| Classification | HHI Range | Enforcement Implication |
|----------------|-----------|------------------------|
| **Unconcentrated** | HHI < 1,500 | Mergers unlikely to raise concerns |
| **Moderately Concentrated** | 1,500 ≤ HHI ≤ 2,500 | Mergers increasing HHI by > 100 warrant scrutiny |
| **Highly Concentrated** | HHI > 2,500 | Mergers increasing HHI by > 100 presumed anticompetitive |

### Delta (Change in HHI) Thresholds

The delta (ΔHHI) measures the change in market concentration caused by a proposed merger:

```
ΔHHI = HHI_post_merger - HHI_pre_merger
```

Simplified calculation for a merger between firms with shares `a` and `b`:

```
ΔHHI = 2 × a × b
```

| Market Status | Delta Threshold | Presumption |
|---------------|-----------------|-------------|
| Moderately Concentrated (1,500–2,500) | ΔHHI > 200 | Presumptively anticompetitive |
| Highly Concentrated (> 2,500) | ΔHHI > 100 | Presumptively anticompetitive |
| Any market | ΔHHI > 200 with post-merger HHI > 2,500 | Strong presumption; shifts burden to merging parties |

### PySpark: HHI Calculation

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # HHI Market Concentration Analysis
# MAGIC Bronze → Silver → Gold pipeline for HHI computation

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Read market share data from Silver layer
df_market = spark.read.table("lh_silver.antitrust_market_shares")

# Calculate HHI per market per year
df_hhi = (
    df_market
    .withColumn("share_squared", F.col("market_share_pct") ** 2)
    .groupBy("market_id", "naics_code", "market_name", "year")
    .agg(
        F.sum("share_squared").alias("hhi"),
        F.count("firm_id").alias("firm_count"),
        F.max("market_share_pct").alias("top_firm_share"),
        F.collect_list(
            F.struct("firm_name", "market_share_pct")
        ).alias("firms")
    )
)

# Classify concentration levels per 2023 Guidelines
df_hhi_classified = (
    df_hhi
    .withColumn(
        "concentration_level",
        F.when(F.col("hhi") < 1500, "Unconcentrated")
         .when(F.col("hhi") <= 2500, "Moderately Concentrated")
         .otherwise("Highly Concentrated")
    )
    .withColumn(
        "enforcement_flag",
        F.when(F.col("hhi") > 2500, True).otherwise(False)
    )
)

# Write to Gold layer
df_hhi_classified.write.format("delta").mode("overwrite").saveAsTable(
    "lh_gold.antitrust_hhi_concentration"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## HHI Year-over-Year Change

# COMMAND ----------

w = Window.partitionBy("market_id").orderBy("year")

df_hhi_delta = (
    df_hhi_classified
    .withColumn("hhi_prior_year", F.lag("hhi").over(w))
    .withColumn("hhi_delta", F.col("hhi") - F.col("hhi_prior_year"))
    .withColumn(
        "trend",
        F.when(F.col("hhi_delta") > 100, "Concentrating")
         .when(F.col("hhi_delta") < -100, "Deconcentrating")
         .otherwise("Stable")
    )
)

df_hhi_delta.write.format("delta").mode("overwrite").saveAsTable(
    "lh_gold.antitrust_hhi_trends"
)
```

---

## Merger Review Pipeline

### Pipeline Stages

A merger subject to HSR notification follows this pipeline:

```
HSR Filing
  └── Initial Review (30 calendar days)
        ├── Early Termination (approved before 30 days)
        └── Second Request (extended investigation)
              └── Extended Review (variable, often 6-12 months)
                    ├── Approved (unconditional clearance)
                    ├── Approved with Conditions (consent decree / divestiture)
                    ├── Challenged (DOJ/FTC files suit)
                    │     ├── Blocked (court injunction)
                    │     └── Settlement (negotiated remedy)
                    └── Abandoned (parties withdraw)
```

### Pipeline Data Model

```
Bronze: raw_hsr_filings
  - filing_id, filing_date, acquirer, target, transaction_value,
    naics_code, agency_assigned (DOJ or FTC)

Silver: hsr_filings_cleansed
  - Standardized names, validated NAICS codes, deduplicated,
    enriched with market_id lookup

Gold: merger_review_pipeline
  - filing_id, stage, stage_entry_date, stage_exit_date,
    days_in_stage, outcome, remedy_type, divestitures
```

### PySpark: Merger Pipeline Analytics

```python
# COMMAND ----------

from pyspark.sql import functions as F

df_mergers = spark.read.table("lh_gold.merger_review_pipeline")

# Stage duration analysis
df_stage_stats = (
    df_mergers
    .groupBy("stage", "outcome")
    .agg(
        F.count("filing_id").alias("filing_count"),
        F.avg("days_in_stage").alias("avg_days"),
        F.percentile_approx("days_in_stage", 0.5).alias("median_days"),
        F.max("days_in_stage").alias("max_days")
    )
    .orderBy("stage", "outcome")
)

# Challenge rate by NAICS sector
df_challenge_rate = (
    df_mergers
    .filter(F.col("stage") == "Decision")
    .groupBy("naics_sector")
    .agg(
        F.count("filing_id").alias("total_reviews"),
        F.sum(
            F.when(F.col("outcome").isin("Challenged", "Blocked"), 1).otherwise(0)
        ).alias("challenged_count"),
    )
    .withColumn(
        "challenge_rate",
        F.round(F.col("challenged_count") / F.col("total_reviews") * 100, 2)
    )
    .orderBy(F.desc("challenge_rate"))
)

df_challenge_rate.write.format("delta").mode("overwrite").saveAsTable(
    "lh_gold.antitrust_challenge_rates"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Second Request Analysis
# MAGIC Second Requests are the "deep dive" investigations. Tracking their
# MAGIC frequency and outcomes reveals enforcement intensity trends.

# COMMAND ----------

df_second_requests = (
    df_mergers
    .filter(F.col("stage") == "Second Request")
    .withColumn("year", F.year("stage_entry_date"))
    .groupBy("year")
    .agg(
        F.count("filing_id").alias("second_requests_issued"),
        F.avg("days_in_stage").alias("avg_review_days"),
        F.sum(
            F.when(F.col("outcome") == "Abandoned", 1).otherwise(0)
        ).alias("abandoned_after_2r")
    )
    .orderBy("year")
)

df_second_requests.write.format("delta").mode("overwrite").saveAsTable(
    "lh_gold.antitrust_second_request_trends"
)
```

---

## Cartel Detection Patterns

### Types of Antitrust Conspiracies

| Pattern | Description | Detection Signals |
|---------|-------------|-------------------|
| **Price Fixing** | Competitors agree to set prices | Parallel pricing, identical bid amounts, unusual price stability |
| **Bid Rigging** | Competitors coordinate bids on contracts | Rotating winners, complementary bidding, cover bids with consistent spreads |
| **Market Allocation** | Competitors divide territories or customers | Geographic exclusivity, customer non-compete, sudden market exits |
| **Group Boycott** | Competitors agree to exclude a rival | Coordinated refusal to deal, simultaneous contract terminations |

### Bid-Rigging Detection Analytics

```python
# COMMAND ----------

# MAGIC %md
# MAGIC # Bid-Rigging Pattern Detection
# MAGIC Identifies suspicious patterns in government contract bidding.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

df_bids = spark.read.table("lh_silver.government_contract_bids")

# Pattern 1: Rotating winners
# If a small group of firms take turns winning in a market, flag it
w_market = Window.partitionBy("market_id", "contract_category").orderBy("award_date")

df_winners = (
    df_bids
    .filter(F.col("is_winner") == True)
    .withColumn("prev_winner", F.lag("firm_id").over(w_market))
    .withColumn("prev_prev_winner", F.lag("firm_id", 2).over(w_market))
    .withColumn(
        "rotation_flag",
        F.when(
            (F.col("firm_id") == F.col("prev_prev_winner")) &
            (F.col("firm_id") != F.col("prev_winner")),
            True
        ).otherwise(False)
    )
)

# Pattern 2: Cover bids with consistent spreads
# If losing bids are always X% above the winner, that is suspicious
df_bid_spreads = (
    df_bids
    .join(
        df_bids.filter(F.col("is_winner") == True)
        .select(
            F.col("contract_id"),
            F.col("bid_amount").alias("winning_bid")
        ),
        on="contract_id"
    )
    .filter(F.col("is_winner") == False)
    .withColumn(
        "spread_pct",
        F.round(
            (F.col("bid_amount") - F.col("winning_bid"))
            / F.col("winning_bid") * 100, 2
        )
    )
)

# Flag markets where spread variance is suspiciously low
df_suspicious_markets = (
    df_bid_spreads
    .groupBy("market_id", "firm_id")
    .agg(
        F.avg("spread_pct").alias("avg_spread"),
        F.stddev("spread_pct").alias("spread_stddev"),
        F.count("contract_id").alias("bid_count")
    )
    .filter(
        (F.col("spread_stddev") < 1.0) &  # Very consistent spreads
        (F.col("bid_count") >= 5)           # Enough data points
    )
)

df_suspicious_markets.write.format("delta").mode("overwrite").saveAsTable(
    "lh_gold.antitrust_bidrigging_flags"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Price-Fixing Detection: Parallel Pricing

# COMMAND ----------

# Pattern 3: Parallel pricing — competitors change prices
# in lockstep within a narrow time window
df_prices = spark.read.table("lh_silver.market_prices")

w_firm = Window.partitionBy("firm_id", "product_category").orderBy("effective_date")

df_price_changes = (
    df_prices
    .withColumn("prev_price", F.lag("price").over(w_firm))
    .withColumn("price_change_pct", 
        F.round((F.col("price") - F.col("prev_price")) / F.col("prev_price") * 100, 2)
    )
    .filter(F.col("price_change_pct").isNotNull())
)

# Find instances where multiple firms changed prices by similar amounts
# within a short window
df_parallel = (
    df_price_changes.alias("a")
    .join(
        df_price_changes.alias("b"),
        (F.col("a.product_category") == F.col("b.product_category")) &
        (F.col("a.firm_id") != F.col("b.firm_id")) &
        (F.abs(F.datediff(F.col("a.effective_date"), F.col("b.effective_date"))) <= 7) &
        (F.abs(F.col("a.price_change_pct") - F.col("b.price_change_pct")) < 0.5)
    )
    .select(
        F.col("a.product_category"),
        F.col("a.firm_id").alias("firm_a"),
        F.col("b.firm_id").alias("firm_b"),
        F.col("a.effective_date").alias("date_a"),
        F.col("b.effective_date").alias("date_b"),
        F.col("a.price_change_pct").alias("change_a"),
        F.col("b.price_change_pct").alias("change_b")
    )
)

df_parallel.write.format("delta").mode("overwrite").saveAsTable(
    "lh_gold.antitrust_parallel_pricing_flags"
)
```

---

## Penalty & Sentencing Analysis

### Criminal Antitrust Penalties

DOJ criminal antitrust cases carry significant penalties. Analysis of USSC sentencing data reveals patterns in enforcement outcomes.

```python
# COMMAND ----------

from pyspark.sql import functions as F

df_sentences = spark.read.table("lh_silver.ussc_antitrust_sentences")

# Penalty analysis by offense type
df_penalties = (
    df_sentences
    .groupBy("offense_type", "fiscal_year")
    .agg(
        F.count("case_id").alias("case_count"),
        F.sum("fine_amount").alias("total_fines"),
        F.avg("fine_amount").alias("avg_fine"),
        F.max("fine_amount").alias("max_fine"),
        F.avg("prison_months").alias("avg_prison_months"),
        F.sum(
            F.when(F.col("prison_months") > 0, 1).otherwise(0)
        ).alias("incarceration_count")
    )
    .withColumn(
        "incarceration_rate",
        F.round(F.col("incarceration_count") / F.col("case_count") * 100, 2)
    )
    .orderBy("fiscal_year", "offense_type")
)

df_penalties.write.format("delta").mode("overwrite").saveAsTable(
    "lh_gold.antitrust_penalty_trends"
)
```

---

## Implementation in Fabric

### Table Inventory

| Layer | Table | Source | Description |
|-------|-------|--------|-------------|
| Bronze | `bronze_doj_antitrust_filings` | DOJ Case Index | Raw case filing records |
| Bronze | `bronze_hsr_filings` | HSR/Data.gov | Raw premerger notification data |
| Bronze | `bronze_ftc_enforcement` | FTC Cases | Raw FTC enforcement actions |
| Bronze | `bronze_ussc_sentences` | USSC | Raw sentencing data |
| Bronze | `bronze_government_bids` | USAspending | Raw contract bid data |
| Silver | `silver_antitrust_cases` | Cleansed, deduplicated case records | |
| Silver | `silver_hsr_filings` | Standardized HSR filings with NAICS validation | |
| Silver | `silver_market_shares` | Computed market shares from revenue/contract data | |
| Silver | `silver_ussc_antitrust_sentences` | Validated sentencing records | |
| Gold | `gold_hhi_concentration` | HHI scores per market per year | |
| Gold | `gold_hhi_trends` | Year-over-year HHI changes | |
| Gold | `gold_merger_pipeline` | Merger review stage tracking | |
| Gold | `gold_challenge_rates` | Challenge rate by sector | |
| Gold | `gold_bidrigging_flags` | Suspicious bidding patterns | |
| Gold | `gold_parallel_pricing_flags` | Parallel pricing detections | |
| Gold | `gold_penalty_trends` | Penalty and sentencing trends | |

### Notebook Sequence

```
01_bronze_doj_antitrust_ingest.py     → Ingest DOJ case filings
02_bronze_hsr_ingest.py               → Ingest HSR filing data
03_silver_antitrust_cleanse.py        → Cleanse and standardize cases
04_silver_market_share_compute.py     → Calculate market shares
05_gold_hhi_analysis.py              → HHI concentration & trends
06_gold_merger_pipeline.py           → Merger review pipeline analytics
07_gold_cartel_detection.py          → Bid-rigging & price-fixing patterns
08_gold_penalty_analysis.py          → Sentencing and fine trends
```

---

## Power BI Visualizations

### Recommended Visuals

| Visual | Type | Data Source | Purpose |
|--------|------|-------------|---------|
| **HHI Scatter Plot** | Scatter chart | `gold_hhi_concentration` | X: firm count, Y: HHI, color: concentration level, size: top firm share |
| **HHI Trend Lines** | Line chart | `gold_hhi_trends` | HHI over time per sector with threshold reference lines at 1,500 and 2,500 |
| **Merger Funnel** | Funnel chart | `gold_merger_pipeline` | Filing → Review → Second Request → Decision (with branch counts) |
| **Challenge Rate Bar** | Bar chart | `gold_challenge_rates` | Challenge rate by NAICS sector, sorted descending |
| **Penalty Waterfall** | Waterfall chart | `gold_penalty_trends` | Total fines by year showing growth/decline contributions |
| **Bid-Rigging Heat Map** | Matrix | `gold_bidrigging_flags` | Markets × firms with color intensity by flag count |
| **Geographic Map** | Map | `gold_hhi_concentration` | Regional HHI by market geography |

### DAX Measures

```dax
// HHI Classification
HHI Classification =
SWITCH(
    TRUE(),
    [HHI] < 1500, "Unconcentrated",
    [HHI] <= 2500, "Moderately Concentrated",
    "Highly Concentrated"
)

// Challenge Rate
Challenge Rate =
DIVIDE(
    CALCULATE(
        COUNTROWS('MergerPipeline'),
        'MergerPipeline'[Outcome] IN {"Challenged", "Blocked"}
    ),
    COUNTROWS('MergerPipeline'),
    0
)

// YoY HHI Change
HHI Delta YoY =
VAR CurrentHHI = [HHI]
VAR PriorHHI =
    CALCULATE(
        [HHI],
        DATEADD('Calendar'[Date], -1, YEAR)
    )
RETURN
    CurrentHHI - PriorHHI
```

---

## Cross-Domain Analysis

### Antitrust × SBA Small Business Lending

**Hypothesis:** Market consolidation (rising HHI) in a region correlates with reduced small business loan origination.

```python
# COMMAND ----------

# Join antitrust HHI data with SBA lending data by geography and year
df_hhi = spark.read.table("lh_gold.antitrust_hhi_concentration")
df_sba = spark.read.table("lh_gold.sba_loan_origination_by_region")

df_cross = (
    df_hhi
    .join(df_sba, on=["state_fips", "year"], how="inner")
    .select(
        "state_fips", "year", "market_name",
        "hhi", "concentration_level",
        "total_loans", "total_loan_amount", "avg_loan_size"
    )
)

# Correlation analysis
from pyspark.ml.stat import Correlation
from pyspark.ml.feature import VectorAssembler

assembler = VectorAssembler(
    inputCols=["hhi", "total_loans", "total_loan_amount"],
    outputCol="features"
)
df_vector = assembler.transform(df_cross)
correlation_matrix = Correlation.corr(df_vector, "features").head()[0]
print("HHI vs Loan Count correlation:", correlation_matrix.toArray()[0][1])
```

### Antitrust × EPA Compliance

**Hypothesis:** Industries with monopolistic market structures (HHI > 2,500) show different environmental compliance patterns than competitive markets.

```python
# COMMAND ----------

df_hhi = spark.read.table("lh_gold.antitrust_hhi_concentration")
df_epa = spark.read.table("lh_gold.epa_enforcement_by_naics")

df_cross_epa = (
    df_hhi
    .join(df_epa, on=["naics_code", "year"], how="inner")
    .groupBy("concentration_level")
    .agg(
        F.avg("violation_count").alias("avg_violations"),
        F.avg("penalty_amount").alias("avg_penalty"),
        F.avg("compliance_rate").alias("avg_compliance_rate")
    )
)

df_cross_epa.show()
```

---

## Published References

### Primary Regulatory Sources

- **2023 Merger Guidelines** — U.S. Department of Justice & Federal Trade Commission (December 2023)
  https://www.justice.gov/atr/2023-merger-guidelines

- **DOJ Antitrust Case Filings Index**
  https://www.justice.gov/atr/antitrust-case-filings

- **FTC Competition Enforcement Cases**
  https://www.ftc.gov/legal-library/browse/cases-proceedings

- **HSR Filing Statistics** — Hart-Scott-Rodino Annual Reports
  https://www.ftc.gov/policy/reports/policy-reports/annual-competition-reports

### Data Sources

- **DOJ Open Data Portal**
  https://www.justice.gov/open/open-data

- **FBI Crime Data Explorer (CDE)**
  https://cde.ucr.cjis.gov

- **U.S. Sentencing Commission Research**
  https://www.ussc.gov/research

- **Bureau of Justice Statistics (BJS)**
  https://bjs.ojp.gov

- **Data.gov Federal Datasets**
  https://catalog.data.gov

- **USAspending.gov**
  https://www.usaspending.gov

### Academic & Research

- **ICPSR National Archive of Criminal Justice Data (NACJD)**
  https://www.icpsr.umich.edu/web/pages/NACJD/index.html

- **Vera Institute of Justice — Incarceration Trends**
  https://github.com/vera-institute/incarceration-trends

- **DEA Data and Statistics**
  https://www.dea.gov/data-and-statistics

- **Bureau of Prisons (BOP) Statistics**
  https://www.bop.gov/about/statistics/

---

## Microsoft Published Resources

The following Microsoft-published white papers and reference architectures provide foundational guidance for building antitrust analytics on Azure and Microsoft Fabric:

- **Microsoft Fabric Security White Paper** — End-to-end security architecture for protecting sensitive enforcement data
  https://learn.microsoft.com/en-us/fabric/security/white-paper-landing-page

- **Medallion Lakehouse Architecture in Fabric** — Official Bronze/Silver/Gold pattern guidance used in this POC
  https://learn.microsoft.com/en-us/fabric/onelake/onelake-medallion-lakehouse-architecture

- **Cloud-Scale Analytics (Cloud Adoption Framework)** — Enterprise data platform patterns including data mesh and governance
  https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/scenarios/cloud-scale-analytics/

- **Real-Time Fraud Detection with Azure Stream Analytics** — Pattern applicable to cartel bid-rigging detection
  https://learn.microsoft.com/en-us/azure/stream-analytics/stream-analytics-real-time-fraud-detection

- **Advanced Analytics with Power BI** — Predictive analytics and DAX patterns for enforcement trend analysis
  https://info.microsoft.com/advanced-analytics-with-power-bi.html?Is=Website

- **Power BI White Papers** — Complete collection including security, dataflows, and deployment guidance
  https://learn.microsoft.com/en-us/power-bi/guidance/whitepapers

---

## Related Documentation

- [Federal Justice Analytics](federal-justice-analytics.md)
- [Use Cases Index](index.md)
- [Published References Catalog](references/README.md)
- [Medallion Architecture Deep Dive](../best-practices/medallion-architecture-deep-dive.md)
- [Data Governance](../best-practices/data-governance-deep-dive.md)

---

*Last Updated: 2026-04-23*
