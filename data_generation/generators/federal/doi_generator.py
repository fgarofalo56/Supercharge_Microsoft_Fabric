"""
DOI Generator
=============

Generates synthetic Department of the Interior (DOI) data for two domains:

- earthquake (default): USGS-style seismic event records drawn from the
  ComCat / ShakeMap schema.  Magnitudes follow the Gutenberg-Richter power
  law (~60 % M1-3, ~25 % M3-5, ~10 % M5-6, ~4 % M6-7, ~1 % M7+).
  Hypocenters are weighted toward real seismically active zones (Pacific
  Ring of Fire, US West Coast, Alaska, New Madrid Seismic Zone).

- land_use: BLM/NPS/FWS/USFS/BOR/DOD parcel records mirroring the
  BLM Geographic Coordinate Database (GCDB) and National Land Cover
  Database (NLCD) schema.  Parcels are weighted toward the western states
  where the federal land estate is largest.

Generated records can be joined with real USGS Earthquake Catalog and
BLM LR2000 data for POC demonstrations.
"""

from datetime import datetime, timedelta
from typing import Any, Literal

import numpy as np

from ..base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# Domain type alias
# ---------------------------------------------------------------------------
DomainType = Literal["earthquake", "land_use"]

# ===========================================================================
# ── EARTHQUAKE DOMAIN ──────────────────────────────────────────────────────
# ===========================================================================

# ── Seismic zone boxes ──────────────────────────────────────────────────────
# Each entry: (name, lat_min, lat_max, lon_min, lon_max, weight)
# Weights must sum to 1.0 across all zones.
_SEISMIC_ZONES: list[tuple[str, float, float, float, float, float]] = [
    # US West Coast  (CA, OR, WA Cascadia / San Andreas)
    ("us_west_coast", 32.5, 49.0, -124.5, -116.0, 0.28),
    # Alaska & Aleutian Arc
    ("alaska", 51.0, 71.5, -168.0, -130.0, 0.22),
    # Pacific Ring of Fire – Japan/NW Pacific
    ("japan", 30.0, 45.0, 130.0, 145.0, 0.12),
    # Pacific Ring of Fire – Central America / Mexico
    ("central_america", 10.0, 22.0, -105.0, -82.0, 0.09),
    # Pacific Ring of Fire – South America (Andes)
    ("south_america", -35.0, 5.0, -81.0, -65.0, 0.08),
    # New Madrid Seismic Zone (US Midwest)
    ("new_madrid", 35.5, 37.5, -90.5, -87.5, 0.05),
    # Hawaii volcanic zone
    ("hawaii", 18.5, 22.5, -160.5, -154.5, 0.04),
    # Mediterranean / Turkey
    ("mediterranean", 35.0, 43.0, 26.0, 43.0, 0.05),
    # New Zealand / SW Pacific
    ("new_zealand", -48.0, -34.0, 165.0, 178.0, 0.04),
    # Indonesia / SE Asia
    ("indonesia", -8.0, 5.0, 95.0, 140.0, 0.03),
]

_ZONE_NAMES = [z[0] for z in _SEISMIC_ZONES]
_ZONE_WEIGHTS = np.array([z[5] for z in _SEISMIC_ZONES], dtype=float)
_ZONE_WEIGHTS /= _ZONE_WEIGHTS.sum()  # normalise in case of rounding

# ── Magnitude distribution buckets ─────────────────────────────────────────
# (mag_min, mag_max, probability)
_MAG_BUCKETS: list[tuple[float, float, float]] = [
    (1.0, 3.0, 0.60),
    (3.0, 5.0, 0.25),
    (5.0, 6.0, 0.10),
    (6.0, 7.0, 0.04),
    (7.0, 9.5, 0.01),
]
_MAG_PROBS = np.array([b[2] for b in _MAG_BUCKETS], dtype=float)
_MAG_PROBS /= _MAG_PROBS.sum()

