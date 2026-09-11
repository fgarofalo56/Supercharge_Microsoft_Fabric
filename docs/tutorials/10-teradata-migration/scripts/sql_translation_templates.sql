-- ============================================================================
-- Teradata to Microsoft Fabric SQL Translation Templates
-- ============================================================================
-- This file provides side-by-side examples of Teradata SQL and their
-- equivalent Microsoft Fabric T-SQL translations.
-- ============================================================================

-- ============================================================================
-- 1. QUALIFY CLAUSE TRANSLATION
-- ============================================================================

-- TERADATA: Get latest record per player using QUALIFY
/*
SELECT
    player_id,
    session_timestamp,
    total_spend,
    loyalty_tier
FROM casino.player_sessions
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY player_id
    ORDER BY session_timestamp DESC
) = 1;
*/

-- FABRIC T-SQL: Use CTE with ROW_NUMBER and filter in WHERE
WITH ranked_sessions AS (
    SELECT
        player_id,
        session_timestamp,
        total_spend,
        loyalty_tier,
        ROW_NUMBER() OVER (
            PARTITION BY player_id
            ORDER BY session_timestamp DESC
        ) AS rn
    FROM casino.player_sessions
)
SELECT
    player_id,
    session_timestamp,
    total_spend,
    loyalty_tier
FROM ranked_sessions
WHERE rn = 1;


-- ============================================================================
-- 2. TOP N WITH TIES TRANSLATION
-- ============================================================================

-- TERADATA: Top 100 players by spend with ties
/*
SELECT TOP 100 WITH TIES
    player_id,
    SUM(total_spend) AS lifetime_spend
FROM casino.player_transactions
GROUP BY player_id
ORDER BY lifetime_spend DESC;
*/

-- FABRIC T-SQL: Use RANK() to handle ties
WITH ranked_players AS (
    SELECT
        player_id,
        SUM(total_spend) AS lifetime_spend,
        RANK() OVER (ORDER BY SUM(total_spend) DESC) AS rnk
    FROM casino.player_transactions
    GROUP BY player_id
)
SELECT player_id, lifetime_spend
FROM ranked_players
WHERE rnk <= 100
ORDER BY lifetime_spend DESC;


-- ============================================================================
-- 3. SET TABLE BEHAVIOR (Duplicate Elimination)
-- ============================================================================

-- TERADATA: SET table automatically rejects duplicates
/*
CREATE SET TABLE casino.unique_events (
    event_id INTEGER,
    event_type VARCHAR(50),
    event_time TIMESTAMP
) PRIMARY INDEX (event_id);
*/

-- FABRIC T-SQL: Use UNIQUE constraint or DISTINCT on insert
CREATE TABLE casino.unique_events (
    event_id INT NOT NULL,
    event_type VARCHAR(50),
    event_time DATETIME2,
    CONSTRAINT PK_unique_events PRIMARY KEY NONCLUSTERED (event_id)
);

-- For inserts, use DISTINCT or EXCEPT to avoid duplicates
INSERT INTO casino.unique_events (event_id, event_type, event_time)
SELECT DISTINCT event_id, event_type, event_time
FROM staging.new_events s
WHERE NOT EXISTS (
    SELECT 1 FROM casino.unique_events e
    WHERE e.event_id = s.event_id
);


-- ============================================================================
-- 4. DATE/TIME FUNCTION TRANSLATIONS
-- ============================================================================

-- Current Date
-- TERADATA: CURRENT_DATE
-- FABRIC:   CAST(GETDATE() AS DATE)
SELECT CAST(GETDATE() AS DATE) AS today;

-- Current Timestamp
-- TERADATA: CURRENT_TIMESTAMP
-- FABRIC:   GETDATE() or CURRENT_TIMESTAMP
SELECT GETDATE() AS now;

-- Date Literal
-- TERADATA: DATE '2024-01-15'
-- FABRIC:   CAST('2024-01-15' AS DATE)
SELECT CAST('2024-01-15' AS DATE) AS specific_date;

