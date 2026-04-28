"""
Unit tests for the Financial Services TransactionGenerator.

Tests cover:
- Basic transaction generation
- PCI DSS compliance (no raw PAN)
- Fraud rate within expected range
- MCC code validity
- Amount positivity
- Reproducibility with seed
"""

import re
import sys
from datetime import datetime
from pathlib import Path

import pytest

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from data_generation.generators.financial.transaction_generator import (
    MCC_CODES,
    TransactionGenerator,
)


@pytest.fixture
def generator():
    """Create a seeded TransactionGenerator for deterministic tests."""
    return TransactionGenerator(seed=42, num_customers=100, fraud_rate=0.0015)


@pytest.fixture
def transactions(generator):
    """Generate a batch of transactions."""
    return generator.generate(num_records=5000, show_progress=False)


class TestTransactionGeneration:
    """Tests for basic transaction generation."""

    def test_generate_transactions(self, transactions):
        """Verify correct number of records and required columns."""
        assert len(transactions) == 5000

        required_cols = [
            "txn_id", "txn_timestamp", "acct_id", "card_hash",
            "channel", "merchant_name", "merchant_mcc", "mcc_category",
            "amount", "currency", "auth_code", "merchant_lat",
            "merchant_lon", "is_fraud", "fraud_pattern",
        ]
        for col_name in required_cols:
            assert col_name in transactions.columns, f"Missing column: {col_name}"

    def test_txn_ids_unique(self, transactions):
        """Transaction IDs must be unique."""
        assert transactions["txn_id"].nunique() == len(transactions)


class TestPCICompliance:
    """PCI DSS v4.0 compliance tests."""

    def test_pci_no_raw_pan(self, transactions):
        """card_hash must be a SHA-256 hex digest, never a raw PAN.

        PCI DSS Req 3.4: Render PAN unreadable anywhere it is stored.
        A raw PAN is 13-19 digits; SHA-256 hex is exactly 64 hex chars.
        """
        for card_hash in transactions["card_hash"]:
            # Must be 64-char hex (SHA-256)
            assert len(card_hash) == 64, f"card_hash wrong length: {len(card_hash)}"
            assert re.match(r"^[0-9a-f]{64}$", card_hash), f"Not hex: {card_hash[:20]}..."
            # Must NOT be a numeric-only string (raw PAN)
            assert not card_hash.isdigit(), "Raw PAN detected in card_hash!"


class TestFraudRate:
    """Fraud rate validation tests."""

    def test_fraud_rate_range(self, transactions):
        """Fraud rate should be within a reasonable range of the configured rate.

        With 5000 records and 0.15% rate, expected ~7.5 frauds.
        Allow wide range due to small sample: 0.01% - 1.0%.
        """
        fraud_rate = transactions["is_fraud"].mean()
        assert 0.0001 <= fraud_rate <= 0.01, (
            f"Fraud rate {fraud_rate:.4%} outside expected range [0.01%, 1.0%]"
        )

    def test_fraud_patterns_valid(self, transactions):
        """Fraud records must have a valid pattern; non-fraud must have None."""
        valid_patterns = {"velocity_burst", "geo_anomaly", "amount_spike", "structuring"}

        fraud_rows = transactions[transactions["is_fraud"]]
        non_fraud_rows = transactions[~transactions["is_fraud"]]

        for pattern in fraud_rows["fraud_pattern"]:
            assert pattern in valid_patterns, f"Invalid fraud pattern: {pattern}"

        assert non_fraud_rows["fraud_pattern"].isna().all(), "Non-fraud has fraud_pattern set"


class TestMCCCodes:
    """MCC code validation tests."""

    def test_mcc_codes_valid(self, transactions):
        """All MCC codes must exist in the defined MCC_CODES mapping."""
        all_valid_mccs = set()
        for mcc_list in MCC_CODES.values():
            all_valid_mccs.update(mcc_list)

        for mcc in transactions["merchant_mcc"]:
            assert mcc in all_valid_mccs, f"Unknown MCC code: {mcc}"

    def test_mcc_category_matches(self, transactions):
        """mcc_category must correspond to the MCC code."""
        for _, row in transactions.head(100).iterrows():
            category = row["mcc_category"]
            mcc = row["merchant_mcc"]
            assert mcc in MCC_CODES[category], (
                f"MCC {mcc} not in category {category}"
            )


class TestAmountValidation:
    """Transaction amount tests."""

    def test_amount_positive(self, transactions):
        """All transaction amounts must be positive."""
        assert (transactions["amount"] > 0).all(), "Found non-positive amounts"

    def test_amount_reasonable_range(self, transactions):
        """Amounts should be within reasonable bounds."""
        assert transactions["amount"].max() <= 999999.99
        assert transactions["amount"].min() >= 0.01


class TestReproducibility:
    """Seed-based reproducibility tests."""

    def test_reproducibility(self):
        """Two generators with the same seed must produce identical output."""
        fixed_start = datetime(2026, 1, 1)
        fixed_end = datetime(2026, 1, 31)
        gen1 = TransactionGenerator(seed=123, num_customers=50, fraud_rate=0.002, start_date=fixed_start, end_date=fixed_end)
        gen2 = TransactionGenerator(seed=123, num_customers=50, fraud_rate=0.002, start_date=fixed_start, end_date=fixed_end)

        df1 = gen1.generate(num_records=100, show_progress=False)
        df2 = gen2.generate(num_records=100, show_progress=False)

        # Compare seeded columns (merchant_name uses Faker which may vary)
        seeded_cols = [
            "txn_id", "txn_timestamp", "acct_id", "card_hash",
            "channel", "merchant_mcc", "mcc_category", "amount",
            "currency", "auth_code", "is_fraud", "fraud_pattern",
        ]
        assert df1[seeded_cols].equals(df2[seeded_cols]), "Same seed produced different results"

    def test_different_seeds_differ(self):
        """Different seeds must produce different output."""
        gen1 = TransactionGenerator(seed=1, num_customers=50)
        gen2 = TransactionGenerator(seed=2, num_customers=50)

        df1 = gen1.generate(num_records=100, show_progress=False)
        df2 = gen2.generate(num_records=100, show_progress=False)

        assert not df1.equals(df2), "Different seeds produced identical results"
