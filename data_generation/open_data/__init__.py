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
# DOI
from .doi_download import (
    download_earthquakes,
    download_park_visitation,
    download_species_data,
    download_water_data,
)
from .doi_download import (
    validate_download as validate_doi_download,
)

# DOT/FAA
from .dot_faa_download import (
    download_bts_flight_data,
    download_faa_airport_data,
    download_faa_safety_reports,
)
from .dot_faa_download import (
    validate_download as validate_dot_faa_download,
)

# EPA
from .epa_download import (
    download_air_quality,
    download_echo_compliance,
    download_tri_data,
    download_water_quality,
)
from .epa_download import (
    validate_download as validate_epa_download,
)

# NOAA
from .noaa_download import (
    download_climate_data,
    download_storm_events,
    download_tide_data,
    download_weather_observations,
)
from .noaa_download import (
    validate_download as validate_noaa_download,
)

# SBA
from .sba_download import (
    download_7a_504_loans,
    download_ppp_loans,
    download_sbir_awards,
)
from .sba_download import (
    validate_download as validate_sba_download,
)

# Tribal Health
from .tribal_health_download import (
    download_cdc_tribal_health,
    download_cms_medicaid_tribal,
    download_hrsa_health_centers,
    download_ihs_statistics,
)
from .tribal_health_download import (
    validate_download as validate_tribal_download,
)
from .usda_download import (
    download_census_of_agriculture,
    download_fsis_recalls,
    download_nass_quickstats,
    download_snap_retailers,
)
from .usda_download import (
    validate_download as validate_usda_download,
)

__all__ = [
    "download_7a_504_loans",
    # EPA
    "download_air_quality",
    # DOT/FAA
    "download_bts_flight_data",
    "download_cdc_tribal_health",
    "download_census_of_agriculture",
    "download_climate_data",
    "download_cms_medicaid_tribal",
    # DOI
    "download_earthquakes",
    "download_echo_compliance",
    "download_faa_airport_data",
    "download_faa_safety_reports",
    "download_fsis_recalls",
    # Tribal Health
    "download_hrsa_health_centers",
    "download_ihs_statistics",
    # USDA
    "download_nass_quickstats",
    "download_park_visitation",
    # SBA
    "download_ppp_loans",
    "download_sbir_awards",
    "download_snap_retailers",
    "download_species_data",
    "download_storm_events",
    "download_tide_data",
    "download_tri_data",
    "download_water_data",
    "download_water_quality",
    # NOAA
    "download_weather_observations",
    "validate_doi_download",
    "validate_dot_faa_download",
    "validate_epa_download",
    "validate_noaa_download",
    "validate_sba_download",
    "validate_tribal_download",
    "validate_usda_download",
]
