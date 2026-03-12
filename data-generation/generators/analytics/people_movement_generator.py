"""
People Movement Generator
=========================

Generates synthetic people movement / foot traffic events for a casino
environment, covering zone-level occupancy counts, dwell times, queue
detection, and per-sensor metadata.

Each record represents a single sensor reading at a point in time.  Sensor
types span Wi-Fi probes, BLE beacons, camera counters, infrared gates,
pressure mats, and LiDAR units distributed across 30 casino zones on up to
three floors.

Data shapes mirror the ``movement_event_schema.json`` schema so generated
records can feed directly into Bronze-layer ingestion pipelines.
"""

import hashlib
import string
from datetime import datetime, timedelta
from typing import Any

import numpy as np

from ..base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# Sensor type distribution
# ---------------------------------------------------------------------------
SENSOR_TYPES = [
    "wifi_probe",
    "ble_beacon",
    "camera_count",
    "infrared",
    "pressure_mat",
    "lidar",
]

SENSOR_TYPE_WEIGHTS = [0.30, 0.25, 0.20, 0.10, 0.10, 0.05]

# ---------------------------------------------------------------------------
# Movement direction distribution
# ---------------------------------------------------------------------------
DIRECTIONS = ["entering", "exiting", "stationary", "passing_through"]
DIRECTION_WEIGHTS = [0.30, 0.25, 0.25, 0.20]

# ---------------------------------------------------------------------------
# Floor level distribution (most activity on floor 1)
# ---------------------------------------------------------------------------
FLOOR_LEVELS = [1, 2, 3]
FLOOR_LEVEL_WEIGHTS = [0.60, 0.30, 0.10]

# ---------------------------------------------------------------------------
# Heat map grid dimensions (columns A-J, rows 1-10)
# ---------------------------------------------------------------------------
HEAT_MAP_COLUMNS = list(string.ascii_uppercase[:10])  # A-J
HEAT_MAP_ROWS = list(range(1, 11))  # 1-10