# ── Magnitude-type selection ────────────────────────────────────────────────
# ML most common for small, MW(W/C/B) for large, mixed in middle
_MAG_TYPES = ["ML", "MD", "MB", "MW", "MS", "MWW", "MWC", "MWB"]
_MAG_TYPE_SMALL = np.array(
    [0.50, 0.20, 0.12, 0.06, 0.04, 0.03, 0.03, 0.02], dtype=float
)
_MAG_TYPE_MEDIUM = np.array(
    [0.20, 0.10, 0.15, 0.25, 0.10, 0.10, 0.05, 0.05], dtype=float
)
_MAG_TYPE_LARGE = np.array(
    [0.02, 0.02, 0.06, 0.30, 0.10, 0.25, 0.15, 0.10], dtype=float
)

# ── Event type ──────────────────────────────────────────────────────────────
_EVENT_TYPES = [
    "EARTHQUAKE",
    "QUARRY_BLAST",
    "EXPLOSION",
    "VOLCANIC_ERUPTION",
    "ICE_QUAKE",
]
_EVENT_WEIGHTS = np.array([0.95, 0.03, 0.01, 0.005, 0.005], dtype=float)
_EVENT_WEIGHTS /= _EVENT_WEIGHTS.sum()

# ── Review status ────────────────────────────────────────────────────────────
_STATUSES = ["AUTOMATIC", "REVIEWED", "DELETED"]
_STATUS_WEIGHTS = np.array([0.35, 0.60, 0.05], dtype=float)

# ── Alert levels ─────────────────────────────────────────────────────────────
_ALERTS = ["GREEN", "YELLOW", "ORANGE", "RED", None]

# ── Source networks ───────────────────────────────────────────────────────────
_NETWORKS = ["us", "ci", "nc", "ak", "hv", "nn"]

# ── Cardinal directions for place description ────────────────────────────────
_DIRECTIONS = [
    "N",
    "NE",
    "E",
    "SE",
    "S",
    "SW",
    "W",
    "NW",
    "NNE",
    "ENE",
    "ESE",
    "SSE",
    "SSW",
    "WSW",
    "WNW",
    "NNW",
]


def _pick_seismic_location(rng: np.random.Generator) -> tuple[float, float]:
    """Return (latitude, longitude) from a randomly selected seismic zone."""
    idx = int(rng.choice(len(_SEISMIC_ZONES), p=_ZONE_WEIGHTS))
    _, lat_min, lat_max, lon_min, lon_max, _ = _SEISMIC_ZONES[idx]
    lat = float(rng.uniform(lat_min, lat_max))
    lon = float(rng.uniform(lon_min, lon_max))
    return round(lat, 4), round(lon, 4)


def _pick_magnitude(rng: np.random.Generator) -> float:
    """Return a magnitude sampled from the Gutenberg-Richter distribution."""
    bucket_idx = int(rng.choice(len(_MAG_BUCKETS), p=_MAG_PROBS))
    mag_min, mag_max, _ = _MAG_BUCKETS[bucket_idx]
    # Uniform within bucket approximates the GR law at this coarse resolution.
    return round(float(rng.uniform(mag_min, mag_max)), 1)


def _pick_mag_type(rng: np.random.Generator, magnitude: float) -> str:
    """Return appropriate magnitude type for a given magnitude value."""
    if magnitude < 3.0:
        weights = _MAG_TYPE_SMALL
    elif magnitude < 5.0:
        weights = _MAG_TYPE_MEDIUM
    else:
        weights = _MAG_TYPE_LARGE
    w = weights / weights.sum()
    return str(rng.choice(_MAG_TYPES, p=w))


def _pick_alert(rng: np.random.Generator, magnitude: float) -> str | None:
    """Return PAGER alert level correlated with magnitude."""
    if magnitude < 5.0:
        # ~95 % null, ~5 % GREEN
        return None if rng.random() < 0.95 else "GREEN"
    elif magnitude < 6.0:
        weights = [0.70, 0.25, 0.04, 0.01, 0.00]
    elif magnitude < 7.0:
        weights = [0.30, 0.45, 0.18, 0.07, 0.00]
    else:
        weights = [0.10, 0.30, 0.35, 0.25, 0.00]
    return _ALERTS[int(rng.choice(len(_ALERTS), p=np.array(weights, dtype=float)))]


