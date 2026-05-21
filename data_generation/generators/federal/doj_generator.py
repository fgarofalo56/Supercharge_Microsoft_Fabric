"""
DOJ Data Generator
==================

Generates synthetic Department of Justice data for four domains:

- crime_stats      : FBI UCR/NIBRS crime incident data
- federal_cases    : USSC federal sentencing statistics
- antitrust        : DOJ Antitrust Division merger/cartel enforcement
- drug_enforcement : DEA drug seizure statistics

Data schemas mirror publicly available datasets from FBI Crime Data Explorer,
US Sentencing Commission, DOJ Antitrust Division, and DEA.
"""

from datetime import datetime, timedelta
from typing import Any

from ..base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# NIBRS Offense Codes (30 most common FBI NIBRS categories)
# ---------------------------------------------------------------------------
NIBRS_OFFENSES: dict[str, dict[str, str]] = {
    "09A": {
        "description": "Murder and Nonnegligent Manslaughter",
        "category": "Persons",
    },
    "09B": {"description": "Negligent Manslaughter", "category": "Persons"},
    "100": {"description": "Kidnapping/Abduction", "category": "Persons"},
    "11A": {"description": "Rape", "category": "Persons"},
    "11B": {"description": "Sodomy", "category": "Persons"},
    "120": {"description": "Robbery", "category": "Persons"},
    "13A": {"description": "Aggravated Assault", "category": "Persons"},
    "13B": {"description": "Simple Assault", "category": "Persons"},
    "13C": {"description": "Intimidation", "category": "Persons"},
    "200": {"description": "Arson", "category": "Property"},
    "220": {"description": "Burglary/Breaking and Entering", "category": "Property"},
    "23A": {"description": "Pocket-picking", "category": "Property"},
    "23B": {"description": "Purse-snatching", "category": "Property"},
    "23C": {"description": "Shoplifting", "category": "Property"},
    "23D": {"description": "Theft From Building", "category": "Property"},
    "23F": {"description": "Theft From Motor Vehicle", "category": "Property"},
    "23H": {"description": "All Other Larceny", "category": "Property"},
    "240": {"description": "Motor Vehicle Theft", "category": "Property"},
    "250": {"description": "Counterfeiting/Forgery", "category": "Property"},
    "26A": {
        "description": "False Pretenses/Swindle/Confidence Game",
        "category": "Property",
    },
    "26B": {
        "description": "Credit Card/Automated Teller Machine Fraud",
        "category": "Property",
    },
    "26C": {"description": "Impersonation", "category": "Property"},
    "270": {"description": "Embezzlement", "category": "Property"},
    "280": {"description": "Stolen Property Offenses", "category": "Property"},
    "290": {
        "description": "Destruction/Damage/Vandalism of Property",
        "category": "Property",
    },
    "35A": {"description": "Drug/Narcotic Violations", "category": "Society"},
    "35B": {"description": "Drug Equipment Violations", "category": "Society"},
    "370": {"description": "Pornography/Obscene Material", "category": "Society"},
    "40A": {"description": "Prostitution", "category": "Society"},
    "520": {"description": "Weapon Law Violations", "category": "Society"},
}

NIBRS_CODES = list(NIBRS_OFFENSES.keys())

# Weighted toward most common offenses
NIBRS_WEIGHTS: list[float] = [
    0.0082,
    0.001,
    0.0051,
    0.0154,
    0.0021,
    0.0154,
    0.0462,
    0.1232,
    0.0411,
    0.0051,
    0.0616,
    0.0051,
    0.0031,
    0.0821,
    0.0308,
    0.0513,
    0.1027,
    0.0513,
    0.0154,
    0.0308,
    0.0205,
    0.0103,
    0.0103,
    0.0154,
    0.0821,
    0.0821,
    0.0308,
    0.0103,
    0.0051,
    0.0361,
]

# ---------------------------------------------------------------------------
# Federal Districts (94 judicial districts)
# ---------------------------------------------------------------------------
FEDERAL_DISTRICTS: list[str] = [
    "SDNY",
    "EDNY",
    "NDIL",
    "CDCA",
    "SDCA",
    "NDCA",
    "EDPA",
    "WDPA",
    "DMD",
    "EDVA",
    "WDVA",
    "SDFL",
    "MDFL",
    "NDFL",
    "SDTX",
    "WDTX",
    "NDTX",
    "EDTX",
    "EDMI",
    "WDMI",
    "NJ",
    "MA",
    "CT",
    "EDLA",
    "WDLA",
    "MDLA",
    "EDMO",
    "WDMO",
    "NDG",
    "SDG",
    "EDWI",
    "WDWI",
    "CO",
    "AZ",
    "NV",
    "OR",
    "EDWA",
    "WDWA",
    "MN",
    "SDIA",
    "NDIA",
    "EDAR",
    "WDAR",
    "EDKY",
    "WDKY",
    "MDNC",
    "EDNC",
    "WDNC",
    "EDTN",
    "MDTN",
    "WDTN",
    "NDOH",
    "SDOH",
    "EDIN",
    "NDIN",
    "SDIN",
    "NDAL",
    "MDAL",
    "SDAL",
    "NDMS",
    "SDMS",
    "NDOK",
    "EDOK",
    "WDOK",
    "KS",
    "NE",
    "NM",
    "UT",
    "ID",
    "MT",
    "WY",
    "NDWV",
    "SDWV",
    "SC",
    "HI",
    "AK",
    "ME",
    "NH",
    "VT",
    "RI",
    "DC",
    "PR",
    "USVI",
    "GUAM",
    "CNMI",
    "EDSC",
    "WDSC",
    "NDGA",
    "MDGA",
    "SDGA",
    "EDNY_MAG",
    "SDNY_MAG",
    "CDCA_MAG",
    "SDCA_MAG",
    "NDIL_MAG",
]

