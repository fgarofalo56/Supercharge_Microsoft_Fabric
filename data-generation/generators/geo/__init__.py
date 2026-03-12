"""
GeoAnalytics Data Generators

This module provides synthetic data generators for geospatial analytics
in the casino/gaming industry, including:

- Casino locations (US and global markets)
- Player demographics with home locations
- Market analysis and catchment areas

Usage:
    from generators.geo import casino_locations, player_demographics

    # Generate 100 US casino locations
    casinos = casino_locations.generate_us_casino_locations(100)

    # Generate 50 international casino locations
    global_casinos = casino_locations.generate_global_casino_locations(50)

    # Generate 10,000 player demographics linked to casinos
    players = player_demographics.generate_player_demographics(10000, casinos)

    # Export to GeoJSON for visualization
    geojson = casino_locations.create_geojson(casinos)
"""

from .casino_locations import (
    GLOBAL_GAMING_MARKETS,
    US_GAMING_MARKETS,
    CasinoLocation,
    create_geojson,
    generate_global_casino_locations,
    generate_us_casino_locations,
)
from .player_demographics import (
    POPULATION_CENTERS,
    create_player_geojson,
    generate_market_summary,
    generate_player_demographics,
    haversine_distance,
)

__all__ = [
    "GLOBAL_GAMING_MARKETS",
    "POPULATION_CENTERS",
    "US_GAMING_MARKETS",
    "CasinoLocation",
    "create_geojson",
    "create_player_geojson",
    "generate_global_casino_locations",
    "generate_market_summary",
    # Player demographics
    "generate_player_demographics",
    # Casino locations
    "generate_us_casino_locations",
    "haversine_distance",
]
