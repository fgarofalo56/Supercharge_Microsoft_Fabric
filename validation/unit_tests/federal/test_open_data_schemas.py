"""
Unit tests for open data download schema alignment.

These tests verify that the schema mapping and alignment functions in
the download modules produce outputs matching the expected generator schemas.
Since we cannot call real APIs in CI, tests use small mock DataFrames that
simulate the shape of API responses.

Each test:
1. Creates a mock DataFrame matching the raw download format (API column names).
2. Runs it through the mapping + alignment pipeline.
3. Checks that the output schema matches the generator's expected output.
"""

import sys
from pathlib import Path

import pandas as pd

# Ensure the data_generation package is importable
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "data_generation"))


# ---------------------------------------------------------------------------
# Helper: generic schema alignment (mirrors open_data._align_schema)
# ---------------------------------------------------------------------------

def _align_schema(df: pd.DataFrame, target_schema: dict[str, str]) -> pd.DataFrame:
    """
    Reproduce the _align_schema logic from usda_download.py for testing.

    Adds missing columns, drops extra columns, reorders to match schema,
    and applies basic type casting.
    """
    for col in target_schema:
        if col not in df.columns:
            df[col] = None

    df = df[[c for c in target_schema if c in df.columns]].copy()

    for col, dtype in target_schema.items():
        if col not in df.columns:
            continue
        try:
            if dtype == "int":
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
            elif dtype == "float":
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("Float64")
            elif dtype == "string":
                df[col] = df[col].astype("string")
        except (ValueError, TypeError):
            pass

    return df


# ===========================================================================
# USDA Crop Production
# ===========================================================================

class TestUSDACropSchemaAlignment:
    """Verify that NASS QuickStats API responses align to generator schema."""

    CROP_PRODUCTION_SCHEMA: dict[str, str] = {
        "record_id": "string",
        "commodity": "string",
        "year": "int",
        "state_fips": "string",
        "state_name": "string",
        "county_fips": "string",
        "county_name": "string",
        "statisticcat_desc": "string",
        "unit_desc": "string",
        "value": "float",
        "cv_percent": "float",
        "source_desc": "string",
        "agg_level_desc": "string",
        "domain_desc": "string",
        "reference_period_desc": "string",
        "load_time": "string",
        "_ingested_at": "string",
        "_source": "string",
        "_batch_id": "string",
    }

    def _mock_nass_response(self) -> pd.DataFrame:
        """Simulate a NASS QuickStats API response with raw column names."""
        return pd.DataFrame(
            [
                {
                    "commodity_desc": "CORN",
                    "year": "2022",
                    "state_fips_code": "17",
                    "state_name": "ILLINOIS",
                    "county_code": "001",
                    "county_name": "ADAMS",
                    "statisticcat_desc": "PRODUCTION",
                    "unit_desc": "BU",
                    "Value": "1,234,567",
                    "CV (%)": "5.2",
                    "source_desc": "SURVEY",
                    "agg_level_desc": "COUNTY",
                    "domain_desc": "TOTAL",
                    "reference_period_desc": "YEAR",
                },
                {
                    "commodity_desc": "SOYBEANS",
                    "year": "2022",
                    "state_fips_code": "19",
                    "state_name": "IOWA",
                    "county_code": "",
                    "county_name": "",
                    "statisticcat_desc": "YIELD",
                    "unit_desc": "BU / ACRE",
                    "Value": "52.0",
                    "CV (%)": "(D)",
                    "source_desc": "SURVEY",
                    "agg_level_desc": "STATE",
                    "domain_desc": "TOTAL",
                    "reference_period_desc": "YEAR",
                },
            ]
        )

    def test_usda_crop_schema_alignment(self):
        """Mapped NASS response has all columns required by CROP_PRODUCTION_SCHEMA."""
        from open_data.usda_download import _add_metadata_columns, _map_nass_to_schema

        raw = self._mock_nass_response()
        mapped = _map_nass_to_schema(raw)
        mapped = _add_metadata_columns(mapped, "test")
        aligned = _align_schema(mapped, self.CROP_PRODUCTION_SCHEMA)

        # Every schema column must be present
        for col in self.CROP_PRODUCTION_SCHEMA:
            assert col in aligned.columns, f"Missing column: {col}"

        # No extra columns
        assert set(aligned.columns) == set(self.CROP_PRODUCTION_SCHEMA.keys())

        # Row count preserved
        assert len(aligned) == 2

        # Value column should have numeric data (commas stripped)
        assert aligned["value"].notna().any(), "Value column should have numeric data"

    def test_usda_crop_column_order(self):
        """Aligned DataFrame columns follow schema order exactly."""
        from open_data.usda_download import _add_metadata_columns, _map_nass_to_schema

        raw = self._mock_nass_response()
        mapped = _map_nass_to_schema(raw)
        mapped = _add_metadata_columns(mapped, "test")
        aligned = _align_schema(mapped, self.CROP_PRODUCTION_SCHEMA)

        expected_order = list(self.CROP_PRODUCTION_SCHEMA.keys())
        assert list(aligned.columns) == expected_order

    def test_usda_crop_generator_schema_matches(self):
        """Generator output schema covers the same columns as download schema."""
        from generators.federal.usda_generator import USDAGenerator

        gen = USDAGenerator(seed=42)
        record = gen.generate_record(domain="crop_production")

        # Every required field in the crop production schema should be
        # present in the generator output (excluding metadata added by align)
        core_fields = {
            "commodity",
            "year",
            "state_fips",
            "value",
            "statisticcat_desc",
            "agg_level_desc",
        }
        for field in core_fields:
            assert field in record, f"Generator missing field: {field}"


