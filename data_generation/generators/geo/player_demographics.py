"""
Player Demographics Data Generator with Geospatial Attributes

Generates synthetic player demographic data with home locations,
distance calculations, and market analysis attributes.
"""

import json
import random
from datetime import datetime, timedelta
from math import atan2, cos, radians, sin, sqrt
from typing import Any

# Import casino locations for reference
try:
    from casino_locations import US_GAMING_MARKETS
except ImportError:
    # Fallback if running standalone
    US_GAMING_MARKETS = []


# US population centers with demographics
POPULATION_CENTERS = [
    # West Coast - Las Vegas feeders
    {
        "city": "Los Angeles",
        "state": "CA",
        "lat": 34.0522,
        "lon": -118.2437,
        "zip_prefix": "900",
        "pop_weight": 10,
        "median_income": 65000,
    },
    {
        "city": "Phoenix",
        "state": "AZ",
        "lat": 33.4484,
        "lon": -112.0740,
        "zip_prefix": "850",
        "pop_weight": 5,
        "median_income": 57000,
    },
    {
        "city": "San Diego",
        "state": "CA",
        "lat": 32.7157,
        "lon": -117.1611,
        "zip_prefix": "921",
        "pop_weight": 4,
        "median_income": 72000,
    },
    {
        "city": "Denver",
        "state": "CO",
        "lat": 39.7392,
        "lon": -104.9903,
        "zip_prefix": "802",
        "pop_weight": 3,
        "median_income": 68000,
    },
    {
        "city": "Salt Lake City",
        "state": "UT",
        "lat": 40.7608,
        "lon": -111.8910,
        "zip_prefix": "841",
        "pop_weight": 2,
        "median_income": 58000,
    },
    {
        "city": "Albuquerque",
        "state": "NM",
        "lat": 35.0844,
        "lon": -106.6504,
        "zip_prefix": "871",
        "pop_weight": 2,
        "median_income": 50000,
    },
    {
        "city": "Tucson",
        "state": "AZ",
        "lat": 32.2226,
        "lon": -110.9747,
        "zip_prefix": "857",
        "pop_weight": 2,
        "median_income": 45000,
    },
    {
        "city": "Las Vegas",
        "state": "NV",
        "lat": 36.1699,
        "lon": -115.1398,
        "zip_prefix": "891",
        "pop_weight": 3,
        "median_income": 55000,
    },
    {
        "city": "Reno",
        "state": "NV",
        "lat": 39.5296,
        "lon": -119.8138,
        "zip_prefix": "895",
        "pop_weight": 1,
        "median_income": 52000,
    },
    {
        "city": "Sacramento",
        "state": "CA",
        "lat": 38.5816,
        "lon": -121.4944,
        "zip_prefix": "958",
        "pop_weight": 3,
        "median_income": 60000,
    },
    {
        "city": "San Francisco",
        "state": "CA",
        "lat": 37.7749,
        "lon": -122.4194,
        "zip_prefix": "941",
        "pop_weight": 4,
        "median_income": 110000,
    },
    {
        "city": "Portland",
        "state": "OR",
        "lat": 45.5051,
        "lon": -122.6750,
        "zip_prefix": "972",
        "pop_weight": 2,
        "median_income": 65000,
    },
    {
        "city": "Seattle",
        "state": "WA",
        "lat": 47.6062,
        "lon": -122.3321,
        "zip_prefix": "981",
        "pop_weight": 3,
        "median_income": 85000,
    },
    # East Coast - Atlantic City feeders
    {
        "city": "New York",
        "state": "NY",
        "lat": 40.7128,
        "lon": -74.0060,
        "zip_prefix": "100",
        "pop_weight": 10,
        "median_income": 75000,
    },
    {
        "city": "Philadelphia",
        "state": "PA",
        "lat": 39.9526,
        "lon": -75.1652,
        "zip_prefix": "191",
        "pop_weight": 5,
        "median_income": 48000,
    },
    {
        "city": "Baltimore",
        "state": "MD",
        "lat": 39.2904,
        "lon": -76.6122,
        "zip_prefix": "212",
        "pop_weight": 3,
        "median_income": 50000,
    },
    {
        "city": "Washington",
        "state": "DC",
        "lat": 38.9072,
        "lon": -77.0369,
        "zip_prefix": "200",
        "pop_weight": 4,
        "median_income": 85000,
    },
    {
        "city": "Boston",
        "state": "MA",
        "lat": 42.3601,
        "lon": -71.0589,
        "zip_prefix": "021",
        "pop_weight": 4,
        "median_income": 70000,
    },
    {
        "city": "Hartford",
        "state": "CT",
        "lat": 41.7658,
        "lon": -72.6734,
        "zip_prefix": "061",
        "pop_weight": 2,
        "median_income": 45000,
    },
    {
        "city": "Providence",
        "state": "RI",
        "lat": 41.8240,
        "lon": -71.4128,
        "zip_prefix": "029",
        "pop_weight": 1,
        "median_income": 42000,
    },
    # Gulf Coast and South
    {
        "city": "New Orleans",
        "state": "LA",
        "lat": 29.9511,
        "lon": -90.0715,
        "zip_prefix": "701",
        "pop_weight": 2,
        "median_income": 40000,
    },
    {
        "city": "Houston",
        "state": "TX",
        "lat": 29.7604,
        "lon": -95.3698,
        "zip_prefix": "770",
        "pop_weight": 5,
        "median_income": 52000,
    },
    {
        "city": "Dallas",
        "state": "TX",
        "lat": 32.7767,
        "lon": -96.7970,
        "zip_prefix": "752",
        "pop_weight": 4,
        "median_income": 55000,
    },
    {
        "city": "San Antonio",
        "state": "TX",
        "lat": 29.4241,
        "lon": -98.4936,
        "zip_prefix": "782",
        "pop_weight": 3,
        "median_income": 48000,
    },
    {
        "city": "Atlanta",
        "state": "GA",
        "lat": 33.7490,
        "lon": -84.3880,
        "zip_prefix": "303",
        "pop_weight": 4,
        "median_income": 55000,
    },
    {
        "city": "Miami",
        "state": "FL",
        "lat": 25.7617,
        "lon": -80.1918,
        "zip_prefix": "331",
        "pop_weight": 4,
        "median_income": 42000,
    },
    {
        "city": "Tampa",
        "state": "FL",
        "lat": 27.9506,
        "lon": -82.4572,
        "zip_prefix": "336",
        "pop_weight": 3,
        "median_income": 50000,
    },
    {
        "city": "Orlando",
        "state": "FL",
        "lat": 28.5383,
        "lon": -81.3792,
        "zip_prefix": "328",
        "pop_weight": 3,
        "median_income": 48000,
    },
    {
        "city": "Jacksonville",
        "state": "FL",
        "lat": 30.3322,
        "lon": -81.6557,
        "zip_prefix": "322",
        "pop_weight": 2,
        "median_income": 52000,
    },
    {
        "city": "Nashville",
        "state": "TN",
        "lat": 36.1627,
        "lon": -86.7816,
        "zip_prefix": "372",
        "pop_weight": 2,
        "median_income": 55000,
    },
    {
        "city": "Charlotte",
        "state": "NC",
        "lat": 35.2271,
        "lon": -80.8431,
        "zip_prefix": "282",
        "pop_weight": 2,
        "median_income": 58000,
    },
    {
        "city": "Birmingham",
        "state": "AL",
        "lat": 33.5207,
        "lon": -86.8025,
        "zip_prefix": "352",
        "pop_weight": 1,
        "median_income": 42000,
    },
    {
        "city": "Jackson",
        "state": "MS",
        "lat": 32.2988,
        "lon": -90.1848,
        "zip_prefix": "392",
        "pop_weight": 1,
        "median_income": 38000,
    },
    {
        "city": "Mobile",
        "state": "AL",
        "lat": 30.6954,
        "lon": -88.0399,
        "zip_prefix": "366",
        "pop_weight": 1,
        "median_income": 40000,
    },
    # Midwest
    {
        "city": "Chicago",
        "state": "IL",
        "lat": 41.8781,
        "lon": -87.6298,
        "zip_prefix": "606",
        "pop_weight": 6,
        "median_income": 58000,
    },
    {
        "city": "Detroit",
        "state": "MI",
        "lat": 42.3314,
        "lon": -83.0458,
        "zip_prefix": "482",
        "pop_weight": 3,
        "median_income": 32000,
    },
    {
        "city": "Cleveland",
        "state": "OH",
        "lat": 41.4993,
        "lon": -81.6944,
        "zip_prefix": "441",
        "pop_weight": 2,
        "median_income": 35000,
    },
    {
        "city": "Columbus",
        "state": "OH",
        "lat": 39.9612,
        "lon": -82.9988,
        "zip_prefix": "432",
        "pop_weight": 2,
        "median_income": 52000,
    },
    {
        "city": "Cincinnati",
        "state": "OH",
        "lat": 39.1031,
        "lon": -84.5120,
        "zip_prefix": "452",
        "pop_weight": 2,
        "median_income": 42000,
    },
    {
        "city": "Indianapolis",
        "state": "IN",
        "lat": 39.7684,
        "lon": -86.1581,
        "zip_prefix": "462",
        "pop_weight": 2,
        "median_income": 48000,
    },
    {
        "city": "Milwaukee",
        "state": "WI",
        "lat": 43.0389,
        "lon": -87.9065,
        "zip_prefix": "532",
        "pop_weight": 2,
        "median_income": 40000,
    },
    {
        "city": "Minneapolis",
        "state": "MN",
        "lat": 44.9778,
        "lon": -93.2650,
        "zip_prefix": "554",
        "pop_weight": 2,
        "median_income": 58000,
    },
    {
        "city": "St. Louis",
        "state": "MO",
        "lat": 38.6270,
        "lon": -90.1994,
        "zip_prefix": "631",
        "pop_weight": 2,
        "median_income": 42000,
    },
    {
        "city": "Kansas City",
        "state": "MO",
        "lat": 39.0997,
        "lon": -94.5786,
        "zip_prefix": "641",
        "pop_weight": 2,
        "median_income": 50000,
    },
    {
        "city": "Omaha",
        "state": "NE",
        "lat": 41.2565,
        "lon": -95.9345,
        "zip_prefix": "681",
        "pop_weight": 1,
        "median_income": 55000,
    },
    {
        "city": "Tulsa",
        "state": "OK",
        "lat": 36.1540,
        "lon": -95.9928,
        "zip_prefix": "741",
        "pop_weight": 2,
        "median_income": 45000,
    },
    {
        "city": "Oklahoma City",
        "state": "OK",
        "lat": 35.4676,
        "lon": -97.5164,
        "zip_prefix": "731",
        "pop_weight": 2,
        "median_income": 50000,
    },
]