# District weighting: use uniform distribution (rng.choice handles it)
# High-volume districts are over-represented via the offense generation logic

FEDERAL_CIRCUITS: dict[str, str] = {
    "1st": "ME, MA, NH, RI, PR",
    "2nd": "CT, NY, VT, USVI",
    "3rd": "DE, NJ, PA",
    "4th": "MD, NC, SC, VA, WV",
    "5th": "LA, MS, TX",
    "6th": "KY, MI, OH, TN",
    "7th": "IL, IN, WI",
    "8th": "AR, IA, MN, MO, NE, ND, SD",
    "9th": "AK, AZ, CA, HI, ID, MT, NV, OR, WA, GUAM, CNMI",
    "10th": "CO, KS, NM, OK, UT, WY",
    "11th": "AL, FL, GA",
    "DC": "DC",
    "Federal": "Nationwide (patent, trade, government contracts)",
}

CIRCUIT_LIST = list(FEDERAL_CIRCUITS.keys())

# ---------------------------------------------------------------------------
# Federal Offense Categories (USSC classification)
# ---------------------------------------------------------------------------
OFFENSE_CATEGORIES: list[str] = [
    "Drug Trafficking",
    "Fraud/Theft/Embezzlement",
    "Immigration",
    "Firearms",
    "Sex Offenses",
    "Money Laundering",
    "Racketeering/Extortion",
    "Tax Offenses",
    "Assault",
    "Robbery",
    "Child Pornography",
    "Environmental/Wildlife",
    "Antitrust",
    "Other",
]

OFFENSE_WEIGHTS: list[float] = [
    0.28,
    0.18,
    0.14,
    0.12,
    0.05,
    0.04,
    0.03,
    0.03,
    0.03,
    0.02,
    0.03,
    0.01,
    0.01,
    0.03,
]

# ---------------------------------------------------------------------------
# DEA Field Divisions (23 divisions)
# ---------------------------------------------------------------------------
DEA_DIVISIONS: list[str] = [
    "Atlanta",
    "Boston",
    "Caribbean",
    "Chicago",
    "Dallas",
    "Denver",
    "Detroit",
    "El Paso",
    "Houston",
    "Los Angeles",
    "Louisville",
    "Miami",
    "Newark",
    "New England",
    "New Orleans",
    "New York",
    "Philadelphia",
    "Phoenix",
    "San Diego",
    "San Francisco",
    "Seattle",
    "St. Louis",
    "Washington DC",
]

DEA_WEIGHTS: list[float] = [
    0.0377,
    0.0283,
    0.0472,
    0.0566,
    0.0472,
    0.0283,
    0.0377,
    0.0660,
    0.0566,
    0.0755,
    0.0283,
    0.0660,
    0.0377,
    0.0283,
    0.0377,
    0.0566,
    0.0377,
    0.0472,
    0.0566,
    0.0377,
    0.0283,
    0.0283,
    0.0285,
]

DRUG_TYPES: list[str] = [
    "Cocaine",
    "Heroin",
    "Fentanyl",
    "Methamphetamine",
    "Cannabis",
    "MDMA",
    "Other",
]

DRUG_WEIGHTS: list[float] = [0.18, 0.10, 0.22, 0.25, 0.15, 0.03, 0.07]

DRUG_SCHEDULES: dict[str, str] = {
    "Cocaine": "II",
    "Heroin": "I",
    "Fentanyl": "II",
    "Methamphetamine": "II",
    "Cannabis": "I",
    "MDMA": "I",
    "Other": "I",
}

# Street value per kg (approximate USD, for realistic estimation)
STREET_VALUE_PER_KG: dict[str, tuple[float, float]] = {
    "Cocaine": (25_000, 40_000),
    "Heroin": (50_000, 80_000),
    "Fentanyl": (100_000, 250_000),
    "Methamphetamine": (10_000, 25_000),
    "Cannabis": (1_000, 5_000),
    "MDMA": (15_000, 35_000),
    "Other": (5_000, 20_000),
}

