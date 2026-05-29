---
hero: assets/heroes/white-papers.svg
hero_alt: "Migration & RTI Research — Field findings"
type: deep-dive
---
# 🔄 Database Migration Paths & Advanced Real-Time Intelligence Research

> **Last Updated**: 2026-04-15 | **Version**: 2.0
> **Status**: ✅ Final | **Maintainer**: Documentation Team

<div align="center" markdown>

![Category](https://img.shields.io/badge/Category-Research-purple?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-April_2026-blue?style=for-the-badge)

</div>

> Research compiled: 2026-03-11
> Sources: Microsoft Learn, Brave Web Search, Microsoft Docs MCP

!!! note "Third-party references — publicly sourced, good-faith comparison"
    This page references non-Microsoft products and services. That information is drawn from each vendor's **publicly available documentation** and is offered for honest, good-faith comparison only. This is a personal project written from a Microsoft Fabric and Azure perspective; it does **not** claim expertise in, or authority over, any third-party product, and nothing here is an official statement by, or endorsed by, those vendors. Capabilities, pricing, and features change often — always verify against the vendor's current official documentation. Where a third-party offering is the stronger choice, we say so plainly.

---

## 🏗️ Part 1: Database Migration Paths to Microsoft Fabric

### 1. Teradata to Microsoft Fabric

#### Official Microsoft Migration Guidance

Microsoft provides a comprehensive Teradata migration guide series originally written for Azure Synapse Analytics, which is the primary reference path for migrating to Fabric Data Warehouse (Fabric DW is the successor to Synapse dedicated SQL pools).

**Key documentation:**

| Document | URL |
|----------|-----|
| Fabric Migration Overview | https://learn.microsoft.com/fabric/fundamentals/migration |
| Fabric Migration Assistant for Data Warehouse | https://learn.microsoft.com/fabric/data-warehouse/migration-assistant |
| Migrate with the Migration Assistant | https://learn.microsoft.com/fabric/data-warehouse/migrate-with-migration-assistant |
| Teradata Design & Performance Migration | https://learn.microsoft.com/azure/synapse-analytics/migration-guides/teradata/1-design-performance-migration |
| Teradata ETL/Load Migration | https://learn.microsoft.com/azure/synapse-analytics/migration-guides/teradata/2-etl-load-migration-considerations |
| Minimize SQL Issues for Teradata | https://learn.microsoft.com/azure/synapse-analytics/migration-guides/teradata/5-minimize-sql-issues |
| Teradata Connector in Fabric Data Factory | https://learn.microsoft.com/fabric/data-factory/connector-teradata-database |
| Configure Teradata Copy Activity | https://learn.microsoft.com/fabric/data-factory/connector-teradata-copy-activity |

**Migration Architecture (High-Level Flow):**

```
Teradata Environment
    |
    v
[Extract] --> BTEQ/TPT scripts export to flat files --> Azure Data Lake Storage Gen2
    |                                                         |
    v                                                         v
[Schema/DDL] --> DACPAC via Migration Assistant        [Data Files: Parquet/CSV]
    |                                                         |
    v                                                         v
Fabric Data Warehouse <--- COPY INTO / Data Factory Pipelines
```

#### Tools for Migration

1. **Fabric Migration Assistant** (Native, built into Fabric)
   - Copies metadata and data from source, auto-converts schema to Fabric DW
   - AI-powered assistance for migration incompatibility resolution (requires Copilot/F2+)
   - Supports DACPAC import for schema migration
   - Migrates: Tables, Views, Functions, Stored Procedures, Security objects

2. **Azure Data Factory / Fabric Data Pipelines**
   - Teradata connector available in Fabric (source only, via on-premises data gateway)
   - Supports Dataflow Gen2, Pipeline Copy Activity, and Copy Job
   - Authentication: Basic (username/password) and Windows

3. **dbt (data build tool)**
   - The dbt adapter for Microsoft Fabric Data Warehouse enables migrating existing dbt projects from Teradata to Fabric with a configuration change
   - Converts DDL and DML to Fabric syntax on the fly
   - URL: https://learn.microsoft.com/fabric/data-warehouse/tutorial-setup-dbt

4. **Third-Party Tools**
   - Informatica, Talend: Native connectors for both Teradata and Azure/Fabric
   - Microsoft partners offer automated migration tooling (mapping, conversion)
   - Teradata AI Unlimited now available as a Fabric Workload Hub ISV (public preview)

5. **Open-Source Toolkits**
   - **microsoft/fabric-migrationfactory** (GitHub): Framework and toolkit for migrating to Fabric with methodologies, automation, and best practices
     - URL: https://github.com/microsoft/fabric-migrationfactory
   - **microsoft/fabric-migration** (GitHub): Scripts and tooling to migrate DW and Spark workloads
     - URL: https://github.com/microsoft/fabric-migration
   - **microsoft/fabric-toolbox** (GitHub): Accelerators, scripts, and samples
     - URL: https://github.com/microsoft/fabric-toolbox

#### Schema/DDL Conversion Patterns (Teradata SQL to T-SQL/Spark SQL)

**Key SQL Syntax Differences:**

| Teradata Feature | Fabric/T-SQL Equivalent |
|-----------------|------------------------|
| `QUALIFY` clause | Subquery with `ROW_NUMBER()` |
| Direct date subtraction (`DATE1 - DATE2`) | `DATEDIFF()` and `DATEADD()` functions |
| `LIKE ANY ('pattern1', 'pattern2')` | Multiple `OR` clauses with `LIKE` |
| `GROUP BY` ordinal | Must use explicit column name |
| Case-insensitive comparisons (default) | Always case-sensitive in Fabric |
| `FALLBACK`, `MULTISET` clauses | Remove (not needed in Fabric) |
| Stored Procedures (SPL language) | Recode in T-SQL |
| Triggers | Not supported in Fabric DW; implement via Azure Data Factory |
| Sequences | Use `IDENTITY` columns |
| Temp tables | Use regular tables (temp tables not supported) |

**DDL Generation Strategy:**
- Access Teradata system catalog (`DBC.ColumnsV`) to extract current definitions
- Generate equivalent `CREATE TABLE` DDL for Fabric
- Remove Teradata-specific clauses (`FALLBACK`, `MULTISET`, index definitions)
- Map data types per the mapping table below

#### Data Type Mapping (Teradata to Fabric)

| Teradata Data Type | Fabric/Azure Synapse Data Type |
|-------------------|-------------------------------|
| BIGINT | bigint |
| BOOLEAN / BOOL | bit |
| BYTEINT | tinyint (Fabric maps to smallint) |
| CHAR(p) | char(p) |
| VARCHAR(p) | varchar(p) |
| DATE | date |
| DATETIME | datetime2 |
| DECIMAL(p,s) | decimal(p,s) |
| DOUBLE / DOUBLE PRECISION | float(53) |
| FLOAT(p) | float(p) |
| INTEGER / INT | int |
| SMALLINT | smallint |
| TIME | time |
| TIMESTAMP | datetime2 |
| TIME WITH TIME ZONE | datetimeoffset |
| BLOB | varbinary (BLOB not directly supported) |
| CLOB | varchar (CLOB not directly supported) |
| INTERVAL types | Not supported; use DATEDIFF/DATEADD |
| ARRAY | Not supported |
| PERIOD types | String |
| NUMBER | Double |
| XML | String |

**Notes on Fabric Data Warehouse Data Types:**
- Fabric DW does not require indexes (automatic optimization)
- TDE not needed (Fabric encrypts data automatically)
- External tables not currently supported
- Identity columns behave differently than Teradata sequences

#### Teradata BTEQ/FastLoad Equivalents in Fabric

| Teradata Utility | Fabric Equivalent | Notes |
|-----------------|-------------------|-------|
| **BTEQ** (interactive SQL) | SQL Query Editor in Fabric Warehouse, KQL Queryset | T-SQL syntax; interactive query execution |
| **FastLoad** (bulk load) | **COPY INTO** statement | Highest-performance bulk ingestion from ADLS Gen2 files |
| **MultiLoad** (bulk update/upsert) | Fabric Data Pipelines + MERGE statements | Combine pipeline with T-SQL MERGE for upserts |
| **TPT (Teradata Parallel Transporter)** | Fabric Data Factory Copy Activity / Copy Job | Parallel data movement with 170+ connectors |
| **FastExport** (bulk extract) | Fabric Pipeline to ADLS Gen2 (Parquet/CSV export) | Export via notebooks or pipelines |
| **MLOAD** | Fabric Data Pipelines with staging tables | Load into staging, then MERGE to target |

**Key Performance Notes:**
- Fabric has no resource contention when loading multiple tables concurrently
- Workload management separates load and query resources
- Maximum ingestion throughput limited only by capacity SKU
- Recommended: Extract to Parquet on ADLS Gen2, then COPY INTO or Data Factory

#### Sample Migration Architecture

```
Phase 1: Assessment & Planning
  - Inventory Teradata objects (DBC.ColumnsV, DBC.TablesV)
  - Identify data volumes (raw data per table)
  - Catalog ETL processes (BTEQ scripts, stored procedures, TPT jobs)
  - Assess third-party tool compatibility

Phase 2: Schema Migration
  - Generate DACPAC or use dbt to convert DDL
  - Use Fabric Migration Assistant for automated conversion
  - Fix incompatible objects (AI-assisted in Migration Assistant)

Phase 3: Data Migration
  - Extract data from Teradata to ADLS Gen2 (Parquet format)
  - Use Fabric Copy Job or COPY INTO for ingestion
  - Parallel load across tables (no contention in Fabric)

Phase 4: ETL/Code Migration
  - Re-engineer BTEQ/TPT scripts to Data Factory pipelines
  - Convert stored procedures from SPL to T-SQL
  - Migrate scheduled jobs to Fabric pipeline triggers

Phase 5: Validation & Cutover
  - Parallel testing (old warehouse vs. new Fabric warehouse)
  - Reroute application connections
  - Update Power BI/reporting connections
```

---

### 2. Snowflake to Microsoft Fabric

#### Official Microsoft Migration Guidance

Microsoft offers multiple pathways for Snowflake integration/migration, ranging from zero-copy data sharing to full migration.

**Key documentation:**

| Document | URL |
|----------|-----|
| Mirroring Snowflake in Fabric | https://learn.microsoft.com/fabric/mirroring/snowflake |
| Snowflake Mirroring Tutorial | https://learn.microsoft.com/fabric/mirroring/snowflake-tutorial |
| Snowflake Mirroring Limitations | https://learn.microsoft.com/fabric/mirroring/snowflake-limitations |
| Snowflake Connector Overview | https://learn.microsoft.com/fabric/data-factory/connector-snowflake-overview |
| Write Iceberg Tables from Snowflake to OneLake | https://learn.microsoft.com/fabric/onelake/snowflake/create-snowflake-database-item |
| Migration Methods (dbt approach) | https://learn.microsoft.com/fabric/data-warehouse/migration-synapse-dedicated-sql-pool-methods |

#### Three Primary Integration/Migration Paths

**Path 1: Snowflake Mirroring (Near Real-Time Replication)**

- Continuously replicates Snowflake data to OneLake in near real-time
- No pipeline management required
- Uses Snowflake Streams under the hood
- Supports up to 1,000 tables (alphabetical selection if "Mirror all" chosen)
- Authentication: Username/password and Microsoft Entra SSO
- Limitations:
  - Only native tables (not External, Transient, Temporary, Dynamic)
  - Max 1,000 tables per mirrored database
  - Replicator backs off exponentially if no updates (up to 1 hour)

**Cost Considerations for Mirroring:**
- Fabric compute for replication: **Free**
- Mirroring storage: **Free** up to capacity limit
- Network ingress fees: **Free**
- Snowflake side: Virtual warehouse compute charges when data changes are read; cloud services compute for metadata queries

**Path 2: Fabric Data Pipelines (Batch ETL)**

- Snowflake connector supports: Dataflow Gen2, Pipeline Copy Activity, Copy Job
- Copy Job supports: Full load, Incremental load, CDC, Append, Override, CDC Merge
- Authentication: Snowflake, Microsoft Account, Key-pair
- Gateway support: None needed, On-premises, Virtual network
- Best for scheduled batch transfers with transformations

**Path 3: Iceberg Table Interoperability (Zero-Copy)**

- Configure Snowflake to write Iceberg tables directly to OneLake
- Both Fabric and Snowflake work with a single copy of data
- No data duplication or movement
- Requires: Fabric workspace with Admin/Member role, Snowflake account identifier

#### Snowflake Connector in Fabric

| Capability | Support |
|-----------|---------|
| Dataflow Gen2 (source) | Yes |
| Pipeline Copy Activity (source/destination) | Yes |
| Copy Job (source/destination) | Yes |
| Full load | Yes |
| Incremental load | Yes |
| CDC | Yes |
| CDC Merge | Yes |
| Gateway: None, On-premises, VNet | Yes |
| Auth: Snowflake, Microsoft Account, Key-pair | Yes |

#### Data Sharing Options (Snowflake to ADLS to Fabric)

1. **Snowflake External Stage to ADLS Gen2** --> OneLake Shortcuts or Copy
2. **Snowflake COPY INTO @azure_stage** --> ADLS Gen2 --> Fabric Lakehouse
3. **Snowflake Data Sharing** --> Snowflake Reader Account in Azure --> Fabric Mirroring
4. **Iceberg Tables** --> OneLake (zero-copy, bidirectional)

#### Stored Procedure / UDF Migration Patterns

| Snowflake Feature | Fabric Equivalent |
|------------------|-------------------|
| Snowflake SQL Stored Procedures | T-SQL Stored Procedures in Fabric Warehouse |
| JavaScript UDFs | Not directly supported; rewrite in T-SQL or use Spark notebooks |
| SQL UDFs | Scalar UDFs (inlineable, preview) in Fabric Warehouse |
| Snowflake Tasks (scheduled SQL) | Fabric Data Pipelines / Scheduled notebooks |
| Snowflake Streams (CDC) | Fabric Mirroring / Eventstream CDC connectors |
| Snowpipe (continuous loading) | Fabric Eventstreams / Copy Job with CDC |

**Migration approach for stored procedures:**
- Use dbt to convert SQL logic (model-based approach)
- AI tools (e.g., ChatGPT) can assist with Snowflake SQL to T-SQL conversion
- Complex JavaScript UDFs require rewrite to PySpark in Fabric notebooks

#### Snowpipe Equivalent in Fabric

| Snowpipe Feature | Fabric Equivalent |
|-----------------|-------------------|
| Auto-ingest from cloud storage | **Eventstreams** with Azure Blob Storage events source |
| Continuous data loading | **Fabric Mirroring** (near real-time) or **Copy Job with CDC** |
| Serverless compute | Fabric capacity-based (included in SKU) |
| Notification-based triggers | **Fabric Data Activator** / Pipeline triggers on events |
| Streaming ingestion | **Eventstreams** with custom endpoint (Kafka protocol) |

#### Cost Comparison Considerations

The table below contrasts a referenced competitor's published pricing and capability model with Microsoft Fabric. The competitor's details are summarized in good faith from its publicly available documentation; the two platforms take different but each valid architectural approaches, so the right choice depends on workload and existing investments. Always verify the competitor's current pricing against its official documentation.

| Factor | Referenced competitor | Microsoft Fabric |
|--------|-----------------------|-----------------|
| Pricing Model | Per-second compute + storage | Capacity Units (CU) - single SKU |
| Data Storage | Per-TB/month | Included in capacity (OneLake) |
| Compute Scaling | Auto-scale warehouses (mature, granular) | Capacity-based, workload management |
| Cross-workload | Strong analytics engine; BI/DE via partner tools | Unified platform (DW, DE, DS, BI) |
| Real-Time | Continuous-ingest + change-stream features | Eventstreams + Eventhouse (native) |
| BI | Pairs with external BI tools | Power BI included natively |
| Governance | Native governance features | Microsoft Purview (integrated) |

#### Sample Migration Steps (5-Phase)

```
Phase 1: Discovery & Assessment
  - Inventory Snowflake objects (INFORMATION_SCHEMA)
  - Identify compute credit usage patterns
  - Catalog Snowpipe/Stream configurations
  - Map stored procedures and UDFs

Phase 2: Data Migration Strategy
  - Option A: Enable Snowflake Mirroring for near-real-time sync
  - Option B: Use Fabric Copy Job for batch migration
  - Option C: Iceberg table interop for zero-copy

Phase 3: Code Migration
  - Convert SQL procedures using dbt or manual conversion
  - Rewrite JavaScript UDFs to PySpark or T-SQL
  - Migrate Snowflake Tasks to Fabric pipelines/notebooks

Phase 4: Pipeline Migration
  - Replace Snowpipe with Eventstreams or Copy Job CDC
  - Migrate Snowflake Streams to Fabric Mirroring
  - Convert external stage references to OneLake paths

Phase 5: Validation & Cutover
  - Run parallel workloads
  - Validate data completeness and freshness
  - Switch Power BI data sources
  - Decommission Snowflake resources
```

---

### 3. IBM DB2 as Source for Microsoft Fabric

#### DB2 Connector Availability in Fabric

The IBM DB2 database connector is natively supported in Microsoft Fabric Data Factory.

| Capability | Support | Gateway | Authentication |
|-----------|---------|---------|---------------|
| **Dataflow Gen2** (source) | Yes | On-premises | Basic, Windows |
| **Pipeline Copy Activity** (source) | Yes | On-premises | Basic |
| **Copy Job** (source, Full load) | Yes | On-premises | Basic |
| Lookup Activity | Yes | On-premises | Basic |

**Key documentation:**

| Document | URL |
|----------|-----|
| IBM DB2 Connector Overview | https://learn.microsoft.com/fabric/data-factory/connector-ibm-db2-database-overview |
| DB2 Connection Setup | https://learn.microsoft.com/fabric/data-factory/connector-ibm-db2-database |
| DB2 Copy Activity Configuration | https://learn.microsoft.com/fabric/data-factory/connector-ibm-db2-database-copy-activity |
| DB2 Troubleshooting | https://learn.microsoft.com/fabric/data-factory/connector-troubleshoot-db2 |
| ADF DB2 Connector (detailed) | https://learn.microsoft.com/azure/data-factory/connector-db2 |

#### Supported DB2 Platforms and Versions

The connector uses the DRDA (Distributed Relational Database Architecture) protocol with SQLAM versions 9, 10, and 11:

| Platform | Supported Versions |
|----------|-------------------|
| IBM DB2 for z/OS | 12.1, 11.1, 10.1 |
| IBM DB2 for i (AS/400) | 7.3, 7.2, 7.1 |
| IBM DB2 for LUW (Linux/Unix/Windows) | 11, 10.5, 10.1 |

#### Data Gateway Requirements

**On-premises Data Gateway is required** for all DB2 connections in Fabric:

- DB2 databases (on-premises or cloud-hosted) require an on-premises data gateway
- The gateway machine must have network connectivity to the DB2 server
- Install the on-premises data gateway on a machine that can reach the DB2 instance
- For DB2 on z/OS: Gateway communicates via DRDA protocol over TCP/IP
- Virtual Network Data Gateway is an alternative for Azure-hosted VMs

**Gateway Setup:**
1. Install on-premises data gateway on a Windows machine with DB2 connectivity
2. Register gateway in Fabric (Manage Connections and Gateways)
3. Create DB2 connection using gateway
4. Configure pipeline or dataflow to use the connection

#### CDC (Change Data Capture) from DB2

**IBM DB2 does not have a native CDC connector in Fabric Eventstreams.** However, there are multiple approaches:

**Approach 1: Debezium CDC via Kafka to Fabric Eventstream**

Debezium provides an open-source CDC connector for DB2:

- **Debezium DB2 Connector**: Captures row-level changes from DB2 LUW
- Writes change events to Apache Kafka topics
- Fabric Eventstreams can then consume from Kafka (Apache Kafka source connector)
- URL: https://debezium.io/documentation/reference/stable/connectors/db2.html
- GitHub: https://github.com/debezium/debezium-connector-db2

**Architecture:**
```
DB2 Database
    |
    v (CDC via transaction log)
Debezium DB2 Connector (Kafka Connect)
    |
    v
Apache Kafka Cluster
    |
    v (Apache Kafka source connector)
Fabric Eventstream
    |
    v
Eventhouse / Lakehouse / Warehouse
```

**Approach 2: IBM InfoSphere Data Replication (IIDR)**

- IBM's enterprise CDC tool for DB2
- Supports DB2 for z/OS, i, and LUW
- Can replicate to Kafka topics or flat files
- Kafka output can feed into Fabric Eventstreams

**Approach 3: Fabric Data Pipeline with Watermark Pattern**

- Use the DB2 copy activity in a Fabric pipeline
- Implement incremental load using a watermark column (timestamp/ID)
- Schedule pipeline to run at desired intervals (pseudo-CDC)
- Not true real-time, but simpler to implement

**Approach 4: IBM Data Gate (for z/OS)**

- Replicates DB2 for z/OS data to DB2 LUW in cloud
- From cloud DB2 LUW, use Fabric DB2 connector or Debezium

#### DB2 for z/OS vs DB2 LUW Considerations

| Aspect | DB2 for z/OS | DB2 LUW |
|--------|-------------|---------|
| Fabric Connector | Yes (via DRDA) | Yes (via DRDA) |
| Gateway Required | Yes (on-premises) | Yes (on-premises) |
| Debezium CDC | Not supported (z/OS) | Supported |
| IBM IIDR CDC | Supported | Supported |
| Network | SNA/TCP-IP via gateway | Direct TCP/IP |
| EBCDIC Handling | May need conversion | Not applicable |
| Package Collection | Must specify (`NULLID` default) | Standard |

**z/OS-Specific Notes:**
- EBCDIC to ASCII conversion may be needed for character data
- Package collection configuration is critical (common error: `SQLSTATE=51002 SQLCODE=-805`)
- Fix: Set `packageCollection` property to `NULLID` in connection settings

#### JDBC/ODBC Connection Patterns

The Fabric DB2 connector uses the Microsoft driver by default, but also supports the IBM driver:

**Microsoft Driver (Default):**
- Built-in, no additional installation needed
- Uses DRDA protocol
- Works for most scenarios

**IBM Driver (Optional):**
- Requires installing IBM DB2 driver for .NET on the gateway machine
- Download from: https://www.ibm.com/support/pages/download-initial-version-115-clients-and-drivers
- Needed for advanced features or specific DB2 versions

**Connection Properties:**
- Server: DB2 hostname and port
- Database: Database name
- Authentication: Basic (username/password)
- Additional properties: Package collection, command timeout

#### On-Premises DB2 to Fabric Pattern

```
On-Premises DB2
    |
    v (DRDA Protocol)
On-Premises Data Gateway (Windows Server)
    |
    v (HTTPS)
Fabric Data Factory
    |
    +--> Copy Activity --> Lakehouse (Bronze)
    +--> Dataflow Gen2 --> Lakehouse/Warehouse
    +--> Copy Job --> Direct table load
    |
    v
Fabric Data Warehouse / Lakehouse (Silver/Gold)
    |
    v
Power BI Reports (Direct Lake)
```

---

## ⚡ Part 2: Advanced Real-Time Intelligence & Streaming

### 4. Multiple Source Connectors for Fabric Eventstreams/RTI

#### Comprehensive Source Connector Matrix

Fabric Eventstreams (Enhanced Capabilities) supports 30+ source connectors. Below is a detailed analysis for each requested source.

---

#### 4a. SQL Server (On-Premises CDC)

**Connector:** SQL Server on VM DB CDC

| Property | Details |
|----------|---------|
| Availability | GA (General Availability) |
| Connector Name | SQL Server on Virtual Machine Database (VM DB) CDC |
| Supported Platforms | SQL Server on Azure VMs, Amazon RDS for SQL Server, Amazon RDS Custom, Google Cloud SQL for SQL Server |
| Authentication | Basic (username/password) |
| Gateway | Not required for public access; VNet data gateway for private networks |
| Latency | Near real-time (seconds to low minutes) |
| Throughput | Depends on source DB transaction volume and Fabric capacity |

**Configuration Steps:**
1. Enable CDC on the SQL Server database: `EXEC sys.sp_cdc_enable_db;`
2. Enable CDC on target tables: `EXEC sys.sp_cdc_enable_table @source_schema=N'dbo', @source_name=N'MyTable', @role_name=NULL`
3. In Fabric, create an Eventstream with Enhanced Capabilities
4. Add Source > SQL Server on VM DB CDC
5. Provide server address, database, credentials
6. Select tables to monitor (supports regex patterns)
7. Configure decimal handling mode (Precise/Double/String)

**Documentation:** https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/add-source-sql-server-change-data-capture

**Important Notes:**
- SQL Server Express edition is NOT supported for CDC
- Database must be publicly accessible or accessible via VNet data gateway
- Only row-level changes captured (INSERT, UPDATE, DELETE)
- Initial snapshot of current data is captured first, then ongoing changes

---

#### 4b. Azure SQL Database (CDC)

**Connector:** Azure SQL Database Change Data Capture (CDC)

| Property | Details |
|----------|---------|
| Availability | GA |
| Connector Name | Azure SQL Database CDC |
| Authentication | Basic (username/password) |
| Gateway | Not required (cloud-to-cloud) |
| Latency | Near real-time |
| Throughput | Depends on DB tier and transaction volume |
| Region Restrictions | Not supported in West US3, Switzerland West |

**Configuration Steps:**
1. Enable CDC in Azure SQL DB:
   ```sql
   EXEC sys.sp_cdc_enable_db;
   EXEC sys.sp_cdc_enable_table @source_schema=N'dbo', @source_name=N'MyTable', @role_name=NULL;
   ```
2. Database must NOT have Mirroring enabled simultaneously
3. In Fabric Eventstream, add Azure SQL Database CDC source
4. Provide server name (`myserver.database.windows.net`), database, credentials
5. Select tables (supports regex: `dbo.test.*`, `dbo\.(test1|test2)`)

**Documentation:** https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/add-source-azure-sql-database-change-data-capture

**Limitations:**
- Multiple tables CDC not supported in a single connector instance (use multiple sources)
- Mirroring and CDC cannot be enabled simultaneously on the same database
- VNet injection supported for private databases

---

#### 4c. Azure Cosmos DB (Change Feed to Eventstreams)

**Connector:** Azure Cosmos DB CDC (for NoSQL API)

| Property | Details |
|----------|---------|
| Availability | GA |
| Connector Name | Azure Cosmos DB CDC |
| Supported API | Azure Cosmos DB for NoSQL only |
| Authentication | Account Key (Primary Key) |
| Gateway | Not required (cloud-to-cloud) |
| Latency | Near real-time |
| Change Feed Mode | Latest Version Mode |
| Region Restrictions | Not supported in West US3, Switzerland West |

**Configuration Steps:**
1. Get Cosmos DB endpoint URI and Primary Key from Azure portal
2. In Fabric Eventstream, add Azure Cosmos DB CDC source
3. Provide: Endpoint URI, Account Key, Database name, Container ID
4. Configure offset policy: Earliest or Latest
5. Publish the eventstream

**Documentation:** https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/add-source-azure-cosmos-db-change-data-capture

**Important Notes:**
- Uses **Latest Version Mode** of Cosmos DB Change Feed
- **Deletions are NOT captured** with this mode
- VNet injection supported for private Cosmos DB instances
- Each connector instance monitors one container

---

#### 4d. IBM DB2 (CDC Options)

**Connector:** No native CDC connector in Fabric Eventstreams

IBM DB2 does not have a direct CDC streaming connector in Fabric Eventstreams. The recommended patterns are:

**Option 1: Debezium DB2 Connector --> Kafka --> Fabric Eventstream**
- Debezium captures DB2 LUW transaction log changes
- Publishes to Kafka topics
- Fabric Eventstream Apache Kafka source connector ingests from Kafka
- Latency: Seconds (near real-time)
- Requires: Kafka cluster, Debezium Connect, DB2 LUW
- NOT supported for DB2 z/OS

**Option 2: IBM IIDR --> Kafka --> Fabric Eventstream**
- IBM InfoSphere Data Replication captures changes from all DB2 platforms (z/OS, i, LUW)
- Publishes to Kafka
- Fabric Eventstream Kafka connector consumes
- Enterprise licensing required from IBM

**Option 3: Batch CDC via Fabric Pipeline**
- Use DB2 connector in Fabric Data Factory
- Incremental load with watermark column
- Schedule at desired frequency
- Not true streaming, but simpler setup
- Latency: Minutes to hours depending on schedule

---

#### 4e. Oracle (GoldenGate to Kafka to Fabric)

**Connector:** Custom endpoint (Kafka protocol) after Oracle GoldenGate Big Data

Microsoft provides an **official end-to-end tutorial** for streaming Oracle CDC data to Fabric:

| Property | Details |
|----------|---------|
| Documentation | https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/stream-oracle-data-to-eventstream |
| Architecture | Oracle DB --> OGG Core (Extract) --> OGG Big Data (Kafka Handler) --> Eventstream Kafka Endpoint |
| Latency | Near real-time (seconds) |
| Authentication | SAS Key (Kafka SASL_SSL) |

**Architecture:**
```
Oracle Database (with Archive Log enabled)
    |
    v (Integrated Extract)
Oracle GoldenGate Core (Extract process - EXT1)
    |
    v (Trail files)
Oracle GoldenGate Big Data (Replicat - RKAFKA)
    |
    v (Kafka Handler, JSON format)
Fabric Eventstream Custom Endpoint (Kafka protocol)
    |
    v
Eventhouse / Lakehouse / Custom Endpoint Destination
```

**Configuration Summary:**
1. Create Oracle VM with database, enable archive logging and GoldenGate replication
2. Install OGG Core, configure Extract process for CDC tables
3. Install OGG Big Data with Kafka handler
4. Create Eventstream with Custom Endpoint source (Kafka tab)
5. Configure OGG Big Data `kafka.props` with Eventstream's topic name
6. Configure `custom_kafka_producer.properties` with bootstrap server and SASL config
7. Start replicat process

**Alternative: Oracle GoldenGate OneLake Event Handler (Direct)**
- OGG Big Data 23c+ includes a native **Microsoft Fabric OneLake Event Handler**
- Can replicate directly to Fabric Lakehouse or Mirrored Database
- Supports Parquet and other formats
- URL: https://docs.oracle.com/en/middleware/goldengate/big-data/23/gadbd/microsoft-fabric-onelake-event-handler.html

---

#### 4f. Apache Kafka (Kafka Connector for Eventstreams)

Fabric Eventstreams supports **three** Kafka-related source connectors:

| Connector | Status | Description |
|-----------|--------|-------------|
| **Apache Kafka** | Preview | Connect to self-managed Kafka clusters |
| **Confluent Cloud for Apache Kafka** | GA | Confluent Cloud managed Kafka |
| **Amazon MSK Kafka** | GA | Amazon Managed Streaming for Apache Kafka |

**Additionally**, Eventstreams expose a native **Kafka-compatible endpoint** (Custom Endpoint):
- Protocol: Apache Kafka (SASL_SSL, PLAIN mechanism)
- Eventstreams are backed by Azure Event Hubs (Kafka-compatible)
- Any Kafka producer can send to Eventstream custom endpoint
- Supports Confluent Schema Registry deserialization (preview)

**Configuration (Apache Kafka Source):**
1. Add Source > Apache Kafka in Eventstream
2. Provide bootstrap servers, topic, authentication
3. Supports SASL/SSL, SASL/PLAIN authentication
4. VNet injection supported for private Kafka clusters

**Configuration (Custom Endpoint as Kafka receiver):**
1. Add Custom Endpoint source to Eventstream
2. Get Kafka tab credentials (bootstrap server, SASL config)
3. Configure any Kafka producer with these credentials
4. Supports Event Hub, Kafka, and AMQP protocols

**Documentation:**
- Apache Kafka source: https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/add-source-apache-kafka
- Confluent Cloud: https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/add-source-confluent-kafka
- Amazon MSK: https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/add-source-amazon-managed-streaming-for-apache-kafka
- Custom Endpoint (Kafka): https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/add-source-custom-app
- Kafka Endpoint Tutorial: https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/stream-consume-events-use-kafka-endpoint

---

#### 4g. IoT Hub / IoT Devices (Direct Ingestion)

**Connector:** Azure IoT Hub

| Property | Details |
|----------|---------|
| Availability | GA |
| Connector Name | Azure IoT Hub |
| Authentication | Shared Access Policy (IoT Hub connection string) |
| Gateway | Not required |
| Data Formats | JSON, Avro, CSV |
| Consumer Groups | Configurable (default: `$Default`) |
| Latency | Near real-time (sub-second to seconds) |

**Configuration Steps:**
1. In Azure portal, create or use existing IoT Hub
2. Create Shared Access Policy with at least `Service connect` permission
3. In Fabric, create Eventstream
4. Add Source > Azure IoT Hub
5. Provide: IoT Hub name, Shared Access Key Name, Key, Consumer Group
6. Select data format (JSON recommended)
7. Publish

**Documentation:**
- Add IoT Hub Source: https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/add-source-azure-iot-hub
- Build Power BI report from IoT Hub: https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/build-report-from-iot-hub
- Azure IoT Operations direct integration: https://learn.microsoft.com/azure/iot-operations/connect-to-cloud/howto-configure-fabric-real-time-intelligence

**Additional IoT Options:**
- **Azure IoT Operations**: Direct integration with Fabric RTI via Eventstream custom endpoint (supports Microsoft Entra ID or SASL)
- **MQTT source connector** (preview): Direct connection to any MQTT v3.1/v3.1.1 broker
- **Azure Event Grid**: For event-driven IoT patterns (MQTT namespace support)

---

#### Complete Eventstream Source Connector Summary

| Source | Connector Status | CDC Type | Gateway Needed | Latency |
|--------|-----------------|----------|---------------|---------|
| SQL Server (on-prem) | GA | Transaction log CDC | VNet gateway for private | Near real-time |
| Azure SQL Database | GA | Transaction log CDC | No | Near real-time |
| Azure SQL MI | GA | Transaction log CDC | No | Near real-time |
| Cosmos DB (NoSQL) | GA | Change Feed (Latest Version) | No | Near real-time |
| IBM DB2 | No native CDC connector | Via Debezium+Kafka | Yes (pipeline) | Seconds (Kafka) |
| Oracle | Tutorial (OGG+Kafka) | GoldenGate Extract | No (Kafka endpoint) | Near real-time |
| Apache Kafka | Preview | N/A (message broker) | VNet optional | Sub-second |
| Confluent Cloud Kafka | GA | N/A | No | Sub-second |
| Amazon MSK Kafka | GA | N/A | VNet optional | Sub-second |
| Azure IoT Hub | GA | Device telemetry | No | Sub-second |
| Azure Event Hubs | GA | Event streaming | No | Sub-second |
| PostgreSQL CDC | GA | WAL-based CDC | No | Near real-time |
| MySQL CDC | GA | Binlog CDC | No | Near real-time |
| MongoDB CDC | Preview | Change Streams | No | Near real-time |
| Google Cloud Pub/Sub | GA | Message streaming | No | Low seconds |
| Amazon Kinesis | GA | Stream processing | No | Low seconds |

---

### 5. Event Processing Patterns

#### Windowed Aggregations in KQL and Eventstreams

Fabric provides windowed aggregation capabilities through **two** mechanisms:

**Mechanism 1: SQL Operator in Eventstreams (Stream Processing)**

Eventstreams support a SQL operator (preview) for in-stream processing with five window types:

| Window Type | Description | Use Case |
|------------|-------------|----------|
| **Tumbling** | Fixed-size, non-overlapping, contiguous | Per-minute sales totals, fixed interval counts |
| **Hopping** | Fixed-size, overlapping, slide by hop size | Rolling averages, burst detection |
| **Sliding** | Variable, triggers only on content change | Event-driven alerting when threshold met |
| **Session** | Groups events by activity periods | User session analysis, idle detection |
| **Snapshot** | Groups events with same timestamp | Point-in-time aggregation |

**Examples (SQL Operator in Eventstreams):**

Per-minute sales aggregation (Tumbling):
```sql
SELECT System.Timestamp AS WindowEnd, city, SUM(salesAmount) AS TotalSales
INTO output
FROM input
GROUP BY city, TumblingWindow(minute, 1)
```

Burst/bot detection (Hopping):
```sql
SELECT System.Timestamp AS WindowEnd, userId, COUNT(*) AS OrderCount
INTO output
FROM input
GROUP BY userId, HoppingWindow(minute, 5, 1)
HAVING COUNT(*) > 10
```

Anomaly flagging (Hopping with statistical threshold):
```sql
SELECT System.Timestamp AS WindowEnd, deviceId, AVG(metricValue) AS RollingAvg, MAX(metricValue) AS CurrentMax
INTO output
FROM input
GROUP BY deviceId, HoppingWindow(minute, 10, 1)
HAVING MAX(metricValue) > 2 * AVG(metricValue)
```

Multiple windows simultaneously:
```sql
SELECT TollId, COUNT(*)
FROM Input TIMESTAMP BY EntryTime
GROUP BY TollId, Windows(
    TumblingWindow(minute, 10),
    TumblingWindow(minute, 20),
    TumblingWindow(minute, 30),
    TumblingWindow(minute, 60))
```

**Mechanism 2: KQL Queries in Eventhouse (Analytical Processing)**

KQL provides native time series analysis capabilities:

- `summarize` with `bin()` for time-based aggregation
- `make-series` for time series creation and analysis
- `series_decompose()` for anomaly detection
- `series_fir()` for filtering and smoothing
- Native support for thousands of time series in seconds

**Documentation:**
- Windows in Eventstreams: https://learn.microsoft.com/stream-analytics-query/windows-azure-stream-analytics
- Windowing functions: https://learn.microsoft.com/azure/stream-analytics/stream-analytics-window-functions
- Common query patterns: https://learn.microsoft.com/azure/stream-analytics/stream-analytics-stream-analytics-query-patterns
- SQL Operator examples: https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/process-events-using-sql-code-editor
- KQL time series analysis: https://learn.microsoft.com/kusto/query/time-series-analysis

---

#### Complex Event Processing (CEP) in Fabric

Fabric supports CEP through the combination of Eventstreams processing and Eventhouse analytics:

**In-Stream CEP (Eventstreams SQL Operator):**

| Pattern | Implementation |
|---------|---------------|
| Threshold detection | `HAVING COUNT(*) > N` with windowed aggregation |
| Moving averages | `HoppingWindow` with `AVG()` |
| Pattern detection | Multi-window comparison with `Windows()` function |
| Burst detection | `HoppingWindow` with `COUNT()` and `HAVING` |
| Missing events | `HoppingWindow` with `TopOne()` for gap detection |
| Correlation | `JOIN` multiple streams with time-based conditions |

**Analytical CEP (KQL in Eventhouse):**

| Pattern | KQL Approach |
|---------|-------------|
| Anomaly detection | `series_decompose_anomalies()` |
| Trend analysis | `series_fit_line()`, `series_fit_2lines()` |
| Forecasting | `series_decompose_forecast()` |
| Pattern matching | `scan` operator for sequential pattern detection |
| Sessionization | `row_window_session()` |

---

#### Event-Driven Architecture Patterns in Fabric

```
Pattern 1: Real-Time Monitoring Pipeline
  IoT Hub / Kafka --> Eventstream --> [Filter/Transform] --> Eventhouse (KQL DB)
                                          |
                                          +--> Data Activator (Alerts)
                                          +--> Real-Time Dashboard

Pattern 2: Multi-Source Correlation
  Source A (CDC) --> Eventstream A --\
  Source B (IoT) --> Eventstream B ---+--> Derived Stream --> Eventhouse
  Source C (Kafka) --> Eventstream C -/

Pattern 3: Lambda Architecture
  Source --> Eventstream --> Eventhouse (Speed layer, real-time queries)
       |
       +--> Data Pipeline --> Lakehouse (Batch layer, historical analysis)
       |
       +--> Power BI (Serving layer, Direct Lake + Real-Time Dashboard)

Pattern 4: Event-Driven ETL
  Azure Blob Storage Events --> Eventstream --> Pipeline Trigger --> ETL Pipeline
  Fabric Workspace Events --> Eventstream --> Data Activator --> Notification
```

---

#### Multi-Source Correlation

Fabric supports multi-source correlation through:

1. **Multiple sources in one Eventstream**: Add multiple CDC/streaming sources to a single Eventstream
2. **Derived Eventstreams**: Create new streams from transformed/aggregated source streams, shareable via Real-Time Hub
3. **Eventhouse cross-database queries**: Query across multiple KQL databases in the same Eventhouse
4. **Materialized Views**: Pre-aggregate data from multiple ingestion streams for fast correlation queries

**Architecture for Multi-Source Correlation:**
```
                    Real-Time Hub
                    (Discovery & Management)
                         |
    +--------------------+--------------------+
    |                    |                    |
Eventstream A       Eventstream B       Eventstream C
(SQL CDC)           (IoT Hub)           (Kafka)
    |                    |                    |
    v                    v                    v
    +-------- Eventhouse (KQL Database) ------+
              |          |          |
         Table A    Table B    Table C
              |          |          |
              +--- Materialized Views ---+
              |    (correlated data)     |
              v                         v
         Real-Time Dashboard      Data Activator
                                  (Alerts/Actions)
```

---

#### Late-Arriving Event Handling

Fabric provides multiple mechanisms for handling late-arriving events:

**In Eventstreams (SQL Operator):**
- `TIMESTAMP BY` clause defines the event time field
- Watermark mechanism handles out-of-order events
- Configurable late-arrival tolerance
- Events arriving within tolerance window are included in correct window

**In Eventhouse (KQL Database):**
- Data is automatically indexed by ingestion time
- Events can be queried by both ingestion time and event time
- Update policies can reprocess late data into materialized views
- Streaming ingestion vs. queued ingestion options

**In Data Pipelines (Batch Correction):**
- Incremental refresh can reprocess recent windows
- Delta Lake merge operations handle late updates
- Watermark-based incremental loads capture delayed records

**Best Practices:**
1. Always use `TIMESTAMP BY` with a business event timestamp in Eventstreams
2. Design ingestion time vs. event time columns in Eventhouse tables
3. Build materialized views that account for late arrivals (use wider windows)
4. Implement reconciliation pipelines for batch correction of late data
5. Set appropriate caching and retention policies in Eventhouse

---

## 🔗 Key Reference Links Summary

### 📖 Official Microsoft Documentation

| Topic | URL |
|-------|-----|
| Fabric Migration Overview | https://learn.microsoft.com/fabric/fundamentals/migration |
| Migration Assistant | https://learn.microsoft.com/fabric/data-warehouse/migration-assistant |
| Teradata Migration Guide | https://learn.microsoft.com/azure/synapse-analytics/migration-guides/teradata/1-design-performance-migration |
| Snowflake Mirroring | https://learn.microsoft.com/fabric/mirroring/snowflake |
| Snowflake Connector | https://learn.microsoft.com/fabric/data-factory/connector-snowflake-overview |
| Iceberg Interop | https://learn.microsoft.com/fabric/onelake/snowflake/create-snowflake-database-item |
| DB2 Connector | https://learn.microsoft.com/fabric/data-factory/connector-ibm-db2-database-overview |
| Eventstreams Overview | https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/overview |
| Eventstream Sources | https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/add-manage-eventstream-sources |
| Real-Time Hub | https://learn.microsoft.com/fabric/real-time-hub/real-time-hub-overview |
| Oracle CDC Tutorial | https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/stream-oracle-data-to-eventstream |
| Kafka Endpoint Tutorial | https://learn.microsoft.com/fabric/real-time-intelligence/event-streams/stream-consume-events-use-kafka-endpoint |
| Windowing Functions | https://learn.microsoft.com/azure/stream-analytics/stream-analytics-window-functions |
| KQL Time Series | https://learn.microsoft.com/kusto/query/time-series-analysis |

### 🛠️ Open-Source Tools and Repositories

| Tool | URL | Purpose |
|------|-----|---------|
| fabric-migrationfactory | https://github.com/microsoft/fabric-migrationfactory | Migration framework and automation toolkit |
| fabric-migration | https://github.com/microsoft/fabric-migration | DW and Spark migration scripts |
| fabric-toolbox | https://github.com/microsoft/fabric-toolbox | Accelerators, samples, monitoring templates |
| Debezium DB2 Connector | https://github.com/debezium/debezium-connector-db2 | CDC from DB2 LUW to Kafka |
| Debezium Documentation | https://debezium.io/documentation/reference/stable/connectors/db2.html | DB2 CDC configuration guide |

### 🌐 Third-Party Resources

| Resource | URL |
|----------|-----|
| OGG OneLake Event Handler | https://docs.oracle.com/en/middleware/goldengate/big-data/23/gadbd/microsoft-fabric-onelake-event-handler.html |
| Snowflake to Fabric Migration (Visionet) | https://www.visionet.com/article/snowflake-to-microsoft-fabric-migration-strategy-and-roadmap |
| Snowflake Migration with ChatGPT | https://www.ilink-digital.com/insights/blog/migration-of-snowflake-data-warehouse-to-microsoft-fabric-using-chatgpt/ |
| Fabric Migration Blog | https://blog.fabric.microsoft.com/en-us/blog/migrating-to-fabric-data-warehouse-guide-now-available/ |

---

## 📚 Related Documentation

| Document | Description |
|----------|-------------|
| [🏗️ Architecture](ARCHITECTURE.md) | System architecture and design |
| [🚀 Deployment Guide](DEPLOYMENT.md) | Infrastructure deployment |
| [📋 Prerequisites](PREREQUISITES.md) | Setup requirements |

---

[⬆️ Back to Top](#-database-migration-paths--advanced-real-time-intelligence-research) | [📚 Docs](./) | [🏠 Home](index.md)

---

> 📖 **Documentation maintained by:** Frank Garofalo
> 🔗 **Repository:** [Suppercharge_Microsoft_Fabric](https://github.com/fgarofalo56/Suppercharge_Microsoft_Fabric)