AGE_GROUPS = ["21-30", "31-40", "41-50", "51-60", "61-70", "70+"]
AGE_WEIGHTS = [0.15, 0.20, 0.25, 0.20, 0.12, 0.08]  # Weighted toward middle-age

GENDERS = ["Male", "Female", "Non-binary"]
GENDER_WEIGHTS = [0.48, 0.48, 0.04]

INCOME_BRACKETS = [
    "Under $30K",
    "$30K-$50K",
    "$50K-$75K",
    "$75K-$100K",
    "$100K-$150K",
    "$150K-$250K",
    "$250K+",
]
VISIT_FREQUENCIES = [
    "Weekly",
    "Bi-weekly",
    "Monthly",
    "Quarterly",
    "Annually",
    "Occasional",
]
PREFERRED_GAMING = [
    "Slots",
    "Table Games",
    "Poker",
    "Sports Betting",
    "Video Poker",
    "Keno",
    "Mixed",
]
LOYALTY_TIERS = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Seven Stars"]

PLAYER_SEGMENTS = [
    "High Roller",
    "Frequent Local",
    "Weekend Warrior",
    "Special Occasion",
    "Sports Bettor",
    "Slot Enthusiast",
    "Table Games Pro",
    "Poker Player",
    "Entertainment Seeker",
    "Comp Chaser",
]


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in miles using Haversine formula."""
    earth_radius = 3959  # Earth's radius in miles

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return round(earth_radius * c, 2)


def get_income_bracket(median_income: int, variation: float = 0.5) -> str:
    """Assign income bracket based on location's median income with variation."""
    # Add random variation
    income = median_income * random.uniform(1 - variation, 1 + variation)

    if income < 30000:
        return "Under $30K"
    elif income < 50000:
        return "$30K-$50K"
    elif income < 75000:
        return "$50K-$75K"
    elif income < 100000:
        return "$75K-$100K"
    elif income < 150000:
        return "$100K-$150K"
    elif income < 250000:
        return "$150K-$250K"
    else:
        return "$250K+"


