# Data Engineer Quickstart

> **Last Updated**: 2026-05-05 | **Role**: Data Engineer
> **Goal**: Ingest, transform, and serve data through a production-ready medallion architecture in Microsoft Fabric.

---

## Persona & Typical Day

You build and maintain data pipelines that move data from source systems into a governed, queryable lakehouse. A typical day involves monitoring pipeline runs, debugging schema drift in bronze tables, optimizing Spark jobs, writing silver-layer transformations, and validating that gold-layer aggregations feed accurate numbers to downstream BI reports.

You care about data quality, pipeline reliability, idempotency, and keeping compute costs under control.

---

## Your First 30 Minutes

Follow these steps in order to get a working medallion pipeline running:

1. **Set up your environment** - Create a workspace, provision Lakehouses for bronze/silver/gold, and configure access.
   [:octicons-arrow-right-24: Tutorial 00: Environment Setup](../../tutorials/00-environment-setup/README.md)

2. **Ingest your first Bronze table** - Run a PySpark notebook that lands raw data into the bronze Lakehouse with append-only semantics.
   [:octicons-arrow-right-24: Tutorial 01: Bronze Layer](../../tutorials/01-bronze-layer/README.md)

3. **Transform to Silver** - Cleanse, deduplicate, and enforce schemas to produce curated silver tables.
   [:octicons-arrow-right-24: Tutorial 02: Silver Layer](../../tutorials/02-silver-layer/README.md)

4. **Build Gold aggregations** - Create star-schema KPI tables that power Direct Lake reports.
   [:octicons-arrow-right-24: Tutorial 03: Gold Layer](../../tutorials/03-gold-layer/README.md)

5. **Create a Data Factory pipeline** - Orchestrate the bronze-to-gold flow with scheduling and error handling.
   [:octicons-arrow-right-24: Tutorial 06: Data Pipelines](../../tutorials/06-data-pipelines/README.md)

---

## Your First Week

| Day | Focus | Resource |
|-----|-------|----------|
| 1 | Complete 30-minute path above | Tutorials 00-03, 06 |
| 2 | Add real-time streaming ingestion | [Tutorial 04: Real-Time Analytics](../../tutorials/04-real-time-analytics/README.md) |
| 3 | Set up Lakehouse schemas and shortcuts | [Lakehouse Setup Best Practices](../best-practices/07_LAKEHOUSE_SETUP.md) |
| 4 | Implement data quality checks | [Testing Strategies](../best-practices/testing-strategies.md) |
| 5 | Configure CI/CD for notebook deployment | [fabric-cicd Deployment](../best-practices/fabric-cicd-deployment.md) |

---

## Key Features for Data Engineers

| Feature | Doc Link | Why It Matters |
|---------|----------|----------------|
| Medallion Architecture | [Deep Dive](../best-practices/medallion-architecture-deep-dive.md) | The foundational pattern for all data transformation layers |
| Spark Notebooks | [Best Practices](../best-practices/05_SPARK_NOTEBOOKS.md) | Your primary development tool for PySpark transformations |
| Data Factory Pipelines | [Pipelines & Data Movement](../best-practices/03_PIPELINES_DATA_MOVEMENT.md) | Orchestration, scheduling, and dependency management |
| Lakehouse Setup | [Setup Guide](../best-practices/07_LAKEHOUSE_SETUP.md) | Delta Lake storage, schema enforcement, and table management |
| Mirroring | [Mirroring Guide](../features/mirroring.md) | Near-real-time replication from operational databases |
| Incremental Refresh & CDC | [CDC Patterns](../best-practices/incremental-refresh-cdc.md) | Efficient data loading without full reprocessing |
| Dataflow Gen2 | [Dataflow Gen2](../features/dataflow-gen2.md) | Low-code/no-code ETL for lighter transformations |
| Shortcut Transformations | [OneLake Shortcuts](../features/onelake-shortcuts-s3-gcs-dataverse.md) | Access external data without copying it into OneLake |
| Copy Job CDC | [Copy Job Guide](../features/copy-job-cdc.md) | Simplified change data capture for common sources |

---

## Common Pitfalls

1. **Skipping schema enforcement in Bronze** - Without explicit schemas, downstream Silver notebooks break silently when source columns change. Always define schemas even on raw ingestion.

2. **Over-partitioning Delta tables** - Partitioning by high-cardinality columns (e.g., user ID) creates millions of small files. Partition by date or a low-cardinality dimension instead.

3. **Ignoring V-Order** - Fabric's V-Order optimization dramatically improves Direct Lake read performance. Make sure gold tables are written with V-Order enabled. See the [V-Order Tuning Guide](../best-practices/v-order-tuning-deep-dive.md).

4. **Not using Lakehouse schemas** - Schemas (GA 2026) let you organize tables into namespaces inside a single Lakehouse. Use them instead of creating multiple Lakehouses for logical separation.

5. **Running full refreshes when incremental is possible** - Full table rewrites waste compute. Use merge/upsert patterns and watermark-based incremental loads.

---

## Related Resources

<div class="grid cards" markdown>

-   :material-layers-triple:{ .lg .middle } __Medallion Architecture__

    ---

    Deep dive into Bronze, Silver, and Gold layer patterns with partitioning, schema evolution, and optimization guidance.

    [:octicons-arrow-right-24: Medallion Deep Dive](../best-practices/medallion-architecture-deep-dive.md)

-   :material-pipe:{ .lg .middle } __Pipeline Orchestration__

    ---

    Metadata-driven pipelines, error handling, retry patterns, and scheduling strategies.

    [:octicons-arrow-right-24: Metadata-Driven Pipelines](../best-practices/04_METADATA_DRIVEN_PIPELINES.md)

-   :material-speedometer:{ .lg .middle } __Performance Tuning__

    ---

    Spark parallelism, query optimization, and V-Order tuning for production workloads.

    [:octicons-arrow-right-24: Performance & Parallelism](../best-practices/performance-parallelism.md)

-   :material-monitor-dashboard:{ .lg .middle } __Error Handling & Monitoring__

    ---

    Structured error handling, alerting, and pipeline monitoring patterns.

    [:octicons-arrow-right-24: Error Handling Guide](../best-practices/error-handling-monitoring.md)

</div>
