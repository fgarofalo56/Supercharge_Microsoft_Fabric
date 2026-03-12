"""
Analytics data generators for video, movement, and geolocation scenarios.
"""

from .geolocation_generator import GeolocationGenerator
from .people_movement_generator import PeopleMovementGenerator
from .video_analytics_generator import VideoAnalyticsGenerator

__all__ = [
    "GeolocationGenerator",
    "PeopleMovementGenerator",
    "VideoAnalyticsGenerator",
]
