"""Pytest fixtures for analytics generator tests."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "data-generation"))


@pytest.fixture
def video_analytics_generator():
    """Fixture for the video analytics generator."""
    from generators.analytics.video_analytics_generator import VideoAnalyticsGenerator

    return VideoAnalyticsGenerator(seed=42)


@pytest.fixture
def people_movement_generator():
    """Fixture for the people movement generator."""
    from generators.analytics.people_movement_generator import PeopleMovementGenerator

    return PeopleMovementGenerator(seed=42)


@pytest.fixture
def geolocation_generator():
    """Fixture for the geolocation generator."""
    from generators.analytics.geolocation_generator import GeolocationGenerator

    return GeolocationGenerator(seed=42)


@pytest.fixture
def sample_size():
    """Default sample size for batch tests."""
    return 100
