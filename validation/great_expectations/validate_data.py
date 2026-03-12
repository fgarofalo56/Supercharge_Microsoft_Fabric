"""
Great Expectations Validation Runner
Casino Fabric POC - Data Quality Validation Utilities

This module provides helper functions for running data quality validations
across all casino data domains using Great Expectations.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import great_expectations as gx
    from great_expectations.checkpoint import Checkpoint
    from great_expectations.core.batch import RuntimeBatchRequest
except ImportError:
    print("Great Expectations not installed. Run: pip install great_expectations")
    sys.exit(1)

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent


class CasinoDataValidator:
    """
    Validator class for casino data quality checks.

    Supports validation of:
    - Slot machine telemetry
    - Player profiles
    - Compliance filings (CTR, SAR, W-2G)
    - Financial transactions
    - Security events
    - Table games events
    """

    # Available expectation suites
    SUITES = {
        "slot_machine": "slot_machine_suite",
        "player": "player_suite",
        "compliance": "compliance_suite",
        "compliance_ctr": "compliance_ctr_conditional_suite",
        "compliance_w2g": "compliance_w2g_conditional_suite",
        "compliance_sar": "compliance_sar_conditional_suite",
        "financial": "financial_suite",
        "security": "security_suite",
        "table_games": "table_games_suite",
        "bronze_slot": "bronze_slot_telemetry_suite",
        "silver_slot": "silver_slot_cleansed_suite",
        "gold_slot": "gold_slot_performance_suite",
    }

    # Available checkpoints
    CHECKPOINTS = {
        "slot_machine": "slot_machine_checkpoint",
        "player": "player_checkpoint",
        "compliance": "compliance_checkpoint",
        "financial": "financial_checkpoint",
        "security": "security_checkpoint",
        "table_games": "table_games_checkpoint",
        "all_domains": "all_domains_checkpoint",
    }

    def __init__(self, context_root_dir: str | None = None):
        """
        Initialize the validator with Great Expectations context.

        Args:
            context_root_dir: Path to the GX context root. Defaults to script directory.
        """
        self.context_root_dir = context_root_dir or str(SCRIPT_DIR)
        self.context = gx.get_context(context_root_dir=self.context_root_dir)

    def list_available_suites(self) -> list[str]:
        """List all available expectation suites."""
        return list(self.SUITES.keys())

    def list_available_checkpoints(self) -> list[str]:
        """List all available checkpoints."""
        return list(self.CHECKPOINTS.keys())

    def validate_dataframe(
        self,
        df: Any,
        suite_name: str,
        data_asset_name: str = "validation_data",
        run_name: str | None = None,
        result_format: str = "COMPLETE",
    ) -> dict[str, Any]:
        """
        Validate a DataFrame against an expectation suite.

        Args:
            df: Pandas or Spark DataFrame to validate
            suite_name: Name of the suite (use keys from SUITES dict)
            data_asset_name: Name for the data asset
            run_name: Optional run name for tracking
            result_format: Result format (SUMMARY, BASIC, COMPLETE)

        Returns:
            Dictionary with validation results
        """
        suite_full_name = self.SUITES.get(suite_name, suite_name)

        if run_name is None:
            run_name = f"{suite_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Determine datasource based on DataFrame type
        try:
            import pandas as pd

            if isinstance(df, pd.DataFrame):
                datasource_name = "casino_pandas"
            else:
                datasource_name = "casino_delta"
        except ImportError:
            datasource_name = "casino_delta"

        # Create batch request
        batch_request = RuntimeBatchRequest(
            datasource_name=datasource_name,
            data_connector_name="runtime_data_connector",
            data_asset_name=data_asset_name,
            runtime_parameters={"batch_data": df},
            batch_identifiers={"default_identifier_name": run_name},
        )

        # Get validator
        validator = self.context.get_validator(
            batch_request=batch_request, expectation_suite_name=suite_full_name
        )

        # Run validation
        results = validator.validate(result_format=result_format)

        return self._format_results(results)

    def run_checkpoint(
        self,
        checkpoint_name: str,
        batch_data: Any | None = None,
        run_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Run a validation checkpoint.

        Args:
            checkpoint_name: Name of the checkpoint (use keys from CHECKPOINTS dict)
            batch_data: Optional DataFrame to validate
            run_name: Optional run name for tracking

        Returns:
            Dictionary with checkpoint results
        """
        checkpoint_full_name = self.CHECKPOINTS.get(checkpoint_name, checkpoint_name)

        if run_name is None:
            run_name = f"{checkpoint_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Run checkpoint
        if batch_data is not None:
            # Runtime batch
            batch_request = RuntimeBatchRequest(
                datasource_name="casino_pandas",
                data_connector_name="runtime_data_connector",
                data_asset_name="runtime_data",
                runtime_parameters={"batch_data": batch_data},
                batch_identifiers={"default_identifier_name": run_name},
            )

            results = self.context.run_checkpoint(
                checkpoint_name=checkpoint_full_name, batch_request=batch_request
            )
        else:
            results = self.context.run_checkpoint(checkpoint_name=checkpoint_full_name)

        return {
            "success": results.success,
            "run_name": run_name,
            "checkpoint": checkpoint_full_name,
            "validation_results": [
                self._format_results(r) for r in results.run_results.values()
            ],
        }

    def validate_compliance_filing(
        self, df: Any, filing_type: str | None = None
    ) -> dict[str, Any]:
        """
        Validate compliance filing data with type-specific rules.

        Args:
            df: DataFrame with compliance filings
            filing_type: Optional filter for CTR, SAR, or W2G

        Returns:
            Validation results
        """
        # Use appropriate suite based on filing type
        if filing_type:
            suite_map = {
                "CTR": "compliance_ctr",
                "SAR": "compliance_sar",
                "W2G": "compliance_w2g",
            }
            suite = suite_map.get(filing_type.upper(), "compliance")
        else:
            suite = "compliance"

        return self.validate_dataframe(
            df=df,
            suite_name=suite,
            data_asset_name=f"compliance_{filing_type or 'all'}",
        )

    def validate_ctr_threshold(self, df: Any) -> dict[str, Any]:
        """
        Validate CTR filings meet the $10,000 threshold.

        Args:
            df: DataFrame with CTR filings

        Returns:
            Validation results
        """
        return self.validate_dataframe(
            df=df, suite_name="compliance_ctr", data_asset_name="ctr_threshold_check"
        )

    def validate_w2g_threshold(self, df: Any) -> dict[str, Any]:
        """
        Validate W-2G filings meet the $600 threshold.

        Args:
            df: DataFrame with W-2G filings

        Returns:
            Validation results
        """
        return self.validate_dataframe(
            df=df, suite_name="compliance_w2g", data_asset_name="w2g_threshold_check"
        )

    def build_data_docs(self) -> str:
        """
        Build and return the path to Data Docs.

        Returns:
            Path to the generated Data Docs index
        """
        self.context.build_data_docs()
        docs_path = (
            Path(self.context_root_dir)
            / "uncommitted"
            / "data_docs"
            / "local_site"
            / "index.html"
        )
        return str(docs_path)

    def _format_results(self, results: Any) -> dict[str, Any]:
        """Format validation results into a clean dictionary."""
        return {
            "success": results.success,
            "statistics": results.statistics,
            "results": [
                {
                    "expectation": r.expectation_config.expectation_type,
                    "success": r.success,
                    "column": r.expectation_config.kwargs.get("column"),
                    "unexpected_count": (
                        r.result.get("unexpected_count", 0) if r.result else 0
                    ),
                    "unexpected_percent": (
                        r.result.get("unexpected_percent", 0) if r.result else 0
                    ),
                }
                for r in results.results
            ],
        }


