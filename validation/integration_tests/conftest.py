"""
Pytest configuration and shared fixtures for Casino Fabric POC integration tests.

This module provides:
- Generator instances with fixed seeds for reproducibility
- Sample datasets for testing
- Schema loaders for validation
- Path configuration
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

# Add data_generation to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "data_generation"))


# =============================================================================
# Path Constants
# =============================================================================

SCHEMAS_DIR = PROJECT_ROOT / "data_generation" / "schemas"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
GENERATORS_DIR = PROJECT_ROOT / "data_generation" / "generators"


# =============================================================================
# Pytest Configuration
# =============================================================================


def pytest_configure(config):
    """Configure custom pytest markers for integration tests."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line(
        "markers", "compliance: marks tests related to compliance rules"
    )
    config.addinivalue_line(
        "markers", "streaming: marks tests related to streaming functionality"
    )
    config.addinivalue_line("markers", "pipeline: marks tests related to data pipeline")
    config.addinivalue_line(
        "markers", "schema: marks tests related to schema validation"
    )
    config.addinivalue_line("markers", "slow: marks tests as slow running")


# =============================================================================
# Fixed Seed Fixtures
# =============================================================================

FIXED_SEED = 42
FIXED_START_DATE = datetime(2024, 1, 1)
FIXED_END_DATE = datetime(2024, 1, 31)


@pytest.fixture(scope="session")
def fixed_seed():
    """Fixed seed for reproducible tests."""
    return FIXED_SEED


@pytest.fixture(scope="session")
def fixed_date_range():
    """Fixed date range for consistent test data."""
    return (FIXED_START_DATE, FIXED_END_DATE)


# =============================================================================
# Generator Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def slot_generator():
    """Session-scoped slot machine generator with fixed seed."""
    from generators.slot_machine_generator import SlotMachineGenerator

    return SlotMachineGenerator(
        seed=FIXED_SEED,
        start_date=FIXED_START_DATE,
        end_date=FIXED_END_DATE,
    )


@pytest.fixture(scope="session")
def player_generator():
    """Session-scoped player generator with fixed seed."""
    from generators.player_generator import PlayerGenerator

    return PlayerGenerator(
        seed=FIXED_SEED,
        start_date=FIXED_START_DATE,
        end_date=FIXED_END_DATE,
    )


@pytest.fixture(scope="session")
def compliance_generator():
    """Session-scoped compliance generator with fixed seed."""
    from generators.compliance_generator import ComplianceGenerator

    return ComplianceGenerator(
        seed=FIXED_SEED,
        start_date=FIXED_START_DATE,
        end_date=FIXED_END_DATE,
    )


@pytest.fixture(scope="session")
def financial_generator():
    """Session-scoped financial generator with fixed seed."""
    from generators.financial_generator import FinancialGenerator

    return FinancialGenerator(
        seed=FIXED_SEED,
        start_date=FIXED_START_DATE,
        end_date=FIXED_END_DATE,
    )


@pytest.fixture(scope="session")
def security_generator():
    """Session-scoped security generator with fixed seed."""
    from generators.security_generator import SecurityGenerator

    return SecurityGenerator(
        seed=FIXED_SEED,
        start_date=FIXED_START_DATE,
        end_date=FIXED_END_DATE,
    )


@pytest.fixture(scope="session")
def table_games_generator():
    """Session-scoped table games generator with fixed seed."""
    from generators.table_games_generator import TableGamesGenerator

    return TableGamesGenerator(
        seed=FIXED_SEED,
        start_date=FIXED_START_DATE,
        end_date=FIXED_END_DATE,
    )


@pytest.fixture(scope="session")
def all_generators(
    slot_generator,
    player_generator,
    compliance_generator,
    financial_generator,
    security_generator,
    table_games_generator,
):
    """Dictionary of all generators for cross-generator tests."""
    return {
        "slot": slot_generator,
        "player": player_generator,
        "compliance": compliance_generator,
        "financial": financial_generator,
        "security": security_generator,
        "table_games": table_games_generator,
    }


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def sample_slot_data(slot_generator):
    """Sample slot machine data (1000 records)."""
    return slot_generator.generate(1000, show_progress=False)


@pytest.fixture(scope="session")
def sample_player_data(player_generator):
    """Sample player data (500 records)."""
    return player_generator.generate(500, show_progress=False)


@pytest.fixture(scope="session")
def sample_compliance_data(compliance_generator):
    """Sample compliance data (500 records)."""
    return compliance_generator.generate(500, show_progress=False)


@pytest.fixture(scope="session")
def sample_financial_data(financial_generator):
    """Sample financial data (1000 records)."""
    return financial_generator.generate(1000, show_progress=False)


