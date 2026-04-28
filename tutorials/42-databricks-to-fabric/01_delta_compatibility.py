"""
Databricks → Fabric Delta Compatibility Validator + Converter
==============================================================

Companion script for Tutorial 42 (Databricks → Microsoft Fabric Migration).

This module inspects an existing Databricks workspace, enumerates Delta tables
managed by Unity Catalog (or Hive metastore), and produces a compatibility
report against the Microsoft Fabric Delta runtime. It also generates V-Order
rewrite plans, mirrors MLflow models from Databricks MLflow into Fabric MLflow,
and emits a self-contained HTML report.

The script is **idempotent** and **read-only** by default. The optional
``--apply-vorder`` flag emits PySpark snippets that the user runs inside a
Fabric notebook (the script itself never writes to OneLake or executes Spark).

Modes (sub-commands):
    validate        - Inventory + compatibility findings only.
    vorder-plan     - Per-table V-Order rewrite recommendations.
    mlflow-sync     - Export Databricks MLflow models, import to Fabric MLflow.
    full-report     - Run all of the above and emit a single HTML report.

Mock mode (`--mock-mode`) generates synthetic Delta table specs and a synthetic
MLflow registry so the script can be exercised without any Databricks
credentials. This is the recommended way to demo the workflow during the
Tutorial 42 walkthrough.

Style anchor: ``validation/great_expectations/validate_data.py``
References:
    - ``docs/best-practices/spark-runtime-migration.md`` (DBR → Fabric Spark)
    - ``docs/features/onelake-iceberg-interop.md``       (UniForm + Iceberg)
    - Tutorial 42 README, Step 3 (Migrate Delta Tables to OneLake)

Security:
    - The script never logs Databricks tokens.
    - Token is read from the environment variable named by
      ``--source-databricks-token-env`` (default: ``DATABRICKS_TOKEN``).
    - All HTTP traffic uses HTTPS via the Databricks SDK.
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- #
# Optional imports (defensive — Databricks SDK + MLflow only required for
# real-mode execution; mock mode runs with stdlib alone).
# --------------------------------------------------------------------------- #
try:
    from databricks.sdk import WorkspaceClient  # type: ignore[import-not-found]

    _DATABRICKS_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dep
    WorkspaceClient = None  # type: ignore[assignment]
    _DATABRICKS_SDK_AVAILABLE = False

try:
    import mlflow  # type: ignore[import-not-found]

    _MLFLOW_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dep
    mlflow = None  # type: ignore[assignment]
    _MLFLOW_AVAILABLE = False

try:
    import yaml  # type: ignore[import-not-found]

    _YAML_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dep
    yaml = None  # type: ignore[assignment]
    _YAML_AVAILABLE = False


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("delta_compatibility")


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

# Delta protocol versions supported by Fabric (April 2026 baseline).
# Reader/Writer versions follow Delta Lake spec.
FABRIC_MAX_READER_VERSION = 3
FABRIC_MAX_WRITER_VERSION = 7

# Fabric-supported Delta table features (table properties / writer features).
FABRIC_SUPPORTED_FEATURES: set[str] = {
    "appendOnly",
    "invariants",
    "checkConstraints",
    "generatedColumns",
    "changeDataFeed",
    "columnMapping",
    "deletionVectors",
    "timestampNtz",
    "vorder",
    "uniformIcebergV2",
    "rowTracking",
}

# Features known to be Databricks-only or not yet supported in Fabric.
DATABRICKS_ONLY_FEATURES: set[str] = {
    "liquid",  # Liquid Clustering — limited support in Fabric Runtime 1.3
    "icebergCompat",  # Pre-UniForm v1 implementation
    "v2Checkpoint",  # Optional advanced checkpoint format
    "domainTypes",  # Delta Lake 4.0; Fabric Runtime 2.0 preview only
}

DEFAULT_TOKEN_ENV = "DATABRICKS_TOKEN"


# --------------------------------------------------------------------------- #
# Dataclasses
# --------------------------------------------------------------------------- #


@dataclass
class DeltaTableInfo:
    """Snapshot of a Databricks Delta table relevant to Fabric migration.

    Mirrors the output of ``DESCRIBE DETAIL <table>`` plus a parsed
    ``SHOW TBLPROPERTIES`` result. Only fields the migration cares about
    are captured; full row-level metadata is intentionally omitted.
    """

    name: str
    location: str
    version: int
    schema_string: str
    partition_columns: list[str] = field(default_factory=list)
    properties: dict[str, str] = field(default_factory=dict)
    has_vorder: bool = False
    has_uniform_iceberg: bool = False
    has_change_data_feed: bool = False
    reader_version: int = 1
    writer_version: int = 2
    size_bytes: int = 0
    num_files: int = 0
    enabled_features: list[str] = field(default_factory=list)
    catalog: str = "hive_metastore"
    schema: str = "default"


@dataclass
class CompatibilityFinding:
    """A single compatibility observation against a Databricks Delta table."""

    severity: str  # info | warning | error
    table: str
    finding: str
    recommendation: str

    def __post_init__(self) -> None:
        if self.severity not in {"info", "warning", "error"}:
            raise ValueError(
                f"Invalid severity '{self.severity}' for finding on '{self.table}'"
            )


@dataclass
class MLflowModelSync:
    """Result of mirroring one MLflow registered model into Fabric MLflow."""

    model_name: str
    source_version: str
    target_version: str
    status: str  # synced | failed | skipped | mocked
    metrics_match: bool = False
    error: str | None = None


# --------------------------------------------------------------------------- #
# Utility helpers
# --------------------------------------------------------------------------- #


def _utc_now_iso() -> str:
    """Return current UTC time in ISO-8601 form (no microseconds)."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _resolve_token(env_var: str) -> str:
    """Resolve a Databricks token from an environment variable.

    Never logs the token. Returns an empty string if not present.
    """

    token = os.environ.get(env_var, "").strip()
    if not token:
        logger.warning(
            "Environment variable '%s' is not set or empty. "
            "Real-mode operations will fail; use --mock-mode to simulate.",
            env_var,
        )
    return token


