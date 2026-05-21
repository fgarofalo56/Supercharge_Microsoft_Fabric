"""
Unit tests for EPAGenerator.

Covers both the air_quality and water_quality domains, including field
presence, value range validation, categorical consistency, ID format, and
the MCL violation logic.
"""

import re


class TestEPAGenerator:
    """Tests for EPAGenerator."""

    # ------------------------------------------------------------------ #
    # Air quality                                                          #
    # ------------------------------------------------------------------ #

    def test_generate_air_quality_record(self, epa_generator):
        """Record produced by generate_record('air_quality') has required fields."""
        record = epa_generator.generate_record(domain="air_quality")

        assert record is not None
        assert "record_id" in record
        assert "site_id" in record
        assert "parameter" in record
        assert "aqi_value" in record

    def test_air_parameter_valid(self, epa_generator):
        """All generated air records use one of the seven EPA criteria pollutants."""
        valid_parameters = {"PM2.5", "PM10", "OZONE", "CO", "SO2", "NO2", "LEAD"}

        for _ in range(100):
            record = epa_generator.generate_record(domain="air_quality")
            assert record["parameter"] in valid_parameters, (
                f"Unexpected parameter: {record['parameter']}"
            )

    def test_aqi_range(self, epa_generator):
        """AQI values must fall within the EPA-defined 0–500 scale."""
        for _ in range(100):
            record = epa_generator.generate_record(domain="air_quality")
            aqi = record["aqi_value"]
            assert 0 <= aqi <= 500, f"AQI {aqi} is outside the valid 0–500 range"

    def test_aqi_category_matches_value(self, epa_generator):
        """aqi_category must correctly reflect aqi_value per EPA breakpoints."""
        category_ranges = {
            "GOOD": (0, 50),
            "MODERATE": (51, 100),
            "UNHEALTHY_SENSITIVE": (101, 150),
            "UNHEALTHY": (151, 200),
            "VERY_UNHEALTHY": (201, 300),
            "HAZARDOUS": (301, 500),
        }

        for _ in range(100):
            record = epa_generator.generate_record(domain="air_quality")
            aqi = record["aqi_value"]
            category = record["aqi_category"]

            assert category in category_ranges, f"Unknown aqi_category: {category}"
            lo, hi = category_ranges[category]
            assert lo <= aqi <= hi, (
                f"aqi_category '{category}' does not match aqi_value {aqi} "
                f"(expected {lo}–{hi})"
            )

    def test_site_id_format(self, epa_generator):
        """site_id must follow the AQS pattern SS-CCC-SSSS (state-county-site)."""
        pattern = re.compile(r"^\d{2}-\d{3}-\d{4}$")

        for _ in range(50):
            record = epa_generator.generate_record(domain="air_quality")
            assert pattern.match(record["site_id"]), (
                f"site_id '{record['site_id']}' does not match pattern SS-CCC-SSSS"
            )

    # ------------------------------------------------------------------ #
    # Water quality                                                        #
    # ------------------------------------------------------------------ #

    def test_generate_water_record(self, epa_generator):
        """Record produced by generate_record('water_quality') has required fields."""
        record = epa_generator.generate_record(domain="water_quality")

        assert record is not None
        assert "record_id" in record
        assert "system_id" in record
        assert "contaminant" in record

    def test_water_system_type_valid(self, epa_generator):
        """system_type must be one of the three SDWIS water-system types or None."""
        valid_types = {"CWS", "NTNCWS", "TNCWS", None}

        for _ in range(100):
            record = epa_generator.generate_record(domain="water_quality")
            assert record["system_type"] in valid_types, (
                f"Unexpected system_type: {record['system_type']}"
            )

    def test_mcl_violation_logic(self, epa_generator):
        """When mcl_violation is True, result_value must exceed the MCL."""
        violation_records_found = 0

        # Generate enough records to encounter at least one ~5 % violation
        for _ in range(500):
            record = epa_generator.generate_record(domain="water_quality")
            if record["mcl_violation"]:
                violation_records_found += 1
                mcl = record["mcl"]
                result = record["result_value"]
                # Coliform MCL is 0 (presence/absence); any positive value counts
                if mcl == 0.0:
                    assert result > 0, (
                        f"MCL violation with MCL=0 should have result_value > 0, "
                        f"got {result}"
                    )
                else:
                    assert result > mcl, (
                        f"MCL violation expected result_value ({result}) > MCL ({mcl})"
                    )
            if violation_records_found >= 3:
                break

        assert violation_records_found >= 1, (
            "No MCL violations encountered in 500 records; "
            "generator may not be producing violations"
        )

    # ------------------------------------------------------------------ #
    # Batch / metadata                                                     #
    # ------------------------------------------------------------------ #

    def test_generate_batch(self, epa_generator, sample_size):
        """generate() should produce the requested number of air quality records."""
        df = epa_generator.generate(sample_size, show_progress=False)
        records = df.to_dict("records")

        assert len(records) == sample_size
        assert all("record_id" in r for r in records)
        assert all("aqi_value" in r for r in records)

    def test_metadata_columns(self, epa_generator):
        """Standard metadata columns added by add_metadata_columns must be present."""
        record = epa_generator.generate_record(domain="air_quality")

        assert "_ingested_at" in record, "Missing '_ingested_at' metadata column"
        assert "_source" in record, "Missing '_source' metadata column"
        assert "_batch_id" in record, "Missing '_batch_id' metadata column"
        assert record["_source"] == "EPAGenerator"
