"""
Tribal Healthcare Generator
============================

Generates synthetic Indian Health Service (IHS) healthcare encounter data
covering outpatient, inpatient, emergency, telehealth, dental, behavioral
health, pharmacy, and laboratory encounters.

Data shapes reflect real IHS reporting structures including area offices,
service units, facility codes, ICD-10 diagnoses weighted toward Native
American health disparities, and HIPAA-compliant de-identified fields.

Key epidemiological weighting:
- Type 2 Diabetes: 15% (highest prevalence among AI/AN populations)
- Respiratory infections: 12%
- Cardiovascular (hypertension, hyperlipidemia): 10%
- Behavioral health (depression, alcohol-related): 10%
- Remaining diagnoses distributed across musculoskeletal, metabolic,
  genitourinary, gastrointestinal, and dental conditions.
"""

from datetime import datetime
from typing import Any

from ..base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# IHS Area Offices (12 regional administrative offices)
# ---------------------------------------------------------------------------
AREA_OFFICES = [
    "Aberdeen",
    "Albuquerque",
    "Bemidji",
    "Billings",
    "Great Plains",
    "Nashville",
    "Navajo",
    "Oklahoma City",
    "Phoenix",
    "Portland",
    "Tucson",
    "California",
]

AREA_OFFICE_WEIGHTS = [
    0.06,
    0.10,
    0.06,
    0.06,
    0.06,
    0.08,
    0.16,
    0.14,
    0.10,
    0.08,
    0.05,
    0.05,
]

# ---------------------------------------------------------------------------
# Tribal Affiliations (30 federally recognized tribes)
# ---------------------------------------------------------------------------
TRIBAL_AFFILIATIONS = [
    "Navajo Nation",
    "Cherokee Nation",
    "Choctaw Nation of Oklahoma",
    "Muscogee (Creek) Nation",
    "Oglala Sioux Tribe",
    "Rosebud Sioux Tribe",
    "Standing Rock Sioux Tribe",
    "Chippewa (Ojibwe)",
    "Apache Tribe",
    "Pueblo of Zuni",
    "Pueblo of Laguna",
    "Blackfeet Nation",
    "Crow Tribe",
    "Northern Cheyenne Tribe",
    "Tohono O'odham Nation",
    "Gila River Indian Community",
    "Salt River Pima-Maricopa",
    "Seminole Tribe of Florida",
    "Chickasaw Nation",
    "Poarch Band of Creek Indians",
    "Eastern Band of Cherokee",
    "Ho-Chunk Nation",
    "Menominee Indian Tribe",
    "Oneida Nation",
    "Yakama Nation",
    "Colville Confederated Tribes",
    "Confederated Tribes of Warm Springs",
    "Hoopa Valley Tribe",
    "Tule River Indian Tribe",
    "Lummi Nation",
]

TRIBAL_WEIGHTS = [
    0.14,
    0.10,
    0.07,
    0.06,
    0.05,
    0.04,
    0.03,
    0.05,
    0.04,
    0.03,
    0.03,
    0.03,
    0.02,
    0.02,
    0.04,
    0.03,
    0.02,
    0.02,
    0.03,
    0.01,
    0.02,
    0.02,
    0.01,
    0.02,
    0.02,
    0.01,
    0.01,
    0.01,
    0.01,
    0.01,
]

