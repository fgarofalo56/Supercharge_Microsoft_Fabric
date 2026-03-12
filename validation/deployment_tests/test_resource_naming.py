"""
Azure Resource Naming Convention Tests

Tests that validate Azure resource names follow:
- Azure naming conventions (rg-, kv-, st, etc.)
- Name length limits
- Character restrictions
- Consistency across environments
"""

import re
from pathlib import Path
from typing import Any, Dict, List

import pytest

# =============================================================================
# Naming Convention Rules
# =============================================================================

NAMING_RULES = {
    "resourceGroup": {
        "prefix": "rg-",
        "pattern": r"^rg-[a-z0-9-]+$",
        "min_length": 1,
        "max_length": 90,
        "allowed_chars": "alphanumeric, underscores, hyphens, periods, parentheses",
        "description": "Resource Group",
    },
    "storageAccount": {
        "prefix": "st",
        "pattern": r"^st[a-z0-9]{3,22}$",
        "min_length": 3,
        "max_length": 24,
        "allowed_chars": "lowercase letters and numbers only",
        "description": "Storage Account",
    },
    "keyVault": {
        "prefix": "kv-",
        "pattern": r"^kv-[a-z0-9-]+$",
        "min_length": 3,
        "max_length": 24,
        "allowed_chars": "alphanumeric and hyphens",
        "description": "Key Vault",
    },
    "logAnalytics": {
        "prefix": "log-",
        "pattern": r"^log-[a-zA-Z0-9-]+$",
        "min_length": 4,
        "max_length": 63,
        "allowed_chars": "alphanumeric and hyphens",
        "description": "Log Analytics Workspace",
    },
    "managedIdentity": {
        "prefix": "id-",
        "pattern": r"^id-[a-zA-Z0-9-]+$",
        "min_length": 3,
        "max_length": 128,
        "allowed_chars": "alphanumeric, hyphens, underscores",
        "description": "Managed Identity",
    },
    "virtualNetwork": {
        "prefix": "vnet-",
        "pattern": r"^vnet-[a-zA-Z0-9-]+$",
        "min_length": 2,
        "max_length": 64,
        "allowed_chars": "alphanumeric, hyphens, underscores, periods",
        "description": "Virtual Network",
    },
    "subnet": {
        "prefix": "snet-",
        "pattern": r"^snet-[a-zA-Z0-9-]+$",
        "min_length": 1,
        "max_length": 80,
        "allowed_chars": "alphanumeric, hyphens, underscores, periods",
        "description": "Subnet",
    },
    "networkSecurityGroup": {
        "prefix": "nsg-",
        "pattern": r"^nsg-[a-zA-Z0-9-]+$",
        "min_length": 1,
        "max_length": 80,
        "allowed_chars": "alphanumeric, hyphens, underscores, periods",
        "description": "Network Security Group",
    },
    "privateEndpoint": {
        "prefix": "pe-",
        "pattern": r"^pe-[a-zA-Z0-9-]+$",
        "min_length": 1,
        "max_length": 64,
        "allowed_chars": "alphanumeric, hyphens, underscores",
        "description": "Private Endpoint",
    },
    "purview": {
        "prefix": "pview",
        "pattern": r"^pview[a-z0-9]+$",
        "min_length": 3,
        "max_length": 63,
        "allowed_chars": "alphanumeric",
        "description": "Purview Account",
    },
    "fabric": {
        "prefix": "fabric",
        "pattern": r"^fabric[a-z0-9]+$",
        "min_length": 3,
        "max_length": 63,
        "allowed_chars": "alphanumeric",
        "description": "Fabric Capacity",
    },
}


class TestResourceGroupNaming:
    """Tests for resource group naming conventions."""

    def test_rg_prefix_used(self, main_bicep_path: Path):
        """Test that resource groups use 'rg-' prefix."""
        content = main_bicep_path.read_text(encoding="utf-8")

        # Find resource group name variable
        rg_pattern = r"resourceGroupName\s*=\s*'([^']+)'"
        match = re.search(rg_pattern, content)

        if match:
            rg_name = match.group(1)
            assert rg_name.startswith(
                "rg-"
            ), f"Resource group name should start with 'rg-', got: {rg_name}"
        else:
            # Check for concatenated names
            assert (
                "var resourceGroupName = 'rg-" in content
            ), "Resource group name should start with 'rg-' prefix"

    def test_rg_name_uses_environment_suffix(self, main_bicep_path: Path):
        """Test that resource group name includes environment."""
        content = main_bicep_path.read_text(encoding="utf-8")

        # Should include ${environment} in the name
        assert (
            "${environment}" in content or "environment}" in content
        ), "Resource group name should include environment parameter"