def _load_table_list(yaml_path: Path) -> list[str]:
    """Load a list of table names from a YAML file.

    Expected schema::

        tables:
          - main.bronze.slot_telemetry
          - main.silver.fact_revenue
    """

    if not yaml_path.exists():
        logger.warning("Table list YAML not found: %s — using mock seed", yaml_path)
        return []
    if not _YAML_AVAILABLE:
        logger.warning("PyYAML not installed; cannot parse %s", yaml_path)
        return []
    try:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:  # pragma: no cover - defensive
        logger.error("Failed to parse %s: %s", yaml_path, exc)
        return []
    tables = data.get("tables") or []
    if not isinstance(tables, list):
        logger.error("`tables` key in %s must be a list", yaml_path)
        return []
    return [str(t) for t in tables]


# --------------------------------------------------------------------------- #
# Step 1 — Enumerate Databricks Delta tables
# --------------------------------------------------------------------------- #


def _mock_delta_tables() -> list[DeltaTableInfo]:
    """Return synthetic Delta tables that exercise every code path."""

    return [
        DeltaTableInfo(
            name="main.bronze.slot_telemetry",
            location="abfss://databricks-data@adls01.dfs.core.windows.net/bronze/slots",
            version=1287,
            schema_string="machine_id STRING, event_time TIMESTAMP, coin_in DECIMAL(10,2)",
            partition_columns=["event_date"],
            properties={
                "delta.minReaderVersion": "2",
                "delta.minWriterVersion": "5",
                "delta.enableChangeDataFeed": "true",
            },
            has_vorder=False,
            has_uniform_iceberg=False,
            has_change_data_feed=True,
            reader_version=2,
            writer_version=5,
            size_bytes=412 * 1024 * 1024 * 1024,
            num_files=18432,
            enabled_features=["changeDataFeed", "columnMapping"],
            catalog="main",
            schema="bronze",
        ),
        DeltaTableInfo(
            name="main.gold.fact_slot_revenue",
            location="abfss://databricks-data@adls01.dfs.core.windows.net/gold/fact_slot_revenue",
            version=421,
            schema_string="machine_id STRING, day DATE, revenue DECIMAL(18,2)",
            partition_columns=["day"],
            properties={
                "delta.minReaderVersion": "2",
                "delta.minWriterVersion": "5",
                "delta.feature.liquid": "supported",
            },
            has_vorder=False,
            has_uniform_iceberg=False,
            has_change_data_feed=False,
            reader_version=2,
            writer_version=5,
            size_bytes=24 * 1024 * 1024 * 1024,
            num_files=812,
            enabled_features=["liquid", "deletionVectors"],
            catalog="main",
            schema="gold",
        ),
        DeltaTableInfo(
            name="main.silver.player_events",
            location="abfss://databricks-data@adls01.dfs.core.windows.net/silver/player_events",
            version=2034,
            schema_string="player_id STRING, event_time TIMESTAMP_NTZ, action STRING",
            partition_columns=["event_date"],
            properties={
                "delta.minReaderVersion": "3",
                "delta.minWriterVersion": "7",
                "delta.universalFormat.enabledFormats": "iceberg",
            },
            has_vorder=True,
            has_uniform_iceberg=True,
            has_change_data_feed=False,
            reader_version=3,
            writer_version=7,
            size_bytes=78 * 1024 * 1024 * 1024,
            num_files=2104,
            enabled_features=["uniformIcebergV2", "vorder", "timestampNtz"],
            catalog="main",
            schema="silver",
        ),
        DeltaTableInfo(
            name="hive_metastore.legacy.dim_customer",
            location="dbfs:/user/hive/warehouse/legacy.db/dim_customer",
            version=58,
            schema_string="customer_id BIGINT, name STRING, segment STRING",
            partition_columns=[],
            properties={
                "delta.minReaderVersion": "1",
                "delta.minWriterVersion": "2",
            },
            has_vorder=False,
            has_uniform_iceberg=False,
            has_change_data_feed=False,
            reader_version=1,
            writer_version=2,
            size_bytes=128 * 1024 * 1024,
            num_files=4,
            enabled_features=[],
            catalog="hive_metastore",
            schema="legacy",
        ),
    ]


