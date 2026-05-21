"""
Shared pytest fixtures and configuration for deployment tests.

Provides fixtures for:
- Bicep file paths
- Parameter file loading
- Mock Azure context
- Test utilities
"""

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

# =============================================================================
# Path Configuration
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
INFRA_ROOT = PROJECT_ROOT / "infra"
MODULES_ROOT = INFRA_ROOT / "modules"
ENVIRONMENTS_ROOT = INFRA_ROOT / "environments"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class BicepFile:
    """Represents a Bicep file with parsed metadata."""

    path: Path
    name: str
    content: str
    parameters: dict[str, Any]
    resources: list[str]
    outputs: list[str]

    @property
    def module_name(self) -> str | None:
        """Get module name from path."""
        parts = self.path.relative_to(INFRA_ROOT).parts
        if len(parts) > 2 and parts[0] == "modules":
            return parts[1]
        return None


@dataclass
class BicepParamFile:
    """Represents a Bicep parameter file."""

    path: Path
    environment: str
    content: str
    parameters: dict[str, Any]


# =============================================================================
# Bicep File Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Get project root path."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def infra_root() -> Path:
    """Get infrastructure root path."""
    return INFRA_ROOT


@pytest.fixture(scope="session")
def modules_root() -> Path:
    """Get modules root path."""
    return MODULES_ROOT


@pytest.fixture(scope="session")
def main_bicep_path() -> Path:
    """Get path to main.bicep."""
    return INFRA_ROOT / "main.bicep"


@pytest.fixture(scope="session")
def all_bicep_files() -> list[Path]:
    """Get all Bicep files in the infrastructure."""
    return list(INFRA_ROOT.rglob("*.bicep"))


@pytest.fixture(scope="session")
def module_bicep_files() -> dict[str, Path]:
    """Get Bicep files organized by module name.

    Each module directory may contain several .bicep files (e.g. security/
    contains security.bicep, workspace-identity.bicep, resource-locks.bicep).
    The "primary" file for a module is the one whose stem matches the parent
    directory name (security/security.bicep), or the only file if there is one.
    """
    # For modules where the directory holds multiple files, the "primary" is
    # the file whose stem matches the directory name (e.g. security/security.bicep).
    # Fall back to a curated map for legacy directories where no file matches.
    PRIMARY_OVERRIDES = {
        "fabric": "fabric-capacity.bicep",
        "networking": "vnet.bicep",
        "monitoring": "log-analytics.bicep",
        "storage": "storage-account.bicep",
        "governance": "purview.bicep",
        "analytics": "powerbi-workspace.bicep",
    }
    modules: dict[str, Path] = {}
    by_dir: dict[str, list[Path]] = {}
    for bicep_file in MODULES_ROOT.rglob("*.bicep"):
        by_dir.setdefault(bicep_file.parent.name, []).append(bicep_file)
    for dir_name, files in by_dir.items():
        override = PRIMARY_OVERRIDES.get(dir_name)
        if override:
            picked = next((f for f in files if f.name == override), None)
            if picked:
                modules[dir_name] = picked
                continue
        primary = next((f for f in files if f.stem == dir_name), files[0])
        modules[dir_name] = primary
    return modules


@pytest.fixture(scope="session")
def all_module_bicep_files() -> dict[str, list[Path]]:
    """Every .bicep file in modules/, grouped by module directory."""
    by_dir: dict[str, list[Path]] = {}
    for bicep_file in MODULES_ROOT.rglob("*.bicep"):
        by_dir.setdefault(bicep_file.parent.name, []).append(bicep_file)
    return by_dir


@pytest.fixture(scope="session")
def all_bicepparam_files() -> list[Path]:
    """Get all Bicep parameter files."""
    return list(INFRA_ROOT.rglob("*.bicepparam"))


@pytest.fixture(scope="session")
def environment_params() -> dict[str, Path]:
    """Get parameter files organized by environment."""
    params = {}
    for env in ["dev", "staging", "prod"]:
        param_file = ENVIRONMENTS_ROOT / env / f"{env}.bicepparam"
        if param_file.exists():
            params[env] = param_file
    return params


# =============================================================================
# Parsed Bicep Fixtures
# =============================================================================


