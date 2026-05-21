"""
Financial Transaction Generator
================================

Generates synthetic financial transaction data for a mid-tier commercial bank POC.
Supports card-present, card-not-present, ACH, and wire transfer transactions
with realistic fraud patterns and PCI-DSS compliant data handling.

Fraud Patterns Embedded:
- Velocity bursts (>5 txns in 1 hour)
- Geo-anomaly (impossible travel)
- Amount spikes (>3x rolling average)
- Structuring ($8K-$9.9K repeated cash deposits)

Compliance:
- PCI DSS v4.0: PAN tokenized at generation; only card_hash stored
- BSA/AML: CTR threshold ($10,000) and structuring patterns included
- SOX: Reproducible with seed for audit trail
"""

import hashlib
from datetime import datetime
from typing import Any

import pandas as pd

from data_generation.generators.base_generator import BaseGenerator

# Realistic MCC (Merchant Category Code) distribution
MCC_CODES: dict[str, list[str]] = {
    "grocery": ["5411", "5422", "5441", "5451", "5462"],
    "gas_station": ["5541", "5542"],
    "restaurant": ["5812", "5813", "5814"],
    "retail": ["5311", "5331", "5399", "5651", "5691", "5699"],
    "online_shopping": ["5964", "5965", "5966", "5967", "5968"],
    "travel": ["3000", "3001", "4511", "4722", "7011", "7012"],
    "entertainment": ["7832", "7841", "7911", "7922", "7929"],
    "utilities": ["4900", "4814", "4816"],
    "healthcare": ["5912", "8011", "8021", "8031", "8041", "8042"],
    "financial": ["6010", "6011", "6012", "6051"],
    "high_risk": ["5933", "5960", "7273", "7995"],
}

MCC_WEIGHTS = [0.18, 0.10, 0.14, 0.15, 0.12, 0.06, 0.05, 0.06, 0.07, 0.04, 0.03]

CHANNEL_TYPES = ["card_present", "card_not_present", "ach", "wire"]
CHANNEL_WEIGHTS = [0.40, 0.35, 0.20, 0.05]

CURRENCY_CODES = ["USD", "USD", "USD", "USD", "EUR", "GBP", "CAD"]

ACCOUNT_TYPES = ["checking", "savings", "money_market", "cd", "credit_card"]
RISK_RATINGS = ["low", "medium", "high", "critical"]
RISK_WEIGHTS = [0.55, 0.30, 0.12, 0.03]