def _significance(rng: np.random.Generator, magnitude: float) -> int:
    """Return significance score (0-1000) correlated with magnitude."""
    # Simple linear mapping with jitter: M1→~20, M5→~400, M7→~800, M9→~1000
    base = min(1000, max(0, int((magnitude - 1.0) / 8.5 * 1000)))
    jitter = int(rng.integers(-30, 31))
    return max(0, min(1000, base + jitter))


# ===========================================================================
# ── LAND USE DOMAIN ────────────────────────────────────────────────────────
# ===========================================================================

# ── Western-weighted state list ─────────────────────────────────────────────
# (state_abbr, weight) — weights must sum to 1.0
_STATES_LAND: list[tuple[str, float]] = [
    ("NV", 0.10),
    ("UT", 0.09),
    ("AZ", 0.08),
    ("NM", 0.07),
    ("WY", 0.07),
    ("MT", 0.07),
    ("ID", 0.06),
    ("OR", 0.06),
    ("AK", 0.06),
    ("CO", 0.06),
    ("CA", 0.06),
    ("WA", 0.04),
    ("ND", 0.03),
    ("SD", 0.03),
    ("NE", 0.02),
    ("KS", 0.02),
    ("OK", 0.02),
    ("TX", 0.02),
    ("MN", 0.01),
    ("WI", 0.01),
    ("MI", 0.01),
    ("VA", 0.01),
    ("FL", 0.01),
]
_STATE_ABBRS_LAND = [s[0] for s in _STATES_LAND]
_STATE_WEIGHTS_LAND = np.array([s[1] for s in _STATES_LAND], dtype=float)
_STATE_WEIGHTS_LAND /= _STATE_WEIGHTS_LAND.sum()

# ── Managing agency ──────────────────────────────────────────────────────────
_AGENCIES = ["BLM", "NPS", "FWS", "USFS", "BOR", "DOD", "OTHER"]
_AGENCY_WEIGHTS = np.array([0.35, 0.15, 0.10, 0.25, 0.08, 0.05, 0.02], dtype=float)
_AGENCY_WEIGHTS /= _AGENCY_WEIGHTS.sum()

# ── Agency → land type affinity ─────────────────────────────────────────────
_AGENCY_LAND_TYPES: dict[str, list[tuple[str, float]]] = {
    "BLM": [
        ("GRAZING", 0.40),
        ("MINING", 0.25),
        ("MIXED_USE", 0.15),
        ("RECREATION", 0.10),
        ("WILDERNESS", 0.05),
        ("TIMBER", 0.03),
        ("CONSERVATION", 0.02),
    ],
    "NPS": [
        ("RECREATION", 0.50),
        ("WILDERNESS", 0.25),
        ("CONSERVATION", 0.15),
        ("MIXED_USE", 0.08),
        ("GRAZING", 0.01),
        ("MINING", 0.01),
        ("TIMBER", 0.00),
    ],
    "FWS": [
        ("CONSERVATION", 0.55),
        ("WILDERNESS", 0.20),
        ("RECREATION", 0.10),
        ("MIXED_USE", 0.08),
        ("GRAZING", 0.05),
        ("TIMBER", 0.01),
        ("MINING", 0.01),
    ],
    "USFS": [
        ("TIMBER", 0.40),
        ("RECREATION", 0.25),
        ("WILDERNESS", 0.15),
        ("GRAZING", 0.10),
        ("MIXED_USE", 0.07),
        ("CONSERVATION", 0.02),
        ("MINING", 0.01),
    ],
    "BOR": [
        ("RECREATION", 0.35),
        ("CONSERVATION", 0.25),
        ("MIXED_USE", 0.25),
        ("GRAZING", 0.10),
        ("WILDERNESS", 0.03),
        ("TIMBER", 0.01),
        ("MINING", 0.01),
    ],
    "DOD": [
        ("MIXED_USE", 0.50),
        ("RECREATION", 0.20),
        ("GRAZING", 0.15),
        ("CONSERVATION", 0.08),
        ("WILDERNESS", 0.05),
        ("TIMBER", 0.01),
        ("MINING", 0.01),
    ],
    "OTHER": [
        ("MIXED_USE", 0.40),
        ("RECREATION", 0.20),
        ("GRAZING", 0.15),
        ("CONSERVATION", 0.10),
        ("MINING", 0.08),
        ("TIMBER", 0.05),
        ("WILDERNESS", 0.02),
    ],
}

