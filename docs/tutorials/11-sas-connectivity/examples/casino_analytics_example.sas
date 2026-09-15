/*******************************************************************************
 * Casino Analytics Integration Example
 *******************************************************************************
 *
 * This example demonstrates a complete SAS analytics workflow integrated
 * with Microsoft Fabric for a casino/gaming environment.
 *
 * Workflow:
 *   1. Connect to Fabric Lakehouse (read Gold layer data)
 *   2. Perform player churn analysis in SAS
 *   3. Score players with prediction model
 *   4. Write results back to Fabric Warehouse
 *   5. Generate compliance reports
 *
 * Prerequisites:
 *   - fabric_connection_macros.sas included
 *   - Fabric DSNs configured:
 *       - Fabric_Casino_Lakehouse (read)
 *       - Fabric_Casino_Warehouse (write)
 *
 *******************************************************************************/

/* Include connection macros */
%INCLUDE 'macros/fabric_connection_macros.sas';

/* Set options */
OPTIONS MPRINT MLOGIC SYMBOLGEN;

/*******************************************************************************
 * STEP 1: Connect to Fabric
 *******************************************************************************/

%PUT;
%PUT ============================================================;
%PUT  STEP 1: Establishing Fabric Connections;
%PUT ============================================================;

/* Connect to Lakehouse (read-only for Gold layer data) */
%fabric_connect(
    dsn=Fabric_Casino_Lakehouse,
    libref=gold,
    schema=gold
);

/* Connect to Warehouse (for writing results) */
%fabric_connect(
    dsn=Fabric_Casino_Warehouse,
    libref=output,
    schema=sas_output
);

/* List available tables */
%fabric_list_tables(libref=gold, filter=player);


/*******************************************************************************
 * STEP 2: Read Player 360 Data from Fabric
 *******************************************************************************/

%PUT;
%PUT ============================================================;
%PUT  STEP 2: Reading Player Data from Fabric Gold Layer;
%PUT ============================================================;

/* Read player 360 view with pass-through SQL for efficiency */
%fabric_passthrough(
    libref=gold,
    sql=%str(
        SELECT
            player_id,
            loyalty_tier,
            lifetime_value,
            total_visits,
            avg_session_duration,
            days_since_last_visit,
            favorite_game_type,
            avg_daily_spend,
            CASE
                WHEN days_since_last_visit > 30 THEN 1
                ELSE 0
            END AS churn_flag
        FROM gold.gold_player_360
        WHERE last_activity_date >= DATEADD(YEAR, -1, GETDATE())
    ),
    out=work.player_data
);

/* Summarize the data */
PROC MEANS DATA=work.player_data N MEAN STD MIN MAX;
    VAR lifetime_value total_visits avg_session_duration days_since_last_visit;
    TITLE "Player Data Summary";
RUN;

PROC FREQ DATA=work.player_data;
    TABLES loyalty_tier churn_flag / NOCUM;
    TITLE "Player Distribution";
RUN;


/*******************************************************************************
 * STEP 3: Feature Engineering for Churn Model
 *******************************************************************************/

%PUT;
%PUT ============================================================;
%PUT  STEP 3: Feature Engineering;
%PUT ============================================================;

DATA work.player_features;
    SET work.player_data;

    /* Derived features */
    visit_frequency = total_visits / 365;  /* Visits per day */

    /* Engagement score */
    engagement_score = (total_visits * 0.3) +
                       (avg_session_duration * 0.3) +
                       (avg_daily_spend / 100 * 0.4);

    /* Recency bucket */
    LENGTH recency_bucket $20;
    SELECT;
        WHEN (days_since_last_visit <= 7) recency_bucket = 'Active';
        WHEN (days_since_last_visit <= 14) recency_bucket = 'Recent';
        WHEN (days_since_last_visit <= 30) recency_bucket = 'At Risk';
        OTHERWISE recency_bucket = 'Churned';
    END;

    /* Value segment */
    LENGTH value_segment $20;
    SELECT;
        WHEN (lifetime_value >= 10000) value_segment = 'VIP';
        WHEN (lifetime_value >= 5000) value_segment = 'High';
        WHEN (lifetime_value >= 1000) value_segment = 'Medium';
        OTHERWISE value_segment = 'Low';
    END;

    /* Log transform skewed variables */
    log_ltv = LOG(lifetime_value + 1);
    log_visits = LOG(total_visits + 1);
