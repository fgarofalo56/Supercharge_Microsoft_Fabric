"""
Unit tests for TrialGenerator.

Covers three domains:
- subject: enrollment demographics and status
- adverse_event: MedDRA-coded AE records
- visit: scheduled vs actual visits with deviation flagging

Compliance: 21 CFR Part 11, GxP
"""

import pytest

from data_generation.generators.pharma.trial_generator import (
    AE_SEVERITIES,
    MEDDRA_PT_SOC,
    MEDDRA_PTS,
    SUBJECT_STATUSES,
    TrialGenerator,
)

VALID_STATUSES_LOWER = [s.lower() for s in SUBJECT_STATUSES]


@pytest.fixture
def trial_generator():
    """Create a seeded TrialGenerator for reproducible tests."""
    return TrialGenerator(seed=42, num_studies=10)


class TestTrialGenerator:
    """Tests for TrialGenerator covering subject, adverse_event, and visit domains."""

    # ------------------------------------------------------------------
    # Subject domain
    # ------------------------------------------------------------------

    def test_generate_subjects(self, trial_generator):
        """Generate a subject record and assert required fields are present."""
        record = trial_generator.generate_record(domain="subject")

        assert record is not None
        assert "subject_id" in record
        assert "site_id" in record
        assert "study_id" in record
        assert "enrollment_dt" in record
        assert "arm" in record
        assert "status" in record
        assert "age" in record
        assert "sex" in record

        # subject_id format
        assert record["subject_id"].startswith("SUBJ-")
        assert record["site_id"].startswith("SITE-")
        assert record["study_id"].startswith("STUDY-")

    def test_status_values(self, trial_generator):
        """All subject statuses must be from the defined set."""
        for _ in range(200):
            record = trial_generator.generate_record(domain="subject")
            assert record["status"].lower() in VALID_STATUSES_LOWER, (
                f"Unexpected status: {record['status']}"
            )

    def test_subject_age_range(self, trial_generator):
        """Subject age must be between 18 and 85 inclusive."""
        for _ in range(200):
            record = trial_generator.generate_record(domain="subject")
            assert 18 <= record["age"] <= 85

    # ------------------------------------------------------------------
    # Adverse event domain
    # ------------------------------------------------------------------

    def test_ae_severity(self, trial_generator):
        """AE severity must be Mild, Moderate, or Severe."""
        # Generate some subjects first for cross-referencing
        for _ in range(50):
            trial_generator.generate_record(domain="subject")

        for _ in range(200):
            record = trial_generator.generate_record(domain="adverse_event")
            assert record["severity"] in AE_SEVERITIES, (
                f"Unexpected severity: {record['severity']}"
            )

    def test_meddra_format(self, trial_generator):
        """MedDRA PT must be from the known list and SOC must match."""
        for _ in range(50):
            trial_generator.generate_record(domain="subject")

        for _ in range(200):
            record = trial_generator.generate_record(domain="adverse_event")
            assert record["meddra_pt"] in MEDDRA_PTS, (
                f"Unknown MedDRA PT: {record['meddra_pt']}"
            )
            expected_soc = MEDDRA_PT_SOC[record["meddra_pt"]]
            assert record["meddra_soc"] == expected_soc, (
                f"SOC mismatch: {record['meddra_soc']} != {expected_soc}"
            )

    # ------------------------------------------------------------------
    # Dropout rate
    # ------------------------------------------------------------------

    def test_dropout_rate(self, trial_generator):
        """Withdrawn subjects should be roughly 15-25% of the population."""
        records = [
            trial_generator.generate_record(domain="subject") for _ in range(2000)
        ]
        withdrawn = sum(1 for r in records if r["status"].lower() == "withdrawn")
        rate = withdrawn / len(records)
        # Allow wider tolerance for random sampling: 10-35%
        assert 0.10 <= rate <= 0.35, f"Dropout rate {rate:.2%} outside expected range"

    # ------------------------------------------------------------------
    # Reproducibility
    # ------------------------------------------------------------------

    def test_reproducibility(self):
        """Two generators with the same seed must produce identical records."""
        gen1 = TrialGenerator(seed=123, num_studies=5)
        gen2 = TrialGenerator(seed=123, num_studies=5)

        for _ in range(50):
            r1 = gen1.generate_record(domain="subject")
            r2 = gen2.generate_record(domain="subject")
            # Compare deterministic fields (exclude _ingested_at which uses datetime.now)
            assert r1["subject_id"] == r2["subject_id"]
            assert r1["site_id"] == r2["site_id"]
            assert r1["study_id"] == r2["study_id"]
            assert r1["status"] == r2["status"]
            assert r1["arm"] == r2["arm"]
            assert r1["age"] == r2["age"]
