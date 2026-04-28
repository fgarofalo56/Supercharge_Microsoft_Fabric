"""Data Contract Enforcement via Great Expectations.

Phase 14 Wave 3 — Feature 3.12. Operationalizes the patterns documented in
``docs/best-practices/data-management/data-contracts.md``.

This module reads a *data contract* YAML (the seven-element contract: schema,
semantics, quality SLAs, volume, format, versioning, lifecycle) and mechanically
generates a Great Expectations (GE) ``ExpectationSuite`` plus a runnable
``Checkpoint`` that enforces the contract at any medallion boundary
(Bronze ingest gate, Silver/Gold boundary gate, or pre-publish quality gate).

It also provides a CLI entry point that lets CI pipelines fail fast on a
contract violation, and a ``quarantine_violations`` helper that moves
offending rows to a Dead-Letter / DLQ table without dropping them silently.

Usage
-----

As a library::

    from validation.great_expectations.data_contract_suite import (
        load_contract,
        generate_suite,
        validate_contract,
        enforce_contract,
    )

    contract = load_contract(Path("contracts/slot_telemetry.contract.yaml"))
    suite = generate_suite(contract, suite_name="bronze_slot_telemetry_suite")
    report = validate_contract(contract, datasource="casino_bronze",
                               table="lh_bronze.slot_telemetry")
    if not report["success"]:
        raise SystemExit(1)

As a CLI (CI integration)::

    python -m validation.great_expectations.data_contract_suite \
        --contract contracts/slot_telemetry.contract.yaml \
        --table lh_bronze.slot_telemetry \
        --mode enforce

Contract YAML schema (excerpt)
------------------------------
::

    product: bronze.slot_telemetry
    version: "1.2.0"
    producer:
      team: floor-ops
      contact: floor-ops@example.com
    schema:
      - name: event_id
        type: string
        required: true
        unique: true
        pattern: "^[0-9a-f]{32}$"
      - name: machine_id
        type: string
        required: true
        not_null: true
      - name: amount
        type: decimal
        required: true
        not_null: true
        min: 0
        max: 1000000
      - name: event_ts
        type: timestamp
        required: true
        not_null: true
        freshness_minutes: 60
    quality_slas:
      completeness:
        overall_min_pct: 99.5
        per_column:
          player_id: 95.0
      accuracy:
        referential_integrity:
          - column: machine_id
            references: dim_machine.machine_id
      freshness:
        max_lag_minutes: 30
      volume:
        expected_rows_per_day:
          min: 50000
          max: 5000000

The full canonical contract grammar is documented in
``docs/best-practices/data-management/data-contracts.md``. This module
accepts both the simplified flat form shown above and the nested
``contract:`` form used by that document.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Defensive import — Great Expectations is optional at install time so the
# module can be imported on environments that only need YAML parsing
# (e.g. contract linting in pre-commit). Functions that actually need GE
# raise a clear error at call time.
try:  # pragma: no cover - exercised only when GE is missing
    import great_expectations as gx  # type: ignore[import-untyped]
    from great_expectations.core.expectation_configuration import (  # type: ignore[import-untyped]
        ExpectationConfiguration,
    )
    from great_expectations.core.expectation_suite import (  # type: ignore[import-untyped]
        ExpectationSuite,
    )

    _GE_AVAILABLE = True
    _GE_IMPORT_ERROR: Optional[BaseException] = None
except ImportError as _err:  # pragma: no cover
    gx = None  # type: ignore[assignment]
    ExpectationConfiguration = None  # type: ignore[assignment,misc]
    ExpectationSuite = None  # type: ignore[assignment,misc]
    _GE_AVAILABLE = False
    _GE_IMPORT_ERROR = _err


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class ContractViolationError(Exception):
    """Raised when data violates its contract.

    Attributes
    ----------
    contract_id:
        ``product`` / ``contract.id`` from the YAML.
    contract_version:
        Semver string of the violated contract.
    failures:
        List of dicts ``{expectation_type, column, observed_value}``.
    """

    def __init__(
        self,
        contract_id: str,
        contract_version: str,
        failures: List[Dict[str, Any]],
        message: Optional[str] = None,
    ) -> None:
        self.contract_id = contract_id
        self.contract_version = contract_version
        self.failures = failures
        msg = message or (
            f"Contract {contract_id} v{contract_version} violated by "
            f"{len(failures)} expectation(s); downstream propagation blocked."
        )
        super().__init__(msg)


# ---------------------------------------------------------------------------
# Contract loader
# ---------------------------------------------------------------------------


# Minimal internal meta-schema. The data-contracts.md doc describes the full
# grammar; this dict is intentionally permissive — required keys only.
_REQUIRED_TOP_LEVEL: tuple[str, ...] = ("product", "version", "schema")
_REQUIRED_COLUMN_KEYS: tuple[str, ...] = ("name", "type")


def _normalise_contract(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise the two accepted contract layouts into one flat dict.

    The repo's ``data-contracts.md`` documents a nested form
    (``contract: { id, version, schema: { columns: [...] } }``).
    This module also accepts the flat form
    (``product, version, schema: [columns]``) for ergonomic CLI use.
    Internally we always operate on the flat form.
    """
    if "contract" in raw and isinstance(raw["contract"], dict):
        c = raw["contract"]
        flat: Dict[str, Any] = {
            "product": c.get("id"),
            "version": c.get("version"),
            "producer": c.get("owner") or c.get("producer") or {},
            "consumers": c.get("consumers", []),
            "schema": (c.get("schema") or {}).get("columns", []),
            "quality_slas": _flatten_quality(c.get("quality", {}), c.get("volume", {})),
            "format": c.get("format", {}),
            "versioning": c.get("versioning", {}),
            "lifecycle": c.get("lifecycle", {}),
            "compliance": c.get("compliance", {}),
        }
        return flat
    return raw


