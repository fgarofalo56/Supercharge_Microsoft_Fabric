"""
Unit tests for player_demographics module.

Covers player demographic generation with geospatial attributes,
distance calculations (Haversine), market type classification,
lifetime value computation, loyalty tier assignment, player segment
logic, and GeoJSON export.
"""

import random

from generators.geo.player_demographics import (
    AGE_GROUPS,
    GENDERS,
    INCOME_BRACKETS,
    LOYALTY_TIERS,
    PLAYER_SEGMENTS,
    PREFERRED_GAMING,
    VISIT_FREQUENCIES,
    create_player_geojson,
    generate_market_summary,
    get_income_bracket,
    get_loyalty_tier,
    haversine_distance,
)

_VALID_AGE_GROUPS = set(AGE_GROUPS)
_VALID_GENDERS = set(GENDERS)
_VALID_INCOME_BRACKETS = set(INCOME_BRACKETS)
_VALID_VISIT_FREQUENCIES = set(VISIT_FREQUENCIES)
_VALID_PREFERRED_GAMING = set(PREFERRED_GAMING)
_VALID_LOYALTY_TIERS = set(LOYALTY_TIERS)
_VALID_PLAYER_SEGMENTS = set(PLAYER_SEGMENTS)
_VALID_MARKET_TYPES = {"Primary", "Secondary", "Tertiary", "Destination"}

# Default casino for tests
_DEFAULT_CASINO = [
    {
        "casino_id": "CAS00001",
        "name": "Test Casino",
        "latitude": 36.1699,
        "longitude": -115.1398,
    }
]


