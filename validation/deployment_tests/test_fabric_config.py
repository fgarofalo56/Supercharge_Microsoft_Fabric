"""
Microsoft Fabric Configuration Tests

Tests that validate Fabric-specific configurations:
- Capacity SKU validation
- Admin email requirements
- Tag application
- Capacity properties
"""

import re
from pathlib import Path
from typing import Any, Dict, List

import pytest

# =============================================================================
# Valid Fabric SKUs
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

SKU_CAPACITY_UNITS = {
    "F2": 2,
    "F4": 4,
    "F8": 8,
    "F16": 16,
    "F32": 32,
    "F64": 64,
    "F128": 128,
    "F256": 256,
    "F512": 512,
    "F1024": 1024,
    "F2048": 2048,
}


class TestFabricCapacitySKU:
    """Tests for Fabric capacity SKU validation."""

    def test_sku_parameter_defined(self, parsed_main_bicep):
        """Test that SKU parameter is defined in main.bicep."""
        assert "fabricCapacitySku" in parsed_main_bicep.parameters or "skuName" in str(
            parsed_main_bicep.content
        ), "Fabric capacity SKU parameter should be defined"

    def test_sku_has_allowed_values(self, main_bicep_path: Path):
        """Test that SKU parameter has @allowed decorator."""
        content = main_bicep_path.read_text(encoding="utf-8")

        # Find allowed values for fabricCapacitySku
        allowed_pattern = (
            r"@allowed\s*\(\s*\[([^\]]+)\]\s*\)\s*param\s+fabricCapacitySku"
        )
        match = re.search(allowed_pattern, content)

        assert match, "fabricCapacitySku should have @allowed decorator"

        allowed_str = match.group(1)
        defined_skus = [s.strip().strip("'\"") for s in allowed_str.split(",")]

        # Verify all defined SKUs are valid
        for sku in defined_skus:
            assert (
                sku in VALID_FABRIC_SKUS
            ), f"Invalid Fabric SKU in allowed values: {sku}"

    def test_all_valid_skus_are_allowed(self, main_bicep_path: Path):
        """Test that all valid Fabric SKUs are available."""
        content = main_bicep_path.read_text(encoding="utf-8")

        # Find allowed values
        allowed_pattern = (
            r"@allowed\s*\(\s*\[([^\]]+)\]\s*\)\s*param\s+fabricCapacitySku"
        )
        match = re.search(allowed_pattern, content)

        if match:
            allowed_str = match.group(1)
            defined_skus = [s.strip().strip("'\"") for s in allowed_str.split(",")]

            # At minimum, common SKUs should be available
            essential_skus = ["F2", "F64"]
            for sku in essential_skus:
                assert (
                    sku in defined_skus
                ), f"Essential SKU {sku} should be in allowed values"

    def test_module_sku_parameter_validation(self, module_bicep_files: dict[str, Path]):
        """Test that Fabric module validates SKU parameter."""
        fabric_path = module_bicep_files.get("fabric")
        if not fabric_path:
            pytest.skip("Fabric module not found")

        content = fabric_path.read_text(encoding="utf-8")

        # Should have @allowed decorator on skuName parameter
        assert (
            "@allowed" in content
        ), "Fabric module should validate SKU parameter with @allowed"

    def test_default_sku_is_reasonable(self, parsed_param_files: dict[str, Any]):
        """Test that default SKU values are reasonable for each environment."""
        for env, params in parsed_param_files.items():
            sku = params.parameters.get("fabricCapacitySku", "").strip("'\"")

            if sku:
                assert sku in VALID_FABRIC_SKUS, f"Invalid SKU for {env}: {sku}"

                # Dev should not use overly large SKUs by default
                if env == "dev":
                    capacity = SKU_CAPACITY_UNITS.get(sku, 0)
                    # Warning level - not a failure, just check
                    if capacity > 64:
                        pytest.skip(
                            f"Dev environment using large SKU ({sku}). "
                            "Consider smaller SKU for cost savings."
                        )


