"""
Energy Meter Reading Generator
===============================

Generates realistic AMI (Advanced Metering Infrastructure) data for a
regional electric utility with 1.2M meters:

- 15-minute interval meter readings with daily load curves
- Meter asset records with rate class and location
- Outage events with IEEE 1366 cause codes

Seasonal and time-of-day patterns model realistic residential/commercial
consumption profiles including morning and evening peaks.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any

from data_generation.generators.base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RATE_CLASSES = ["RESIDENTIAL", "SMALL_COMMERCIAL", "LARGE_COMMERCIAL", "INDUSTRIAL"]
RATE_WEIGHTS = [0.72, 0.18, 0.07, 0.03]

CAUSE_CODES = [
    ("WEATHER_WIND", "High wind / storm damage"),
    ("WEATHER_LIGHTNING", "Lightning strike"),
    ("WEATHER_ICE", "Ice accumulation"),
    ("EQUIPMENT_TRANSFORMER", "Transformer failure"),
    ("EQUIPMENT_FUSE", "Fuse failure"),
    ("EQUIPMENT_CABLE", "Underground cable fault"),
    ("VEGETATION", "Tree / vegetation contact"),
    ("ANIMAL", "Animal contact"),
    ("VEHICLE", "Vehicle accident"),
    ("PLANNED", "Planned maintenance"),
    ("UNKNOWN", "Unknown / under investigation"),
]

DISTRICTS = ["NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"]

FEEDER_PREFIXES = ["FDR", "CKT"]


class MeterReadingGenerator(BaseGenerator):
    """Generate AMI meter readings, meter assets, and outage events."""

    def __init__(
        self,
        seed: int | None = None,
        num_meters: int = 5000,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)
        self.num_meters = num_meters
        self._meters = self._build_meter_fleet()
        self._schema = {
            "meter_id": "STRING",
            "reading_timestamp": "TIMESTAMP",
            "kwh_delivered": "DOUBLE",
            "kwh_received": "DOUBLE",
            "voltage_a": "DOUBLE",
            "power_factor": "DOUBLE",
            "demand_kw": "DOUBLE",
            "tamper_flag": "BOOLEAN",
            "read_quality": "STRING",
        }

    # ------------------------------------------------------------------
    # Meter fleet
    # ------------------------------------------------------------------

    def _build_meter_fleet(self) -> list[dict[str, Any]]:
        """Pre-generate a fleet of meter assets."""
        meters: list[dict[str, Any]] = []
        for i in range(self.num_meters):
            rate_class = str(self.rng.choice(RATE_CLASSES, p=RATE_WEIGHTS))
            district = str(self.rng.choice(DISTRICTS))
            feeder_prefix = str(self.rng.choice(FEEDER_PREFIXES))
            meters.append(
                {
                    "meter_id": f"MTR-{i:08d}",
                    "account_id": f"ACCT-{i:010d}",
                    "premise_id": f"PRM-{i:08d}",
                    "rate_class": rate_class,
                    "district": district,
                    "feeder_id": f"{feeder_prefix}-{district[:1]}{int(self.rng.integers(100, 999))}",
                    "lat": round(float(self.rng.uniform(33.0, 35.5)), 6),
                    "lon": round(float(self.rng.uniform(-118.5, -116.0)), 6),
                    "has_solar": bool(self.rng.random() < 0.12),
                    "base_load_kw": self._base_load(rate_class),
                }
            )
        return meters

    def _base_load(self, rate_class: str) -> float:
        """Return a typical base load (kW) for a rate class."""
        means = {
            "RESIDENTIAL": 1.2,
            "SMALL_COMMERCIAL": 5.0,
            "LARGE_COMMERCIAL": 45.0,
            "INDUSTRIAL": 250.0,
        }
        mean = means.get(rate_class, 1.2)
        return max(0.1, float(self.rng.normal(mean, mean * 0.25)))

    # ------------------------------------------------------------------
    # Load curve
    # ------------------------------------------------------------------

    @staticmethod
    def _load_curve_factor(hour: float, month: int) -> float:
        """Return a multiplier (0-1 scale) for the given hour and month.

        Models:
        - Morning ramp 6-9 AM
        - Midday dip (residential) / plateau (commercial)
        - Evening peak 17-21
        - Seasonal: summer AC peak, winter heating bump
        """
        # Base diurnal curve (two-hump residential)
        morning = 0.6 * math.exp(-((hour - 7.5) ** 2) / 4.0)
        evening = 1.0 * math.exp(-((hour - 19.0) ** 2) / 5.0)
        base = 0.25 + morning + evening  # overnight ~0.25

        # Seasonal adjustment
        if month in (6, 7, 8):  # summer
            base *= 1.35  # AC load
        elif month in (12, 1, 2):  # winter
            base *= 1.15  # heating
        else:
            base *= 1.0

        return min(base, 2.0)

    # ------------------------------------------------------------------
    # Record generation
    # ------------------------------------------------------------------

    def generate_record(self) -> dict[str, Any]:
        """Generate a single 15-minute meter reading."""
        meter = self._meters[int(self.rng.integers(0, self.num_meters))]
        ts = self._random_interval_timestamp()
        hour = ts.hour + ts.minute / 60.0
        month = ts.month

        factor = self._load_curve_factor(hour, month)
        noise = float(self.rng.normal(1.0, 0.08))
        demand_kw = max(0.0, meter["base_load_kw"] * factor * noise)
        kwh = demand_kw * 0.25  # 15-min interval

        # Solar generation (net metering)
        kwh_received = 0.0
        if meter["has_solar"] and 8 <= hour <= 18:
            solar_factor = math.sin(math.pi * (hour - 6) / 12) * 0.8
            solar_kw = float(self.rng.uniform(2.0, 8.0)) * solar_factor
            kwh_received = max(0.0, (solar_kw - demand_kw) * 0.25)
            kwh = max(0.0, kwh - solar_kw * 0.25)

        # Voltage (120V nominal, ANSI C84.1)
        voltage = float(self.rng.normal(120.0, 2.5))

        # Power factor
        pf = min(1.0, max(0.7, float(self.rng.normal(0.95, 0.04))))

        # Tamper (rare)
        tamper = bool(self.rng.random() < 0.001)

        # Quality
        quality = "ACTUAL"
        if self.rng.random() < 0.005:
            quality = str(self.rng.choice(["ESTIMATED", "MISSING"]))

        record = {
            "meter_id": meter["meter_id"],
            "reading_timestamp": ts.isoformat(),
            "kwh_delivered": round(kwh, 4),
            "kwh_received": round(kwh_received, 4),
            "voltage_a": round(voltage, 2),
            "power_factor": round(pf, 4),
            "demand_kw": round(demand_kw, 4),
            "tamper_flag": tamper,
            "read_quality": quality,
            "rate_class": meter["rate_class"],
            "district": meter["district"],
            "feeder_id": meter["feeder_id"],
            "lat": meter["lat"],
            "lon": meter["lon"],
        }
        return self.add_metadata_columns(record)

    def generate_meter_assets(self) -> list[dict[str, Any]]:
        """Return the full meter fleet as a list of dicts."""
        return [
            {
                "meter_id": m["meter_id"],
                "account_id": m["account_id"],
                "premise_id": m["premise_id"],
                "rate_class": m["rate_class"],
                "district": m["district"],
                "feeder_id": m["feeder_id"],
                "lat": m["lat"],
                "lon": m["lon"],
                "has_solar": m["has_solar"],
            }
            for m in self._meters
        ]

    def generate_outage_event(self) -> dict[str, Any]:
        """Generate a single outage event."""
        cause_idx = int(self.rng.integers(0, len(CAUSE_CODES)))
        cause_code, cause_desc = CAUSE_CODES[cause_idx]
        district = str(self.rng.choice(DISTRICTS))
        prefix = str(self.rng.choice(FEEDER_PREFIXES))

        start_dt = self.random_datetime()
        duration_min = float(self.rng.exponential(90.0))  # mean 90 min
        duration_min = min(max(duration_min, 1.0), 4320.0)  # 1 min to 3 days
        restore_dt = start_dt + timedelta(minutes=duration_min)

        customers = int(self.rng.integers(1, 8000))
        weather_related = cause_code.startswith("WEATHER")

        return {
            "event_id": self.generate_uuid(),
            "feeder_id": f"{prefix}-{district[:1]}{int(self.rng.integers(100, 999))}",
            "substation_id": f"SUB-{district[:1]}{int(self.rng.integers(10, 99))}",
            "district": district,
            "start_datetime": start_dt.isoformat(),
            "restore_datetime": restore_dt.isoformat(),
            "duration_minutes": round(duration_min, 1),
            "cause_code": cause_code,
            "cause_description": cause_desc,
            "customers_affected": customers,
            "equipment_failed": cause_desc.split()[0]
            if "EQUIPMENT" in cause_code
            else None,
            "weather_related": weather_related,
            "major_event": customers > 5000 or duration_min > 1440,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _random_interval_timestamp(self) -> datetime:
        """Generate a random timestamp aligned to 15-min intervals."""
        dt = self.random_datetime()
        # Align to 15-min boundary
        minute = (dt.minute // 15) * 15
        return dt.replace(minute=minute, second=0, microsecond=0)