# ---------------------------------------------------------------------------
# IHS Facilities (20 health centers / hospitals)
# ---------------------------------------------------------------------------
FACILITIES: list[dict[str, str]] = [
    {
        "id": "IHS-NAV-001",
        "name": "Shiprock Northern Navajo Medical Center",
        "area": "Navajo",
        "service_unit": "Shiprock Service Unit",
    },
    {
        "id": "IHS-NAV-002",
        "name": "Chinle Comprehensive Health Care Facility",
        "area": "Navajo",
        "service_unit": "Chinle Service Unit",
    },
    {
        "id": "IHS-NAV-003",
        "name": "Gallup Indian Medical Center",
        "area": "Navajo",
        "service_unit": "Gallup Service Unit",
    },
    {
        "id": "IHS-NAV-004",
        "name": "Crownpoint Health Care Facility",
        "area": "Navajo",
        "service_unit": "Crownpoint Service Unit",
    },
    {
        "id": "IHS-NAV-005",
        "name": "Kayenta Health Center",
        "area": "Navajo",
        "service_unit": "Kayenta Service Unit",
    },
    {
        "id": "IHS-PHX-001",
        "name": "Phoenix Indian Medical Center",
        "area": "Phoenix",
        "service_unit": "Phoenix Service Unit",
    },
    {
        "id": "IHS-PHX-002",
        "name": "Hu Hu Kam Memorial Hospital",
        "area": "Phoenix",
        "service_unit": "Gila River Service Unit",
    },
    {
        "id": "IHS-PHX-003",
        "name": "Salt River Health Center",
        "area": "Phoenix",
        "service_unit": "Salt River Service Unit",
    },
    {
        "id": "IHS-TUC-001",
        "name": "Sells Indian Hospital",
        "area": "Tucson",
        "service_unit": "Sells Service Unit",
    },
    {
        "id": "IHS-ABQ-001",
        "name": "Albuquerque Indian Health Center",
        "area": "Albuquerque",
        "service_unit": "Albuquerque Service Unit",
    },
    {
        "id": "IHS-ABQ-002",
        "name": "Zuni Comprehensive Health Center",
        "area": "Albuquerque",
        "service_unit": "Zuni-Ramah Service Unit",
    },
    {
        "id": "IHS-OKC-001",
        "name": "Claremore Indian Hospital",
        "area": "Oklahoma City",
        "service_unit": "Claremore Service Unit",
    },
    {
        "id": "IHS-OKC-002",
        "name": "Lawton Indian Hospital",
        "area": "Oklahoma City",
        "service_unit": "Lawton Service Unit",
    },
    {
        "id": "IHS-OKC-003",
        "name": "Chickasaw Nation Medical Center",
        "area": "Oklahoma City",
        "service_unit": "Ada Service Unit",
    },
    {
        "id": "IHS-ABD-001",
        "name": "Pine Ridge Hospital",
        "area": "Great Plains",
        "service_unit": "Pine Ridge Service Unit",
    },
    {
        "id": "IHS-ABD-002",
        "name": "Rosebud Hospital",
        "area": "Great Plains",
        "service_unit": "Rosebud Service Unit",
    },
    {
        "id": "IHS-BIL-001",
        "name": "Blackfeet Community Hospital",
        "area": "Billings",
        "service_unit": "Blackfeet Service Unit",
    },
    {
        "id": "IHS-BMJ-001",
        "name": "Red Lake Hospital",
        "area": "Bemidji",
        "service_unit": "Red Lake Service Unit",
    },
    {
        "id": "IHS-NSH-001",
        "name": "Cherokee Indian Hospital",
        "area": "Nashville",
        "service_unit": "Cherokee Service Unit",
    },
    {
        "id": "IHS-POR-001",
        "name": "Yakama Indian Health Center",
        "area": "Portland",
        "service_unit": "Yakama Service Unit",
    },
]

# ---------------------------------------------------------------------------
# Encounter types and weights
# ---------------------------------------------------------------------------
ENCOUNTER_TYPES = [
    "outpatient",
    "inpatient",
    "emergency",
    "telehealth",
    "dental",
    "behavioral_health",
    "pharmacy",
    "laboratory",
]

ENCOUNTER_WEIGHTS = [0.35, 0.08, 0.10, 0.07, 0.12, 0.08, 0.12, 0.08]