class TestFabricAdminEmail:
    """Tests for Fabric admin email requirements."""

    def test_admin_email_required(self, parsed_main_bicep):
        """Test that admin email parameter is required (no default)."""
        admin_param = parsed_main_bicep.parameters.get("fabricAdminEmail")
        assert admin_param is not None, "fabricAdminEmail parameter should be defined"

        # Should not have a default (or default should be placeholder)
        default_value = admin_param.get("default")
        if default_value:
            # If there's a default, it should be obvious placeholder
            default_clean = default_value.strip("'\"")
            assert (
                "@contoso.com" in default_clean or "example" in default_clean.lower()
            ), f"Admin email default should be obvious placeholder, got: {default_value}"

    def test_admin_email_passed_to_module(self, main_bicep_path: Path):
        """Test that admin email is passed to Fabric module."""
        content = main_bicep_path.read_text(encoding="utf-8")

        # Should pass fabricAdminEmail to module
        assert (
            "adminEmail: fabricAdminEmail" in content or "adminEmail:" in content
        ), "Admin email should be passed to Fabric module"

    def test_module_uses_admin_email(self, module_bicep_files: dict[str, Path]):
        """Test that Fabric module uses admin email in capacity configuration."""
        fabric_path = module_bicep_files.get("fabric")
        if not fabric_path:
            pytest.skip("Fabric module not found")

        content = fabric_path.read_text(encoding="utf-8")

        # Should use adminEmail in administration.members
        assert (
            "administration:" in content
        ), "Fabric capacity should have administration block"
        assert "members:" in content, "Fabric capacity should have members array"
        assert (
            "adminEmail" in content
        ), "Fabric capacity should reference adminEmail parameter"

    def test_admin_email_in_param_files(self, parsed_param_files: dict[str, Any]):
        """Test that all environment param files specify admin email."""
        for env, params in parsed_param_files.items():
            email = params.parameters.get("fabricAdminEmail", "").strip("'\"")
            assert email, f"Environment {env} should specify fabricAdminEmail"

            # Basic email format validation
            assert (
                "@" in email
            ), f"Admin email for {env} should be valid email format: {email}"


class TestFabricTags:
    """Tests for tag application to Fabric resources."""

    def test_tags_param_defined(self, parsed_main_bicep):
        """Test that tags parameter is defined."""
        assert (
            "tags" in parsed_main_bicep.parameters
        ), "Tags parameter should be defined in main.bicep"

    def test_default_tags_applied(self, main_bicep_path: Path):
        """Test that default tags are applied to resources."""
        content = main_bicep_path.read_text(encoding="utf-8")

        # Should have defaultTags variable
        assert (
            "var defaultTags" in content or "defaultTags" in content
        ), "Should have default tags variable"

        # Default tags should include essential metadata
        essential_tags = ["Environment", "Project", "ManagedBy"]
        for tag in essential_tags:
            assert tag in content, f"Default tags should include '{tag}'"

    def test_fabric_module_accepts_tags(self, module_bicep_files: dict[str, Path]):
        """Test that Fabric module accepts tags parameter."""
        fabric_path = module_bicep_files.get("fabric")
        if not fabric_path:
            pytest.skip("Fabric module not found")

        content = fabric_path.read_text(encoding="utf-8")

        assert (
            "param tags object" in content
        ), "Fabric module should accept tags parameter"

    def test_fabric_capacity_has_tags(self, module_bicep_files: dict[str, Path]):
        """Test that Fabric capacity resource has tags applied."""
        fabric_path = module_bicep_files.get("fabric")
        if not fabric_path:
            pytest.skip("Fabric module not found")

        content = fabric_path.read_text(encoding="utf-8")

        # Find the fabricCapacity resource and check for tags
        resource_pattern = r"resource\s+fabricCapacity[^{]+\{[^}]+tags:"
        assert re.search(
            resource_pattern, content, re.DOTALL
        ), "Fabric capacity resource should have tags property"

    def test_environment_specific_tags(self, parsed_param_files: dict[str, Any]):
        """Test that environments have appropriate tags."""
        for env, params in parsed_param_files.items():
            tags_value = params.parameters.get("tags", "")

            # Environment-specific tags should include environment info
            assert (
                "Environment" in tags_value or env in tags_value.lower()
            ), f"Tags for {env} should include environment information"

    def test_production_compliance_tags(self, parsed_param_files: dict[str, Any]):
        """Test that production has compliance-related tags."""
        prod_params = parsed_param_files.get("prod")
        if not prod_params:
            pytest.skip("Production parameters not found")

        tags_value = prod_params.parameters.get("tags", "")

        # Production should have compliance tags for gaming industry
        compliance_keywords = ["Compliance", "NIGC", "MICS", "Gaming"]
        has_compliance = any(kw in tags_value for kw in compliance_keywords)

        if not has_compliance:
            pytest.skip(
                "Production may need compliance tags (NIGC-MICS) for gaming. "
                "Consider adding Compliance tag."
            )


