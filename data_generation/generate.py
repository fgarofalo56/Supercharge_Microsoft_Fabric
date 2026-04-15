#!/usr/bin/env python3
"""Data Generation CLI.

Generates synthetic casino/gaming + federal/analytics data for the Fabric POC.

Usage examples::

    python generate.py --all --days 30 --output ./output
    python generate.py --slots 10000 --players 1000
    python generate.py --federal usda,sba --output ./output
    python generate.py --analytics --output ./output
"""

from __future__ import annotations

import argparse
import os
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

# Federal and analytics generators are optional -- import lazily so the CLI
# still runs with only the casino core installed.
try:
    from generators.federal import (  # type: ignore[attr-defined]
        DOIGenerator,
        DOTFAAGenerator,
        EPAGenerator,
        NOAAGenerator,
        SBAGenerator,
        TribalHealthcareGenerator,
        USDAGenerator,
    )
    FEDERAL_AVAILABLE = True
except ImportError:
    FEDERAL_AVAILABLE = False

try:
    from generators.analytics import (  # type: ignore[attr-defined]
        GeolocationGenerator,
        PeopleMovementGenerator,
        VideoAnalyticsGenerator,
    )
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False


FEDERAL_GENERATORS: dict[str, tuple[str, type]] = {
    # key: (output_filename_stem, generator_class)
}
if FEDERAL_AVAILABLE:
    FEDERAL_GENERATORS = {
        "usda": ("bronze_usda_crop_production", USDAGenerator),
        "sba": ("bronze_sba_loans", SBAGenerator),
        "noaa": ("bronze_noaa_climate", NOAAGenerator),
        "epa": ("bronze_epa_air_quality", EPAGenerator),
        "doi": ("bronze_doi_earthquakes", DOIGenerator),
        "dot_faa": ("bronze_dot_flight_ops", DOTFAAGenerator),
        "tribal_healthcare": ("bronze_tribal_healthcare", TribalHealthcareGenerator),
    }

