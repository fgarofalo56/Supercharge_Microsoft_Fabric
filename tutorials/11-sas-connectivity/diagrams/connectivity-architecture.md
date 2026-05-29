# SAS to Microsoft Fabric Connectivity Diagrams

!!! note "Third-party references — publicly sourced, good-faith comparison"
    This page references non-Microsoft products and services. That information is drawn from each vendor's **publicly available documentation** and is offered for honest, good-faith comparison only. This is a personal project written from a Microsoft Fabric and Azure perspective; it does **not** claim expertise in, or authority over, any third-party product, and nothing here is an official statement by, or endorsed by, those vendors. Capabilities, pricing, and features change often — always verify against the vendor's current official documentation. Where a third-party offering is the stronger choice, we say so plainly.

## 1. High-Level Connectivity Architecture

```mermaid
flowchart TB
    subgraph SAS["🖥️ SAS Environment"]
        SAS_BASE[SAS Base]
        SAS_EG[SAS Enterprise Guide]
        SAS_STUDIO[SAS Studio]
        SAS_VIYA[SAS Viya]
    end

    subgraph Drivers["🔌 Connection Layer"]
        ODBC[ODBC Driver 18+]
        OLEDB[OLE DB Driver]
    end

    subgraph Auth["🔐 Authentication"]
        ENTRA[Microsoft Entra ID]
        INTERACTIVE[Interactive<br/>Browser Login]
        SPN[Service Principal<br/>Client ID + Secret]
        MSI[Managed Identity<br/>Azure-Hosted]
    end

    subgraph Fabric["☁️ Microsoft Fabric"]
        LH_SQL[(Lakehouse<br/>SQL Endpoint<br/>Read-Only)]
        WH[(Data Warehouse<br/>Read/Write)]
    end

    SAS_BASE --> ODBC
    SAS_BASE --> OLEDB
    SAS_EG --> ODBC
    SAS_STUDIO --> ODBC
    SAS_VIYA --> ODBC

    ODBC --> ENTRA
    OLEDB --> ENTRA

    ENTRA --> INTERACTIVE
    ENTRA --> SPN
    ENTRA --> MSI

    INTERACTIVE --> LH_SQL
    INTERACTIVE --> WH
    SPN --> LH_SQL
    SPN --> WH
    MSI --> LH_SQL
    MSI --> WH

    style SAS fill:#1d4ed8,color:#fff
    style Auth fill:#059669,color:#fff
    style Fabric fill:#7c3aed,color:#fff
```

---

## 2. Authentication Flow Diagrams

### Interactive Authentication

```mermaid
sequenceDiagram
    participant SAS as SAS Application
    participant ODBC as ODBC Driver
    participant Browser as Web Browser
    participant Entra as Microsoft Entra ID
    participant Fabric as Microsoft Fabric

    SAS->>ODBC: LIBNAME with ActiveDirectoryInteractive
    ODBC->>Browser: Open login.microsoftonline.com
    Browser->>Entra: User enters credentials
    Entra->>Entra: Validate + MFA (if required)
    Entra->>Browser: Return authorization code
    Browser->>ODBC: Pass auth code
    ODBC->>Entra: Exchange for access token
    Entra-->>ODBC: Access token
    ODBC->>Fabric: Connect with token
    Fabric-->>ODBC: Connection established
    ODBC-->>SAS: LIBNAME assigned successfully

    Note over SAS,Fabric: Connection ready for queries
```

### Service Principal Authentication

```mermaid
sequenceDiagram
    participant SAS as SAS Batch Job
    participant ENV as Environment
    participant ODBC as ODBC Driver
    participant Entra as Microsoft Entra ID
    participant Fabric as Microsoft Fabric

    SAS->>ENV: Read FABRIC_CLIENT_ID
    ENV-->>SAS: Client ID
    SAS->>ENV: Read FABRIC_CLIENT_SECRET
    ENV-->>SAS: Client Secret

    SAS->>ODBC: LIBNAME with credentials
    ODBC->>Entra: Request token (client credentials flow)
    Entra->>Entra: Validate client ID + secret
    Entra-->>ODBC: Access token
    ODBC->>Fabric: Connect with token
    Fabric-->>ODBC: Connection established
    ODBC-->>SAS: LIBNAME assigned

    Note over SAS,Fabric: Automated job can now run
```

---

## 3. Data Flow Patterns

### Read Pattern (Lakehouse → SAS)

```mermaid
flowchart LR
    subgraph Fabric["Microsoft Fabric"]
        GOLD[(Gold Layer<br/>Delta Tables)]
        SQL_EP[SQL Analytics<br/>Endpoint]
    end

    subgraph Network["Network"]
        TLS[TLS 1.2+<br/>Port 1433]
    end

    subgraph SAS["SAS Environment"]
        LIBNAME[LIBNAME fabric ODBC]
        DATASET[work.analysis]
        PROC[PROC SQL /<br/>DATA Step]
    end

    GOLD --> SQL_EP
    SQL_EP -->|Read-Only| TLS
    TLS --> LIBNAME
    LIBNAME --> PROC
    PROC --> DATASET

    style Fabric fill:#7c3aed,color:#fff
    style SAS fill:#1d4ed8,color:#fff
```

