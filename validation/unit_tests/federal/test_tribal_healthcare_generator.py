"""
Unit tests for TribalHealthcareGenerator.

Covers synthetic Indian Health Service (IHS) healthcare encounter data
generation including encounter types, ICD-10 diagnoses weighted toward
Native American health disparities, CPT codes, provider types, tribal
affiliations, medications, lab results, and HIPAA compliance flags.
"""
import pytest

from generators.federal.tribal_healthcare_generator import (
    TribalHealthcareGenerator,
    AREA_OFFICES,
    ENCOUNTER_TYPES,
    TRIBAL_AFFILIATIONS,
    PROVIDER_TYPES,
    AGE_GROUPS,
    GENDERS,
    INSURANCE_TYPES,
    ICD10_CODES,
    CPT_CODES,
    MEDICATIONS,
    LAB_TESTS,
    FACILITIES,
)

_VALID_ENCOUNTER_TYPES = set(ENCOUNTER_TYPES)
_VALID_AREA_OFFICES = {f["area"] for f in FACILITIES}
_VALID_FACILITY_IDS = {f["id"] for f in FACILITIES}
_VALID_TRIBAL_AFFILIATIONS = set(TRIBAL_AFFILIATIONS)
_VALID_PROVIDER_TYPES = set(PROVIDER_TYPES)
_VALID_AGE_GROUPS = set(AGE_GROUPS)
_VALID_GENDERS = set(GENDERS)
_VALID_INSURANCE_TYPES = set(INSURANCE_TYPES)
_VALID_ICD10_CODES = {c["code"] for c in ICD10_CODES}
_VALID_CPT_CODES = {c["code"] for c in CPT_CODES}
_VALID_MEDICATION_NAMES = {m["name"] for m in MEDICATIONS}
_VALID_LAB_TEST_NAMES = {t["name"] for t in LAB_TESTS}
_VALID_LAB_ABNORMAL_FLAGS = {"N", "L", "H", "LL", "HH"}


