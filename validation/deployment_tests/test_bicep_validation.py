"""
Bicep IaC Validation Tests

Tests that validate Bicep templates for:
- Syntactic validity
- Compilation without errors
- Parameter validation (required params, allowed values)
- Module reference resolution
"""

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import pytest


class TestBicepSyntaxValidation:
    """Tests for Bicep file syntactic validation."""

    def test_main_bicep_exists(self, main_bicep_path: Path):
        """Test that main.bicep file exists."""
        assert main_bicep_path.exists(), f"main.bicep not found at {main_bicep_path}"

    def test_main_bicep_not_empty(self, main_bicep_path: Path):
        """Test that main.bicep is not empty."""
        content = main_bicep_path.read_text(encoding="utf-8")
        assert len(content) > 0, "main.bicep is empty"

    def test_all_bicep_files_exist(self, all_bicep_files: list[Path]):
        """Test that all expected Bicep files exist."""
        expected_modules = [
            "fabric-capacity",
            "storage-account",
            "security",
            "vnet",
            "log-analytics",
            "purview",
        ]
        found_modules = [f.stem for f in all_bicep_files]

        for expected in expected_modules:
            assert (
                expected in found_modules
            ), f"Missing expected Bicep module: {expected}"

    def test_bicep_files_have_valid_utf8_encoding(self, all_bicep_files: list[Path]):
        """Test that all Bicep files use valid UTF-8 encoding."""
        for bicep_file in all_bicep_files:
            try:
                bicep_file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                pytest.fail(f"File {bicep_file} is not valid UTF-8 encoded")

    def test_bicep_files_have_no_bom(self, all_bicep_files: list[Path]):
        """Test that Bicep files don't have BOM (Byte Order Mark)."""
        for bicep_file in all_bicep_files:
            with open(bicep_file, "rb") as f:
                first_bytes = f.read(3)
            assert (
                first_bytes != b"\xef\xbb\xbf"
            ), f"File {bicep_file} has UTF-8 BOM which may cause issues"


