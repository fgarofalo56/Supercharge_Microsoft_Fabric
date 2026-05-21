"""
Clinical Trial Data Generator
==============================

Generates synthetic clinical trial data for the Pharma & Life Sciences vertical:
- Subjects (enrollment, demographics, study arm assignments)
- Adverse Events (MedDRA-coded, severity, causality, outcomes)
- Visits (scheduled vs. actual, protocol deviations)

Compliance: 21 CFR Part 11, GxP, ICH E6(R2) GCP
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from data_generation.generators.base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PHASES = ["Phase I", "Phase II", "Phase III", "Phase IV"]
PHASE_WEIGHTS = [0.15, 0.25, 0.45, 0.15]

THERAPEUTIC_AREAS = [
    "Oncology",
    "Immunology",
    "Neuroscience",
    "Cardiovascular",
    "Rare Disease",
    "Metabolic",
    "Respiratory",
    "Infectious Disease",
]

SUBJECT_STATUSES = ["screened", "enrolled", "completed", "withdrawn"]
SUBJECT_STATUS_WEIGHTS = [0.12, 0.38, 0.30, 0.20]

ARMS = ["Treatment A", "Treatment B", "Placebo", "Active Comparator"]
ARM_WEIGHTS = [0.35, 0.25, 0.25, 0.15]

AE_SEVERITIES = ["Mild", "Moderate", "Severe"]
AE_SEVERITY_WEIGHTS = [0.55, 0.30, 0.15]

AE_CAUSALITIES = [
    "Not Related",
    "Unlikely",
    "Possible",
    "Probable",
    "Definite",
]
AE_CAUSALITY_WEIGHTS = [0.30, 0.20, 0.25, 0.18, 0.07]

AE_OUTCOMES = [
    "Recovered",
    "Recovering",
    "Not Recovered",
    "Recovered with Sequelae",
    "Fatal",
    "Unknown",
]
AE_OUTCOME_WEIGHTS = [0.45, 0.20, 0.12, 0.10, 0.03, 0.10]

# MedDRA Preferred Terms mapped to System Organ Class (SOC)
MEDDRA_PT_SOC: dict[str, str] = {
    "Headache": "Nervous system disorders",
    "Nausea": "Gastrointestinal disorders",
    "Fatigue": "General disorders and administration site conditions",
    "Diarrhoea": "Gastrointestinal disorders",
    "Arthralgia": "Musculoskeletal and connective tissue disorders",
    "Pyrexia": "General disorders and administration site conditions",
    "Cough": "Respiratory, thoracic and mediastinal disorders",
    "Rash": "Skin and subcutaneous tissue disorders",
    "Dizziness": "Nervous system disorders",
    "Vomiting": "Gastrointestinal disorders",
    "Back pain": "Musculoskeletal and connective tissue disorders",
    "Insomnia": "Psychiatric disorders",
    "Hypertension": "Vascular disorders",
    "Neutropenia": "Blood and lymphatic system disorders",
    "Anaemia": "Blood and lymphatic system disorders",
    "Dyspnoea": "Respiratory, thoracic and mediastinal disorders",
    "Pruritus": "Skin and subcutaneous tissue disorders",
    "Constipation": "Gastrointestinal disorders",
    "Alopecia": "Skin and subcutaneous tissue disorders",
    "Peripheral neuropathy": "Nervous system disorders",
}

MEDDRA_PTS = list(MEDDRA_PT_SOC.keys())

VISIT_TYPES = [
    "Screening",
    "Baseline",
    "Week 2",
    "Week 4",
    "Week 8",
    "Week 12",
    "Week 16",
    "Week 24",
    "Week 36",
    "Week 48",
    "End of Treatment",
    "Follow-up",
]

SITES = [f"SITE-{i:03d}" for i in range(1, 321)]


class TrialGenerator(BaseGenerator):
    """Generate synthetic clinical trial data.

    Supports three record domains via the ``domain`` parameter on
    ``generate_record``:

    - ``subject``  -- enrolled subject demographics and status
    - ``adverse_event`` -- adverse event records with MedDRA coding
    - ``visit`` -- scheduled and actual visit records

    Example::

        gen = TrialGenerator(seed=42)
        subjects = [gen.generate_record(domain="subject") for _ in range(100)]
        aes = [gen.generate_record(domain="adverse_event") for _ in range(200)]
        visits = [gen.generate_record(domain="visit") for _ in range(500)]
    """

    def __init__(
        self,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        num_studies: int = 45,
    ):
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)
        self.num_studies = num_studies

        # Pre-generate study metadata for consistency
        self._studies = self._generate_studies()
        # Track subject IDs for cross-referencing
        self._subject_counter = 0

        self._schema = {
            "subject_id": "string",
            "site_id": "string",
            "study_id": "string",
            "enrollment_dt": "datetime",
            "arm": "string",
            "status": "string",
            "phase": "string",
            "therapeutic_area": "string",
        }

    # ------------------------------------------------------------------
    # Study metadata
    # ------------------------------------------------------------------

    def _generate_studies(self) -> list[dict[str, Any]]:
        """Pre-generate study-level metadata."""
        studies = []
        for i in range(self.num_studies):
            phase = str(self.weighted_choice(PHASES, PHASE_WEIGHTS))
            ta = str(self.rng.choice(THERAPEUTIC_AREAS))
            planned_enrollment = int(self.rng.integers(50, 800))
            studies.append(
                {
                    "study_id": f"STUDY-{i + 1:04d}",
                    "phase": phase,
                    "therapeutic_area": ta,
                    "planned_enrollment": planned_enrollment,
                    "num_sites": int(self.rng.integers(5, 45)),
                }
            )
        return studies

    # ------------------------------------------------------------------
    # Domain generators
    # ------------------------------------------------------------------

    def generate_record(self, domain: str = "subject") -> dict[str, Any]:
        """Generate a single record for the specified domain.

        Args:
            domain: One of 'subject', 'adverse_event', 'visit'.

        Returns:
            Dictionary with domain-specific fields.

        Raises:
            ValueError: If domain is not recognized.
        """
        if domain == "subject":
            return self._generate_subject()
        elif domain == "adverse_event":
            return self._generate_adverse_event()
        elif domain == "visit":
            return self._generate_visit()
        else:
            raise ValueError(
                f"Unknown domain '{domain}'. "
                f"Expected one of: subject, adverse_event, visit"
            )

    def _generate_subject(self) -> dict[str, Any]:
        """Generate a subject enrollment record."""
        self._subject_counter += 1
        study = self.rng.choice(self._studies)
        site_idx = int(self.rng.integers(0, min(study["num_sites"], len(SITES))))

        enrollment_dt = self.random_datetime()
        status = str(self.weighted_choice(SUBJECT_STATUSES, SUBJECT_STATUS_WEIGHTS))
        arm = str(self.weighted_choice(ARMS, ARM_WEIGHTS))

        age = int(self.rng.integers(18, 86))
        sex = str(self.rng.choice(["Male", "Female"]))
        race = str(
            self.rng.choice(
                [
                    "White",
                    "Black or African American",
                    "Asian",
                    "American Indian or Alaska Native",
                    "Native Hawaiian or Other Pacific Islander",
                    "Multiple",
                    "Unknown",
                ]
            )
        )
        ethnicity = str(
            self.rng.choice(["Hispanic or Latino", "Not Hispanic or Latino", "Unknown"])
        )

        record: dict[str, Any] = {
            "subject_id": f"SUBJ-{self._subject_counter:06d}",
            "site_id": SITES[site_idx],
            "study_id": study["study_id"],
            "phase": study["phase"],
            "therapeutic_area": study["therapeutic_area"],
            "enrollment_dt": enrollment_dt.isoformat(),
            "arm": arm,
            "status": status,
            "age": age,
            "sex": sex,
            "race": race,
            "ethnicity": ethnicity,
        }
        return self.add_metadata_columns(record)

    def _generate_adverse_event(self) -> dict[str, Any]:
        """Generate an adverse event record with MedDRA coding."""
        study = self.rng.choice(self._studies)
        subject_num = int(self.rng.integers(1, max(2, self._subject_counter + 1)))

        pt = str(self.rng.choice(MEDDRA_PTS))
        soc = MEDDRA_PT_SOC[pt]
        severity = str(self.weighted_choice(AE_SEVERITIES, AE_SEVERITY_WEIGHTS))
        serious_flag = severity == "Severe" or bool(self.rng.random() < 0.08)
        causality = str(self.weighted_choice(AE_CAUSALITIES, AE_CAUSALITY_WEIGHTS))
        outcome = str(self.weighted_choice(AE_OUTCOMES, AE_OUTCOME_WEIGHTS))

        onset_dt = self.random_datetime()
        duration_days = int(self.rng.integers(1, 90))
        resolution_dt = onset_dt + timedelta(days=duration_days)
        if outcome in ("Not Recovered", "Fatal"):
            resolution_dt = None

        record: dict[str, Any] = {
            "ae_id": self.generate_uuid(),
            "subject_id": f"SUBJ-{subject_num:06d}",
            "study_id": study["study_id"],
            "ae_term": pt,
            "meddra_pt": pt,
            "meddra_soc": soc,
            "severity": severity,
            "serious_flag": serious_flag,
            "onset_dt": onset_dt.isoformat(),
            "resolution_dt": resolution_dt.isoformat() if resolution_dt else None,
            "causality": causality,
            "outcome": outcome,
            "action_taken": str(
                self.rng.choice(
                    [
                        "None",
                        "Dose Reduced",
                        "Drug Interrupted",
                        "Drug Withdrawn",
                        "Concomitant Medication",
                    ]
                )
            ),
        }
        return self.add_metadata_columns(record)

    def _generate_visit(self) -> dict[str, Any]:
        """Generate a visit record with protocol deviation flagging."""
        study = self.rng.choice(self._studies)
        subject_num = int(self.rng.integers(1, max(2, self._subject_counter + 1)))

        visit_type = str(self.rng.choice(VISIT_TYPES))
        scheduled_dt = self.random_datetime()

        # Simulate visit timing deviation: ~85% on-time, ~15% deviated
        deviation_days = int(self.rng.integers(-2, 3))  # -2 to +2 days normal
        if self.rng.random() < 0.15:
            deviation_days = int(self.rng.integers(-14, 15))  # wider deviation

        actual_dt = scheduled_dt + timedelta(days=deviation_days)
        protocol_deviation_flag = abs(deviation_days) > 3

        # Vital signs (if applicable)
        systolic_bp = (
            int(self.rng.integers(90, 180)) if self.rng.random() < 0.7 else None
        )
        diastolic_bp = int(self.rng.integers(55, 110)) if systolic_bp else None
        heart_rate = (
            int(self.rng.integers(50, 110)) if self.rng.random() < 0.7 else None
        )
        weight_kg = (
            round(float(self.rng.uniform(45.0, 140.0)), 1)
            if self.rng.random() < 0.5
            else None
        )

        record: dict[str, Any] = {
            "visit_id": self.generate_uuid(),
            "subject_id": f"SUBJ-{subject_num:06d}",
            "study_id": study["study_id"],
            "visit_type": visit_type,
            "scheduled_dt": scheduled_dt.isoformat(),
            "actual_dt": actual_dt.isoformat(),
            "deviation_days": deviation_days,
            "protocol_deviation_flag": protocol_deviation_flag,
            "systolic_bp": systolic_bp,
            "diastolic_bp": diastolic_bp,
            "heart_rate": heart_rate,
            "weight_kg": weight_kg,
        }
        return self.add_metadata_columns(record)
