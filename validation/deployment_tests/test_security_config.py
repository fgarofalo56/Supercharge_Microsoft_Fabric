"""
Security Configuration Tests

Tests that validate security configurations for:
- Key Vault access policies and features
- Storage account HTTPS-only and encryption
- Private endpoints configuration
- Managed identity proper configuration
- RBAC role assignments
"""

import re
from pathlib import Path
from typing import Any, Dict, List

import pytest


class TestKeyVaultSecurity:
    """Tests for Key Vault security configuration."""

    def test_keyvault_soft_delete_enabled(self, module_bicep_files: dict[str, Path]):
        """Test that Key Vault has soft delete enabled."""
        security_path = module_bicep_files.get("security")
        if not security_path:
            pytest.skip("Security module not found")

        content = security_path.read_text(encoding="utf-8")

        assert "enableSoftDelete: true" in content, (
            "Key Vault should have soft delete enabled"
        )

    def test_keyvault_purge_protection_enabled(
        self, module_bicep_files: dict[str, Path]
    ):
        """Test that Key Vault has purge protection enabled."""
        security_path = module_bicep_files.get("security")
        if not security_path:
            pytest.skip("Security module not found")

        content = security_path.read_text(encoding="utf-8")

        assert "enablePurgeProtection: true" in content, (
            "Key Vault should have purge protection enabled for production safety"
        )

    def test_keyvault_uses_rbac_authorization(
        self, module_bicep_files: dict[str, Path]
    ):
        """Test that Key Vault uses RBAC authorization instead of access policies."""
        security_path = module_bicep_files.get("security")
        if not security_path:
            pytest.skip("Security module not found")

        content = security_path.read_text(encoding="utf-8")

        assert "enableRbacAuthorization: true" in content, (
            "Key Vault should use RBAC authorization (recommended over access policies)"
        )

    def test_keyvault_soft_delete_retention(self, module_bicep_files: dict[str, Path]):
        """Test that Key Vault has adequate soft delete retention."""
        security_path = module_bicep_files.get("security")
        if not security_path:
            pytest.skip("Security module not found")

        content = security_path.read_text(encoding="utf-8")

        # Find softDeleteRetentionInDays value
        retention_pattern = r"softDeleteRetentionInDays:\s*(\d+)"
        match = re.search(retention_pattern, content)

        if match:
            retention_days = int(match.group(1))
            assert retention_days >= 7, (
                f"Soft delete retention should be at least 7 days, got: {retention_days}"
            )
            assert retention_days <= 90, (
                f"Soft delete retention should not exceed 90 days, got: {retention_days}"
            )

    def test_keyvault_network_acls_configured(
        self, module_bicep_files: dict[str, Path]
    ):
        """Test that Key Vault has network ACLs configured."""
        security_path = module_bicep_files.get("security")
        if not security_path:
            pytest.skip("Security module not found")

        content = security_path.read_text(encoding="utf-8")

        assert "networkAcls:" in content, (
            "Key Vault should have network ACLs configured"
        )
        assert "bypass: 'AzureServices'" in content, (
            "Key Vault should bypass Azure services for trusted access"
        )

    def test_keyvault_diagnostic_settings(self, module_bicep_files: dict[str, Path]):
        """Test that Key Vault has diagnostic settings configured."""
        security_path = module_bicep_files.get("security")
        if not security_path:
            pytest.skip("Security module not found")

        content = security_path.read_text(encoding="utf-8")

        assert "diagnosticSettings" in content, (
            "Key Vault should have diagnostic settings configured"
        )
        assert "audit" in content.lower(), "Key Vault should have audit logging enabled"


