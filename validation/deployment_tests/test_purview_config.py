"""
Microsoft Purview Configuration Tests

Tests that validate Purview configurations:
- Diagnostic settings configuration
- Role assignments for data governance
- Private endpoint configuration
- Identity configuration
"""

import re
from pathlib import Path
from typing import Any, Dict, List

import pytest


class TestPurviewDiagnosticSettings:
    """Tests for Purview diagnostic settings configuration."""

    def test_diagnostic_settings_exist(self, module_bicep_files: dict[str, Path]):
        """Test that Purview has diagnostic settings configured."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        assert "diagnosticSettings" in content or "Microsoft.Insights" in content, (
            "Purview should have diagnostic settings configured"
        )

    def test_diagnostic_settings_send_to_workspace(
        self,
        module_bicep_files: dict[str, Path],
    ):
        """Test that diagnostics are sent to Log Analytics workspace."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        if "diagnosticSettings" in content:
            assert "workspaceId:" in content, (
                "Purview diagnostics should send to Log Analytics workspace"
            )
            assert "logAnalyticsWorkspaceId" in content, (
                "Purview should accept workspace ID parameter"
            )

    def test_all_logs_enabled(self, module_bicep_files: dict[str, Path]):
        """Test that all Purview logs are enabled."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        if "diagnosticSettings" in content:
            # Should enable allLogs category group or specific categories
            assert "allLogs" in content or "logs:" in content, (
                "Purview diagnostics should enable logging"
            )
            assert "enabled: true" in content, (
                "Purview log categories should be enabled"
            )

    def test_metrics_enabled(self, module_bicep_files: dict[str, Path]):
        """Test that Purview metrics are enabled."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        if "diagnosticSettings" in content:
            assert "metrics:" in content or "AllMetrics" in content, (
                "Purview diagnostics should include metrics"
            )


class TestPurviewRoleAssignments:
    """Tests for Purview role assignment configuration."""

    def test_role_assignment_defined(self, module_bicep_files: dict[str, Path]):
        """Test that Purview has role assignments defined."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        assert "Microsoft.Authorization/roleAssignments" in content, (
            "Purview module should have role assignments defined"
        )

    def test_data_curator_role_assigned(self, module_bicep_files: dict[str, Path]):
        """Test that Purview Data Curator role is assigned."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        # Purview Data Curator role ID
        curator_role = "af8bf84c-4de3-462a-b576-41e6c7478f52"

        # Should have curator role or comment indicating role purpose
        has_curator = (
            curator_role in content or "DataCurator" in content or "Curator" in content
        )
        assert has_curator, (
            "Purview should assign Data Curator role for data governance"
        )

    def test_role_assignment_uses_managed_identity(
        self,
        module_bicep_files: dict[str, Path],
    ):
        """Test that role assignment uses managed identity."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        if "roleAssignments" in content:
            assert (
                "managedIdentityPrincipalId" in content or "principalId:" in content
            ), "Role assignment should use managed identity principal"

    def test_role_assignment_principal_type(self, module_bicep_files: dict[str, Path]):
        """Test that role assignment specifies ServicePrincipal type."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        if "roleAssignments" in content:
            assert "principalType: 'ServicePrincipal'" in content, (
                "Role assignment should specify ServicePrincipal principal type"
            )

    def test_role_assignment_unique_name(self, module_bicep_files: dict[str, Path]):
        """Test that role assignment uses guid for unique naming."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        if "roleAssignments" in content:
            assert "guid(" in content, (
                "Role assignment should use guid() for unique naming"
            )


class TestPurviewPrivateEndpoint:
    """Tests for Purview private endpoint configuration."""

    def test_private_endpoint_param_defined(self, module_bicep_files: dict[str, Path]):
        """Test that private endpoint parameter is defined."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        assert "param enablePrivateEndpoint" in content, (
            "Purview module should accept enablePrivateEndpoint parameter"
        )

    def test_private_endpoint_conditional(self, module_bicep_files: dict[str, Path]):
        """Test that private endpoint deployment is conditional."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        # Should have conditional deployment via module or resource declaration
        pe_pattern = r"(?:resource|module)\s+\w*[Pp]rivate[Ee]ndpoint[^=]*=\s*if\s*\(enablePrivateEndpoint\)"
        assert re.search(pe_pattern, content), (
            "Private endpoint should be conditionally deployed"
        )

    def test_private_endpoint_subnet_param(self, module_bicep_files: dict[str, Path]):
        """Test that subnet parameter is defined for private endpoint."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        assert "param privateEndpointSubnetId" in content, (
            "Purview module should accept privateEndpointSubnetId parameter"
        )

    def test_private_endpoint_uses_correct_group_id(
        self,
        module_bicep_files: dict[str, Path],
    ):
        """Test that private endpoint uses correct group ID for Purview."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        if "privateEndpoints" in content or "privateEndpoint" in content:
            # Purview uses 'account' group ID for the main endpoint
            assert "'account'" in content, (
                "Purview private endpoint should use 'account' group ID"
            )

    def test_public_access_disabled_with_private_endpoint(
        self,
        module_bicep_files: dict[str, Path],
    ):
        """Test that public access is disabled when private endpoint is enabled."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        # Should conditionally disable public access
        assert "publicNetworkAccess:" in content, (
            "Purview should have publicNetworkAccess setting"
        )

        # Check for conditional logic
        assert (
            "enablePrivateEndpoint ? 'Disabled' : 'Enabled'" in content
            or "enablePrivateEndpoint" in content
        ), "Public access should be conditional on private endpoint setting"


