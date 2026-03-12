"""
Unit tests for casino data generators.
"""

from datetime import datetime

import pytest


class TestSlotMachineGenerator:
    """Tests for SlotMachineGenerator."""

    def test_generate_single_record(self, slot_generator):
        """Test generation of a single record."""
        record = slot_generator.generate_record()

        assert record is not None
        assert "machine_id" in record
        assert "event_type" in record
        assert "event_timestamp" in record

    def test_machine_id_format(self, slot_generator):
        """Test machine ID follows expected format."""
        record = slot_generator.generate_record()

        assert record["machine_id"].startswith("SLOT-")
        assert len(record["machine_id"]) == 9  # SLOT-XXXX

    def test_event_type_valid(self, slot_generator):
        """Test event type is from valid set."""
        valid_types = [
            "GAME_PLAY",
            "JACKPOT",
            "METER_UPDATE",
            "DOOR_OPEN",
            "DOOR_CLOSE",
            "POWER_ON",
            "POWER_OFF",
            "BILL_IN",
            "TICKET_OUT",
            "TILT",
        ]

        for _ in range(100):
            record = slot_generator.generate_record()
            assert record["event_type"] in valid_types

    def test_coin_in_non_negative(self, slot_generator):
        """Test coin_in is non-negative."""
        for _ in range(100):
            record = slot_generator.generate_record()
            if record["coin_in"] is not None:
                assert record["coin_in"] >= 0

    def test_generate_batch(self, slot_generator, sample_size):
        """Test batch generation."""
        df = slot_generator.generate(sample_size, show_progress=False)
        records = df.to_dict("records")

        assert len(records) == sample_size
        assert all("machine_id" in r for r in records)

    def test_zone_valid(self, slot_generator):
        """Test zone is from valid set."""
        valid_zones = ["North", "South", "East", "West", "VIP", "High Limit", "Penny"]

        for _ in range(100):
            record = slot_generator.generate_record()
            if record["zone"] is not None:
                assert record["zone"] in valid_zones

    def test_denomination_valid(self, slot_generator):
        """Test denomination is valid."""
        valid_denoms = [0.01, 0.05, 0.25, 0.50, 1.00, 2.00, 5.00, 10.00, 25.00, 100.00]

        for _ in range(100):
            record = slot_generator.generate_record()
            if record["denomination"] is not None:
                assert record["denomination"] in valid_denoms

    def test_jackpot_amount_on_jackpot_event(self, slot_generator):
        """Test jackpot amount is set for jackpot events."""
        jackpot_records = []

        # Generate until we get jackpot events
        for _ in range(1000):
            record = slot_generator.generate_record()
            if record["event_type"] == "JACKPOT":
                jackpot_records.append(record)
            if len(jackpot_records) >= 5:
                break

        for record in jackpot_records:
            assert record["jackpot_amount"] is not None
            assert record["jackpot_amount"] > 0


class TestPlayerGenerator:
    """Tests for PlayerGenerator."""

    def test_generate_single_record(self, player_generator):
        """Test generation of a single player record."""
        record = player_generator.generate_record()

        assert record is not None
        assert "player_id" in record
        assert "first_name" in record
        assert "last_name" in record

    def test_player_id_format(self, player_generator):
        """Test player ID format."""
        record = player_generator.generate_record()

        assert record["player_id"].startswith("P")
        # ID should be numeric after P
        assert record["player_id"][1:].isdigit()

    def test_loyalty_tier_valid(self, player_generator):
        """Test loyalty tier is from valid set."""
        valid_tiers = ["Bronze", "Silver", "Gold", "Platinum", "Diamond"]

        for _ in range(100):
            record = player_generator.generate_record()
            assert record["loyalty_tier"] in valid_tiers

    def test_ssn_hash_not_raw(self, player_generator):
        """Test SSN is hashed, not raw."""
        record = player_generator.generate_record()

        # Should have ssn_hash, not ssn
        assert "ssn_hash" in record or "ssn" not in record
        if "ssn_hash" in record:
            # Hash should be 64 chars (SHA-256)
            assert len(record["ssn_hash"]) == 64

    def test_email_format(self, player_generator):
        """Test email has valid format."""
        record = player_generator.generate_record()

        if record["email"]:
            assert "@" in record["email"]
            assert "." in record["email"]

    def test_date_of_birth_reasonable(self, player_generator):
        """Test DOB is reasonable (18+ years old)."""
        record = player_generator.generate_record()

        if record["date_of_birth"]:
            dob = datetime.strptime(record["date_of_birth"], "%Y-%m-%d")
            age = (datetime.now() - dob).days / 365

            # Must be 21+ for casino
            assert age >= 21


class TestComplianceGenerator:
    """Tests for ComplianceGenerator."""

    def test_generate_single_record(self, compliance_generator):
        """Test generation of a single compliance record."""
        record = compliance_generator.generate_record()

        assert record is not None
        assert "filing_type" in record

    def test_filing_type_valid(self, compliance_generator):
        """Test filing type is from valid set."""
        valid_types = ["CTR", "SAR", "W2G"]

        for _ in range(100):
            record = compliance_generator.generate_record()
            assert record["filing_type"] in valid_types

    @pytest.mark.compliance
    def test_ctr_threshold(self, compliance_generator):
        """Test CTR threshold logic ($10,000+)."""
        ctr_records = []

        for _ in range(500):
            record = compliance_generator.generate_record()
            if record["filing_type"] == "CTR":
                ctr_records.append(record)
            if len(ctr_records) >= 10:
                break

        for record in ctr_records:
            assert record["amount"] >= 10000

    @pytest.mark.compliance
    def test_w2g_threshold(self, compliance_generator):
        """Test W-2G threshold logic ($1,200+ slots, $600+ table with 300:1)."""
        w2g_records = []

        for _ in range(500):
            record = compliance_generator.generate_record()
            if record["filing_type"] == "W2G":
                w2g_records.append(record)
            if len(w2g_records) >= 10:
                break

        for record in w2g_records:
            # W-2G threshold varies by game type
            assert record["amount"] >= 600  # Minimum threshold


