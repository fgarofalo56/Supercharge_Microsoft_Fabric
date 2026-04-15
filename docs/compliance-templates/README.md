[Home](../index.md) > [Docs](..) > [Compliance Templates](./) > Overview

# 📋 Compliance Templates

> **Last Updated**: 2026-04-15 | **Version**: 2.0
> **Status**: ✅ Final | **Maintainer**: Documentation Team

<div align="center">

![Category](https://img.shields.io/badge/Category-Compliance-red)
![Status](https://img.shields.io/badge/Status-Final-green)
![Regulation](https://img.shields.io/badge/Regulation-BSA%20%7C%20FinCEN%20%7C%20IRS-blue)

</div>

---

## 📖 Overview

This directory contains templates and data extraction scripts for gaming regulatory compliance reports. These templates are designed to meet the requirements of various gaming commissions and federal regulations.

---

## 📑 Template Index

| Template | Regulation | Authority | Filing Deadline |
|----------|------------|-----------|-----------------|
| [CTR Template](./CTR_TEMPLATE.md) | Title 31 / BSA | FinCEN | 15 days |
| [W-2G Template](./W2G_TEMPLATE.md) | IRS Gaming | IRS | Jan 31 / Mar 31 |
| [SAR Template](./SAR_TEMPLATE.md) | BSA | FinCEN | 30 days |
| [NIGC MICS](./MICS_TEMPLATE.md) | NIGC Regulations | NIGC | Varies |

---

## 🏛️ Regulatory Framework

### Federal Requirements

| Regulation | Description | Threshold |
|------------|-------------|-----------|
| **CTR** | Currency Transaction Report | Cash > $10,000 |
| **SAR** | Suspicious Activity Report | Suspicious patterns |
| **W-2G** | Gambling Winnings | Slots >= $1,200 |
| **1042-S** | Foreign Person Winnings | NRA winnings |

### State Requirements

Gaming regulations vary by jurisdiction. Common requirements include:

- Daily revenue reports
- Jackpot logs
- Patron dispute records
- Self-exclusion compliance
- Responsible gaming reports

---

## 🗄️ Data Sources

All compliance reports draw from these platform tables:

| Table | Purpose |
|-------|---------|
| `bronze_financial_transactions` | Cash transactions |
| `silver_slot_telemetry` | Jackpots, large wins |
| `dim_player` | Player identification |
| `gold.compliance_ctr_filings` | CTR staging |
| `gold.compliance_w2g_filings` | W-2G staging |

---

## ⚙️ Automation

### Daily Compliance Checks

```python
# Run daily to identify compliance events
def daily_compliance_check():
    # CTR threshold monitoring
    check_ctr_thresholds()

    # W-2G jackpot identification
    identify_reportable_jackpots()

    # SAR pattern detection
    run_sar_detection_rules()

    # Self-exclusion compliance
    verify_self_exclusion_compliance()
```

### Filing Workflow

```mermaid
flowchart LR
    A[Transaction] --> B{Threshold?}
    B -->|Yes| C[Extract Data]
    B -->|No| D[Log Only]
    C --> E[Compliance Review]
    E --> F{Approved?}
    F -->|Yes| G[Generate Filing]
    F -->|No| H[Additional Review]
    G --> I[Submit to Authority]
    I --> J[Archive]
```

---

## ✅ Best Practices

1. **Automate Threshold Monitoring** - Use real-time queries to flag reportable events
2. **Maintain Audit Trail** - Log all compliance decisions and filings
3. **Secure PII** - Encrypt sensitive player data
4. **Regular Testing** - Validate extraction queries quarterly
5. **Document Exceptions** - Record any manual overrides or adjustments

---

## 📞 Contact

**Compliance Questions:** compliance@casino.com
**Technical Support:** data-engineering@casino.com

---

## 🔗 Related Documents

| Document | Description |
|----------|-------------|
| [CTR Template](./CTR_TEMPLATE.md) | Currency Transaction Report data extraction template |
| [SAR Template](./SAR_TEMPLATE.md) | Suspicious Activity Report detection and filing |
| [W-2G Template](./W2G_TEMPLATE.md) | Gambling winnings tax reporting template |
| [MICS Template](./MICS_TEMPLATE.md) | NIGC Minimum Internal Control Standards |
| [Data Governance](../best-practices/data-governance-deep-dive.md) | Governance and compliance frameworks |

---

[⬆️ Back to Top](#-compliance-templates) | [📚 Parent](./) | [🏠 Home](../index.md)
