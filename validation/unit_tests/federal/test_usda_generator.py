"""
Unit tests for USDAGenerator.

Covers both supported domains:
- crop_production: NASS QuickStats-style records
- food_safety:     FSIS recall-style records
"""

VALID_COMMODITIES = [
    "CORN",
    "SOYBEANS",
    "WHEAT",
    "COTTON",
    "RICE",
    "BARLEY",
    "OATS",
    "SORGHUM",
    "HAY",
    "POTATOES",
]
VALID_RECALL_CLASSES = ["Class I", "Class II", "Class III"]
VALID_RISK_LEVELS = ["HIGH", "MEDIUM", "LOW"]
VALID_AGG_LEVELS = ["NATIONAL", "STATE", "COUNTY"]


class TestUSDAGenerator:
    """Tests for USDAGenerator covering crop_production and food_safety domains."""

    # ------------------------------------------------------------------
    # crop_production domain
    # ------------------------------------------------------------------

    def test_generate_crop_record(self, usda_generator):
        """Generate a crop production record and assert required fields are present."""
        record = usda_generator.generate_record(domain="crop_production")

        assert record is not None
        assert "record_id" in record
        assert "commodity" in record
        assert "year" in record
        assert "state_fips" in record

    def test_crop_commodity_valid(self, usda_generator):
        """All commodities across 100 records must come from the defined commodity list."""
        for _ in range(100):
            record = usda_generator.generate_record(domain="crop_production")
            assert record["commodity"] in VALID_COMMODITIES

    def test_crop_state_fips_format(self, usda_generator):
        """state_fips must be a 2-digit zero-padded numeric string."""
        for _ in range(50):
            record = usda_generator.generate_record(domain="crop_production")
            fips = record["state_fips"]
            assert isinstance(fips, str), "state_fips must be a string"
            assert len(fips) == 2, f"state_fips must be 2 digits, got '{fips}'"
            assert fips.isdigit(), f"state_fips must contain only digits, got '{fips}'"

    def test_crop_value_positive(self, usda_generator):
        """Crop production value must be strictly positive."""
        for _ in range(100):
            record = usda_generator.generate_record(domain="crop_production")
            assert record["value"] > 0, "crop value must be > 0"

    def test_crop_agg_level_valid(self, usda_generator):
        """agg_level_desc must be one of NATIONAL, STATE, or COUNTY."""
        for _ in range(100):
            record = usda_generator.generate_record(domain="crop_production")
            assert record["agg_level_desc"] in VALID_AGG_LEVELS

    # ------------------------------------------------------------------
    # food_safety domain
    # ------------------------------------------------------------------

    def test_generate_food_safety_record(self, usda_generator):
        """Generate a food safety record and assert required fields are present."""
        record = usda_generator.generate_record(domain="food_safety")

        assert record is not None
        assert "recall_id" in record
        assert "product_type" in record
        assert "reason" in record

    def test_food_safety_recall_class_valid(self, usda_generator):
        """recall_class must be one of Class I, Class II, or Class III."""
        for _ in range(100):
            record = usda_generator.generate_record(domain="food_safety")
            assert record["recall_class"] in VALID_RECALL_CLASSES

    def test_food_safety_risk_level_valid(self, usda_generator):
        """risk_level must be HIGH, MEDIUM, or LOW and consistent with recall_class."""
        risk_map = {"Class I": "HIGH", "Class II": "MEDIUM", "Class III": "LOW"}
        for _ in range(100):
            record = usda_generator.generate_record(domain="food_safety")
            assert record["risk_level"] in VALID_RISK_LEVELS
            expected_risk = risk_map[record["recall_class"]]
            assert record["risk_level"] == expected_risk, (
                f"recall_class {record['recall_class']} should map to "
                f"{expected_risk}, got {record['risk_level']}"
            )

    # ------------------------------------------------------------------
    # Batch generation
    # ------------------------------------------------------------------

    def test_generate_batch(self, usda_generator, sample_size):
        """generate_batch returns a DataFrame with the requested number of rows."""
        df = usda_generator.generate_batch(count=sample_size, domain="crop_production")

        assert len(df) == sample_size, f"Expected {sample_size} rows, got {len(df)}"

    # ------------------------------------------------------------------
    # Metadata columns
    # ------------------------------------------------------------------

    def test_metadata_columns_present(self, usda_generator):
        """Standard metadata columns _ingested_at, _source, and _batch_id must be present."""
        record = usda_generator.generate_record(domain="crop_production")

        assert "_ingested_at" in record, "_ingested_at metadata column missing"
        assert "_source" in record, "_source metadata column missing"
        assert "_batch_id" in record, "_batch_id metadata column missing"

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def test_invalid_domain_raises(self, usda_generator):
        """generate_record with an unrecognised domain must raise a ValueError.

        The current generator silently falls back to crop_production for any
        non-'food_safety' string (no explicit guard).  This test documents the
        *intended* contract: callers should receive a ValueError for invalid
        domains.  The test raises ValueError explicitly after a silent fallback
        so that it will pass once the generator adds input validation, and will
        serve as a reminder to add that guard if it is not yet present.
        """
        try:
            result = usda_generator.generate_record(domain="invalid")  # type: ignore[arg-type]
        except (ValueError, KeyError):
            # Generator already validates — test passes.
            return

        # Generator fell back silently; raise to enforce the contract.
        raise ValueError(
            f"generate_record(domain='invalid') should raise ValueError but "
            f"returned a record instead: {list(result.keys())}"
        )
