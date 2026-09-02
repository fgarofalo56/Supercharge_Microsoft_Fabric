---
hero: assets/heroes/getting-started.svg
hero_alt: Quickstart — Platform Admin Quickstart
type: quick-start
---
# Platform Admin Quickstart

> **Last Updated**: 2026-05-05 | **Role**: Platform Admin
> **Goal**: Provision, govern, monitor, and optimize Microsoft Fabric capacity and workspaces for your organization.

---

## Persona & Typical Day

You manage the Fabric tenant, capacity, and workspace infrastructure that everyone else depends on. A typical day involves monitoring capacity utilization, reviewing workspace access requests, troubleshooting throttled workloads, planning capacity scaling for upcoming projects, and ensuring that disaster recovery procedures are tested and current.

You care about uptime, cost efficiency, access governance, performance consistency, and having clear operational runbooks.

---

## Your First 30 Minutes

Follow these steps to establish baseline platform operations:

1. **Provision your environment** - Deploy Fabric capacity with Bicep, create workspaces, and configure initial access policies.
   [:octicons-arrow-right-24: Tutorial 00: Environment Setup](../tutorials/00-environment-setup/README.md)

2. **Configure workspace structure and naming** - Set up a workspace hierarchy that scales with your organization's teams and environments.
   [:octicons-arrow-right-24: Workspaces & Naming Best Practices](../best-practices/01-workspaces-naming.md)

3. **Establish RBAC policies** - Define who can do what across workspaces using Fabric's identity and role-based access model.
   [:octicons-arrow-right-24: Identity & RBAC Patterns](../best-practices/identity-rbac-patterns.md)

4. **Set up monitoring and alerting** - Enable workspace monitoring to track capacity usage, job durations, and failure rates.
   [:octicons-arrow-right-24: Workspace Monitoring](../features/workspace-monitoring.md)

5. **Review cost management controls** - Configure alerts and budgets to prevent cost overruns.
   [:octicons-arrow-right-24: Capacity Planning & Cost Optimization](../best-practices/capacity-planning-cost-optimization.md)

---

## Your First Week

| Day | Focus | Resource |
|-----|-------|----------|
| 1 | Complete 30-minute path above | Tutorials 00 + best practices |
| 2 | Configure network security and private endpoints | [Network Security](../best-practices/network-security.md) |
| 3 | Set up disaster recovery and BCDR procedures | [BCDR Guide](../best-practices/disaster-recovery-bcdr.md) |
| 4 | Design multi-tenant workspace architecture | [Multi-Tenant Architecture](../best-practices/multi-tenant-workspace-architecture.md) |
| 5 | Implement CI/CD for infrastructure and Fabric items | [fabric-cicd Deployment](../best-practices/fabric-cicd-deployment.md) |

---

## Key Features for Platform Admins

| Feature | Doc Link | Why It Matters |
|---------|----------|----------------|
| Capacity Planning | [Cost Optimization](../best-practices/capacity-planning-cost-optimization.md) | Right-size capacity to balance performance and cost |
| RBAC & Identity | [RBAC Patterns](../best-practices/identity-rbac-patterns.md) | Control access at tenant, workspace, and item levels |
| Network Security | [Network Security](../best-practices/network-security.md) | Private endpoints, VNet gateways, and firewall rules |
| Workspace Monitoring | [Monitoring](../features/workspace-monitoring.md) | Track utilization, throttling, and job performance |
| Observability | [Observability Guide](../best-practices/monitoring-observability.md) | End-to-end monitoring across pipelines, notebooks, and queries |
| BCDR | [Disaster Recovery](../best-practices/disaster-recovery-bcdr.md) | Business continuity planning, geo-redundancy, and recovery procedures |
| Multi-Tenant Architecture | [Multi-Tenant](../best-practices/multi-tenant-workspace-architecture.md) | Workspace isolation strategies for multi-team or multi-customer scenarios |
| Deployment Pipelines | [Deployment Pipelines](../features/deployment-pipelines.md) | Promote Fabric items through dev/test/prod lifecycle stages |
| Fabric Admin Monitoring | [Admin Monitoring](../features/fabric-unified-admin-monitoring.md) | Centralized tenant-wide administration and usage monitoring |
| Data Sharing & Federation | [Data Sharing](../best-practices/data-sharing-federation.md) | Cross-workspace and cross-tenant data sharing patterns |

---

## Common Pitfalls

1. **Under-provisioning capacity for burst workloads** - A single F64 capacity shared by many workloads can throttle during peak hours. Use capacity metrics to identify utilization patterns and consider smoothing or scaling strategies.

2. **Flat workspace structure** - Putting everything in one workspace makes RBAC unmanageable. Design a workspace-per-domain or workspace-per-environment hierarchy from the start. See [Workspaces & Naming](../best-practices/01-workspaces-naming.md).

3. **No disaster recovery plan** - Without a tested BCDR plan, a regional outage means extended downtime. Document and test recovery procedures quarterly.

4. **Granting Admin when Contributor would suffice** - Overly broad role assignments increase your blast radius. Follow least-privilege principles and review access quarterly.

5. **Ignoring cost alerts until the bill arrives** - Set budget alerts at 50%, 75%, and 90% thresholds. Use the [FinOps Cost Governance](../best-practices/finops-cost-governance.md) guide to build proactive cost management habits.

---

## Related Resources

<div class="grid cards" markdown>

-   :material-cash:{ .lg .middle } __Capacity & Cost Management__

    ---

    SKU sizing, autoscale patterns, budget alerts, and cost optimization strategies.

    [:octicons-arrow-right-24: Capacity Planning](../best-practices/capacity-planning-cost-optimization.md)

-   :material-shield-account:{ .lg .middle } __Identity & RBAC__

    ---

    Role assignments, workspace permissions, item-level security, and least-privilege patterns.

    [:octicons-arrow-right-24: RBAC Patterns](../best-practices/identity-rbac-patterns.md)

-   :material-hospital-building:{ .lg .middle } __Disaster Recovery__

    ---

    BCDR planning, geo-redundancy, recovery objectives, and tested runbooks.

    [:octicons-arrow-right-24: BCDR Guide](../best-practices/disaster-recovery-bcdr.md)

-   :material-monitor-eye:{ .lg .middle } __Monitoring & Observability__

    ---

    End-to-end platform monitoring covering capacity, pipelines, notebooks, and queries.

    [:octicons-arrow-right-24: Observability Guide](../best-practices/monitoring-observability.md)

</div>