def validate_all_domains(data_dir: str) -> dict[str, Any]:
    """
    Validate all data domains from a directory.

    Args:
        data_dir: Directory containing data files

    Returns:
        Combined validation results
    """
    import pandas as pd

    validator = CasinoDataValidator()
    results = {}

    # Map file patterns to suites
    file_suite_map = {
        "slot": "slot_machine",
        "player": "player",
        "compliance": "compliance",
        "financial": "financial",
        "security": "security",
        "table": "table_games",
    }

    data_path = Path(data_dir)

    for pattern, suite in file_suite_map.items():
        # Find matching files
        files = list(data_path.glob(f"*{pattern}*.parquet")) + list(
            data_path.glob(f"*{pattern}*.csv")
        )

        for file_path in files:
            print(f"Validating {file_path.name} with {suite} suite...")

            try:
                if file_path.suffix == ".parquet":
                    df = pd.read_parquet(file_path)
                else:
                    df = pd.read_csv(file_path)

                result = validator.validate_dataframe(
                    df=df, suite_name=suite, data_asset_name=file_path.stem
                )

                results[file_path.name] = result

            except Exception as e:
                results[file_path.name] = {"success": False, "error": str(e)}

    return results


def main():
    """Main entry point for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Casino Data Quality Validator")
    parser.add_argument(
        "--checkpoint",
        choices=CasinoDataValidator.CHECKPOINTS.keys(),
        help="Run a specific checkpoint",
    )
    parser.add_argument(
        "--suite",
        choices=CasinoDataValidator.SUITES.keys(),
        help="Validate using a specific suite",
    )
    parser.add_argument("--data-file", type=str, help="Path to data file to validate")
    parser.add_argument(
        "--data-dir", type=str, help="Directory with data files to validate"
    )
    parser.add_argument(
        "--build-docs", action="store_true", help="Build Data Docs after validation"
    )
    parser.add_argument(
        "--list-suites", action="store_true", help="List available expectation suites"
    )
    parser.add_argument(
        "--list-checkpoints", action="store_true", help="List available checkpoints"
    )

    args = parser.parse_args()

    validator = CasinoDataValidator()

    if args.list_suites:
        print("Available Expectation Suites:")
        for suite in validator.list_available_suites():
            print(f"  - {suite}")
        return

    if args.list_checkpoints:
        print("Available Checkpoints:")
        for cp in validator.list_available_checkpoints():
            print(f"  - {cp}")
        return

    if args.data_dir:
        results = validate_all_domains(args.data_dir)
        print(json.dumps(results, indent=2, default=str))

    elif args.checkpoint:
        results = validator.run_checkpoint(args.checkpoint)
        print(json.dumps(results, indent=2, default=str))

    elif args.suite and args.data_file:
        import pandas as pd

        if args.data_file.endswith(".parquet"):
            df = pd.read_parquet(args.data_file)
        else:
            df = pd.read_csv(args.data_file)

        results = validator.validate_dataframe(df, args.suite)
        print(json.dumps(results, indent=2, default=str))

    if args.build_docs:
        docs_path = validator.build_data_docs()
        print(f"\nData Docs generated at: {docs_path}")


if __name__ == "__main__":
    main()