def parse_bicep_parameters(content: str) -> dict[str, Any]:
    """Parse parameters from Bicep file content."""
    params = {}
    # Match parameter declarations like: param paramName string = 'value'
    # or @allowed(['value1', 'value2']) param paramName string
    param_pattern = r"param\s+(\w+)\s+(\w+)(?:\s*=\s*([^\n]+))?"

    for match in re.finditer(param_pattern, content):
        param_name = match.group(1)
        param_type = match.group(2)
        default_value = match.group(3).strip() if match.group(3) else None

        # Check for @allowed decorator
        allowed_pattern = rf"@allowed\s*\(\s*\[([^\]]+)\]\s*\)\s*param\s+{param_name}"
        allowed_match = re.search(allowed_pattern, content)
        allowed_values = None
        if allowed_match:
            allowed_str = allowed_match.group(1)
            allowed_values = [v.strip().strip("'\"") for v in allowed_str.split(",")]

        # Check for @minLength, @maxLength decorators
        min_length_pattern = rf"@minLength\s*\(\s*(\d+)\s*\).*?param\s+{param_name}"
        max_length_pattern = rf"@maxLength\s*\(\s*(\d+)\s*\).*?param\s+{param_name}"
        min_value_pattern = rf"@minValue\s*\(\s*(\d+)\s*\).*?param\s+{param_name}"
        max_value_pattern = rf"@maxValue\s*\(\s*(\d+)\s*\).*?param\s+{param_name}"

        min_length = None
        max_length = None
        min_value = None
        max_value = None

        min_len_match = re.search(min_length_pattern, content, re.DOTALL)
        max_len_match = re.search(max_length_pattern, content, re.DOTALL)
        min_val_match = re.search(min_value_pattern, content, re.DOTALL)
        max_val_match = re.search(max_value_pattern, content, re.DOTALL)

        if min_len_match:
            min_length = int(min_len_match.group(1))
        if max_len_match:
            max_length = int(max_len_match.group(1))
        if min_val_match:
            min_value = int(min_val_match.group(1))
        if max_val_match:
            max_value = int(max_val_match.group(1))

        params[param_name] = {
            "type": param_type,
            "default": default_value,
            "allowed": allowed_values,
            "minLength": min_length,
            "maxLength": max_length,
            "minValue": min_value,
            "maxValue": max_value,
        }

    return params


def parse_bicep_resources(content: str) -> list[str]:
    """Parse resource types from Bicep file content."""
    resources = []
    # Match resource declarations like: resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01'
    resource_pattern = r"resource\s+\w+\s+'([^']+)'"

    for match in re.finditer(resource_pattern, content):
        resource_type = match.group(1)
        resources.append(resource_type)

    return resources


def parse_bicep_outputs(content: str) -> list[str]:
    """Parse outputs from Bicep file content."""
    outputs = []
    # Match output declarations like: output storageAccountName string = storageAccount.name
    output_pattern = r"output\s+(\w+)\s+\w+"

    for match in re.finditer(output_pattern, content):
        output_name = match.group(1)
        outputs.append(output_name)

    return outputs


def parse_bicepparam_values(content: str) -> dict[str, Any]:
    """Parse parameter values from Bicep parameter file content."""
    params = {}
    # Split content into lines for line-by-line parsing
    lines = content.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip comments and empty lines
        if not line or line.startswith("//") or line.startswith("using"):
            i += 1
            continue

        # Match param assignments like: param environment = 'dev'
        param_match = re.match(r"param\s+(\w+)\s*=\s*(.+)", line)
        if param_match:
            param_name = param_match.group(1)
            param_value = param_match.group(2).strip()

            # Handle multi-line object values (e.g., tags = { ... })
            if param_value.startswith("{") and not param_value.endswith("}"):
                # Collect lines until closing brace
                brace_count = param_value.count("{") - param_value.count("}")
                while brace_count > 0 and i + 1 < len(lines):
                    i += 1
                    next_line = lines[i]
                    param_value += "\n" + next_line
                    brace_count += next_line.count("{") - next_line.count("}")

            params[param_name] = param_value

        i += 1

    return params


@pytest.fixture(scope="session")
def parsed_main_bicep(main_bicep_path: Path) -> BicepFile:
    """Parse main.bicep file."""
    content = main_bicep_path.read_text(encoding="utf-8")
    return BicepFile(
        path=main_bicep_path,
        name="main.bicep",
        content=content,
        parameters=parse_bicep_parameters(content),
        resources=parse_bicep_resources(content),
        outputs=parse_bicep_outputs(content),
    )


