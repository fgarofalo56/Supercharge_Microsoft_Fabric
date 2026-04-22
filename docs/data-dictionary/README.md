[Home](../index.md) > [Docs](..) > Data Dictionary

# 📖 Data Dictionary

> **Last Updated**: 2026-04-15 | **Version**: 2.0
> **Status**: ✅ Final | **Maintainer**: Documentation Team

<div align="center" markdown>

![Category](https://img.shields.io/badge/Category-Reference-purple)
![Status](https://img.shields.io/badge/Status-Final-green)
![Tables](https://img.shields.io/badge/Tables-Bronze%20%7C%20Silver%20%7C%20Gold-blue)

</div>

---

## 📖 Overview

This data dictionary provides comprehensive documentation for all tables in the Casino Analytics data platform. Each layer (Bronze, Silver, Gold) maintains specific schemas optimized for their purpose.

---

## 📑 Table of Contents

- [Bronze Layer Tables](#bronze-layer-tables)
- [Silver Layer Tables](#silver-layer-tables)
- [Gold Layer Tables](#gold-layer-tables)
- [Real-Time Tables (Eventhouse)](#real-time-tables)
- [Reference Data](#reference-data)

---

## 🥉 Bronze Layer Tables

### bronze_slot_telemetry

**Description:** Raw slot machine event telemetry data
**Update Frequency:** Real-time / Batch (hourly)
**Retention:** 7 years (regulatory requirement)
**Partitioning:** `_year`, `_month`, `_day`

| Column | Data Type | Nullable | Description | Example |
|--------|-----------|----------|-------------|---------|
| event_id | STRING | No | Unique event identifier (UUID) | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| machine_id | STRING | No | Slot machine identifier | `SLT1234` |
| casino_id | STRING | Yes | Casino/property identifier | `CAS001` |
| floor_location | STRING | Yes | Physical location on gaming floor | `A1`, `VIP2` |
| event_timestamp | STRING | No | ISO 8601 timestamp of event | `2024-01-15T14:30:45.123Z` |
| event_type | STRING | No | Type of event | `SPIN`, `WIN`, `JACKPOT`, `CASH_IN`, `CASH_OUT` |
| denomination | DOUBLE | Yes | Machine denomination in dollars | `0.01`, `0.25`, `1.00` |
| bet_amount | DOUBLE | Yes | Amount wagered in dollars | `2.50` |
| win_amount | DOUBLE | Yes | Amount won in dollars | `15.00` |
| jackpot_contribution | DOUBLE | Yes | Progressive jackpot contribution | `0.05` |
| credits_in | INT | Yes | Credits inserted | `100` |
| credits_out | INT | Yes | Credits cashed out | `150` |
| credits_wagered | INT | Yes | Credits bet on spin | `5` |
| credits_won | INT | Yes | Credits won on spin | `20` |
| games_played | INT | Yes | Cumulative games on session | `45` |
| player_id | STRING | Yes | Loyalty card player ID (null if anonymous) | `PLY12345678` |
| session_id | STRING | Yes | Unique session identifier | `uuid` |
| is_bonus_round | BOOLEAN | Yes | Whether spin was during bonus | `true`, `false` |
| rng_seed | STRING | Yes | Random number generator seed | `ABC12345` |
| game_outcome | STRING | Yes | Outcome classification | `WIN`, `LOSS`, `JACKPOT` |
| paytable_version | STRING | Yes | Paytable software version | `PT2.1` |
| firmware_version | STRING | Yes | Machine firmware version | `FW3.2.15` |
| error_code | STRING | Yes | Error code if applicable | `E101`, null |
| door_status | STRING | Yes | Machine door status | `OPEN`, `CLOSED` |
| meter_readings | STRING | Yes | JSON string of meter values | `{"coin_in": 123456, ...}` |
| _ingestion_timestamp | TIMESTAMP | No | When record was ingested | `2024-01-15T14:31:00Z` |
| _source_file | STRING | Yes | Source file path | `raw/slot_telemetry/...` |
| _batch_id | STRING | No | Batch processing identifier | `20240115143100` |
| _record_hash | STRING | No | SHA-256 hash for deduplication | `abc123...` |
| _year | INT | No | Partition: Year | `2024` |
| _month | INT | No | Partition: Month | `1` |
| _day | INT | No | Partition: Day | `15` |

---

### bronze_player_profiles

**Description:** Raw player profile and loyalty data
**Update Frequency:** Daily batch
**Retention:** Active + 7 years after last activity
**Contains PII:** Yes - requires access controls

| Column | Data Type | Nullable | PII | Description |
|--------|-----------|----------|-----|-------------|
| player_id | STRING | No | No | Unique player identifier |
| first_name | STRING | Yes | **Yes** | Player first name |
| last_name | STRING | Yes | **Yes** | Player last name |
| email | STRING | Yes | **Yes** | Email address |
| phone | STRING | Yes | **Yes** | Phone number |
| date_of_birth | STRING | Yes | **Yes** | DOB (YYYY-MM-DD) |
| ssn_last_four | STRING | Yes | **Yes** | Last 4 digits of SSN |
| address_line1 | STRING | Yes | **Yes** | Street address |
| address_line2 | STRING | Yes | **Yes** | Apartment/Suite |
| city | STRING | Yes | No | City |
| state | STRING | Yes | No | State code |
| zip_code | STRING | Yes | **Yes** | ZIP code |
| country | STRING | Yes | No | Country code |
| loyalty_tier | STRING | Yes | No | Current loyalty tier |
| loyalty_points | INT | Yes | No | Current point balance |
| enrollment_date | STRING | Yes | No | Loyalty program enrollment date |
| preferred_property | STRING | Yes | No | Preferred casino property |
| marketing_opt_in | BOOLEAN | Yes | No | Marketing consent flag |
| self_exclusion_status | BOOLEAN | Yes | No | Responsible gaming exclusion |
| responsible_gaming_limit | DOUBLE | Yes | No | Daily/session limit |
| vip_host_id | STRING | Yes | No | Assigned VIP host |
| created_at | STRING | Yes | No | Record creation timestamp |
| updated_at | STRING | Yes | No | Last update timestamp |
| email_hash | STRING | Yes | No | SHA-256 hash of email |
| phone_hash | STRING | Yes | No | SHA-256 hash of phone |
| ssn_hash | STRING | Yes | No | SHA-256 hash of SSN |
| name_hash | STRING | Yes | No | SHA-256 hash of full name |

---

### bronze_financial_transactions

**Description:** Raw financial transaction records (cage, ATM, markers)
**Update Frequency:** Real-time
**Retention:** 7 years (BSA requirement)
**Contains PII:** Yes
**Compliance:** Title 31, BSA, CTR/SAR

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| transaction_id | STRING | No | Unique transaction identifier |
| transaction_type | STRING | No | `CASH_IN`, `CASH_OUT`, `MARKER`, `CHIP_PURCHASE`, `ATM` |
| transaction_timestamp | STRING | No | Transaction date/time |
| player_id | STRING | Yes | Player ID if identified |
| amount | DOUBLE | No | Transaction amount |
| currency | STRING | Yes | Currency code (USD) |
| location | STRING | Yes | Transaction location (cage, ATM ID) |
| employee_id | STRING | Yes | Employee processing transaction |
| payment_method | STRING | Yes | `CASH`, `CHECK`, `WIRE`, `MARKER` |
| source_of_funds | STRING | Yes | Declared source (for large transactions) |
| id_type | STRING | Yes | ID used for verification |
| id_number_hash | STRING | Yes | Hashed ID number |
| ctr_reportable | BOOLEAN | Yes | Exceeds $10,000 threshold |
| suspicious_flag | BOOLEAN | Yes | Flagged for SAR review |

---

## 🥈 Silver Layer Tables

### silver_slot_telemetry

**Description:** Cleansed and validated slot telemetry
**Update Frequency:** Hourly
**Source:** bronze_slot_telemetry

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| event_id | STRING | No | Unique event identifier |
| machine_id | STRING | No | Slot machine identifier |
| casino_id | STRING | No | Casino identifier (defaulted if null) |
| floor_location | STRING | No | Floor location (defaulted if null) |
| event_timestamp | TIMESTAMP | No | Validated timestamp |
| event_type | STRING | No | Event type |
| denomination | DOUBLE | No | Denomination (validated) |
| bet_amount | DOUBLE | No | Bet amount (validated, >= 0) |
| win_amount | DOUBLE | No | Win amount (validated, >= 0) |
| jackpot_contribution | DOUBLE | Yes | Progressive contribution |
| credits_wagered | INT | No | Credits wagered |
| credits_won | INT | No | Credits won |
| player_id | STRING | No | Player ID (ANONYMOUS if null) |
| session_id | STRING | Yes | Session identifier |
| is_bonus_round | BOOLEAN | Yes | Bonus round flag |
| game_outcome | STRING | Yes | WIN/LOSS/JACKPOT |
| is_valid_bet | BOOLEAN | No | Business rule: valid bet |
| is_valid_win | BOOLEAN | No | Business rule: valid win |
| is_large_win | BOOLEAN | No | Win >= $1,200 (W-2G threshold) |
| quality_score | DOUBLE | No | Data quality score (0-1) |
| bronze_ingestion_timestamp | TIMESTAMP | No | Original ingestion time |
| silver_processed_timestamp | TIMESTAMP | No | Silver processing time |
| year | INT | No | Partition column |
| month | INT | No | Partition column |
| day | INT | No | Partition column |

---

### silver_player_master

**Description:** Cleansed player data with SCD Type 2 history
**Update Frequency:** Daily
**SCD Type:** Type 2 (full history)

| Column | Data Type | Description |
|--------|-----------|-------------|
| player_key | STRING | Surrogate key (hash) |
| player_id | STRING | Natural key |
| first_name | STRING | First name (cleansed) |
| last_name | STRING | Last name (cleansed) |
| email_domain | STRING | Email domain only (privacy) |
| city | STRING | City |
| state | STRING | State |
| loyalty_tier | STRING | Loyalty tier |
| loyalty_points | INT | Point balance |
| enrollment_date | DATE | Enrollment date |
| is_vip | BOOLEAN | VIP status flag |
| self_exclusion_status | BOOLEAN | Exclusion status |
| effective_start_date | TIMESTAMP | SCD start date |
| effective_end_date | TIMESTAMP | SCD end date (null if current) |
| is_current | BOOLEAN | Current record flag |
| version | INT | Record version number |

---

## 🥇 Gold Layer Tables

### fact_daily_slot_performance

**Description:** Daily slot machine performance metrics
**Grain:** One row per machine per day
**Update Frequency:** Daily

| Column | Data Type | Description | Business Rule |
|--------|-----------|-------------|---------------|
| machine_id | STRING | Machine identifier | FK to dim_machine |
| casino_id | STRING | Casino identifier | FK to dim_casino |
| floor_location | STRING | Floor section | FK to dim_location |
| denomination | DOUBLE | Machine denomination | |
| play_date | DATE | Date of play | Partition key |
| total_spins | BIGINT | Total spin count | Count of SPIN events |
| total_coin_in | DOUBLE | Total amount wagered | Sum of bet_amount |
| total_coin_out | DOUBLE | Total amount paid | Sum of win_amount |
| net_revenue | DOUBLE | Net win/loss | coin_in - coin_out |
| hold_percentage | DOUBLE | Actual hold % | (net_revenue / coin_in) * 100 |
| theoretical_hold | DOUBLE | Expected hold % | From paytable config |
| unique_players | BIGINT | Distinct players | dcount(player_id) |
| total_sessions | BIGINT | Session count | dcount(session_id) |
| max_single_win | DOUBLE | Largest single win | Max(win_amount) |
| avg_bet_amount | DOUBLE | Average bet size | Avg(bet_amount) |
| jackpot_count | BIGINT | Jackpots hit | Count where win >= 1200 |
| total_jackpot_contribution | DOUBLE | Progressive pool contribution | Sum(jackpot_contribution) |

---

### fact_hourly_revenue

**Description:** Hourly revenue by floor section
**Grain:** One row per casino/location per hour
**Update Frequency:** Hourly

| Column | Data Type | Description |
|--------|-----------|-------------|
| casino_id | STRING | Casino identifier |
| floor_location | STRING | Floor section |
| play_hour | TIMESTAMP | Hour bucket |
| total_transactions | BIGINT | Transaction count |
| hourly_coin_in | DOUBLE | Hour's total wagered |
| hourly_coin_out | DOUBLE | Hour's total paid |
| hourly_net_revenue | DOUBLE | Hour's net revenue |
| active_machines | BIGINT | Distinct machines |
| active_players | BIGINT | Distinct players |
| revenue_per_machine | DOUBLE | Avg revenue/machine |

---

### dim_machine

**Description:** Machine dimension (Type 1 - overwrite)
**Grain:** One row per machine

| Column | Data Type | Description |
|--------|-----------|-------------|
| machine_key | STRING | Surrogate key |
| machine_id | STRING | Natural key |
| casino_id | STRING | Casino location |
| floor_location | STRING | Floor section |
| denomination | DOUBLE | Denomination |
| effective_date | DATE | Record date |
| is_current | BOOLEAN | Current flag |

---

### dim_player

**Description:** Player dimension (Type 2 - history)
**Grain:** One row per player per version

| Column | Data Type | Description |
|--------|-----------|-------------|
| player_key | STRING | Surrogate key |
| player_id | STRING | Natural key |
| loyalty_tier | STRING | Tier at version |
| is_vip | BOOLEAN | VIP status |
| home_casino | STRING | Preferred property |
| enrollment_date | DATE | Original enrollment |
| effective_start | TIMESTAMP | Version start |
| effective_end | TIMESTAMP | Version end |
| is_current | BOOLEAN | Current version |

---

## ⚡ Real-Time Tables

### SlotTelemetry (Eventhouse)

**Description:** Real-time slot telemetry in KQL database
**Retention:** 30 days hot, 90 days warm
**Ingestion:** Eventstream from Event Hubs

| Column | Data Type | Description |
|--------|-----------|-------------|
| EventId | string | Event identifier |
| MachineId | string | Machine identifier |
| CasinoId | string | Casino identifier |
| FloorLocation | string | Floor location |
| EventTimestamp | datetime | Event time |
| EventType | string | Event type |
| BetAmount | real | Bet amount |
| WinAmount | real | Win amount |
| PlayerId | string | Player ID |
| SessionId | string | Session ID |

---

## 📚 Reference Data

### ref_loyalty_tiers

| tier_code | tier_name | points_min | points_max | benefits |
|-----------|-----------|------------|------------|----------|
| BRZ | Bronze | 0 | 999 | Basic |
| SLV | Silver | 1000 | 4999 | 5% bonus |
| GLD | Gold | 5000 | 19999 | 10% bonus, free parking |
| PLT | Platinum | 20000 | 49999 | 15% bonus, room upgrades |
| DMD | Diamond | 50000 | NULL | 20% bonus, VIP host |

### ref_event_types

| event_code | event_name | description |
|------------|------------|-------------|
| SPIN | Game Spin | Regular game play |
| WIN | Win | Any winning outcome |
| JACKPOT | Jackpot | Progressive jackpot hit |
| BONUS_START | Bonus Start | Bonus round begins |
| BONUS_END | Bonus End | Bonus round ends |
| CASH_IN | Cash In | Money inserted |
| CASH_OUT | Cash Out | Ticket printed |
| CARD_IN | Card Insert | Loyalty card inserted |
| CARD_OUT | Card Remove | Loyalty card removed |
| DOOR_OPEN | Door Open | Machine door opened |
| DOOR_CLOSE | Door Close | Machine door closed |

---

## 📝 Glossary

| Term | Definition |
|------|------------|
| **Coin In** | Total amount wagered by players |
| **Coin Out** | Total amount paid to players |
| **Hold** | Net revenue as percentage of coin in |
| **Theoretical Hold** | Expected hold based on paytable mathematics |
| **CTR** | Currency Transaction Report (>$10,000) |
| **SAR** | Suspicious Activity Report |
| **W-2G** | IRS form for gambling winnings >=$1,200 |
| **MICS** | Minimum Internal Control Standards |
| **Progressive** | Jackpot that increases with play |
| **Denomination** | Base credit value of machine |

---

---

## 🔗 Related Documents

| Document | Description |
|----------|-------------|
| [Architecture Overview](../diagrams/architecture-overview.md) | System architecture and data flow diagrams |
| [Compliance Templates](../compliance-templates/README.md) | Regulatory compliance report templates |
| [Medallion Architecture](../best-practices/medallion-architecture-deep-dive.md) | Bronze/Silver/Gold patterns deep dive |
| [Best Practices](../best-practices/README.md) | Data engineering best practices |

---

[⬆️ Back to Top](#-data-dictionary) | [📚 Parent](./) | [🏠 Home](../index.md)
