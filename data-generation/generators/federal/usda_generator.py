"""
USDA Generator
==============

Generates synthetic USDA (United States Department of Agriculture) data for two domains:

- crop_production: NASS (National Agricultural Statistics Service) crop survey records
  covering commodities, yields, planted/harvested acreage, and prices by state/county.

- food_safety: FSIS (Food Safety and Inspection Service) recall records covering
  meat, poultry, and processed food recalls with class, reason, and distribution.

Data shapes mirror the USDA NASS QuickStats API response and the FSIS recall dataset
so generated records can be joined with real public data for POC demonstrations.
"""

from datetime import datetime, date
from typing import Any, Literal

import numpy as np

from ..base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# Domain type alias
# ---------------------------------------------------------------------------
DomainType = Literal["crop_production", "food_safety"]

# ---------------------------------------------------------------------------
# US State FIPS lookup (covers the 20 most agriculturally significant states
# plus enough coverage for a nationally representative distribution)
# ---------------------------------------------------------------------------
STATE_FIPS: dict[str, str] = {
    "01": "ALABAMA",
    "04": "ARIZONA",
    "05": "ARKANSAS",
    "06": "CALIFORNIA",
    "08": "COLORADO",
    "17": "ILLINOIS",
    "18": "INDIANA",
    "19": "IOWA",
    "20": "KANSAS",
    "21": "KENTUCKY",
    "27": "MINNESOTA",
    "28": "MISSISSIPPI",
    "29": "MISSOURI",
    "31": "NEBRASKA",
    "37": "NORTH CAROLINA",
    "38": "NORTH DAKOTA",
    "39": "OHIO",
    "40": "OKLAHOMA",
    "42": "PENNSYLVANIA",
    "45": "SOUTH CAROLINA",
    "46": "SOUTH DAKOTA",
    "47": "TENNESSEE",
    "48": "TEXAS",
    "55": "WISCONSIN",
    "56": "WYOMING",
}

# Abbreviated state codes used in food-safety records
STATE_ABBR: dict[str, str] = {
    "01": "AL", "04": "AZ", "05": "AR", "06": "CA", "08": "CO",
    "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY",
    "27": "MN", "28": "MS", "29": "MO", "31": "NE", "37": "NC",
    "38": "ND", "39": "OH", "40": "OK", "42": "PA", "45": "SC",
    "46": "SD", "47": "TN", "48": "TX", "55": "WI", "56": "WY",
}

_FIPS_KEYS = list(STATE_FIPS.keys())

# ---------------------------------------------------------------------------
# Crop production configuration
# ---------------------------------------------------------------------------
COMMODITIES = [
    "CORN", "SOYBEANS", "WHEAT", "COTTON", "RICE",
    "BARLEY", "OATS", "SORGHUM", "HAY", "POTATOES",
]

# Weighted distribution: corn and soybeans dominate US cropland
COMMODITY_WEIGHTS = [0.28, 0.24, 0.16, 0.07, 0.05, 0.05, 0.04, 0.04, 0.04, 0.03]

STATISTIC_CATEGORIES = [
    "AREA PLANTED",
    "AREA HARVESTED",
    "YIELD",
    "PRODUCTION",
    "PRICE RECEIVED",
]

STATISTIC_WEIGHTS = [0.25, 0.25, 0.20, 0.20, 0.10]

# Unit and realistic value range per statistic category
_STAT_META: dict[str, dict[str, Any]] = {
    "AREA PLANTED":   {"unit": "ACRES",    "low": 50_000,   "high": 12_000_000},
    "AREA HARVESTED": {"unit": "ACRES",    "low": 40_000,   "high": 11_500_000},
    "YIELD":          {"unit": "BU / ACRE","low": 10.0,     "high": 250.0},
    "PRODUCTION":     {"unit": "BU",       "low": 500_000,  "high": 2_000_000_000},
    "PRICE RECEIVED": {"unit": "$ / BU",   "low": 2.50,     "high": 18.00},
}

SOURCE_DESCS = ["SURVEY", "CENSUS"]
SOURCE_WEIGHTS = [0.85, 0.15]

AGG_LEVELS = ["NATIONAL", "STATE", "COUNTY"]
AGG_WEIGHTS = [0.10, 0.50, 0.40]

MONTHS = [
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
]

# ---------------------------------------------------------------------------
# Food safety configuration
# ---------------------------------------------------------------------------
PRODUCT_TYPES = ["BEEF", "POULTRY", "PORK", "PROCESSED", "READY-TO-EAT", "IMPORTED", "OTHER"]
PRODUCT_WEIGHTS = [0.28, 0.22, 0.18, 0.14, 0.10, 0.05, 0.03]

RECALL_CLASSES = ["Class I", "Class II", "Class III"]
RECALL_CLASS_WEIGHTS = [0.55, 0.35, 0.10]   # Class I (health hazard) is most common