def calculate_ltv(
    visit_frequency: str, income_bracket: str, preferred_gaming: str, years_active: int
) -> float:
    """Calculate estimated lifetime value based on player characteristics."""
    # Base multipliers
    freq_multiplier = {
        "Weekly": 52,
        "Bi-weekly": 26,
        "Monthly": 12,
        "Quarterly": 4,
        "Annually": 1,
        "Occasional": 0.5,
    }.get(visit_frequency, 1)

    income_multiplier = {
        "Under $30K": 50,
        "$30K-$50K": 100,
        "$50K-$75K": 200,
        "$75K-$100K": 400,
        "$100K-$150K": 800,
        "$150K-$250K": 1500,
        "$250K+": 3000,
    }.get(income_bracket, 100)

    gaming_multiplier = {
        "High Roller Table Games": 3.0,
        "Table Games": 2.0,
        "Poker": 1.5,
        "Sports Betting": 1.8,
        "Slots": 1.0,
        "Video Poker": 0.9,
        "Keno": 0.5,
        "Mixed": 1.2,
    }.get(preferred_gaming, 1.0)

    # Calculate LTV
    annual_value = (
        freq_multiplier
        * income_multiplier
        * gaming_multiplier
        * random.uniform(0.5, 2.0)
    )
    ltv = annual_value * years_active

    return round(ltv, 2)


