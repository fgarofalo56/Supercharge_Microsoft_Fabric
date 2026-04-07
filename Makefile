# Supercharge Microsoft Fabric - Development Makefile
# ===================================================

.PHONY: help test test-casino test-federal test-streaming test-analytics \
        lint format typecheck security-scan validate-schemas generate-sample clean

PYTHON ?= python
PYTEST ?= $(PYTHON) -m pytest
PYTEST_OPTS ?= -v --tb=short

# Default target
help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==========================================================================
# Testing
# ==========================================================================

test: ## Run all unit tests
	$(PYTEST) validation/unit_tests/ $(PYTEST_OPTS)

test-casino: ## Run casino/gaming generator tests
	$(PYTEST) validation/unit_tests/test_generators.py $(PYTEST_OPTS)

test-federal: ## Run federal agency generator tests
	$(PYTEST) validation/unit_tests/federal/ $(PYTEST_OPTS)

test-streaming: ## Run streaming simulator tests
	$(PYTEST) validation/unit_tests/streaming/ $(PYTEST_OPTS)

test-analytics: ## Run analytics generator tests
	$(PYTEST) validation/unit_tests/analytics/ $(PYTEST_OPTS)

test-geo: ## Run geolocation module tests
	$(PYTEST) validation/unit_tests/geo/ $(PYTEST_OPTS)

test-cov: ## Run tests with coverage report
	$(PYTEST) validation/unit_tests/ --cov=data_generation/generators --cov-report=term-missing $(PYTEST_OPTS)

test-compliance: ## Run compliance-specific tests
	$(PYTEST) validation/unit_tests/ -m compliance $(PYTEST_OPTS)

# ==========================================================================
# Code Quality
# ==========================================================================

lint: ## Check code style with ruff
	$(PYTHON) -m ruff check data_generation/ validation/
	$(PYTHON) -m ruff format --check data_generation/ validation/

format: ## Auto-format code with ruff
	$(PYTHON) -m ruff check --fix data_generation/ validation/
	$(PYTHON) -m ruff format data_generation/ validation/

typecheck: ## Run mypy type checking
	$(PYTHON) -m mypy data_generation/generators/ --ignore-missing-imports

security-scan: ## Run bandit security scan
	$(PYTHON) -m bandit -r data_generation/generators/ -c bandit.yml
	$(PYTHON) -m pip_audit

# ==========================================================================
# Validation
# ==========================================================================

validate-schemas: ## Validate all JSON schemas
	$(PYTHON) -c "\
	import json, glob; \
	schemas = glob.glob('data_generation/schemas/**/*.json', recursive=True); \
	[json.load(open(s)) for s in schemas]; \
	print(f'Validated {len(schemas)} schemas successfully')"

validate-notebooks: ## Compile-check all notebooks
	$(PYTHON) -c "\
	import py_compile, glob; \
	nbs = glob.glob('notebooks/**/*.py', recursive=True); \
	[py_compile.compile(n, doraise=True) for n in nbs]; \
	print(f'Compiled {len(nbs)} notebooks successfully')"

validate-generators: ## Compile-check all generators
	$(PYTHON) -c "\
	import py_compile, glob; \
	gens = glob.glob('data_generation/generators/**/*.py', recursive=True); \
	[py_compile.compile(g, doraise=True) for g in gens]; \
	print(f'Compiled {len(gens)} generators successfully')"

validate-all: validate-schemas validate-notebooks validate-generators ## Run all validation checks

# ==========================================================================
# Data Generation
# ==========================================================================

generate-sample: ## Generate sample data (1000 records)
	cd data_generation && $(PYTHON) generate.py --records 1000 --format parquet --output temp/sample

# ==========================================================================
# Infrastructure
# ==========================================================================

validate-bicep: ## Validate Bicep templates
	az bicep build --file infra/main.bicep

# ==========================================================================
# Cleanup
# ==========================================================================

clean: ## Remove generated artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf temp/ htmlcov/ .coverage
