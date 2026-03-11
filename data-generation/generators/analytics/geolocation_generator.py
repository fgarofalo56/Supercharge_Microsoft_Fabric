"""
Geolocation Generator
=====================

Generates synthetic geolocation analytics events for a casino resort environment.

Records represent location pings, geofence crossings, and proximity-triggered events
from various device types across a Las Vegas casino resort campus:

- patron_app: Guest mobile application check-ins and movement
- employee_badge: Staff BLE badge location tracking
- asset_tag: Equipment and high-value asset tracking
- vehicle_gps: Casino-owned vehicle fleet GPS
- shuttle_tracker: Resort shuttle route tracking
- valet_tag: Valet vehicle location tags

Coordinates are centered on the Las Vegas Strip area (~36.17, -115.14) with small
random offsets to simulate movement across a resort campus. Indoor locations
include floor-level and zone information for multi-story hotel towers.

Data shapes are designed for integration with H3 spatial indexing, geofence
analytics, and real-time patron movement dashboards in Microsoft Fabric.
"""

from datetime import datetime
from typing import Any

import numpy as np

from ..base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# Las Vegas base coordinates
# ---------------------------------------------------------------------------
BASE_LATITUDE = 36.1699
BASE_LONGITUDE = -115.1398
COORDINATE_OFFSET_RANGE = 0.01  # ~1.1 km radius

# ---------------------------------------------------------------------------
# Device configuration
# ---------------------------------------------------------------------------
DEVICE_TYPES = [
    "patron_app",
    "employee_badge",
    "asset_tag",
    "vehicle_gps",
    "shuttle_tracker",
    "valet_tag",
]
DEVICE_TYPE_WEIGHTS = [0.40, 0.25, 0.15, 0.08, 0.07, 0.05]

NUM_DEVICES = 200

# ---------------------------------------------------------------------------
# Source system configuration
# ---------------------------------------------------------------------------
SOURCE_SYSTEMS = [
    "gps",
    "wifi_triangulation",
    "ble_trilateration",
    "uwb",
    "hybrid",
]
SOURCE_SYSTEM_WEIGHTS = [0.35, 0.25, 0.20, 0.10, 0.10]

# Accuracy ranges (meters) by source system
ACCURACY_RANGES: dict[str, tuple[float, float]] = {
    "gps":                (3.0, 15.0),
    "wifi_triangulation": (5.0, 30.0),
    "ble_trilateration":  (1.0, 5.0),
    "uwb":                (0.1, 1.0),
    "hybrid":             (1.0, 10.0),
}

# ---------------------------------------------------------------------------
# Geofence configuration
# ---------------------------------------------------------------------------
NUM_GEOFENCES = 20

GEOFENCE_NAMES = [
    "Casino Main Floor",
    "Casino VIP Salon",
    "Parking Lot A",
    "Parking Lot B",
    "Parking Lot C",
    "Parking Lot D",
    "Pool Area",
    "Valet Zone",
    "Employee Parking",
    "VIP Entrance",
    "Loading Dock",
    "Hotel Tower North",
    "Hotel Tower South",
    "Convention Center",
    "Restaurant Row",
    "Sports Book Entrance",
    "Night Club Entry",
    "Spa & Fitness Center",
    "Retail Promenade",
    "Shuttle Pickup Zone",
]

GEOFENCE_EVENTS = ["enter", "exit", "dwell"]
GEOFENCE_EVENT_WEIGHTS = [0.35, 0.30, 0.35]

# ---------------------------------------------------------------------------
# Points of interest
# ---------------------------------------------------------------------------
POI_NAMES = [
    "Main Entrance",
    "Valet Stand",
    "Slot Floor",
    "High Limit Room",
    "Poker Room",
    "Sports Book",
    "Steakhouse",
    "Buffet",
    "Night Club",
    "Hotel Front Desk",
    "Pool Bar",
    "Gift Shop",
]

# ---------------------------------------------------------------------------
# Indoor zone configuration
# ---------------------------------------------------------------------------
INDOOR_ZONES = [
    "Lobby",
    "Main Gaming Floor",
    "High Limit Salon",
    "Poker Room",
    "Sports Book Lounge",
    "VIP Lounge",
    "Restaurant Level",
    "Spa Level",
    "Convention Hall A",
    "Convention Hall B",
    "Back of House Corridor",
    "Security Operations Center",
    "Hotel Hallway",
    "Elevator Bank",
    "Retail Concourse",
]

