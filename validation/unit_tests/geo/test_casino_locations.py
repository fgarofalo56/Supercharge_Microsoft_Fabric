"""
Unit tests for casino_locations module.

Covers US and global casino location generation, geospatial attributes,
GeoJSON export, coordinate format conversions, and field validation
for casino properties.
"""

from generators.geo.casino_locations import (
    CASINO_BRANDS,
    GLOBAL_GAMING_MARKETS,
    PROPERTY_TYPES,
    REVENUE_TIERS,
    US_GAMING_MARKETS,
    create_geojson,
    decimal_to_dms,
)

_VALID_PROPERTY_TYPES = set(PROPERTY_TYPES)
_VALID_REVENUE_TIERS = set(REVENUE_TIERS)
_VALID_CASINO_BRANDS = set(CASINO_BRANDS)
_VALID_US_STATES = {m["state"] for m in US_GAMING_MARKETS}
_VALID_US_CITIES = {m["city"] for m in US_GAMING_MARKETS}
_VALID_GLOBAL_CITIES = {m["city"] for m in GLOBAL_GAMING_MARKETS}
_VALID_GLOBAL_COUNTRIES = {m["country"] for m in GLOBAL_GAMING_MARKETS}


class TestCasinoLocations:
    """Tests for casino location generation covering US and global markets."""

    # ------------------------------------------------------------------
    # US casino generation -- basic fields
    # ------------------------------------------------------------------

    def test_generate_us_casino_count(self, casino_locations_seeded):
        """generate_us_casino_locations returns the requested number of casinos."""
        casinos = casino_locations_seeded(50)

        assert len(casinos) == 50, f"Expected 50 US casinos, got {len(casinos)}"

    def test_us_casino_required_fields(self, casino_locations_seeded):
        """Each US casino record must contain all required fields."""
        casinos = casino_locations_seeded(10)
        required_fields = [
            "casino_id",
            "name",
            "brand",
            "latitude",
            "longitude",
            "city",
            "state",
            "zip_code",
            "country",
            "region",
            "property_type",
            "gaming_sqft",
            "slot_machines",
            "table_games",
            "geo_point_wkt",
        ]

        for casino in casinos:
            for field in required_fields:
                assert (
                    field in casino
                ), f"Required field '{field}' missing from US casino record"

    # ------------------------------------------------------------------
    # Casino ID format
    # ------------------------------------------------------------------

    def test_us_casino_id_format(self, casino_locations_seeded):
        """casino_id must follow the CAS##### pattern."""
        casinos = casino_locations_seeded(20)

        for casino in casinos:
            cid = casino["casino_id"]
            assert cid.startswith(
                "CAS"
            ), f"US casino_id must start with 'CAS', got '{cid}'"
            assert (
                len(cid) == 8
            ), f"US casino_id must be 8 chars, got '{cid}' (len={len(cid)})"

    # ------------------------------------------------------------------
    # Property type validation
    # ------------------------------------------------------------------

    def test_property_type_valid(self, casino_locations_seeded):
        """property_type must be one of the 5 known types."""
        casinos = casino_locations_seeded(_sample_size_val := 100)

        for casino in casinos:
            assert (
                casino["property_type"] in _VALID_PROPERTY_TYPES
            ), f"Unexpected property_type '{casino['property_type']}'"

    # ------------------------------------------------------------------
    # Geospatial coordinate bounds
    # ------------------------------------------------------------------

    def test_us_casino_coordinates_in_bounds(self, casino_locations_seeded):
        """US casino coordinates must be within reasonable continental US bounds."""
        casinos = casino_locations_seeded(100)

        for casino in casinos:
            lat = casino["latitude"]
            lon = casino["longitude"]
            # Continental US approximate bounds (with ~0.1 degree tolerance)
            assert (
                24.0 <= lat <= 50.0
            ), f"US latitude {lat} out of continental bounds [24, 50]"
            assert (
                -126.0 <= lon <= -66.0
            ), f"US longitude {lon} out of continental bounds [-126, -66]"

    # ------------------------------------------------------------------
    # WKT geo_point format
    # ------------------------------------------------------------------

    def test_geo_point_wkt_format(self, casino_locations_seeded):
        """geo_point_wkt must follow POINT(lon lat) format."""
        casinos = casino_locations_seeded(20)

        for casino in casinos:
            wkt = casino["geo_point_wkt"]
            assert wkt.startswith(
                "POINT("
            ), f"geo_point_wkt must start with 'POINT(', got '{wkt[:20]}'"
            assert wkt.endswith(
                ")"
            ), f"geo_point_wkt must end with ')', got '{wkt[-5:]}'"

    # ------------------------------------------------------------------
    # Global casino generation
    # ------------------------------------------------------------------

    def test_generate_global_casino_count(self, global_casino_locations_seeded):
        """generate_global_casino_locations returns the requested number of casinos."""
        casinos = global_casino_locations_seeded(25)

        assert len(casinos) == 25, f"Expected 25 global casinos, got {len(casinos)}"

    def test_global_casino_has_currency(self, global_casino_locations_seeded):
        """Global casino records must have a currency field."""
        casinos = global_casino_locations_seeded(20)

        for casino in casinos:
            assert "currency" in casino, "Global casino must have 'currency' field"
            assert casino["currency"] is not None, "currency must not be None"

    # ------------------------------------------------------------------
    # GeoJSON export
    # ------------------------------------------------------------------

    def test_create_geojson_structure(self, casino_locations_seeded):
        """create_geojson must return a valid GeoJSON FeatureCollection."""
        casinos = casino_locations_seeded(10)
        geojson = create_geojson(casinos)

        assert (
            geojson["type"] == "FeatureCollection"
        ), f"GeoJSON type must be 'FeatureCollection', got '{geojson['type']}'"
        assert "features" in geojson, "GeoJSON must have 'features' key"
        assert (
            len(geojson["features"]) == 10
        ), f"Expected 10 features, got {len(geojson['features'])}"

        feature = geojson["features"][0]
        assert feature["type"] == "Feature", "Each feature type must be 'Feature'"
        assert feature["geometry"]["type"] == "Point", "Geometry type must be 'Point'"
        assert (
            len(feature["geometry"]["coordinates"]) == 2
        ), "Point coordinates must have exactly 2 values [lon, lat]"

    # ------------------------------------------------------------------
    # decimal_to_dms utility
    # ------------------------------------------------------------------

    def test_decimal_to_dms_latitude(self):
        """decimal_to_dms correctly converts positive latitude to N direction."""
        result = decimal_to_dms(36.1699, is_latitude=True)
        assert "N" in result, f"Positive latitude should have 'N', got '{result}'"
        assert result.startswith("36"), f"Expected 36 degrees, got '{result}'"

    def test_decimal_to_dms_negative_longitude(self):
        """decimal_to_dms correctly converts negative longitude to W direction."""
        result = decimal_to_dms(-115.1398, is_latitude=False)
        assert "W" in result, f"Negative longitude should have 'W', got '{result}'"
        assert result.startswith("115"), f"Expected 115 degrees, got '{result}'"

    # ------------------------------------------------------------------
    # Country field for US casinos
    # ------------------------------------------------------------------

    def test_us_casino_country_is_usa(self, casino_locations_seeded):
        """All US casino records must have country='USA'."""
        casinos = casino_locations_seeded(50)

        for casino in casinos:
            assert (
                casino["country"] == "USA"
            ), f"US casino country must be 'USA', got '{casino['country']}'"