class TestStorageAccountSecurity:
    """Tests for Storage Account security configuration."""

    def test_storage_https_only(self, module_bicep_files: dict[str, Path]):
        """Test that storage account requires HTTPS only."""
        storage_path = module_bicep_files.get("storage")
        if not storage_path:
            pytest.skip("Storage module not found")

        content = storage_path.read_text(encoding="utf-8")

        assert "supportsHttpsTrafficOnly: true" in content, (
            "Storage account should require HTTPS traffic only"
        )

    def test_storage_minimum_tls_version(self, module_bicep_files: dict[str, Path]):
        """Test that storage account uses TLS 1.2 minimum."""
        storage_path = module_bicep_files.get("storage")
        if not storage_path:
            pytest.skip("Storage module not found")

        content = storage_path.read_text(encoding="utf-8")

        assert "minimumTlsVersion: 'TLS1_2'" in content, (
            "Storage account should require TLS 1.2 minimum"
        )

    def test_storage_public_access_disabled(self, module_bicep_files: dict[str, Path]):
        """Test that storage account has public blob access disabled."""
        storage_path = module_bicep_files.get("storage")
        if not storage_path:
            pytest.skip("Storage module not found")

        content = storage_path.read_text(encoding="utf-8")

        assert "allowBlobPublicAccess: false" in content, (
            "Storage account should disable public blob access"
        )

    def test_storage_encryption_enabled(self, module_bicep_files: dict[str, Path]):
        """Test that storage account has encryption enabled."""
        storage_path = module_bicep_files.get("storage")
        if not storage_path:
            pytest.skip("Storage module not found")

        content = storage_path.read_text(encoding="utf-8")

        assert "encryption:" in content, (
            "Storage account should have encryption configured"
        )
        assert "keySource: 'Microsoft.Storage'" in content or "keySource:" in content, (
            "Storage account should specify encryption key source"
        )

    def test_storage_container_public_access_none(
        self, module_bicep_files: dict[str, Path]
    ):
        """Test that storage containers have no public access."""
        storage_path = module_bicep_files.get("storage")
        if not storage_path:
            pytest.skip("Storage module not found")

        content = storage_path.read_text(encoding="utf-8")

        # All containers should have publicAccess: 'None'
        container_pattern = r"containers@[^']+'\s*=\s*\{[^}]+publicAccess:\s*'([^']+)'"
        matches = re.findall(container_pattern, content, re.DOTALL)

        for access_level in matches:
            assert access_level == "None", (
                f"Container should have publicAccess: 'None', got: {access_level}"
            )

    def test_storage_soft_delete_enabled(self, module_bicep_files: dict[str, Path]):
        """Test that storage account has blob soft delete enabled."""
        storage_path = module_bicep_files.get("storage")
        if not storage_path:
            pytest.skip("Storage module not found")

        content = storage_path.read_text(encoding="utf-8")

        assert "deleteRetentionPolicy:" in content, (
            "Storage account should have blob soft delete configured"
        )
        assert "enabled: true" in content, "Blob soft delete should be enabled"


class TestPrivateEndpointConfiguration:
    """Tests for private endpoint configuration."""

    def test_private_endpoint_conditional_deployment(
        self, module_bicep_files: dict[str, Path]
    ):
        """Test that private endpoints can be conditionally deployed."""
        storage_path = module_bicep_files.get("storage")
        if not storage_path:
            pytest.skip("Storage module not found")

        content = storage_path.read_text(encoding="utf-8")

        # Should have conditional deployment
        assert (
            "if (enablePrivateEndpoint)" in content
            or "param enablePrivateEndpoint" in content
        ), "Private endpoints should be conditionally deployable"

    def test_private_endpoint_subnet_param(self, module_bicep_files: dict[str, Path]):
        """Test that private endpoint subnet is parameterized."""
        storage_path = module_bicep_files.get("storage")
        if not storage_path:
            pytest.skip("Storage module not found")

        content = storage_path.read_text(encoding="utf-8")

        assert "param privateEndpointSubnetId" in content, (
            "Private endpoint should accept subnet ID parameter"
        )

    def test_network_acls_updated_with_private_endpoint(
        self,
        module_bicep_files: dict[str, Path],
    ):
        """Test that network ACLs are updated when private endpoint is enabled."""
        storage_path = module_bicep_files.get("storage")
        if not storage_path:
            pytest.skip("Storage module not found")

        content = storage_path.read_text(encoding="utf-8")

        # Should deny public access when private endpoint enabled
        assert (
            "enablePrivateEndpoint ? 'Deny' : 'Allow'" in content
            or "defaultAction: 'Deny'" in content
        ), "Network ACLs should restrict access when private endpoint is enabled"

    def test_private_endpoint_group_ids(self, module_bicep_files: dict[str, Path]):
        """Test that private endpoints specify correct group IDs."""
        expected_group_ids = {
            "storage": ["dfs", "blob"],
            "governance": ["account", "portal"],
        }

        for module, group_ids in expected_group_ids.items():
            module_path = module_bicep_files.get(module)
            if not module_path:
                continue

            content = module_path.read_text(encoding="utf-8")

            if "privateEndpoints" in content or "privateEndpoint" in content:
                # Check that at least one expected group ID is present
                found_group = False
                for gid in group_ids:
                    if f"'{gid}'" in content:
                        found_group = True
                        break

                if "Microsoft.Network/privateEndpoints" in content:
                    assert found_group, (
                        f"Private endpoint in {module} should specify group ID from {group_ids}"
                    )