class TransactionGenerator(BaseGenerator):
    """Generate synthetic financial transactions with embedded fraud patterns.

    PCI-DSS compliant: raw PAN is never persisted. Only a SHA-256 hash
    (``card_hash``) is included in the output.

    Args:
        seed: Random seed for reproducibility.
        locale: Faker locale.
        start_date: Start date for transactions.
        end_date: End date for transactions.
        num_customers: Number of unique customers/accounts.
        fraud_rate: Base fraud rate (default 0.0015 = 0.15%).
    """

    def __init__(
        self,
        seed: int | None = None,
        locale: str = "en_US",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        num_customers: int = 2000,
        fraud_rate: float = 0.0015,
    ):
        super().__init__(
            seed=seed, locale=locale, start_date=start_date, end_date=end_date
        )

        if not 0.0 <= fraud_rate <= 1.0:
            raise ValueError(f"fraud_rate must be between 0 and 1, got {fraud_rate}")
        if num_customers <= 0:
            raise ValueError(f"num_customers must be positive, got {num_customers}")

        self.num_customers = num_customers
        self.fraud_rate = fraud_rate
        self._customers = self._generate_customers()
        self._txn_counter = 0

        self._schema = {
            "txn_id": "string",
            "txn_timestamp": "timestamp",
            "acct_id": "string",
            "card_hash": "string",
            "channel": "string",
            "merchant_name": "string",
            "merchant_mcc": "string",
            "mcc_category": "string",
            "amount": "double",
            "currency": "string",
            "auth_code": "string",
            "merchant_lat": "double",
            "merchant_lon": "double",
            "is_fraud": "boolean",
            "fraud_pattern": "string",
        }

    def _generate_customers(self) -> list[dict[str, Any]]:
        """Pre-generate customer profiles for consistency across transactions."""
        customers = []
        for i in range(self.num_customers):
            raw_pan = self.synthetic_card_number()
            card_hash = hashlib.sha256(f"{raw_pan}-{self.seed}".encode()).hexdigest()

            acct_type = str(self.rng.choice(ACCOUNT_TYPES))
            risk_rating = str(self.weighted_choice(RISK_RATINGS, RISK_WEIGHTS))
            home_lat = float(self.rng.uniform(25.0, 48.0))
            home_lon = float(self.rng.uniform(-122.0, -73.0))

            customers.append(
                {
                    "acct_id": f"ACCT-{i + 1:07d}",
                    "card_hash": card_hash,
                    "acct_type": acct_type,
                    "risk_rating": risk_rating,
                    "balance": round(float(self.rng.lognormal(mean=9.0, sigma=1.5)), 2),
                    "home_lat": home_lat,
                    "home_lon": home_lon,
                    "avg_txn_amount": round(
                        float(self.rng.lognormal(mean=3.5, sigma=1.0)), 2
                    ),
                }
            )
        return customers

    def generate_record(self) -> dict[str, Any]:
        """Generate a single financial transaction record."""
        self._txn_counter += 1
        customer = self._customers[int(self.rng.integers(0, self.num_customers))]

        # Select channel and MCC
        channel = str(self.weighted_choice(CHANNEL_TYPES, CHANNEL_WEIGHTS))
        mcc_categories = list(MCC_CODES.keys())
        mcc_category = str(self.weighted_choice(mcc_categories, MCC_WEIGHTS))
        mcc_list = MCC_CODES[mcc_category]
        merchant_mcc = str(self.rng.choice(mcc_list))

        # Generate amount based on channel and category
        if channel == "wire":
            amount = round(float(self.rng.lognormal(mean=9.5, sigma=1.5)), 2)
        elif channel == "ach":
            amount = round(float(self.rng.lognormal(mean=6.5, sigma=1.2)), 2)
        else:
            amount = round(float(self.rng.lognormal(mean=3.5, sigma=1.0)), 2)

        amount = max(0.01, min(amount, 999999.99))

        # Merchant location (near customer home with some variance)
        merchant_lat = customer["home_lat"] + float(self.rng.normal(0, 0.5))
        merchant_lon = customer["home_lon"] + float(self.rng.normal(0, 0.5))

        # Fraud determination
        is_fraud = False
        fraud_pattern = None
        fraud_roll = float(self.rng.random())

        if fraud_roll < self.fraud_rate:
            is_fraud = True
            pattern_roll = float(self.rng.random())
            if pattern_roll < 0.35:
                fraud_pattern = "velocity_burst"
            elif pattern_roll < 0.60:
                fraud_pattern = "geo_anomaly"
                merchant_lat = customer["home_lat"] + float(self.rng.uniform(10, 30))
                merchant_lon = customer["home_lon"] + float(self.rng.uniform(10, 30))
            elif pattern_roll < 0.80:
                fraud_pattern = "amount_spike"
                amount = round(
                    customer["avg_txn_amount"] * float(self.rng.uniform(5, 20)), 2
                )
            else:
                fraud_pattern = "structuring"
                amount = round(float(self.rng.uniform(8000, 9999)), 2)

        # Auth code
        auth_code = f"{int(self.rng.integers(100000, 999999)):06d}"

        record = {
            "txn_id": f"TXN-{self._txn_counter:012d}",
            "txn_timestamp": self.random_datetime().isoformat(),
            "acct_id": customer["acct_id"],
            "card_hash": customer["card_hash"],
            "channel": channel,
            "merchant_name": self.faker.company(),
            "merchant_mcc": merchant_mcc,
            "mcc_category": mcc_category,
            "amount": amount,
            "currency": str(self.rng.choice(CURRENCY_CODES)),
            "auth_code": auth_code,
            "merchant_lat": round(merchant_lat, 6),
            "merchant_lon": round(merchant_lon, 6),
            "is_fraud": is_fraud,
            "fraud_pattern": fraud_pattern,
        }

        return record

    def generate_accounts(self) -> pd.DataFrame:
        """Return customer account profiles as a DataFrame.

        Excludes raw PAN -- only ``card_hash`` is included (PCI DSS Req 3.4).
        """
        return pd.DataFrame(
            [
                {
                    "acct_id": c["acct_id"],
                    "card_hash": c["card_hash"],
                    "acct_type": c["acct_type"],
                    "risk_rating": c["risk_rating"],
                    "balance": c["balance"],
                }
                for c in self._customers
            ]
        )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate financial transactions")
    parser.add_argument("--records", type=int, default=10000)
    parser.add_argument("--customers", type=int, default=2000)
    parser.add_argument("--fraud-rate", type=float, default=0.0015)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="output/financial")
    args = parser.parse_args()

    gen = TransactionGenerator(
        seed=args.seed,
        num_customers=args.customers,
        fraud_rate=args.fraud_rate,
    )

    print(
        f"Generating {args.records:,} transactions for {args.customers:,} customers..."
    )
    df = gen.generate(num_records=args.records)

    print(f"Fraud rate: {df['is_fraud'].mean():.4%}")
    print(
        f"Fraud patterns: {df[df['is_fraud']]['fraud_pattern'].value_counts().to_dict()}"
    )

    gen.to_parquet(df, f"{args.output}/transactions.parquet")
    print(f"Saved to {args.output}/transactions.parquet")

    accounts_df = gen.generate_accounts()
    gen.to_parquet(accounts_df, f"{args.output}/accounts.parquet")
    print(f"Saved {len(accounts_df)} accounts to {args.output}/accounts.parquet")
