"""
Tutorial 57 — Sample Data Orchestrator
======================================

Runs both generators and writes parquet + CSV outputs into
sample-data/57-better-together/ ready to be uploaded into Databricks UC
volumes (or directly into a Fabric Lakehouse Files area for the
non-Databricks path).

Usage:
    python tutorials/57-databricks-better-together/scripts/generate_sample_data.py

Outputs:
    sample-data/57-better-together/
        retail/
            customers.parquet
            products.parquet
            orders.parquet
            order_lines.parquet
            returns.parquet
        personas/
            users.csv
            groups.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make the script runnable from any working directory by adding the repo
# root (4 levels up from this file) to sys.path. No-op when already on path.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from data_generation.generators.better_together import (  # noqa: E402
    BetterTogetherRetailGenerator,
    UserPersonaGenerator,
)


def main(output_root: Path, seed: int) -> None:
    retail_root = output_root / "retail"
    persona_root = output_root / "personas"
    retail_root.mkdir(parents=True, exist_ok=True)
    persona_root.mkdir(parents=True, exist_ok=True)

    print(f"[Tutorial 57] Writing retail dataset to {retail_root}")
    retail = BetterTogetherRetailGenerator(seed=seed).generate_all()
    for name, df in retail.items():
        path = retail_root / f"{name}.parquet"
        # coerce_timestamps='us' is required for Spark/Delta — Spark cannot
        # ingest the nanosecond timestamps that pyarrow writes by default
        # (Illegal Parquet type: INT64 (TIMESTAMP(NANOS,false))).
        df.to_parquet(
            path,
            engine="pyarrow",
            index=False,
            coerce_timestamps="us",
            allow_truncated_timestamps=True,
        )
        print(f"  - {name:<14} {len(df):>7,} rows  -> {path.name}")

    print(f"[Tutorial 57] Writing persona seed data to {persona_root}")
    personas = UserPersonaGenerator(seed=seed).generate_all()
    for name, df in personas.items():
        path = persona_root / f"{name}.csv"
        df.to_csv(path, index=False)
        print(f"  - {name:<14} {len(df):>7,} rows  -> {path.name}")

    print("[Tutorial 57] Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("sample-data/57-better-together"),
        help="Output root directory (default: sample-data/57-better-together).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=57,
        help="Random seed (default: 57, matches tutorial number).",
    )
    args = parser.parse_args()
    main(args.output, args.seed)