# ===========================================================================
# USDA Food Safety
# ===========================================================================

class TestUSDAFoodSafetySchemaAlignment:
    """Verify that FSIS recall CSV data aligns to generator schema."""

    FOOD_SAFETY_SCHEMA: dict[str, str] = {
        "recall_id": "string",
        "recall_number": "string",
        "recall_date": "string",
        "product_type": "string",
        "recall_class": "string",
        "reason": "string",
        "risk_level": "string",
        "company_name": "string",
        "establishment_number": "string",
        "city": "string",
        "state": "string",
        "pounds_recalled": "float",
        "distribution": "string",
        "status": "string",
        "press_release_url": "string",
        "load_time": "string",
        "_ingested_at": "string",
        "_source": "string",
        "_batch_id": "string",
    }

    def _mock_fsis_csv(self) -> pd.DataFrame:
        """Simulate parsed FSIS recall CSV with raw column names."""
        return pd.DataFrame(
            [
                {
                    "recall_number": "FSIS-2023-042",
                    "recall_date": "2023-06-15",
                    "product": "BEEF",
                    "classification": "Class I",
                    "reason_for_recall": "E. coli O157:H7 contamination",
                    "company": "Test Beef Corp",
                    "establishment": "EST. 12345",
                    "city": "Omaha",
                    "state": "NE",
                    "pounds_recalled": "45,000 lbs",
                    "distribution_pattern": "Nationwide",
                    "current_status": "CLOSED",
                },
            ]
        )

    def test_usda_food_safety_schema_alignment(self):
        """Mapped FSIS response has all columns required by FOOD_SAFETY_SCHEMA."""
        from open_data.usda_download import _add_metadata_columns, _map_fsis_to_schema

        raw = self._mock_fsis_csv()
        # Normalise column names to match what download code does
        raw.columns = raw.columns.str.strip().str.lower().str.replace(" ", "_")
        mapped = _map_fsis_to_schema(raw)
        mapped = _add_metadata_columns(mapped, "test")
        aligned = _align_schema(mapped, self.FOOD_SAFETY_SCHEMA)

        for col in self.FOOD_SAFETY_SCHEMA:
            assert col in aligned.columns, f"Missing column: {col}"

        assert set(aligned.columns) == set(self.FOOD_SAFETY_SCHEMA.keys())
        assert len(aligned) == 1

    def test_usda_food_safety_generator_schema_matches(self):
        """Generator output schema covers the same columns as download schema."""
        from generators.federal.usda_generator import USDAGenerator

        gen = USDAGenerator(seed=42)
        record = gen.generate_record(domain="food_safety")

        core_fields = {
            "recall_id",
            "recall_number",
            "product_type",
            "recall_class",
            "risk_level",
            "status",
        }
        for field in core_fields:
            assert field in record, f"Generator missing field: {field}"


# ===========================================================================
# SBA PPP Loans
# ===========================================================================

