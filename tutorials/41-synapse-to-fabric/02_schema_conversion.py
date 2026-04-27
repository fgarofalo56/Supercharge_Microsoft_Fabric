"""
Synapse Dedicated SQL Pool -> Fabric Warehouse Schema/DDL Converter
==================================================================

Phase 14 Wave 4 / Tutorial 41 / Step 3 companion script.

Reads a source Synapse Dedicated SQL Pool schema (or a synthetic mock schema in
``--mock-mode``) and emits Fabric Warehouse-compatible CREATE TABLE DDL files,
plus a conversion report and an unsupported-features ledger.

Type conversion rules mirror the canonical "Type Conversion Table" in the
companion tutorial README (`tutorials/41-synapse-to-fabric/README.md`, Step 3).
Any change to the rules in code MUST be reflected in the README and vice versa.

Conversion behavior
-------------------
1.  Source schema is read from ``INFORMATION_SCHEMA.TABLES`` /
    ``INFORMATION_SCHEMA.COLUMNS`` plus Synapse-specific catalog views
    (``sys.pdw_table_distribution_properties``, ``sys.indexes``).
2.  Each column type is mapped through ``TYPE_CONVERSIONS``.
3.  Synapse-specific table clauses (``WITH (DISTRIBUTION = ...)``,
    ``CLUSTERED COLUMNSTORE INDEX``, etc.) are stripped — Fabric Warehouse
    handles distribution and indexing automatically (Delta + V-Order).
4.  Per-table ``CREATE TABLE`` DDL is written to
    ``{output_dir}/{schema}.{table}.sql`` with a header comment describing the
    transformation actions taken on that specific table.
5.  Aggregate artifacts are written:
        - ``_conversion_report.md`` — summary of all warnings + statistics
        - ``_unsupported_features.md`` — items requiring manual intervention
6.  Optional ``--validate`` flag runs a regex-based syntactic sanity check on
    each generated DDL file before declaring success.

Mock mode
---------
``--mock-mode`` returns 15 realistic synthetic tables across 3 schemas
(``casino``, ``federal``, ``staging``) including unsupported-type cases
(``xml``, ``geography``, ``hierarchyid``) so tutorial readers can exercise the
full conversion pipeline without a live Synapse workspace.

Usage
-----
::

    python 02_schema_conversion.py \\
        --source-conn "Server=tcp:syn-prod-ws01.sql.azuresynapse.net;Database=master;Authentication=Active Directory Default" \\
        --target-warehouse "wh-analytics-prod" \\
        --target-workspace "ws-analytics-prod" \\
        --output-ddl ./output-ddl/

    # No live Synapse? Use mock mode:
    python 02_schema_conversion.py --mock-mode --output-ddl ./output-ddl/

Production deployment
---------------------
This script writes DDL files only. Apply them via fabric-cicd
(`scripts/fabric-cicd-deploy.py`) — the ``apply_to_target()`` function in this
module is a placeholder that documents the deployment hand-off.

Author: Platform Team
Phase: 14 Wave 4 (Synapse migration tooling)
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Logging setup (mirrors validate_data.py simple-stderr pattern)
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("synapse_to_fabric.schema_conversion")

# ---------------------------------------------------------------------------
# Defensive imports for Synapse SQL drivers
# ---------------------------------------------------------------------------

_SQL_DRIVER: str | None = None
try:
    import pyodbc  # type: ignore[import-not-found]

    _SQL_DRIVER = "pyodbc"
except ImportError:  # pragma: no cover - environment dependent
    try:
        import pymssql  # type: ignore[import-not-found]

        _SQL_DRIVER = "pymssql"
    except ImportError:
        pyodbc = None  # type: ignore[assignment]
        pymssql = None  # type: ignore[assignment]


def _require_driver() -> str:
    """Return the available driver name or raise a helpful error."""
    if _SQL_DRIVER is None:
        raise RuntimeError(
            "Neither 'pyodbc' nor 'pymssql' is installed. To run against a real "
            "Synapse workspace, install one:\n"
            "    pip install pyodbc        # preferred (ODBC Driver 18+ required)\n"
            "    pip install pymssql       # alternative, no ODBC dependency\n"
            "Or run with --mock-mode for offline conversion of synthetic schemas."
        )
    return _SQL_DRIVER


# ---------------------------------------------------------------------------
# Type Conversion Table — canonical mirror of README Step 3
# ---------------------------------------------------------------------------
# Format: source_type -> (target_type_template, conversion_action)
#   target_type_template: target Fabric Warehouse type, or None if unsupported
#   conversion_action: one of
#     - "DIRECT"                    (1:1 type)
#     - "DIRECT_WITH_PRECISION"     (preserve precision/scale, e.g. decimal)
#     - "DIRECT_WITH_LENGTH"        (preserve declared length, e.g. nvarchar(50))
#     - "UTF8_NOTE"                 (direct, but call out UTF-8 default)
#     - "RECOMMENDED_UPGRADE"       (technically direct, prefer upgraded type)
#     - "DEPRECATED_REPLACE"        (legacy type, replace with modern equivalent)
#     - "NOT_SUPPORTED"             (no Fabric Warehouse equivalent)

TYPE_CONVERSIONS: dict[str, tuple[str | None, str]] = {
    # Numeric -- direct
    "bigint": ("bigint", "DIRECT"),
    "int": ("int", "DIRECT"),
    "smallint": ("smallint", "DIRECT"),
    "tinyint": ("tinyint", "DIRECT"),
    "bit": ("bit", "DIRECT"),
    "decimal": ("decimal", "DIRECT_WITH_PRECISION"),
    "numeric": ("decimal", "DIRECT_WITH_PRECISION"),
    "money": ("decimal(19,4)", "RECOMMENDED_UPGRADE"),
    "smallmoney": ("decimal(10,4)", "RECOMMENDED_UPGRADE"),
    "float": ("float", "DIRECT"),
    "real": ("real", "DIRECT"),
    # Strings
    "char": ("char", "DIRECT_WITH_LENGTH"),
    "varchar": ("varchar", "DIRECT_WITH_LENGTH"),
    "nchar": ("char", "UTF8_NOTE"),
    "nvarchar": ("varchar", "UTF8_NOTE"),
    "text": ("varchar(max)", "DEPRECATED_REPLACE"),
    "ntext": ("varchar(max)", "DEPRECATED_REPLACE"),
    # Binary
    "binary": ("varbinary", "RECOMMENDED_UPGRADE"),
    "varbinary": ("varbinary", "DIRECT_WITH_LENGTH"),
    "image": ("varbinary(max)", "DEPRECATED_REPLACE"),
    # Temporal
    "date": ("date", "DIRECT"),
    "datetime": ("datetime2(6)", "RECOMMENDED_UPGRADE"),
    "datetime2": ("datetime2", "DIRECT_WITH_PRECISION"),
    "datetimeoffset": ("datetime2(6)", "RECOMMENDED_UPGRADE"),
    "smalldatetime": ("datetime2(0)", "RECOMMENDED_UPGRADE"),
    "time": ("time(6)", "RECOMMENDED_UPGRADE"),
    # Identifiers
    "uniqueidentifier": ("uniqueidentifier", "DIRECT"),
    # Unsupported -- block with action
    "xml": (None, "NOT_SUPPORTED"),
    "geography": (None, "NOT_SUPPORTED"),
    "geometry": (None, "NOT_SUPPORTED"),
    "hierarchyid": (None, "NOT_SUPPORTED"),
    "sql_variant": (None, "NOT_SUPPORTED"),
    "rowversion": (None, "NOT_SUPPORTED"),
    "timestamp": (None, "NOT_SUPPORTED"),  # rowversion alias
}

# Recommended fallback target types when an unsupported type is rewritten
UNSUPPORTED_FALLBACKS: dict[str, str] = {
    "xml": "varchar(max)",
    "geography": "varchar(max)",  # Use Lakehouse + sedona for real geo work
    "geometry": "varchar(max)",
    "hierarchyid": "varchar(4000)",  # Materialized path string
    "sql_variant": "varchar(max)",
    "rowversion": "binary(8)",
    "timestamp": "binary(8)",
}

# ---------------------------------------------------------------------------
# Synapse-specific clauses to strip from generated DDL
# ---------------------------------------------------------------------------

SYNAPSE_CLAUSES_TO_STRIP: list[str] = [
    "WITH (DISTRIBUTION = HASH",
    "WITH (DISTRIBUTION = ROUND_ROBIN",
    "WITH (DISTRIBUTION = REPLICATE",
    "DISTRIBUTION = HASH",
    "DISTRIBUTION = ROUND_ROBIN",
    "DISTRIBUTION = REPLICATE",
    "CLUSTERED COLUMNSTORE INDEX",
    "NONCLUSTERED COLUMNSTORE INDEX",
    "WITH (HEAP)",
    "CLUSTERED INDEX",
    "NONCLUSTERED INDEX",
    "WITH (HEAP, DISTRIBUTION",
    "PARTITION (",
]

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ColumnSpec:
    """A single column conversion result."""

    name: str
    source_type: str
    target_type: str | None
    nullable: bool
    default: str | None = None
    conversion_action: str = "DIRECT"
    warning: str | None = None

    def is_blocked(self) -> bool:
        """Column could not be converted (no fallback applied)."""
        return self.target_type is None


@dataclass
class TableSpec:
    """A single table conversion result."""

    schema: str
    name: str
    columns: list[ColumnSpec] = field(default_factory=list)
    source_distribution: str | None = None
    source_index_type: str | None = None
    conversion_warnings: list[str] = field(default_factory=list)
    target_ddl: str | None = None

    @property
    def fqn(self) -> str:
        return f"{self.schema}.{self.name}"

    @property
    def has_unsupported(self) -> bool:
        return any(c.conversion_action == "NOT_SUPPORTED" for c in self.columns)

    @property
    def is_fully_direct(self) -> bool:
        return all(c.conversion_action == "DIRECT" for c in self.columns)


@dataclass
class ConversionReport:
    """Aggregate conversion statistics."""

    total_tables: int = 0
    fully_converted: int = 0
    with_warnings: int = 0
    blocked_unsupported: int = 0
    unsupported_columns_per_table: dict[str, list[str]] = field(default_factory=dict)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Source schema reading
# ---------------------------------------------------------------------------


_INFO_SCHEMA_QUERY = """
SELECT
    t.TABLE_SCHEMA      AS schema_name,
    t.TABLE_NAME        AS table_name,
    c.COLUMN_NAME       AS column_name,
    c.DATA_TYPE         AS data_type,
    c.CHARACTER_MAXIMUM_LENGTH AS max_length,
    c.NUMERIC_PRECISION AS num_precision,
    c.NUMERIC_SCALE     AS num_scale,
    c.DATETIME_PRECISION AS dt_precision,
    c.IS_NULLABLE       AS is_nullable,
    c.COLUMN_DEFAULT    AS column_default,
    c.ORDINAL_POSITION  AS ordinal_position