class TestStorageAccountNaming:
    """Tests for storage account naming conventions."""

    def test_storage_prefix_used(self, module_bicep_files: dict[str, Path]):
        """Test that storage accounts use 'st' prefix."""
        storage_path = module_bicep_files.get("storage")
        if not storage_path:
            pytest.skip("Storage module not found")

        # Check main.bicep for storage account name variable
        from conftest import INFRA_ROOT

        main_content = (INFRA_ROOT / "main.bicep").read_text(encoding="utf-8")

        # Look for storageAccountName variable
        assert (
            "'st${" in main_content or "storageAccountName = 'st" in main_content
        ), "Storage account name should start with 'st' prefix"

    def test_storage_name_lowercase_only(self, main_bicep_path: Path):
        """Test that storage account names are lowercase."""
        content = main_bicep_path.read_text(encoding="utf-8")

        # Find storage account name definition
        storage_pattern = r"var\s+storageAccountName\s*=\s*'([^']+)'"
        match = re.search(storage_pattern, content)

        if match:
            name_template = match.group(1)
            # Check that static parts are lowercase
            static_parts = re.sub(r"\$\{[^}]+\}", "", name_template)
            assert (
                static_parts == static_parts.lower()
            ), f"Storage account name should be lowercase: {name_template}"

    def test_storage_name_no_special_chars(self, main_bicep_path: Path):
        """Test that storage account names have no special characters."""
        content = main_bicep_path.read_text(encoding="utf-8")

        storage_pattern = r"var\s+storageAccountName\s*=\s*'([^']+)'"
        match = re.search(storage_pattern, content)

        if match:
            name_template = match.group(1)
            # Remove variable interpolations
            static_parts = re.sub(r"\$\{[^}]+\}", "x", name_template)
            # Should only contain alphanumeric
            assert re.match(
                r"^[a-z0-9]+$", static_parts
            ), f"Storage account name should only contain lowercase alphanumeric: {name_template}"


class TestKeyVaultNaming:
    """Tests for Key Vault naming conventions."""

    def test_keyvault_prefix_used(self, main_bicep_path: Path):
        """Test that Key Vault uses 'kv-' prefix."""
        content = main_bicep_path.read_text(encoding="utf-8")

        assert (
            "'kv-${" in content or "keyVaultName = 'kv-" in content
        ), "Key Vault name should start with 'kv-' prefix"

    def test_keyvault_name_length(
        self, main_bicep_path: Path, parsed_param_files: dict[str, Any]
    ):
        """Test that Key Vault names don't exceed 24 characters."""
        # With typical values:
        # kv-fabricpoc-dev = 16 chars (ok)
        # kv-fabricpoc-staging = 20 chars (ok)
        # kv-fabricpoc-prod = 17 chars (ok)

        for env, params in parsed_param_files.items():
            prefix = params.parameters.get("projectPrefix", "").strip("'\"")
            if prefix:
                # Calculate expected length: kv- + prefix + - + env
                expected_length = 3 + len(prefix) + 1 + len(env)
                assert (
                    expected_length <= 24
                ), f"Key Vault name for {env} would exceed 24 chars: {expected_length}"


class TestLogAnalyticsNaming:
    """Tests for Log Analytics workspace naming conventions."""

    def test_log_analytics_prefix_used(self, main_bicep_path: Path):
        """Test that Log Analytics uses 'log-' prefix."""
        content = main_bicep_path.read_text(encoding="utf-8")

        assert (
            "'log-${" in content or "logAnalyticsName = 'log-" in content
        ), "Log Analytics name should start with 'log-' prefix"


class TestManagedIdentityNaming:
    """Tests for Managed Identity naming conventions."""

    def test_managed_identity_prefix_used(self, main_bicep_path: Path):
        """Test that Managed Identity uses 'id-' prefix."""
        content = main_bicep_path.read_text(encoding="utf-8")

        assert (
            "'id-${" in content or "managedIdentityName = 'id-" in content
        ), "Managed Identity name should start with 'id-' prefix"


