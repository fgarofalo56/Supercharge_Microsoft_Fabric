"""
Unit tests for IoTDeviceSimulator.

Covers all seven casino-floor device types:
- slot_machine  : SAS-protocol meters and status
- table_sensor  : Occupancy and chip-count readings
- hvac_sensor   : HVAC zone environmental readings
- door_sensor   : Access-control door events
- camera        : Video analytics frame metadata
- beacon        : BLE proximity beacon signals
- environmental : Ambient noise, light, and smoke readings
"""

from generators.streaming.iot_device_simulator import (
    DEVICE_CONFIG,
)

_VALID_PROTOCOLS = {"MQTT", "AMQP", "HTTPS"}

_DEVICE_TYPES = list(DEVICE_CONFIG.keys())

# Required slot-machine telemetry fields (from _telemetry_slot_machine)
_SLOT_TELEMETRY_FIELDS = {
    "machine_number",
    "denomination",
    "game_id",
    "coin_in_meter",
    "coin_out_meter",
    "games_played_meter",
    "jackpot_meter",
    "bill_in_meter",
    "status",
}


class TestIoTDeviceSimulator:
    """Tests for IoTDeviceSimulator covering all device types and fleet operations."""

    # ------------------------------------------------------------------
    # Basic field presence
    # ------------------------------------------------------------------

    def test_generate_slot_machine_record(self, iot_simulator):
        """Generate a slot machine record and assert all required top-level fields exist."""
        record = iot_simulator.generate_record(device_type="slot_machine")

        assert record is not None
        assert "message_id" in record, "message_id field missing"
        assert "device_id" in record, "device_id field missing"
        assert "device_type" in record, "device_type field missing"
        assert "timestamp" in record, "timestamp field missing"
        assert "telemetry" in record, "telemetry field missing"

    # ------------------------------------------------------------------
    # device_type enum
    # ------------------------------------------------------------------

    def test_device_type_matches(self, iot_simulator):
        """Generating with device_type='slot_machine' must yield device_type='SLOT_MACHINE'."""
        record = iot_simulator.generate_record(device_type="slot_machine")

        assert record["device_type"] == "SLOT_MACHINE", (
            f"Expected SLOT_MACHINE, got {record['device_type']}"
        )

    def test_all_device_types(self, iot_simulator):
        """Each of the seven device types must produce a valid record with the correct enum."""
        expected_enums = {
            "slot_machine": "SLOT_MACHINE",
            "table_sensor": "TABLE_SENSOR",
            "hvac_sensor": "HVAC_SENSOR",
            "door_sensor": "DOOR_SENSOR",
            "camera": "CAMERA",
            "beacon": "BEACON",
            "environmental": "ENVIRONMENTAL",
        }
        for device_key, expected_enum in expected_enums.items():
            record = iot_simulator.generate_record(device_type=device_key)
            assert record is not None, (
                f"No record returned for device_type='{device_key}'"
            )
            assert record["device_type"] == expected_enum, (
                f"device_type='{device_key}' should yield enum '{expected_enum}', "
                f"got '{record['device_type']}'"
            )

    # ------------------------------------------------------------------
    # Telemetry shape
    # ------------------------------------------------------------------

    def test_telemetry_is_dict(self, iot_simulator):
        """The telemetry field must be a non-empty dictionary for every device type."""
        for device_key in _DEVICE_TYPES:
            record = iot_simulator.generate_record(device_type=device_key)
            assert isinstance(record["telemetry"], dict), (
                f"telemetry must be a dict for device_type='{device_key}', "
                f"got {type(record['telemetry'])}"
            )
            assert len(record["telemetry"]) > 0, (
                f"telemetry must not be empty for device_type='{device_key}'"
            )

    def test_slot_telemetry_fields(self, iot_simulator):
        """Slot machine telemetry must contain all machine-specific meter fields."""
        record = iot_simulator.generate_record(device_type="slot_machine")
        telemetry = record["telemetry"]

        for field in _SLOT_TELEMETRY_FIELDS:
            assert field in telemetry, (
                f"Slot telemetry missing expected field '{field}'"
            )

    # ------------------------------------------------------------------
    # Protocol
    # ------------------------------------------------------------------

    def test_protocol_valid(self, iot_simulator):
        """protocol must be MQTT, AMQP, or HTTPS across all device types."""
        for device_key in _DEVICE_TYPES:
            for _ in range(10):
                record = iot_simulator.generate_record(device_type=device_key)
                assert record["protocol"] in _VALID_PROTOCOLS, (
                    f"Unexpected protocol '{record['protocol']}' "
                    f"for device_type='{device_key}'"
                )

    # ------------------------------------------------------------------
    # Signal strength
    # ------------------------------------------------------------------

    def test_signal_strength_range(self, iot_simulator):
        """signal_strength_dbm must be an integer between -100 and 0 (inclusive)."""
        for device_key in _DEVICE_TYPES:
            for _ in range(20):
                record = iot_simulator.generate_record(device_type=device_key)
                rssi = record["signal_strength_dbm"]
                assert isinstance(rssi, int), (
                    f"signal_strength_dbm must be int, got {type(rssi)}"
                )
                assert -100 <= rssi <= 0, (
                    f"signal_strength_dbm {rssi} is outside [-100, 0] "
                    f"for device_type='{device_key}'"
                )

    # ------------------------------------------------------------------
    # Batch generation
    # ------------------------------------------------------------------

    def test_generate_batch(self, iot_simulator, sample_size):
        """generate_batch returns exactly the requested number of records."""
        batch = iot_simulator.generate_batch(
            count=sample_size, device_type="slot_machine"
        )

        assert isinstance(batch, list), "generate_batch must return a list"
        assert len(batch) == sample_size, (
            f"Expected {sample_size} records, got {len(batch)}"
        )

    # ------------------------------------------------------------------
    # Fleet snapshot
    # ------------------------------------------------------------------

    def test_fleet_snapshot(self, iot_simulator):
        """generate_fleet_snapshot returns exactly one message per device in the fleet."""
        fleet = iot_simulator.get_fleet()
        total_devices = sum(len(devices) for devices in fleet.values())

        snapshot = iot_simulator.generate_fleet_snapshot()

        assert isinstance(snapshot, list), "generate_fleet_snapshot must return a list"
        assert len(snapshot) == total_devices, (
            f"Snapshot should contain {total_devices} messages (one per device), "
            f"got {len(snapshot)}"
        )

        # Every device type in the fleet must be represented in the snapshot
        snapshot_types = {record["device_type"] for record in snapshot}
        expected_types = {dtype.upper() for dtype in fleet}
        assert snapshot_types == expected_types, (
            f"Snapshot device types {snapshot_types} do not match "
            f"fleet device types {expected_types}"
        )

    # ------------------------------------------------------------------
    # Metadata columns
    # ------------------------------------------------------------------

    def test_metadata_columns(self, iot_simulator):
        """Standard metadata columns _ingested_at, _source, and _batch_id must be present."""
        record = iot_simulator.generate_record(device_type="slot_machine")

        assert "_ingested_at" in record, "_ingested_at metadata column missing"
        assert "_source" in record, "_source metadata column missing"
        assert "_batch_id" in record, "_batch_id metadata column missing"
