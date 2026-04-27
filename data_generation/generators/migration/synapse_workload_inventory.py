"""
Synapse Workload Inventory Generator
=====================================

Synthetic Azure Synapse Analytics workspace inventory used by the
``tutorials/41-synapse-to-fabric/01_assessment.py --mock-mode`` flow as a
teaching artifact for tutorial readers who do not have a real Synapse
workspace to assess.

The generator produces a coherent workspace consisting of:

- 30-100 tables across 3-5 schemas (bronze, silver, gold, staging, ref) with
  realistic mixes of Heap / Clustered Columnstore / External (PolyBase)
  table types and HASH / REPLICATE / ROUND_ROBIN distribution strategies.
- 10-30 pipelines with realistic activity counts; a small fraction contain
  Mapping Data Flows / Dataflow Gen2 (the migration "hard parts").
- 5-20 Spark notebooks (Python, SQL, Scala mix) with realistic cell counts
  and library imports.
- Dependencies between objects: silver tables read from bronze; gold reads
  from silver; pipelines load tables; notebooks read tables.

Casino-domain (slot_telemetry, player_canonical, fact_daily_revenue) and
federal-domain (usda_crop_production, sba_ppp_loans, noaa_storm_events)
table names are seeded into the pool so generated inventories are
recognizable to tutorial readers and to the wider POC.

Inheritance
-----------
:class:`SynapseWorkloadInventoryGenerator` extends :class:`BaseGenerator` and
implements :meth:`generate_record` (rotation across kinds), :meth:`generate_batch`,
and the workspace-shaped :meth:`generate_workspace` helper.

Output schema
-------------
The CSV emitted by :func:`to_csv` matches the columns expected by
``01_assessment.py`` (``item_kind``, ``schema``, ``table_name``,
``row_count``, ``size_gb``, ``last_used``, ``distribution_type``,
``dependencies``, ``complexity_score``, ``complexity_band``, ``name``,
``activity_count``, ``has_data_flow``, ``dependency_count``, ``cell_count``,
``magic_command_count``, ``language``).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

from ..base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# Schemas, kinds, and weights
# ---------------------------------------------------------------------------

SCHEMAS: list[str] = ["bronze", "silver", "gold", "staging", "ref"]
SCHEMA_WEIGHTS: list[float] = [0.30, 0.30, 0.20, 0.12, 0.08]

TABLE_TYPES: list[str] = ["heap", "columnstore", "external"]
TABLE_TYPE_WEIGHTS: list[float] = [0.20, 0.65, 0.15]

DISTRIBUTION_TYPES: list[str] = ["HASH", "REPLICATE", "ROUND_ROBIN"]
DISTRIBUTION_WEIGHTS: list[float] = [0.55, 0.20, 0.25]

NOTEBOOK_LANGUAGES: list[str] = ["python", "sql", "scala"]
NOTEBOOK_LANGUAGE_WEIGHTS: list[float] = [0.65, 0.25, 0.10]

PIPELINE_SCHEDULES: list[str] = ["hourly", "daily", "weekly", "manual", "event-driven"]
PIPELINE_SCHEDULE_WEIGHTS: list[float] = [0.18, 0.50, 0.10, 0.15, 0.07]

PIPELINE_RUN_STATUSES: list[str] = ["Succeeded", "Succeeded", "Succeeded", "Failed", "InProgress"]
PIPELINE_RUN_STATUS_WEIGHTS: list[float] = [0.55, 0.18, 0.12, 0.10, 0.05]

# Realistic complexity band distribution targeted by the generator.
COMPLEXITY_BAND_TARGETS: dict[str, float] = {
    "Easy": 0.50,
    "Medium": 0.30,
    "Hard": 0.15,
    "Very Hard": 0.05,
}

# ---------------------------------------------------------------------------
# Realistic table name pools (casino + federal flavors)
# ---------------------------------------------------------------------------

# Bronze: raw, minimally transformed -- mirrors actual repo notebooks/tables.
BRONZE_TABLES: list[str] = [
    "slot_telemetry",
    "table_games_actions",
    "player_signups",
    "player_loyalty_events",
    "cage_transactions",
    "compliance_alerts",
    "video_surveillance_events",
    "kiosk_telemetry",
    "iot_floor_sensors",
    "usda_crop_production",
    "usda_food_safety",
    "sba_ppp_loans",
    "sba_7a_loans",
    "noaa_storm_events",
    "noaa_climate_observations",
    "epa_air_quality",
    "epa_water_systems",
    "doi_park_visits",
    "doj_case_filings",
    "doj_court_dockets",
    "dot_faa_aircraft_registry",
    "tribal_health_encounters",
    "raw_clickstream",
    "raw_event_hub_capture",
]

SILVER_TABLES: list[str] = [
    "player_canonical",
    "slot_session_cleansed",
    "table_session_cleansed",
    "transaction_cleansed",
    "compliance_filings_validated",
    "video_events_enriched",
    "loyalty_member_dim",
    "usda_crop_yield_clean",
    "sba_loan_normalized",
    "noaa_storm_normalized",
    "epa_aqi_validated",
    "doi_visitation_clean",
    "doj_case_master",
    "patient_canonical",
    "claim_canonical",
    "device_telemetry_typed",
]

GOLD_TABLES: list[str] = [
    "fact_daily_revenue",
    "fact_player_lifetime_value",
    "fact_slot_performance",
    "fact_table_game_performance",
    "fact_compliance_summary",
    "dim_player",
    "dim_machine",
    "dim_date",
    "dim_geography",
    "kpi_floor_utilization",
    "kpi_revenue_per_machine_hour",
    "fact_usda_crop_kpis",
    "fact_sba_loan_outcomes",
    "fact_noaa_storm_impact",
    "fact_epa_compliance_score",
    "fact_doi_visitor_kpis",
    "fact_doj_case_disposition",
    "kpi_tribal_health_outcomes",
]

STAGING_TABLES: list[str] = [
    "stg_player_landing",
    "stg_slot_landing",
    "stg_loyalty_landing",
    "stg_compliance_landing",
    "stg_federal_open_data_landing",
    "stg_archive_drop",
    "stg_late_arriving_facts",
]

REF_TABLES: list[str] = [
    "ref_machine_master",
    "ref_paytable",
    "ref_w2g_thresholds",
    "ref_state_codes",
    "ref_currency_rates",
    "ref_naics_codes",
    "ref_fips_codes",
    "ref_compliance_rules",
]

# Plausible candidate hash-distribution columns for HASH-distributed tables.
HASH_KEY_CANDIDATES: list[str] = [
    "player_id",
    "machine_id",
    "transaction_id",
    "loan_id",
    "case_id",
    "patient_id",
    "device_id",
    "session_id",
    "event_id",
    "claim_id",
    "filing_id",
]

# Common Spark library imports referenced by mock notebooks.
SPARK_LIBRARY_IMPORTS: list[str] = [
    "pyspark.sql",
    "pyspark.sql.functions",
    "delta.tables",
    "great_expectations",
    "pandas",
    "numpy",
    "scikit-learn",
    "xgboost",
    "mlflow",
    "azure.storage.blob",
    "azure.identity",
    "requests",
]

# Synapse-specific unsupported features that may be flagged on a table.
TABLE_UNSUPPORTED_FEATURES: list[str] = [
    "geography",
    "geometry",
    "hierarchyid",
    "sql_variant",
    "xml",
    "MASTER KEY",
    "WORKLOAD GROUP",
]

PARTITION_COLUMN_CANDIDATES: list[str] = [
    "event_date",
    "load_date",
    "transaction_date",
    "report_year",
    "fiscal_quarter",
    "ingestion_hour",
]

# Common Synapse Spark pool naming patterns.
SPARK_POOL_NAMES: list[str] = ["sparkPoolSmall", "sparkPoolMedium", "sparkPoolLarge"]

ItemKind = Literal["table", "pipeline", "notebook"]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class SynapseTableMeta:
    """Metadata for a single Synapse Dedicated SQL pool table."""

    schema: str
    name: str
    table_type: str  # heap | columnstore | external
    row_count: int
    size_gb: float
    distribution: str  # HASH | REPLICATE | ROUND_ROBIN
    hash_key: str | None
    partitioned_by: str | None
    last_used_days_ago: int
    dependencies: list[str] = field(default_factory=list)
    unsupported_features: list[str] = field(default_factory=list)

    @property
    def fqn(self) -> str:
        """Fully qualified name (``schema.name``)."""
        return f"{self.schema}.{self.name}"

    def to_csv_row(self) -> dict[str, Any]:
        """Return an ``01_assessment.py``-compatible flat dict row."""
        last_used_iso = (
            datetime.now(timezone.utc).date() - timedelta(days=self.last_used_days_ago)
        ).isoformat()
        return {
            "item_kind": "table",
            "schema": self.schema,
            "table_name": self.name,
            "type": self.table_type,
            "row_count": self.row_count,
            "size_gb": round(self.size_gb, 3),
            "last_used": last_used_iso,
            "distribution_type": self.distribution,
            "hash_key": self.hash_key or "",
            "partitioned_by": self.partitioned_by or "",
            "dependencies": "|".join(self.dependencies),
            "unsupported_features": "|".join(self.unsupported_features),
        }


@dataclass
class SynapsePipelineMeta:
    """Metadata for a single Synapse Pipeline."""

    name: str
    activity_count: int
    has_data_flow: bool
    has_dataflow_g2: bool
    source_count: int
    sink_count: int
    schedule: str
    last_run_status: str
    dependencies: list[str] = field(default_factory=list)

    def to_csv_row(self) -> dict[str, Any]:
        """Return an ``01_assessment.py``-compatible flat dict row."""
        return {
            "item_kind": "pipeline",
            "name": self.name,
            "activity_count": self.activity_count,
            "has_data_flow": self.has_data_flow,
            "has_dataflow_g2": self.has_dataflow_g2,
            "source_count": self.source_count,
            "sink_count": self.sink_count,
            "schedule": self.schedule,
            "last_run_status": self.last_run_status,
            "dependency_count": len(self.dependencies),
            "dependencies": "|".join(self.dependencies),
        }


@dataclass
class SynapseNotebookMeta:
    """Metadata for a single Synapse Spark notebook."""

    name: str
    language: str  # python | sql | scala
    cell_count: int
    magic_command_count: int
    library_imports: list[str]
    attached_pool: str
    last_run_days_ago: int
    dependencies: list[str] = field(default_factory=list)

    def to_csv_row(self) -> dict[str, Any]:
        """Return an ``01_assessment.py``-compatible flat dict row."""
        return {
            "item_kind": "notebook",
            "name": self.name,
            "language": self.language,
            "cell_count": self.cell_count,
            "magic_command_count": self.magic_command_count,
            "library_imports": "|".join(self.library_imports),
            "attached_pool": self.attached_pool,
            "last_run_days_ago": self.last_run_days_ago,
            "dependencies": "|".join(self.dependencies),
        }


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


class SynapseWorkloadInventoryGenerator(BaseGenerator):
    """Synthetic Synapse workspace inventory for migration assessment tutorials.

    Generates a coherent Synapse workspace -- tables, pipelines, notebooks --
    with realistic dependency edges and a complexity-band distribution roughly
    matching what tutorial readers will see in real workspaces.

    Args
    ----
    seed: Random seed for reproducibility (BaseGenerator semantics).
    table_count: Total number of tables to generate. Clamped to [30, 100].
    pipeline_count: Total number of pipelines. Clamped to [10, 30].
    notebook_count: Total number of notebooks. Clamped to [5, 20].
    start_date: Lower bound for ``last_used`` derivation (BaseGenerator).
    end_date: Upper bound for ``last_used`` derivation (BaseGenerator).

    Examples
    --------
    >>> gen = SynapseWorkloadInventoryGenerator(seed=42)
    >>> ws = gen.generate_workspace()
    >>> assert 30 <= len(ws["tables"]) <= 100
    >>> assert 10 <= len(ws["pipelines"]) <= 30
    >>> assert 5 <= len(ws["notebooks"]) <= 20
    """

    KIND_ROTATION: tuple[ItemKind, ...] = ("table", "pipeline", "notebook")

    def __init__(
        self,
        seed: int | None = None,
        table_count: int = 50,
        pipeline_count: int = 15,
        notebook_count: int = 10,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> None:
        super().__init__(seed=seed, start_date=start_date, end_date=end_date)

        self.table_count = max(30, min(100, int(table_count)))
        self.pipeline_count = max(10, min(30, int(pipeline_count)))
        self.notebook_count = max(5, min(20, int(notebook_count)))

        self._workspace_cache: dict[str, list[Any]] | None = None
        self._record_pool: list[dict[str, Any]] | None = None
        self._record_cursor: int = 0

        self._schema = {
            # Shared
            "item_kind": "string",
            # Tables
            "schema": "string",
            "table_name": "string",
            "type": "string",
            "row_count": "int",
            "size_gb": "float",
            "last_used": "string",
            "distribution_type": "string",
            "hash_key": "string",
            "partitioned_by": "string",
            "dependencies": "string",
            "unsupported_features": "string",
            # Pipelines
            "name": "string",
            "activity_count": "int",
            "has_data_flow": "bool",
            "has_dataflow_g2": "bool",
            "source_count": "int",
            "sink_count": "int",
            "schedule": "string",
            "last_run_status": "string",
            "dependency_count": "int",
            # Notebooks
            "language": "string",
            "cell_count": "int",
            "magic_command_count": "int",
            "library_imports": "string",
            "attached_pool": "string",
            "last_run_days_ago": "int",
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_record(self) -> dict[str, Any]:
        """Generate one inventory record (rotates table -> pipeline -> notebook).

        Records are drawn from the cached workspace produced by
        :meth:`generate_workspace`. On first call (or after :meth:`reset`),
        the workspace is generated. Subsequent calls cycle through tables,
        pipelines, and notebooks in a deterministic rotation.

        Returns
        -------
        Flat dict row in the format expected by ``01_assessment.py``.
        """
        if self._record_pool is None:
            self._build_record_pool()

        assert self._record_pool is not None  # for type checker
        if not self._record_pool:
            raise RuntimeError("Generator produced an empty record pool.")

        record = self._record_pool[self._record_cursor % len(self._record_pool)]
        self._record_cursor += 1
        return record

    def generate_batch(self, n: int) -> list[dict[str, Any]]:  # type: ignore[override]
        """Generate ``n`` records by drawing from the cached workspace pool.

        Args
        ----
        n: Number of records to return. Must be a positive integer.

        Returns
        -------
        List of ``n`` flat dict rows. May repeat records if ``n`` exceeds
        the workspace pool size.
        """
        if not isinstance(n, int) or n <= 0:
            raise ValueError(f"n must be a positive integer, got {n}")
        return [self.generate_record() for _ in range(n)]

    def generate_workspace(self) -> dict[str, Any]:
        """Generate (or return cached) full Synapse workspace inventory.

        Returns
        -------
        Dict with keys:
            - ``tables``: list[SynapseTableMeta]
            - ``pipelines``: list[SynapsePipelineMeta]
            - ``notebooks``: list[SynapseNotebookMeta]
            - ``dependency_graph``: dict[str, list[str]] keyed by FQN/name
            - ``generated_at``: ISO timestamp string
        """
        if self._workspace_cache is not None:
            cached_graph = self._build_dependency_graph(
                self._workspace_cache["tables"],
                self._workspace_cache["pipelines"],
                self._workspace_cache["notebooks"],
            )
            return {
                "tables": self._workspace_cache["tables"],
                "pipelines": self._workspace_cache["pipelines"],
                "notebooks": self._workspace_cache["notebooks"],
                "dependency_graph": cached_graph,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        tables = self._build_tables(self.table_count)
        pipelines = self._build_pipelines(self.pipeline_count, tables)
        notebooks = self._build_notebooks(self.notebook_count, tables)

        self._workspace_cache = {
            "tables": tables,
            "pipelines": pipelines,
            "notebooks": notebooks,
        }

        return {
            "tables": tables,
            "pipelines": pipelines,
            "notebooks": notebooks,
            "dependency_graph": self._build_dependency_graph(tables, pipelines, notebooks),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def reset(self) -> None:
        """Clear cached workspace so the next call regenerates fresh data."""
        self._workspace_cache = None
        self._record_pool = None
        self._record_cursor = 0

    # ------------------------------------------------------------------
    # Workspace builders
    # ------------------------------------------------------------------

    def _build_tables(self, total: int) -> list[SynapseTableMeta]:
        """Build ``total`` tables across schemas with realistic dependency edges."""
        # Allocate per-schema counts via weighted sampling.
        schema_counts: dict[str, int] = dict.fromkeys(SCHEMAS, 0)
        for _ in range(total):
            chosen = self.weighted_choice(SCHEMAS, SCHEMA_WEIGHTS)
            schema_counts[str(chosen)] += 1

        bronze_pool = list(BRONZE_TABLES)
        silver_pool = list(SILVER_TABLES)
        gold_pool = list(GOLD_TABLES)
        staging_pool = list(STAGING_TABLES)
        ref_pool = list(REF_TABLES)

        per_schema_pools: dict[str, list[str]] = {
            "bronze": bronze_pool,
            "silver": silver_pool,
            "gold": gold_pool,
            "staging": staging_pool,
            "ref": ref_pool,
        }

        tables: list[SynapseTableMeta] = []
        names_by_schema: dict[str, list[str]] = {s: [] for s in SCHEMAS}

        # Build tables in dependency order so silver can reference bronze, etc.
        for schema in ["ref", "staging", "bronze", "silver", "gold"]:
            count_for_schema = schema_counts[schema]
            pool = per_schema_pools[schema]
            for i in range(count_for_schema):
                name = self._unique_table_name(pool, taken=names_by_schema[schema], idx=i)
                table = self._build_one_table(schema, name, names_by_schema)
                tables.append(table)
                names_by_schema[schema].append(name)

        return tables

    def _unique_table_name(
        self,
        pool: list[str],
        taken: list[str],
        idx: int,
    ) -> str:
        """Return a unique table name -- prefer pool entries, then suffix."""
        available = [n for n in pool if n not in taken]
        if available:
            return str(self.rng.choice(available))
        # Fall back to a synthetic suffix if the pool is exhausted.
        base = str(self.rng.choice(pool))
        return f"{base}_v{idx + 2}"

    def _build_one_table(
        self,
        schema: str,
        name: str,
        existing_names_by_schema: dict[str, list[str]],
    ) -> SynapseTableMeta:
        """Build a single ``SynapseTableMeta`` with realistic distribution edges."""
        table_type = str(self.weighted_choice(TABLE_TYPES, TABLE_TYPE_WEIGHTS))

        # External tables and ref tables skew toward smaller / round-robin shapes.
        if table_type == "external":
            distribution = "ROUND_ROBIN"
        elif schema == "ref":
            distribution = "REPLICATE"
        else:
            distribution = str(
                self.weighted_choice(DISTRIBUTION_TYPES, DISTRIBUTION_WEIGHTS)
            )

        hash_key: str | None = None
        if distribution == "HASH":
            hash_key = str(self.rng.choice(HASH_KEY_CANDIDATES))

        # Right-skewed row count distribution: lots of small ref tables, a few huge facts.
        row_count = self._weighted_row_count(schema)
        size_gb = self._row_count_to_size_gb(row_count, table_type)

        # Optional partitioning (more common on bronze/silver large tables).
        partitioned_by: str | None = None
        if schema in {"bronze", "silver"} and row_count > 1_000_000 and self.rng.random() < 0.55:
            partitioned_by = str(self.rng.choice(PARTITION_COLUMN_CANDIDATES))

        last_used_days_ago = self._weighted_last_used()

        # Dependencies: silver reads bronze (1-3 deps), gold reads silver (1-2 deps).
        dependencies: list[str] = []
        if schema == "silver" and existing_names_by_schema.get("bronze"):
            k = int(self.rng.integers(1, min(4, len(existing_names_by_schema["bronze"]) + 1)))
            sampled = self.rng.choice(
                existing_names_by_schema["bronze"], size=k, replace=False
            )
            dependencies = [f"bronze.{n}" for n in sampled]
        elif schema == "gold" and existing_names_by_schema.get("silver"):
            k = int(self.rng.integers(1, min(3, len(existing_names_by_schema["silver"]) + 1)))
            sampled = self.rng.choice(
                existing_names_by_schema["silver"], size=k, replace=False
            )
            dependencies = [f"silver.{n}" for n in sampled]
        elif schema == "staging" and existing_names_by_schema.get("ref") and self.rng.random() < 0.30:
            ref_dep = str(self.rng.choice(existing_names_by_schema["ref"]))
            dependencies = [f"ref.{ref_dep}"]

        # Unsupported features -- only a small fraction of tables hit these.
        unsupported_features: list[str] = []
        if self.rng.random() < 0.08:
            unsupported_features.append(
                str(self.rng.choice(TABLE_UNSUPPORTED_FEATURES))
            )

        return SynapseTableMeta(
            schema=schema,
            name=name,
            table_type=table_type,
            row_count=row_count,
            size_gb=size_gb,
            distribution=distribution,
            hash_key=hash_key,
            partitioned_by=partitioned_by,
            last_used_days_ago=last_used_days_ago,
            dependencies=dependencies,
            unsupported_features=unsupported_features,
        )

    def _build_pipelines(
        self,
        total: int,
        tables: list[SynapseTableMeta],
    ) -> list[SynapsePipelineMeta]:
        """Build ``total`` pipelines with realistic activity counts and source/sink edges."""
        pipelines: list[SynapsePipelineMeta] = []
        # ~15 % of pipelines contain a Mapping Data Flow (the migration "hard part").
        target_data_flows = max(1, int(round(total * 0.15)))

        bronze_silver_tables = [t for t in tables if t.schema in {"bronze", "silver"}]
        all_table_fqns = [t.fqn for t in tables]

        for i in range(total):
            name = f"pl_{self._pipeline_purpose(i)}_{i:02d}"
            has_data_flow = i < target_data_flows
            has_dataflow_g2 = (i >= target_data_flows) and (self.rng.random() < 0.10)

            # Activity count distribution:
            # - small loaders: 2-8
            # - mid pipelines: 8-20
            # - heavy orchestrators: 20-40
            tier = self.rng.random()
            if tier < 0.50:
                activity_count = int(self.rng.integers(2, 9))
            elif tier < 0.85:
                activity_count = int(self.rng.integers(8, 21))
            else:
                activity_count = int(self.rng.integers(20, 41))

            source_count = int(self.rng.integers(1, 5))
            sink_count = int(self.rng.integers(1, 4))

            schedule = str(self.weighted_choice(PIPELINE_SCHEDULES, PIPELINE_SCHEDULE_WEIGHTS))
            last_run_status = str(
                self.weighted_choice(PIPELINE_RUN_STATUSES, PIPELINE_RUN_STATUS_WEIGHTS)
            )

            # Dependencies: tables this pipeline reads/writes.
            dep_pool = bronze_silver_tables if bronze_silver_tables else tables
            dep_size = min(source_count + sink_count, max(1, len(dep_pool)))
            sampled = self.rng.choice(
                [t.fqn for t in dep_pool], size=dep_size, replace=False
            ) if dep_pool else []
            dependencies = [str(d) for d in sampled]

            # 10 % of pipelines have an Execute Pipeline edge to an upstream pipeline.
            if i > 0 and self.rng.random() < 0.10:
                upstream = pipelines[int(self.rng.integers(0, i))].name
                dependencies.append(upstream)

            # Sanity-check we picked at least one dep so wave plan can route.
            if not dependencies and all_table_fqns:
                dependencies = [str(self.rng.choice(all_table_fqns))]

            pipelines.append(
                SynapsePipelineMeta(
                    name=name,
                    activity_count=activity_count,
                    has_data_flow=has_data_flow,
                    has_dataflow_g2=has_dataflow_g2,
                    source_count=source_count,
                    sink_count=sink_count,
                    schedule=schedule,
                    last_run_status=last_run_status,
                    dependencies=dependencies,
                )
            )
        return pipelines

    def _pipeline_purpose(self, idx: int) -> str:
        """Return a recognizable pipeline purpose token (cycled for variety)."""
        purposes = [
            "ingest_bronze",
            "transform_silver",
            "publish_gold",
            "compliance_export",
            "federal_open_data_sync",
            "loyalty_etl",
            "video_analytics_etl",
            "iot_telemetry_etl",
            "kpi_refresh",
            "audit_archive",
        ]
        return purposes[idx % len(purposes)]

    def _build_notebooks(
        self,
        total: int,
        tables: list[SynapseTableMeta],
    ) -> list[SynapseNotebookMeta]:
        """Build ``total`` Spark notebooks with realistic shape and table dependencies."""
        notebooks: list[SynapseNotebookMeta] = []
        all_table_fqns = [t.fqn for t in tables]

        for i in range(total):
            language = str(
                self.weighted_choice(NOTEBOOK_LANGUAGES, NOTEBOOK_LANGUAGE_WEIGHTS)
            )

            # Cell count: bell-curve-ish around 15-30, long tail to 60.
            tier = self.rng.random()
            if tier < 0.20:
                cell_count = int(self.rng.integers(5, 15))
            elif tier < 0.85:
                cell_count = int(self.rng.integers(15, 35))
            else:
                cell_count = int(self.rng.integers(35, 61))

            magic_command_count = int(self.rng.integers(0, max(1, cell_count // 5) + 1))

            # Library imports: 2-6 per notebook.
            n_libs = int(self.rng.integers(2, 7))
            sampled_libs = self.rng.choice(
                SPARK_LIBRARY_IMPORTS, size=n_libs, replace=False
            )
            library_imports = [str(s) for s in sampled_libs]

            attached_pool = str(self.rng.choice(SPARK_POOL_NAMES))
            last_run_days_ago = self._weighted_last_used()

            # 0-3 table dependencies per notebook.
            dep_count = int(self.rng.integers(0, 4))
            dependencies: list[str] = []
            if dep_count > 0 and all_table_fqns:
                dep_size = min(dep_count, len(all_table_fqns))
                sampled = self.rng.choice(
                    all_table_fqns, size=dep_size, replace=False
                )
                dependencies = [str(d) for d in sampled]

            notebook_name = f"nb_{self._notebook_purpose(i)}_{i:02d}"
            notebooks.append(
                SynapseNotebookMeta(
                    name=notebook_name,
                    language=language,
                    cell_count=cell_count,
                    magic_command_count=magic_command_count,
                    library_imports=library_imports,
                    attached_pool=attached_pool,
                    last_run_days_ago=last_run_days_ago,
                    dependencies=dependencies,
                )
            )
        return notebooks

    def _notebook_purpose(self, idx: int) -> str:
        """Return a recognizable notebook purpose token (cycled for variety)."""
        purposes = [
            "bronze_ingest_slot",
            "silver_player_canonical",
            "gold_revenue_kpis",
            "compliance_ctr_sar",
            "video_analytics_inference",
            "loyalty_segmentation",
            "iot_floor_aggregation",
            "federal_usda_etl",
            "federal_sba_etl",
            "ml_train_ltv_model",
        ]
        return purposes[idx % len(purposes)]

    # ------------------------------------------------------------------
    # Distribution helpers
    # ------------------------------------------------------------------

    def _weighted_row_count(self, schema: str) -> int:
        """Right-skewed row count distribution. Schema biases the band."""
        roll = self.rng.random()
        if schema == "ref":
            # Reference tables are tiny.
            return int(self.rng.integers(50, 50_001))
        if schema == "staging":
            return int(self.rng.integers(1_000, 10_000_001))
        if schema == "bronze":
            if roll < 0.20:
                return int(self.rng.integers(10_000, 1_000_001))
            if roll < 0.75:
                return int(self.rng.integers(1_000_000, 100_000_001))
            return int(self.rng.integers(100_000_000, 5_000_000_001))
        if schema == "silver":
            if roll < 0.30:
                return int(self.rng.integers(10_000, 1_000_001))
            if roll < 0.85:
                return int(self.rng.integers(1_000_000, 50_000_001))
            return int(self.rng.integers(50_000_000, 1_000_000_001))
        # gold
        if roll < 0.40:
            return int(self.rng.integers(1_000, 100_001))
        if roll < 0.90:
            return int(self.rng.integers(100_000, 10_000_001))
        return int(self.rng.integers(10_000_000, 200_000_001))

    def _row_count_to_size_gb(self, row_count: int, table_type: str) -> float:
        """Approximate size_gb from row_count -- heap is denser than columnstore."""
        # Bytes per row -- columnstore is much smaller post-compression.
        avg_bytes_per_row = {
            "heap": 800.0,
            "columnstore": 120.0,
            "external": 600.0,
        }.get(table_type, 500.0)
        size_bytes = row_count * avg_bytes_per_row
        size_gb = size_bytes / (1024.0 ** 3)
        # Add 5-15 % jitter for realism.
        jitter = 1.0 + float(self.rng.uniform(-0.05, 0.15))
        return max(0.001, size_gb * jitter)

    def _weighted_last_used(self) -> int:
        """Most objects used in last 30 days; small tail of dormant ones."""
        roll = self.rng.random()
        if roll < 0.55:
            return int(self.rng.integers(0, 8))
        if roll < 0.85:
            return int(self.rng.integers(8, 31))
        if roll < 0.97:
            return int(self.rng.integers(31, 121))
        return int(self.rng.integers(121, 731))

    # ------------------------------------------------------------------
    # Dependency graph + complexity scoring
    # ------------------------------------------------------------------

    def _build_dependency_graph(
        self,
        tables: list[SynapseTableMeta],
        pipelines: list[SynapsePipelineMeta],
        notebooks: list[SynapseNotebookMeta],
    ) -> dict[str, list[str]]:
        """Adjacency map keyed by FQN/name -> list of dependency identifiers."""
        graph: dict[str, list[str]] = {}
        for t in tables:
            graph[t.fqn] = list(t.dependencies)
        for p in pipelines:
            graph[p.name] = list(p.dependencies)
        for n in notebooks:
            graph[n.name] = list(n.dependencies)
        return graph

    def compute_complexity(self, item: dict[str, Any]) -> tuple[int, str]:
        """Compute (score, band) for a single item -- mirrors ``01_assessment.py``.

        Args
        ----
        item: A dict-shaped record (use the output of ``to_csv_row``).

        Returns
        -------
        Tuple of numeric score and band name (Easy / Medium / Hard / Very Hard).
        """
        kind = item.get("item_kind", "table")

        if kind == "table":
            rows = max(1, int(item.get("row_count", 1)))
            deps_raw = item.get("dependencies", "")
            dep_count = len([d for d in str(deps_raw).split("|") if d])
            row_term = max(1, int(math.log10(rows)))
            dep_term = 1 + (dep_count * 2)
            type_multiplier = {
                "external": 0.5,
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
            score = activities + (40 if has_df else 0) + (dep_count * 3)
        elif kind == "notebook":
            cells = int(item.get("cell_count", 0))
            magics = int(item.get("magic_command_count", 0))
            lang = str(item.get("language", "python")).lower()
            lang_penalty = {"python": 0, "sql": 0, "scala": 5, "csharp": 15}.get(lang, 5)
            score = cells + (magics * 2) + lang_penalty
        else:
            score = 0

        if score <= 10:
            band = "Easy"
        elif score <= 30:
            band = "Medium"
        elif score <= 70:
            band = "Hard"
        else:
            band = "Very Hard"
        return score, band

    def _build_record_pool(self) -> None:
        """Materialize the workspace as a flat list of dicts for ``generate_record``."""
        ws = self.generate_workspace()
        pool: list[dict[str, Any]] = []
        for t in ws["tables"]:
            row = t.to_csv_row()
            row["complexity_score"], row["complexity_band"] = self.compute_complexity(row)
            pool.append(row)
        for p in ws["pipelines"]:
            row = p.to_csv_row()
            row["complexity_score"], row["complexity_band"] = self.compute_complexity(row)
            pool.append(row)
        for n in ws["notebooks"]:
            row = n.to_csv_row()
            row["complexity_score"], row["complexity_band"] = self.compute_complexity(row)
            pool.append(row)
        self._record_pool = pool


# ---------------------------------------------------------------------------
# CSV / JSON serialization helpers
# ---------------------------------------------------------------------------


def to_csv(workspace_dict: dict[str, Any], output_dir: str | Path) -> dict[str, Path]:
    """Serialize a generated workspace to CSV + JSON artifacts.

    Writes:
    - ``inventory.csv`` -- flat table of all items (matches ``01_assessment.py``).
    - ``complexity_scores.csv`` -- (item_kind, name, score, band) ranking.
    - ``dependency_graph.json`` -- adjacency map keyed by FQN/name.

    Args
    ----
    workspace_dict: Output of :meth:`SynapseWorkloadInventoryGenerator.generate_workspace`.
    output_dir: Destination directory; created if missing.

    Returns
    -------
    Dict mapping artifact name -> output Path.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    tables: list[SynapseTableMeta] = workspace_dict["tables"]
    pipelines: list[SynapsePipelineMeta] = workspace_dict["pipelines"]
    notebooks: list[SynapseNotebookMeta] = workspace_dict["notebooks"]

    # Build flat rows + score them.
    rows: list[dict[str, Any]] = []
    complexity_rows: list[dict[str, Any]] = []
    scorer = SynapseWorkloadInventoryGenerator(seed=0)

    for t in tables:
        row = t.to_csv_row()
        row["complexity_score"], row["complexity_band"] = scorer.compute_complexity(row)
        rows.append(row)
        complexity_rows.append(
            {
                "item_kind": "table",
                "name": t.fqn,
                "complexity_score": row["complexity_score"],
                "complexity_band": row["complexity_band"],
            }
        )

    for p in pipelines:
        row = p.to_csv_row()
        row["complexity_score"], row["complexity_band"] = scorer.compute_complexity(row)
        rows.append(row)
        complexity_rows.append(
            {
                "item_kind": "pipeline",
                "name": p.name,
                "complexity_score": row["complexity_score"],
                "complexity_band": row["complexity_band"],
            }
        )

    for n in notebooks:
        row = n.to_csv_row()
        row["complexity_score"], row["complexity_band"] = scorer.compute_complexity(row)
        rows.append(row)
        complexity_rows.append(
            {
                "item_kind": "notebook",
                "name": n.name,
                "complexity_score": row["complexity_score"],
                "complexity_band": row["complexity_band"],
            }
        )

    inventory_path = out / "inventory.csv"
    if rows:
        field_set: set[str] = set()
        for row in rows:
            field_set.update(row.keys())
        fieldnames = sorted(field_set)
        with inventory_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
    else:
        inventory_path.write_text("item_kind\n", encoding="utf-8")

    complexity_path = out / "complexity_scores.csv"
    complexity_rows.sort(key=lambda r: r["complexity_score"], reverse=True)
    with complexity_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["item_kind", "name", "complexity_score", "complexity_band"],
        )
        writer.writeheader()
        writer.writerows(complexity_rows)

    graph_path = out / "dependency_graph.json"
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []

    for t in tables:
        nodes.append(
            {
                "id": t.fqn,
                "kind": "table",
                "type": t.table_type,
                "schema": t.schema,
            }
        )
        for dep in t.dependencies:
            edges.append({"from": t.fqn, "to": dep})
    for p in pipelines:
        nodes.append({"id": p.name, "kind": "pipeline"})
        for dep in p.dependencies:
            edges.append({"from": p.name, "to": dep})
    for n in notebooks:
        nodes.append({"id": n.name, "kind": "notebook"})
        for dep in n.dependencies:
            edges.append({"from": n.name, "to": dep})

    graph_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "adjacency": workspace_dict.get("dependency_graph", {}),
    }
    graph_path.write_text(json.dumps(graph_payload, indent=2), encoding="utf-8")

    return {
        "inventory": inventory_path,
        "complexity_scores": complexity_path,
        "dependency_graph": graph_path,
    }