def get_loyalty_tier(ltv: float) -> str:
    """Assign loyalty tier based on LTV."""
    if ltv >= 250000:
        return "Seven Stars"
    elif ltv >= 100000:
        return "Diamond"
    elif ltv >= 50000:
        return "Platinum"
    elif ltv >= 20000:
        return "Gold"
    elif ltv >= 5000:
        return "Silver"
    else:
        return "Bronze"


def assign_player_segment(
    preferred_gaming: str, visit_frequency: str, income_bracket: str, ltv: float
) -> str:
    """Assign a player segment based on characteristics."""
    if ltv > 100000:
        return "High Roller"
    if income_bracket in ["$150K-$250K", "$250K+"]:
        if preferred_gaming == "Table Games":
            return "Table Games Pro"
        elif preferred_gaming == "Poker":
            return "Poker Player"

    if visit_frequency in ["Weekly", "Bi-weekly"]:
        return "Frequent Local"
    elif visit_frequency == "Monthly":
        if preferred_gaming == "Sports Betting":
            return "Sports Bettor"
        return "Weekend Warrior"
    elif preferred_gaming == "Slots":
        return "Slot Enthusiast"
    elif preferred_gaming == "Sports Betting":
        return "Sports Bettor"
    elif visit_frequency in ["Annually", "Occasional"]:
        return random.choice(
            ["Special Occasion", "Entertainment Seeker", "Comp Chaser"]
        )

    return random.choice(PLAYER_SEGMENTS)