@pytest.fixture(scope="session")
def parsed_module_files(module_bicep_files: dict[str, Path]) -> dict[str, BicepFile]:
    """Parse all module Bicep files."""
    parsed = {}
    for module_name, path in module_bicep_files.items():
        content = path.read_text(encoding="utf-8")
        parsed[module_name] = BicepFile(
            path=path,
            name=path.name,
            content=content,
            parameters=parse_bicep_parameters(content),
            resources=parse_bicep_resources(content),
            outputs=parse_bicep_outputs(content),
        )
    return parsed


@pytest.fixture(scope="session")
def parsed_param_files(
    environment_params: dict[str, Path],
) -> dict[str, BicepParamFile]:
    """Parse all environment parameter files."""
    parsed = {}
    for env, path in environment_params.items():
        content = path.read_text(encoding="utf-8")
        parsed[env] = BicepParamFile(
            path=path,
            environment=env,
            content=content,
            parameters=parse_bicepparam_values(content),
        )
    return parsed


# =============================================================================
# Azure Context Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def azure_cli_available() -> bool:
    """Check if Azure CLI is available."""
    try:
        result = subprocess.run(
            ["az", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


@pytest.fixture(scope="session")
def azure_logged_in(azure_cli_available: bool) -> bool:
    """Check if user is logged into Azure CLI."""
    if not azure_cli_available:
        return False

    try:
        result = subprocess.run(
            ["az", "account", "show"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except subprocess.SubprocessError:
        return False


@pytest.fixture(scope="session")
def azure_subscription_id(azure_logged_in: bool) -> str | None:
    """Get current Azure subscription ID."""
    if not azure_logged_in:
        return None

    try:
        result = subprocess.run(
            ["az", "account", "show", "--query", "id", "-o", "tsv"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except subprocess.SubprocessError:
        pass

    return None


@pytest.fixture(scope="session")
def bicep_cli_available() -> bool:
    """Check if Bicep CLI is available *and* can read these source paths.

    A `WSL` host running a Windows-installed `az` cannot resolve the Linux
    paths under /mnt/...; in that case `az bicep build` fails with
    "An error occurred reading file". Probe a real build of main.bicep so
    we skip cleanly in unsupported environments rather than failing.
    """
    try:
        result = subprocess.run(
            ["az", "bicep", "version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return False
        # Probe build with the actual file we care about. If the host az can't
        # read the path, downstream tests would fail with a path-translation
        # error rather than a real Bicep error -- skip them instead.
        probe = subprocess.run(
            [
                "az",
                "bicep",
                "build",
                "--file",
                str(INFRA_ROOT / "main.bicep"),
                "--stdout",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return not (
            probe.returncode != 0
            and "Could not find a part of the path" in probe.stderr
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


# =============================================================================
# Mock Azure Context
# =============================================================================


@pytest.fixture
def mock_azure_context() -> dict[str, Any]:
    """Provide mock Azure context for tests that don't require real Azure access."""
    return {
        "subscription_id": "00000000-0000-0000-0000-000000000000",
        "tenant_id": "00000000-0000-0000-0000-000000000001",
        "location": "eastus2",
        "resource_group": "rg-test-fabricpoc-dev",
    }


@pytest.fixture
def mock_deployment_outputs() -> dict[str, Any]:
    """Provide mock deployment outputs for testing."""
    return {
        "resourceGroupName": {"type": "string", "value": "rg-fabricpoc-dev"},
        "fabricCapacityName": {"type": "string", "value": "fabricfabricpocdev"},
        "storageAccountName": {"type": "string", "value": "stfabricpocdev"},
        "keyVaultName": {"type": "string", "value": "kv-fabricpoc-dev"},
        "keyVaultUri": {
            "type": "string",
            "value": "https://kv-fabricpoc-dev.vault.azure.net/",
        },
        "logAnalyticsWorkspaceId": {
            "type": "string",
            "value": "/subscriptions/xxx/resourceGroups/rg-fabricpoc-dev/providers/Microsoft.OperationalInsights/workspaces/log-fabricpoc-dev",
        },
    }


# =============================================================================
# Utility Functions
# =============================================================================


def skip_if_no_azure_cli(azure_cli_available: bool):
    """Pytest skip decorator for tests requiring Azure CLI."""
    if not azure_cli_available:
        pytest.skip("Azure CLI not available")


def skip_if_not_logged_in(azure_logged_in: bool):
    """Pytest skip decorator for tests requiring Azure login."""
    if not azure_logged_in:
        pytest.skip("Not logged into Azure CLI")


def skip_if_no_bicep_cli(bicep_cli_available: bool):
    """Pytest skip decorator for tests requiring Bicep CLI."""
    if not bicep_cli_available:
        pytest.skip("Bicep CLI not available")


@pytest.fixture
def require_azure_cli(azure_cli_available: bool):
    """Fixture that skips test if Azure CLI is not available."""
    skip_if_no_azure_cli(azure_cli_available)


@pytest.fixture
def require_azure_login(azure_logged_in: bool):
    """Fixture that skips test if not logged into Azure."""
    skip_if_not_logged_in(azure_logged_in)


@pytest.fixture
def require_bicep_cli(bicep_cli_available: bool):
    """Fixture that skips test if Bicep CLI is not available."""
    skip_if_no_bicep_cli(bicep_cli_available)


# =============================================================================
# Azure Resource Naming Constants
# =============================================================================

AZURE_RESOURCE_PREFIXES = {
    "resourceGroup": "rg-",
    "storageAccount": "st",
    "keyVault": "kv-",
    "logAnalytics": "log-",
    "managedIdentity": "id-",
    "virtualNetwork": "vnet-",
    "subnet": "snet-",
    "networkSecurityGroup": "nsg-",
    "privateEndpoint": "pe-",
    "purview": "pview",
    "fabric": "fabric",
}

AZURE_RESOURCE_MAX_LENGTHS = {
    "resourceGroup": 90,
    "storageAccount": 24,
    "keyVault": 24,
    "logAnalytics": 63,
    "managedIdentity": 128,
    "virtualNetwork": 64,
    "subnet": 80,
    "networkSecurityGroup": 80,
    "privateEndpoint": 64,
    "purview": 63,
    "fabric": 63,
}

AZURE_RESOURCE_MIN_LENGTHS = {
    "resourceGroup": 1,
    "storageAccount": 3,
    "keyVault": 3,
    "logAnalytics": 4,
    "managedIdentity": 3,
    "virtualNetwork": 2,
    "subnet": 1,
    "networkSecurityGroup": 1,
    "privateEndpoint": 1,
    "purview": 3,
    "fabric": 3,
}


@pytest.fixture(scope="session")
def resource_prefixes() -> dict[str, str]:
    """Get Azure resource naming prefixes."""
    return AZURE_RESOURCE_PREFIXES


@pytest.fixture(scope="session")
def resource_max_lengths() -> dict[str, int]:
    """Get Azure resource max name lengths."""
    return AZURE_RESOURCE_MAX_LENGTHS


@pytest.fixture(scope="session")
def resource_min_lengths() -> dict[str, int]:
    """Get Azure resource min name lengths."""
    return AZURE_RESOURCE_MIN_LENGTHS


# =============================================================================
# Valid SKUs and Configurations
# =============================================================================

VALID_FABRIC_SKUS = [
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
VALID_ENVIRONMENTS = ["dev", "staging", "prod"]
VALID_LOCATIONS = [
    "eastus",
    "eastus2",
    "westus",
    "westus2",
    "westus3",
    "centralus",
    "northcentralus",
    "southcentralus",
    "westcentralus",
    "northeurope",
    "westeurope",
    "uksouth",
    "ukwest",
    "australiaeast",
    "australiasoutheast",
    "southeastasia",
    "eastasia",
    "japaneast",
    "japanwest",
    "brazilsouth",
    "canadacentral",
    "canadaeast",
    "francecentral",
    "germanywestcentral",
    "norwayeast",
    "switzerlandnorth",
    "uaenorth",
    "southafricanorth",
    "koreacentral",
    "koreasouth",
    "centralindia",
    "westindia",
    "southindia",
]


@pytest.fixture(scope="session")
def valid_fabric_skus() -> list[str]:
    """Get list of valid Fabric SKUs."""
    return VALID_FABRIC_SKUS


@pytest.fixture(scope="session")
def valid_environments() -> list[str]:
    """Get list of valid environments."""
    return VALID_ENVIRONMENTS


@pytest.fixture(scope="session")
def valid_locations() -> list[str]:
    """Get list of valid Azure locations."""
    return VALID_LOCATIONS
