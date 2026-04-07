"""
Casino Location Data Generator

Generates synthetic casino location data across US and global gaming markets.
Includes geospatial attributes for GIS analysis with ArcGIS and Power BI.
"""

import json
import random
from dataclasses import asdict, dataclass
from typing import Any

# Major US gaming markets with coordinates
US_GAMING_MARKETS = [
    # Las Vegas area
    {
        "city": "Las Vegas",
        "state": "NV",
        "region": "West",
        "lat": 36.1699,
        "lon": -115.1398,
        "zip_prefix": "891",
    },
    {
        "city": "Henderson",
        "state": "NV",
        "region": "West",
        "lat": 36.0395,
        "lon": -114.9817,
        "zip_prefix": "890",
    },
    {
        "city": "North Las Vegas",
        "state": "NV",
        "region": "West",
        "lat": 36.1989,
        "lon": -115.1175,
        "zip_prefix": "890",
    },
    {
        "city": "Reno",
        "state": "NV",
        "region": "West",
        "lat": 39.5296,
        "lon": -119.8138,
        "zip_prefix": "895",
    },
    {
        "city": "Laughlin",
        "state": "NV",
        "region": "West",
        "lat": 35.1678,
        "lon": -114.5728,
        "zip_prefix": "890",
    },
    # Atlantic City
    {
        "city": "Atlantic City",
        "state": "NJ",
        "region": "Northeast",
        "lat": 39.3643,
        "lon": -74.4229,
        "zip_prefix": "084",
    },
    # Gulf Coast
    {
        "city": "Biloxi",
        "state": "MS",
        "region": "South",
        "lat": 30.3960,
        "lon": -88.8853,
        "zip_prefix": "395",
    },
    {
        "city": "Gulfport",
        "state": "MS",
        "region": "South",
        "lat": 30.3674,
        "lon": -89.0928,
        "zip_prefix": "395",
    },
    {
        "city": "New Orleans",
        "state": "LA",
        "region": "South",
        "lat": 29.9511,
        "lon": -90.0715,
        "zip_prefix": "701",
    },
    {
        "city": "Lake Charles",
        "state": "LA",
        "region": "South",
        "lat": 30.2266,
        "lon": -93.2174,
        "zip_prefix": "706",
    },
    # Midwest Gaming
    {
        "city": "Detroit",
        "state": "MI",
        "region": "Midwest",
        "lat": 42.3314,
        "lon": -83.0458,
        "zip_prefix": "482",
    },
    {
        "city": "Chicago",
        "state": "IL",
        "region": "Midwest",
        "lat": 41.8781,
        "lon": -87.6298,
        "zip_prefix": "606",
    },
    {
        "city": "St. Louis",
        "state": "MO",
        "region": "Midwest",
        "lat": 38.6270,
        "lon": -90.1994,
        "zip_prefix": "631",
    },
    {
        "city": "Kansas City",
        "state": "MO",
        "region": "Midwest",
        "lat": 39.0997,
        "lon": -94.5786,
        "zip_prefix": "641",
    },
    {
        "city": "Cincinnati",
        "state": "OH",
        "region": "Midwest",
        "lat": 39.1031,
        "lon": -84.5120,
        "zip_prefix": "452",
    },
    {
        "city": "Cleveland",
        "state": "OH",
        "region": "Midwest",
        "lat": 41.4993,
        "lon": -81.6944,
        "zip_prefix": "441",
    },
    # Connecticut Tribal
    {
        "city": "Mashantucket",
        "state": "CT",
        "region": "Northeast",
        "lat": 41.4778,
        "lon": -71.9696,
        "zip_prefix": "063",
    },
    {
        "city": "Uncasville",
        "state": "CT",
        "region": "Northeast",
        "lat": 41.4345,
        "lon": -72.1081,
        "zip_prefix": "063",
    },
    # Pennsylvania
    {
        "city": "Philadelphia",
        "state": "PA",
        "region": "Northeast",
        "lat": 39.9526,
        "lon": -75.1652,
        "zip_prefix": "191",
    },
    {
        "city": "Pittsburgh",
        "state": "PA",
        "region": "Northeast",
        "lat": 40.4406,
        "lon": -79.9959,
        "zip_prefix": "152",
    },
    {
        "city": "Mount Pocono",
        "state": "PA",
        "region": "Northeast",
        "lat": 41.1220,
        "lon": -75.3602,
        "zip_prefix": "183",
    },
    # California Tribal
    {
        "city": "Temecula",
        "state": "CA",
        "region": "West",
        "lat": 33.4936,
        "lon": -117.1484,
        "zip_prefix": "925",
    },
    {
        "city": "San Diego",
        "state": "CA",
        "region": "West",
        "lat": 32.7157,
        "lon": -117.1611,
        "zip_prefix": "921",
    },
    {
        "city": "Palm Springs",
        "state": "CA",
        "region": "West",
        "lat": 33.8303,
        "lon": -116.5453,
        "zip_prefix": "922",
    },
    {
        "city": "Sacramento",
        "state": "CA",
        "region": "West",
        "lat": 38.5816,
        "lon": -121.4944,
        "zip_prefix": "958",
    },
    # Oklahoma Tribal
    {
        "city": "Durant",
        "state": "OK",
        "region": "South",
        "lat": 33.9940,
        "lon": -96.3708,
        "zip_prefix": "747",
    },
    {
        "city": "Tulsa",
        "state": "OK",
        "region": "South",
        "lat": 36.1540,
        "lon": -95.9928,
        "zip_prefix": "741",
    },
    {
        "city": "Oklahoma City",
        "state": "OK",
        "region": "South",
        "lat": 35.4676,
        "lon": -97.5164,
        "zip_prefix": "731",
    },
    # Arizona Tribal
    {
        "city": "Scottsdale",
        "state": "AZ",
        "region": "West",
        "lat": 33.4942,
        "lon": -111.9261,
        "zip_prefix": "852",
    },
    {
        "city": "Phoenix",
        "state": "AZ",
        "region": "West",
        "lat": 33.4484,
        "lon": -112.0740,
        "zip_prefix": "850",
    },
    {
        "city": "Tucson",
        "state": "AZ",
        "region": "West",
        "lat": 32.2226,
        "lon": -110.9747,
        "zip_prefix": "857",
    },
    # Florida
    {
        "city": "Tampa",
        "state": "FL",
        "region": "South",
        "lat": 27.9506,
        "lon": -82.4572,
        "zip_prefix": "336",
    },
    {
        "city": "Fort Lauderdale",
        "state": "FL",
        "region": "South",
        "lat": 26.1224,
        "lon": -80.1373,
        "zip_prefix": "333",
    },
    {
        "city": "Miami",
        "state": "FL",
        "region": "South",
        "lat": 25.7617,
        "lon": -80.1918,
        "zip_prefix": "331",
    },
    # Washington State
    {
        "city": "Seattle",
        "state": "WA",
        "region": "West",
        "lat": 47.6062,
        "lon": -122.3321,
        "zip_prefix": "981",
    },
    {
        "city": "Tacoma",
        "state": "WA",
        "region": "West",
        "lat": 47.2529,
        "lon": -122.4443,
        "zip_prefix": "984",
    },
    # New York
    {
        "city": "Monticello",
        "state": "NY",
        "region": "Northeast",
        "lat": 41.6559,
        "lon": -74.6901,
        "zip_prefix": "127",
    },
    {
        "city": "Schenectady",
        "state": "NY",
        "region": "Northeast",
        "lat": 42.8142,
        "lon": -73.9396,
        "zip_prefix": "123",
    },
]