RECALL_REASONS = [
    "E. coli O157:H7 contamination",
    "Salmonella contamination",
    "Listeria monocytogenes contamination",
    "Undeclared allergen - milk",
    "Undeclared allergen - soy",
    "Undeclared allergen - wheat (gluten)",
    "Undeclared allergen - peanuts",
    "Foreign material contamination - metal fragments",
    "Foreign material contamination - plastic pieces",
    "Foreign material contamination - bone fragments",
    "Improper labeling - net weight discrepancy",
    "Temperature abuse during transport",
    "Inadequate cooking instructions",
    "Campylobacter contamination",
    "Product produced under insanitary conditions",
]

REASON_WEIGHTS = [
    0.14, 0.14, 0.12,
    0.08, 0.07, 0.07, 0.06,
    0.07, 0.05, 0.04,
    0.05, 0.04, 0.03,
    0.03, 0.01,
]

RECALL_RISK: dict[str, str] = {
    "Class I":   "HIGH",
    "Class II":  "MEDIUM",
    "Class III": "LOW",
}

RECALL_STATUSES = ["OPEN", "CLOSED", "EXPANDED"]
STATUS_WEIGHTS = [0.30, 0.60, 0.10]


class USDAGenerator(BaseGenerator):
    """
    Generate synthetic USDA crop production and food safety recall data.

    Supports two domains controlled via the ``domain`` parameter on
    :meth:`generate_record` and :meth:`generate_batch`:

    - ``"crop_production"`` (default) – NASS QuickStats-style records
    - ``"food_safety"`` – FSIS recall-style records
    """

    def __init__(
        self,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Initialize the USDA generator.

        Args:
            seed: Random seed for reproducibility.
            start_date: Start date used by :meth:`random_datetime`.
            end_date: End date used by :meth:`random_datetime`.
        """
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)

        # Schema reflects the union of both domains; active fields depend on domain.
        self._schema = {
            # Shared / metadata
            "record_id": "string",
            "load_time": "datetime",
            # Crop production fields
            "commodity": "string",
            "year": "int",
            "state_fips": "string",
            "state_name": "string",
            "county_fips": "string",
            "county_name": "string",
            "statisticcat_desc": "string",
            "unit_desc": "string",
            "value": "float",
            "cv_percent": "float",
            "source_desc": "string",
            "agg_level_desc": "string",
            "domain_desc": "string",
            "reference_period_desc": "string",
            # Food safety fields
            "recall_id": "string",
            "recall_number": "string",
            "recall_date": "string",
            "product_type": "string",
            "recall_class": "string",
            "reason": "string",
            "risk_level": "string",
            "company_name": "string",
            "establishment_number": "string",
            "city": "string",
            "state": "string",
            "pounds_recalled": "float",
            "distribution": "string",
            "status": "string",
            "press_release_url": "string",
        }

    # ------------------------------------------------------------------
    # Abstract method implementation (default domain: crop_production)
    # ------------------------------------------------------------------

    def generate_record(self, domain: DomainType = "crop_production") -> dict[str, Any]:
        """
        Generate a single USDA record for the specified domain.

        Args:
            domain: ``"crop_production"`` or ``"food_safety"``.

        Returns:
            Dictionary with domain-specific fields plus standard metadata columns.
        """
        if domain == "crop_production":
            return self._generate_crop_production_record()
        elif domain == "food_safety":
            return self._generate_food_safety_record()
        else:
            raise ValueError(f"Unknown domain '{domain}'. Must be 'crop_production' or 'food_safety'.")

    # ------------------------------------------------------------------
    # Batch helper
    # ------------------------------------------------------------------

    def generate_batch(
        self,
        count: int = 1000,
        domain: DomainType = "crop_production",
    ) -> "pd.DataFrame":  # type: ignore[name-defined]  # noqa: F821
        """
        Generate a batch of USDA records for the specified domain.

        Args:
            count: Number of records to generate.
            domain: ``"crop_production"`` or ``"food_safety"``.

        Returns:
            :class:`pandas.DataFrame` containing ``count`` rows.
        """
        import pandas as pd  # local import keeps the class importable without pandas

        records = [self.generate_record(domain=domain) for _ in range(count)]
        return pd.DataFrame(records)

    # ------------------------------------------------------------------
    # Crop production record builder
    # ------------------------------------------------------------------

    def _generate_crop_production_record(self) -> dict[str, Any]:
        """Build a single NASS QuickStats-style crop production record."""
        commodity = self.weighted_choice(COMMODITIES, COMMODITY_WEIGHTS)
        stat_cat = self.weighted_choice(STATISTIC_CATEGORIES, STATISTIC_WEIGHTS)
        agg_level = self.weighted_choice(AGG_LEVELS, AGG_WEIGHTS)
        source_desc = self.weighted_choice(SOURCE_DESCS, SOURCE_WEIGHTS)
        year = int(np.random.randint(2015, 2026))  # 2015–2025 inclusive

        # Geography
        state_fips = str(np.random.choice(_FIPS_KEYS))
        state_name = STATE_FIPS[state_fips]
        county_fips: str | None = None
        county_name: str | None = None
        if agg_level == "COUNTY":
            # Generate a plausible 5-digit FIPS (state prefix + 3-digit county code)
            county_suffix = f"{np.random.randint(1, 200):03d}"
            county_fips = f"{state_fips}{county_suffix}"
            county_name = self.faker.city() + " County"

        # Realistic value range for the statistic category
        meta = _STAT_META[stat_cat]
        value = round(float(np.random.uniform(meta["low"], meta["high"])), 2)

        # CV% applies to survey estimates; not applicable for Census
        cv_percent: float | None = None
        if source_desc == "SURVEY" and np.random.random() < 0.75:
            cv_percent = round(float(np.random.uniform(1.0, 25.0)), 1)

        # Reference period: annual or a specific month
        use_month = np.random.random() < 0.25
        reference_period_desc = (
            str(np.random.choice(MONTHS)) if use_month else "YEAR"
        )

        record: dict[str, Any] = {
            "record_id": self.generate_uuid(),
            "commodity": commodity,
            "year": year,
            "state_fips": state_fips,
            "state_name": state_name,
            "county_fips": county_fips,
            "county_name": county_name,
            "statisticcat_desc": stat_cat,
            "unit_desc": meta["unit"],
            "value": value,
            "cv_percent": cv_percent,
            "source_desc": source_desc,
            "agg_level_desc": agg_level,
            "domain_desc": "TOTAL",
            "reference_period_desc": reference_period_desc,
            "load_time": datetime.now().isoformat(),
        }

        return self.add_metadata_columns(record)

    # ------------------------------------------------------------------
    # Food safety record builder
    # ------------------------------------------------------------------

    def _generate_food_safety_record(self) -> dict[str, Any]:
        """Build a single FSIS recall-style food safety record."""
        recall_class = self.weighted_choice(RECALL_CLASSES, RECALL_CLASS_WEIGHTS)
        product_type = self.weighted_choice(PRODUCT_TYPES, PRODUCT_WEIGHTS)
        reason = self.weighted_choice(RECALL_REASONS, REASON_WEIGHTS)
        status = self.weighted_choice(RECALL_STATUSES, STATUS_WEIGHTS)

        # Recall date: random date between start_date and end_date
        recall_dt = self.random_datetime()
        recall_date_str = recall_dt.strftime("%Y-%m-%d")
        recall_year = recall_dt.year

        # Recall number pattern: FSIS-YYYY-NNN
        recall_seq = int(np.random.randint(1, 500))
        recall_number = f"FSIS-{recall_year}-{recall_seq:03d}"

        # State geography
        state_fips = str(np.random.choice(_FIPS_KEYS))
        state_abbr = STATE_ABBR[state_fips]

        # Optional establishment number (80 % present)
        establishment_number: str | None = None
        if np.random.random() < 0.80:
            est_num = int(np.random.randint(100, 99999))
            establishment_number = f"EST. {est_num}"

        # Optional city (70 % present)
        city: str | None = self.faker.city() if np.random.random() < 0.70 else None

        # Optional pounds recalled (90 % present, realistic range)
        pounds_recalled: float | None = None
        if np.random.random() < 0.90:
            pounds_recalled = round(float(np.random.uniform(100.0, 2_500_000.0)), 0)

        # Distribution scope
        distribution: str | None = None
        dist_roll = np.random.random()
        if dist_roll < 0.50:
            distribution = "Nationwide"
        elif dist_roll < 0.85:
            # 2–6 state abbreviations
            n_states = int(np.random.randint(2, 7))
            sampled = np.random.choice(list(STATE_ABBR.values()), size=n_states, replace=False)
            distribution = ", ".join(sorted(str(s) for s in sampled))
        # else: None (distribution unknown)

        record: dict[str, Any] = {
            "recall_id": self.generate_uuid(),
            "recall_number": recall_number,
            "recall_date": recall_date_str,
            "product_type": product_type,
            "recall_class": recall_class,
            "reason": reason,
            "risk_level": RECALL_RISK[recall_class],
            "company_name": self.faker.company(),
            "establishment_number": establishment_number,
            "city": city,
            "state": state_abbr,
            "pounds_recalled": pounds_recalled,
            "distribution": distribution,
            "status": status,
            "press_release_url": None,
            "load_time": datetime.now().isoformat(),
        }

        return self.add_metadata_columns(record)