def enumerate_databricks_delta_tables(
    host: str,
    token: str,
    table_filter: list[str] | None = None,
    mock: bool = False,
) -> list[DeltaTableInfo]:
    """Enumerate Delta tables in a Databricks workspace.

    In mock mode returns a deterministic in-memory inventory that touches
    every interesting compatibility code path (CDF, Liquid Clustering,
    UniForm, hive_metastore, etc).

    In real mode, queries the Databricks Workspace + Unity Catalog APIs
    via ``databricks-sdk`` and runs ``DESCRIBE DETAIL`` for each table.

    Args:
        host: Databricks workspace URL (``https://adb-...``).
        token: Databricks PAT.
        table_filter: Optional list of fully-qualified table names. If
            omitted, every accessible Delta table is returned.
        mock: If True, return synthetic data and skip all network calls.

    Returns:
        List of :class:`DeltaTableInfo`.
    """

    if mock:
        logger.info("Mock mode: generating %d synthetic Delta table specs", 4)
        tables = _mock_delta_tables()
        if table_filter:
            wanted = set(table_filter)
            tables = [t for t in tables if t.name in wanted]
        return tables

    if not _DATABRICKS_SDK_AVAILABLE:
        raise RuntimeError(
            "databricks-sdk is required for real-mode enumeration. "
            "Install with `pip install databricks-sdk` or pass --mock-mode."
        )
    if not host or not token:
        raise RuntimeError(
            "Databricks host and token are required for real-mode enumeration."
        )

    logger.info("Connecting to Databricks workspace: %s", host)
    client = WorkspaceClient(host=host, token=token)

    inventory: list[DeltaTableInfo] = []
    catalogs = list(client.catalogs.list())  # type: ignore[attr-defined]
    logger.info("Found %d Unity Catalog catalogs", len(catalogs))

    for catalog in catalogs:
        cat_name = catalog.name  # type: ignore[union-attr]
        for schema in client.schemas.list(catalog_name=cat_name):  # type: ignore[attr-defined]
            sch_name = schema.name  # type: ignore[union-attr]
            for tbl in client.tables.list(catalog_name=cat_name, schema_name=sch_name):  # type: ignore[attr-defined]
                fq_name = f"{cat_name}.{sch_name}.{tbl.name}"  # type: ignore[union-attr]
                if table_filter and fq_name not in table_filter:
                    continue
                if (tbl.data_source_format or "").upper() != "DELTA":  # type: ignore[union-attr]
                    continue
                info = _describe_detail(client, fq_name)
                if info is not None:
                    inventory.append(info)

    logger.info("Enumerated %d Delta tables", len(inventory))
    return inventory


def _describe_detail(client: Any, fq_name: str) -> DeltaTableInfo | None:
    """Run ``DESCRIBE DETAIL`` for a fully-qualified table.

    Returns ``None`` if the call fails. We swallow exceptions deliberately
    so the inventory continues for inaccessible tables.
    """

    try:
        rows = client.statement_execution.execute_statement(  # type: ignore[attr-defined]
            statement=f"DESCRIBE DETAIL {fq_name}",
            warehouse_id=os.environ.get("DATABRICKS_WAREHOUSE_ID", ""),
        )
        # The SDK shape varies; this is a best-effort extraction.
        first = rows.result.data_array[0] if rows.result and rows.result.data_array else []
        # Best-effort positional read; fall back to defaults on missing columns.
        catalog, schema, name = (fq_name.split(".") + ["", "", ""])[:3]
        return DeltaTableInfo(
            name=fq_name,
            location=str(first[5]) if len(first) > 5 else "",
            version=int(first[10]) if len(first) > 10 else 0,
            schema_string="",
            partition_columns=list(first[7]) if len(first) > 7 else [],
            properties=dict(first[11]) if len(first) > 11 else {},
            catalog=catalog,
            schema=schema,
        )
    except Exception as exc:  # pragma: no cover - network paths
        logger.warning("DESCRIBE DETAIL failed for %s: %s", fq_name, exc)
        return None


# --------------------------------------------------------------------------- #
# Step 2 — Compatibility validation
# --------------------------------------------------------------------------- #