FROM INFORMATION_SCHEMA.TABLES t
JOIN INFORMATION_SCHEMA.COLUMNS c
  ON c.TABLE_SCHEMA = t.TABLE_SCHEMA
 AND c.TABLE_NAME   = t.TABLE_NAME
WHERE t.TABLE_TYPE = 'BASE TABLE'
ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME, c.ORDINAL_POSITION;
"""

_DISTRIBUTION_QUERY = """
SELECT
    s.name AS schema_name,
    o.name AS table_name,
    p.distribution_policy_desc AS distribution_policy
FROM sys.pdw_table_distribution_properties p
JOIN sys.objects o ON o.object_id = p.object_id
JOIN sys.schemas s ON s.schema_id = o.schema_id
WHERE o.type = 'U';
"""

_INDEX_QUERY = """
SELECT
    s.name AS schema_name,
    o.name AS table_name,
    i.type_desc AS index_type
FROM sys.indexes i
JOIN sys.objects o ON o.object_id = i.object_id
JOIN sys.schemas s ON s.schema_id = o.schema_id
WHERE o.type = 'U' AND i.index_id <= 1;
"""


def _connect(conn_string: str):
    """Open a connection using whichever driver is available."""
    driver = _require_driver()
    if driver == "pyodbc":
        return pyodbc.connect(conn_string)
    return pymssql.connect(conn_string)  # pragma: no cover - alt driver path


def read_source_schema(conn_string: str, mock: bool = False) -> list[TableSpec]:
    """Read source Synapse schema and return a list of :class:`TableSpec`.

    In ``mock=True`` mode, returns a fixed synthetic catalog (15 tables across
    3 schemas) covering casino + federal samples plus unsupported-type edge
    cases. This is the path tutorial readers use when no live Synapse exists.
    """
    if mock:
        logger.info("Mock mode: returning 15 synthetic tables across 3 schemas.")
        return _build_mock_schema()

    logger.info("Connecting to source Synapse Dedicated SQL Pool...")
    conn = _connect(conn_string)
    try:
        cursor = conn.cursor()

        cursor.execute(_INFO_SCHEMA_QUERY)
        info_rows = cursor.fetchall()

        # Distribution properties (Synapse-specific; will fail on plain SQL Server)
        distributions: dict[tuple[str, str], str] = {}
        try:
            cursor.execute(_DISTRIBUTION_QUERY)
            for row in cursor.fetchall():
                distributions[(row[0], row[1])] = row[2]
        except Exception as exc:  # noqa: BLE001 - defensive across drivers
            logger.warning(
                "Could not read sys.pdw_table_distribution_properties (%s). "
                "Source may not be a Synapse Dedicated SQL pool.",
                exc,
            )

        # Index information
        indexes: dict[tuple[str, str], str] = {}
        try:
            cursor.execute(_INDEX_QUERY)
            for row in cursor.fetchall():
                indexes[(row[0], row[1])] = row[2]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not read sys.indexes (%s).", exc)

        return _rows_to_table_specs(info_rows, distributions, indexes)
    finally:
        conn.close()


def _rows_to_table_specs(
    info_rows: Iterable[Any],
    distributions: dict[tuple[str, str], str],
    indexes: dict[tuple[str, str], str],
) -> list[TableSpec]:
    """Group raw INFORMATION_SCHEMA rows into TableSpecs."""
    tables: dict[tuple[str, str], TableSpec] = {}
    for row in info_rows:
        schema_name, table_name = row[0], row[1]
        key = (schema_name, table_name)
        if key not in tables:
            tables[key] = TableSpec(
                schema=schema_name,
                name=table_name,
                source_distribution=distributions.get(key),
                source_index_type=indexes.get(key),
            )
        col_dict = {
            "column_name": row[2],
            "data_type": row[3],
            "max_length": row[4],
            "num_precision": row[5],
            "num_scale": row[6],
            "dt_precision": row[7],
            "is_nullable": row[8],
            "column_default": row[9],
        }
        tables[key].columns.append(convert_column(col_dict))
    return list(tables.values())


# ---------------------------------------------------------------------------
# Mock schema (used when --mock-mode or no Synapse driver is available)
# ---------------------------------------------------------------------------


def _build_mock_schema() -> list[TableSpec]:
    """15-table synthetic catalog spanning casino + federal + staging schemas."""
    mocks: list[dict[str, Any]] = [
        # ----- casino -----
        {
            "schema": "casino",
            "name": "slot_telemetry",
            "distribution": "HASH(machine_id)",
            "index": "CLUSTERED COLUMNSTORE INDEX",
            "columns": [
                ("event_id", "bigint", None, None, None, None, "NO"),
                ("machine_id", "int", None, None, None, None, "NO"),
                ("event_ts", "datetime", None, None, None, None, "NO"),
                ("amount_wagered", "decimal", None, 18, 2, None, "YES"),
                ("metadata", "xml", None, None, None, None, "YES"),  # unsupported
            ],
        },
        {
            "schema": "casino",
            "name": "player_profile",
            "distribution": "HASH(player_id)",
            "index": "CLUSTERED COLUMNSTORE INDEX",
            "columns": [
                ("player_id", "uniqueidentifier", None, None, None, None, "NO"),
                ("ssn_hash", "binary", 32, None, None, None, "NO"),
                ("display_name", "nvarchar", 100, None, None, None, "NO"),
                ("notes", "ntext", None, None, None, None, "YES"),  # deprecated
                ("preferences_xml", "xml", None, None, None, None, "YES"),
            ],
        },
        {
            "schema": "casino",
            "name": "ctr_filing",
            "distribution": "ROUND_ROBIN",
            "index": "HEAP",
            "columns": [
                ("filing_id", "bigint", None, None, None, None, "NO"),
                ("amount", "money", None, None, None, None, "NO"),
                ("filed_at", "datetime", None, None, None, None, "NO"),
                ("officer_initials", "char", 3, None, None, None, "YES"),
            ],
        },
        {
            "schema": "casino",
            "name": "table_games_event",
            "distribution": "HASH(table_id)",
            "index": "CLUSTERED COLUMNSTORE INDEX",
            "columns": [
                ("event_id", "bigint", None, None, None, None, "NO"),
                ("table_id", "int", None, None, None, None, "NO"),
                ("event_ts", "datetime2", None, None, None, 6, "NO"),
                ("payout", "decimal", None, 18, 2, None, "YES"),
                ("location_geo", "geography", None, None, None, None, "YES"),
            ],
        },
        {
            "schema": "casino",
            "name": "compliance_lookup",
            "distribution": "REPLICATE",
            "index": "CLUSTERED INDEX",
            "columns": [
                ("code", "varchar", 16, None, None, None, "NO"),
                ("description", "nvarchar", 256, None, None, None, "NO"),
                ("threshold_usd", "decimal", None, 18, 2, None, "YES"),
            ],
        },
        # ----- federal -----
        {
            "schema": "federal",
            "name": "usda_crop_production",
            "distribution": "HASH(state_fips)",
            "index": "CLUSTERED COLUMNSTORE INDEX",
            "columns": [
                ("year", "int", None, None, None, None, "NO"),
                ("state_fips", "char", 2, None, None, None, "NO"),
                ("commodity", "nvarchar", 64, None, None, None, "NO"),
                ("yield_per_acre", "float", None, None, None, None, "YES"),
                ("harvested_acres", "bigint", None, None, None, None, "YES"),
            ],
        },
        {
            "schema": "federal",
            "name": "sba_ppp_loans",
            "distribution": "HASH(borrower_id)",
            "index": "CLUSTERED COLUMNSTORE INDEX",
            "columns": [
                ("loan_id", "bigint", None, None, None, None, "NO"),
                ("borrower_id", "uniqueidentifier", None, None, None, None, "NO"),
                ("loan_amount", "money", None, None, None, None, "NO"),
                ("approval_dt", "date", None, None, None, None, "NO"),
                ("naics_code", "char", 6, None, None, None, "YES"),
            ],
        },
        {
            "schema": "federal",
            "name": "noaa_weather_obs",
            "distribution": "HASH(station_id)",
            "index": "CLUSTERED COLUMNSTORE INDEX",
            "columns": [
                ("obs_id", "bigint", None, None, None, None, "NO"),
                ("station_id", "varchar", 16, None, None, None, "NO"),
                ("obs_ts", "datetimeoffset", None, None, None, 7, "NO"),
                ("temp_c", "real", None, None, None, None, "YES"),
                ("location", "geography", None, None, None, None, "YES"),
            ],
        },
        {
            "schema": "federal",
            "name": "epa_air_quality",
            "distribution": "HASH(monitor_id)",
            "index": "CLUSTERED COLUMNSTORE INDEX",
            "columns": [
                ("reading_id", "bigint", None, None, None, None, "NO"),
                ("monitor_id", "varchar", 32, None, None, None, "NO"),
                ("reading_ts", "datetime", None, None, None, None, "NO"),
                ("aqi", "int", None, None, None, None, "YES"),
                ("pollutant", "nvarchar", 64, None, None, None, "YES"),
            ],
        },
        {
            "schema": "federal",
            "name": "doi_park_visitation",
            "distribution": "HASH(park_id)",
            "index": "CLUSTERED COLUMNSTORE INDEX",
            "columns": [
                ("park_id", "int", None, None, None, None, "NO"),
                ("visit_dt", "date", None, None, None, None, "NO"),
                ("visitor_count", "bigint", None, None, None, None, "NO"),
                ("revenue_usd", "money", None, None, None, None, "YES"),
            ],
        },
        {
            "schema": "federal",
            "name": "doj_case_filing",
            "distribution": "HASH(case_id)",
            "index": "HEAP",
            "columns": [
                ("case_id", "bigint", None, None, None, None, "NO"),
                ("filed_dt", "datetime", None, None, None, None, "NO"),
                ("hierarchy", "hierarchyid", None, None, None, None, "YES"),
                ("variant_value", "sql_variant", None, None, None, None, "YES"),
            ],
        },
        {
            "schema": "federal",
            "name": "tribal_health_claim",
            "distribution": "HASH(member_id)",
            "index": "CLUSTERED COLUMNSTORE INDEX",
            "columns": [
                ("claim_id", "bigint", None, None, None, None, "NO"),
                ("member_id", "uniqueidentifier", None, None, None, None, "NO"),
                ("claim_amount", "decimal", None, 12, 2, None, "NO"),
                ("dx_code", "char", 7, None, None, None, "YES"),
            ],
        },
        # ----- staging -----
        {
            "schema": "staging",
            "name": "etl_audit",
            "distribution": "ROUND_ROBIN",
            "index": "HEAP",
            "columns": [
                ("audit_id", "bigint", None, None, None, None, "NO"),
                ("pipeline_name", "nvarchar", 128, None, None, None, "NO"),
                ("started_at", "datetime", None, None, None, None, "NO"),
                ("rowversion_col", "rowversion", None, None, None, None, "YES"),
            ],
        },
        {
            "schema": "staging",
            "name": "raw_csv_landing",
            "distribution": "ROUND_ROBIN",
            "index": "HEAP",
            "columns": [
                ("row_id", "bigint", None, None, None, None, "NO"),
                ("payload", "nvarchar", -1, None, None, None, "YES"),  # nvarchar(max)
                ("ingested_at", "smalldatetime", None, None, None, None, "NO"),
                ("source_blob", "nvarchar", 512, None, None, None, "YES"),
            ],
        },
        {
            "schema": "staging",
            "name": "legacy_blob_archive",
            "distribution": "ROUND_ROBIN",
            "index": "HEAP",
            "columns": [
                ("archive_id", "bigint", None, None, None, None, "NO"),
                ("blob_data", "image", None, None, None, None, "YES"),
                ("description", "text", None, None, None, None, "YES"),
                ("archived_at", "datetime", None, None, None, None, "NO"),
            ],
        },
    ]

    specs: list[TableSpec] = []
    for tbl in mocks:
        spec = TableSpec(
            schema=tbl["schema"],
            name=tbl["name"],
            source_distribution=tbl["distribution"],
            source_index_type=tbl["index"],
        )
        for col in tbl["columns"]:
            (
                col_name,
                data_type,
                max_length,
                num_precision,
                num_scale,
                dt_precision,
                nullable,
            ) = col
            spec.columns.append(
                convert_column(
                    {
                        "column_name": col_name,
                        "data_type": data_type,
                        "max_length": max_length,
                        "num_precision": num_precision,
                        "num_scale": num_scale,
                        "dt_precision": dt_precision,
                        "is_nullable": nullable,
                        "column_default": None,
                    }
                )
            )
        specs.append(spec)
    return specs


# ---------------------------------------------------------------------------
# Column / table conversion
# ---------------------------------------------------------------------------


def convert_column(col: dict[str, Any]) -> ColumnSpec:
    """Convert a single source column dict into a :class:`ColumnSpec`.

    Applies the type conversion table, preserves precision/scale/length where
    appropriate, and produces a warning string for any non-direct conversion.
    """
    source_type_raw = (col.get("data_type") or "").strip().lower()
    source_type = source_type_raw  # canonical lookup key
    nullable = (col.get("is_nullable") or "YES").upper() == "YES"
    default = col.get("column_default")

    target_template, action = TYPE_CONVERSIONS.get(source_type, (None, "NOT_SUPPORTED"))

    target_type: str | None = target_template
    warning: str | None = None

    if action == "DIRECT":
        target_type = target_template

    elif action == "DIRECT_WITH_PRECISION":
        precision = col.get("num_precision")
        scale = col.get("num_scale")
        if precision is not None:
            if scale is not None:
                target_type = f"{target_template}({precision},{scale})"
            else:
                target_type = f"{target_template}({precision})"
        else:
            target_type = target_template
            warning = "precision metadata missing; defaulted"

    elif action == "DIRECT_WITH_LENGTH":
        max_length = col.get("max_length")
        if max_length == -1 or max_length is None:
            target_type = f"{target_template}(max)"
        else:
            target_type = f"{target_template}({max_length})"

    elif action == "UTF8_NOTE":
        max_length = col.get("max_length")
        if max_length == -1 or max_length is None:
            target_type = f"{target_template}(max)"
        else:
            target_type = f"{target_template}({max_length})"
        warning = (
            f"{source_type} -> {target_type}: Fabric Warehouse uses UTF-8 by default; "
            "byte-length budgeting may differ from Synapse UCS-2."
        )

    elif action == "RECOMMENDED_UPGRADE":
        precision = col.get("dt_precision") or col.get("num_precision")
        if target_template and "(" in target_template:
            target_type = target_template  # already has precision baked in
        elif precision is not None:
            target_type = f"{target_template}({precision})"
        else:
            target_type = target_template
        warning = (
            f"{source_type} upgraded to {target_type} for higher precision / "
            "modern semantics."
        )

    elif action == "DEPRECATED_REPLACE":
        target_type = target_template
        warning = (
            f"{source_type} is deprecated in T-SQL; replaced with {target_type}. "
            "Verify downstream readers tolerate the swap."
        )

    elif action == "NOT_SUPPORTED":
        fallback = UNSUPPORTED_FALLBACKS.get(source_type)
        if fallback:
            target_type = fallback
            warning = (
                f"{source_type} is NOT SUPPORTED in Fabric Warehouse. "
                f"Auto-converted to {fallback}; manual review required."
            )
        else:
            target_type = None
            warning = (
                f"{source_type} is NOT SUPPORTED and has no automatic fallback. "
                "Manual intervention required."
            )

    else:  # pragma: no cover - defensive
        target_type = None
        warning = f"unknown conversion action: {action}"

    return ColumnSpec(
        name=col["column_name"],
        source_type=source_type_raw,
        target_type=target_type,
        nullable=nullable,
        default=str(default) if default is not None else None,
        conversion_action=action,
        warning=warning,
    )


def _strip_synapse_clauses(ddl: str) -> str:
    """Remove any residual Synapse-specific clauses from a DDL fragment.

    Operates only on the SQL body (lines that don't start with ``--``); header
    comment lines are preserved verbatim so the conversion notes remain
    legible.
    """
    body_lines: list[str] = []
    for line in ddl.split("\n"):
        if line.lstrip().startswith("--"):
            body_lines.append(line)
            continue
        cleaned_line = line
        for clause in SYNAPSE_CLAUSES_TO_STRIP:
            pattern = re.compile(re.escape(clause) + r"[^;\n]*", re.IGNORECASE)
            cleaned_line = pattern.sub("", cleaned_line)
        body_lines.append(cleaned_line)

    cleaned = "\n".join(body_lines)
    # Drop fully blank header-comment artifacts ("--   - ") with nothing after
    cleaned = re.sub(r"^--\s*-\s*$\n?", "", cleaned, flags=re.MULTILINE)
    # Collapse multiple blank lines / orphan commas left by stripping
    cleaned = re.sub(r"\n\s*\n", "\n", cleaned)
    cleaned = re.sub(r",\s*\)", ")", cleaned)
    return cleaned


def convert_table(source: TableSpec) -> TableSpec:
    """Run end-to-end conversion for a single table.

    Mutates ``source.target_ddl`` and ``source.conversion_warnings`` in place
    and returns the same object for fluent use.
    """
    notes: list[str] = []

    if source.source_distribution:
        notes.append(
            f"DISTRIBUTION = {source.source_distribution} removed "
            "(Fabric Warehouse handles distribution automatically)."
        )

    if source.source_index_type:
        idx_upper = source.source_index_type.upper()
        if "COLUMNSTORE" in idx_upper:
            notes.append(
                "CLUSTERED COLUMNSTORE INDEX removed "
                "(Fabric Warehouse uses Delta + V-Order)."
            )
        elif "HEAP" in idx_upper:
            notes.append("HEAP option removed (not applicable in Fabric Warehouse).")
        elif "CLUSTERED" in idx_upper:
            notes.append(
                "CLUSTERED INDEX removed (Fabric Warehouse manages indexing)."
            )

    for col in source.columns:
        if col.warning:
            notes.append(f"Column '{col.name}' ({col.source_type}): {col.warning}")

    source.conversion_warnings = notes
    source.target_ddl = generate_ddl(source)
    return source


def _format_column(col: ColumnSpec) -> str:
    """Render a single column line of CREATE TABLE."""
    null_clause = "NULL" if col.nullable else "NOT NULL"
    if col.target_type is None:
        # Render as a comment so the file remains parseable manually
        return (
            f"    -- BLOCKED: [{col.name}] {col.source_type} "
            f"-- {col.warning or 'unsupported type'}"
        )
    base = f"    [{col.name}] {col.target_type} {null_clause}"
    if col.default:
        base += f" DEFAULT {col.default}"
    return base


def generate_ddl(table: TableSpec) -> str:
    """Generate the Fabric Warehouse CREATE TABLE DDL string for a table."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    header_lines = [
        "-- Source: Synapse Dedicated SQL Pool",
        "-- Target: Fabric Warehouse",
        f"-- Generated: {today}",
        f"-- Table: {table.fqn}",
        "-- Notes:",
    ]
    if table.conversion_warnings:
        for note in table.conversion_warnings:
            header_lines.append(f"--   - {note}")
    else:
        header_lines.append("--   - Direct conversion: no transformations applied.")

    column_lines = [_format_column(c) for c in table.columns]
    # Active (non-blocked) columns are joined with commas; blocked rows are
    # comments and must not get a trailing comma.
    rendered: list[str] = []
    active_indices = [
        i for i, c in enumerate(table.columns) if c.target_type is not None
    ]
    last_active = active_indices[-1] if active_indices else -1
    for i, line in enumerate(column_lines):
        if i in active_indices and i != last_active:
            rendered.append(line + ",")
        else:
            rendered.append(line)

    ddl = "\n".join(
        [
            *header_lines,
            "",
            f"CREATE TABLE [{table.schema}].[{table.name}] (",
            *rendered,
            ");",
            "",
        ]
    )
    return _strip_synapse_clauses(ddl)


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def write_ddl_files(tables: list[TableSpec], output_dir: Path) -> ConversionReport:
    """Write per-table DDL plus aggregate report files. Return the report."""
    output_dir.mkdir(parents=True, exist_ok=True)

    report = ConversionReport(total_tables=len(tables))

    for table in tables:
        target_path = output_dir / f"{table.schema}.{table.name}.sql"
        target_path.write_text(table.target_ddl or "", encoding="utf-8")
        logger.info("Wrote DDL: %s", target_path)

        unsupported_cols = [
            c.name for c in table.columns if c.conversion_action == "NOT_SUPPORTED"
        ]
        if unsupported_cols:
            report.blocked_unsupported += 1
            report.unsupported_columns_per_table[table.fqn] = unsupported_cols
        elif table.conversion_warnings:
            report.with_warnings += 1
        elif table.is_fully_direct:
            report.fully_converted += 1
        else:
            report.with_warnings += 1

    _write_conversion_report(tables, report, output_dir)
    _write_unsupported_features(tables, output_dir)
    return report


