"""
Unit tests for VideoAnalyticsGenerator.

Covers video security analytics event generation including:
- object_detection    : YOLO/RetinaNet detections with bounding boxes
- zone_crossing       : Tracked objects crossing casino zones
- anomaly             : Unusual behavior detection
- face_match          : Facial recognition matches
- crowd_density       : Crowd monitoring in high-traffic areas
- loitering           : Dwell-time violation alerts
- tailgating          : Unauthorized access following
- abandoned_object    : Unattended item detection
"""
from generators.analytics.video_analytics_generator import (
    VideoAnalyticsGenerator,
    EVENT_TYPES,
    OBJECT_CLASSES,
)

_VALID_EVENT_TYPES = set(EVENT_TYPES)

_VALID_OBJECT_CLASSES = set(OBJECT_CLASSES)

_VALID_ALERT_LEVELS = {"INFO", "WARNING", "CRITICAL", "EMERGENCY"}


class TestVideoAnalyticsGenerator:
    """Tests for VideoAnalyticsGenerator covering all event types."""

    # ------------------------------------------------------------------
    # Basic field presence
    # ------------------------------------------------------------------

    def test_generate_record(self, video_analytics_generator):
        """Generate a record and assert required top-level fields exist."""
        record = video_analytics_generator.generate_record()

        assert record is not None
        assert "event_id" in record, "event_id field missing"
        assert "camera_id" in record, "camera_id field missing"
        assert "event_type" in record, "event_type field missing"
        assert "timestamp" in record, "timestamp field missing"

    # ------------------------------------------------------------------
    # camera_id format
    # ------------------------------------------------------------------

    def test_camera_id_format(self, video_analytics_generator):
        """camera_id must follow the CAM-NNNN pattern."""
        record = video_analytics_generator.generate_record()
        camera_id = record["camera_id"]

        assert camera_id.startswith("CAM-"), (
            f"camera_id must start with 'CAM-', got '{camera_id}'"
        )
        suffix = camera_id[4:]
        assert len(suffix) == 4 and suffix.isdigit(), (
            f"camera_id suffix must be 4 digits, got '{suffix}'"
        )

    # ------------------------------------------------------------------
    # event_type enum
    # ------------------------------------------------------------------

    def test_event_type_valid(self, video_analytics_generator, sample_size):
        """All generated event_type values must be one of the 8 known types."""
        for _ in range(sample_size):
            record = video_analytics_generator.generate_record()
            assert record["event_type"] in _VALID_EVENT_TYPES, (
                f"Unexpected event_type '{record['event_type']}'"
            )

    # ------------------------------------------------------------------
    # confidence_score range
    # ------------------------------------------------------------------

    def test_confidence_score_range(self, video_analytics_generator, sample_size):
        """confidence_score must be between 0.0 and 1.0 for every record."""
        for _ in range(sample_size):
            record = video_analytics_generator.generate_record()
            score = record["confidence_score"]
            assert 0.0 <= score <= 1.0, (
                f"confidence_score must be in [0.0, 1.0], got {score}"
            )

    # ------------------------------------------------------------------
    # alert_level enum
    # ------------------------------------------------------------------

    def test_alert_level_valid(self, video_analytics_generator, sample_size):
        """alert_level must be one of INFO, WARNING, CRITICAL, or EMERGENCY."""
        for _ in range(sample_size):
            record = video_analytics_generator.generate_record()
            assert record["alert_level"] in _VALID_ALERT_LEVELS, (
                f"Unexpected alert_level '{record['alert_level']}'"
            )

    # ------------------------------------------------------------------
    # object_class enum
    # ------------------------------------------------------------------

    def test_object_class_valid(self, video_analytics_generator, sample_size):
        """When object_class is not None, it must be one of the 9 known classes."""
        for _ in range(sample_size):
            record = video_analytics_generator.generate_record()
            obj_class = record["object_class"]
            if obj_class is not None:
                assert obj_class in _VALID_OBJECT_CLASSES, (
                    f"Unexpected object_class '{obj_class}'"
                )

    # ------------------------------------------------------------------
    # Zone crossing logic
    # ------------------------------------------------------------------

    def test_zone_crossing_has_zones(self, video_analytics_generator):
        """When event_type == 'zone_crossing', zone_from and zone_to must be present."""
        found = False
        for _ in range(500):
            record = video_analytics_generator.generate_record()
            if record["event_type"] == "zone_crossing":
                found = True
                assert record["zone_from"] is not None, (
                    "zone_crossing must have zone_from"
                )
                assert record["zone_to"] is not None, (
                    "zone_crossing must have zone_to"
                )
                assert record["zone_from"] != record["zone_to"], (
                    "zone_from and zone_to must differ"
                )

        assert found, "No zone_crossing events seen in 500 records"

    # ------------------------------------------------------------------
    # Anomaly type logic
    # ------------------------------------------------------------------

    def test_anomaly_has_type(self, video_analytics_generator):
        """When event_type == 'anomaly', anomaly_type must not be None."""
        found = False
        for _ in range(500):
            record = video_analytics_generator.generate_record()
            if record["event_type"] == "anomaly":
                found = True
                assert record["anomaly_type"] is not None, (
                    "anomaly event must have anomaly_type"
                )

        assert found, "No anomaly events seen in 500 records"

    # ------------------------------------------------------------------
    # Batch generation
    # ------------------------------------------------------------------

    def test_generate_batch(self, video_analytics_generator, sample_size):
        """generate_batch returns exactly the requested number of records."""
        batch = video_analytics_generator.generate_batch(count=sample_size)

        assert isinstance(batch, list), "generate_batch must return a list"
        assert len(batch) == sample_size, (
            f"Expected {sample_size} records, got {len(batch)}"
        )

    # ------------------------------------------------------------------
    # Metadata columns
    # ------------------------------------------------------------------

    def test_metadata_columns(self, video_analytics_generator):
        """Standard metadata columns _ingested_at, _source, _batch_id must be present."""
        record = video_analytics_generator.generate_record()

        assert "_ingested_at" in record, "_ingested_at metadata field missing"
        assert "_source" in record, "_source metadata field missing"
        assert "_batch_id" in record, "_batch_id metadata field missing"
        assert record["_source"] == "VideoAnalyticsGenerator", (
            f"Expected _source='VideoAnalyticsGenerator', got '{record['_source']}'"
        )
