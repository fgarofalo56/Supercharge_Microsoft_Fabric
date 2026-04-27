"""
Migration Generators
====================

Synthetic data generators for source-system migration tutorials (Phase 14, Wave 4).

Modules
-------
- synapse_workload_inventory : Synthetic Azure Synapse workspace inventory
  (tables, pipelines, notebooks, dependencies) for Tutorial 41.
"""

from .synapse_workload_inventory import (
    SynapseNotebookMeta,
    SynapsePipelineMeta,
    SynapseTableMeta,
    SynapseWorkloadInventoryGenerator,
    from_seed,
    to_csv,
)

__all__ = [
    "SynapseNotebookMeta",
    "SynapsePipelineMeta",
    "SynapseTableMeta",
    "SynapseWorkloadInventoryGenerator",
    "from_seed",
    "to_csv",
]
