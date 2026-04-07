"""
SBA Loan Generator
==================

Generates synthetic Small Business Administration (SBA) loan data for four programs:

- ppp      : Paycheck Protection Program (COVID-era forgivable loans)
- 7a       : SBA 7(a) general small-business loans
- disaster : SBA Disaster Loans (physical/economic injury)
- sbir     : Small Business Innovation Research grants/contracts

Data schema mirrors the public SBA FOIA datasets published on data.sba.gov.
"""

from datetime import datetime, timedelta
from typing import Any

from ..base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# NAICS reference table (code -> description)
# ---------------------------------------------------------------------------
NAICS_CODES: dict[str, str] = {
    "722511": "Full-Service Restaurants",
    "722513": "Limited-Service Restaurants",
    "236220": "Commercial and Institutional Building Construction",
    "236115": "New Single-Family Housing Construction",
    "541511": "Custom Computer Programming Services",
    "541512": "Computer Systems Design Services",
    "621111": "Offices of Physicians (except Mental Health Specialists)",
    "621210": "Offices of Dentists",
    "811111": "General Automotive Repair",
    "811121": "Automotive Body, Paint, and Interior Repair and Maintenance",
    "448140": "Family Clothing Stores",
    "448110": "Men's Clothing Stores",
    "452319": "All Other General Merchandise Stores",
    "531110": "Lessors of Residential Buildings and Dwellings",
    "561320": "Temporary Help Services",
    "611110": "Elementary and Secondary Schools",
    "712110": "Museums",
    "713210": "Casinos (except Casino Hotels)",
    "524114": "Direct Health and Medical Insurance Carriers",
    "336111": "Automobile Manufacturing",
}

NAICS_LIST = list(NAICS_CODES.keys())

# ---------------------------------------------------------------------------
# US state codes
# ---------------------------------------------------------------------------
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
    "GU",
]

# Weighted toward the largest states by small-business count
STATE_WEIGHTS: list[float] = [
    0.015,
    0.005,
    0.022,
    0.012,
    0.111,
    0.020,
    0.013,
    0.004,
    0.065,
    0.038,
    0.005,
    0.006,
    0.040,
    0.020,
    0.010,
    0.009,
    0.013,
    0.016,
    0.005,
    0.020,
    0.022,
    0.025,
    0.018,
    0.009,
    0.018,
    0.004,
    0.007,
    0.011,
    0.005,
    0.028,
    0.007,
    0.055,
    0.032,
    0.003,
    0.035,
    0.012,
    0.013,
    0.038,
    0.004,
    0.015,
    0.003,
    0.019,
    0.065,
    0.009,
    0.003,
    0.027,
    0.023,
    0.006,
    0.017,
    0.002,
    0.008,
    0.006,
    0.002,
]

# ---------------------------------------------------------------------------
# Real lender names
# ---------------------------------------------------------------------------
LENDERS = [
    "JPMorgan Chase Bank, National Association",
    "Bank of America, National Association",
    "Wells Fargo Bank, National Association",
    "U.S. Bank National Association",
    "PNC Bank, National Association",
    "Truist Bank",
    "Citizens Bank, National Association",
    "Regions Bank",
    "Fifth Third Bank, National Association",
    "KeyBank National Association",
    "Huntington National Bank",
    "TD Bank, National Association",
    "Flagstar Bank, FSB",
    "Comerica Bank",
    "First National Bank of Omaha",
    "Live Oak Banking Company",
    "Newtek Small Business Finance, LLC",
    "Harvest Small Business Finance, LLC",
    "Byline Bank",
    "ReadyCap Lending, LLC",
]

LENDER_WEIGHTS: list[float] = [
    0.12,
    0.11,
    0.10,
    0.07,
    0.07,
    0.06,
    0.05,
    0.05,
    0.04,
    0.04,
    0.04,
    0.04,
    0.03,
    0.03,
    0.03,
    0.03,
    0.03,
    0.03,
    0.02,
    0.01,
]

BUSINESS_TYPES = [
    "SOLE_PROPRIETORSHIP",
    "LLC",
    "CORPORATION",
    "PARTNERSHIP",
    "NON_PROFIT",
    "OTHER",
]

BUSINESS_TYPE_WEIGHTS: list[float] = [0.28, 0.35, 0.20, 0.08, 0.06, 0.03]

RURAL_URBAN = ["RURAL", "URBAN", "UNDEFINED"]
RURAL_URBAN_WEIGHTS: list[float] = [0.22, 0.71, 0.07]

