"""
Hospital Operations Generator
==============================

Generates synthetic hospital operations data for the Healthcare vertical:
- Patient admissions (encounters with DRG, payer, LOS, readmission tracking)
- Claims (CPT/ICD-10 coded, billed/allowed/paid amounts, denial reasons)
- Staffing records (unit-level nurse staffing with acuity scores)

All data is HIPAA-safe:
- MRNs are HMAC-SHA-256 hashed (requires FABRIC_POC_HASH_SALT)
- SSNs use 900-series synthetic range (never real)
- No real PHI is generated
"""

from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

from data_generation.generators.base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# Reference code lists (top-25 MS-DRG, common ICD-10, CPT)
# ---------------------------------------------------------------------------

TOP_25_DRG = [
    "470",  # Major hip/knee joint replacement
    "871",  # Septicemia w/o MV >96h w MCC
    "872",  # Septicemia w/o MV >96h w/o MCC
    "291",  # Heart failure & shock w MCC
    "292",  # Heart failure & shock w CC
    "193",  # Pneumonia w MCC
    "194",  # Pneumonia w CC
    "690",  # Kidney & urinary tract infections w/o MCC
    "689",  # Kidney & urinary tract infections w MCC
    "392",  # Esophagitis/gastro w/o MCC
    "065",  # Intracranial hemorrhage w MCC
    "378",  # GI hemorrhage w CC
    "683",  # Renal failure w CC
    "682",  # Renal failure w MCC
    "190",  # COPD w MCC
    "191",  # COPD w CC
    "247",  # Perc cardiovascular proc w drug-eluting stent w MCC
    "603",  # Cellulitis w/o MCC
    "287",  # Circulatory disorders w/o MCC
    "312",  # Syncope & collapse
    "641",  # Misc disorders of nutrition/metabolism w/o MCC
    "189",  # Pulmonary edema & respiratory failure
    "638",  # Diabetes w CC
    "069",  # Transient ischemia w/o MCC
    "948",  # Signs & symptoms w/o MCC
]

COMMON_ICD10 = [
    "A41.9", "I50.9", "J18.9", "J44.1", "N39.0", "E11.9", "I21.9",
    "K92.2", "N17.9", "J96.01", "I63.9", "R55", "L03.116", "E87.1",
    "K21.0", "J15.9", "I10", "E11.65", "I48.91", "R06.02",
]

COMMON_CPT = [
    "99213", "99214", "99223", "99232", "99233", "99238", "99291",
    "36415", "71046", "74177", "93000", "93306", "85025", "80053",
    "43239", "27447", "33533", "47562", "49505", "99285",
]

PAYER_MIX = ["Medicare", "Medicaid", "Commercial", "Self-Pay", "Tricare"]
PAYER_WEIGHTS = [0.35, 0.20, 0.30, 0.10, 0.05]

DENIAL_REASONS = [
    None, None, None, None, None, None, None,  # ~70% no denial
    "CO-4",   # Procedure code inconsistent with modifier
    "CO-16",  # Lack of information
    "CO-29",  # Time limit for filing has expired
    "CO-50",  # Non-covered service
    "PR-1",   # Deductible amount
    "CO-97",  # Benefit included in payment of another service
]

UNITS = ["ICU", "MICU", "SICU", "PCU", "MedSurg", "Telemetry", "ED", "L&D", "NICU", "Ortho"]
SHIFTS = ["Day", "Evening", "Night"]

DISPOSITIONS = [
    "Home", "Home Health", "SNF", "Rehab", "LTAC",
    "Transfer", "AMA", "Expired",
]
DISPOSITION_WEIGHTS = [0.45, 0.15, 0.12, 0.08, 0.05, 0.05, 0.03, 0.07]