class TestNetworkingNaming:
    """Tests for networking resource naming conventions."""

    def test_vnet_prefix_used(self, main_bicep_path: Path):
        """Test that VNet uses 'vnet-' prefix."""
        content = main_bicep_path.read_text(encoding="utf-8")

        assert (
            "'vnet-${" in content or "vnetName = 'vnet-" in content
        ), "Virtual Network name should start with 'vnet-' prefix"

    def test_subnet_prefix_used(self, module_bicep_files: dict[str, Path]):
        """Test that subnets use 'snet-' prefix."""
        vnet_path = module_bicep_files.get("networking")
        if not vnet_path:
            pytest.skip("Networking module not found")

        content = vnet_path.read_text(encoding="utf-8")

        # Check for subnet names
        assert "snet-" in content, "Subnet names should start with 'snet-' prefix"

    def test_nsg_prefix_used(self, module_bicep_files: dict[str, Path]):
        """Test that NSGs use 'nsg-' prefix."""
        vnet_path = module_bicep_files.get("networking")
        if not vnet_path:
            pytest.skip("Networking module not found")

        content = vnet_path.read_text(encoding="utf-8")

        # Check for NSG names
        assert (
            "nsg-" in content
        ), "Network Security Group names should start with 'nsg-' prefix"


class TestPrivateEndpointNaming:
    """Tests for private endpoint naming conventions."""

    def test_private_endpoint_prefix_used(self, all_bicep_files: list[Path]):
        """Test that private endpoints use 'pe-' prefix."""
        pe_found = False

        for bicep_file in all_bicep_files:
            content = bicep_file.read_text(encoding="utf-8")

            if ("privateEndpoint" in content.lower() and "'pe-${" in content) or (
                "privateEndpoint" in content.lower() and "'pe-" in content
            ):
                pe_found = True
                break

        if not pe_found:
            # Check if private endpoints are used at all
            for bicep_file in all_bicep_files:
                content = bicep_file.read_text(encoding="utf-8")
                if "Microsoft.Network/privateEndpoints" in content:
                    assert (
                        "'pe-" in content
                    ), f"Private endpoint in {bicep_file.name} should use 'pe-' prefix"


class TestPurviewNaming:
    """Tests for Purview account naming conventions."""

    def test_purview_prefix_used(self, main_bicep_path: Path):
        """Test that Purview uses 'pview' prefix."""
        content = main_bicep_path.read_text(encoding="utf-8")

        assert (
            "'pview${" in content or "purviewAccountName = 'pview" in content
        ), "Purview account name should start with 'pview' prefix"

    def test_purview_name_no_hyphens(self, main_bicep_path: Path):
        """Test that Purview name doesn't contain hyphens (not allowed)."""
        content = main_bicep_path.read_text(encoding="utf-8")

        purview_pattern = r"var\s+purviewAccountName\s*=\s*'([^']+)'"
        match = re.search(purview_pattern, content)

        if match:
            name_template = match.group(1)
            # Static parts should not have hyphens
            static_parts = re.sub(r"\$\{[^}]+\}", "", name_template)
            assert (
                "-" not in static_parts
            ), f"Purview name should not contain hyphens: {name_template}"


class TestFabricNaming:
    """Tests for Fabric capacity naming conventions."""

    def test_fabric_prefix_used(self, main_bicep_path: Path):
        """Test that Fabric uses 'fabric' prefix."""
        content = main_bicep_path.read_text(encoding="utf-8")

        assert (
            "'fabric${" in content or "fabricCapacityName = 'fabric" in content
        ), "Fabric capacity name should start with 'fabric' prefix"


class TestNamingConsistency:
    """Tests for naming consistency across environments."""

    def test_consistent_prefix_across_environments(
        self, parsed_param_files: dict[str, Any]
    ):
        """Test that projectPrefix is consistent or intentionally different."""
        prefixes = {}
        for env, params in parsed_param_files.items():
            prefix = params.parameters.get("projectPrefix", "").strip("'\"")
            if prefix:
                prefixes[env] = prefix

        # For a POC, prefix should typically be the same
        unique_prefixes = set(prefixes.values())
        if len(unique_prefixes) > 1:
            # This might be intentional, so just warn
            pytest.skip(
                f"Multiple project prefixes found: {prefixes}. "
                "This may be intentional for different workloads."
            )

    def test_environment_suffix_matches(self, parsed_param_files: dict[str, Any]):
        """Test that environment parameter matches expected values."""
        for env, params in parsed_param_files.items():
            env_value = params.parameters.get("environment", "").strip("'\"")
            assert (
                env_value == env
            ), f"Environment value '{env_value}' doesn't match file name '{env}'"