# ---------------------------------------------------------------------------
# ICD-10 Diagnoses weighted toward Native American health disparities
# ---------------------------------------------------------------------------
ICD10_CODES: list[dict[str, str]] = [
    # Diabetes (15%)
    {"code": "E11.9", "desc": "Type 2 diabetes mellitus without complications"},
    {"code": "E11.65", "desc": "Type 2 diabetes mellitus with hyperglycemia"},
    {"code": "E11.22", "desc": "Type 2 diabetes with diabetic chronic kidney disease"},
    {"code": "E11.40", "desc": "Type 2 diabetes with diabetic neuropathy, unspecified"},
    {
        "code": "E11.311",
        "desc": "Type 2 diabetes with unspecified diabetic retinopathy with macular edema",
    },
    # Respiratory (12%)
    {"code": "J06.9", "desc": "Acute upper respiratory infection, unspecified"},
    {"code": "J45.20", "desc": "Mild intermittent asthma, uncomplicated"},
    {"code": "J45.40", "desc": "Moderate persistent asthma, uncomplicated"},
    # Cardiovascular (10%)
    {"code": "I10", "desc": "Essential (primary) hypertension"},
    {"code": "E78.5", "desc": "Hyperlipidemia, unspecified"},
    {
        "code": "I25.10",
        "desc": "Atherosclerotic heart disease of native coronary artery without angina pectoris",
    },
    # Behavioral Health (10%)
    {"code": "F32.1", "desc": "Major depressive disorder, single episode, moderate"},
    {"code": "F32.9", "desc": "Major depressive disorder, single episode, unspecified"},
    {"code": "F10.20", "desc": "Alcohol dependence, uncomplicated"},
    {"code": "F10.10", "desc": "Alcohol abuse, uncomplicated"},
    # Metabolic / Obesity (8%)
    {"code": "E66.01", "desc": "Morbid (severe) obesity due to excess calories"},
    {"code": "E66.9", "desc": "Obesity, unspecified"},
    # Musculoskeletal (8%)
    {"code": "M54.5", "desc": "Low back pain"},
    {"code": "M54.2", "desc": "Cervicalgia"},
    {"code": "M25.50", "desc": "Pain in unspecified joint"},
    # Gastrointestinal (6%)
    {"code": "K21.0", "desc": "Gastro-esophageal reflux disease with esophagitis"},
    {"code": "K58.9", "desc": "Irritable bowel syndrome without diarrhea"},
    # Genitourinary (5%)
    {"code": "N39.0", "desc": "Urinary tract infection, site not specified"},
    # Dental (4%)
    {"code": "K02.9", "desc": "Dental caries, unspecified"},
    # Pregnancy-related (2%)
    {"code": "O24.11", "desc": "Pre-existing type 2 diabetes mellitus in pregnancy"},
]

ICD10_WEIGHTS = [
    # Diabetes (17%) - 5 codes
    0.07,
    0.04,
    0.03,
    0.02,
    0.01,
    # Respiratory (14%) - 3 codes
    0.07,
    0.04,
    0.03,
    # Cardiovascular (12%) - 3 codes
    0.06,
    0.04,
    0.02,
    # Behavioral Health (12%) - 4 codes
    0.04,
    0.03,
    0.03,
    0.02,
    # Metabolic / Obesity (10%) - 2 codes
    0.06,
    0.04,
    # Musculoskeletal (10%) - 3 codes
    0.05,
    0.03,
    0.02,
    # Gastrointestinal (8%) - 2 codes
    0.05,
    0.03,
    # Genitourinary (7%) - 1 code
    0.07,
    # Dental (6%) - 1 code
    0.06,
    # Pregnancy-related (4%) - 1 code
    0.04,
]  # sum = 1.00

# ---------------------------------------------------------------------------
# CPT codes for common procedures
# ---------------------------------------------------------------------------
CPT_CODES: list[dict[str, str]] = [
    {"code": "99213", "desc": "Office visit, established patient, low complexity"},
    {"code": "99214", "desc": "Office visit, established patient, moderate complexity"},
    {"code": "99215", "desc": "Office visit, established patient, high complexity"},
    {"code": "99203", "desc": "Office visit, new patient, low complexity"},
    {"code": "99281", "desc": "Emergency department visit, minor problem"},
    {"code": "99283", "desc": "Emergency department visit, moderate severity"},
    {"code": "99285", "desc": "Emergency department visit, high severity"},
    {"code": "99386", "desc": "Initial preventive medicine, 40-64 years"},
    {"code": "36415", "desc": "Collection of venous blood by venipuncture"},
    {"code": "80053", "desc": "Comprehensive metabolic panel"},
    {"code": "83036", "desc": "Hemoglobin A1c"},
    {"code": "80061", "desc": "Lipid panel"},
    {"code": "85025", "desc": "Complete blood count with differential"},
    {"code": "81001", "desc": "Urinalysis with microscopy"},
    {"code": "90837", "desc": "Psychotherapy, 60 minutes"},
    {"code": "D0120", "desc": "Periodic oral evaluation"},
    {"code": "D2391", "desc": "Resin-based composite, one surface, posterior"},
    {"code": "96372", "desc": "Therapeutic injection, subcutaneous or intramuscular"},
]

CPT_WEIGHTS = [
    0.15,
    0.12,
    0.05,
    0.06,
    0.05,
    0.06,
    0.03,
    0.04,
    0.08,
    0.06,
    0.06,
    0.04,
    0.05,
    0.03,
    0.04,
    0.04,
    0.02,
    0.02,
]

# ---------------------------------------------------------------------------
# Provider types and weights
# ---------------------------------------------------------------------------
PROVIDER_TYPES = [
    "physician",
    "nurse_practitioner",
    "physician_assistant",
    "dentist",
    "pharmacist",
    "psychologist",
    "social_worker",
    "community_health_rep",
]

