"""
IoT Device Fleet Simulator
==========================

Simulates telemetry messages from a heterogeneous fleet of casino-floor IoT
devices and routes each message through Azure IoT Hub conventions.

Device types supported
----------------------
- slot_machine    : SAS-protocol slot machine meters and status
- table_sensor    : Occupancy and chip-count sensors on gaming tables
- hvac_sensor     : HVAC zone environmental readings
- door_sensor     : Access-control door events (badge + direction)
- camera          : Video analytics frame metadata
- beacon          : BLE proximity beacon signals
- environmental   : Ambient noise, light, and smoke sensors

Typical usage
-------------
    from data_generation.generators.streaming.iot_device_simulator import IoTDeviceSimulator

    sim = IoTDeviceSimulator(num_devices=200, seed=42)

    # Single record for a given device type
    msg = sim.generate_record(device_type="hvac_sensor")

    # Batch of 500 slot-machine messages
    msgs = sim.generate_batch(count=500, device_type="slot_machine")

    # One message per device in the fleet
    snapshot = sim.generate_fleet_snapshot()
"""

from datetime import datetime, timedelta
from typing import Any

import numpy as np

from ..base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# Fleet configuration
# ---------------------------------------------------------------------------

DEVICE_CONFIG: dict[str, dict[str, Any]] = {
    "slot_machine": {
        "count": 500,
        "protocol": "MQTT",
        "telemetry_interval_sec": 5,
        "zones": ["North", "South", "East", "West", "VIP", "High Limit", "Penny"],
        "firmware_prefix": "SAS",
        "id_prefix": "SLOT",
        "id_format": "{prefix}-{n:04d}",
    },
    "table_sensor": {
        "count": 80,
        "protocol": "MQTT",
        "telemetry_interval_sec": 10,
        "zones": ["North", "South", "VIP", "High Limit"],
        "firmware_prefix": "TSN",
        "id_prefix": "TABLE",
        "id_format": "{prefix}-{n:03d}",
    },
    "hvac_sensor": {
        "count": 40,
        "protocol": "AMQP",
        "telemetry_interval_sec": 60,
        "zones": ["HVAC-ZONE-A", "HVAC-ZONE-B", "HVAC-ZONE-C", "HVAC-ZONE-D"],
        "firmware_prefix": "HVA",
        "id_prefix": "HVAC-ZONE",
        "id_format": "{prefix}-{letter}",
    },
    "door_sensor": {
        "count": 60,
        "protocol": "MQTT",
        "telemetry_interval_sec": 1,
        "zones": ["Entrance", "Exit", "VIP Access", "Staff Only", "Vault"],
        "firmware_prefix": "DRS",
        "id_prefix": "DOOR",
        "id_format": "{prefix}-{area}-{n:02d}",
    },
    "camera": {
        "count": 120,
        "protocol": "HTTPS",
        "telemetry_interval_sec": 30,
        "zones": ["North", "South", "East", "West", "VIP", "High Limit", "Entrance"],
        "firmware_prefix": "CAM",
        "id_prefix": "CAM",
        "id_format": "{prefix}-FLOOR-{n:02d}",
    },
    "beacon": {
        "count": 200,
        "protocol": "MQTT",
        "telemetry_interval_sec": 3,
        "zones": ["North", "South", "East", "West", "VIP", "Entrance", "Restroom"],
        "firmware_prefix": "BLE",
        "id_prefix": "BLE",
        "id_format": "{prefix}-{n:03d}",
    },
    "environmental": {
        "count": 50,
        "protocol": "MQTT",
        "telemetry_interval_sec": 15,
        "zones": ["North", "South", "East", "West", "Kitchen", "Bar", "Restroom"],
        "firmware_prefix": "ENV",
        "id_prefix": "ENV",
        "id_format": "{prefix}-{n:03d}",
    },
}

# Slot-machine game library for realistic telemetry
_SLOT_GAME_IDS = [
    "WMS-BBAR-01",
    "IGT-WOLF-02",
    "ARN-BUFF-03",
    "KNM-DRFT-04",
    "SGS-ZEUS-05",
    "EVR-FIRE-06",
    "IGT-CLEO-07",
    "ARN-QUEN-08",
]

_SLOT_STATUSES = ["ACTIVE", "IDLE", "ERROR", "MAINTENANCE", "DOOR_OPEN"]
_SLOT_STATUS_WEIGHTS = [0.70, 0.15, 0.05, 0.05, 0.05]