# ── Permit types ─────────────────────────────────────────────────────────────
_PERMIT_TYPES = [
    "GRAZING_PERMIT",
    "MINING_CLAIM",
    "SPECIAL_USE",
    "RIGHT_OF_WAY",
    "NONE",
    None,
]
_PERMIT_WEIGHTS = np.array([0.30, 0.20, 0.20, 0.15, 0.10, 0.05], dtype=float)
_PERMIT_WEIGHTS /= _PERMIT_WEIGHTS.sum()

# ── Fire risk levels ─────────────────────────────────────────────────────────
_FIRE_RISK = ["LOW", "MODERATE", "HIGH", "VERY_HIGH", "EXTREME", None]
_FIRE_RISK_WEST = np.array([0.05, 0.20, 0.30, 0.25, 0.15, 0.05], dtype=float)
_FIRE_RISK_EAST = np.array([0.25, 0.35, 0.20, 0.10, 0.05, 0.05], dtype=float)

# ── Western state set for fire-risk weighting ─────────────────────────────────
_WESTERN_STATES = {
    "AK",
    "AZ",
    "CA",
    "CO",
    "ID",
    "MT",
    "NM",
    "NV",
    "OR",
    "UT",
    "WA",
    "WY",
}

# ── Designations by agency ────────────────────────────────────────────────────
_DESIGNATIONS: dict[str, list[str]] = {
    "BLM": [
        "National Monument",
        "National Conservation Area",
        "Wilderness Study Area",
        "Special Recreation Management Area",
        None,
        None,
    ],
    "NPS": [
        "National Park",
        "National Monument",
        "National Seashore",
        "National Recreation Area",
        "National Historic Site",
    ],
    "FWS": [
        "National Wildlife Refuge",
        "Wilderness Area",
        "Critical Habitat",
        "Waterfowl Production Area",
        None,
    ],
    "USFS": [
        "National Forest",
        "Wilderness Area",
        "National Grassland",
        "Special Interest Area",
        None,
    ],
    "BOR": [
        "National Recreation Area",
        "Reservoir Management Area",
        "Water Project Area",
        None,
        None,
    ],
    "DOD": ["Military Installation", "Training Range", "Reserved Zone", None, None],
    "OTHER": [None, None, "State Conservation Area", "Tribal Land"],
}

# US bounding box biased west (lon_min weighted heavily toward -124 to -95)
_US_LAT = (24.0, 71.5)
_US_LON_WEST = (-168.0, -104.0)  # Alaska + contiguous west
_US_LON_EAST = (-104.0, -66.9)  # Contiguous east


def _pick_land_location(rng: np.random.Generator, state: str) -> tuple[float, float]:
    """Return US (latitude, longitude) weighted toward western states."""
    if state in _WESTERN_STATES:
        lat = float(rng.uniform(24.0, 71.5))
        lon = float(rng.uniform(-168.0, -104.0))
    else:
        lat = float(rng.uniform(24.0, 49.0))
        lon = float(rng.uniform(-104.0, -66.9))
    return round(lat, 6), round(lon, 6)


def _pick_land_type(rng: np.random.Generator, agency: str) -> str:
    """Return a land type correlated with the managing agency."""
    choices_weights = _AGENCY_LAND_TYPES[agency]
    choices = [cw[0] for cw in choices_weights]
    weights = np.array([cw[1] for cw in choices_weights], dtype=float)
    weights /= weights.sum()
    return str(rng.choice(choices, p=weights))


