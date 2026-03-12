"""
Event Hub Producer for streaming slot machine telemetry.

This module provides real-time event streaming capabilities for
casino floor monitoring scenarios.
"""
import json
import time
import asyncio
from datetime import datetime
from collections.abc import Callable
from typing import Any
import logging

# Optional Azure Event Hubs SDK
try:
    from azure.eventhub import EventHubProducerClient, EventData
    from azure.eventhub.aio import EventHubProducerClient as AsyncEventHubProducerClient
    EVENTHUB_AVAILABLE = True
except ImportError:
    EVENTHUB_AVAILABLE = False

from ..slot_machine_generator import SlotMachineGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventHubProducer:
    """
    Produces streaming events to Azure Event Hub or stdout.

    Can operate in two modes:
    1. Azure Event Hub mode (requires connection string)
    2. Stdout mode (for local testing/development)
    """

    def __init__(
        self,
        connection_string: str | None = None,
        eventhub_name: str | None = None,
        events_per_second: float = 10,
        seed: int | None = None
    ):
        """
        Initialize the producer.

        Args:
            connection_string: Azure Event Hub connection string (optional)
            eventhub_name: Event Hub name (optional)
            events_per_second: Target rate of events per second
            seed: Random seed for reproducibility
        """
        self.connection_string = connection_string
        self.eventhub_name = eventhub_name
        self.events_per_second = events_per_second
        self.generator = SlotMachineGenerator(seed=seed)

        self._running = False
        self._event_count = 0

        if connection_string and EVENTHUB_AVAILABLE:
            self._use_eventhub = True
        else:
            self._use_eventhub = False
            if connection_string and not EVENTHUB_AVAILABLE:
                logger.warning(
                    "azure-eventhub not installed. "
                    "Install with: pip install azure-eventhub"
                )

    def generate_event(self) -> dict[str, Any]:
        """Generate a single slot machine event."""
        return self.generator.generate_record()

    def _event_to_json(self, event: dict[str, Any]) -> str:
        """Convert event to JSON string."""
        # Handle datetime serialization
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        return json.dumps(event, default=json_serializer)

    def run_sync(
        self,
        duration_seconds: int | None = None,
        max_events: int | None = None,
        callback: Callable[[dict[str, Any]], None] | None = None
    ):
        """
        Run the producer synchronously.

        Args:
            duration_seconds: How long to run (None = indefinitely)
            max_events: Maximum events to generate (None = unlimited)
            callback: Optional callback for each event
        """
        self._running = True
        self._event_count = 0
        start_time = time.time()
        interval = 1.0 / self.events_per_second

        logger.info(f"Starting producer at {self.events_per_second} events/second")

        try:
            while self._running:
                # Check termination conditions
                if duration_seconds and (time.time() - start_time) >= duration_seconds:
                    break
                if max_events and self._event_count >= max_events:
                    break

                # Generate event
                event = self.generate_event()
                self._event_count += 1

                # Output event
                if self._use_eventhub:
                    self._send_to_eventhub(event)
                else:
                    print(self._event_to_json(event))

                # Callback if provided
                if callback:
                    callback(event)

                # Rate limiting
                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Producer stopped by user")
        finally:
            self._running = False
            logger.info(f"Generated {self._event_count} events")

    def _send_to_eventhub(self, event: dict[str, Any]) -> None:
        """Send event to Azure Event Hub."""
        if not EVENTHUB_AVAILABLE:
            return

        producer = EventHubProducerClient.from_connection_string(
            self.connection_string,
            eventhub_name=self.eventhub_name
        )

        try:
            event_data_batch = producer.create_batch()
            event_data_batch.add(EventData(self._event_to_json(event)))
            producer.send_batch(event_data_batch)
        finally:
            producer.close()

    async def run_async(
        self,
        duration_seconds: int | None = None,
        max_events: int | None = None,
        batch_size: int = 100
    ):
        """
        Run the producer asynchronously with batching.

        Args:
            duration_seconds: How long to run
            max_events: Maximum events to generate
            batch_size: Number of events per batch
        """
        if not self._use_eventhub or not EVENTHUB_AVAILABLE:
            logger.error("Async mode requires Event Hub connection")
            return

        self._running = True
        self._event_count = 0
        start_time = time.time()

        async with AsyncEventHubProducerClient.from_connection_string(
            self.connection_string,
            eventhub_name=self.eventhub_name
        ) as producer:

            while self._running:
                # Check termination conditions
                if duration_seconds and (time.time() - start_time) >= duration_seconds:
                    break
                if max_events and self._event_count >= max_events:
                    break

                # Create batch
                batch = await producer.create_batch()

                for _ in range(batch_size):
                    event = self.generate_event()
                    try:
                        batch.add(EventData(self._event_to_json(event)))
                        self._event_count += 1
                    except ValueError:
                        # Batch is full
                        break

                # Send batch
                await producer.send_batch(batch)

                # Rate limiting
                await asyncio.sleep(batch_size / self.events_per_second)

        logger.info(f"Generated {self._event_count} events")

    def stop(self):
        """Stop the producer."""
        self._running = False

    @property
    def event_count(self) -> int:
        """Return number of events generated."""
        return self._event_count


def main():
    """CLI entry point for streaming producer."""
    import argparse

    parser = argparse.ArgumentParser(description="Stream slot machine events")
    parser.add_argument("--connection-string", help="Event Hub connection string")
    parser.add_argument("--eventhub-name", help="Event Hub name")
    parser.add_argument("--rate", type=float, default=10, help="Events per second")
    parser.add_argument("--duration", type=int, help="Duration in seconds")
    parser.add_argument("--max-events", type=int, help="Maximum events")
    parser.add_argument("--seed", type=int, help="Random seed")

    args = parser.parse_args()

    producer = EventHubProducer(
        connection_string=args.connection_string,
        eventhub_name=args.eventhub_name,
        events_per_second=args.rate,
        seed=args.seed
    )

    producer.run_sync(
        duration_seconds=args.duration,
        max_events=args.max_events
    )


if __name__ == "__main__":
    main()
