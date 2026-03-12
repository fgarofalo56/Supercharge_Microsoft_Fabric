#!/usr/bin/env python3
"""
Data Generation CLI
===================

Command-line interface for generating synthetic casino/gaming data.

Usage:
    python generate.py --all --days 30 --output ./output
    python generate.py --slots 10000 --players 1000
    python generate.py --compliance 5000 --output ./data
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

from generators import (
    ComplianceGenerator,
    FinancialGenerator,
    PlayerGenerator,
    SecurityGenerator,
    SlotMachineGenerator,
    TableGameGenerator,
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic casino/gaming data for Microsoft Fabric POC"
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="./output",
        help="Output directory for generated data (default: ./output)",
    )

    parser.add_argument(
        "--format",
        "-f",
        type=str,
        choices=["parquet", "json", "csv"],
        default="parquet",
        help="Output format (default: parquet)",
    )

    parser.add_argument(
        "--days",
        "-d",
        type=int,
        default=30,
        help="Number of days of historical data (default: 30)",
    )

    parser.add_argument(
        "--seed",
        "-s",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )

    # Data volume flags
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Generate all data types with default volumes",
    )

    parser.add_argument(
        "--slots", type=int, help="Number of slot machine events to generate"
    )

    parser.add_argument(
        "--tables", type=int, help="Number of table game events to generate"
    )

    parser.add_argument(
        "--players", type=int, help="Number of player profiles to generate"
    )

    parser.add_argument(
        "--financial", type=int, help="Number of financial transactions to generate"
    )

    parser.add_argument(
        "--security", type=int, help="Number of security events to generate"
    )

    parser.add_argument(
        "--compliance", type=int, help="Number of compliance records to generate"
    )

    parser.add_argument(
        "--include-pii",
        action="store_true",
        help="Include unhashed PII (for testing only)",
    )

    return parser.parse_args()


def generate_data(args):
    """Generate data based on command line arguments."""
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)

    print(f"Generating data from {start_date.date()} to {end_date.date()}")
    print(f"Output directory: {output_dir.absolute()}")
    print(f"Output format: {args.format}")
    print("-" * 50)

    # Default volumes for --all flag
    default_volumes = {
        "slots": 500000,
        "tables": 100000,
        "players": 10000,
        "financial": 50000,
        "security": 25000,
        "compliance": 10000,
    }

    generated = []

    # Slot Machine Events
    if args.all or args.slots:
        count = args.slots or default_volumes["slots"]
        print(f"\nGenerating {count:,} slot machine events...")

        gen = SlotMachineGenerator(
            seed=args.seed,
            start_date=start_date,
            end_date=end_date,
        )
        df = gen.generate(count)
        save_data(df, output_dir / f"bronze_slot_telemetry.{args.format}", args.format)
        generated.append(
            ("Slot Machine Events", count, df.memory_usage(deep=True).sum() / 1e6)
        )

    # Table Game Events
    if args.all or args.tables:
        count = args.tables or default_volumes["tables"]
        print(f"\nGenerating {count:,} table game events...")

        gen = TableGameGenerator(
            seed=args.seed,
            start_date=start_date,
            end_date=end_date,
        )
        df = gen.generate(count)
        save_data(df, output_dir / f"bronze_table_games.{args.format}", args.format)
        generated.append(
            ("Table Game Events", count, df.memory_usage(deep=True).sum() / 1e6)
        )

    # Player Profiles
    if args.all or args.players:
        count = args.players or default_volumes["players"]
        print(f"\nGenerating {count:,} player profiles...")

        gen = PlayerGenerator(
            seed=args.seed,
            include_pii=args.include_pii,
            start_date=start_date,
            end_date=end_date,
        )
        df = gen.generate(count)
        save_data(df, output_dir / f"bronze_player_profile.{args.format}", args.format)
        generated.append(
            ("Player Profiles", count, df.memory_usage(deep=True).sum() / 1e6)
        )

    # Financial Transactions
    if args.all or args.financial:
        count = args.financial or default_volumes["financial"]
        print(f"\nGenerating {count:,} financial transactions...")

        gen = FinancialGenerator(
            seed=args.seed,
            start_date=start_date,
            end_date=end_date,
        )
        df = gen.generate(count)
        save_data(df, output_dir / f"bronze_financial_txn.{args.format}", args.format)
        generated.append(
            ("Financial Transactions", count, df.memory_usage(deep=True).sum() / 1e6)
        )

    # Security Events
    if args.all or args.security:
        count = args.security or default_volumes["security"]
        print(f"\nGenerating {count:,} security events...")

        gen = SecurityGenerator(
            seed=args.seed,
            start_date=start_date,
            end_date=end_date,
        )
        df = gen.generate(count)
        save_data(df, output_dir / f"bronze_security_events.{args.format}", args.format)
        generated.append(
            ("Security Events", count, df.memory_usage(deep=True).sum() / 1e6)
        )

    # Compliance Records
    if args.all or args.compliance:
        count = args.compliance or default_volumes["compliance"]
        print(f"\nGenerating {count:,} compliance records...")

        gen = ComplianceGenerator(
            seed=args.seed,
            start_date=start_date,
            end_date=end_date,
        )
        df = gen.generate(count)
        save_data(df, output_dir / f"bronze_compliance.{args.format}", args.format)
        generated.append(
            ("Compliance Records", count, df.memory_usage(deep=True).sum() / 1e6)
        )

    # Print summary
    if generated:
        print("\n" + "=" * 50)
        print("GENERATION SUMMARY")
        print("=" * 50)
        total_records = 0
        total_size = 0
        for name, count, size in generated:
            print(f"{name:25} {count:>12,} records  {size:>8.2f} MB")
            total_records += count
            total_size += size
        print("-" * 50)
        print(f"{'TOTAL':25} {total_records:>12,} records  {total_size:>8.2f} MB")
        print(f"\nFiles saved to: {output_dir.absolute()}")
    else:
        print("\nNo data generated. Use --all or specify data types to generate.")
        print("Run with --help for usage information.")


def save_data(df, filepath, format_type):
    """Save DataFrame to specified format."""
    filepath = Path(filepath)

    if format_type == "parquet":
        df.to_parquet(filepath, engine="pyarrow", index=False)
    elif format_type == "json":
        df.to_json(filepath, orient="records", lines=True, date_format="iso")
    elif format_type == "csv":
        df.to_csv(filepath, index=False)

    print(f"  Saved: {filepath.name} ({filepath.stat().st_size / 1e6:.2f} MB)")


def main():
    """Main entry point."""
    args = parse_args()

    try:
        generate_data(args)
    except KeyboardInterrupt:
        print("\nGeneration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during generation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
