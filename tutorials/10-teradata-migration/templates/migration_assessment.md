# Teradata to Microsoft Fabric Migration Assessment

!!! note "Third-party references — publicly sourced, good-faith comparison"
    This page references non-Microsoft products and services. That information is drawn from each vendor's **publicly available documentation** and is offered for honest, good-faith comparison only. This is a personal project written from a Microsoft Fabric and Azure perspective; it does **not** claim expertise in, or authority over, any third-party product, and nothing here is an official statement by, or endorsed by, those vendors. Capabilities, pricing, and features change often — always verify against the vendor's current official documentation. Where a third-party offering is the stronger choice, we say so plainly.

## Project Information

| Field | Value |
|-------|-------|
| **Project Name** | |
| **Assessment Date** | |
| **Assessor** | |
| **Teradata Version** | |
| **Target Fabric Capacity** | |

---

## 1. Source Environment Inventory

### 1.1 Database Summary

| Database Name | Size (GB) | Table Count | View Count | Procedure Count |
|---------------|-----------|-------------|------------|-----------------|
| | | | | |
| | | | | |
| | | | | |
| **TOTAL** | | | | |

### 1.2 Top Tables by Size

| # | Database.Table | Size (GB) | Row Count | Primary Index | Partitioned? |
|---|----------------|-----------|-----------|---------------|--------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |
| 6 | | | | | |
| 7 | | | | | |
| 8 | | | | | |
| 9 | | | | | |
| 10 | | | | | |

### 1.3 Object Type Breakdown

| Object Type | Count | Migration Complexity |
|-------------|-------|---------------------|
| MULTISET Tables | | Low |
| SET Tables | | Medium (dedup required) |
| Views | | Low-Medium |
| Stored Procedures | | High (manual rewrite) |
| Macros | | High (manual rewrite) |
| User Defined Functions | | High |
| Triggers | | High |
| Indexes | | Medium (rethink for Delta) |

---

## 2. Workload Analysis

### 2.1 Query Patterns

| Pattern | Count | Complexity | Notes |
|---------|-------|------------|-------|
| QUALIFY clause usage | | Medium | Convert to CTE |
| SET table dependencies | | Medium | Add deduplication |
| TOP N WITH TIES | | Low | Use RANK() |
| SAMPLE queries | | Low | TABLESAMPLE |
| Recursive CTEs | | Low | Same syntax |
| MERGE statements | | Low | Same syntax |
| Teradata-specific functions | | Medium | See function mapping |

### 2.2 ETL/ELT Processes

| Process Name | Type | Frequency | Source Tool | Migration Approach |
|--------------|------|-----------|-------------|-------------------|
| | BTEQ | | Native | Convert to Notebook |
| | TPT | | Native | Convert to Pipeline |
| | Informatica | | Third-party | Migrate to Data Factory |
| | Ab Initio | | Third-party | Migrate to Data Factory |
| | Custom Script | | Various | Rewrite |

### 2.3 BTEQ Script Inventory

| Script Name | Purpose | Lines of Code | Complexity | Priority |
|-------------|---------|---------------|------------|----------|
| | | | | |
| | | | | |
| | | | | |

---

## 3. Data Quality Considerations

### 3.1 Data Types Requiring Attention

| Teradata Type | Fabric Equivalent | Conversion Notes |
|---------------|-------------------|------------------|
| BYTEINT | TINYINT | Direct mapping |
| NUMBER | DECIMAL/FLOAT | Check precision |
| PERIOD | Two columns | Manual conversion |
| ARRAY | JSON | Serialize |
| BLOB/CLOB | VARBINARY(MAX)/VARCHAR(MAX) | Size limits |
| INTERVAL | Calculated field | Manual conversion |
| TIME WITH TIME ZONE | DATETIMEOFFSET | Check timezone handling |

### 3.2 Character Set Considerations

| Issue | Impact | Mitigation |
|-------|--------|------------|
| LATIN vs UNICODE | | Standardize to UTF-8 |
| Trailing spaces (CHAR) | | TRIM on migration |
| Case sensitivity | | Verify collation settings |

---

## 4. Complexity Scoring

### 4.1 Per-Table Complexity

| Table | Size Score | SQL Score | Dependency Score | Total | Priority |
|-------|------------|-----------|------------------|-------|----------|
| | | | | | |
| | | | | | |

**Scoring Guide:**
- Size: 1 (< 1GB), 2 (1-10GB), 3 (10-100GB), 4 (100GB-1TB), 5 (> 1TB)
- SQL: 1 (Simple), 2 (Standard), 3 (Complex), 4 (Very Complex), 5 (Requires Rewrite)
- Dependencies: 1 (None), 2 (Few), 3 (Moderate), 4 (Many), 5 (Critical)

### 4.2 Overall Migration Complexity

| Category | Score (1-5) | Weight | Weighted Score |
|----------|-------------|--------|----------------|
| Data Volume | | 25% | |
| SQL Complexity | | 25% | |
| ETL Complexity | | 20% | |
| Dependencies | | 15% | |
| Timeline Pressure | | 15% | |
| **TOTAL** | | 100% | |

