"""
Table Games Generator
=====================

Generates synthetic table game data including:
- Blackjack, Craps, Roulette, Baccarat, Poker
- Buy-ins, cash-outs, markers
- Dealer assignments
- Ratings and player tracking
"""

from datetime import datetime
from typing import Any

from .base_generator import BaseGenerator


class TableGamesGenerator(BaseGenerator):
    """Generate table game transactions and events."""

    GAME_TYPES = ["Blackjack", "Craps", "Roulette", "Baccarat", "Poker", "Pai Gow"]
    GAME_WEIGHTS = [0.35, 0.20, 0.15, 0.15, 0.10, 0.05]

    TABLE_LIMITS = {
        "Blackjack": [(10, 500), (25, 1000), (100, 5000), (500, 25000)],
        "Craps": [(10, 5000), (25, 10000), (100, 25000)],
        "Roulette": [(5, 500), (25, 2000), (100, 10000)],
        "Baccarat": [(50, 5000), (100, 15000), (500, 100000)],
        "Poker": [(1, 2), (2, 5), (5, 10), (25, 50), (100, 200)],
        "Pai Gow": [(25, 5000), (50, 10000), (100, 25000)],
    }

    EVENT_TYPES = [
        "BUY_IN",
        "CASH_OUT",
        "MARKER_ISSUED",
        "MARKER_PAID",
        "FILL",
        "CREDIT",
        "RATING_START",
        "RATING_END",
        "SHIFT_START",
        "SHIFT_END",
    ]

    ZONES = ["Main Pit", "High Limit", "VIP Salon", "Poker Room", "Asian Gaming"]

    def __init__(
        self,
        num_tables: int = 100,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Initialize table game generator.

        Args:
            num_tables: Number of tables to simulate
            seed: Random seed for reproducibility
            start_date: Start date for generated data
            end_date: End date for generated data
        """
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)
        self.num_tables = num_tables
        self._tables = self._generate_tables()
        self._dealers = self._generate_dealers()

        self._schema = {
            "event_id": "string",
            "table_id": "string",
            "game_type": "string",
            "table_number": "int",
            "zone": "string",
            "event_type": "string",
            "event_timestamp": "datetime",
            "player_id": "string",
            "player_rating_id": "string",
            "dealer_id": "string",
            "shift": "string",
            "amount": "float",
            "chip_denomination": "float",
            "min_bet": "float",
            "max_bet": "float",
            "average_bet": "float",
            "hands_played": "int",
            "hours_played": "float",
            "theoretical_win": "float",
            "actual_win_loss": "float",
            "marker_number": "string",
            "fill_slip_number": "string",
            "drop_amount": "float",
        }

    def _generate_tables(self) -> list[dict[str, Any]]:
        """Generate static table configurations."""
        tables = []
        table_num = 1

        for _ in range(self.num_tables):
            game_type = self.weighted_choice(self.GAME_TYPES, self.GAME_WEIGHTS)
            limits = self.TABLE_LIMITS[game_type]
            min_bet, max_bet = limits[self.rng.integers(0, len(limits))]

            # Generate zone code for table_id (first 2 letters of zone)
            zone = self.rng.choice(self.ZONES)
            zone_code = "".join(c for c in zone if c.isupper())[:2]
            if len(zone_code) < 2:
                zone_code = zone[:2].upper()

            table = {
                "table_id": f"TBL-{zone_code}-{table_num:03d}",
                "table_number": table_num,
                "game_type": game_type,
                "zone": zone,
                "min_bet": min_bet,
                "max_bet": max_bet,
                "positions": 7 if game_type == "Blackjack" else 8,
                "house_edge": self._get_house_edge(game_type),
            }
            tables.append(table)
            table_num += 1

        return tables

    def _generate_dealers(self) -> list[dict[str, Any]]:
        """Generate dealer roster."""
        dealers = []
        for i in range(150):
            dealer = {
                "dealer_id": f"DLR-{i+1:04d}",
                "first_name": self.faker.first_name(),
                "last_name": self.faker.last_name(),
                "certifications": self.rng.choice(
                    self.GAME_TYPES, size=self.rng.integers(1, 4), replace=False
                ).tolist(),
            }
            dealers.append(dealer)
        return dealers

    def _get_house_edge(self, game_type: str) -> float:
        """Get theoretical house edge for a game type."""
        edges = {
            "Blackjack": 0.005,
            "Craps": 0.014,
            "Roulette": 0.053,
            "Baccarat": 0.0106,
            "Poker": 0.025,  # Rake equivalent
            "Pai Gow": 0.026,
        }
        return edges.get(game_type, 0.02)

    def _get_shift(self, timestamp: datetime) -> str:
        """Determine shift based on time."""
        hour = timestamp.hour
        if 6 <= hour < 14:
            return "Day"
        elif 14 <= hour < 22:
            return "Swing"
        else:
            return "Grave"

    def generate_record(self) -> dict[str, Any]:
        """Generate a single table game event."""
        table = self.rng.choice(self._tables)
        timestamp = self.random_datetime()

        # Select event type (weighted toward player activity)
        event_type = self.weighted_choice(
            self.EVENT_TYPES,
            [0.25, 0.20, 0.05, 0.05, 0.08, 0.07, 0.12, 0.12, 0.03, 0.03],
        )

        # Select dealer for table
        eligible_dealers = [
            d for d in self._dealers if table["game_type"] in d["certifications"]
        ]
        dealer = (
            self.rng.choice(eligible_dealers) if eligible_dealers else self._dealers[0]
        )

        record = {
            "event_id": self.generate_uuid(),
            "table_id": table["table_id"],
            "game_type": table["game_type"],
            "table_number": table["table_number"],
            "zone": table["zone"],
            "event_type": event_type,
            "event_timestamp": timestamp,
            "dealer_id": dealer["dealer_id"],
            "shift": self._get_shift(timestamp),
            "min_bet": table["min_bet"],
            "max_bet": table["max_bet"],
        }

        # Event-specific data
        if event_type in ["BUY_IN", "CASH_OUT"]:
            record = self._add_buyin_cashout(record, table, event_type)
        elif event_type in ["MARKER_ISSUED", "MARKER_PAID"]:
            record = self._add_marker_data(record, table)
        elif event_type in ["FILL", "CREDIT"]:
            record = self._add_fill_credit(record, table, event_type)
        elif event_type in ["RATING_START", "RATING_END"]:
            record = self._add_rating_data(record, table)
        elif event_type in ["SHIFT_START", "SHIFT_END"]:
            record = self._add_shift_data(record, table)

        # Add nullable defaults
        record.setdefault("player_id", None)
        record.setdefault("player_rating_id", None)
        record.setdefault("amount", None)
        record.setdefault("chip_denomination", None)
        record.setdefault("average_bet", None)
        record.setdefault("hands_played", None)
        record.setdefault("hours_played", None)
        record.setdefault("theoretical_win", None)
        record.setdefault("actual_win_loss", None)
        record.setdefault("marker_number", None)
        record.setdefault("fill_slip_number", None)
        record.setdefault("drop_amount", None)

        return self.add_metadata_columns(record)

    def _add_buyin_cashout(
        self, record: dict[str, Any], table: dict[str, Any], event_type: str
    ) -> dict[str, Any]:
        """Add buy-in or cash-out data."""
        record["player_id"] = f"PLY-{self.rng.integers(1, 10000):06d}"

        # Amount based on table limits
        min_amount = table["min_bet"] * 10
        max_amount = table["max_bet"] * 5

        if event_type == "BUY_IN":
            record["amount"] = round(self.rng.uniform(min_amount, max_amount), 0)
        else:
            # Cash out typically different from buy-in
            record["amount"] = round(
                self.rng.uniform(min_amount * 0.5, max_amount * 1.5), 0
            )

        record["chip_denomination"] = float(
            self.rng.choice([1, 5, 25, 100, 500, 1000])
        )

        return record

    def _add_marker_data(
        self, record: dict[str, Any], table: dict[str, Any]
    ) -> dict[str, Any]:
        """Add marker (credit) data."""
        record["player_id"] = f"PLY-{self.rng.integers(1, 10000):06d}"
        record["marker_number"] = f"MKR-{self.rng.integers(100000, 999999)}"
        record["amount"] = round(
            self.rng.choice([1000, 2500, 5000, 10000, 25000, 50000, 100000]), 0
        )
        return record

    def _add_fill_credit(
        self, record: dict[str, Any], table: dict[str, Any], event_type: str
    ) -> dict[str, Any]:
        """Add fill or credit slip data."""
        record["fill_slip_number"] = (
            f"{'FIL' if event_type == 'FILL' else 'CRD'}-{self.rng.integers(100000, 999999)}"
        )
        record["amount"] = round(
            self.rng.choice([5000, 10000, 25000, 50000, 100000]), 0
        )
        record["chip_denomination"] = float(self.rng.choice([25, 100, 500, 1000]))
        return record

    def _add_rating_data(
        self, record: dict[str, Any], table: dict[str, Any]
    ) -> dict[str, Any]:
        """Add player rating data."""
        record["player_id"] = f"PLY-{self.rng.integers(1, 10000):06d}"
        record["player_rating_id"] = f"RAT-{self.generate_uuid()[:8]}"

        avg_bet = self.rng.uniform(table["min_bet"], max(table["min_bet"] + 1, table["max_bet"] * 0.3))
        hours = round(self.rng.uniform(0.5, 6), 1)
        hands = int(hours * self.rng.integers(30, 80))

        record["average_bet"] = round(avg_bet, 0)
        record["hands_played"] = hands
        record["hours_played"] = hours
        record["theoretical_win"] = round(avg_bet * hands * table["house_edge"], 2)
        record["actual_win_loss"] = round(
            avg_bet * hands * self.rng.uniform(-0.5, 0.3), 2
        )

        return record

    def _add_shift_data(
        self, record: dict[str, Any], table: dict[str, Any]
    ) -> dict[str, Any]:
        """Add shift start/end data with drop amounts."""
        record["drop_amount"] = round(self.rng.uniform(5000, 100000), 0)
        return record