class TestPlayerDemographics:
    """Tests for player demographic generation with geospatial attributes."""

    # ------------------------------------------------------------------
    # Basic generation and field presence
    # ------------------------------------------------------------------

    def test_generate_player_count(self, player_demographics_seeded):
        """generate_player_demographics returns the requested number of players."""
        players = player_demographics_seeded(50, _DEFAULT_CASINO)

        assert len(players) == 50, f"Expected 50 players, got {len(players)}"

    def test_player_required_fields(self, player_demographics_seeded):
        """Each player record must contain all required fields."""
        players = player_demographics_seeded(10, _DEFAULT_CASINO)
        required_fields = [
            "player_id",
            "home_casino_id",
            "home_latitude",
            "home_longitude",
            "home_city",
            "home_state",
            "distance_to_casino_miles",
            "market_type",
            "age_group",
            "gender",
            "income_bracket",
            "visit_frequency",
            "preferred_gaming",
            "loyalty_tier",
            "player_segment",
            "lifetime_value",
            "geo_point_wkt",
        ]

        for player in players:
            for field in required_fields:
                assert field in player, (
                    f"Required field '{field}' missing from player record"
                )

    # ------------------------------------------------------------------
    # Player ID format
    # ------------------------------------------------------------------

    def test_player_id_format(self, player_demographics_seeded):
        """player_id must follow the PLY######## pattern."""
        players = player_demographics_seeded(20, _DEFAULT_CASINO)

        for player in players:
            pid = player["player_id"]
            assert pid.startswith("PLY"), (
                f"player_id must start with 'PLY', got '{pid}'"
            )
            assert len(pid) == 11, (
                f"player_id must be 11 chars (PLY + 8 digits), got '{pid}' (len={len(pid)})"
            )

    # ------------------------------------------------------------------
    # Enum field validation
    # ------------------------------------------------------------------

    def test_age_group_valid(self, player_demographics_seeded):
        """age_group must be one of the defined age groups."""
        players = player_demographics_seeded(100, _DEFAULT_CASINO)

        for player in players:
            assert player["age_group"] in _VALID_AGE_GROUPS, (
                f"Unexpected age_group '{player['age_group']}'"
            )

    def test_gender_valid(self, player_demographics_seeded):
        """gender must be one of Male, Female, or Non-binary."""
        players = player_demographics_seeded(100, _DEFAULT_CASINO)

        for player in players:
            assert player["gender"] in _VALID_GENDERS, (
                f"Unexpected gender '{player['gender']}'"
            )

    def test_market_type_valid(self, player_demographics_seeded):
        """market_type must be Primary, Secondary, Tertiary, or Destination."""
        players = player_demographics_seeded(100, _DEFAULT_CASINO)

        for player in players:
            assert player["market_type"] in _VALID_MARKET_TYPES, (
                f"Unexpected market_type '{player['market_type']}'"
            )

    # ------------------------------------------------------------------
    # Distance and market type consistency
    # ------------------------------------------------------------------

    def test_distance_positive(self, player_demographics_seeded):
        """distance_to_casino_miles must be non-negative."""
        players = player_demographics_seeded(100, _DEFAULT_CASINO)

        for player in players:
            assert player["distance_to_casino_miles"] >= 0, (
                f"distance must be >= 0, got {player['distance_to_casino_miles']}"
            )

    # ------------------------------------------------------------------
    # Haversine distance utility
    # ------------------------------------------------------------------

    def test_haversine_same_point_zero(self):
        """Haversine distance between a point and itself must be 0."""
        dist = haversine_distance(36.1699, -115.1398, 36.1699, -115.1398)
        assert dist == 0.0, f"Distance to self must be 0, got {dist}"

    def test_haversine_known_distance(self):
        """Haversine distance between LA and LV should be approximately 230 miles."""
        dist = haversine_distance(34.0522, -118.2437, 36.1699, -115.1398)
        # LA to LV is approximately 230 miles
        assert 220 <= dist <= 275, f"LA-to-LV distance should be ~230 miles, got {dist}"

    # ------------------------------------------------------------------
    # Lifetime value and loyalty tier
    # ------------------------------------------------------------------

    def test_lifetime_value_positive(self, player_demographics_seeded):
        """lifetime_value must be non-negative for all players."""
        players = player_demographics_seeded(100, _DEFAULT_CASINO)

        for player in players:
            assert player["lifetime_value"] >= 0, (
                f"lifetime_value must be >= 0, got {player['lifetime_value']}"
            )

    def test_loyalty_tier_valid(self, player_demographics_seeded):
        """loyalty_tier must be one of the 6 defined tiers."""
        players = player_demographics_seeded(100, _DEFAULT_CASINO)

        for player in players:
            assert player["loyalty_tier"] in _VALID_LOYALTY_TIERS, (
                f"Unexpected loyalty_tier '{player['loyalty_tier']}'"
            )

    def test_get_loyalty_tier_thresholds(self):
        """get_loyalty_tier must return correct tiers based on LTV thresholds."""
        assert get_loyalty_tier(1000) == "Bronze", "LTV 1000 should be Bronze"
        assert get_loyalty_tier(10000) == "Silver", "LTV 10000 should be Silver"
        assert get_loyalty_tier(30000) == "Gold", "LTV 30000 should be Gold"
        assert get_loyalty_tier(60000) == "Platinum", "LTV 60000 should be Platinum"
        assert get_loyalty_tier(150000) == "Diamond", "LTV 150000 should be Diamond"
        assert get_loyalty_tier(300000) == "Seven Stars", (
            "LTV 300000 should be Seven Stars"
        )

    # ------------------------------------------------------------------
    # GeoJSON export
    # ------------------------------------------------------------------

    def test_create_player_geojson_structure(self, player_demographics_seeded):
        """create_player_geojson must return a valid GeoJSON FeatureCollection."""
        players = player_demographics_seeded(10, _DEFAULT_CASINO)
        geojson = create_player_geojson(players)

        assert geojson["type"] == "FeatureCollection", (
            f"GeoJSON type must be 'FeatureCollection', got '{geojson['type']}'"
        )
        assert len(geojson["features"]) == 10, (
            f"Expected 10 features, got {len(geojson['features'])}"
        )

        feature = geojson["features"][0]
        assert feature["type"] == "Feature", "Feature type must be 'Feature'"
        assert feature["geometry"]["type"] == "Point", "Geometry must be Point"

    # ------------------------------------------------------------------
    # Market summary
    # ------------------------------------------------------------------

    def test_generate_market_summary(self, player_demographics_seeded):
        """generate_market_summary must return summary with expected keys."""
        players = player_demographics_seeded(50, _DEFAULT_CASINO)
        summary = generate_market_summary(players)

        assert summary["total_players"] == 50, (
            f"Expected total_players=50, got {summary['total_players']}"
        )
        assert "by_market_type" in summary, "Summary must have 'by_market_type'"
        assert "by_loyalty_tier" in summary, "Summary must have 'by_loyalty_tier'"
        assert "distance_stats" in summary, "Summary must have 'distance_stats'"
        assert "avg" in summary["distance_stats"], "distance_stats must have 'avg'"

    # ------------------------------------------------------------------
    # Income bracket utility
    # ------------------------------------------------------------------

    def test_get_income_bracket_returns_valid_bracket(self):
        """get_income_bracket must return one of the defined income brackets."""
        random.seed(42)
        for _ in range(100):
            bracket = get_income_bracket(60000)
            assert bracket in _VALID_INCOME_BRACKETS, (
                f"Unexpected income bracket '{bracket}'"
            )