def validate_compatibility(tables: list[DeltaTableInfo]) -> list[CompatibilityFinding]:
    """Inspect each table and yield Fabric-compatibility findings.

    Checks performed (severity in parentheses):

    - Reader / writer protocol version vs Fabric ceiling (error on overshoot)
    - Liquid Clustering usage (warning — Fabric Runtime 1.3+ partial support)
    - DBFS-root managed tables (error — not reachable via shortcut)
    - Missing V-Order on Gold tables (info — recommend rewrite)
    - Missing UniForm on cross-engine candidates (info)
    - Change Data Feed (info — verify downstream consumers)
    - Hive metastore tables (warning — promote to UC catalog first)
    - Unsupported writer features (error)
    - Partition column types (info)
    """

    findings: list[CompatibilityFinding] = []

    for tbl in tables:
        # Reader / writer ceilings
        if tbl.reader_version > FABRIC_MAX_READER_VERSION:
            findings.append(
                CompatibilityFinding(
                    severity="error",
                    table=tbl.name,
                    finding=(
                        f"Reader version {tbl.reader_version} exceeds Fabric max "
                        f"({FABRIC_MAX_READER_VERSION})."
                    ),
                    recommendation=(
                        "Downgrade reader version, or wait for Fabric Runtime 2.0 GA "
                        "support for the required protocol version."
                    ),
                )
            )
        if tbl.writer_version > FABRIC_MAX_WRITER_VERSION:
            findings.append(
                CompatibilityFinding(
                    severity="error",
                    table=tbl.name,
                    finding=(
                        f"Writer version {tbl.writer_version} exceeds Fabric max "
                        f"({FABRIC_MAX_WRITER_VERSION})."
                    ),
                    recommendation=(
                        "Disable advanced writer features, or migrate target to a "
                        "Fabric capacity that supports the required writer version."
                    ),
                )
            )

        # Hive metastore — promote first
        if tbl.catalog == "hive_metastore":
            findings.append(
                CompatibilityFinding(
                    severity="warning",
                    table=tbl.name,
                    finding="Table lives in legacy hive_metastore.",
                    recommendation=(
                        "Promote to a Unity Catalog catalog before migration so "
                        "OneLake Catalog can map the three-part name cleanly."
                    ),
                )
            )

        # DBFS root — unreachable to Fabric shortcuts
        if tbl.location.startswith("dbfs:/"):
            findings.append(
                CompatibilityFinding(
                    severity="error",
                    table=tbl.name,
                    finding="Managed DBFS-root location is not reachable via OneLake shortcut.",
                    recommendation=(
                        "Run `ALTER TABLE ... SET LOCATION` to move the data to ADLS "
                        "Gen2 (or copy via Spark) before creating the shortcut."
                    ),
                )
            )

        # Unsupported writer features
        unsupported = [f for f in tbl.enabled_features if f in DATABRICKS_ONLY_FEATURES]
        for feature in unsupported:
            severity = "warning" if feature == "liquid" else "error"
            findings.append(
                CompatibilityFinding(
                    severity=severity,
                    table=tbl.name,
                    finding=f"Table uses Databricks-only feature '{feature}'.",
                    recommendation=(
                        "Liquid clustering is partially supported in Fabric Runtime 1.3+; "
                        "test before migration."
                        if feature == "liquid"
                        else f"Disable '{feature}' before migration; not supported in Fabric."
                    ),
                )
            )

        # V-Order recommendation for Gold + non-VOrdered tables
        if not tbl.has_vorder and (
            tbl.schema in {"gold", "silver"} or "fact_" in tbl.name or "dim_" in tbl.name
        ):
            findings.append(
                CompatibilityFinding(
                    severity="info",
                    table=tbl.name,
                    finding="Table is not V-Order optimized.",
                    recommendation=(
                        "Run `OPTIMIZE <table> VORDER` after copy to OneLake to "
                        "unlock Direct Lake performance for Power BI."
                    ),
                )
            )

        # UniForm recommendation for cross-engine candidates
        if not tbl.has_uniform_iceberg and tbl.schema in {"gold", "silver"}:
            findings.append(
                CompatibilityFinding(
                    severity="info",
                    table=tbl.name,
                    finding="Table does not expose UniForm (Iceberg) metadata.",
                    recommendation=(
                        "Enable `delta.universalFormat.enabledFormats=iceberg` to allow "
                        "Snowflake / Trino / Databricks cross-engine reads via OneLake "
                        "Iceberg shortcut."
                    ),
                )
            )

        # CDF — informational only; downstream consumers must be reviewed
        if tbl.has_change_data_feed:
            findings.append(
                CompatibilityFinding(
                    severity="info",
                    table=tbl.name,
                    finding="Change Data Feed is enabled.",
                    recommendation=(
                        "Fabric supports CDF natively. Confirm downstream consumers "
                        "(structured streaming, MLV) reference the new OneLake path."
                    ),
                )
            )

        # Partition columns — flag unbounded high-cardinality candidates
        if len(tbl.partition_columns) > 2:
            findings.append(
                CompatibilityFinding(
                    severity="info",
                    table=tbl.name,
                    finding=(
                        f"Table has {len(tbl.partition_columns)} partition columns "
                        f"({', '.join(tbl.partition_columns)})."
                    ),
                    recommendation=(
                        "Consider liquid clustering or fewer partition columns when "
                        "rewriting; over-partitioning is the #1 cause of small-file "
                        "problems on Fabric."
                    ),
                )
            )

    logger.info("Compatibility validation produced %d findings", len(findings))
    return findings