class TestSBAPPPSchemaAlignment:
    """Verify that SBA PPP FOIA column mapping produces expected schema."""

    SBA_CORE_SCHEMA: dict[str, str] = {
        "loan_id": "string",
        "program_type": "string",
        "loan_amount": "float",
        "approval_date": "string",
        "borrower_name": "string",
        "borrower_city": "string",
        "borrower_state": "string",
        "borrower_zip": "string",
        "naics_code": "string",
        "jobs_retained": "int",
        "lender_name": "string",
        "loan_status": "string",
        "forgiveness_amount": "float",
        "forgiveness_date": "string",
        "term_months": "int",
        "interest_rate": "float",
        "rural_urban": "string",
        "business_type": "string",
        "load_time": "string",
    }

    def _mock_ppp_csv(self) -> pd.DataFrame:
        """Simulate raw PPP FOIA CSV columns before mapping."""
        return pd.DataFrame(
            [
                {
                    "LoanNumber": "1234567890",
                    "DateApproved": "04/03/2020",
                    "BorrowerName": "ACME Small Business LLC",
                    "BorrowerCity": "Austin",
                    "BorrowerState": "TX",
                    "BorrowerZip": "78701",
                    "InitialApprovalAmount": "150000.00",
                    "ServicingLenderName": "JPMorgan Chase Bank",
                    "NAICSCode": "722511",
                    "JobsReported": "25",
                    "LoanStatus": "Paid in Full",
                    "Term": "24",
                    "RuralUrbanIndicator": "U",
                    "ForgivenessAmount": "150000.00",
                    "ForgivenessDate": "12/15/2020",
                },
            ]
        )

    def test_sba_ppp_schema_alignment(self):
        """Mapped PPP CSV has the core columns expected by downstream notebooks."""
        from open_data.sba_download import PPP_COLUMN_MAP

        raw = self._mock_ppp_csv()
        raw.rename(columns=PPP_COLUMN_MAP, inplace=True)

        # Add standard fields
        raw["program_type"] = "PPP"
        raw["interest_rate"] = 1.0
        raw["load_time"] = "2023-01-01T00:00:00"

        aligned = _align_schema(raw, self.SBA_CORE_SCHEMA)

        for col in self.SBA_CORE_SCHEMA:
            assert col in aligned.columns, f"Missing column: {col}"

        assert len(aligned) == 1

        # loan_amount should be numeric
        assert aligned["loan_amount"].notna().all()

    def test_sba_generator_schema_matches(self):
        """Generator output schema covers the same fields as download schema."""
        from generators.federal.sba_generator import SBAGenerator

        gen = SBAGenerator(seed=42)
        record = gen.generate_record(domain="ppp")

        core_fields = {
            "loan_id",
            "loan_amount",
            "borrower_state",
            "naics_code",
            "jobs_retained",
            "forgiveness_amount",
        }
        for field in core_fields:
            assert field in record, f"Generator missing field: {field}"


# ===========================================================================
# NOAA Weather
# ===========================================================================

class TestNOAAWeatherSchemaAlignment:
    """Verify NOAA weather observation schema alignment."""

    WEATHER_SCHEMA: dict[str, str] = {
        "observation_id": "string",
        "station_id": "string",
        "station_name": "string",
        "timestamp": "string",
        "latitude": "float",
        "longitude": "float",
        "elevation_m": "float",
        "parameter": "string",
        "value": "float",
        "unit": "string",
        "quality_flag": "string",
        "data_source": "string",
        "report_type": "string",
        "load_time": "string",
    }

    def _mock_noaa_weather(self) -> pd.DataFrame:
        """Simulate NOAA CDO API weather observation response."""
        return pd.DataFrame(
            [
                {
                    "observation_id": "obs-001",
                    "station_id": "KJFK",
                    "station_name": "JFK International Airport",
                    "timestamp": "2023-07-15T14:00:00",
                    "latitude": 40.6413,
                    "longitude": -73.7781,
                    "elevation_m": 4.0,
                    "parameter": "TEMPERATURE",
                    "value": 85.2,
                    "unit": "F",
                    "quality_flag": "PASS",
                    "data_source": "ASOS",
                    "report_type": None,
                    "load_time": "2023-07-15T15:00:00",
                },
                {
                    "observation_id": "obs-002",
                    "station_id": "KLAX",
                    "station_name": "Los Angeles International Airport",
                    "timestamp": "2023-07-15T14:00:00",
                    "latitude": 33.9425,
                    "longitude": -118.4081,
                    "elevation_m": 38.0,
                    "parameter": "HUMIDITY",
                    "value": 62.0,
                    "unit": "PCT",
                    "quality_flag": "PASS",
                    "data_source": "METAR",
                    "report_type": None,
                    "load_time": "2023-07-15T15:00:00",
                },
            ]
        )

    def test_noaa_weather_schema_alignment(self):
        """Mock NOAA weather data aligns to expected schema."""
        raw = self._mock_noaa_weather()
        aligned = _align_schema(raw, self.WEATHER_SCHEMA)

        for col in self.WEATHER_SCHEMA:
            assert col in aligned.columns, f"Missing column: {col}"

        assert set(aligned.columns) == set(self.WEATHER_SCHEMA.keys())
        assert len(aligned) == 2

    def test_noaa_weather_generator_schema_matches(self):
        """Generator output schema covers the same columns as expected weather schema."""
        from generators.federal.noaa_generator import NOAAGenerator

        gen = NOAAGenerator(seed=42)
        record = gen.generate_record(domain="weather")

        core_fields = {
            "observation_id",
            "station_id",
            "latitude",
            "longitude",
            "parameter",
            "value",
        }
        for field in core_fields:
            assert field in record, f"Generator missing field: {field}"


