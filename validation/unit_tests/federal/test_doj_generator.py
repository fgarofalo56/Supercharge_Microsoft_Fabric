"""
Unit tests for DOJGenerator.

Tests cover all four DOJ domains (crime_stats, federal_cases, antitrust,
drug_enforcement) and validate field presence, value constraints, business
rules, and metadata columns.
Fixtures are provided by the federal conftest.py (doj_generator, sample_size).
"""

import re

# Valid reference sets for assertions
VALID_OFFENSE_CATEGORIES = {"Persons", "Property", "Society"}
VALID_CLEARANCE_STATUSES = {"Cleared by Arrest", "Not Cleared", "Exceptionally Cleared"}
VALID_CASE_TYPES = {"Criminal", "Civil", "Merger Review"}
VALID_DOJ_ACTIONS = {"Approved", "Challenged", "Consent Decree", "Blocked", "Abandoned"}
VALID_DRUG_TYPES = {"Cocaine", "Heroin", "Fentanyl", "Methamphetamine", "Cannabis", "MDMA", "Other"}
VALID_DRUG_SCHEDULES = {"I", "II"}
VALID_DEPARTURE_TYPES = {"None", "Above", "Below", "Substantial Assistance"}


class TestDOJGeneratorCrimeStats:
    """Tests for the crime_stats domain (FBI UCR/NIBRS)."""

    def test_generate_crime_record(self, doj_generator):
        """Generated crime record contains required identification fields."""
        record = doj_generator.generate_record(domain="crime_stats")

        assert "incident_id" in record
        assert "ori_code" in record
        assert "offense_code" in record
        assert "state_code" in record

    def test_offense_category_valid(self, doj_generator):
        """offense_category is always Persons, Property, or Society."""
        for _ in range(100):
            record = doj_generator.generate_record(domain="crime_stats")
            assert record["offense_category"] in VALID_OFFENSE_CATEGORIES

    def test_state_code_format(self, doj_generator):
        """state_code is a 2-letter uppercase abbreviation."""
        for _ in range(100):
            record = doj_generator.generate_record(domain="crime_stats")
            state = record["state_code"]
            assert len(state) == 2, f"Expected 2-letter state, got '{state}'"
            assert state.isupper(), f"State must be uppercase, got '{state}'"

    def test_clearance_status_valid(self, doj_generator):
        """clearance_status is always a valid status."""
        for _ in range(100):
            record = doj_generator.generate_record(domain="crime_stats")
            assert record["clearance_status"] in VALID_CLEARANCE_STATUSES

    def test_victim_count_non_negative(self, doj_generator):
        """victim_count is non-negative (0 for society crimes)."""
        for _ in range(100):
            record = doj_generator.generate_record(domain="crime_stats")
            assert record["victim_count"] >= 0

    def test_ori_code_format(self, doj_generator):
        """ORI code follows state+prefix+number pattern."""
        record = doj_generator.generate_record(domain="crime_stats")
        ori = record["ori_code"]
        assert len(ori) >= 7, f"ORI code too short: '{ori}'"
        assert ori[:2].isalpha(), f"ORI should start with state code: '{ori}'"


class TestDOJGeneratorFederalCases:
    """Tests for the federal_cases domain (USSC sentencing)."""

    def test_generate_federal_case(self, doj_generator):
        """Generated federal case contains required fields."""
        record = doj_generator.generate_record(domain="federal_cases")

        assert "case_id" in record
        assert "district_court" in record
        assert "circuit" in record
        assert "sentence_months" in record

    def test_sentence_non_negative(self, doj_generator):
        """sentence_months is non-negative."""
        for _ in range(100):
            record = doj_generator.generate_record(domain="federal_cases")
            assert record["sentence_months"] >= 0

    def test_guideline_range_logic(self, doj_generator):
        """guideline_range_max_months >= guideline_range_min_months."""
        for _ in range(100):
            record = doj_generator.generate_record(domain="federal_cases")
            assert record["guideline_range_max_months"] >= record["guideline_range_min_months"]

    def test_departure_type_valid(self, doj_generator):
        """departure_type is a valid value."""
        for _ in range(100):
            record = doj_generator.generate_record(domain="federal_cases")
            assert record["departure_type"] in VALID_DEPARTURE_TYPES

    def test_defendant_age_range(self, doj_generator):
        """defendant_age is within realistic range (18-75)."""
        for _ in range(100):
            record = doj_generator.generate_record(domain="federal_cases")
            assert 18 <= record["defendant_age"] <= 75

    def test_plea_type_present(self, doj_generator):
        """plea_type field is present and non-empty."""
        record = doj_generator.generate_record(domain="federal_cases")
        assert record["plea_type"] in {"Guilty Plea", "Not Guilty", "Nolo Contendere"}


