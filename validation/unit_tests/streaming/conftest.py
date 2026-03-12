"""Pytest fixtures for streaming generator tests."""
import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "data-generation"))


@pytest.fixture
def multi_source_simulator():
    """Fixture for the multi-source CDC event simulator."""
    from generators.streaming.multi_source_simulator import MultiSourceSimulator
    return MultiSourceSimulator(seed=42)


@pytest.fixture
def iot_simulator():
    """Fixture for the IoT device fleet simulator (50-device fleet)."""
    from generators.streaming.iot_device_simulator import IoTDeviceSimulator
    return IoTDeviceSimulator(num_devices=50, seed=42)


@pytest.fixture
def sample_size():
    """Default sample size for batch tests."""
    return 100