def _log_normal_acres(rng: np.random.Generator) -> float:
    """Return a log-normally distributed acreage (10 – 5,000,000)."""
    # mu and sigma chosen so median ≈ 2,000 acres, 99th pct ≈ 5 M acres
    raw = float(rng.lognormal(mean=7.6, sigma=2.0))
    return round(min(5_000_000.0, max(10.0, raw)), 1)


# ===========================================================================
# ── GENERATOR CLASS ────────────────────────────────────────────────────────
# ===========================================================================


class DOIGenerator(BaseGenerator):
    """
    Generate synthetic Department of the Interior (DOI) data.

    Supports two domains via the ``domain`` parameter on
    :meth:`generate_record` and :meth:`generate_batch`:

    - ``"earthquake"`` (default) – USGS ComCat-style seismic event records
    - ``"land_use"`` – BLM/NPS/FWS/USFS parcel management records
    """

    def __init__(
        self,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Initialize the DOI generator.

        Args:
            seed: Random seed for reproducibility.
            start_date: Earliest event/record timestamp.
            end_date: Latest event/record timestamp.
        """
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)

        self._schema: dict[str, str] = {
            # ── shared ──────────────────────────────────────────────────────
            "load_time": "datetime",
            # ── earthquake domain ────────────────────────────────────────────
            "event_id": "string",
            "usgs_id": "string",
            "time": "datetime",
            "latitude": "float",
            "longitude": "float",
            "depth_km": "float",
            "magnitude": "float",
            "mag_type": "string",
            "place": "string",
            "event_type": "string",
            "status": "string",
            "tsunami": "bool",
            "significance": "int",
            "felt": "int",
            "cdi": "float",
            "mmi": "float",
            "alert": "string",
            "net": "string",
            "nst": "int",
            "gap": "float",
            "rms": "float",
            "url": "string",
            # ── land_use domain ──────────────────────────────────────────────
            "parcel_id": "string",
            "blm_serial_number": "string",
            "managing_agency": "string",
            "state": "string",
            "county": "string",
            "land_type": "string",
            "total_acres": "float",
            "designation": "string",
            "designation_date": "date",
            "permit_type": "string",
            "permit_holder": "string",
            "annual_revenue": "float",
            "environmental_assessment": "bool",
            "protected_species_present": "bool",
            "fire_risk_level": "string",
            "last_inspection_date": "date",
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Abstract method (default domain: earthquake)
    # ─────────────────────────────────────────────────────────────────────────

    def generate_record(self, domain: DomainType = "earthquake") -> dict[str, Any]:
        """
        Generate a single DOI record for the specified domain.

        Args:
            domain: ``"earthquake"`` (default) or ``"land_use"``.

        Returns:
            Dictionary with domain-specific fields plus standard metadata columns.
        """
        if domain == "land_use":
            return self._generate_land_use_record()
        return self._generate_earthquake_record()

    # ─────────────────────────────────────────────────────────────────────────
    # Batch helper
    # ─────────────────────────────────────────────────────────────────────────

    def generate_batch(
        self,
        count: int = 1000,
        domain: DomainType = "earthquake",
    ) -> "pd.DataFrame":  # type: ignore[name-defined]  # noqa: F821
        """
        Generate a batch of DOI records for the specified domain.

        Args:
            count: Number of records to generate.
            domain: ``"earthquake"`` or ``"land_use"``.

        Returns:
            :class:`pandas.DataFrame` containing ``count`` rows.
        """
        import pandas as pd  # local import keeps the class importable without pandas

        records = [self.generate_record(domain=domain) for _ in range(count)]
        return pd.DataFrame(records)

    # ─────────────────────────────────────────────────────────────────────────
    # Earthquake record builder
    # ─────────────────────────────────────────────────────────────────────────

    def _generate_earthquake_record(self) -> dict[str, Any]:
        """Build a single USGS ComCat-style earthquake event record."""
        # ── core seismic parameters ──────────────────────────────────────────
        magnitude = _pick_magnitude(self.rng)
        mag_type = _pick_mag_type(self.rng, magnitude)
        lat, lon = _pick_seismic_location(self.rng)

        # Depth: most shallow (0-30 km), long tail to 700 km
        depth_roll = self.rng.random()
        if depth_roll < 0.70:
            depth_km = round(float(self.rng.uniform(0.0, 30.0)), 2)
        elif depth_roll < 0.90:
            depth_km = round(float(self.rng.uniform(30.0, 100.0)), 2)
        else:
            depth_km = round(float(self.rng.uniform(100.0, 700.0)), 2)

        # ── identifiers ──────────────────────────────────────────────────────
        event_id = self.generate_uuid()
        # USGS network ID present 85 % of the time
        usgs_id: str | None = None
        if self.rng.random() < 0.85:
            usgs_id = "us" + self.faker.hexify("^^^^^^^")

        # ── event time ───────────────────────────────────────────────────────
        event_time = self.random_datetime()

        # ── place description ────────────────────────────────────────────────
        dist_km = int(self.rng.integers(2, 100))
        direction = str(self.rng.choice(_DIRECTIONS))
        city_name = self.faker.city()
        state_abbr = self.faker.state_abbr()
        place = f"{dist_km}km {direction} of {city_name}, {state_abbr}"

        # ── event type & review status ───────────────────────────────────────
        event_type = str(self.rng.choice(_EVENT_TYPES, p=_EVENT_WEIGHTS))
        status = str(self.rng.choice(_STATUSES, p=_STATUS_WEIGHTS))

        # ── tsunami flag: shallow and large only ─────────────────────────────
        tsunami = bool(
            magnitude >= 6.5 and depth_km <= 70.0 and self.rng.random() < 0.40
        )

        # ── felt reports (DYFI): only M2+ and only some fraction ─────────────
        felt: int | None = None
        cdi: float | None = None
        if magnitude >= 2.0 and self.rng.random() < 0.35:
            felt = int(self.rng.integers(1, max(2, int(10 ** (magnitude - 1.5)))))
            cdi = round(float(self.rng.uniform(1.0, min(12.0, magnitude * 1.6))), 1)

        # ── ShakeMap MMI ──────────────────────────────────────────────────────
        mmi: float | None = None
        if magnitude >= 3.0 and self.rng.random() < 0.60:
            mmi = round(float(self.rng.uniform(1.0, min(12.0, magnitude * 1.5))), 1)

        # ── PAGER alert level ─────────────────────────────────────────────────
        alert = _pick_alert(self.rng, magnitude)

        # ── quality / network parameters ──────────────────────────────────────
        sig = _significance(self.rng, magnitude)
        net = str(self.rng.choice(_NETWORKS))
        nst = int(self.rng.integers(5, 501))
        gap = round(float(self.rng.uniform(10.0, 360.0)), 1)
        rms = round(float(self.rng.uniform(0.01, 2.0)), 3)

        record: dict[str, Any] = {
            "event_id": event_id,
            "usgs_id": usgs_id,
            "time": event_time.isoformat(),
            "latitude": lat,
            "longitude": lon,
            "depth_km": depth_km,
            "magnitude": magnitude,
            "mag_type": mag_type,
            "place": place,
            "event_type": event_type,
            "status": status,
            "tsunami": tsunami,
            "significance": sig,
            "felt": felt,
            "cdi": cdi,
            "mmi": mmi,
            "alert": alert,
            "net": net,
            "nst": nst,
            "gap": gap,
            "rms": rms,
            "url": None,
            "load_time": datetime.now().isoformat(),
        }

        return self.add_metadata_columns(record)

    # ─────────────────────────────────────────────────────────────────────────
    # Land use record builder
    # ─────────────────────────────────────────────────────────────────────────

    def _generate_land_use_record(self) -> dict[str, Any]:
        """Build a single BLM/NPS/FWS parcel land-use record."""
        # ── geography & managing agency ───────────────────────────────────────
        state = str(self.rng.choice(_STATE_ABBRS_LAND, p=_STATE_WEIGHTS_LAND))
        agency = str(self.rng.choice(_AGENCIES, p=_AGENCY_WEIGHTS))
        lat, lon = _pick_land_location(self.rng, state)

        # ── land classification ───────────────────────────────────────────────
        land_type = _pick_land_type(self.rng, agency)
        total_acres = _log_normal_acres(self.rng)

        # ── identifiers ──────────────────────────────────────────────────────
        parcel_id = self.generate_uuid()
        blm_serial: str | None = None
        if agency in ("BLM", "BOR") and self.rng.random() < 0.80:
            seq = f"{int(self.rng.integers(100000, 999999))}"
            blm_serial = f"BLM-{state}-{seq}"

        # ── county (optional, 75 %) ───────────────────────────────────────────
        county: str | None = self.faker.city() if self.rng.random() < 0.75 else None

        # ── designation ───────────────────────────────────────────────────────
        desig_pool = _DESIGNATIONS.get(agency, [None])
        designation: str | None = str(self.rng.choice(desig_pool))
        if designation == "None":
            designation = None

        # Designation date only when there is a designation
        designation_date: str | None = None
        if designation is not None:
            # Designations go back to 1906 (Antiquities Act)
            days_back = int(self.rng.integers(0, 365 * 120))
            desig_dt = datetime.now() - timedelta(days=days_back)
            designation_date = desig_dt.strftime("%Y-%m-%d")

        # ── permit ────────────────────────────────────────────────────────────
        permit_type: str | None = str(self.rng.choice(_PERMIT_TYPES, p=_PERMIT_WEIGHTS))
        if permit_type == "None":
            permit_type = None

        permit_holder: str | None = None
        if permit_type not in (None, "NONE"):
            permit_holder = self.faker.company()

        # ── financials (permit_holder or BLM/BOR revenue) ─────────────────────
        annual_revenue: float | None = None
        if permit_holder is not None and self.rng.random() < 0.70:
            annual_revenue = round(float(self.rng.uniform(0.0, 10_000_000.0)), 2)

        # ── environmental / ecological flags ─────────────────────────────────
        env_assess: bool | None = None
        if self.rng.random() < 0.80:
            env_assess = bool(self.rng.random() < 0.55)

        protected_species: bool | None = None
        if self.rng.random() < 0.75:
            # FWS lands have higher probability of protected species
            prob = 0.65 if agency == "FWS" else 0.30
            protected_species = bool(self.rng.random() < prob)

        # ── fire risk ─────────────────────────────────────────────────────────
        fire_risk: str | None = None
        if self.rng.random() < 0.85:
            weights = _FIRE_RISK_WEST if state in _WESTERN_STATES else _FIRE_RISK_EAST
            w = weights / weights.sum()
            fire_risk = str(self.rng.choice(_FIRE_RISK, p=w))
            if fire_risk == "None":
                fire_risk = None

        # ── last inspection date (optional, 65 %) ────────────────────────────
        last_inspection: str | None = None
        if self.rng.random() < 0.65:
            days_ago = int(self.rng.integers(0, 365 * 5))
            insp_dt = datetime.now() - timedelta(days=days_ago)
            last_inspection = insp_dt.strftime("%Y-%m-%d")

        record: dict[str, Any] = {
            "parcel_id": parcel_id,
            "blm_serial_number": blm_serial,
            "managing_agency": agency,
            "state": state,
            "county": county,
            "land_type": land_type,
            "total_acres": total_acres,
            "latitude": lat,
            "longitude": lon,
            "designation": designation,
            "designation_date": designation_date,
            "permit_type": permit_type,
            "permit_holder": permit_holder,
            "annual_revenue": annual_revenue,
            "environmental_assessment": env_assess,
            "protected_species_present": protected_species,
            "fire_risk_level": fire_risk,
            "last_inspection_date": last_inspection,
            "load_time": datetime.now().isoformat(),
        }

        return self.add_metadata_columns(record)
