# 📋 Microsoft Fabric - Comprehensive Feature Inventory (April 2026)

> **Last Updated**: 2026-04-15 | **Version**: 2.0
> **Status**: ✅ Final | **Maintainer**: Documentation Team

<div align="center" markdown>

![Category](https://img.shields.io/badge/Category-Feature_Inventory-informational?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-April_2026-blue?style=for-the-badge)

</div>

> **Research Date:** April 13, 2026
> **Coverage Period:** July 2025 - April 2026 ("New Fabric Experience" era)
> **Purpose:** Cross-reference against existing codebase for gap analysis

---

!!! info "Third-party references — publicly sourced, good-faith comparison"
    This page references non-Microsoft products and services. That information is drawn from each vendor's **publicly available documentation** and is offered for honest, good-faith comparison only. This is a personal project written from a Microsoft Fabric and Azure perspective; it does **not** claim expertise in, or authority over, any third-party product, and nothing here is an official statement by, or endorsed by, those vendors. Capabilities, pricing, and features change often — always verify against the vendor's current official documentation. Where a third-party offering is the stronger choice, we say so plainly.

---

## 🔧 1. Data Engineering

### Spark Runtime & Compute

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Fabric Runtime 2.0 (Spark 4.0 + Delta Lake 4.0) | Preview | ~Oct 2025 | New runtime with Apache Spark 4.0, Delta Lake 4.0, Python 3.12, upgraded libraries |
| Fabric Spark Applications Comparison | Preview | ~2025 | Compare up to four Spark application runs side by side for performance tuning |
| Fabric Spark Diagnostic Emitter | Preview | Sep 2024 | Collect logs, event logs, and metrics from Spark applications |
| JobInsight Diagnostics Library | Preview | ~2025 | Analyze completed Spark applications via APIs |
| Fabric JDBC Driver | Preview | ~2025 | Java connectivity to Spark SQL with enterprise Entra authentication |
| Fabric ODBC Driver | Preview | ~2025 | ODBC-compatible connectivity to Spark SQL endpoints |
| Spark Connector for SQL databases | Preview | ~2025 | Spark read/write to Azure SQL and Fabric SQL databases |
| Livy REST API | Preview | ~2025 | Submit and execute Spark code on Fabric compute via REST |

### Notebooks

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Fabric Notebook Public APIs | **GA** | Mar 2026 | Programmatic notebook management with full CRUD support |
| Inline code completion (Copilot) | Preview | Jun 2025 | AI-assisted Python/PySpark code completion in notebooks |
| Notebook debug within vscode.dev | Preview | Sep 2024 | Place breakpoints and debug notebook code in browser-based VS Code |
| Fabric Connection inside Notebook | Preview | ~2025 | Create and manage cloud data source connections directly in notebooks |
| MSSQL extension for VS Code Fabric integration | Preview | ~2025 | Connect, query, and manage Fabric SQL databases in VS Code |

### Lakehouse

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Lakehouse Schemas | **GA** | Dec 2025 | Group tables into schemas for better discovery, organization, and access control |
| Lakehouse support for Git integration & deployment pipelines | Preview | ~2025 | Lifecycle management (source control, CI/CD) for Lakehouse items |
| Materialized Lake Views | Preview | Build 2025 | Precomputed, cached query results over OneLake data for fast reads |
| Data Wrangler | **GA** | Pre-2025 | Low-code data exploration and transformation interface in notebooks |

### Shortcuts & Transformations

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Shortcut Transformations | **GA** | Apr 2026 | Automatically convert structured files (CSV, Parquet, JSON) to Delta tables on read |
| Azure Blob Storage shortcut type | Preview | ~2025 | Create OneLake shortcuts to Azure Blob Storage |
| SharePoint and OneDrive shortcut identities | Preview | ~2025 | Workspace identity and service principal auth for SP/OD shortcuts |
| Microsoft Entra service principal support for Amazon S3 Shortcuts | **GA** | Mar 2026 | OIDC-based access to S3 without long-term access keys |

---

## ⚡ 2. Real-Time Intelligence

### Eventstreams

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Eventstream SQL Operator | **GA** | Mar 2026 | SQL-based real-time stream processing with multi-destination writes |
| DeltaFlow Transformation in Eventstream | Preview | Mar 2026 | Transform CDC events into flattened, analytics-ready format |
| Multiple-Schema Inferencing in Eventstream | Preview | ~2025 | Handle multiple data sources with varying schemas in a single eventstream |
| Confluent Schema Registry Support | Preview | ~2025 | Decode schema-encoded streaming data from Confluent Cloud |
| Schema Registry | Preview | ~2025 | Contract-based event schema definition and validation |
| Eventstream connectors for private network streaming | Preview | ~2025 | Secure streaming via Azure virtual network |
| Eventstream Derived Streams (Direct Ingestion mode) | Preview | ~2025 | Ingest from eventstream derived streams directly to Eventhouse |
| Solace PubSub+ Connector for Eventstream | Preview | ~2025 | Connect Fabric Eventstream with Solace PubSub+ |
| Real-Time Intelligence Cribl source | Preview | ~2025 | Real-time data from diverse telemetry sources via Cribl Stream |
| Pass Parameter Values to Fabric Items | Preview | Jul 2025 | Pass values to parameters when activating Fabric items from RTI |

### Eventhouse & KQL

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Eventhouse as Vector Database | Preview | ~2025 | Store and query vector embeddings using dynamic columns, Vector16 encoding, series_cosine_similarity() |
| Entity diagram in Eventhouse KQL database | Preview | ~2025 | Visual exploration of tables, relationships, and data flow |
| Continuous ingestion from Azure Storage to Eventhouse | Preview | ~2025 | Automatically ingest data from Azure Storage into Eventhouse |
| Azure Monitor to Fabric Eventhouse | Preview | ~2025 | Route VM telemetry via Azure Monitor Agent into Eventhouse |
| OpenAI plugins for Eventhouse | Preview | ~2025 | AI Embed Text and Chat Completion plugins for KQL queries |
| Synapse Data Explorer to Eventhouse migration tooling | Preview | ~2025 | Migration assistance from legacy ADX platform |

### Activator & Alerts

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Business Events in Real-Time Intelligence | Preview | Mar 2026 | Generate events from user data functions and notebooks to trigger alerts/workflows |
| Fabric Activator integration in User Data Functions | Preview | ~2025 | Process events from Fabric events and OneLake events |
| MCP remote servers for Activator and Eventhouse | Preview | Mar 2026 | Hosted MCP remote servers for RTI components |
| Anomaly Detection | Preview | ~2025 | No-code interface for tracking changes and unexpected events with automatic model selection |

### Digital Twin Builder

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Digital Twin Builder | Preview | Mar 2026 | Create data-driven, real-time representations of physical entities (buildings, machines, systems) |

### Fabric Maps

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Fabric Maps in Real-Time Intelligence | **GA** | Mar 2026 | Visualize real-time and historical location data on maps |

### Real-Time Dashboards

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Data Series Colors in Real-Time Dashboards | **GA** | Feb 2026 | Direct color assignment for data series in charts |
| Fabric Capacity overview events in Real-Time Hub | Preview | ~2025 | Monitor capacity health and detect throttling in real-time |

### MCP for RTI

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| MCP Support for Real-Time Intelligence | Preview | ~2025 | Model Context Protocol server for AI agents to interact with RTI |

---

## 🏢 3. Data Warehouse

### T-SQL & Query Engine

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| MERGE support (T-SQL) | **GA** | Jan 2026 | Full T-SQL MERGE statement for INSERT/UPDATE/DELETE operations |
| ANY_VALUE aggregate function | **GA** | Mar 2026 | Return representative value from grouped rows |
| DATE_BUCKET() function | **GA** | Dec 2025 | Custom time-based aggregations for temporal analysis |
| ALTER TABLE support in explicit transactions | **GA** | Apr 2026 | Execute ALTER TABLE within user-defined transactions |
| OneLake as source for COPY INTO and OPENROWSET | **GA** | Mar 2026 | SQL-based data ingestion directly from OneLake paths |
| Scalar user-defined functions (UDFs) | Preview | ~2025 | CREATE FUNCTION support for reusable T-SQL logic |
| IDENTITY columns | Preview | ~2025 | Automatically generate unique values for new rows |
| Delta column mapping in SQL analytics endpoint | Preview | ~2025 | Support Delta tables with column mapping enabled |
| Custom SQL pools | Preview | ~2025 | Configure workload classifiers and resource allocation per pool |

### Performance & Statistics

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Incremental statistics refresh | **GA** | Dec 2025 | Faster automatic statistics updates on large tables |
| Proactive statistics refresh | **GA** | Dec 2025 | Opportunistic statistic refresh triggered after data changes |
| Data clustering | Preview | ~2025 | Organize data by similarity for query performance improvement |

### Security & Compliance

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Warehouse SQL Audit Logs | **GA** | Mar 2026 | Comprehensive, immutable database activity records for compliance |
| Outbound Access Protection (OAP) for Warehouse | **GA** | Mar 2026 | Control and restrict external data source access from warehouse |

### AI Functions

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| AI Functions in Fabric Data Warehouse | Preview | ~2025 | Built-in AI functions for text categorization, sentiment analysis, translation, etc. in T-SQL |
| AI Functions cost transparency | Preview | Mar 2026 | Cost visibility in notebooks and Capacity Metrics App |

### Copilot for Warehouse

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Copilot for Data Warehouse Chat | Preview | Feb 2025 | Natural language chat for data warehousing tasks |
| Copilot for SQL analytics endpoint | Preview | ~2025 | Generate and optimize SQL queries via natural language |

### Migration

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Migration Assistant for Fabric Data Warehouse | Preview | ~2025 | Direct connection to source warehouse for migration |
| Warehouse source control | Preview | ~2025 | Manage versioned warehouse objects with Git integration |
| DacFx Integration for Warehouse ALM | Preview | ~2025 | Simplify warehouse application lifecycle management |

---

## 🏭 4. Data Factory

### Dataflows Gen2

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Modern evaluator for Dataflow Gen2 | **GA** | Feb 2026 | New .NET Core 8 query execution engine (significant perf improvement) |
| Preview-only steps for Dataflow Gen2 | **GA** | Mar 2026 | Transformation steps that run only during authoring (not at refresh) |
| Schema support in Fabric data destinations | **GA** | Mar 2026 | Write Dataflow Gen2 data into specific Lakehouse schemas |
| AI-Powered Prompt Transform | **GA** | Mar 2026 | Enrich and transform data using natural language prompts |
| Dataflow Gen2 Public APIs | Preview | May 2025 | Automate dataflow creation, management, scheduling, monitoring |
| Partitioned compute for Dataflow Gen2 | Preview | ~2025 | Parallel execution of dataflow logic for large datasets |
| Advanced edit for data destination queries | Preview | ~2025 | Modify destination-side query logic in authoring |
| Public parameter values to refresh Dataflow Gen2 | Preview | ~2025 | Pass parameters with CI/CD support |
| Fabric variable libraries in Dataflow Gen2 | Preview | ~2025 | Centralized configuration management across environments |
| Evaluate Power Query programmatically | Preview | ~2025 | Public REST API to execute Power Query M scripts |
| Recent data in Dataflow Gen2 | Preview | ~2025 | Quick access to frequently used data items |
| Copilot for Dataflow Gen2 Modern Get Data | Preview | ~2025 | Natural language commands for data ingestion and transformation |
| Data Factory Adaptive performance tuning | Preview | ~2025 | Intelligently optimize data movement performance |
| Data Factory MCP | Preview | Mar 2026 | AI assistants create, test, and deploy Dataflow Gen2 via natural language (Model Context Protocol) |

### Pipelines

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Invoke SSIS Package activity | Preview | ~2025 | Execute SSIS packages from pipeline orchestration |
| Copy job support for change data capture (CDC) | Preview | May 2025 | Efficient replication of inserted, updated, and deleted records |
| Upsert to delta table with Lakehouse connector | Preview | ~2025 | Upsert support for Delta table writes from pipelines |

### dbt Integration

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| dbt Job in Fabric Data Factory | Preview | ~2025 | Author, schedule, and monitor dbt projects natively in Fabric |

### Connectors

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Google BigQuery connector | **GA** | Mar 2026 | Improved reliability for BigQuery access |
| IBM Netezza ODBC Driver connector | **GA** | Mar 2026 | Reliable IBM Netezza connectivity |
| Snowflake Key-Pair Authentication | **GA** | Feb 2026 | Password-less RSA/ECDSA authentication for Snowflake |
| Azure Key Vault references for authentication | Preview | ~2025 | Authenticate to data connections using AKV stored secrets |

### Gateways

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| PowerShell model for gateways | **GA** | Mar 2026 | Fully supported gateway lifecycle automation |
| Certificate and proxy support for VNet data gateway | **GA** | Mar 2026 | Secure connectivity in enterprise environments |
| On-premises data gateway auto-update (admin triggered) | **GA** | Mar 2026 | Admin-triggered gateway updates on demand |
| Data Factory On-premises gateway manual update | Preview | Dec 2025 | Manual gateway update option via portal or API |
| REST APIs for connections and gateways | Preview | ~2025 | Manage connections and gateways programmatically |

---

## 📊 5. Power BI / Semantic Models

### Direct Lake

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Direct Lake in OneLake | **GA** | Mar 2026 | Accelerated query performance directly against OneLake without data refresh; OneLake security compat |
| Direct Lake from Power BI Desktop | **GA** | Mar 2026 | Create Direct Lake semantic models from Desktop (not just service) |

### DAX & Modeling

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| DAX user-defined functions | Preview | ~2025 | CREATE FUNCTION in DAX with type hints, auto-dependency tracking, 256 params, JSDoc support |
| TMDL View in web modeling | Preview | Mar 2026 | Code-first semantic modeling using Tabular Model Definition Language in browser |
| Custom totals (visual calculations) | Preview | Mar 2026 | Control total row values in table/matrix (sum, min, max, count, distinct) |
| Visual calculations | **GA** | Pre-2025 | DAX calculations scoped to visual context |
| INFO.USERDEFINEDFUNCTIONS() | Preview | Mar 2026 | New DAX function returning metadata about UDFs |

### Reporting

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Translytical Task Flows | **GA** | Mar 2026 | End users take action (write-back, workflows) directly from Power BI reports via User Data Functions |
| Modern visual defaults (Fluent 2) | Preview | Mar 2026 | Updated base theme with Fluent 2 design, smooth lines, uniform padding, style presets |
| Series label leader lines for line charts | **GA** | Mar 2026 | Visual connections between series labels and data points |
| Input slicer conditional formatting | **GA** | Mar 2026 | Dynamic formatting rules for text colors, icons, borders in input slicers |
| Report Theme Updates (page size, structural colors) | **GA** | Mar 2026 | Define default page size and reference structural colors in theme JSON |
| AI Narrative auto refresh | **GA** | Mar 2026 | Auto-refresh AI narrative visual on slicer selection changes |

### Copilot in Power BI

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Copilot pane UX update | **GA** | Mar 2026 | Updated experience matching standalone Copilot look/feel |
| Copilot feedback with diagnostics | **GA** | Mar 2026 | Share diagnostic context with thumbs up/down feedback |
| Copilot in Fabric (worldwide) | Preview | ~2025 | AI assistance across Power BI, Data Factory, Data Science, KQL |

### Semantic Link

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Semantic Link | **GA** | Feb 2026 | Connect AI, BI, and data engineering through the Power BI semantic layer |

---

## 🗃️ 6. OneLake

### Security

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| OneLake Security (fine-grained access control) | Preview | ~2025 | Folder-level, row-level, and column-level security for OneLake data |
| OneLake data access roles for Lakehouse | Preview | ~2025 | Fine-grained role-based access control for lakehouse items |
| Secure mirrored Azure Databricks data with OneLake security | Preview | ~2025 | Map Unity Catalog policies to OneLake security |

### Iceberg Interoperability

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Access Delta Lake tables as Apache Iceberg in OneLake | Preview | ~2025 | Automatic Iceberg-compatible access to Delta tables without data movement |
| Apache Iceberg data in OneLake using Snowflake and shortcuts | Preview | ~2025 | Consume Iceberg-formatted data with Snowflake via shortcuts |
| OneLake and Snowflake interoperability | **GA** | Feb 2026 | Bidirectional Iceberg data reads between OneLake and Snowflake |

### Table APIs

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| OneLake Table APIs | **GA** | Feb 2026 | Iceberg REST Catalog API and Delta Lake APIs for programmatic table access |

### Discovery & Catalog

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| OneLake Catalog search API and MCP tool | Preview | Mar 2026 | Cross-workspace discovery with search API and AI MCP integration |
| Govern in OneLake Catalog for Fabric admins | **GA** | Mar 2026 | Admin insights and recommended governance actions |
| Centralized data governance in OneLake catalog | Preview | Feb 2025 | Aggregated insights and recommended governance actions |
| Load Fabric OneLake Data in Excel | Preview | ~2025 | Integrated OneLake catalog in Excel with modern Get Data |

### Cross-Platform Access

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Zero-copy access to OneLake data in Azure Databricks | Preview | ~2025 | Unity Catalog query Fabric data without copying |

---

## 🔄 7. Mirroring

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Oracle database mirroring | **GA** | Mar 2026 | Mirror Oracle databases including Autonomous Database into OneLake |
| Mirroring from SAP databases | **GA** | Mar 2026 | Continuously replicate SAP data into OneLake |
| Mirroring Azure Databricks catalogs from private endpoints | **GA** | Feb 2026 | Secure private connectivity with VNet data gateway |
| Mirroring for Azure Database for MySQL | Preview | ~2025 | Seamless integration of MySQL data into Fabric |
| Mirroring for Google BigQuery | Preview | ~2025 | Integrate Google BigQuery data into Fabric |
| SAP Datasphere Mirroring and Copy Job support | Preview | ~2025 | Mirror and copy data from SAP Datasphere |
| Data replication from Lakehouse with Delta Change Feed | Preview | Sep 2025 | Changed data from Lakehouse via Delta CDF to supported destinations |
| Manage built-in SQL database mirroring to OneLake (REST API) | Preview | ~2025 | Selectively manage which tables are mirrored into OneLake |
| Open Mirrored Databases (Cosmos DB, Snowflake, etc.) | **GA** | Pre-2025 | Mirror Azure Cosmos DB, Azure SQL DB, Azure SQL MI, Snowflake, and more |

---

## 🛡️ 8. Governance

### Purview & Sensitivity Labels

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Default domain sensitivity labels | **GA** | Feb 2026 | Automatically apply sensitivity labels to new items in a domain |
| Workspace Tags | **GA** | Mar 2026 | Organize workspaces by team, project, cost center, or environment |
| Centralized data governance in OneLake catalog | Preview | Feb 2025 | View aggregated governance insights and recommended actions |
| OneLake Catalog search API and MCP tool | Preview | Mar 2026 | Programmatic cross-workspace data discovery |

### Outbound Access Protection

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Outbound Access Protection (OAP) for Warehouse | **GA** | Mar 2026 | Control which external data sources warehouse can access |

### Customer-Managed Keys

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Fabric SQL database customer-managed keys | **GA** | Mar 2026 | Use Azure Key Vault keys for workspace SQL database encryption |

### SQL Audit Logs

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Warehouse SQL Audit Logs | **GA** | Mar 2026 | Comprehensive, immutable database activity records for compliance |

### Dynamic Data Masking

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| SQL database Dynamic Data Masking (DDM) | **GA** | Mar 2026 | Mask sensitive data from non-privileged users |

---

## 🤖 9. AI & Copilot

### Fabric IQ

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Fabric IQ workload | Preview | ~Nov 2025 | Unify business semantics across data, models, and systems (ontology, plan, graph) |
| Ontology item | Preview | ~Nov 2025 | Define entity types, relationships, and properties for business semantics |
| Plan item | Preview | ~Nov 2025 | Unified no-code planning and reporting platform |

### Data Agents

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Fabric Data Agents + Microsoft Copilot Studio | Preview | ~2025 | Integration for multi-agent orchestration and enterprise copilots |
| Fabric data agent integration with Azure AI Agent Service | Preview | ~2025 | Deploy agents using Fabric data agent SDK |
| Evaluate Fabric data agents with Python SDK | Preview | ~2025 | Programmatic evaluation and testing of data agents |
| Share the Fabric Data agent | Preview | Sep 2024 | Share data agents with others using permission models |

### AI Functions

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| AI Functions in Data Warehouse (T-SQL) | Preview | ~2025 | Text categorization, sentiment analysis, info extraction, translation, grammar correction |
| Multimodal support in AI Functions | Preview | ~2025 | Process images, PDFs, and text formats with aifunc helpers |
| AI Functions helpers for multimodal workflows | **GA** | Mar 2026 | Simplified multimodal file processing helpers |
| AI Functions cost transparency | Preview | Mar 2026 | Cost visibility in notebooks and Capacity Metrics App |

### AutoML & Data Science

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| AutoML low-code user experience | **GA** | Mar 2026 | Automated ML for regression, forecasting, classification |
| Code-First Hyperparameter Tuning (FLAML) | Preview | ~2025 | Streamlined hyperparameter tuning for ML models |
| ML model endpoints | Preview | ~2025 | Real-time predictions from secure, scalable endpoints |
| Prebuilt Foundry Tools in Fabric | Preview | ~2025 | Integration with Azure AI services (OpenAI, Language, Translator) |

### MCP (Model Context Protocol)

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Fabric MCP | Preview | ~Mar 2026 | MCP server for AI-assisted development across Fabric workloads |
| Data Factory MCP | Preview | Mar 2026 | AI assistants create, test, deploy Dataflow Gen2 via natural language |
| MCP Support for Real-Time Intelligence | Preview | ~2025 | MCP server for AI agents to interact with RTI |
| MCP remote servers for Activator and Eventhouse | Preview | Mar 2026 | Hosted MCP remote servers for RTI components |
| OneLake Catalog MCP tool | Preview | Mar 2026 | Cross-workspace discovery via MCP |

### Copilot Experiences

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Copilot in Fabric (worldwide) | Preview | ~2025 | Available across Power BI, Data Factory, Data Science, KQL queries |
| Enhanced conversation with Copilot | Preview | ~2025 | Improved AI with prompt storage and history |
| Copilot for Data Warehouse Chat | Preview | Feb 2025 | Natural language chat for warehousing tasks |
| Copilot for SQL analytics endpoint | Preview | ~2025 | Generate and optimize SQL queries via natural language |
| Copilot for Dataflow Gen2 Modern Get Data | Preview | ~2025 | Natural language data ingestion and transformation |
| Inline code completion in notebooks | Preview | Jun 2025 | AI-assisted code completion in notebook cells |

---

## 🔄 10. CI/CD & DevOps

### fabric-cicd

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| fabric-cicd Python package | **GA** | Feb 2026 | Official Microsoft Python tool for CI/CD deployments to Fabric workspaces |
| CI/CD for API for GraphQL | **GA** | Feb 2026 | Git-based GraphQL item management and deployment |
| Fabric variable libraries in Dataflow Gen2 with CI/CD | Preview | ~2025 | Centralized config management across environments |

### Git Integration

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Service principal support for Fabric Git with Azure DevOps | **GA** | Dec 2025 | Automated Git operations using service principals |
| Lakehouse support for Git integration & deployment pipelines | Preview | ~2025 | Lifecycle management for Lakehouse items |
| Warehouse source control | Preview | ~2025 | Manage versioned warehouse objects with Git |
| DacFx Integration for Warehouse ALM | Preview | ~2025 | Simplify warehouse application lifecycle management |

### Deployment Pipelines & APIs

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Fabric notebook public APIs | **GA** | Mar 2026 | Programmatic notebook management (CRUD, execute) |
| Dataflow Gen2 Public APIs | Preview | May 2025 | Automate dataflow creation, management, scheduling |
| Folder REST API | Preview | ~2025 | Create and manage workspace folders via automation |
| REST APIs for connections and gateways | Preview | ~2025 | Manage connections and gateways programmatically |
| Microsoft Fabric Admin APIs | Available | ~2025 | Administrative APIs for tenant and workspace management |

---

## ⚙️ 11. Admin & Platform

### Workspace Identity

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Workspace Identity (Managed Service Principal) | **GA** | ~Feb 2026 | Automatically managed service principal for secure access to Azure resources (ADLS Gen2, etc.) |
| Fabric Identities (tenant limit control) | **GA** | Jan 2026 | Increased identity limit with custom tenant-level control (default 10,000) |

### Security & Networking

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Workspace IP firewall rules | **GA** | Mar 2026 | Define allow list of IP addresses for workspace access |
| Workspace-level surge protection controls | Preview | Jan 2026 | Per-workspace CU percentage limits with auto-blocking of excessive workloads |
| SQL database Tenant-level private links | Preview | ~2025 | Secure data traffic access via private endpoints |

### Capacity Management

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Workspace-level workload assignment and centralized admin | **GA** | Mar 2026 | Add workloads directly to workspaces; centralized admin control |
| Item History in Fabric Capacity Metrics App | Preview | ~2025 | 30-day capacity consumption view with interactive visuals |
| Microsoft Fabric SKU estimator | Preview | ~2025 | Enhanced capacity planning and sizing tool |
| Workspace monitoring | Preview | ~2025 | Database collecting Fabric item logs, metrics, and performance data |

### Extensibility

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Fabric Extensibility Toolkit | **GA** | Mar 2026 | Build, validate, and publish custom Fabric workloads |
| Tabbed navigation for multitasking | Preview | ~2025 | Open multiple items with tabs and object explorer |

### Gateway Administration

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| PowerShell model for gateways | **GA** | Mar 2026 | Fully supported gateway lifecycle automation |
| Certificate and proxy support for VNet data gateway | **GA** | Mar 2026 | Secure connectivity in enterprise environments |
| On-premises data gateway auto-update | **GA** | Mar 2026 | Admin-triggered on-demand gateway updates |

---

## 🆕 12. New Workloads

### Fabric SQL Database

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| SQL database in Fabric | **GA** | ~Nov 2024 | Developer-friendly OLTP database based on Azure SQL Database engine |
| SQL database Dynamic Data Masking (DDM) | **GA** | Mar 2026 | Mask sensitive data from non-privileged users |
| SQL database customer-managed keys | **GA** | Mar 2026 | Use Azure Key Vault keys for encryption |
| SQL database data virtualization | Preview | ~2025 | Query external OneLake data using T-SQL |
| SQL database control compute utilization (max vCore) | Preview | ~2025 | Limit maximum vCore utilization to reduce capacity |
| SQL database Tenant-level private links | Preview | ~2025 | Secure private connectivity |
| ALTER DATABASE SET options + Full Text Indexing | Preview | ~2025 | Extended SQL database configuration options |
| Automatic index compaction | Preview | ~2025 | Reduces storage space and I/O without manual maintenance |
| Migration Assistant to SQL database | Preview | ~2025 | Simplified SQL Server migration with DACPACs and guidance |

### API for GraphQL

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| API for GraphQL | **GA** | ~2024 | GraphQL data access layer for querying multiple Fabric data sources |
| CI/CD for API for GraphQL | **GA** | Feb 2026 | Git-based GraphQL item management |
| GraphQL MCP server for AI agents | Preview | ~2026 | Build local MCP server connecting AI agents to Fabric data |

### User Data Functions

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| User Data Functions | Preview | ~Nov 2025 | Serverless C#/.NET functions for event-driven data processing and write-back |
| Translytical Task Flows (via UDF) | **GA** | Mar 2026 | Enable Power BI report write-back actions using User Data Functions |
| Fabric Activator integration in User Data Functions | Preview | ~2025 | Process events from Fabric events and OneLake events |

### Digital Twin Builder

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Digital Twin Builder | Preview | Mar 2026 | Create data-driven, real-time digital representations of physical entities |

### Fabric IQ

| Feature | Status | Date | Description |
|---------|--------|------|-------------|
| Fabric IQ workload | Preview | ~Nov 2025 | Unify business semantics with Ontology, Plan, and Graph items |
| Ontology item | Preview | ~Nov 2025 | Define entity types, relationships, and properties |
| Plan item | Preview | ~Nov 2025 | No-code planning and reporting platform |

---

## 📈 13. Summary Statistics

### Features by Status

| Status | Count |
|--------|-------|
| Generally Available (GA) | ~55 |
| Preview | ~130 |
| **Total** | **~185** |

### Key GA Milestones (Jul 2025 - Apr 2026)

| Month | Notable GA Features |
|-------|--------------------|
| **Dec 2025** | Lakehouse Schemas, DATE_BUCKET(), Incremental/Proactive Statistics |
| **Jan 2026** | MERGE support, Fabric Identities |
| **Feb 2026** | OneLake Table APIs, Snowflake Interop, Semantic Link, Default Domain Labels, fabric-cicd, Modern Evaluator, Snowflake Key-Pair Auth, CI/CD for GraphQL, Data Series Colors |
| **Mar 2026** | Direct Lake in OneLake, Translytical Task Flows, Fabric Maps, SQL Operator, SQL Audit Logs, OAP for Warehouse, ANY_VALUE, Workspace Tags, Workspace IP Firewall, AutoML, Notebook APIs, Extensibility Toolkit, Gateway PowerShell, Oracle/SAP Mirroring, AI-Powered Prompt Transform, CMK for SQL DB, DDM, Entra SP for S3 |
| **Apr 2026** | Shortcut Transformations, ALTER TABLE in Transactions |

### Features Still in Preview (High Priority)

These are major features still in Preview as of April 2026:
- Fabric Runtime 2.0 (Spark 4.0)
- Materialized Lake Views
- OneLake Security (fine-grained)
- Digital Twin Builder
- Business Events
- Fabric IQ (Ontology/Plan/Graph)
- Data Agents
- AI Functions in Warehouse
- dbt Job in Data Factory
- User Data Functions
- Eventhouse Vector Database
- Anomaly Detection
- Warehouse Custom SQL Pools
- Warehouse IDENTITY columns
- Multiple mirroring connectors (MySQL, BigQuery)

---

## 🔍 14. Cross-Reference Notes for POC Codebase

### Features Already Covered in Phase 9

Based on the CLAUDE.md project notes, these features were addressed:
- Digital Twin Builder (doc + notebook)
- Data Agents (doc)
- Fabric IQ (doc update)
- RTI Update (Business Events, Maps, SQL Operator)
- OneLake Security (doc)
- Workspace Identity (Bicep module)
- Lakehouse Schemas (notebook updates)
- Shortcut Transformations (notebook)
- fabric-cicd CI/CD (workflow + script + doc)
- SQL Audit Logs (doc)
- Workspace Tags (Bicep update)
- Default Domain Sensitivity Labels (doc update)
- Outbound Access Protection (doc)
- Customer-Managed Keys (Bicep + doc)
- Iceberg Interoperability (doc)
- dbt Integration (doc)
- AI Functions Compliance (notebook)
- Materialized Lake Views (doc)
- Spark Runtime 2.0 Migration (doc)
- Vector Database in Eventhouse (doc)

### Potential Gaps to Investigate

Reconciled against the current `docs/features/` inventory (55 feature docs). **All 30 former gaps are now covered.**

| # | Feature | Status | Coverage |
|---|---------|--------|----------|
| 1 | Direct Lake in OneLake GA (Mar 2026) | ✅ Covered | `direct-lake.md` |
| 2 | Translytical Task Flows (GA Mar 2026) | ✅ Covered | `translytical-task-flows.md` |
| 3 | User Data Functions | ✅ Covered | `user-data-functions.md` |
| 4 | TMDL View in web modeling | ✅ Covered | `tmdl-power-bi-developer-mode.md` |
| 5 | DAX user-defined functions | ✅ Covered | `dax-user-defined-functions.md` |
| 6 | Fabric MCP / Data Factory MCP | ✅ Covered | `fabric-mcp.md` |
| 7 | MCP for RTI (Activator/Eventhouse) | ✅ Covered | `fabric-mcp.md` |
| 8 | Modern visual defaults (Fluent 2) | ✅ Covered | `tmdl-power-bi-developer-mode.md` |
| 9 | MERGE support (GA Jan 2026) | ✅ Covered | `fabric-sql-database.md` |
| 10 | ANY_VALUE aggregate (GA Mar 2026) | ✅ Covered | `best-practices/08_WAREHOUSE_SETUP.md` |
| 11 | Workspace IP firewall rules (GA Mar 2026) | ✅ Covered | `workspace-ip-firewall.md` |
| 12 | Workspace-level surge protection | ✅ Covered | `workspace-ip-firewall.md` |
| 13 | Fabric Extensibility Toolkit (GA Mar 2026) | ✅ Covered | `fabric-extensibility-toolkit.md` |
| 14 | Oracle database mirroring (GA Mar 2026) | ✅ Covered | `mirroring.md` |
| 15 | SAP database mirroring (GA Mar 2026) | ✅ Covered | `mirroring.md` |
| 16 | OneLake Catalog search API | ✅ Covered | `onelake-catalog.md` |
| 17 | AutoML low-code UX (GA Mar 2026) | ✅ Covered | `automl-model-endpoints.md` |
| 18 | AI-Powered Prompt Transform (GA Mar 2026) | ✅ Covered | `dataflow-gen2-ai-prompt-transform.md` |
| 19 | DeltaFlow transformation | ✅ Covered | `real-time-intelligence.md` |
| 20 | Eventhouse entity diagrams | ✅ Covered | `eventhouse-entity-diagrams.md` |
| 21 | Prebuilt Foundry Tools | ✅ Covered | `data-agents.md`, `fabric-mcp.md` |
| 22 | Data Agents + Azure AI Agent Service | ✅ Covered | `data-agents.md` |
| 23 | Semantic Link GA (Feb 2026) | ✅ Covered | `semantic-link.md` |
| 24 | Copy job CDC support | ✅ Covered | `copy-job-cdc.md` |
| 25 | Workspace monitoring | ✅ Covered | `workspace-monitoring.md` |
| 26 | PowerShell gateway model (GA Mar 2026) | ✅ Covered | `gateway-powershell-automation.md` |
| 27 | Incremental/Proactive statistics (GA Dec 2025) | ✅ Covered | `best-practices/08_WAREHOUSE_SETUP.md` |
| 28 | Custom totals (Preview Mar 2026) | ✅ Covered | `tmdl-power-bi-developer-mode.md` |
| 29 | Series label leader lines | ✅ Covered | `tmdl-power-bi-developer-mode.md` |
| 30 | Copilot pane UX update | ✅ Covered | `ai-copilot-configuration.md` |

---

## 📖 Sources

- [Microsoft Fabric What's New](https://learn.microsoft.com/en-us/fabric/fundamentals/whats-new)
- [Power BI What's New - March 2026](https://learn.microsoft.com/en-us/power-bi/fundamentals/whats-new)
- [Microsoft Fabric Roadmap](https://roadmap.fabric.microsoft.com/)
- [Fabric Blog](https://blog.fabric.microsoft.com/)
- [Workspace Identity Documentation](https://learn.microsoft.com/en-us/fabric/security/workspace-identity)
- [API for GraphQL Overview](https://learn.microsoft.com/en-us/fabric/data-engineering/api-graphql-overview)
- [SQL Database in Fabric Overview](https://learn.microsoft.com/en-us/fabric/database/sql/overview)
- [Eventhouse Vector Database](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/vector-database)

---

## 📚 Related Documentation

| Document | Description |
|----------|-------------|
| [🏗️ Architecture](ARCHITECTURE.md) | System architecture and design |
| [🚀 Deployment Guide](DEPLOYMENT.md) | Infrastructure deployment |
| [📖 Glossary](GLOSSARY.md) | Technical terms reference |

---

[⬆️ Back to Top](#-microsoft-fabric---comprehensive-feature-inventory-april-2026) | [📚 Docs](./) | [🏠 Home](index.md)

---

> 📖 **Documentation maintained by:** Frank Garofalo
> 🔗 **Repository:** [Suppercharge_Microsoft_Fabric](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric)