class TestDOJGeneratorAntitrust:
    """Tests for the antitrust domain (DOJ Antitrust Division)."""

    def test_generate_antitrust_record(self, doj_generator):
        """Generated antitrust record contains required fields."""
        record = doj_generator.generate_record(domain="antitrust")

        assert "case_id" in record
        assert "case_type" in record
        assert "doj_action" in record
        assert "industry_sector" in record

    def test_case_type_valid(self, doj_generator):
        """case_type is Criminal, Civil, or Merger Review."""
        for _ in range(100):
            record = doj_generator.generate_record(domain="antitrust")
            assert record["case_type"] in VALID_CASE_TYPES

    def test_doj_action_valid(self, doj_generator):
        """doj_action is always a recognized action."""
        for _ in range(100):
            record = doj_generator.generate_record(domain="antitrust")
            assert record["doj_action"] in VALID_DOJ_ACTIONS

    def test_hhi_logic_merger_only(self, doj_generator):
        """HHI fields are populated only for Merger Review cases."""
        for _ in range(200):
            record = doj_generator.generate_record(domain="antitrust")
            if record["case_type"] == "Merger Review":
                assert record["hhi_pre_merger"] is not None
                assert record["hhi_post_merger"] is not None
                assert record["hhi_delta"] is not None
                assert record["hhi_post_merger"] == (
                    record["hhi_pre_merger"] + record["hhi_delta"]
                ), "HHI post = pre + delta"
            else:
                assert record["hhi_pre_merger"] is None

    def test_hhi_delta_positive(self, doj_generator):
        """HHI delta is positive for merger cases (mergers increase concentration)."""
        for _ in range(200):
            record = doj_generator.generate_record(domain="antitrust")
            if record["hhi_delta"] is not None:
                assert record["hhi_delta"] > 0

    def test_transaction_value_positive(self, doj_generator):
        """transaction_value_usd is positive."""
        for _ in range(50):
            record = doj_generator.generate_record(domain="antitrust")
            assert record["transaction_value_usd"] > 0

    def test_industry_sector_naics(self, doj_generator):
        """industry_sector is a valid 2-digit NAICS code."""
        record = doj_generator.generate_record(domain="antitrust")
        sector = record["industry_sector"]
        assert len(sector) == 2
        assert sector.isdigit()


class TestDOJGeneratorDrugEnforcement:
    """Tests for the drug_enforcement domain (DEA)."""

    def test_generate_drug_record(self, doj_generator):
        """Generated drug enforcement record contains required fields."""
        record = doj_generator.generate_record(domain="drug_enforcement")

        assert "seizure_id" in record
        assert "drug_type" in record
        assert "quantity_kg" in record
        assert "estimated_street_value_usd" in record

    def test_drug_type_valid(self, doj_generator):
        """drug_type is a recognized DEA drug classification."""
        for _ in range(100):
            record = doj_generator.generate_record(domain="drug_enforcement")
            assert record["drug_type"] in VALID_DRUG_TYPES

    def test_drug_schedule_valid(self, doj_generator):
        """drug_schedule is a valid CSA schedule."""
        for _ in range(100):
            record = doj_generator.generate_record(domain="drug_enforcement")
            assert record["drug_schedule"] in VALID_DRUG_SCHEDULES

    def test_quantity_positive(self, doj_generator):
        """quantity_kg is strictly positive."""
        for _ in range(100):
            record = doj_generator.generate_record(domain="drug_enforcement")
            assert record["quantity_kg"] > 0

    def test_street_value_positive(self, doj_generator):
        """estimated_street_value_usd is positive."""
        for _ in range(100):
            record = doj_generator.generate_record(domain="drug_enforcement")
            assert record["estimated_street_value_usd"] > 0

    def test_quarter_valid(self, doj_generator):
        """quarter is 1-4."""
        for _ in range(100):
            record = doj_generator.generate_record(domain="drug_enforcement")
            assert record["quarter"] in {1, 2, 3, 4}


class TestDOJGeneratorGeneral:
    """Cross-domain and general tests."""

    def test_invalid_domain_raises(self, doj_generator):
        """Passing an invalid domain raises ValueError."""
        try:
            doj_generator.generate_record(domain="invalid")
            assert False, "Expected ValueError"
        except ValueError:
            pass

    def test_generate_batch(self, doj_generator, sample_size):
        """generate_batch returns the requested number of records."""
        records = doj_generator.generate_batch(count=sample_size, domain="crime_stats")

        assert len(records) == sample_size
        assert all(isinstance(r, dict) for r in records)
        assert all("incident_id" in r for r in records)

    def test_metadata_columns(self, doj_generator):
        """Every record includes the standard metadata columns."""
        for domain in ("crime_stats", "federal_cases", "antitrust", "drug_enforcement"):
            record = doj_generator.generate_record(domain=domain)
            assert "_ingested_at" in record, f"Missing _ingested_at in {domain}"
            assert "_source" in record, f"Missing _source in {domain}"
            assert "_batch_id" in record, f"Missing _batch_id in {domain}"

    def test_source_identifies_generator(self, doj_generator):
        """_source metadata identifies DOJGenerator."""
        record = doj_generator.generate_record(domain="crime_stats")
        assert record["_source"] == "DOJGenerator"
