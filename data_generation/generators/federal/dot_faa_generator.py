"""
DOT/FAA Generator
=================

Generates synthetic U.S. Department of Transportation / Federal Aviation
Administration data across four domains:

- flight_operations: BTS On-Time Performance-style records covering scheduled
  and actual departure times, delays, cancellations, and diversions.

- safety_incident: FAA safety event records including runway incursions, bird
  strikes, turbulence reports, and mechanical issues with severity ratings.

- traffic_statistics: T-100 traffic statistics-style records covering
  passenger counts, carrier operations, and airport-level metrics.

- infrastructure: Airport and runway infrastructure records covering
  categories, surface conditions, and facility metadata.

Data shapes mirror the Bureau of Transportation Statistics (BTS) On-Time
Performance database, FAA Incident Data System, and T-100 Domestic Segment
datasets so generated records can be joined with real public data for POC
demonstrations.
"""

from datetime import datetime
from typing import Any, Literal

from ..base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# Domain type alias
# ---------------------------------------------------------------------------
DomainType = Literal[
    "flight_operations", "safety_incident", "traffic_statistics", "infrastructure"
]

# ---------------------------------------------------------------------------
# Airlines: 20 major US carriers with IATA codes
# ---------------------------------------------------------------------------
CARRIERS: list[dict[str, str]] = [
    {"code": "AA", "name": "American Airlines"},
    {"code": "DL", "name": "Delta Air Lines"},
    {"code": "UA", "name": "United Airlines"},
    {"code": "WN", "name": "Southwest Airlines"},
    {"code": "B6", "name": "JetBlue Airways"},
    {"code": "AS", "name": "Alaska Airlines"},
    {"code": "NK", "name": "Spirit Airlines"},
    {"code": "F9", "name": "Frontier Airlines"},
    {"code": "HA", "name": "Hawaiian Airlines"},
    {"code": "G4", "name": "Allegiant Air"},
    {"code": "SY", "name": "Sun Country Airlines"},
    {"code": "MX", "name": "Breeze Airways"},
    {"code": "QX", "name": "Horizon Air"},
    {"code": "OH", "name": "PSA Airlines"},
    {"code": "OO", "name": "SkyWest Airlines"},
    {"code": "YX", "name": "Republic Airways"},
    {"code": "9E", "name": "Endeavor Air"},
    {"code": "MQ", "name": "Envoy Air"},
    {"code": "YV", "name": "Mesa Airlines"},
    {"code": "CP", "name": "Compass Airlines"},
]

# Weighted distribution: majors get more traffic than regionals
CARRIER_WEIGHTS: list[float] = [
    0.14,
    0.13,
    0.12,
    0.12,
    0.06,
    0.05,
    0.05,
    0.04,
    0.03,
    0.03,
    0.02,
    0.02,
    0.02,
    0.02,
    0.04,
    0.03,
    0.03,
    0.02,
    0.02,
    0.01,
]

