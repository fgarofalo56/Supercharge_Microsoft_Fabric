# Teradata to Microsoft Fabric Migration Checklist

Use this checklist to track progress through your migration project.

!!! info "Third-party references — publicly sourced, good-faith comparison"
    This page references non-Microsoft products and services. That information is drawn from each vendor's **publicly available documentation** and is offered for honest, good-faith comparison only. This is a personal project written from a Microsoft Fabric and Azure perspective; it does **not** claim expertise in, or authority over, any third-party product, and nothing here is an official statement by, or endorsed by, those vendors. Capabilities, pricing, and features change often — always verify against the vendor's current official documentation. Where a third-party offering is the stronger choice, we say so plainly.

---

## Phase 1: Assessment & Planning

### Environment Discovery

- [ ] Document Teradata version and configuration
- [ ] Inventory all databases and their sizes
- [ ] List all tables with row counts and sizes
- [ ] Identify SET vs MULTISET tables
- [ ] Catalog stored procedures and macros
- [ ] Document views and their dependencies
- [ ] List BTEQ and TPT scripts
- [ ] Identify third-party ETL tools in use
- [ ] Map data sources and targets

### Complexity Assessment

- [ ] Score each table for migration complexity
- [ ] Identify QUALIFY clause usage
- [ ] Document Teradata-specific SQL patterns
- [ ] List custom functions requiring translation
- [ ] Assess date/time function usage
- [ ] Identify PRIMARY INDEX dependencies
- [ ] Document partition strategies
- [ ] Evaluate query performance baselines

### Technical Requirements

- [ ] Confirm network connectivity to Azure
- [ ] Verify firewall rules (port 1025 for Teradata)
- [ ] Plan VPN or ExpressRoute if needed
- [ ] Size Fabric capacity requirements
- [ ] Estimate OneLake storage needs
- [ ] Identify Self-Hosted IR requirements
- [ ] Obtain Teradata JDBC drivers

### Security & Compliance

- [ ] Create migration service account in Teradata
- [ ] Grant SELECT permissions on source tables
- [ ] Provision Fabric workspace with appropriate access
- [ ] Set up Azure Key Vault for credentials
- [ ] Document PII handling requirements
- [ ] Review data residency requirements
- [ ] Plan for audit logging

### Project Planning

- [ ] Define migration scope and phases
- [ ] Identify pilot tables for proof of concept
- [ ] Establish success criteria
- [ ] Create rollback procedures
- [ ] Define testing strategy
- [ ] Assign team roles and responsibilities
- [ ] Set up project tracking

---

## Phase 2: Foundation Setup

### Fabric Environment

- [ ] Provision Fabric capacity (F64+ recommended)
- [ ] Create workspace for migration
- [ ] Create Bronze Lakehouse
- [ ] Create Silver Lakehouse
- [ ] Create Gold Lakehouse
- [ ] Create Data Warehouse for analytics
- [ ] Set up workspace access controls

### Connectivity

- [ ] Install Self-Hosted Integration Runtime (if needed)
- [ ] Create Teradata linked service in Data Factory
- [ ] Configure JDBC connection string
- [ ] Store credentials in Key Vault
- [ ] Test connectivity to Teradata
- [ ] Verify network throughput

### Development Environment

- [ ] Set up Fabric notebooks for testing
- [ ] Create SQL translation reference
- [ ] Establish code repository for scripts
- [ ] Configure CI/CD pipeline (optional)
- [ ] Create testing framework

### Monitoring

- [ ] Set up Data Factory monitoring
- [ ] Configure alert rules for failures
- [ ] Create dashboard for migration progress
- [ ] Establish logging standards

---

## Phase 3: Pilot Migration

### Select Pilot Tables

- [ ] Choose 3-5 representative tables
- [ ] Include at least one large table
- [ ] Include at least one with complex SQL
- [ ] Document expected results

### Execute Pilot

- [ ] Create pipeline for pilot tables
- [ ] Execute initial data load
- [ ] Validate row counts
- [ ] Validate column checksums
- [ ] Test sample data accuracy
- [ ] Measure load times

### SQL Translation Testing

- [ ] Translate sample QUALIFY queries
- [ ] Test SET table deduplication
- [ ] Validate date function conversions
- [ ] Test complex analytical queries
- [ ] Compare query results to Teradata

### Performance Baseline

- [ ] Run benchmark queries on Teradata
- [ ] Run same queries on Fabric
- [ ] Document performance comparison
- [ ] Identify optimization opportunities

### Lessons Learned

- [ ] Document issues encountered
- [ ] Update translation patterns
- [ ] Refine estimation models
- [ ] Adjust timeline if needed

