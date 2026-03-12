"""
Unit tests for DOTFAAGenerator.

Covers all four data domains:
- flight_operations   : BTS On-Time Performance-style records
- safety_incident     : FAA safety incident records
- traffic_statistics  : T-100 traffic statistics records
- infrastructure      : Airport and runway infrastructure records
"""

import pytest

from generators.federal.dot_faa_generator import (
    AIRCRAFT_TYPES,
    AIRPORT_CATEGORIES,
    AIRPORTS,
    CARRIERS,
    DELAY_CAUSES,
    FAA_REGIONS,
    INCIDENT_SEVERITIES,
    INCIDENT_TYPES,
    RUNWAY_IDS,
)

_VALID_CARRIER_CODES = {c["code"] for c in CARRIERS}
_VALID_AIRPORT_CODES = {a["code"] for a in AIRPORTS}
_VALID_DELAY_CAUSES = set(DELAY_CAUSES)
_VALID_INCIDENT_TYPES = set(INCIDENT_TYPES)
_VALID_INCIDENT_SEVERITIES = set(INCIDENT_SEVERITIES)
_VALID_AIRCRAFT_TYPES = {a["type"] for a in AIRCRAFT_TYPES}
_VALID_AIRPORT_CATEGORIES = set(AIRPORT_CATEGORIES)
_VALID_RUNWAY_IDS = set(RUNWAY_IDS)
_VALID_FAA_REGIONS = set(FAA_REGIONS)
_VALID_DOMAINS = {
    "flight_operations",
    "safety_incident",
    "traffic_statistics",
    "infrastructure",
}


