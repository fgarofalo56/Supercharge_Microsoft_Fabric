-- ============================================================================
-- Sample Teradata DDL for Migration Practice
-- ============================================================================
-- This script creates sample Teradata table definitions for practicing
-- migration to Microsoft Fabric. These are representative of casino/gaming
-- industry data structures.
-- ============================================================================

-- ============================================================================
-- DATABASE CREATION
-- ============================================================================

CREATE DATABASE CASINO_DW
    AS PERMANENT = 100000000000
    SPOOL = 50000000000;

-- ============================================================================
-- DIMENSION TABLES
-- ============================================================================

-- Player Dimension (SET table - no duplicates)
CREATE SET TABLE CASINO_DW.DIM_PLAYER (
    player_id VARCHAR(50) NOT NULL,
    player_hash CHAR(64),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(20),
    date_of_birth DATE,
    registration_date DATE,
    loyalty_tier VARCHAR(20),
    status VARCHAR(20),
    address_line1 VARCHAR(200),
    city VARCHAR(100),
    state_code CHAR(2),
    postal_code VARCHAR(10),
    country_code CHAR(2),
    created_at TIMESTAMP(6),
    updated_at TIMESTAMP(6)
)
PRIMARY INDEX (player_id)
PARTITION BY RANGE_N(registration_date BETWEEN DATE '2015-01-01' AND DATE '2025-12-31' EACH INTERVAL '1' YEAR);

-- Machine Dimension
CREATE MULTISET TABLE CASINO_DW.DIM_MACHINE (
    machine_id VARCHAR(50) NOT NULL,
    machine_name VARCHAR(100),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    game_theme VARCHAR(100),
    game_type VARCHAR(50),
    denomination DECIMAL(10,2),
    max_bet DECIMAL(10,2),
    payback_percentage DECIMAL(5,2),
    floor_location VARCHAR(50),
    zone VARCHAR(50),
    bank_id VARCHAR(20),
    install_date DATE,
    status VARCHAR(20),
    created_at TIMESTAMP(6),
    updated_at TIMESTAMP(6)
)
PRIMARY INDEX (machine_id);

-- Date Dimension
CREATE MULTISET TABLE CASINO_DW.DIM_DATE (
    date_key INTEGER NOT NULL,
    calendar_date DATE NOT NULL,
    year_number SMALLINT,
    quarter_number SMALLINT,
    month_number SMALLINT,
    week_number SMALLINT,
    day_of_week SMALLINT,
    day_of_month SMALLINT,
    day_of_year SMALLINT,
    day_name VARCHAR(20),
    month_name VARCHAR(20),
    is_weekend CHAR(1),
    is_holiday CHAR(1),
    fiscal_year SMALLINT,
    fiscal_quarter SMALLINT,
    fiscal_month SMALLINT
)
UNIQUE PRIMARY INDEX (date_key);

-- ============================================================================
-- FACT TABLES
-- ============================================================================

-- Slot Transactions Fact (Large volume)
CREATE MULTISET TABLE CASINO_DW.FACT_SLOT_TRANSACTIONS (
    transaction_id BIGINT NOT NULL,
    player_id VARCHAR(50),
    machine_id VARCHAR(50) NOT NULL,
    date_key INTEGER NOT NULL,
    transaction_timestamp TIMESTAMP(6) NOT NULL,
    transaction_type VARCHAR(20),
    denomination DECIMAL(10,2),
    coin_in DECIMAL(12,2),
    coin_out DECIMAL(12,2),
    jackpot_amount DECIMAL(12,2),
    bonus_amount DECIMAL(12,2),
    session_id BIGINT,
    spin_count INTEGER,
    theoretical_hold DECIMAL(12,2),
    actual_hold DECIMAL(12,2)
)
PRIMARY INDEX (transaction_id)
PARTITION BY RANGE_N(transaction_timestamp BETWEEN TIMESTAMP '2020-01-01 00:00:00' AND TIMESTAMP '2025-12-31 23:59:59' EACH INTERVAL '1' MONTH);

-- Player Sessions Fact
CREATE MULTISET TABLE CASINO_DW.FACT_PLAYER_SESSIONS (
    session_id BIGINT NOT NULL,
    player_id VARCHAR(50) NOT NULL,
    date_key INTEGER NOT NULL,
    session_start TIMESTAMP(6) NOT NULL,
    session_end TIMESTAMP(6),
    duration_minutes INTEGER,
    machines_played INTEGER,
    games_played INTEGER,
    total_coin_in DECIMAL(12,2),
    total_coin_out DECIMAL(12,2),
    net_win_loss DECIMAL(12,2),
    comps_earned DECIMAL(10,2),
    points_earned INTEGER,
    bonus_triggered INTEGER,
    jackpots_hit INTEGER
)
PRIMARY INDEX (session_id)
PARTITION BY RANGE_N(session_start BETWEEN TIMESTAMP '2020-01-01 00:00:00' AND TIMESTAMP '2025-12-31 23:59:59' EACH INTERVAL '1' MONTH);

