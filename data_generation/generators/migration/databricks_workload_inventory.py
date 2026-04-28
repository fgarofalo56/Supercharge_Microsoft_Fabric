"""
Databricks Workload Inventory Generator
========================================

Generates a synthetic Microsoft Databricks workspace inventory for
Tutorial 42 (Databricks → Microsoft Fabric Migration). The inventory
mirrors what `01_assessment.py` would emit when run against a real
workspace, allowing readers to walk every step of the tutorial without
provisioning Databricks.

What is generated
-----------------
- Delta tables across Unity Catalog (catalog.schema.table) and the
  legacy hive_metastore. Mix of managed Delta, external Delta, Iceberg
  (UniForm), and Hive metastore tables. A realistic V-Order absence rate
  ensures the compatibility validator surfaces findings.
- Multi-task Databricks Workflows with realistic DAG dependencies.
- Delta Live Tables (DLT) pipelines.
- Notebooks (PySpark / SQL / Scala) with magic / dbutils call counts.
- MLflow registered models with stage tracking.
- Cluster configurations (job, all-purpose, DLT) with DBR version,
  node types, and Photon settings.

Used by
-------
- `tutorials/42-databricks-to-fabric/01_delta_compatibility.py --mock-mode`
- `tutorials/42-databricks-to-fabric/01_assessment.py --mock-mode`
- Future Phase 14 Wave 4 migration tutorials

Style anchor
------------
``data_generation/generators/federal/sba_generator.py`` — same dataclass
+ ``BaseGenerator`` + CLI entry-point pattern.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..base_generator import BaseGenerator

# ---------------------------------------------------------------------------
# Constants — Unity Catalog naming, DBR runtimes, node types
# ---------------------------------------------------------------------------

# Unity Catalog namespace candidates: (catalog, schema). Mix of casino,
# federal, and infrastructure workloads to mirror the broader POC.
UNITY_CATALOG_NAMESPACES: list[tuple[str, str]] = [
    ("prod", "bronze"),
    ("prod", "silver"),
    ("prod", "gold"),
    ("prod", "ml_features"),
    ("prod", "compliance"),
    ("dev", "scratch"),
    ("dev", "bronze"),
    ("dev", "silver"),
    ("staging", "bronze"),
    ("staging", "silver"),
    ("staging", "gold"),
    ("hive_metastore", "default"),
    ("hive_metastore", "legacy"),
]

# Casino domain table names (mirrors notebooks/bronze + silver + gold).
CASINO_TABLE_NAMES: list[str] = [
    "slot_telemetry",
    "table_game_events",
    "player_sessions",
    "ctr_filings",
    "sar_alerts",
    "w2g_records",
    "loyalty_transactions",
    "cage_movements",
    "fact_slot_revenue",
    "fact_table_game_revenue",
    "dim_player",
    "dim_machine",
    "dim_pit",
    "dim_date",
    "kpi_daily_revenue",
    "kpi_player_ltv",
]

# Federal domain table names (mirrors agencies covered in Phases 7-13).
FEDERAL_TABLE_NAMES: list[str] = [
    "usda_crop_production",
    "usda_food_safety_recalls",
    "sba_ppp_loans",
    "sba_7a_loans",
    "noaa_storm_events",
    "noaa_weather_observations",
    "epa_air_quality",
    "epa_facility_inspections",
    "doi_earthquake_events",
    "doi_land_permits",
    "ihs_clinical_encounters",
    "faa_flight_operations",
    "doj_federal_cases",
    "doj_crime_statistics",
]

# Generic / infrastructure table names.
GENERIC_TABLE_NAMES: list[str] = [
    "audit_log",
    "lineage_events",
    "config_kv",
    "feature_store_offline",
    "feature_store_online",
    "model_registry_metadata",
    "experiment_runs",
    "raw_kafka_events",
    "raw_eventhub_events",
    "checkpoint_state",
]

# Databricks Runtime versions in the field today (April 2026).
DBR_VERSIONS: list[str] = [
    "11.3.x-scala2.12",  # legacy LTS
    "12.2.x-scala2.12",  # LTS
    "13.3.x-scala2.12",  # LTS
    "14.3.x-scala2.12",  # LTS (most common)
    "15.4.x-scala2.12",  # LTS (newest LTS)
    "16.0.x-scala2.12",  # latest non-LTS
    "13.3.x-photon-scala2.12",
    "14.3.x-photon-scala2.12",
    "15.4.x-photon-scala2.12",
]

# Cluster node types (Azure Databricks SKUs).
NODE_TYPES: list[str] = [
    "Standard_DS3_v2",
    "Standard_DS4_v2",
    "Standard_DS5_v2",
    "Standard_E4ds_v5",
    "Standard_E8ds_v5",
    "Standard_E16ds_v5",
    "Standard_L4s",
    "Standard_L8s_v3",
    "Standard_NC4as_T4_v3",  # GPU
]

# Notebook languages.
NOTEBOOK_LANGUAGES: list[str] = ["python", "sql", "scala", "r"]
NOTEBOOK_LANGUAGE_WEIGHTS: list[float] = [0.65, 0.20, 0.10, 0.05]

# MLflow model frameworks.
MODEL_FRAMEWORKS: list[str] = [
    "sklearn",
    "xgboost",
    "lightgbm",
    "pytorch",
    "tensorflow",
    "spark-ml",
]
MODEL_FRAMEWORK_WEIGHTS: list[float] = [0.35, 0.20, 0.15, 0.10, 0.10, 0.10]

MODEL_STAGES: list[str | None] = [None, "Staging", "Production", "Archived"]
MODEL_STAGE_WEIGHTS: list[float] = [0.30, 0.25, 0.30, 0.15]

# DLT editions.
DLT_EDITIONS: list[str] = ["core", "pro", "advanced"]
DLT_EDITION_WEIGHTS: list[float] = [0.20, 0.40, 0.40]

# Workflow task types.
WORKFLOW_TASK_TYPES: list[str] = [
    "notebook_task",
    "python_wheel_task",
    "spark_jar_task",
    "sql_task",
    "pipeline_task",
    "dbt_task",
    "run_job_task",
    "condition_task",
    "for_each_task",
]
WORKFLOW_TASK_TYPE_WEIGHTS: list[float] = [
    0.55,  # notebooks dominate
    0.10,
    0.05,
    0.10,
    0.08,
    0.05,
    0.03,
    0.02,
    0.02,
]

# Cron schedule samples (Quartz format used by Databricks).
SCHEDULE_SAMPLES: list[str | None] = [
    None,  # manual / continuous
    "0 0 * * * ?",  # hourly
    "0 0 0 * * ?",  # daily
    "0 0 6 * * ?",  # daily at 6 AM
    "0 30 2 * * ?",  # daily at 02:30
    "0 0 0 ? * MON",  # weekly Monday
    "0 0 0 1 * ?",  # monthly first
]

# Realistic adoption rates for table features.
VORDER_ADOPTION_RATE = 0.30  # ~70% absent — gives validator findings
LIQUID_CLUSTERING_ADOPTION_RATE = 0.20
UNIFORM_ADOPTION_RATE = 0.15
CDF_ADOPTION_RATE = 0.25
DELETION_VECTOR_ADOPTION_RATE = 0.40
PHOTON_ENABLED_RATE = 0.55

# Delta protocol version pools (reader, writer).
DELTA_PROTOCOL_POOL: list[tuple[int, int]] = [
    (1, 2),  # legacy
    (2, 5),  # CDF / column mapping
    (2, 6),  # + deletion vectors
    (3, 7),  # latest stable (timestamp_ntz, V-Order, UniForm)
]
DELTA_PROTOCOL_WEIGHTS: list[float] = [0.10, 0.40, 0.25, 0.25]

# Table type mix.
TABLE_TYPES: list[str] = ["managed", "external", "iceberg-uniform", "hive"]
TABLE_TYPE_WEIGHTS: list[float] = [0.45, 0.30, 0.10, 0.15]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class DatabricksDeltaTableMeta:
    """Metadata snapshot of a Databricks Delta table.

    Mirrors the union of ``DESCRIBE DETAIL`` + ``SHOW TBLPROPERTIES`` plus
    the bits needed by Tutorial 42 step 3 (Delta compatibility) and the
    OneLake shortcut planner.
    """

    catalog: str
    schema: str
    name: str
    location_uri: str
    table_type: str  # managed | external | iceberg-uniform | hive
    delta_reader_version: int
    delta_writer_version: int
    row_count: int
    size_gb: float
    partition_columns: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)
    last_used: str = ""

    @property
    def fq_name(self) -> str:
        """Three-part Unity Catalog name."""

        return f"{self.catalog}.{self.schema}.{self.name}"


@dataclass
class DatabricksWorkflowMeta:
    """A Databricks multi-task Workflow / Job."""

    name: str
    job_id: int
    task_count: int
    task_types: list[str]  # one entry per task
    dependencies: list[tuple[str, str]] = field(default_factory=list)  # (parent, child)
    schedule: str | None = None
    cluster_spec: str = "job-cluster"  # job-cluster | existing | serverless
    continuous: bool = False
    last_run_status: str = "SUCCESS"
    last_run_at: str = ""


@dataclass
class DatabricksDLTMeta:
    """A Delta Live Tables pipeline."""

    name: str
    pipeline_id: str
    target_schema: str
    table_count: int
    autoscale_min: int
    autoscale_max: int
    edition: str  # core | pro | advanced
    continuous: bool = False
    photon: bool = True
    last_run_status: str = "SUCCESS"


@dataclass
class DatabricksNotebookMeta:
    """A Databricks notebook (workspace path)."""

    path: str
    language: str  # python | sql | scala | r
    cell_count: int
    magic_count: int
    dbutils_calls: int
    libraries: list[str] = field(default_factory=list)
    last_modified: str = ""


@dataclass
class DatabricksMLflowModelMeta:
    """An MLflow registered model snapshot."""

    name: str
    latest_version: int
    stage: str | None
    framework: str
    run_count: int
    last_updated: str = ""


@dataclass
class DatabricksClusterMeta:
    """A Databricks cluster configuration (job, all-purpose, or DLT)."""

    name: str
    cluster_id: str
    purpose: str  # job | all-purpose | dlt
    dbr_version: str
    node_type: str
    num_workers: int | None  # None when autoscaling
    autoscale_min: int | None
    autoscale_max: int | None
    photon_enabled: bool
    init_scripts: list[str] = field(default_factory=list)
    custom_libraries: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


class DatabricksWorkloadInventoryGenerator(BaseGenerator):
    """Synthetic Databricks workspace inventory for migration tutorials.

    Produces a self-consistent set of Unity Catalog tables, Workflows,
    DLT pipelines, notebooks, MLflow models, and cluster configurations.
    Output is reproducible when ``seed`` is supplied.

    Example
    -------
    >>> gen = DatabricksWorkloadInventoryGenerator(seed=42)
    >>> ws = gen.generate_workspace()
    >>> len(ws["tables"]) >= 30
    True
    """

    def __init__(
        self,
        seed: int | None = None,
        table_count: int = 50,
        workflow_count: int = 15,
        dlt_count: int = 5,
        notebook_count: int = 10,
        model_count: int = 5,
        cluster_count: int = 8,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> None:
        """Initialize the Databricks inventory generator.

        Args:
            seed: Random seed for reproducibility.
            table_count: Number of Delta tables to generate (30-100 typical).
            workflow_count: Number of multi-task Workflows (10-30 typical).
            dlt_count: Number of Delta Live Tables pipelines (5-15 typical).
            notebook_count: Number of notebooks (5-20 typical).
            model_count: Number of MLflow registered models (3-10 typical).
            cluster_count: Number of cluster configurations (5-20 typical).
            start_date: Earliest synthetic activity date.
            end_date: Latest synthetic activity date.
        """

        super().__init__(seed=seed, start_date=start_date, end_date=end_date)

        if table_count < 1:
            raise ValueError(f"table_count must be >= 1, got {table_count}")
        if workflow_count < 0:
            raise ValueError(f"workflow_count must be >= 0, got {workflow_count}")
        if dlt_count < 0:
            raise ValueError(f"dlt_count must be >= 0, got {dlt_count}")
        if notebook_count < 0:
            raise ValueError(f"notebook_count must be >= 0, got {notebook_count}")
        if model_count < 0:
            raise ValueError(f"model_count must be >= 0, got {model_count}")
        if cluster_count < 0:
            raise ValueError(f"cluster_count must be >= 0, got {cluster_count}")

        self.table_count = table_count
        self.workflow_count = workflow_count
        self.dlt_count = dlt_count
        self.notebook_count = notebook_count
        self.model_count = model_count
        self.cluster_count = cluster_count

        # Use a stdlib Random tied to seed so set ordering / shuffles
        # are also reproducible alongside numpy rng.
        self._py_rng = random.Random(self.seed)

        self._schema = {
            "table_count": "int",
            "workflow_count": "int",
            "dlt_count": "int",
            "notebook_count": "int",
            "model_count": "int",
            "cluster_count": "int",
            "generated_at_utc": "string",
        }

    # ---------------------------------------------------------------- #
    # BaseGenerator abstract methods
    # ---------------------------------------------------------------- #

    def generate_record(self) -> dict[str, Any]:
        """Generate a single Delta table metadata record.

        Returns the same shape as :py:meth:`_generate_table` so callers
        that pull one record at a time get a complete table snapshot.
        """

        return asdict(self._generate_table())

    def generate_batch(  # type: ignore[override]
        self, n: int = 1
    ) -> list[dict[str, Any]]:
        """Generate ``n`` Delta table metadata records.

        Args:
            n: Number of records to generate.

        Returns:
            List of dicts (one per Delta table).
        """

        if n < 1:
            raise ValueError(f"n must be >= 1, got {n}")
        return [self.generate_record() for _ in range(n)]

    # ---------------------------------------------------------------- #
    # Top-level workspace generator
    # ---------------------------------------------------------------- #

    def generate_workspace(self) -> dict[str, Any]:
        """Generate a coherent synthetic Databricks workspace.

        Returns:
            Dictionary with keys:
            - ``tables``: list[DatabricksDeltaTableMeta]
            - ``workflows``: list[DatabricksWorkflowMeta]
            - ``dlt_pipelines``: list[DatabricksDLTMeta]
            - ``notebooks``: list[DatabricksNotebookMeta]
            - ``models``: list[DatabricksMLflowModelMeta]
            - ``clusters``: list[DatabricksClusterMeta]
            - ``dependency_graph``: list[(parent_fq, child_fq)] table edges
            - ``metadata``: generator metadata (seed, counts, timestamp)
        """

        tables = [self._generate_table() for _ in range(self.table_count)]
        workflows = [
            self._generate_workflow(i + 1) for i in range(self.workflow_count)
        ]
        dlt_pipelines = [self._generate_dlt(i) for i in range(self.dlt_count)]
        notebooks = [self._generate_notebook(i) for i in range(self.notebook_count)]
        models = [self._generate_mlflow_model(i) for i in range(self.model_count)]
        clusters = [self._generate_cluster(i) for i in range(self.cluster_count)]

        dependency_graph = self._build_table_dependency_graph(tables)

        return {
            "tables": tables,
            "workflows": workflows,
            "dlt_pipelines": dlt_pipelines,
            "notebooks": notebooks,
            "models": models,
            "clusters": clusters,
            "dependency_graph": dependency_graph,
            "metadata": {
                "seed": self.seed,
                "table_count": len(tables),
                "workflow_count": len(workflows),
                "dlt_count": len(dlt_pipelines),
                "notebook_count": len(notebooks),
                "model_count": len(models),
                "cluster_count": len(clusters),
                "generated_at_utc": datetime.utcnow().isoformat() + "Z",
            },
        }

    # ---------------------------------------------------------------- #
    # Per-asset generators
    # ---------------------------------------------------------------- #

    def _generate_table(self) -> DatabricksDeltaTableMeta:
        """Generate a single Delta table metadata record."""

        catalog, schema = self._py_rng.choice(UNITY_CATALOG_NAMESPACES)

        # Pick a name from the appropriate pool to keep coherent semantics.
        name_pool: list[str]
        if "compliance" in schema or schema in ("bronze", "silver", "gold"):
            # Mix casino + federal + generic for the medallion schemas.
            name_pool = CASINO_TABLE_NAMES + FEDERAL_TABLE_NAMES + GENERIC_TABLE_NAMES
        elif schema == "ml_features":
            name_pool = ["features_" + n for n in CASINO_TABLE_NAMES[:6]]
        elif schema == "scratch":
            name_pool = [
                f"sandbox_{n}_{int(self.rng.integers(0, 1000))}"
                for n in GENERIC_TABLE_NAMES[:5]
            ]
        else:
            name_pool = GENERIC_TABLE_NAMES + CASINO_TABLE_NAMES

        base_name = self._py_rng.choice(name_pool)
        # Disambiguate so names don't repeat across tables.
        suffix = int(self.rng.integers(0, 100_000))
        name = f"{base_name}_{suffix:05d}" if self.rng.random() < 0.4 else base_name

        # Reader / writer versions.
        reader_version, writer_version = self.weighted_choice(
            DELTA_PROTOCOL_POOL, DELTA_PROTOCOL_WEIGHTS
        )

        # Type mix — Hive metastore tables only ever live in hive_metastore.
        if catalog == "hive_metastore":
            table_type = "hive"
        else:
            table_type = self.weighted_choice(TABLE_TYPES, TABLE_TYPE_WEIGHTS)
            if table_type == "hive":
                # Don't put a 'hive' table in a UC catalog; coerce to managed.
                table_type = "managed"

        # Location URI — DBFS root for hive_metastore managed tables, ADLS for
        # everything else.
        if table_type == "hive":
            location_uri = f"dbfs:/user/hive/warehouse/{schema}.db/{name}"
        elif table_type == "iceberg-uniform":
            location_uri = (
                "abfss://uniform@adlsdbx01.dfs.core.windows.net/"
                f"{catalog}/{schema}/{name}"
            )
        else:
            location_uri = (
                "abfss://databricks-data@adlsdbx01.dfs.core.windows.net/"
                f"{catalog}/{schema}/{name}"
            )

        # Sizing — heavy right-skew matching real Databricks workspaces.
        size_tier = self.rng.random()
        if size_tier < 0.5:
            size_gb = round(self.rng.uniform(0.01, 1.0), 3)
            row_count = int(self.rng.integers(1_000, 1_000_000))
        elif size_tier < 0.85:
            size_gb = round(self.rng.uniform(1.0, 50.0), 2)
            row_count = int(self.rng.integers(1_000_000, 100_000_000))
        elif size_tier < 0.97:
            size_gb = round(self.rng.uniform(50.0, 500.0), 2)
            row_count = int(self.rng.integers(100_000_000, 5_000_000_000))
        else:
            size_gb = round(self.rng.uniform(500.0, 5000.0), 2)
            row_count = int(self.rng.integers(5_000_000_000, 50_000_000_000))

        # Partition columns — most tables have 0-1, some up to 3.
        partition_columns = self._generate_partition_columns()

        # Feature flags — these drive the Tutorial 42 compatibility findings.
        has_vorder = self.rng.random() < VORDER_ADOPTION_RATE and table_type != "hive"
        has_uniform = (
            table_type == "iceberg-uniform" or self.rng.random() < UNIFORM_ADOPTION_RATE
        )
        has_cdf = self.rng.random() < CDF_ADOPTION_RATE and reader_version >= 2
        has_liquid = (
            self.rng.random() < LIQUID_CLUSTERING_ADOPTION_RATE
            and writer_version >= 7
            and len(partition_columns) == 0
        )
        has_deletion_vectors = (
            self.rng.random() < DELETION_VECTOR_ADOPTION_RATE and writer_version >= 6
        )

        properties: dict[str, Any] = {
            "delta.minReaderVersion": str(reader_version),
            "delta.minWriterVersion": str(writer_version),
            "has_vorder": has_vorder,
            "has_uniform": has_uniform,
            "has_cdf": has_cdf,
            "liquid_clustering": has_liquid,
            "deletion_vectors": has_deletion_vectors,
        }
        if has_cdf:
            properties["delta.enableChangeDataFeed"] = "true"
        if has_uniform:
            properties["delta.universalFormat.enabledFormats"] = "iceberg"
        if has_vorder:
            properties["delta.parquet.vorder.default"] = "true"
        if has_liquid:
            properties["delta.feature.liquid"] = "supported"
        if has_deletion_vectors:
            properties["delta.enableDeletionVectors"] = "true"

        last_used = self.random_datetime().isoformat()

        return DatabricksDeltaTableMeta(
            catalog=catalog,
            schema=schema,
            name=name,
            location_uri=location_uri,
            table_type=table_type,
            delta_reader_version=reader_version,
            delta_writer_version=writer_version,
            row_count=row_count,
            size_gb=size_gb,
            partition_columns=partition_columns,
            properties=properties,
            last_used=last_used,
        )

    def _generate_partition_columns(self) -> list[str]:
        """Generate a realistic partition column list (mostly empty / single)."""

        roll = self.rng.random()
        if roll < 0.45:
            return []
        if roll < 0.85:
            return [self._py_rng.choice(["event_date", "ingestion_date", "day"])]
        if roll < 0.97:
            return [
                self._py_rng.choice(["event_date", "ingestion_date"]),
                self._py_rng.choice(["region", "country", "tenant_id"]),
            ]
        return [
            "event_date",
            self._py_rng.choice(["region", "country"]),
            self._py_rng.choice(["product_line", "channel"]),
        ]

    def _generate_workflow(self, idx: int) -> DatabricksWorkflowMeta:
        """Generate a multi-task Workflow with a realistic DAG."""

        task_count = int(self.rng.integers(1, 12))
        task_types = [
            self.weighted_choice(WORKFLOW_TASK_TYPES, WORKFLOW_TASK_TYPE_WEIGHTS)
            for _ in range(task_count)
        ]
        task_names = [f"task_{i + 1}" for i in range(task_count)]

        # Build a simple DAG — each task depends on at most 2 prior tasks.
        dependencies: list[tuple[str, str]] = []
        for i in range(1, task_count):
            num_parents = min(i, int(self.rng.integers(1, 3)))
            parent_indices = self._py_rng.sample(range(i), num_parents)
            for p in parent_indices:
                dependencies.append((task_names[p], task_names[i]))

        schedule = self.weighted_choice(
            SCHEDULE_SAMPLES, [0.40, 0.10, 0.20, 0.10, 0.05, 0.10, 0.05]
        )
        # numpy returns numpy types — coerce.
        schedule = None if schedule is None else str(schedule)

        continuous = bool(self.rng.random() < 0.10 and schedule is None)

        cluster_spec = self._py_rng.choice(["job-cluster", "existing", "serverless"])
        last_run_status = self.weighted_choice(
            ["SUCCESS", "FAILED", "TIMEDOUT", "CANCELED"], [0.85, 0.10, 0.03, 0.02]
        )

        # Workflow naming hints at domain.
        prefix = self._py_rng.choice(
            ["bronze", "silver", "gold", "ml", "compliance", "ops", "rti"]
        )
        domain_hint = self._py_rng.choice(
            ["slot", "table_game", "loyalty", "usda", "noaa", "epa", "doj", "ihs", "faa"]
        )
        name = f"wf_{prefix}_{domain_hint}_{idx:03d}"

        return DatabricksWorkflowMeta(
            name=name,
            job_id=100_000 + idx,
            task_count=task_count,
            task_types=task_types,
            dependencies=dependencies,
            schedule=schedule,
            cluster_spec=cluster_spec,
            continuous=continuous,
            last_run_status=str(last_run_status),
            last_run_at=self.random_datetime().isoformat(),
        )

    def _generate_dlt(self, idx: int) -> DatabricksDLTMeta:
        """Generate a Delta Live Tables pipeline configuration."""

        target_schema = self._py_rng.choice(["bronze", "silver", "gold"])
        table_count = int(self.rng.integers(2, 15))
        autoscale_min = int(self.rng.integers(1, 4))
        autoscale_max = autoscale_min + int(self.rng.integers(2, 12))
        edition = self.weighted_choice(DLT_EDITIONS, DLT_EDITION_WEIGHTS)
        continuous = bool(self.rng.random() < 0.30)
        photon = bool(self.rng.random() < 0.80)
        last_run_status = self.weighted_choice(
            ["SUCCESS", "FAILED", "RUNNING"], [0.85, 0.10, 0.05]
        )
        domain = self._py_rng.choice(
            ["slot_telemetry", "loyalty", "usda_crops", "noaa_storms", "epa_air"]
        )

        return DatabricksDLTMeta(
            name=f"dlt_{target_schema}_{domain}_{idx:02d}",
            pipeline_id=self.generate_uuid(),
            target_schema=target_schema,
            table_count=table_count,
            autoscale_min=autoscale_min,
            autoscale_max=autoscale_max,
            edition=str(edition),
            continuous=continuous,
            photon=photon,
            last_run_status=str(last_run_status),
        )

    def _generate_notebook(self, idx: int) -> DatabricksNotebookMeta:
        """Generate a notebook metadata record."""

        language = self.weighted_choice(NOTEBOOK_LANGUAGES, NOTEBOOK_LANGUAGE_WEIGHTS)
        cell_count = int(self.rng.integers(5, 80))
        # Magic counts scale loosely with cell counts but always lower.
        magic_count = int(self.rng.integers(0, max(1, cell_count // 4)))
        # dbutils calls — heavier in PySpark, lower in SQL.
        if language == "python":
            dbutils_calls = int(self.rng.integers(0, 25))
        elif language == "scala":
            dbutils_calls = int(self.rng.integers(0, 15))
        else:
            dbutils_calls = int(self.rng.integers(0, 3))

        # Library imports — synthetic but realistic.
        lib_pool = [
            "pandas",
            "numpy",
            "pyspark",
            "delta-spark",
            "mlflow",
            "scikit-learn",
            "xgboost",
            "great-expectations",
            "azure-identity",
            "azure-storage-blob",
            "requests",
            "pyyaml",
        ]
        num_libs = int(self.rng.integers(0, 6))
        libraries = self._py_rng.sample(lib_pool, min(num_libs, len(lib_pool)))

        owner = self._py_rng.choice(
            ["alice@contoso.com", "bob@contoso.com", "carol@contoso.com",
             "dave@contoso.com", "eve@contoso.com"]
        )
        domain = self._py_rng.choice(
            ["bronze", "silver", "gold", "ml", "compliance", "ops"]
        )
        path = f"/Users/{owner}/{domain}/nb_{idx:03d}_{language}"

        return DatabricksNotebookMeta(
            path=path,
            language=str(language),
            cell_count=cell_count,
            magic_count=magic_count,
            dbutils_calls=dbutils_calls,
            libraries=libraries,
            last_modified=self.random_datetime().isoformat(),
        )

    def _generate_mlflow_model(self, idx: int) -> DatabricksMLflowModelMeta:
        """Generate an MLflow registered model record."""

        model_names = [
            "fraud_detection",
            "player_ltv",
            "slot_anomaly",
            "ctr_likelihood",
            "sar_pattern_detector",
            "weather_severity_forecast",
            "epa_aqi_predictor",
            "loan_default_risk",
            "flight_delay_predictor",
            "crop_yield_forecast",
        ]
        # Disambiguate by index so we don't collide.
        name = model_names[idx % len(model_names)]
        if idx >= len(model_names):
            name = f"{name}_v{idx}"

        latest_version = int(self.rng.integers(1, 20))
        stage = self.weighted_choice(MODEL_STAGES, MODEL_STAGE_WEIGHTS)
        framework = self.weighted_choice(MODEL_FRAMEWORKS, MODEL_FRAMEWORK_WEIGHTS)
        run_count = int(self.rng.integers(1, 250))

        return DatabricksMLflowModelMeta(
            name=name,
            latest_version=latest_version,
            stage=None if stage is None else str(stage),
            framework=str(framework),
            run_count=run_count,
            last_updated=self.random_datetime().isoformat(),
        )

    def _generate_cluster(self, idx: int) -> DatabricksClusterMeta:
        """Generate a cluster configuration record."""

        purpose = self.weighted_choice(
            ["job", "all-purpose", "dlt"], [0.55, 0.35, 0.10]
        )
        dbr_version = self._py_rng.choice(DBR_VERSIONS)
        node_type = self._py_rng.choice(NODE_TYPES)
        photon_enabled = (
            "photon" in dbr_version or self.rng.random() < PHOTON_ENABLED_RATE
        )

        # ~60% of clusters autoscale.
        if self.rng.random() < 0.60:
            autoscale_min = int(self.rng.integers(1, 4))
            autoscale_max = autoscale_min + int(self.rng.integers(2, 30))
            num_workers = None
        else:
            autoscale_min = None
            autoscale_max = None
            num_workers = int(self.rng.integers(1, 16))

        # Init scripts — shrinking pattern, only ~25% of clusters use them.
        init_scripts: list[str] = []
        if self.rng.random() < 0.25:
            init_scripts = [
                self._py_rng.choice(
                    [
                        "dbfs:/init/install_drivers.sh",
                        "dbfs:/init/configure_proxy.sh",
                        "dbfs:/init/jdbc_drivers.sh",
                    ]
                )
            ]

        # Custom libraries — JARs and Maven coordinates.
        custom_lib_pool = [
            "com.azure:azure-identity:1.11.0",
            "com.databricks:dbutils-api_2.12:0.0.6",
            "io.delta:delta-core_2.12:3.1.0",
            "com.microsoft.azure:spark-mssql-connector_2.12:1.4.0",
            "org.apache.hadoop:hadoop-azure:3.3.6",
        ]
        num_libs = int(self.rng.integers(0, 4))
        custom_libraries = self._py_rng.sample(
            custom_lib_pool, min(num_libs, len(custom_lib_pool))
        )

        cluster_name = f"cluster-{purpose}-{idx:03d}"

        return DatabricksClusterMeta(
            name=cluster_name,
            cluster_id=f"0426-{int(self.rng.integers(100000, 999999))}-{idx:04d}",
            purpose=str(purpose),
            dbr_version=dbr_version,
            node_type=node_type,
            num_workers=num_workers,
            autoscale_min=autoscale_min,
            autoscale_max=autoscale_max,
            photon_enabled=photon_enabled,
            init_scripts=init_scripts,
            custom_libraries=custom_libraries,
        )

    def _build_table_dependency_graph(
        self, tables: list[DatabricksDeltaTableMeta]
    ) -> list[tuple[str, str]]:
        """Build a synthetic Bronze → Silver → Gold dependency graph.

        Edges flow from upstream (bronze) to downstream (silver/gold).
        """

        bronze = [t.fq_name for t in tables if t.schema == "bronze"]
        silver = [t.fq_name for t in tables if t.schema == "silver"]
        gold = [t.fq_name for t in tables if t.schema == "gold"]

        edges: list[tuple[str, str]] = []
        for s in silver:
            num_parents = min(len(bronze), int(self.rng.integers(1, 3)))
            if bronze and num_parents > 0:
                for parent in self._py_rng.sample(bronze, num_parents):
                    edges.append((parent, s))

        for g in gold:
            num_parents = min(len(silver), int(self.rng.integers(1, 4)))
            if silver and num_parents > 0:
                for parent in self._py_rng.sample(silver, num_parents):
                    edges.append((parent, g))

        return edges


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _workspace_to_jsonable(workspace: dict[str, Any]) -> dict[str, Any]:
    """Convert dataclass instances to dicts so the workspace is JSON-serializable."""

    def _convert(value: Any) -> Any:
        if hasattr(value, "__dataclass_fields__"):
            return asdict(value)
        if isinstance(value, list):
            return [_convert(v) for v in value]
        if isinstance(value, tuple):
            return [_convert(v) for v in value]
        if isinstance(value, dict):
            return {k: _convert(v) for k, v in value.items()}
        return value

    return _convert(workspace)  # type: ignore[no-any-return]


def to_yaml(workspace_dict: dict[str, Any], output_dir: str | Path) -> Path:
    """Write ``tables-to-migrate.yaml`` in the format expected by
    ``01_delta_compatibility.py``.

    The validator only consumes the ``tables:`` top-level list of
    fully-qualified names. We additionally emit a sibling
    ``workspace-inventory.json`` containing the full structured inventory
    for callers that want richer metadata.

    Args:
        workspace_dict: Output of
            :py:meth:`DatabricksWorkloadInventoryGenerator.generate_workspace`.
        output_dir: Folder to write artifacts into. Created if missing.

    Returns:
        Path to the YAML file.
    """

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    tables = workspace_dict.get("tables", [])
    fq_names: list[str] = []
    for t in tables:
        if hasattr(t, "fq_name"):
            fq_names.append(t.fq_name)
        elif isinstance(t, dict):
            fq_names.append(f"{t['catalog']}.{t['schema']}.{t['name']}")

    yaml_path = out / "tables-to-migrate.yaml"
    lines = [
        "# Auto-generated by databricks_workload_inventory.py",
        "# Consumed by tutorials/42-databricks-to-fabric/01_delta_compatibility.py",
        "tables:",
    ]
    for fq in fq_names:
        lines.append(f"  - {fq}")
    yaml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Sidecar JSON with the full structured inventory.
    json_path = out / "workspace-inventory.json"
    json_path.write_text(
        json.dumps(_workspace_to_jsonable(workspace_dict), indent=2, default=str),
        encoding="utf-8",
    )

    return yaml_path


def from_seed(
    seed: int,
    output_dir: str | Path,
    table_count: int = 50,
    workflow_count: int = 15,
    dlt_count: int = 5,
    notebook_count: int = 10,
    model_count: int = 5,
    cluster_count: int = 8,
) -> dict[str, Any]:
    """Convenience wrapper: build a workspace from a seed and persist it.

    Args:
        seed: Random seed.
        output_dir: Folder for ``tables-to-migrate.yaml`` + JSON sidecar.
        table_count: Override default Delta-table count.
        workflow_count: Override default Workflow count.
        dlt_count: Override default DLT pipeline count.
        notebook_count: Override default notebook count.
        model_count: Override default MLflow model count.
        cluster_count: Override default cluster count.

    Returns:
        The full workspace dictionary (with dataclass instances intact).
    """

    gen = DatabricksWorkloadInventoryGenerator(
        seed=seed,
        table_count=table_count,
        workflow_count=workflow_count,
        dlt_count=dlt_count,
        notebook_count=notebook_count,
        model_count=model_count,
        cluster_count=cluster_count,
    )
    ws = gen.generate_workspace()
    to_yaml(ws, output_dir)
    return ws


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    """Construct argparse parser for the CLI."""

    parser = argparse.ArgumentParser(
        prog="databricks_workload_inventory.py",
        description=(
            "Generate a synthetic Databricks workspace inventory for "
            "Tutorial 42 (Databricks → Microsoft Fabric Migration)."
        ),
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--table-count", type=int, default=50, help="Number of Delta tables."
    )
    parser.add_argument(
        "--workflow-count", type=int, default=15, help="Number of Workflows."
    )
    parser.add_argument(
        "--dlt-count", type=int, default=5, help="Number of DLT pipelines."
    )
    parser.add_argument(
        "--notebook-count", type=int, default=10, help="Number of notebooks."
    )
    parser.add_argument(
        "--model-count", type=int, default=5, help="Number of MLflow models."
    )
    parser.add_argument(
        "--cluster-count", type=int, default=8, help="Number of cluster configs."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./databricks-mock-output",
        help="Folder for the generated YAML + JSON sidecar.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns process exit code."""

    args = _build_parser().parse_args(argv)
    ws = from_seed(
        seed=args.seed,
        output_dir=args.output_dir,
        table_count=args.table_count,
        workflow_count=args.workflow_count,
        dlt_count=args.dlt_count,
        notebook_count=args.notebook_count,
        model_count=args.model_count,
        cluster_count=args.cluster_count,
    )
    out = Path(args.output_dir)
    print(
        f"Generated synthetic Databricks workspace "
        f"(seed={args.seed}, tables={len(ws['tables'])}, "
        f"workflows={len(ws['workflows'])}, dlt={len(ws['dlt_pipelines'])}, "
        f"notebooks={len(ws['notebooks'])}, models={len(ws['models'])}, "
        f"clusters={len(ws['clusters'])})"
    )
    print(f"  YAML: {out / 'tables-to-migrate.yaml'}")
    print(f"  JSON: {out / 'workspace-inventory.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