class HospitalOperationsGenerator(BaseGenerator):
    """Generate synthetic hospital operations data (HIPAA-safe)."""

    def __init__(
        self,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)
        self._encounter_seq = 0
        self._claim_seq = 0
        self._schema = {
            "encounter_id": "string",
            "mrn_hash": "string",
            "admit_dt": "datetime",
            "discharge_dt": "datetime",
            "los": "int",
            "drg_code": "string",
            "payer": "string",
            "readmit_flag": "int",
            "ed_arrival_dt": "datetime",
            "disposition": "string",
        }

    # ------------------------------------------------------------------
    # Core record generator (admissions)
    # ------------------------------------------------------------------

    def generate_record(self) -> dict[str, Any]:
        """Generate a single patient admission record."""
        return self.generate_admission()

    def generate_admission(self) -> dict[str, Any]:
        """Generate a HIPAA-safe patient admission encounter."""
        self._encounter_seq += 1
        encounter_id = f"ENC-{self._encounter_seq:08d}"

        # Synthetic MRN (hashed for HIPAA)
        raw_mrn = f"MRN-{int(self.rng.integers(100000, 999999)):06d}"
        mrn_hash = self.hash_value(raw_mrn)

        # Synthetic SSN (900-series, never stored — only used if needed downstream)
        ssn = self.synthetic_ssn()

        # Admission timeline
        admit_dt = self.random_datetime()
        los = int(self.rng.exponential(scale=4.5)) + 1  # avg ~4.5 days
        los = min(los, 60)  # cap at 60 days
        discharge_dt = admit_dt + timedelta(days=los)

        # ED arrival (70% come through ED)
        ed_arrival_dt = None
        if self.rng.random() < 0.70:
            ed_wait_minutes = int(self.rng.integers(15, 360))
            ed_arrival_dt = admit_dt - timedelta(minutes=ed_wait_minutes)

        # Clinical
        drg_code = str(self.rng.choice(TOP_25_DRG))
        payer = str(self.weighted_choice(PAYER_MIX, PAYER_WEIGHTS))
        disposition = str(self.weighted_choice(DISPOSITIONS, DISPOSITION_WEIGHTS))

        # Readmission flag (15% readmission rate)
        readmit_flag = int(self.rng.random() < 0.15)

        record = {
            "encounter_id": encounter_id,
            "mrn_hash": mrn_hash,
            "ssn_masked": self.mask_ssn(ssn),
            "admit_dt": admit_dt.isoformat(),
            "discharge_dt": discharge_dt.isoformat(),
            "los": los,
            "drg_code": drg_code,
            "payer": payer,
            "readmit_flag": readmit_flag,
            "ed_arrival_dt": ed_arrival_dt.isoformat() if ed_arrival_dt else None,
            "disposition": disposition,
            "age": int(self.rng.integers(18, 95)),
            "gender": str(self.rng.choice(["M", "F", "X"])),
        }
        return self.add_metadata_columns(record)

    # ------------------------------------------------------------------
    # Claims generator
    # ------------------------------------------------------------------

    def generate_claim(self) -> dict[str, Any]:
        """Generate a single medical claim record."""
        self._claim_seq += 1
        claim_id = f"CLM-{self._claim_seq:010d}"
        encounter_id = f"ENC-{int(self.rng.integers(1, max(self._encounter_seq, 1) + 1)):08d}"

        cpt = str(self.rng.choice(COMMON_CPT))
        icd10 = str(self.rng.choice(COMMON_ICD10))
        billed_amt = round(float(self.rng.uniform(150, 25000)), 2)

        # Allowed is typically 40-80% of billed
        allowed_pct = float(self.rng.uniform(0.40, 0.80))
        allowed_amt = round(billed_amt * allowed_pct, 2)

        # Paid is 80-100% of allowed (unless denied)
        denial_reason = self.rng.choice(DENIAL_REASONS)
        if denial_reason is not None:
            denial_reason = str(denial_reason)
            paid_amt = 0.0
        else:
            paid_pct = float(self.rng.uniform(0.80, 1.00))
            paid_amt = round(allowed_amt * paid_pct, 2)

        return {
            "claim_id": claim_id,
            "encounter_id": encounter_id,
            "cpt_code": cpt,
            "icd10_code": icd10,
            "billed_amt": billed_amt,
            "allowed_amt": allowed_amt,
            "paid_amt": paid_amt,
            "denial_reason_code": denial_reason,
            "service_dt": self.random_datetime().isoformat(),
            "_ingested_at": datetime.now().isoformat(),
            "_source": self.__class__.__name__,
        }

    # ------------------------------------------------------------------
    # Staffing generator
    # ------------------------------------------------------------------

    def generate_staffing(self) -> dict[str, Any]:
        """Generate a unit-level staffing record."""
        unit = str(self.rng.choice(UNITS))
        shift = str(self.rng.choice(SHIFTS))

        # ICU has fewer patients, higher acuity
        if unit in ("ICU", "MICU", "SICU", "NICU"):
            patient_count = int(self.rng.integers(4, 16))
            rn_count = int(self.rng.integers(3, 10))
            acuity_score = round(float(self.rng.uniform(3.0, 5.0)), 2)
        else:
            patient_count = int(self.rng.integers(10, 40))
            rn_count = int(self.rng.integers(3, 12))
            acuity_score = round(float(self.rng.uniform(1.0, 3.5)), 2)

        return {
            "staffing_id": self.generate_uuid(),
            "unit": unit,
            "shift": shift,
            "shift_date": self.random_datetime().strftime("%Y-%m-%d"),
            "rn_count": rn_count,
            "patient_count": patient_count,
            "ratio": round(patient_count / max(rn_count, 1), 2),
            "acuity_score": acuity_score,
            "_ingested_at": datetime.now().isoformat(),
            "_source": self.__class__.__name__,
        }

    # ------------------------------------------------------------------
    # Batch helpers
    # ------------------------------------------------------------------

    def generate_admissions(self, num_records: int) -> pd.DataFrame:
        """Generate a DataFrame of admission records."""
        return pd.DataFrame([self.generate_admission() for _ in range(num_records)])

    def generate_claims(self, num_records: int) -> pd.DataFrame:
        """Generate a DataFrame of claim records."""
        return pd.DataFrame([self.generate_claim() for _ in range(num_records)])

    def generate_staffing_records(self, num_records: int) -> pd.DataFrame:
        """Generate a DataFrame of staffing records."""
        return pd.DataFrame([self.generate_staffing() for _ in range(num_records)])


if __name__ == "__main__":
    import os
    os.environ.setdefault("FABRIC_POC_HASH_SALT", "demo-salt-do-not-use-in-prod")

    gen = HospitalOperationsGenerator(seed=42)
    print("=== Admissions (5 rows) ===")
    print(gen.generate_admissions(5).to_string(index=False))
    print("\n=== Claims (5 rows) ===")
    print(gen.generate_claims(5).to_string(index=False))
    print("\n=== Staffing (5 rows) ===")
    print(gen.generate_staffing_records(5).to_string(index=False))
