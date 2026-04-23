# Use Cases & Applied Analytics

> Domain-specific analytical use cases built on the **Supercharge Microsoft Fabric** POC infrastructure, demonstrating how the medallion architecture, real-time intelligence, and governance frameworks apply to real-world federal and regulatory scenarios.

---

## Overview

The Supercharge Microsoft Fabric POC provides a comprehensive data platform foundation. These use cases show how that foundation translates into actionable analytics for specific domains — combining publicly available federal datasets with the Bronze/Silver/Gold medallion architecture, PySpark transformations, and Power BI visualizations already established in the POC.

Each use case includes:

- **Data source catalog** with real, publicly available URLs
- **Medallion pipeline design** (Bronze ingestion, Silver cleansing, Gold analytics)
- **PySpark implementation examples** ready for Fabric notebooks
- **Power BI visualization recommendations**
- **Cross-domain analysis** connecting multiple federal datasets

---

## Use Cases

| Use Case | Domain | Key Analytics | Status |
|----------|--------|---------------|--------|
| [Antitrust Analytics](antitrust-analytics.md) | DOJ/FTC Competition | HHI concentration, merger review, cartel detection | Available |
| [Federal Justice Analytics](federal-justice-analytics.md) | DOJ/FBI/BOP | Crime trends, prosecution pipeline, sentencing disparity | Available |

---

## Cross-Domain Analysis Possibilities

One of the strengths of a unified Fabric lakehouse is the ability to join datasets across agencies and domains. The following cross-domain analyses become possible when multiple use cases are deployed together:

| Cross-Domain Pair | Analytical Question |
|--------------------|---------------------|
| **DOJ Antitrust x SBA Lending** | Does market consolidation in a region correlate with reduced small business lending? |
| **DOJ Antitrust x EPA Compliance** | Do monopolistic industries show different environmental compliance patterns? |
| **FBI Crime x USDA Rural** | How do crime trends in rural counties correlate with agricultural economic indicators? |
| **BOP Incarceration x SBA** | Do regions with higher incarceration rates show lower small business formation? |
| **DOJ Sentencing x NOAA Weather** | Are there seasonal patterns in federal case filings or sentencing outcomes? |
| **DEA Enforcement x EPA** | Do drug enforcement seizure patterns correlate with environmental contamination reports? |

These analyses leverage the shared lakehouse — no data movement required, just Gold-layer joins across domain tables.

---

## Architecture Alignment

All use cases follow the POC's established patterns:

```
Bronze (Raw Ingestion)
  └── API/CSV ingestion via PySpark notebooks
  └── Append-only, schema-on-read
  └── Source metadata preserved

Silver (Cleansed & Validated)
  └── Schema enforcement, deduplication
  └── Data quality checks (Great Expectations)
  └── Standardized column naming

Gold (Business Analytics)
  └── Star schema / aggregated KPIs
  └── Direct Lake connectivity to Power BI
  └── Cross-domain join tables
```

---

## Reference Data

A curated catalog of all published data sources, organized by category, is available in the [References](references/README.md) section.

---

## Getting Started

1. **Deploy the POC infrastructure** — See the main [Deployment Guide](../index.md)
2. **Choose a use case** — Start with one that aligns with your agency or analytical goals
3. **Ingest data** — Use the Bronze notebook patterns with the data source URLs provided
4. **Build analytics** — Follow the Silver/Gold pipeline examples in each use case
5. **Visualize** — Use the Power BI recommendations or build custom reports via Direct Lake

---

## Related Documentation

- [Main Documentation Index](../index.md)
- [Medallion Architecture Deep Dive](../best-practices/medallion-architecture-deep-dive.md)
- [Data Governance](../best-practices/data-governance-deep-dive.md)
- [Testing Strategies](../best-practices/testing-strategies.md)
- [Migration Patterns](../best-practices/migration-patterns.md)

---

## Contributing New Use Cases

To add a new use case:

1. Create a new markdown file in `docs/use-cases/`
2. Follow the template structure: Executive Summary, Data Sources, Implementation, Visualizations, Cross-Domain, References
3. Ensure all data source URLs point to real, publicly available resources
4. Include PySpark code examples compatible with Fabric notebooks
5. Add the use case to the table above
6. Update the [References](references/README.md) with any new data sources

---

*Last Updated: 2026-04-23*