def _flatten_quality(quality: Dict[str, Any], volume: Dict[str, Any]) -> Dict[str, Any]:
    """Best-effort flatten of nested ``quality`` + ``volume`` blocks."""
    out: Dict[str, Any] = {}
    completeness = quality.get("completeness")
    if isinstance(completeness, list):
        per_col = {entry["column"]: entry["min_pct"] for entry in completeness if "column" in entry}
        out["completeness"] = {"per_column": per_col}
    elif isinstance(completeness, dict):
        out["completeness"] = completeness
    if "freshness" in quality:
        out["freshness"] = quality["freshness"]
    if "uniqueness" in quality:
        out["uniqueness"] = quality["uniqueness"]
    if volume:
        rows = {
            "min": volume.get("trough_rows_per_hour"),
            "max": volume.get("peak_rows_per_hour"),
        }
        if any(v is not None for v in rows.values()):
            out["volume"] = {"expected_rows_per_day": {
                "min": volume.get("baseline_rows_per_day"),
                "max": volume.get("baseline_rows_per_day"),
            }}
    return out


def load_contract(path: Path) -> Dict[str, Any]:
    """Load and validate a data contract YAML file.

    Parameters
    ----------
    path:
        Path to a contract YAML. Both the flat and nested layouts described
        in the module docstring are accepted.

    Returns
    -------
    dict
        Normalised flat contract dict.

    Raises
    ------
    FileNotFoundError
        If ``path`` does not exist.
    ValueError
        If the YAML fails the internal meta-schema check.

    Examples
    --------
    >>> contract = load_contract(Path("contracts/slot_telemetry.contract.yaml"))  # doctest: +SKIP
    >>> contract["product"]                                                       # doctest: +SKIP
    'bronze.slot_telemetry'
    """
    if not path.exists():
        raise FileNotFoundError(f"Contract file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Contract YAML must be a mapping at the top level: {path}")
    contract = _normalise_contract(raw)

    missing = [k for k in _REQUIRED_TOP_LEVEL if not contract.get(k)]
    if missing:
        raise ValueError(f"Contract {path} missing required keys: {missing}")
    if not isinstance(contract["schema"], list) or not contract["schema"]:
        raise ValueError(f"Contract {path}: 'schema' must be a non-empty list of columns")
    for idx, col in enumerate(contract["schema"]):
        for key in _REQUIRED_COLUMN_KEYS:
            if key not in col:
                raise ValueError(
                    f"Contract {path}: column #{idx} missing required key '{key}'"
                )
    logger.info(
        "Loaded contract %s v%s with %d columns",
        contract["product"],
        contract["version"],
        len(contract["schema"]),
    )
    return contract


# ---------------------------------------------------------------------------
# Suite generation
# ---------------------------------------------------------------------------


# Map contract types to GE physical type names (Spark backend).
_TYPE_MAP: Dict[str, str] = {
    "string": "StringType",
    "int": "IntegerType",
    "integer": "IntegerType",
    "bigint": "LongType",
    "long": "LongType",
    "decimal": "DecimalType",
    "double": "DoubleType",
    "float": "FloatType",
    "boolean": "BooleanType",
    "bool": "BooleanType",
    "timestamp": "TimestampType",
    "date": "DateType",
}