PROVIDER_WEIGHTS = [0.30, 0.20, 0.12, 0.10, 0.10, 0.06, 0.05, 0.07]

# ---------------------------------------------------------------------------
# Medications (20 common prescriptions for prevalent conditions)
# ---------------------------------------------------------------------------
MEDICATIONS: list[dict[str, str]] = [
    {"name": "Metformin 500mg", "ndc": "00093-7214-01"},
    {"name": "Metformin 1000mg", "ndc": "00093-7267-01"},
    {"name": "Insulin Glargine", "ndc": "00088-2220-33"},
    {"name": "Glipizide 5mg", "ndc": "00093-0317-01"},
    {"name": "Lisinopril 10mg", "ndc": "00093-1044-01"},
    {"name": "Lisinopril 20mg", "ndc": "00093-1045-01"},
    {"name": "Amlodipine 5mg", "ndc": "00093-3170-01"},
    {"name": "Atorvastatin 20mg", "ndc": "00093-5058-01"},
    {"name": "Atorvastatin 40mg", "ndc": "00093-5059-01"},
    {"name": "Hydrochlorothiazide 25mg", "ndc": "00093-0314-01"},
    {"name": "Omeprazole 20mg", "ndc": "00093-5287-01"},
    {"name": "Ibuprofen 600mg", "ndc": "00093-0618-01"},
    {"name": "Amoxicillin 500mg", "ndc": "00093-4150-01"},
    {"name": "Azithromycin 250mg", "ndc": "00093-7169-01"},
    {"name": "Albuterol Inhaler", "ndc": "59310-0579-22"},
    {"name": "Fluoxetine 20mg", "ndc": "00093-0731-01"},
    {"name": "Sertraline 50mg", "ndc": "00093-7196-01"},
    {"name": "Gabapentin 300mg", "ndc": "00093-0215-01"},
    {"name": "Levothyroxine 50mcg", "ndc": "00378-1805-01"},
    {"name": "Prednisone 10mg", "ndc": "00093-0817-01"},
]

# ---------------------------------------------------------------------------
# Lab tests (common panels and individual tests)
# ---------------------------------------------------------------------------
LAB_TESTS: list[dict[str, Any]] = [
    {
        "name": "Hemoglobin A1c",
        "unit": "%",
        "low": 4.0,
        "high": 14.0,
        "normal_low": 4.0,
        "normal_high": 5.6,
    },
    {
        "name": "Fasting Glucose",
        "unit": "mg/dL",
        "low": 60,
        "high": 400,
        "normal_low": 70,
        "normal_high": 100,
    },
    {
        "name": "Total Cholesterol",
        "unit": "mg/dL",
        "low": 100,
        "high": 350,
        "normal_low": 100,
        "normal_high": 200,
    },
    {
        "name": "LDL Cholesterol",
        "unit": "mg/dL",
        "low": 40,
        "high": 250,
        "normal_low": 40,
        "normal_high": 100,
    },
    {
        "name": "HDL Cholesterol",
        "unit": "mg/dL",
        "low": 20,
        "high": 100,
        "normal_low": 40,
        "normal_high": 60,
    },
    {
        "name": "Triglycerides",
        "unit": "mg/dL",
        "low": 50,
        "high": 500,
        "normal_low": 50,
        "normal_high": 150,
    },
    {
        "name": "Serum Creatinine",
        "unit": "mg/dL",
        "low": 0.5,
        "high": 5.0,
        "normal_low": 0.7,
        "normal_high": 1.3,
    },
    {
        "name": "BUN",
        "unit": "mg/dL",
        "low": 5,
        "high": 60,
        "normal_low": 7,
        "normal_high": 20,
    },
    {
        "name": "WBC Count",
        "unit": "K/uL",
        "low": 2.0,
        "high": 20.0,
        "normal_low": 4.5,
        "normal_high": 11.0,
    },
    {
        "name": "Hemoglobin",
        "unit": "g/dL",
        "low": 7.0,
        "high": 18.0,
        "normal_low": 12.0,
        "normal_high": 17.5,
    },
    {
        "name": "ALT",
        "unit": "U/L",
        "low": 5,
        "high": 200,
        "normal_low": 7,
        "normal_high": 56,
    },
    {
        "name": "AST",
        "unit": "U/L",
        "low": 5,
        "high": 200,
        "normal_low": 10,
        "normal_high": 40,
    },
    {
        "name": "TSH",
        "unit": "mIU/L",
        "low": 0.1,
        "high": 15.0,
        "normal_low": 0.4,
        "normal_high": 4.0,
    },
    {
        "name": "Urinalysis pH",
        "unit": "pH",
        "low": 4.5,
        "high": 8.5,
        "normal_low": 4.5,
        "normal_high": 8.0,
    },
    {
        "name": "Blood Alcohol Level",
        "unit": "mg/dL",
        "low": 0.0,
        "high": 400.0,
        "normal_low": 0.0,
        "normal_high": 0.0,
    },
]