# ---------------------------------------------------------------------------
# Airports: 30 major US airports with IATA codes
# ---------------------------------------------------------------------------
AIRPORTS: list[dict[str, str]] = [
    {
        "code": "ATL",
        "name": "Hartsfield-Jackson Atlanta Intl",
        "region": "ASO",
        "category": "large_hub",
    },
    {
        "code": "ORD",
        "name": "Chicago O'Hare Intl",
        "region": "AGL",
        "category": "large_hub",
    },
    {
        "code": "DFW",
        "name": "Dallas/Fort Worth Intl",
        "region": "ASW",
        "category": "large_hub",
    },
    {"code": "DEN", "name": "Denver Intl", "region": "ANM", "category": "large_hub"},
    {
        "code": "LAX",
        "name": "Los Angeles Intl",
        "region": "AWP",
        "category": "large_hub",
    },
    {
        "code": "JFK",
        "name": "John F. Kennedy Intl",
        "region": "AEA",
        "category": "large_hub",
    },
    {
        "code": "SFO",
        "name": "San Francisco Intl",
        "region": "AWP",
        "category": "large_hub",
    },
    {
        "code": "SEA",
        "name": "Seattle-Tacoma Intl",
        "region": "ANM",
        "category": "large_hub",
    },
    {"code": "MCO", "name": "Orlando Intl", "region": "ASO", "category": "large_hub"},
    {"code": "MIA", "name": "Miami Intl", "region": "ASO", "category": "large_hub"},
    {
        "code": "LAS",
        "name": "Harry Reid Intl",
        "region": "AWP",
        "category": "large_hub",
    },
    {
        "code": "PHX",
        "name": "Phoenix Sky Harbor Intl",
        "region": "AWP",
        "category": "large_hub",
    },
    {
        "code": "IAH",
        "name": "George Bush Intercontinental",
        "region": "ASW",
        "category": "large_hub",
    },
    {
        "code": "CLT",
        "name": "Charlotte Douglas Intl",
        "region": "ASO",
        "category": "large_hub",
    },
    {
        "code": "EWR",
        "name": "Newark Liberty Intl",
        "region": "AEA",
        "category": "large_hub",
    },
    {
        "code": "MSP",
        "name": "Minneapolis-Saint Paul Intl",
        "region": "AGL",
        "category": "large_hub",
    },
    {
        "code": "DTW",
        "name": "Detroit Metropolitan Wayne County",
        "region": "AGL",
        "category": "large_hub",
    },
    {
        "code": "BOS",
        "name": "Boston Logan Intl",
        "region": "ANE",
        "category": "large_hub",
    },
    {
        "code": "PHL",
        "name": "Philadelphia Intl",
        "region": "AEA",
        "category": "large_hub",
    },
    {"code": "LGA", "name": "LaGuardia", "region": "AEA", "category": "large_hub"},
    {
        "code": "FLL",
        "name": "Fort Lauderdale-Hollywood Intl",
        "region": "ASO",
        "category": "large_hub",
    },
    {
        "code": "BWI",
        "name": "Baltimore/Washington Intl",
        "region": "AEA",
        "category": "medium_hub",
    },
    {
        "code": "DCA",
        "name": "Ronald Reagan Washington National",
        "region": "AEA",
        "category": "medium_hub",
    },
    {
        "code": "SAN",
        "name": "San Diego Intl",
        "region": "AWP",
        "category": "medium_hub",
    },
    {"code": "TPA", "name": "Tampa Intl", "region": "ASO", "category": "medium_hub"},
    {"code": "PDX", "name": "Portland Intl", "region": "ANM", "category": "medium_hub"},
    {
        "code": "SLC",
        "name": "Salt Lake City Intl",
        "region": "ANM",
        "category": "medium_hub",
    },
    {
        "code": "STL",
        "name": "St. Louis Lambert Intl",
        "region": "ACE",
        "category": "medium_hub",
    },
    {
        "code": "BNA",
        "name": "Nashville Intl",
        "region": "ASO",
        "category": "medium_hub",
    },
    {
        "code": "AUS",
        "name": "Austin-Bergstrom Intl",
        "region": "ASW",
        "category": "medium_hub",
    },
]

# Build lookup dicts for quick access
_AIRPORT_BY_CODE: dict[str, dict[str, str]] = {a["code"]: a for a in AIRPORTS}
_AIRPORT_CODES: list[str] = [a["code"] for a in AIRPORTS]

# ---------------------------------------------------------------------------
# FAA regions
# ---------------------------------------------------------------------------
FAA_REGIONS: list[str] = ["AAL", "ACE", "AEA", "AGL", "ANE", "ANM", "ASO", "ASW", "AWP"]

# Region weights (continental US regions get more traffic)
FAA_REGION_WEIGHTS: list[float] = [0.02, 0.06, 0.16, 0.12, 0.08, 0.10, 0.18, 0.14, 0.14]

# ---------------------------------------------------------------------------
# Delay cause distribution (65% on-time)
# ---------------------------------------------------------------------------
DELAY_CAUSES: list[str] = [
    "none",
    "carrier",
    "weather",
    "nas",
    "security",
    "late_aircraft",
]
DELAY_CAUSE_WEIGHTS: list[float] = [0.65, 0.15, 0.10, 0.05, 0.03, 0.02]

