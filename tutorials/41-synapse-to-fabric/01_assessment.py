"""
Synapse Workspace Assessment + Wave Planning + Capacity Recommendation
=======================================================================

Tutorial 41 (Phase 14, Wave 4) companion script for the Azure Synapse Analytics
to Microsoft Fabric migration. This is the assessment anchor referenced by
``tutorials/41-synapse-to-fabric/README.md`` Steps 1, 2, and 7.

Modes
-----
1. ``inventory`` (default) -- catalog Synapse tables, pipelines, notebooks, and
   compute pools; compute a complexity score per item; emit inventory.csv,
   complexity_scores.csv, dependency_graph.json, unsupported_features.md.
2. ``wave-plan`` -- consume an existing inventory and produce a topologically
   ordered migration plan capped at ``--max-wave-effort-days``; emit
   migration-waves.md.
3. ``capacity-recommendation`` -- combine inventory size + DWU baseline + Spark
   pool vCores + (optional) query history p95 latency to recommend a Fabric
   F-SKU; emit capacity-recommendation.md.

Usage
-----
    # Mode 1 -- inventory
    python 01_assessment.py inventory \\
        --synapse-workspace "syn-prod-ws01" \\
        --resource-group "rg-analytics-prod" \\
        --output-dir "./assessment-output"

    # Offline / CI testing
    python 01_assessment.py inventory --mock-mode \\
        --output-dir "./assessment-output"

    # Mode 2 -- wave plan
    python 01_assessment.py wave-plan \\
        --inventory ./assessment-output/inventory.csv \\
        --max-wave-effort-days 10

    # Mode 3 -- capacity recommendation
    python 01_assessment.py capacity-recommendation \\
        --inventory ./assessment-output/inventory.csv \\
        --dwu-baseline 5000 \\
        --spark-pool-vcores 200 \\
        --query-history-csv ./synapse-query-history.csv

Exit codes
----------
0 -- success.
1 -- error (missing inputs, malformed inventory, IO failure).
2 -- inventory completed but unsupported Synapse features were detected (warning).

References
----------
- Synapse to Fabric migration guide:
  https://learn.microsoft.com/fabric/migrate/synapse
- Fabric Warehouse T-SQL surface area:
  https://learn.microsoft.com/fabric/data-warehouse/data-warehousing
- Fabric capacity sizing:
  ../../docs/best-practices/capacity-planning-cost-optimization.md
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Defensive imports
# ---------------------------------------------------------------------------
# Azure SDK is only required for live (non-mock) mode. Importing them at module
# import time would prevent offline/CI usage of `--mock-mode`. We attempt the
# imports and stash a module-level flag; the actual bind only matters when
# `inventory_synapse_workspace(..., mock=False)` is called.

_AZURE_SDK_AVAILABLE: bool = False
_AZURE_IMPORT_ERROR: str | None = None

try:  # pragma: no cover -- exercised only when SDK is installed
    from azure.identity import DefaultAzureCredential  # type: ignore[import-not-found]
    from azure.mgmt.synapse import SynapseManagementClient  # type: ignore[import-not-found]

    _AZURE_SDK_AVAILABLE = True
except ImportError as exc:  # pragma: no cover -- offline path
    _AZURE_IMPORT_ERROR = str(exc)
    DefaultAzureCredential = None  # type: ignore[assignment, misc]
    SynapseManagementClient = None  # type: ignore[assignment, misc]


logger = logging.getLogger("synapse_assessment")


def _utcnow_iso() -> str:
    """Return a timezone-aware UTC timestamp in ISO format with trailing Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Per-band complexity score thresholds.
COMPLEXITY_BANDS: list[tuple[int, str]] = [
    (10, "Easy"),
    (30, "Medium"),
    (70, "Hard"),
    (10**9, "Very Hard"),
]

#: Approximate effort in days per complexity band (used by wave planning).
EFFORT_DAYS_PER_BAND: dict[str, float] = {
    "Easy": 0.5,
    "Medium": 1.5,
    "Hard": 3.5,
    "Very Hard": 7.0,
}

#: DWU -> Fabric F-SKU starting recommendation (see Tutorial 41 Step 7).
DWU_TO_FSKU: list[tuple[int, str]] = [
    (100, "F8"),
    (500, "F32"),
    (1000, "F64"),
    (3000, "F128"),
    (6000, "F256"),
    (7500, "F512"),
    (15000, "F1024"),
    (30000, "F2048"),
]

#: Spark vCore pressure adjustment thresholds (vCores -> minimum F-SKU).
SPARK_VCORE_MIN_FSKU: list[tuple[int, str]] = [
    (50, "F32"),
    (100, "F64"),
    (200, "F128"),
    (400, "F256"),
    (800, "F512"),
]

