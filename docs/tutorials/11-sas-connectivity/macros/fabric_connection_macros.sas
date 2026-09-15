/*******************************************************************************
 * Microsoft Fabric SAS Connection Macros
 *******************************************************************************
 *
 * This library provides reusable SAS macros for connecting to Microsoft Fabric
 * Lakehouses and Warehouses using ODBC.
 *
 * Prerequisites:
 *   - ODBC Driver 18+ for SQL Server installed
 *   - Microsoft Entra ID credentials configured
 *   - Network access to Fabric endpoint (port 1433)
 *
 * Usage:
 *   %include 'fabric_connection_macros.sas';
 *   %fabric_connect(dsn=Fabric_Lakehouse, libref=fabric);
 *
 *******************************************************************************/

/*******************************************************************************
 * MACRO: fabric_connect
 * Purpose: Establish ODBC connection to Microsoft Fabric
 *
 * Parameters:
 *   dsn      - ODBC Data Source Name (required)
 *   libref   - SAS libref to assign (default: fabric)
 *   schema   - Database schema (default: dbo)
 *   readbuff - Read buffer size (default: 10000)
 *
 * Example:
 *   %fabric_connect(dsn=Fabric_Casino_Lakehouse, libref=lh, schema=bronze);
 *******************************************************************************/
%MACRO fabric_connect(
    dsn=,
    libref=fabric,
    schema=dbo,
    readbuff=10000
);
    %PUT NOTE: Connecting to Microsoft Fabric via DSN: &dsn.;

    LIBNAME &libref. ODBC
        DSN="&dsn."
        SCHEMA="&schema."
        READBUFF=&readbuff.
        DIRECT_SQL=ALLOW
        PRESERVE_COL_NAMES=YES
        PRESERVE_TAB_NAMES=YES;

    %IF %SYSFUNC(LIBREF(&libref.)) = 0 %THEN %DO;
        %PUT NOTE: Successfully connected to Fabric as &libref.;

        /* List available tables */
        PROC SQL NOPRINT;
            SELECT COUNT(*) INTO :table_count
            FROM dictionary.tables
            WHERE UPCASE(libname) = UPCASE("&libref.");
        QUIT;

        %PUT NOTE: Found &table_count. tables in &libref..&schema.;
    %END;
    %ELSE %DO;
        %PUT ERROR: Failed to connect to Fabric DSN: &dsn.;
        %PUT ERROR: Check DSN configuration and credentials;
    %END;
%MEND fabric_connect;


/*******************************************************************************
 * MACRO: fabric_connect_spn
 * Purpose: Connect to Fabric using Service Principal authentication
 *
 * Parameters:
 *   server      - Fabric server endpoint (required)
 *   database    - Database name (required)
 *   client_id   - Service Principal client ID (from env var if empty)
 *   client_secret - Service Principal secret (from env var if empty)
 *   libref      - SAS libref to assign (default: fabric)
 *   schema      - Database schema (default: dbo)
 *
 * Example:
 *   %fabric_connect_spn(
 *       server=abc123.datawarehouse.fabric.microsoft.com,
 *       database=lh_casino_poc,
 *       libref=fabric
 *   );
 *******************************************************************************/
%MACRO fabric_connect_spn(
    server=,
    database=,
    client_id=,
    client_secret=,
    libref=fabric,
    schema=dbo
);
    /* Get credentials from environment if not provided */
    %IF %LENGTH(&client_id.) = 0 %THEN %DO;
        %LET client_id = %SYSGET(FABRIC_CLIENT_ID);
    %END;

    %IF %LENGTH(&client_secret.) = 0 %THEN %DO;
        %LET client_secret = %SYSGET(FABRIC_CLIENT_SECRET);
    %END;

    /* Validate credentials */
    %IF %LENGTH(&client_id.) = 0 OR %LENGTH(&client_secret.) = 0 %THEN %DO;
        %PUT ERROR: Service Principal credentials not provided;
        %PUT ERROR: Set FABRIC_CLIENT_ID and FABRIC_CLIENT_SECRET environment variables;
        %RETURN;
    %END;

    %PUT NOTE: Connecting to Fabric with Service Principal;

    LIBNAME &libref. ODBC
        NOPROMPT="Driver={ODBC Driver 18 for SQL Server};
                  Server=&server.;
                  Database=&database.;
                  Authentication=ActiveDirectoryServicePrincipal;
                  UID=&client_id.;
                  PWD=&client_secret.;
                  Encrypt=yes;
                  TrustServerCertificate=no;"
        SCHEMA="&schema."
        READBUFF=50000
        INSERTBUFF=10000
        DIRECT_SQL=ALLOW;

    %IF %SYSFUNC(LIBREF(&libref.)) = 0 %THEN %DO;
        %PUT NOTE: Successfully connected to Fabric as &libref.;
    %END;
    %ELSE %DO;
        %PUT ERROR: Failed to connect to Fabric;
    %END;
