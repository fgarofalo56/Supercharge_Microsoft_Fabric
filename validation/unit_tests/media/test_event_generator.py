"""
Unit tests for Media Event Generator.

Tests cover:
- Basic event generation and field presence
- Event type validity
- Position within content duration bounds
- Device type values
- Age bucket values and COPPA constraints
- Reproducibility with fixed seed
"""

import pytest

from data_generation.generators.media.event_generator import (
    AGE_BUCKETS,
    DEVICE_TYPES,
    EVENT_TYPES,
    MediaEventGenerator,
)


@pytest.fixture
def generator():
    """Create a seeded generator for deterministic tests."""
    return MediaEventGenerator(seed=42, catalog_size=50, user_pool_size=200)


@pytest.fixture
def sample_events(generator):
    """Generate a batch of events for testing."""
    return generator.generate_batch(500)


class TestGenerateEvents:
    """Test basic event generation."""

    def test_generate_returns_records(self, generator):
        df = generator.generate(num_records=10, show_progress=False)
        assert len(df) == 10

    def test_generate_batch_returns_list(self, generator):
        batch = generator.generate_batch(5)
        assert isinstance(batch, list)
        assert len(batch) == 5

    def test_required_fields_present(self, sample_events):
        required = [
            "event_id",
            "user_id",
            "content_id",
            "event_type",
            "event_timestamp",
            "position_sec",
            "device_type",
            "bitrate_kbps",
            "plan_tier",
            "age_bucket",
            "region",
        ]
        for record in sample_events[:10]:
            for field in required:
                assert field in record, f"Missing field: {field}"

    def test_event_id_unique(self, sample_events):
        ids = [e["event_id"] for e in sample_events]
        assert len(ids) == len(set(ids)), "event_id values must be unique"

    def test_metadata_columns_present(self, sample_events):
        for record in sample_events[:5]:
            assert "_ingested_at" in record
            assert "_source" in record
            assert "_batch_id" in record


class TestEventTypes:
    """Test event type validity."""

    def test_all_event_types_valid(self, sample_events):
        for record in sample_events:
            assert record["event_type"] in EVENT_TYPES, (
                f"Invalid event type: {record['event_type']}"
            )

    def test_event_type_distribution(self, sample_events):
        """All event types should appear in a large enough sample."""
        types_seen = {r["event_type"] for r in sample_events}
        for et in EVENT_TYPES:
            assert et in types_seen, f"Event type '{et}' not seen in 500 records"


class TestPositionWithinDuration:
    """Test that position_sec is within reasonable bounds."""

    def test_position_non_negative(self, sample_events):
        for record in sample_events:
            assert record["position_sec"] >= 0, (
                f"Negative position: {record['position_sec']}"
            )

    def test_play_events_start_at_zero(self, sample_events):
        play_events = [r for r in sample_events if r["event_type"] == "play"]
        for record in play_events:
            assert record["position_sec"] == 0, (
                f"Play event should start at 0, got {record['position_sec']}"
            )


class TestDeviceTypes:
    """Test device type values."""

    def test_all_device_types_valid(self, sample_events):
        for record in sample_events:
            assert record["device_type"] in DEVICE_TYPES, (
                f"Invalid device type: {record['device_type']}"
            )

    def test_device_type_distribution(self, sample_events):
        devices_seen = {r["device_type"] for r in sample_events}
        for dt in DEVICE_TYPES:
            assert dt in devices_seen, f"Device type '{dt}' not seen in 500 records"


class TestAgeBucketValues:
    """Test age bucket values and COPPA constraints."""

    def test_all_age_buckets_valid(self, sample_events):
        for record in sample_events:
            assert record["age_bucket"] in AGE_BUCKETS, (
                f"Invalid age bucket: {record['age_bucket']}"
            )

    def test_age_bucket_distribution(self, sample_events):
        buckets_seen = {r["age_bucket"] for r in sample_events}
        for ab in AGE_BUCKETS:
            assert ab in buckets_seen, f"Age bucket '{ab}' not seen in 500 records"

    def test_child_plan_tiers(self, sample_events):
        """Child profiles should not have premium tier."""
        child_events = [r for r in sample_events if r["age_bucket"] == "child"]
        assert len(child_events) > 0, "No child events generated"
        for record in child_events:
            assert record["plan_tier"] in ("free", "basic"), (
                f"Child should not have plan_tier={record['plan_tier']}"
            )


class TestReproducibility:
    """Test that the same seed produces the same output."""

    def test_same_seed_same_output(self):
        gen1 = MediaEventGenerator(seed=123, catalog_size=20, user_pool_size=50)
        gen2 = MediaEventGenerator(seed=123, catalog_size=20, user_pool_size=50)

        batch1 = gen1.generate_batch(20)
        batch2 = gen2.generate_batch(20)

        for r1, r2 in zip(batch1, batch2, strict=False):
            assert r1["event_id"] == r2["event_id"]
            assert r1["user_id"] == r2["user_id"]
            assert r1["content_id"] == r2["content_id"]
            assert r1["event_type"] == r2["event_type"]

    def test_different_seed_different_output(self):
        gen1 = MediaEventGenerator(seed=1, catalog_size=20, user_pool_size=50)
        gen2 = MediaEventGenerator(seed=2, catalog_size=20, user_pool_size=50)

        batch1 = gen1.generate_batch(10)
        batch2 = gen2.generate_batch(10)

        # At least some records should differ
        diffs = sum(
            1
            for r1, r2 in zip(batch1, batch2, strict=False)
            if r1["event_id"] != r2["event_id"]
        )
        assert diffs > 0, "Different seeds should produce different output"

    def test_catalog_reproducibility(self):
        gen1 = MediaEventGenerator(seed=42, catalog_size=10, user_pool_size=10)
        gen2 = MediaEventGenerator(seed=42, catalog_size=10, user_pool_size=10)

        cat1 = gen1.get_catalog()
        cat2 = gen2.get_catalog()

        for c1, c2 in zip(cat1, cat2, strict=False):
            assert c1["content_id"] == c2["content_id"]
            assert c1["genre"] == c2["genre"]
            assert c1["duration_min"] == c2["duration_min"]