# Global gaming markets
GLOBAL_GAMING_MARKETS = [
    # Asia Pacific
    {
        "city": "Macau",
        "country": "China",
        "region": "APAC",
        "lat": 22.1987,
        "lon": 113.5439,
        "currency": "MOP",
    },
    {
        "city": "Singapore",
        "country": "Singapore",
        "region": "APAC",
        "lat": 1.2655,
        "lon": 103.8194,
        "currency": "SGD",
    },
    {
        "city": "Manila",
        "country": "Philippines",
        "region": "APAC",
        "lat": 14.5995,
        "lon": 120.9842,
        "currency": "PHP",
    },
    {
        "city": "Melbourne",
        "country": "Australia",
        "region": "APAC",
        "lat": -37.8136,
        "lon": 144.9631,
        "currency": "AUD",
    },
    {
        "city": "Sydney",
        "country": "Australia",
        "region": "APAC",
        "lat": -33.8688,
        "lon": 151.2093,
        "currency": "AUD",
    },
    {
        "city": "Seoul",
        "country": "South Korea",
        "region": "APAC",
        "lat": 37.5665,
        "lon": 126.9780,
        "currency": "KRW",
    },
    {
        "city": "Jeju",
        "country": "South Korea",
        "region": "APAC",
        "lat": 33.4890,
        "lon": 126.4983,
        "currency": "KRW",
    },
    # Europe
    {
        "city": "Monte Carlo",
        "country": "Monaco",
        "region": "EMEA",
        "lat": 43.7384,
        "lon": 7.4246,
        "currency": "EUR",
    },
    {
        "city": "London",
        "country": "UK",
        "region": "EMEA",
        "lat": 51.5074,
        "lon": -0.1278,
        "currency": "GBP",
    },
    {
        "city": "Baden-Baden",
        "country": "Germany",
        "region": "EMEA",
        "lat": 48.7628,
        "lon": 8.2408,
        "currency": "EUR",
    },
    {
        "city": "Malta",
        "country": "Malta",
        "region": "EMEA",
        "lat": 35.9375,
        "lon": 14.3754,
        "currency": "EUR",
    },
    {
        "city": "Prague",
        "country": "Czech Republic",
        "region": "EMEA",
        "lat": 50.0755,
        "lon": 14.4378,
        "currency": "CZK",
    },
    # Americas (non-US)
    {
        "city": "Toronto",
        "country": "Canada",
        "region": "Americas",
        "lat": 43.6532,
        "lon": -79.3832,
        "currency": "CAD",
    },
    {
        "city": "Vancouver",
        "country": "Canada",
        "region": "Americas",
        "lat": 49.2827,
        "lon": -123.1207,
        "currency": "CAD",
    },
    {
        "city": "Niagara Falls",
        "country": "Canada",
        "region": "Americas",
        "lat": 43.0896,
        "lon": -79.0849,
        "currency": "CAD",
    },
    {
        "city": "Mexico City",
        "country": "Mexico",
        "region": "Americas",
        "lat": 19.4326,
        "lon": -99.1332,
        "currency": "MXN",
    },
    {
        "city": "Cancun",
        "country": "Mexico",
        "region": "Americas",
        "lat": 21.1619,
        "lon": -86.8515,
        "currency": "MXN",
    },
    {
        "city": "Nassau",
        "country": "Bahamas",
        "region": "Americas",
        "lat": 25.0343,
        "lon": -77.3963,
        "currency": "BSD",
    },
    {
        "city": "San Juan",
        "country": "Puerto Rico",
        "region": "Americas",
        "lat": 18.4655,
        "lon": -66.1057,
        "currency": "USD",
    },
]