def _write_conversion_report(
    tables: list[TableSpec], report: ConversionReport, output_dir: Path
) -> None:
    """Render ``_conversion_report.md``."""
    lines: list[str] = [
        "# Synapse -> Fabric Warehouse Conversion Report",
        "",
        f"**Generated:** {report.generated_at}",
        "",
        "## Summary",
        "",
        f"- Total tables: **{report.total_tables}**",
        f"- Fully direct (no warnings): **{report.fully_converted}**",
        f"- Converted with warnings: **{report.with_warnings}**",
        f"- Blocked / unsupported columns present: **{report.blocked_unsupported}**",
        "",
        "## Per-Table Detail",
        "",
        "| Table | Status | Warnings |",
        "|-------|--------|----------|",
    ]
    for table in tables:
        if table.has_unsupported:
            status = "BLOCKED (unsupported types)"
        elif table.conversion_warnings:
            status = "WARNINGS"
        else:
            status = "OK"
        warn_count = len(table.conversion_warnings)
        lines.append(f"| `{table.fqn}` | {status} | {warn_count} |")

    lines.append("")
    lines.append("## Warning Details")
    lines.append("")
    for table in tables:
        if not table.conversion_warnings:
            continue
        lines.append(f"### `{table.fqn}`")
        lines.append("")
        for note in table.conversion_warnings:
            lines.append(f"- {note}")
        lines.append("")

    out = output_dir / "_conversion_report.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Wrote conversion report: %s", out)