-- Cage Operations Fact (Compliance critical)
CREATE MULTISET TABLE CASINO_DW.FACT_CAGE_OPERATIONS (
    transaction_id BIGINT NOT NULL,
    player_id VARCHAR(50),
    date_key INTEGER NOT NULL,
    transaction_timestamp TIMESTAMP(6) NOT NULL,
    transaction_type VARCHAR(50),
    amount DECIMAL(12,2),
    payment_method VARCHAR(50),
    currency_code CHAR(3),
    window_number VARCHAR(10),
    cashier_id VARCHAR(50),
    shift_id VARCHAR(20),
    supervisor_approved CHAR(1),
    ctr_flag CHAR(1),
    sar_flag CHAR(1),
    notes VARCHAR(500)
)
PRIMARY INDEX (transaction_id)
PARTITION BY RANGE_N(transaction_timestamp BETWEEN TIMESTAMP '2020-01-01 00:00:00' AND TIMESTAMP '2025-12-31 23:59:59' EACH INTERVAL '1' MONTH);

-- ============================================================================
-- VIEWS WITH QUALIFY (Migration Challenge)
-- ============================================================================

-- Latest player session view (uses QUALIFY)
CREATE VIEW CASINO_DW.VW_LATEST_PLAYER_SESSION AS
SELECT
    player_id,
    session_id,
    session_start,
    session_end,
    duration_minutes,
    total_coin_in,
    total_coin_out,
    net_win_loss
FROM CASINO_DW.FACT_PLAYER_SESSIONS
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY player_id
    ORDER BY session_start DESC
) = 1;

-- Top performing machines view
CREATE VIEW CASINO_DW.VW_TOP_MACHINES AS
SELECT TOP 100 WITH TIES
    machine_id,
    game_theme,
    SUM(coin_in) AS total_coin_in,
    SUM(actual_hold) AS total_hold,
    COUNT(DISTINCT player_id) AS unique_players
FROM CASINO_DW.FACT_SLOT_TRANSACTIONS
WHERE transaction_timestamp >= ADD_MONTHS(CURRENT_DATE, -1)
GROUP BY machine_id, game_theme
ORDER BY total_coin_in DESC;

-- Player 360 view (aggregated metrics)
CREATE VIEW CASINO_DW.VW_PLAYER_360 AS
SELECT
    p.player_id,
    p.first_name,
    p.last_name,
    p.loyalty_tier,
    NVL(s.total_sessions, 0) AS total_sessions,
    NVL(s.total_coin_in, 0) AS lifetime_coin_in,
    NVL(s.total_coin_out, 0) AS lifetime_coin_out,
    NVL(s.total_coin_in, 0) - NVL(s.total_coin_out, 0) AS lifetime_theo_win,
    NVL(s.avg_session_duration, 0) AS avg_session_duration,
    s.last_session_date,
    CURRENT_DATE - s.last_session_date AS days_since_last_visit
FROM CASINO_DW.DIM_PLAYER p
LEFT JOIN (
    SELECT
        player_id,
        COUNT(*) AS total_sessions,
        SUM(total_coin_in) AS total_coin_in,
        SUM(total_coin_out) AS total_coin_out,
        AVG(duration_minutes) AS avg_session_duration,
        MAX(CAST(session_start AS DATE)) AS last_session_date
    FROM CASINO_DW.FACT_PLAYER_SESSIONS
    GROUP BY player_id
) s ON p.player_id = s.player_id;

-- ============================================================================
-- STORED PROCEDURES
-- ============================================================================

-- Daily aggregation procedure
REPLACE PROCEDURE CASINO_DW.SP_DAILY_SLOT_SUMMARY(IN p_date DATE)
BEGIN
    -- Delete existing data for the date
    DELETE FROM CASINO_DW.AGG_DAILY_SLOT_SUMMARY
    WHERE summary_date = p_date;

    -- Insert new summary
    INSERT INTO CASINO_DW.AGG_DAILY_SLOT_SUMMARY
    SELECT
        CAST(transaction_timestamp AS DATE) AS summary_date,
        machine_id,
        COUNT(*) AS transaction_count,
        COUNT(DISTINCT player_id) AS unique_players,
        SUM(coin_in) AS total_coin_in,
        SUM(coin_out) AS total_coin_out,
        SUM(jackpot_amount) AS total_jackpots,
        AVG(theoretical_hold) AS avg_theo_hold,
        CURRENT_TIMESTAMP AS created_at
    FROM CASINO_DW.FACT_SLOT_TRANSACTIONS
    WHERE CAST(transaction_timestamp AS DATE) = p_date
    GROUP BY 1, 2;
END;

-- ============================================================================
-- MACROS
-- ============================================================================

-- Compliance check macro
REPLACE MACRO CASINO_DW.MAC_CTR_CHECK(check_date DATE) AS (
    SELECT
        transaction_id,
        player_id,
        transaction_type,
        amount,
        transaction_timestamp,
        'CTR' AS report_type
    FROM CASINO_DW.FACT_CAGE_OPERATIONS
    WHERE CAST(transaction_timestamp AS DATE) = :check_date
      AND amount >= 10000
    ORDER BY amount DESC;
);