class TestTribalHealthcareGenerator:
    """Tests for TribalHealthcareGenerator covering encounter generation."""

    # ------------------------------------------------------------------
    # Basic field presence
    # ------------------------------------------------------------------

    def test_generate_record(self, tribal_healthcare_generator):
        """Generate a record and assert required top-level fields exist."""
        record = tribal_healthcare_generator.generate_record()

        assert record is not None, "generate_record returned None"
        assert "record_id" in record, "record_id field missing"
        assert "patient_id" in record, "patient_id field missing"
        assert "facility_id" in record, "facility_id field missing"
        assert "encounter_type" in record, "encounter_type field missing"
        assert "encounter_date" in record, "encounter_date field missing"
        assert "icd10_code" in record, "icd10_code field missing"
        assert "tribal_affiliation" in record, "tribal_affiliation field missing"

    # ------------------------------------------------------------------
    # Encounter type enum
    # ------------------------------------------------------------------

    def test_encounter_type_valid(self, tribal_healthcare_generator, sample_size):
        """All encounter_type values must come from the defined set."""
        for _ in range(sample_size):
            record = tribal_healthcare_generator.generate_record()
            assert record["encounter_type"] in _VALID_ENCOUNTER_TYPES, (
                f"Unexpected encounter_type '{record['encounter_type']}'"
            )

    # ------------------------------------------------------------------
    # Facility validation
    # ------------------------------------------------------------------

    def test_facility_id_valid(self, tribal_healthcare_generator, sample_size):
        """facility_id must be one of the 20 known IHS facility IDs."""
        for _ in range(sample_size):
            record = tribal_healthcare_generator.generate_record()
            assert record["facility_id"] in _VALID_FACILITY_IDS, (
                f"Unexpected facility_id '{record['facility_id']}'"
            )

    # ------------------------------------------------------------------
    # ICD-10 diagnosis codes
    # ------------------------------------------------------------------

    def test_icd10_code_valid(self, tribal_healthcare_generator, sample_size):
        """icd10_code must be one of the known ICD-10 codes."""
        for _ in range(sample_size):
            record = tribal_healthcare_generator.generate_record()
            assert record["icd10_code"] in _VALID_ICD10_CODES, (
                f"Unexpected icd10_code '{record['icd10_code']}'"
            )

    # ------------------------------------------------------------------
    # Tribal affiliation enum
    # ------------------------------------------------------------------

    def test_tribal_affiliation_valid(self, tribal_healthcare_generator, sample_size):
        """tribal_affiliation must be one of the 30 known tribes."""
        for _ in range(sample_size):
            record = tribal_healthcare_generator.generate_record()
            assert record["tribal_affiliation"] in _VALID_TRIBAL_AFFILIATIONS, (
                f"Unexpected tribal_affiliation '{record['tribal_affiliation']}'"
            )

    # ------------------------------------------------------------------
    # Demographics validation
    # ------------------------------------------------------------------

    def test_demographics_valid(self, tribal_healthcare_generator, sample_size):
        """age_group, gender, and insurance_type must be valid enum values."""
        for _ in range(sample_size):
            record = tribal_healthcare_generator.generate_record()
            assert record["age_group"] in _VALID_AGE_GROUPS, (
                f"Unexpected age_group '{record['age_group']}'"
            )
            assert record["gender"] in _VALID_GENDERS, (
                f"Unexpected gender '{record['gender']}'"
            )
            assert record["insurance_type"] in _VALID_INSURANCE_TYPES, (
                f"Unexpected insurance_type '{record['insurance_type']}'"
            )

    # ------------------------------------------------------------------
    # HIPAA compliance flags
    # ------------------------------------------------------------------

    def test_hipaa_compliance_flags(self, tribal_healthcare_generator, sample_size):
        """hipaa_consent and phi_masked must always be True."""
        for _ in range(sample_size):
            record = tribal_healthcare_generator.generate_record()
            assert record["hipaa_consent"] is True, (
                "hipaa_consent must be True for de-identified data"
            )
            assert record["phi_masked"] is True, (
                "phi_masked must be True for de-identified data"
            )

    # ------------------------------------------------------------------
    # Lab result abnormal flag validation
    # ------------------------------------------------------------------

    def test_lab_abnormal_flag_valid(self, tribal_healthcare_generator):
        """When lab results are present, lab_abnormal_flag must be a valid flag."""
        found_lab = False
        for _ in range(500):
            record = tribal_healthcare_generator.generate_record()
            if record["lab_test_name"] is not None:
                found_lab = True
                assert record["lab_abnormal_flag"] in _VALID_LAB_ABNORMAL_FLAGS, (
                    f"Unexpected lab_abnormal_flag '{record['lab_abnormal_flag']}'"
                )
                assert record["lab_result_value"] is not None, (
                    "lab_result_value must not be None when lab_test_name is set"
                )
                assert record["lab_result_unit"] is not None, (
                    "lab_result_unit must not be None when lab_test_name is set"
                )

        assert found_lab, "No lab results seen in 500 records"

    # ------------------------------------------------------------------
    # Patient ID format
    # ------------------------------------------------------------------

    def test_patient_id_format(self, tribal_healthcare_generator, sample_size):
        """patient_id must follow the PAT-XXXXXXXX pattern."""
        for _ in range(sample_size):
            record = tribal_healthcare_generator.generate_record()
            pid = record["patient_id"]
            assert pid.startswith("PAT-"), (
                f"patient_id must start with 'PAT-', got '{pid}'"
            )
            assert len(pid) == 12, (
                f"patient_id must be 12 chars (PAT- + 8 hex), got '{pid}' (len={len(pid)})"
            )

    # ------------------------------------------------------------------
    # Batch generation
    # ------------------------------------------------------------------

    def test_generate_batch(self, tribal_healthcare_generator, sample_size):
        """generate_batch returns a DataFrame with the requested number of rows."""
        df = tribal_healthcare_generator.generate_batch(count=sample_size)

        assert len(df) == sample_size, (
            f"Expected {sample_size} rows, got {len(df)}"
        )

    # ------------------------------------------------------------------
    # Metadata columns
    # ------------------------------------------------------------------

    def test_metadata_columns_present(self, tribal_healthcare_generator):
        """Standard metadata columns _ingested_at, _source, _batch_id must be present."""
        record = tribal_healthcare_generator.generate_record()

        assert "_ingested_at" in record, "_ingested_at metadata column missing"
        assert "_source" in record, "_source metadata column missing"
        assert "_batch_id" in record, "_batch_id metadata column missing"
        assert record["_source"] == "TribalHealthcareGenerator", (
            f"Expected _source='TribalHealthcareGenerator', got '{record['_source']}'"
        )

    # ------------------------------------------------------------------
    # Medication conditional presence
    # ------------------------------------------------------------------

    def test_pharmacy_encounter_has_medication(self, tribal_healthcare_generator):
        """Pharmacy encounters must always have medication_name and medication_ndc."""
        found_pharmacy = False
        for _ in range(500):
            record = tribal_healthcare_generator.generate_record()
            if record["encounter_type"] == "pharmacy":
                found_pharmacy = True
                assert record["medication_name"] is not None, (
                    "pharmacy encounter must have medication_name"
                )
                assert record["medication_ndc"] is not None, (
                    "pharmacy encounter must have medication_ndc"
                )

        assert found_pharmacy, "No pharmacy encounters seen in 500 records"
