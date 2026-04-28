"""
Insurance Claims Generator
===========================

Generates synthetic P&C insurance data: policies, claims, and adjusters.
Supports four lines of business (Personal Auto, Homeowners, Commercial
Multi-Peril, Workers' Compensation) with realistic loss types, reserve
development patterns, and a configurable fraud rate (~2%).

Inherits from BaseGenerator for reproducibility and output handling.
"""

from datetime import datetime, timedelta
from typing import Any

import numpy as np

from data_generation.generators.base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

LINES_OF_BUSINESS = ["auto", "home", "commercial", "workers_comp"]
LOB_WEIGHTS = [0.40, 0.25, 0.20, 0.15]

LOSS_TYPES: dict[str, list[str]] = {
    "auto": ["collision", "comprehensive", "bodily_injury", "property_damage", "uninsured_motorist", "pip"],
    "home": ["fire", "water_damage", "wind_hail", "theft", "liability", "other_structural"],
    "commercial": ["general_liability", "property_damage", "business_interruption", "product_liability", "professional_liability", "cyber"],
    "workers_comp": ["slip_fall", "strain_sprain", "laceration", "fracture", "repetitive_stress", "occupational_illness"],
}

CLAIM_STATUSES = ["open", "under_investigation", "reserved", "closed_paid", "closed_no_pay", "reopened", "subrogation"]
STATUS_WEIGHTS = [0.15, 0.10, 0.20, 0.30, 0.10, 0.05, 0.10]

STATES = [
    "CA", "TX", "FL", "NY", "PA", "IL", "OH", "GA", "NC", "MI",
    "NJ", "VA", "WA", "AZ", "MA", "TN", "IN", "MO", "MD", "WI",
    "CO", "MN", "SC", "AL", "LA", "KY", "OR", "OK", "CT", "UT",
]

SEVERITY_RANGES: dict[str, tuple[float, float]] = {
    "auto":         (500.0, 150_000.0),
    "home":         (1_000.0, 500_000.0),
    "commercial":   (2_000.0, 1_000_000.0),
    "workers_comp": (1_000.0, 250_000.0),
}

PREMIUM_RANGES: dict[str, tuple[float, float]] = {
    "auto":         (800.0, 8_000.0),
    "home":         (1_200.0, 15_000.0),
    "commercial":   (3_000.0, 25_000.0),
    "workers_comp": (2_000.0, 20_000.0),
}


class InsuranceClaimsGenerator(BaseGenerator):
    """Generate synthetic P&C insurance policies, claims, and adjusters."""

    FRAUD_RATE = 0.02  # 2 % baseline fraud rate

    def __init__(
        self,
        seed: int | None = None,
        num_policies: int = 1_000,
        num_adjusters: int = 50,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)
        self.num_policies = num_policies
        self.num_adjusters = num_adjusters

        # Pre-generate reference data
        self._policies: list[dict[str, Any]] = []
        self._adjusters: list[dict[str, Any]] = []
        self._generate_adjusters()
        self._generate_policies()

        self._schema = {
            "claim_id": "string",
            "policy_id": "string",
            "loss_dt": "datetime",
            "report_dt": "datetime",
            "claimant_name": "string",
            "loss_type": "string",
            "line_of_business": "string",
            "state": "string",
            "reserve_amt": "float",
            "paid_amt": "float",
            "status": "string",
            "fraud_flag": "boolean",
            "adjuster_id": "string",
            "agent_id": "string",
        }

    # ------------------------------------------------------------------
    # Reference data generation
    # ------------------------------------------------------------------

    def _generate_adjusters(self) -> None:
        """Pre-generate adjuster roster."""
        for i in range(self.num_adjusters):
            self._adjusters.append({
                "adjuster_id": f"ADJ-{i + 1:04d}",
                "adjuster_name": self.faker.name(),
                "speciality": str(self.rng.choice(LINES_OF_BUSINESS)),
                "years_experience": int(self.rng.integers(1, 30)),
                "state_licensed": str(self.rng.choice(STATES)),
            })

    def _generate_policies(self) -> None:
        """Pre-generate policy book."""
        for i in range(self.num_policies):
            lob = str(self.weighted_choice(LINES_OF_BUSINESS, LOB_WEIGHTS))
            state = str(self.rng.choice(STATES))
            prem_lo, prem_hi = PREMIUM_RANGES[lob]
            premium = round(float(self.rng.uniform(prem_lo, prem_hi)), 2)
            effective_dt = self.random_datetime(
                self.start_date - timedelta(days=365),
                self.end_date,
            )
            expiry_dt = effective_dt + timedelta(days=365)
            self._policies.append({
                "policy_id": f"POL-{i + 1:06d}",
                "line_of_business": lob,
                "effective_dt": effective_dt.isoformat()[:10],
                "expiry_dt": expiry_dt.isoformat()[:10],
                "premium": premium,
                "state": state,
                "agent_id": f"AGT-{int(self.rng.integers(1, 201)):04d}",
                "insured_name": self.faker.name(),
            })

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------

    @property
    def policies(self) -> list[dict[str, Any]]:
        """Return pre-generated policies."""
        return self._policies

    @property
    def adjusters(self) -> list[dict[str, Any]]:
        """Return pre-generated adjusters."""
        return self._adjusters

    # ------------------------------------------------------------------
    # Core generation
    # ------------------------------------------------------------------

    def generate_record(self) -> dict[str, Any]:
        """Generate a single insurance claim record."""
        policy = self._policies[int(self.rng.integers(0, len(self._policies)))]
        lob = policy["line_of_business"]
        state = policy["state"]

        # Loss date within policy period, report date after loss
        loss_dt = self.random_datetime()
        report_lag_days = int(self.rng.exponential(scale=7.0)) + 1
        report_dt = loss_dt + timedelta(days=report_lag_days)

        # Loss type realistic per LOB
        loss_type = str(self.rng.choice(LOSS_TYPES[lob]))

        # Reserve amount (log-normal for heavy tail)
        sev_lo, sev_hi = SEVERITY_RANGES[lob]
        mu = np.log((sev_lo + sev_hi) / 4)
        sigma = 0.8
        reserve_amt = float(np.clip(
            self.rng.lognormal(mean=mu, sigma=sigma),
            sev_lo,
            sev_hi,
        ))
        reserve_amt = round(reserve_amt, 2)

        # Paid amount (0 to reserve depending on status)
        status = str(self.weighted_choice(CLAIM_STATUSES, STATUS_WEIGHTS))
        if status in ("closed_paid", "subrogation"):
            paid_pct = float(self.rng.uniform(0.5, 1.0))
        elif status == "closed_no_pay":
            paid_pct = 0.0
        else:
            paid_pct = float(self.rng.uniform(0.0, 0.6))
        paid_amt = round(reserve_amt * paid_pct, 2)

        # Fraud flag ~2%
        fraud_flag = bool(self.rng.random() < self.FRAUD_RATE)

        # Assign adjuster
        adjuster = self._adjusters[int(self.rng.integers(0, len(self._adjusters)))]

        return {
            "claim_id": f"CLM-{self.generate_uuid()[:12].upper()}",
            "policy_id": policy["policy_id"],
            "line_of_business": lob,
            "state": state,
            "loss_dt": loss_dt.isoformat()[:10],
            "report_dt": report_dt.isoformat()[:10],
            "claimant_name": self.faker.name(),
            "loss_type": loss_type,
            "reserve_amt": reserve_amt,
            "paid_amt": paid_amt,
            "status": status,
            "fraud_flag": fraud_flag,
            "adjuster_id": adjuster["adjuster_id"],
            "agent_id": policy["agent_id"],
        }