# ---------------------------------------------------------------------------
# Antitrust Reference Data
# ---------------------------------------------------------------------------
ANTITRUST_INDUSTRIES: dict[str, str] = {
    "21": "Mining, Quarrying, and Oil/Gas Extraction",
    "22": "Utilities",
    "31": "Manufacturing - Food/Beverage/Textile",
    "32": "Manufacturing - Wood/Paper/Chemical/Plastics",
    "33": "Manufacturing - Metals/Machinery/Electronics",
    "42": "Wholesale Trade",
    "44": "Retail Trade - Motor Vehicle/Furniture/Electronics",
    "45": "Retail Trade - Sporting/General/Misc",
    "48": "Transportation and Warehousing",
    "51": "Information/Media/Telecommunications",
    "52": "Finance and Insurance",
    "53": "Real Estate",
    "54": "Professional, Scientific, Technical Services",
    "56": "Administrative and Support/Waste Management",
    "62": "Health Care and Social Assistance",
    "72": "Accommodation and Food Services",
}

ANTITRUST_INDUSTRY_CODES = list(ANTITRUST_INDUSTRIES.keys())
ANTITRUST_INDUSTRY_WEIGHTS: list[float] = [
    0.04,
    0.05,
    0.08,
    0.07,
    0.08,
    0.06,
    0.06,
    0.04,
    0.06,
    0.12,
    0.08,
    0.04,
    0.06,
    0.03,
    0.08,
    0.05,
]

CARTEL_TYPES: list[str] = [
    "Price-fixing",
    "Bid-rigging",
    "Market Allocation",
    "None",
]
CARTEL_WEIGHTS: list[float] = [0.35, 0.25, 0.15, 0.25]

DOJ_ACTIONS: list[str] = [
    "Approved",
    "Challenged",
    "Consent Decree",
    "Blocked",
    "Abandoned",
]
DOJ_ACTION_WEIGHTS: list[float] = [0.55, 0.15, 0.12, 0.05, 0.13]

# US states (shared with other generators)
US_STATES = [
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
    "DC",
    "PR",
]

STATE_WEIGHTS: list[float] = [
    0.0143,
    0.0048,
    0.0210,
    0.0095,
    0.1144,
    0.0172,
    0.0105,
    0.0038,
    0.0629,
    0.0315,
    0.0048,
    0.0057,
    0.0381,
    0.0200,
    0.0095,
    0.0086,
    0.0133,
    0.0143,
    0.0038,
    0.0181,
    0.0210,
    0.0305,
    0.0172,
    0.0095,
    0.0181,
    0.0038,
    0.0057,
    0.0095,
    0.0038,
    0.0276,
    0.0067,
    0.0601,
    0.0315,
    0.0029,
    0.0353,
    0.0124,
    0.0124,
    0.0391,
    0.0038,
    0.0153,
    0.0029,
    0.0210,
    0.0858,
    0.0095,
    0.0019,
    0.0257,
    0.0229,
    0.0057,
    0.0181,
    0.0019,
    0.0076,
    0.0047,
]

# ---------------------------------------------------------------------------
# Agency Types (for crime_stats ORI codes)
# ---------------------------------------------------------------------------
AGENCY_TYPES: list[str] = [
    "City",
    "County",
    "State",
    "Federal",
    "Tribal",
]
AGENCY_TYPE_WEIGHTS: list[float] = [0.55, 0.25, 0.10, 0.07, 0.03]

WEAPON_TYPES: list[str] = [
    "None",
    "Firearm",
    "Knife/Cutting Instrument",
    "Other",
]
WEAPON_WEIGHTS: list[float] = [0.55, 0.22, 0.10, 0.13]

LOCATION_TYPES: list[str] = [
    "Residence/Home",
    "Highway/Road/Alley",
    "Parking Lot/Garage",
    "Commercial/Office Building",
    "Convenience Store",
    "Department Store",
    "Restaurant",
    "School/College",
    "Hotel/Motel",
    "Bar/Nightclub",
    "Government/Public Building",
    "Church/Synagogue/Temple",
    "Park/Playground",
    "Drug Store/Doctor/Hospital",
    "Other/Unknown",
]

CLEARANCE_STATUSES: list[str] = [
    "Cleared by Arrest",
    "Not Cleared",
    "Exceptionally Cleared",
]
CLEARANCE_WEIGHTS: list[float] = [0.38, 0.52, 0.10]

POPULATION_GROUPS: list[str] = [
    "City 250K+",
    "City 100K-249K",
    "City 50K-99K",
    "City 25K-49K",
    "City 10K-24K",
    "City <10K",
    "County 100K+",
    "County 25K-99K",
    "County <25K",
]


