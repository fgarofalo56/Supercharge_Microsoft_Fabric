# BI Developer Quickstart

> **Last Updated**: 2026-05-05 | **Role**: BI Developer
> **Goal**: Build performant Power BI reports backed by Direct Lake semantic models, DAX measures, and enterprise-grade delivery mechanisms.

---

## Persona & Typical Day

You design and maintain Power BI semantic models, reports, dashboards, and data visualizations. A typical day involves authoring DAX measures, optimizing model relationships for query performance, publishing reports to workspaces, troubleshooting slow visuals, and collaborating with data engineers on gold-layer table design to ensure the right granularity for your reports.

You care about user experience, query performance, data freshness, and visual clarity.

---

## Your First 30 Minutes

Follow these steps to get your first Direct Lake report running:

1. **Verify your environment** - Make sure your workspace has a Fabric capacity and that gold-layer Lakehouse tables are available.
   [:octicons-arrow-right-24: Tutorial 00: Environment Setup](../../tutorials/00-environment-setup/README.md)

2. **Connect Direct Lake to gold tables** - Create a semantic model that reads directly from Delta tables without import or DirectQuery overhead.
   [:octicons-arrow-right-24: Tutorial 05: Direct Lake & Power BI](../../tutorials/05-direct-lake-powerbi/README.md)

3. **Explore the Power BI best practices guide** - Understand naming conventions, measure organization, and relationship modeling for Fabric.
   [:octicons-arrow-right-24: Power BI Best Practices](../best-practices/power-bi-best-practices.md)

4. **Review star schema modeling patterns** - Gold tables should follow star schema conventions for optimal Direct Lake performance.
   [:octicons-arrow-right-24: Data Modeling & Star Schema](../best-practices/data-modeling-star-schema.md)

5. **Set up Scorecards for KPI tracking** - Create metrics-driven scorecards for executive reporting.
   [:octicons-arrow-right-24: Scorecards & Metrics](../features/scorecards-metrics.md)

---

## Your First Week

| Day | Focus | Resource |
|-----|-------|----------|
| 1 | Complete 30-minute path above | Tutorials 00, 05 + Power BI best practices |
| 2 | Build Composite Models for multi-source reports | [Composite Models](../features/composite-models.md) |
| 3 | Author Paginated Reports for operational/compliance needs | [Paginated Reports](../features/paginated-reports.md) |
| 4 | Set up deployment pipelines for dev/test/prod promotion | [Deployment Pipelines](../features/deployment-pipelines.md) |
| 5 | Configure Data Activator alerts on key metrics | [Data Activator](../features/data-activator.md) |

---

## Key Features for BI Developers

| Feature | Doc Link | Why It Matters |
|---------|----------|----------------|
| Direct Lake | [Direct Lake Guide](../features/direct-lake.md) | Import-speed performance with DirectQuery freshness - no data duplication |
| Power BI Best Practices | [Best Practices](../best-practices/power-bi-best-practices.md) | Naming, relationships, measures, and model optimization |
| Star Schema Modeling | [Modeling Guide](../best-practices/data-modeling-star-schema.md) | Correct dimensional modeling is the foundation of fast reports |
| Paginated Reports | [Paginated Reports](../features/paginated-reports.md) | Pixel-perfect reports for print, compliance, and operational delivery |
| Scorecards & Metrics | [Scorecards](../features/scorecards-metrics.md) | Executive KPI tracking with goals and status indicators |
| Composite Models | [Composite Models](../features/composite-models.md) | Combine Direct Lake with DirectQuery for cross-source reporting |
| TMDL & Developer Mode | [TMDL Guide](../features/tmdl-power-bi-developer-mode.md) | Version-control semantic models as text files for CI/CD |
| Deployment Pipelines | [Deployment Pipelines](../features/deployment-pipelines.md) | Promote content across dev, test, and production workspaces |
| Data Activator | [Data Activator](../features/data-activator.md) | Trigger alerts and actions when data conditions are met |

---

## Common Pitfalls

1. **Using Import mode when Direct Lake is available** - Direct Lake gives you import-speed queries without the memory overhead of importing data. Always prefer it for Lakehouse-backed models.

2. **Building one massive flat table instead of a star schema** - Wide denormalized tables degrade query performance and bloat model size. Use fact and dimension tables with proper relationships.

3. **Not optimizing DAX measures** - Complex DAX that iterates row-by-row (SUMX over large tables without filters) kills report performance. Use aggregation functions and pre-calculated gold columns where possible.

4. **Skipping deployment pipelines** - Manually publishing to production invites errors. Use Fabric deployment pipelines to promote content through dev/test/prod stages.

5. **Ignoring Paginated Reports for operational use cases** - Standard Power BI reports are not designed for pixel-perfect printing or parameterized batch delivery. Use Paginated Reports for invoices, compliance forms, and operational exports.

---

## Related Resources

<div class="grid cards" markdown>

-   :material-lightning-bolt:{ .lg .middle } __Direct Lake Deep Dive__

    ---

    Architecture, fallback behavior, framing, and performance tuning for Direct Lake semantic models.

    [:octicons-arrow-right-24: Direct Lake Guide](../features/direct-lake.md)

-   :material-star:{ .lg .middle } __Star Schema Modeling__

    ---

    Dimension and fact table design patterns optimized for Fabric analytics.

    [:octicons-arrow-right-24: Data Modeling Guide](../best-practices/data-modeling-star-schema.md)

-   :material-rocket-launch:{ .lg .middle } __Deployment Pipelines__

    ---

    Content lifecycle management across development, test, and production.

    [:octicons-arrow-right-24: Deployment Pipelines](../features/deployment-pipelines.md)

-   :material-format-page-break:{ .lg .middle } __Paginated Reports__

    ---

    Pixel-perfect, parameterized reports for compliance and operational delivery.

    [:octicons-arrow-right-24: Paginated Reports](../features/paginated-reports.md)

</div>
