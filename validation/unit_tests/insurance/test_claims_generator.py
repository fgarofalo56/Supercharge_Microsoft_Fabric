"""
Unit Tests for InsuranceClaimsGenerator
========================================

Tests cover:
- Basic claim generation and schema
- Fraud rate within expected bounds
- Reserve positivity
- Policy-claim linkage integrity
- LOB value validation
- Reproducibility via seed
"""

from datetime import datetime

import pytest

from data_generation.generators.insurance.claims_generator import (
    CLAIM_STATUSES,
    LINES_OF_BUSINESS,
    LOSS_TYPES,
    STATES,
    InsuranceClaimsGenerator,
)


@pytest.fixture
def generator() -> InsuranceClaimsGenerator:
    """Create a seeded generator for deterministic tests."""
    return InsuranceClaimsGenerator(
        seed=42,
        num_policies=100,
        num_adjusters=10,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31),
    )


@pytest.fixture
def claims_df(generator: InsuranceClaimsGenerator):
    """Generate a batch of claims for aggregate tests."""
    return generator.generate(num_records=1_000, show_progress=False)


class TestGenerateClaims:
    """Test basic claim generation."""

    def test_generate_single_record(self, generator: InsuranceClaimsGenerator):
        record = generator.generate_record()
        assert isinstance(record, dict)
        assert "claim_id" in record
        assert "policy_id" in record
        assert "loss_dt" in record
        assert "report_dt" in record
        assert "reserve_amt" in record
        assert "paid_amt" in record
        assert "status" in record
        assert "fraud_flag" in record

    def test_generate_batch(self, generator: InsuranceClaimsGenerator):
        df = generator.generate(num_records=50, show_progress=False)
        assert len(df) == 50
        assert "claim_id" in df.columns

    def test_claim_id_format(self, generator: InsuranceClaimsGenerator):
        record = generator.generate_record()
        assert record["claim_id"].startswith("CLM-")

    def test_all_schema_fields_present(self, generator: InsuranceClaimsGenerator):
        record = generator.generate_record()
        for field in generator.schema:
            assert field in record, f"Missing field: {field}"

    def test_generate_batch_list(self, generator: InsuranceClaimsGenerator):
        batch = generator.generate_batch(20)
        assert isinstance(batch, list)
        assert len(batch) == 20
        assert isinstance(batch[0], dict)


class TestFraudRate:
    """Test fraud flag distribution."""

    def test_fraud_rate_within_bounds(self, claims_df):
        """Fraud rate should be near 2% (allow 0.5%-5% for 1K samples)."""
        fraud_rate = claims_df["fraud_flag"].mean()
        assert 0.005 <= fraud_rate <= 0.05, (
            f"Fraud rate {fraud_rate:.3f} outside expected bounds"
        )

    def test_fraud_flag_is_boolean(self, claims_df):
        assert claims_df["fraud_flag"].dtype == bool


class TestReservePositive:
    """Test that reserves are always positive."""

    def test_reserve_amt_positive(self, claims_df):
        assert (claims_df["reserve_amt"] > 0).all(), "All reserves must be positive"

    def test_paid_amt_non_negative(self, claims_df):
        assert (claims_df["paid_amt"] >= 0).all(), "Paid amounts must be non-negative"

    def test_paid_lte_reserve_for_closed(self, claims_df):
        """For closed-paid claims, paid should not exceed reserve significantly."""
        closed = claims_df[claims_df["status"] == "closed_paid"]
        if len(closed) > 0:
            # Allow 5% tolerance for rounding
            ratio = closed["paid_amt"] / closed["reserve_amt"]
            assert (ratio <= 1.05).all(), "Paid should not greatly exceed reserve"


class TestPolicyClaimLinkage:
    """Test that claims reference valid policies."""

    def test_policy_id_format(self, claims_df):
        assert claims_df["policy_id"].str.startswith("POL-").all()

    def test_policy_id_references_generated_policies(
        self, generator: InsuranceClaimsGenerator
    ):
        valid_ids = {p["policy_id"] for p in generator.policies}
        for _ in range(100):
            record = generator.generate_record()
            assert record["policy_id"] in valid_ids, (
                f"Orphan policy: {record['policy_id']}"
            )

    def test_adjuster_id_references_generated_adjusters(
        self, generator: InsuranceClaimsGenerator
    ):
        valid_ids = {a["adjuster_id"] for a in generator.adjusters}
        for _ in range(100):
            record = generator.generate_record()
            assert record["adjuster_id"] in valid_ids


class TestLobValues:
    """Test line of business values."""

    def test_lob_values_valid(self, claims_df):
        assert claims_df["line_of_business"].isin(LINES_OF_BUSINESS).all()

    def test_all_lobs_represented(self, claims_df):
        """With 1K records, all 4 LOBs should appear."""
        unique_lobs = set(claims_df["line_of_business"].unique())
        assert unique_lobs == set(LINES_OF_BUSINESS)

    def test_loss_type_matches_lob(self, generator: InsuranceClaimsGenerator):
        """Loss types should be valid for their LOB."""
        for _ in range(200):
            record = generator.generate_record()
            lob = record["line_of_business"]
            assert record["loss_type"] in LOSS_TYPES[lob], (
                f"Loss type '{record['loss_type']}' invalid for LOB '{lob}'"
            )

    def test_status_values_valid(self, claims_df):
        assert claims_df["status"].isin(CLAIM_STATUSES).all()

    def test_state_values_valid(self, claims_df):
        assert claims_df["state"].isin(STATES).all()


class TestReproducibility:
    """Test that seeded generators produce identical output."""

    def test_same_seed_same_output(self):
        gen1 = InsuranceClaimsGenerator(
            seed=123,
            num_policies=50,
            num_adjusters=5,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 6, 30),
        )
        gen2 = InsuranceClaimsGenerator(
            seed=123,
            num_policies=50,
            num_adjusters=5,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 6, 30),
        )
        df1 = gen1.generate(num_records=50, show_progress=False)
        df2 = gen2.generate(num_records=50, show_progress=False)
        # Drop Faker-generated columns (Faker RNG can diverge from numpy RNG)
        deterministic_cols = [c for c in df1.columns if c != "claimant_name"]
        assert df1[deterministic_cols].equals(df2[deterministic_cols]), (
            "Same seed must produce identical output"
        )

    def test_different_seed_different_output(self):
        gen1 = InsuranceClaimsGenerator(
            seed=1,
            num_policies=50,
            num_adjusters=5,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 6, 30),
        )
        gen2 = InsuranceClaimsGenerator(
            seed=2,
            num_policies=50,
            num_adjusters=5,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 6, 30),
        )
        df1 = gen1.generate(num_records=50, show_progress=False)
        df2 = gen2.generate(num_records=50, show_progress=False)
        assert not df1.equals(df2), "Different seeds should produce different output"

    def test_policies_reproducible(self):
        gen1 = InsuranceClaimsGenerator(seed=99, num_policies=20, num_adjusters=5)
        gen2 = InsuranceClaimsGenerator(seed=99, num_policies=20, num_adjusters=5)
        assert gen1.policies == gen2.policies
        assert gen1.adjusters == gen2.adjusters
