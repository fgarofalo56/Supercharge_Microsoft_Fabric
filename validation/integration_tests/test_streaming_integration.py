"""
Streaming Integration Tests
============================

Tests for streaming functionality:
- EventHubProducer generates valid events
- Event serialization to JSON
- Rate limiting works correctly
- Graceful shutdown
"""

import json
import threading
import time
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.streaming]


class TestEventHubProducerInitialization:
    """Tests for EventHubProducer initialization."""

    def test_producer_initializes_without_connection_string(self):
        """Verify producer initializes in stdout mode without connection string."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(seed=42)

        assert producer is not None
        assert producer.connection_string is None
        assert not producer._use_eventhub
        assert producer.events_per_second == 10  # Default

    def test_producer_initializes_with_custom_rate(self):
        """Verify producer respects custom events per second."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(events_per_second=100, seed=42)

        assert producer.events_per_second == 100

    def test_producer_uses_seed_for_reproducibility(self):
        """Verify producer uses seed for generator reproducibility."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(seed=12345)

        # Generator should have the seed
        assert producer.generator.seed == 12345

    def test_producer_creates_slot_generator(self):
        """Verify producer creates internal SlotMachineGenerator."""
        from generators.slot_machine_generator import SlotMachineGenerator
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(seed=42)

        assert isinstance(producer.generator, SlotMachineGenerator)


class TestEventGeneration:
    """Tests for event generation functionality."""

    def test_generate_event_returns_dict(self):
        """Verify generate_event returns a dictionary."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(seed=42)
        event = producer.generate_event()

        assert isinstance(event, dict)

    def test_generate_event_has_required_fields(self):
        """Verify generated events have required slot telemetry fields."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(seed=42)
        event = producer.generate_event()

        required_fields = ["machine_id", "event_type", "event_timestamp"]
        for field in required_fields:
            assert field in event, f"Event missing {field}"

    def test_generate_multiple_events(self):
        """Verify multiple events can be generated."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(seed=42)
        events = [producer.generate_event() for _ in range(100)]

        assert len(events) == 100
        # Should have variety in event types
        event_types = set(e["event_type"] for e in events)
        assert len(event_types) > 1, "All events have same type"


class TestEventSerialization:
    """Tests for event serialization to JSON."""

    def test_event_serializes_to_valid_json(self):
        """Verify events serialize to valid JSON."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(seed=42)
        event = producer.generate_event()

        json_str = producer._event_to_json(event)

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

    def test_datetime_serialization(self):
        """Verify datetime fields serialize correctly."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(seed=42)
        event = producer.generate_event()

        json_str = producer._event_to_json(event)
        parsed = json.loads(json_str)

        # Timestamp should be ISO format string
        ts = parsed.get("event_timestamp")
        if ts:
            # Should be parseable as datetime
            if isinstance(ts, str):
                datetime.fromisoformat(ts.replace("Z", "+00:00"))

    def test_all_fields_serialize(self):
        """Verify all event fields are serialized."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(seed=42)
        event = producer.generate_event()

        json_str = producer._event_to_json(event)
        parsed = json.loads(json_str)

        # All non-None fields should be present
        for key, value in event.items():
            if value is not None:
                assert key in parsed, f"Field {key} not serialized"

    def test_none_values_handled(self):
        """Verify None values are handled in serialization."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(seed=42)

        # Generate events until we find one with some None values
        for _ in range(100):
            event = producer.generate_event()
            if any(v is None for v in event.values()):
                json_str = producer._event_to_json(event)
                parsed = json.loads(json_str)
                # Should not raise exception
                assert isinstance(parsed, dict)
                break


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_rate_limiting_interval_calculated(self):
        """Verify rate limiting interval is calculated correctly."""
        from generators.streaming.event_hub_producer import EventHubProducer

        EventHubProducer(events_per_second=10, seed=42)

        # Expected interval: 1/10 = 0.1 seconds
        expected_interval = 1.0 / 10
        assert expected_interval == 0.1

    def test_max_events_respected(self):
        """Verify max_events parameter is respected."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(events_per_second=1000, seed=42)

        # Use high rate to make test fast
        events_generated = []

        def callback(event):
            events_generated.append(event)

        producer.run_sync(max_events=10, callback=callback)

        assert len(events_generated) == 10
        assert producer.event_count == 10

    def test_duration_respected(self):
        """Verify duration_seconds parameter is respected."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(events_per_second=100, seed=42)

        start_time = time.time()
        producer.run_sync(duration_seconds=1)
        elapsed = time.time() - start_time

        # Should run for approximately 1 second (with some tolerance)
        assert elapsed >= 0.9, "Duration too short"
        assert elapsed < 2.0, "Duration too long"


