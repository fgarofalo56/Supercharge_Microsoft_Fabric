# Integration Tests for Microsoft Fabric Casino/Gaming POC

This directory contains comprehensive integration tests for validating the data generation, pipeline transformations, schema compliance, and regulatory requirements of the Casino/Gaming proof-of-concept.

## Test Structure

```
integration_tests/
├── conftest.py                    # Shared fixtures and configuration
├── test_generator_integration.py  # Generator integration tests
├── test_data_pipeline.py          # Data pipeline transformation tests
├── test_schema_compliance.py      # JSON schema validation tests
├── test_compliance_rules.py       # Business/regulatory compliance tests
├── test_streaming_integration.py  # Streaming functionality tests
├── test_notebook_imports.py       # Notebook dependency tests
└── README.md                      # This file
```

## Test Categories

### 1. Generator Integration Tests (`test_generator_integration.py`)
Tests that verify all data generators work together correctly:
- All generators can be instantiated together
- Player IDs are compatible across generators for cross-referencing
- Date ranges are consistent across generators
- Seed reproducibility for deterministic test runs

### 2. Data Pipeline Tests (`test_data_pipeline.py`)
Tests for medallion architecture transformations:
- **Bronze -> Silver**: Null filtering, type casting, standardization, deduplication, data quality scoring
- **Silver -> Gold**: Aggregations, KPI calculations, net win, hold percentage, player metrics
- Data type consistency through layers
- Null handling behavior

### 3. Schema Compliance Tests (`test_schema_compliance.py`)
Tests validating generated data against JSON schemas:
- Required field presence
- Field type validation (string, number, datetime)
- Enum value validation (event types, zones, loyalty tiers)
- Pattern matching (machine_id, player_id formats)
- Constraint validation (minimum values, ranges)

### 4. Compliance Rules Tests (`test_compliance_rules.py`)
Tests for regulatory compliance requirements:
- **CTR Threshold**: $10,000 triggers Currency Transaction Report
- **W-2G Threshold**: $1,200 for slots, $600 for table games (300:1 odds)
- **SAR Detection**: Suspicious Activity Report pattern detection
- **PII Masking**: SSN hashing, name masking, no raw PII exposure

### 5. Streaming Integration Tests (`test_streaming_integration.py`)
Tests for real-time streaming functionality:
- EventHubProducer initialization and configuration
- Event generation and JSON serialization
- Rate limiting and max events constraints
- Graceful shutdown handling
- Callback functionality

### 6. Notebook Import Tests (`test_notebook_imports.py`)
Tests for notebook dependencies:
- Import statement parsing and validation
- Standard library availability
- No circular dependencies between notebooks
- Layer ordering (Bronze -> Silver -> Gold)
- Required packages documentation

## Running Tests

### Run All Integration Tests
```bash
cd E:\Repos\GitHub\MyDemoRepos\Suppercharge_Microsoft_Fabric
pytest validation/integration_tests/ -v
```

### Run by Marker
```bash
# Integration tests only
pytest validation/integration_tests/ -m integration -v

# Compliance tests only
pytest validation/integration_tests/ -m compliance -v

# Schema tests only
pytest validation/integration_tests/ -m schema -v

# Streaming tests only
pytest validation/integration_tests/ -m streaming -v

# Pipeline tests only
pytest validation/integration_tests/ -m pipeline -v
```

### Run Specific Test File
```bash
# Generator tests
pytest validation/integration_tests/test_generator_integration.py -v

# Compliance rules tests
pytest validation/integration_tests/test_compliance_rules.py -v
```

### Skip Slow Tests
```bash
pytest validation/integration_tests/ -m "not slow" -v
```

### Run with Coverage
```bash
pytest validation/integration_tests/ --cov=data_generation --cov-report=html
```

## Test Markers

The tests use the following pytest markers:

| Marker | Description |
|--------|-------------|
| `@pytest.mark.integration` | All integration tests |
| `@pytest.mark.compliance` | Regulatory compliance tests |
| `@pytest.mark.schema` | JSON schema validation tests |
| `@pytest.mark.streaming` | Streaming functionality tests |
| `@pytest.mark.pipeline` | Data pipeline tests |
| `@pytest.mark.slow` | Long-running tests |