_TABLE_GAME_TYPES = [
    "Blackjack",
    "Baccarat",
    "Roulette",
    "Craps",
    "Poker",
    "Let It Ride",
]

_DOOR_AREAS = ["MAIN", "VIP", "STAFF", "VAULT", "CAGE", "KITCHEN", "SERVICE"]

_HVAC_ZONE_LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H"]


class IoTDeviceSimulator(BaseGenerator):
    """
    Simulate telemetry messages for a casino IoT device fleet.

    The fleet is pre-generated at construction time so that device identifiers,
    zones, and firmware versions are stable across calls—matching the behaviour
    of SlotMachineGenerator._generate_machines().
    """

    DEVICE_TYPES = list(DEVICE_CONFIG.keys())

    def __init__(
        self,
        num_devices: int = 100,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Initialise the simulator and pre-generate the device fleet.

        Args:
            num_devices: Approximate total fleet size. Each device type receives
                         a proportional slice of this budget (minimum 1 each).
            seed:        Random seed for reproducibility.
            start_date:  Earliest timestamp for generated telemetry.
            end_date:    Latest timestamp for generated telemetry.
        """
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)
        self.num_devices = num_devices

        self._schema = {
            "message_id": "string",
            "device_id": "string",
            "device_type": "string",
            "timestamp": "datetime",
            "protocol": "string",
            "hub_name": "string",
            "enqueued_time": "datetime",
            "correlation_id": "string",
            "content_type": "string",
            "properties": "object",
            "telemetry": "object",
            "location_zone": "string",
            "firmware_version": "string",
            "signal_strength_dbm": "int",
        }

        # Pre-generate the device fleet keyed by device_type
        self._fleet: dict[str, list[dict[str, Any]]] = self._generate_fleet()

    # ------------------------------------------------------------------
    # Fleet generation
    # ------------------------------------------------------------------

    def _generate_fleet(self) -> dict[str, list[dict[str, Any]]]:
        """Build a stable device registry for all device types."""
        total_configured = sum(cfg["count"] for cfg in DEVICE_CONFIG.values())
        fleet: dict[str, list[dict[str, Any]]] = {}

        for dtype, cfg in DEVICE_CONFIG.items():
            # Scale count proportionally to num_devices budget
            scaled = max(1, round(cfg["count"] * self.num_devices / total_configured))
            fleet[dtype] = self._generate_devices_of_type(dtype, scaled)

        return fleet

    def _generate_devices_of_type(
        self, device_type: str, count: int
    ) -> list[dict[str, Any]]:
        """Generate static device records for one device type."""
        cfg = DEVICE_CONFIG[device_type]
        zones: list[str] = cfg["zones"]
        cfg["firmware_prefix"]
        devices = []

        for n in range(1, count + 1):
            device_id = self._make_device_id(device_type, n, cfg)
            firmware_version = (
                f"v{np.random.randint(1, 4)}"
                f".{np.random.randint(0, 9)}"
                f".{np.random.randint(0, 9)}"
            )
            devices.append(
                {
                    "device_id": device_id,
                    "device_type": device_type.upper(),
                    "protocol": cfg["protocol"],
                    "location_zone": str(np.random.choice(zones)),
                    "firmware_version": firmware_version,
                    "telemetry_interval_sec": cfg["telemetry_interval_sec"],
                }
            )

        return devices

    @staticmethod
    def _make_device_id(device_type: str, n: int, cfg: dict[str, Any]) -> str:
        """Produce a human-readable device ID for the given type and index."""
        prefix = cfg["id_prefix"]
        fmt = cfg["id_format"]

        if device_type == "hvac_sensor":
            letter = _HVAC_ZONE_LETTERS[(n - 1) % len(_HVAC_ZONE_LETTERS)]
            return fmt.format(prefix=prefix, letter=letter, n=n)
        if device_type == "door_sensor":
            area = _DOOR_AREAS[(n - 1) % len(_DOOR_AREAS)]
            return fmt.format(prefix=prefix, area=area, n=n)
        return fmt.format(prefix=prefix, n=n)

    # ------------------------------------------------------------------
    # Core generation API
    # ------------------------------------------------------------------

    def generate_record(self, device_type: str = "slot_machine") -> dict[str, Any]:
        """
        Generate a single IoT telemetry message.

        Args:
            device_type: One of the 7 supported device types.

        Returns:
            Dict conforming to iot_telemetry_schema.json.
        """
        if device_type not in self._fleet:
            raise ValueError(
                f"Unknown device_type '{device_type}'. "
                f"Choose from: {self.DEVICE_TYPES}"
            )

        device = np.random.choice(self._fleet[device_type])  # type: ignore[arg-type]
        timestamp = self.random_datetime()
        enqueued_offset = int(np.random.uniform(50, 2000))  # ms
        enqueued_time = timestamp + timedelta(milliseconds=enqueued_offset)

        # Routing properties vary by type
        properties = self._make_properties(device_type, device)

        # Correlation ID present ~40 % of messages
        correlation_id = self.generate_uuid() if np.random.random() < 0.40 else None

        record: dict[str, Any] = {
            "message_id": self.generate_uuid(),
            "device_id": device["device_id"],
            "device_type": device["device_type"],
            "timestamp": timestamp.isoformat(),
            "protocol": device["protocol"],
            "hub_name": "casino-iot-hub-prod",
            "enqueued_time": enqueued_time.isoformat(),
            "correlation_id": correlation_id,
            "content_type": "application/json",
            "properties": properties,
            "telemetry": self._make_telemetry(device_type, device),
            "location_zone": device["location_zone"],
            "firmware_version": device["firmware_version"],
            "signal_strength_dbm": int(np.random.randint(-90, -29)),
        }

        return self.add_metadata_columns(record)

    def generate_batch(
        self,
        count: int = 1000,
        device_type: str = "slot_machine",
    ) -> list[dict[str, Any]]:
        """
        Generate a list of IoT telemetry messages.

        Args:
            count:       Number of messages to generate.
            device_type: Device type for all messages in the batch.

        Returns:
            List of dicts, each conforming to iot_telemetry_schema.json.
        """
        return [self.generate_record(device_type=device_type) for _ in range(count)]

    def generate_fleet_snapshot(self) -> list[dict[str, Any]]:
        """
        Generate exactly one current telemetry message per device in the fleet.

        Returns:
            List of dicts ordered by device_type then device_id.
        """
        snapshot: list[dict[str, Any]] = []
        for dtype, devices in self._fleet.items():
            for device in devices:
                # Patch timestamp to "now" for a live snapshot feel
                timestamp = datetime.now()
                enqueued_offset = int(np.random.uniform(50, 500))
                enqueued_time = timestamp + timedelta(milliseconds=enqueued_offset)

                properties = self._make_properties(dtype, device)
                correlation_id = (
                    self.generate_uuid() if np.random.random() < 0.40 else None
                )

                record: dict[str, Any] = {
                    "message_id": self.generate_uuid(),
                    "device_id": device["device_id"],
                    "device_type": device["device_type"],
                    "timestamp": timestamp.isoformat(),
                    "protocol": device["protocol"],
                    "hub_name": "casino-iot-hub-prod",
                    "enqueued_time": enqueued_time.isoformat(),
                    "correlation_id": correlation_id,
                    "content_type": "application/json",
                    "properties": properties,
                    "telemetry": self._make_telemetry(dtype, device),
                    "location_zone": device["location_zone"],
                    "firmware_version": device["firmware_version"],
                    "signal_strength_dbm": int(np.random.randint(-90, -29)),
                }
                snapshot.append(self.add_metadata_columns(record))

        return snapshot

    # ------------------------------------------------------------------
    # Telemetry payload builders
    # ------------------------------------------------------------------

    def _make_telemetry(
        self, device_type: str, device: dict[str, Any]
    ) -> dict[str, Any]:
        """Dispatch to the appropriate telemetry builder."""
        builders = {
            "slot_machine": self._telemetry_slot_machine,
            "table_sensor": self._telemetry_table_sensor,
            "hvac_sensor": self._telemetry_hvac_sensor,
            "door_sensor": self._telemetry_door_sensor,
            "camera": self._telemetry_camera,
            "beacon": self._telemetry_beacon,
            "environmental": self._telemetry_environmental,
        }
        return builders[device_type](device)

    def _telemetry_slot_machine(self, device: dict[str, Any]) -> dict[str, Any]:
        """Slot machine meter snapshot and status."""
        status = str(self.weighted_choice(_SLOT_STATUSES, _SLOT_STATUS_WEIGHTS))
        error_code = None
        if status == "ERROR":
            error_code = f"E{np.random.randint(1, 8):03d}"

        denomination = float(
            np.random.choice([0.01, 0.05, 0.25, 0.50, 1.00, 2.00, 5.00])
        )
        coin_in = round(float(np.random.uniform(10_000, 1_000_000)), 2)
        hold = np.random.uniform(0.04, 0.12)
        coin_out = round(coin_in * (1 - hold), 2)

        return {
            "machine_number": device["device_id"].split("-")[-1],
            "denomination": denomination,
            "game_id": str(np.random.choice(_SLOT_GAME_IDS)),
            "coin_in_meter": coin_in,
            "coin_out_meter": coin_out,
            "games_played_meter": int(coin_in / denomination / 3),
            "jackpot_meter": round(float(np.random.uniform(0, 50_000)), 2),
            "bill_in_meter": round(float(np.random.uniform(5_000, 500_000)), 2),
            "status": status,
            "error_code": error_code,
        }

    def _telemetry_table_sensor(self, device: dict[str, Any]) -> dict[str, Any]:
        """Table occupancy and game state."""
        players_seated = int(np.random.randint(0, 9))
        return {
            "table_id": device["device_id"],
            "game_type": str(np.random.choice(_TABLE_GAME_TYPES)),
            "players_seated": players_seated,
            "chips_on_table": round(float(np.random.uniform(0, 50_000)), 2),
            "active_hand": players_seated > 0,
        }

    def _telemetry_hvac_sensor(self, device: dict[str, Any]) -> dict[str, Any]:
        """HVAC zone environmental readings."""
        return {
            "zone_id": device["device_id"],
            "temperature": round(float(np.random.uniform(65.0, 80.0)), 1),
            "humidity": round(float(np.random.uniform(30.0, 70.0)), 1),
            "co2_level": int(np.random.randint(400, 2001)),
            "air_flow_cfm": round(float(np.random.uniform(200.0, 2000.0)), 1),
        }

    def _telemetry_door_sensor(self, device: dict[str, Any]) -> dict[str, Any]:
        """Door access-control event."""
        badge_id = f"BADGE-{np.random.randint(10000, 99999)}"
        area = device["location_zone"]
        # Higher-security areas have lower grant rate
        grant_rate = 0.95 if area not in ("Staff Only", "Vault") else 0.70
        return {
            "door_id": device["device_id"],
            "direction": str(np.random.choice(["IN", "OUT"])),
            "badge_id": badge_id,
            "access_granted": bool(np.random.random() < grant_rate),
            "area": area,
        }

    def _telemetry_camera(self, device: dict[str, Any]) -> dict[str, Any]:
        """Video analytics frame metadata."""
        objects_detected = int(np.random.randint(0, 20))
        return {
            "camera_id": device["device_id"],
            "frame_count": int(np.random.randint(1, 10_000_001)),
            "objects_detected": objects_detected,
            "motion_detected": bool(objects_detected > 0 and np.random.random() < 0.80),
            "recording": True,
        }

    def _telemetry_beacon(self, device: dict[str, Any]) -> dict[str, Any]:
        """BLE beacon proximity signal."""
        rssi = int(np.random.randint(-100, -29))
        # Rough distance estimate: RSSI ~ -59 at 1 m, path-loss exponent 2.5
        distance = round(10 ** ((-59 - rssi) / (10 * 2.5)), 2)
        return {
            "beacon_id": device["device_id"],
            "uuid": self.generate_uuid(),
            "major": int(np.random.randint(1, 65536)),
            "minor": int(np.random.randint(1, 65536)),
            "rssi": rssi,
            "estimated_distance_m": distance,
        }

    def _telemetry_environmental(self, device: dict[str, Any]) -> dict[str, Any]:
        """Ambient noise, light, and smoke sensor readings."""
        return {
            "sensor_id": device["device_id"],
            "noise_level_db": round(float(np.random.uniform(40.0, 100.0)), 1),
            "light_level_lux": round(float(np.random.uniform(50.0, 1000.0)), 1),
            "smoke_detected": bool(np.random.random() < 0.005),
        }

    # ------------------------------------------------------------------
    # Routing properties
    # ------------------------------------------------------------------

    @staticmethod
    def _make_properties(
        device_type: str, device: dict[str, Any]
    ) -> dict[str, str] | None:
        """Return IoT Hub message routing properties or None (~20 % of messages)."""
        if np.random.random() < 0.20:
            return None
        return {
            "deviceType": device["device_type"],
            "locationZone": device["location_zone"],
            "routingKey": f"casino.iot.{device_type}",
        }

    # ------------------------------------------------------------------
    # Inspection helpers
    # ------------------------------------------------------------------

    def get_fleet(self) -> dict[str, list[dict[str, Any]]]:
        """Return the pre-generated device registry."""
        return self._fleet

    def fleet_summary(self) -> dict[str, int]:
        """Return count of devices per type."""
        return {dtype: len(devices) for dtype, devices in self._fleet.items()}
