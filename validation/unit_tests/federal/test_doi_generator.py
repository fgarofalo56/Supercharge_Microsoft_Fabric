"""
Unit tests for DOIGenerator.

Covers both the earthquake (USGS ComCat-style) and land_use (BLM/NPS/FWS)
domains, including field presence, geophysical range validation, categorical
consistency, and the tsunami/magnitude correlation.
"""
import pytest


class TestDOIGenerator:
    """Tests for DOIGenerator."""

    # ------------------------------------------------------------------ #
    # Earthquake domain                                                    #
    # ------------------------------------------------------------------ #

    def test_generate_earthquake_record(self, doi_generator):
        """Record produced by generate_record('earthquake') has required fields."""
        record = doi_generator.generate_record(domain="earthquake")

        assert record is not None
        assert "event_id" in record
        assert "time" in record
        assert "latitude" in record
        assert "longitude" in record
        assert "magnitude" in record

    def test_earthquake_magnitude_range(self, doi_generator):
        """Earthquake magnitudes must fall between -1 and 10 on the Richter-like scale."""
        for _ in range(100):
            record = doi_generator.generate_record(domain="earthquake")
            mag = record["magnitude"]
            assert -1 <= mag <= 10, (
                f"Magnitude {mag} is outside the expected -1 to 10 range"
            )

    def test_earthquake_depth_positive(self, doi_generator):
        """Earthquake depth in kilometres must be non-negative."""
        for _ in range(100):
            record = doi_generator.generate_record(domain="earthquake")
            depth = record["depth_km"]
            assert depth >= 0, (
                f"depth_km {depth} is negative; depth must be >= 0"
            )

    def test_earthquake_mag_type_valid(self, doi_generator):
        """mag_type must be one of the USGS-recognised magnitude scale codes."""
        valid_mag_types = {"ML", "MD", "MB", "MW", "MS", "MWW", "MWC", "MWB"}

        for _ in range(100):
            record = doi_generator.generate_record(domain="earthquake")
            assert record["mag_type"] in valid_mag_types, (
                f"Unexpected mag_type: {record['mag_type']}"
            )

    def test_earthquake_coordinates(self, doi_generator):
        """Earthquake coordinates must be within valid geographic bounds."""
        for _ in range(100):
            record = doi_generator.generate_record(domain="earthquake")
            lat = record["latitude"]
            lon = record["longitude"]
            assert -90 <= lat <= 90, (
                f"latitude {lat} is outside -90 to 90 range"
            )
            assert -180 <= lon <= 180, (
                f"longitude {lon} is outside -180 to 180 range"
            )

    def test_tsunami_only_large_quakes(self, doi_generator):
        """When tsunami is True, the magnitude should be at or above M6.0 approximately."""
        # The generator sets tsunami=True only when magnitude >= 6.5 and depth <= 70 km.
        # We verify the observable invariant: no small-magnitude events are flagged.
        tsunami_records_found = 0

        for _ in range(2000):
            record = doi_generator.generate_record(domain="earthquake")
            if record["tsunami"]:
                tsunami_records_found += 1
                assert record["magnitude"] >= 6.0, (
                    f"Tsunami flagged for magnitude {record['magnitude']} < 6.0; "
                    "tsunamis should only occur for large earthquakes"
                )
            if tsunami_records_found >= 3:
                break

        # If no tsunamis were generated the test is vacuously passing; that is
        # acceptable given the low probability (~1 % of records are M7+).

    # ------------------------------------------------------------------ #
    # Land use domain                                                      #
    # ------------------------------------------------------------------ #

    def test_generate_land_use_record(self, doi_generator):
        """Record produced by generate_record('land_use') has required fields."""
        record = doi_generator.generate_record(domain="land_use")

        assert record is not None
        assert "parcel_id" in record
        assert "managing_agency" in record
        assert "state" in record
        assert "land_type" in record

    def test_land_managing_agency_valid(self, doi_generator):
        """managing_agency must be one of the recognised federal land agencies."""
        valid_agencies = {"BLM", "NPS", "FWS", "USFS", "BOR", "DOD", "OTHER"}

        for _ in range(100):
            record = doi_generator.generate_record(domain="land_use")
            assert record["managing_agency"] in valid_agencies, (
                f"Unexpected managing_agency: {record['managing_agency']}"
            )

    def test_land_acres_positive(self, doi_generator):
        """total_acres must be strictly greater than zero."""
        for _ in range(100):
            record = doi_generator.generate_record(domain="land_use")
            assert record["total_acres"] > 0, (
                f"total_acres {record['total_acres']} is not positive"
            )

    def test_land_fire_risk_valid(self, doi_generator):
        """fire_risk_level must be one of the five NIFC levels or None."""
        valid_levels = {"LOW", "MODERATE", "HIGH", "VERY_HIGH", "EXTREME", None}

        for _ in range(100):
            record = doi_generator.generate_record(domain="land_use")
            assert record["fire_risk_level"] in valid_levels, (
                f"Unexpected fire_risk_level: {record['fire_risk_level']}"
            )

    # ------------------------------------------------------------------ #
    # Batch / metadata                                                     #
    # ------------------------------------------------------------------ #

    def test_generate_batch(self, doi_generator, sample_size):
        """generate_batch() should produce the requested number of earthquake records."""
        df = doi_generator.generate_batch(count=sample_size, domain="earthquake")
        records = df.to_dict("records")

        assert len(records) == sample_size
        assert all("event_id" in r for r in records)
        assert all("magnitude" in r for r in records)

    def test_metadata_columns(self, doi_generator):
        """Standard metadata columns added by add_metadata_columns must be present."""
        record = doi_generator.generate_record(domain="earthquake")

        assert "_ingested_at" in record, "Missing '_ingested_at' metadata column"
        assert "_source" in record, "Missing '_source' metadata column"
        assert "_batch_id" in record, "Missing '_batch_id' metadata column"
        assert record["_source"] == "DOIGenerator"
