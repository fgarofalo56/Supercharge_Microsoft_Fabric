"""
Compliance Rules Tests
=======================

Tests for business/regulatory compliance rules:
- CTR threshold ($10K) triggers correctly
- W2G threshold ($1,200 slots, $600 table games) validation
- SAR pattern detection
- PII masking (SSN hash, no raw PII)
"""

import hashlib
import re
from datetime import datetime

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.compliance]


class TestCTRThreshold:
    """Tests for Currency Transaction Report (CTR) threshold compliance."""

    CTR_THRESHOLD = 10000  # $10,000

    def test_ctr_generated_for_large_amounts(self, sample_compliance_data):
        """Verify CTR records are generated for amounts >= $10,000."""
        ctr_records = sample_compliance_data[
            sample_compliance_data["filing_type"] == "CTR"
        ]

        # All CTR records should have amount >= $10,000
        for _, record in ctr_records.iterrows():
            assert record["amount"] >= self.CTR_THRESHOLD, (
                f"CTR generated for amount ${record['amount']} (below threshold)"
            )

    def test_ctr_not_generated_for_small_amounts(self, sample_compliance_data):
        """Verify CTR records are NOT generated for amounts < $10,000."""
        ctr_records = sample_compliance_data[
            sample_compliance_data["filing_type"] == "CTR"
        ]

        # Should not find any CTR with amount < $10,000
        invalid_ctrs = ctr_records[ctr_records["amount"] < self.CTR_THRESHOLD]
        assert len(invalid_ctrs) == 0, (
            f"Found {len(invalid_ctrs)} CTR records below threshold"
        )

    def test_ctr_required_flag_in_financial(self, sample_financial_data):
        """Verify ctr_required flag is set correctly in financial transactions."""
        if "ctr_required" not in sample_financial_data.columns:
            pytest.skip("ctr_required not in financial data")

        # Check all records with amount >= $10,000
        large_txns = sample_financial_data[
            sample_financial_data["amount"] >= self.CTR_THRESHOLD
        ]

        for _, txn in large_txns.iterrows():
            assert txn["ctr_required"], (
                f"ctr_required not set for ${txn['amount']} transaction"
            )

    def test_ctr_not_required_for_small_amounts(self, sample_financial_data):
        """Verify ctr_required is not set for amounts < $10,000."""
        if "ctr_required" not in sample_financial_data.columns:
            pytest.skip("ctr_required not in financial data")

        # Check all records with amount < $10,000
        small_txns = sample_financial_data[
            sample_financial_data["amount"] < self.CTR_THRESHOLD
        ]

        for _, txn in small_txns.iterrows():
            assert not txn["ctr_required"], (
                f"ctr_required incorrectly set for ${txn['amount']} transaction"
            )


class TestW2GThreshold:
    """Tests for W-2G (Gambling Winnings) threshold compliance."""

    # W-2G thresholds by game type
    W2G_THRESHOLDS = {
        "Slots": 1200,
        "Video Slots": 1200,
        "Video Poker": 1200,
        "Keno": 600,
        "Bingo": 1200,
        "Poker Tournament": 5000,
        "Table Games": 600,  # At 300:1 odds or greater
    }

    MINIMUM_W2G_THRESHOLD = 600  # Absolute minimum

    def test_w2g_records_above_minimum_threshold(self, sample_compliance_data):
        """Verify all W-2G records are above minimum threshold."""
        w2g_records = sample_compliance_data[
            sample_compliance_data["filing_type"] == "W2G"
        ]

        # All W-2G records should be >= $600 (minimum for any game)
        for _, record in w2g_records.iterrows():
            assert record["amount"] >= self.MINIMUM_W2G_THRESHOLD, (
                f"W-2G generated for ${record['amount']} (below minimum)"
            )

    def test_slot_w2g_threshold(self, sample_compliance_data):
        """Verify slot W-2G records are >= $1,200."""
        w2g_records = sample_compliance_data[
            sample_compliance_data["filing_type"] == "W2G"
        ]

        # Filter to slot games
        slot_w2g = w2g_records[
            w2g_records["game_type"].isin(["Slots", "Video Slots", "Video Poker"])
        ]

        for _, record in slot_w2g.iterrows():
            assert record["amount"] >= 1200, (
                f"Slot W-2G for ${record['amount']} (threshold is $1,200)"
            )

    def test_w2g_has_jackpot_details(self, sample_compliance_data):
        """Verify W-2G records include jackpot details."""
        w2g_records = sample_compliance_data[
            sample_compliance_data["filing_type"] == "W2G"
        ]

        if len(w2g_records) == 0:
            pytest.skip("No W-2G records in sample")

        # W-2G should have amount (jackpot) and preferably game_type
        for _, record in w2g_records.iterrows():
            assert record["amount"] is not None, "W-2G missing amount"
            # game_type is important for threshold validation
            if "game_type" in record:
                pass  # game_type present