class TestManagedIdentityConfiguration:
    """Tests for managed identity configuration."""

    def test_user_assigned_identity_created(self, module_bicep_files: dict[str, Path]):
        """Test that user-assigned managed identity is created."""
        security_path = module_bicep_files.get("security")
        if not security_path:
            pytest.skip("Security module not found")

        content = security_path.read_text(encoding="utf-8")

        assert "Microsoft.ManagedIdentity/userAssignedIdentities" in content, (
            "User-assigned managed identity should be created"
        )

    def test_managed_identity_outputs(self, parsed_module_files: dict[str, Any]):
        """Test that managed identity outputs required properties."""
        security = parsed_module_files.get("security")
        if not security:
            pytest.skip("Security module not found")

        required_outputs = [
            "managedIdentityId",
            "managedIdentityPrincipalId",
            "managedIdentityClientId",
        ]

        for output in required_outputs:
            assert output in security.outputs, f"Security module should output {output}"

    def test_managed_identity_has_role_assignments(
        self,
        module_bicep_files: dict[str, Path],
    ):
        """Test that managed identity has role assignments configured."""
        # Check multiple modules for role assignments
        modules_with_rbac = ["security", "storage", "governance"]

        for module in modules_with_rbac:
            module_path = module_bicep_files.get(module)
            if not module_path:
                continue

            content = module_path.read_text(encoding="utf-8")

            assert "Microsoft.Authorization/roleAssignments" in content, (
                f"Module {module} should have role assignments for managed identity"
            )


class TestRBACConfiguration:
    """Tests for RBAC role assignment configuration."""

    def test_storage_blob_contributor_role(self, module_bicep_files: dict[str, Path]):
        """Test that storage module assigns Storage Blob Data Contributor role."""
        storage_path = module_bicep_files.get("storage")
        if not storage_path:
            pytest.skip("Storage module not found")

        content = storage_path.read_text(encoding="utf-8")

        # Storage Blob Data Contributor role ID
        contributor_role = "ba92f5b4-2d11-453d-a403-e96b0029c9fe"
        assert contributor_role in content, (
            "Storage module should assign Storage Blob Data Contributor role"
        )

    def test_keyvault_secrets_user_role(self, module_bicep_files: dict[str, Path]):
        """Test that Key Vault module assigns Key Vault Secrets User role."""
        security_path = module_bicep_files.get("security")
        if not security_path:
            pytest.skip("Security module not found")

        content = security_path.read_text(encoding="utf-8")

        # Key Vault Secrets User role ID
        secrets_user_role = "4633458b-17de-408a-b874-0445c86b69e6"
        assert secrets_user_role in content, (
            "Security module should assign Key Vault Secrets User role"
        )

    def test_role_assignments_use_guid(self, module_bicep_files: dict[str, Path]):
        """Test that role assignments use guid() for unique names."""
        for module_name, module_path in module_bicep_files.items():
            content = module_path.read_text(encoding="utf-8")

            if "Microsoft.Authorization/roleAssignments" in content:
                assert "guid(" in content, (
                    f"Role assignments in {module_name} should use guid() for unique naming"
                )

    def test_role_assignments_specify_principal_type(
        self,
        module_bicep_files: dict[str, Path],
    ):
        """Test that role assignments specify principalType."""
        for module_name, module_path in module_bicep_files.items():
            content = module_path.read_text(encoding="utf-8")

            if "Microsoft.Authorization/roleAssignments" in content:
                assert "principalType:" in content, (
                    f"Role assignments in {module_name} should specify principalType"
                )