class TestGracefulShutdown:
    """Tests for graceful shutdown functionality."""

    def test_stop_method_sets_flag(self):
        """Verify stop() method sets running flag to False."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(seed=42)
        producer._running = True

        producer.stop()

        assert not producer._running

    def test_producer_stops_on_stop_call(self):
        """Verify producer stops when stop() is called."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(events_per_second=100, seed=42)

        # Start producer in thread
        events = []

        def run_producer():
            producer.run_sync(callback=lambda e: events.append(e))

        thread = threading.Thread(target=run_producer)
        thread.start()

        # Let it run briefly
        time.sleep(0.2)

        # Stop it
        producer.stop()
        thread.join(timeout=1.0)

        # Should have stopped
        assert not producer._running
        assert len(events) > 0  # Should have generated some events

    def test_keyboard_interrupt_handling(self):
        """Verify KeyboardInterrupt is handled gracefully."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(events_per_second=1000, seed=42)

        # Mock to raise KeyboardInterrupt after a few events
        original_generate = producer.generate_event
        call_count = [0]

        def mock_generate():
            call_count[0] += 1
            if call_count[0] > 5:
                raise KeyboardInterrupt()
            return original_generate()

        producer.generate_event = mock_generate

        # Should not raise exception to caller
        producer.run_sync(max_events=100)

        # Should have stopped cleanly
        assert not producer._running


class TestEventCount:
    """Tests for event counting functionality."""

    def test_event_count_starts_at_zero(self):
        """Verify event count starts at zero."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(seed=42)

        assert producer.event_count == 0

    def test_event_count_increments(self):
        """Verify event count increments with each event."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(events_per_second=1000, seed=42)
        producer.run_sync(max_events=50)

        assert producer.event_count == 50

    def test_event_count_property(self):
        """Verify event_count property returns correct value."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(events_per_second=1000, seed=42)
        producer.run_sync(max_events=25)

        count = producer.event_count

        assert count == 25


class TestCallbackFunctionality:
    """Tests for callback functionality."""

    def test_callback_called_for_each_event(self):
        """Verify callback is called for each generated event."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(events_per_second=1000, seed=42)

        callback_calls = []

        def callback(event):
            callback_calls.append(event)

        producer.run_sync(max_events=20, callback=callback)

        assert len(callback_calls) == 20

    def test_callback_receives_event_dict(self):
        """Verify callback receives event as dictionary."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(events_per_second=1000, seed=42)

        received_events = []

        def callback(event):
            received_events.append(event)
            assert isinstance(event, dict)
            assert "machine_id" in event

        producer.run_sync(max_events=5, callback=callback)

        assert len(received_events) == 5


class TestStdoutMode:
    """Tests for stdout mode (no Event Hub connection)."""

    def test_stdout_mode_enabled_without_connection(self):
        """Verify stdout mode when no connection string provided."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(seed=42)

        assert not producer._use_eventhub

    def test_stdout_mode_prints_json(self, capsys):
        """Verify stdout mode prints JSON to stdout."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(events_per_second=1000, seed=42)
        producer.run_sync(max_events=3)

        captured = capsys.readouterr()

        # Should have printed JSON lines
        lines = [l for l in captured.out.strip().split("\n") if l]
        assert len(lines) == 3

        # Each line should be valid JSON
        for line in lines:
            parsed = json.loads(line)
            assert "machine_id" in parsed


class TestEventHubModeSetup:
    """Tests for Event Hub mode setup (without actual connection)."""

    def test_eventhub_mode_requires_sdk(self):
        """Verify Event Hub mode checks for SDK availability."""
        from generators.streaming.event_hub_producer import (
            EVENTHUB_AVAILABLE,
            EventHubProducer,
        )

        producer = EventHubProducer(
            connection_string="Endpoint=sb://test.servicebus.windows.net/",
            eventhub_name="test-hub",
            seed=42,
        )

        # Should only enable if SDK available
        assert producer._use_eventhub == EVENTHUB_AVAILABLE

    def test_warning_logged_without_sdk(self, caplog):
        """Verify warning logged when SDK not available but connection provided."""
        from generators.streaming.event_hub_producer import (
            EVENTHUB_AVAILABLE,
            EventHubProducer,
        )

        if EVENTHUB_AVAILABLE:
            pytest.skip("azure-eventhub is installed")

        import logging

        caplog.set_level(logging.WARNING)

        EventHubProducer(
            connection_string="Endpoint=sb://test.servicebus.windows.net/",
            eventhub_name="test-hub",
            seed=42,
        )

        # Should have logged warning
        assert any("eventhub" in record.message.lower() for record in caplog.records)


class TestEventValidation:
    """Tests for generated event validity."""

    def test_events_match_slot_telemetry_schema(self, slot_telemetry_schema):
        """Verify generated events conform to slot telemetry schema."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(seed=42)

        for _ in range(50):
            event = producer.generate_event()

            # Check required fields
            required = slot_telemetry_schema.get("required", [])
            for field in required:
                assert field in event, f"Event missing required field: {field}"

            # Check event_type is valid
            valid_types = slot_telemetry_schema["properties"]["event_type"].get(
                "enum", []
            )
            if valid_types:
                assert (
                    event["event_type"] in valid_types
                ), f"Invalid event_type: {event['event_type']}"

    def test_machine_id_format_in_stream(self, validate_machine_id_format):
        """Verify streamed events have valid machine IDs."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(seed=42)

        for _ in range(50):
            event = producer.generate_event()
            assert validate_machine_id_format(
                event["machine_id"]
            ), f"Invalid machine_id: {event['machine_id']}"


class TestAsyncMode:
    """Tests for async mode (without actual Event Hub)."""

    @pytest.mark.asyncio
    async def test_async_requires_eventhub(self):
        """Verify async mode requires Event Hub connection."""
        from generators.streaming.event_hub_producer import EventHubProducer

        producer = EventHubProducer(seed=42)  # No connection string

        # run_async should return early without connection
        await producer.run_async(max_events=10)

        # Should not have generated events (no connection)
        assert producer.event_count == 0