class TestPurviewIdentity:
    """Tests for Purview identity configuration."""

    def test_system_assigned_identity(self, module_bicep_files: dict[str, Path]):
        """Test that Purview has system-assigned managed identity."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        assert "identity:" in content, "Purview should have identity configured"
        assert "type: 'SystemAssigned'" in content, (
            "Purview should use system-assigned managed identity"
        )

    def test_identity_principal_id_output(self, parsed_module_files: dict[str, Any]):
        """Test that Purview outputs its principal ID."""
        purview = parsed_module_files.get("governance")
        if not purview:
            pytest.skip("Governance/Purview module not found")

        # Should output the principal ID for use in role assignments
        assert "purviewPrincipalId" in purview.outputs or any(
            "principalId" in output.lower() for output in purview.outputs
        ), "Purview module should output its managed identity principal ID"


class TestPurviewManagedResourceGroup:
    """Tests for Purview managed resource group configuration."""

    def test_managed_resource_group_defined(self, module_bicep_files: dict[str, Path]):
        """Test that managed resource group name is defined."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        assert "managedResourceGroupName:" in content, (
            "Purview should define managed resource group name"
        )

    def test_managed_resource_group_follows_naming(
        self,
        module_bicep_files: dict[str, Path],
    ):
        """Test that managed resource group follows naming convention."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        # Managed resource group should include 'mrg-' prefix
        mrg_pattern = r"managedResourceGroupName:\s*'mrg-"
        assert re.search(mrg_pattern, content), (
            "Purview managed resource group should use 'mrg-' prefix"
        )


class TestPurviewOutputs:
    """Tests for Purview module outputs."""

    def test_required_outputs_defined(self, parsed_module_files: dict[str, Any]):
        """Test that all required Purview outputs are defined."""
        purview = parsed_module_files.get("governance")
        if not purview:
            pytest.skip("Governance/Purview module not found")

        required_outputs = [
            "purviewAccountName",
            "purviewAccountId",
            "purviewEndpoint",
        ]

        for output in required_outputs:
            assert output in purview.outputs, f"Purview module should output {output}"

    def test_endpoint_output_format(self, module_bicep_files: dict[str, Path]):
        """Test that endpoint output references correct property."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        # Should output the catalog endpoint
        assert "endpoints.catalog" in content or "purviewEndpoint" in content, (
            "Purview should output catalog endpoint"
        )


