"""
Unit Tests for RetailSalesGenerator
====================================

Validates POS transaction generation for the Retail/CPG vertical.
"""

import re

import pytest

from data_generation.generators.retail.sales_generator import (
    CATEGORIES,
    PAYMENT_METHODS,
    RetailSalesGenerator,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def generator():
    """Create a seeded generator for deterministic tests."""
    return RetailSalesGenerator(
        seed=42,
        num_stores=10,
        num_skus=100,
        num_customers=200,
    )


@pytest.fixture
def sample_records(generator):
    """Generate a small batch of records."""
    return generator.generate_batch(50)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGenerateSales:
    """Core generation tests."""

    def test_generate_sales(self, generator):
        """generate() returns a DataFrame with expected columns."""
        df = generator.generate(num_records=20, show_progress=False)
        assert len(df) == 20

        expected_cols = {
            "txn_id", "txn_timestamp", "store_id", "sku",
            "category", "subcategory", "brand", "qty",
            "unit_price", "discount_pct", "line_total",
            "payment_method", "loyalty_id", "customer_segment",
            "store_format", "region",
            "card_token", "card_last4",
            "_ingested_at", "_source", "_batch_id",
        }
        assert expected_cols.issubset(set(df.columns))

    def test_generate_batch_returns_list(self, generator):
        """generate_batch returns list[dict]."""
        batch = generator.generate_batch(5)
        assert isinstance(batch, list)
        assert len(batch) == 5
        assert isinstance(batch[0], dict)

    def test_record_has_metadata(self, sample_records):
        """Every record has _ingested_at, _source, _batch_id."""
        for rec in sample_records:
            assert "_ingested_at" in rec
            assert "_source" in rec
            assert rec["_source"] == "RetailSalesGenerator"


class TestQuantityValidation:
    """Quantity must always be positive."""

    def test_qty_positive(self, sample_records):
        """All qty values must be >= 1."""
        for rec in sample_records:
            assert rec["qty"] >= 1, f"qty={rec['qty']} in txn {rec['txn_id']}"

    def test_qty_is_integer(self, sample_records):
        """qty must be an integer."""
        for rec in sample_records:
            assert isinstance(rec["qty"], int)


class TestPriceValidation:
    """Prices and totals must be positive."""

    def test_price_positive(self, sample_records):
        """unit_price must be > 0."""
        for rec in sample_records:
            assert rec["unit_price"] > 0

    def test_line_total_non_negative(self, sample_records):
        """line_total must be >= 0 (discount can reduce but not negate)."""
        for rec in sample_records:
            assert rec["line_total"] >= 0

    def test_discount_in_range(self, sample_records):
        """discount_pct must be in [0, 1)."""
        for rec in sample_records:
            assert 0.0 <= rec["discount_pct"] < 1.0


class TestCategoryValidation:
    """Categories must match reference data."""

    def test_category_valid(self, sample_records):
        """category must be one of the defined categories."""
        valid = set(CATEGORIES.keys())
        for rec in sample_records:
            assert rec["category"] in valid, f"Invalid category: {rec['category']}"

    def test_subcategory_matches_parent(self, sample_records):
        """subcategory must belong to its parent category."""
        for rec in sample_records:
            valid_subs = CATEGORIES[rec["category"]]["subcategories"]
            assert rec["subcategory"] in valid_subs

    def test_payment_method_valid(self, sample_records):
        """payment_method must be from the defined set."""
        for rec in sample_records:
            assert rec["payment_method"] in PAYMENT_METHODS


class TestLoyaltyId:
    """Loyalty ID format tests."""

    def test_loyalty_id_format(self, sample_records):
        """loyalty_id must match LYL-XXXXXXXXXX or be None."""
        pattern = re.compile(r"^LYL-\d{10}$")
        for rec in sample_records:
            lid = rec["loyalty_id"]
            if lid is not None:
                assert pattern.match(lid), f"Bad loyalty_id: {lid}"

    def test_loyalty_rate_reasonable(self, sample_records):
        """Roughly 70-85% of transactions should have loyalty linkage."""
        linked = sum(1 for r in sample_records if r["loyalty_id"] is not None)
        rate = linked / len(sample_records)
        assert 0.50 <= rate <= 0.95, f"Loyalty rate {rate:.1%} outside bounds"


class TestPCIDSS:
    """PCI-DSS compliance: no raw PANs."""

    def test_no_raw_pan(self, sample_records):
        """card_token must start with 'tok_' or be None — never a raw PAN."""
        pan_pattern = re.compile(r"^\d{13,19}$")
        for rec in sample_records:
            token = rec["card_token"]
            if token is not None:
                assert token.startswith("tok_"), f"Non-token card: {token}"
                assert not pan_pattern.match(token)


class TestReproducibility:
    """Seeded generators must produce identical output."""

    def test_reproducibility(self):
        """Two generators with same seed produce identical records."""
        gen_a = RetailSalesGenerator(seed=99, num_stores=5, num_skus=20, num_customers=50)
        gen_b = RetailSalesGenerator(seed=99, num_stores=5, num_skus=20, num_customers=50)

        records_a = gen_a.generate_batch(10)
        records_b = gen_b.generate_batch(10)

        for a, b in zip(records_a, records_b):
            assert a["txn_id"] == b["txn_id"]
            assert a["sku"] == b["sku"]
            assert a["qty"] == b["qty"]
            assert a["unit_price"] == b["unit_price"]
            assert a["line_total"] == b["line_total"]

    def test_different_seeds_differ(self):
        """Different seeds produce different output."""
        gen_a = RetailSalesGenerator(seed=1, num_stores=5, num_skus=20, num_customers=50)
        gen_b = RetailSalesGenerator(seed=2, num_stores=5, num_skus=20, num_customers=50)

        rec_a = gen_a.generate_record()
        rec_b = gen_b.generate_record()
        # At least one field should differ
        assert rec_a["txn_id"] != rec_b["txn_id"] or rec_a["sku"] != rec_b["sku"]