def from_seed(
    seed: int,
    output_dir: str | Path,
    table_count: int = 50,
    pipeline_count: int = 15,
    notebook_count: int = 10,
) -> dict[str, Any]:
    """Convenience: generate + serialize a workspace from a seed.

    Args
    ----
    seed: Random seed for reproducibility.
    output_dir: Destination directory for ``inventory.csv``,
        ``complexity_scores.csv``, ``dependency_graph.json``.
    table_count: Number of tables (clamped to [30, 100]).
    pipeline_count: Number of pipelines (clamped to [10, 30]).
    notebook_count: Number of notebooks (clamped to [5, 20]).

    Returns
    -------
    Dict containing the workspace dataclasses plus an ``artifacts`` key
    pointing to the file paths written by :func:`to_csv`.
    """
    gen = SynapseWorkloadInventoryGenerator(
        seed=seed,
        table_count=table_count,
        pipeline_count=pipeline_count,
        notebook_count=notebook_count,
    )
    workspace = gen.generate_workspace()
    artifacts = to_csv(workspace, output_dir)
    workspace_out: dict[str, Any] = {
        "tables": [asdict(t) for t in workspace["tables"]],
        "pipelines": [asdict(p) for p in workspace["pipelines"]],
        "notebooks": [asdict(n) for n in workspace["notebooks"]],
        "dependency_graph": workspace["dependency_graph"],
        "generated_at": workspace["generated_at"],
        "artifacts": {k: str(v) for k, v in artifacts.items()},
    }
    return workspace_out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_cli_parser() -> argparse.ArgumentParser:
    """Build the argparse parser for the module CLI."""
    parser = argparse.ArgumentParser(
        prog="synapse_workload_inventory",
        description=(
            "Generate a synthetic Synapse workspace inventory for the "
            "Tutorial 41 migration assessment flow."
        ),
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed (default: 42)."
    )
    parser.add_argument(
        "--table-count",
        type=int,
        default=50,
        help="Number of tables (clamped to [30, 100], default: 50).",
    )
    parser.add_argument(
        "--pipeline-count",
        type=int,
        default=15,
        help="Number of pipelines (clamped to [10, 30], default: 15).",
    )
    parser.add_argument(
        "--notebook-count",
        type=int,
        default=10,
        help="Number of notebooks (clamped to [5, 20], default: 10).",
    )
    parser.add_argument(
        "--output-dir",
        default="./synapse-mock-inventory",
        help="Directory to write inventory.csv, complexity_scores.csv, "
        "dependency_graph.json (default: ./synapse-mock-inventory).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns process exit code."""
    parser = _build_cli_parser()
    args = parser.parse_args(argv)

    result = from_seed(
        seed=args.seed,
        output_dir=args.output_dir,
        table_count=args.table_count,
        pipeline_count=args.pipeline_count,
        notebook_count=args.notebook_count,
    )

    print(
        f"Generated synthetic Synapse workspace inventory "
        f"({len(result['tables'])} tables, "
        f"{len(result['pipelines'])} pipelines, "
        f"{len(result['notebooks'])} notebooks)."
    )
    print("Artifacts:")
    for name, path in result["artifacts"].items():
        print(f"  {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