class TestFinancialGenerator:
    """Tests for FinancialGenerator."""

    def test_generate_single_record(self, financial_generator):
        """Test generation of a single financial record."""
        record = financial_generator.generate_record()

        assert record is not None
        assert "transaction_id" in record
        assert "amount" in record

    def test_transaction_type_valid(self, financial_generator):
        """Test transaction type is valid."""
        # Use the generator's defined transaction types
        valid_types = financial_generator.TRANSACTION_TYPES

        for _ in range(100):
            record = financial_generator.generate_record()
            assert record["transaction_type"] in valid_types

    def test_amount_positive(self, financial_generator):
        """Test amount is positive."""
        for _ in range(100):
            record = financial_generator.generate_record()
            assert record["amount"] > 0

    @pytest.mark.compliance
    def test_ctr_flag_logic(self, financial_generator):
        """Test CTR required flag is set for $10K+ transactions."""
        large_txn_records = []

        for _ in range(500):
            record = financial_generator.generate_record()
            if record["amount"] >= 10000:
                large_txn_records.append(record)
            if len(large_txn_records) >= 5:
                break

        for record in large_txn_records:
            assert record.get("ctr_required", False) is True


class TestSecurityGenerator:
    """Tests for SecurityGenerator."""

    def test_generate_single_record(self, security_generator):
        """Test generation of a single security record."""
        record = security_generator.generate_record()

        assert record is not None
        assert "event_id" in record
        assert "event_type" in record

    def test_event_type_valid(self, security_generator):
        """Test event type is valid per security_events_schema.json."""
        valid_types = [
            "BADGE_SWIPE",
            "DOOR_ENTRY",
            "ACCESS_GRANTED",
            "ACCESS_DENIED",
            "CAMERA_ALERT",
            "MOTION_DETECTED",
            "CAMERA_OBSTRUCTION",
            "EXCLUSION_CHECK",
            "EXCLUSION_VIOLATION",
            "INCIDENT_REPORT",
            "ALTERCATION",
            "MEDICAL_EMERGENCY",
            "THREAT_DETECTED",
            "WEAPON_DETECTED",
            "TRESPASS",
            "UNAUTHORIZED_ACCESS",
            "SUSPICIOUS_ACTIVITY",
            "PATRON_COMPLAINT",
            "ESCORT_REQUEST",
            "SECURITY_PATROL",
        ]

        for _ in range(100):
            record = security_generator.generate_record()
            assert record["event_type"] in valid_types

    def test_severity_valid(self, security_generator):
        """Test severity_level is valid per security_events_schema.json."""
        valid_severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

        for _ in range(100):
            record = security_generator.generate_record()
            # Generator uses severity_level field per schema
            if record.get("severity_level"):
                assert record["severity_level"] in valid_severities


class TestTableGamesGenerator:
    """Tests for TableGamesGenerator."""

    def test_generate_single_record(self, table_games_generator):
        """Test generation of a single table games record."""
        record = table_games_generator.generate_record()

        assert record is not None
        assert "table_id" in record
        assert "game_type" in record

    def test_game_type_valid(self, table_games_generator):
        """Test game type is valid."""
        valid_types = [
            "Blackjack",
            "Roulette",
            "Craps",
            "Baccarat",
            "Poker",
            "Pai Gow",
            "Three Card Poker",
        ]

        for _ in range(100):
            record = table_games_generator.generate_record()
            assert record["game_type"] in valid_types

    def test_buy_in_positive(self, table_games_generator):
        """Test buy-in is positive."""
        for _ in range(100):
            record = table_games_generator.generate_record()
            if record.get("buy_in"):
                assert record["buy_in"] > 0


class TestGeneratorReproducibility:
    """Tests for generator reproducibility with seeds."""

    def test_same_seed_same_results(self):
        """Test that same seed produces deterministic results within a generator."""
        import numpy as np
        from faker import Faker

        from generators.slot_machine_generator import SlotMachineGenerator

        # Reset global random state and create generator
        np.random.seed(12345)
        Faker.seed(12345)
        gen1 = SlotMachineGenerator(seed=12345)
        records1 = gen1.generate(10, show_progress=False).to_dict("records")

        # Reset global random state and create new generator
        np.random.seed(12345)
        Faker.seed(12345)
        gen2 = SlotMachineGenerator(seed=12345)
        records2 = gen2.generate(10, show_progress=False).to_dict("records")

        # Compare key fields
        for r1, r2 in zip(records1, records2, strict=False):
            assert r1["machine_id"] == r2["machine_id"]
            assert r1["event_type"] == r2["event_type"]

    def test_different_seed_different_results(self):
        """Test that different seeds produce different results."""
        from generators.slot_machine_generator import SlotMachineGenerator

        gen1 = SlotMachineGenerator(seed=11111)
        gen2 = SlotMachineGenerator(seed=22222)

        records1 = gen1.generate(100, show_progress=False).to_dict("records")
        records2 = gen2.generate(100, show_progress=False).to_dict("records")

        # At least some records should be different
        differences = sum(
            1
            for r1, r2 in zip(records1, records2, strict=False)
            if r1["machine_id"] != r2["machine_id"]
        )
        assert differences > 0
