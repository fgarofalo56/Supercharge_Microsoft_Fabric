---
hero: assets/heroes/decisions.svg
hero_alt: Decisions — Architecture trade-offs and ADRs
---

# Decision Trees: Interactive Architecture Guides

<div align="center" markdown>

**Navigate Microsoft Fabric's key architectural decisions with step-by-step flowcharts**

![Category](https://img.shields.io/badge/Category-Architecture-purple?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-May_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-05-05` | **Version:** 1.0.0

!!! info "Third-party references — publicly sourced, good-faith comparison"
    This page references non-Microsoft products and services. That information is drawn from each vendor's **publicly available documentation** and is offered for honest, good-faith comparison only. This is a personal project written from a Microsoft Fabric and Azure perspective; it does **not** claim expertise in, or authority over, any third-party product, and nothing here is an official statement by, or endorsed by, those vendors. Capabilities, pricing, and features change often — always verify against the vendor's current official documentation. Where a third-party offering is the stronger choice, we say so plainly.

---

## When to Use These Guides

These interactive decision trees help you navigate the most common "which should I choose?" questions in Microsoft Fabric projects. Each guide includes a visual flowchart, tradeoff analysis, and anti-pattern warnings drawn from real-world POC experience.

---

## Decision Tree Catalog

<div class="grid cards" markdown>

-   **[Lakehouse vs Warehouse vs SQL Database](lakehouse-warehouse-sqldb.md)**

    ---

    Choose the right Fabric storage engine based on workload type, query patterns, and team skills. Covers OLTP, OLAP, and data engineering scenarios.

    [:octicons-arrow-right-24: Navigate decision tree](lakehouse-warehouse-sqldb.md)

-   **[ETL vs ELT vs Streaming](etl-elt-streaming.md)**

    ---

    Select the optimal data movement strategy based on latency requirements, data volume, transformation complexity, and source characteristics.

    [:octicons-arrow-right-24: Navigate decision tree](etl-elt-streaming.md)

-   **[Direct Lake vs Import vs DirectQuery](direct-lake-import-directquery.md)**

    ---

    Pick the right Power BI connectivity mode by balancing freshness, performance, dataset size, and governance requirements.

    [:octicons-arrow-right-24: Navigate decision tree](direct-lake-import-directquery.md)

-   **[Fabric vs. competing analytics platforms](fabric-databricks-synapse.md)**

    ---

    Platform selection from a Fabric-first perspective. Understand when Fabric is the right fit and when complementary platforms add value.

    [:octicons-arrow-right-24: Navigate decision tree](fabric-databricks-synapse.md)

-   **[Workspace Topology](workspace-topology.md)**

    ---

    Decide between single workspace, multi-workspace, and multi-capacity architectures based on team size, compliance, and isolation needs.

    [:octicons-arrow-right-24: Navigate decision tree](workspace-topology.md)

</div>

---

## How to Read These Guides

Each decision tree follows a consistent structure:

| Section | Purpose |
|---------|---------|
| **TL;DR** | 3-sentence summary of the decision space |
| **When This Question Comes Up** | Scenarios that trigger this decision |
| **Decision Flowchart** | Interactive Mermaid diagram with branching logic |
| **Recommendation Sections** | Deep dive per option: When, Why, Tradeoffs, Anti-patterns |
| **Related Links** | Cross-references to feature docs and best practices |

---

## Related Resources

| Resource | Description |
|----------|-------------|
| [Component Decision Trees](../decision-trees.md) | Detailed component-level decision flowcharts |
| [Architecture Overview](../architecture.md) | End-to-end system architecture |
| [Best Practices Index](../best-practices/index.md) | Enterprise best practice guides |
| [Capacity Planning](../best-practices/capacity-planning-cost-optimization.md) | Cost and capacity optimization |
| [Medallion Architecture](../best-practices/medallion-architecture-deep-dive.md) | Medallion pattern deep dive |