# ---------------------------------------------------------------------------
# Per-domain configuration
# ---------------------------------------------------------------------------
_DOMAIN_CONFIG: dict[str, dict[str, Any]] = {
    "ppp": {
        "program_type": "PPP",
        "loan_status_choices": ["APPROVED", "PAID_IN_FULL", "CHARGED_OFF", "CANCELLED"],
        "loan_status_weights": [0.03, 0.88, 0.05, 0.04],
        "term_choices": [24, 60],
        "term_weights": [0.55, 0.45],
        "interest_rate": 1.0,
    },
    "7a": {
        "program_type": "7A",
        "loan_status_choices": [
            "APPROVED",
            "ACTIVE",
            "PAID_IN_FULL",
            "CHARGED_OFF",
            "CANCELLED",
        ],
        "loan_status_weights": [0.05, 0.40, 0.42, 0.08, 0.05],
        "term_min": 60,
        "term_max": 300,
        "rate_min": 5.5,
        "rate_max": 8.0,
    },
    "disaster": {
        "program_type": "DISASTER",
        "loan_status_choices": [
            "APPROVED",
            "ACTIVE",
            "PAID_IN_FULL",
            "CHARGED_OFF",
            "CANCELLED",
        ],
        "loan_status_weights": [0.08, 0.45, 0.35, 0.07, 0.05],
        "term_choices": [360],
        "term_weights": [1.0],
        "rate_min": 2.0,
        "rate_max": 4.0,
    },
    "sbir": {
        "program_type": "SBIR",
        "loan_status_choices": ["APPROVED", "ACTIVE", "PAID_IN_FULL", "CANCELLED"],
        "loan_status_weights": [0.10, 0.50, 0.35, 0.05],
        "term_min": 12,
        "term_max": 36,
        "rate_min": 0.0,
        "rate_max": 0.0,
    },
}