ANALYTICS_GENERATORS: dict[str, tuple[str, type]] = {}
if ANALYTICS_AVAILABLE:
    ANALYTICS_GENERATORS = {
        "geolocation": ("bronze_geolocation", GeolocationGenerator),
        "people_movement": ("bronze_people_movement", PeopleMovementGenerator),
        "video_analytics": ("bronze_video_analytics", VideoAnalyticsGenerator),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--output", "-o", type=str, default="./output", help="Output directory (default: ./output)")
    p.add_argument("--format", "-f", choices=["parquet", "json", "csv"], default="parquet", help="Output format (default: parquet)")
    p.add_argument("--days", "-d", type=int, default=30, help="Days of history (default: 30)")
    p.add_argument("--seed", "-s", type=int, default=42, help="Random seed (default: 42)")

    # Casino generators
    p.add_argument("--all", "-a", action="store_true", help="Generate every casino data type at default volumes")
    p.add_argument("--slots", type=int, help="Slot machine event count")
    p.add_argument("--tables", type=int, help="Table game event count")
    p.add_argument("--players", type=int, help="Player profile count")
    p.add_argument("--financial", type=int, help="Financial transaction count")
    p.add_argument("--security", type=int, help="Security event count")
    p.add_argument("--compliance", type=int, help="Compliance record count")
    p.add_argument("--include-pii", action="store_true", help="Include unhashed PII (testing only)")

    # Federal generators
    federal_choices = ",".join(sorted(FEDERAL_GENERATORS)) if FEDERAL_GENERATORS else "(none installed)"
    p.add_argument(
        "--federal",
        type=str,
        default="",
        help=f"Comma-separated federal generators to run, or 'all'. Available: {federal_choices}",
    )
    p.add_argument("--federal-records", type=int, default=5000, help="Records per federal generator (default: 5000)")

    # Analytics generators
    analytics_choices = ",".join(sorted(ANALYTICS_GENERATORS)) if ANALYTICS_GENERATORS else "(none installed)"
    p.add_argument(
        "--analytics",
        type=str,
        nargs="?",
        const="all",
        default="",
        help=f"Run analytics generators. Pass comma list or 'all'. Available: {analytics_choices}",
    )
    p.add_argument("--analytics-records", type=int, default=10000, help="Records per analytics generator (default: 10000)")

    return p.parse_args()


def _save(df, filepath: Path, fmt: str) -> None:
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "parquet":
        df.to_parquet(filepath, engine="pyarrow", index=False)
    elif fmt == "json":
        df.to_json(filepath, orient="records", lines=True, date_format="iso")
    elif fmt == "csv":
        df.to_csv(filepath, index=False)
    else:
        raise ValueError(f"unsupported format {fmt}")
    print(f"  Saved: {filepath.name} ({filepath.stat().st_size / 1e6:.2f} MB)")


def _emit(name: str, gen, count: int, output_dir: Path, fmt: str, summary: list) -> None:
    print(f"\nGenerating {count:,} {name} records...")
    df = gen.generate(count)
    _save(df, output_dir / f"{name}.{fmt}", fmt)
    summary.append((name, count, df.memory_usage(deep=True).sum() / 1e6))


def _parse_subset(selection: str, universe: dict) -> list[str]:
    if not selection:
        return []
    if selection.lower() == "all":
        return list(universe)
    return [s.strip() for s in selection.split(",") if s.strip()]


def generate_data(args: argparse.Namespace) -> None:
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    print(f"Generating data {start_date.date()} -> {end_date.date()}")
    print(f"Output: {output_dir.absolute()}  format={args.format}")
    print("-" * 60)

    # Any PII generator requires the hash-salt env var.
    if not os.environ.get("FABRIC_POC_HASH_SALT"):
        os.environ["FABRIC_POC_HASH_SALT"] = "ci-only-placeholder-not-for-production"
        print("WARNING: FABRIC_POC_HASH_SALT not set; using ephemeral placeholder.")

    default_casino_volumes = {
        "slots": 500_000,
        "tables": 100_000,
        "players": 10_000,
        "financial": 50_000,
        "security": 25_000,
        "compliance": 10_000,
    }
    summary: list[tuple[str, int, float]] = []

    def gen_casino(name: str, cls, flag_value, default_count, extra_kwargs=None):
        if not (args.all or flag_value):
            return
        count = flag_value or default_count
        kw = dict(seed=args.seed, start_date=start_date, end_date=end_date)
        if extra_kwargs:
            kw.update(extra_kwargs)
        _emit(f"bronze_{name}", cls(**kw), count, output_dir, args.format, summary)

    gen_casino("slot_telemetry",     SlotMachineGenerator, args.slots,      default_casino_volumes["slots"])
    gen_casino("table_games",        TableGameGenerator,   args.tables,     default_casino_volumes["tables"])
    gen_casino("player_profile",     PlayerGenerator,      args.players,    default_casino_volumes["players"], {"include_pii": args.include_pii})
    gen_casino("financial_txn",      FinancialGenerator,   args.financial,  default_casino_volumes["financial"])
    gen_casino("security_events",    SecurityGenerator,    args.security,   default_casino_volumes["security"])
    gen_casino("compliance_filings", ComplianceGenerator,  args.compliance, default_casino_volumes["compliance"])

    # Federal
    federal_subset = _parse_subset(args.federal, FEDERAL_GENERATORS)
    if federal_subset and not FEDERAL_AVAILABLE:
        print("ERROR: --federal selected but federal generators not installed", file=sys.stderr)
        sys.exit(2)
    for key in federal_subset:
        if key not in FEDERAL_GENERATORS:
            print(f"WARNING: unknown federal generator {key!r}; available: {sorted(FEDERAL_GENERATORS)}", file=sys.stderr)
            continue
        stem, cls = FEDERAL_GENERATORS[key]
        _emit(stem, cls(seed=args.seed, start_date=start_date, end_date=end_date), args.federal_records, output_dir, args.format, summary)

    # Analytics
    analytics_subset = _parse_subset(args.analytics, ANALYTICS_GENERATORS)
    if analytics_subset and not ANALYTICS_AVAILABLE:
        print("ERROR: --analytics selected but analytics generators not installed", file=sys.stderr)
        sys.exit(2)
    for key in analytics_subset:
        if key not in ANALYTICS_GENERATORS:
            print(f"WARNING: unknown analytics generator {key!r}; available: {sorted(ANALYTICS_GENERATORS)}", file=sys.stderr)
            continue
        stem, cls = ANALYTICS_GENERATORS[key]
        _emit(stem, cls(seed=args.seed, start_date=start_date, end_date=end_date), args.analytics_records, output_dir, args.format, summary)

    _print_summary(summary, output_dir)


def _print_summary(summary: list[tuple[str, int, float]], output_dir: Path) -> None:
    if not summary:
        print("\nNo data generated. Pass --all, --federal, --analytics or an individual flag.")
        print("See --help for options.")
        return
    print("\n" + "=" * 60)
    print("GENERATION SUMMARY")
    print("=" * 60)
    total_records, total_size = 0, 0.0
    for name, count, size in summary:
        print(f"{name:35} {count:>12,}  {size:>8.2f} MB")
        total_records += count
        total_size += size
    print("-" * 60)
    print(f"{'TOTAL':35} {total_records:>12,}  {total_size:>8.2f} MB")
    print(f"\nFiles saved to: {output_dir.absolute()}")


def main() -> int:
    args = parse_args()
    try:
        generate_data(args)
        return 0
    except KeyboardInterrupt:
        print("\nGeneration cancelled by user.")
        return 1
    except Exception as exc:  # pragma: no cover
        print(f"\nError during generation: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