# ===========================================================================
# EPA Air Quality
# ===========================================================================

class TestEPAAirQualitySchemaAlignment:
    """Verify EPA AQS air quality monitoring schema alignment."""

    AIR_QUALITY_SCHEMA: dict[str, str] = {
        "record_id": "string",
        "site_id": "string",
        "site_name": "string",
        "parameter": "string",
        "parameter_code": "string",
        "date_local": "string",
        "time_local": "string",
        "aqi_value": "int",
        "aqi_category": "string",
        "concentration": "float",
        "units": "string",
        "sample_duration": "string",
        "latitude": "float",
        "longitude": "float",
        "state_code": "string",
        "county_code": "string",
        "state_name": "string",
        "county_name": "string",
        "cbsa_name": "string",
        "method_code": "string",
        "load_time": "string",
    }

    def _mock_epa_aqs(self) -> pd.DataFrame:
        """Simulate EPA AQS API air quality response."""
        return pd.DataFrame(
            [
                {
                    "record_id": "aqs-001",
                    "site_id": "06-037-0002",
                    "site_name": "Los Angeles Monitoring Station",
                    "parameter": "PM2.5",
                    "parameter_code": "88101",
                    "date_local": "2023-07-15",
                    "time_local": "14:00",
                    "aqi_value": 72,
                    "aqi_category": "MODERATE",
                    "concentration": 22.5,
                    "units": "UG/M3",
                    "sample_duration": "24 HOUR",
                    "latitude": 34.0667,
                    "longitude": -118.2267,
                    "state_code": "06",
                    "county_code": "037",
                    "state_name": "California",
                    "county_name": "Los Angeles County",
                    "cbsa_name": "Los Angeles-Long Beach MSA",
                    "method_code": None,
                    "load_time": "2023-07-15T15:00:00",
                },
            ]
        )

    def test_epa_air_quality_schema_alignment(self):
        """Mock EPA AQS data aligns to expected schema."""
        raw = self._mock_epa_aqs()
        aligned = _align_schema(raw, self.AIR_QUALITY_SCHEMA)

        for col in self.AIR_QUALITY_SCHEMA:
            assert col in aligned.columns, f"Missing column: {col}"

        assert set(aligned.columns) == set(self.AIR_QUALITY_SCHEMA.keys())
        assert len(aligned) == 1

    def test_epa_air_quality_generator_schema_matches(self):
        """Generator output schema covers the same columns as expected AQS schema."""
        from generators.federal.epa_generator import EPAGenerator

        gen = EPAGenerator(seed=42, domain="air_quality")
        record = gen.generate_record(domain="air_quality")

        core_fields = {
            "record_id",
            "site_id",
            "parameter",
            "aqi_value",
            "aqi_category",
            "concentration",
            "latitude",
            "longitude",
        }
        for field in core_fields:
            assert field in record, f"Generator missing field: {field}"

    def test_epa_air_quality_aqi_range(self):
        """AQI value after alignment is an integer within 0-500."""
        raw = self._mock_epa_aqs()
        aligned = _align_schema(raw, self.AIR_QUALITY_SCHEMA)

        for val in aligned["aqi_value"].dropna():
            assert 0 <= int(val) <= 500, f"AQI out of range: {val}"


