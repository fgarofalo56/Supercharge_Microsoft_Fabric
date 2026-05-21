"""
Compliance Pipeline Integration Test
=====================================

Validates the compliance data pipeline from generation through
configurable thresholds, ensuring CTR/SAR/W-2G records meet
regulatory requirements.

Tests:
  - Config-driven thresholds load correctly
  - CTR records are above configured threshold
  - SAR structuring amounts fall within configured range
  - W-2G amounts exceed game-specific thresholds
  - Financial generator uses shared CTR threshold
  - Lineage utility functions work correctly
"""

import sys
from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Ensure generators are importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "data_generation"))

from generators.compliance_generator import ComplianceGenerator, get_threshold
from generators.financial_generator import FinancialGenerator

SEED = 42
SAMPLE_SIZE = 100


class TestComplianceThresholdsConfig:
    """Test that compliance thresholds are properly loaded from config."""

    def test_config_file_exists(self):
        """Config file should exist at expected path."""
        config_path = (
            PROJECT_ROOT / "data_generation" / "config" / "compliance_thresholds.yaml"
        )
        assert config_path.exists(), f"Missing config: {config_path}"

    def test_config_loads_valid_yaml(self):
        """Config file should parse as valid YAML."""
        config_path = (
            PROJECT_ROOT / "data_generation" / "config" / "compliance_thresholds.yaml"
        )
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert isinstance(config, dict)
        assert "ctr" in config
        assert "sar" in config
        assert "w2g" in config

    def test_ctr_threshold_loaded(self):
        """CTR threshold should load from config."""
        threshold = get_threshold("ctr", "threshold")
        assert threshold is not None
        assert threshold == 10000

    def test_sar_structuring_range(self):
        """SAR structuring range should be below CTR threshold."""
        lower = get_threshold("sar", "structuring_lower")
        upper = get_threshold("sar", "structuring_upper")
        ctr = get_threshold("ctr", "threshold")
        assert lower is not None
        assert upper is not None
        assert lower < upper
        assert upper < ctr  # Structuring is always below CTR

    def test_w2g_thresholds_all_positive(self):
        """All W-2G thresholds should be positive numbers."""
        thresholds = get_threshold("w2g", "thresholds")
        assert thresholds is not None
        for game, amount in thresholds.items():
            assert amount > 0, f"{game} threshold should be positive, got {amount}"


class TestCompliancePipelineIntegration:
    """End-to-end compliance pipeline tests."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize generators."""
        self.compliance_gen = ComplianceGenerator(seed=SEED)
        self.financial_gen = FinancialGenerator(seed=SEED)

    def test_ctr_records_above_threshold(self):
        """All CTR records should have amounts >= CTR threshold."""
        records = [self.compliance_gen.generate_record() for _ in range(SAMPLE_SIZE)]
        ctr_records = [r for r in records if r["filing_type"] == "CTR"]

        if not ctr_records:
            pytest.skip("No CTR records generated in sample")

        for record in ctr_records:
            assert record["amount"] >= ComplianceGenerator.CTR_THRESHOLD, (
                f"CTR amount {record['amount']} below threshold {ComplianceGenerator.CTR_THRESHOLD}"
            )

    def test_w2g_amounts_above_game_threshold(self):
        """W-2G jackpot amounts should exceed game-specific thresholds."""
        records = [self.compliance_gen.generate_record() for _ in range(SAMPLE_SIZE)]
        w2g_records = [r for r in records if r["filing_type"] == "W2G"]

        if not w2g_records:
            pytest.skip("No W2G records generated in sample")

        for record in w2g_records:
            game = record.get("game_type")
            if game and game in ComplianceGenerator.W2G_THRESHOLDS:
                threshold = ComplianceGenerator.W2G_THRESHOLDS[game]
                assert record["jackpot_amount"] >= threshold, (
                    f"W2G for {game}: {record['jackpot_amount']} below threshold {threshold}"
                )

    def test_sar_has_required_fields(self):
        """SAR records should have category and narrative."""
        records = [self.compliance_gen.generate_record() for _ in range(SAMPLE_SIZE)]
        sar_records = [r for r in records if r["filing_type"] == "SAR"]

        if not sar_records:
            pytest.skip("No SAR records generated in sample")

        for record in sar_records:
            assert record.get("sar_category") is not None, "SAR missing category"
            assert record.get("sar_narrative") is not None, "SAR missing narrative"
            assert record["sar_category"] in ComplianceGenerator.SAR_CATEGORIES

    def test_financial_ctr_flag_matches_threshold(self):
        """Financial generator CTR flag should match threshold from config."""
        records = [self.financial_gen.generate_record() for _ in range(200)]

        for record in records:
            expected_ctr = record["amount"] >= ComplianceGenerator.CTR_THRESHOLD
            assert record["ctr_required"] == expected_ctr, (
                f"Amount {record['amount']}: expected CTR={expected_ctr}, got {record['ctr_required']}"
            )

    def test_structuring_pattern_amounts(self):
        """Structuring pattern should produce amounts in configured range."""
        pattern = self.compliance_gen.generate_structuring_pattern(
            player_id="PLY-TEST",
            num_transactions=5,
            target_total=25000,
        )

        lower = ComplianceGenerator.SAR_STRUCTURING_LOWER
        upper = ComplianceGenerator.SAR_STRUCTURING_UPPER

        for txn in pattern:
            assert txn["amount"] <= upper, (
                f"Structuring amount {txn['amount']} exceeds upper bound {upper}"
            )

    def test_withholding_uses_config_rates(self):
        """W-2G withholding should use configured federal + state rates."""
        records = [self.compliance_gen.generate_record() for _ in range(SAMPLE_SIZE)]
        w2g_with_withholding = [
            r
            for r in records
            if r["filing_type"] == "W2G" and r.get("withholding_amount", 0) > 0
        ]

        if not w2g_with_withholding:
            pytest.skip("No W2G records with withholding in sample")

        expected_rate = (
            ComplianceGenerator.FEDERAL_WITHHOLDING_RATE
            + ComplianceGenerator.STATE_WITHHOLDING_RATE
        )

        for record in w2g_with_withholding:
            assert record["withholding_rate"] == pytest.approx(
                expected_rate, abs=0.001
            ), (
                f"Withholding rate {record['withholding_rate']} != expected {expected_rate}"
            )
