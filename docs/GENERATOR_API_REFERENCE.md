# Generator API Reference

[Home](../README.md) > [Docs](./README.md) > Generator API Reference

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![Python](https://img.shields.io/badge/python-3.11%2B-green) ![Generators](https://img.shields.io/badge/generators-19-orange)

**TL;DR** -- This document covers all 19 data generators in the `data-generation/generators/` package. Every generator inherits from `BaseGenerator`, which provides reproducible seeding, output serialization (DataFrame, Parquet, JSON), batch iteration, and PII masking helpers. Generators span four domains: Casino/Gaming (6), Federal Agency (7), Analytics (3), and Streaming (3).

---

## Table of Contents

1. [BaseGenerator Interface](#-basegenerator-interface)
2. [Casino Generators](#-casino-generators)
   - [SlotMachineGenerator](#slotmachinegenerator)
   - [PlayerGenerator](#playergenerator)
   - [FinancialGenerator](#financialgenerator)
   - [ComplianceGenerator](#compliancegenerator)
   - [SecurityGenerator](#securitygenerator)
   - [TableGamesGenerator](#tablegamesgenerator)
3. [Federal Generators](#-federal-generators)
   - [USDAGenerator](#usdagenerator)
   - [SBAGenerator](#sbagenerator)
   - [NOAAGenerator](#noaagenerator)
   - [EPAGenerator](#epagenerator)
   - [DOIGenerator](#doigenerator)
   - [TribalHealthcareGenerator](#tribalhealthcaregenerator)
   - [DOTFAAGenerator](#dotfaagenerator)
4. [Analytics Generators](#-analytics-generators)
   - [VideoAnalyticsGenerator](#videoanalyticsgenerator)
   - [PeopleMovementGenerator](#peoplemoovementgenerator)
   - [GeolocationGenerator](#geolocationgenerator)
5. [Streaming Generators](#-streaming-generators)
   - [EventHubProducer](#eventhubproducer)
   - [MultiSourceSimulator](#multisourcesimulator)
   - [IoTDeviceSimulator](#iotdevicesimulator)
6. [Extension Guide](#-extension-guide)
7. [Return Value Schemas](#-return-value-schemas)

---

## # BaseGenerator Interface

**Module:** `data-generation/generators/base_generator.py`
**Type:** Abstract base class (ABC)

All generators inherit from `BaseGenerator`. It provides seed management, output serialization, batch iteration, and helper utilities.

### Constructor

```python
BaseGenerator(
    seed: int | None = None,
    locale: str = "en_US",
    start_date: datetime | None = None,
    end_date: datetime | None = None,
)
```

| Parameter    | Type              | Default             | Description                                    |
|-------------|-------------------|---------------------|------------------------------------------------|
| `seed`       | `int \| None`     | `42`                | Non-negative integer for reproducibility       |
| `locale`     | `str`             | `"en_US"`           | Faker locale for generated text                |
| `start_date` | `datetime \| None`| now - 30 days       | Start of the date range for generated data     |
| `end_date`   | `datetime \| None`| now                 | End of the date range for generated data       |

**Raises:** `ValueError` if `seed` is negative or `start_date > end_date`.

### Abstract Method

```python
@abstractmethod
def generate_record(self) -> dict[str, Any]:
    """Generate a single record. Must be implemented by subclasses."""
```

### Core Methods

#### `generate(num_records, show_progress=True) -> pd.DataFrame`

Generate multiple records into a DataFrame.

| Parameter      | Type   | Default | Description                        |
|---------------|--------|---------|-------------------------------------|
| `num_records`  | `int`  | --      | Number of records (must be > 0)     |
| `show_progress`| `bool` | `True`  | Show tqdm progress bar              |

**Returns:** `pd.DataFrame` containing generated records.
**Raises:** `ValueError` if `num_records` is not a positive integer.

#### `generate_batches(num_records, batch_size=10000, show_progress=True) -> Iterator[pd.DataFrame]`

Memory-efficient batch generator.

| Parameter      | Type   | Default  | Description                          |
|---------------|--------|----------|---------------------------------------|
| `num_records`  | `int`  | --       | Total record count (must be > 0)      |
| `batch_size`   | `int`  | `10000`  | Records per batch (must be > 0)       |
| `show_progress`| `bool` | `True`   | Print batch progress messages         |

**Yields:** `pd.DataFrame` batches.
**Raises:** `ValueError` if either argument is not a positive integer.

#### `to_parquet(df, output_path, partition_cols=None) -> None`

Save a DataFrame to Parquet format.

| Parameter       | Type                 | Default | Description                     |
|----------------|----------------------|---------|---------------------------------|
| `df`            | `pd.DataFrame`       | --      | DataFrame to save               |
| `output_path`   | `str \| Path`        | --      | Output file or directory path   |
| `partition_cols` | `list[str] \| None` | `None`  | Columns to partition by         |

**Raises:** `OSError` if the output path is not writable.

#### `to_json(df, output_path, orient="records", lines=True) -> None`

Save a DataFrame to JSON format.

| Parameter     | Type          | Default     | Description                     |
|--------------|---------------|-------------|---------------------------------|
| `df`          | `pd.DataFrame`| --          | DataFrame to save               |
| `output_path` | `str \| Path` | --          | Output file path                |
| `orient`      | `str`         | `"records"` | JSON orientation                |
| `lines`       | `bool`        | `True`      | Write as JSON lines             |

**Raises:** `OSError` if the output path is not writable.

### Properties

```python
@property
def schema(self) -> dict[str, str]:
    """Return the schema definition for this generator."""
```

### Helper Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `random_datetime` | `(start=None, end=None) -> datetime` | Random datetime within configured or specified range |
| `generate_uuid` | `() -> str` | Generate a UUID v4 string |
| `hash_value` | `(value: str, salt: str = "") -> str` | SHA-256 hash of a value |
| `mask_ssn` | `(ssn: str) -> str` | Mask SSN to `XXX-XX-1234` format |
| `mask_card_number` | `(card_number: str) -> str` | Mask card to `****-****-****-1234` |
| `weighted_choice` | `(choices, weights) -> Any` | Weighted random selection (weights must sum to ~1.0) |
| `add_metadata_columns` | `(record: dict) -> dict` | Append `_ingested_at`, `_source`, `_batch_id` |

> **Note:** Every `generate_record()` call appends three metadata columns via `add_metadata_columns`: `_ingested_at` (ISO timestamp), `_source` (class name), and `_batch_id` (8-char UUID prefix).

---

## # Casino Generators

Six generators covering the core casino/gaming domain: slot telemetry, player profiles, cage financials, compliance filings, security events, and table game transactions.

---

### SlotMachineGenerator

**Module:** `data-generation/generators/slot_machine_generator.py`
**Purpose:** Generates SAS-protocol slot machine telemetry events.

#### Constructor

```python
SlotMachineGenerator(
    num_machines: int = 500,
    seed: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
)
```

| Parameter      | Type   | Default | Description                          |
|---------------|--------|---------|---------------------------------------|
| `num_machines` | `int`  | `500`   | Number of slot machines to simulate   |

#### Event Types (enum values)

`GAME_PLAY`, `JACKPOT`, `METER_UPDATE`, `DOOR_OPEN`, `DOOR_CLOSE`, `BILL_IN`, `TICKET_OUT`, `TILT`, `POWER_OFF`, `POWER_ON`

**Weights:** GAME_PLAY dominates at 70%, JACKPOT at 2%, METER_UPDATE at 10%.

#### Record Schema Fields

`event_id`, `machine_id`, `asset_number`, `location_id`, `zone`, `event_type`, `event_timestamp`, `denomination`, `coin_in`, `coin_out`, `jackpot_amount`, `games_played`, `theoretical_hold`, `actual_hold`, `player_id`, `session_id`, `machine_type`, `manufacturer`, `game_theme`, `error_code`, `error_message`

#### Valid Enums

- **MACHINE_TYPES:** `Video Slots`, `Mechanical Reels`, `Video Poker`, `Progressive`
- **DENOMINATIONS:** `0.01` through `100.00` (10 values)
- **MANUFACTURERS:** `IGT`, `Aristocrat`, `Konami`, `Scientific Games`, `Everi`
- **ZONES:** `North`, `South`, `East`, `West`, `VIP`, `High Limit`, `Penny`

#### Domain-Specific Methods

- `get_machines() -> list[dict]` -- Returns the pre-generated machine configuration list.

#### Usage Example

```python
from data_generation.generators.slot_machine_generator import SlotMachineGenerator

gen = SlotMachineGenerator(num_machines=200, seed=42)
df = gen.generate(10_000)
gen.to_parquet(df, "output/slot_telemetry.parquet", partition_cols=["zone"])
```

---

### PlayerGenerator

**Module:** `data-generation/generators/player_generator.py`
**Purpose:** Generates player profiles with loyalty tiers and PII handling.

#### Constructor

```python
PlayerGenerator(
    seed: int | None = None,
    include_pii: bool = False,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
)
```

| Parameter     | Type   | Default | Description                                      |
|--------------|--------|---------|--------------------------------------------------|
| `include_pii` | `bool` | `False` | If `True`, include raw PII; if `False`, mask/hash |

#### Record Schema Fields

`player_id`, `loyalty_number`, `first_name`, `last_name`, `email`, `phone`, `date_of_birth`, `ssn_hash`, `ssn_masked`, `address`, `city`, `state`, `zip_code`, `country`, `loyalty_tier`, `points_balance`, `lifetime_points`, `tier_credits`, `enrollment_date`, `last_visit_date`, `total_visits`, `total_theo`, `total_actual_win_loss`, `average_daily_theo`, `preferred_game`, `communication_preference`, `marketing_opt_in`, `marketing_channel`, `host_assigned`, `vip_flag`, `self_excluded`, `account_status`

#### Valid Enums

- **LOYALTY_TIERS:** `Bronze` (40%), `Silver` (30%), `Gold` (18%), `Platinum` (9%), `Diamond` (3%)
- **PREFERRED_GAMES:** `Video Slots`, `Blackjack`, `Craps`, `Roulette`, `Poker`, `Baccarat`, `Video Poker`
- **ACCOUNT_STATUS:** `Active` (85%), `Inactive` (10%), `Suspended` (3%), `Closed` (2%)

#### Domain-Specific Methods

```python
def generate_with_history(
    num_players: int,
    history_days: int = 30,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate players with historical visit data.
    Returns: (players_df, visits_df)"""
```

#### Usage Example

```python
gen = PlayerGenerator(seed=42, include_pii=False)
players_df, visits_df = gen.generate_with_history(500, history_days=60)
```

---

### FinancialGenerator

**Module:** `data-generation/generators/financial_generator.py`
**Purpose:** Generates cage and financial transaction data with CTR and SAR flagging.

#### Constructor

```python
FinancialGenerator(
    seed: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
)
```

No additional parameters beyond `BaseGenerator`.

#### Transaction Types (14 types, weighted)

`CASH_IN` (20%), `CASH_OUT` (18%), `CHIP_PURCHASE` (15%), `CHIP_REDEMPTION` (12%), `WIRE_TRANSFER_IN` (3%), `WIRE_TRANSFER_OUT` (2%), `CHECK_CASHING` (8%), `MARKER_ISSUE` (5%), `MARKER_PAYMENT` (5%), `FRONT_MONEY_DEPOSIT` (4%), `FRONT_MONEY_WITHDRAWAL` (3%), `JACKPOT_PAYOUT` (3%), `SAFEKEEPING_DEPOSIT` (1%), `SAFEKEEPING_WITHDRAWAL` (1%)

#### Record Schema Fields

`transaction_id`, `transaction_type`, `transaction_timestamp`, `cage_location`, `cashier_id`, `supervisor_id`, `player_id`, `amount`, `currency`, `payment_method`, `check_number`, `wire_reference`, `marker_number`, `id_type`, `id_number_hash`, `ctr_required`, `ctr_filed`, `ctr_reference`, `suspicious_activity_flag`, `notes`, `shift`, `business_date`

> **Important:** The `ctr_required` flag is automatically set to `True` for transactions >= $10,000. SAR structuring detection flags amounts in the $8,000-$9,999 range at a 10% rate.

---

### ComplianceGenerator

**Module:** `data-generation/generators/compliance_generator.py`
**Purpose:** Generates CTR, SAR, and W-2G regulatory filings.

#### Constructor

```python
ComplianceGenerator(
    seed: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
)
```

#### Filing Types

- **CTR** (40%) -- Currency Transaction Reports >= $10,000; filed within 15 days
- **SAR** (15%) -- Suspicious Activity Reports; filed within 30 days
- **W2G** (45%) -- Gambling Winnings (IRS Form W-2G)

#### W-2G Thresholds

| Game Type         | Threshold |
|-------------------|-----------|
| Slots             | $1,200    |
| Video Poker       | $1,200    |
| Keno              | $1,500    |
| Bingo             | $1,200    |
| Poker Tournament  | $5,000    |
| Table Games       | $600      |

#### SAR Categories

`Structuring`, `Unusual Transaction Pattern`, `Third Party Activity`, `Identity Concerns`, `Employee Involvement`, `Counterfeit Currency`, `Wire Transfer Anomaly`, `Chip Walking`, `Credit Abuse`, `Other Suspicious Activity`

#### Domain-Specific Methods

```python
def generate_structuring_pattern(
    player_id: str,
    num_transactions: int = 5,
    target_total: float = 25000,
) -> list[dict[str, Any]]:
    """Generate a structuring pattern for SAR detection testing.
    Each transaction stays just under the $10K threshold."""
```

---

### SecurityGenerator

**Module:** `data-generation/generators/security_generator.py`
**Purpose:** Generates security and surveillance events including access control, camera alerts, and incident reports.

#### Constructor

```python
SecurityGenerator(
    num_employees: int = 500,
    seed: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
)
```

| Parameter       | Type  | Default | Description                          |
|----------------|-------|---------|---------------------------------------|
| `num_employees` | `int` | `500`   | Number of employees for badge events  |

#### Event Types (20 types)

`BADGE_SWIPE` (20%), `DOOR_ENTRY` (15%), `ACCESS_GRANTED` (10%), `ACCESS_DENIED` (5%), `CAMERA_ALERT` (8%), `MOTION_DETECTED` (6%), `CAMERA_OBSTRUCTION` (2%), `EXCLUSION_CHECK` (3%), `EXCLUSION_VIOLATION` (1%), `INCIDENT_REPORT` (5%), `ALTERCATION` (2%), `MEDICAL_EMERGENCY` (2%), `THREAT_DETECTED` (1%), `WEAPON_DETECTED` (1%), `TRESPASS` (2%), `UNAUTHORIZED_ACCESS` (3%), `SUSPICIOUS_ACTIVITY` (4%), `PATRON_COMPLAINT` (3%), `ESCORT_REQUEST` (2%), `SECURITY_PATROL` (5%)

#### Severity Levels

`CRITICAL` (WEAPON_DETECTED, THREAT_DETECTED, EXCLUSION_VIOLATION), `HIGH` (ALTERCATION, MEDICAL_EMERGENCY, TRESPASS, UNAUTHORIZED_ACCESS), `MEDIUM` (INCIDENT_REPORT, SUSPICIOUS_ACTIVITY, ACCESS_DENIED, CAMERA_OBSTRUCTION), `LOW` (all others)

#### Zones (14)

`Main Floor`, `Cage`, `Count Room`, `Vault`, `Surveillance Room`, `Server Room`, `Executive Offices`, `Employee Entrance`, `Loading Dock`, `Parking Garage`, `Hotel Lobby`, `Restaurant`, `Bar`, `Retail`

---

### TableGamesGenerator

**Module:** `data-generation/generators/table_games_generator.py`
**Purpose:** Generates table game transactions, player ratings, and dealer assignments.

#### Constructor

```python
TableGamesGenerator(
    num_tables: int = 100,
    seed: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
)
```

| Parameter    | Type  | Default | Description                     |
|-------------|-------|---------|---------------------------------|
| `num_tables` | `int` | `100`   | Number of tables to simulate    |

#### Game Types and House Edges

| Game Type   | Weight | House Edge |
|-------------|--------|------------|
| Blackjack   | 35%    | 0.5%       |
| Craps       | 20%    | 1.4%       |
| Roulette    | 15%    | 5.3%       |
| Baccarat    | 15%    | 1.06%      |
| Poker       | 10%    | 2.5% (rake)|
| Pai Gow     | 5%     | 2.6%       |

#### Event Types (10 types)

`BUY_IN` (25%), `CASH_OUT` (20%), `MARKER_ISSUED` (5%), `MARKER_PAID` (5%), `FILL` (8%), `CREDIT` (7%), `RATING_START` (12%), `RATING_END` (12%), `SHIFT_START` (3%), `SHIFT_END` (3%)

---

## # Federal Generators

Seven generators covering federal agency data: USDA, SBA, NOAA, EPA, DOI, Tribal Healthcare (IHS), and DOT/FAA. Federal generators use a `domain` parameter on `generate_record()` to select between sub-domains within the same agency.

---

### USDAGenerator

**Module:** `data-generation/generators/federal/usda_generator.py`
**Domains:** `crop_production` (default), `food_safety`

#### Constructor

```python
USDAGenerator(
    seed: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
)
```

#### `generate_record(domain="crop_production")`

**Domain `crop_production`** -- NASS QuickStats-style records.

Key fields: `record_id`, `commodity`, `year`, `state_fips`, `state_name`, `county_fips`, `county_name`, `statisticcat_desc`, `unit_desc`, `value`, `cv_percent`, `source_desc`, `agg_level_desc`, `domain_desc`, `reference_period_desc`, `load_time`

Commodities: `CORN` (28%), `SOYBEANS` (24%), `WHEAT` (16%), `COTTON` (7%), `RICE` (5%), `BARLEY` (5%), `OATS` (4%), `SORGHUM` (4%), `HAY` (4%), `POTATOES` (3%)

**Domain `food_safety`** -- FSIS recall records.

Key fields: `recall_id`, `recall_number`, `recall_date`, `product_type`, `recall_class`, `reason`, `risk_level`, `company_name`, `establishment_number`, `city`, `state`, `pounds_recalled`, `distribution`, `status`, `load_time`

#### `generate_batch(count=1000, domain="crop_production") -> pd.DataFrame`

---

### SBAGenerator

**Module:** `data-generation/generators/federal/sba_generator.py`
**Domains:** `ppp`, `7a`, `disaster`, `sbir`

#### Constructor

```python
SBAGenerator(
    seed: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
)
```

#### `generate_record(domain="ppp")`

Key fields: `loan_id`, `program_type`, `loan_amount`, `approval_date`, `borrower_name`, `borrower_city`, `borrower_state`, `borrower_zip`, `naics_code`, `naics_description`, `jobs_retained`, `lender_name`, `sba_office`, `loan_status`, `forgiveness_amount`, `forgiveness_date`, `term_months`, `interest_rate`, `rural_urban`, `business_type`, `load_time`

| Domain     | Program Type | Interest Rate | Term Range     | Loan Amount Range    |
|-----------|-------------|---------------|----------------|----------------------|
| `ppp`      | PPP          | 1.0% fixed    | 24 or 60 months | $20K - $10M         |
| `7a`       | 7A           | 5.5% - 8.0%  | 60-300 months   | $5K - $5M           |
| `disaster` | DISASTER     | 2.0% - 4.0%  | 360 months      | $1K - $2M           |
| `sbir`     | SBIR         | 0.0%          | 12-36 months    | $50K - $1.5M        |

> **Note:** PPP domain includes `forgiveness_amount` and `forgiveness_date` fields. Approximately 88% of PPP loans receive full forgiveness.

#### `generate_batch(count=1000, domain="ppp") -> list[dict]`

---

### NOAAGenerator

**Module:** `data-generation/generators/federal/noaa_generator.py`
**Domains:** `weather` (default), `storm`

#### Constructor

```python
NOAAGenerator(**kwargs)  # Passes all kwargs to BaseGenerator
```

#### `generate_record(domain="weather")`

**Domain `weather`** -- Surface station observations from 18 real US ASOS/AWOS stations.

Key fields: `observation_id`, `station_id`, `station_name`, `timestamp`, `latitude`, `longitude`, `elevation_m`, `parameter`, `value`, `unit`, `quality_flag`, `data_source`, `report_type`, `load_time`

Parameters: `TEMPERATURE` (F), `DEWPOINT` (F), `HUMIDITY` (PCT), `WIND_SPEED` (MPH), `WIND_DIRECTION` (DEG), `PRESSURE` (IN_HG), `VISIBILITY` (MI), `PRECIPITATION` (IN), `CLOUD_COVER` (PCT)

**Domain `storm`** -- Storm Events Database records.

Key fields: `event_id`, `episode_id`, `event_type`, `state`, `state_fips`, `county_fips`, `begin_date`, `end_date`, `injuries_direct`, `injuries_indirect`, `deaths_direct`, `deaths_indirect`, `damage_property`, `damage_crops`, `magnitude`, `magnitude_type`, `begin_lat`, `begin_lon`, `end_lat`, `end_lon`, `tor_f_scale`, `source`, `flood_cause`, `load_time`

Storm event types: `THUNDERSTORM_WIND` (30%), `HAIL` (25%), `FLASH_FLOOD` (15%), `TORNADO` (10%), and 10 more.

#### Overridden `generate(num_records, show_progress=True, domain="weather") -> pd.DataFrame`

The `generate()` method accepts a `domain` parameter (unlike base class).

---

### EPAGenerator

**Module:** `data-generation/generators/federal/epa_generator.py`
**Domains:** `air_quality` (default), `water_quality`

#### Constructor

```python
EPAGenerator(
    seed: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    domain: str = "air_quality",
)
```

| Parameter | Type  | Default        | Description                                |
|----------|-------|----------------|--------------------------------------------|
| `domain`  | `str` | `"air_quality"` | Default domain for `generate_record()` calls |

#### `generate_record(domain=None)`

If `domain` is `None`, uses the default set at construction.

**Domain `air_quality`** -- AQS monitoring site measurements.

Key fields: `record_id`, `site_id`, `site_name`, `parameter`, `parameter_code`, `date_local`, `time_local`, `aqi_value`, `aqi_category`, `concentration`, `units`, `sample_duration`, `latitude`, `longitude`, `state_code`, `county_code`, `state_name`, `county_name`, `cbsa_name`, `method_code`, `load_time`

Air quality parameters: `PM2.5`, `PM10`, `OZONE`, `CO`, `SO2`, `NO2`, `LEAD`

AQI categories: `GOOD` (0-50, ~55%), `MODERATE` (51-100, ~30%), `UNHEALTHY_SENSITIVE` (101-150, ~10%), `UNHEALTHY` (151-200, ~4%), `VERY_UNHEALTHY`/`HAZARDOUS` (201-500, ~1%)

**Domain `water_quality`** -- SDWIS public water system sample results.

Key fields: `record_id`, `system_id`, `system_name`, `system_type`, `sample_date`, `contaminant`, `contaminant_code`, `result_value`, `unit`, `mcl`, `mcl_violation`, `violation_type`, `state_code`, `county_served`, `population_served`, `source_type`, `primacy_agency`, `load_time`

Contaminants: `Arsenic`, `Lead`, `Nitrate`, `Fluoride`, `Copper`, `Coliform`, `Turbidity`, `Chlorine Residual`, `Trihalomethanes`, `Radium-226`

> **Important:** Approximately 5% of water quality records will have MCL violations (`mcl_violation=True`).

---

### DOIGenerator

**Module:** `data-generation/generators/federal/doi_generator.py`
**Domains:** `earthquake` (default), `land_use`

#### Constructor

```python
DOIGenerator(
    seed: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
)
```

#### `generate_record(domain="earthquake")`

**Domain `earthquake`** -- USGS ComCat-style seismic event records.

Key fields: `event_id`, `usgs_id`, `time`, `latitude`, `longitude`, `depth_km`, `magnitude`, `mag_type`, `place`, `event_type`, `status`, `tsunami`, `significance`, `felt`, `cdi`, `mmi`, `alert`, `net`, `nst`, `gap`, `rms`, `url`, `load_time`

Magnitude distribution (Gutenberg-Richter): M1-3 (60%), M3-5 (25%), M5-6 (10%), M6-7 (4%), M7+ (1%)

Seismic zones: US West Coast (28%), Alaska (22%), Japan (12%), Central America (9%), South America (8%), and 5 others.

**Domain `land_use`** -- BLM/NPS/FWS/USFS parcel management records.

Key fields: `parcel_id`, `blm_serial_number`, `managing_agency`, `state`, `county`, `land_type`, `total_acres`, `latitude`, `longitude`, `designation`, `designation_date`, `permit_type`, `permit_holder`, `annual_revenue`, `environmental_assessment`, `protected_species_present`, `fire_risk_level`, `last_inspection_date`, `load_time`

Managing agencies: `BLM` (35%), `USFS` (25%), `NPS` (15%), `FWS` (10%), `BOR` (8%), `DOD` (5%), `OTHER` (2%)

#### `generate_batch(count=1000, domain="earthquake") -> pd.DataFrame`

---

### TribalHealthcareGenerator

**Module:** `data-generation/generators/federal/tribal_healthcare_generator.py`
**Domains:** Single domain (IHS healthcare encounters)

#### Constructor

```python
TribalHealthcareGenerator(
    seed: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
)
```

#### `generate_record() -> dict[str, Any]`

No `domain` parameter. Generates IHS encounter records across 20 facilities, 12 area offices, and 30 tribal affiliations.

Key fields: `record_id`, `patient_id`, `facility_id`, `facility_name`, `encounter_type`, `encounter_date`, `icd10_code`, `icd10_description`, `cpt_code`, `cpt_description`, `provider_id`, `provider_type`, `tribal_affiliation`, `service_unit`, `area_office`, `age_group`, `gender`, `insurance_type`, `medication_name`, `medication_ndc`, `lab_test_name`, `lab_result_value`, `lab_result_unit`, `lab_abnormal_flag`, `hipaa_consent`, `phi_masked`, `load_time`

#### Encounter Types

`outpatient` (35%), `inpatient` (8%), `emergency` (10%), `telehealth` (7%), `dental` (12%), `behavioral_health` (8%), `pharmacy` (12%), `laboratory` (8%)

#### Diagnosis Weighting (ICD-10, reflecting Native American health disparities)

| Category           | Weight | Example Codes           |
|-------------------|--------|-------------------------|
| Diabetes           | 17%    | E11.9, E11.65, E11.22   |
| Respiratory        | 14%    | J06.9, J45.20, J45.40   |
| Cardiovascular     | 12%    | I10, E78.5, I25.10      |
| Behavioral Health  | 12%    | F32.1, F10.20, F10.10   |
| Metabolic/Obesity  | 10%    | E66.01, E66.9           |
| Musculoskeletal    | 10%    | M54.5, M54.2, M25.50   |
| Gastrointestinal   | 8%     | K21.0, K58.9            |
| Genitourinary      | 7%     | N39.0                   |
| Dental             | 6%     | K02.9                   |
| Pregnancy          | 4%     | O24.11                  |

> **Note:** All records have `hipaa_consent=True` and `phi_masked=True` to reflect HIPAA-compliant de-identified data.

#### `generate_batch(count=1000) -> pd.DataFrame`

---

### DOTFAAGenerator

**Module:** `data-generation/generators/federal/dot_faa_generator.py`
**Domains:** `flight_operations` (default), `safety_incident`, `traffic_statistics`, `infrastructure`

#### Constructor

```python
DOTFAAGenerator(
    seed: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
)
```

#### `generate_record(domain="flight_operations")`

**Domain `flight_operations`** -- BTS On-Time Performance records with 20 carriers and 30 airports.

Key fields: `record_id`, `data_domain`, `carrier_code`, `carrier_name`, `flight_number`, `origin_airport`, `destination_airport`, `departure_date`, `faa_region`, `report_year`, `report_month`, `scheduled_departure`, `actual_departure`, `delay_minutes`, `delay_cause`, `cancelled`, `diverted`, `aircraft_type`, `tail_number`, `passengers`, `airport_category`, `runway_id`, `visibility_miles`, `wind_speed_knots`, `load_time`

Delay causes: `none` (65%), `carrier` (15%), `weather` (10%), `nas` (5%), `security` (3%), `late_aircraft` (2%). Cancellation rate: 5%. Diversion rate: 1%.

**Domain `safety_incident`** -- FAA safety event records.

Additional fields: `incident_type`, `incident_severity`

Incident types: `bird_strike` (30%), `turbulence` (25%), `mechanical` (20%), `runway_incursion` (8%), `fuel_issue` (6%), `medical` (5%), `security_threat` (3%), `near_miss` (3%)

**Domain `traffic_statistics`** -- T-100 aggregate traffic records.

**Domain `infrastructure`** -- Airport and runway records.

#### `generate_batch(count=1000, domain="flight_operations") -> list[dict]`

---

## # Analytics Generators

Three generators producing event-level data for video security analytics, people movement tracking, and geolocation services within a casino resort environment.

---

### VideoAnalyticsGenerator

**Module:** `data-generation/generators/analytics/video_analytics_generator.py`
**Purpose:** Generates video security analytics events from 50 cameras across 14 casino zones.

#### Constructor

```python
VideoAnalyticsGenerator(
    seed: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
)
```

#### Event Types

| Event Type         | Weight | Alert Level |
|-------------------|--------|-------------|
| `object_detection` | 35%    | INFO        |
| `zone_crossing`    | 20%    | INFO        |
| `crowd_density`    | 12%    | WARNING     |
| `anomaly`          | 10%    | CRITICAL    |
| `face_match`       | 8%     | WARNING     |
| `loitering`        | 7%     | WARNING     |
| `tailgating`       | 5%     | WARNING     |
| `abandoned_object` | 3%     | CRITICAL    |

#### Record Schema Fields

`event_id`, `camera_id`, `camera_location`, `event_type`, `timestamp`, `confidence_score`, `object_class`, `object_count`, `bounding_box`, `track_id`, `zone_from`, `zone_to`, `dwell_time_seconds`, `anomaly_type`, `alert_level`, `frame_number`, `video_resolution`, `fps`, `model_name`, `model_version`, `metadata`, `load_time`

Object classes: `person` (40%), `vehicle` (10%), `bag` (12%), `chip_tray` (8%), `cash_bundle` (6%), `card` (8%), `phone` (7%), `weapon` (2%), `unknown` (7%)

Model names: `YOLOv8` (35%), `DeepSORT` (25%), `RetinaNet` (20%), `SSD-MobileNet` (10%), `FairMOT` (10%)

#### `generate_batch(count=1000) -> list[dict]`

---

### PeopleMovementGenerator

**Module:** `data-generation/generators/analytics/people_movement_generator.py`
**Purpose:** Generates foot traffic sensor readings from 80 sensors across 29 casino zones on 3 floors.

#### Constructor

```python
PeopleMovementGenerator(
    seed: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
)
```

#### Sensor Types

`wifi_probe` (30%), `ble_beacon` (25%), `camera_count` (20%), `infrared` (10%), `pressure_mat` (10%), `lidar` (5%)

#### Directions

`entering` (30%), `exiting` (25%), `stationary` (25%), `passing_through` (20%)

#### Record Schema Fields

`event_id`, `sensor_id`, `sensor_type`, `zone_id`, `zone_name`, `timestamp`, `person_count`, `direction`, `dwell_time_seconds`, `velocity_mps`, `x_coordinate`, `y_coordinate`, `floor_level`, `heat_map_cell`, `occupancy_percentage`, `queue_detected`, `queue_length`, `queue_wait_minutes`, `device_mac_hash`, `signal_strength_dbm`, `battery_level`, `calibration_date`, `load_time`

> **Note:** Queue detection activates automatically when `occupancy_percentage > 70%` in queue-eligible zones (Cage Windows, Buffet, Steakhouse, Hotel Check-In, Main Bar). Wi-Fi probe sensors include a SHA-256 MAC address hash. BLE beacon sensors include battery level.

#### `generate_batch(count=1000) -> list[dict]`

---

### GeolocationGenerator

**Module:** `data-generation/generators/analytics/geolocation_generator.py`
**Purpose:** Generates GPS/indoor positioning events from a 200-device fleet across a Las Vegas casino resort campus.

#### Constructor

```python
GeolocationGenerator(
    seed: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
)
```

#### Device Types

`patron_app` (40%), `employee_badge` (25%), `asset_tag` (15%), `vehicle_gps` (8%), `shuttle_tracker` (7%), `valet_tag` (5%)

#### Source Systems and Accuracy

| Source System        | Weight | Accuracy Range |
|---------------------|--------|----------------|
| `gps`                | 35%    | 3-15 m         |
| `wifi_triangulation` | 25%    | 5-30 m         |
| `ble_trilateration`  | 20%    | 1-5 m          |
| `uwb`                | 10%    | 0.1-1.0 m      |
| `hybrid`             | 10%    | 1-10 m         |

#### Record Schema Fields

`event_id`, `device_id`, `device_type`, `timestamp`, `latitude`, `longitude`, `altitude_meters`, `accuracy_meters`, `speed_mps`, `heading_degrees`, `h3_index`, `geofence_id`, `geofence_name`, `geofence_event`, `geofence_dwell_seconds`, `poi_name`, `poi_distance_meters`, `floor_level`, `indoor_zone`, `proximity_trigger`, `source_system`, `battery_level`, `load_time`

Geofence events: `enter` (35%), `exit` (30%), `dwell` (35%). Geofence interaction rate: ~40% of events.

Proximity triggers (patron_app only, ~15%): `marketing_push`, `loyalty_offer`, `vip_greeting`, `safety_alert`, `staff_dispatch`

#### `generate_batch(count=1000) -> list[dict]`

---

## # Streaming Generators

Three generators designed for real-time and near-real-time event streaming scenarios: Event Hub slot telemetry, multi-source CDC events, and IoT device fleet telemetry.

---

### EventHubProducer

**Module:** `data-generation/generators/streaming/event_hub_producer.py`
**Purpose:** Streams slot machine telemetry events to Azure Event Hub or stdout.

> **Note:** This generator does NOT inherit from `BaseGenerator` in the typical way. It wraps a `SlotMachineGenerator` internally.

#### Constructor

```python
EventHubProducer(
    connection_string: str | None = None,
    eventhub_name: str | None = None,
    events_per_second: float = 10,
    seed: int | None = None,
)
```

| Parameter            | Type          | Default | Description                                 |
|---------------------|---------------|---------|---------------------------------------------|
| `connection_string`  | `str \| None` | `None`  | Azure Event Hub connection string           |
| `eventhub_name`      | `str \| None` | `None`  | Event Hub name                              |
| `events_per_second`  | `float`       | `10`    | Target event rate                           |
| `seed`               | `int \| None` | `None`  | Random seed passed to inner generator       |

**Modes:** If `connection_string` is provided and `azure-eventhub` is installed, events are sent to Event Hub. Otherwise, events are printed to stdout as JSON lines.

#### Public Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `generate_event` | `() -> dict` | Generate a single slot machine event |
| `run_sync` | `(duration_seconds=None, max_events=None, callback=None)` | Run synchronously with rate limiting |
| `run_async` | `(duration_seconds=None, max_events=None, batch_size=100)` | Run asynchronously with batched Event Hub sends |
| `stop` | `()` | Stop a running producer |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `event_count` | `int` | Number of events generated so far |

#### CLI Usage

```bash
python -m data_generation.generators.streaming.event_hub_producer \
    --rate 50 --duration 60 --seed 42
```

---

### MultiSourceSimulator

**Module:** `data-generation/generators/streaming/multi_source_simulator.py`
**Purpose:** Generates CDC (Change Data Capture) events from 5 database source types for Eventstreams demos.

#### Constructor

```python
MultiSourceSimulator(
    seed: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
)
```

#### `generate_record(source_type="sql_server")`

| Source Type   | Enum Value   | Connectors                     | Latency (ms) | Has LSN | Has SCN | Has Partition Key |
|-------------|-------------|--------------------------------|--------------|---------|---------|-------------------|
| `sql_server` | SQL_SERVER   | DEBEZIUM, FABRIC_MIRRORING     | 50-2000      | Yes     | No      | No                |
| `azure_sql`  | AZURE_SQL    | FABRIC_MIRRORING, CHANGE_FEED  | 10-500       | No      | No      | No                |
| `cosmos_db`  | COSMOS_DB    | CHANGE_FEED, FABRIC_MIRRORING  | 10-200       | No      | No      | Yes               |
| `ibm_db2`    | IBM_DB2      | INFOSPHERE_CDC                 | 500-5000     | No      | No      | No                |
| `oracle`     | ORACLE       | GOLDEN_GATE, LOGMINER          | 100-3000     | No      | Yes     | No                |

#### Record Schema Fields

`event_id`, `source_type`, `operation`, `timestamp`, `server_name`, `database_name`, `schema_name`, `table_name`, `primary_key`, `before_image`, `after_image`, `transaction_id`, `lsn`, `scn`, `partition_key`, `sequence_number`, `connector_name`, `latency_ms`, `schema_version`, `load_time`

Operations: `INSERT` (40%), `UPDATE` (35%), `DELETE` (15%), `READ` (10%)

> **Note:** `before_image` and `after_image` follow CDC conventions: INSERT has only `after_image`, DELETE has only `before_image`, UPDATE has both, READ has only `after_image`.

#### Additional Methods

```python
def generate_batch(count=1000, source_type="sql_server") -> list[dict]:
    """Generate events from a single source type."""

def generate_mixed_batch(count=1000) -> list[dict]:
    """Generate events drawn randomly from all source types."""
```

---

### IoTDeviceSimulator

**Module:** `data-generation/generators/streaming/iot_device_simulator.py`
**Purpose:** Simulates telemetry from a heterogeneous fleet of casino IoT devices via Azure IoT Hub conventions.

#### Constructor

```python
IoTDeviceSimulator(
    num_devices: int = 100,
    seed: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
)
```

| Parameter     | Type  | Default | Description                                        |
|--------------|-------|---------|----------------------------------------------------|
| `num_devices` | `int` | `100`   | Approximate fleet size (proportionally distributed) |

#### Device Types (7)

| Device Type     | Default Count | Protocol | Telemetry Interval |
|----------------|--------------|----------|--------------------|
| `slot_machine`  | 500           | MQTT     | 5 sec              |
| `table_sensor`  | 80            | MQTT     | 10 sec             |
| `hvac_sensor`   | 40            | AMQP     | 60 sec             |
| `door_sensor`   | 60            | MQTT     | 1 sec              |
| `camera`        | 120           | HTTPS    | 30 sec             |
| `beacon`        | 200           | MQTT     | 3 sec              |
| `environmental` | 50            | MQTT     | 15 sec             |

#### `generate_record(device_type="slot_machine")`

Record schema fields: `message_id`, `device_id`, `device_type`, `timestamp`, `protocol`, `hub_name`, `enqueued_time`, `correlation_id`, `content_type`, `properties`, `telemetry`, `location_zone`, `firmware_version`, `signal_strength_dbm`

The `telemetry` field is a nested object whose structure varies by device type (e.g., slot machines include `coin_in_meter`, `status`, `error_code`; HVAC sensors include `temperature`, `humidity`, `co2_level`).

#### Additional Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `generate_batch` | `(count=1000, device_type="slot_machine") -> list[dict]` | Batch of messages for one device type |
| `generate_fleet_snapshot` | `() -> list[dict]` | One message per device in the fleet |
| `get_fleet` | `() -> dict[str, list[dict]]` | Pre-generated device registry |
| `fleet_summary` | `() -> dict[str, int]` | Device count per type |

---

## # Extension Guide

To create a custom generator, inherit from `BaseGenerator` and implement `generate_record()`.

### Minimal Template

```python
"""
Custom Generator
================
Generates synthetic data for [your domain].
"""

from datetime import datetime
from typing import Any

import numpy as np

from data_generation.generators.base_generator import BaseGenerator


class CustomGenerator(BaseGenerator):
    """Generate synthetic [domain] data."""

    def __init__(
        self,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)

        self._schema = {
            "record_id": "string",
            "timestamp": "datetime",
            "value": "float",
            "category": "string",
        }

    def generate_record(self) -> dict[str, Any]:
        """Generate a single record."""
        record = {
            "record_id": self.generate_uuid(),
            "timestamp": self.random_datetime().isoformat(),
            "value": round(float(np.random.uniform(0, 100)), 2),
            "category": self.weighted_choice(
                ["A", "B", "C"],
                [0.5, 0.3, 0.2],
            ),
        }
        return self.add_metadata_columns(record)
```

### Implementation Checklist

1. Inherit from `BaseGenerator`
2. Call `super().__init__()` in your constructor
3. Define `self._schema` with field names and types
4. Implement `generate_record()` returning a `dict[str, Any]`
5. Call `self.add_metadata_columns(record)` before returning
6. Use `self.weighted_choice()` for realistic distributions
7. Use `self.random_datetime()` for timestamp generation
8. Use `self.generate_uuid()` for unique identifiers
9. Use `self.hash_value()` / `self.mask_ssn()` for PII protection
10. (Optional) Add a `generate_batch()` method if you need domain-specific batch logic

### Adding Domain Support

For multi-domain generators (like the federal generators), override `generate_record()` with a `domain` parameter:

```python
def generate_record(self, domain: str = "default") -> dict[str, Any]:
    if domain == "domain_a":
        return self._generate_domain_a_record()
    elif domain == "domain_b":
        return self._generate_domain_b_record()
    raise ValueError(f"Unknown domain '{domain}'")
```

---

## # Return Value Schemas

Each casino generator has a corresponding JSON schema file in `data-generation/schemas/`. Federal, analytics, and streaming generators define their schemas inline via the `_schema` property.

### Casino Generator Schema Mapping

| Generator                | Schema File                                            |
|-------------------------|--------------------------------------------------------|
| `SlotMachineGenerator`   | `data-generation/schemas/slot_telemetry_schema.json`    |
| `PlayerGenerator`        | `data-generation/schemas/player_profile_schema.json`    |
| `FinancialGenerator`     | `data-generation/schemas/financial_transaction_schema.json` |
| `ComplianceGenerator`    | `data-generation/schemas/compliance_filing_schema.json` |
| `SecurityGenerator`      | `data-generation/schemas/security_events_schema.json`   |
| `TableGamesGenerator`    | `data-generation/schemas/table_games_schema.json`       |

### Federal / Analytics / Streaming Schema Access

These generators define schemas programmatically. Access via the `schema` property:

```python
gen = USDAGenerator(seed=42)
print(gen.schema)  # Returns dict[str, str] of field names to types
```

### Common Metadata Columns (all generators)

Every record returned by any generator includes these three metadata fields appended by `add_metadata_columns()`:

| Field          | Type     | Description                         |
|---------------|----------|-------------------------------------|
| `_ingested_at` | `string` | ISO-8601 timestamp of generation    |
| `_source`      | `string` | Generator class name                |
| `_batch_id`    | `string` | 8-character UUID prefix for batching |

---

*Last updated: 2026-03-11 | Generator API Reference v1.0.0*