-- Add Months
-- TERADATA: ADD_MONTHS(date_col, 3)
-- FABRIC:   DATEADD(MONTH, 3, date_col)
SELECT DATEADD(MONTH, 3, GETDATE()) AS three_months_later;

-- Date Arithmetic
-- TERADATA: date_col + INTERVAL '7' DAY
-- FABRIC:   DATEADD(DAY, 7, date_col)
SELECT DATEADD(DAY, 7, GETDATE()) AS next_week;

-- Extract Date Part
-- TERADATA: EXTRACT(MONTH FROM date_col)
-- FABRIC:   MONTH(date_col) or DATEPART(MONTH, date_col)
SELECT
    YEAR(transaction_date) AS txn_year,
    MONTH(transaction_date) AS txn_month,
    DAY(transaction_date) AS txn_day
FROM casino.transactions;

-- Date Difference (in days)
-- TERADATA: date1 - date2
-- FABRIC:   DATEDIFF(DAY, date2, date1)
SELECT DATEDIFF(DAY, '2024-01-01', GETDATE()) AS days_since_new_year;


-- ============================================================================
-- 5. NULL HANDLING FUNCTION TRANSLATIONS
-- ============================================================================

-- NVL (Null Value Logic)
-- TERADATA: NVL(column, default_value)
-- FABRIC:   ISNULL(column, default_value) or COALESCE(column, default_value)
SELECT
    player_id,
    COALESCE(bonus_amount, 0) AS bonus_amount,
    ISNULL(loyalty_tier, 'Bronze') AS loyalty_tier
FROM casino.players;

-- NULLIFZERO
-- TERADATA: NULLIFZERO(column)
-- FABRIC:   NULLIF(column, 0)
SELECT
    machine_id,
    NULLIF(coin_out, 0) AS coin_out_null_if_zero
FROM casino.slot_transactions;

-- ZEROIFNULL
-- TERADATA: ZEROIFNULL(column)
-- FABRIC:   ISNULL(column, 0)
SELECT
    player_id,
    ISNULL(total_spend, 0) AS total_spend
FROM casino.player_summary;


-- ============================================================================
-- 6. STRING FUNCTION TRANSLATIONS
-- ============================================================================

-- String Position
-- TERADATA: INDEX(string, substring)
-- FABRIC:   CHARINDEX(substring, string)
SELECT CHARINDEX('@', email) AS at_position
FROM casino.players
WHERE email IS NOT NULL;

-- String Replace
-- TERADATA: OREPLACE(string, old, new)
-- FABRIC:   REPLACE(string, old, new)
SELECT REPLACE(phone_number, '-', '') AS clean_phone
FROM casino.players;

-- Substring
-- TERADATA: SUBSTR(string, start, length)
-- FABRIC:   SUBSTRING(string, start, length)
SELECT SUBSTRING(player_id, 1, 3) AS player_prefix
FROM casino.players;

-- Trim
-- TERADATA: TRIM(string)
-- FABRIC:   TRIM(string) (same in recent SQL Server versions)
SELECT TRIM(first_name) AS first_name
FROM casino.players;


-- ============================================================================
-- 7. CASE EXPRESSION (Same syntax, minor differences)
-- ============================================================================

-- Both Teradata and Fabric support standard CASE expressions
SELECT
    player_id,
    total_spend,
    CASE
        WHEN total_spend >= 10000 THEN 'Platinum'
        WHEN total_spend >= 5000 THEN 'Gold'
        WHEN total_spend >= 1000 THEN 'Silver'
        ELSE 'Bronze'
    END AS loyalty_tier
FROM casino.player_summary;


-- ============================================================================
-- 8. SAMPLE / RANDOM SAMPLING
-- ============================================================================

-- TERADATA: SAMPLE 0.01 (1% sample)
/*
SELECT * FROM casino.large_table SAMPLE 0.01;
*/

-- FABRIC T-SQL: TABLESAMPLE
SELECT * FROM casino.large_table
TABLESAMPLE (1 PERCENT);