**Complexity Rating:**
- 1.0 - 2.0: Simple (2-4 weeks)
- 2.1 - 3.0: Moderate (1-3 months)
- 3.1 - 4.0: Complex (3-6 months)
- 4.1 - 5.0: Very Complex (6-12 months)

---

## 5. Technical Requirements

### 5.1 Connectivity

| Requirement | Status | Notes |
|-------------|--------|-------|
| Network access Teradata → Azure | ☐ | |
| VPN/ExpressRoute configured | ☐ | |
| Firewall rules (port 1025) | ☐ | |
| Self-Hosted IR installed | ☐ | |
| Teradata JDBC driver available | ☐ | |

### 5.2 Security

| Requirement | Status | Notes |
|-------------|--------|-------|
| Service account created | ☐ | |
| SELECT permissions granted | ☐ | |
| Fabric workspace provisioned | ☐ | |
| Key Vault for credentials | ☐ | |
| PII handling documented | ☐ | |

### 5.3 Fabric Capacity

| Resource | Required | Available | Gap |
|----------|----------|-----------|-----|
| Fabric Capacity (CUs) | | | |
| OneLake Storage (TB) | | | |
| Concurrent pipelines | | | |

---

## 6. Migration Phases

### Phase 1: Foundation (Week 1-2)

| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| Set up Fabric workspace | | ☐ | |
| Configure Teradata connectivity | | ☐ | |
| Create Lakehouse structure | | ☐ | |
| Set up monitoring | | ☐ | |

### Phase 2: Pilot Migration (Week 3-4)

| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| Migrate 3-5 simple tables | | ☐ | |
| Validate data accuracy | | ☐ | |
| Test query performance | | ☐ | |
| Document lessons learned | | ☐ | |

### Phase 3: Core Migration (Week 5-8)

| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| Migrate dimension tables | | ☐ | |
| Migrate fact tables | | ☐ | |
| Convert critical BTEQ scripts | | ☐ | |
| Set up incremental loads | | ☐ | |

### Phase 4: Validation & Cutover (Week 9-10)

| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| Full data validation | | ☐ | |
| Performance testing | | ☐ | |
| User acceptance testing | | ☐ | |
| Cutover execution | | ☐ | |
| Decommission Teradata queries | | ☐ | |

---

## 7. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Data volume exceeds transfer capacity | | | Incremental approach |
| SQL translation errors | | | Thorough testing |
| Performance degradation | | | Optimize Delta tables |
| Business disruption | | | Parallel run period |
| Timeline overrun | | | Phase approach |

---

## 8. Success Criteria

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Data accuracy | 100% row match | Row count validation |
| Data integrity | 100% checksum match | Numeric column sums |
| Query performance | Within 20% of Teradata | Benchmark queries |
| ETL reliability | 99.9% success rate | Pipeline monitoring |
| User satisfaction | > 80% approval | Survey |

---

## 9. Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Project Sponsor | | | |
| Technical Lead | | | |
| Data Architect | | | |
| Business Owner | | | |

---

## Appendix A: Teradata Inventory Queries

```sql
-- Database sizes
SELECT
    DatabaseName,
    SUM(CurrentPerm) / 1024 / 1024 / 1024 AS SizeGB,
    COUNT(DISTINCT TableName) AS TableCount
FROM DBC.TableSizeV
WHERE DatabaseName NOT IN ('DBC', 'SYSLIB', 'SYSSPATIAL')
GROUP BY DatabaseName
ORDER BY SizeGB DESC;

-- Table details
SELECT
    t.DatabaseName,
    t.TableName,
    t.TableKind,
    t.CreatorName,
    t.CreateTimeStamp,
    s.CurrentPerm / 1024 / 1024 AS SizeMB,
    s.RowCount
FROM DBC.TablesV t
LEFT JOIN DBC.TableSizeV s
    ON t.DatabaseName = s.DatabaseName
    AND t.TableName = s.TableName
WHERE t.DatabaseName = 'YOUR_DATABASE'
ORDER BY s.CurrentPerm DESC;

-- Stored procedures
SELECT DatabaseName, ProcedureName, CreateTimeStamp
FROM DBC.ProceduresV
WHERE DatabaseName = 'YOUR_DATABASE';

-- Views
SELECT DatabaseName, TableName AS ViewName, CreateTimeStamp
FROM DBC.TablesV
WHERE DatabaseName = 'YOUR_DATABASE'
  AND TableKind = 'V';
```

---

## Appendix B: Quick Reference - Function Mappings

| Teradata | Fabric T-SQL |
|----------|--------------|
| `NVL(a, b)` | `COALESCE(a, b)` |
| `NULLIFZERO(x)` | `NULLIF(x, 0)` |
| `ZEROIFNULL(x)` | `ISNULL(x, 0)` |
| `ADD_MONTHS(d, n)` | `DATEADD(MONTH, n, d)` |
| `CURRENT_DATE` | `CAST(GETDATE() AS DATE)` |
| `INDEX(s, p)` | `CHARINDEX(p, s)` |
| `OREPLACE(s, o, n)` | `REPLACE(s, o, n)` |
| `QUALIFY` | CTE with `ROW_NUMBER()` |