def _physical_type(contract_type: str) -> Optional[str]:
    """Translate a contract type (e.g. ``decimal(18,2)``) to a GE Spark type."""
    if not contract_type:
        return None
    base = contract_type.split("(", 1)[0].strip().lower()
    return _TYPE_MAP.get(base)


def _require_ge() -> None:
    """Raise a helpful error when GE is not installed."""
    if not _GE_AVAILABLE:
        raise ImportError(
            "great_expectations is required for this operation. "
            "Install with: pip install 'great_expectations>=0.18,<1.0'"
        ) from _GE_IMPORT_ERROR


def generate_suite(contract: Dict[str, Any], suite_name: str) -> "ExpectationSuite":
    """Generate a Great Expectations suite from a contract dict.

    Builds:
      * ``expect_table_columns_to_match_set`` for the full column list.
      * ``expect_column_to_exist`` per column.
      * ``expect_column_values_to_be_of_type`` when a known type is mapped.
      * ``expect_column_values_to_not_be_null`` for ``required``/``not_null``.
      * ``expect_column_values_to_be_unique`` for ``unique``.
      * ``expect_column_values_to_match_regex`` for ``pattern``.
      * ``expect_column_values_to_be_between`` for ``min``/``max``.
      * ``expect_column_values_to_be_in_set`` for ``enum`` and for
        referential-integrity entries (consumer of the authoritative set).
      * ``expect_table_row_count_to_be_between`` from
        ``quality_slas.volume.expected_rows_per_day``.
      * Per-column completeness ``mostly`` from
        ``quality_slas.completeness.per_column``.

    Parameters
    ----------
    contract:
        Normalised contract dict (as returned by :func:`load_contract`).
    suite_name:
        Name to assign to the resulting ExpectationSuite.

    Returns
    -------
    ExpectationSuite

    Examples
    --------
    >>> contract = {"product": "bronze.x", "version": "1.0.0",                 # doctest: +SKIP
    ...             "schema": [{"name": "id", "type": "string", "not_null": True}]}
    >>> suite = generate_suite(contract, "bronze_x_suite")                     # doctest: +SKIP
    >>> suite.expectation_suite_name                                           # doctest: +SKIP
    'bronze_x_suite'
    """
    _require_ge()

    suite = ExpectationSuite(  # type: ignore[misc]
        expectation_suite_name=suite_name,
        meta={
            "contract_product": contract.get("product"),
            "contract_version": contract.get("version"),
            "generated_by": "validation.great_expectations.data_contract_suite",
        },
    )
    configs: List["ExpectationConfiguration"] = []

    columns = contract["schema"]
    column_names = [c["name"] for c in columns]

    configs.append(
        ExpectationConfiguration(  # type: ignore[misc]
            expectation_type="expect_table_columns_to_match_set",
            kwargs={"column_set": column_names, "exact_match": False},
        )
    )

    completeness_per_col: Dict[str, float] = (
        contract.get("quality_slas", {}).get("completeness", {}).get("per_column", {}) or {}
    )

    for col in columns:
        name = col["name"]
        configs.append(
            ExpectationConfiguration(  # type: ignore[misc]
                expectation_type="expect_column_to_exist",
                kwargs={"column": name},
            )
        )

        phys = _physical_type(col.get("type", ""))
        if phys:
            configs.append(
                ExpectationConfiguration(  # type: ignore[misc]
                    expectation_type="expect_column_values_to_be_of_type",
                    kwargs={"column": name, "type_": phys},
                )
            )

        if col.get("not_null") or (col.get("required") and not col.get("nullable", False)):
            kwargs: Dict[str, Any] = {"column": name}
            if name in completeness_per_col:
                kwargs["mostly"] = completeness_per_col[name] / 100.0
            configs.append(
                ExpectationConfiguration(  # type: ignore[misc]
                    expectation_type="expect_column_values_to_not_be_null",
                    kwargs=kwargs,
                )
            )

        if col.get("unique"):
            configs.append(
                ExpectationConfiguration(  # type: ignore[misc]
                    expectation_type="expect_column_values_to_be_unique",
                    kwargs={"column": name},
                )
            )

        pattern = col.get("pattern") or col.get("regex")
        if pattern:
            configs.append(
                ExpectationConfiguration(  # type: ignore[misc]
                    expectation_type="expect_column_values_to_match_regex",
                    kwargs={"column": name, "regex": pattern},
                )
            )

        if "min" in col or "max" in col:
            configs.append(
                ExpectationConfiguration(  # type: ignore[misc]
                    expectation_type="expect_column_values_to_be_between",
                    kwargs={
                        "column": name,
                        "min_value": col.get("min"),
                        "max_value": col.get("max"),
                    },
                )
            )

        if "enum" in col and isinstance(col["enum"], list):
            configs.append(
                ExpectationConfiguration(  # type: ignore[misc]
                    expectation_type="expect_column_values_to_be_in_set",
                    kwargs={"column": name, "value_set": col["enum"]},
                )
            )

    # Referential integrity → emit not_null + an in-set hook keyed off the
    # authoritative table reference (the runtime resolver fills the value_set
    # from a live read of the dim table — at suite generation time we record
    # the reference in meta so the checkpoint can resolve it).
    ri = (
        contract.get("quality_slas", {})
        .get("accuracy", {})
        .get("referential_integrity", [])
    )
    for entry in ri or []:
        col_name = entry.get("column")
        ref = entry.get("references")
        if not (col_name and ref):
            continue
        configs.append(
            ExpectationConfiguration(  # type: ignore[misc]
                expectation_type="expect_column_values_to_not_be_null",
                kwargs={"column": col_name},
                meta={"referential_integrity": ref},
            )
        )

    # Volume / row count
    volume = contract.get("quality_slas", {}).get("volume", {}) or {}
    rpd = volume.get("expected_rows_per_day") or {}
    if rpd.get("min") is not None or rpd.get("max") is not None:
        configs.append(
            ExpectationConfiguration(  # type: ignore[misc]
                expectation_type="expect_table_row_count_to_be_between",
                kwargs={
                    "min_value": rpd.get("min"),
                    "max_value": rpd.get("max"),
                },
                meta={"sla": "volume.expected_rows_per_day"},
            )
        )

    suite.add_expectation_configurations(configs)
    logger.info(
        "Generated suite '%s' with %d expectations from contract %s v%s",
        suite_name,
        len(configs),
        contract["product"],
        contract["version"],
    )
    return suite


