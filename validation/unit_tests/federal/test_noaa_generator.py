"""
Unit tests for NOAAGenerator.

Tests cover both NOAA domains (weather and storm) and validate field presence,
enum membership, domain-specific business rules (e.g., tornadoes have F-scale),
and standard metadata columns.
Fixtures are provided by the federal conftest.py (noaa_generator, sample_size).
"""

VALID_PARAMETERS = {
    "TEMPERATURE",
    "DEWPOINT",
    "HUMIDITY",
    "WIND_SPEED",
    "WIND_DIRECTION",
    "PRESSURE",
    "VISIBILITY",
    "PRECIPITATION",
    "CLOUD_COVER",
}

VALID_QUALITY_FLAGS = {"PASS", "SUSPECT", "ERRONEOUS", "MISSING"}

VALID_EVENT_TYPES = {
    "THUNDERSTORM_WIND",
    "HAIL",
    "FLASH_FLOOD",
    "TORNADO",
    "FLOOD",
    "WINTER_STORM",
    "BLIZZARD",
    "ICE_STORM",
    "HURRICANE",
    "TROPICAL_STORM",
    "WILDFIRE",
    "DROUGHT",
    "EXTREME_COLD",
    "EXTREME_HEAT",
}

VALID_TOR_F_SCALES = {"EF0", "EF1", "EF2", "EF3", "EF4", "EF5"}


class TestNOAAGenerator:
    """Tests for NOAAGenerator covering weather observation and storm event domains."""

    def test_generate_weather_record(self, noaa_generator):
        """Generated weather record contains required observation identification fields."""
        record = noaa_generator.generate_record(domain="weather")

        assert "observation_id" in record
        assert "station_id" in record
        assert "parameter" in record
        assert "value" in record

    def test_weather_parameter_valid(self, noaa_generator):
        """Weather parameter is always a member of the defined parameter set."""
        for _ in range(100):
            record = noaa_generator.generate_record(domain="weather")
            assert record["parameter"] in VALID_PARAMETERS, (
                f"Unexpected parameter '{record['parameter']}'"
            )

    def test_weather_station_format(self, noaa_generator):
        """Weather station_id follows ICAO convention: starts with 'K' and is 4 characters."""
        for _ in range(100):
            record = noaa_generator.generate_record(domain="weather")
            station_id = record["station_id"]
            assert len(station_id) == 4, (
                f"Expected 4-character station ID, got '{station_id}'"
            )
            assert station_id.startswith("K"), (
                f"US ASOS station ID must start with 'K', got '{station_id}'"
            )

    def test_weather_quality_flag(self, noaa_generator):
        """quality_flag is always one of the four defined QC values."""
        for _ in range(100):
            record = noaa_generator.generate_record(domain="weather")
            assert record["quality_flag"] in VALID_QUALITY_FLAGS, (
                f"Unexpected quality flag '{record['quality_flag']}'"
            )

    def test_generate_storm_record(self, noaa_generator):
        """Generated storm record contains required event identification fields."""
        record = noaa_generator.generate_record(domain="storm")

        assert "event_id" in record
        assert "event_type" in record
        assert "state" in record
        assert "begin_date" in record

    def test_storm_event_type_valid(self, noaa_generator):
        """Storm event_type is always a member of the defined event type set."""
        for _ in range(100):
            record = noaa_generator.generate_record(domain="storm")
            assert record["event_type"] in VALID_EVENT_TYPES, (
                f"Unexpected event type '{record['event_type']}'"
            )

    def test_storm_damage_non_negative(self, noaa_generator):
        """damage_property is non-negative when present."""
        for _ in range(100):
            record = noaa_generator.generate_record(domain="storm")
            damage = record.get("damage_property")
            if damage is not None:
                assert damage >= 0, (
                    f"damage_property must be non-negative, got {damage}"
                )

    def test_tornado_has_fscale(self, noaa_generator):
        """TORNADO events always carry a valid EF-scale rating in tor_f_scale."""
        tornado_records_found = 0

        for _ in range(2000):
            record = noaa_generator.generate_record(domain="storm")
            if record["event_type"] == "TORNADO":
                assert record.get("tor_f_scale") is not None, (
                    "TORNADO event must have tor_f_scale set"
                )
                assert record["tor_f_scale"] in VALID_TOR_F_SCALES, (
                    f"Unexpected tor_f_scale '{record['tor_f_scale']}'"
                )
                tornado_records_found += 1
                if tornado_records_found >= 5:
                    break

        assert tornado_records_found >= 5, (
            "Expected to find at least 5 TORNADO records within 2000 iterations "
            f"(found {tornado_records_found})"
        )

    def test_generate_batch(self, noaa_generator, sample_size):
        """generate_record called sample_size times yields the correct number of records."""
        records = [
            noaa_generator.generate_record(domain="weather") for _ in range(sample_size)
        ]

        assert len(records) == sample_size
        assert all(isinstance(r, dict) for r in records)
        assert all("observation_id" in r for r in records)

    def test_metadata_columns(self, noaa_generator):
        """Every record includes the standard metadata columns added by BaseGenerator."""
        for domain in ("weather", "storm"):
            record = noaa_generator.generate_record(domain=domain)
            assert "_ingested_at" in record, f"Missing _ingested_at in {domain} record"
            assert "_source" in record, f"Missing _source in {domain} record"
            assert "_batch_id" in record, f"Missing _batch_id in {domain} record"
