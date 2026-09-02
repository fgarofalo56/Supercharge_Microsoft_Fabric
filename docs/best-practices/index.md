---
title: Best Practices
description: Enterprise best practices for Microsoft Fabric implementations
hero: assets/heroes/best-practices.svg
hero_alt: "Best Practices — Architecture, security, performance, and operational guidance for Fabric"
---
# Best Practices

Proven patterns, architectural guidance, and operational best practices for production Microsoft Fabric deployments.

!!! info "Third-party references — publicly sourced, good-faith comparison"
    This page references non-Microsoft products and services. That information is drawn from each vendor's **publicly available documentation** and is offered for honest, good-faith comparison only. This is a personal project written from a Microsoft Fabric and Azure perspective; it does **not** claim expertise in, or authority over, any third-party product, and nothing here is an official statement by, or endorsed by, those vendors. Capabilities, pricing, and features change often — always verify against the vendor's current official documentation. Where a third-party offering is the stronger choice, we say so plainly.

## Workspace & Infrastructure

<div class="grid cards" markdown>

-   :material-folder-cog:{ .lg .middle } __Workspaces & Naming__

    ---

    Naming conventions, workspace organization, and environment structure.

    [:octicons-arrow-right-24: Workspace guide](01-workspaces-naming.md)

-   :material-lan-connect:{ .lg .middle } __Data Gateway__

    ---

    On-premises data gateway setup, configuration, and management.

    [:octicons-arrow-right-24: Gateway guide](02-data-gateway.md)

-   :material-home-analytics:{ .lg .middle } __Lakehouse Setup__

    ---

    Lakehouse architecture, schema design, and optimization patterns.

    [:octicons-arrow-right-24: Lakehouse setup](07-lakehouse-setup.md)

-   :material-warehouse:{ .lg .middle } __Warehouse Setup__

    ---

    Data Warehouse configuration, loading patterns, and query tuning.

    [:octicons-arrow-right-24: Warehouse setup](08-warehouse-setup.md)

</div>

## Data Movement & Processing

<div class="grid cards" markdown>

-   :material-pipe:{ .lg .middle } __Pipelines & Data Movement__

    ---

    Pipeline design, Copy Activity optimization, and data movement patterns.

    [:octicons-arrow-right-24: Pipeline guide](03-pipelines-data-movement.md)

-   :material-cog-transfer:{ .lg .middle } __Metadata-Driven Pipelines__

    ---

    Dynamic, configuration-driven pipelines for scalable data ingestion.

    [:octicons-arrow-right-24: Metadata pipelines](04-metadata-driven-pipelines.md)

-   :material-notebook:{ .lg .middle } __Spark & Notebooks__

    ---

    PySpark optimization, notebook best practices, and Spark configuration.

    [:octicons-arrow-right-24: Spark guide](05-spark-notebooks.md)

-   :material-pipe-wrench:{ .lg .middle } __Dataflows Gen2__

    ---

    Power Query dataflow patterns for low-code transformations.

    [:octicons-arrow-right-24: Dataflow guide](06-dataflows.md)

-   :material-refresh-auto:{ .lg .middle } __Incremental Refresh & CDC__

    ---

    Change data capture and incremental refresh patterns for efficiency.

    [:octicons-arrow-right-24: CDC patterns](incremental-refresh-cdc.md)

-   :material-compare:{ .lg .middle } __ETL/ELT Comparison__

    ---

    When to use ETL vs ELT approaches in Fabric workloads.

    [:octicons-arrow-right-24: ETL vs ELT](etl-elt-comparison-guide.md)

</div>

## Source Systems & Migration

<div class="grid cards" markdown>

-   :material-database-cog:{ .lg .middle } __Oracle & SQL Server Patterns__

    ---

    Source-specific ingestion patterns for Oracle and SQL Server.

    [:octicons-arrow-right-24: Source patterns](09-source-specific-patterns.md)

-   :material-wrench:{ .lg .middle } __Oracle Gateway Troubleshooting__

    ---

    Common Oracle gateway issues, diagnostics, and resolution steps.

    [:octicons-arrow-right-24: Troubleshooting](11-oracle-gateway-troubleshooting.md)

-   :material-database-export:{ .lg .middle } __Migration Patterns__

    ---

    Strategies for migrating from legacy platforms to Microsoft Fabric.

    [:octicons-arrow-right-24: Migration guide](migration-patterns.md)

-   :material-swap-horizontal:{ .lg .middle } __Spark Runtime Migration__

    ---

    Upgrade path and breaking changes for Spark Runtime 2.0.

    [:octicons-arrow-right-24: Runtime migration](spark-runtime-migration.md)

</div>

## Architecture & Design

<div class="grid cards" markdown>

-   :material-help-circle:{ .lg .middle } __Decision Guide__

    ---

    Choosing between Fabric compute engines, storage layers, and patterns.

    [:octicons-arrow-right-24: Decision guide](10-decision-guide.md)

-   :material-layers-triple:{ .lg .middle } __Medallion Architecture Deep Dive__

    ---

    Bronze, Silver, Gold layer patterns with implementation details.

    [:octicons-arrow-right-24: Medallion deep dive](medallion-architecture-deep-dive.md)