class TestFabricCapacityProperties:
    """Tests for Fabric capacity properties configuration."""

    def test_capacity_tier_is_fabric(self, module_bicep_files: dict[str, Path]):
        """Test that capacity tier is set to 'Fabric'."""
        fabric_path = module_bicep_files.get("fabric")
        if not fabric_path:
            pytest.skip("Fabric module not found")

        content = fabric_path.read_text(encoding="utf-8")

        assert (
            "tier: 'Fabric'" in content
        ), "Fabric capacity should have tier set to 'Fabric'"

    def test_capacity_outputs_defined(self, parsed_module_files: dict[str, Any]):
        """Test that Fabric module outputs capacity properties."""
        fabric = parsed_module_files.get("fabric")
        if not fabric:
            pytest.skip("Fabric module not found")

        expected_outputs = ["capacityName", "capacityId"]
        for output in expected_outputs:
            assert output in fabric.outputs, f"Fabric module should output {output}"

    def test_capacity_uses_correct_api_version(
        self, module_bicep_files: dict[str, Path]
    ):
        """Test that Fabric capacity uses appropriate API version."""
        fabric_path = module_bicep_files.get("fabric")
        if not fabric_path:
            pytest.skip("Fabric module not found")

        content = fabric_path.read_text(encoding="utf-8")

        # Find API version
        api_pattern = r"Microsoft\.Fabric/capacities@(\d{4}-\d{2}-\d{2})"
        match = re.search(api_pattern, content)

        assert match, "Should use Microsoft.Fabric/capacities resource type"

        api_version = match.group(1)
        year = int(api_version.split("-")[0])

        assert (
            year >= 2023
        ), f"Fabric API version should be 2023 or later, got: {api_version}"


class TestFabricModuleStructure:
    """Tests for Fabric module structure and organization."""

    def test_module_has_description_header(self, module_bicep_files: dict[str, Path]):
        """Test that Fabric module has descriptive header comments."""
        fabric_path = module_bicep_files.get("fabric")
        if not fabric_path:
            pytest.skip("Fabric module not found")

        content = fabric_path.read_text(encoding="utf-8")

        # Should have header comment
        assert content.strip().startswith("//") or content.strip().startswith(
            "/*"
        ), "Fabric module should have header documentation"

    def test_module_parameters_have_descriptions(
        self, module_bicep_files: dict[str, Path]
    ):
        """Test that all Fabric module parameters have descriptions."""
        fabric_path = module_bicep_files.get("fabric")
        if not fabric_path:
            pytest.skip("Fabric module not found")

        content = fabric_path.read_text(encoding="utf-8")

        # Find all params
        param_pattern = r"param\s+(\w+)\s+"
        params = re.findall(param_pattern, content)

        # Allow any number of additional decorators (e.g., @allowed, @minValue)
        # between @description and the param keyword.
        missing_desc = []
        for param in params:
            desc_pattern = rf"@description\s*\([^\)]+\)\s*(?:@\w+\s*\([^\)]*\)\s*)*param\s+{param}\s+"
            if not re.search(desc_pattern, content):
                missing_desc.append(param)

        if missing_desc:
            pytest.fail(
                f"Fabric module parameters missing @description: {', '.join(missing_desc)}"
            )

    def test_module_outputs_have_descriptions(
        self, module_bicep_files: dict[str, Path]
    ):
        """Test that all Fabric module outputs have descriptions."""
        fabric_path = module_bicep_files.get("fabric")
        if not fabric_path:
            pytest.skip("Fabric module not found")

        content = fabric_path.read_text(encoding="utf-8")

        # Find all outputs
        output_pattern = r"output\s+(\w+)\s+"
        outputs = re.findall(output_pattern, content)

        missing_desc = []
        for output in outputs:
            desc_pattern = rf"@description\s*\([^\)]+\)\s*output\s+{output}\s+"
            if not re.search(desc_pattern, content):
                missing_desc.append(output)

        if missing_desc:
            pytest.fail(
                f"Fabric module outputs missing @description: {', '.join(missing_desc)}"
            )


