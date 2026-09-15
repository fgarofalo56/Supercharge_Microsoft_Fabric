# Deployment Tests

Comprehensive test suite for validating Microsoft Fabric Casino/Gaming POC infrastructure deployment configurations.

## Overview

These tests validate Bicep IaC templates without requiring actual Azure deployment. They use static analysis, parsing, and mock contexts to verify:

- **Bicep Syntax & Compilation**: Validates all `.bicep` files compile correctly
- **Resource Naming**: Ensures Azure naming conventions are followed
- **Security Configuration**: Validates security best practices
- **Fabric Configuration**: Tests Microsoft Fabric-specific settings
- **Purview Configuration**: Validates data governance setup

## Test Files

| File | Description |
|------|-------------|
| `conftest.py` | Shared pytest fixtures for Bicep paths, parsing, and mock Azure context |
| `test_bicep_validation.py` | Bicep syntax, compilation, parameters, and module references |
| `test_resource_naming.py` | Azure naming conventions, length limits, character restrictions |
| `test_security_config.py` | Key Vault, storage security, RBAC, private endpoints |
| `test_fabric_config.py` | Fabric capacity SKU, admin email, tags |
| `test_purview_config.py` | Purview diagnostics, role assignments, private endpoints |

## Prerequisites

### Required Tools

1. **Python 3.9+** with pytest:
   ```bash
   pip install pytest
   ```

2. **Azure CLI** (for compilation tests):
   ```bash
   # Install Azure CLI
   # https://docs.microsoft.com/en-us/cli/azure/install-azure-cli

   # Install Bicep CLI
   az bicep install
   az bicep upgrade
   ```

### Optional (for what-if tests)

- Azure subscription with appropriate permissions
- Azure CLI logged in: `az login`

## Running Tests

### Run All Tests

```bash
# From project root
pytest validation/deployment_tests/ -v

# Or from deployment_tests directory
cd validation/deployment_tests
pytest -v
```

### Run Specific Test File

```bash
# Bicep validation only
pytest validation/deployment_tests/test_bicep_validation.py -v

# Security configuration only
pytest validation/deployment_tests/test_security_config.py -v

# Resource naming only
pytest validation/deployment_tests/test_resource_naming.py -v

# Fabric configuration only
pytest validation/deployment_tests/test_fabric_config.py -v

# Purview configuration only
pytest validation/deployment_tests/test_purview_config.py -v
```

### Run Specific Test Class

```bash
# Run all Key Vault security tests
pytest validation/deployment_tests/test_security_config.py::TestKeyVaultSecurity -v

# Run all Bicep compilation tests
pytest validation/deployment_tests/test_bicep_validation.py::TestBicepCompilation -v
```

### Run with Markers

```bash
# Skip tests requiring Azure CLI
pytest validation/deployment_tests/ -v -m "not requires_azure_cli"

# Run only static analysis tests (no external dependencies)
pytest validation/deployment_tests/ -v -k "not whatif"
```

### Run with Coverage

```bash
pip install pytest-cov
pytest validation/deployment_tests/ --cov=. --cov-report=html
```

## Test Categories

### 1. Bicep Validation Tests (`test_bicep_validation.py`)

#### Syntax Tests
- File existence and encoding
- No BOM (Byte Order Mark)
- UTF-8 validity

#### Compilation Tests
- `main.bicep` compiles successfully
- All module files compile
- Bicep linter passes (no errors)

**Note**: Requires Azure CLI with Bicep installed.

#### Parameter Validation
- Required parameters present
- `@allowed` decorators on constrained values
- Length constraints (`@minLength`, `@maxLength`)
- Value constraints (`@minValue`, `@maxValue`)
- All parameters have `@description`

#### Module References
- All expected modules referenced
- Module paths resolve to existing files
- Module outputs are used appropriately

### 2. Resource Naming Tests (`test_resource_naming.py`)

#### Naming Conventions
| Resource Type | Prefix | Example |
|--------------|--------|---------|
| Resource Group | `rg-` | `rg-fabricpoc-dev` |
| Storage Account | `st` | `stfabricpocdev` |
| Key Vault | `kv-` | `kv-fabricpoc-dev` |
| Log Analytics | `log-` | `log-fabricpoc-dev` |
| Managed Identity | `id-` | `id-fabricpoc-dev` |
| Virtual Network | `vnet-` | `vnet-fabricpoc-dev` |
| Subnet | `snet-` | `snet-fabric` |
| NSG | `nsg-` | `nsg-private-endpoints` |
| Private Endpoint | `pe-` | `pe-stfabricpocdev` |
| Purview | `pview` | `pviewfabricpocdev` |
| Fabric Capacity | `fabric` | `fabricfabricpocdev` |

#### Length Limits
- Storage Account: max 24 chars
- Key Vault: max 24 chars
- Resource Group: max 90 chars

#### Character Restrictions
- Storage: lowercase alphanumeric only
- No consecutive hyphens
- No trailing hyphens

### 3. Security Configuration Tests (`test_security_config.py`)

#### Key Vault Security
- Soft delete enabled
- Purge protection enabled
- RBAC authorization (not access policies)
- Network ACLs configured
- Diagnostic settings enabled

#### Storage Security
- HTTPS-only traffic
- TLS 1.2 minimum
- Public blob access disabled
- Encryption enabled
- Container public access: None
- Soft delete enabled

#### Private Endpoints
- Conditional deployment support
- Subnet parameter defined
- Network ACLs updated when enabled
- Correct group IDs specified

#### Managed Identity & RBAC
- User-assigned identity created
- Required outputs (ID, principal ID, client ID)
- Role assignments use `guid()` for names
- Principal type specified

### 4. Fabric Configuration Tests (`test_fabric_config.py`)

