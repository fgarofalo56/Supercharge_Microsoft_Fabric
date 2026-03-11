"""
EPA Generator
=============

Generates synthetic EPA environmental monitoring data for two domains:

- air_quality: AQS (Air Quality System) monitoring site measurements
- water_quality: SDWIS (Safe Drinking Water Information System) sample results

Data mirrors real EPA public datasets documented in federal_datasets.yaml.
"""

from datetime import datetime
from typing import Any, Optional

import numpy as np

from ..base_generator import BaseGenerator


# ---------------------------------------------------------------------------
# Reference tables
# ---------------------------------------------------------------------------

# Air quality: parameter → (code, primary_unit, realistic_range, sample_durations)
PARAMETER_MAP: dict[str, dict[str, Any]] = {
    "PM2.5": {
        "code": "88101",
        "unit": "UG/M3",
        "range": (0.0, 500.0),
        "durations": ["24 HOUR", "1 HOUR"],
        "duration_weights": [0.7, 0.3],
    },
    "PM10": {
        "code": "81102",
        "unit": "UG/M3",
        "range": (0.0, 700.0),
        "durations": ["24 HOUR", "1 HOUR"],
        "duration_weights": [0.6, 0.4],
    },
    "OZONE": {
        "code": "44201",
        "unit": "PPB",
        "range": (0.0, 200.0),
        "durations": ["1 HOUR", "8 HOUR"],
        "duration_weights": [0.5, 0.5],
    },
    "CO": {
        "code": "42101",
        "unit": "PPM",
        "range": (0.0, 50.0),
        "durations": ["1 HOUR", "8 HOUR"],
        "duration_weights": [0.6, 0.4],
    },
    "SO2": {
        "code": "42401",
        "unit": "PPB",
        "range": (0.0, 500.0),
        "durations": ["1 HOUR", "24 HOUR"],
        "duration_weights": [0.7, 0.3],
    },
    "NO2": {
        "code": "42602",
        "unit": "PPB",
        "range": (0.0, 200.0),
        "durations": ["1 HOUR"],
        "duration_weights": [1.0],
    },
    "LEAD": {
        "code": "14129",
        "unit": "UG/M3",
        "range": (0.0, 5.0),
        "durations": ["24 HOUR"],
        "duration_weights": [1.0],
    },
}

# AQI category boundaries (inclusive lower, inclusive upper)
_AQI_CATEGORIES = [
    (0, 50, "GOOD"),
    (51, 100, "MODERATE"),
    (101, 150, "UNHEALTHY_SENSITIVE"),
    (151, 200, "UNHEALTHY"),
    (201, 300, "VERY_UNHEALTHY"),
    (301, 500, "HAZARDOUS"),
]

# Water quality: contaminant → (code, unit, typical_range, mcl)
# MCL values are US EPA Maximum Contaminant Levels
CONTAMINANT_SPECS: dict[str, dict[str, Any]] = {
    "Arsenic": {
        "code": None,
        "unit": "MG/L",
        "range": (0.0, 0.020),
        "mcl": 0.010,
    },
    "Lead": {
        "code": None,
        "unit": "UG/L",
        "range": (0.0, 30.0),
        "mcl": 15.0,
    },
    "Nitrate": {
        "code": None,
        "unit": "MG/L",
        "range": (0.0, 15.0),
        "mcl": 10.0,
    },
    "Fluoride": {
        "code": None,
        "unit": "MG/L",
        "range": (0.0, 5.0),
        "mcl": 4.0,
    },
    "Copper": {
        "code": None,
        "unit": "MG/L",
        "range": (0.0, 2.0),
        "mcl": 1.3,
    },
    "Coliform": {
        "code": None,
        "unit": "CFU/100ML",
        "range": (0.0, 10.0),
        "mcl": 0.0,  # Zero tolerance (presence/absence rule)
    },
    "Turbidity": {
        "code": None,
        "unit": "NTU",
        "range": (0.0, 5.0),
        "mcl": 1.0,
    },
    "Chlorine Residual": {
        "code": None,
        "unit": "MG/L",
        "range": (0.0, 4.0),
        "mcl": 4.0,
    },
    "Trihalomethanes": {
        "code": None,
        "unit": "UG/L",
        "range": (0.0, 120.0),
        "mcl": 80.0,
    },
    "Radium-226": {
        "code": None,
        "unit": "PCI/L",
        "range": (0.0, 10.0),
        "mcl": 5.0,
    },
}

# US state codes (FIPS 2-digit) paired with abbreviated name for site_id construction
_STATE_CODES = [
    "01", "02", "04", "05", "06", "08", "09", "10", "11", "12",
    "13", "15", "16", "17", "18", "19", "20", "21", "22", "23",
    "24", "25", "26", "27", "28", "29", "30", "31", "32", "33",
    "34", "35", "36", "37", "38", "39", "40", "41", "42", "44",
    "45", "46", "47", "48", "49", "50", "51", "53", "54", "55",
    "56",
]

_STATE_NAMES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "District of Columbia", "Florida", "Georgia",
    "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
    "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
    "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota",
    "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
    "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia",
    "Washington", "West Virginia", "Wisconsin", "Wyoming",
]

