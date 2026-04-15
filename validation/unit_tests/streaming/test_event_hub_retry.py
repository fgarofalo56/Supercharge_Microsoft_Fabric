"""
EventHub Producer Retry/Backoff Tests
======================================

Tests for the EventHub producer's retry logic with exponential backoff.
Uses mocking to simulate send failures without requiring an actual Event Hub.
"""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Ensure generators are importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "data_generation"))

from generators.streaming import event_hub_producer as _eh_mod
from generators.streaming.event_hub_producer import (
    DEFAULT_BASE_DELAY,
    DEFAULT_MAX_DELAY,
    DEFAULT_MAX_RETRIES,
    EventHubProducer,
)

# Autouse fixture: the module-level EVENTHUB_AVAILABLE flag gates _send_to_eventhub
# from running when azure-eventhub isn't installed. The retry tests exercise the
# retry path through a mock producer, so force the flag on and stub EventData.


@pytest.fixture(autouse=True)
def _force_eventhub_available(monkeypatch):
    monkeypatch.setattr(_eh_mod, "EVENTHUB_AVAILABLE", True)
    monkeypatch.setattr(
        _eh_mod, "EventData", lambda body=None: MagicMock(name="EventData"), raising=False
    )
    yield


class TestEventHubProducerDefaults:
    """Test producer initialization and default configuration."""

    def test_default_retry_config(self):
        """Producer should have default retry configuration."""
        producer = EventHubProducer(seed=42)
        assert producer.max_retries == DEFAULT_MAX_RETRIES
        assert producer.base_delay == DEFAULT_BASE_DELAY
        assert producer.max_delay == DEFAULT_MAX_DELAY

    def test_custom_retry_config(self):
        """Producer should accept custom retry configuration."""
        producer = EventHubProducer(
            seed=42,
            max_retries=5,
            base_delay=2.0,
            max_delay=60.0,
        )
        assert producer.max_retries == 5
        assert producer.base_delay == 2.0
        assert producer.max_delay == 60.0

    def test_initial_counters_zero(self):
        """All counters should start at zero."""
        producer = EventHubProducer(seed=42)
        assert producer.event_count == 0
        assert producer.retry_count == 0
        assert producer.failed_count == 0

    def test_stdout_mode_without_connection(self):
        """Producer without connection string should use stdout mode."""
        producer = EventHubProducer(seed=42)
        assert producer._use_eventhub is False

    def test_event_generation(self):
        """Producer should generate valid events."""
        producer = EventHubProducer(seed=42)
        event = producer.generate_event()
        assert "machine_id" in event
        assert "event_type" in event
        assert "event_timestamp" in event


class TestEventHubRetryLogic:
    """Test retry behavior with mocked Event Hub client."""

    def test_successful_send_no_retry(self):
        """Successful send should not trigger retries."""
        producer = EventHubProducer(seed=42)
        producer._use_eventhub = True

        # Mock the sync producer
        mock_producer = MagicMock()
        mock_batch = MagicMock()
        mock_producer.create_batch.return_value = mock_batch
        producer._sync_producer = mock_producer

        event = producer.generate_event()
        producer._send_to_eventhub(event)

        assert mock_producer.send_batch.call_count == 1
        assert producer.retry_count == 0
        assert producer.failed_count == 0

    def test_retry_on_transient_failure(self):
        """Should retry on transient failure then succeed."""
        producer = EventHubProducer(seed=42, max_retries=3, base_delay=0.01)
        producer._use_eventhub = True

        mock_producer = MagicMock()
        mock_batch = MagicMock()
        mock_producer.create_batch.return_value = mock_batch
        # Fail twice, then succeed
        mock_producer.send_batch.side_effect = [
            Exception("Transient error 1"),
            Exception("Transient error 2"),
            None,  # Success on 3rd attempt
        ]
        producer._sync_producer = mock_producer

        event = producer.generate_event()
        producer._send_to_eventhub(event)

        assert mock_producer.send_batch.call_count == 3
        assert producer.retry_count == 2
        assert producer.failed_count == 0

    def test_exhausted_retries(self):
        """Should count as failed after exhausting all retries."""
        producer = EventHubProducer(seed=42, max_retries=2, base_delay=0.01)
        producer._use_eventhub = True

        mock_producer = MagicMock()
        mock_batch = MagicMock()
        mock_producer.create_batch.return_value = mock_batch
        # Fail all attempts
        mock_producer.send_batch.side_effect = Exception("Persistent error")
        producer._sync_producer = mock_producer

        event = producer.generate_event()
        producer._send_to_eventhub(event)

        # 1 initial + 2 retries = 3 total attempts
        assert mock_producer.send_batch.call_count == 3
        assert producer.retry_count == 2
        assert producer.failed_count == 1

    def test_backoff_delay_increases(self):
        """Backoff delay should increase exponentially."""
        producer = EventHubProducer(
            seed=42,
            max_retries=3,
            base_delay=0.1,
            max_delay=10.0,
        )
        producer._use_eventhub = True

        mock_producer = MagicMock()
        mock_batch = MagicMock()
        mock_producer.create_batch.return_value = mock_batch
        mock_producer.send_batch.side_effect = Exception("Always fail")
        producer._sync_producer = mock_producer

        delays = []
        original_sleep = time.sleep

        def mock_sleep(duration):
            delays.append(duration)
            # Don't actually sleep in tests

        with patch("time.sleep", mock_sleep):
            producer._send_to_eventhub(producer.generate_event())

        # Should have 3 delays (for 3 retries)
        assert len(delays) == 3
        # Each delay should be larger than the previous
        for i in range(1, len(delays)):
            assert delays[i] > delays[i - 1], (
                f"Delay {i} ({delays[i]}) should be > delay {i-1} ({delays[i-1]})"
            )

    def test_backoff_respects_max_delay(self):
        """Backoff should be capped at max_delay."""
        producer = EventHubProducer(
            seed=42,
            max_retries=10,
            base_delay=1.0,
            max_delay=5.0,
        )
        producer._use_eventhub = True

        mock_producer = MagicMock()
        mock_batch = MagicMock()
        mock_producer.create_batch.return_value = mock_batch
        mock_producer.send_batch.side_effect = Exception("Always fail")
        producer._sync_producer = mock_producer

        delays = []
        with patch("time.sleep", lambda d: delays.append(d)):
            producer._send_to_eventhub(producer.generate_event())

        for delay in delays:
            assert delay <= 5.0, f"Delay {delay} exceeds max_delay 5.0"


class TestEventHubSyncRun:
    """Test the sync run method with event counting."""

    def test_max_events_limit(self):
        """run_sync should stop after max_events."""
        producer = EventHubProducer(seed=42, events_per_second=10000)
        producer.run_sync(max_events=5)
        assert producer.event_count == 5

    def test_callback_invoked(self):
        """Callback should be invoked for each event."""
        producer = EventHubProducer(seed=42, events_per_second=10000)
        events = []
        producer.run_sync(max_events=3, callback=lambda e: events.append(e))
        assert len(events) == 3
        assert all("machine_id" in e for e in events)

    def test_stop_method(self):
        """stop() should halt the producer."""
        producer = EventHubProducer(seed=42, events_per_second=10000)
        # Run for a short time then stop
        import threading

        def stop_after():
            time.sleep(0.1)
            producer.stop()

        t = threading.Thread(target=stop_after)
        t.start()
        producer.run_sync(max_events=100000)  # Would run forever without stop
        t.join()
        assert producer.event_count > 0
        assert producer.event_count < 100000