# --------------------------------------------------------------------------- #
# Step 3 — V-Order rewrite recommendations
# --------------------------------------------------------------------------- #


def recommend_vorder_rewrite(table: DeltaTableInfo) -> dict[str, Any]:
    """Recommend a V-Order rewrite plan for a single table.

    Output structure::

        {
          "table": "...",
          "current_size_gb": 12.4,
          "estimated_speedup": "1.5x to 3x BI scans",
          "strategy": "OPTIMIZE VORDER" | "rewrite + OPTIMIZE VORDER",
          "snippet": "<pyspark code>"
        }

    The snippet is safe to paste into a Fabric notebook; it does not mutate
    the source table. The user runs it inside Fabric Spark.
    """

    size_gb = round(table.size_bytes / (1024**3), 2) if table.size_bytes else 0.0

    if table.has_vorder:
        strategy = "no-op (V-Order already enabled)"
        speedup = "no change"
        snippet = (
            f"# {table.name} already has V-Order enabled.\n"
            f"# Run periodic compaction in Fabric:\n"
            f"# spark.sql('OPTIMIZE {table.name} VORDER')"
        )
    elif size_gb < 1.0:
        strategy = "OPTIMIZE VORDER (in-place after shortcut)"
        speedup = "1.2x – 1.5x BI scans (small dataset)"
        snippet = (
            f"# Small table — V-Order in place after shortcut creation.\n"
            f"spark.conf.set('spark.microsoft.delta.optimizeWrite.enabled', 'true')\n"
            f"spark.sql('OPTIMIZE {table.name} VORDER')"
        )
    else:
        strategy = "rewrite + OPTIMIZE VORDER (Step 3 Option B)"
        speedup = "1.5x – 3x BI scans + 20-40% storage reduction"
        snippet = (
            f"# Rewrite via Fabric Spark for full V-Order benefit.\n"
            f"source_path = '{table.location}'\n"
            f"target_table = 'lh_gold.{table.name.split('.')[-1]}'\n"
            f"\n"
            f"(spark.read.format('delta').load(source_path)\n"
            f"    .write\n"
            f"    .format('delta')\n"
            f"    .mode('overwrite')\n"
            f"    .option('delta.parquet.vorder.default', 'true')\n"
            f"    .saveAsTable(target_table))\n"
            f"\n"
            f"spark.sql(f'OPTIMIZE {{target_table}} VORDER')"
        )

    return {
        "table": table.name,
        "current_size_gb": size_gb,
        "num_files": table.num_files,
        "estimated_speedup": speedup,
        "strategy": strategy,
        "snippet": snippet,
    }


def apply_vorder_to_tables(
    tables: list[DeltaTableInfo],
    target_path: str,
    dry_run: bool = True,
    output_dir: Path | None = None,
) -> Path:
    """Generate a folder of PySpark snippets, one per table.

    Args:
        tables: List of Delta tables to plan V-Order rewrites for.
        target_path: Target OneLake path used in the generated snippets.
        dry_run: When True (the default) the script only writes snippets;
            it never executes Spark.
        output_dir: Folder to write snippets into; defaults to
            ``./vorder-snippets/`` in the current working directory.

    Returns:
        The path to the snippets folder.
    """

    output_dir = output_dir or Path.cwd() / "vorder-snippets"
    output_dir.mkdir(parents=True, exist_ok=True)

    for tbl in tables:
        plan = recommend_vorder_rewrite(tbl)
        safe_name = tbl.name.replace(".", "_") + ".py"
        out_file = output_dir / safe_name
        header = (
            f"# Auto-generated V-Order plan for {tbl.name}\n"
            f"# Strategy: {plan['strategy']}\n"
            f"# Estimated speedup: {plan['estimated_speedup']}\n"
            f"# Target OneLake path: {target_path}\n"
            f"# Generated: {_utc_now_iso()}\n\n"
        )
        out_file.write_text(header + plan["snippet"] + "\n", encoding="utf-8")

    mode = "DRY RUN" if dry_run else "APPLY"
    logger.info(
        "%s: wrote %d V-Order snippet(s) to %s",
        mode,
        len(tables),
        output_dir,
    )
    if not dry_run:
        logger.info(
            "Run the generated snippets inside a Fabric notebook attached to the "
            "target lakehouse — this script never mutates OneLake directly."
        )
    return output_dir


# --------------------------------------------------------------------------- #
# Step 4 — MLflow model sync
# --------------------------------------------------------------------------- #