def generate_player_demographics(
    count: int = 10000, casino_locations: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    """Generate synthetic player demographic data with geospatial attributes."""

    if casino_locations is None:
        # Use a default Las Vegas casino
        casino_locations = [
            {
                "casino_id": "CAS00001",
                "name": "Default Casino",
                "latitude": 36.1699,
                "longitude": -115.1398,
            }
        ]

    # Weight population centers for selection
    weighted_centers = []
    for center in POPULATION_CENTERS:
        weighted_centers.extend([center] * center["pop_weight"])

    players = []

    for i in range(count):
        # Select home location
        home_center = random.choice(weighted_centers)

        # Add randomness to home coordinates (within ~20 miles)
        lat_offset = random.uniform(-0.3, 0.3)
        lon_offset = random.uniform(-0.3, 0.3)
        home_lat = round(home_center["lat"] + lat_offset, 6)
        home_lon = round(home_center["lon"] + lon_offset, 6)

        # Find nearest casino
        nearest_casino = min(
            casino_locations,
            key=lambda c: haversine_distance(
                home_lat, home_lon, c["latitude"], c["longitude"]
            ),
        )

        distance = haversine_distance(
            home_lat, home_lon, nearest_casino["latitude"], nearest_casino["longitude"]
        )

        # Visit frequency influenced by distance
        if distance < 25:
            visit_weights = [0.15, 0.20, 0.30, 0.20, 0.10, 0.05]
        elif distance < 100:
            visit_weights = [0.05, 0.10, 0.25, 0.30, 0.20, 0.10]
        elif distance < 250:
            visit_weights = [0.02, 0.05, 0.15, 0.30, 0.28, 0.20]
        else:
            visit_weights = [0.01, 0.02, 0.07, 0.20, 0.35, 0.35]

        visit_frequency = random.choices(VISIT_FREQUENCIES, weights=visit_weights)[0]

        # Demographics
        age_group = random.choices(AGE_GROUPS, weights=AGE_WEIGHTS)[0]
        gender = random.choices(GENDERS, weights=GENDER_WEIGHTS)[0]
        income_bracket = get_income_bracket(home_center["median_income"])
        preferred_gaming = random.choice(PREFERRED_GAMING)

        # Calculate years active (influenced by age)
        age_idx = AGE_GROUPS.index(age_group)
        min_years = max(1, age_idx)
        max_years = min(20, age_idx * 5 + 5)
        years_active = random.randint(min_years, max_years)

        active_since = datetime.now() - timedelta(
            days=years_active * 365 + random.randint(0, 364)
        )

        # Calculate LTV and assign tier
        ltv = calculate_ltv(
            visit_frequency, income_bracket, preferred_gaming, years_active
        )
        loyalty_tier = get_loyalty_tier(ltv)
        player_segment = assign_player_segment(
            preferred_gaming, visit_frequency, income_bracket, ltv
        )

        # Market area calculation
        if distance < 50:
            market_type = "Primary"
        elif distance < 150:
            market_type = "Secondary"
        elif distance < 300:
            market_type = "Tertiary"
        else:
            market_type = "Destination"

        player = {
            "player_id": f"PLY{i:08d}",
            "home_casino_id": nearest_casino["casino_id"],
            "home_casino_name": nearest_casino.get("name", "Unknown"),
            "home_latitude": home_lat,
            "home_longitude": home_lon,
            "home_city": home_center["city"],
            "home_state": home_center["state"],
            "home_zip": f"{home_center['zip_prefix']}{random.randint(10, 99)}",
            "distance_to_casino_miles": distance,
            "market_type": market_type,
            "age_group": age_group,
            "gender": gender,
            "income_bracket": income_bracket,
            "visit_frequency": visit_frequency,
            "preferred_gaming": preferred_gaming,
            "loyalty_tier": loyalty_tier,
            "player_segment": player_segment,
            "lifetime_value": ltv,
            "years_active": years_active,
            "active_since": active_since.strftime("%Y-%m-%d"),
            "last_visit": (
                datetime.now() - timedelta(days=random.randint(1, 365))
            ).strftime("%Y-%m-%d"),
            "total_visits_ytd": int(
                {
                    "Weekly": 52,
                    "Bi-weekly": 26,
                    "Monthly": 12,
                    "Quarterly": 4,
                    "Annually": 1,
                    "Occasional": 0,
                }.get(visit_frequency, 1)
                * random.uniform(0.5, 1.2)
            ),
            "avg_trip_worth": round(
                ltv
                / (
                    years_active
                    * max(
                        1,
                        {
                            "Weekly": 52,
                            "Bi-weekly": 26,
                            "Monthly": 12,
                            "Quarterly": 4,
                            "Annually": 1,
                            "Occasional": 0.5,
                        }.get(visit_frequency, 1),
                    )
                ),
                2,
            ),
            "has_hotel_booking": random.random() > (0.9 if distance < 50 else 0.3),
            "has_show_tickets": random.random() > 0.7,
            "has_dining_reservations": random.random() > 0.5,
            "email_opt_in": random.random() > 0.3,
            "sms_opt_in": random.random() > 0.5,
            "direct_mail_opt_in": random.random() > 0.4,
            "geo_point_wkt": f"POINT({home_lon} {home_lat})",
        }

        players.append(player)

    return players


def create_player_geojson(players: list[dict[str, Any]]) -> dict[str, Any]:
    """Convert player list to GeoJSON FeatureCollection."""
    features = []

    for player in players:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [player["home_longitude"], player["home_latitude"]],
            },
            "properties": {
                "player_id": player["player_id"],
                "home_casino_id": player["home_casino_id"],
                "home_city": player["home_city"],
                "home_state": player["home_state"],
                "distance_miles": player["distance_to_casino_miles"],
                "market_type": player["market_type"],
                "age_group": player["age_group"],
                "income_bracket": player["income_bracket"],
                "loyalty_tier": player["loyalty_tier"],
                "player_segment": player["player_segment"],
                "lifetime_value": player["lifetime_value"],
            },
        }
        features.append(feature)

    return {"type": "FeatureCollection", "features": features}