#: Synapse features that don't have a 1:1 Fabric equivalent.
UNSUPPORTED_FEATURE_RULES: dict[str, str] = {
    "DISTRIBUTION = HASH": "Remove -- Fabric Warehouse handles distribution automatically.",
    "DISTRIBUTION = REPLICATE": "Remove -- replace with V-Order Delta in Fabric.",
    "DISTRIBUTION = ROUND_ROBIN": "Remove -- Fabric handles automatically.",
    "CLUSTERED COLUMNSTORE INDEX": "Remove -- Fabric uses Delta + V-Order.",
    "EXTERNAL TABLE": "Convert to OneLake shortcut + Lakehouse table.",
    "MASTER KEY": "Migrate to OneLake Security + sensitivity labels.",
    "WORKLOAD GROUP": "Use Fabric workspace + capacity assignment.",
    "geography": "Not supported in Warehouse -- use Lakehouse + sedona.",
    "geometry": "Not supported in Warehouse -- use Lakehouse + sedona.",
    "hierarchyid": "Not supported -- convert to materialized path string.",
    "sql_variant": "Not supported -- convert to varchar(max) + type column.",
    "xml": "Not supported in Warehouse -- convert to varchar(max) + JSON.",
    "MAPPING_DATA_FLOW": "Recreate in Dataflow Gen2 (Power Query). Budget 4-8h each.",
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class TableInventoryEntry:
    """One Synapse table inventoried for migration."""

    table_name: str
    schema: str
    type: str  # heap | columnstore | external | view
    row_count: int
    size_gb: float
    last_used: str  # ISO date or "unknown"
    distribution_type: str  # HASH | REPLICATE | ROUND_ROBIN | NONE
    dependencies: list[str] = field(default_factory=list)
    complexity_score: int = 0
    complexity_band: str = "Easy"

    def to_csv_row(self) -> dict[str, Any]:
        """Flatten dependencies (list) into a pipe-delimited string for CSV."""
        row = asdict(self)
        row["dependencies"] = "|".join(self.dependencies)
        row["item_kind"] = "table"
        return row


@dataclass
class PipelineInventoryEntry:
    """One Synapse pipeline inventoried for migration."""

    name: str
    activity_count: int
    has_data_flow: bool
    dependency_count: int
    complexity_score: int = 0
    complexity_band: str = "Easy"

    def to_csv_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["item_kind"] = "pipeline"
        return row


@dataclass
class NotebookInventoryEntry:
    """One Synapse notebook inventoried for migration."""

    name: str
    cell_count: int
    magic_command_count: int
    language: str  # python | scala | sql | csharp
    complexity_score: int = 0
    complexity_band: str = "Easy"

    def to_csv_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["item_kind"] = "notebook"
        return row


@dataclass
class WavePlan:
    """A single migration wave -- units that can move together."""

    wave_number: int
    items: list[str]
    estimated_effort_days: float
    dependencies: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)


@dataclass
class CapacityRecommendation:
    """F-SKU recommendation produced by the capacity-recommendation mode."""

    recommended_sku: str
    rationale: str
    fallback_sku: str
    scaling_strategy: str


# ---------------------------------------------------------------------------
# Complexity scoring
# ---------------------------------------------------------------------------


def _band_for_score(score: int) -> str:
    """Return the band label for a numeric score."""
    for upper, label in COMPLEXITY_BANDS:
        if score <= upper:
            return label
    return "Very Hard"


def compute_complexity_score(item: dict[str, Any]) -> tuple[int, str]:
    """Compute (numeric_score, band) for a single inventoried item.

    Heuristics
    ----------
    Tables: row_count contribution (log10) x dependency contribution x type
        complexity multiplier. External tables and views are easier (shortcuts);
        columnstore + heavy distribution are harder.
    Pipelines: activity_count + (data flow penalty) + dependency_count.
    Notebooks: cell_count + (magic_command_count x 2) + language penalty.

    Args
    ----
    item: A dict-shaped record. Must contain ``item_kind`` in
        {table, pipeline, notebook} OR be a TableInventoryEntry / etc dataclass.

    Returns
    -------
    Tuple of (score, band) where band is one of "Easy" / "Medium" / "Hard" /
    "Very Hard".
    """
    kind = item.get("item_kind", "table")

    if kind == "table":
        rows = max(1, int(item.get("row_count", 1)))
        deps = item.get("dependencies", [])
        if isinstance(deps, str):
            deps = [d for d in deps.split("|") if d]
        dep_count = len(deps)

        # log10 row-count contribution: 1k=3, 1M=6, 1B=9
        import math

        row_term = max(1, int(math.log10(rows)))
        dep_term = 1 + (dep_count * 2)

        type_multiplier = {
            "external": 0.5,  # often becomes a OneLake shortcut -- easy
            "view": 0.7,
            "heap": 1.0,
            "columnstore": 1.5,
        }.get(str(item.get("type", "heap")).lower(), 1.0)

        dist_multiplier = {
            "HASH": 1.3,
            "REPLICATE": 1.1,
            "ROUND_ROBIN": 1.0,
            "NONE": 1.0,
        }.get(str(item.get("distribution_type", "NONE")).upper(), 1.0)

        score = int(row_term * dep_term * type_multiplier * dist_multiplier)

    elif kind == "pipeline":
        activities = int(item.get("activity_count", 0))
        has_df = bool(item.get("has_data_flow", False))
        dep_count = int(item.get("dependency_count", 0))
        # Mapping Data Flows are the single most expensive Synapse-to-Fabric task.
        score = activities + (40 if has_df else 0) + (dep_count * 3)

    elif kind == "notebook":
        cells = int(item.get("cell_count", 0))
        magics = int(item.get("magic_command_count", 0))
        lang = str(item.get("language", "python")).lower()
        lang_penalty = {"python": 0, "sql": 0, "scala": 5, "csharp": 15}.get(lang, 5)
        score = cells + (magics * 2) + lang_penalty

    else:
        score = 0

    return score, _band_for_score(score)