RUN;

PROC PRINT DATA=work.player_features (OBS=10);
    VAR player_id loyalty_tier engagement_score recency_bucket value_segment;
    TITLE "Sample Feature-Engineered Player Data";
RUN;


/*******************************************************************************
 * STEP 4: Build Churn Prediction Model
 *******************************************************************************/

%PUT;
%PUT ============================================================;
%PUT  STEP 4: Building Churn Prediction Model;
%PUT ============================================================;

/* Split data into training and validation */
PROC SURVEYSELECT DATA=work.player_features
    OUT=work.player_split
    METHOD=SRS
    SAMPRATE=0.7
    SEED=42
    OUTALL;
RUN;

DATA work.train work.validate;
    SET work.player_split;
    IF Selected = 1 THEN OUTPUT work.train;
    ELSE OUTPUT work.validate;
RUN;

/* Build logistic regression model */
PROC LOGISTIC DATA=work.train OUTMODEL=work.churn_model DESCENDING;
    CLASS loyalty_tier value_segment recency_bucket favorite_game_type / PARAM=REF;
    MODEL churn_flag =
        log_ltv
        log_visits
        avg_session_duration
        engagement_score
        loyalty_tier
        value_segment
        recency_bucket
        favorite_game_type
        / SELECTION=STEPWISE
          SLENTRY=0.05
          SLSTAY=0.05
          DETAILS
          LACKFIT;
    OUTPUT OUT=work.train_scored P=churn_probability;
    TITLE "Churn Prediction Model";
RUN;

/* Score validation set */
PROC LOGISTIC INMODEL=work.churn_model;
    SCORE DATA=work.validate OUT=work.validate_scored;
RUN;

/* Evaluate model performance */
PROC FREQ DATA=work.validate_scored;
    TABLES churn_flag * I_churn_flag / NOPERCENT NOCOL;
    TITLE "Confusion Matrix - Validation Set";
RUN;


/*******************************************************************************
 * STEP 5: Score All Players and Prepare Output
 *******************************************************************************/

%PUT;
%PUT ============================================================;
%PUT  STEP 5: Scoring All Players;
%PUT ============================================================;

/* Score all players */
PROC LOGISTIC INMODEL=work.churn_model;
    SCORE DATA=work.player_features OUT=work.all_scored;
RUN;

/* Prepare final output */
DATA work.churn_predictions;
    SET work.all_scored;

    /* Rename probability columns */
    churn_probability = P_1;

    /* Create risk category */
    LENGTH risk_category $20;
    SELECT;
        WHEN (P_1 >= 0.7) risk_category = 'High Risk';
        WHEN (P_1 >= 0.4) risk_category = 'Medium Risk';
        OTHERWISE risk_category = 'Low Risk';
    END;

    /* Add metadata */
    prediction_date = TODAY();
    model_version = 'v1.0';

    FORMAT prediction_date DATE9.;

    KEEP
        player_id
        loyalty_tier
        lifetime_value
        days_since_last_visit
        engagement_score
        value_segment
        churn_probability
        risk_category
        prediction_date
        model_version;
RUN;

PROC PRINT DATA=work.churn_predictions (OBS=20);
    WHERE risk_category = 'High Risk';
    TITLE "High Risk Churners - Top 20";
RUN;


/*******************************************************************************
 * STEP 6: Write Results to Fabric Warehouse
 *******************************************************************************/

%PUT;
%PUT ============================================================;
%PUT  STEP 6: Writing Results to Fabric Warehouse;
%PUT ============================================================;

/* Write churn predictions */
%fabric_write(
    data=work.churn_predictions,
    libref=output,
    table=player_churn_predictions,
    mode=REPLACE
);

/* Create summary by segment */
PROC SQL;
    CREATE TABLE work.segment_summary AS
    SELECT
        value_segment,
        risk_category,
        COUNT(*) AS player_count,
        MEAN(churn_probability) AS avg_churn_prob FORMAT=PERCENT8.2,
        SUM(lifetime_value) AS total_ltv FORMAT=DOLLAR15.2
    FROM work.churn_predictions
    GROUP BY value_segment, risk_category
    ORDER BY value_segment, risk_category;
