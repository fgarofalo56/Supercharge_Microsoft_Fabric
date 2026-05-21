"""
Unit tests for HospitalOperationsGenerator.

Tests cover:
- Admission record generation
- HIPAA compliance (synthetic SSNs, hashed MRNs)
- DRG code validity
- LOS positivity
- Readmit flag binary constraint
- Claims amount relationships
- Reproducibility with seed
"""

import os
import re

import pytest

# Ensure hash salt is set for tests
os.environ.setdefault("FABRIC_POC_HASH_SALT", "test-salt-unit-tests")

from data_generation.generators.healthcare.hospital_operations_generator import (
    TOP_25_DRG,
    HospitalOperationsGenerator,
)


@pytest.fixture
def generator():
    return HospitalOperationsGenerator(seed=42)


class TestGenerateAdmissions:
    """Test admission record generation."""

    def test_generate_single_admission(self, generator):
        record = generator.generate_admission()
        assert "encounter_id" in record
        assert "mrn_hash" in record
        assert "admit_dt" in record
        assert "discharge_dt" in record
        assert "los" in record
        assert "drg_code" in record
        assert "payer" in record

    def test_generate_admissions_batch(self, generator):
        df = generator.generate_admissions(100)
        assert len(df) == 100
        assert "encounter_id" in df.columns

    def test_generate_record_returns_admission(self, generator):
        record = generator.generate_record()
        assert record["encounter_id"].startswith("ENC-")


class TestHipaaCompliance:
    """Verify no real PHI is generated."""

    def test_ssn_is_900_series(self, generator):
        for _ in range(50):
            record = generator.generate_admission()
            ssn_masked = record["ssn_masked"]
            # Masked format: XXX-XX-####
            assert ssn_masked.startswith("XXX-XX-"), f"SSN not masked: {ssn_masked}"

    def test_ssn_synthetic_range(self, generator):
        """Verify underlying SSN generation uses 900-series."""
        for _ in range(50):
            ssn = generator.synthetic_ssn()
            area = int(ssn.split("-")[0])
            assert 900 <= area <= 999, f"SSN area {area} not in 900-series"

    def test_mrn_is_hashed(self, generator):
        record = generator.generate_admission()
        mrn_hash = record["mrn_hash"]
        # HMAC-SHA-256 produces 64 hex characters
        assert len(mrn_hash) == 64
        assert re.match(r"^[a-f0-9]{64}$", mrn_hash)

    def test_no_raw_mrn_in_record(self, generator):
        record = generator.generate_admission()
        for key, value in record.items():
            if isinstance(value, str) and key != "mrn_hash":
                assert not value.startswith("MRN-"), f"Raw MRN found in {key}"


class TestDrgCodes:
    """Validate DRG code generation."""

    def test_drg_codes_valid(self, generator):
        for _ in range(100):
            record = generator.generate_admission()
            assert record["drg_code"] in TOP_25_DRG

    def test_drg_codes_distributed(self, generator):
        codes = {generator.generate_admission()["drg_code"] for _ in range(500)}
        assert len(codes) >= 5, "DRG codes should have some variety"


class TestLos:
    """Validate length of stay."""

    def test_los_positive(self, generator):
        for _ in range(100):
            record = generator.generate_admission()
            assert record["los"] >= 1, f"LOS must be >= 1, got {record['los']}"

    def test_los_capped(self, generator):
        for _ in range(200):
            record = generator.generate_admission()
            assert record["los"] <= 60, f"LOS must be <= 60, got {record['los']}"


class TestReadmitFlag:
    """Validate readmission flag."""

    def test_readmit_flag_binary(self, generator):
        for _ in range(100):
            record = generator.generate_admission()
            assert record["readmit_flag"] in (0, 1)


class TestClaimsAmounts:
    """Validate claim financial amounts."""

    def test_claims_amounts_valid(self, generator):
        for _ in range(100):
            claim = generator.generate_claim()
            assert claim["billed_amt"] > 0
            assert claim["allowed_amt"] > 0
            assert claim["allowed_amt"] <= claim["billed_amt"]
            if claim["denial_reason_code"] is None:
                assert claim["paid_amt"] > 0
                assert claim["paid_amt"] <= claim["allowed_amt"]
            else:
                assert claim["paid_amt"] == 0.0

    def test_claim_has_valid_codes(self, generator):
        claim = generator.generate_claim()
        assert claim["cpt_code"] is not None
        assert claim["icd10_code"] is not None
        assert claim["claim_id"].startswith("CLM-")


class TestReproducibility:
    """Verify seed-based reproducibility."""

    def test_reproducibility_with_seed(self):
        gen1 = HospitalOperationsGenerator(seed=123)
        gen2 = HospitalOperationsGenerator(seed=123)

        records1 = [gen1.generate_admission() for _ in range(10)]
        records2 = [gen2.generate_admission() for _ in range(10)]

        for r1, r2 in zip(records1, records2, strict=False):
            assert r1["encounter_id"] == r2["encounter_id"]
            assert r1["mrn_hash"] == r2["mrn_hash"]
            assert r1["drg_code"] == r2["drg_code"]
            assert r1["los"] == r2["los"]
            assert r1["payer"] == r2["payer"]

    def test_different_seeds_differ(self):
        gen1 = HospitalOperationsGenerator(seed=1)
        gen2 = HospitalOperationsGenerator(seed=2)

        r1 = gen1.generate_admission()
        r2 = gen2.generate_admission()
        # Very unlikely to match on all fields
        assert r1["mrn_hash"] != r2["mrn_hash"] or r1["drg_code"] != r2["drg_code"]