## Fixtures

### Session-Scoped Fixtures
These fixtures are created once per test session for efficiency:

| Fixture | Description |
|---------|-------------|
| `fixed_seed` | Fixed seed (42) for reproducible tests |
| `fixed_date_range` | Fixed date range (Jan 2024) |
| `slot_generator` | SlotMachineGenerator instance |
| `player_generator` | PlayerGenerator instance |
| `compliance_generator` | ComplianceGenerator instance |
| `financial_generator` | FinancialGenerator instance |
| `security_generator` | SecurityGenerator instance |
| `table_games_generator` | TableGamesGenerator instance |
| `all_generators` | Dictionary of all generators |
| `sample_slot_data` | 1000 slot machine records |
| `sample_player_data` | 500 player records |
| `sample_compliance_data` | 500 compliance records |
| `sample_financial_data` | 1000 financial records |

### Schema Fixtures
| Fixture | Description |
|---------|-------------|
| `slot_telemetry_schema` | Slot telemetry JSON schema |
| `player_profile_schema` | Player profile JSON schema |
| `compliance_filing_schema` | Compliance filing JSON schema |
| `financial_transaction_schema` | Financial transaction JSON schema |
| `all_schemas` | Dictionary of all schemas |

### Validation Fixtures
| Fixture | Description |
|---------|-------------|
| `validate_player_id_format` | Player ID pattern validator |
| `validate_machine_id_format` | Machine ID pattern validator |
| `validate_ssn_hash` | SSN hash validator |
| `validate_iso_datetime` | ISO datetime validator |

## Compliance Thresholds

The tests validate the following regulatory thresholds:

### CTR (Currency Transaction Report)
- Threshold: **$10,000** aggregate cash transactions per gaming day
- Required fields: Amount, player ID, transaction date

### W-2G (Gambling Winnings)
- Slots/Video Poker: **$1,200**
- Keno: **$1,500**
- Bingo: **$1,200**
- Poker Tournament: **$5,000**
- Table Games: **$600** (at 300:1 odds or greater)

### SAR (Suspicious Activity Report)
- Structuring: Multiple transactions just below $10,000
- Required: Suspicion category and narrative

### PII Protection
- SSN: SHA-256 hashed (64 hex characters)
- SSN Display: Masked format `XXX-XX-####`
- Names: Masked when PII disabled
- Addresses: Masked when PII disabled

## Adding New Tests

### 1. Add Test Class
```python
class TestNewFeature:
    """Tests for new feature."""

    def test_feature_behavior(self, sample_slot_data):
        """Test specific behavior."""
        # Arrange
        data = sample_slot_data.copy()

        # Act
        result = some_transformation(data)

        # Assert
        assert expected_condition
```

### 2. Use Appropriate Markers
```python
@pytest.mark.compliance
@pytest.mark.slow
def test_complex_compliance_rule(self, sample_compliance_data):
    ...
```

### 3. Add Fixtures if Needed
Add to `conftest.py`:
```python
@pytest.fixture(scope="session")
def new_fixture():
    """Description of fixture."""
    return setup_value
```

## Dependencies

Required packages for running tests:
- `pytest` >= 7.0
- `pytest-asyncio` (for async tests)
- `pandas`
- `numpy`
- `faker`

Optional:
- `pytest-cov` (for coverage reports)
- `azure-eventhub` (for full streaming tests)

## Troubleshooting

### Import Errors
Ensure the data_generation directory is in PYTHONPATH:
```bash
set PYTHONPATH=%PYTHONPATH%;E:\Repos\GitHub\MyDemoRepos\Suppercharge_Microsoft_Fabric\data_generation
```

### Fixture Not Found
Verify `conftest.py` is in the test directory and contains the required fixture.

### Schema Not Found
Ensure JSON schemas exist in `data_generation/schemas/`.

### Slow Test Timeout
Use `-s` flag to see output and increase timeout:
```bash
pytest --timeout=300 -s
```