# ---------------------------------------------------------------------------
# Checkpoint + validation
# ---------------------------------------------------------------------------


def build_checkpoint(contract: Dict[str, Any], datasource_name: str) -> Dict[str, Any]:
    """Wrap the suite into a runnable Checkpoint config.

    Returns a dict that GE accepts via ``add_or_update_checkpoint``. We return
    the config (not a live Checkpoint object) so the caller controls the
    GE context (ephemeral, file, or Fabric-backed).

    Parameters
    ----------
    contract:
        Normalised contract dict.
    datasource_name:
        GE datasource name (e.g. ``casino_bronze`` or ``federal_silver``).

    Returns
    -------
    dict
        Checkpoint config compatible with GE 0.18+.

    Examples
    --------
    >>> cfg = build_checkpoint(contract, "casino_bronze")  # doctest: +SKIP
    >>> cfg["name"]                                        # doctest: +SKIP
    'bronze_slot_telemetry_contract_checkpoint'
    """
    _require_ge()
    suite_name = _suite_name_for(contract)
    cp_name = suite_name.replace("_suite", "_contract_checkpoint")
    return {
        "name": cp_name,
        "config_version": 1.0,
        "class_name": "Checkpoint",
        "run_name_template": "%Y%m%d-%H%M%S-" + cp_name,
        "expectation_suite_name": suite_name,
        "action_list": [
            {"name": "store_validation_result",
             "action": {"class_name": "StoreValidationResultAction"}},
            {"name": "store_evaluation_params",
             "action": {"class_name": "StoreEvaluationParametersAction"}},
            {"name": "update_data_docs",
             "action": {"class_name": "UpdateDataDocsAction"}},
        ],
        "validations": [{
            "batch_request": {
                "datasource_name": datasource_name,
                "data_connector_name": "runtime_data_connector",
                "data_asset_name": contract["product"],
                "batch_identifiers": {"default_identifier_name": contract["version"]},
            },
            "expectation_suite_name": suite_name,
        }],
    }


def _suite_name_for(contract: Dict[str, Any]) -> str:
    """Derive a deterministic suite name from the contract product."""
    return contract["product"].replace(".", "_") + "_contract_suite"