class TestFabricIntegration:
    """Tests for Fabric integration with other resources."""

    def test_fabric_module_deployment_in_main(self, main_bicep_path: Path):
        """Test that Fabric module is deployed from main.bicep."""
        content = main_bicep_path.read_text(encoding="utf-8")

        assert (
            "module fabric" in content or "fabric-capacity.bicep" in content
        ), "main.bicep should deploy Fabric module"

    def test_fabric_depends_on_resource_group(self, main_bicep_path: Path):
        """Test that Fabric deployment is scoped to resource group."""
        content = main_bicep_path.read_text(encoding="utf-8")

        # Find fabric module deployment
        fabric_pattern = r"module\s+fabric[^{]+\{[^}]+scope:\s*resourceGroup"
        assert re.search(
            fabric_pattern, content, re.DOTALL
        ), "Fabric module should be scoped to resource group"

    def test_fabric_outputs_exposed_from_main(self, parsed_main_bicep):
        """Test that Fabric outputs are exposed from main.bicep."""
        expected_outputs = ["fabricCapacityName", "fabricCapacityId"]

        for output in expected_outputs:
            assert (
                output in parsed_main_bicep.outputs
            ), f"main.bicep should expose {output} output"


class TestFabricEnvironmentConfiguration:
    """Tests for Fabric configuration across environments."""

    def test_dev_environment_configuration(self, parsed_param_files: dict[str, Any]):
        """Test that dev environment has appropriate Fabric configuration."""
        dev_params = parsed_param_files.get("dev")
        if not dev_params:
            pytest.skip("Dev parameters not found")

        # Dev should have Fabric SKU
        sku = dev_params.parameters.get("fabricCapacitySku", "").strip("'\"")
        assert sku in VALID_FABRIC_SKUS, f"Dev should have valid Fabric SKU, got: {sku}"

    def test_prod_environment_configuration(self, parsed_param_files: dict[str, Any]):
        """Test that prod environment has appropriate Fabric configuration."""
        prod_params = parsed_param_files.get("prod")
        if not prod_params:
            pytest.skip("Prod parameters not found")

        # Production should have Fabric SKU
        sku = prod_params.parameters.get("fabricCapacitySku", "").strip("'\"")
        assert (
            sku in VALID_FABRIC_SKUS
        ), f"Prod should have valid Fabric SKU, got: {sku}"

    def test_consistent_location_across_environments(
        self,
        parsed_param_files: dict[str, Any],
    ):
        """Test that location is consistent across environments."""
        locations = {}
        for env, params in parsed_param_files.items():
            location = params.parameters.get("location", "").strip("'\"")
            if location:
                locations[env] = location

        if len(set(locations.values())) > 1:
            # Different locations might be intentional for DR
            pytest.skip(
                f"Different locations across environments: {locations}. "
                "This may be intentional for DR scenarios."
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