# ---------------------------------------------------------------------------
# Zone configuration
#
# Each key is a zone name.  Values:
#   capacity        – maximum occupancy for the zone
#   person_count    – (low, high) range for person_count readings
#   dwell_range     – (low, high) seconds for typical dwell time
#   floor           – default floor level for the zone
#   queue_eligible  – True if queue detection is meaningful (cage, restaurant)
# ---------------------------------------------------------------------------
_ZONE_CONFIG: dict[str, dict[str, Any]] = {
    "Main Slot Floor": {
        "capacity": 400,
        "person_count": (20, 200),
        "dwell_range": (300, 3600),
        "floor": 1,
        "queue_eligible": False,
    },
    "High-Limit Slots": {
        "capacity": 60,
        "person_count": (5, 40),
        "dwell_range": (600, 3600),
        "floor": 1,
        "queue_eligible": False,
    },
    "Poker Room": {
        "capacity": 120,
        "person_count": (10, 80),
        "dwell_range": (1800, 7200),
        "floor": 1,
        "queue_eligible": False,
    },
    "Blackjack Pit A": {
        "capacity": 100,
        "person_count": (10, 70),
        "dwell_range": (600, 3600),
        "floor": 1,
        "queue_eligible": False,
    },
    "Blackjack Pit B": {
        "capacity": 100,
        "person_count": (10, 70),
        "dwell_range": (600, 3600),
        "floor": 1,
        "queue_eligible": False,
    },
    "Craps Area": {
        "capacity": 80,
        "person_count": (8, 50),
        "dwell_range": (600, 3600),
        "floor": 1,
        "queue_eligible": False,
    },
    "Roulette Section": {
        "capacity": 60,
        "person_count": (5, 35),
        "dwell_range": (300, 2400),
        "floor": 1,
        "queue_eligible": False,
    },
    "VIP Lounge": {
        "capacity": 30,
        "person_count": (2, 20),
        "dwell_range": (1200, 5400),
        "floor": 2,
        "queue_eligible": False,
    },
    "Sports Book": {
        "capacity": 150,
        "person_count": (15, 100),
        "dwell_range": (900, 5400),
        "floor": 1,
        "queue_eligible": False,
    },
    "Buffet": {
        "capacity": 200,
        "person_count": (10, 80),
        "dwell_range": (1200, 5400),
        "floor": 1,
        "queue_eligible": True,
    },
    "Steakhouse": {
        "capacity": 80,
        "person_count": (10, 60),
        "dwell_range": (2400, 5400),
        "floor": 2,
        "queue_eligible": True,
    },
    "Main Bar": {
        "capacity": 60,
        "person_count": (5, 40),
        "dwell_range": (600, 3600),
        "floor": 1,
        "queue_eligible": True,
    },
    "Cage Window 1": {
        "capacity": 20,
        "person_count": (2, 15),
        "dwell_range": (60, 600),
        "floor": 1,
        "queue_eligible": True,
    },
    "Cage Window 2": {
        "capacity": 20,
        "person_count": (2, 15),
        "dwell_range": (60, 600),
        "floor": 1,
        "queue_eligible": True,
    },
    "Cage Window 3": {
        "capacity": 20,
        "person_count": (2, 15),
        "dwell_range": (60, 600),
        "floor": 1,
        "queue_eligible": True,
    },
    "Cage Window 4": {
        "capacity": 20,
        "person_count": (2, 15),
        "dwell_range": (60, 600),
        "floor": 1,
        "queue_eligible": True,
    },
    "Cage Window 5": {
        "capacity": 20,
        "person_count": (2, 15),
        "dwell_range": (60, 600),
        "floor": 1,
        "queue_eligible": True,
    },
    "Entrance North": {
        "capacity": 50,
        "person_count": (5, 50),
        "dwell_range": (5, 30),
        "floor": 1,
        "queue_eligible": False,
    },
    "Entrance South": {
        "capacity": 50,
        "person_count": (5, 50),
        "dwell_range": (5, 30),
        "floor": 1,
        "queue_eligible": False,
    },
    "Entrance Valet": {
        "capacity": 40,
        "person_count": (5, 30),
        "dwell_range": (5, 30),
        "floor": 1,
        "queue_eligible": False,
    },
    "Elevator Bank A": {
        "capacity": 25,
        "person_count": (2, 15),
        "dwell_range": (10, 120),
        "floor": 1,
        "queue_eligible": False,
    },
    "Elevator Bank B": {
        "capacity": 25,
        "person_count": (2, 15),
        "dwell_range": (10, 120),
        "floor": 2,
        "queue_eligible": False,
    },
    "Hotel Check-In": {
        "capacity": 40,
        "person_count": (3, 25),
        "dwell_range": (120, 900),
        "floor": 1,
        "queue_eligible": True,
    },
    "Pool Deck": {
        "capacity": 100,
        "person_count": (5, 60),
        "dwell_range": (1800, 7200),
        "floor": 3,
        "queue_eligible": False,
    },
    "Convention Hall A": {
        "capacity": 300,
        "person_count": (10, 150),
        "dwell_range": (1800, 7200),
        "floor": 2,
        "queue_eligible": False,
    },
    "Convention Hall B": {
        "capacity": 300,
        "person_count": (10, 150),
        "dwell_range": (1800, 7200),
        "floor": 2,
        "queue_eligible": False,
    },
    "Back of House Corridor": {
        "capacity": 30,
        "person_count": (1, 10),
        "dwell_range": (10, 300),
        "floor": 1,
        "queue_eligible": False,
    },
    "Baccarat Salon": {
        "capacity": 40,
        "person_count": (2, 25),
        "dwell_range": (900, 5400),
        "floor": 2,
        "queue_eligible": False,
    },
    "Race Book": {
        "capacity": 60,
        "person_count": (5, 35),
        "dwell_range": (600, 3600),
        "floor": 1,
        "queue_eligible": False,
    },
}

