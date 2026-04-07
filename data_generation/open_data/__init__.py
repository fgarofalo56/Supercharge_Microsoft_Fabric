"""
Open Data Download Package
===========================

Scripts for downloading real federal agency datasets for POC demonstrations.
Each module provides download functions for a specific agency's public data.

Usage:
    # Download USDA data
    from data_generation.open_data import download_nass_quickstats, download_fsis_recalls

    # Download EPA data
    from data_generation.open_data import download_air_quality, download_water_quality

    # Download NOAA data
    from data_generation.open_data import download_weather_observations, download_storm_events

    # Download SBA data
    from data_generation.open_data import download_ppp_loans, download_7a_504_loans

    # Download DOI data
    from data_generation.open_data import download_earthquakes, download_park_visitation

    # Download Tribal Health data
    from data_generation.open_data import download_hrsa_health_centers, download_ihs_statistics

    # Download DOT/FAA data
    from data_generation.open_data import download_bts_flight_data, download_faa_safety_reports
"""

# USDA
from .usda_download import (
    download_census_of_agriculture,
    download_fsis_recalls,
    download_nass_quickstats,
    download_snap_retailers,
    validate_download as validate_usda_download,
)

# SBA
from .sba_download import (
    download_7a_504_loans,
    download_ppp_loans,
    download_sbir_awards,
    validate_download as validate_sba_download,
)

# NOAA
from .noaa_download import (
    download_climate_data,
    download_storm_events,
    download_tide_data,
    download_weather_observations,
    validate_download as validate_noaa_download,
)

# EPA
from .epa_download import (
    download_air_quality,
    download_echo_compliance,
    download_tri_data,
    download_water_quality,
    validate_download as validate_epa_download,
)

# DOI
from .doi_download import (
    download_earthquakes,
    download_park_visitation,
    download_species_data,
    download_water_data,
    validate_download as validate_doi_download,
)

# Tribal Health
from .tribal_health_download import (
    download_cdc_tribal_health,
    download_cms_medicaid_tribal,
    download_hrsa_health_centers,
    download_ihs_statistics,
    validate_download as validate_tribal_download,
)

# DOT/FAA
from .dot_faa_download import (
    download_bts_flight_data,
    download_faa_airport_data,
    download_faa_safety_reports,
    validate_download as validate_dot_faa_download,
)

__all__ = [
    # USDA
    "download_nass_quickstats",
    "download_fsis_recalls",
    "download_snap_retailers",
    "download_census_of_agriculture",
    "validate_usda_download",
    # SBA
    "download_ppp_loans",
    "download_7a_504_loans",
    "download_sbir_awards",
    "validate_sba_download",
    # NOAA
    "download_weather_observations",
    "download_storm_events",
    "download_climate_data",
    "download_tide_data",
    "validate_noaa_download",
    # EPA
    "download_air_quality",
    "download_tri_data",
    "download_echo_compliance",
    "download_water_quality",
    "validate_epa_download",
    # DOI
    "download_earthquakes",
    "download_water_data",
    "download_park_visitation",
    "download_species_data",
    "validate_doi_download",
    # Tribal Health
    "download_hrsa_health_centers",
    "download_ihs_statistics",
    "download_cdc_tribal_health",
    "download_cms_medicaid_tribal",
    "validate_tribal_download",
    # DOT/FAA
    "download_bts_flight_data",
    "download_faa_safety_reports",
    "download_faa_airport_data",
    "validate_dot_faa_download",
]