-- SAR candidate detection macro
REPLACE MACRO CASINO_DW.MAC_SAR_CANDIDATES(start_date DATE, end_date DATE) AS (
    SELECT
        player_id,
        COUNT(*) AS transaction_count,
        SUM(amount) AS total_amount,
        MIN(transaction_timestamp) AS first_transaction,
        MAX(transaction_timestamp) AS last_transaction
    FROM CASINO_DW.FACT_CAGE_OPERATIONS
    WHERE CAST(transaction_timestamp AS DATE) BETWEEN :start_date AND :end_date
      AND amount BETWEEN 8000 AND 9999.99
    GROUP BY player_id
    HAVING COUNT(*) >= 3
    ORDER BY total_amount DESC;
);

-- ============================================================================
-- SAMPLE DATA GENERATION (for testing)
-- ============================================================================

-- Note: In Teradata, you would typically use BTEQ or TPT for data loading.
-- Below is a simple INSERT for illustration purposes.

-- Sample date dimension population
INSERT INTO CASINO_DW.DIM_DATE
SELECT
    CAST(calendar_date - DATE '1900-01-01' AS INTEGER) AS date_key,
    calendar_date,
    EXTRACT(YEAR FROM calendar_date) AS year_number,
    CASE
        WHEN EXTRACT(MONTH FROM calendar_date) IN (1,2,3) THEN 1
        WHEN EXTRACT(MONTH FROM calendar_date) IN (4,5,6) THEN 2
        WHEN EXTRACT(MONTH FROM calendar_date) IN (7,8,9) THEN 3
        ELSE 4
    END AS quarter_number,
    EXTRACT(MONTH FROM calendar_date) AS month_number,
    CAST((calendar_date - DATE '2020-01-01' + 1) / 7 AS INTEGER) + 1 AS week_number,
    EXTRACT(DAY FROM calendar_date) % 7 + 1 AS day_of_week,
    EXTRACT(DAY FROM calendar_date) AS day_of_month,
    calendar_date - CAST(EXTRACT(YEAR FROM calendar_date) || '-01-01' AS DATE) + 1 AS day_of_year,
    CASE EXTRACT(DAY FROM calendar_date) % 7 + 1
        WHEN 1 THEN 'Sunday'
        WHEN 2 THEN 'Monday'
        WHEN 3 THEN 'Tuesday'
        WHEN 4 THEN 'Wednesday'
        WHEN 5 THEN 'Thursday'
        WHEN 6 THEN 'Friday'
        WHEN 7 THEN 'Saturday'
    END AS day_name,
    CASE EXTRACT(MONTH FROM calendar_date)
        WHEN 1 THEN 'January'
        WHEN 2 THEN 'February'
        WHEN 3 THEN 'March'
        WHEN 4 THEN 'April'
        WHEN 5 THEN 'May'
        WHEN 6 THEN 'June'
        WHEN 7 THEN 'July'
        WHEN 8 THEN 'August'
        WHEN 9 THEN 'September'
        WHEN 10 THEN 'October'
        WHEN 11 THEN 'November'
        WHEN 12 THEN 'December'
    END AS month_name,
    CASE WHEN EXTRACT(DAY FROM calendar_date) % 7 + 1 IN (1, 7) THEN 'Y' ELSE 'N' END AS is_weekend,
    'N' AS is_holiday,
    EXTRACT(YEAR FROM calendar_date) AS fiscal_year,
    CASE
        WHEN EXTRACT(MONTH FROM calendar_date) IN (1,2,3) THEN 1
        WHEN EXTRACT(MONTH FROM calendar_date) IN (4,5,6) THEN 2
        WHEN EXTRACT(MONTH FROM calendar_date) IN (7,8,9) THEN 3
        ELSE 4
    END AS fiscal_quarter,
    EXTRACT(MONTH FROM calendar_date) AS fiscal_month
FROM sys_calendar.calendar
WHERE calendar_date BETWEEN DATE '2020-01-01' AND DATE '2025-12-31';

-- ============================================================================
-- INDEXES (for reference - different approach in Fabric)
-- ============================================================================

-- Secondary indexes in Teradata
CREATE INDEX idx_slot_trans_player ON CASINO_DW.FACT_SLOT_TRANSACTIONS (player_id);
CREATE INDEX idx_slot_trans_machine ON CASINO_DW.FACT_SLOT_TRANSACTIONS (machine_id);
CREATE INDEX idx_cage_ops_player ON CASINO_DW.FACT_CAGE_OPERATIONS (player_id);

-- ============================================================================
-- STATISTICS (for reference - different in Fabric)
-- ============================================================================

COLLECT STATISTICS ON CASINO_DW.DIM_PLAYER COLUMN (player_id);
COLLECT STATISTICS ON CASINO_DW.DIM_PLAYER COLUMN (loyalty_tier);
COLLECT STATISTICS ON CASINO_DW.FACT_SLOT_TRANSACTIONS COLUMN (player_id);
COLLECT STATISTICS ON CASINO_DW.FACT_SLOT_TRANSACTIONS COLUMN (machine_id);
COLLECT STATISTICS ON CASINO_DW.FACT_SLOT_TRANSACTIONS COLUMN (transaction_timestamp);