# Ordered zone names and their IDs, derived at import time
_ZONE_NAMES: list[str] = list(_ZONE_CONFIG.keys())
_ZONE_IDS: list[str] = [f"Z-{i:03d}" for i in range(1, len(_ZONE_NAMES) + 1)]
_ZONE_ID_TO_NAME: dict[str, str] = dict(zip(_ZONE_IDS, _ZONE_NAMES, strict=False))

# Number of pre-generated sensors
NUM_SENSORS = 80


class PeopleMovementGenerator(BaseGenerator):
    """
    Generate synthetic people movement / foot traffic events for a casino.

    Each record represents a single sensor reading capturing zone occupancy,
    dwell time, optional queue information, and sensor-specific metadata
    (MAC hash for Wi-Fi probes, signal strength for wireless sensors, battery
    level for BLE beacons).

    Sensors are pre-assigned to zones during initialization so that
    successive calls to :meth:`generate_record` produce a coherent
    distribution of readings across the casino floor plan.
    """

    def __init__(
        self,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Initialize the people movement generator.

        Args:
            seed: Random seed for reproducibility.
            start_date: Start date used by :meth:`random_datetime`.
            end_date: End date used by :meth:`random_datetime`.
        """
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)

        # Pre-generate sensors and assign each to a zone
        self._sensors: list[dict[str, str]] = []
        for i in range(1, NUM_SENSORS + 1):
            sensor_id = f"SENS-{i:04d}"
            zone_idx = (i - 1) % len(_ZONE_IDS)
            zone_id = _ZONE_IDS[zone_idx]
            sensor_type = str(self.weighted_choice(SENSOR_TYPES, SENSOR_TYPE_WEIGHTS))
            self._sensors.append(
                {
                    "sensor_id": sensor_id,
                    "zone_id": zone_id,
                    "sensor_type": sensor_type,
                }
            )

        # Pre-generate calibration dates for each sensor (80 % present)
        self._calibration_dates: dict[str, str | None] = {}
        for s in self._sensors:
            if np.random.random() < 0.80:
                days_ago = int(np.random.randint(1, 365))
                cal_date = (datetime.now() - timedelta(days=days_ago)).strftime(
                    "%Y-%m-%d"
                )
                self._calibration_dates[s["sensor_id"]] = cal_date
            else:
                self._calibration_dates[s["sensor_id"]] = None

        # Schema definition
        self._schema = {
            "event_id": "string",
            "sensor_id": "string",
            "sensor_type": "string",
            "zone_id": "string",
            "zone_name": "string",
            "timestamp": "datetime",
            "person_count": "int",
            "direction": "string",
            "dwell_time_seconds": "float",
            "velocity_mps": "float",
            "x_coordinate": "float",
            "y_coordinate": "float",
            "floor_level": "int",
            "heat_map_cell": "string",
            "occupancy_percentage": "float",
            "queue_detected": "boolean",
            "queue_length": "int",
            "queue_wait_minutes": "float",
            "device_mac_hash": "string",
            "signal_strength_dbm": "int",
            "battery_level": "int",
            "calibration_date": "string",
            "load_time": "datetime",
        }

    # ------------------------------------------------------------------
    # Abstract method implementation
    # ------------------------------------------------------------------

    def generate_record(self) -> dict[str, Any]:
        """
        Generate a single people movement event record.

        Returns:
            Dictionary with movement event fields plus standard metadata columns.
        """
        # Pick a random sensor (carries zone assignment and type)
        sensor_idx = int(np.random.randint(0, len(self._sensors)))
        sensor = self._sensors[sensor_idx]
        sensor_id = sensor["sensor_id"]
        sensor_type = sensor["sensor_type"]
        zone_id = sensor["zone_id"]
        zone_name = _ZONE_ID_TO_NAME[zone_id]
        zone_cfg = _ZONE_CONFIG[zone_name]

        # Timestamp
        timestamp = self.random_datetime()

        # Person count (zone-dependent range)
        pc_low, pc_high = zone_cfg["person_count"]
        person_count = int(np.random.randint(pc_low, pc_high + 1))

        # Direction
        direction = str(self.weighted_choice(DIRECTIONS, DIRECTION_WEIGHTS))

        # Dwell time (zone-dependent range)
        dw_low, dw_high = zone_cfg["dwell_range"]
        dwell_time_seconds = round(float(np.random.uniform(dw_low, dw_high)), 1)

        # Velocity – normally distributed around typical walking speed
        velocity_raw = float(np.random.normal(1.2, 0.4))
        velocity_mps = round(max(0.0, min(velocity_raw, 2.5)), 2)

        # Coordinates (normalized 0-100 within zone)
        x_coordinate = round(float(np.random.uniform(0.0, 100.0)), 2)
        y_coordinate = round(float(np.random.uniform(0.0, 100.0)), 2)

        # Floor level (use zone default most of the time)
        floor_level = zone_cfg["floor"]

        # Heat map cell
        col = str(np.random.choice(HEAT_MAP_COLUMNS))
        row = int(np.random.choice(HEAT_MAP_ROWS))
        heat_map_cell = f"{col}{row}"

        # Occupancy percentage
        capacity = zone_cfg["capacity"]
        occupancy_percentage = round(min(person_count / capacity * 100.0, 100.0), 1)

        # Queue detection
        queue_detected: bool | None = False
        queue_length: int | None = None
        queue_wait_minutes: float | None = None

        if (
            zone_cfg["queue_eligible"] and occupancy_percentage > 70.0
        ) or np.random.random() < 0.05:
            queue_detected = True

        if queue_detected:
            queue_length = int(np.random.randint(2, 26))
            queue_wait_minutes = round(float(np.random.uniform(1.0, 45.0)), 1)

        # Sensor-specific fields
        device_mac_hash: str | None = None
        signal_strength_dbm: int | None = None
        battery_level: int | None = None

        if sensor_type == "wifi_probe":
            raw_mac = self.faker.mac_address()
            device_mac_hash = hashlib.sha256(raw_mac.encode()).hexdigest()[:12]
            signal_strength_dbm = int(np.random.randint(-90, -29))
        elif sensor_type == "ble_beacon":
            signal_strength_dbm = int(np.random.randint(-90, -29))
            battery_level = int(np.random.randint(10, 101))

        # Calibration date from pre-generated map
        calibration_date = self._calibration_dates[sensor_id]

        record: dict[str, Any] = {
            "event_id": self.generate_uuid(),
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "zone_id": zone_id,
            "zone_name": zone_name,
            "timestamp": timestamp.isoformat(),
            "person_count": person_count,
            "direction": direction,
            "dwell_time_seconds": dwell_time_seconds,
            "velocity_mps": velocity_mps,
            "x_coordinate": x_coordinate,
            "y_coordinate": y_coordinate,
            "floor_level": floor_level,
            "heat_map_cell": heat_map_cell,
            "occupancy_percentage": occupancy_percentage,
            "queue_detected": queue_detected,
            "queue_length": queue_length,
            "queue_wait_minutes": queue_wait_minutes,
            "device_mac_hash": device_mac_hash,
            "signal_strength_dbm": signal_strength_dbm,
            "battery_level": battery_level,
            "calibration_date": calibration_date,
            "load_time": datetime.now().isoformat(),
        }

        return self.add_metadata_columns(record)

    # ------------------------------------------------------------------
    # Batch helper
    # ------------------------------------------------------------------

    def generate_batch(self, count: int = 1000) -> list[dict[str, Any]]:
        """
        Generate a batch of people movement event records.

        Args:
            count: Number of records to generate.

        Returns:
            List of dictionaries, each containing one movement event record.
        """
        return [self.generate_record() for _ in range(count)]