def _write_unsupported_features(tables: list[TableSpec], output_dir: Path) -> None:
    """Render ``_unsupported_features.md`` ledger."""
    lines: list[str] = [
        "# Unsupported Features Requiring Manual Intervention",
        "",
        "Items below could not be auto-converted or required a fallback.",
        "Review each entry before deploying the generated DDL.",
        "",
    ]

    blocked_any = False
    for table in tables:
        unsupported = [
            c for c in table.columns if c.conversion_action == "NOT_SUPPORTED"
        ]
        if not unsupported:
            continue
        blocked_any = True
        lines.append(f"## `{table.fqn}`")
        lines.append("")
        lines.append("| Column | Source Type | Auto-Fallback | Action Required |")
        lines.append("|--------|-------------|---------------|-----------------|")
        for col in unsupported:
            fallback = col.target_type or "(none)"
            lines.append(
                f"| `{col.name}` | `{col.source_type}` | `{fallback}` | "
                f"{col.warning or 'review'} |"
            )
        lines.append("")

    if not blocked_any:
        lines.append("_No unsupported features detected. Conversion is clean._")

    out = output_dir / "_unsupported_features.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Wrote unsupported features ledger: %s", out)


# ---------------------------------------------------------------------------
# Validation (optional)
# ---------------------------------------------------------------------------