-- FABRIC: Random sample with NEWID()
SELECT TOP 1000 *
FROM casino.large_table
ORDER BY NEWID();


-- ============================================================================
-- 9. VOLATILE TABLES to TEMP TABLES
-- ============================================================================

-- TERADATA: Volatile table
/*
CREATE VOLATILE TABLE vt_temp_results (
    player_id VARCHAR(50),
    score DECIMAL(10,2)
) ON COMMIT PRESERVE ROWS;
*/

-- FABRIC T-SQL: Temp table
CREATE TABLE #temp_results (
    player_id VARCHAR(50),
    score DECIMAL(10,2)
);

-- Or for session-scoped:
CREATE TABLE ##global_temp_results (
    player_id VARCHAR(50),
    score DECIMAL(10,2)
);


-- ============================================================================
-- 10. MERGE STATEMENT (Similar syntax)
-- ============================================================================

-- Both Teradata and Fabric support standard MERGE syntax
MERGE INTO casino.player_summary AS target
USING staging.daily_player_stats AS source
ON target.player_id = source.player_id
WHEN MATCHED THEN
    UPDATE SET
        total_spend = target.total_spend + source.daily_spend,
        last_activity = source.activity_date
WHEN NOT MATCHED THEN
    INSERT (player_id, total_spend, last_activity)
    VALUES (source.player_id, source.daily_spend, source.activity_date);


-- ============================================================================
-- 11. WINDOW FUNCTIONS (Mostly compatible)
-- ============================================================================

-- Running totals, moving averages work the same way
SELECT
    player_id,
    transaction_date,
    amount,
    SUM(amount) OVER (
        PARTITION BY player_id
        ORDER BY transaction_date
        ROWS UNBOUNDED PRECEDING
    ) AS running_total,
    AVG(amount) OVER (
        PARTITION BY player_id
        ORDER BY transaction_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS seven_day_avg
FROM casino.player_transactions;


-- ============================================================================
-- 12. RECURSIVE CTE (Same syntax)
-- ============================================================================

-- Both support recursive CTEs with same syntax
WITH RECURSIVE employee_hierarchy AS (
    -- Anchor member
    SELECT
        employee_id,
        manager_id,
        employee_name,
        1 AS level
    FROM hr.employees
    WHERE manager_id IS NULL

    UNION ALL

    -- Recursive member
    SELECT
        e.employee_id,
        e.manager_id,
        e.employee_name,
        h.level + 1
    FROM hr.employees e
    INNER JOIN employee_hierarchy h ON e.manager_id = h.employee_id
)
SELECT * FROM employee_hierarchy
ORDER BY level, employee_name;


-- ============================================================================
-- 13. CAST and CONVERT
-- ============================================================================

-- TERADATA: CAST with FORMAT
/*
SELECT CAST(transaction_date AS FORMAT 'YYYY-MM-DD')
FROM casino.transactions;
*/

-- FABRIC T-SQL: Use FORMAT function
SELECT FORMAT(transaction_date, 'yyyy-MM-dd') AS formatted_date
FROM casino.transactions;

-- Or CONVERT with style codes
SELECT CONVERT(VARCHAR(10), transaction_date, 23) AS formatted_date
FROM casino.transactions;


-- ============================================================================
-- 14. GROUP BY EXTENSIONS
-- ============================================================================

-- TERADATA: GROUP BY with ROLLUP
/*
SELECT
    region,
    machine_type,
    SUM(revenue) AS total_revenue
FROM casino.slot_summary
GROUP BY ROLLUP(region, machine_type);
*/

-- FABRIC T-SQL: Same syntax (standard SQL)
SELECT
    region,
    machine_type,
    SUM(revenue) AS total_revenue
FROM casino.slot_summary
GROUP BY ROLLUP(region, machine_type);

-- CUBE also works the same way
SELECT
    region,
    machine_type,
    SUM(revenue) AS total_revenue
FROM casino.slot_summary
GROUP BY CUBE(region, machine_type);
