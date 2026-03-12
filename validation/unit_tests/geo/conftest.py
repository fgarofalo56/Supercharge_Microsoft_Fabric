"""Pytest fixtures for geospatial data generator tests."""
import pytest
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "data-generation"))


@pytest.fixture
def casino_locations_seeded():
    """Fixture that seeds random and returns the generate function."""
    random.seed(42)
    from generators.geo.casino_locations import generate_us_casino_locations
    return generate_us_casino_locations


@pytest.fixture
def global_casino_locations_seeded():
    """Fixture that seeds random and returns the global generate function."""
    random.seed(42)
    from generators.geo.casino_locations import generate_global_casino_locations
    return generate_global_casino_locations


@pytest.fixture
def player_demographics_seeded():
    """Fixture that seeds random and returns the generate function."""
    random.seed(42)
    from generators.geo.player_demographics import generate_player_demographics
    return generate_player_demographics


@pytest.fixture
def sample_casinos():
    """Fixture providing a small set of pre-generated casino locations."""
    random.seed(42)
    from generators.geo.casino_locations import generate_us_casino_locations
    return generate_us_casino_locations(10)


@pytest.fixture
def sample_size():
    """Default sample size for batch tests."""
    return 100