# ===========================================================================
# DOI Earthquake
# ===========================================================================

class TestDOIEarthquakeSchemaAlignment:
    """Verify USGS earthquake event schema alignment."""

    EARTHQUAKE_SCHEMA: dict[str, str] = {
        "event_id": "string",
        "usgs_id": "string",
        "time": "string",
        "latitude": "float",
        "longitude": "float",
        "depth_km": "float",
        "magnitude": "float",
        "mag_type": "string",
        "place": "string",
        "event_type": "string",
        "status": "string",
        "tsunami": "string",
        "significance": "int",
        "felt": "int",
        "cdi": "float",
        "mmi": "float",
        "alert": "string",
        "net": "string",
        "nst": "int",
        "gap": "float",
        "rms": "float",
        "url": "string",
        "load_time": "string",
    }

    def _mock_usgs_earthquake(self) -> pd.DataFrame:
        """Simulate a USGS ComCat earthquake API response."""
        return pd.DataFrame(
            [
                {
                    "event_id": "eq-001",
                    "usgs_id": "us7000abc1",
                    "time": "2023-07-15T12:34:56",
                    "latitude": 34.0522,
                    "longitude": -118.2437,
                    "depth_km": 12.5,
                    "magnitude": 4.2,
                    "mag_type": "ML",
                    "place": "10km NW of Los Angeles, CA",
                    "event_type": "EARTHQUAKE",
                    "status": "REVIEWED",
                    "tsunami": False,
                    "significance": 280,
                    "felt": 150,
                    "cdi": 4.5,
                    "mmi": 5.0,
                    "alert": "GREEN",
                    "net": "ci",
                    "nst": 42,
                    "gap": 85.3,
                    "rms": 0.15,
                    "url": None,
                    "load_time": "2023-07-15T13:00:00",
                },
                {
                    "event_id": "eq-002",
                    "usgs_id": None,
                    "time": "2023-07-15T08:22:11",
                    "latitude": 61.2,
                    "longitude": -149.9,
                    "depth_km": 45.0,
                    "magnitude": 2.1,
                    "mag_type": "MD",
                    "place": "50km S of Anchorage, AK",
                    "event_type": "EARTHQUAKE",
                    "status": "AUTOMATIC",
                    "tsunami": False,
                    "significance": 70,
                    "felt": None,
                    "cdi": None,
                    "mmi": None,
                    "alert": None,
                    "net": "ak",
                    "nst": 15,
                    "gap": 200.0,
                    "rms": 0.52,
                    "url": None,
                    "load_time": "2023-07-15T09:00:00",
                },
            ]
        )

    def test_doi_earthquake_schema_alignment(self):
        """Mock USGS earthquake data aligns to expected schema."""
        raw = self._mock_usgs_earthquake()
        aligned = _align_schema(raw, self.EARTHQUAKE_SCHEMA)

        for col in self.EARTHQUAKE_SCHEMA:
            assert col in aligned.columns, f"Missing column: {col}"

        assert set(aligned.columns) == set(self.EARTHQUAKE_SCHEMA.keys())
        assert len(aligned) == 2

    def test_doi_earthquake_generator_schema_matches(self):
        """Generator output schema covers the same columns as expected earthquake schema."""
        from generators.federal.doi_generator import DOIGenerator

        gen = DOIGenerator(seed=42)
        record = gen.generate_record(domain="earthquake")

        core_fields = {
            "event_id",
            "magnitude",
            "depth_km",
            "latitude",
            "longitude",
            "time",
            "event_type",
            "status",
        }
        for field in core_fields:
            assert field in record, f"Generator missing field: {field}"

    def test_doi_earthquake_magnitude_range(self):
        """Magnitude after alignment is within physically valid range."""
        raw = self._mock_usgs_earthquake()
        aligned = _align_schema(raw, self.EARTHQUAKE_SCHEMA)

        for val in aligned["magnitude"].dropna():
            assert -1.0 <= float(val) <= 10.0, f"Magnitude out of range: {val}"

    def test_doi_earthquake_depth_non_negative(self):
        """Depth values are non-negative after alignment."""
        raw = self._mock_usgs_earthquake()
        aligned = _align_schema(raw, self.EARTHQUAKE_SCHEMA)

        for val in aligned["depth_km"].dropna():
            assert float(val) >= 0, f"Depth must be non-negative: {val}"