-   :material-scale-balance:{ .lg .middle } __Lakehouse vs Warehouse vs SQL DB__

    ---

    When to choose Lakehouse, Warehouse, or SQL Database in Fabric.

    [:octicons-arrow-right-24: Comparison guide](lakehouse-warehouse-sqldb-decision-guide.md)

-   :material-star-four-points:{ .lg .middle } __Data Modeling & Star Schema__

    ---

    Dimensional modeling, star schema design, and semantic layer patterns.

    [:octicons-arrow-right-24: Data modeling](data-modeling-star-schema.md)

-   :material-domain:{ .lg .middle } __Multi-Tenant Architecture__

    ---

    Workspace isolation, tenant management, and multi-org patterns.

    [:octicons-arrow-right-24: Multi-tenant guide](multi-tenant-workspace-architecture.md)

</div>

## Security & Governance

<div class="grid cards" markdown>

-   :material-shield-check:{ .lg .middle } __Data Governance Deep Dive__

    ---

    Purview integration, lineage, classification, and governance policies.

    [:octicons-arrow-right-24: Governance guide](data-governance-deep-dive.md)

-   :material-account-key:{ .lg .middle } __Identity & RBAC Patterns__

    ---

    Role-based access control, workspace roles, and identity management.

    [:octicons-arrow-right-24: RBAC patterns](identity-rbac-patterns.md)

-   :material-security-network:{ .lg .middle } __Network Security__

    ---

    Private endpoints, managed VNets, and network isolation patterns.

    [:octicons-arrow-right-24: Network security](network-security.md)

-   :material-key-variant:{ .lg .middle } __Customer-Managed Keys__

    ---

    CMK encryption for data-at-rest with Azure Key Vault integration.

    [:octicons-arrow-right-24: CMK guide](customer-managed-keys.md)

-   :material-shield-outline:{ .lg .middle } __Outbound Access Protection__

    ---

    Control and monitor outbound network traffic from Fabric workspaces.

    [:octicons-arrow-right-24: OAP guide](outbound-access-protection.md)

-   :material-clipboard-text:{ .lg .middle } __SQL Audit Logs Compliance__

    ---

    SQL audit logging for regulatory compliance and forensic analysis.

    [:octicons-arrow-right-24: Audit logs](sql-audit-logs-compliance.md)

</div>

## Operations & Monitoring

<div class="grid cards" markdown>

-   :material-alert-circle:{ .lg .middle } __Error Handling & Monitoring__

    ---

    Error handling patterns, retry logic, and monitoring setup.

    [:octicons-arrow-right-24: Error handling](error-handling-monitoring.md)

-   :material-bell-alert:{ .lg .middle } __Alerting & Data Activator__

    ---

    Proactive alerting with Data Activator and Azure Monitor integration.

    [:octicons-arrow-right-24: Alerting guide](alerting-data-activator.md)

-   :material-speedometer:{ .lg .middle } __Performance & Parallelism__

    ---

    Query optimization, parallel processing, and performance tuning.

    [:octicons-arrow-right-24: Performance guide](performance-parallelism.md)

-   :material-chart-timeline-variant:{ .lg .middle } __Monitoring & Observability__

    ---

    End-to-end observability with metrics, logs, and dashboards.

    [:octicons-arrow-right-24: Observability](monitoring-observability.md)

-   :material-infinity:{ .lg .middle } __CI/CD with fabric-cicd__

    ---

    Continuous integration and deployment for Fabric items.

    [:octicons-arrow-right-24: CI/CD guide](fabric-cicd-deployment.md)

-   :material-test-tube:{ .lg .middle } __Testing Strategies__

    ---

    Unit, integration, and end-to-end testing for Fabric workloads.

    [:octicons-arrow-right-24: Testing guide](testing-strategies.md)

</div>

## Cost & Capacity

<div class="grid cards" markdown>

-   :material-currency-usd:{ .lg .middle } __Capacity Planning & Cost__

    ---

    SKU sizing, CU consumption analysis, and capacity optimization.

    [:octicons-arrow-right-24: Capacity planning](capacity-planning-cost-optimization.md)

-   :material-finance:{ .lg .middle } __FinOps & Cost Governance__

    ---

    Financial operations framework for Fabric cost management.

    [:octicons-arrow-right-24: FinOps guide](finops-cost-governance.md)

-   :material-restore:{ .lg .middle } __Disaster Recovery & BCDR__

    ---

    Business continuity, disaster recovery, and geo-redundancy patterns.

    [:octicons-arrow-right-24: BCDR guide](disaster-recovery-bcdr.md)

</div>

## Analytics & BI

<div class="grid cards" markdown>

-   :material-chart-bar:{ .lg .middle } __Power BI Best Practices__

    ---

    Report design, DAX optimization, and semantic model patterns.

    [:octicons-arrow-right-24: Power BI guide](power-bi-best-practices.md)

-   :material-share-variant:{ .lg .middle } __Data Sharing & Federation__

    ---

    Cross-workspace sharing, external data sharing, and federation patterns.

    [:octicons-arrow-right-24: Sharing guide](data-sharing-federation.md)

</div>
