"""
NOAA Generator
==============

Generates synthetic NOAA (National Oceanic and Atmospheric Administration)
observational data for two domains:

- weather: Surface station observations (ASOS/AWOS/METAR/SYNOP/COOP)
- storm: Storm Events Database records

Data mirrors the NOAA Climate Data Online (CDO) and Storm Events APIs.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    import pandas as pd

from ..base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

# Real US ASOS/AWOS weather stations: ICAO → (name, lat, lon, elevation_m)
STATIONS: dict[str, dict[str, Any]] = {
    "KJFK": {
        "name": "John F. Kennedy International Airport",
        "lat": 40.6413,
        "lon": -73.7781,
        "elevation_m": 4,
    },
    "KLAX": {
        "name": "Los Angeles International Airport",
        "lat": 33.9425,
        "lon": -118.4081,
        "elevation_m": 38,
    },
    "KORD": {
        "name": "Chicago O'Hare International Airport",
        "lat": 41.9742,
        "lon": -87.9073,
        "elevation_m": 202,
    },
    "KATL": {
        "name": "Hartsfield-Jackson Atlanta International Airport",
        "lat": 33.6407,
        "lon": -84.4277,
        "elevation_m": 313,
    },
    "KDFW": {
        "name": "Dallas/Fort Worth International Airport",
        "lat": 32.8998,
        "lon": -97.0403,
        "elevation_m": 182,
    },
    "KDEN": {
        "name": "Denver International Airport",
        "lat": 39.8561,
        "lon": -104.6737,
        "elevation_m": 1655,
    },
    "KPHX": {
        "name": "Phoenix Sky Harbor International Airport",
        "lat": 33.4373,
        "lon": -112.0078,
        "elevation_m": 338,
    },
    "KSEA": {
        "name": "Seattle-Tacoma International Airport",
        "lat": 47.4502,
        "lon": -122.3088,
        "elevation_m": 131,
    },
    "KMIA": {
        "name": "Miami International Airport",
        "lat": 25.7959,
        "lon": -80.2870,
        "elevation_m": 8,
    },
    "KBOS": {
        "name": "Boston Logan International Airport",
        "lat": 42.3656,
        "lon": -71.0096,
        "elevation_m": 9,
    },
    "KLAS": {
        "name": "Harry Reid International Airport",
        "lat": 36.0840,
        "lon": -115.1537,
        "elevation_m": 664,
    },
    "KMSP": {
        "name": "Minneapolis-Saint Paul International Airport",
        "lat": 44.8848,
        "lon": -93.2223,
        "elevation_m": 255,
    },
    "KIAH": {
        "name": "George Bush Intercontinental Airport",
        "lat": 29.9902,
        "lon": -95.3368,
        "elevation_m": 30,
    },
    "KSLC": {
        "name": "Salt Lake City International Airport",
        "lat": 40.7884,
        "lon": -111.9778,
        "elevation_m": 1288,
    },
    "KPIT": {
        "name": "Pittsburgh International Airport",
        "lat": 40.4915,
        "lon": -80.2329,
        "elevation_m": 367,
    },
    "KDTW": {
        "name": "Detroit Metropolitan Wayne County Airport",
        "lat": 42.2124,
        "lon": -83.3534,
        "elevation_m": 195,
    },
    "KSTL": {
        "name": "St. Louis Lambert International Airport",
        "lat": 38.7487,
        "lon": -90.3700,
        "elevation_m": 172,
    },
    "KMCO": {
        "name": "Orlando International Airport",
        "lat": 28.4294,
        "lon": -81.3089,
        "elevation_m": 29,
    },
}

STATION_CODES: list[str] = list(STATIONS.keys())

# State FIPS codes (weighted toward storm-prone states)
STATE_FIPS: dict[str, str] = {
    "TX": "48",
    "OK": "40",
    "KS": "20",
    "FL": "12",
    "AL": "01",
    "MS": "28",
    "LA": "22",
    "GA": "13",
    "AR": "05",
    "MO": "29",
    "TN": "47",
    "NC": "37",
    "SC": "45",
    "NE": "31",
    "IA": "19",
    "IL": "17",
    "IN": "18",
    "OH": "39",
    "MN": "27",
    "CO": "08",
}

# Storm-prone states get higher probability
_STORM_STATES = list(STATE_FIPS.keys())
_STORM_WEIGHTS_RAW = [
    10,
    9,
    8,
    7,
    6,
    6,
    6,
    5,  # TX, OK, KS, FL, AL, MS, LA, GA
    4,
    4,
    4,
    3,
    3,
    3,
    3,  # AR, MO, TN, NC, SC, NE, IA
    3,
    3,
    3,
    2,
    2,  # IL, IN, OH, MN, CO
]
_STORM_WEIGHTS_TOTAL = sum(_STORM_WEIGHTS_RAW)
STORM_STATE_WEIGHTS: list[float] = [
    w / _STORM_WEIGHTS_TOTAL for w in _STORM_WEIGHTS_RAW
]

# Weather observation parameters and their realistic value ranges / units
PARAMETER_CONFIG: dict[str, dict[str, Any]] = {
    "TEMPERATURE": {
        "unit": "F",
        "range": (-30.0, 120.0),
        "distribution": "normal",
        "mean": 55.0,
        "std": 25.0,
    },
    "DEWPOINT": {
        "unit": "F",
        "range": (-40.0, 80.0),
        "distribution": "normal",
        "mean": 40.0,
        "std": 20.0,
    },
    "HUMIDITY": {
        "unit": "PCT",
        "range": (0.0, 100.0),
        "distribution": "uniform",
    },
    "WIND_SPEED": {
        "unit": "MPH",
        "range": (0.0, 100.0),
        "distribution": "gamma",
        "shape": 1.5,
        "scale": 8.0,
    },
    "WIND_DIRECTION": {
        "unit": "DEG",
        "range": (0.0, 359.0),
        "distribution": "uniform",
    },
    "PRESSURE": {
        "unit": "IN_HG",
        "range": (28.0, 31.0),
        "distribution": "normal",
        "mean": 29.92,
        "std": 0.3,
    },
    "VISIBILITY": {
        "unit": "MI",
        "range": (0.0, 10.0),
        "distribution": "normal",
        "mean": 8.0,
        "std": 2.5,
    },
    "PRECIPITATION": {
        "unit": "IN",
        "range": (0.0, 5.0),
        "distribution": "exponential",
        "scale": 0.1,
    },
    "CLOUD_COVER": {
        "unit": "PCT",
        "range": (0.0, 100.0),
        "distribution": "uniform",
    },
}

PARAMETERS: list[str] = list(PARAMETER_CONFIG.keys())

QUALITY_FLAGS = ["PASS", "SUSPECT", "ERRONEOUS", "MISSING"]
QUALITY_WEIGHTS = [0.95, 0.03, 0.01, 0.01]

DATA_SOURCES = ["ASOS", "AWOS", "METAR", "SYNOP", "COOP"]

# Storm event types with realistic weights
EVENT_TYPES = [
    "THUNDERSTORM_WIND",
    "HAIL",
    "FLASH_FLOOD",
    "TORNADO",
    "FLOOD",
    "WINTER_STORM",
    "BLIZZARD",
    "ICE_STORM",
    "HURRICANE",
    "TROPICAL_STORM",
    "WILDFIRE",
    "DROUGHT",
    "EXTREME_COLD",
    "EXTREME_HEAT",
]
EVENT_WEIGHTS_RAW = [30, 25, 15, 10, 4, 3, 2, 2, 1, 1, 2, 2, 2, 1]
_EVENT_TOTAL = sum(EVENT_WEIGHTS_RAW)
EVENT_WEIGHTS: list[float] = [w / _EVENT_TOTAL for w in EVENT_WEIGHTS_RAW]

STORM_SOURCES = ["TRAINED SPOTTER", "LAW ENFORCEMENT", "NWS EMPLOYEE", "PUBLIC"]

FLOOD_CAUSES = ["HEAVY RAIN", "DAM BREAK", "ICE JAM"]

# EF scale weights for tornadoes
TOR_F_SCALES = ["EF0", "EF1", "EF2", "EF3", "EF4", "EF5"]
TOR_F_WEIGHTS = [0.50, 0.25, 0.15, 0.07, 0.025, 0.005]


class NOAAGenerator(BaseGenerator):
    """
    Generator for NOAA observational datasets.

    Supports two domains:
    - ``weather``: Surface station observations aligned with NOAA CDO GHCND/LCD.
    - ``storm``: Storm Events Database records (injuries, damage, etc.).

    Usage::

        gen = NOAAGenerator(seed=42)

        # Generate weather observations
        weather_df = gen.generate(1000)                        # default domain
        weather_df = gen.generate(1000, domain="weather")

        # Generate storm events
        storm_df = gen.generate(500, domain="storm")

        # Single record
        record = gen.generate_record("weather")
        storm_record = gen.generate_record("storm")
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._schema = {
            "weather": {
                "observation_id": "string",
                "station_id": "string",
                "station_name": "string",
                "timestamp": "datetime",
                "latitude": "float",
                "longitude": "float",
                "elevation_m": "float",
                "parameter": "string",
                "value": "float",
                "unit": "string",
                "quality_flag": "string",
                "data_source": "string",
                "report_type": "string",
                "load_time": "datetime",
            },
            "storm": {
                "event_id": "string",
                "episode_id": "string",
                "event_type": "string",
                "state": "string",
                "state_fips": "string",
                "county_fips": "string",
                "begin_date": "datetime",
                "end_date": "datetime",
                "injuries_direct": "int",
                "injuries_indirect": "int",
                "deaths_direct": "int",
                "deaths_indirect": "int",
                "damage_property": "float",
                "damage_crops": "float",
                "magnitude": "float",
                "magnitude_type": "string",
                "begin_lat": "float",
                "begin_lon": "float",
                "end_lat": "float",
                "end_lon": "float",
                "tor_f_scale": "string",
                "source": "string",
                "flood_cause": "string",
                "load_time": "datetime",
            },
        }

    # ------------------------------------------------------------------
    # Override generate() to accept domain kwarg
    # ------------------------------------------------------------------

    def generate(  # type: ignore[override]
        self,
        num_records: int,
        show_progress: bool = True,
        domain: str = "weather",
    ) -> pd.DataFrame:
        """
        Generate multiple records for the specified domain.

        Args:
            num_records: Number of records to generate.
            show_progress: Show progress bar.
            domain: ``"weather"`` (default) or ``"storm"``.

        Returns:
            DataFrame containing generated records.
        """
        import pandas as pd
        from tqdm import tqdm

        records = []
        iterator = range(num_records)

        if show_progress:
            iterator = tqdm(iterator, desc=f"Generating NOAA {domain}")

        for _ in iterator:
            records.append(self.generate_record(domain=domain))

        return pd.DataFrame(records)

    # ------------------------------------------------------------------
    # Core record generators
    # ------------------------------------------------------------------

    def generate_record(self, domain: str = "weather") -> dict[str, Any]:  # type: ignore[override]
        """
        Generate a single NOAA record.

        Args:
            domain: ``"weather"`` or ``"storm"``.

        Returns:
            Dictionary with all domain-specific fields plus metadata columns.
        """
        if domain == "storm":
            record = self._generate_storm_record()
        else:
            record = self._generate_weather_record()

        return self.add_metadata_columns(record)

    # ------------------------------------------------------------------
    # Weather observation record
    # ------------------------------------------------------------------

    def _generate_weather_record(self) -> dict[str, Any]:
        """Generate a single surface weather observation record."""
        station_code: str = str(np.random.choice(STATION_CODES))
        station: dict[str, Any] = STATIONS[station_code]

        timestamp: datetime = self.random_datetime()
        parameter: str = str(np.random.choice(PARAMETERS))
        value: float = self._sample_parameter_value(parameter)
        unit: str = PARAMETER_CONFIG[parameter]["unit"]
        quality_flag: str = str(self.weighted_choice(QUALITY_FLAGS, QUALITY_WEIGHTS))
        data_source: str = str(np.random.choice(DATA_SOURCES))

        return {
            "observation_id": self.generate_uuid(),
            "station_id": station_code,
            "station_name": station["name"],
            "timestamp": timestamp.isoformat(),
            "latitude": station["lat"],
            "longitude": station["lon"],
            "elevation_m": float(station["elevation_m"]),
            "parameter": parameter,
            "value": round(value, 2),
            "unit": unit,
            "quality_flag": quality_flag,
            "data_source": data_source,
            "report_type": None,
            "load_time": datetime.now().isoformat(),
        }

    def _sample_parameter_value(self, parameter: str) -> float:
        """Sample a realistic value for the given weather parameter."""
        cfg = PARAMETER_CONFIG[parameter]
        lo, hi = cfg["range"]
        dist = cfg["distribution"]

        if dist == "normal":
            val = np.random.normal(cfg["mean"], cfg["std"])
        elif dist == "gamma":
            val = np.random.gamma(cfg["shape"], cfg["scale"])
        elif dist == "exponential":
            val = np.random.exponential(cfg["scale"])
        else:  # uniform
            val = np.random.uniform(lo, hi)

        return float(np.clip(val, lo, hi))

    # ------------------------------------------------------------------
    # Storm event record
    # ------------------------------------------------------------------

    def _generate_storm_record(self) -> dict[str, Any]:
        """Generate a single NOAA Storm Events Database record."""
        event_id: str = self.generate_uuid()

        # episode_id: present ~70% of the time
        episode_id: str | None = (
            f"EP-{self.generate_uuid()[:8]}" if np.random.random() < 0.70 else None
        )

        event_type: str = str(self.weighted_choice(EVENT_TYPES, EVENT_WEIGHTS))

        state: str = str(self.weighted_choice(_STORM_STATES, STORM_STATE_WEIGHTS))
        state_fips: str = STATE_FIPS[state]

        # county FIPS: 3-digit suffix, ~80% present
        county_fips: str | None = (
            f"{state_fips}{np.random.randint(1, 200):03d}"
            if np.random.random() < 0.80
            else None
        )

        begin_date: datetime = self.random_datetime()
        duration_hours: float = float(np.random.exponential(scale=6.0))
        duration_hours = max(0.5, min(duration_hours, 168.0))  # 30 min – 7 days
        end_date: datetime = begin_date + timedelta(hours=duration_hours)

        # Casualty figures: mostly zero, occasionally non-zero
        injuries_direct: int = self._sample_casualties(p_nonzero=0.05, max_val=50)
        injuries_indirect: int = self._sample_casualties(p_nonzero=0.03, max_val=20)
        deaths_direct: int = self._sample_casualties(p_nonzero=0.02, max_val=10)
        deaths_indirect: int = self._sample_casualties(p_nonzero=0.01, max_val=5)

        # Property and crop damage: log-normal, floored at 0
        damage_property: float = self._sample_damage(max_val=10_000_000.0)
        damage_crops: float = self._sample_damage(max_val=5_000_000.0)

        # Magnitude fields
        magnitude, magnitude_type = self._sample_magnitude(event_type)

        # Geographic coordinates — roughly within continental US
        begin_lat: float = round(float(np.random.uniform(25.0, 49.0)), 4)
        begin_lon: float = round(float(np.random.uniform(-125.0, -67.0)), 4)
        end_lat: float = round(begin_lat + float(np.random.normal(0, 0.5)), 4)
        end_lon: float = round(begin_lon + float(np.random.normal(0, 0.5)), 4)

        # Tornado F/EF scale
        tor_f_scale: str | None = None
        if event_type == "TORNADO":
            tor_f_scale = str(self.weighted_choice(TOR_F_SCALES, TOR_F_WEIGHTS))

        # Flood cause
        flood_cause: str | None = None
        if event_type in ("FLASH_FLOOD", "FLOOD"):
            flood_cause = str(np.random.choice(FLOOD_CAUSES))

        source: str = str(np.random.choice(STORM_SOURCES))

        return {
            "event_id": event_id,
            "episode_id": episode_id,
            "event_type": event_type,
            "state": state,
            "state_fips": state_fips,
            "county_fips": county_fips,
            "begin_date": begin_date.isoformat(),
            "end_date": end_date.isoformat(),
            "injuries_direct": injuries_direct,
            "injuries_indirect": injuries_indirect,
            "deaths_direct": deaths_direct,
            "deaths_indirect": deaths_indirect,
            "damage_property": round(damage_property, 2),
            "damage_crops": round(damage_crops, 2),
            "magnitude": magnitude,
            "magnitude_type": magnitude_type,
            "begin_lat": begin_lat,
            "begin_lon": begin_lon,
            "end_lat": end_lat,
            "end_lon": end_lon,
            "tor_f_scale": tor_f_scale,
            "source": source,
            "flood_cause": flood_cause,
            "load_time": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # Storm helper methods
    # ------------------------------------------------------------------

    def _sample_casualties(self, p_nonzero: float, max_val: int) -> int:
        """Return 0 with probability (1 - p_nonzero), else a small integer."""
        if np.random.random() > p_nonzero:
            return 0
        return int(np.clip(np.random.exponential(scale=2.0), 1, max_val))

    def _sample_damage(self, max_val: float) -> float:
        """Return a log-normal damage value between 0 and max_val."""
        if np.random.random() < 0.30:
            return 0.0
        raw = np.random.lognormal(mean=7.0, sigma=2.5)
        return float(np.clip(raw, 0.0, max_val))

    def _sample_magnitude(self, event_type: str) -> tuple[float | None, str | None]:
        """Return (magnitude, magnitude_type) appropriate to the event type."""
        if event_type == "TORNADO":
            # Wind speed in mph for tornado vortex
            mag = float(np.clip(np.random.uniform(65.0, 300.0), 65.0, 300.0))
            return round(mag, 1), "MPH"
        if event_type == "HAIL":
            # Hail diameter in inches
            mag = float(np.clip(np.random.exponential(scale=0.75) + 0.5, 0.5, 5.0))
            return round(mag, 2), "INCHES"
        if event_type == "THUNDERSTORM_WIND":
            mag = float(np.clip(np.random.normal(55.0, 15.0), 25.0, 120.0))
            return round(mag, 1), "MPH"
        if event_type in ("HURRICANE", "TROPICAL_STORM"):
            mag = float(np.clip(np.random.normal(90.0, 30.0), 39.0, 185.0))
            return round(mag, 1), "MPH"
        # All other event types: no magnitude
        return None, None