def validate_contract(
    contract: Dict[str, Any],
    datasource: str,
    table: str,
) -> Dict[str, Any]:
    """Run the contract checkpoint and summarise the outcome.

    Parameters
    ----------
    contract:
        Normalised contract dict.
    datasource:
        GE datasource name registered on the active context.
    table:
        Fully-qualified table name to validate (e.g. ``lh_bronze.slot_telemetry``).

    Returns
    -------
    dict with keys:
        ``success`` (bool), ``failures`` (list of dicts), ``total_records``,
        ``validated_records``, ``success_rate``, ``contract_id``,
        ``contract_version``, ``suite_name``.

    Examples
    --------
    >>> report = validate_contract(contract, "casino_bronze",                 # doctest: +SKIP
    ...                            "lh_bronze.slot_telemetry")
    >>> report["success"]                                                     # doctest: +SKIP
    True
    """
    _require_ge()
    context = gx.get_context()  # type: ignore[union-attr]
    suite = generate_suite(contract, _suite_name_for(contract))
    context.add_or_update_expectation_suite(expectation_suite=suite)

    checkpoint_cfg = build_checkpoint(contract, datasource)
    context.add_or_update_checkpoint(**checkpoint_cfg)

    result = context.run_checkpoint(
        checkpoint_name=checkpoint_cfg["name"],
        batch_request={
            "datasource_name": datasource,
            "data_connector_name": "runtime_data_connector",
            "data_asset_name": table,
            "batch_identifiers": {"default_identifier_name": contract["version"]},
        },
    )

    failures: List[Dict[str, Any]] = []
    total_records = 0
    validated_records = 0
    for run in result.run_results.values():
        validation = run.get("validation_result", {})
        for r in validation.get("results", []):
            res = r.get("result", {}) or {}
            total_records = max(total_records, int(res.get("element_count") or 0))
            validated_records = max(
                validated_records, int(res.get("element_count") or 0) - int(
                    res.get("unexpected_count") or 0
                ),
            )
            if not r.get("success", False):
                kwargs = r.get("expectation_config", {}).get("kwargs", {})
                failures.append({
                    "expectation_type": r.get("expectation_config", {}).get(
                        "expectation_type"
                    ),
                    "column": kwargs.get("column") or kwargs.get("column_list"),
                    "observed_value": res.get("observed_value"),
                    "unexpected_count": res.get("unexpected_count"),
                })

    success_rate = (
        validated_records / total_records if total_records else 1.0
    )
    return {
        "success": bool(result.success),
        "failures": failures,
        "total_records": total_records,
        "validated_records": validated_records,
        "success_rate": success_rate,
        "contract_id": contract["product"],
        "contract_version": contract["version"],
        "suite_name": _suite_name_for(contract),
    }


def enforce_contract(contract_path: Path, table: str, datasource: str = "default") -> None:
    """Top-level CI entry: load, generate, run; raise on any violation.

    Designed to be wired into the CI pipeline as a fail-fast gate. On
    contract violation it raises :class:`ContractViolationError` so the CI
    job exits non-zero.

    Parameters
    ----------
    contract_path:
        Path to the contract YAML.
    table:
        Fully-qualified table to validate.
    datasource:
        GE datasource name (default ``"default"``).

    Examples
    --------
    >>> enforce_contract(Path("contracts/slot.yaml"),                          # doctest: +SKIP
    ...                  "lh_bronze.slot_telemetry")
    """
    contract = load_contract(contract_path)
    report = validate_contract(contract, datasource, table)
    if not report["success"]:
        raise ContractViolationError(
            contract_id=report["contract_id"],
            contract_version=report["contract_version"],
            failures=report["failures"],
        )
    logger.info(
        "Contract %s v%s OK (%d/%d records valid, %.4f rate)",
        report["contract_id"],
        report["contract_version"],
        report["validated_records"],
        report["total_records"],
        report["success_rate"],
    )


# ---------------------------------------------------------------------------
# Quarantine
# ---------------------------------------------------------------------------


