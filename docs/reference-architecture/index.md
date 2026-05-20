[Home](../index.md) > [Docs](../) > Reference Architectures

# 🏗️ Reference Architectures for Microsoft Fabric

<div align="center" markdown>

**Production-Grade Deployment Patterns for Every Scale and Workload**

![Category](https://img.shields.io/badge/Category-Architecture-purple?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-May_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-05-05` | **Version:** 1.0.0

---

## 🎯 Overview

These reference architectures provide proven, production-grade deployment patterns for Microsoft Fabric. Each architecture addresses a different organizational scale, workload profile, or integration scenario — from a single-capacity setup for small teams to multi-domain data mesh deployments for large enterprises.

Use these architectures as starting points. Every organization has unique requirements; adapt the patterns to fit your data volumes, compliance needs, team structure, and budget.

---

## 📐 Choose Your Architecture

<div class="grid" markdown>

<div class="card" markdown>

### 🏢 Small-Medium Enterprise

Single capacity, 2–3 workspaces, medallion lakehouse, Direct Lake Power BI. Ideal for **5–20 data practitioners** getting started with Fabric.

[View Architecture](small-medium-enterprise.md){ .md-button .md-button--primary }

</div>

<div class="card" markdown>

### 🏛️ Large Enterprise Multi-Domain

Multiple capacities, domain workspaces (Data Mesh), Purview governance hub, CI/CD via fabric-cicd, network isolation. For organizations with **50+ data practitioners**.

[View Architecture](large-enterprise-multi-domain.md){ .md-button .md-button--primary }

</div>

<div class="card" markdown>

### ☁️ Hybrid Cloud

Fabric for analytics and BI combined with Azure services for OLTP, custom apps, and high-volume streaming. Integration via Mirroring, Shortcuts, and Dataflow Gen2.

[View Architecture](hybrid-cloud.md){ .md-button .md-button--primary }

</div>

<div class="card" markdown>

### ⚡ Real-Time Analytics

Eventstream → Eventhouse (KQL) → Real-Time Dashboard + Data Activator alerts. Purpose-built for **IoT, gaming, financial tick data, and operational monitoring**.

[View Architecture](real-time-analytics.md){ .md-button .md-button--primary }

</div>

</div>

---

## 🗺️ Architecture Decision Guide

| Factor | Small-Medium | Large Enterprise | Hybrid Cloud | Real-Time |
|:-------|:-------------|:-----------------|:-------------|:----------|
| **Team Size** | 5–20 | 50+ | Any | Any |
| **Data Volume** | < 5 TB | 5–500+ TB | Varies | High-velocity streams |
| **Capacities** | 1 | 2–10+ | 1–3 | 1–2 |
| **Workspaces** | 2–3 | 10–50+ | 3–6 | 2–4 |
| **Governance** | Workspace-level | Purview + Data Mesh domains | Cross-platform | RTI-focused |
| **CI/CD** | Manual / Git integration | fabric-cicd pipelines | Azure DevOps / GitHub Actions | Git + Eventstream config |
| **Network** | Public endpoint + Entra ID | Private endpoints + VNet | VNet + Private Link across services | Public or private |
| **Primary Workload** | Batch analytics + BI | Multi-domain analytics | Mixed OLTP + analytics | Streaming + alerting |

---

## 🔗 Related Resources

| Resource | Description |
|:---------|:------------|
| [Capacity Planning & Cost Optimization](../best-practices/capacity-planning-cost-optimization.md) | SKU selection, CU model, cost governance |
| [Network Security](../best-practices/network-security.md) | Private endpoints, VNet gateways, firewall rules |
| [Identity & RBAC Patterns](../best-practices/identity-rbac-patterns.md) | Workspace roles, item permissions, row-level security |
| [Medallion Architecture Deep Dive](../best-practices/medallion-architecture-deep-dive.md) | Bronze/Silver/Gold design patterns |
| [Disaster Recovery & BCDR](../best-practices/disaster-recovery-bcdr.md) | HA, geo-redundancy, RPO/RTO planning |
| [Multi-Tenant Workspace Architecture](../best-practices/multi-tenant-workspace-architecture.md) | Isolation patterns for multi-tenant deployments |
| [fabric-cicd Deployment](../best-practices/fabric-cicd-deployment.md) | CI/CD pipeline patterns for Fabric items |
| [Infrastructure as Code](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric/blob/main/infra/main.bicep) | Bicep modules for automated deployment |