---

## Phase 4: Core Migration

### Dimension Tables

- [ ] List all dimension tables
- [ ] Create migration schedule
- [ ] Execute dimension migrations
- [ ] Validate each dimension
- [ ] Create lookup documentation

### Fact Tables

- [ ] List all fact tables by priority
- [ ] Determine partitioning strategy
- [ ] Configure incremental load parameters
- [ ] Execute fact table migrations
- [ ] Validate fact tables

### ETL/ELT Conversion

- [ ] Inventory BTEQ scripts to convert
- [ ] Prioritize scripts by criticality
- [ ] Convert BTEQ to Fabric notebooks
- [ ] Convert TPT jobs to pipelines
- [ ] Test converted processes
- [ ] Document conversion patterns

### Stored Procedure Migration

- [ ] List procedures to migrate
- [ ] Translate to T-SQL or notebooks
- [ ] Test procedure logic
- [ ] Validate output accuracy

### Incremental Loads

- [ ] Identify watermark columns
- [ ] Configure incremental pipelines
- [ ] Test incremental logic
- [ ] Validate change capture

---

## Phase 5: Validation

### Data Accuracy

- [ ] Run row count validation on all tables
- [ ] Execute checksum validation
- [ ] Perform sample data comparison
- [ ] Validate referential integrity
- [ ] Check for duplicate handling

### Query Testing

- [ ] Compile list of critical queries
- [ ] Execute all queries on both systems
- [ ] Compare result sets
- [ ] Document any differences
- [ ] Resolve discrepancies

### Performance Testing

- [ ] Run performance benchmark suite
- [ ] Compare to baseline
- [ ] Optimize slow queries
- [ ] Tune Delta table settings
- [ ] Run OPTIMIZE on large tables

### User Acceptance

- [ ] Identify key users for UAT
- [ ] Provide access to test environment
- [ ] Collect user feedback
- [ ] Address reported issues
- [ ] Obtain sign-off

---

## Phase 6: Cutover

### Pre-Cutover

- [ ] Freeze Teradata schema changes
- [ ] Complete final incremental sync
- [ ] Verify all data is current
- [ ] Notify stakeholders of timeline
- [ ] Prepare rollback scripts

### Cutover Execution

- [ ] Stop writes to Teradata
- [ ] Execute final data sync
- [ ] Validate final row counts
- [ ] Switch application connections to Fabric
- [ ] Monitor for errors

### Post-Cutover

- [ ] Verify applications functioning
- [ ] Monitor query performance
- [ ] Address any issues
- [ ] Update documentation
- [ ] Communicate success

### Decommission

- [ ] Archive Teradata data (if required)
- [ ] Document archive location
- [ ] Plan Teradata shutdown timeline
- [ ] Remove Teradata access
- [ ] Update asset inventory

---

## Phase 7: Post-Migration

### Optimization

- [ ] Review query performance
- [ ] Implement Z-ORDER on large tables
- [ ] Set up scheduled OPTIMIZE jobs
- [ ] Tune Spark configurations
- [ ] Review cost efficiency

### Documentation

- [ ] Update system architecture diagrams
- [ ] Document new data flows
- [ ] Create user guides
- [ ] Update operational runbooks
- [ ] Archive migration artifacts

### Knowledge Transfer

- [ ] Train operations team
- [ ] Train development team
- [ ] Train business analysts
- [ ] Create FAQ document

### Continuous Improvement

- [ ] Gather post-migration feedback
- [ ] Identify improvement opportunities
- [ ] Plan future optimizations
- [ ] Document lessons for future migrations

---

## Quick Reference

### Key Contacts

| Role | Name | Email |
|------|------|-------|
| Project Manager | | |
| Technical Lead | | |
| Teradata DBA | | |
| Fabric Admin | | |
| Business Owner | | |

### Critical Dates

| Milestone | Target Date | Actual Date | Status |
|-----------|-------------|-------------|--------|
| Assessment Complete | | | |
| Pilot Complete | | | |
| Core Migration Start | | | |
| Core Migration End | | | |
| Cutover | | | |
| Decommission | | | |

### Key Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Tables Migrated | | |
| Total Data Volume (TB) | | |
| Query Performance vs Baseline | ≤120% | |
| Data Accuracy | 100% | |
| Migration Duration | | |

---

## Sign-Off

| Phase | Approver | Date | Signature |
|-------|----------|------|-----------|
| Assessment | | | |
| Pilot | | | |
| Core Migration | | | |
| Validation | | | |
| Cutover | | | |
| Project Complete | | | |