# ---------------------------------------------------------------------------
# Mode 1 -- inventory
# ---------------------------------------------------------------------------


def inventory_synapse_workspace(
    workspace: str,
    rg: str,
    output_dir: str | Path,
    mock: bool = False,
) -> dict[str, Any]:
    """Inventory a Synapse workspace and emit assessment artifacts.

    When ``mock=True`` a synthetic inventory is generated; no Azure calls are
    made. When ``mock=False`` the function authenticates with
    DefaultAzureCredential and queries the Synapse management plane.

    Args
    ----
    workspace: Synapse workspace name.
    rg: Resource group containing the workspace.
    output_dir: Directory to write inventory.csv, complexity_scores.csv,
        dependency_graph.json, unsupported_features.md.
    mock: If True, generate a synthetic inventory without contacting Azure.

    Returns
    -------
    Dict with keys: ``tables``, ``pipelines``, ``notebooks``, ``unsupported``,
    and ``output_dir``.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    logger.info("Inventorying Synapse workspace %s (rg=%s, mock=%s)", workspace, rg, mock)

    if mock:
        records = generate_mock_inventory(out)
    else:
        if not _AZURE_SDK_AVAILABLE:
            raise RuntimeError(
                "Azure SDK not available "
                f"(import error: {_AZURE_IMPORT_ERROR}). "
                "Install with: pip install azure-mgmt-synapse azure-identity\n"
                "Or pass --mock-mode for offline testing."
            )
        records = _inventory_via_azure(workspace, rg)

    # Score each record
    for table in records["tables"]:
        table.complexity_score, table.complexity_band = compute_complexity_score(
            table.to_csv_row()
        )
    for pipeline in records["pipelines"]:
        pipeline.complexity_score, pipeline.complexity_band = compute_complexity_score(
            pipeline.to_csv_row()
        )
    for nb in records["notebooks"]:
        nb.complexity_score, nb.complexity_band = compute_complexity_score(nb.to_csv_row())

    unsupported = _detect_unsupported_features(records)

    _write_inventory_csv(out / "inventory.csv", records)
    _write_complexity_csv(out / "complexity_scores.csv", records)
    _write_dependency_graph(out / "dependency_graph.json", records)
    _write_unsupported_md(out / "unsupported_features.md", unsupported)

    logger.info(
        "Inventory complete: %d tables, %d pipelines, %d notebooks, %d unsupported features",
        len(records["tables"]),
        len(records["pipelines"]),
        len(records["notebooks"]),
        len(unsupported),
    )

    return {
        "tables": records["tables"],
        "pipelines": records["pipelines"],
        "notebooks": records["notebooks"],
        "unsupported": unsupported,
        "output_dir": str(out),
    }


def _inventory_via_azure(workspace: str, rg: str) -> dict[str, list[Any]]:  # pragma: no cover
    """Pull live inventory from Synapse management plane.

    NOTE: This walks the management API. For per-row table sizing it would
    additionally need a Dedicated SQL Pool connection (pyodbc) and a Spark
    metrics extraction step. For Phase 14 Wave 4 we capture the topology and
    leave the deep T-SQL stats to ``02_schema_conversion.py``.
    """
    credential = DefaultAzureCredential()
    sub_id = _resolve_subscription_id()
    client = SynapseManagementClient(credential, sub_id)

    tables: list[TableInventoryEntry] = []
    pipelines: list[PipelineInventoryEntry] = []
    notebooks: list[NotebookInventoryEntry] = []

    # SQL pools and Spark pools -- topology only at this layer.
    for pool in client.sql_pools.list_by_workspace(rg, workspace):
        # Each SQL pool would be drilled into via INFORMATION_SCHEMA in
        # 02_schema_conversion.py. For inventory we record the pool itself
        # as a pseudo-table so it shows up in the wave plan.
        tables.append(
            TableInventoryEntry(
                table_name=pool.name,
                schema="dbo",
                type="columnstore",
                row_count=0,
                size_gb=0.0,
                last_used="unknown",
                distribution_type="NONE",
            )
        )

    # Pipelines and notebooks live on the artifacts plane; the management SDK
    # exposes them indirectly. The Wave 9 follow-up integrates the Synapse
    # artifacts SDK; here we leave a TODO and rely on mock-mode for the demo.
    logger.warning(
        "Live pipeline/notebook enumeration requires the Synapse artifacts SDK "
        "(planned for Wave 9). Use --mock-mode for a complete demo inventory."
    )

    return {"tables": tables, "pipelines": pipelines, "notebooks": notebooks}


def _resolve_subscription_id() -> str:  # pragma: no cover -- requires Azure SDK
    """Resolve the active Azure subscription id from environment or CLI context."""
    import os

    sub_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    if not sub_id:
        raise RuntimeError(
            "AZURE_SUBSCRIPTION_ID not set. Either export it or run "
            "`az account set --subscription <id>` and re-run."
        )
    return sub_id


def _detect_unsupported_features(records: dict[str, list[Any]]) -> list[dict[str, str]]:
    """Scan inventory for Synapse features that don't have a 1:1 Fabric equivalent."""
    found: list[dict[str, str]] = []
    seen_keys: set[str] = set()

    for table in records["tables"]:
        if table.distribution_type and table.distribution_type.upper() in {
            "HASH",
            "REPLICATE",
            "ROUND_ROBIN",
        }:
            key = f"DISTRIBUTION_{table.distribution_type.upper()}"
            if key not in seen_keys:
                seen_keys.add(key)
                rule = f"DISTRIBUTION = {table.distribution_type.upper()}"
                found.append(
                    {
                        "object": f"{table.schema}.{table.table_name}",
                        "feature": rule,
                        "remediation": UNSUPPORTED_FEATURE_RULES.get(rule, "Review."),
                    }
                )
        if str(table.type).lower() == "external" and "EXTERNAL TABLE" not in seen_keys:
            seen_keys.add("EXTERNAL TABLE")
            found.append(
                {
                    "object": f"{table.schema}.{table.table_name}",
                    "feature": "EXTERNAL TABLE",
                    "remediation": UNSUPPORTED_FEATURE_RULES["EXTERNAL TABLE"],
                }
            )

    for pipeline in records["pipelines"]:
        if pipeline.has_data_flow and "MAPPING_DATA_FLOW" not in seen_keys:
            seen_keys.add("MAPPING_DATA_FLOW")
            found.append(
                {
                    "object": pipeline.name,
                    "feature": "Mapping Data Flow",
                    "remediation": UNSUPPORTED_FEATURE_RULES["MAPPING_DATA_FLOW"],
                }
            )

    return found


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def _write_inventory_csv(path: Path, records: dict[str, list[Any]]) -> None:
    """Serialize all three inventory categories into a single flat CSV."""
    rows: list[dict[str, Any]] = []
    rows.extend(t.to_csv_row() for t in records["tables"])
    rows.extend(p.to_csv_row() for p in records["pipelines"])
    rows.extend(n.to_csv_row() for n in records["notebooks"])

    if not rows:
        logger.warning("No inventory rows to write.")
        path.write_text("item_kind\n", encoding="utf-8")
        return

    # Build a stable union of keys across the three kinds.
    field_set: set[str] = set()
    for row in rows:
        field_set.update(row.keys())
    fieldnames = sorted(field_set)

    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    logger.info("Wrote inventory CSV: %s (%d rows)", path, len(rows))