class TestDOTFAAGenerator:
    """Tests for DOTFAAGenerator covering all four data domains."""

    # ------------------------------------------------------------------
    # Basic field presence -- flight_operations (default domain)
    # ------------------------------------------------------------------

    def test_generate_flight_operations_record(self, dot_faa_generator):
        """Generate a flight operations record and assert required fields exist."""
        record = dot_faa_generator.generate_record(domain="flight_operations")

        assert record is not None, "generate_record returned None"
        assert "record_id" in record, "record_id field missing"
        assert "data_domain" in record, "data_domain field missing"
        assert (
            record["data_domain"] == "flight_operations"
        ), f"Expected data_domain='flight_operations', got '{record['data_domain']}'"
        assert "carrier_code" in record, "carrier_code field missing"
        assert "origin_airport" in record, "origin_airport field missing"
        assert "destination_airport" in record, "destination_airport field missing"

    # ------------------------------------------------------------------
    # Carrier code validation
    # ------------------------------------------------------------------

    def test_carrier_code_valid(self, dot_faa_generator, sample_size):
        """carrier_code must be one of the 20 known IATA carrier codes."""
        for _ in range(sample_size):
            record = dot_faa_generator.generate_record()
            assert (
                record["carrier_code"] in _VALID_CARRIER_CODES
            ), f"Unexpected carrier_code '{record['carrier_code']}'"

    # ------------------------------------------------------------------
    # Airport code validation
    # ------------------------------------------------------------------

    def test_airport_codes_valid(self, dot_faa_generator, sample_size):
        """origin_airport and destination_airport must be known IATA codes."""
        for _ in range(sample_size):
            record = dot_faa_generator.generate_record()
            assert (
                record["origin_airport"] in _VALID_AIRPORT_CODES
            ), f"Unexpected origin_airport '{record['origin_airport']}'"
            assert (
                record["destination_airport"] in _VALID_AIRPORT_CODES
            ), f"Unexpected destination_airport '{record['destination_airport']}'"

    def test_origin_destination_differ(self, dot_faa_generator, sample_size):
        """origin_airport and destination_airport must be different."""
        for _ in range(sample_size):
            record = dot_faa_generator.generate_record()
            assert (
                record["origin_airport"] != record["destination_airport"]
            ), f"origin and destination must differ, both are '{record['origin_airport']}'"

    # ------------------------------------------------------------------
    # Delay cause validation (flight_operations domain)
    # ------------------------------------------------------------------

    def test_delay_cause_valid(self, dot_faa_generator, sample_size):
        """delay_cause in flight_operations must be from the defined set."""
        for _ in range(sample_size):
            record = dot_faa_generator.generate_record(domain="flight_operations")
            assert (
                record["delay_cause"] in _VALID_DELAY_CAUSES
            ), f"Unexpected delay_cause '{record['delay_cause']}'"

    def test_no_delay_means_zero_minutes(self, dot_faa_generator):
        """When delay_cause is 'none' and not cancelled, delay_minutes must be 0."""
        found = False
        for _ in range(500):
            record = dot_faa_generator.generate_record(domain="flight_operations")
            if record["delay_cause"] == "none" and not record.get("cancelled", False):
                found = True
                assert (
                    record["delay_minutes"] == 0
                ), f"delay_minutes must be 0 when no delay, got {record['delay_minutes']}"
        assert found, "No on-time (delay_cause='none') records seen in 500 flights"

    # ------------------------------------------------------------------
    # Safety incident domain
    # ------------------------------------------------------------------

    def test_safety_incident_fields(self, dot_faa_generator, sample_size):
        """Safety incident records must have incident_type and incident_severity."""
        for _ in range(sample_size):
            record = dot_faa_generator.generate_record(domain="safety_incident")
            assert (
                record["data_domain"] == "safety_incident"
            ), f"Expected domain 'safety_incident', got '{record['data_domain']}'"
            assert (
                record["incident_type"] in _VALID_INCIDENT_TYPES
            ), f"Unexpected incident_type '{record['incident_type']}'"
            assert (
                record["incident_severity"] in _VALID_INCIDENT_SEVERITIES
            ), f"Unexpected incident_severity '{record['incident_severity']}'"

    # ------------------------------------------------------------------
    # Traffic statistics domain
    # ------------------------------------------------------------------

    def test_traffic_statistics_aggregate_fields(self, dot_faa_generator):
        """Traffic statistics records are aggregated and must have null flight-level fields."""
        record = dot_faa_generator.generate_record(domain="traffic_statistics")

        assert (
            record["data_domain"] == "traffic_statistics"
        ), f"Expected domain 'traffic_statistics', got '{record['data_domain']}'"
        assert (
            record["flight_number"] is None
        ), "flight_number should be None for aggregate stats"
        assert (
            record["tail_number"] is None
        ), "tail_number should be None for aggregate stats"
        assert (
            record["passengers"] is not None
        ), "passengers must be present for traffic stats"
        assert (
            record["passengers"] >= 500
        ), f"Monthly segment passenger count must be >= 500, got {record['passengers']}"

    # ------------------------------------------------------------------
    # Infrastructure domain
    # ------------------------------------------------------------------

    def test_infrastructure_fields(self, dot_faa_generator):
        """Infrastructure records should have airport_category and runway_id but no aircraft data."""
        record = dot_faa_generator.generate_record(domain="infrastructure")

        assert (
            record["data_domain"] == "infrastructure"
        ), f"Expected domain 'infrastructure', got '{record['data_domain']}'"
        assert (
            record["aircraft_type"] is None
        ), "aircraft_type should be None for infrastructure"
        assert (
            record["passengers"] is None
        ), "passengers should be None for infrastructure"
        assert (
            record["airport_category"] is not None
        ), "airport_category should be present"
        assert record["runway_id"] is not None, "runway_id should be present"

    # ------------------------------------------------------------------
    # Batch generation
    # ------------------------------------------------------------------

    def test_generate_batch(self, dot_faa_generator, sample_size):
        """generate_batch returns a list with the requested number of records."""
        batch = dot_faa_generator.generate_batch(
            count=sample_size, domain="flight_operations"
        )

        assert isinstance(batch, list), "generate_batch must return a list"
        assert (
            len(batch) == sample_size
        ), f"Expected {sample_size} records, got {len(batch)}"

    # ------------------------------------------------------------------
    # Metadata columns
    # ------------------------------------------------------------------

    def test_metadata_columns_present(self, dot_faa_generator):
        """Standard metadata columns _ingested_at, _source, _batch_id must be present."""
        record = dot_faa_generator.generate_record()

        assert "_ingested_at" in record, "_ingested_at metadata column missing"
        assert "_source" in record, "_source metadata column missing"
        assert "_batch_id" in record, "_batch_id metadata column missing"
        assert (
            record["_source"] == "DOTFAAGenerator"
        ), f"Expected _source='DOTFAAGenerator', got '{record['_source']}'"

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def test_invalid_domain_raises(self, dot_faa_generator):
        """generate_record with an unrecognised domain must raise ValueError."""
        with pytest.raises(ValueError, match="Unknown domain"):
            dot_faa_generator.generate_record(domain="invalid_domain")
