"""
Slot Machine Generator
======================

Generates synthetic slot machine telemetry data including:
- Machine status events
- Meter readings (coin-in, coin-out, jackpots)
- Game play events
- Error/fault events

Based on SAS Protocol standards used in gaming industry.
"""

from datetime import datetime
from typing import Any

from .base_generator import BaseGenerator


class SlotMachineGenerator(BaseGenerator):
    """Generate slot machine telemetry and events."""

    # Machine configurations
    MACHINE_TYPES = ["Video Slots", "Mechanical Reels", "Video Poker", "Progressive"]
    DENOMINATIONS = [0.01, 0.05, 0.25, 0.50, 1.00, 2.00, 5.00, 10.00, 25.00, 100.00]
    MANUFACTURERS = ["IGT", "Aristocrat", "Konami", "Scientific Games", "Everi"]
    ZONES = ["North", "South", "East", "West", "VIP", "High Limit", "Penny"]

    # Event types based on SAS protocol (aligned with schema)
    EVENT_TYPES = [
        "GAME_PLAY",
        "JACKPOT",
        "METER_UPDATE",
        "DOOR_OPEN",
        "DOOR_CLOSE",
        "BILL_IN",
        "TICKET_OUT",
        "TILT",
        "POWER_OFF",
        "POWER_ON",
    ]

    def __init__(
        self,
        num_machines: int = 500,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Initialize slot machine generator.

        Args:
            num_machines: Number of slot machines to simulate
            seed: Random seed for reproducibility
            start_date: Start date for generated data
            end_date: End date for generated data
        """
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)
        self.num_machines = num_machines
        self._machines = self._generate_machines()

        self._schema = {
            "event_id": "string",
            "machine_id": "string",
            "asset_number": "string",
            "location_id": "string",
            "zone": "string",
            "event_type": "string",
            "event_timestamp": "datetime",
            "denomination": "float",
            "coin_in": "float",
            "coin_out": "float",
            "jackpot_amount": "float",
            "games_played": "int",
            "theoretical_hold": "float",
            "actual_hold": "float",
            "player_id": "string",
            "session_id": "string",
            "machine_type": "string",
            "manufacturer": "string",
            "game_theme": "string",
            "error_code": "string",
            "error_message": "string",
        }

    def _generate_machines(self) -> list[dict[str, Any]]:
        """Generate static machine configurations."""
        machines = []
        for i in range(self.num_machines):
            machine = {
                "machine_id": f"SLOT-{i + 1:04d}",
                "asset_number": f"AST-{self.faker.unique.random_number(digits=8)}",
                "location_id": f"LOC-{self.rng.integers(1, 20):03d}",
                "zone": self.rng.choice(self.ZONES),
                "denomination": self.rng.choice(self.DENOMINATIONS),
                "machine_type": self.rng.choice(self.MACHINE_TYPES),
                "manufacturer": self.rng.choice(self.MANUFACTURERS),
                "game_theme": self.faker.word().title()
                + " "
                + self.rng.choice(
                    ["Fortune", "Riches", "Gold", "Diamond", "Wild", "Bonus"]
                ),
                "theoretical_hold": round(self.rng.uniform(0.04, 0.12), 4),
                "max_bet": self.rng.choice([100, 200, 300, 500, 1000]),
            }
            machines.append(machine)
        return machines

    def generate_record(self) -> dict[str, Any]:
        """Generate a single slot machine event."""
        # Select random machine
        machine = self.rng.choice(self._machines)

        # Determine event type (weighted) - 10 event types
        event_type = self.weighted_choice(
            self.EVENT_TYPES,
            [0.70, 0.02, 0.10, 0.02, 0.02, 0.05, 0.04, 0.03, 0.01, 0.01],
        )

        # Generate base record
        record = {
            "event_id": self.generate_uuid(),
            "machine_id": machine["machine_id"],
            "asset_number": machine["asset_number"],
            "location_id": machine["location_id"],
            "zone": machine["zone"],
            "event_type": event_type,
            "event_timestamp": self.random_datetime(),
            "denomination": machine["denomination"],
            "machine_type": machine["machine_type"],
            "manufacturer": machine["manufacturer"],
            "game_theme": machine["game_theme"],
            "theoretical_hold": machine["theoretical_hold"],
        }

        # Event-specific data
        if event_type == "GAME_PLAY":
            record = self._add_gameplay_data(record, machine)
        elif event_type == "JACKPOT":
            record = self._add_jackpot_data(record, machine)
        elif event_type == "METER_UPDATE":
            record = self._add_meter_data(record, machine)
        elif event_type in ["TILT", "POWER_OFF"]:
            record = self._add_error_data(record)
        elif event_type == "BILL_IN":
            record = self._add_bill_data(record)

        # Add nullable fields
        record.setdefault("coin_in", None)
        record.setdefault("coin_out", None)
        record.setdefault("jackpot_amount", None)
        record.setdefault("games_played", 0)
        record.setdefault("actual_hold", None)
        record.setdefault("player_id", None)
        record.setdefault("session_id", None)
        record.setdefault("error_code", None)
        record.setdefault("error_message", None)

        return self.add_metadata_columns(record)

    def _add_gameplay_data(
        self, record: dict[str, Any], machine: dict[str, Any]
    ) -> dict[str, Any]:
        """Add game play specific data."""
        bet_amount = machine["denomination"] * self.rng.integers(1, 10)
        win_amount = 0

        # Determine if win (based on theoretical hold)
        if self.rng.random() > machine["theoretical_hold"]:
            # Calculate win amount (most wins are small)
            win_multiplier = self.weighted_choice(
                [0, 0.5, 1, 2, 5, 10, 50, 100],
                [0.30, 0.25, 0.20, 0.12, 0.08, 0.03, 0.015, 0.005],
            )
            win_amount = round(bet_amount * win_multiplier, 2)

        record["coin_in"] = round(bet_amount, 2)
        record["coin_out"] = round(win_amount, 2)
        record["games_played"] = 1

        # 60% chance of having a player card
        if self.rng.random() < 0.6:
            record["player_id"] = f"P{self.rng.integers(1, 10000)}"
            record["session_id"] = f"SES-{self.generate_uuid()[:8]}"

        return record

    def _add_jackpot_data(
        self, record: dict[str, Any], machine: dict[str, Any]
    ) -> dict[str, Any]:
        """Add jackpot event data."""
        # Jackpot amounts vary by denomination
        base_jackpot = machine["denomination"] * 1000
        multiplier = self.weighted_choice(
            [1, 2, 5, 10, 50], [0.50, 0.25, 0.15, 0.08, 0.02]
        )
        jackpot_amount = round(base_jackpot * multiplier, 2)

        record["jackpot_amount"] = jackpot_amount
        record["coin_out"] = jackpot_amount

        # Jackpots usually have player tracking
        record["player_id"] = f"P{self.rng.integers(1, 10000)}"
        record["session_id"] = f"SES-{self.generate_uuid()[:8]}"

        return record

    def _add_meter_data(
        self, record: dict[str, Any], machine: dict[str, Any]
    ) -> dict[str, Any]:
        """Add meter update data (periodic readings)."""
        # Simulate cumulative meter values
        base_coin_in = self.rng.uniform(10000, 1000000)
        actual_hold = machine["theoretical_hold"] + self.rng.uniform(-0.02, 0.02)

        record["coin_in"] = round(base_coin_in, 2)
        record["coin_out"] = round(base_coin_in * (1 - actual_hold), 2)
        record["actual_hold"] = round(actual_hold, 4)
        record["games_played"] = int(base_coin_in / machine["denomination"] / 3)

        return record

    def _add_error_data(self, record: dict[str, Any]) -> dict[str, Any]:
        """Add error/tilt event data."""
        error_codes = {
            "E001": "Door Open Tilt",
            "E002": "Bill Jam",
            "E003": "Coin Hopper Empty",
            "E004": "Communication Error",
            "E005": "Power Fluctuation",
            "E006": "Reel Error",
            "E007": "Touch Screen Error",
        }
        code = self.rng.choice(list(error_codes.keys()))
        record["error_code"] = code
        record["error_message"] = error_codes[code]
        return record

    def _add_bill_data(self, record: dict[str, Any]) -> dict[str, Any]:
        """Add bill acceptor data."""
        bills = [1, 5, 10, 20, 50, 100]
        weights = [0.10, 0.15, 0.20, 0.35, 0.15, 0.05]
        amount = self.weighted_choice(bills, weights)
        record["coin_in"] = float(amount)
        return record

    def get_machines(self) -> list[dict[str, Any]]:
        """Return the list of machine configurations."""
        return self._machines
