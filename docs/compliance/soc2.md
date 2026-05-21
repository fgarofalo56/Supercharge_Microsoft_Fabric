---
hero: assets/heroes/compliance-soc2.svg
hero_alt: "SOC 2 — Trust Services Criteria readiness"
---

# 🔒 SOC 2 Compliance Mapping for Microsoft Fabric

<div align="center" markdown>

**Trust Service Criteria Mapped to Fabric Controls**

![Framework](https://img.shields.io/badge/Framework-SOC_2_Type_II-blue?style=for-the-badge)
![Controls](https://img.shields.io/badge/Controls-15_Mapped-green?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-May_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-05-05` | **Version:** 1.0.0

---

## 🎯 Overview

SOC 2 (System and Organization Controls 2) is a compliance framework developed by the AICPA (American Institute of Certified Public Accountants) that evaluates an organization's controls relevant to security, availability, processing integrity, confidentiality, and privacy — known as the Trust Service Criteria (TSC).

### Applicability to Fabric

SOC 2 applies to Microsoft Fabric deployments when:

- Your organization provides SaaS or cloud services and must demonstrate control effectiveness to customers
- Customer contracts or RFPs require SOC 2 Type II attestation
- You process or store customer data in Fabric and must demonstrate security posture
- Your organization's internal risk management program requires SOC 2 compliance

### Microsoft's SOC 2 Coverage

Microsoft Azure (including Fabric) maintains SOC 2 Type II reports covering all five Trust Service Criteria. Customers can:

1. **Leverage Microsoft's SOC 2 report** for platform-level controls (available via Service Trust Portal)
2. **Implement customer-level controls** for their specific Fabric configuration
3. **Include Fabric in their own SOC 2 audit** by referencing the complementary user entity controls (CUECs)

### Trust Service Categories

| Category | Description | Fabric Relevance |
|----------|-------------|-----------------|
| **Security (CC)** | Protection against unauthorized access | RBAC, MFA, encryption, network controls |
| **Availability (A)** | System uptime and performance | SLA, BCDR, capacity management |
| **Processing Integrity (PI)** | Data processing is complete, valid, accurate, timely | ETL validation, Delta ACID, data quality checks |
| **Confidentiality (C)** | Confidential information is protected | Sensitivity labels, DLP, CMK, data classification |
| **Privacy (P)** | Personal information lifecycle management | Purview, consent management, data subject rights |

---

## 📊 Control Mapping Table

Trust Service Criteria mapped to Microsoft Fabric implementations:

| Control ID | Control Name | TSC Category | Fabric Implementation | Evidence |
|-----------|-------------|-------------|----------------------|----------|
| CC1.1 | COSO Principle 1 — Integrity and Ethics | Security | Organization-level code of conduct; Fabric acceptable use policy; tenant admin controls restricting unauthorized actions | Policy documents, tenant settings export |
| CC2.1 | Internal Communication of Objectives | Security | Documented Fabric security architecture; workspace naming conventions with classification; onboarding procedures for Fabric users | Architecture documentation, naming standards |
| CC3.1 | Risk Assessment | Security | Risk assessment covering Fabric data processing; threat modeling for data flows; Defender for Cloud risk scoring | Risk assessment report, Defender findings |
| CC5.1 | Control Activities — Logical Access | Security | Entra ID authentication; MFA enforcement via Conditional Access; workspace RBAC (Admin/Member/Contributor/Viewer); OneLake data access roles | CA policies, role assignments, data access roles |
| CC5.2 | Control Activities — Access Provisioning | Security | Entra ID group-based provisioning; access request workflows; quarterly access reviews; automated deprovisioning | Access review reports, provisioning logs |
| CC5.3 | Control Activities — Access Removal | Security | Automated deprovisioning via Entra ID lifecycle; workspace role removal on team change; guest access expiration policies | Deprovisioning logs, guest expiration config |
| CC6.1 | Logical and Physical Access — Infrastructure | Security | Microsoft datacenter physical security; Fabric managed VNet; private endpoints; Outbound Access Protection; IP firewall rules | SOC 2 report (Microsoft), network config |
| CC6.6 | Encryption at Rest | Security | AES-256 encryption for OneLake (MMK); SQL Database TDE with CMK option; Storage Account SSE with CMK | Encryption configuration, CMK status |
| CC6.7 | Encryption in Transit | Security | TLS 1.2+ enforced for all Fabric communications; HTTPS-only access; encrypted gateway connections | TLS audit, network configuration |
| CC7.1 | Monitoring — Anomaly Detection | Security | Microsoft Sentinel SIEM integration; Fabric admin audit logs; Defender for Cloud alerts; anomalous access detection via Entra ID Protection | Sentinel rules, Defender alerts, risk detections |
| CC7.2 | Monitoring — Incident Management | Security | Incident response procedures; Microsoft Sentinel playbooks; Fabric admin notifications; integration with ITSM | IR plan, Sentinel playbooks, incident logs |
| A1.1 | Availability — Capacity Management | Availability | Fabric capacity monitoring; auto-pause/resume; capacity alerts and budgets; Azure Monitor metrics | Capacity metrics, alert config, budget settings |
| A1.2 | Availability — Recovery | Availability | OneLake geo-redundant storage; SQL Database backup/restore; workspace BCDR procedures; documented RTO/RPO | BCDR plan, backup config, DR test results |
| PI1.1 | Processing Integrity — Data Accuracy | Processing Integrity | Delta Lake ACID transactions; Great Expectations data quality suites; schema enforcement at Bronze layer; reconciliation checks | GE suite results, schema definitions, pipeline logs |
| C1.1 | Confidentiality — Data Classification | Confidentiality | Microsoft Purview sensitivity labels; DLP policies; workspace-level classification; data governance policies | Label assignments, DLP policy reports, governance config |

---

## 🤝 Shared Responsibility Model

| TSC Category | Microsoft Responsibility | Customer Responsibility |
|-------------|--------------------------|------------------------|
| **Security — Physical** | Datacenter physical security, environmental controls, hardware security (attested in Microsoft SOC 2 report) | N/A |
| **Security — Platform** | Fabric runtime security, OneLake storage encryption, platform patching, network backbone | N/A |
| **Security — Logical Access** | Entra ID infrastructure, MFA platform, RBAC engine, platform audit event generation | User provisioning, role assignments, MFA policy enforcement, access reviews, RLS configuration |
| **Security — Network** | TLS enforcement, Azure backbone encryption, DDoS protection | Managed VNet configuration, private endpoints, OAP, firewall rules |
| **Security — Encryption** | Platform-managed encryption (MMK), TLS in transit | CMK configuration, sensitivity labels, DLP policies |
| **Availability** | Azure SLA (99.9%+ for Fabric), infrastructure redundancy, platform scaling | Capacity planning, BCDR procedures, DR testing, monitoring dashboards |
| **Processing Integrity** | Platform data integrity (storage checksums, transaction logs) | ETL validation logic, data quality checks, reconciliation, schema enforcement |
| **Confidentiality** | Platform encryption, tenant isolation | Data classification, sensitivity labels, DLP policies, access controls for confidential data |
| **Privacy** | Privacy controls in Azure platform; Microsoft Privacy Statement | Data subject request handling, consent management, privacy impact assessments, data retention policies |

---

## ⚠️ Gap Analysis and Limitations

| Gap | TSC Criteria | Impact | Compensating Control |
|-----|------------|--------|---------------------|
| No built-in data classification discovery | C1.1, CC3.1 | Confidential data may be unclassified | Deploy Purview auto-labeling policies; scan OneLake with data classification rules |
| Fabric lacks native DLP enforcement for all item types | C1.1 | DLP policies may not cover all Fabric artifacts | Apply DLP at the Power BI layer; use sensitivity labels for classification; restrict export capabilities |
| No automatic access review in Fabric | CC5.2, CC5.3 | Stale access may persist | Use Entra ID Access Reviews for quarterly recertification; script workspace role audits via Admin API |
| Processing integrity monitoring requires custom implementation | PI1.1 | No built-in data quality dashboard | Implement Great Expectations suites; build monitoring notebook for data quality metrics |
| Privacy request fulfillment requires manual orchestration | P1.1 | No automated DSR fulfillment for OneLake data | Build DSR workflow using Power Automate; document data locations for each PII category |
| Capacity throttling may impact availability | A1.1 | Heavy workloads can be throttled on shared capacity | Use dedicated capacity (F64+); configure capacity alerts; implement workload scheduling |
| No formal penetration testing API for Fabric | CC3.1 | Cannot fully test application-layer security | Conduct authorized pen testing through Microsoft's process; focus on configuration review |
| SOC 2 Type II evidence collection is manual | All | Ongoing evidence collection burden | Automate evidence collection via Admin API scripts; build compliance dashboard |

---

## ✅ Implementation Checklist

### Security (Common Criteria)

- [ ] **CC5.1:** Configure Conditional Access policies enforcing MFA for all Fabric users
- [ ] **CC5.1:** Implement workspace RBAC with least privilege roles
- [ ] **CC5.1:** Configure OneLake data access roles for granular data access control
- [ ] **CC5.2:** Set up Entra ID group-based provisioning for Fabric workspace access
- [ ] **CC5.2:** Configure quarterly Entra ID Access Reviews for Fabric workspace roles
- [ ] **CC5.3:** Verify automated deprovisioning removes Fabric access on employee offboarding
- [ ] **CC6.1:** Deploy managed VNet and private endpoints for Fabric workspace
- [ ] **CC6.1:** Enable Outbound Access Protection
- [ ] **CC6.6:** Enable CMK for Fabric SQL Database; document MMK for OneLake
- [ ] **CC7.1:** Integrate Fabric audit logs with Microsoft Sentinel
- [ ] **CC7.1:** Configure anomaly detection alerts for unusual data access patterns
- [ ] **CC7.2:** Document incident response procedure specific to Fabric workloads

### Availability

- [ ] **A1.1:** Configure capacity alerts and budget thresholds
- [ ] **A1.1:** Implement auto-pause and workload scheduling for capacity management
- [ ] **A1.2:** Document RTO/RPO for all Fabric workloads
- [ ] **A1.2:** Configure SQL Database backup retention and test restore procedures
- [ ] **A1.2:** Conduct annual DR test and document results

### Processing Integrity

- [ ] **PI1.1:** Implement schema enforcement at Bronze layer ingestion
- [ ] **PI1.1:** Deploy Great Expectations data quality suites for Silver/Gold layers
- [ ] **PI1.1:** Configure pipeline monitoring and alerting for processing failures
- [ ] **PI1.1:** Implement data reconciliation checks between source and Fabric

### Confidentiality

- [ ] **C1.1:** Deploy sensitivity labels across all Fabric workspaces
- [ ] **C1.1:** Configure DLP policies for sensitive data types
- [ ] **C1.1:** Restrict data export formats for workspaces containing confidential data
- [ ] **C1.1:** Enable Purview auto-labeling for known confidential data patterns

### Privacy

- [ ] Document PII data flows through Fabric
- [ ] Implement data subject request workflow for OneLake data
- [ ] Configure data retention policies aligned with privacy requirements
- [ ] Conduct privacy impact assessment for Fabric analytics workloads

---

## 📚 References

### Internal Best-Practices

| Guide | Relevant TSC Criteria |
|-------|----------------------|
| [Customer-Managed Keys](../best-practices/customer-managed-keys.md) | CC6.6 — Encryption at rest |
| [SQL Audit Logs Compliance](../best-practices/sql-audit-logs-compliance.md) | CC7.1 — Monitoring |
| [Identity & RBAC Patterns](../best-practices/identity-rbac-patterns.md) | CC5.1, CC5.2, CC5.3 — Access controls |
| [Network Security](../best-practices/network-security.md) | CC6.1 — Infrastructure security |
| [Outbound Access Protection](../best-practices/outbound-access-protection.md) | CC6.1 — Boundary protection |
| [Monitoring & Observability](../best-practices/monitoring-observability.md) | CC7.1, CC7.2 — Monitoring and incident management |
| [Disaster Recovery & BCDR](../best-practices/disaster-recovery-bcdr.md) | A1.1, A1.2 — Availability |
| [Capacity Planning](../best-practices/capacity-planning-cost-optimization.md) | A1.1 — Capacity management |
| [Testing Strategies](../best-practices/testing-strategies.md) | PI1.1 — Processing integrity |
| [Data Governance Deep Dive](../best-practices/data-governance-deep-dive.md) | C1.1 — Confidentiality |

### External References

- [AICPA Trust Service Criteria](https://www.aicpa.org/resources/landing/system-and-organization-controls-soc-suite-of-services)
- [Microsoft SOC Reports — Service Trust Portal](https://servicetrust.microsoft.com/)
- [Microsoft Compliance Offerings](https://learn.microsoft.com/en-us/compliance/regulatory/offering-home)
- [SOC 2 Complementary User Entity Controls](https://learn.microsoft.com/en-us/compliance/regulatory/offering-soc-2)

---

*This mapping reflects SOC 2 Trust Service Criteria (2017) and Microsoft Fabric capabilities as of May 2026. Organizations should reference Microsoft's SOC 2 Type II report from the Service Trust Portal and implement complementary user entity controls (CUECs) for their specific Fabric deployment.*
