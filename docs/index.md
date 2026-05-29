---
title: Home
description: A personal, hands-on Microsoft Fabric reference for regulated industries — from casino & gaming through Tribal Nations to federal agency analytics. Not an official Microsoft product.
hide:
  - navigation
  - toc
hero: assets/heroes/home.svg
hero_alt: "Supercharge Microsoft Fabric — Casino & gaming POC + federal expansions on F64 capacity"
---
# Supercharge Microsoft Fabric

**A hands-on Microsoft Fabric reference for data teams in regulated industries — it starts in casino & gaming, bridges through Tribal Nations gaming and health, and extends out to federal agency analytics.** Same medallion + governance backbone, applied across each domain.

*Real-time insights · Medallion Architecture · Regulatory Compliance · Direct Lake BI*

!!! info "Personal project — not an official Microsoft product"
    This is a personal, community-built reference maintained by [Frank Garofalo](https://github.com/fgarofalo56). It is **not** a sanctioned Microsoft deliverable, nor official Microsoft Fabric product documentation, and opinions here are the author's own. The compliance pages (FedRAMP, HIPAA, NIST 800-53, NIGC MICS, Title 31/BSA, etc.) are **reference control mappings for education and POC scoping — not authorizations, attestations, or certifications.**

[Quick Start](PREREQUISITES.md){ .md-button .md-button--primary }
[Tutorials](tutorials/index.md){ .md-button }

---

## Three Core Paradigms

This POC is built on three paradigms that define how data flows from source to insight inside Microsoft Fabric.

**OneLake** is the unified storage layer. It's Delta Lake–native — Fabric engines read and write Delta tables to a single lake with no data movement — and interoperates with Apache Iceberg via metadata virtualization (shortcuts and the Iceberg/Delta translation layer), so Iceberg readers and writers can work against the same data.

**Medallion Architecture** (Bronze → Silver → Gold) organizes that data by quality tier. Bronze captures raw ingestion, Silver cleanses and validates, Gold produces business-ready KPIs and star schemas.

**Direct Lake** connects Power BI semantic models straight to Gold-layer Delta tables in OneLake — low-latency analytics with no import step and no scheduled refresh. (On large or over-limit models it can fall back to DirectQuery, and cold caches warm on first access.)

Together they give you a single pipeline from raw events to executive dashboards, with governance enforced by Microsoft Purview at every layer.

---

## How this relates to CSA-in-a-Box

<!-- TODO(frank): PLACEHOLDER — confirm and finalize before publishing.
     1. Replace the (#) links with the real CSA-in-a-Box URL.
     2. Disambiguate the three brand names so a newcomer isn't lost:
          - CSA-in-a-Box → ?
          - CSA Loom      → ?   (the /fiab/ slug — "Fabric-in-a-Box"?)
          - "fiab"        → ?
     3. Mirror this same blurb on the CSA-in-a-Box home page so both repos
        cross-link and tell the same "which repo, when" story. -->

This project is a **Microsoft Fabric reference**: use it once you've committed to Fabric and want hands-on patterns, tutorials, and governance mappings on F64 capacity.

Its sibling, **[CSA-in-a-Box](#)** *(TODO: link)*, takes the **platform-agnostic / build-your-own** angle and includes "vs Microsoft Fabric" comparisons — use it when you're still deciding whether to adopt Fabric, or want a non-Fabric option.

!!! tip "Which one do I use?"
    **Already on Fabric** → you're in the right place (this repo). **Still choosing a platform, or want a non-Fabric alternative** → start with CSA-in-a-Box. *(Placeholder positioning — Frank to confirm the CSA-in-a-Box vs CSA Loom vs "fiab" naming and finalize the links.)*

---

## Start Here

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } __Quick Start__

    ---

    Prerequisites, Azure setup, one-click Bicep deployment

    [:octicons-arrow-right-24: Get started](PREREQUISITES.md)

-   :material-school:{ .lg .middle } __Tutorials__

    ---

    50+ self-paced, hands-on tutorials from Bronze ingestion to AI/ML

    [:octicons-arrow-right-24: Browse tutorials](tutorials/index.md)

-   :material-domain:{ .lg .middle } __Architecture__

    ---

    System design, component overview, data flow diagrams

    [:octicons-arrow-right-24: View architecture](ARCHITECTURE.md)

-   :material-calendar-check:{ .lg .middle } __3-Day POC Agenda__

    ---

    A curated subset of the tutorials, packaged as a guided workshop: Foundation → Transformation → BI & Governance

    [:octicons-arrow-right-24: View agenda](poc-agenda/README.md)

</div>

---

## Choose Your Path

<div class="grid cards" markdown>

-   :material-database-cog:{ .lg .middle } __Data Engineers__

    ---

    PySpark notebooks, pipelines, ETL, medallion implementation

    [:octicons-arrow-right-24: Bronze layer tutorial](tutorials/01-bronze-layer/README.md)

-   :material-chart-areaspline:{ .lg .middle } __BI Developers__

    ---

    Direct Lake, Power BI semantic models, DAX measures

    [:octicons-arrow-right-24: Direct Lake tutorial](tutorials/05-direct-lake-powerbi/README.md)

-   :material-shield-lock:{ .lg .middle } __Security & Compliance__

    ---

    Microsoft Purview governance, gaming internal controls (NIGC MICS), and anti-money-laundering reporting (CTR/SAR)

    [:octicons-arrow-right-24: Governance tutorial](tutorials/07-governance-purview/README.md)

-   :material-lightning-bolt:{ .lg .middle } __Real-Time Analytics__

    ---

    Eventstreams, Eventhouse, KQL for streaming workloads

    [:octicons-arrow-right-24: Real-time tutorial](tutorials/04-real-time-analytics/README.md)

</div>

---

## Feature Documentation

<div class="grid cards" markdown>

-   :material-brain:{ .lg .middle } __Fabric IQ__

    ---

    Natural language data exploration with Ontology & Plan layers

    [:octicons-arrow-right-24: Fabric IQ](features/fabric-iq.md)

-   :material-lightning-bolt:{ .lg .middle } __Real-Time Intelligence__

    ---

    Eventstreams, Eventhouse, KQL, Business Events, Maps

    [:octicons-arrow-right-24: RTI](features/real-time-intelligence.md)

-   :material-robot:{ .lg .middle } __AI Copilot__

    ---

    Copilot Studio integration and governance configuration

    [:octicons-arrow-right-24: Copilot](features/ai-copilot-configuration.md)

-   :material-lan:{ .lg .middle } __Data Mesh__

    ---

    Enterprise data mesh patterns with Fabric domains

    [:octicons-arrow-right-24: Data Mesh](features/data-mesh-enterprise-patterns.md)

</div>

[:octicons-arrow-right-24: View all features](features/fabric-iq.md){ .md-button }

---

## Compliance & Governance

This POC addresses casino/gaming regulations (NIGC MICS, Title 31/BSA, IRS Gaming) and supports **8 federal agency domains** — USDA, SBA, NOAA, EPA, DOI, DOT/FAA, Tribal Healthcare, and DOJ.

!!! warning "These are reference mappings, not authorizations"
    The compliance and governance pages illustrate how Fabric controls *can* map to each framework, for education and POC scoping. They are **not** ATOs, attestations, audits, or certifications, and they don't represent the compliance posture of any production system.

| Framework | Coverage |
|:----------|:---------|
| **NIGC MICS** | Minimum Internal Control Standards |
| **Title 31/BSA** | Anti-money laundering, CTR/SAR |
| **IRS Gaming** | W-2G, 1042-S reporting |
| **State Gaming Commissions** | Jurisdiction-specific requirements |

[:octicons-arrow-right-24: Security documentation](SECURITY.md){ .md-button }

---

## Quick Links

<div class="grid cards" markdown>

-   :fontawesome-brands-github:{ .lg .middle } __GitHub Repository__

    ---

    Source code, issues, and releases

    [:octicons-arrow-right-24: Open on GitHub](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric)

-   :material-file-document-multiple:{ .lg .middle } __Documentation__

    ---

    Full documentation index and guides

    [:octicons-arrow-right-24: Browse docs](index.md)

-   :material-cog:{ .lg .middle } __Infrastructure__

    ---

    Bicep IaC modules for Azure deployment

    [:octicons-arrow-right-24: View infra](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/tree/main/infra)

-   :material-currency-usd:{ .lg .middle } __Cost Estimation__

    ---

    F64 24/7 ≈ $9,500–$12,500/mo (commercial list, as of Jan 2025). Azure Government pricing differs — see the guide.

    [:octicons-arrow-right-24: Cost details](COST_ESTIMATION.md)

</div>

---

<div align="center" markdown>

**License:** MIT · **Maintained by:** [Frank Garofalo](https://github.com/fgarofalo56) · A personal/community project — not affiliated with, sponsored by, or endorsed by Microsoft.

[:material-github: View on GitHub](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric){ .md-button }

</div>