# ---------------------------------------------------------------------------
# Safety incident configuration
# ---------------------------------------------------------------------------
INCIDENT_TYPES: list[str] = [
    "bird_strike",
    "turbulence",
    "mechanical",
    "runway_incursion",
    "fuel_issue",
    "medical",
    "security_threat",
    "near_miss",
]
INCIDENT_TYPE_WEIGHTS: list[float] = [0.30, 0.25, 0.20, 0.08, 0.06, 0.05, 0.03, 0.03]

INCIDENT_SEVERITIES: list[str] = ["minor", "moderate", "serious", "critical"]
INCIDENT_SEVERITY_WEIGHTS: list[float] = [0.50, 0.30, 0.15, 0.05]

# ---------------------------------------------------------------------------
# Aircraft types and passenger capacity ranges
# ---------------------------------------------------------------------------
AIRCRAFT_TYPES: list[dict[str, Any]] = [
    {"type": "B737", "pax_min": 130, "pax_max": 189},
    {"type": "B777", "pax_min": 300, "pax_max": 350},
    {"type": "B787", "pax_min": 240, "pax_max": 330},
    {"type": "B757", "pax_min": 180, "pax_max": 230},
    {"type": "B767", "pax_min": 200, "pax_max": 290},
    {"type": "A320", "pax_min": 140, "pax_max": 186},
    {"type": "A321", "pax_min": 170, "pax_max": 220},
    {"type": "A319", "pax_min": 120, "pax_max": 156},
    {"type": "A220", "pax_min": 100, "pax_max": 140},
    {"type": "E175", "pax_min": 50, "pax_max": 88},
    {"type": "CRJ-900", "pax_min": 70, "pax_max": 90},
    {"type": "CRJ-700", "pax_min": 60, "pax_max": 78},
    {"type": "ERJ-145", "pax_min": 50, "pax_max": 50},
    {"type": "B738", "pax_min": 160, "pax_max": 189},
]

# Weighted distribution: narrowbodies dominate domestic flights
AIRCRAFT_WEIGHTS: list[float] = [
    0.22,
    0.04,
    0.06,
    0.05,
    0.03,
    0.15,
    0.10,
    0.06,
    0.04,
    0.10,
    0.06,
    0.04,
    0.02,
    0.03,
]

# ---------------------------------------------------------------------------
# Airport categories
# ---------------------------------------------------------------------------
AIRPORT_CATEGORIES: list[str] = [
    "large_hub",
    "medium_hub",
    "small_hub",
    "non_hub",
    "general_aviation",
]
AIRPORT_CATEGORY_WEIGHTS: list[float] = [0.45, 0.25, 0.15, 0.10, 0.05]

# ---------------------------------------------------------------------------
# Runway identifiers (common patterns)
# ---------------------------------------------------------------------------
RUNWAY_IDS: list[str] = [
    "09L/27R",
    "09R/27L",
    "10L/28R",
    "10R/28L",
    "04R/22L",
    "04L/22R",
    "08L/26R",
    "08R/26L",
    "13L/31R",
    "13R/31L",
    "17L/35R",
    "17R/35L",
    "01/19",
    "06/24",
    "14/32",
    "18/36",
]