def generate_market_summary(players: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate market analysis summary from player data."""
    summary = {
        "total_players": len(players),
        "by_market_type": {},
        "by_loyalty_tier": {},
        "by_segment": {},
        "by_state": {},
        "avg_ltv_by_market": {},
        "distance_stats": {"avg": 0, "min": float("inf"), "max": 0},
    }

    total_distance = 0
    ltv_by_market = {}
    count_by_market = {}

    for player in players:
        # Market type
        market = player["market_type"]
        summary["by_market_type"][market] = summary["by_market_type"].get(market, 0) + 1

        # Loyalty tier
        tier = player["loyalty_tier"]
        summary["by_loyalty_tier"][tier] = summary["by_loyalty_tier"].get(tier, 0) + 1

        # Segment
        segment = player["player_segment"]
        summary["by_segment"][segment] = summary["by_segment"].get(segment, 0) + 1

        # State
        state = player["home_state"]
        summary["by_state"][state] = summary["by_state"].get(state, 0) + 1

        # Distance
        dist = player["distance_to_casino_miles"]
        total_distance += dist
        summary["distance_stats"]["min"] = min(summary["distance_stats"]["min"], dist)
        summary["distance_stats"]["max"] = max(summary["distance_stats"]["max"], dist)

        # LTV by market
        ltv_by_market[market] = ltv_by_market.get(market, 0) + player["lifetime_value"]
        count_by_market[market] = count_by_market.get(market, 0) + 1

    summary["distance_stats"]["avg"] = round(total_distance / len(players), 2)

    for market in ltv_by_market:
        summary["avg_ltv_by_market"][market] = round(
            ltv_by_market[market] / count_by_market[market], 2
        )

    return summary


def main():
    """Generate player demographic data and export to various formats."""
    # Generate casino locations first (if module available)
    try:
        from casino_locations import generate_us_casino_locations

        casinos = generate_us_casino_locations(100)
        print(f"Generated {len(casinos)} casino locations for reference")
    except ImportError:
        casinos = [
            {
                "casino_id": "CAS00001",
                "name": "Las Vegas Casino",
                "latitude": 36.1699,
                "longitude": -115.1398,
            }
        ]
        print("Using default casino location")

    # Generate players
    players = generate_player_demographics(10000, casinos)
    print(f"Generated {len(players)} player demographics")

    # Export to JSON
    with open("player_demographics.json", "w") as f:
        json.dump(players, f, indent=2)
    print("Exported to player_demographics.json")

    # Export to GeoJSON
    geojson = create_player_geojson(players)
    with open("player_demographics.geojson", "w") as f:
        json.dump(geojson, f, indent=2)
    print("Exported to player_demographics.geojson")

    # Generate and print market summary
    summary = generate_market_summary(players)
    with open("market_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\nMarket Summary:")
    print(json.dumps(summary, indent=2))

    # Print sample player
    print("\nSample player:")
    print(json.dumps(players[0], indent=2))


if __name__ == "__main__":
    main()