# ---------------------------------------------------------------------------
# Per-domain configuration
# ---------------------------------------------------------------------------
_DOMAIN_CONFIG: dict[str, dict[str, Any]] = {
    "crime_stats": {
        "label": "FBI UCR/NIBRS Crime Statistics",
    },
    "federal_cases": {
        "label": "USSC Federal Sentencing Statistics",
        "departure_types": ["None", "Above", "Below", "Substantial Assistance"],
        "departure_weights": [0.50, 0.05, 0.25, 0.20],
        "plea_types": ["Guilty Plea", "Not Guilty", "Nolo Contendere"],
        "plea_weights": [0.90, 0.08, 0.02],
        "trial_outcomes": ["Plea Agreement", "Bench Trial", "Jury Trial"],
        "trial_weights": [0.90, 0.03, 0.07],
        "criminal_history_categories": ["I", "II", "III", "IV", "V", "VI"],
        "history_weights": [0.42, 0.15, 0.13, 0.10, 0.08, 0.12],
    },
    "antitrust": {
        "label": "DOJ Antitrust Enforcement",
        "case_types": ["Criminal", "Civil", "Merger Review"],
        "case_type_weights": [0.20, 0.25, 0.55],
        "case_statuses": ["Open", "Closed", "Consent Decree", "Dismissed"],
        "status_weights": [0.15, 0.50, 0.20, 0.15],
    },
    "drug_enforcement": {
        "label": "DEA Drug Seizure Statistics",
        "seizure_types": ["Land", "Maritime", "Air", "Mail/Parcel"],
        "seizure_weights": [0.55, 0.15, 0.10, 0.20],
    },
}


