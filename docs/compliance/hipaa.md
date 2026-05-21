# 🏥 HIPAA Compliance Mapping for Microsoft Fabric

<div align="center" markdown>

**Health Insurance Portability and Accountability Act — PHI Handling in Fabric**

![Framework](https://img.shields.io/badge/Framework-HIPAA-blue?style=for-the-badge)
![Controls](https://img.shields.io/badge/Controls-15_Mapped-green?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-May_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-05-05` | **Version:** 1.0.0

---

## 🎯 Overview

The Health Insurance Portability and Accountability Act (HIPAA) establishes national standards for protecting individuals' electronic protected health information (ePHI). The HIPAA Security Rule (45 CFR Part 160 and Part 164, Subparts A and C) specifies administrative, physical, and technical safeguards that covered entities and business associates must implement.

### Applicability to Fabric

HIPAA applies to Microsoft Fabric deployments when:

- A covered entity (healthcare provider, health plan, clearinghouse) uses Fabric to process ePHI
- A business associate uses Fabric on behalf of a covered entity
- Fabric is part of a healthcare analytics platform processing patient data
- The deployment handles data subject to 42 CFR Part 2 (substance abuse records)

### Business Associate Agreement (BAA)

Microsoft offers a HIPAA BAA as part of the Microsoft Online Services Terms. Key points:

| BAA Element | Details |
|-------------|---------|
| **Coverage** | Microsoft Fabric is a covered service under the Microsoft HIPAA BAA |
| **Scope** | Applies to ePHI processed, stored, or transmitted through Fabric |
| **Execution** | Automatically included in Enterprise Agreement; available via Microsoft Trust Center |
| **Customer Obligation** | Must sign BAA before processing ePHI; must implement required safeguards |

> **Critical:** A signed BAA is a **prerequisite** for processing any ePHI in Fabric. The BAA does not replace the customer's obligation to implement required safeguards.

### PHI Data Categories in Fabric

| Data Category | Examples | Fabric Storage | Protection Level |
|--------------|----------|----------------|-----------------|
| **Direct Identifiers** | Name, SSN, MRN, phone, email, address | Lakehouse (OneLake), SQL Database | Encrypt, mask, restrict access |
| **Clinical Data** | Diagnoses, procedures, lab results, medications | Lakehouse (OneLake), Warehouse | Encrypt, audit access, RLS |
| **Financial/Billing** | Claims, EOBs, billing codes | Lakehouse (OneLake), SQL Database | Encrypt, restrict to billing roles |
| **Operational** | Appointment schedules, provider notes | Lakehouse (OneLake) | Encrypt, limit to care team |

---

## 📊 Control Mapping Table

HIPAA Security Rule safeguards mapped to Microsoft Fabric implementations:

| Control ID | Control Name | HIPAA Requirement | Fabric Implementation | Evidence |
|-----------|-------------|-------------------|----------------------|----------|
| §164.308(a)(1) | Security Management Process | Risk analysis, risk management, sanctions, review | Azure Security Center risk assessment; Fabric admin monitoring; documented risk analysis covering Fabric workloads | Risk assessment report, monitoring dashboards |
| §164.308(a)(3) | Workforce Security | Authorization and supervision; workforce clearance; termination procedures | Entra ID lifecycle management; workspace role assignment tied to HR provisioning; automated deprovisioning on termination | Entra ID access reviews, deprovisioning logs |
| §164.308(a)(4) | Information Access Management | Access authorization; access establishment and modification | OneLake data access roles; workspace RBAC (Admin/Member/Contributor/Viewer); item-level permissions | Role assignment matrix, data access role definitions |
| §164.308(a)(5) | Security Awareness Training | Security reminders; protection from malware; login monitoring; password management | Customer-managed training program; Entra ID sign-in risk monitoring; password policies | Training completion records, sign-in risk reports |
| §164.308(a)(6) | Security Incident Procedures | Response and reporting | Microsoft Sentinel integration for Fabric; incident response playbooks; automated alerting on anomalous ePHI access | Sentinel rules, IR playbook, alert history |
| §164.308(a)(7) | Contingency Plan | Data backup; disaster recovery; emergency operations; testing | Fabric BCDR capabilities; OneLake geo-redundant storage; SQL Database backup/restore; documented DR plan | BCDR plan, backup configuration, DR test results |
| §164.308(a)(8) | Evaluation | Periodic technical and non-technical evaluation | Annual HIPAA assessment; Fabric security configuration review; penetration testing | Assessment reports, configuration audit |
| §164.310(a)(1) | Facility Access Controls | Contingency operations; facility security plan; access control and validation | Microsoft datacenter physical security (SOC 2 Type II attested); customer office controls | Microsoft SOC 2 report, facility access logs |
| §164.310(d)(1) | Device and Media Controls | Disposal; media re-use; accountability; data backup and storage | OneLake soft-delete and purge; Fabric SQL Database deletion procedures; encrypted backups | Data disposal procedures, backup encryption config |
| §164.312(a)(1) | Access Control | Unique user identification; emergency access; automatic logoff; encryption | Entra ID unique identifiers; break-glass accounts for emergency access; session timeout via Conditional Access; AES-256 encryption at rest | Entra ID config, break-glass procedure, CA policy |
| §164.312(b) | Audit Controls | Record and examine activity | Fabric admin audit logs; SQL audit logs; Entra ID sign-in logs; comprehensive audit trail for ePHI access | Audit log samples, retention configuration |
| §164.312(c)(1) | Integrity | Protect ePHI from improper alteration or destruction | Delta Lake ACID transactions; OneLake versioning; SQL Database transaction logging; checksums on data movement | Delta transaction logs, pipeline validation |
| §164.312(d) | Person or Entity Authentication | Verify identity before granting access to ePHI | Entra ID MFA; Conditional Access policies; certificate-based authentication for clinical systems | MFA enforcement policy, CBA configuration |
| §164.312(e)(1) | Transmission Security | Guard against unauthorized access to ePHI in transit; encryption | TLS 1.2+ enforced for all Fabric communications; HTTPS-only access; encrypted gateway connections | TLS configuration audit, network trace |
| §164.316(b)(1) | Documentation | Maintain policies and procedures; retain for 6 years | Policies stored in SharePoint/Purview; Fabric configurations documented in IaC; audit logs retained per policy | Policy repository, IaC templates, retention settings |

---

## 🤝 Shared Responsibility Model

| HIPAA Domain | Microsoft Responsibility | Customer Responsibility |
|-------------|--------------------------|------------------------|
| **Physical Safeguards** | Datacenter physical security, environmental controls, media disposal at infrastructure level | Office/facility access controls for end-user devices accessing Fabric |
| **Platform Encryption** | AES-256 encryption at rest for OneLake; TLS 1.2+ in transit; platform-managed keys | CMK configuration for SQL Database; ensuring encryption covers all ePHI stores |
| **Access Control** | Entra ID platform; MFA infrastructure; RBAC engine | User provisioning; role assignments; RLS policies; minimum necessary access enforcement |
| **Audit Controls** | Audit event generation for platform operations | Audit log collection, retention (min 6 years for HIPAA), SIEM integration, regular review |
| **Integrity Controls** | Platform data integrity (Delta Lake ACID, storage checksums) | Data validation in ETL pipelines; quality checks; reconciliation procedures |
| **Transmission Security** | TLS enforcement; encrypted backbone | Gateway encryption configuration; VPN for on-premises connections |
| **BAA Compliance** | Execute BAA; maintain covered service status; breach notification | Sign BAA; implement required safeguards; breach reporting to HHS |
| **Risk Analysis** | Platform-level risk assessment; SOC 2/ISO 27001 attestations | Workload-specific risk analysis covering ePHI in Fabric; annual review |
| **Training** | N/A | HIPAA security awareness training for all workforce members accessing Fabric |
| **Incident Response** | Platform security incident detection; Microsoft breach notification obligations | Workload-specific IR plan; breach assessment; HHS notification within 60 days |

---

## ⚠️ Gap Analysis and Limitations

| Gap | HIPAA Requirement | Impact | Compensating Control |
|-----|-------------------|--------|---------------------|
| No built-in PHI detection in Fabric | §164.308(a)(1) — Risk analysis must identify all ePHI | ePHI may exist in unclassified datasets | Use Purview sensitivity labels with healthcare classifiers; scan OneLake for PHI patterns |
| OneLake lacks granular delete for right-of-amendment | §164.526 — Right to amend | Difficult to surgically update specific records | Implement amendment tracking table; use Delta Lake merge operations for record updates |
| Minimum necessary not enforced by platform | §164.502(b) — Minimum necessary standard | Overly broad access possible without configuration | Configure OneLake data access roles at folder level; implement RLS in semantic models; use column-level security |
| No automatic session logoff in Fabric web UI | §164.312(a)(2)(iii) — Auto logoff | Extended idle sessions remain active | Configure Conditional Access session controls (sign-in frequency, persistent browser) |
| 6-year retention requirement exceeds Log Analytics max | §164.316(b)(2) — 6-year documentation retention | Log Analytics max 730 days insufficient | Archive audit logs to immutable blob storage with 6-year lifecycle policy |
| Fabric Copilot/AI may process ePHI | §164.312(a)(1) — Access control for all ePHI access | AI features may access ePHI without explicit authorization | Disable Copilot for workspaces containing ePHI until AI governance controls are validated |
| No BAA-specific configuration toggle | BAA compliance is procedural, not technical | Must ensure only BAA-covered services process ePHI | Document Fabric as covered service; restrict ePHI to approved workspaces |
| Breach notification timeline | §164.408 — 60-day notification | Requires coordination between Microsoft and customer | Establish breach response procedure integrating Microsoft notifications with customer IR plan |

---

## ✅ Implementation Checklist

### Prerequisites

- [ ] Execute Microsoft HIPAA BAA (Enterprise Agreement or Microsoft Customer Agreement)
- [ ] Complete risk analysis covering Fabric as ePHI processing environment
- [ ] Designate HIPAA Security Officer responsible for Fabric compliance
- [ ] Document all ePHI data flows through Fabric (ingestion, processing, storage, reporting)

### Access Controls (§164.312(a))

- [ ] Configure workspace RBAC enforcing minimum necessary access
- [ ] Implement OneLake data access roles restricting ePHI folders to authorized roles
- [ ] Configure RLS in all semantic models containing ePHI
- [ ] Enable MFA for all users accessing ePHI workspaces via Conditional Access
- [ ] Set up emergency access (break-glass) accounts with monitoring
- [ ] Configure session timeout policies via Conditional Access

### Audit Controls (§164.312(b))

- [ ] Enable Fabric admin audit logging
- [ ] Configure SQL audit logs for all databases containing ePHI
- [ ] Set up Entra ID sign-in log collection
- [ ] Configure audit log retention (archive to blob storage for 6-year minimum)
- [ ] Integrate audit logs with Microsoft Sentinel or equivalent SIEM
- [ ] Create scheduled audit review process (minimum quarterly)

### Integrity Controls (§164.312(c))

- [ ] Implement data validation in all ETL pipelines processing ePHI
- [ ] Enable Delta Lake ACID transactions for Lakehouse ePHI tables
- [ ] Configure checksums or reconciliation for data movement pipelines
- [ ] Implement amendment tracking for patient record corrections

### Transmission Security (§164.312(e))

- [ ] Verify TLS 1.2+ enforcement for all Fabric connections
- [ ] Configure encrypted gateway connections for on-premises data sources
- [ ] Enable private endpoints for data sources containing ePHI
- [ ] Document all data transmission paths in system security documentation

### Data Protection

- [ ] Apply sensitivity labels (e.g., "HIPAA — ePHI") to all workspaces with patient data
- [ ] Enable DLP policies to prevent ePHI exfiltration
- [ ] Configure Outbound Access Protection
- [ ] Enable CMK for Fabric SQL databases containing ePHI
- [ ] Disable Copilot/AI features in ePHI workspaces (until governance validated)

### Documentation & Training (§164.316)

- [ ] Maintain HIPAA policies and procedures in controlled document repository
- [ ] Retain all security documentation for minimum 6 years
- [ ] Conduct annual HIPAA security awareness training for Fabric users
- [ ] Document Fabric configuration as part of the organization's HIPAA security plan

---

## 📚 References

### Internal Best-Practices

| Guide | Relevant HIPAA Safeguards |
|-------|--------------------------|
| [Customer-Managed Keys](../best-practices/customer-managed-keys.md) | §164.312(a)(2)(iv) — Encryption |
| [SQL Audit Logs Compliance](../best-practices/sql-audit-logs-compliance.md) | §164.312(b) — Audit controls |
| [Identity & RBAC Patterns](../best-practices/identity-rbac-patterns.md) | §164.312(a)(1) — Access control |
| [Network Security](../best-practices/network-security.md) | §164.312(e)(1) — Transmission security |
| [Outbound Access Protection](../best-practices/outbound-access-protection.md) | §164.312(e)(1) — Guard against unauthorized access |
| [Monitoring & Observability](../best-practices/monitoring-observability.md) | §164.312(b) — Audit controls |
| [Disaster Recovery & BCDR](../best-practices/disaster-recovery-bcdr.md) | §164.308(a)(7) — Contingency plan |
| [Data Governance Deep Dive](../best-practices/data-governance-deep-dive.md) | §164.308(a)(4) — Information access management |
| [Data Sharing & Federation](../best-practices/data-sharing-federation.md) | §164.502(b) — Minimum necessary |
| [Testing Strategies](../best-practices/testing-strategies.md) | §164.308(a)(8) — Evaluation |

### External References

- [HIPAA Security Rule (45 CFR §164)](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [HHS HIPAA Guidance](https://www.hhs.gov/hipaa/for-professionals/index.html)
- [Microsoft HIPAA/HITECH Offering](https://learn.microsoft.com/en-us/compliance/regulatory/offering-hipaa-hitech)
- [Microsoft Trust Center — HIPAA](https://www.microsoft.com/en-us/trust-center/compliance/hipaa)
- [42 CFR Part 2 — Substance Abuse Records](https://www.ecfr.gov/current/title-42/chapter-I/subchapter-A/part-2)

---

*This mapping reflects HIPAA Security Rule requirements and Microsoft Fabric capabilities as of May 2026. Organizations must conduct their own risk analysis and implement safeguards appropriate to their specific ePHI processing activities.*