class DOTFAAGenerator(BaseGenerator):
    """
    Generate synthetic DOT/FAA transportation data.

    Supports four domains controlled via the ``domain`` parameter on
    :meth:`generate_record` and :meth:`generate_batch`:

    - ``"flight_operations"`` (default) -- BTS On-Time Performance records
    - ``"safety_incident"`` -- FAA safety incident/event records
    - ``"traffic_statistics"`` -- T-100 traffic statistics records
    - ``"infrastructure"`` -- Airport and runway infrastructure records
    """

    def __init__(
        self,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Initialize the DOT/FAA generator.

        Args:
            seed: Random seed for reproducibility.
            start_date: Start date used by :meth:`random_datetime`.
            end_date: End date used by :meth:`random_datetime`.
        """
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)

        # Schema reflects the union of all four domains; active fields depend on domain.
        self._schema = {
            # Identifiers / metadata
            "record_id": "string",
            "data_domain": "string",
            "carrier_code": "string",
            "carrier_name": "string",
            "flight_number": "string",
            "origin_airport": "string",
            "destination_airport": "string",
            "departure_date": "string",
            "faa_region": "string",
            "report_year": "int",
            "report_month": "int",
            "load_time": "datetime",
            # Flight operations
            "scheduled_departure": "string",
            "actual_departure": "string",
            "delay_minutes": "int",
            "delay_cause": "string",
            "cancelled": "bool",
            "diverted": "bool",
            # Aircraft
            "aircraft_type": "string",
            "tail_number": "string",
            "passengers": "int",
            # Safety incident
            "incident_type": "string",
            "incident_severity": "string",
            # Infrastructure / weather
            "airport_category": "string",
            "runway_id": "string",
            "visibility_miles": "float",
            "wind_speed_knots": "int",
        }

    # ------------------------------------------------------------------
    # Abstract method implementation (default domain: flight_operations)
    # ------------------------------------------------------------------

    def generate_record(
        self, domain: DomainType = "flight_operations"
    ) -> dict[str, Any]:
        """
        Generate a single DOT/FAA record for the specified domain.

        Args:
            domain: ``"flight_operations"``, ``"safety_incident"``,
                    ``"traffic_statistics"``, or ``"infrastructure"``.

        Returns:
            Dictionary with domain-specific fields plus standard metadata columns.
        """
        if domain == "flight_operations":
            return self._generate_flight_operations_record()
        elif domain == "safety_incident":
            return self._generate_safety_incident_record()
        elif domain == "traffic_statistics":
            return self._generate_traffic_statistics_record()
        elif domain == "infrastructure":
            return self._generate_infrastructure_record()
        else:
            raise ValueError(
                f"Unknown domain '{domain}'. Must be one of: "
                "'flight_operations', 'safety_incident', 'traffic_statistics', 'infrastructure'."
            )

    # ------------------------------------------------------------------
    # Batch helper
    # ------------------------------------------------------------------

    def generate_batch(
        self,
        count: int = 1000,
        domain: DomainType = "flight_operations",
    ) -> list[dict[str, Any]]:
        """
        Generate a batch of DOT/FAA records for the specified domain.

        Args:
            count: Number of records to generate.
            domain: ``"flight_operations"``, ``"safety_incident"``,
                    ``"traffic_statistics"``, or ``"infrastructure"``.

        Returns:
            List of dictionaries containing ``count`` records.
        """
        return [self.generate_record(domain=domain) for _ in range(count)]

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _pick_carrier(self) -> dict[str, str]:
        """Select a carrier using weighted distribution."""
        idx = int(self.rng.choice(len(CARRIERS), p=CARRIER_WEIGHTS))
        return CARRIERS[idx]

    def _pick_airports(self) -> tuple[dict[str, str], dict[str, str]]:
        """Select distinct origin and destination airports."""
        indices = self.rng.choice(len(AIRPORTS), size=2, replace=False)
        return AIRPORTS[int(indices[0])], AIRPORTS[int(indices[1])]

    def _pick_aircraft(self) -> dict[str, Any]:
        """Select an aircraft type using weighted distribution."""
        idx = int(self.rng.choice(len(AIRCRAFT_TYPES), p=AIRCRAFT_WEIGHTS))
        return AIRCRAFT_TYPES[idx]

    def _generate_tail_number(self) -> str:
        """Generate a realistic US aircraft tail number."""
        digits = int(self.rng.integers(100, 99999))
        suffix = str(self.rng.choice(["", "A", "B", "C", "D", "E"]))
        return f"N{digits}{suffix}"

    def _generate_time(self, hour_min: int = 5, hour_max: int = 23) -> str:
        """Generate a random HH:MM time string."""
        hour = int(self.rng.integers(hour_min, hour_max + 1))
        minute = int(self.rng.integers(0, 60))
        return f"{hour:02d}:{minute:02d}"

    def _add_delay_to_time(self, time_str: str, delay_minutes: int) -> str:
        """Add delay minutes to a time string, wrapping at 24h."""
        parts = time_str.split(":")
        total_minutes = int(parts[0]) * 60 + int(parts[1]) + delay_minutes
        total_minutes = total_minutes % (24 * 60)
        return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"

    def _generate_departure_date(self) -> datetime:
        """Generate a random departure date within the configured range."""
        return self.random_datetime()

    def _build_common_fields(
        self,
        domain: str,
        carrier: dict[str, str],
        origin: dict[str, str],
        destination: dict[str, str],
        dep_dt: datetime,
    ) -> dict[str, Any]:
        """Build the common fields shared across all domains."""
        return {
            "record_id": self.generate_uuid(),
            "data_domain": domain,
            "carrier_code": carrier["code"],
            "carrier_name": carrier["name"],
            "origin_airport": origin["code"],
            "destination_airport": destination["code"],
            "departure_date": dep_dt.strftime("%Y-%m-%d"),
            "faa_region": origin.get(
                "region", str(self.rng.choice(FAA_REGIONS, p=FAA_REGION_WEIGHTS))
            ),
            "report_year": dep_dt.year,
            "report_month": dep_dt.month,
            "load_time": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------
    # Flight operations record builder
    # ------------------------------------------------------------------

    def _generate_flight_operations_record(self) -> dict[str, Any]:
        """Build a single BTS On-Time Performance-style flight operations record."""
        carrier = self._pick_carrier()
        origin, destination = self._pick_airports()
        dep_dt = self._generate_departure_date()
        aircraft = self._pick_aircraft()

        record = self._build_common_fields(
            "flight_operations", carrier, origin, destination, dep_dt
        )

        # Flight number
        record["flight_number"] = str(int(self.rng.integers(100, 9999)))

        # Scheduled and actual departure times
        scheduled = self._generate_time()
        record["scheduled_departure"] = scheduled

        # Determine delay cause and minutes
        delay_cause = self.weighted_choice(DELAY_CAUSES, DELAY_CAUSE_WEIGHTS)
        record["delay_cause"] = delay_cause

        if delay_cause == "none":
            # On-time: 0 delay or slightly early (represented as 0)
            record["delay_minutes"] = 0
            record["actual_departure"] = scheduled
        else:
            # Delay: realistic distribution skewed toward short delays
            delay_minutes = int(self.rng.exponential(scale=30.0)) + 1
            delay_minutes = min(delay_minutes, 600)  # Cap at 10 hours
            record["delay_minutes"] = delay_minutes
            record["actual_departure"] = self._add_delay_to_time(
                scheduled, delay_minutes
            )

        # Cancellation (5% of flights)
        cancelled = bool(self.rng.random() < 0.05)
        record["cancelled"] = cancelled
        if cancelled:
            record["actual_departure"] = None
            record["delay_minutes"] = None

        # Diversion (1% of non-cancelled flights)
        record["diverted"] = False if cancelled else bool(self.rng.random() < 0.01)

        # Aircraft details
        record["aircraft_type"] = aircraft["type"]
        record["tail_number"] = self._generate_tail_number()
        record["passengers"] = int(
            self.rng.integers(aircraft["pax_min"], aircraft["pax_max"] + 1)
        )

        # Safety incident fields are null for flight operations
        record["incident_type"] = None
        record["incident_severity"] = None

        # Airport and weather context
        record["airport_category"] = origin.get(
            "category",
            self.weighted_choice(AIRPORT_CATEGORIES, AIRPORT_CATEGORY_WEIGHTS),
        )
        record["runway_id"] = str(self.rng.choice(RUNWAY_IDS))
        record["visibility_miles"] = round(float(self.rng.uniform(1.0, 10.0)), 1)
        record["wind_speed_knots"] = int(self.rng.integers(0, 35))

        return self.add_metadata_columns(record)

    # ------------------------------------------------------------------
    # Safety incident record builder
    # ------------------------------------------------------------------

    def _generate_safety_incident_record(self) -> dict[str, Any]:
        """Build a single FAA safety incident record."""
        carrier = self._pick_carrier()
        origin, destination = self._pick_airports()
        dep_dt = self._generate_departure_date()
        aircraft = self._pick_aircraft()

        record = self._build_common_fields(
            "safety_incident", carrier, origin, destination, dep_dt
        )

        # Flight context
        record["flight_number"] = str(int(self.rng.integers(100, 9999)))
        record["scheduled_departure"] = self._generate_time()
        record["actual_departure"] = (
            None  # Incident records may not have actual departure
        )
        record["delay_minutes"] = None
        record["delay_cause"] = None
        record["cancelled"] = None
        record["diverted"] = bool(
            self.rng.random() < 0.15
        )  # Higher diversion rate for incidents

        # Aircraft details
        record["aircraft_type"] = aircraft["type"]
        record["tail_number"] = self._generate_tail_number()
        record["passengers"] = int(
            self.rng.integers(aircraft["pax_min"], aircraft["pax_max"] + 1)
        )

        # Incident-specific fields
        record["incident_type"] = self.weighted_choice(
            INCIDENT_TYPES, INCIDENT_TYPE_WEIGHTS
        )
        record["incident_severity"] = self.weighted_choice(
            INCIDENT_SEVERITIES, INCIDENT_SEVERITY_WEIGHTS
        )

        # Airport and weather context (weather often matters for incidents)
        record["airport_category"] = origin.get(
            "category",
            self.weighted_choice(AIRPORT_CATEGORIES, AIRPORT_CATEGORY_WEIGHTS),
        )
        record["runway_id"] = str(self.rng.choice(RUNWAY_IDS))
        # Incidents more likely in poor visibility
        record["visibility_miles"] = round(float(self.rng.uniform(0.0, 10.0)), 1)
        record["wind_speed_knots"] = int(self.rng.integers(0, 50))

        return self.add_metadata_columns(record)

    # ------------------------------------------------------------------
    # Traffic statistics record builder
    # ------------------------------------------------------------------

    def _generate_traffic_statistics_record(self) -> dict[str, Any]:
        """Build a single T-100 traffic statistics record."""
        carrier = self._pick_carrier()
        origin, destination = self._pick_airports()
        dep_dt = self._generate_departure_date()
        aircraft = self._pick_aircraft()

        record = self._build_common_fields(
            "traffic_statistics", carrier, origin, destination, dep_dt
        )

        # Traffic stats are aggregated -- no individual flight details
        record["flight_number"] = None
        record["scheduled_departure"] = None
        record["actual_departure"] = None
        record["delay_minutes"] = None
        record["delay_cause"] = None
        record["cancelled"] = None
        record["diverted"] = None

        # Aircraft and passenger aggregates
        record["aircraft_type"] = aircraft["type"]
        record["tail_number"] = None  # Not applicable for aggregate stats
        # Passenger count represents monthly segment total
        record["passengers"] = int(self.rng.integers(500, 50000))

        # No incident data for traffic stats
        record["incident_type"] = None
        record["incident_severity"] = None

        # Airport context (no weather for aggregate stats)
        record["airport_category"] = origin.get(
            "category",
            self.weighted_choice(AIRPORT_CATEGORIES, AIRPORT_CATEGORY_WEIGHTS),
        )
        record["runway_id"] = None
        record["visibility_miles"] = None
        record["wind_speed_knots"] = None

        return self.add_metadata_columns(record)

    # ------------------------------------------------------------------
    # Infrastructure record builder
    # ------------------------------------------------------------------

    def _generate_infrastructure_record(self) -> dict[str, Any]:
        """Build a single airport/runway infrastructure record."""
        carrier = self._pick_carrier()
        origin, destination = self._pick_airports()
        dep_dt = self._generate_departure_date()

        record = self._build_common_fields(
            "infrastructure", carrier, origin, destination, dep_dt
        )

        # Infrastructure records focus on airport, not flights
        record["flight_number"] = None
        record["scheduled_departure"] = None
        record["actual_departure"] = None
        record["delay_minutes"] = None
        record["delay_cause"] = None
        record["cancelled"] = None
        record["diverted"] = None

        # No aircraft-specific data
        record["aircraft_type"] = None
        record["tail_number"] = None
        record["passengers"] = None

        # No incident data
        record["incident_type"] = None
        record["incident_severity"] = None

        # Infrastructure-specific fields
        record["airport_category"] = origin.get(
            "category",
            self.weighted_choice(AIRPORT_CATEGORIES, AIRPORT_CATEGORY_WEIGHTS),
        )
        record["runway_id"] = str(self.rng.choice(RUNWAY_IDS))
        record["visibility_miles"] = None
        record["wind_speed_knots"] = None

        return self.add_metadata_columns(record)
