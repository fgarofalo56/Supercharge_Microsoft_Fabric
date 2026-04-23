"""Pytest fixtures for federal data generator tests."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "data_generation"))


@pytest.fixture
def usda_generator():
    """Fixture for USDA data generator."""
    from generators.federal.usda_generator import USDAGenerator

    return USDAGenerator(seed=42)


@pytest.fixture
def sba_generator():
    """Fixture for SBA data generator."""
    from generators.federal.sba_generator import SBAGenerator

    return SBAGenerator(seed=42)


@pytest.fixture
def noaa_generator():
    """Fixture for NOAA data generator."""
    from generators.federal.noaa_generator import NOAAGenerator

    return NOAAGenerator(seed=42)


@pytest.fixture
def epa_generator():
    """Fixture for EPA data generator."""
    from generators.federal.epa_generator import EPAGenerator

    return EPAGenerator(seed=42)


@pytest.fixture
def doi_generator():
    """Fixture for DOI data generator."""
    from generators.federal.doi_generator import DOIGenerator

    return DOIGenerator(seed=42)


@pytest.fixture
def tribal_healthcare_generator():
    """Fixture for Tribal Healthcare (IHS) data generator."""
    from generators.federal.tribal_healthcare_generator import TribalHealthcareGenerator

    return TribalHealthcareGenerator(seed=42)


@pytest.fixture
def dot_faa_generator():
    """Fixture for DOT/FAA data generator."""
    from generators.federal.dot_faa_generator import DOTFAAGenerator

    return DOTFAAGenerator(seed=42)


@pytest.fixture
def doj_generator():
    """Fixture for DOJ data generator."""
    from generators.federal.doj_generator import DOJGenerator

    return DOJGenerator(seed=42)


@pytest.fixture
def sample_size():
    """Default sample size for batch tests."""
    return 100
