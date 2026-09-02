---
hero: assets/heroes/reference.svg
hero_alt: Reference — Glossary
type: reference
---
# 📖 Glossary

> **Last Updated**: 2026-04-15 | **Version**: 2.0
> **Status**: ✅ Final | **Maintainer**: Documentation Team

<div align="center" markdown>

![Category](https://img.shields.io/badge/Category-Reference-purple?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-April_2026-blue?style=for-the-badge)

</div>

!!! info "Third-party references — publicly sourced, good-faith comparison"
    This page references non-Microsoft products and services. That information is drawn from each vendor's **publicly available documentation** and is offered for honest, good-faith comparison only. This is a personal project written from a Microsoft Fabric and Azure perspective; it does **not** claim expertise in, or authority over, any third-party product, and nothing here is an official statement by, or endorsed by, those vendors. Capabilities, pricing, and features change often — always verify against the vendor's current official documentation. Where a third-party offering is the stronger choice, we say so plainly.

---

## 🔷 Microsoft Fabric Terms

| Term | Definition | Category | Related Terms |
|------|------------|----------|---------------|
| **Capacity** | A dedicated pool of compute and storage resources in Microsoft Fabric, measured in Capacity Units (CUs). | Infrastructure | SKU, F-Series, Pause |
| **Dataflows Gen2** | Low-code data integration tool for extracting, transforming, and loading data with visual interface and Power Query. | Data Integration | ETL, Power Query, Pipeline |
| **Delta Lake** | Open-source storage layer that provides ACID transactions, scalable metadata handling, and time travel on data lakes. | Storage | Parquet, ACID, Time Travel |
| **Direct Lake** | Query mode enabling Power BI to directly query data from OneLake without importing or using DirectQuery, providing sub-second performance. | Analytics | Power BI, Semantic Model, OneLake |
| **Eventhouse** | Real-time analytics database optimized for streaming and time-series data using KQL (Kusto Query Language). | Analytics | KQL, Real-Time Intelligence, Kusto |
| **Eventstream** | Real-time data ingestion and routing service for streaming data, compatible with Apache Kafka protocol. | Streaming | Kafka, Real-Time, Streaming |
| **F-Series** | Fabric capacity SKU naming convention (F2, F4, F8, F16, F32, F64, F128, etc.), where number represents capacity units. | Infrastructure | Capacity, SKU, Scaling |
| **Fabric API for GraphQL** | GraphQL-based API layer for querying Fabric data with a unified interface. | API | GraphQL, REST, API |
| **KQL** | Kusto Query Language - SQL-like query language optimized for real-time analytics and log/telemetry data. | Query Language | Kusto, Eventhouse, ADX |
| **Lakehouse** | Combined data lake and data warehouse architecture providing file storage (Parquet/Delta) and SQL analytics. | Architecture | Data Lake, Data Warehouse, OneLake |
| **Microsoft Purview** | Data governance platform providing data catalog, lineage tracking, classification, and compliance. | Governance | Data Catalog, Lineage, Classification |
| **Mirroring** | Near real-time replication of data from external databases (Azure SQL, Snowflake, Cosmos DB) into Fabric. | Data Integration | Replication, CDC, Synchronization |
| **Notebook** | Interactive development environment supporting PySpark, Scala, SQL, and R for data transformation and exploration. | Development | PySpark, Jupyter, Apache Spark |
| **OneLake** | Unified data lake foundation for Microsoft Fabric, providing a single namespace for all organizational data. | Storage | Data Lake, ADLS Gen2, Delta Lake |
| **Pipeline** | Orchestration tool for scheduling and coordinating data workflows across Fabric items (similar to Azure Data Factory). | Orchestration | ADF, Workflow, Scheduling |
| **Semantic Model** | Business-oriented data model (formerly "dataset") defining relationships, measures, and calculations for BI reporting. | Analytics | Dataset, Power BI, DAX |
| **Shortcuts** | Virtual folders providing access to external data sources (ADLS, S3, Dataverse) without data duplication. | Data Integration | Mount Point, External Table, Virtual |
| **Warehouse** | SQL-based analytics engine in Fabric optimized for structured data and T-SQL queries. | Analytics | SQL Pool, T-SQL, DW |
| **Workspace** | Collaboration space containing Fabric items (lakehouses, notebooks, pipelines, reports) with shared access controls. | Organization | Container, Project, Folder |

---

## 🏛️ Medallion Architecture

| Term | Definition | Category | Related Terms |
|------|------------|----------|---------------|
| **Bronze Layer** | Initial ingestion layer storing raw, unprocessed data in its original format for auditability and reprocessing. | Data Layer | Raw, Landing Zone, Source |
| **Cleansing** | Process of fixing data quality issues such as nulls, duplicates, and invalid values during Bronze-to-Silver transformation. | Transformation | Validation, Enrichment, Quality |
| **Data Quality** | Measures ensuring data is accurate, complete, consistent, timely, and valid according to business rules. | Quality | Validation, Great Expectations, Rules |
| **Enrichment** | Adding contextual information to data (lookups, calculations, derived columns) during Silver layer processing. | Transformation | Augmentation, Enhancement, Joining |
| **Gold Layer** | Final consumption layer containing aggregated, business-ready data optimized for reporting and analytics. | Data Layer | Curated, Business, Consumption |
| **Incremental Load** | Processing only new or changed records since the last pipeline run, rather than full data refresh. | Data Processing | Delta Load, CDC, Watermark |
| **Medallion Pattern** | Three-tier data architecture pattern (Bronze → Silver → Gold) organizing data by refinement level. | Architecture | Multi-hop, Layered, Progressive |
| **Schema-on-Read** | Approach where data structure is interpreted when reading (Bronze), allowing flexible ingestion of varied formats. | Data Pattern | Flexible Schema, Late Binding |
| **Schema-on-Write** | Approach enforcing data structure during ingestion (Silver/Gold), ensuring consistency and quality. | Data Pattern | Fixed Schema, Early Binding |
| **Silver Layer** | Intermediate layer with cleansed, validated, and conformed data following business rules and standards. | Data Layer | Cleansed, Validated, Conformed |
| **Star Schema** | Dimensional modeling pattern with central fact tables surrounded by dimension tables, common in Gold layer. | Data Modeling | Fact Table, Dimension, Kimball |
| **Time Travel** | Delta Lake capability to query data as it existed at a previous point in time using snapshots. | Feature | Versioning, Snapshot, History |
| **Watermark** | Timestamp or sequence number tracking the last successfully processed record for incremental loads. | Data Processing | Checkpoint, High Water Mark, Bookmark |

---

## 🎰 Casino/Gaming Industry Terms

| Term | Definition | Category | Related Terms |
|------|------------|----------|---------------|
| **Cage** | Casino cashier area where players exchange chips for cash, cash checks, and perform financial transactions. | Operations | Cashier, Vault, Till |
| **Coin-In** | Total amount of money wagered on slot machines, primary metric for slot machine activity. | Metric | Wager, Handle, Theo |
| **Coin-Out** | Total amount paid out by slot machines to players (wins, cashouts). | Metric | Payout, Winnings |
| **Comp** | Complimentary service or item (room, food, beverage) given to players based on their gaming activity. | Player Rewards | Freeplay, Perk, Benefit |
| **CTR** | Currency Transaction Report - mandatory filing for cash transactions exceeding $10,000 in a gaming day. | Compliance | FinCEN, BSA, 8300 |
| **Drop** | Amount of cash and chips placed into table game drop boxes or slot machine bill validators. | Metric | Handle, Revenue, Cash In |
| **Fill** | Transfer of chips or cash from the cage to a gaming table to replenish the table's chip bank. | Operations | Chip Fill, Replenishment |
| **Floor** | Physical casino gaming area containing slot machines, table games, and related amenities. | Operations | Gaming Floor, Casino Floor |
| **Hold** | Percentage of money wagered that the casino retains as revenue (Handle - Payout = Hold). | Metric | Win, House Edge, Revenue |
| **Jackpot** | Large payout on a slot machine, typically requiring hand-pay and tax documentation (W-2G). | Event | Hand Pay, Taxable Win, Big Win |
| **Meter** | Electronic counter on slot machine tracking coin-in, coin-out, jackpots, games played, and other statistics. | Technology | Counter, Register, Accounting |
| **MICS** | Minimum Internal Control Standards - regulatory framework defining casino operational controls. | Compliance | NIGC MICS, Controls, Standards |
| **Par Sheet** | Theoretical probability and payout schedule for a slot machine showing expected hold percentage. | Configuration | Paytable, Math, RTP |
| **Pit** | Area on casino floor containing a group of table games supervised by a pit manager. | Operations | Table Games Area, Pit Boss |
| **Player Club** | Casino loyalty program tracking player activity and awarding points, comps, and benefits. | Program | Loyalty, Rewards, Members |
| **SAR** | Suspicious Activity Report - mandatory filing for potentially fraudulent or suspicious transactions. | Compliance | FinCEN, AML, BSA |
| **SAS** | Slot Accounting System - protocol enabling communication between slot machines and casino management systems. | Technology | Protocol, Interface, G2S |
| **Slot Machine** | Electronic gaming device (EGM) where players wager on games of chance, tracked via SAS telemetry. | Equipment | EGM, VGT, Gaming Device |
| **Table Game** | Live dealer casino games (blackjack, roulette, craps, baccarat) played on physical tables. | Gaming | Pit Games, Live Games, Cards |
| **Theo** | Theoretical Win - expected casino revenue calculated using actual play volume and mathematical house edge. | Metric | Expected Win, Theoretical |
| **Voucher** | Ticket printed from slot machine representing cash value, also called Ticket-In-Ticket-Out (TITO). | Technology | TITO, Ticket, Cashout |
| **W-2G** | IRS tax form documenting gambling winnings exceeding reporting thresholds ($1,200+ slots, $600+ keno, $5,000+ poker, etc.). | Tax | Tax Form, Reportable Win, 1099 |

---

## ⚙️ Data Engineering Terms

| Term | Definition | Category | Related Terms |
|------|------------|----------|---------------|
| **ACID** | Atomicity, Consistency, Isolation, Durability - properties ensuring reliable database transactions. | Concept | Transaction, Reliability, Delta Lake |
| **Apache Spark** | Distributed computing framework for large-scale data processing, foundation of Fabric notebooks. | Framework | PySpark, DataFrame, RDD |
| **Batch Processing** | Processing data in scheduled groups rather than continuously, typically nightly or hourly. | Pattern | Scheduled, Bulk, Job |
| **CDC** | Change Data Capture - technique tracking inserts, updates, and deletes in source systems for incremental processing. | Pattern | Delta, Incremental, Mirroring |
| **Columnar Storage** | File format organizing data by columns rather than rows (Parquet, ORC) for efficient analytics. | Storage | Parquet, ORC, Compression |
| **Data Lineage** | Visual map showing data origins, transformations, and consumption paths across systems. | Governance | Provenance, Traceability, Purview |
| **Data Lake** | Centralized repository storing structured and unstructured data at any scale in raw format. | Architecture | ADLS, Storage, Raw Data |
| **Data Pipeline** | Automated workflow moving and transforming data from sources to destinations. | Orchestration | ETL, Workflow, Pipeline |
| **Data Quality** | Measures of data fitness (accuracy, completeness, consistency, timeliness, validity) for intended use. | Quality | Validation, DQ, Cleansing |
| **Data Warehouse** | Structured repository optimized for analytics queries, typically using dimensional modeling. | Architecture | DW, EDW, OLAP |
| **DataFrame** | Distributed collection of data organized into named columns, primary abstraction in Apache Spark. | Concept | Dataset, Table, RDD |
| **Deduplication** | Process of identifying and removing duplicate records, common in Silver layer transformations. | Transformation | Distinct, Unique, Merge |
| **Delta Format** | Open-source storage format providing ACID transactions and time travel on Parquet files. | Format | Delta Lake, Parquet, Transaction Log |
| **Dimension Table** | Reference table in star schema containing descriptive attributes (Customer, Product, Date). | Data Modeling | Lookup, Reference, SCD |
| **ELT** | Extract, Load, Transform - loading raw data first, then transforming within target system (modern pattern). | Pattern | Data Integration, Transformation |
| **ETL** | Extract, Transform, Load - transforming data before loading into target system (traditional pattern). | Pattern | Data Integration, Dataflow |
| **Fact Table** | Central table in star schema containing measurable business events and foreign keys to dimensions. | Data Modeling | Metrics, Measures, Grain |
| **Idempotent** | Operation producing the same result when executed multiple times, critical for reliable pipelines. | Concept | Replayable, Deterministic |
| **Ingestion** | Process of importing data from source systems into data platform (batch or streaming). | Process | Import, Load, Intake |
| **Metadata** | Data about data - schemas, lineage, descriptions, quality scores, and technical properties. | Concept | Catalog, Dictionary, Purview |
| **Orchestration** | Coordination and scheduling of data workflows across multiple systems and dependencies. | Process | Scheduling, Workflow, Pipeline |
| **Parquet** | Open-source columnar file format optimized for analytics, foundation of Delta Lake. | Format | Columnar, Compressed, Apache |
| **Partitioning** | Dividing data into segments (typically by date) for efficient querying and maintenance. | Optimization | Bucketing, Sharding, Segmentation |
| **PySpark** | Python API for Apache Spark, used in Fabric notebooks for distributed data processing. | Language | Python, Spark, DataFrame |
| **Query Optimization** | Techniques improving query performance through caching, partitioning, statistics, and indexing. | Performance | Tuning, Acceleration, Optimization |
| **Real-Time Processing** | Processing data with minimal latency as events occur, typically seconds or less. | Pattern | Streaming, Low-Latency, Live |
| **SCD** | Slowly Changing Dimension - technique tracking historical changes in dimension tables (Type 0, 1, 2, 3, 4, 6). | Data Modeling | History, Versioning, Temporal |
| **Schema Evolution** | Ability to modify data structure (add/remove columns) while maintaining compatibility with existing data. | Feature | Schema Change, Migration, Versioning |
| **Streaming** | Continuous processing of data as it arrives in real-time, using technologies like Eventstreams or Kafka. | Pattern | Real-Time, Continuous, Event-Driven |
| **Surrogate Key** | Artificial primary key (typically integer) generated during ETL, independent of business data. | Data Modeling | Synthetic Key, ID, Sequence |
| **Transformation** | Process of converting data from source format to target format, including cleansing and enrichment. | Process | Mapping, Conversion, Processing |
| **Upsert** | Operation combining insert and update - insert if record doesn't exist, update if it does. | Operation | Merge, Insert-Update, MERGE |

---

## 📋 Compliance & Regulatory Terms

| Term | Definition | Category | Related Terms |
|------|------------|----------|---------------|
| **AML** | Anti-Money Laundering - regulations requiring casinos to detect and report suspicious financial activities. | Regulation | BSA, SAR, CTR |
| **BSA** | Bank Secrecy Act - U.S. law requiring financial institutions (including casinos) to report large cash transactions. | Regulation | FinCEN, AML, 31 CFR |
| **Compliance** | Adherence to laws, regulations, standards, and internal policies governing casino operations. | Concept | Regulatory, Controls, Governance |
| **FinCEN** | Financial Crimes Enforcement Network - U.S. Treasury bureau enforcing BSA and AML regulations. | Agency | BSA, AML, Federal |
| **GDPR** | General Data Protection Regulation - EU privacy law applicable to player data if operating in Europe. | Regulation | Privacy, PII, Data Protection |
| **HIPAA** | Health Insurance Portability and Accountability Act - protects health information, relevant for tribal healthcare. | Regulation | PHI, Privacy, Healthcare |
| **IRS** | Internal Revenue Service - U.S. tax authority requiring W-2G reporting for gambling winnings. | Agency | Tax, W-2G, Federal |
| **KYC** | Know Your Customer - process of verifying player identity to prevent fraud and comply with AML regulations. | Process | Identity, Verification, AML |
| **MICS** | Minimum Internal Control Standards - NIGC regulations defining required internal controls for tribal casinos. | Regulation | NIGC, Controls, Standards |
| **NIGC** | National Indian Gaming Commission - federal agency regulating gaming on tribal lands. | Agency | Tribal Gaming, Federal, MICS |
| **PCI-DSS** | Payment Card Industry Data Security Standard - requirements for protecting credit card data. | Standard | Card Security, Payment, Compliance |
| **PII** | Personally Identifiable Information - data that can identify an individual (SSN, name, address, etc.). | Concept | Privacy, Sensitive, Personal Data |
| **PHI** | Protected Health Information - individually identifiable health information protected under HIPAA. | Concept | Healthcare, Privacy, HIPAA |
| **Reportable Transaction** | Financial transaction meeting thresholds requiring regulatory filing (CTR ≥$10,000, W-2G ≥$1,200 slots). | Concept | Filing, Threshold, Reporting |
| **Retention Policy** | Rules defining how long data must be kept before deletion, typically 5-7 years for gaming records. | Policy | Data Retention, Archival, Lifecycle |
| **SMTF** | Suspicious Multiple Transaction Form - tracks aggregate cash transactions below CTR threshold from single patron. | Form | Structuring, Pattern, BSA |
| **Structuring** | Illegal practice of breaking large transactions into smaller amounts to avoid CTR reporting requirements. | Violation | Smurfing, Avoidance, SAR |
| **W-2G** | IRS form documenting gambling winnings exceeding reporting thresholds (varies by game type). | Form | Tax, Reportable, Jackpot |

---

## ☁️ Azure/Cloud Terms

| Term | Definition | Category | Related Terms |
|------|------------|----------|---------------|
| **ADLS Gen2** | Azure Data Lake Storage Gen2 - hierarchical namespace storage optimized for big data analytics. | Storage | OneLake, Data Lake, Blob Storage |
| **ARM** | Azure Resource Manager - deployment and management service providing infrastructure as code capabilities. | IaC | Template, Deployment, Bicep |
| **Azure AD** | Azure Active Directory (now Microsoft Entra ID) - cloud identity and access management service. | Identity | Entra ID, IAM, SSO |
| **Bicep** | Domain-specific language for deploying Azure resources declaratively, transpiles to ARM templates. | IaC | ARM, Template, Infrastructure |
| **Capacity Unit (CU)** | Unit of compute and storage capacity in Microsoft Fabric, determines performance and concurrency. | Measurement | CU, Capacity, SKU |
| **Conditional Access** | Microsoft Entra ID feature controlling access based on conditions (location, device, risk level). | Security | MFA, Policy, Zero Trust |
| **Defender for Cloud** | Azure security posture management and threat protection service. | Security | Security Center, CSPM, CWPP |
| **Key Vault** | Azure service for securely storing and managing secrets, certificates, and encryption keys. | Security | Secrets, Keys, Certificates |
| **Managed Identity** | Microsoft Entra ID identity for Azure resources, eliminating need for credentials in code. | Identity | Service Principal, MSI, Authentication |
| **MFA** | Multi-Factor Authentication - requiring multiple verification methods to authenticate users. | Security | 2FA, Authentication, Microsoft Entra ID |
| **NSG** | Network Security Group - firewall rules controlling inbound/outbound traffic to Azure resources. | Networking | Firewall, Rules, Security |
| **PIM** | Privileged Identity Management - Microsoft Entra ID feature providing just-in-time admin access. | Security | JIT, Admin, Elevation |
| **Private Endpoint** | Network interface connecting privately to Azure services over private IP address. | Networking | Private Link, VNet, Connectivity |
| **RBAC** | Role-Based Access Control - authorization system assigning permissions based on roles. | Security | Permissions, IAM, Authorization |
| **Region** | Azure geographic area containing one or more datacenters (e.g., East US, West Europe). | Geography | Location, Datacenter, Availability |
| **Resource Group** | Logical container grouping related Azure resources for management and organization. | Organization | RG, Container, Logical Grouping |
| **Sentinel** | Azure-native SIEM (Security Information and Event Management) and SOAR solution. | Security | SIEM, SOAR, Security Analytics |
| **SKU** | Stock Keeping Unit - tier or size variant of Azure service (Basic, Standard, Premium, F64, etc.). | Pricing | Tier, Size, Capacity |
| **Subscription** | Azure billing and management boundary containing resource groups and resources. | Management | Billing, Tenant, Account |
| **Tenant** | Dedicated Microsoft Entra ID instance representing an organization. | Identity | Directory, Organization, Microsoft Entra ID |
| **VNet** | Virtual Network - isolated network environment in Azure for deploying resources. | Networking | Network, Subnet, Virtual Network |

---

## 🔐 Security Terms

| Term | Definition | Category | Related Terms |
|------|------------|----------|---------------|
| **Authentication** | Process of verifying identity (who you are) using credentials, tokens, or biometrics. | Concept | Login, Identity, Microsoft Entra ID |
| **Authorization** | Process of determining permissions (what you can do) after authentication. | Concept | RBAC, Permissions, Access Control |
| **Classification** | Tagging data by sensitivity level (Public, Internal, Confidential, Restricted) for governance. | Governance | Labeling, Sensitivity, Purview |
| **Data Masking** | Technique hiding sensitive data by replacing characters (e.g., SSN: ***-**-1234). | Protection | Obfuscation, Redaction, Privacy |
| **DDoS Protection** | Azure service mitigating distributed denial of service attacks. | Security | Attack Protection, Availability |
| **Defense in Depth** | Security strategy using multiple layers of protection rather than relying on single control. | Strategy | Layered Security, Multi-Layer |
| **Encryption at Rest** | Protecting stored data using encryption (AES-256), automatically enabled in Azure Storage. | Protection | Storage Encryption, AES, Keys |
| **Encryption in Transit** | Protecting data during transmission using TLS/SSL protocols. | Protection | TLS, SSL, HTTPS |
| **Just-In-Time (JIT)** | Providing temporary elevated access only when needed, reducing attack surface. | Pattern | PIM, Temporary, Time-Bound |
| **Least Privilege** | Security principle of granting minimum permissions necessary to perform job function. | Principle | Minimal Access, RBAC, Security |
| **Object-Level Security** | Controlling access to specific data objects (tables, views, folders) within workspace. | Access Control | Permissions, RBAC, Authorization |
| **Row-Level Security (RLS)** | Filtering data rows based on user identity, common in Power BI semantic models. | Access Control | Data Filtering, Security, Power BI |
| **Security Principal** | Identity that can be authenticated and authorized (user, group, service principal, managed identity). | Identity | User, Group, Service Account |
| **Service Principal** | Identity used by applications and services to access Azure resources programmatically. | Identity | App Identity, Service Account, Auth |
| **SSO** | Single Sign-On - authentication allowing one set of credentials to access multiple systems. | Authentication | Microsoft Entra ID, Federation, Login |
| **TLS** | Transport Layer Security - cryptographic protocol for secure network communication. | Protocol | SSL, HTTPS, Encryption |
| **Zero Trust** | Security model assuming breach and verifying every access request regardless of location. | Strategy | Never Trust, Always Verify, Modern Security |

---

## 📊 Analytics & BI Terms

| Term | Definition | Category | Related Terms |
|------|------------|----------|---------------|
| **Aggregation** | Summarizing detailed data into higher-level metrics (SUM, AVG, COUNT, MAX, MIN). | Calculation | Summary, Rollup, Grouping |
| **Calculated Column** | Column defined by DAX formula, computed during data refresh and stored in model. | Power BI | DAX, Column, Computed |
| **Calculated Table** | Entire table defined by DAX expression, created during data refresh. | Power BI | DAX, Table, Virtual |
| **DAX** | Data Analysis Expressions - formula language for Power BI calculations and aggregations. | Language | Power BI, Measure, Formula |
| **Dataset** | Former term for Power BI semantic model containing data, relationships, and calculations. | Power BI | Semantic Model, Data Model, PBIX |
| **Dimension** | Descriptive attributes providing context for measures (Customer, Product, Time, Location). | Concept | Attribute, Lookup, Qualifier |
| **DirectQuery** | Power BI query mode sending queries to source system in real-time without importing data. | Power BI | Live Connection, Query Mode |
| **Drill-Down** | Navigating from summary to detailed data (Year → Quarter → Month → Day). | Interaction | Hierarchy, Navigation, Detail |
| **Drill-Through** | Jumping from one report page to related detail page, passing filter context. | Interaction | Navigation, Detail, Filter |
| **Import Mode** | Power BI query mode loading entire dataset into memory for fast performance. | Power BI | In-Memory, Cache, Data Model |
| **KPI** | Key Performance Indicator - critical metric measuring business success (Revenue, Utilization, Hold %). | Metric | Measure, Target, Performance |
| **Measure** | DAX calculation evaluated at query time based on filter context, not stored in model. | Power BI | DAX, Calculation, Dynamic |
| **OLAP** | Online Analytical Processing - multidimensional database technology for complex analytics queries. | Concept | Cube, MDX, Analysis Services |
| **OLTP** | Online Transaction Processing - database optimized for transactional operations (insert, update, delete). | Concept | Transactional, Operational, Source System |
| **Power BI** | Microsoft business intelligence platform for data visualization and report development. | Tool | BI, Visualization, Dashboard |
| **Power Query** | Data transformation tool using M language, available in Power BI, Excel, and Dataflows Gen2. | Tool | M, ETL, Transformation |
| **Refresh** | Process of updating Power BI dataset with latest data from sources. | Operation | Update, Reload, Sync |
| **Relationship** | Connection between tables defining how they relate (one-to-many, many-to-many). | Data Modeling | Join, Foreign Key, Cardinality |
| **Report** | Collection of visualizations, tables, and charts on one or more pages in Power BI. | Artifact | Dashboard, Visual, PBIX |
| **Slicer** | Visual filter allowing users to interactively filter report data. | Visual | Filter, Parameter, Selection |
| **T-SQL** | Transact-SQL - Microsoft's extension of SQL used in Fabric Warehouses and SQL databases. | Language | SQL, Query, Database |
| **Time Intelligence** | DAX functions for date-based calculations (YTD, MTD, Prior Year, Rolling Average). | Concept | Date Calculation, Period, DAX |
| **Visualization** | Graphical representation of data (chart, graph, map, table) in Power BI reports. | Concept | Visual, Chart, Graph |

---

## 🔗 Quick Reference Links

### Microsoft Documentation

- [Microsoft Fabric Documentation](https://learn.microsoft.com/en-us/fabric/)
- [Power BI Documentation](https://learn.microsoft.com/en-us/power-bi/)
- [Azure Documentation](https://learn.microsoft.com/en-us/azure/)
- [Microsoft Purview Documentation](https://learn.microsoft.com/en-us/purview/)
- [Delta Lake Documentation](https://docs.delta.io/)

### Compliance Resources

- [NIGC Minimum Internal Control Standards (MICS)](https://www.nigc.gov/compliance-enforcement/regulations)
- [FinCEN BSA Requirements](https://www.fincen.gov/resources/statutes-and-regulations/bank-secrecy-act)
- [IRS W-2G Gambling Winnings](https://www.irs.gov/forms-pubs/about-form-w-2-g)
- [PCI-DSS Standards](https://www.pcisecuritystandards.org/)

### Technology References

- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [Bicep Language Reference](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [KQL (Kusto Query Language)](https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/)
- [DAX Function Reference](https://dax.guide/)

---

## 📝 Usage Tips

### Searching This Glossary

1. **Browser Search**: Use `Ctrl+F` (Windows/Linux) or `Cmd+F` (Mac) to search for specific terms
2. **Category Navigation**: Click category links in Table of Contents to jump to specific sections
3. **Related Terms**: Use the "Related Terms" column to discover connected concepts

### Contributing

Found a missing term or see an opportunity for improvement? Please:

1. Open an issue with the term and suggested definition
2. Submit a pull request following our [Contributing Guidelines](CONTRIBUTING.md)
3. Ensure new terms include: Definition, Category, and Related Terms

### Best Practices

- **For New Team Members**: Start with Microsoft Fabric Terms and Medallion Architecture sections
- **For Developers**: Focus on Data Engineering Terms and Azure/Cloud Terms
- **For Compliance Officers**: Review Compliance & Regulatory Terms and Casino/Gaming Terms
- **For Business Users**: Begin with Analytics & BI Terms and Casino/Gaming Industry Terms

---

## 🏛️ Federal Agency Terms

| Term | Definition | Category | Related Terms |
|------|------------|----------|---------------|
| **BLM** | Bureau of Land Management — manages public lands and mineral resources under the Department of the Interior. | Agency | DOI, NPS, FWS |
| **DOI** | Department of the Interior — federal agency managing natural resources, including USGS earthquakes and BLM land use. | Agency | USGS, BLM, NPS, FWS |
| **DOT** | Department of Transportation — federal agency overseeing transportation infrastructure, highways, and aviation. | Agency | FAA, NHTSA |
| **EPA** | Environmental Protection Agency — federal agency protecting human health and the environment through AQI and water quality standards. | Agency | AQI, MCL, TRI |
| **FAA** | Federal Aviation Administration — division of DOT regulating civil aviation, flight operations, and airport safety. | Agency | DOT, FISMA, FedRAMP |
| **FedRAMP** | Federal Risk and Authorization Management Program — standardized security assessment for cloud services used by federal agencies. | Compliance | FISMA, NIST 800-53, ATO |
| **FIPS** | Federal Information Processing Standards — codes identifying US states and counties, used in USDA and Census data. | Standard | State FIPS, County FIPS |
| **FISMA** | Federal Information Security Modernization Act — requires federal agencies to develop and maintain information security programs. | Compliance | FedRAMP, NIST 800-53 |
| **FSIS** | Food Safety and Inspection Service — USDA division responsible for food safety recalls and inspections. | Agency | USDA, NASS |
| **HHS** | Department of Health and Human Services — oversees IHS and administers HIPAA regulations. | Agency | IHS, HIPAA |
| **HIPAA** | Health Insurance Portability and Accountability Act — federal law protecting patient health information. Used in tribal healthcare. | Compliance | PHI, IHS, 42 CFR Part 2 |
| **IHS** | Indian Health Service — HHS agency providing health services to American Indians and Alaska Natives. | Agency | HHS, HIPAA, Tribal Health |
| **MCL** | Maximum Contaminant Level — EPA threshold for allowable contaminant levels in drinking water. | Standard | EPA, Safe Drinking Water Act |
| **NAICS** | North American Industry Classification System — standard codes classifying business establishments, used in SBA loan data. | Standard | SBA, PPP |
| **NASS** | National Agricultural Statistics Service — USDA division providing crop production statistics via QuickStats API. | Agency | USDA, FSIS |
| **NIGC** | National Indian Gaming Commission — federal agency regulating gaming on Indian lands under IGRA. | Agency | MICS, IGRA, Tribal Gaming |
| **NIST 800-53** | National Institute of Standards and Technology Special Publication 800-53 — security and privacy controls for federal information systems. | Standard | FedRAMP, FISMA |
| **NOAA** | National Oceanic and Atmospheric Administration — federal agency providing weather observations, storm events, and climate data. | Agency | NWS, Climate Data Online |
| **PPP** | Paycheck Protection Program — SBA loan program providing forgivable loans to small businesses. | Program | SBA, 7(a) Loans |
| **SBA** | Small Business Administration — federal agency supporting small businesses through loans (PPP, 7(a), Disaster) and SBIR awards. | Agency | PPP, NAICS |
| **TRI** | Toxics Release Inventory — EPA program tracking release of toxic chemicals by industrial facilities. | Program | EPA, AQI |
| **USDA** | United States Department of Agriculture — federal agency overseeing agriculture, food safety, and rural development. | Agency | NASS, FSIS, Crop Production |
| **USGS** | United States Geological Survey — DOI science agency monitoring earthquakes, water resources, and land use. | Agency | DOI, Seismic Data |
| **42 CFR Part 2** | Code of Federal Regulations governing confidentiality of substance use disorder patient records. | Compliance | HIPAA, IHS, Behavioral Health |

---

## 📈 Document History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-01-21 | Initial glossary creation with 150+ terms across 8 categories | Documentation Team |
| 2.0.0 | 2026-03-11 | Added Federal Agency Terms section (24 entries) for Phase 7 expansions | Claude Code |

---

<div align="center" markdown>

**[⬆ Back to Top](#-glossary)**

---

*Last Updated: 2025-01-21 | Questions? See [CONTRIBUTING.md](CONTRIBUTING.md)*

</div>
