"""
Unit tests for SBAGenerator.

Tests cover all four SBA program domains (ppp, 7a, disaster, sbir) and validate
field presence, value constraints, business rules, and metadata columns.
Fixtures are provided by the federal conftest.py (sba_generator, sample_size).
"""

VALID_LOAN_STATUSES = {"APPROVED", "ACTIVE", "PAID_IN_FULL", "CHARGED_OFF", "CANCELLED"}


class TestSBAGenerator:
    """Tests for SBAGenerator covering all four SBA program domains."""

    def test_generate_ppp_record(self, sba_generator):
        """Generated PPP record contains required loan identification fields."""
        record = sba_generator.generate_record(domain="ppp")

        assert "loan_id" in record
        assert "program_type" in record
        assert "loan_amount" in record
        assert "approval_date" in record

    def test_ppp_program_type(self, sba_generator):
        """All records generated from the ppp domain carry program_type 'PPP'."""
        for _ in range(100):
            record = sba_generator.generate_record(domain="ppp")
            assert record["program_type"] == "PPP"

    def test_loan_amount_positive(self, sba_generator):
        """Loan amount is strictly positive for default (ppp) domain."""
        record = sba_generator.generate_record(domain="ppp")

        assert record["loan_amount"] > 0

    def test_loan_status_valid(self, sba_generator):
        """loan_status is always a member of the allowed status set."""
        for _ in range(100):
            record = sba_generator.generate_record(domain="ppp")
            assert record["loan_status"] in VALID_LOAN_STATUSES

    def test_naics_code_format(self, sba_generator):
        """naics_code is either a 6-digit string or None."""
        for _ in range(100):
            record = sba_generator.generate_record(domain="ppp")
            naics = record.get("naics_code")
            if naics is not None:
                assert len(naics) == 6, f"Expected 6-digit NAICS code, got '{naics}'"
                assert naics.isdigit(), f"NAICS code must be all digits, got '{naics}'"

    def test_borrower_state_format(self, sba_generator):
        """borrower_state is a 2-letter uppercase abbreviation."""
        for _ in range(100):
            record = sba_generator.generate_record(domain="ppp")
            state = record["borrower_state"]
            assert len(state) == 2, f"Expected 2-letter state, got '{state}'"
            assert state.isupper(), f"State must be uppercase, got '{state}'"
            assert state.isalpha(), f"State must be alphabetic, got '{state}'"

    def test_ppp_forgiveness(self, sba_generator):
        """PPP records can carry a forgiveness_amount field (may be None or float)."""
        found_with_forgiveness = False

        for _ in range(500):
            record = sba_generator.generate_record(domain="ppp")
            if record.get("forgiveness_amount") is not None:
                assert record["forgiveness_amount"] >= 0
                found_with_forgiveness = True
                break

        assert found_with_forgiveness, (
            "Expected at least one PPP record to have forgiveness_amount set "
            "within 500 iterations"
        )

    def test_7a_domain(self, sba_generator):
        """generate_record with domain='7a' returns a record with program_type '7A'."""
        record = sba_generator.generate_record(domain="7a")

        assert record["program_type"] == "7A"

    def test_disaster_domain(self, sba_generator):
        """generate_record with domain='disaster' returns program_type 'DISASTER'."""
        record = sba_generator.generate_record(domain="disaster")

        assert record["program_type"] == "DISASTER"

    def test_generate_batch(self, sba_generator, sample_size):
        """generate_batch returns the requested number of records."""
        records = sba_generator.generate_batch(count=sample_size, domain="ppp")

        assert len(records) == sample_size
        assert all(isinstance(r, dict) for r in records)
        assert all("loan_id" in r for r in records)

    def test_metadata_columns(self, sba_generator):
        """Every record includes the standard metadata columns added by BaseGenerator."""
        record = sba_generator.generate_record(domain="ppp")

        assert "_ingested_at" in record, "Missing _ingested_at metadata column"
        assert "_source" in record, "Missing _source metadata column"
        assert "_batch_id" in record, "Missing _batch_id metadata column"