def _write_complexity_csv(path: Path, records: dict[str, list[Any]]) -> None:
    """Emit a focused (item_kind, name, score, band) ranking CSV."""
    rows: list[dict[str, Any]] = []
    for t in records["tables"]:
        rows.append(
            {
                "item_kind": "table",
                "name": f"{t.schema}.{t.table_name}",
                "complexity_score": t.complexity_score,
                "complexity_band": t.complexity_band,
            }
        )
    for p in records["pipelines"]:
        rows.append(
            {
                "item_kind": "pipeline",
                "name": p.name,
                "complexity_score": p.complexity_score,
                "complexity_band": p.complexity_band,
            }
        )
    for n in records["notebooks"]:
        rows.append(
            {
                "item_kind": "notebook",
                "name": n.name,
                "complexity_score": n.complexity_score,
                "complexity_band": n.complexity_band,
            }
        )
    rows.sort(key=lambda r: r["complexity_score"], reverse=True)

    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["item_kind", "name", "complexity_score", "complexity_band"],
        )
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Wrote complexity CSV: %s", path)


def _write_dependency_graph(path: Path, records: dict[str, list[Any]]) -> None:
    """Emit the dependency graph used by ``wave-plan`` to topologically order migrations."""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []

    for t in records["tables"]:
        full_name = f"{t.schema}.{t.table_name}"
        nodes.append(
            {
                "id": full_name,
                "kind": "table",
                "type": t.type,
                "complexity_band": t.complexity_band,
            }
        )
        for dep in t.dependencies:
            edges.append({"from": full_name, "to": dep})

    for p in records["pipelines"]:
        nodes.append(
            {
                "id": p.name,
                "kind": "pipeline",
                "complexity_band": p.complexity_band,
            }
        )
    for n in records["notebooks"]:
        nodes.append(
            {
                "id": n.name,
                "kind": "notebook",
                "complexity_band": n.complexity_band,
            }
        )

    graph = {
        "generated_at": _utcnow_iso(),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
    }
    path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    logger.info("Wrote dependency graph: %s", path)