QUIT;

%fabric_write(
    data=work.segment_summary,
    libref=output,
    table=churn_segment_summary,
    mode=REPLACE
);


/*******************************************************************************
 * STEP 7: Compliance Reporting (CTR/SAR)
 *******************************************************************************/

%PUT;
%PUT ============================================================;
%PUT  STEP 7: Generating Compliance Reports;
%PUT ============================================================;

/* Read cage operations for compliance */
%fabric_passthrough(
    libref=gold,
    sql=%str(
        SELECT
            transaction_id,
            player_id,
            transaction_type,
            amount,
            transaction_timestamp,
            CAST(transaction_timestamp AS DATE) AS transaction_date
        FROM gold.gold_cage_operations
        WHERE transaction_timestamp >= DATEADD(DAY, -1, GETDATE())
          AND transaction_timestamp < GETDATE()
    ),
    out=work.yesterday_transactions
);

/* CTR Report: Transactions >= $10,000 */
DATA work.ctr_report;
    SET work.yesterday_transactions;
    WHERE amount >= 10000;
    report_type = 'CTR';
    report_date = TODAY();
    FORMAT report_date DATE9.;
RUN;

%LET ctr_count = %NOBS(work.ctr_report);
%PUT NOTE: CTR Report generated with &ctr_count. transactions;

/* SAR Candidates: Multiple transactions $8K-$9.9K */
PROC SQL;
    CREATE TABLE work.sar_candidates AS
    SELECT
        player_id,
        COUNT(*) AS transaction_count,
        SUM(amount) AS total_amount FORMAT=DOLLAR15.2,
        MIN(transaction_timestamp) AS first_transaction,
        MAX(transaction_timestamp) AS last_transaction,
        'SAR_CANDIDATE' AS report_type,
        TODAY() AS report_date FORMAT=DATE9.
    FROM work.yesterday_transactions
    WHERE amount BETWEEN 8000 AND 9999.99
    GROUP BY player_id
    HAVING COUNT(*) >= 2;  /* 2+ transactions in suspicious range */
QUIT;

%LET sar_count = %NOBS(work.sar_candidates);
%PUT NOTE: SAR Candidates identified: &sar_count. players;

/* Write compliance reports to Fabric */
%fabric_write(data=work.ctr_report, libref=output, table=ctr_daily_report, mode=APPEND);
%fabric_write(data=work.sar_candidates, libref=output, table=sar_candidates, mode=APPEND);


/*******************************************************************************
 * STEP 8: Generate Summary Report
 *******************************************************************************/

%PUT;
%PUT ============================================================;
%PUT  STEP 8: Final Summary Report;
%PUT ============================================================;

ODS HTML FILE="casino_analytics_report.html";

TITLE1 "Casino Analytics Daily Report";
TITLE2 "Generated: %SYSFUNC(TODAY(), DATE9.)";

PROC PRINT DATA=work.segment_summary NOOBS;
    TITLE3 "Churn Risk by Segment";
RUN;

PROC SGPLOT DATA=work.churn_predictions;
    VBAR risk_category / RESPONSE=lifetime_value STAT=SUM;
    XAXIS LABEL="Risk Category";
    YAXIS LABEL="Total Lifetime Value ($)";
    TITLE3 "Lifetime Value at Risk by Churn Category";
RUN;

PROC PRINT DATA=work.ctr_report (OBS=10) NOOBS;
    TITLE3 "CTR Transactions (Sample)";
RUN;

PROC PRINT DATA=work.sar_candidates NOOBS;
    TITLE3 "SAR Candidates";
RUN;

ODS HTML CLOSE;


/*******************************************************************************
 * STEP 9: Cleanup
 *******************************************************************************/

%PUT;
%PUT ============================================================;
%PUT  STEP 9: Cleanup and Disconnect;
%PUT ============================================================;

/* Clear work datasets */
PROC DATASETS LIBRARY=work NOLIST;
    DELETE player_: train validate churn_: segment_: ctr_: sar_: yesterday_:;
QUIT;

/* Disconnect from Fabric */
%fabric_disconnect(libref=gold);
%fabric_disconnect(libref=output);

%PUT;
%PUT ============================================================;
%PUT  Casino Analytics Workflow Complete;
%PUT ============================================================;
%PUT;