CASINO_BRANDS = [
    "Golden Sands",
    "Silver Creek",
    "Desert Star",
    "River Palace",
    "Mountain View",
    "Sunset",
    "Grand Vista",
    "Royal Oak",
    "Diamond",
    "Emerald",
    "Sapphire",
    "Ruby",
    "Lucky",
    "Fortune",
    "Jackpot",
    "Winners",
    "Eagle",
    "Thunder",
    "Wind River",
    "Rising Sun",
    "Paradise",
    "Oasis",
    "Mirage",
    "Atlantis",
]

PROPERTY_TYPES = ["Resort", "Local", "Riverboat", "Tribal", "Racino"]
REVENUE_TIERS = [
    "Tier 1 ($500M+)",
    "Tier 2 ($250-500M)",
    "Tier 3 ($100-250M)",
    "Tier 4 (<$100M)",
]

GAMING_REGULATIONS = {
    "NV": "Nevada Gaming Control Board",
    "NJ": "New Jersey Casino Control Commission",
    "PA": "Pennsylvania Gaming Control Board",
    "MI": "Michigan Gaming Control Board",
    "MS": "Mississippi Gaming Commission",
    "LA": "Louisiana Gaming Control Board",
    "FL": "Florida Gaming Control Commission",
    "CT": "Connecticut Department of Consumer Protection",
    "CA": "California Gambling Control Commission",
    "OK": "Oklahoma Horse Racing Commission",
    "AZ": "Arizona Department of Gaming",
    "WA": "Washington State Gambling Commission",
    "NY": "New York State Gaming Commission",
    "OH": "Ohio Casino Control Commission",
    "IL": "Illinois Gaming Board",
    "MO": "Missouri Gaming Commission",
}