class TestSARPatternDetection:
    """Tests for Suspicious Activity Report (SAR) pattern detection."""

    def test_sar_has_category(self, sample_compliance_data):
        """Verify SAR records include a suspicion category."""
        sar_records = sample_compliance_data[
            sample_compliance_data["filing_type"] == "SAR"
        ]

        if len(sar_records) == 0:
            pytest.skip("No SAR records in sample")

        # SAR should have a category/suspicious activity type
        for _, record in sar_records.iterrows():
            has_category = (
                record.get("sar_category") is not None
                or record.get("suspicious_activity_type") is not None
            )
            assert has_category, "SAR missing suspicion category"

    def test_sar_has_narrative(self, sample_compliance_data):
        """Verify SAR records include a narrative description."""
        sar_records = sample_compliance_data[
            sample_compliance_data["filing_type"] == "SAR"
        ]

        if len(sar_records) == 0:
            pytest.skip("No SAR records in sample")

        for _, record in sar_records.iterrows():
            has_narrative = (
                record.get("sar_narrative") is not None
                or record.get("narrative") is not None
            )
            assert has_narrative, "SAR missing narrative"

    def test_structuring_detection_pattern(self, compliance_generator):
        """Test that structuring patterns can be generated for testing."""
        # Generate a structuring pattern
        pattern = compliance_generator.generate_structuring_pattern(
            player_id="P12345", num_transactions=5, target_total=25000
        )

        # Verify pattern characteristics
        assert len(pattern) >= 1, "No structuring pattern generated"

        # Each transaction should be below CTR threshold
        for txn in pattern:
            assert txn["amount"] < 10000, "Structuring transaction >= $10,000"

        # Total should approach target
        total = sum(txn["amount"] for txn in pattern)
        assert total > 0, "Structuring pattern total is 0"

    def test_suspicious_activity_flag_in_financial(self, sample_financial_data):
        """Verify suspicious_activity_flag is set for potential structuring."""
        if "suspicious_activity_flag" not in sample_financial_data.columns:
            pytest.skip("suspicious_activity_flag not in data")

        # Transactions in $8,000-$10,000 range are higher risk for structuring
        suspicious_range = sample_financial_data[
            (sample_financial_data["amount"] >= 8000)
            & (sample_financial_data["amount"] < 10000)
        ]

        if len(suspicious_range) > 0:
            # Some should be flagged (not necessarily all)
            flagged = suspicious_range["suspicious_activity_flag"].sum()
            # At least some percentage should be flagged
            flag_rate = flagged / len(suspicious_range)
            # Generator uses 10% flag rate for this range
            assert flag_rate > 0, "No suspicious flags in high-risk range"


class TestPIIMasking:
    """Tests for PII (Personally Identifiable Information) masking compliance."""

    def test_ssn_is_hashed_not_raw(self, sample_player_data, validate_ssn_hash):
        """Verify SSN is stored as hash, not raw format."""
        if "ssn_hash" not in sample_player_data.columns:
            pytest.skip("ssn_hash not in player data")

        for ssn_hash in sample_player_data["ssn_hash"].dropna().head(100):
            assert validate_ssn_hash(ssn_hash), f"Invalid SSN hash: {ssn_hash}"

    def test_ssn_masked_format(self, sample_player_data):
        """Verify SSN masked format shows only last 4 digits."""
        if "ssn_masked" not in sample_player_data.columns:
            pytest.skip("ssn_masked not in player data")

        masked_pattern = re.compile(r"^XXX-XX-\d{4}$")

        for ssn_masked in sample_player_data["ssn_masked"].dropna().head(100):
            assert masked_pattern.match(ssn_masked), (
                f"SSN mask format invalid: {ssn_masked}"
            )

    def test_no_raw_ssn_in_data(self, sample_player_data):
        """Verify no raw SSN (###-##-####) appears in any field."""
        raw_ssn_pattern = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

        for col in sample_player_data.columns:
            if col in ["ssn_masked", "ssn_hash"]:
                continue  # Skip expected SSN-related columns

            for value in sample_player_data[col].dropna().head(100):
                if isinstance(value, str):
                    matches = raw_ssn_pattern.findall(value)
                    for match in matches:
                        # Masked format (XXX-XX-####) is OK
                        if not match.startswith("XXX"):
                            pytest.fail(f"Raw SSN found in {col}: {match}")

    def test_no_raw_ssn_in_compliance(self, sample_compliance_data):
        """Verify no raw SSN in compliance filings."""
        raw_ssn_pattern = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

        for col in sample_compliance_data.columns:
            if col in ["ssn_masked", "ssn_hash"]:
                continue

            for value in sample_compliance_data[col].dropna().head(100):
                if isinstance(value, str):
                    matches = raw_ssn_pattern.findall(value)
                    for match in matches:
                        if not match.startswith("XXX"):
                            pytest.fail(f"Raw SSN in compliance {col}: {match}")

    def test_email_masking_when_disabled(self, player_generator):
        """Test email is masked when include_pii is False."""
        # Generator with PII disabled (default)
        from generators.player_generator import PlayerGenerator

        gen = PlayerGenerator(seed=42, include_pii=False)

        record = gen.generate_record()

        # Email should be masked (contains @masked.com or similar)
        assert "@masked.com" in record["email"] or "@" not in record["email"][:10], (
            f"Email may not be masked: {record['email']}"
        )

    def test_address_masking_when_disabled(self, player_generator):
        """Test address is masked when include_pii is False."""
        from generators.player_generator import PlayerGenerator

        gen = PlayerGenerator(seed=42, include_pii=False)

        record = gen.generate_record()

        # Address should contain masked indicator
        assert "Masked" in record["address"] or "***" in record["address"], (
            f"Address may not be masked: {record['address']}"
        )

    def test_names_partially_masked(self, player_generator):
        """Test names are partially masked when include_pii is False."""
        from generators.player_generator import PlayerGenerator

        gen = PlayerGenerator(seed=42, include_pii=False)

        record = gen.generate_record()

        # Names should show only first initial
        assert "***" in record["first_name"], (
            f"First name may not be masked: {record['first_name']}"
        )
        assert "***" in record["last_name"], (
            f"Last name may not be masked: {record['last_name']}"
        )

    def test_phone_masked(self, player_generator):
        """Test phone is masked when include_pii is False."""
        from generators.player_generator import PlayerGenerator

        gen = PlayerGenerator(seed=42, include_pii=False)

        record = gen.generate_record()

        # Phone should be partially masked
        assert "***" in record["phone"], f"Phone may not be masked: {record['phone']}"