class TestNameLengthValidation:
    """Tests for resource name length limits."""

    def test_generated_names_within_limits(
        self,
        main_bicep_path: Path,
        parsed_param_files: dict[str, Any],
    ):
        """Test that generated resource names are within Azure limits."""
        content = main_bicep_path.read_text(encoding="utf-8")

        # Extract variable patterns
        var_patterns = {
            "resourceGroupName": (90, r"var\s+resourceGroupName\s*=\s*'([^']+)'"),
            "storageAccountName": (24, r"var\s+storageAccountName\s*=\s*'([^']+)'"),
            "keyVaultName": (24, r"var\s+keyVaultName\s*=\s*'([^']+)'"),
            "logAnalyticsName": (63, r"var\s+logAnalyticsName\s*=\s*'([^']+)'"),
            "managedIdentityName": (128, r"var\s+managedIdentityName\s*=\s*'([^']+)'"),
            "vnetName": (64, r"var\s+vnetName\s*=\s*'([^']+)'"),
            "purviewAccountName": (63, r"var\s+purviewAccountName\s*=\s*'([^']+)'"),
            "fabricCapacityName": (63, r"var\s+fabricCapacityName\s*=\s*'([^']+)'"),
        }

        for env, params in parsed_param_files.items():
            prefix = params.parameters.get("projectPrefix", "").strip("'\"")
            if not prefix:
                continue

            for var_name, (max_length, pattern) in var_patterns.items():
                match = re.search(pattern, content)
                if match:
                    template = match.group(1)
                    # Estimate final length by substituting known values
                    estimated_name = template.replace(
                        "${projectPrefix}", prefix
                    ).replace("${environment}", env)
                    # Remove remaining ${...} placeholders for length calc
                    estimated_name = re.sub(r"\$\{[^}]+\}", "", estimated_name)

                    assert len(estimated_name) <= max_length, (
                        f"{var_name} for {env} exceeds {max_length} chars: "
                        f"{len(estimated_name)} chars ({estimated_name})"
                    )


class TestCharacterRestrictions:
    """Tests for character restrictions in resource names."""

    def test_storage_account_lowercase_alphanumeric(self, main_bicep_path: Path):
        """Test storage account uses only lowercase alphanumeric."""
        content = main_bicep_path.read_text(encoding="utf-8")

        match = re.search(r"var\s+storageAccountName\s*=\s*'([^']+)'", content)
        if match:
            template = match.group(1)
            # Remove interpolations
            static = re.sub(r"\$\{[^}]+\}", "", template)
            assert (
                static == static.lower()
            ), f"Storage account static parts must be lowercase: {static}"
            assert re.match(
                r"^[a-z0-9]*$", static
            ), f"Storage account must be alphanumeric only: {static}"

    def test_no_consecutive_hyphens(self, main_bicep_path: Path):
        """Test that resource names don't have consecutive hyphens."""
        content = main_bicep_path.read_text(encoding="utf-8")

        # Find all variable assignments for names
        var_pattern = r"var\s+(\w+Name)\s*=\s*'([^']+)'"
        for match in re.finditer(var_pattern, content):
            var_name = match.group(1)
            name_template = match.group(2)

            # Check static parts for consecutive hyphens
            static = re.sub(r"\$\{[^}]+\}", "x", name_template)
            assert (
                "--" not in static
            ), f"{var_name} should not have consecutive hyphens: {name_template}"

    def test_names_dont_end_with_hyphen(self, main_bicep_path: Path):
        """Test that resource names don't end with a hyphen."""
        content = main_bicep_path.read_text(encoding="utf-8")

        var_pattern = r"var\s+(\w+Name)\s*=\s*'([^']+)'"
        for match in re.finditer(var_pattern, content):
            var_name = match.group(1)
            name_template = match.group(2)

            # The template ends with ${environment}, so static won't end with -
            # But check patterns like 'prefix-${var}-' are avoided
            if name_template.endswith("-"):
                pytest.fail(f"{var_name} template ends with hyphen: {name_template}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