def _write_unsupported_md(path: Path, unsupported: list[dict[str, str]]) -> None:
    """Emit a human-readable markdown report of unsupported features and remediations."""
    lines = [
        "# Unsupported Synapse Features",
        "",
        f"_Generated {_utcnow_iso()} by 01_assessment.py_",
        "",
    ]
    if not unsupported:
        lines.append("None detected. All Synapse constructs have a 1:1 Fabric equivalent.")
    else:
        lines.extend(
            [
                "The following Synapse features were detected and require manual handling.",
                "",
                "| Object | Feature | Remediation |",
                "|--------|---------|-------------|",
            ]
        )
        for item in unsupported:
            lines.append(
                f"| `{item['object']}` | `{item['feature']}` | {item['remediation']} |"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Wrote unsupported features report: %s", path)


# ---------------------------------------------------------------------------
# Mode 2 -- wave plan
# ---------------------------------------------------------------------------


def plan_migration_waves(
    inventory_csv: str | Path,
    max_effort_days: float,
) -> list[WavePlan]:
    """Produce a topologically-ordered, effort-bounded migration plan.

    Algorithm
    ---------
    1. Parse inventory.csv into (item_id, dependencies, complexity_band) tuples.
    2. Topologically sort the dependency graph (leaves first -- migrate things
       that nothing depends on first, things that everything depends on last).
    3. Pack items into successive waves capped at ``max_effort_days`` of
       cumulative estimated effort (using ``EFFORT_DAYS_PER_BAND``).
    4. A wave only starts after all of its dependencies are in earlier waves.

    Args
    ----
    inventory_csv: Path to inventory.csv emitted by ``inventory_synapse_workspace``.
    max_effort_days: Maximum cumulative effort per wave.

    Returns
    -------
    Ordered list of WavePlan objects (wave_number=1 is the first wave to run).
    Also writes ``migration-waves.md`` next to the inventory CSV.
    """
    inv_path = Path(inventory_csv)
    if not inv_path.exists():
        raise FileNotFoundError(f"Inventory CSV not found: {inv_path}")
    if max_effort_days <= 0:
        raise ValueError("max_effort_days must be positive.")

    items, dep_map = _parse_inventory_for_waves(inv_path)

    order = _topological_sort(items.keys(), dep_map)

    waves: list[WavePlan] = []
    current_wave_items: list[str] = []
    current_wave_effort = 0.0
    placed: set[str] = set()
    wave_number = 1

    for item_id in order:
        item_band = items[item_id]
        item_effort = EFFORT_DAYS_PER_BAND.get(item_band, 1.5)

        # Cannot start a wave until all dependencies are already placed.
        deps = dep_map.get(item_id, [])
        if any(d not in placed for d in deps if d in items):
            # Force a wave boundary -- finalize current wave first.
            if current_wave_items:
                waves.append(
                    WavePlan(
                        wave_number=wave_number,
                        items=list(current_wave_items),
                        estimated_effort_days=round(current_wave_effort, 2),
                        dependencies=[],
                    )
                )
                placed.update(current_wave_items)
                wave_number += 1
                current_wave_items = []
                current_wave_effort = 0.0

        if current_wave_effort + item_effort > max_effort_days and current_wave_items:
            waves.append(
                WavePlan(
                    wave_number=wave_number,
                    items=list(current_wave_items),
                    estimated_effort_days=round(current_wave_effort, 2),
                    dependencies=[],
                )
            )
            placed.update(current_wave_items)
            wave_number += 1
            current_wave_items = []
            current_wave_effort = 0.0

        current_wave_items.append(item_id)
        current_wave_effort += item_effort

    if current_wave_items:
        waves.append(
            WavePlan(
                wave_number=wave_number,
                items=list(current_wave_items),
                estimated_effort_days=round(current_wave_effort, 2),
                dependencies=[],
            )
        )

    # Detect blockers: items with deps outside the inventory.
    for wave in waves:
        for item_id in wave.items:
            for dep in dep_map.get(item_id, []):
                if dep not in items:
                    wave.blockers.append(f"{item_id} depends on external object `{dep}`")

    output_md = inv_path.parent / "migration-waves.md"
    _write_waves_md(output_md, waves)
    logger.info("Wrote migration plan: %s (%d waves)", output_md, len(waves))
    return waves


def _parse_inventory_for_waves(
    inv_path: Path,
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Extract item_id -> band and item_id -> [deps] from inventory.csv."""
    items: dict[str, str] = {}
    dep_map: dict[str, list[str]] = defaultdict(list)

    with inv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            kind = (row.get("item_kind") or "").strip()
            band = (row.get("complexity_band") or "Easy").strip() or "Easy"
            if kind == "table":
                item_id = f"{row.get('schema', 'dbo')}.{row.get('table_name', '?')}"
                deps_raw = row.get("dependencies", "") or ""
                deps = [d for d in deps_raw.split("|") if d]
            elif kind in {"pipeline", "notebook"}:
                item_id = row.get("name", "?")
                deps = []
            else:
                continue
            items[item_id] = band
            if deps:
                dep_map[item_id] = deps

    return items, dict(dep_map)


def _topological_sort(
    nodes: Any,  # iterable of node ids
    dep_map: dict[str, list[str]],
) -> list[str]:
    """Kahn's algorithm: leaves (no dependencies) first.

    Items with circular or external dependencies are appended at the end with
    a warning logged.
    """
    nodes_list = list(nodes)
    in_degree: dict[str, int] = {n: 0 for n in nodes_list}
    out_edges: dict[str, list[str]] = defaultdict(list)

    for child, parents in dep_map.items():
        for parent in parents:
            if parent in in_degree:
                in_degree[child] = in_degree.get(child, 0) + 1
                out_edges[parent].append(child)

    queue: deque[str] = deque(sorted(n for n, d in in_degree.items() if d == 0))
    order: list[str] = []
    while queue:
        n = queue.popleft()
        order.append(n)
        for child in out_edges.get(n, []):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    leftovers = [n for n in nodes_list if n not in order]
    if leftovers:
        logger.warning(
            "Cyclic or unresolved dependencies detected for %d items: %s",
            len(leftovers),
            ", ".join(leftovers[:5]),
        )
        order.extend(leftovers)

    return order


def _write_waves_md(path: Path, waves: list[WavePlan]) -> None:
    """Emit migration-waves.md with one section per wave."""
    lines = [
        "# Migration Wave Plan",
        "",
        f"_Generated {_utcnow_iso()} by 01_assessment.py_",
        "",
        f"**Total waves:** {len(waves)}",
        f"**Total estimated effort:** "
        f"{sum(w.estimated_effort_days for w in waves):.1f} person-days",
        "",
        "Migrate Wave 1 first; each subsequent wave can start once the previous "
        "wave's items have passed three-tier validation (see Tutorial 41 Step 8).",
        "",
    ]
    for wave in waves:
        lines.extend(
            [
                f"## Wave {wave.wave_number}",
                "",
                f"- **Items:** {len(wave.items)}",
                f"- **Estimated effort:** {wave.estimated_effort_days} person-days",
                "",
                "### Items",
                "",
            ]
        )
        for item in wave.items:
            lines.append(f"- `{item}`")
        if wave.blockers:
            lines.extend(["", "### Blockers", ""])
            for blocker in wave.blockers:
                lines.append(f"- WARNING: {blocker}")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Mode 3 -- capacity recommendation
# ---------------------------------------------------------------------------


def recommend_capacity(
    inventory_csv: str | Path,
    dwu_baseline: int,
    spark_vcores: int,
    query_history_csv: str | Path | None = None,
) -> CapacityRecommendation:
    """Recommend a Fabric F-SKU from Synapse usage signals.

    Heuristic
    ---------
    1. Map DWU -> baseline F-SKU using the Tutorial 41 Step 7 table.
    2. If Spark vCore footprint implies a higher F-SKU floor, lift the
       recommendation to cover the unified CU pool.
    3. If query history shows p95 latency > 5s on common queries, suggest one
       step up; if p95 < 500ms across the board, leave headroom.
    4. Always emit a fallback (one step down) and a scaling strategy.

    Args
    ----
    inventory_csv: Path to inventory.csv (used for total size context).
    dwu_baseline: Steady-state DWU consumption.
    spark_vcores: Concurrent Spark vCores (peak).
    query_history_csv: Optional CSV with column ``duration_ms`` for p95 calc.

    Returns
    -------
    CapacityRecommendation with rationale text suitable for inclusion in a
    capacity-recommendation.md report. Also writes that report next to the
    inventory CSV.
    """
    inv_path = Path(inventory_csv)
    if not inv_path.exists():
        raise FileNotFoundError(f"Inventory CSV not found: {inv_path}")
    if dwu_baseline < 0 or spark_vcores < 0:
        raise ValueError("DWU baseline and Spark vCores must be non-negative.")

    total_size_gb = _sum_inventory_size_gb(inv_path)

    # Step 1: DWU -> base F-SKU
    base_sku = _dwu_to_fsku(dwu_baseline)

    # Step 2: Spark vCores floor
    spark_floor = _spark_vcores_to_min_fsku(spark_vcores)
    final_sku = _max_fsku(base_sku, spark_floor)
    spark_lift = final_sku != base_sku

    # Step 3: Query history adjustment
    p95_ms: float | None = None
    if query_history_csv:
        p95_ms = _query_history_p95_ms(Path(query_history_csv))

    if p95_ms is not None and p95_ms > 5000:
        final_sku = _step_fsku(final_sku, +1)
        latency_note = (
            f"Query p95 latency = {p95_ms:.0f}ms exceeds the 5s comfort band; "
            f"stepping up by one F-SKU to absorb concurrency headroom."
        )
    elif p95_ms is not None and p95_ms < 500:
        latency_note = (
            f"Query p95 latency = {p95_ms:.0f}ms is comfortable; current band held."
        )
    else:
        latency_note = "No query history provided; sized from DWU + Spark only."

    fallback = _step_fsku(final_sku, -1)
    rationale = (
        f"DWU baseline {dwu_baseline} -> {base_sku} from the Tutorial 41 Step 7 table. "
        + (
            f"Spark concurrency ({spark_vcores} vCores) lifts the floor to "
            f"{spark_floor}; final pick {final_sku}. "
            if spark_lift
            else f"Spark concurrency ({spark_vcores} vCores) fits within {base_sku}. "
        )
        + latency_note
        + f" Total inventoried size on disk: {total_size_gb:.1f} GB."
    )

    scaling_strategy = (
        f"Provision {final_sku} for steady-state. Pause to {fallback} during "
        f"low-traffic windows (Synapse pause is replaced by Fabric capacity "
        f"pause/scale -- see capacity-planning-cost-optimization.md). "
        f"Validate via 30-day CU consumption analysis before committing to a "
        f"reservation."
    )

    rec = CapacityRecommendation(
        recommended_sku=final_sku,
        rationale=rationale,
        fallback_sku=fallback,
        scaling_strategy=scaling_strategy,
    )

    out_md = inv_path.parent / "capacity-recommendation.md"
    _write_capacity_md(out_md, rec, dwu_baseline, spark_vcores, p95_ms, total_size_gb)
    logger.info("Wrote capacity recommendation: %s", out_md)

    return rec


def _dwu_to_fsku(dwu: int) -> str:
    """Map a DWU number to its starting F-SKU."""
    for upper, sku in DWU_TO_FSKU:
        if dwu <= upper:
            return sku
    return DWU_TO_FSKU[-1][1]


def _spark_vcores_to_min_fsku(vcores: int) -> str:
    """Floor F-SKU for the given Spark vCore peak."""
    for upper, sku in SPARK_VCORE_MIN_FSKU:
        if vcores <= upper:
            return sku
    return SPARK_VCORE_MIN_FSKU[-1][1]


_FSKU_LADDER: list[str] = [
    "F2",
    "F4",
    "F8",
    "F16",
    "F32",
    "F64",
    "F128",
    "F256",
    "F512",
    "F1024",
    "F2048",
]


def _fsku_index(sku: str) -> int:
    if sku not in _FSKU_LADDER:
        raise ValueError(f"Unknown F-SKU: {sku}")
    return _FSKU_LADDER.index(sku)


def _max_fsku(a: str, b: str) -> str:
    return a if _fsku_index(a) >= _fsku_index(b) else b


def _step_fsku(sku: str, delta: int) -> str:
    """Move ``delta`` rungs up (+) or down (-) the F-SKU ladder, clamped."""
    idx = max(0, min(len(_FSKU_LADDER) - 1, _fsku_index(sku) + delta))
    return _FSKU_LADDER[idx]


def _sum_inventory_size_gb(inv_path: Path) -> float:
    """Sum size_gb across all inventoried tables. Returns 0.0 if column missing."""
    total = 0.0
    with inv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                total += float(row.get("size_gb") or 0)
            except ValueError:
                continue
    return total


def _query_history_p95_ms(path: Path) -> float | None:
    """Compute p95 of the ``duration_ms`` column from a query history export."""
    if not path.exists():
        logger.warning("Query history CSV not found: %s -- skipping latency adjustment", path)
        return None
    durations: list[float] = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            val = row.get("duration_ms") or row.get("duration") or row.get("elapsed_ms")
            try:
                if val is not None:
                    durations.append(float(val))
            except ValueError:
                continue
    if not durations:
        return None
    durations.sort()
    idx = int(0.95 * (len(durations) - 1))
    return durations[idx]


def _write_capacity_md(
    path: Path,
    rec: CapacityRecommendation,
    dwu: int,
    vcores: int,
    p95_ms: float | None,
    size_gb: float,
) -> None:
    """Render the human-readable capacity recommendation report."""
    p95_text = f"{p95_ms:.0f} ms" if p95_ms is not None else "not provided"
    body = f"""# Fabric Capacity Recommendation

_Generated {_utcnow_iso()} by 01_assessment.py_

## Recommendation

| Field | Value |
|-------|-------|
| **Recommended F-SKU** | **{rec.recommended_sku}** |
| Fallback F-SKU | {rec.fallback_sku} |
| DWU baseline | {dwu} |
| Spark pool peak vCores | {vcores} |
| Query p95 latency | {p95_text} |
| Total inventoried size | {size_gb:.1f} GB |

## Rationale

{rec.rationale}

## Scaling Strategy

{rec.scaling_strategy}

## Validation Plan

1. Provision the recommended F-SKU as a non-prod capacity for the coexistence period.
2. Run identical workloads against Synapse and Fabric for 14 days.
3. Compare CU consumption to F-SKU ceiling (target steady-state band 40-70%).
4. If consistently > 70%, step up; if consistently < 30%, step down.
5. See `../../docs/best-practices/capacity-planning-cost-optimization.md`.
"""
    path.write_text(body, encoding="utf-8")


# ---------------------------------------------------------------------------
# Mock inventory generator (offline / CI testing)
# ---------------------------------------------------------------------------


def generate_mock_inventory(
    output_dir: str | Path,
) -> dict[str, list[Any]]:
    """Generate a deterministic synthetic inventory for offline testing.

    Produces 50 tables, 10 pipelines, 5 notebooks with realistic-shaped
    distributions (heap/columnstore/external mix, dependency edges across
    Bronze -> Silver -> Gold layers, two pipelines with Mapping Data Flows,
    one Scala notebook).

    Args
    ----
    output_dir: Directory used by the caller (passed through; this function
        does not write directly -- the caller serializes the records).

    Returns
    -------
    Dict with keys ``tables``, ``pipelines``, ``notebooks`` containing the
    synthesized dataclasses.
    """
    import random

    rng = random.Random(42)
    _ = output_dir  # for symmetry with real inventory; writes happen upstream

    distributions = ["HASH", "REPLICATE", "ROUND_ROBIN", "NONE"]
    types = ["heap", "columnstore", "columnstore", "external", "view"]

    tables: list[TableInventoryEntry] = []
    layer_tables: dict[str, list[str]] = {"bronze": [], "silver": [], "gold": []}

    for i in range(50):
        if i < 20:
            layer = "bronze"
        elif i < 40:
            layer = "silver"
        else:
            layer = "gold"

        schema = layer
        name = f"{layer}_table_{i:02d}"
        deps: list[str] = []
        if layer == "silver" and layer_tables["bronze"]:
            deps = rng.sample(
                layer_tables["bronze"], k=rng.randint(1, min(3, len(layer_tables["bronze"])))
            )
        elif layer == "gold" and layer_tables["silver"]:
            deps = rng.sample(
                layer_tables["silver"], k=rng.randint(1, min(2, len(layer_tables["silver"])))
            )

        rows = rng.choice([1_000, 100_000, 10_000_000, 1_000_000_000])
        tables.append(
            TableInventoryEntry(
                table_name=name,
                schema=schema,
                type=rng.choice(types),
                row_count=rows,
                size_gb=round(rows / 1_000_000 * rng.uniform(0.8, 2.0), 2),
                last_used=datetime.now(timezone.utc).date().isoformat(),
                distribution_type=rng.choice(distributions),
                dependencies=[f"{schema}.{d}" if "." not in d else d for d in deps],
            )
        )
        layer_tables[layer].append(name)

    pipelines: list[PipelineInventoryEntry] = []
    for i in range(10):
        pipelines.append(
            PipelineInventoryEntry(
                name=f"pipeline_{i:02d}",
                activity_count=rng.randint(2, 30),
                has_data_flow=(i in {3, 7}),
                dependency_count=rng.randint(0, 5),
            )
        )

    notebooks: list[NotebookInventoryEntry] = []
    languages = ["python", "python", "python", "sql", "scala"]
    for i in range(5):
        notebooks.append(
            NotebookInventoryEntry(
                name=f"notebook_{i:02d}",
                cell_count=rng.randint(5, 60),
                magic_command_count=rng.randint(0, 5),
                language=languages[i],
            )
        )

    logger.info(
        "Generated mock inventory: %d tables, %d pipelines, %d notebooks",
        len(tables),
        len(pipelines),
        len(notebooks),
    )
    return {"tables": tables, "pipelines": pipelines, "notebooks": notebooks}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Build the argparse subcommand tree."""
    parser = argparse.ArgumentParser(
        prog="01_assessment.py",
        description=(
            "Synapse -> Fabric assessment, wave planning, and capacity "
            "recommendation (Tutorial 41 / Phase 14 Wave 4)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging.",
    )

    subparsers = parser.add_subparsers(dest="command", required=False)

    # Mode 1 -- inventory
    p_inv = subparsers.add_parser(
        "inventory",
        help="Catalog Synapse tables/pipelines/notebooks and score complexity.",
    )
    p_inv.add_argument("--synapse-workspace", default=None, help="Synapse workspace name.")
    p_inv.add_argument("--resource-group", default=None, help="Resource group name.")
    p_inv.add_argument(
        "--output-dir",
        default="./assessment-output",
        help="Directory to write inventory artifacts.",
    )
    p_inv.add_argument(
        "--mock-mode",
        action="store_true",
        help="Generate synthetic inventory without contacting Azure.",
    )

    # Mode 2 -- wave plan
    p_wp = subparsers.add_parser(
        "wave-plan",
        help="Produce migration wave order from an existing inventory.",
    )
    p_wp.add_argument("--inventory", required=True, help="Path to inventory.csv.")
    p_wp.add_argument(
        "--max-wave-effort-days",
        type=float,
        default=10.0,
        help="Maximum cumulative effort per wave (default: 10).",
    )

    # Mode 3 -- capacity recommendation
    p_cap = subparsers.add_parser(
        "capacity-recommendation",
        help="Recommend a Fabric F-SKU from DWU + Spark + query history.",
    )
    p_cap.add_argument("--inventory", required=True, help="Path to inventory.csv.")
    p_cap.add_argument(
        "--dwu-baseline", type=int, required=True, help="Steady-state DWU consumption."
    )
    p_cap.add_argument(
        "--spark-pool-vcores",
        type=int,
        default=0,
        help="Peak concurrent Spark vCores.",
    )
    p_cap.add_argument(
        "--query-history-csv",
        default=None,
        help="Optional CSV of query durations (column: duration_ms).",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    command = args.command or "inventory"

    try:
        if command == "inventory":
            result = inventory_synapse_workspace(
                workspace=args.synapse_workspace or "mock-workspace",
                rg=args.resource_group or "mock-rg",
                output_dir=args.output_dir,
                mock=args.mock_mode
                or not (args.synapse_workspace and args.resource_group),
            )
            if result["unsupported"]:
                logger.warning(
                    "Inventory complete with %d unsupported feature(s) detected.",
                    len(result["unsupported"]),
                )
                return 2
            return 0

        if command == "wave-plan":
            waves = plan_migration_waves(
                inventory_csv=args.inventory,
                max_effort_days=args.max_wave_effort_days,
            )
            logger.info("Wave plan complete: %d waves.", len(waves))
            return 0

        if command == "capacity-recommendation":
            rec = recommend_capacity(
                inventory_csv=args.inventory,
                dwu_baseline=args.dwu_baseline,
                spark_vcores=args.spark_pool_vcores,
                query_history_csv=args.query_history_csv,
            )
            logger.info(
                "Capacity recommendation: %s (fallback %s).",
                rec.recommended_sku,
                rec.fallback_sku,
            )
            return 0

        parser.print_help()
        return 1

    except FileNotFoundError as exc:
        logger.error("Input file not found: %s", exc)
        return 1
    except ValueError as exc:
        logger.error("Invalid input: %s", exc)
        return 1
    except RuntimeError as exc:
        logger.error("Runtime error: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