%MEND fabric_connect_spn;


/*******************************************************************************
 * MACRO: fabric_disconnect
 * Purpose: Clear Fabric LIBNAME connection
 *
 * Parameters:
 *   libref - SAS libref to clear (default: fabric)
 *******************************************************************************/
%MACRO fabric_disconnect(libref=fabric);
    LIBNAME &libref. CLEAR;
    %PUT NOTE: Disconnected from Fabric (&libref.);
%MEND fabric_disconnect;


/*******************************************************************************
 * MACRO: fabric_list_tables
 * Purpose: List all tables in Fabric connection
 *
 * Parameters:
 *   libref - SAS libref for Fabric (default: fabric)
 *   filter - Optional table name filter (supports wildcards)
 *******************************************************************************/
%MACRO fabric_list_tables(libref=fabric, filter=);
    PROC SQL;
        SELECT
            memname AS Table_Name,
            nobs AS Row_Count FORMAT=COMMA20.,
            nvar AS Column_Count
        FROM dictionary.tables
        WHERE UPCASE(libname) = UPCASE("&libref.")
        %IF %LENGTH(&filter.) > 0 %THEN %DO;
            AND UPCASE(memname) LIKE UPCASE("%&filter.%")
        %END;
        ORDER BY memname;
    QUIT;
%MEND fabric_list_tables;


/*******************************************************************************
 * MACRO: fabric_read
 * Purpose: Read Fabric table into SAS work dataset with pass-through SQL
 *
 * Parameters:
 *   libref     - Fabric libref (required)
 *   table      - Source table name (required)
 *   out        - Output dataset name (default: work.<table>)
 *   where      - Optional WHERE clause
 *   keep       - Optional column list to keep
 *   obs        - Maximum observations (default: all)
 *******************************************************************************/
%MACRO fabric_read(
    libref=,
    table=,
    out=,
    where=,
    keep=,
    obs=
);
    %IF %LENGTH(&out.) = 0 %THEN %LET out = work.&table.;

    %PUT NOTE: Reading &libref..&table. into &out.;

    DATA &out.;
        SET &libref..&table.
        %IF %LENGTH(&where.) > 0 %THEN %DO;
            (WHERE=(&where.))
        %END;
        %IF %LENGTH(&keep.) > 0 %THEN %DO;
            (KEEP=&keep.)
        %END;
        %IF %LENGTH(&obs.) > 0 %THEN %DO;
            (OBS=&obs.)
        %END;
        ;
    RUN;

    %LET row_count = %NOBS(&out.);
    %PUT NOTE: Read &row_count. rows into &out.;
%MEND fabric_read;


/*******************************************************************************
 * MACRO: fabric_write
 * Purpose: Write SAS dataset to Fabric Warehouse
 *
 * Parameters:
 *   data       - Source SAS dataset (required)
 *   libref     - Fabric Warehouse libref (required)
 *   table      - Target table name (required)
 *   mode       - Write mode: REPLACE or APPEND (default: REPLACE)
 *******************************************************************************/
%MACRO fabric_write(
    data=,
    libref=,
    table=,
    mode=REPLACE
);
    %PUT NOTE: Writing &data. to &libref..&table. (mode=&mode.);

    %IF %UPCASE(&mode.) = REPLACE %THEN %DO;
        /* Drop existing table if exists */
        PROC SQL NOERRORSTOP;
            DROP TABLE &libref..&table.;
        QUIT;

        DATA &libref..&table.;
            SET &data.;
        RUN;
    %END;
    %ELSE %IF %UPCASE(&mode.) = APPEND %THEN %DO;
        PROC APPEND
            BASE=&libref..&table.
            DATA=&data.
            FORCE;
        RUN;
    %END;
    %ELSE %DO;
        %PUT ERROR: Invalid mode &mode.. Use REPLACE or APPEND;
        %RETURN;
    %END;

    %PUT NOTE: Successfully wrote to &libref..&table.;
%MEND fabric_write;