@pytest.fixture(scope="session")
def sample_security_data(security_generator):
    """Sample security data (500 records)."""
    return security_generator.generate(500, show_progress=False)


@pytest.fixture(scope="session")
def sample_table_games_data(table_games_generator):
    """Sample table games data (500 records)."""
    return table_games_generator.generate(500, show_progress=False)


# =============================================================================
# Schema Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def schema_dir():
    """Path to schema directory."""
    return SCHEMAS_DIR


@pytest.fixture(scope="session")
def slot_telemetry_schema():
    """Load slot telemetry JSON schema."""
    schema_path = SCHEMAS_DIR / "slot_telemetry_schema.json"
    with open(schema_path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def player_profile_schema():
    """Load player profile JSON schema."""
    schema_path = SCHEMAS_DIR / "player_profile_schema.json"
    with open(schema_path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def compliance_filing_schema():
    """Load compliance filing JSON schema."""
    schema_path = SCHEMAS_DIR / "compliance_filing_schema.json"
    with open(schema_path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def financial_transaction_schema():
    """Load financial transaction JSON schema."""
    schema_path = SCHEMAS_DIR / "financial_transaction_schema.json"
    with open(schema_path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def table_games_schema():
    """Load table games JSON schema."""
    schema_path = SCHEMAS_DIR / "table_games_schema.json"
    if schema_path.exists():
        with open(schema_path) as f:
            return json.load(f)
    return None


@pytest.fixture(scope="session")
def security_events_schema():
    """Load security events JSON schema."""
    schema_path = SCHEMAS_DIR / "security_events_schema.json"
    if schema_path.exists():
        with open(schema_path) as f:
            return json.load(f)
    return None


@pytest.fixture(scope="session")
def all_schemas(
    slot_telemetry_schema,
    player_profile_schema,
    compliance_filing_schema,
    financial_transaction_schema,
    table_games_schema,
    security_events_schema,
):
    """Dictionary of all loaded schemas."""
    schemas = {
        "slot_telemetry": slot_telemetry_schema,
        "player_profile": player_profile_schema,
        "compliance_filing": compliance_filing_schema,
        "financial_transaction": financial_transaction_schema,
    }
    if table_games_schema:
        schemas["table_games"] = table_games_schema
    if security_events_schema:
        schemas["security_events"] = security_events_schema
    return schemas


# =============================================================================
# Directory Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def project_root():
    """Project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def notebooks_dir():
    """Notebooks directory."""
    return NOTEBOOKS_DIR


@pytest.fixture(scope="session")
def temp_output_dir(tmp_path_factory):
    """Session-scoped temporary directory for test outputs."""
    return tmp_path_factory.mktemp("integration_test_output")


# =============================================================================
# Helper Functions Available as Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def validate_player_id_format():
    """Fixture providing player ID format validation function."""
    import re

    def _validate(player_id: str) -> bool:
        """Validate player ID follows expected pattern."""
        if player_id is None:
            return True  # None is valid for optional fields
        # Pattern: P followed by digits OR PLY- followed by digits
        return bool(re.match(r"^(P\d+|PLY-\d+)$", player_id))

    return _validate


@pytest.fixture(scope="session")
def validate_machine_id_format():
    """Fixture providing machine ID format validation function."""
    import re

    def _validate(machine_id: str) -> bool:
        """Validate machine ID follows expected pattern."""
        if machine_id is None:
            return False  # Machine ID is required
        # Pattern: SLOT-XXXX (4 digits)
        return bool(re.match(r"^SLOT-\d{4}$", machine_id))

    return _validate


@pytest.fixture(scope="session")
def validate_ssn_hash():
    """Fixture providing SSN hash validation function."""

    def _validate(ssn_hash: str) -> bool:
        """Validate SSN hash is proper SHA-256 (64 hex chars, no raw SSN)."""
        if ssn_hash is None:
            return True  # None is valid
        # SHA-256 produces 64 character hex string
        if len(ssn_hash) != 64:
            return False
        # Must be valid hex
        try:
            int(ssn_hash, 16)
            return True
        except ValueError:
            return False

    return _validate


@pytest.fixture(scope="session")
def validate_iso_datetime():
    """Fixture providing ISO datetime validation function."""
    from datetime import datetime

    def _validate(dt_str: Any) -> bool:
        """Validate datetime is valid ISO format or datetime object."""
        if dt_str is None:
            return True
        if isinstance(dt_str, datetime):
            return True
        if isinstance(dt_str, str):
            try:
                # Handle various ISO formats
                dt_str = dt_str.replace("Z", "+00:00")
                datetime.fromisoformat(dt_str)
                return True
            except ValueError:
                return False
        return False

    return _validate