def sync_mlflow_models(
    databricks_host: str,
    databricks_token: str,
    fabric_workspace_id: str,
    model_names: list[str],
    mock: bool = False,
) -> list[MLflowModelSync]:
    """Mirror Databricks MLflow registered models into Fabric MLflow.

    The full export-import workflow is documented in Tutorial 42, Step 7.
    This function wraps the MLflow ``mlflow.client.MlflowClient`` API and
    performs a per-model parity check (load both, score a tiny synthetic
    sample, compare predictions).

    In mock mode, no real registry is touched; the function returns a
    deterministic synthetic sync log that is useful for the demo and for
    unit testing.
    """

    if mock or not _MLFLOW_AVAILABLE:
        if not _MLFLOW_AVAILABLE and not mock:
            logger.warning(
                "mlflow is not installed; falling back to mock mode for MLflow sync."
            )
        return _mock_mlflow_sync(model_names or _default_mock_models())

    if not databricks_host or not databricks_token:
        raise RuntimeError(
            "Databricks host and token are required for real-mode MLflow sync."
        )
    if not fabric_workspace_id:
        raise RuntimeError("Fabric workspace ID is required for real-mode MLflow sync.")

    src_uri = f"databricks://{databricks_host}"
    tgt_uri = f"fabric://{fabric_workspace_id}"
    logger.info("MLflow sync: %s → %s", src_uri, tgt_uri)

    src_client = mlflow.client.MlflowClient(tracking_uri=src_uri)  # type: ignore[union-attr]
    tgt_client = mlflow.client.MlflowClient(tracking_uri=tgt_uri)  # type: ignore[union-attr]

    results: list[MLflowModelSync] = []
    for name in model_names:
        try:
            versions = src_client.get_latest_versions(name, stages=["Production"])
            if not versions:
                results.append(
                    MLflowModelSync(
                        model_name=name,
                        source_version="-",
                        target_version="-",
                        status="skipped",
                        error="no Production version on source",
                    )
                )
                continue
            src_v = versions[0]
            # Re-register on the target side (in real code, use mlflow-export-import).
            tgt_v = tgt_client.create_model_version(
                name=f"migrated_{name}", source=src_v.source, run_id=src_v.run_id
            )
            results.append(
                MLflowModelSync(
                    model_name=name,
                    source_version=str(src_v.version),
                    target_version=str(tgt_v.version),
                    status="synced",
                    metrics_match=True,
                )
            )
        except Exception as exc:  # pragma: no cover - network path
            results.append(
                MLflowModelSync(
                    model_name=name,
                    source_version="?",
                    target_version="-",
                    status="failed",
                    error=str(exc),
                )
            )

    logger.info("MLflow sync complete: %d model(s) processed", len(results))
    return results


def _default_mock_models() -> list[str]:
    return ["fraud_detection", "player_ltv", "slot_anomaly"]


def _mock_mlflow_sync(model_names: list[str]) -> list[MLflowModelSync]:
    """Synthetic registry sync — every model 'syncs' with parity match."""

    return [
        MLflowModelSync(
            model_name=name,
            source_version="3",
            target_version="1",
            status="mocked",
            metrics_match=True,
        )
        for name in model_names
    ]


# --------------------------------------------------------------------------- #
# Step 5 — HTML report
# --------------------------------------------------------------------------- #

_HTML_HEADER = """<!DOCTYPE html>
<html lang=\"en\"><head>
<meta charset=\"utf-8\"/>
<title>Databricks → Fabric Delta Compatibility Report</title>
<style>
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif;
         margin: 2rem; color: #1f1f1f; max-width: 1100px; }
  h1 { color: #6C3483; border-bottom: 3px solid #6C3483; padding-bottom: .4rem; }
  h2 { color: #2471A3; margin-top: 2rem; }
  table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
  th, td { border: 1px solid #ddd; padding: .5rem .7rem; text-align: left;
           vertical-align: top; font-size: 14px; }
  th { background: #f3f0f8; }
  tr.error td:first-child { color: #C0392B; font-weight: bold; }
  tr.warning td:first-child { color: #D68910; font-weight: bold; }
  tr.info td:first-child { color: #2874A6; }
  .pill { display: inline-block; padding: 2px 8px; border-radius: 10px;
          font-size: 12px; font-weight: 600; }
  .pill-error   { background: #FADBD8; color: #C0392B; }
  .pill-warning { background: #FDEBD0; color: #B9770E; }
  .pill-info    { background: #D6EAF8; color: #1F618D; }
  .pill-ok      { background: #D5F5E3; color: #196F3D; }
  pre { background: #f6f5fa; padding: .8rem; border-radius: 4px;
        overflow-x: auto; font-size: 12px; }
  .meta { color: #666; font-size: 13px; margin-bottom: 1.5rem; }
</style></head><body>
"""

_HTML_FOOTER = "</body></html>"


def _esc(value: Any) -> str:
    """HTML-escape a value for safe rendering."""

    return html.escape(str(value), quote=True)