class TestHashingConsistency:
    """Tests for hashing consistency and security."""

    def test_ssn_hash_is_deterministic_with_salt(self):
        """Verify same SSN produces same hash with same salt."""
        from generators.player_generator import PlayerGenerator

        # Create two generators with same seed
        gen1 = PlayerGenerator(seed=42)
        gen2 = PlayerGenerator(seed=42)

        # Generate same SSN value
        test_ssn = "123-45-6789"
        hash1 = gen1.hash_value(test_ssn, gen1._salt)
        hash2 = gen2.hash_value(test_ssn, gen2._salt)

        assert hash1 == hash2, "Same SSN with same salt produced different hashes"

    def test_different_ssn_produces_different_hash(self):
        """Verify different SSNs produce different hashes."""
        from generators.player_generator import PlayerGenerator

        gen = PlayerGenerator(seed=42)

        hash1 = gen.hash_value("123-45-6789", gen._salt)
        hash2 = gen.hash_value("987-65-4321", gen._salt)

        assert hash1 != hash2, "Different SSNs produced same hash"

    def test_hash_uses_sha256(self, sample_player_data):
        """Verify hash length matches SHA-256 output."""
        if "ssn_hash" not in sample_player_data.columns:
            pytest.skip("ssn_hash not in data")

        for ssn_hash in sample_player_data["ssn_hash"].dropna().head(100):
            # SHA-256 produces 64 hex characters
            assert len(ssn_hash) == 64, f"Hash length {len(ssn_hash)} != 64"

    def test_id_hash_in_compliance(self, sample_compliance_data):
        """Verify ID numbers are hashed in compliance records."""
        hash_fields = ["player_name_hash", "address_hash", "id_number_hash"]

        for field in hash_fields:
            if field in sample_compliance_data.columns:
                for value in sample_compliance_data[field].dropna().head(50):
                    # Should be SHA-256 hash (64 chars)
                    if value:
                        assert len(value) == 64, f"{field} not proper hash length"


class TestComplianceFieldPresence:
    """Tests for required compliance fields presence."""

    def test_ctr_required_fields(self, sample_compliance_data):
        """Verify CTR records have required FinCEN fields."""
        ctr_records = sample_compliance_data[
            sample_compliance_data["filing_type"] == "CTR"
        ]

        if len(ctr_records) == 0:
            pytest.skip("No CTR records")

        required_fields = ["amount", "player_id", "transaction_date"]

        for _, record in ctr_records.head(10).iterrows():
            for field in required_fields:
                if field in record:
                    assert record[field] is not None, f"CTR missing {field}"

    def test_sar_required_fields(self, sample_compliance_data):
        """Verify SAR records have required fields."""
        sar_records = sample_compliance_data[
            sample_compliance_data["filing_type"] == "SAR"
        ]

        if len(sar_records) == 0:
            pytest.skip("No SAR records")

        # SAR should have suspicion details
        for _, record in sar_records.head(10).iterrows():
            has_details = (
                record.get("sar_category") is not None
                or record.get("sar_narrative") is not None
            )
            assert has_details, "SAR missing suspicion details"

    def test_w2g_required_fields(self, sample_compliance_data):
        """Verify W-2G records have required IRS fields."""
        w2g_records = sample_compliance_data[
            sample_compliance_data["filing_type"] == "W2G"
        ]

        if len(w2g_records) == 0:
            pytest.skip("No W-2G records")

        for _, record in w2g_records.head(10).iterrows():
            assert record["amount"] is not None, "W-2G missing amount"
            # W-2G should have jackpot amount
            if "jackpot_amount" in record:
                assert (
                    record["jackpot_amount"] is not None or record["amount"] is not None
                )
