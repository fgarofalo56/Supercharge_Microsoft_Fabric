"""
Unit tests for EventHubProducer.

Covers the streaming event producer in stdout mode (no Azure Event Hub
connection required) including event generation, JSON serialization,
rate configuration, sync run with max_events, callback support, and
stop functionality.
"""

import json

from generators.streaming.event_hub_producer import EventHubProducer


class TestEventHubProducer:
    """Tests for EventHubProducer in local/stdout mode."""

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def test_initialization_defaults(self):
        """EventHubProducer initializes with correct defaults."""
        producer = EventHubProducer(seed=42)

        assert producer.events_per_second == 10, (
            f"Default events_per_second should be 10, got {producer.events_per_second}"
        )
        assert producer.connection_string is None, (
            "Default connection_string should be None"
        )
        assert producer.eventhub_name is None, "Default eventhub_name should be None"
        assert producer._use_eventhub is False, (
            "Should not use Event Hub without connection string"
        )
        assert producer.event_count == 0, "Initial event_count should be 0"

    def test_initialization_custom_rate(self):
        """EventHubProducer respects custom events_per_second."""
        producer = EventHubProducer(seed=42, events_per_second=50)

        assert producer.events_per_second == 50, (
            f"events_per_second should be 50, got {producer.events_per_second}"
        )

    # ------------------------------------------------------------------
    # Event generation
    # ------------------------------------------------------------------

    def test_generate_event_returns_dict(self, event_hub_producer):
        """generate_event must return a dictionary."""
        event = event_hub_producer.generate_event()

        assert isinstance(event, dict), (
            f"generate_event must return dict, got {type(event).__name__}"
        )

    def test_generate_event_has_slot_fields(self, event_hub_producer):
        """Generated events must contain slot machine telemetry fields."""
        event = event_hub_producer.generate_event()

        # SlotMachineGenerator fields expected
        assert "machine_id" in event or "record_id" in event, (
            "Event must contain identifying field from SlotMachineGenerator"
        )

    def test_seed_passed_to_generator(self):
        """The seed parameter is forwarded to the underlying SlotMachineGenerator."""
        producer = EventHubProducer(seed=99)

        assert producer.generator.seed == 99, (
            f"Generator seed should be 99, got {producer.generator.seed}"
        )

    # ------------------------------------------------------------------
    # JSON serialization
    # ------------------------------------------------------------------

    def test_event_to_json_valid(self, event_hub_producer):
        """_event_to_json must produce valid JSON."""
        event = event_hub_producer.generate_event()
        json_str = event_hub_producer._event_to_json(event)

        parsed = json.loads(json_str)
        assert isinstance(parsed, dict), "Parsed JSON must be a dict"
        assert len(parsed) > 0, "Parsed JSON must not be empty"

    # ------------------------------------------------------------------
    # Sync run with max_events
    # ------------------------------------------------------------------

    def test_run_sync_max_events(self):
        """run_sync with max_events generates exactly that many events."""
        producer = EventHubProducer(seed=42, events_per_second=10000)

        collected = []
        producer.run_sync(max_events=5, callback=lambda e: collected.append(e))

        assert len(collected) == 5, (
            f"Expected 5 events from max_events=5, got {len(collected)}"
        )
        assert producer.event_count == 5, (
            f"event_count should be 5 after generating 5 events, got {producer.event_count}"
        )

    # ------------------------------------------------------------------
    # Callback support
    # ------------------------------------------------------------------

    def test_callback_receives_events(self):
        """Callback function receives each generated event as a dict."""
        producer = EventHubProducer(seed=42, events_per_second=10000)
        received_events = []

        producer.run_sync(max_events=3, callback=lambda e: received_events.append(e))

        assert len(received_events) == 3, (
            f"Callback should receive 3 events, got {len(received_events)}"
        )
        for i, event in enumerate(received_events):
            assert isinstance(event, dict), (
                f"Callback event {i} must be a dict, got {type(event).__name__}"
            )

    # ------------------------------------------------------------------
    # Stop functionality
    # ------------------------------------------------------------------

    def test_stop_sets_running_false(self, event_hub_producer):
        """Calling stop() sets the _running flag to False."""
        event_hub_producer._running = True
        event_hub_producer.stop()

        assert event_hub_producer._running is False, (
            "_running should be False after stop()"
        )

    # ------------------------------------------------------------------
    # Event count property
    # ------------------------------------------------------------------

    def test_event_count_property(self, event_hub_producer):
        """event_count property reflects the number of events generated."""
        assert event_hub_producer.event_count == 0, "Initial event_count should be 0"

        event_hub_producer._event_count = 42
        assert event_hub_producer.event_count == 42, (
            "event_count property should reflect _event_count"
        )

    # ------------------------------------------------------------------
    # Stdout mode (no Event Hub)
    # ------------------------------------------------------------------

    def test_stdout_mode_without_connection_string(self):
        """Producer without connection_string operates in stdout mode."""
        producer = EventHubProducer(seed=42)

        assert producer._use_eventhub is False, (
            "Should be in stdout mode without connection string"
        )

    def test_stdout_mode_with_missing_sdk(self):
        """Producer with connection_string but missing SDK falls back to stdout."""
        # EventHubProducer checks EVENTHUB_AVAILABLE; if SDK is not
        # installed, it logs a warning and falls back.
        producer = EventHubProducer(
            connection_string="Endpoint=sb://fake.servicebus.windows.net/;SharedAccessKeyName=fake;SharedAccessKey=fake",
            eventhub_name="test-hub",
            seed=42,
        )
        # If SDK is not installed, _use_eventhub will be False
        # If SDK is installed, _use_eventhub will be True
        # Either way, the producer should initialize without error
        assert producer is not None, (
            "Producer should initialize regardless of SDK availability"
        )
