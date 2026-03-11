"""
Unit tests for GeolocationGenerator.

Covers geolocation analytics event generation including:
- patron_app       : Guest mobile application location pings
- employee_badge   : Staff BLE badge tracking
- asset_tag        : Equipment and high-value asset tracking
- vehicle_gps      : Casino-owned vehicle fleet GPS
- shuttle_tracker   : Resort shuttle route tracking
- valet_tag        : Valet vehicle location tags
"""
from generators.analytics.geolocation_generator import (
    GeolocationGenerator,
    DEVICE_TYPES,
    SOURCE_SYSTEMS,
    GEOFENCE_EVENTS,
)

_VALID_DEVICE_TYPES = set(DEVICE_TYPES)

_VALID_SOURCE_SYSTEMS = set(SOURCE_SYSTEMS)

_VALID_GEOFENCE_EVENTS = set(GEOFENCE_EVENTS)


class TestGeolocationGenerator:
    """Tests for GeolocationGenerator covering all device types."""

    # ------------------------------------------------------------------
    # Basic field presence
    # ------------------------------------------------------------------

    def test_generate_record(self, geolocation_generator):
        """Generate a record and assert required top-level fields exist."""
        record = geolocation_generator.generate_record()

        assert record is not None
        assert "event_id" in record, "event_id field missing"
        assert "device_id" in record, "device_id field missing"
        assert "device_type" in record, "device_type field missing"
        assert "latitude" in record, "latitude field missing"
        assert "longitude" in record, "longitude field missing"

    # ------------------------------------------------------------------
    # device_type enum
    # ------------------------------------------------------------------

    def test_device_type_valid(self, geolocation_generator, sample_size):
        """All generated device_type values must be one of the 6 known types."""
        for _ in range(sample_size):
            record = geolocation_generator.generate_record()
            assert record["device_type"] in _VALID_DEVICE_TYPES, (
                f"Unexpected device_type '{record['device_type']}'"
            )

    # ------------------------------------------------------------------
    # Latitude range (Las Vegas area)
    # ------------------------------------------------------------------

    def test_latitude_range(self, geolocation_generator, sample_size):
        """latitude must be approximately 36.16-36.18 (Las Vegas area)."""
        for _ in range(sample_size):
            record = geolocation_generator.generate_record()
            lat = record["latitude"]
            assert 36.15 <= lat <= 36.19, (
                f"latitude must be in Las Vegas range [36.15, 36.19], got {lat}"
            )

    # ------------------------------------------------------------------
    # Longitude range (Las Vegas area)
    # ------------------------------------------------------------------

    def test_longitude_range(self, geolocation_generator, sample_size):
        """longitude must be approximately -115.15 to -115.13 (Las Vegas area)."""
        for _ in range(sample_size):
            record = geolocation_generator.generate_record()
            lon = record["longitude"]
            assert -115.16 <= lon <= -115.12, (
                f"longitude must be in Las Vegas range [-115.16, -115.12], got {lon}"
            )

    # ------------------------------------------------------------------
    # source_system enum
    # ------------------------------------------------------------------

    def test_source_system_valid(self, geolocation_generator, sample_size):
        """source_system must be one of the 5 known positioning systems."""
        for _ in range(sample_size):
            record = geolocation_generator.generate_record()
            assert record["source_system"] in _VALID_SOURCE_SYSTEMS, (
                f"Unexpected source_system '{record['source_system']}'"
            )

    # ------------------------------------------------------------------
    # geofence_event enum
    # ------------------------------------------------------------------

    def test_geofence_event_valid(self, geolocation_generator):
        """When geofence_event is not None, it must be one of enter, exit, or dwell."""
        found = False
        for _ in range(500):
            record = geolocation_generator.generate_record()
            gf_event = record["geofence_event"]
            if gf_event is not None:
                found = True
                assert gf_event in _VALID_GEOFENCE_EVENTS, (
                    f"Unexpected geofence_event '{gf_event}'"
                )

        assert found, "No records with geofence_event seen in 500 records"

    # ------------------------------------------------------------------
    # h3_index format
    # ------------------------------------------------------------------

    def test_h3_index_format(self, geolocation_generator):
        """When h3_index is not None, it must be a 15-character hex string."""
        found = False
        for _ in range(500):
            record = geolocation_generator.generate_record()
            h3 = record["h3_index"]
            if h3 is not None:
                found = True
                assert len(h3) == 15, (
                    f"h3_index must be 15 characters, got {len(h3)}: '{h3}'"
                )
                assert all(c in "0123456789abcdef" for c in h3), (
                    f"h3_index must be a hex string, got '{h3}'"
                )

        assert found, "No records with h3_index seen in 500 records"

    # ------------------------------------------------------------------
    # speed non-negative
    # ------------------------------------------------------------------

    def test_speed_non_negative(self, geolocation_generator, sample_size):
        """When speed_mps is not None, it must be >= 0.0."""
        for _ in range(sample_size):
            record = geolocation_generator.generate_record()
            speed = record["speed_mps"]
            if speed is not None:
                assert speed >= 0.0, (
                    f"speed_mps must be >= 0.0, got {speed}"
                )

    # ------------------------------------------------------------------
    # Batch generation
    # ------------------------------------------------------------------

    def test_generate_batch(self, geolocation_generator, sample_size):
        """generate_batch returns exactly the requested number of records."""
        batch = geolocation_generator.generate_batch(count=sample_size)

        assert isinstance(batch, list), "generate_batch must return a list"
        assert len(batch) == sample_size, (
            f"Expected {sample_size} records, got {len(batch)}"
        )

    # ------------------------------------------------------------------
    # Metadata columns
    # ------------------------------------------------------------------

    def test_metadata_columns(self, geolocation_generator):
        """Standard metadata columns _ingested_at, _source, _batch_id must be present."""
        record = geolocation_generator.generate_record()

        assert "_ingested_at" in record, "_ingested_at metadata field missing"
        assert "_source" in record, "_source metadata field missing"
        assert "_batch_id" in record, "_batch_id metadata field missing"
        assert record["_source"] == "GeolocationGenerator", (
            f"Expected _source='GeolocationGenerator', got '{record['_source']}'"
        )