# ---------------------------------------------------------------------------
# Age group and gender distributions
# ---------------------------------------------------------------------------
AGE_GROUPS = ["0-4", "5-14", "15-24", "25-44", "45-64", "65+"]
AGE_GROUP_WEIGHTS = [0.08, 0.12, 0.15, 0.28, 0.24, 0.13]

GENDERS = ["M", "F", "X"]
GENDER_WEIGHTS = [0.47, 0.52, 0.01]

# ---------------------------------------------------------------------------
# Insurance types and weights
# ---------------------------------------------------------------------------
INSURANCE_TYPES = [
    "IHS_CONTRACT",
    "MEDICAID",
    "MEDICARE",
    "PRIVATE",
    "UNINSURED",
    "VA",
]

INSURANCE_WEIGHTS = [0.30, 0.28, 0.15, 0.10, 0.12, 0.05]


class TribalHealthcareGenerator(BaseGenerator):
    """
    Generate synthetic Indian Health Service (IHS) tribal healthcare
    encounter data.

    Records include clinical encounters across 20 IHS facilities spanning
    12 area offices, with diagnoses weighted toward Native American health
    disparities (diabetes 15%, respiratory 12%, cardiovascular 10%,
    behavioral health 10%).

    All generated records have ``hipaa_consent=True`` and ``phi_masked=True``
    to reflect HIPAA-compliant de-identified data.
    """

    def __init__(
        self,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Initialize the Tribal Healthcare generator.

        Args:
            seed: Random seed for reproducibility.
            start_date: Start date for encounter date generation.
            end_date: End date for encounter date generation.
        """
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)

        self._schema = {
            "record_id": "string",
            "patient_id": "string",
            "facility_id": "string",
            "facility_name": "string",
            "encounter_type": "string",
            "encounter_date": "datetime",
            "icd10_code": "string",
            "icd10_description": "string",
            "cpt_code": "string",
            "cpt_description": "string",
            "provider_id": "string",
            "provider_type": "string",
            "tribal_affiliation": "string",
            "service_unit": "string",
            "area_office": "string",
            "age_group": "string",
            "gender": "string",
            "insurance_type": "string",
            "medication_name": "string",
            "medication_ndc": "string",
            "lab_test_name": "string",
            "lab_result_value": "float",
            "lab_result_unit": "string",
            "lab_abnormal_flag": "string",
            "hipaa_consent": "boolean",
            "phi_masked": "boolean",
            "load_time": "datetime",
        }

    # ------------------------------------------------------------------
    # Abstract method implementation
    # ------------------------------------------------------------------

    def generate_record(self) -> dict[str, Any]:
        """
        Generate a single tribal healthcare encounter record.

        Returns:
            Dictionary with all encounter fields plus standard metadata.
        """
        # --- Encounter basics ---
        encounter_type = self.weighted_choice(ENCOUNTER_TYPES, ENCOUNTER_WEIGHTS)
        encounter_dt = self.random_datetime()

        # --- Facility selection ---
        facility = FACILITIES[int(self.rng.integers(0, len(FACILITIES)))]

        # --- Diagnosis ---
        icd10_idx = int(self.rng.choice(len(ICD10_CODES), p=ICD10_WEIGHTS))
        icd10 = ICD10_CODES[icd10_idx]

        # --- CPT code (present ~75% of the time) ---
        cpt_code: str | None = None
        cpt_description: str | None = None
        if self.rng.random() < 0.75:
            cpt_idx = int(self.rng.choice(len(CPT_CODES), p=CPT_WEIGHTS))
            cpt = CPT_CODES[cpt_idx]
            cpt_code = cpt["code"]
            cpt_description = cpt["desc"]

        # --- Provider ---
        provider_id: str | None = None
        provider_type: str | None = None
        if self.rng.random() < 0.85:
            npi_num = int(self.rng.uniform(1_000_000_000, 9_999_999_999))
            provider_id = f"{npi_num}"
            provider_type = self.weighted_choice(PROVIDER_TYPES, PROVIDER_WEIGHTS)

        # --- Patient demographics ---
        age_group = self.weighted_choice(AGE_GROUPS, AGE_GROUP_WEIGHTS)
        gender = self.weighted_choice(GENDERS, GENDER_WEIGHTS)
        tribal = self.weighted_choice(TRIBAL_AFFILIATIONS, TRIBAL_WEIGHTS)
        insurance = self.weighted_choice(INSURANCE_TYPES, INSURANCE_WEIGHTS)

        # Adjust insurance for age group (Medicare more likely for 65+)
        if age_group == "65+" and self.rng.random() < 0.60:
            insurance = "MEDICARE"
        elif age_group in ("0-4", "5-14") and self.rng.random() < 0.50:
            insurance = "MEDICAID"

        # --- Patient ID ---
        patient_hash = self.hash_value(
            f"{tribal}-{gender}-{age_group}-{self.rng.integers(0, 999999)}"
        )[:8].upper()
        patient_id = f"PAT-{patient_hash}"

        # --- Medication (present for pharmacy encounters and ~30% of others) ---
        medication_name: str | None = None
        medication_ndc: str | None = None
        if encounter_type == "pharmacy" or self.rng.random() < 0.30:
            med = MEDICATIONS[int(self.rng.integers(0, len(MEDICATIONS)))]
            medication_name = med["name"]
            medication_ndc = med["ndc"]

        # --- Lab results (present for laboratory encounters and ~20% of others) ---
        lab_test_name: str | None = None
        lab_result_value: float | None = None
        lab_result_unit: str | None = None
        lab_abnormal_flag: str | None = None
        if encounter_type == "laboratory" or self.rng.random() < 0.20:
            lab = LAB_TESTS[int(self.rng.integers(0, len(LAB_TESTS)))]
            lab_test_name = lab["name"]
            lab_result_value = round(
                float(self.rng.uniform(lab["low"], lab["high"])), 2
            )
            lab_result_unit = lab["unit"]

            # Determine abnormal flag based on normal ranges
            if lab_result_value < lab["normal_low"]:
                # Check if critically low (more than 20% below normal)
                if lab["normal_low"] > 0 and lab_result_value < lab["normal_low"] * 0.8:
                    lab_abnormal_flag = "LL"
                else:
                    lab_abnormal_flag = "L"
            elif lab_result_value > lab["normal_high"]:
                # Check if critically high (more than 20% above normal)
                if (
                    lab["normal_high"] > 0
                    and lab_result_value > lab["normal_high"] * 1.2
                ):
                    lab_abnormal_flag = "HH"
                else:
                    lab_abnormal_flag = "H"
            else:
                lab_abnormal_flag = "N"

        record: dict[str, Any] = {
            "record_id": self.generate_uuid(),
            "patient_id": patient_id,
            "facility_id": facility["id"],
            "facility_name": facility["name"],
            "encounter_type": encounter_type,
            "encounter_date": encounter_dt.isoformat(),
            "icd10_code": icd10["code"],
            "icd10_description": icd10["desc"],
            "cpt_code": cpt_code,
            "cpt_description": cpt_description,
            "provider_id": provider_id,
            "provider_type": provider_type,
            "tribal_affiliation": tribal,
            "service_unit": facility["service_unit"],
            "area_office": facility["area"],
            "age_group": age_group,
            "gender": gender,
            "insurance_type": insurance,
            "medication_name": medication_name,
            "medication_ndc": medication_ndc,
            "lab_test_name": lab_test_name,
            "lab_result_value": lab_result_value,
            "lab_result_unit": lab_result_unit,
            "lab_abnormal_flag": lab_abnormal_flag,
            "hipaa_consent": True,
            "phi_masked": True,
            "load_time": datetime.now().isoformat(),
        }

        return self.add_metadata_columns(record)

    # ------------------------------------------------------------------
    # Batch helper
    # ------------------------------------------------------------------

    def generate_batch(
        self,
        count: int = 1000,
    ) -> "pd.DataFrame":  # type: ignore[name-defined]  # noqa: F821
        """
        Generate a batch of tribal healthcare encounter records.

        Args:
            count: Number of records to generate (default 1000).

        Returns:
            :class:`pandas.DataFrame` containing ``count`` rows.
        """
        import pandas as pd  # local import keeps the class importable without pandas

        records = [self.generate_record() for _ in range(count)]
        return pd.DataFrame(records)