class TestBicepCompilation:
    """Tests for Bicep compilation."""

    def test_main_bicep_compiles(self, require_bicep_cli, main_bicep_path: Path):
        """Test that main.bicep compiles without errors."""
        result = subprocess.run(
            ["az", "bicep", "build", "--file", str(main_bicep_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"main.bicep compilation failed: {result.stderr}"

        # Clean up generated ARM template
        arm_template = main_bicep_path.with_suffix(".json")
        if arm_template.exists():
            arm_template.unlink()

    def test_all_modules_compile(
        self, require_bicep_cli, module_bicep_files: dict[str, Path]
    ):
        """Test that all Bicep modules compile without errors."""
        failed_modules = []

        for module_name, bicep_path in module_bicep_files.items():
            result = subprocess.run(
                ["az", "bicep", "build", "--file", str(bicep_path)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                failed_modules.append((module_name, result.stderr))

            # Clean up generated ARM template
            arm_template = bicep_path.with_suffix(".json")
            if arm_template.exists():
                arm_template.unlink()

        if failed_modules:
            error_msg = "\n".join(
                [f"- {name}: {error}" for name, error in failed_modules]
            )
            pytest.fail(f"The following modules failed to compile:\n{error_msg}")

    def test_bicep_lint_no_errors(self, require_bicep_cli, main_bicep_path: Path):
        """Test that Bicep linter doesn't report errors."""
        result = subprocess.run(
            ["az", "bicep", "lint", "--file", str(main_bicep_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Linter may return warnings, but shouldn't fail
        # Check for error-level diagnostics
        if "Error" in result.stderr:
            pytest.fail(f"Bicep linter reported errors: {result.stderr}")


class TestParameterValidation:
    """Tests for Bicep parameter validation."""

    def test_required_parameters_present(self, parsed_main_bicep):
        """Test that required parameters are defined in main.bicep."""
        required_params = ["environment", "location", "fabricAdminEmail"]

        for param in required_params:
            assert (
                param in parsed_main_bicep.parameters
            ), f"Required parameter '{param}' not found in main.bicep"

    def test_environment_has_allowed_values(self, parsed_main_bicep):
        """Test that environment parameter has correct allowed values."""
        env_param = parsed_main_bicep.parameters.get("environment")
        assert env_param is not None, "environment parameter not found"

        expected_values = ["dev", "staging", "prod"]
        actual_values = env_param.get("allowed", [])

        for expected in expected_values:
            assert (
                expected in actual_values
            ), f"Environment parameter missing allowed value: {expected}"

    def test_fabric_sku_has_allowed_values(self, parsed_main_bicep):
        """Test that fabricCapacitySku parameter has valid allowed values."""
        sku_param = parsed_main_bicep.parameters.get("fabricCapacitySku")
        assert sku_param is not None, "fabricCapacitySku parameter not found"

        allowed = sku_param.get("allowed", [])
        assert len(allowed) > 0, "fabricCapacitySku should have allowed values"

        # Verify at least F2, F64 are present (common SKUs)
        assert "F64" in allowed, "F64 should be an allowed Fabric SKU"
        assert "F2" in allowed, "F2 should be an allowed Fabric SKU"

    def test_project_prefix_has_length_constraints(self, parsed_main_bicep):
        """Test that projectPrefix has length constraints."""
        prefix_param = parsed_main_bicep.parameters.get("projectPrefix")
        assert prefix_param is not None, "projectPrefix parameter not found"

        min_len = prefix_param.get("minLength")
        max_len = prefix_param.get("maxLength")

        assert min_len is not None, "projectPrefix should have minLength constraint"
        assert max_len is not None, "projectPrefix should have maxLength constraint"
        assert min_len >= 1, "projectPrefix minLength should be at least 1"
        assert max_len <= 20, "projectPrefix maxLength should be reasonable (<=20)"

    def test_log_retention_has_value_constraints(self, parsed_main_bicep):
        """Test that logRetentionDays has min/max value constraints.

        Max ceiling is 4383 days (12 years) to support HIPAA / 42 CFR Part 2
        retention requirements (HIPAA: 6 yrs / NIGC MICS: 5 yrs).
        """
        retention_param = parsed_main_bicep.parameters.get("logRetentionDays")
        assert retention_param is not None, "logRetentionDays parameter not found"

        min_val = retention_param.get("minValue")
        max_val = retention_param.get("maxValue")

        assert min_val is not None, "logRetentionDays should have minValue constraint"
        assert max_val is not None, "logRetentionDays should have maxValue constraint"
        assert min_val >= 30, "Log retention should be at least 30 days"
        assert max_val <= 4383, "Log retention should not exceed 4383 days (12 yrs ceiling)"

    def test_parameters_have_descriptions(self, main_bicep_path: Path):
        """Test that all parameters have @description decorators.

        The regex tolerates additional decorators (@allowed, @minValue, etc.)
        between @description and `param`, and quoted strings containing
        balanced parentheses inside the description text.
        """
        content = main_bicep_path.read_text(encoding="utf-8")

        # Find all param declarations
        param_pattern = r"param\s+(\w+)\s+"
        params = re.findall(param_pattern, content)

        missing_descriptions = []
        for param in params:
            # @description('...') optionally followed by other decorators, then `param NAME `.
            # Use [\s\S]*? for the description body so it can include literal `)`s
            # within balanced quoted strings.
            desc_pattern = (
                r"@description\s*\(\s*'(?:[^'\\]|\\.)*'\s*\)\s*"
                r"(?:@\w+\s*\([\s\S]*?\)\s*)*"
                rf"param\s+{re.escape(param)}\b"
            )
            if not re.search(desc_pattern, content):
                missing_descriptions.append(param)

        if missing_descriptions:
            pytest.fail(
                f"Parameters missing @description: {', '.join(missing_descriptions)}"
            )


class TestModuleReferences:
    """Tests for Bicep module reference resolution."""

    def test_main_references_all_expected_modules(self, main_bicep_path: Path):
        """Test that main.bicep references all expected modules."""
        content = main_bicep_path.read_text(encoding="utf-8")

        expected_modules = [
            "modules/fabric/fabric-capacity.bicep",
            "modules/storage/storage-account.bicep",
            "modules/security/security.bicep",
            "modules/monitoring/log-analytics.bicep",
            "modules/governance/purview.bicep",
            "modules/networking/vnet.bicep",
        ]

        for module in expected_modules:
            assert module in content, f"main.bicep should reference module: {module}"

    def test_all_module_paths_are_valid(self, infra_root: Path, main_bicep_path: Path):
        """Test that all module paths in main.bicep point to existing files."""
        content = main_bicep_path.read_text(encoding="utf-8")

        # Extract module paths
        module_pattern = r"module\s+\w+\s+'([^']+)'"
        module_paths = re.findall(module_pattern, content)

        for rel_path in module_paths:
            full_path = (main_bicep_path.parent / rel_path).resolve()
            assert full_path.exists(), f"Module path not found: {rel_path}"

    def test_module_outputs_are_used(self, main_bicep_path: Path):
        """Test that module outputs are used in main.bicep."""
        content = main_bicep_path.read_text(encoding="utf-8")

        # Check that at least some module outputs are being used
        assert ".outputs." in content, "main.bicep should use module outputs"

        # Check for specific expected output usages
        expected_output_usages = [
            "monitoring.outputs.workspaceId",
            "security.outputs.managedIdentityPrincipalId",
        ]

        for expected in expected_output_usages:
            assert expected in content, f"Expected output usage not found: {expected}"


class TestParameterFiles:
    """Tests for Bicep parameter files."""

    def test_all_environment_param_files_exist(
        self, environment_params: dict[str, Path]
    ):
        """Test that parameter files exist for all environments."""
        expected_envs = ["dev", "staging", "prod"]

        for env in expected_envs:
            assert (
                env in environment_params
            ), f"Missing parameter file for environment: {env}"
            assert environment_params[
                env
            ].exists(), f"Parameter file doesn't exist: {env}"

    def test_param_files_reference_main_bicep(self, all_bicepparam_files: list[Path]):
        """Test that all param files use 'using' directive."""
        for param_file in all_bicepparam_files:
            content = param_file.read_text(encoding="utf-8")
            assert (
                "using" in content
            ), f"Parameter file {param_file.name} should have 'using' directive"

    def test_dev_params_have_required_values(self, parsed_param_files: dict[str, Any]):
        """Test that dev parameter file has required values."""
        dev_params = parsed_param_files.get("dev")
        assert dev_params is not None, "Dev parameters not found"

        required = ["environment", "location", "fabricCapacitySku", "fabricAdminEmail"]
        for param in required:
            assert (
                param in dev_params.parameters
            ), f"Dev params missing required parameter: {param}"

    def test_prod_params_enable_private_endpoints(
        self, parsed_param_files: dict[str, Any]
    ):
        """Test that production parameters enable private endpoints."""
        prod_params = parsed_param_files.get("prod")
        assert prod_params is not None, "Prod parameters not found"

        pe_param = prod_params.parameters.get("enablePrivateEndpoints")
        if pe_param:
            # Should be true for production
            assert (
                pe_param.lower() == "true"
            ), "Production should enable private endpoints"

    def test_param_environments_match_filenames(
        self, parsed_param_files: dict[str, Any]
    ):
        """Test that environment param value matches the filename."""
        for env_name, param_file in parsed_param_files.items():
            env_value = param_file.parameters.get("environment")
            if env_value:
                # Remove quotes if present
                env_value = env_value.strip("'\"")
                assert (
                    env_value == env_name
                ), f"Parameter file {env_name} has mismatched environment value: {env_value}"


class TestBicepBestPractices:
    """Tests for Bicep best practices."""

    def test_target_scope_is_set(self, main_bicep_path: Path):
        """Test that targetScope is explicitly set in main.bicep."""
        content = main_bicep_path.read_text(encoding="utf-8")
        assert "targetScope" in content, "main.bicep should explicitly set targetScope"
        assert (
            "targetScope = 'subscription'" in content
        ), "main.bicep should target subscription scope for resource group creation"

    def test_resources_have_tags_parameter(self, module_bicep_files: dict[str, Path]):
        """Test that all modules accept a tags parameter."""
        for module_name, bicep_path in module_bicep_files.items():
            content = bicep_path.read_text(encoding="utf-8")
            assert (
                "param tags object" in content
            ), f"Module {module_name} should accept tags parameter"

    def test_no_hardcoded_locations(self, module_bicep_files: dict[str, Path]):
        """Test that modules don't hardcode locations."""
        hardcoded_locations = ["'eastus'", "'westus'", "'eastus2'", "'centralus'"]

        for module_name, bicep_path in module_bicep_files.items():
            content = bicep_path.read_text(encoding="utf-8")
            for location in hardcoded_locations:
                # Exclude parameter default values (those are acceptable)
                pattern = rf"(?<!param location string = ){location}"
                matches = re.findall(pattern, content)
                if matches and "param location string" not in content:
                    pytest.fail(
                        f"Module {module_name} has hardcoded location: {location}"
                    )

    def test_modules_use_latest_api_versions(self, module_bicep_files: dict[str, Path]):
        """Test that modules use reasonably recent API versions.

        Some Microsoft RPs publish APIs only on older year stamps (e.g., the
        Power BI Dedicated RP's stable API is still 2021-01-01 and there is no
        newer GA). Allow per-RP overrides for those legitimate cases.
        """
        min_year = 2022
        ALLOWED_OLDER = {
            # RP : minimum_year_allowed_for_this_RP
            "Microsoft.PowerBIDedicated": 2021,
            "Microsoft.PowerBIDedicated/capacities": 2021,
            "Microsoft.OperationsManagement": 2015,
            "Microsoft.OperationsManagement/solutions": 2015,
            "Microsoft.Insights/diagnosticSettings": 2021,
        }

        for module_name, bicep_path in module_bicep_files.items():
            content = bicep_path.read_text(encoding="utf-8")
            # Find lines like  Microsoft.X/y@2023-01-01
            api_pattern = r"(Microsoft\.[A-Za-z]+(?:/[A-Za-z]+)?)@(\d{4})-\d{2}-\d{2}"
            for rp, year_str in re.findall(api_pattern, content):
                year = int(year_str)
                allowed_floor = ALLOWED_OLDER.get(rp, min_year)
                if year < allowed_floor:
                    pytest.fail(
                        f"Module {module_name} uses outdated API version from {year} "
                        f"on {rp}. Consider updating to {allowed_floor} or later."
                    )

    def test_outputs_have_descriptions(self, module_bicep_files: dict[str, Path]):
        """Test that module outputs have @description decorators.

        Tolerates description bodies that contain literal `)` characters by
        consuming the description string explicitly with a balanced quoted body.
        """
        for module_name, bicep_path in module_bicep_files.items():
            content = bicep_path.read_text(encoding="utf-8")

            output_pattern = r"output\s+(\w+)\s+"
            outputs = re.findall(output_pattern, content)

            missing = []
            for output in outputs:
                desc_pattern = (
                    r"@description\s*\(\s*'(?:[^'\\]|\\.)*'\s*\)\s*"
                    rf"output\s+{re.escape(output)}\b"
                )
                if not re.search(desc_pattern, content):
                    missing.append(output)

            if missing:
                pytest.fail(
                    f"Module {module_name} outputs missing @description: {', '.join(missing)}"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
