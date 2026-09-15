---
hero: assets/heroes/features.svg
hero_alt: Fabric feature — Approval Activity — Human-in-the-Loop Pipeline Gates
type: feature
---
# ✅ Approval Activity — Human-in-the-Loop Pipeline Gates

<div align="center" markdown>

**Pause Pipelines for Human Decisions — Auditable Sign-Off in Data Factory**

![Category](https://img.shields.io/badge/Category-Operations_%26_DevOps-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-September_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-09-07` | **Version:** 1.0.0

---

## 🎯 Overview

The **Approval activity** in Fabric Data Factory pipelines pauses execution and sends an approval request to one or more reviewers. The pipeline waits for a response, then continues down different paths depending on whether the request is **approved** or **rejected** — bringing governed, auditable human decision points directly into data orchestration.

Use it when a workflow needs a human decision before moving forward: signing off on a data load, approving a report for publication, or enforcing separation of duties for compliance.

### How It Works

1. The pipeline reaches an approval activity
2. An approval request is sent to the reviewers you specified
3. The pipeline **pauses** and waits
4. Based on the decision, the pipeline continues along the **success** (approved) or **failure** (rejected/timeout) path

### Approval Types

| Type | Notification | RBAC Support |
|------|-------------|--------------|
| **Outlook 365** | Email with **Approve**/**Reject** buttons | ❌ No RBAC |
| **Microsoft Teams** | Teams message with approval action links | ❌ No RBAC |
| **Custom endpoint** | HTTP request to your configured endpoint | ✅ Use this when you need RBAC |

---

## 🏗️ Configuration

### Adding the Activity

1. Create or open a pipeline, then search for **Approval** in the **Activities** pane
2. On the **General** tab, set the activity name and **Timeout** — if no response arrives before the timeout, the activity fails and follows the rejection path
3. On the **Settings** tab, choose the approval **Type** and configure:
   - **Connection** (Outlook 365 or Teams)
   - **Request** title (appears in the email subject / first line of the Teams message)
   - **Description** — include enough context so the reviewer understands what they're approving and why
   - **Approver** — individual user or group (Outlook); channel or group chat (Teams)

> **Note:** The requestor is automatically the last person to modify the pipeline.

### Approver Experience

1. Reviewers receive the notification with a link to the **Monitoring Hub**
2. They open the **Review** tab and submit their decision
3. If an approver has multiple pending approvals, they can **bulk approve or reject** from the Review tab
4. The pipeline resumes automatically after the decision

### Monitoring and Audit

Approval runs appear in pipeline run history with full traceability:

- When approval requests were created and resolved
- **Who** approved or rejected each request
- Approval outcomes alongside overall pipeline status

---

## 🏛️ Business Workflow Patterns

| Pattern | Design |
|---------|--------|
| **Approval-gated publishing** | Require business owner or compliance sign-off before data is published or exposed |
| **Operational handoffs** | Pause processing until downstream teams confirm readiness |
| **Exception handling** | Route failures to manual review paths with Teams/email notification |
| **Controlled promotions** | Gate data movement from dev/staging into production |

Combine with **If Condition** (branch on approval results), **Switch** (route on defined cases), **Web activity** (call external workflow systems), and **Teams/Outlook activities** (notify stakeholders of outcomes).

---

## 🎰 Casino/Gaming POC Applications

| Use Case | Application |
|----------|-------------|
| **CTR filing gate** | Compliance officer approves the day's CTR batch before submission to FinCEN |
| **Gold layer promotion** | Data steward approves silver→gold promotion after data quality checks pass |
| **SAR case escalation** | Rejection path routes flagged transactions to a manual review queue |
| **Federal report release** | Program manager approves grant spending reports before publication |
| **Separation of duties** | The person who built the pipeline can't approve its production data loads |

---

## ⚠️ Best Practices & Limitations

1. **Include clear context** — give reviewers enough detail so they don't need follow-up questions
2. **Keep approval scopes narrow** — only gate steps that genuinely need a human decision
3. **Design clear rejection paths** — handle rejections with notifications or remediation steps, not dead ends
4. **Don't use approvals as generic delays** — reflect real business processes
5. **RBAC requires Custom endpoint** — Outlook 365 and Teams approval types don't support role-based access control
6. **Timeout = rejection** — set timeouts deliberately; an expired approval follows the failure path

---

## 🔗 Related Documents

- [Deployment Pipelines](deployment-pipelines.md) — Stage-based promotion (complementary governance layer)
- [Data Activator](data-activator.md) — Rule-based automated actions (the no-human counterpart)
- [Copy Job CDC](copy-job-cdc.md) — Ingestion pipelines that can be approval-gated
- [Fabric REST APIs](fabric-rest-apis.md) — Programmatic pipeline management
- [Fabric CI/CD Deployment](../best-practices/fabric-cicd-deployment.md) — Pipeline promotion patterns

---

## 📚 Microsoft Learn References

- [Approval activity in Fabric Data Factory pipelines](https://learn.microsoft.com/fabric/data-factory/approval-activity)
- [Business workflow management with pipelines](https://learn.microsoft.com/fabric/data-factory/business-workflow-management)
- [Activity overview](https://learn.microsoft.com/fabric/data-factory/activity-overview)

---

> 📝 **Document Metadata**
> - **Author**: Documentation Team
> - **Reviewers**: Data Engineering, Compliance, Operations
> - **Classification**: Internal
> - **Next Review**: 2026-12-07
