"""Run Great Expectations suites against sample CSV data (ephemeral context).

Uses an in-memory GX context so the committed yml (which has a schema quirk
for this version of GE) is not touched.
"""

import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import great_expectations as gx
import pandas as pd
from great_expectations.core.expectation_configuration import (
    ExpectationConfiguration,
)
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.expectations.registry import (
    get_expectation_impl,
)

ROOT = Path(__file__).parent
EXPECT_DIR = ROOT / "expectations"
SAMPLE = ROOT.parent.parent / "sample-data" / "bronze"

# Map each sample CSV to its primary suite
PAIRS = [
    ("slot_telemetry_sample.csv", "slot_machine_suite"),
    ("player_profile_sample.csv", "player_suite"),
    ("compliance_filings_sample.csv", "compliance_suite"),
    ("financial_transactions_sample.csv", "financial_suite"),
    ("security_events_sample.csv", "security_suite"),
    ("table_games_sample.csv", "table_games_suite"),
]


def load_suite(name: str) -> ExpectationSuite:
    path = EXPECT_DIR / f"{name}.json"
    data = json.loads(path.read_text())
    suite = ExpectationSuite(expectation_suite_name=name, meta=data.get("meta", {}))
    configs = []
    skipped = []
    for exp in data["expectations"]:
        etype = exp["expectation_type"]
        try:
            get_expectation_impl(etype)
        except Exception:
            skipped.append(etype)
            continue
        configs.append(
            ExpectationConfiguration(
                expectation_type=etype,
                kwargs=exp.get("kwargs", {}),
                meta=exp.get("meta", {}),
            )
        )
    suite.add_expectation_configurations(configs)
    return suite, skipped


context = gx.get_context(mode="ephemeral")
datasource = context.sources.add_pandas(name="pandas_runtime")

summary = []
for csv_name, suite_name in PAIRS:
    path = SAMPLE / csv_name
    if not path.exists():
        summary.append({"suite": suite_name, "file": csv_name, "status": "missing"})
        continue

    df = pd.read_csv(path, engine="python", on_bad_lines="skip")
    suite, skipped_types = load_suite(suite_name)
    context.add_or_update_expectation_suite(expectation_suite=suite)

    asset_name = csv_name.replace(".csv", "")
    try:
        asset = datasource.add_dataframe_asset(name=asset_name)
    except Exception:
        asset = datasource.get_asset(asset_name)
    batch_request = asset.build_batch_request(dataframe=df)

    validator = context.get_validator(
        batch_request=batch_request, expectation_suite_name=suite_name
    )
    result = validator.validate(result_format="BASIC")
    stats = result.statistics

    summary.append(
        {
            "suite": suite_name,
            "file": csv_name,
            "rows": len(df),
            "success": result.success,
            "evaluated": stats.get("evaluated_expectations"),
            "successful": stats.get("successful_expectations"),
            "unsuccessful": stats.get("unsuccessful_expectations"),
            "success_percent": round(stats.get("success_percent", 0), 1),
            "skipped_unknown_types": skipped_types,
            "failed": [
                {
                    "type": r.expectation_config.expectation_type,
                    "column": r.expectation_config.kwargs.get("column"),
                    "unexpected_count": (r.result or {}).get("unexpected_count", 0),
                }
                for r in result.results
                if not r.success
            ][:8],
        }
    )

print(json.dumps(summary, indent=2, default=str))

total = len(summary)
passed = sum(1 for s in summary if s.get("success"))
print(f"\n=== Overall: {passed}/{total} suites passed ===", file=sys.stderr)
sys.exit(0 if passed == total else 1)
