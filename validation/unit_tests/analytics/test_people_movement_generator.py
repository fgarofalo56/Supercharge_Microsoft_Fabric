"""
Unit tests for PeopleMovementGenerator.

Covers people movement / foot traffic event generation including:
- wifi_probe      : Wi-Fi probe request tracking with MAC hash
- ble_beacon      : BLE beacon proximity and battery monitoring
- camera_count    : Camera-based people counting
- infrared        : IR gate crossing detection
- pressure_mat    : Weight-based step detection
- lidar           : LiDAR-based 3D people tracking
"""

from generators.analytics.people_movement_generator import (
    DIRECTIONS,
    SENSOR_TYPES,
)

_VALID_SENSOR_TYPES = set(SENSOR_TYPES)

_VALID_DIRECTIONS = set(DIRECTIONS)


class TestPeopleMovementGenerator:
    """Tests for PeopleMovementGenerator covering all sensor types."""

    # ------------------------------------------------------------------
    # Basic field presence
    # ------------------------------------------------------------------

    def test_generate_record(self, people_movement_generator):
        """Generate a record and assert required top-level fields exist."""
        record = people_movement_generator.generate_record()

        assert record is not None
        assert "event_id" in record, "event_id field missing"
        assert "sensor_id" in record, "sensor_id field missing"
        assert "sensor_type" in record, "sensor_type field missing"
        assert "zone_name" in record, "zone_name field missing"

    # ------------------------------------------------------------------
    # sensor_id format
    # ------------------------------------------------------------------

    def test_sensor_id_format(self, people_movement_generator):
        """sensor_id must follow the SENS-NNNN pattern."""
        record = people_movement_generator.generate_record()
        sensor_id = record["sensor_id"]

        assert sensor_id.startswith("SENS-"), (
            f"sensor_id must start with 'SENS-', got '{sensor_id}'"
        )

    # ------------------------------------------------------------------
    # sensor_type enum
    # ------------------------------------------------------------------

    def test_sensor_type_valid(self, people_movement_generator, sample_size):
        """All generated sensor_type values must be one of the 6 known types."""
        for _ in range(sample_size):
            record = people_movement_generator.generate_record()
            assert record["sensor_type"] in _VALID_SENSOR_TYPES, (
                f"Unexpected sensor_type '{record['sensor_type']}'"
            )

    # ------------------------------------------------------------------
    # person_count non-negative
    # ------------------------------------------------------------------

    def test_person_count_non_negative(self, people_movement_generator, sample_size):
        """person_count must be >= 0 for every record."""
        for _ in range(sample_size):
            record = people_movement_generator.generate_record()
            assert record["person_count"] >= 0, (
                f"person_count must be >= 0, got {record['person_count']}"
            )

    # ------------------------------------------------------------------
    # direction enum
    # ------------------------------------------------------------------

    def test_direction_valid(self, people_movement_generator, sample_size):
        """When direction is not None, it must be one of the 4 known directions."""
        for _ in range(sample_size):
            record = people_movement_generator.generate_record()
            direction = record["direction"]
            if direction is not None:
                assert direction in _VALID_DIRECTIONS, (
                    f"Unexpected direction '{direction}'"
                )

    # ------------------------------------------------------------------
    # occupancy_percentage range
    # ------------------------------------------------------------------

    def test_occupancy_percentage_range(self, people_movement_generator, sample_size):
        """When occupancy_percentage is not None, it must be between 0 and 100."""
        for _ in range(sample_size):
            record = people_movement_generator.generate_record()
            occ = record["occupancy_percentage"]
            if occ is not None:
                assert 0 <= occ <= 100, (
                    f"occupancy_percentage must be in [0, 100], got {occ}"
                )

    # ------------------------------------------------------------------
    # Queue logic
    # ------------------------------------------------------------------

    def test_queue_logic(self, people_movement_generator):
        """When queue_detected is True, queue_length must not be None and must be > 0."""
        found = False
        for _ in range(500):
            record = people_movement_generator.generate_record()
            if record["queue_detected"] is True:
                found = True
                assert record["queue_length"] is not None, (
                    "queue_detected=True must have queue_length"
                )
                assert record["queue_length"] > 0, (
                    f"queue_length must be > 0 when queue_detected, "
                    f"got {record['queue_length']}"
                )

        assert found, "No queue_detected=True events seen in 500 records"

    # ------------------------------------------------------------------
    # signal_strength_dbm range
    # ------------------------------------------------------------------

    def test_signal_strength_range(self, people_movement_generator):
        """When signal_strength_dbm is not None, it must be between -90 and 0."""
        found = False
        for _ in range(500):
            record = people_movement_generator.generate_record()
            signal = record["signal_strength_dbm"]
            if signal is not None:
                found = True
                assert -90 <= signal <= 0, (
                    f"signal_strength_dbm must be in [-90, 0], got {signal}"
                )

        assert found, "No records with signal_strength_dbm seen in 500 records"

    # ------------------------------------------------------------------
    # Batch generation
    # ------------------------------------------------------------------

    def test_generate_batch(self, people_movement_generator, sample_size):
        """generate_batch returns exactly the requested number of records."""
        batch = people_movement_generator.generate_batch(count=sample_size)

        assert isinstance(batch, list), "generate_batch must return a list"
        assert len(batch) == sample_size, (
            f"Expected {sample_size} records, got {len(batch)}"
        )

    # ------------------------------------------------------------------
    # Metadata columns
    # ------------------------------------------------------------------

    def test_metadata_columns(self, people_movement_generator):
        """Standard metadata columns _ingested_at, _source, _batch_id must be present."""
        record = people_movement_generator.generate_record()

        assert "_ingested_at" in record, "_ingested_at metadata field missing"
        assert "_source" in record, "_source metadata field missing"
        assert "_batch_id" in record, "_batch_id metadata field missing"
        assert record["_source"] == "PeopleMovementGenerator", (
            f"Expected _source='PeopleMovementGenerator', got '{record['_source']}'"
        )
