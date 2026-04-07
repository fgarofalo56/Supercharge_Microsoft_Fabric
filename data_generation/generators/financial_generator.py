"""
Financial Generator
===================

Generates synthetic cage and financial transaction data including:
- Cash transactions
- Chip exchanges
- Wire transfers
- Check cashing
- Front money deposits/withdrawals
"""

from datetime import datetime, timedelta
from typing import Any

from .base_generator import BaseGenerator
from .compliance_generator import get_threshold

# Load CTR threshold from shared config
_CTR_THRESHOLD = get_threshold("ctr", "threshold", 10000)


class FinancialGenerator(BaseGenerator):
    """Generate cage and financial transaction data."""

    TRANSACTION_TYPES = [
        "CASH_IN",
        "CASH_OUT",
        "CHIP_PURCHASE",
        "CHIP_REDEMPTION",
        "WIRE_TRANSFER_IN",
        "WIRE_TRANSFER_OUT",
        "CHECK_CASHING",
        "MARKER_ISSUE",
        "MARKER_PAYMENT",
        "FRONT_MONEY_DEPOSIT",
        "FRONT_MONEY_WITHDRAWAL",
        "JACKPOT_PAYOUT",
        "SAFEKEEPING_DEPOSIT",
        "SAFEKEEPING_WITHDRAWAL",
    ]

    TRANSACTION_WEIGHTS = [
        0.20,  # CASH_IN
        0.18,  # CASH_OUT
        0.15,  # CHIP_PURCHASE
        0.12,  # CHIP_REDEMPTION
        0.03,  # WIRE_TRANSFER_IN
        0.02,  # WIRE_TRANSFER_OUT
        0.08,  # CHECK_CASHING
        0.05,  # MARKER_ISSUE
        0.05,  # MARKER_PAYMENT
        0.04,  # FRONT_MONEY_DEPOSIT
        0.03,  # FRONT_MONEY_WITHDRAWAL
        0.03,  # JACKPOT_PAYOUT
        0.01,  # SAFEKEEPING_DEPOSIT
        0.01,  # SAFEKEEPING_WITHDRAWAL
    ]

    PAYMENT_METHODS = ["Cash", "Check", "Wire", "Chip", "TITO", "Marker"]
    CAGE_WINDOWS = [
        "Main Cage",
        "High Limit",
        "VIP",
        "Poker Cage",
        "Satellite 1",
        "Satellite 2",
    ]

    def __init__(
        self,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Initialize financial generator.

        Args:
            seed: Random seed for reproducibility
            start_date: Start date for generated data
            end_date: End date for generated data
        """
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)

        self._schema = {
            "transaction_id": "string",
            "transaction_type": "string",
            "transaction_timestamp": "datetime",
            "cage_location": "string",
            "cashier_id": "string",
            "supervisor_id": "string",
            "player_id": "string",
            "amount": "float",
            "currency": "string",
            "payment_method": "string",
            "check_number": "string",
            "wire_reference": "string",
            "marker_number": "string",
            "id_type": "string",
            "id_number_hash": "string",
            "ctr_required": "bool",
            "ctr_filed": "bool",
            "ctr_reference": "string",
            "suspicious_activity_flag": "bool",
            "notes": "string",
            "shift": "string",
            "business_date": "date",
        }

    def _get_shift(self, timestamp: datetime) -> str:
        """Determine shift based on time."""
        hour = timestamp.hour
        if 6 <= hour < 14:
            return "Day"
        elif 14 <= hour < 22:
            return "Swing"
        else:
            return "Grave"

    def _get_business_date(self, timestamp: datetime) -> str:
        """Get gaming day business date (ends at 6 AM)."""
        if timestamp.hour < 6:
            return (timestamp - timedelta(days=1)).strftime("%Y-%m-%d")
        return timestamp.strftime("%Y-%m-%d")

    def generate_record(self) -> dict[str, Any]:
        """Generate a single financial transaction."""
        txn_type = self.weighted_choice(
            self.TRANSACTION_TYPES, self.TRANSACTION_WEIGHTS
        )
        timestamp = self.random_datetime()

        # Generate amount based on transaction type
        amount = self._get_amount_for_type(txn_type)

        # Determine if CTR required (threshold from config)
        ctr_required = bool(amount >= _CTR_THRESHOLD)

        record = {
            "transaction_id": f"TXN-{self.generate_uuid()[:12]}",
            "transaction_type": txn_type,
            "transaction_timestamp": timestamp,
            "cage_location": self._get_cage_location(txn_type, amount),
            "cashier_id": f"CSH-{self.rng.integers(1, 100):03d}",
            "supervisor_id": (
                f"SUP-{self.rng.integers(1, 20):03d}"
                if amount >= 5000 or txn_type in ["MARKER_ISSUE", "CHECK_CASHING"]
                else None
            ),
            "player_id": f"PLY-{self.rng.integers(1, 10000):06d}",
            "amount": amount,
            "currency": "USD",
            "payment_method": self._get_payment_method(txn_type),
            "ctr_required": ctr_required,
            "ctr_filed": bool(ctr_required and self.rng.random() > 0.02),  # 98% compliance
            "ctr_reference": (
                f"CTR-{self.rng.integers(1000000, 9999999)}" if ctr_required else None
            ),
            "suspicious_activity_flag": self._check_suspicious(txn_type, amount),
            "shift": self._get_shift(timestamp),
            "business_date": self._get_business_date(timestamp),
        }

        # Add type-specific fields
        record = self._add_type_specific_fields(record, txn_type)

        # Add nullable defaults
        record.setdefault("check_number", None)
        record.setdefault("wire_reference", None)
        record.setdefault("marker_number", None)
        record.setdefault("id_type", None)
        record.setdefault("id_number_hash", None)
        record.setdefault("notes", None)

        return self.add_metadata_columns(record)

    def _get_amount_for_type(self, txn_type: str) -> float:
        """Generate appropriate amount for transaction type."""
        if txn_type in ["WIRE_TRANSFER_IN", "WIRE_TRANSFER_OUT"]:
            return round(self.rng.uniform(5000, 500000), 2)
        elif txn_type in ["MARKER_ISSUE", "MARKER_PAYMENT"]:
            return round(self.rng.choice([5000, 10000, 25000, 50000, 100000]), 0)
        elif txn_type in ["FRONT_MONEY_DEPOSIT", "FRONT_MONEY_WITHDRAWAL"]:
            return round(self.rng.uniform(1000, 100000), 2)
        elif txn_type == "JACKPOT_PAYOUT":
            return round(self.rng.uniform(1200, 100000), 2)
        elif txn_type == "CHECK_CASHING":
            return round(self.rng.uniform(100, 10000), 2)
        else:
            # Most cash transactions are smaller
            return round(
                self.rng.choice(
                    [100, 200, 300, 500, 1000, 2000, 5000, 10000, 25000],
                    p=[0.25, 0.20, 0.15, 0.15, 0.10, 0.07, 0.04, 0.03, 0.01],
                ),
                0,
            )

    def _get_cage_location(self, txn_type: str, amount: float) -> str:
        """Determine cage location based on transaction."""
        if amount >= _CTR_THRESHOLD or txn_type in ["MARKER_ISSUE", "WIRE_TRANSFER_IN"]:
            return self.rng.choice(["High Limit", "VIP"])
        elif txn_type == "JACKPOT_PAYOUT":
            return "Main Cage"
        else:
            return self.rng.choice(self.CAGE_WINDOWS)

    def _get_payment_method(self, txn_type: str) -> str:
        """Determine payment method for transaction type."""
        method_map = {
            "CASH_IN": "Cash",
            "CASH_OUT": "Cash",
            "CHIP_PURCHASE": "Cash",
            "CHIP_REDEMPTION": "Chip",
            "WIRE_TRANSFER_IN": "Wire",
            "WIRE_TRANSFER_OUT": "Wire",
            "CHECK_CASHING": "Check",
            "MARKER_ISSUE": "Marker",
            "MARKER_PAYMENT": self.rng.choice(["Cash", "Check", "Wire"]),
            "FRONT_MONEY_DEPOSIT": self.rng.choice(["Cash", "Check", "Wire"]),
            "FRONT_MONEY_WITHDRAWAL": self.rng.choice(["Cash", "Check"]),
            "JACKPOT_PAYOUT": self.rng.choice(["Cash", "Check"]),
            "SAFEKEEPING_DEPOSIT": self.rng.choice(["Cash", "Chip"]),
            "SAFEKEEPING_WITHDRAWAL": self.rng.choice(["Cash", "Chip"]),
        }
        return method_map.get(txn_type, "Cash")

    def _check_suspicious(self, txn_type: str, amount: float) -> bool:
        """Flag potentially suspicious transactions for SAR review."""
        # Structuring pattern: multiple transactions just under CTR threshold
        _sar_lower = get_threshold("sar", "structuring_lower", 8000)
        if _sar_lower <= amount < _CTR_THRESHOLD:
            return self.rng.random() < 0.1  # 10% flagged for review

        # Unusual transaction patterns
        if txn_type in ["WIRE_TRANSFER_IN", "WIRE_TRANSFER_OUT"] and amount > 50000:
            return self.rng.random() < 0.05

        return self.rng.random() < 0.005  # 0.5% baseline

    def _add_type_specific_fields(
        self, record: dict[str, Any], txn_type: str
    ) -> dict[str, Any]:
        """Add fields specific to transaction type."""
        if txn_type == "CHECK_CASHING":
            record["check_number"] = f"CHK{self.rng.integers(1000, 9999)}"
            record["id_type"] = self.rng.choice(
                ["Drivers License", "Passport", "State ID"]
            )
            record["id_number_hash"] = self.hash_value(
                f"ID-{self.rng.integers(100000000, 999999999)}"
            )

        elif txn_type in ["WIRE_TRANSFER_IN", "WIRE_TRANSFER_OUT"]:
            record["wire_reference"] = (
                f"WIRE-{self.rng.integers(100000000, 999999999)}{self.rng.integers(0, 9)}"
            )

        elif txn_type in ["MARKER_ISSUE", "MARKER_PAYMENT"]:
            record["marker_number"] = f"MKR-{self.rng.integers(100000, 999999)}"

        # Require ID for large transactions
        if record["amount"] >= 3000 and not record.get("id_type"):
            record["id_type"] = self.rng.choice(
                ["Drivers License", "Passport", "State ID"]
            )
            record["id_number_hash"] = self.hash_value(
                f"ID-{self.rng.integers(100000000, 999999999)}"
            )

        return record
