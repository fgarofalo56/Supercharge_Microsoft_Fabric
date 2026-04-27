"""
Telecom CDR Generator
=====================

Generates realistic Call Detail Records (CDRs), subscriber profiles,
and cell site reference data for a regional wireless carrier.

- 3.5M subscriber base, 8,000 cell sites
- Plan mix: postpaid (60%), prepaid (25%), MVNO (15%)
- ~3% monthly churn rate
- Peak usage patterns: data-heavy evenings, voice peaks mid-morning
- RAT types: 4G LTE (70%), 5G NR (30%)
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from data_generation.generators.base_generator import BaseGenerator


class TelecomCDRGenerator(BaseGenerator):
    """Generate CDR records, subscriber profiles, and cell site data."""

    # -------------------------------------------------------------------
    # Constants
    # -------------------------------------------------------------------
    CALL_TYPES = ["voice", "sms", "data"]
    CALL_TYPE_WEIGHTS = [0.25, 0.15, 0.60]

    PLAN_TYPES = ["postpaid", "prepaid", "mvno"]
    PLAN_WEIGHTS = [0.60, 0.25, 0.15]

    RAT_TYPES = ["4G", "5G"]
    RAT_WEIGHTS = [0.70, 0.30]

    TECHNOLOGIES = ["LTE", "NR", "LTE-A"]
    TECH_WEIGHTS = [0.55, 0.30, 0.15]

    NUM_CELL_SITES = 8_000
    NUM_SUBSCRIBERS = 100  # default pool size for generation (scaled down)
    CHURN_RATE = 0.03

    # Monthly charge ranges by plan type
    PLAN_CHARGES = {
        "postpaid": (55.0, 120.0),
        "prepaid": (20.0, 50.0),
        "mvno": (25.0, 60.0),
    }

    def __init__(
        self,
        seed: int | None = None,
        num_subscribers: int = 100,
        num_cell_sites: int = 500,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)
        self.num_subscribers = num_subscribers
        self.num_cell_sites = min(num_cell_sites, self.NUM_CELL_SITES)

        # Pre-generate reference data
        self._subscribers = self._generate_subscribers()
        self._cell_sites = self._generate_cell_sites()

        self._schema = {
            "cdr_id": "string",
            "subscriber_id": "string",
            "call_type": "string",
            "start_dt": "datetime",
            "duration_sec": "int",
            "bytes_up": "bigint",
            "bytes_down": "bigint",
            "cell_id": "string",
            "sector": "string",
            "rat_type": "string",
            "rated_amount": "float",
            "_ingested_at": "string",
            "_source": "string",
            "_batch_id": "string",
        }

    # -------------------------------------------------------------------
    # Reference data generators
    # -------------------------------------------------------------------

    def _generate_subscribers(self) -> list[dict[str, Any]]:
        """Generate a pool of subscriber profiles."""
        subscribers = []
        for i in range(self.num_subscribers):
            plan = self.weighted_choice(self.PLAN_TYPES, self.PLAN_WEIGHTS)
            charge_min, charge_max = self.PLAN_CHARGES[plan]
            tenure = int(self.rng.integers(1, 120))
            churn = bool(self.rng.random() < self.CHURN_RATE)

            subscribers.append({
                "subscriber_id": f"SUB-{i:07d}",
                "plan_type": plan,
                "tenure_months": tenure,
                "monthly_charge": round(
                    float(self.rng.uniform(charge_min, charge_max)), 2
                ),
                "data_usage_gb": round(float(self.rng.uniform(0.5, 80.0)), 2),
                "churn_flag": churn,
                "cpni_consent": bool(self.rng.random() < 0.85),
            })
        return subscribers

    def _generate_cell_sites(self) -> list[dict[str, Any]]:
        """Generate a pool of cell site reference records."""
        sites = []
        for i in range(self.num_cell_sites):
            tech = self.weighted_choice(self.TECHNOLOGIES, self.TECH_WEIGHTS)
            lat = round(float(self.rng.uniform(25.0, 48.0)), 6)
            lon = round(float(self.rng.uniform(-123.0, -71.0)), 6)

            for sector in ["A", "B", "C"]:
                sites.append({
                    "cell_id": f"CELL-{i:05d}",
                    "sector": sector,
                    "latitude": lat,
                    "longitude": lon,
                    "technology": tech,
                    "azimuth": {"A": 0, "B": 120, "C": 240}[sector],
                })
        return sites

    # -------------------------------------------------------------------
    # CDR record generation
    # -------------------------------------------------------------------

    def generate_record(self) -> dict[str, Any]:
        """Generate a single CDR record with realistic usage patterns."""
        cdr_id = self.generate_uuid()
        subscriber = self._subscribers[
            int(self.rng.integers(0, len(self._subscribers)))
        ]
        cell_site = self._cell_sites[
            int(self.rng.integers(0, len(self._cell_sites)))
        ]

        call_type = self.weighted_choice(self.CALL_TYPES, self.CALL_TYPE_WEIGHTS)
        rat_type = self.weighted_choice(self.RAT_TYPES, self.RAT_WEIGHTS)
        start_dt = self.random_datetime()

        # Apply peak-hour weighting: bias toward evening for data
        hour = start_dt.hour
        if call_type == "data" and self.rng.random() < 0.4:
            # Shift toward evening peak (18-23)
            start_dt = start_dt.replace(hour=int(self.rng.integers(18, 24)))

        # Duration and bytes depend on call type
        if call_type == "voice":
            duration_sec = max(1, int(self.rng.exponential(180)))
            bytes_up = int(self.rng.integers(5000, 20000))
            bytes_down = int(self.rng.integers(5000, 20000))
            rated_amount = round(duration_sec * 0.02, 4)
        elif call_type == "sms":
            duration_sec = 0
            bytes_up = int(self.rng.integers(100, 500))
            bytes_down = 0
            rated_amount = 0.10
        else:  # data
            duration_sec = max(1, int(self.rng.exponential(600)))
            bytes_down = int(self.rng.exponential(50_000_000))
            bytes_up = int(bytes_down * self.rng.uniform(0.05, 0.3))
            rated_amount = round(bytes_down / 1_073_741_824 * 10.0, 4)

        record = {
            "cdr_id": cdr_id,
            "subscriber_id": subscriber["subscriber_id"],
            "call_type": call_type,
            "start_dt": start_dt.isoformat(),
            "duration_sec": duration_sec,
            "bytes_up": bytes_up,
            "bytes_down": bytes_down,
            "cell_id": cell_site["cell_id"],
            "sector": cell_site["sector"],
            "rat_type": rat_type,
            "rated_amount": rated_amount,
        }
        return self.add_metadata_columns(record)

    # -------------------------------------------------------------------
    # Accessors for reference data
    # -------------------------------------------------------------------

    @property
    def subscribers(self) -> list[dict[str, Any]]:
        """Return the pre-generated subscriber pool."""
        return self._subscribers

    @property
    def cell_sites(self) -> list[dict[str, Any]]:
        """Return the pre-generated cell site pool."""
        return self._cell_sites

    def get_subscriber_df(self):
        """Return subscribers as a pandas DataFrame."""
        import pandas as pd
        return pd.DataFrame(self._subscribers)

    def get_cell_site_df(self):
        """Return cell sites as a pandas DataFrame."""
        import pandas as pd
        return pd.DataFrame(self._cell_sites)


# -------------------------------------------------------------------
# CLI entry point
# -------------------------------------------------------------------

if __name__ == "__main__":
    generator = TelecomCDRGenerator(seed=42, num_subscribers=1000, num_cell_sites=200)
    df = generator.generate(num_records=5000, show_progress=True)
    print(f"\nGenerated {len(df)} CDR records")
    print(f"Call type distribution:\n{df['call_type'].value_counts()}")
    print(f"\nSubscriber pool: {len(generator.subscribers)} subscribers")
    print(f"Churn rate: {sum(1 for s in generator.subscribers if s['churn_flag'])}/{len(generator.subscribers)}")
    print(f"Cell sites: {len(generator.cell_sites)} sectors across {generator.num_cell_sites} sites")

    # Save sample output
    output_dir = Path("data_generation/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    generator.to_parquet(df, output_dir / "telecom_cdr_sample.parquet")
    print(f"\nSaved to {output_dir / 'telecom_cdr_sample.parquet'}")