class DOJGenerator(BaseGenerator):
    """
    Generate synthetic DOJ data records for four domains.

    Supported domains
    -----------------
    crime_stats      - FBI UCR/NIBRS crime incident reports
    federal_cases    - USSC federal sentencing statistics
    antitrust        - DOJ Antitrust Division enforcement actions
    drug_enforcement - DEA drug seizure statistics
    """

    VALID_DOMAINS = ("crime_stats", "federal_cases", "antitrust", "drug_enforcement")

    def __init__(
        self,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Initialize the DOJ generator.

        Args:
            seed: Random seed for reproducibility.
            start_date: Earliest date for generated records.
            end_date: Latest date for generated records.
        """
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)

        self._schema = {
            # crime_stats fields
            "incident_id": "string",
            "ori_code": "string",
            "agency_name": "string",
            "agency_type": "string",
            "state_code": "string",
            "incident_date": "string",
            "offense_code": "string",
            "offense_category": "string",
            "offense_description": "string",
            "victim_count": "int",
            "offender_count": "int",
            "arrest_made": "boolean",
            "weapon_involved": "string",
            "location_type": "string",
            "clearance_status": "string",
            "population_group": "string",
            "reporting_year": "int",
            # federal_cases fields
            "case_id": "string",
            "district_court": "string",
            "circuit": "string",
            "filing_date": "string",
            "sentencing_date": "string",
            "primary_offense": "string",
            "offense_category_federal": "string",
            "guideline_range_min_months": "int",
            "guideline_range_max_months": "int",
            "sentence_months": "int",
            "departure_type": "string",
            "fine_amount": "float",
            "restitution_amount": "float",
            "defendant_age": "int",
            "defendant_gender": "string",
            "defendant_race": "string",
            "defendant_citizenship": "string",
            "criminal_history_category": "string",
            "plea_type": "string",
            "trial_outcome": "string",
            # antitrust fields
            "case_type": "string",
            "case_status": "string",
            "industry_sector": "string",
            "industry_name": "string",
            "acquiring_party": "string",
            "target_party": "string",
            "transaction_value_usd": "float",
            "hhi_pre_merger": "int",
            "hhi_post_merger": "int",
            "hhi_delta": "int",
            "market_definition": "string",
            "doj_action": "string",
            "penalty_amount_usd": "float",
            "cartel_type": "string",
            "affected_commerce_usd": "float",
            "defendant_count": "int",
            "hsr_filing_flag": "boolean",
            "second_request_flag": "boolean",
            "fiscal_year": "int",
            # drug_enforcement fields
            "seizure_id": "string",
            "seizure_date": "string",
            "dea_region": "string",
            "drug_type": "string",
            "drug_schedule": "string",
            "quantity_kg": "float",
            "estimated_street_value_usd": "float",
            "seizure_type": "string",
            "operation_name": "string",
            "arrests_count": "int",
            "quarter": "int",
            "load_time": "string",
        }

    # ------------------------------------------------------------------
    # Abstract method implementation
    # ------------------------------------------------------------------

    def generate_record(self, domain: str = "crime_stats") -> dict[str, Any]:  # type: ignore[override]
        """
        Generate a single DOJ record.

        Args:
            domain: One of 'crime_stats', 'federal_cases', 'antitrust',
                    'drug_enforcement'.

        Returns:
            Dictionary containing one record plus metadata columns.
        """
        if domain not in self.VALID_DOMAINS:
            raise ValueError(
                f"Invalid domain '{domain}'. Choose from {self.VALID_DOMAINS}."
            )

        if domain == "crime_stats":
            return self._generate_crime_stats()
        elif domain == "federal_cases":
            return self._generate_federal_case()
        elif domain == "antitrust":
            return self._generate_antitrust()
        else:
            return self._generate_drug_enforcement()

    # ------------------------------------------------------------------
    # Batch helper
    # ------------------------------------------------------------------

    def generate_batch(  # type: ignore[override]
        self, count: int = 1000, domain: str = "crime_stats"
    ) -> list[dict[str, Any]]:
        """
        Generate a batch of DOJ records.

        Args:
            count: Number of records to generate.
            domain: Domain ('crime_stats', 'federal_cases', 'antitrust',
                    'drug_enforcement').

        Returns:
            List of record dictionaries.
        """
        if domain not in self.VALID_DOMAINS:
            raise ValueError(
                f"Invalid domain '{domain}'. Choose from {self.VALID_DOMAINS}."
            )
        return [self.generate_record(domain=domain) for _ in range(count)]

    # ------------------------------------------------------------------
    # Domain: crime_stats (FBI UCR/NIBRS)
    # ------------------------------------------------------------------

    def _generate_crime_stats(self) -> dict[str, Any]:
        """Generate a single FBI crime incident record."""
        state = self.weighted_choice(US_STATES, STATE_WEIGHTS)
        offense_code = self.weighted_choice(NIBRS_CODES, NIBRS_WEIGHTS)
        offense_info = NIBRS_OFFENSES[offense_code]
        incident_dt = self.random_datetime()
        agency_type = self.weighted_choice(AGENCY_TYPES, AGENCY_TYPE_WEIGHTS)

        # ORI code format: 2-letter state + agency type prefix + 5-digit number
        ori_prefix = {
            "City": "PD",
            "County": "SO",
            "State": "SP",
            "Federal": "FB",
            "Tribal": "TB",
        }
        ori_num = int(self.rng.integers(10000, 99999))
        ori_code = f"{state}{ori_prefix[agency_type]}{ori_num}"

        record: dict[str, Any] = {
            "incident_id": self.generate_uuid(),
            "ori_code": ori_code,
            "agency_name": f"{self.faker.city()} {agency_type} {ori_prefix[agency_type]}",
            "agency_type": agency_type,
            "state_code": state,
            "incident_date": incident_dt.strftime("%Y-%m-%d"),
            "offense_code": offense_code,
            "offense_category": offense_info["category"],
            "offense_description": offense_info["description"],
            "victim_count": self._generate_victim_count(offense_info["category"]),
            "offender_count": max(1, int(self.rng.poisson(1.3))),
            "arrest_made": bool(self.rng.random() < 0.42),
            "weapon_involved": self.weighted_choice(WEAPON_TYPES, WEAPON_WEIGHTS),
            "location_type": str(self.rng.choice(LOCATION_TYPES)),
            "clearance_status": self.weighted_choice(
                CLEARANCE_STATUSES, CLEARANCE_WEIGHTS
            ),
            "population_group": str(self.rng.choice(POPULATION_GROUPS)),
            "reporting_year": incident_dt.year,
            "load_time": datetime.now().isoformat(),
        }
        return self.add_metadata_columns(record)

    def _generate_victim_count(self, category: str) -> int:
        """Generate realistic victim count based on offense category."""
        if category == "Society":
            return 0  # victimless/society crimes
        elif category == "Property":
            return max(1, int(self.rng.poisson(1.2)))
        else:  # Persons
            return max(1, int(self.rng.poisson(1.5)))

    # ------------------------------------------------------------------
    # Domain: federal_cases (USSC Sentencing)
    # ------------------------------------------------------------------

    def _generate_federal_case(self) -> dict[str, Any]:
        """Generate a single USSC federal sentencing record."""
        cfg = _DOMAIN_CONFIG["federal_cases"]
        district = str(self.rng.choice(FEDERAL_DISTRICTS))
        circuit = str(self.rng.choice(CIRCUIT_LIST))
        offense_cat = self.weighted_choice(OFFENSE_CATEGORIES, OFFENSE_WEIGHTS)

        filing_dt = self.random_datetime()
        # Sentencing typically 6-18 months after filing
        months_to_sentence = int(self.rng.integers(6, 19))
        sentencing_dt = filing_dt + timedelta(days=months_to_sentence * 30)

        guideline_min = self._generate_guideline_range(offense_cat)
        guideline_max = guideline_min + int(self.rng.integers(6, 60))
        sentence = self._generate_sentence(guideline_min, guideline_max, cfg)

        # Demographics (matching USSC published distributions)
        age = int(self.rng.integers(18, 76))
        gender = self.weighted_choice(["Male", "Female"], [0.87, 0.13])
        race = self.weighted_choice(
            ["White", "Black", "Hispanic", "Asian", "Other"],
            [0.22, 0.20, 0.50, 0.03, 0.05],
        )
        citizenship = self.weighted_choice(
            ["US Citizen", "Non-US Citizen"],
            [0.60, 0.40],
        )

        departure = self.weighted_choice(
            cfg["departure_types"], cfg["departure_weights"]
        )
        fine_amount = (
            round(self.rng.uniform(0, 250_000), 2) if self.rng.random() < 0.30 else 0.0
        )
        restitution = (
            round(self.rng.uniform(0, 5_000_000), 2)
            if self.rng.random() < 0.20
            else 0.0
        )

        record: dict[str, Any] = {
            "case_id": self.generate_uuid(),
            "district_court": district,
            "circuit": circuit,
            "filing_date": filing_dt.strftime("%Y-%m-%d"),
            "sentencing_date": sentencing_dt.strftime("%Y-%m-%d"),
            "primary_offense": f"18 USC {int(self.rng.integers(100, 2000))}",
            "offense_category": offense_cat,
            "guideline_range_min_months": guideline_min,
            "guideline_range_max_months": guideline_max,
            "sentence_months": sentence,
            "departure_type": departure,
            "fine_amount": fine_amount,
            "restitution_amount": restitution,
            "defendant_age": age,
            "defendant_gender": gender,
            "defendant_race": race,
            "defendant_citizenship": citizenship,
            "criminal_history_category": self.weighted_choice(
                cfg["criminal_history_categories"], cfg["history_weights"]
            ),
            "plea_type": self.weighted_choice(cfg["plea_types"], cfg["plea_weights"]),
            "trial_outcome": self.weighted_choice(
                cfg["trial_outcomes"], cfg["trial_weights"]
            ),
            "fiscal_year": filing_dt.year,
            "load_time": datetime.now().isoformat(),
        }
        return self.add_metadata_columns(record)

    def _generate_guideline_range(self, offense_category: str) -> int:
        """Generate guideline minimum months based on offense type."""
        ranges: dict[str, tuple[int, int]] = {
            "Drug Trafficking": (24, 120),
            "Fraud/Theft/Embezzlement": (6, 60),
            "Immigration": (1, 24),
            "Firearms": (12, 120),
            "Sex Offenses": (24, 180),
            "Money Laundering": (12, 60),
            "Racketeering/Extortion": (24, 120),
            "Tax Offenses": (6, 36),
            "Assault": (12, 60),
            "Robbery": (24, 120),
            "Child Pornography": (24, 120),
            "Environmental/Wildlife": (1, 24),
            "Antitrust": (6, 36),
            "Other": (1, 60),
        }
        low, high = ranges.get(offense_category, (1, 60))
        return int(self.rng.integers(low, high + 1))

    def _generate_sentence(
        self, guideline_min: int, guideline_max: int, cfg: dict[str, Any]
    ) -> int:
        """Generate actual sentence considering departures."""
        # Most sentences within guideline range
        base = int(self.rng.integers(guideline_min, guideline_max + 1))
        departure = self.weighted_choice(
            cfg["departure_types"], cfg["departure_weights"]
        )
        if departure == "Above":
            return int(base * self.rng.uniform(1.05, 1.50))
        elif departure == "Below":
            return max(0, int(base * self.rng.uniform(0.50, 0.95)))
        elif departure == "Substantial Assistance":
            return max(0, int(base * self.rng.uniform(0.25, 0.70)))
        return base

    # ------------------------------------------------------------------
    # Domain: antitrust (DOJ Antitrust Division)
    # ------------------------------------------------------------------

    def _generate_antitrust(self) -> dict[str, Any]:
        """Generate a single DOJ antitrust enforcement record."""
        cfg = _DOMAIN_CONFIG["antitrust"]
        case_type = self.weighted_choice(cfg["case_types"], cfg["case_type_weights"])
        industry_code = self.weighted_choice(
            ANTITRUST_INDUSTRY_CODES, ANTITRUST_INDUSTRY_WEIGHTS
        )

        filing_dt = self.random_datetime()
        # Resolution 6-36 months later (or None if still open)
        resolution_dt = None
        case_status = self.weighted_choice(cfg["case_statuses"], cfg["status_weights"])
        if case_status != "Open":
            months_to_resolve = int(self.rng.integers(6, 37))
            resolution_dt = filing_dt + timedelta(days=months_to_resolve * 30)

        # HHI (Herfindahl-Hirschman Index) for merger cases
        hhi_pre = int(self.rng.integers(800, 4000))
        hhi_delta = int(self.rng.integers(50, 1500))
        hhi_post = hhi_pre + hhi_delta

        # Transaction values (right-skewed)
        transaction_value = self._generate_transaction_value(case_type)

        # DOJ action depends on HHI concentration
        doj_action = self._determine_doj_action(hhi_post, hhi_delta, case_type)

        # Cartel type only for criminal cases
        cartel_type = "None"
        if case_type == "Criminal":
            cartel_type = self.weighted_choice(CARTEL_TYPES, CARTEL_WEIGHTS)

        # Penalties
        penalty = self._generate_penalty(case_type, cartel_type, transaction_value)

        record: dict[str, Any] = {
            "case_id": self.generate_uuid(),
            "case_type": case_type,
            "filing_date": filing_dt.strftime("%Y-%m-%d"),
            "resolution_date": resolution_dt.strftime("%Y-%m-%d")
            if resolution_dt
            else None,
            "case_status": case_status,
            "industry_sector": industry_code,
            "industry_name": ANTITRUST_INDUSTRIES[industry_code],
            "acquiring_party": self.faker.company()
            if case_type == "Merger Review"
            else None,
            "target_party": self.faker.company()
            if case_type == "Merger Review"
            else None,
            "transaction_value_usd": transaction_value,
            "hhi_pre_merger": hhi_pre if case_type == "Merger Review" else None,
            "hhi_post_merger": hhi_post if case_type == "Merger Review" else None,
            "hhi_delta": hhi_delta if case_type == "Merger Review" else None,
            "market_definition": self._generate_market_definition(industry_code),
            "doj_action": doj_action,
            "penalty_amount_usd": penalty,
            "cartel_type": cartel_type,
            "affected_commerce_usd": round(
                transaction_value * self.rng.uniform(0.5, 3.0), 2
            )
            if case_type == "Criminal"
            else None,
            "defendant_count": int(self.rng.integers(1, 12))
            if case_type == "Criminal"
            else None,
            "hsr_filing_flag": case_type == "Merger Review",
            "second_request_flag": (
                case_type == "Merger Review" and self.rng.random() < 0.04
            ),
            "fiscal_year": filing_dt.year,
            "load_time": datetime.now().isoformat(),
        }
        return self.add_metadata_columns(record)

    def _generate_transaction_value(self, case_type: str) -> float:
        """Generate realistic transaction/deal value."""
        if case_type == "Merger Review":
            # HSR threshold is $111.4M (2024); most filings $100M-$50B
            tier = self.rng.random()
            if tier < 0.40:
                return round(self.rng.uniform(111_400_000, 500_000_000), 2)
            elif tier < 0.75:
                return round(self.rng.uniform(500_000_000, 5_000_000_000), 2)
            elif tier < 0.95:
                return round(self.rng.uniform(5_000_000_000, 25_000_000_000), 2)
            else:
                return round(self.rng.uniform(25_000_000_000, 100_000_000_000), 2)
        elif case_type == "Criminal":
            # Cartel affected commerce
            return round(self.rng.uniform(1_000_000, 500_000_000), 2)
        else:
            # Civil case value
            return round(self.rng.uniform(10_000_000, 10_000_000_000), 2)

    def _determine_doj_action(
        self, hhi_post: int, hhi_delta: int, case_type: str
    ) -> str:
        """Determine DOJ action based on HHI thresholds (2023 Merger Guidelines).

        Per the 2023 DOJ/FTC Merger Guidelines:
        - HHI > 2,500 AND delta > 200: presumptively anticompetitive
        - HHI > 1,800 AND delta > 100: also potentially problematic
        - Lower values: generally approved
        """
        if case_type != "Merger Review":
            return self.weighted_choice(DOJ_ACTIONS, DOJ_ACTION_WEIGHTS)

        # Apply 2023 Merger Guidelines HHI thresholds
        if hhi_post > 2500 and hhi_delta > 200:
            # Highly concentrated market with significant increase
            return self.weighted_choice(
                ["Challenged", "Consent Decree", "Blocked", "Abandoned"],
                [0.35, 0.30, 0.15, 0.20],
            )
        elif hhi_post > 1800 and hhi_delta > 100:
            # Moderately concentrated with meaningful increase
            return self.weighted_choice(
                ["Approved", "Challenged", "Consent Decree", "Abandoned"],
                [0.40, 0.25, 0.20, 0.15],
            )
        else:
            # Low concentration: usually approved
            return self.weighted_choice(
                ["Approved", "Challenged", "Consent Decree"],
                [0.85, 0.08, 0.07],
            )

    def _generate_penalty(
        self, case_type: str, cartel_type: str, transaction_value: float
    ) -> float:
        """Generate penalty amount based on case type and severity."""
        if case_type == "Criminal" and cartel_type != "None":
            # Criminal cartel penalties: typically 10-20% of affected commerce
            # or up to $100M per count
            return round(
                min(transaction_value * self.rng.uniform(0.05, 0.25), 100_000_000), 2
            )
        elif case_type == "Civil":
            # Civil penalties: generally lower
            return (
                round(self.rng.uniform(0, 10_000_000), 2)
                if self.rng.random() < 0.30
                else 0.0
            )
        else:
            return 0.0  # Merger reviews don't carry direct penalties

    def _generate_market_definition(self, industry_code: str) -> str:
        """Generate a plausible relevant market definition."""
        markets: dict[str, list[str]] = {
            "21": [
                "US crude oil production",
                "Permian Basin natural gas",
                "coal mining equipment",
            ],
            "22": ["Southeast electric power generation", "natural gas distribution"],
            "31": [
                "packaged snack foods",
                "carbonated soft drinks",
                "poultry processing",
            ],
            "32": [
                "commodity chemicals",
                "containerboard packaging",
                "generic pharmaceuticals",
            ],
            "33": [
                "automotive semiconductors",
                "enterprise networking equipment",
                "steel flat products",
            ],
            "42": ["pharmaceutical distribution", "foodservice distribution"],
            "44": ["new automobile dealerships", "consumer electronics retail"],
            "45": ["sporting goods retail", "e-commerce marketplace platforms"],
            "48": [
                "domestic air travel",
                "ocean container shipping",
                "railroad freight",
            ],
            "51": [
                "broadband internet service",
                "enterprise cloud computing",
                "digital advertising",
            ],
            "52": [
                "commercial banking",
                "health insurance exchange",
                "payment processing",
            ],
            "53": ["commercial real estate brokerage", "single-family rental housing"],
            "54": ["management consulting", "IT staffing services"],
            "56": ["commercial waste hauling", "temporary staffing"],
            "62": ["hospital inpatient services", "dialysis services", "generic drugs"],
            "72": ["limited-service restaurants", "economy hotel lodging"],
        }
        choices = markets.get(industry_code, ["general commerce"])
        return str(self.rng.choice(choices))

    # ------------------------------------------------------------------
    # Domain: drug_enforcement (DEA)
    # ------------------------------------------------------------------

    def _generate_drug_enforcement(self) -> dict[str, Any]:
        """Generate a single DEA drug seizure record."""
        cfg = _DOMAIN_CONFIG["drug_enforcement"]
        drug_type = self.weighted_choice(DRUG_TYPES, DRUG_WEIGHTS)
        region = self.weighted_choice(DEA_DIVISIONS, DEA_WEIGHTS)
        seizure_dt = self.random_datetime()

        # Quantity varies dramatically by drug type
        quantity_kg = self._generate_seizure_quantity(drug_type)
        value_range = STREET_VALUE_PER_KG[drug_type]
        street_value = round(
            quantity_kg * self.rng.uniform(value_range[0], value_range[1]), 2
        )

        # Operation name (~15% of seizures are part of named operations)
        operation_name = None
        if self.rng.random() < 0.15:
            op_prefixes = ["Operation", "Project", "Task Force"]
            op_names = [
                "Dark Web",
                "Pipeline",
                "Fury",
                "Crystal Clear",
                "Border Shield",
                "Deadfall",
                "Snowfall",
                "Overdrive",
                "Iron Curtain",
                "Blue Lightning",
                "Rolling Thunder",
            ]
            operation_name = (
                f"{self.rng.choice(op_prefixes)} {self.rng.choice(op_names)}"
            )

        record: dict[str, Any] = {
            "seizure_id": self.generate_uuid(),
            "seizure_date": seizure_dt.strftime("%Y-%m-%d"),
            "dea_region": region,
            "state_code": self.weighted_choice(US_STATES, STATE_WEIGHTS),
            "drug_type": drug_type,
            "drug_schedule": DRUG_SCHEDULES[drug_type],
            "quantity_kg": round(quantity_kg, 3),
            "estimated_street_value_usd": street_value,
            "seizure_type": self.weighted_choice(
                cfg["seizure_types"], cfg["seizure_weights"]
            ),
            "operation_name": operation_name,
            "arrests_count": int(self.rng.integers(0, 15)),
            "fiscal_year": seizure_dt.year,
            "quarter": (seizure_dt.month - 1) // 3 + 1,
            "load_time": datetime.now().isoformat(),
        }
        return self.add_metadata_columns(record)

    def _generate_seizure_quantity(self, drug_type: str) -> float:
        """Generate realistic seizure quantity in kg based on drug type."""
        ranges: dict[str, tuple[float, float, float, float]] = {
            # (small_max, mid_max, large_max, mega_max) in kg
            "Cocaine": (1.0, 50.0, 500.0, 5000.0),
            "Heroin": (0.1, 10.0, 100.0, 500.0),
            "Fentanyl": (0.01, 2.0, 50.0, 200.0),
            "Methamphetamine": (0.5, 25.0, 250.0, 2000.0),
            "Cannabis": (5.0, 100.0, 2000.0, 20000.0),
            "MDMA": (0.1, 5.0, 50.0, 200.0),
            "Other": (0.1, 10.0, 100.0, 500.0),
        }
        r = ranges[drug_type]
        tier = self.rng.random()
        if tier < 0.50:
            return float(self.rng.uniform(0.001, r[0]))
        elif tier < 0.80:
            return float(self.rng.uniform(r[0], r[1]))
        elif tier < 0.95:
            return float(self.rng.uniform(r[1], r[2]))
        else:
            return float(self.rng.uniform(r[2], r[3]))