class TestPurviewSecurity:
    """Tests for Purview security configuration."""

    def test_purview_system_identity(self, module_bicep_files: dict[str, Path]):
        """Test that Purview uses system-assigned identity."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance module not found")

        content = purview_path.read_text(encoding="utf-8")

        assert "identity:" in content, "Purview should have managed identity configured"
        assert "type: 'SystemAssigned'" in content, (
            "Purview should use system-assigned managed identity"
        )

    def test_purview_public_access_conditional(
        self, module_bicep_files: dict[str, Path]
    ):
        """Test that Purview public access is conditionally set."""
        purview_path = module_bicep_files.get("governance")
        if not purview_path:
            pytest.skip("Governance module not found")

        content = purview_path.read_text(encoding="utf-8")

        # Should have conditional public access based on private endpoint
        assert "publicNetworkAccess:" in content, (
            "Purview should specify publicNetworkAccess setting"
        )
        assert "enablePrivateEndpoint" in content, (
            "Purview public access should be conditional on private endpoint setting"
        )


class TestNetworkSecurity:
    """Tests for network security configuration."""

    def test_nsg_deny_all_inbound_rule(self, module_bicep_files: dict[str, Path]):
        """Test that NSGs have deny-all inbound rule."""
        vnet_path = module_bicep_files.get("networking")
        if not vnet_path:
            pytest.skip("Networking module not found")

        content = vnet_path.read_text(encoding="utf-8")

        assert "DenyAllInbound" in content or "access: 'Deny'" in content, (
            "NSG should have deny-all inbound rule"
        )

    def test_private_endpoint_subnet_policies_disabled(
        self,
        module_bicep_files: dict[str, Path],
    ):
        """Test that private endpoint subnet has network policies disabled."""
        vnet_path = module_bicep_files.get("networking")
        if not vnet_path:
            pytest.skip("Networking module not found")

        content = vnet_path.read_text(encoding="utf-8")

        assert "privateEndpointNetworkPolicies: 'Disabled'" in content, (
            "Private endpoint subnet should have network policies disabled"
        )

    def test_service_endpoints_configured(self, module_bicep_files: dict[str, Path]):
        """Test that service endpoints are configured for Azure services."""
        vnet_path = module_bicep_files.get("networking")
        if not vnet_path:
            pytest.skip("Networking module not found")

        content = vnet_path.read_text(encoding="utf-8")

        # Check for common service endpoints
        expected_services = ["Microsoft.Storage", "Microsoft.KeyVault"]

        for service in expected_services:
            assert service in content, (
                f"VNet should have service endpoint for {service}"
            )


class TestDiagnosticSettings:
    """Tests for diagnostic settings configuration."""

    def test_all_resources_have_diagnostics(self, module_bicep_files: dict[str, Path]):
        """Test that all resources have diagnostic settings."""
        modules_requiring_diagnostics = [
            "security",
            "storage",
            "governance",
            "monitoring",
        ]

        for module in modules_requiring_diagnostics:
            module_path = module_bicep_files.get(module)
            if not module_path:
                continue

            content = module_path.read_text(encoding="utf-8")

            if (
                module != "monitoring"
            ):  # Monitoring is the log analytics workspace itself
                assert (
                    "diagnosticSettings" in content or "Microsoft.Insights" in content
                ), f"Module {module} should have diagnostic settings configured"

    def test_diagnostics_send_to_log_analytics(
        self, module_bicep_files: dict[str, Path]
    ):
        """Test that diagnostics are sent to Log Analytics."""
        for module_name, module_path in module_bicep_files.items():
            content = module_path.read_text(encoding="utf-8")

            if "diagnosticSettings" in content:
                assert "workspaceId:" in content, (
                    f"Diagnostic settings in {module_name} should send to Log Analytics"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