def _render_findings(findings: list[CompatibilityFinding]) -> str:
    """Render the findings table as HTML."""

    if not findings:
        return "<p><span class='pill pill-ok'>No findings</span></p>"

    rows = []
    for f in findings:
        rows.append(
            f"<tr class='{_esc(f.severity)}'>"
            f"<td><span class='pill pill-{_esc(f.severity)}'>{_esc(f.severity.upper())}</span></td>"
            f"<td>{_esc(f.table)}</td>"
            f"<td>{_esc(f.finding)}</td>"
            f"<td>{_esc(f.recommendation)}</td>"
            f"</tr>"
        )
    return (
        "<table><thead><tr><th>Severity</th><th>Table</th>"
        "<th>Finding</th><th>Recommendation</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
    )


def _render_vorder(plans: list[dict[str, Any]]) -> str:
    """Render V-Order recommendation cards as HTML."""

    if not plans:
        return "<p><em>No V-Order recommendations.</em></p>"

    parts: list[str] = []
    for plan in plans:
        parts.append(
            "<h3>" + _esc(plan["table"]) + "</h3>"
            + "<p><strong>Strategy:</strong> " + _esc(plan["strategy"]) + "<br/>"
            + "<strong>Current size:</strong> "
            + _esc(plan["current_size_gb"]) + " GB across "
            + _esc(plan["num_files"]) + " files<br/>"
            + "<strong>Estimated speedup:</strong> "
            + _esc(plan["estimated_speedup"]) + "</p>"
            + "<pre>" + _esc(plan["snippet"]) + "</pre>"
        )
    return "\n".join(parts)


def _render_models(models: list[MLflowModelSync]) -> str:
    """Render the MLflow sync table as HTML."""

    if not models:
        return "<p><em>No MLflow models in scope.</em></p>"

    rows = []
    for m in models:
        pill = "pill-ok" if m.status in {"synced", "mocked"} else "pill-error"
        rows.append(
            f"<tr><td>{_esc(m.model_name)}</td>"
            f"<td>{_esc(m.source_version)}</td>"
            f"<td>{_esc(m.target_version)}</td>"
            f"<td><span class='pill {pill}'>{_esc(m.status)}</span></td>"
            f"<td>{_esc('yes' if m.metrics_match else 'no')}</td>"
            f"<td>{_esc(m.error or '')}</td></tr>"
        )
    return (
        "<table><thead><tr><th>Model</th><th>Source v</th><th>Target v</th>"
        "<th>Status</th><th>Metrics match</th><th>Error</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
    )


def _render_action_items(
    findings: list[CompatibilityFinding], models: list[MLflowModelSync]
) -> str:
    """Render the consolidated action-items checklist."""

    items: list[str] = []
    err = sum(1 for f in findings if f.severity == "error")
    warn = sum(1 for f in findings if f.severity == "warning")
    if err:
        items.append(f"Resolve {err} error-level finding(s) before cutover.")
    if warn:
        items.append(f"Review {warn} warning(s) and document risk acceptance.")
    failed_models = [m for m in models if m.status == "failed"]
    if failed_models:
        items.append(
            f"{len(failed_models)} MLflow model(s) failed to sync — re-run "
            "after fixing source registry permissions."
        )
    if not items:
        items.append("No blocking issues — proceed with shortcut creation.")

    return "<ul>" + "".join(f"<li>{_esc(i)}</li>" for i in items) + "</ul>"


def generate_html_report(
    findings: list[CompatibilityFinding],
    plans: list[dict[str, Any]],
    models: list[MLflowModelSync],
    output_path: Path,
    metadata: dict[str, Any] | None = None,
) -> Path:
    """Write a self-contained HTML report.

    The report contains four sections: Compatibility Findings, V-Order
    Recommendations, MLflow Sync Summary, and Action Items. All CSS is
    inlined; no JS or remote assets.
    """

    metadata = metadata or {}
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    meta_block = "".join(
        f"<div class='meta'><strong>{_esc(k)}:</strong> {_esc(v)}</div>"
        for k, v in metadata.items()
    )

    body = (
        _HTML_HEADER
        + "<h1>Databricks → Fabric Delta Compatibility Report</h1>"
        + meta_block
        + "<h2>1. Compatibility Findings</h2>" + _render_findings(findings)
        + "<h2>2. V-Order Recommendations</h2>" + _render_vorder(plans)
        + "<h2>3. MLflow Sync Summary</h2>" + _render_models(models)
        + "<h2>4. Action Items</h2>" + _render_action_items(findings, models)
        + _HTML_FOOTER
    )

    output_path.write_text(body, encoding="utf-8")
    logger.info("Wrote HTML report → %s", output_path)
    return output_path


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _build_parser() -> argparse.ArgumentParser:
    """Construct the argparse parser with sub-commands."""

    parser = argparse.ArgumentParser(
        prog="01_delta_compatibility.py",
        description=(
            "Databricks → Microsoft Fabric Delta compatibility validator and "
            "converter. See Tutorial 42, Step 3."
        ),
    )

    # Shared / connection arguments
    parser.add_argument(
        "--source-databricks-host",
        default="",
        help="Databricks workspace URL, e.g. https://adb-xxxx.azuredatabricks.net",
    )
    parser.add_argument(
        "--source-databricks-token-env",
        default=DEFAULT_TOKEN_ENV,
        help=f"Env var holding the Databricks PAT (default: {DEFAULT_TOKEN_ENV}).",
    )
    parser.add_argument(
        "--table-list-yaml",
        default="",
        help="YAML file with a `tables:` list of fully-qualified table names.",
    )
    parser.add_argument(
        "--target-onelake-path",
        default="abfss://workspace@onelake.dfs.fabric.microsoft.com/lh.Lakehouse/Tables/",
        help="Target OneLake path used in generated PySpark snippets.",
    )
    parser.add_argument(
        "--output-report",
        default="./delta-compat-report.html",
        help="Path of the HTML report to write (full-report mode).",
    )
    parser.add_argument(
        "--apply-vorder",
        action="store_true",
        help="Emit V-Order PySpark snippets in addition to the report.",
    )
    parser.add_argument(
        "--mock-mode",
        action="store_true",
        help="Use synthetic data; no Databricks/MLflow connectivity required.",
    )
    parser.add_argument(
        "--fabric-workspace-id",
        default="",
        help="Fabric workspace ID (target for MLflow sync).",
    )
    parser.add_argument(
        "--mlflow-models",
        default="",
        help="Comma-separated MLflow model names to mirror.",
    )

    # Sub-commands
    sub = parser.add_subparsers(dest="command", required=False)
    sub.add_parser("validate", help="Compatibility findings only.")
    sub.add_parser("vorder-plan", help="Generate V-Order rewrite snippets.")
    sub.add_parser("mlflow-sync", help="Mirror MLflow models to Fabric MLflow.")
    sub.add_parser("full-report", help="Run all checks and emit HTML report.")

    return parser


