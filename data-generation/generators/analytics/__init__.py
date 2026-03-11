"""
Analytics data generators for video, movement, and geolocation scenarios.
"""
from .video_analytics_generator import VideoAnalyticsGenerator
from .people_movement_generator import PeopleMovementGenerator
from .geolocation_generator import GeolocationGenerator

__all__ = [
    "VideoAnalyticsGenerator",
    "PeopleMovementGenerator",
    "GeolocationGenerator",
]
