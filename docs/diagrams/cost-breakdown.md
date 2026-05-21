# 💰 Cost Breakdown Diagram

> **Last Updated**: 2026-04-15 | **Version**: 2.0
> **Status**: ✅ Final | **Maintainer**: Documentation Team

<div align="center" markdown>

![Category](https://img.shields.io/badge/Category-Cost_Management-green)
![Status](https://img.shields.io/badge/Status-Final-green)
![SKU](https://img.shields.io/badge/SKU-F64-blue)

</div>

---

## 📊 Production POC Cost Distribution

Distribution of monthly costs for a full production POC deployment (F64, 24/7).

```mermaid
pie showData
    title Monthly Cost Distribution - Production POC (~$10,340/month)
    "Fabric Capacity (F64)" : 8480
    "ADLS Gen2 Storage" : 500
    "Microsoft Purview" : 800
    "Log Analytics" : 350
    "Networking (Private EP)" : 200
    "Key Vault" : 10
```

### Key Insights

- **Fabric Capacity** represents approximately **82%** of total costs
- Storage and governance combined represent **13%** of costs
- Monitoring and security infrastructure represent **5%** of costs

---

## 🏢 Cost Comparison by Environment

Comparison of monthly costs across different deployment environments.

```mermaid
xychart-beta
    title "Monthly Cost by Environment (USD)"
    x-axis ["POC Demo (3-day)", "Development", "Staging", "Production Pilot"]
    y-axis "Monthly Cost ($)" 0 --> 12000
    bar [324, 535, 2200, 10340]
```

### Environment Cost Breakdown

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#0078d4', 'secondaryColor': '#50e6ff'}}}%%
flowchart TB
    subgraph Environments["Cost by Environment"]
        direction LR

        subgraph Demo["POC Demo<br/>(3 Days)"]
            D_COST["~$970"]
            D_FABRIC["Fabric: $835"]
            D_OTHER["Other: $135"]
        end

        subgraph Dev["Development<br/>(1 Month)"]
            DEV_COST["~$535"]
            DEV_FABRIC["Fabric: $130"]
            DEV_OTHER["Other: $405"]
        end

        subgraph Staging["Staging<br/>(1 Month)"]
            S_COST["~$2,200"]
            S_FABRIC["Fabric: $1,400"]
            S_OTHER["Other: $800"]
        end

        subgraph Prod["Production Pilot<br/>(1 Month)"]
            P_COST["~$10,340"]
            P_FABRIC["Fabric: $8,480"]
            P_OTHER["Other: $1,860"]
        end
    end

    style Demo fill:#e3f2fd
    style Dev fill:#e8f5e9
    style Staging fill:#fff3e0
    style Prod fill:#fce4ec
```

---

## 📈 Fabric SKU Cost Comparison

Comparison of Fabric capacity SKUs by monthly cost at different usage patterns.

```mermaid
xychart-beta
    title "Fabric SKU Monthly Costs by Usage Pattern"
    x-axis ["F2", "F4", "F8", "F16", "F32", "F64"]
    y-axis "Monthly Cost ($)" 0 --> 9000
    bar "24/7" [265, 530, 1060, 2120, 4240, 8480]
    bar "12hr/day" [133, 265, 530, 1060, 2120, 4240]
    bar "8hr/day (weekdays)" [88, 176, 353, 706, 1413, 2827]
```

### SKU Selection Decision Tree

```mermaid
flowchart TD
    A[Start: Select Fabric SKU] --> B{Parallel Jobs<br/>Needed?}

    B -->|1-2 jobs| C{Data Volume}
    B -->|4-8 jobs| D{Performance<br/>Requirements}
    B -->|8+ jobs| E[F32 or higher]

    C -->|< 10 GB/day| F[F2 - $265/mo]
    C -->|10-50 GB/day| G[F4 - $530/mo]
    C -->|> 50 GB/day| H[F8 - $1,060/mo]

    D -->|Standard| I[F16 - $2,120/mo]
    D -->|High| J[F32 - $4,240/mo]

    E --> K{Enterprise<br/>Workload?}
    K -->|POC/Pilot| L[F64 - $8,480/mo]
    K -->|Production| M[F128+ - $16,960+/mo]

    style L fill:#ffd700
    style F fill:#90EE90
    style G fill:#90EE90
```

---

## 💡 Cost Optimization Opportunities

Visualization of potential savings through optimization strategies.

```mermaid
pie showData
    title Potential Monthly Savings (From $10,340 baseline)
    "Optimized Cost" : 5170
    "Pause/Resume Savings" : 2827
    "Reserved Capacity Savings" : 1270
    "Storage Lifecycle Savings" : 200
    "Log Optimization Savings" : 100
    "Other Optimizations" : 773
```

### Optimization Strategy Flow

```mermaid
flowchart LR
    subgraph Current["Current State"]
        A["$10,340/mo<br/>Pay-as-you-go<br/>24/7 capacity"]
    end

    subgraph Strategies["Optimization Strategies"]
        B["Pause/Resume<br/>-50% Fabric"]
        C["Reserved Capacity<br/>-25% Fabric"]
        D["Storage Lifecycle<br/>-40% Cold Data"]
        E["Log Basic Tier<br/>-70% High-Volume"]
    end

    subgraph Optimized["Optimized State"]
        F["$5,170/mo<br/>50% savings"]
    end

    A --> B --> F
    A --> C --> F
    A --> D --> F
    A --> E --> F

    style A fill:#ff6b6b
    style F fill:#51cf66
```

### Savings Breakdown by Strategy

```mermaid
xychart-beta
    title "Monthly Savings by Optimization Strategy"
    x-axis ["Pause/Resume", "Reserved 1-yr", "Storage Lifecycle", "Basic Logs", "Purview Schedule"]
    y-axis "Monthly Savings ($)" 0 --> 3000
    bar [2827, 2120, 200, 175, 100]
```

---

## 📅 Monthly Cost Forecast

Projected costs over a 6-month POC timeline.

```mermaid
xychart-beta
    title "6-Month POC Cost Forecast"
    x-axis ["Month 1", "Month 2", "Month 3", "Month 4", "Month 5", "Month 6"]
    y-axis "Cumulative Cost ($)" 0 --> 45000
    line "Without Optimization" [10340, 20680, 31020, 41360, 51700, 62040]
    line "With Optimization" [8000, 13170, 18340, 23510, 28680, 33850]
    line "Pilot (Reduced Scope)" [5000, 8000, 11000, 14000, 17000, 20000]
```

### Cost Timeline with Milestones

```mermaid
gantt
    title POC Cost Timeline with Key Milestones
    dateFormat YYYY-MM-DD
    section Fabric
    F64 Development (F4)     :a1, 2025-01-01, 30d
    F64 Staging (F16)        :a2, after a1, 30d
    F64 Production Pilot     :a3, after a2, 90d

    section Cost Events
    Initial Setup (~$1K)     :milestone, 2025-01-01, 1d
    Month 1 Review (~$2.5K)  :milestone, 2025-01-31, 1d
    Month 2 Review (~$5K)    :milestone, 2025-02-28, 1d
    Reserved Capacity Decision :milestone, 2025-03-15, 1d
    Month 3-5 Pilot (~$8.5K/mo) :milestone, 2025-03-01, 90d
    Final Review             :milestone, 2025-05-31, 1d
```

---

## 🔥 Resource Cost Heat Map

Visual representation of cost intensity by resource type and activity.

```mermaid
quadrantChart
    title Resource Cost vs Usage Frequency
    x-axis Low Frequency --> High Frequency
    y-axis Low Cost --> High Cost
    quadrant-1 Optimize First
    quadrant-2 Monitor Closely
    quadrant-3 Acceptable
    quadrant-4 Review Usage

    "Fabric Compute": [0.9, 0.95]
    "Storage Writes": [0.8, 0.3]
    "Storage Reads": [0.9, 0.2]
    "Purview Scanning": [0.3, 0.4]
    "Log Ingestion": [0.85, 0.25]
    "Key Vault Ops": [0.5, 0.05]
    "Private Endpoints": [0.95, 0.1]
```

---

## 🧩 Component Cost Relationship

How different components contribute to total cost.

```mermaid
flowchart TB
    subgraph Total["Total Monthly Cost: ~$10,340"]
        direction TB

        subgraph Compute["Compute Layer (82%)"]
            FABRIC["Microsoft Fabric F64<br/>$8,480"]
        end

        subgraph Data["Data Layer (5%)"]
            STORAGE["ADLS Gen2<br/>$500"]
        end

        subgraph Gov["Governance (8%)"]
            PURVIEW["Microsoft Purview<br/>$800"]
        end

        subgraph Ops["Operations (5%)"]
            LOGS["Log Analytics<br/>$350"]
            NET["Networking<br/>$200"]
            KV["Key Vault<br/>$10"]
        end
    end

    FABRIC -->|"Processes"| STORAGE
    STORAGE -->|"Cataloged by"| PURVIEW
    FABRIC -->|"Logs to"| LOGS
    STORAGE -->|"Secured by"| KV
    FABRIC -->|"Connected via"| NET

    style FABRIC fill:#0078d4,color:#fff
    style STORAGE fill:#50e6ff
    style PURVIEW fill:#7719aa,color:#fff
    style LOGS fill:#00a4ef,color:#fff
```

---

## 🔗 Related Documents

| Document | Description |
|----------|-------------|
| [Cost Estimation Guide](../COST_ESTIMATION.md) | Detailed cost breakdown and scenarios |
| [Architecture Overview](architecture-overview.md) | System architecture diagrams |
| [Deployment Guide](../DEPLOYMENT.md) | Infrastructure deployment instructions |
| [Capacity Planning](../best-practices/capacity-planning-cost-optimization.md) | SKU selection and cost optimization |

---

[⬆️ Back to Top](#-cost-breakdown-diagram) | [📚 Parent](../ARCHITECTURE.md) | [🏠 Home](../index.md)
