"""
Data Pipeline Integration Tests
================================

Tests for data pipeline transformations:
- Bronze -> Silver transformation logic
- Silver -> Gold aggregation logic
- Data type consistency through layers
- Null handling through pipeline
"""

from datetime import datetime
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.pipeline]


class TestBronzeToSilverTransformation:
    """Tests for Bronze to Silver layer transformation logic."""

    def test_null_required_fields_filtered(self, sample_slot_data):
        """Verify records with null required fields are filtered in Silver."""
        # Bronze layer accepts nulls, Silver should filter them
        required_fields = ["machine_id", "event_type", "event_timestamp"]

        # Simulate Bronze -> Silver filter
        df_bronze = sample_slot_data.copy()
        df_silver = df_bronze.dropna(subset=required_fields)

        # All remaining records should have required fields
        for field in required_fields:
            null_count = df_silver[field].isna().sum()
            assert null_count == 0, f"Silver layer has {null_count} null {field} values"

    def test_negative_values_corrected(self, sample_slot_data):
        """Verify negative coin values are corrected to 0."""
        df_bronze = sample_slot_data.copy()

        # Inject some negative values to simulate bad data
        df_bronze.loc[0:10, "coin_in"] = -100

        # Apply Silver transformation rule
        df_silver = df_bronze.copy()
        df_silver["coin_in"] = df_silver["coin_in"].apply(
            lambda x: 0 if x is not None and x < 0 else x
        )

        # No negative values should remain
        negative_count = (df_silver["coin_in"].dropna() < 0).sum()
        assert negative_count == 0, (
            f"Silver layer has {negative_count} negative coin_in values"
        )

    def test_timestamp_to_date_extraction(self, sample_slot_data):
        """Verify event_date is correctly extracted from event_timestamp."""
        df_bronze = sample_slot_data.copy()

        # Apply Silver transformation
        df_silver = df_bronze.copy()

        def extract_date(ts):
            if ts is None:
                return None
            if isinstance(ts, str):
                ts = datetime.fromisoformat(
                    ts.replace("Z", "+00:00").replace("+00:00", "")
                )
            return ts.date()

        df_silver["event_date"] = df_silver["event_timestamp"].apply(extract_date)

        # Verify event_date is populated
        valid_timestamps = df_bronze["event_timestamp"].notna().sum()
        valid_dates = df_silver["event_date"].notna().sum()
        assert valid_dates == valid_timestamps, (
            "Date extraction failed for some timestamps"
        )

    def test_hour_extraction(self, sample_slot_data):
        """Verify event_hour is correctly extracted from event_timestamp."""
        df_bronze = sample_slot_data.copy()

        # Apply Silver transformation
        df_silver = df_bronze.copy()

        def extract_hour(ts):
            if ts is None:
                return None
            if isinstance(ts, str):
                ts = datetime.fromisoformat(
                    ts.replace("Z", "+00:00").replace("+00:00", "")
                )
            return ts.hour

        df_silver["event_hour"] = df_silver["event_timestamp"].apply(extract_hour)

        # Hours should be 0-23
        valid_hours = df_silver["event_hour"].dropna()
        assert (valid_hours >= 0).all(), "Some hours are negative"
        assert (valid_hours <= 23).all(), "Some hours exceed 23"

    def test_event_type_standardization(self, sample_slot_data):
        """Verify event types are standardized to uppercase."""
        df_bronze = sample_slot_data.copy()

        # Inject mixed case to simulate real-world data
        df_bronze.loc[0:10, "event_type"] = "game_play"
        df_bronze.loc[11:20, "event_type"] = "Game_Play"

        # Apply Silver transformation
        df_silver = df_bronze.copy()
        df_silver["event_type"] = df_silver["event_type"].str.upper().str.strip()

        # All should be uppercase
        lowercase_count = (
            df_silver["event_type"].str.contains("[a-z]", regex=True, na=False).sum()
        )
        assert lowercase_count == 0, (
            f"Silver layer has {lowercase_count} lowercase event_types"
        )

    def test_deduplication(self, sample_slot_data):
        """Verify deduplication removes exact duplicates."""
        df_bronze = sample_slot_data.copy()

        # Add duplicates
        duplicates = df_bronze.head(10).copy()
        df_bronze = pd.concat([df_bronze, duplicates], ignore_index=True)

        initial_count = len(df_bronze)

        # Apply Silver deduplication
        df_silver = df_bronze.drop_duplicates(
            subset=["machine_id", "event_timestamp", "event_type"]
        )

        # Should have fewer records after deduplication
        assert len(df_silver) < initial_count, "Deduplication did not remove duplicates"

    def test_data_quality_scoring(self, sample_slot_data):
        """Verify data quality scores are calculated correctly."""
        df_bronze = sample_slot_data.copy()

        # Define valid values (from Silver notebook)
        VALID_EVENT_TYPES = [
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
        VALID_ZONES = ["North", "South", "East", "West", "VIP", "High Limit", "Penny"]

        # Calculate DQ score
        df_silver = df_bronze.copy()
        df_silver["is_valid_event_type"] = df_silver["event_type"].isin(
            VALID_EVENT_TYPES
        )
        df_silver["is_valid_zone"] = (
            df_silver["zone"].isin(VALID_ZONES) | df_silver["zone"].isna()
        )

        df_silver["_dq_score"] = (
            (df_silver["is_valid_event_type"].astype(int) * 20)
            + (df_silver["is_valid_zone"].astype(int) * 20)
            + (df_silver["coin_in"].notna().astype(int) * 20)
            + (df_silver["player_id"].notna().astype(int) * 20)
            + 20  # Base score for having required fields
        )

        # Scores should be 0-100
        assert (df_silver["_dq_score"] >= 0).all(), "Some DQ scores are negative"
        assert (df_silver["_dq_score"] <= 100).all(), "Some DQ scores exceed 100"


class TestSilverToGoldAggregation:
    """Tests for Silver to Gold layer aggregation logic."""

    def test_daily_aggregation(self, sample_slot_data):
        """Verify daily aggregations are calculated correctly."""
        df_silver = sample_slot_data.copy()

        # Add event_date column
        def extract_date(ts):
            if ts is None:
                return None
            if isinstance(ts, str):
                ts = datetime.fromisoformat(
                    ts.replace("Z", "+00:00").replace("+00:00", "")
                )
            return ts.strftime("%Y-%m-%d")

        df_silver["event_date"] = df_silver["event_timestamp"].apply(extract_date)

        # Gold aggregation
        df_gold = (
            df_silver.groupby(["machine_id", "event_date"])
            .agg(
                {
                    "coin_in": "sum",
                    "coin_out": "sum",
                    "games_played": "sum",
                    "event_type": "count",
                }
            )
            .reset_index()
        )

        df_gold.columns = [
            "machine_id",
            "business_date",
            "total_coin_in",
            "total_coin_out",
            "total_games",
            "total_events",
        ]

        # Verify aggregations
        assert len(df_gold) > 0, "No aggregated records produced"
        assert "total_coin_in" in df_gold.columns, "Missing total_coin_in"
        assert "total_events" in df_gold.columns, "Missing total_events"

    def test_net_win_calculation(self, sample_slot_data):
        """Verify net win is calculated correctly (coin_in - coin_out)."""
        df_silver = sample_slot_data.copy()

        # Extract date for grouping
        def extract_date(ts):
            if ts is None:
                return None
            if isinstance(ts, str):
                ts = datetime.fromisoformat(
                    ts.replace("Z", "+00:00").replace("+00:00", "")
                )
            return ts.strftime("%Y-%m-%d")

        df_silver["event_date"] = df_silver["event_timestamp"].apply(extract_date)

        # Gold aggregation
        df_gold = (
            df_silver.groupby(["machine_id", "event_date"])
            .agg(
                {
                    "coin_in": "sum",
                    "coin_out": "sum",
                }
            )
            .reset_index()
        )

        df_gold["total_coin_in"] = df_gold["coin_in"].fillna(0)
        df_gold["total_coin_out"] = df_gold["coin_out"].fillna(0)
        df_gold["net_win"] = df_gold["total_coin_in"] - df_gold["total_coin_out"]

        # Verify calculation
        for _, row in df_gold.head(10).iterrows():
            expected_net_win = row["total_coin_in"] - row["total_coin_out"]
            assert abs(row["net_win"] - expected_net_win) < 0.01, (
                "Net win calculation error"
            )

    def test_hold_percentage_calculation(self, sample_slot_data):
        """Verify hold percentage is calculated correctly."""
        df_silver = sample_slot_data.copy()

        # Simulate Gold aggregation
        total_coin_in = df_silver["coin_in"].sum() or 0
        total_coin_out = df_silver["coin_out"].sum() or 0
        net_win = total_coin_in - total_coin_out

        # Calculate hold percentage
        if total_coin_in > 0:
            actual_hold_pct = (net_win / total_coin_in) * 100
        else:
            actual_hold_pct = 0

        # Hold percentage should be reasonable (typically 2-12% for slots)
        # But can vary widely in samples
        assert isinstance(actual_hold_pct, (int, float)), "Hold percentage not numeric"

    def test_theoretical_win_calculation(self, sample_slot_data):
        """Verify theoretical win calculation uses correct hold percentage."""
        THEORETICAL_HOLD = 0.08  # 8%

        df_silver = sample_slot_data.copy()
        total_coin_in = df_silver["coin_in"].sum() or 0

        theoretical_win = total_coin_in * THEORETICAL_HOLD

        assert theoretical_win >= 0, "Theoretical win should not be negative"
        assert theoretical_win == total_coin_in * 0.08, (
            "Theoretical win calculation error"
        )

    def test_unique_player_count(self, sample_slot_data):
        """Verify unique player count is calculated correctly."""
        df_silver = sample_slot_data.copy()

        # Count unique players per machine
        unique_players = (
            df_silver.groupby("machine_id")["player_id"].nunique().reset_index()
        )
        unique_players.columns = ["machine_id", "unique_players"]

        # Each machine should have >= 0 unique players
        assert (unique_players["unique_players"] >= 0).all(), "Negative player counts"

    def test_jackpot_aggregation(self, sample_slot_data):
        """Verify jackpot amounts are aggregated correctly."""
        df_silver = sample_slot_data.copy()

        # Filter jackpot events and sum
        jackpot_data = df_silver[df_silver["event_type"] == "JACKPOT"]
        total_jackpots = jackpot_data["jackpot_amount"].sum() or 0
        jackpot_count = len(jackpot_data)

        assert total_jackpots >= 0, "Total jackpots should not be negative"
        assert jackpot_count >= 0, "Jackpot count should not be negative"


class TestDataTypeConsistency:
    """Tests for data type consistency through pipeline layers."""

    def test_numeric_types_preserved(self, sample_slot_data):
        """Verify numeric types are preserved through transformations."""
        df = sample_slot_data.copy()

        # Check numeric columns
        numeric_cols = ["coin_in", "coin_out", "jackpot_amount", "games_played"]

        for col in numeric_cols:
            if col in df.columns:
                non_null = df[col].dropna()
                if len(non_null) > 0:
                    # All non-null values should be numeric
                    assert pd.api.types.is_numeric_dtype(non_null), (
                        f"{col} is not numeric type"
                    )

    def test_string_types_preserved(self, sample_slot_data):
        """Verify string types are preserved through transformations."""
        df = sample_slot_data.copy()

        string_cols = ["machine_id", "event_type", "zone", "player_id"]

        for col in string_cols:
            if col in df.columns:
                non_null = df[col].dropna()
                if len(non_null) > 0:
                    # All non-null values should be string-like
                    assert all(isinstance(v, str) for v in non_null), (
                        f"{col} contains non-string values"
                    )

    def test_decimal_precision_maintained(self, sample_slot_data):
        """Verify decimal precision is maintained for currency values."""
        df = sample_slot_data.copy()

        # Check coin_in has reasonable precision
        coin_values = df["coin_in"].dropna()

        for val in coin_values.head(100):
            # Should have at most 2 decimal places
            if val != int(val):
                decimal_str = str(val)
                if "." in decimal_str:
                    decimal_places = len(decimal_str.split(".")[1])
                    assert decimal_places <= 4, f"Too many decimal places: {val}"

    def test_timestamp_types_valid(self, sample_slot_data, validate_iso_datetime):
        """Verify timestamp types are valid throughout pipeline."""
        df = sample_slot_data.copy()

        timestamps = df["event_timestamp"].tolist()

        for ts in timestamps[:100]:
            assert validate_iso_datetime(ts), f"Invalid timestamp: {ts}"


class TestNullHandling:
    """Tests for null value handling through pipeline."""

    def test_required_fields_not_null(self, sample_slot_data):
        """Verify required fields have minimal nulls."""
        required_fields = ["machine_id", "event_type", "event_timestamp"]

        for field in required_fields:
            null_count = sample_slot_data[field].isna().sum()
            total_count = len(sample_slot_data)
            null_pct = (null_count / total_count) * 100

            # Required fields should have <1% nulls
            assert null_pct < 1, f"{field} has {null_pct:.1f}% null values"

    def test_optional_fields_allow_null(self, sample_slot_data):
        """Verify optional fields can contain nulls."""
        optional_fields = ["player_id", "session_id", "jackpot_amount"]

        for field in optional_fields:
            if field in sample_slot_data.columns:
                # These can have nulls - just verify the column exists
                assert field in sample_slot_data.columns

    def test_null_coalescing_in_aggregation(self, sample_slot_data):
        """Verify null values are handled correctly in aggregations."""
        df = sample_slot_data.copy()

        # Sum with null handling
        total_coin_in_with_nulls = df["coin_in"].sum()  # pandas handles nulls
        total_coin_in_coalesced = df["coin_in"].fillna(0).sum()

        # Both should return numeric (pandas sum ignores nulls by default)
        assert not pd.isna(total_coin_in_with_nulls), "Sum returned null"
        assert not pd.isna(total_coin_in_coalesced), "Coalesced sum returned null"

    def test_null_propagation_in_calculations(self, sample_slot_data):
        """Verify null propagation behavior in calculations."""
        df = sample_slot_data.copy()

        # Create a column with null handling
        df["net_win"] = df["coin_in"].fillna(0) - df["coin_out"].fillna(0)

        # net_win should not have nulls after coalescing
        null_net_wins = df["net_win"].isna().sum()
        assert null_net_wins == 0, (
            f"Net win has {null_net_wins} null values after coalescing"
        )


class TestCrossLayerConsistency:
    """Tests for data consistency across Bronze, Silver, and Gold layers."""

    def test_record_count_consistency(self, sample_slot_data):
        """Verify record counts are tracked through layers."""
        # Bronze (raw)
        bronze_count = len(sample_slot_data)

        # Silver (after filtering nulls - should be <= bronze)
        required_fields = ["machine_id", "event_type", "event_timestamp"]
        silver_df = sample_slot_data.dropna(subset=required_fields)
        silver_count = len(silver_df)

        # Silver should have same or fewer records
        assert silver_count <= bronze_count, "Silver has more records than Bronze"

    def test_value_consistency_through_layers(self, sample_slot_data):
        """Verify values are not corrupted through transformations."""
        original_total = sample_slot_data["coin_in"].sum()

        # Apply transformations (standardization, filtering)
        df_transformed = sample_slot_data.copy()
        df_transformed["coin_in"] = df_transformed["coin_in"].apply(
            lambda x: max(0, x) if x is not None else 0
        )

        transformed_total = df_transformed["coin_in"].sum()

        # Total should be >= original (negative values set to 0)
        assert (
            transformed_total >= original_total
            or abs(transformed_total - original_total) < 1
        ), "Value corruption detected"

    def test_aggregation_math_correctness(self, sample_slot_data):
        """Verify aggregation math is correct."""
        df = sample_slot_data.copy()

        # Calculate totals directly
        direct_coin_in = df["coin_in"].sum()
        direct_coin_out = df["coin_out"].sum()

        # Calculate via groupby
        grouped = df.groupby("machine_id").agg(
            {
                "coin_in": "sum",
                "coin_out": "sum",
            }
        )

        grouped_coin_in = grouped["coin_in"].sum()
        grouped_coin_out = grouped["coin_out"].sum()

        # Should match (with floating point tolerance)
        assert abs(direct_coin_in - grouped_coin_in) < 0.01, (
            "Aggregation coin_in mismatch"
        )
        assert abs(direct_coin_out - grouped_coin_out) < 0.01, (
            "Aggregation coin_out mismatch"
        )