@dataclass
class CasinoLocation:
    """Casino location with geospatial attributes."""

    casino_id: str
    name: str
    brand: str
    latitude: float
    longitude: float
    address: str
    city: str
    state: str
    zip_code: str
    country: str
    region: str
    property_type: str
    gaming_sqft: int
    hotel_rooms: int
    slot_machines: int
    table_games: int
    poker_tables: int
    sports_book: bool
    opened_date: str
    last_renovation: str | None
    annual_revenue_tier: str
    employee_count: int
    regulatory_body: str
    license_number: str
    latitude_dms: str
    longitude_dms: str
    geo_point_wkt: str


def decimal_to_dms(decimal_degree: float, is_latitude: bool = True) -> str:
    """Convert decimal degrees to degrees/minutes/seconds format."""
    direction = ""
    if is_latitude:
        direction = "N" if decimal_degree >= 0 else "S"
    else:
        direction = "E" if decimal_degree >= 0 else "W"

    decimal_degree = abs(decimal_degree)
    degrees = int(decimal_degree)
    minutes_decimal = (decimal_degree - degrees) * 60
    minutes = int(minutes_decimal)
    seconds = (minutes_decimal - minutes) * 60

    return f"{degrees}{direction} {minutes}' {seconds:.2f}\""


def generate_us_casino_locations(count: int = 100) -> list[dict[str, Any]]:
    """Generate synthetic US casino locations."""
    casinos = []

    for i in range(count):
        market = random.choice(US_GAMING_MARKETS)

        # Add randomness to coordinates (within ~5 miles)
        lat_offset = random.uniform(-0.05, 0.05)
        lon_offset = random.uniform(-0.05, 0.05)
        latitude = round(market["lat"] + lat_offset, 6)
        longitude = round(market["lon"] + lon_offset, 6)

        property_type = random.choice(PROPERTY_TYPES)

        # Scale properties based on property type
        if property_type == "Resort":
            gaming_sqft = random.randint(80000, 200000)
            hotel_rooms = random.randint(1000, 5000)
            slot_machines = random.randint(1500, 4000)
            table_games = random.randint(100, 300)
            poker_tables = random.randint(20, 60)
            revenue_tier = random.choice(REVENUE_TIERS[:2])
            employees = random.randint(3000, 10000)
        elif property_type == "Tribal":
            gaming_sqft = random.randint(40000, 150000)
            hotel_rooms = random.randint(200, 1500)
            slot_machines = random.randint(1000, 3000)
            table_games = random.randint(30, 150)
            poker_tables = random.randint(5, 30)
            revenue_tier = random.choice(REVENUE_TIERS[1:3])
            employees = random.randint(1000, 5000)
        elif property_type == "Racino":
            gaming_sqft = random.randint(30000, 80000)
            hotel_rooms = random.randint(0, 300)
            slot_machines = random.randint(1500, 3500)
            table_games = random.randint(0, 50)
            poker_tables = random.randint(0, 15)
            revenue_tier = random.choice(REVENUE_TIERS[2:])
            employees = random.randint(800, 2500)
        else:  # Local or Riverboat
            gaming_sqft = random.randint(20000, 80000)
            hotel_rooms = random.randint(0, 500)
            slot_machines = random.randint(500, 2000)
            table_games = random.randint(20, 80)
            poker_tables = random.randint(0, 20)
            revenue_tier = random.choice(REVENUE_TIERS[2:])
            employees = random.randint(500, 2500)

        brand = random.choice(CASINO_BRANDS)
        name = f"{brand} {market['city']}"
        if random.random() > 0.7:
            name += (
                f" {random.choice(['Resort', 'Casino', 'Hotel & Casino', 'Gaming'])}"
            )

        opened_year = random.randint(1990, 2020)
        regulatory_body = GAMING_REGULATIONS.get(
            market["state"], "State Gaming Commission"
        )

        casino = CasinoLocation(
            casino_id=f"CAS{i:05d}",
            name=name,
            brand=brand,
            latitude=latitude,
            longitude=longitude,
            address=f"{random.randint(100, 9999)} Gaming Blvd",
            city=market["city"],
            state=market["state"],
            zip_code=f"{market['zip_prefix']}{random.randint(10, 99)}",
            country="USA",
            region=market["region"],
            property_type=property_type,
            gaming_sqft=gaming_sqft,
            hotel_rooms=hotel_rooms,
            slot_machines=slot_machines,
            table_games=table_games,
            poker_tables=poker_tables,
            sports_book=random.random() > 0.3,
            opened_date=f"{opened_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            last_renovation=(
                f"{random.randint(opened_year+1, 2024)}-{random.randint(1,12):02d}-01"
                if random.random() > 0.3
                else None
            ),
            annual_revenue_tier=revenue_tier,
            employee_count=employees,
            regulatory_body=regulatory_body,
            license_number=f"GL-{market['state']}-{random.randint(10000, 99999)}",
            latitude_dms=decimal_to_dms(latitude, True),
            longitude_dms=decimal_to_dms(longitude, False),
            geo_point_wkt=f"POINT({longitude} {latitude})",
        )

        casinos.append(asdict(casino))

    return casinos


