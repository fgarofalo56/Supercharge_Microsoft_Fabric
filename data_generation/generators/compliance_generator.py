"""
Compliance Generator
====================

Generates synthetic compliance and regulatory data including:
- CTR (Currency Transaction Reports) - $10,000+ threshold
- SAR (Suspicious Activity Reports)
- W-2G (Gambling Winnings) - $1,200+ for slots, $600+ for keno/bingo
- Title 31 compliance records
"""

from datetime import datetime, timedelta
from typing import Any

from .base_generator import BaseGenerator


class ComplianceGenerator(BaseGenerator):
    """Generate compliance and regulatory filing data."""

    # filing_type enum values per schema (CTR, SAR, W2G only)
    FILING_TYPES = ["CTR", "SAR", "W2G"]

    # W-2G thresholds by game type
    W2G_THRESHOLDS = {
        "Slots": 1200,
        "Video Poker": 1200,
        "Keno": 1500,
        "Bingo": 1200,
        "Poker Tournament": 5000,
        "Table Games": 600,  # At 300:1 odds or greater
    }

    SAR_CATEGORIES = [
        "Structuring",
        "Unusual Transaction Pattern",
        "Third Party Activity",
        "Identity Concerns",
        "Employee Involvement",
        "Counterfeit Currency",
        "Wire Transfer Anomaly",
        "Chip Walking",
        "Credit Abuse",
        "Other Suspicious Activity",
    ]

    FILING_STATUS = ["Draft", "Pending Review", "Filed", "Rejected", "Amended"]

    def __init__(
        self,
        seed: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Initialize compliance generator.

        Args:
            seed: Random seed for reproducibility
            start_date: Start date for generated data
            end_date: End date for generated data
        """
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)

        self._schema = {
            "filing_id": "string",
            "filing_type": "string",
            "filing_timestamp": "datetime",
            "filing_date": "date",
            "due_date": "date",
            "status": "string",
            "player_id": "string",
            "player_name_hash": "string",
            "ssn_hash": "string",
            "ssn_masked": "string",
            "date_of_birth": "date",
            "address_hash": "string",
            "id_type": "string",
            "id_number_hash": "string",
            "transaction_date": "date",
            "transaction_amount": "float",
            "cash_in_amount": "float",
            "cash_out_amount": "float",
            "game_type": "string",
            "machine_id": "string",
            "table_id": "string",
            "jackpot_amount": "float",
            "withholding_amount": "float",
            "withholding_rate": "float",
            "sar_category": "string",
            "sar_narrative": "string",
            "suspicious_activity_date": "date",
            "fincen_reference": "string",
            "irs_reference": "string",
            "compliance_officer_id": "string",
            "review_notes": "string",
            "amended_from": "string",
            "property_code": "string",
        }

    def generate_record(self) -> dict[str, Any]:
        """Generate a single compliance record."""
        # Weight toward CTR and W2G (most common filings)
        # Use FILING_TYPES to match schema enum: CTR, SAR, W2G
        filing_type = self.weighted_choice(
            self.FILING_TYPES,
            [0.40, 0.15, 0.45],  # Adjusted weights for 3 types
        )

        timestamp = self.random_datetime()
        filing_id = f"{filing_type}-{timestamp.strftime('%Y%m%d')}-{self.rng.integers(10000, 99999)}"

        record = {
            "filing_id": filing_id,
            "filing_type": filing_type,
            "filing_timestamp": timestamp,
            "amount": 0,  # Set by type-specific methods below
            "player_id": f"PLY-{self.rng.integers(1, 10000):06d}",
            "compliance_officer_id": f"CO-{self.rng.integers(1, 10):02d}",
            "property_code": f"PROP-{self.rng.integers(1, 5):02d}",
        }

        # Generate player info (hashed/masked for compliance)
        record = self._add_player_info(record)

        # Generate type-specific data
        if filing_type == "CTR":
            record = self._generate_ctr(record, timestamp)
        elif filing_type == "SAR":
            record = self._generate_sar(record, timestamp)
        elif filing_type == "W2G":
            record = self._generate_w2g(record, timestamp)

        # Add nullable defaults
        for field in [
            "game_type",
            "machine_id",
            "table_id",
            "jackpot_amount",
            "withholding_amount",
            "withholding_rate",
            "sar_category",
            "sar_narrative",
            "suspicious_activity_date",
            "fincen_reference",
            "irs_reference",
            "review_notes",
            "amended_from",
            "cash_in_amount",
            "cash_out_amount",
        ]:
            record.setdefault(field, None)

        return self.add_metadata_columns(record)

    def _add_player_info(self, record: dict[str, Any]) -> dict[str, Any]:
        """Add hashed/masked player information."""
        name = f"{self.faker.first_name()} {self.faker.last_name()}"
        ssn = self.faker.ssn()
        address = self.faker.address().replace("\n", ", ")

        record["player_name_hash"] = self.hash_value(name)
        record["ssn_hash"] = self.hash_value(ssn)
        record["ssn_masked"] = self.mask_ssn(ssn)
        record["date_of_birth"] = self.faker.date_of_birth(
            minimum_age=21, maximum_age=85
        ).isoformat()
        record["address_hash"] = self.hash_value(address)
        record["id_type"] = self.rng.choice(
            ["Drivers License", "Passport", "State ID", "Military ID"]
        )
        record["id_number_hash"] = self.hash_value(
            f"ID-{self.rng.integers(100000000, 999999999)}"
        )

        return record

    def _generate_ctr(
        self, record: dict[str, Any], timestamp: datetime
    ) -> dict[str, Any]:
        """Generate Currency Transaction Report data."""
        # CTR required for cash transactions >= $10,000
        total_amount = round(self.rng.uniform(10000, 100000), 2)

        # Split between cash in and cash out
        cash_in = round(total_amount * self.rng.uniform(0, 1), 2)
        cash_out = round(total_amount - cash_in, 2)

        record["transaction_date"] = timestamp.strftime("%Y-%m-%d")
        record["transaction_amount"] = total_amount
        record["amount"] = total_amount  # Schema field
        record["cash_in_amount"] = cash_in
        record["cash_out_amount"] = cash_out

        # CTR must be filed within 15 days
        record["filing_date"] = (
            timestamp + timedelta(days=int(self.rng.integers(1, 15)))
        ).strftime("%Y-%m-%d")
        record["due_date"] = (timestamp + timedelta(days=15)).strftime("%Y-%m-%d")

        record["status"] = self.weighted_choice(
            self.FILING_STATUS,
            [0.05, 0.10, 0.80, 0.03, 0.02],
        )

        if record["status"] == "Filed":
            record["fincen_reference"] = (
                f"FINCEN-CTR-{self.rng.integers(100000000, 999999999)}"
            )

        return record

    def _generate_sar(
        self, record: dict[str, Any], timestamp: datetime
    ) -> dict[str, Any]:
        """Generate Suspicious Activity Report data."""
        record["transaction_date"] = timestamp.strftime("%Y-%m-%d")
        record["suspicious_activity_date"] = timestamp.strftime("%Y-%m-%d")

        # SAR amount can vary widely
        sar_amount = round(
            self.rng.choice(
                [5000, 9000, 9500, 9900, 15000, 25000, 50000],
                p=[0.15, 0.25, 0.20, 0.15, 0.10, 0.10, 0.05],
            ),
            2,
        )
        record["transaction_amount"] = sar_amount
        record["amount"] = sar_amount  # Schema field

        record["sar_category"] = self.rng.choice(self.SAR_CATEGORIES)
        record["sar_narrative"] = self._generate_sar_narrative(record["sar_category"])

        # SAR must be filed within 30 days
        record["filing_date"] = (
            timestamp + timedelta(days=int(self.rng.integers(1, 30)))
        ).strftime("%Y-%m-%d")
        record["due_date"] = (timestamp + timedelta(days=30)).strftime("%Y-%m-%d")

        record["status"] = self.weighted_choice(
            ["Draft", "Pending Review", "Filed"],
            [0.15, 0.25, 0.60],
        )

        if record["status"] == "Filed":
            record["fincen_reference"] = (
                f"FINCEN-SAR-{self.rng.integers(100000000, 999999999)}"
            )

        return record

    def _generate_sar_narrative(self, category: str) -> str:
        """Generate SAR narrative text based on category."""
        narratives = {
            "Structuring": "Subject conducted multiple cash transactions just below $10,000 reporting threshold within a 24-hour period.",
            "Unusual Transaction Pattern": "Subject exhibited unusual betting patterns inconsistent with documented income level.",
            "Third Party Activity": "Observed third party providing chips/cash to subject for gaming purposes.",
            "Identity Concerns": "Subject presented identification documents with inconsistent information.",
            "Employee Involvement": "Employee observed conducting transactions outside normal job duties.",
            "Counterfeit Currency": "Counterfeit currency detected during transaction processing.",
            "Wire Transfer Anomaly": "Wire transfer originated from high-risk jurisdiction without clear business purpose.",
            "Chip Walking": "Subject observed transporting significant chip value between gaming areas.",
            "Credit Abuse": "Subject exhibited pattern of marker draws followed by minimal play.",
            "Other Suspicious Activity": "Activity observed that warrants further review and documentation.",
        }
        return narratives.get(
            category, "Suspicious activity detected requiring review."
        )

    def _generate_w2g(
        self, record: dict[str, Any], timestamp: datetime
    ) -> dict[str, Any]:
        """Generate W-2G Gambling Winnings form data."""
        # Select game type and calculate winnings above threshold
        game_type = self.rng.choice(list(self.W2G_THRESHOLDS.keys()))
        threshold = self.W2G_THRESHOLDS[game_type]

        # Generate winning amount above threshold
        jackpot_amount = round(threshold * self.rng.uniform(1.0, 100.0), 2)

        record["game_type"] = game_type
        record["transaction_date"] = timestamp.strftime("%Y-%m-%d")
        record["jackpot_amount"] = jackpot_amount
        record["transaction_amount"] = jackpot_amount
        record["amount"] = jackpot_amount  # Schema field

        # Add machine or table ID
        if game_type in ["Slots", "Video Poker"]:
            record["machine_id"] = f"SM-{self.rng.integers(1, 500):05d}"
        else:
            record["table_id"] = f"TBL-{self.rng.integers(1, 100):04d}"

        # Calculate withholding (24% federal, 6% state typical)
        # Backup withholding required if no SSN provided
        federal_rate = 0.24
        state_rate = 0.06
        total_rate = federal_rate + state_rate

        if jackpot_amount >= 5000:  # Withholding required
            record["withholding_rate"] = total_rate
            record["withholding_amount"] = round(jackpot_amount * total_rate, 2)
        else:
            record["withholding_rate"] = 0
            record["withholding_amount"] = 0

        # W-2G issued immediately
        record["filing_date"] = timestamp.strftime("%Y-%m-%d")
        record["due_date"] = f"{timestamp.year + 1}-01-31"  # Due by Jan 31 next year

        record["status"] = "Filed"
        record["irs_reference"] = (
            f"W2G-{timestamp.strftime('%Y')}-{self.rng.integers(100000, 999999)}"
        )

        return record

    def generate_structuring_pattern(
        self, player_id: str, num_transactions: int = 5, target_total: float = 25000
    ) -> list[dict[str, Any]]:
        """
        Generate a structuring pattern for SAR detection testing.

        Args:
            player_id: Player ID for the pattern
            num_transactions: Number of transactions
            target_total: Total amount across transactions

        Returns:
            List of transaction records exhibiting structuring
        """
        records = []
        base_date = self.random_datetime()
        remaining = target_total

        for i in range(num_transactions):
            # Keep each transaction just under $10K
            amount = min(remaining, round(self.rng.uniform(8000, 9900), 2))
            remaining -= amount

            timestamp = base_date + timedelta(hours=int(self.rng.integers(1, 8)) * i)

            record = {
                "transaction_id": f"TXN-STRUCT-{i+1:02d}",
                "player_id": player_id,
                "timestamp": timestamp,
                "amount": amount,
                "transaction_type": "CASH_IN",
                "structuring_flag": True,
            }
            records.append(record)

            if remaining <= 0:
                break

        return records