### Write Pattern (SAS → Warehouse)

```mermaid
flowchart LR
    subgraph SAS["SAS Environment"]
        WORK[work.predictions]
        LIBNAME[LIBNAME output ODBC]
    end

    subgraph Network["Network"]
        TLS[TLS 1.2+<br/>Port 1433]
    end

    subgraph Fabric["Microsoft Fabric"]
        WH[(Data Warehouse)]
        TABLE[sas_output.table]
    end

    WORK --> LIBNAME
    LIBNAME -->|Bulk Insert| TLS
    TLS --> WH
    WH --> TABLE

    style Fabric fill:#7c3aed,color:#fff
    style SAS fill:#1d4ed8,color:#fff
```

---

## 4. Casino Analytics Workflow

```mermaid
flowchart TB
    subgraph Fabric["Microsoft Fabric Data Platform"]
        BRONZE[(Bronze<br/>Raw Data)]
        SILVER[(Silver<br/>Cleansed)]
        GOLD[(Gold<br/>Analytics)]
        WH[(Warehouse<br/>SAS Output)]
    end

    subgraph SAS["SAS Analytics"]
        READ[1. Read Gold Data<br/>LIBNAME ODBC]
        FEATURE[2. Feature Engineering<br/>DATA Step]
        MODEL[3. Build Model<br/>PROC LOGISTIC]
        SCORE[4. Score Players<br/>PROC LOGISTIC SCORE]
        WRITE[5. Write Results<br/>DATA output.table]
    end

    subgraph Reports["Outputs"]
        PRED[Churn<br/>Predictions]
        CTR[CTR<br/>Report]
        SAR[SAR<br/>Candidates]
    end

    BRONZE --> SILVER --> GOLD
    GOLD -->|ODBC Read| READ
    READ --> FEATURE --> MODEL --> SCORE --> WRITE
    WRITE -->|ODBC Write| WH
    WH --> PRED
    WH --> CTR
    WH --> SAR

    style Fabric fill:#7c3aed,color:#fff
    style SAS fill:#1d4ed8,color:#fff
    style Reports fill:#059669,color:#fff
```

---

## 5. LIBNAME Configuration Matrix

```mermaid
flowchart TD
    START([Need Fabric<br/>Connection]) --> Q1{Read or<br/>Write?}

    Q1 -->|Read Only| LAKEHOUSE[Use Lakehouse<br/>SQL Endpoint]
    Q1 -->|Read/Write| WAREHOUSE[Use Data<br/>Warehouse]

    LAKEHOUSE --> Q2{Interactive<br/>or Batch?}
    WAREHOUSE --> Q2

    Q2 -->|Interactive| INTERACTIVE[ActiveDirectory<br/>Interactive]
    Q2 -->|Batch Job| SERVICE_PRINCIPAL[ActiveDirectory<br/>ServicePrincipal]

    INTERACTIVE --> CONFIG1[LIBNAME fabric ODBC<br/>DSN='Fabric_LH'<br/>Auth=Interactive]
    SERVICE_PRINCIPAL --> CONFIG2[LIBNAME fabric ODBC<br/>NOPROMPT=...<br/>Auth=ServicePrincipal]

    CONFIG1 --> CONNECT([Connection<br/>Established])
    CONFIG2 --> CONNECT

    style LAKEHOUSE fill:#10b981,color:#fff
    style WAREHOUSE fill:#3b82f6,color:#fff
    style CONNECT fill:#22c55e,color:#fff
```

---

## 6. Pass-Through SQL Decision

```mermaid
flowchart TD
    START([SAS Query]) --> Q1{Simple<br/>SELECT?}

    Q1 -->|Yes| Q2{Filters<br/>Applied?}
    Q1 -->|No| PASSTHROUGH[Use Pass-Through<br/>SQL]

    Q2 -->|SAS WHERE| IMPLICIT[Implicit<br/>Pass-Through<br/>May Work]
    Q2 -->|No Filters| DIRECT[Direct<br/>Table Read]

    IMPLICIT --> CHECK{Check<br/>SASTRACE}
    CHECK -->|Optimized| OK([Good<br/>Performance])
    CHECK -->|Not Optimized| PASSTHROUGH

    PASSTHROUGH --> EXPLICIT[PROC SQL<br/>CONNECT USING<br/>CONNECTION TO]
    EXPLICIT --> OK

    DIRECT --> OK

    style PASSTHROUGH fill:#f59e0b,color:#fff
    style OK fill:#22c55e,color:#fff
```

---

## 7. Troubleshooting Flowchart