# ---------------------------------------------------------------------------
# Proximity trigger configuration
# ---------------------------------------------------------------------------
PROXIMITY_TRIGGERS = [
    "marketing_push",
    "loyalty_offer",
    "vip_greeting",
    "safety_alert",
    "staff_dispatch",
]


class GeolocationGenerator(BaseGenerator):
    """
    Generate synthetic geolocation analytics events for a casino resort.

    Each record represents a location ping from a tracked device (patron app,
    employee badge, asset tag, etc.) within a Las Vegas casino resort campus.
    Records include GPS coordinates, geofence interactions, indoor positioning,
    and proximity-triggered events.

    Example usage::

        gen = GeolocationGenerator(seed=42)
        record = gen.generate_record()
        batch = gen.generate_batch(count=5000)
    """

    def __init__(
        self,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Initialize the geolocation generator.

        Args:
            seed: Random seed for reproducibility.
            start_date: Start date used by :meth:`random_datetime`.
            end_date: End date used by :meth:`random_datetime`.
        """
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)

        # Pre-generate device fleet: device_id -> device_type
        self._device_fleet: dict[str, str] = {}
        for i in range(NUM_DEVICES):
            dev_id = f"DEV-{np.random.randint(10_000_000, 99_999_999):08d}"
            dev_type = str(self.weighted_choice(DEVICE_TYPES, DEVICE_TYPE_WEIGHTS))
            self._device_fleet[dev_id] = dev_type
        self._device_ids = list(self._device_fleet.keys())

        # Pre-generate geofence lookup: geofence_id -> geofence_name
        self._geofences: dict[str, str] = {}
        for i in range(NUM_GEOFENCES):
            gf_id = f"GF-{i + 1:03d}"
            self._geofences[gf_id] = GEOFENCE_NAMES[i]
        self._geofence_ids = list(self._geofences.keys())

        # Schema definition
        self._schema = {
            "event_id": "string",
            "device_id": "string",
            "device_type": "string",
            "timestamp": "datetime",
            "latitude": "float",
            "longitude": "float",
            "altitude_meters": "float",
            "accuracy_meters": "float",
            "speed_mps": "float",
            "heading_degrees": "float",
            "h3_index": "string",
            "geofence_id": "string",
            "geofence_name": "string",
            "geofence_event": "string",
            "geofence_dwell_seconds": "int",
            "poi_name": "string",
            "poi_distance_meters": "float",
            "floor_level": "int",
            "indoor_zone": "string",
            "proximity_trigger": "string",
            "source_system": "string",
            "battery_level": "int",
            "load_time": "datetime",
        }

    # ------------------------------------------------------------------
    # Abstract method implementation
    # ------------------------------------------------------------------

    def generate_record(self) -> dict[str, Any]:
        """
        Generate a single geolocation analytics event.

        Returns:
            Dictionary with geolocation event fields plus standard metadata columns.
        """
        # Select a device from the pre-generated fleet
        device_id = str(np.random.choice(self._device_ids))
        device_type = self._device_fleet[device_id]

        # Source system and accuracy
        source_system = str(self.weighted_choice(SOURCE_SYSTEMS, SOURCE_SYSTEM_WEIGHTS))
        acc_low, acc_high = ACCURACY_RANGES[source_system]
        accuracy_meters = round(float(np.random.uniform(acc_low, acc_high)), 2)

        # Determine indoor vs outdoor (~50% each)
        is_indoor = bool(np.random.random() < 0.50)

        # Coordinates: Las Vegas base + small random offset
        latitude = round(
            BASE_LATITUDE + float(np.random.uniform(-COORDINATE_OFFSET_RANGE, COORDINATE_OFFSET_RANGE)),
            6,
        )
        longitude = round(
            BASE_LONGITUDE + float(np.random.uniform(-COORDINATE_OFFSET_RANGE, COORDINATE_OFFSET_RANGE)),
            6,
        )

        # Altitude: outdoor only
        altitude_meters: float | None = None
        if not is_indoor:
            altitude_meters = round(float(np.random.uniform(600.0, 650.0)), 1)

        # Speed: stationary (~40%), walking, or vehicle
        speed_mps: float | None
        heading_degrees: float | None
        speed_roll = float(np.random.random())
        if speed_roll < 0.40:
            # Stationary
            speed_mps = 0.0
            heading_degrees = None
        elif speed_roll < 0.75:
            # Walking pace (0–2 m/s)
            speed_mps = round(float(np.random.uniform(0.0, 2.0)), 2)
            heading_degrees = round(float(np.random.uniform(0.0, 360.0)), 1)
        else:
            # Vehicle speed (5–15 m/s for shuttles/valet, up to 30 m/s)
            if device_type in ("vehicle_gps", "shuttle_tracker", "valet_tag"):
                speed_mps = round(float(np.random.uniform(5.0, 30.0)), 2)
            else:
                speed_mps = round(float(np.random.uniform(2.0, 15.0)), 2)
            heading_degrees = round(float(np.random.uniform(0.0, 360.0)), 1)

        # H3 index: present ~70% of the time (15-character hex string)
        h3_index: str | None = None
        if np.random.random() < 0.70:
            h3_raw = np.random.randint(0, 2**60, dtype=np.int64)
            h3_index = f"{h3_raw:015x}"

        # Geofence interaction: ~40% of events involve a geofence
        geofence_id: str | None = None
        geofence_name: str | None = None
        geofence_event: str | None = None
        geofence_dwell_seconds: int | None = None
        if np.random.random() < 0.40:
            geofence_id = str(np.random.choice(self._geofence_ids))
            geofence_name = self._geofences[geofence_id]
            geofence_event = str(self.weighted_choice(GEOFENCE_EVENTS, GEOFENCE_EVENT_WEIGHTS))
            if geofence_event == "dwell":
                geofence_dwell_seconds = int(np.random.randint(30, 7201))

        # Nearest POI
        poi_name = str(np.random.choice(POI_NAMES))
        poi_distance_meters = round(float(np.random.uniform(1.0, 500.0)), 1)

        # Indoor positioning
        floor_level: int | None = None
        indoor_zone: str | None = None
        if is_indoor:
            floor_level = int(np.random.randint(1, 31))
            indoor_zone = str(np.random.choice(INDOOR_ZONES))

        # Proximity trigger: ~15% of patron_app events
        proximity_trigger: str | None = None
        if device_type == "patron_app" and np.random.random() < 0.15:
            proximity_trigger = str(np.random.choice(PROXIMITY_TRIGGERS))

        # Battery level: present ~80% of time
        battery_level: int | None = None
        if np.random.random() < 0.80:
            battery_level = int(np.random.randint(5, 101))

        record: dict[str, Any] = {
            "event_id": self.generate_uuid(),
            "device_id": device_id,
            "device_type": device_type,
            "timestamp": self.random_datetime().isoformat(),
            "latitude": latitude,
            "longitude": longitude,
            "altitude_meters": altitude_meters,
            "accuracy_meters": accuracy_meters,
            "speed_mps": speed_mps,
            "heading_degrees": heading_degrees,
            "h3_index": h3_index,
            "geofence_id": geofence_id,
            "geofence_name": geofence_name,
            "geofence_event": geofence_event,
            "geofence_dwell_seconds": geofence_dwell_seconds,
            "poi_name": poi_name,
            "poi_distance_meters": poi_distance_meters,
            "floor_level": floor_level,
            "indoor_zone": indoor_zone,
            "proximity_trigger": proximity_trigger,
            "source_system": source_system,
            "battery_level": battery_level,
            "load_time": datetime.now().isoformat(),
        }

        return self.add_metadata_columns(record)

    # ------------------------------------------------------------------
    # Batch helper
    # ------------------------------------------------------------------

    def generate_batch(self, count: int = 1000) -> list[dict[str, Any]]:
        """
        Generate a batch of geolocation analytics events.

        Args:
            count: Number of records to generate.

        Returns:
            List of dictionaries, each containing a single geolocation event.
        """
        return [self.generate_record() for _ in range(count)]
