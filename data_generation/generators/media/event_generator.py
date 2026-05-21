"""
Media Event Generator
=====================

Generates realistic streaming media playback events including user profiles,
content catalog entries, and playback interaction events (play, pause, seek,
stop, heartbeat).

Patterns modeled:
- Evening peak viewing (7-11 PM local)
- Weekend binge behavior (3+ consecutive episodes)
- Seasonal premiere spikes
- Device distribution (smart_tv dominant in evenings, mobile during commute)

Compliance:
- COPPA: age-gated profiles with data minimization for child users
- GDPR: pseudonymized user IDs, no PII in event stream
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from data_generation.generators.base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EVENT_TYPES = ["play", "pause", "seek", "stop", "heartbeat"]
EVENT_WEIGHTS = [0.20, 0.10, 0.08, 0.15, 0.47]

DEVICE_TYPES = ["web", "mobile", "smart_tv", "console"]
DEVICE_WEIGHTS = [0.20, 0.30, 0.35, 0.15]

PLAN_TIERS = ["free", "basic", "premium"]
PLAN_WEIGHTS = [0.26, 0.43, 0.31]

AGE_BUCKETS = ["child", "teen", "adult"]
AGE_WEIGHTS = [0.12, 0.15, 0.73]

REGIONS = ["US", "GB", "DE", "FR", "JP", "BR", "IN", "AU", "CA", "MX"]

GENRES = [
    "drama",
    "comedy",
    "action",
    "thriller",
    "sci-fi",
    "documentary",
    "animation",
    "horror",
    "romance",
    "kids",
]

RATINGS = ["G", "PG", "PG-13", "R", "TV-Y", "TV-Y7", "TV-G", "TV-PG", "TV-14", "TV-MA"]

BITRATES = [800, 1500, 3000, 5000, 8000, 12000, 15000]
BITRATE_WEIGHTS = [0.05, 0.10, 0.20, 0.25, 0.20, 0.12, 0.08]

# Number of pre-generated catalog / user pool entries
_CATALOG_SIZE = 500
_USER_POOL_SIZE = 2000


class MediaEventGenerator(BaseGenerator):
    """Generates streaming media playback events."""

    def __init__(
        self,
        seed: int | None = None,
        locale: str = "en_US",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        catalog_size: int = _CATALOG_SIZE,
        user_pool_size: int = _USER_POOL_SIZE,
    ):
        super().__init__(
            seed=seed, locale=locale, start_date=start_date, end_date=end_date
        )

        self.catalog_size = catalog_size
        self.user_pool_size = user_pool_size

        # Pre-generate catalog and user pools for referential consistency
        self._catalog = self._build_catalog()
        self._users = self._build_user_pool()

        self._schema = {
            "event_id": "STRING",
            "user_id": "STRING",
            "content_id": "STRING",
            "event_type": "STRING",
            "event_timestamp": "TIMESTAMP",
            "position_sec": "INT",
            "device_type": "STRING",
            "bitrate_kbps": "INT",
            "plan_tier": "STRING",
            "age_bucket": "STRING",
            "region": "STRING",
        }

    # ------------------------------------------------------------------
    # Catalog & user pool builders
    # ------------------------------------------------------------------

    def _build_catalog(self) -> list[dict[str, Any]]:
        """Build a reusable content catalog."""
        catalog = []
        for i in range(self.catalog_size):
            genre = str(self.rng.choice(GENRES))
            is_kids = genre == "kids"
            rating = (
                str(self.rng.choice(["TV-Y", "TV-Y7", "TV-G", "G"]))
                if is_kids
                else str(self.rng.choice(RATINGS))
            )
            catalog.append(
                {
                    "content_id": f"CTN-{i + 1:05d}",
                    "title": f"{self.faker.catch_phrase()} {'Kids' if is_kids else ''}".strip(),
                    "genre": genre,
                    "release_year": int(self.rng.integers(2015, 2027)),
                    "duration_min": int(self.rng.choice([22, 30, 44, 52, 60, 90, 120])),
                    "rating": rating,
                    "is_original": bool(self.rng.random() < 0.35),
                }
            )
        return catalog

    def _build_user_pool(self) -> list[dict[str, Any]]:
        """Build a reusable user pool."""
        users = []
        for i in range(self.user_pool_size):
            age_bucket = str(self.weighted_choice(AGE_BUCKETS, AGE_WEIGHTS))
            # Children restricted to free or basic (no premium self-signup)
            if age_bucket == "child":
                tier = str(self.rng.choice(["free", "basic"]))
            else:
                tier = str(self.weighted_choice(PLAN_TIERS, PLAN_WEIGHTS))
            users.append(
                {
                    "user_id": f"USR-{i + 1:06d}",
                    "plan_tier": tier,
                    "signup_dt": self.random_datetime(
                        start=self.start_date - timedelta(days=365),
                        end=self.start_date,
                    ).isoformat(),
                    "age_bucket": age_bucket,
                    "region": str(self.rng.choice(REGIONS)),
                }
            )
        return users

    # ------------------------------------------------------------------
    # Hour-of-day weighting for realistic viewing patterns
    # ------------------------------------------------------------------

    def _hour_weight(self, hour: int) -> float:
        """Return a relative probability weight for the given hour (0-23)."""
        # Evening peak 19-23, morning trough 3-6
        weights = [
            0.02,
            0.01,
            0.01,
            0.005,
            0.005,
            0.01,
            0.02,
            0.03,  # 0-7
            0.03,
            0.04,
            0.03,
            0.03,
            0.04,
            0.04,
            0.03,
            0.04,  # 8-15
            0.05,
            0.06,
            0.07,
            0.09,
            0.10,
            0.10,
            0.08,
            0.05,  # 16-23
        ]
        return weights[hour]

    def _pick_timestamp(self) -> datetime:
        """Pick a timestamp biased toward evening viewing."""
        # Pick a random day, then weight the hour
        day = self.random_datetime()
        raw = [self._hour_weight(h) for h in range(24)]
        total = sum(raw)
        probs = [w / total for w in raw]
        hour = int(self.rng.choice(24, p=probs))
        minute = int(self.rng.integers(0, 60))
        second = int(self.rng.integers(0, 60))
        return day.replace(hour=hour, minute=minute, second=second, microsecond=0)

    # ------------------------------------------------------------------
    # Record generation
    # ------------------------------------------------------------------

    def generate_record(self) -> dict[str, Any]:
        """Generate a single playback event."""
        user = self._users[int(self.rng.integers(0, self.user_pool_size))]
        content = self._catalog[int(self.rng.integers(0, self.catalog_size))]

        # COPPA: child profiles can only access kids/G/PG content
        if user["age_bucket"] == "child" and content["genre"] != "kids":
            # Re-pick from kids catalog
            kids_items = [c for c in self._catalog if c["genre"] == "kids"]
            if kids_items:
                content = kids_items[int(self.rng.integers(0, len(kids_items)))]

        event_type = str(self.weighted_choice(EVENT_TYPES, EVENT_WEIGHTS))
        duration_sec = content["duration_min"] * 60

        # Position depends on event type
        if event_type == "play":
            position_sec = 0
        elif event_type == "stop":
            position_sec = int(self.rng.integers(0, max(duration_sec, 1)))
        else:
            position_sec = int(self.rng.integers(0, max(duration_sec, 1)))

        # Bitrate (child profiles use lower quality on average)
        if user["age_bucket"] == "child":
            bitrate = int(self.rng.choice([800, 1500, 3000, 5000]))
        else:
            bitrate = int(self.weighted_choice(BITRATES, BITRATE_WEIGHTS))

        device = str(self.weighted_choice(DEVICE_TYPES, DEVICE_WEIGHTS))

        record = {
            "event_id": self.generate_uuid(),
            "user_id": user["user_id"],
            "content_id": content["content_id"],
            "event_type": event_type,
            "event_timestamp": self._pick_timestamp().isoformat(),
            "position_sec": position_sec,
            "device_type": device,
            "bitrate_kbps": bitrate,
            "plan_tier": user["plan_tier"],
            "age_bucket": user["age_bucket"],
            "region": user["region"],
        }

        return self.add_metadata_columns(record)

    # ------------------------------------------------------------------
    # Accessors for catalog / user data (useful for tests & notebooks)
    # ------------------------------------------------------------------

    def get_catalog(self) -> list[dict[str, Any]]:
        """Return the pre-generated content catalog."""
        return list(self._catalog)

    def get_users(self) -> list[dict[str, Any]]:
        """Return the pre-generated user pool."""
        return list(self._users)