```mermaid
flowchart TD
    ERROR([Connection<br/>Error]) --> E1{Driver<br/>Found?}

    E1 -->|No| FIX1[Install ODBC<br/>Driver 18+]
    E1 -->|Yes| E2{DSN<br/>Configured?}

    E2 -->|No| FIX2[Create DSN in<br/>ODBC Administrator]
    E2 -->|Yes| E3{Network<br/>Access?}

    E3 -->|No| FIX3[Open Port 1433<br/>Check Firewall]
    E3 -->|Yes| E4{Auth<br/>Failed?}

    E4 -->|Yes| FIX4[Verify Credentials<br/>Check Workspace Access]
    E4 -->|No| E5{Database<br/>Found?}

    E5 -->|No| FIX5[Verify Database Name<br/>Case Sensitive]
    E5 -->|Yes| E6{Permission<br/>Denied?}

    E6 -->|Write Error| FIX6[Use Warehouse<br/>Not Lakehouse]
    E6 -->|Read Error| FIX7[Check Schema Name<br/>Grant SELECT]

    FIX1 --> RETRY([Retry<br/>Connection])
    FIX2 --> RETRY
    FIX3 --> RETRY
    FIX4 --> RETRY
    FIX5 --> RETRY
    FIX6 --> RETRY
    FIX7 --> RETRY

    style ERROR fill:#ef4444,color:#fff
    style RETRY fill:#22c55e,color:#fff
```

---

## 8. Performance Optimization

```mermaid
flowchart LR
    subgraph Slow["❌ Slow Pattern"]
        S1[Read All Rows]
        S2[Filter in SAS]
        S3[Process Subset]
    end

    subgraph Fast["✅ Fast Pattern"]
        F1[Pass-Through SQL<br/>with WHERE]
        F2[Read Subset Only]
        F3[Process in SAS]
    end

    S1 --> S2 --> S3
    F1 --> F2 --> F3

    style Slow fill:#ef4444,color:#fff
    style Fast fill:#22c55e,color:#fff
```

### Performance Settings

```
┌─────────────────────────────────────────────────────────────┐
│              SAS LIBNAME Performance Options                │
├─────────────────────┬───────────────────────────────────────┤
│     Option          │           Recommendation              │
├─────────────────────┼───────────────────────────────────────┤
│ READBUFF=           │ 10000-50000 (rows per fetch)          │
│ INSERTBUFF=         │ 10000 (rows per insert batch)         │
│ DBCOMMIT=           │ 0 (commit after all rows)             │
│ BULKLOAD=           │ YES (enable bulk operations)          │
│ DIRECT_SQL=         │ ALLOW (enable pass-through)           │
│ PRESERVE_COL_NAMES= │ YES (keep original names)             │
│ PRESERVE_TAB_NAMES= │ YES (keep original names)             │
└─────────────────────┴───────────────────────────────────────┘
```

---

## 9. Security Architecture

```mermaid
flowchart TB
    subgraph OnPrem["On-Premises"]
        SAS[SAS Server]
        ENV[Environment<br/>Variables]
        KV[Credential<br/>Store]
    end

    subgraph Azure["Azure"]
        ENTRA[Microsoft<br/>Entra ID]
        FABRIC[Microsoft<br/>Fabric]
        RBAC[Workspace<br/>RBAC]
    end

    subgraph Security["Security Controls"]
        TLS[TLS 1.2+<br/>Encryption]
        AUDIT[Entra ID<br/>Audit Logs]
        ROTATE[Secret<br/>Rotation]
    end

    SAS --> ENV
    ENV --> KV
    KV -->|Credentials| TLS
    TLS --> ENTRA
    ENTRA --> RBAC
    RBAC --> FABRIC

    ENTRA --> AUDIT
    KV --> ROTATE

    style Security fill:#059669,color:#fff
```

---

## 10. Complete Integration Example

```mermaid
sequenceDiagram
    participant Scheduler as Job Scheduler
    participant SAS as SAS Server
    participant Fabric as Microsoft Fabric
    participant Users as Business Users

    Note over Scheduler,Users: Daily Analytics Pipeline

    Scheduler->>SAS: Trigger nightly job
    SAS->>SAS: Load environment credentials
    SAS->>Fabric: Connect via Service Principal

    SAS->>Fabric: Read Gold player data
    Fabric-->>SAS: Return 100K player records

    SAS->>SAS: Feature engineering
    SAS->>SAS: Apply churn model
    SAS->>SAS: Generate predictions

    SAS->>Fabric: Write to Warehouse
    Note over Fabric: sas_output.churn_predictions

    SAS->>SAS: Generate CTR report
    SAS->>Fabric: Write compliance data

    SAS->>SAS: Disconnect

    Fabric->>Users: Refresh Power BI reports
    Users->>Users: Review analytics

    Note over Scheduler,Users: Pipeline complete
```