# Zip-aligned state code → name mapping (index-matched to _STATE_CODES)
_STATE_CODE_TO_NAME: dict[str, str] = dict(zip(_STATE_CODES, _STATE_NAMES))


def _aqi_category(aqi_value: int) -> str:
    """Return the AQI category string for a given AQI integer value."""
    for lo, hi, label in _AQI_CATEGORIES:
        if lo <= aqi_value <= hi:
            return label
    return "HAZARDOUS"


# ---------------------------------------------------------------------------
# Generator class
# ---------------------------------------------------------------------------


class EPAGenerator(BaseGenerator):
    """
    Generate synthetic EPA environmental monitoring records.

    Supports two domains selected via the ``domain`` argument to
    :meth:`generate_record`:

    * ``"air_quality"``  – AQS monitoring site measurements
    * ``"water_quality"`` – SDWIS public water system sample results
    """

    def __init__(
        self,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        domain: str = "air_quality",
    ):
        """
        Initialize the EPA generator.

        Args:
            seed: Random seed for reproducibility.
            start_date: Earliest date for generated observations.
            end_date: Latest date for generated observations.
            domain: Default domain when :meth:`generate_record` is called
                without an explicit argument.  One of ``"air_quality"``
                or ``"water_quality"``.
        """
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)

        if domain not in ("air_quality", "water_quality"):
            raise ValueError(
                f"domain must be 'air_quality' or 'water_quality', got {domain!r}"
            )
        self.default_domain = domain

        # Shared schema is merged at runtime; keep separate schemas for clarity.
        self._air_schema: dict[str, str] = {
            "record_id": "string",
            "site_id": "string",
            "site_name": "string",
            "parameter": "string",
            "parameter_code": "string",
            "date_local": "date",
            "time_local": "string",
            "aqi_value": "integer",
            "aqi_category": "string",
            "concentration": "float",
            "units": "string",
            "sample_duration": "string",
            "latitude": "float",
            "longitude": "float",
            "state_code": "string",
            "county_code": "string",
            "state_name": "string",
            "county_name": "string",
            "cbsa_name": "string",
            "method_code": "string",
            "load_time": "datetime",
        }

        self._water_schema: dict[str, str] = {
            "record_id": "string",
            "system_id": "string",
            "system_name": "string",
            "system_type": "string",
            "sample_date": "date",
            "contaminant": "string",
            "contaminant_code": "string",
            "result_value": "float",
            "unit": "string",
            "mcl": "float",
            "mcl_violation": "boolean",
            "violation_type": "string",
            "state_code": "string",
            "county_served": "string",
            "population_served": "integer",
            "source_type": "string",
            "primacy_agency": "string",
            "load_time": "datetime",
        }

        self._schema = (
            self._air_schema
            if domain == "air_quality"
            else self._water_schema
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_record(self, domain: Optional[str] = None) -> dict[str, Any]:
        """
        Generate a single EPA environmental monitoring record.

        Args:
            domain: ``"air_quality"`` or ``"water_quality"``.  Defaults to
                the value passed at construction time.

        Returns:
            Dictionary representing one monitoring observation.
        """
        domain = domain or self.default_domain
        if domain == "air_quality":
            return self._generate_air_quality_record()
        if domain == "water_quality":
            return self._generate_water_quality_record()
        raise ValueError(
            f"domain must be 'air_quality' or 'water_quality', got {domain!r}"
        )

    # ------------------------------------------------------------------
    # Air quality
    # ------------------------------------------------------------------

    def _generate_air_quality_record(self) -> dict[str, Any]:
        """Generate a single AQS monitoring site observation."""
        # Choose parameter with equal probability
        parameters = list(PARAMETER_MAP.keys())
        parameter = str(np.random.choice(parameters))
        spec = PARAMETER_MAP[parameter]

        # Generate AQI – skewed toward the GOOD/MODERATE range (realistic US avg)
        aqi_value = self._realistic_aqi()
        aqi_category = _aqi_category(aqi_value)

        # Concentration: scale within parameter range proportional to AQI fraction
        lo, hi = spec["range"]
        aqi_fraction = aqi_value / 500.0
        concentration = round(
            float(np.random.uniform(lo, lo + (hi - lo) * min(aqi_fraction * 1.5, 1.0))),
            4,
        )

        # Sample duration
        durations: list[str] = spec["durations"]
        dur_weights: list[float] = spec["duration_weights"]
        sample_duration: Optional[str] = str(
            np.random.choice(durations, p=dur_weights)
        ) if np.random.random() > 0.05 else None

        # Time: 1-HOUR readings have an explicit time; 24-HOUR often null
        if sample_duration == "1 HOUR":
            hour = np.random.randint(0, 24)
            time_local: Optional[str] = f"{hour:02d}:00"
        elif sample_duration == "8 HOUR":
            start_hour = np.random.choice([0, 8, 16])
            time_local = f"{start_hour:02d}:00"
        else:
            time_local = None if np.random.random() > 0.3 else "00:00"

        # Location
        state_code = str(np.random.choice(_STATE_CODES))
        county_code = f"{np.random.randint(1, 999):03d}"
        site_num = f"{np.random.randint(1, 9999):04d}"
        site_id = f"{state_code}-{county_code}-{site_num}"

        lat = round(float(np.random.uniform(25.0, 49.0)), 6)
        lon = round(float(np.random.uniform(-125.0, -67.0)), 6)

        obs_dt = self.random_datetime()

        record: dict[str, Any] = {
            "record_id": self.generate_uuid(),
            "site_id": site_id,
            "site_name": self.faker.city() + " Monitoring Station",
            "parameter": parameter,
            "parameter_code": spec["code"],
            "date_local": obs_dt.strftime("%Y-%m-%d"),
            "time_local": time_local,
            "aqi_value": aqi_value,
            "aqi_category": aqi_category,
            "concentration": concentration,
            "units": spec["unit"],
            "sample_duration": sample_duration,
            "latitude": lat,
            "longitude": lon,
            "state_code": state_code,
            "county_code": county_code,
            "state_name": _STATE_CODE_TO_NAME.get(state_code),
            "county_name": self.faker.city() + " County"
            if np.random.random() > 0.1
            else None,
            "cbsa_name": self.faker.city() + "-" + self.faker.city() + " MSA"
            if np.random.random() > 0.3
            else None,
            "method_code": None,
            "load_time": datetime.now().isoformat(),
        }

        return self.add_metadata_columns(record)

    def _realistic_aqi(self) -> int:
        """
        Return a realistic AQI integer with a right-skewed distribution.

        Approximately:
          ~55 % GOOD (0-50)
          ~30 % MODERATE (51-100)
          ~10 % UNHEALTHY_SENSITIVE (101-150)
           ~4 % UNHEALTHY (151-200)
           ~1 % VERY_UNHEALTHY / HAZARDOUS (201-500)
        """
        bucket = np.random.random()
        if bucket < 0.55:
            return int(np.random.randint(0, 51))
        elif bucket < 0.85:
            return int(np.random.randint(51, 101))
        elif bucket < 0.95:
            return int(np.random.randint(101, 151))
        elif bucket < 0.99:
            return int(np.random.randint(151, 201))
        else:
            return int(np.random.randint(201, 501))

    # ------------------------------------------------------------------
    # Water quality
    # ------------------------------------------------------------------

    def _generate_water_quality_record(self) -> dict[str, Any]:
        """Generate a single SDWIS public water system sample result."""
        contaminant = str(np.random.choice(list(CONTAMINANT_SPECS.keys())))
        spec = CONTAMINANT_SPECS[contaminant]

        lo, hi = spec["range"]
        mcl: float = spec["mcl"]
        unit: str = spec["unit"]

        # ~5 % of records exceed the MCL
        is_violation = np.random.random() < 0.05
        if is_violation and mcl > 0:
            # Result above MCL up to 3× MCL
            result_value = round(float(np.random.uniform(mcl * 1.01, mcl * 3.0)), 6)
        elif is_violation and mcl == 0:
            # Coliform: any positive is a violation
            result_value = round(float(np.random.uniform(0.1, hi)), 4)
        else:
            # Compliant result – keep below MCL (or within range for MCL=0)
            upper = mcl * 0.9 if mcl > 0 else hi * 0.5
            upper = min(upper, hi)
            result_value = round(float(np.random.uniform(lo, upper)), 6)

        # Clamp to spec range
        result_value = float(np.clip(result_value, lo, hi * 1.5))

        violation_type: Optional[str] = "MCL" if is_violation else None

        # System type weighted 70/20/10
        system_type = str(
            self.weighted_choice(
                ["CWS", "NTNCWS", "TNCWS"],
                [0.70, 0.20, 0.10],
            )
        )

        state_code = str(np.random.choice(_STATE_CODES))
        sample_dt = self.random_datetime()

        population_served = int(
            np.random.choice(
                [100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000, 5000000],
                p=[0.05, 0.10, 0.15, 0.20, 0.20, 0.15, 0.08, 0.04, 0.02, 0.01],
            )
        )
        # Add jitter so values are not always round
        population_served = max(
            100,
            population_served + int(np.random.randint(-50, 50)),
        )

        source_type = str(
            np.random.choice(
                ["GROUND_WATER", "SURFACE_WATER", "MIXED"],
                p=[0.55, 0.35, 0.10],
            )
        )

        record: dict[str, Any] = {
            "record_id": self.generate_uuid(),
            "system_id": "PWS" + f"{np.random.randint(1000000, 9999999):07d}",
            "system_name": self.faker.city() + " Water System",
            "system_type": system_type,
            "sample_date": sample_dt.strftime("%Y-%m-%d"),
            "contaminant": contaminant,
            "contaminant_code": spec["code"],
            "result_value": result_value,
            "unit": unit,
            "mcl": mcl,
            "mcl_violation": bool(is_violation),
            "violation_type": violation_type,
            "state_code": state_code,
            "county_served": None,
            "population_served": population_served,
            "source_type": source_type,
            "primacy_agency": None,
            "load_time": datetime.now().isoformat(),
        }

        return self.add_metadata_columns(record)