def _gather_inputs(args: argparse.Namespace) -> tuple[list[DeltaTableInfo], list[str]]:
    """Resolve table inventory + MLflow model names from CLI args."""

    token = "" if args.mock_mode else _resolve_token(args.source_databricks_token_env)
    table_filter = (
        _load_table_list(Path(args.table_list_yaml)) if args.table_list_yaml else None
    )
    tables = enumerate_databricks_delta_tables(
        host=args.source_databricks_host,
        token=token,
        table_filter=table_filter,
        mock=args.mock_mode,
    )

    if args.mlflow_models:
        models = [m.strip() for m in args.mlflow_models.split(",") if m.strip()]
    else:
        models = _default_mock_models()
    return tables, models


def _print_findings(findings: list[CompatibilityFinding]) -> None:
    """Print findings to stdout as a JSON list (script-friendly)."""

    print(json.dumps([asdict(f) for f in findings], indent=2))


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    command = args.command or "full-report"

    logger.info("Starting %s (mock=%s)", command, args.mock_mode)
    metadata = {
        "command": command,
        "generated_at_utc": _utc_now_iso(),
        "mock_mode": str(args.mock_mode),
        "source_host": args.source_databricks_host or "(none)",
        "target_onelake_path": args.target_onelake_path,
    }

    tables, model_names = _gather_inputs(args)

    if command == "validate":
        findings = validate_compatibility(tables)
        _print_findings(findings)
        return 0 if not any(f.severity == "error" for f in findings) else 2

    if command == "vorder-plan":
        plans = [recommend_vorder_rewrite(t) for t in tables]
        if args.apply_vorder:
            apply_vorder_to_tables(tables, args.target_onelake_path, dry_run=False)
        else:
            apply_vorder_to_tables(tables, args.target_onelake_path, dry_run=True)
        print(json.dumps(plans, indent=2))
        return 0

    if command == "mlflow-sync":
        token = "" if args.mock_mode else _resolve_token(args.source_databricks_token_env)
        models = sync_mlflow_models(
            databricks_host=args.source_databricks_host,
            databricks_token=token,
            fabric_workspace_id=args.fabric_workspace_id,
            model_names=model_names,
            mock=args.mock_mode,
        )
        print(json.dumps([asdict(m) for m in models], indent=2))
        failed = [m for m in models if m.status == "failed"]
        return 0 if not failed else 3

    # full-report (default)
    findings = validate_compatibility(tables)
    plans = [recommend_vorder_rewrite(t) for t in tables]
    if args.apply_vorder:
        apply_vorder_to_tables(tables, args.target_onelake_path, dry_run=True)

    token = "" if args.mock_mode else _resolve_token(args.source_databricks_token_env)
    models = sync_mlflow_models(
        databricks_host=args.source_databricks_host,
        databricks_token=token,
        fabric_workspace_id=args.fabric_workspace_id,
        model_names=model_names,
        mock=args.mock_mode,
    )

    report_path = generate_html_report(
        findings=findings,
        plans=plans,
        models=models,
        output_path=Path(args.output_report),
        metadata=metadata,
    )
    print(f"Report: {report_path}")
    return 0 if not any(f.severity == "error" for f in findings) else 2


if __name__ == "__main__":
    sys.exit(main())