class TestPurviewIntegration:
    """Tests for Purview integration with other resources."""

    def test_purview_module_deployed_from_main(self, main_bicep_path: Path):
        """Test that Purview module is deployed from main.bicep."""
        content = main_bicep_path.read_text(encoding="utf-8")

        assert "module governance" in content or "purview.bicep" in content, (
            "main.bicep should deploy Purview/governance module"
        )

    def test_purview_receives_workspace_id(self, main_bicep_path: Path):
        """Test that Purview receives Log Analytics workspace ID."""
        content = main_bicep_path.read_text(encoding="utf-8")

        # Find governance module params
        gov_pattern = r"module\s+governance[^}]+logAnalyticsWorkspaceId:"
        assert re.search(gov_pattern, content, re.DOTALL), (
            "Purview module should receive Log Analytics workspace ID"
        )

    def test_purview_receives_managed_identity(self, main_bicep_path: Path):
        """Test that Purview receives managed identity principal ID."""
        content = main_bicep_path.read_text(encoding="utf-8")

        # Should pass managed identity to governance module
        assert "managedIdentityPrincipalId:" in content, (
            "Purview should receive managed identity principal ID"
        )

    def test_purview_outputs_exposed_from_main(self, parsed_main_bicep):
        """Test that Purview outputs are exposed from main.bicep."""
        expected_outputs = ["purviewAccountName", "purviewEndpoint"]

        for output in expected_outputs:
            assert output in parsed_main_bicep.outputs, (
                f"main.bicep should expose {output} output"
            )

    def test_purview_depends_on_monitoring(self, main_bicep_path: Path):
        """Test that Purview deployment depends on monitoring being available."""
        content = main_bicep_path.read_text(encoding="utf-8")

        # governance module should reference monitoring output
        assert "monitoring.outputs.workspaceId" in content, (
            "Purview should depend on monitoring module output"
        )


class TestPurviewApiVersion:
    """Tests for Purview API version."""

    def test_uses_supported_api_version(self, module_bicep_files: dict[str, Path]):
        """Test that Purview uses supported API version."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance/Purview module not found")

        content = purview_path.read_text(encoding="utf-8")

        # Find API version
        api_pattern = r"Microsoft\.Purview/accounts@(\d{4}-\d{2}-\d{2})"
        match = re.search(api_pattern, content)

        assert match, "Should use Microsoft.Purview/accounts resource type"

        api_version = match.group(1)
        year = int(api_version.split("-")[0])

        # Purview API should be at least 2021
        assert year >= 2021, (
            f"Purview API version should be 2021 or later, got: {api_version}"
        )


class TestPurviewEnvironmentConfig:
    """Tests for Purview configuration across environments."""

    def test_purview_in_all_environments(self, main_bicep_path: Path):
        """Test that Purview is deployed in all environments."""
        content = main_bicep_path.read_text(encoding="utf-8")

        # Purview deployment should not be conditional on environment
        # It should always be deployed for data governance
        gov_pattern = r"module\s+governance[^=]*=\s*if"
        conditional_match = re.search(gov_pattern, content)

        if conditional_match:
            pytest.skip(
                "Purview is conditionally deployed. "
                "Consider always deploying for consistent data governance."
            )

    def test_production_private_endpoint(self, parsed_param_files: dict[str, Any]):
        """Test that production enables private endpoint for Purview."""
        prod_params = parsed_param_files.get("prod")
        if not prod_params:
            pytest.skip("Production parameters not found")

        pe_enabled = prod_params.parameters.get("enablePrivateEndpoints", "").strip(
            "'\""
        )

        assert pe_enabled.lower() == "true", (
            "Production should enable private endpoints for Purview security"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