def generate_global_casino_locations(count: int = 50) -> list[dict[str, Any]]:
    """Generate synthetic international casino locations."""
    casinos = []

    for i in range(count):
        market = random.choice(GLOBAL_GAMING_MARKETS)

        lat_offset = random.uniform(-0.02, 0.02)
        lon_offset = random.uniform(-0.02, 0.02)
        latitude = round(market["lat"] + lat_offset, 6)
        longitude = round(market["lon"] + lon_offset, 6)

        # International casinos tend to be larger resorts
        gaming_sqft = random.randint(50000, 300000)
        hotel_rooms = random.randint(500, 6000)
        slot_machines = random.randint(800, 5000)
        table_games = random.randint(50, 500)
        poker_tables = random.randint(10, 100)

        brand = random.choice(CASINO_BRANDS)
        name = f"Grand {brand} {market['city']}"

        opened_year = random.randint(1980, 2022)

        casino = {
            "casino_id": f"INT{i:05d}",
            "name": name,
            "brand": brand,
            "latitude": latitude,
            "longitude": longitude,
            "address": f"{random.randint(1, 999)} Casino Avenue",
            "city": market["city"],
            "state": None,
            "zip_code": None,
            "country": market["country"],
            "region": market["region"],
            "property_type": "Resort",
            "gaming_sqft": gaming_sqft,
            "hotel_rooms": hotel_rooms,
            "slot_machines": slot_machines,
            "table_games": table_games,
            "poker_tables": poker_tables,
            "sports_book": random.random() > 0.4,
            "opened_date": f"{opened_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "last_renovation": (
                f"{random.randint(opened_year+1, 2024)}-{random.randint(1,12):02d}-01"
                if random.random() > 0.4
                else None
            ),
            "annual_revenue_tier": random.choice(REVENUE_TIERS[:3]),
            "employee_count": random.randint(2000, 15000),
            "regulatory_body": f"{market['country']} Gaming Authority",
            "license_number": f"INTL-{market['country'][:3].upper()}-{random.randint(10000, 99999)}",
            "currency": market.get("currency", "USD"),
            "timezone": None,  # Would be populated based on coordinates
            "latitude_dms": decimal_to_dms(latitude, True),
            "longitude_dms": decimal_to_dms(longitude, False),
            "geo_point_wkt": f"POINT({longitude} {latitude})",
        }

        casinos.append(casino)

    return casinos


def create_geojson(casinos: list[dict[str, Any]]) -> dict[str, Any]:
    """Convert casino list to GeoJSON FeatureCollection."""
    features = []

    for casino in casinos:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [casino["longitude"], casino["latitude"]],
            },
            "properties": {
                k: v
                for k, v in casino.items()
                if k
                not in [
                    "latitude",
                    "longitude",
                    "geo_point_wkt",
                    "latitude_dms",
                    "longitude_dms",
                ]
            },
        }
        features.append(feature)

    return {"type": "FeatureCollection", "features": features}


def main():
    """Generate casino location data and export to various formats."""
    # Generate US casinos
    us_casinos = generate_us_casino_locations(100)
    print(f"Generated {len(us_casinos)} US casino locations")

    # Generate international casinos
    global_casinos = generate_global_casino_locations(50)
    print(f"Generated {len(global_casinos)} international casino locations")

    # Combine all casinos
    all_casinos = us_casinos + global_casinos

    # Export to JSON
    with open("casino_locations.json", "w") as f:
        json.dump(all_casinos, f, indent=2)
    print("Exported to casino_locations.json")

    # Export to GeoJSON
    geojson = create_geojson(all_casinos)
    with open("casino_locations.geojson", "w") as f:
        json.dump(geojson, f, indent=2)
    print("Exported to casino_locations.geojson")

    # Print sample
    print("\nSample casino:")
    print(json.dumps(us_casinos[0], indent=2))


if __name__ == "__main__":
    main()