class SBAGenerator(BaseGenerator):
    """
    Generate synthetic SBA loan records for four program types.

    Supported domains
    -----------------
    ppp      – Paycheck Protection Program forgivable loans
    7a       – SBA 7(a) general-purpose small-business loans
    disaster – SBA physical / economic-injury disaster loans
    sbir     – Small Business Innovation Research awards
    """

    VALID_DOMAINS = ("ppp", "7a", "disaster", "sbir")

    def __init__(
        self,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Initialize the SBA generator.

        Args:
            seed: Random seed for reproducibility.
            start_date: Earliest approval date for generated loans.
            end_date: Latest approval date for generated loans.
        """
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)

        self._schema = {
            "loan_id": "string",
            "program_type": "string",
            "loan_amount": "float",
            "approval_date": "string",
            "borrower_name": "string",
            "borrower_city": "string",
            "borrower_state": "string",
            "borrower_zip": "string",
            "naics_code": "string",
            "naics_description": "string",
            "jobs_retained": "int",
            "lender_name": "string",
            "sba_office": "string",
            "loan_status": "string",
            "forgiveness_amount": "float",
            "forgiveness_date": "string",
            "term_months": "int",
            "interest_rate": "float",
            "rural_urban": "string",
            "business_type": "string",
            "load_time": "string",
        }

    # ------------------------------------------------------------------
    # Abstract method implementation
    # ------------------------------------------------------------------

    def generate_record(self, domain: str = "ppp") -> dict[str, Any]:  # type: ignore[override]
        """
        Generate a single SBA loan record.

        Args:
            domain: One of 'ppp', '7a', 'disaster', 'sbir'.

        Returns:
            Dictionary containing one loan record plus metadata columns.
        """
        if domain not in self.VALID_DOMAINS:
            raise ValueError(
                f"Invalid domain '{domain}'. Choose from {self.VALID_DOMAINS}."
            )

        cfg = _DOMAIN_CONFIG[domain]

        loan_amount = self._generate_loan_amount(domain)
        approval_dt = self.random_datetime()
        approval_date_str = approval_dt.strftime("%Y-%m-%d")
        loan_status = self.weighted_choice(
            cfg["loan_status_choices"], cfg["loan_status_weights"]
        )
        naics_code = str(self.rng.choice(NAICS_LIST))
        borrower_state = self.weighted_choice(US_STATES, STATE_WEIGHTS)

        # Nullable city (~5 % missing to mirror real data)
        borrower_city: str | None = (
            self.faker.city() if self.rng.random() > 0.05 else None
        )

        record: dict[str, Any] = {
            "loan_id": self.generate_uuid(),
            "program_type": cfg["program_type"],
            "loan_amount": loan_amount,
            "approval_date": approval_date_str,
            "borrower_name": self.faker.company(),
            "borrower_city": borrower_city,
            "borrower_state": borrower_state,
            "borrower_zip": self.faker.zipcode(),
            "naics_code": naics_code,
            "naics_description": NAICS_CODES[naics_code],
            "jobs_retained": self._generate_jobs_retained(),
            "lender_name": self.weighted_choice(LENDERS, LENDER_WEIGHTS),
            "sba_office": None,
            "loan_status": loan_status,
            "forgiveness_amount": None,
            "forgiveness_date": None,
            "term_months": self._generate_term(domain, cfg),
            "interest_rate": self._generate_interest_rate(domain, cfg),
            "rural_urban": self.weighted_choice(RURAL_URBAN, RURAL_URBAN_WEIGHTS),
            "business_type": self.weighted_choice(
                BUSINESS_TYPES, BUSINESS_TYPE_WEIGHTS
            ),
            "load_time": datetime.now().isoformat(),
        }

        # PPP forgiveness fields
        if domain == "ppp":
            record["forgiveness_amount"], record["forgiveness_date"] = (
                self._generate_forgiveness(loan_amount, loan_status, approval_dt)
            )

        return self.add_metadata_columns(record)

    # ------------------------------------------------------------------
    # Batch helper
    # ------------------------------------------------------------------

    def generate_batch(  # type: ignore[override]
        self, count: int = 1000, domain: str = "ppp"
    ) -> list[dict[str, Any]]:
        """
        Generate a batch of SBA loan records.

        Args:
            count: Number of records to generate.
            domain: Program domain ('ppp', '7a', 'disaster', 'sbir').

        Returns:
            List of record dictionaries.
        """
        if domain not in self.VALID_DOMAINS:
            raise ValueError(
                f"Invalid domain '{domain}'. Choose from {self.VALID_DOMAINS}."
            )
        return [self.generate_record(domain=domain) for _ in range(count)]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generate_loan_amount(self, domain: str) -> float:
        """Return a realistic loan amount for the given program domain."""
        if domain == "ppp":
            # Highly right-skewed: most loans $20K-$150K, long tail to $10M
            tier = self.rng.random()
            if tier < 0.55:
                # Small businesses: $20K-$150K
                return round(self.rng.uniform(20_000, 150_000), 2)
            elif tier < 0.80:
                # Mid-size: $150K-$500K
                return round(self.rng.uniform(150_000, 500_000), 2)
            elif tier < 0.95:
                # Larger: $500K-$2M
                return round(self.rng.uniform(500_000, 2_000_000), 2)
            else:
                # Max band: $2M-$10M
                return round(self.rng.uniform(2_000_000, 10_000_000), 2)

        elif domain == "7a":
            tier = self.rng.random()
            if tier < 0.40:
                return round(self.rng.uniform(5_000, 150_000), 2)
            elif tier < 0.75:
                return round(self.rng.uniform(150_000, 1_000_000), 2)
            else:
                return round(self.rng.uniform(1_000_000, 5_000_000), 2)

        elif domain == "disaster":
            return round(self.rng.uniform(1_000, 2_000_000), 2)

        else:  # sbir
            tier = self.rng.random()
            if tier < 0.60:
                # Phase I awards ~$50K-$250K
                return round(self.rng.uniform(50_000, 250_000), 2)
            else:
                # Phase II awards ~$250K-$1.5M
                return round(self.rng.uniform(250_000, 1_500_000), 2)

    def _generate_jobs_retained(self) -> int:
        """Generate a realistic jobs-retained count (right-skewed, 0-500)."""
        tier = self.rng.random()
        if tier < 0.10:
            return 0  # sole proprietor / no retained jobs reported
        elif tier < 0.70:
            return int(self.rng.integers(1, 25))
        elif tier < 0.92:
            return int(self.rng.integers(25, 100))
        elif tier < 0.99:
            return int(self.rng.integers(100, 300))
        else:
            return int(self.rng.integers(300, 501))

    def _generate_term(self, domain: str, cfg: dict[str, Any]) -> int:
        """Return loan term in months appropriate for the domain."""
        if "term_choices" in cfg:
            return int(self.weighted_choice(cfg["term_choices"], cfg["term_weights"]))
        # Continuous range
        return int(self.rng.integers(cfg["term_min"], cfg["term_max"] + 1))

    def _generate_interest_rate(self, domain: str, cfg: dict[str, Any]) -> float:
        """Return the interest rate for the loan."""
        if "interest_rate" in cfg:
            return float(cfg["interest_rate"])
        rate_min: float = cfg["rate_min"]
        rate_max: float = cfg["rate_max"]
        if rate_min == rate_max:
            return round(rate_min, 2)
        return round(self.rng.uniform(rate_min, rate_max), 2)

    def _generate_forgiveness(
        self,
        loan_amount: float,
        loan_status: str,
        approval_dt: datetime,
    ) -> tuple[float | None, str | None]:
        """
        Generate PPP forgiveness amount and date.

        Most PPP loans (>90 %) were fully forgiven.  A small fraction had
        partial forgiveness or none at all.
        """
        if loan_status not in ("PAID_IN_FULL", "CHARGED_OFF"):
            return None, None

        roll = self.rng.random()
        if roll < 0.88:
            # Full forgiveness
            forgiveness_amount = round(loan_amount, 2)
        elif roll < 0.95:
            # Partial forgiveness
            forgiveness_amount = round(
                self.rng.uniform(loan_amount * 0.50, loan_amount * 0.99), 2
            )
        else:
            # No forgiveness / charge-off with zero forgiveness
            forgiveness_amount = 0.0

        # Forgiveness date is typically 8-24 weeks after approval
        weeks_offset = int(self.rng.integers(8, 25))
        forgiveness_dt = approval_dt + timedelta(weeks=weeks_offset)
        forgiveness_date_str = forgiveness_dt.strftime("%Y-%m-%d")

        return forgiveness_amount, forgiveness_date_str