/*******************************************************************************
 * MACRO: fabric_passthrough
 * Purpose: Execute pass-through SQL query against Fabric
 *
 * Parameters:
 *   libref  - Fabric libref (required)
 *   sql     - SQL query to execute (required)
 *   out     - Output dataset name (required)
 *******************************************************************************/
%MACRO fabric_passthrough(libref=, sql=, out=);
    %PUT NOTE: Executing pass-through SQL;

    PROC SQL;
        CONNECT USING &libref.;

        CREATE TABLE &out. AS
        SELECT * FROM CONNECTION TO &libref. (
            &sql.
        );

        DISCONNECT FROM &libref.;
    QUIT;

    %LET row_count = %NOBS(&out.);
    %PUT NOTE: Pass-through query returned &row_count. rows;
%MEND fabric_passthrough;


/*******************************************************************************
 * MACRO: fabric_validate_connection
 * Purpose: Test and validate Fabric connection
 *
 * Parameters:
 *   dsn - ODBC Data Source Name to test
 *******************************************************************************/
%MACRO fabric_validate_connection(dsn=);
    %PUT ;
    %PUT ========================================;
    %PUT  Fabric Connection Validation Test;
    %PUT ========================================;
    %PUT ;
    %PUT Testing DSN: &dsn.;

    /* Attempt connection */
    LIBNAME _test_ ODBC DSN="&dsn.";

    %IF %SYSFUNC(LIBREF(_test_)) = 0 %THEN %DO;
        %PUT NOTE: ✓ LIBNAME assignment successful;

        /* Count tables */
        PROC SQL NOPRINT;
            SELECT COUNT(*) INTO :table_count
            FROM dictionary.tables
            WHERE libname = '_TEST_';
        QUIT;

        %PUT NOTE: ✓ Tables accessible: &table_count.;

        /* Test query */
        PROC SQL NOPRINT;
            SELECT COUNT(*) INTO :test_result
            FROM dictionary.columns
            WHERE libname = '_TEST_';
        QUIT;

        %PUT NOTE: ✓ Query execution successful;
        %PUT ;
        %PUT ========================================;
        %PUT  CONNECTION TEST: PASSED;
        %PUT ========================================;
    %END;
    %ELSE %DO;
        %PUT ERROR: ✗ LIBNAME assignment failed;
        %PUT ;
        %PUT ========================================;
        %PUT  CONNECTION TEST: FAILED;
        %PUT ========================================;
        %PUT ;
        %PUT Check the following:;
        %PUT   1. ODBC Driver 18+ installed;
        %PUT   2. DSN configured correctly;
        %PUT   3. Network access to Fabric;
        %PUT   4. Microsoft Entra ID credentials;
    %END;

    LIBNAME _test_ CLEAR;
%MEND fabric_validate_connection;


/*******************************************************************************
 * MACRO: NOBS
 * Purpose: Return number of observations in a dataset
 *
 * Parameters:
 *   dsn - Dataset name
 *******************************************************************************/
%MACRO NOBS(dsn);
    %LOCAL nobs dsid rc;
    %LET nobs = 0;
    %LET dsid = %SYSFUNC(OPEN(&dsn.));
    %IF &dsid. %THEN %DO;
        %LET nobs = %SYSFUNC(ATTRN(&dsid., NOBS));
        %LET rc = %SYSFUNC(CLOSE(&dsid.));
    %END;
    &nobs.
%MEND NOBS;


/*******************************************************************************
 * Example Usage
 *******************************************************************************

 * 1. Basic connection using DSN:

    %fabric_connect(dsn=Fabric_Casino_Lakehouse, libref=lh, schema=bronze);
    %fabric_list_tables(libref=lh);

 * 2. Read data from Fabric:

    %fabric_read(libref=lh, table=slot_transactions,
                 where=transaction_date >= '2024-01-01',
                 obs=10000);

 * 3. Execute pass-through SQL:

    %fabric_passthrough(
        libref=lh,
        sql=%str(
            SELECT player_id, SUM(coin_in) AS total_coin_in
            FROM bronze.slot_transactions
            WHERE transaction_date >= '2024-01-01'
            GROUP BY player_id
            ORDER BY total_coin_in DESC
        ),
        out=work.player_summary
    );

 * 4. Write to Fabric Warehouse:

    %fabric_connect(dsn=Fabric_Casino_Warehouse, libref=wh, schema=sas_output);
    %fabric_write(data=work.model_scores, libref=wh, table=player_scores, mode=REPLACE);

 * 5. Disconnect:

    %fabric_disconnect(libref=lh);
    %fabric_disconnect(libref=wh);

*******************************************************************************/
