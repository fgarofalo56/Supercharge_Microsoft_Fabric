"""
Player Generator
================

Generates synthetic player profile and loyalty data including:
- Player demographics (with PII handling)
- Loyalty tier information
- Preferences and contact info
- Gaming history summary
"""

from datetime import datetime
from typing import Any

from .base_generator import BaseGenerator


class PlayerGenerator(BaseGenerator):
    """Generate player profiles and loyalty data."""

    LOYALTY_TIERS = ["Bronze", "Silver", "Gold", "Platinum", "Diamond"]
    TIER_WEIGHTS = [0.40, 0.30, 0.18, 0.09, 0.03]

    PREFERRED_GAMES = [
        "Video Slots",
        "Blackjack",
        "Craps",
        "Roulette",
        "Poker",
        "Baccarat",
        "Video Poker",
    ]

    COMMUNICATION_PREFERENCES = ["Email", "SMS", "Mail", "Phone", "None"]
    MARKETING_CHANNELS = ["Email", "Direct Mail", "SMS", "App Push", "None"]

    def __init__(
        self,
        seed: int | None = None,
        include_pii: bool = False,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Initialize player generator.

        Args:
            seed: Random seed for reproducibility
            include_pii: If True, include actual PII; if False, hash/mask PII
            start_date: Start date for generated data
            end_date: End date for generated data
        """
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)
        self.include_pii = include_pii
        self._salt = "fabric-poc-2024"  # Salt for hashing

        self._schema = {
            "player_id": "string",
            "loyalty_number": "string",
            "first_name": "string",
            "last_name": "string",
            "email": "string",
            "phone": "string",
            "date_of_birth": "date",
            "ssn_hash": "string",
            "ssn_masked": "string",
            "address": "string",
            "city": "string",
            "state": "string",
            "zip_code": "string",
            "country": "string",
            "loyalty_tier": "string",
            "points_balance": "int",
            "lifetime_points": "int",
            "tier_credits": "int",
            "enrollment_date": "date",
            "last_visit_date": "date",
            "total_visits": "int",
            "total_theo": "float",
            "total_actual_win_loss": "float",
            "average_daily_theo": "float",
            "preferred_game": "string",
            "communication_preference": "string",
            "marketing_opt_in": "bool",
            "marketing_channel": "string",
            "host_assigned": "string",
            "vip_flag": "bool",
            "self_excluded": "bool",
            "account_status": "string",
        }

    def generate_record(self) -> dict[str, Any]:
        """Generate a single player profile."""
        player_id = f"P{self.rng.integers(1, 999999)}"
        loyalty_number = f"LC{self.rng.integers(100000000, 999999999)}"

        # Generate personal info
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()

        # Generate SSN (will be hashed/masked)
        ssn = self.faker.ssn()

        # Determine loyalty tier
        tier = self.weighted_choice(self.LOYALTY_TIERS, self.TIER_WEIGHTS)
        tier_idx = self.LOYALTY_TIERS.index(tier)

        # Calculate points and metrics based on tier
        base_points = [1000, 5000, 25000, 100000, 500000]
        points_balance = int(self.rng.uniform(0.1, 2.0) * base_points[tier_idx])
        lifetime_points = int(points_balance * self.rng.uniform(3, 20))
        tier_credits = int(lifetime_points * 0.1)

        # Calculate gaming metrics
        enrollment_date = self.faker.date_between(start_date="-10y", end_date="-30d")
        _days_as_member = (datetime.now().date() - enrollment_date).days
        total_visits = int(self.rng.uniform(1, 500) * (tier_idx + 1) / 3)

        # Theoretical and actual based on tier
        base_theo = [500, 2500, 15000, 75000, 500000]
        total_theo = round(self.rng.uniform(0.5, 2.0) * base_theo[tier_idx], 2)
        # Actual win/loss (house edge means usually negative)
        actual_wl = round(total_theo * self.rng.uniform(-0.15, 0.05), 2)

        # Generate dates
        last_visit = self.faker.date_between(
            start_date=enrollment_date, end_date="today"
        )

        # Build record
        record = {
            "player_id": player_id,
            "loyalty_number": loyalty_number,
            "first_name": first_name if self.include_pii else first_name[0] + "***",
            "last_name": last_name if self.include_pii else last_name[0] + "***",
            "email": (
                self.faker.email()
                if self.include_pii
                else f"{self.hash_value(self.faker.email(), self._salt)[:16]}@masked.com"
            ),
            "phone": (
                self.faker.phone_number()
                if self.include_pii
                else f"***-***-{self.rng.integers(1000, 9999)}"
            ),
            "date_of_birth": self.faker.date_of_birth(
                minimum_age=21, maximum_age=85
            ).isoformat(),
            "ssn_hash": self.hash_value(ssn, self._salt),
            "ssn_masked": self.mask_ssn(ssn),
            "address": (
                self.faker.street_address()
                if self.include_pii
                else "*** Masked Address ***"
            ),
            "city": self.faker.city(),
            "state": self.faker.state_abbr(),
            "zip_code": self.faker.zipcode(),
            "country": "USA",
            "loyalty_tier": tier,
            "points_balance": points_balance,
            "lifetime_points": lifetime_points,
            "tier_credits": tier_credits,
            "enrollment_date": enrollment_date.isoformat(),
            "last_visit_date": last_visit.isoformat(),
            "total_visits": total_visits,
            "total_theo": total_theo,
            "total_actual_win_loss": actual_wl,
            "average_daily_theo": round(total_theo / max(total_visits, 1), 2),
            "preferred_game": self.rng.choice(self.PREFERRED_GAMES),
            "communication_preference": self.rng.choice(
                self.COMMUNICATION_PREFERENCES
            ),
            "marketing_opt_in": bool(self.rng.random() > 0.3),
            "marketing_channel": self.rng.choice(self.MARKETING_CHANNELS),
            "host_assigned": (
                f"HOST-{self.rng.integers(1, 50):03d}"
                if tier in ["Gold", "Platinum", "Diamond"]
                else None
            ),
            "vip_flag": tier in ["Platinum", "Diamond"],
            "self_excluded": bool(self.rng.random() < 0.01),  # 1% self-exclusion rate
            "account_status": self.weighted_choice(
                ["Active", "Inactive", "Suspended", "Closed"],
                [0.85, 0.10, 0.03, 0.02],
            ),
        }

        return self.add_metadata_columns(record)

    def generate_with_history(
        self, num_players: int, history_days: int = 30
    ) -> tuple[Any, Any]:
        """
        Generate players with historical visit data.

        Args:
            num_players: Number of players to generate
            history_days: Days of history to generate

        Returns:
            Tuple of (players_df, visits_df)
        """
        import pandas as pd

        # Generate base players
        players_df = self.generate(num_players)

        # Generate visit history
        visits = []
        for _, player in players_df.iterrows():
            num_visits = min(player["total_visits"], history_days)
            for _ in range(num_visits):
                visit = {
                    "player_id": player["player_id"],
                    "visit_date": self.faker.date_between(
                        start_date=f"-{history_days}d", end_date="today"
                    ).isoformat(),
                    "visit_duration_minutes": self.rng.integers(30, 480),
                    "games_played": self.rng.integers(1, 10),
                    "theo_for_visit": round(
                        player["average_daily_theo"] * self.rng.uniform(0.5, 2.0),
                        2,
                    ),
                }
                visits.append(visit)

        visits_df = pd.DataFrame(visits)
        return players_df, visits_df
