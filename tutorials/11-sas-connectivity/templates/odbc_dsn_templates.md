# ODBC DSN Configuration Templates for Microsoft Fabric

This document provides ready-to-use ODBC Data Source Name (DSN) configurations for connecting to Microsoft Fabric from SAS and other applications.

---

!!! note "Third-party references — publicly sourced, good-faith comparison"
    This page references non-Microsoft products and services. That information is drawn from each vendor's **publicly available documentation** and is offered for honest, good-faith comparison only. This is a personal project written from a Microsoft Fabric and Azure perspective; it does **not** claim expertise in, or authority over, any third-party product, and nothing here is an official statement by, or endorsed by, those vendors. Capabilities, pricing, and features change often — always verify against the vendor's current official documentation. Where a third-party offering is the stronger choice, we say so plainly.

---

## Prerequisites

1. **ODBC Driver 18+ for SQL Server** installed
   - Windows: [Download from Microsoft](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
   - Linux: See installation commands below

2. **Fabric SQL Endpoint Information:**
   - Server: `<workspace-id>.datawarehouse.fabric.microsoft.com`
   - Database: `<lakehouse-name>` or `<warehouse-name>`

---

## Windows DSN Templates

### Template 1: Lakehouse with Interactive Authentication

Use for **interactive sessions** where a browser popup is acceptable.

**ODBC Data Source Administrator Settings:**

| Field | Value |
|-------|-------|
| Name | `Fabric_Casino_Lakehouse` |
| Description | `Casino POC Lakehouse - Read Only` |
| Server | `abc12345.datawarehouse.fabric.microsoft.com` |
| Database | `lh_casino_poc` |

**Authentication:** Azure Active Directory Interactive

---

### Template 2: Warehouse with Service Principal

Use for **automated jobs** and **batch processing**.

**ODBC Data Source Administrator Settings:**

| Field | Value |
|-------|-------|
| Name | `Fabric_Casino_Warehouse_SPN` |
| Description | `Casino POC Warehouse - Service Principal` |
| Server | `xyz67890.datawarehouse.fabric.microsoft.com` |
| Database | `wh_casino_analytics` |

**Authentication:** Azure Active Directory Service Principal
- Client ID: `<your-client-id>`
- Client Secret: `<from-environment-variable>`

---

## Linux DSN Templates

### /etc/odbc.ini

```ini
#
# Microsoft Fabric ODBC Data Sources
# Location: /etc/odbc.ini (system-wide) or ~/.odbc.ini (user)
#

# ============================================================
# Lakehouse - Interactive Authentication
# ============================================================
[Fabric_Casino_Lakehouse]
Description = Casino POC Lakehouse - Interactive Auth
Driver = ODBC Driver 18 for SQL Server
Server = abc12345.datawarehouse.fabric.microsoft.com
Database = lh_casino_poc
Authentication = ActiveDirectoryInteractive
Encrypt = yes
TrustServerCertificate = no

# ============================================================
# Lakehouse - Service Principal Authentication
# ============================================================
[Fabric_Casino_Lakehouse_SPN]
Description = Casino POC Lakehouse - Service Principal
Driver = ODBC Driver 18 for SQL Server
Server = abc12345.datawarehouse.fabric.microsoft.com
Database = lh_casino_poc
Authentication = ActiveDirectoryServicePrincipal
# UID and PWD should be set via environment or connection string
Encrypt = yes
TrustServerCertificate = no

# ============================================================
# Warehouse - Interactive Authentication
# ============================================================
[Fabric_Casino_Warehouse]
Description = Casino POC Warehouse - Interactive Auth
Driver = ODBC Driver 18 for SQL Server
Server = xyz67890.datawarehouse.fabric.microsoft.com
Database = wh_casino_analytics
Authentication = ActiveDirectoryInteractive
Encrypt = yes
TrustServerCertificate = no

# ============================================================
# Warehouse - Service Principal Authentication
# ============================================================
[Fabric_Casino_Warehouse_SPN]
Description = Casino POC Warehouse - Service Principal
Driver = ODBC Driver 18 for SQL Server
Server = xyz67890.datawarehouse.fabric.microsoft.com
Database = wh_casino_analytics
Authentication = ActiveDirectoryServicePrincipal
Encrypt = yes
TrustServerCertificate = no
```

### /etc/odbcinst.ini

```ini
#
# ODBC Driver Configuration
# Location: /etc/odbcinst.ini
#

[ODBC Driver 18 for SQL Server]
Description = Microsoft ODBC Driver 18 for SQL Server
Driver = /opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.3.so.2.1
UsageCount = 1

# If using Driver 17 (legacy)
[ODBC Driver 17 for SQL Server]
Description = Microsoft ODBC Driver 17 for SQL Server
Driver = /opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.10.so.1.1
UsageCount = 1
```

---

## Linux Installation Commands

### RHEL/CentOS 8+

```bash
# Add Microsoft repository
curl https://packages.microsoft.com/config/rhel/8/prod.repo | sudo tee /etc/yum.repos.d/mssql-release.repo

# Install ODBC Driver 18
sudo ACCEPT_EULA=Y yum install -y msodbcsql18

# Install optional tools
sudo ACCEPT_EULA=Y yum install -y mssql-tools18 unixODBC-devel

# Add tools to PATH
echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
source ~/.bashrc
```

### Ubuntu 20.04+

```bash
# Add Microsoft repository
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list

# Update and install
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Install optional tools
sudo ACCEPT_EULA=Y apt-get install -y mssql-tools18 unixodbc-dev

# Add tools to PATH
echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
source ~/.bashrc
```

### Verify Installation

```bash
# List installed drivers
odbcinst -q -d

# Test connection (interactive)
isql -v Fabric_Casino_Lakehouse

# Test with sqlcmd
sqlcmd -S abc12345.datawarehouse.fabric.microsoft.com -d lh_casino_poc -G
```

---

## SAS LIBNAME Statements

### Interactive Authentication

```sas
/* Using DSN */
LIBNAME fabric ODBC
    DSN="Fabric_Casino_Lakehouse"
    SCHEMA="bronze"
    READBUFF=50000
    DIRECT_SQL=ALLOW;

/* DSN-less */
LIBNAME fabric ODBC
    NOPROMPT="Driver={ODBC Driver 18 for SQL Server};
              Server=abc12345.datawarehouse.fabric.microsoft.com;
              Database=lh_casino_poc;
              Authentication=ActiveDirectoryInteractive;
              Encrypt=yes;"
    SCHEMA="bronze";
```

### Service Principal Authentication

```sas
/* Set credentials from environment */
%LET client_id = %SYSGET(FABRIC_CLIENT_ID);
%LET client_secret = %SYSGET(FABRIC_CLIENT_SECRET);

/* Connect using Service Principal */
LIBNAME fabric ODBC
    NOPROMPT="Driver={ODBC Driver 18 for SQL Server};
              Server=abc12345.datawarehouse.fabric.microsoft.com;
              Database=lh_casino_poc;
              Authentication=ActiveDirectoryServicePrincipal;
              UID=&client_id.;
              PWD=&client_secret.;
              Encrypt=yes;"
    SCHEMA="bronze"
    READBUFF=50000;
```

---

## Environment Variables

Set these environment variables for Service Principal authentication:

### Windows (PowerShell)

```powershell
$env:FABRIC_CLIENT_ID = "your-client-id-here"
$env:FABRIC_CLIENT_SECRET = "your-client-secret-here"
```

### Windows (Command Prompt)

```batch
SET FABRIC_CLIENT_ID=your-client-id-here
SET FABRIC_CLIENT_SECRET=your-client-secret-here
```

### Linux/Mac (Bash)

```bash
export FABRIC_CLIENT_ID="your-client-id-here"
export FABRIC_CLIENT_SECRET="your-client-secret-here"
```

### SAS Autoexec (secure approach)

```sas
/* Read from secure file instead of env vars */
%INCLUDE '/secure/credentials/fabric_credentials.sas' / NOSOURCE2;
```

---

## Connection String Quick Reference

| Authentication | Connection String |
|----------------|-------------------|
| **Interactive** | `Driver={ODBC Driver 18 for SQL Server};Server=<server>;Database=<db>;Authentication=ActiveDirectoryInteractive;Encrypt=yes;` |
| **Service Principal** | `Driver={ODBC Driver 18 for SQL Server};Server=<server>;Database=<db>;Authentication=ActiveDirectoryServicePrincipal;UID=<client_id>;PWD=<secret>;Encrypt=yes;` |
| **Managed Identity** | `Driver={ODBC Driver 18 for SQL Server};Server=<server>;Database=<db>;Authentication=ActiveDirectoryManagedIdentity;Encrypt=yes;` |

---

## Troubleshooting

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `[IM002] Data source name not found` | DSN not configured | Create DSN in ODBC Administrator |
| `Login failed for user` | Authentication failed | Check credentials, verify workspace access |
| `TCP Provider: timeout` | Network blocked | Ensure port 1433 is open |
| `SSL Provider: certificate` | Certificate issue | Use `TrustServerCertificate=yes` for testing only |
| `Cannot open database` | Wrong database name | Verify Lakehouse/Warehouse name |

### Debug Logging

Enable ODBC trace for debugging:

```ini
# /etc/odbcinst.ini
[ODBC]
Trace = yes
TraceFile = /tmp/odbc_trace.log
```

---

## Security Best Practices

1. **Never hardcode credentials** in scripts or config files
2. **Use Service Principals** for automated jobs
3. **Store secrets** in Azure Key Vault or secure credential stores
4. **Limit permissions** - grant only required workspace access
5. **Use encrypted connections** - always set `Encrypt=yes`
6. **Rotate secrets** regularly (recommended: 90 days)
7. **Audit access** via Microsoft Entra ID logs