#### SKU Validation
- Valid SKUs: F2, F4, F8, F16, F32, F64, F128, F256, F512, F1024, F2048
- `@allowed` decorator enforces valid values
- Default SKU appropriate for environment

#### Admin Email
- Required parameter (no default or placeholder default)
- Passed to Fabric module
- Used in `administration.members`
- Specified in all environment param files

#### Tags
- Tags parameter defined
- Default tags include: Environment, Project, ManagedBy
- Production includes compliance tags (NIGC-MICS)

#### Capacity Properties
- Tier set to 'Fabric'
- Required outputs defined
- API version 2023 or later

### 5. Purview Configuration Tests (`test_purview_config.py`)

#### Diagnostic Settings
- Configured to send to Log Analytics
- All logs enabled
- Metrics enabled

#### Role Assignments
- Data Curator role assigned
- Uses managed identity principal
- `guid()` for unique naming
- Principal type: ServicePrincipal

#### Private Endpoint
- Conditional deployment
- Subnet parameter defined
- Group ID: 'account'
- Public access disabled when PE enabled

#### Identity
- System-assigned managed identity
- Principal ID output available

## Fixtures Reference

### Path Fixtures

```python
@pytest.fixture
def project_root() -> Path:
    """Project root directory"""


@pytest.fixture
def infra_root() -> Path:
    """infra/ directory path"""


@pytest.fixture
def main_bicep_path() -> Path:
    """Path to main.bicep"""


@pytest.fixture
def all_bicep_files() -> List[Path]:
    """All .bicep files in infra/"""


@pytest.fixture
def module_bicep_files() -> Dict[str, Path]:
    """Module files by name (e.g., {'fabric': Path, 'storage': Path})"""


@pytest.fixture
def environment_params() -> Dict[str, Path]:
    """Parameter files by environment (e.g., {'dev': Path, 'prod': Path})"""
```

### Parsed Content Fixtures

```python
@pytest.fixture
def parsed_main_bicep() -> BicepFile:
    """Parsed main.bicep with parameters, resources, outputs"""


@pytest.fixture
def parsed_module_files() -> Dict[str, BicepFile]:
    """All parsed module files"""


@pytest.fixture
def parsed_param_files() -> Dict[str, BicepParamFile]:
    """All parsed parameter files"""
```

### Azure Context Fixtures

```python
@pytest.fixture
def azure_cli_available() -> bool:
    """True if Azure CLI is installed"""


@pytest.fixture
def azure_logged_in() -> bool:
    """True if logged into Azure CLI"""


@pytest.fixture
def bicep_cli_available() -> bool:
    """True if Bicep CLI is available"""


@pytest.fixture
def mock_azure_context() -> Dict:
    """Mock Azure context for tests without Azure"""
```

### Skip Fixtures

```python
@pytest.fixture
def require_azure_cli():
    """Skips test if Azure CLI not available"""


@pytest.fixture
def require_azure_login():
    """Skips test if not logged into Azure"""


@pytest.fixture
def require_bicep_cli():
    """Skips test if Bicep CLI not available"""
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deployment Tests

on:
  push:
    paths:
      - 'infra/**'
  pull_request:
    paths:
      - 'infra/**'

jobs:
  deployment-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Azure CLI
        run: |
          curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
          az bicep install

      - name: Install dependencies
        run: |
          pip install pytest pytest-cov

      - name: Run deployment tests
        run: |
          pytest validation/deployment_tests/ -v --tb=short

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: pytest-results.xml
```

### Azure DevOps Pipeline Example

```yaml
trigger:
  paths:
    include:
      - infra/*

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'

  - script: |
      curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
      az bicep install
    displayName: 'Install Azure CLI and Bicep'

  - script: |
      pip install pytest pytest-cov
    displayName: 'Install Python dependencies'

  - script: |
      pytest validation/deployment_tests/ -v --junitxml=test-results.xml
    displayName: 'Run deployment tests'

  - task: PublishTestResults@2
    inputs:
      testResultsFormat: 'JUnit'
      testResultsFiles: 'test-results.xml'
    condition: always()
```

## Troubleshooting

### Common Issues

#### "Bicep CLI not available"
```bash
# Install Bicep via Azure CLI
az bicep install

# Or install standalone
# Windows
winget install Microsoft.Bicep

# macOS
brew install bicep

# Linux
curl -Lo bicep https://github.com/Azure/bicep/releases/latest/download/bicep-linux-x64
chmod +x bicep
sudo mv bicep /usr/local/bin/
```

#### "Not logged into Azure CLI"
```bash
# Login to Azure
az login

# Or use service principal for CI/CD
az login --service-principal -u <app-id> -p <password> --tenant <tenant-id>
```

#### Tests Skipped
Some tests require external dependencies and will be skipped if unavailable:
- Compilation tests need Bicep CLI
- What-if tests need Azure login

Run without skipping:
```bash
# Ensure Azure CLI and Bicep are installed
az bicep version

# Ensure logged in
az account show

# Run all tests
pytest validation/deployment_tests/ -v
```

## Contributing

When adding new Bicep modules or modifying infrastructure:

1. **Add corresponding tests** for any new resources
2. **Update fixtures** if new modules are added
3. **Run tests locally** before committing
4. **Update this README** if test categories change

### Adding New Test Cases

```python
# In appropriate test file
class TestNewResource:
    """Tests for new resource configuration."""

    def test_new_resource_property(self, module_bicep_files: Dict[str, Path]):
        """Test that new resource has required property."""
        module_path = module_bicep_files.get("new-module")
        if not module_path:
            pytest.skip("New module not found")

        content = module_path.read_text(encoding="utf-8")

        assert "requiredProperty:" in content, (
            "New resource should have required property"
        )
```

## License

Part of the Microsoft Fabric Casino/Gaming POC project.
