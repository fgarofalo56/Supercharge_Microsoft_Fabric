"""
Fabric CI/CD Deployment Script
===============================
Deploys Microsoft Fabric items (notebooks, lakehouses, semantic models)
across environments using the officially supported fabric-cicd Python library (GA Feb 2026).

Usage:
    python scripts/fabric-cicd-deploy.py \\
        --workspace-id <workspace-guid> \\
        --environment dev \\
        --item-type-in-scope Notebook Lakehouse SemanticModel \\
        --dry-run

Prerequisites:
    pip install fabric-cicd azure-identity

References:
    - https://learn.microsoft.com/fabric/cicd/manage-deployment
    - https://pypi.org/project/fabric-cicd/
"""

import argparse
import sys
from pathlib import Path

try:
    from fabric_cicd import FabricWorkspace, publish_all_items
    from azure.identity import DefaultAzureCredential
except ImportError:
    print("ERROR: Required packages not installed.")
    print("Run: pip install fabric-cicd azure-identity")
    sys.exit(1)


# =============================================================================
# Configuration
# =============================================================================

# Item type directories relative to repo root
ITEM_DIRECTORIES = {
    "Notebook": "notebooks",
    "Lakehouse": "lakehouses",
    "SemanticModel": "semantic-models",
    "Pipeline": "pipelines",
}

# Environment-specific parameter overrides
ENVIRONMENT_PARAMS = {
    "dev": {
        "lakehouse_name_suffix": "_dev",
        "connection_overrides": {},
    },
    "staging": {
        "lakehouse_name_suffix": "_staging",
        "connection_overrides": {},
    },
    "prod": {
        "lakehouse_name_suffix": "",
        "connection_overrides": {},
    },
}


# =============================================================================
# Deployment Functions
# =============================================================================

def create_workspace_client(workspace_id: str) -> FabricWorkspace:
    """Create an authenticated FabricWorkspace client using DefaultAzureCredential."""
    credential = DefaultAzureCredential()

    # Determine repository root (script is in scripts/)
    repo_root = Path(__file__).parent.parent

    workspace = FabricWorkspace(
        workspace_id=workspace_id,
        repository_directory=str(repo_root),
        item_type_in_scope=["Notebook", "Lakehouse", "SemanticModel"],
        credential=credential,
    )

    return workspace


def deploy(
    workspace_id: str,
    environment: str,
    item_types: list[str],
    dry_run: bool = False,
) -> None:
    """Deploy Fabric items to the target workspace."""
    print(f"\n{'=' * 60}")
    print(f"Fabric CI/CD Deployment")
    print(f"{'=' * 60}")
    print(f"  Workspace ID:  {workspace_id}")
    print(f"  Environment:   {environment}")
    print(f"  Item Types:    {', '.join(item_types)}")
    print(f"  Dry Run:       {dry_run}")
    print(f"{'=' * 60}\n")

    if dry_run:
        print("DRY RUN MODE - No changes will be applied\n")

    # Create authenticated workspace client
    print("Authenticating with Azure...")
    workspace = create_workspace_client(workspace_id)
    print(f"  Connected to workspace: {workspace_id}")

    # Get environment-specific parameters
    env_params = ENVIRONMENT_PARAMS.get(environment, {})
    print(f"  Environment config: {environment}")

    if dry_run:
        print("\n--- DRY RUN SUMMARY ---")
        print(f"Would deploy {len(item_types)} item type(s) to {environment}")
        for item_type in item_types:
            item_dir = ITEM_DIRECTORIES.get(item_type, item_type.lower())
            repo_root = Path(__file__).parent.parent
            item_path = repo_root / item_dir
            if item_path.exists():
                file_count = len(list(item_path.rglob("*")))
                print(f"  {item_type}: {file_count} files from {item_dir}/")
            else:
                print(f"  {item_type}: directory {item_dir}/ not found (skipped)")
        print("--- END DRY RUN ---\n")
        return

    # Publish items to workspace
    print("\nPublishing items to workspace...")
    try:
        publish_all_items(workspace)
        print("\n  Deployment completed successfully!")
    except Exception as e:
        print(f"\n  ERROR: Deployment failed: {e}")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"  Deployment to {environment} COMPLETE")
    print(f"{'=' * 60}\n")


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Deploy Fabric items using fabric-cicd (GA Feb 2026)"
    )
    parser.add_argument(
        "--workspace-id",
        required=True,
        help="Target Fabric workspace GUID",
    )
    parser.add_argument(
        "--environment",
        required=True,
        choices=["dev", "staging", "prod"],
        help="Target deployment environment",
    )
    parser.add_argument(
        "--item-type-in-scope",
        nargs="+",
        default=["Notebook", "Lakehouse", "SemanticModel"],
        help="Fabric item types to deploy (default: Notebook Lakehouse SemanticModel)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without deploying",
    )

    args = parser.parse_args()

    deploy(
        workspace_id=args.workspace_id,
        environment=args.environment,
        item_types=args.item_type_in_scope,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
