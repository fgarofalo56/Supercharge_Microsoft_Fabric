"""
Pytest configuration and fixtures for Casino Fabric POC unit tests.
"""

import sys
from pathlib import Path

import pytest

# Add data-generation to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "data-generation"))


@pytest.fixture
def sample_size():
    """Default sample size for tests."""
    return 100


@pytest.fixture
def test_date_range():
    """Default date range for tests."""
    return 7  # days


@pytest.fixture
def slot_generator():
    """Fixture for slot machine generator."""
    from generators.slot_machine_generator import SlotMachineGenerator

    return SlotMachineGenerator(seed=42)


@pytest.fixture
def player_generator():
    """Fixture for player generator."""
    from generators.player_generator import PlayerGenerator

    return PlayerGenerator(seed=42)


@pytest.fixture
def compliance_generator():
    """Fixture for compliance generator."""
    from generators.compliance_generator import ComplianceGenerator

    return ComplianceGenerator(seed=42)


@pytest.fixture
def financial_generator():
    """Fixture for financial generator."""
    from generators.financial_generator import FinancialGenerator

    return FinancialGenerator(seed=42)


@pytest.fixture
def security_generator():
    """Fixture for security generator."""
    from generators.security_generator import SecurityGenerator

    return SecurityGenerator(seed=42)


@pytest.fixture
def table_games_generator():
    """Fixture for table games generator."""
    from generators.table_games_generator import TableGamesGenerator

    return TableGamesGenerator(seed=42)


@pytest.fixture(scope="session")
def temp_output_dir(tmp_path_factory):
    """Create temporary directory for test outputs."""
    return tmp_path_factory.mktemp("test_output")


# Markers for test categorization
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line(
        "markers", "compliance: marks tests related to compliance logic"
    )