_DDL_SANITY_REGEX = re.compile(
    r"CREATE\s+TABLE\s+\[[^\]]+\]\.\[[^\]]+\]\s*\(.+\)\s*;",
    re.IGNORECASE | re.DOTALL,
)


def _validate_ddl_files(output_dir: Path) -> tuple[int, list[str]]:
    """Regex-sanity-check every ``.sql`` in ``output_dir``.

    Returns ``(passed_count, failures)`` where failures is a list of file paths
    that did not match the basic CREATE TABLE shape.
    """
    failures: list[str] = []
    passed = 0
    for path in sorted(output_dir.glob("*.sql")):
        content = path.read_text(encoding="utf-8")
        if _DDL_SANITY_REGEX.search(content):
            passed += 1
        else:
            failures.append(str(path))
    return passed, failures


# ---------------------------------------------------------------------------
# Target deployment placeholder
# ---------------------------------------------------------------------------


def apply_to_target(
    tables: list[TableSpec],
    workspace: str,
    warehouse: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Placeholder for target deployment.

    Production deployment is performed via ``scripts/fabric-cicd-deploy.py``,
    which reads the generated DDL files and applies them through the
    fabric-cicd CI/CD pipeline. This function only logs the intended action
    so the conversion script can be wired into automation later without
    bypassing the supported deployment path.
    """
    logger.warning(
        "apply_to_target is a placeholder. "
        "Use scripts/fabric-cicd-deploy.py to deploy the generated DDL "
        "to workspace=%s warehouse=%s.",
        workspace,
        warehouse,
    )
    return {
        "dry_run": dry_run,
        "workspace": workspace,
        "warehouse": warehouse,
        "tables_in_scope": [t.fqn for t in tables],
        "deploy_command_hint": (
            "python scripts/fabric-cicd-deploy.py "
            f"--workspace {workspace} --warehouse {warehouse} "
            "--ddl-dir <output-ddl-path>"
        ),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="02_schema_conversion.py",
        description=(
            "Convert Synapse Dedicated SQL Pool schema to Fabric Warehouse DDL. "
            "Companion to Tutorial 41 Step 3."
        ),
    )
    parser.add_argument(
        "--source-conn",
        type=str,
        default=None,
        help=(
            "Source Synapse connection string. Required unless --mock-mode is "
            "supplied. NEVER hard-code; pass via env var or vault. Example: "
            "'Server=tcp:syn.sql.azuresynapse.net;Database=master;"
            "Authentication=Active Directory Default'"
        ),
    )
    parser.add_argument(
        "--target-warehouse",
        type=str,
        default=None,
        help="Target Fabric Warehouse name (used for deployment hand-off only).",
    )
    parser.add_argument(
        "--target-workspace",
        type=str,
        default=None,
        help="Target Fabric workspace name (used for deployment hand-off only).",
    )
    parser.add_argument(
        "--output-ddl",
        type=Path,
        required=True,
        help="Directory to write generated DDL and reports.",
    )
    parser.add_argument(
        "--mock-mode",
        action="store_true",
        help=(
            "Use a synthetic mock catalog (15 tables across 3 schemas) instead "
            "of querying a live Synapse workspace. Required for tutorial mode."
        ),
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run regex sanity check on generated DDL files after writing.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Call the apply_to_target placeholder. Does NOT actually deploy; "
            "prints the recommended fabric-cicd command."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if not args.mock_mode and not args.source_conn:
        logger.error(
            "Either --source-conn (live Synapse) or --mock-mode is required."
        )
        return 2

    try:
        sources = read_source_schema(args.source_conn or "", mock=args.mock_mode)
    except RuntimeError as exc:
        logger.error("%s", exc)
        return 3
    except Exception as exc:  # noqa: BLE001 - top-level CLI guard
        logger.exception("Failed to read source schema: %s", exc)
        return 4

    logger.info("Read %d source tables; converting...", len(sources))
    converted = [convert_table(t) for t in sources]
    report = write_ddl_files(converted, args.output_ddl)

    summary = {
        "tables": report.total_tables,
        "fully_converted": report.fully_converted,
        "with_warnings": report.with_warnings,
        "blocked_unsupported": report.blocked_unsupported,
        "output_dir": str(args.output_ddl.resolve()),
    }
    logger.info("Conversion complete: %s", json.dumps(summary))

    if args.validate:
        passed, failures = _validate_ddl_files(args.output_ddl)
        logger.info(
            "DDL sanity check: %d passed, %d failed.", passed, len(failures)
        )
        if failures:
            for fail in failures:
                logger.error("DDL sanity check failed: %s", fail)
            return 5

    if args.apply:
        if not (args.target_workspace and args.target_warehouse):
            logger.warning(
                "--apply requested but target workspace/warehouse not provided; "
                "skipping deployment hand-off."
            )
        else:
            apply_to_target(
                converted,
                workspace=args.target_workspace,
                warehouse=args.target_warehouse,
                dry_run=True,
            )

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
