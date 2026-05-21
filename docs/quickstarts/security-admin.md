---
hero: assets/heroes/getting-started.svg
hero_alt: Quickstart — Security Admin Quickstart
type: quick-start
---
# Security Admin Quickstart

> **Last Updated**: 2026-05-05 | **Role**: Security Admin
> **Goal**: Secure your Fabric environment with defense-in-depth controls, governance policies, encryption, audit logging, and regulatory compliance frameworks.

---

## Persona & Typical Day

You define and enforce the security posture of your organization's Fabric deployment. A typical day involves reviewing audit logs for anomalous access patterns, managing data classification labels, configuring customer-managed encryption keys, responding to compliance questionnaires, ensuring PII handling meets regulatory requirements, and coordinating with platform admins on network security controls.

You care about data protection, regulatory compliance, least-privilege access, auditability, and being able to prove controls work during audits.

---

## Your First 30 Minutes

Follow these steps to establish baseline security controls:

1. **Understand the security architecture** - Review how OneLake Security, workspace roles, and item permissions layer together.
   [:octicons-arrow-right-24: OneLake Security](../features/onelake-security.md)

2. **Configure data governance with Purview** - Set up data classification, sensitivity labels, and lineage tracking.
   [:octicons-arrow-right-24: Tutorial 07: Governance & Purview](../tutorials/07-governance-purview/README.md)

3. **Enable SQL audit logging** - Configure audit logs to capture all data access and administrative actions for compliance.
   [:octicons-arrow-right-24: SQL Audit Logs Compliance](../best-practices/sql-audit-logs-compliance.md)

4. **Review RBAC patterns** - Ensure workspace and item-level permissions follow least-privilege principles.
   [:octicons-arrow-right-24: Identity & RBAC Patterns](../best-practices/identity-rbac-patterns.md)

5. **Set up customer-managed keys** - Configure CMK for encryption at rest to meet data sovereignty requirements.
   [:octicons-arrow-right-24: Customer-Managed Keys](../best-practices/customer-managed-keys.md)

---

## Your First Week

| Day | Focus | Resource |
|-----|-------|----------|
| 1 | Complete 30-minute path above | OneLake Security, Purview, RBAC |
| 2 | Configure network security and outbound access protection | [Network Security](../best-practices/network-security.md) |
| 3 | Implement data governance deep dive with lineage | [Data Governance Deep Dive](../best-practices/data-governance-deep-dive.md) |
| 4 | Map controls to compliance frameworks (SOC2, ISO 27001) | [SOC2 Readiness](../best-practices/security/soc2-type2-readiness.md) |
| 5 | Build threat model and review zero-trust architecture | [Zero Trust Blueprint](../best-practices/security/zero-trust-blueprint.md) |

---

## Key Features for Security Admins

| Feature | Doc Link | Why It Matters |
|---------|----------|----------------|
| OneLake Security | [OneLake Security](../features/onelake-security.md) | Fine-grained access control at the data layer across all Fabric workloads |
| Data Governance | [Governance Deep Dive](../best-practices/data-governance-deep-dive.md) | Classification, sensitivity labels, lineage, and data cataloging with Purview |
| Customer-Managed Keys | [CMK Guide](../best-practices/customer-managed-keys.md) | Control encryption keys for data at rest using Azure Key Vault |
| SQL Audit Logs | [Audit Logs](../best-practices/sql-audit-logs-compliance.md) | Immutable audit trail for all data access and admin operations |
| Network Security | [Network Security](../best-practices/network-security.md) | Private endpoints, managed VNets, and workspace IP firewalls |
| Outbound Access Protection | [OAP Guide](../best-practices/outbound-access-protection.md) | Control what external endpoints Fabric workloads can reach |
| RBAC Patterns | [RBAC Guide](../best-practices/identity-rbac-patterns.md) | Workspace roles, item permissions, and Entra ID integration |
| Zero Trust | [Zero Trust](../best-practices/security/zero-trust-blueprint.md) | Never-trust, always-verify architecture for Fabric deployments |
| SOC2 Readiness | [SOC2 Guide](../best-practices/security/soc2-type2-readiness.md) | Map Fabric controls to SOC2 Trust Service Criteria |
| Threat Modeling | [STRIDE Model](../best-practices/security/threat-model-stride.md) | Systematic threat identification using STRIDE methodology |
| Data Exfiltration Prevention | [DLP Guide](../best-practices/security/data-exfiltration-prevention.md) | Prevent unauthorized data movement out of the Fabric environment |
| Audit Trail Immutability | [Immutability](../best-practices/security/audit-trail-immutability.md) | Tamper-proof logging for regulatory evidence |

---

## Common Pitfalls

1. **Relying only on workspace roles for security** - Workspace roles (Admin, Member, Contributor, Viewer) are coarse-grained. Use OneLake Security for table- and column-level access control when you need fine-grained data protection.

2. **Not enabling audit logs early** - Audit logs are essential for incident investigation and compliance evidence. Enable them in your first session, not after an incident. Retroactive logging is not possible.

3. **Using Microsoft-managed keys by default without a decision** - For regulated workloads, defaulting to Microsoft-managed keys may not meet data sovereignty requirements. Make an explicit decision about CMK vs. MMK and document the rationale.

4. **Skipping outbound access protection** - Without OAP, Spark notebooks and pipelines can reach any internet endpoint, creating data exfiltration risk. Restrict outbound access to approved destinations only.

5. **Treating compliance as a one-time exercise** - SOC2, ISO 27001, and GDPR compliance require continuous monitoring, not a point-in-time checklist. Set up recurring control reviews and automated evidence collection. See the [ISO 27001 Mapping](../best-practices/security/iso27001-mapping.md).

---

## Related Resources

<div class="grid cards" markdown>

-   :material-lock:{ .lg .middle } __OneLake Security__

    ---

    Fine-grained security at the data layer: row-level, column-level, and object-level access control.

    [:octicons-arrow-right-24: OneLake Security](../features/onelake-security.md)

-   :material-eye:{ .lg .middle } __Data Governance__

    ---

    Purview integration, sensitivity labels, data classification, and end-to-end lineage tracking.

    [:octicons-arrow-right-24: Governance Deep Dive](../best-practices/data-governance-deep-dive.md)

-   :material-key:{ .lg .middle } __Customer-Managed Keys__

    ---

    Azure Key Vault integration for encryption at rest with customer-controlled keys.

    [:octicons-arrow-right-24: CMK Guide](../best-practices/customer-managed-keys.md)

-   :material-shield-check:{ .lg .middle } __Compliance Frameworks__

    ---

    SOC2, ISO 27001, GDPR, and CCPA control mappings for Fabric deployments.

    [:octicons-arrow-right-24: SOC2 Readiness](../best-practices/security/soc2-type2-readiness.md)

</div>