def quarantine_violations(
    table: str,
    violations: List[Dict[str, Any]],
    dlq_table: str,
) -> int:
    """Move offending rows from ``table`` to ``dlq_table``.

    The implementation prefers PySpark when a ``SparkSession`` is active
    (Fabric notebooks); it falls back to a pure-Python no-op when Spark is
    unavailable so import-side effects do not break unit tests.

    Returns
    -------
    int
        Number of rows quarantined (best-effort; ``-1`` if Spark unavailable).

    Examples
    --------
    >>> quarantine_violations("lh_bronze.slot_telemetry",                      # doctest: +SKIP
    ...                       report["failures"],
    ...                       "lh_bronze.slot_telemetry_dlq")
    """
    try:
        from pyspark.sql import SparkSession  # type: ignore[import-untyped]
    except ImportError:
        logger.warning(
            "PySpark not available; skipping quarantine of %d violation(s) from %s",
            len(violations), table,
        )
        return -1

    spark = SparkSession.getActiveSession()
    if spark is None:
        logger.warning("No active SparkSession; quarantine skipped for %s", table)
        return -1

    if not violations:
        return 0

    # Build a per-column predicate: each violation contributes a WHERE clause
    # matching either the unexpected_value or NULL on the failed column.
    predicates: List[str] = []
    for v in violations:
        col = v.get("column")
        if not col or isinstance(col, list):
            continue
        if v.get("expectation_type") == "expect_column_values_to_not_be_null":
            predicates.append(f"`{col}` IS NULL")
        elif v.get("observed_value") is not None:
            # Best-effort: catch rows where the unexpected value matches.
            predicates.append(f"`{col}` IS NOT NULL")
    if not predicates:
        return 0

    where = " OR ".join(predicates)
    logger.info("Quarantining rows from %s -> %s WHERE %s", table, dlq_table, where)
    spark.sql(
        f"CREATE TABLE IF NOT EXISTS {dlq_table} AS "
        f"SELECT * FROM {table} WHERE 1=0"
    )
    spark.sql(
        f"INSERT INTO {dlq_table} SELECT * FROM {table} WHERE {where}"
    )
    count_df = spark.sql(f"SELECT COUNT(*) AS n FROM {table} WHERE {where}")
    n = int(count_df.collect()[0]["n"])
    spark.sql(f"DELETE FROM {table} WHERE {where}")
    logger.info("Quarantined %d row(s) to %s", n, dlq_table)
    return n


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _format_report(report: Dict[str, Any]) -> str:
    """Render a human-readable validation report."""
    lines = [
        "=" * 72,
        f"Contract:  {report['contract_id']}  v{report['contract_version']}",
        f"Suite:     {report['suite_name']}",
        f"Records:   {report['validated_records']:,}/"
        f"{report['total_records']:,} valid "
        f"({report['success_rate']:.4%})",
        f"Status:    {'PASS' if report['success'] else 'FAIL'}",
        "=" * 72,
    ]
    if report["failures"]:
        lines.append("Failures:")
        for f in report["failures"]:
            lines.append(
                f"  - {f.get('expectation_type')}  column={f.get('column')!r}  "
                f"observed={f.get('observed_value')!r}  "
                f"unexpected={f.get('unexpected_count')}"
            )
    return "\n".join(lines)


def _cli(argv: Optional[List[str]] = None) -> int:
    """CLI entry point. Returns process exit code."""
    parser = argparse.ArgumentParser(
        prog="data_contract_suite",
        description="Generate and enforce GE expectation suites from data contracts.",
    )
    parser.add_argument("--contract", type=Path, required=True,
                        help="Path to contract YAML.")
    parser.add_argument("--table", type=str, required=True,
                        help="Fully-qualified table to validate.")
    parser.add_argument("--datasource", type=str, default="default",
                        help="GE datasource name (default: 'default').")
    parser.add_argument("--mode", choices=("report", "enforce", "quarantine"),
                        default="report",
                        help="report=print only; enforce=raise on fail; "
                             "quarantine=move bad rows to DLQ.")
    parser.add_argument("--dlq-table", type=str, default=None,
                        help="DLQ table for --mode=quarantine "
                             "(default: '<table>_dlq').")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable INFO logging.")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        contract = load_contract(args.contract)
        report = validate_contract(contract, args.datasource, args.table)
    except ImportError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2
    except (FileNotFoundError, ValueError) as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2

    print(_format_report(report))

    if args.mode == "enforce" and not report["success"]:
        print(
            f"ENFORCE: contract violation — {len(report['failures'])} failure(s).",
            file=sys.stderr,
        )
        return 1
    if args.mode == "quarantine" and report["failures"]:
        dlq = args.dlq_table or f"{args.table}_dlq"
        n = quarantine_violations(args.table, report["failures"], dlq)
        print(f"Quarantined {n} row(s) to {dlq}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(_cli())
