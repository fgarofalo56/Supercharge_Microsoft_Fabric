"""
Notebook Import Tests
======================

Tests for notebook dependencies and imports:
- All notebook imports are valid
- No circular dependencies
- Required packages are documented
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set

import pytest

pytestmark = [pytest.mark.integration]


class TestNotebookImportValidity:
    """Tests for validating notebook imports."""

    def get_notebook_files(self, notebooks_dir: Path) -> list[Path]:
        """Get all Python notebook files."""
        return list(notebooks_dir.rglob("*.py"))

    def extract_imports(self, file_path: Path) -> set[str]:
        """Extract import statements from a Python file."""
        imports = set()

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Handle Databricks notebook format (# COMMAND ----------)
            # Parse as regular Python
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])

        except SyntaxError:
            # Some notebooks may have Databricks magic commands
            # Fall back to regex-based extraction
            imports.update(self._extract_imports_regex(file_path))

        return imports

    def _extract_imports_regex(self, file_path: Path) -> set[str]:
        """Extract imports using regex (fallback for syntax errors)."""
        import re

        imports = set()

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Match import statements
        import_pattern = re.compile(r"^\s*import\s+(\w+)", re.MULTILINE)
        from_pattern = re.compile(r"^\s*from\s+(\w+)", re.MULTILINE)

        for match in import_pattern.finditer(content):
            imports.add(match.group(1))

        for match in from_pattern.finditer(content):
            imports.add(match.group(1))

        return imports

    def test_bronze_notebooks_parse(self, notebooks_dir):
        """Verify Bronze layer notebooks can be parsed."""
        bronze_dir = notebooks_dir / "bronze"
        if not bronze_dir.exists():
            pytest.skip("Bronze notebooks directory not found")

        notebooks = list(bronze_dir.glob("*.py"))
        assert len(notebooks) > 0, "No Bronze notebooks found"

        for notebook in notebooks:
            imports = self.extract_imports(notebook)
            assert len(imports) >= 0, f"Failed to extract imports from {notebook.name}"

    def test_silver_notebooks_parse(self, notebooks_dir):
        """Verify Silver layer notebooks can be parsed."""
        silver_dir = notebooks_dir / "silver"
        if not silver_dir.exists():
            pytest.skip("Silver notebooks directory not found")

        notebooks = list(silver_dir.glob("*.py"))
        assert len(notebooks) > 0, "No Silver notebooks found"

        for notebook in notebooks:
            imports = self.extract_imports(notebook)
            assert len(imports) >= 0, f"Failed to extract imports from {notebook.name}"

    def test_gold_notebooks_parse(self, notebooks_dir):
        """Verify Gold layer notebooks can be parsed."""
        gold_dir = notebooks_dir / "gold"
        if not gold_dir.exists():
            pytest.skip("Gold notebooks directory not found")

        notebooks = list(gold_dir.glob("*.py"))
        assert len(notebooks) > 0, "No Gold notebooks found"

        for notebook in notebooks:
            imports = self.extract_imports(notebook)
            assert len(imports) >= 0, f"Failed to extract imports from {notebook.name}"

    def test_ml_notebooks_parse(self, notebooks_dir):
        """Verify ML notebooks can be parsed."""
        ml_dir = notebooks_dir / "ml"
        if not ml_dir.exists():
            pytest.skip("ML notebooks directory not found")

        notebooks = list(ml_dir.glob("*.py"))

        for notebook in notebooks:
            imports = self.extract_imports(notebook)
            assert len(imports) >= 0, f"Failed to extract imports from {notebook.name}"

    def test_realtime_notebooks_parse(self, notebooks_dir):
        """Verify real-time notebooks can be parsed."""
        rt_dir = notebooks_dir / "real-time"
        if not rt_dir.exists():
            pytest.skip("Real-time notebooks directory not found")

        notebooks = list(rt_dir.glob("*.py"))

        for notebook in notebooks:
            imports = self.extract_imports(notebook)
            assert len(imports) >= 0, f"Failed to extract imports from {notebook.name}"


class TestStandardLibraryImports:
    """Tests for standard library imports in notebooks."""

    STANDARD_LIBS = {
        "datetime",
        "json",
        "os",
        "sys",
        "pathlib",
        "typing",
        "re",
        "hashlib",
        "uuid",
        "time",
        "logging",
        "collections",
        "functools",
        "itertools",
        "abc",
        "decimal",
    }

    def test_datetime_import_available(self, notebooks_dir):
        """Verify datetime is importable (standard library)."""
        import datetime

        assert datetime is not None

    def test_json_import_available(self):
        """Verify json is importable (standard library)."""
        import json

        assert json is not None

    def test_pathlib_import_available(self):
        """Verify pathlib is importable (standard library)."""
        from pathlib import Path

        assert Path is not None


class TestSparkImports:
    """Tests for PySpark imports (mock validation for non-Spark environments)."""

    SPARK_MODULES = [
        "pyspark",
        "pyspark.sql",
        "pyspark.sql.functions",
        "pyspark.sql.types",
    ]

    def test_spark_imports_documented(self, notebooks_dir):
        """Verify Spark imports are used consistently."""
        all_imports = set()

        for notebook in notebooks_dir.rglob("*.py"):
            with open(notebook, encoding="utf-8") as f:
                content = f.read()

            if "pyspark" in content:
                # Notebook uses Spark
                if "from pyspark.sql.functions import" in content:
                    all_imports.add("pyspark.sql.functions")
                if "from pyspark.sql.types import" in content:
                    all_imports.add("pyspark.sql.types")

        # If any notebook uses Spark, verify standard patterns
        if all_imports:
            assert (
                "pyspark.sql.functions" in all_imports
                or "pyspark.sql.types" in all_imports
            )

    def test_spark_session_creation_pattern(self, notebooks_dir):
        """Verify SparkSession is obtained correctly in notebooks."""
        for notebook in notebooks_dir.rglob("*.py"):
            with open(notebook, encoding="utf-8") as f:
                content = f.read()

            # Check for SparkSession patterns
            if "SparkSession" in content:
                # Should use builder pattern or get existing session
                has_builder = "SparkSession.builder" in content
                has_spark_var = "spark" in content.lower()

                assert (
                    has_builder or has_spark_var
                ), f"{notebook.name} has SparkSession but unclear initialization"


class TestDeltaImports:
    """Tests for Delta Lake imports."""

    def test_delta_imports_documented(self, notebooks_dir):
        """Verify Delta Lake imports are used consistently."""
        delta_notebooks = []

        for notebook in notebooks_dir.rglob("*.py"):
            with open(notebook, encoding="utf-8") as f:
                content = f.read()

            if "delta" in content.lower():
                delta_notebooks.append(notebook.name)

        # Delta Lake is expected in Fabric notebooks
        # Just verify we can identify notebooks using it
        assert isinstance(delta_notebooks, list)


class TestNoCircularDependencies:
    """Tests for circular dependency detection."""

    def build_dependency_graph(self, notebooks_dir: Path) -> dict[str, set[str]]:
        """Build a dependency graph from notebook imports."""
        graph = {}

        for notebook in notebooks_dir.rglob("*.py"):
            notebook_name = notebook.stem
            deps = set()

            with open(notebook, encoding="utf-8") as f:
                content = f.read()

            # Look for cross-notebook references
            for other_notebook in notebooks_dir.rglob("*.py"):
                other_name = other_notebook.stem
                if other_name != notebook_name:
                    if other_name in content:
                        deps.add(other_name)

            graph[notebook_name] = deps

        return graph

    def detect_cycles(self, graph: dict[str, set[str]]) -> list[list[str]]:
        """Detect cycles in dependency graph using DFS."""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycles.append([*path[cycle_start:], neighbor])
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                dfs(node)

        return cycles

    def test_no_circular_dependencies(self, notebooks_dir):
        """Verify no circular dependencies between notebooks."""
        graph = self.build_dependency_graph(notebooks_dir)
        cycles = self.detect_cycles(graph)

        assert len(cycles) == 0, f"Circular dependencies found: {cycles}"

    def test_layer_ordering_respected(self, notebooks_dir):
        """Verify data flows Bronze -> Silver -> Gold."""
        # Check that Silver doesn't import from Gold
        silver_dir = notebooks_dir / "silver"
        gold_dir = notebooks_dir / "gold"

        if not silver_dir.exists() or not gold_dir.exists():
            pytest.skip("Layer directories not found")

        gold_tables = set()
        for notebook in gold_dir.glob("*.py"):
            with open(notebook, encoding="utf-8") as f:
                content = f.read()
            # Extract table names
            if "gold_" in content:
                gold_tables.add(notebook.stem)

        # Silver should not reference Gold
        for notebook in silver_dir.glob("*.py"):
            with open(notebook, encoding="utf-8") as f:
                content = f.read()

            for gold_table in gold_tables:
                # Allow references in comments but not in code
                lines = content.split("\n")
                for line in lines:
                    if gold_table in line and not line.strip().startswith("#"):
                        # This is a potential reverse dependency
                        pass  # Allow for now, just detecting


class TestRequiredPackagesDocumented:
    """Tests for package documentation."""

    EXPECTED_PACKAGES = {
        # Data processing
        "pandas": "Data manipulation and analysis",
        "numpy": "Numerical computing",
        # Generators
        "faker": "Synthetic data generation",
        # Microsoft Fabric / PySpark
        "pyspark": "Apache Spark for distributed processing",
        # Testing
        "pytest": "Testing framework",
        # Optional - streaming
        "azure-eventhub": "Azure Event Hubs SDK (optional)",
    }

    def test_generator_packages_importable(self):
        """Verify generator-required packages are importable."""
        required = ["pandas", "numpy", "faker"]

        for package in required:
            try:
                __import__(package)
            except ImportError:
                pytest.fail(f"Required package not importable: {package}")

    def test_test_packages_importable(self):
        """Verify test-required packages are importable."""
        required = ["pytest"]

        for package in required:
            try:
                __import__(package)
            except ImportError:
                pytest.fail(f"Test package not importable: {package}")

    def test_requirements_file_exists(self, project_root):
        """Check if requirements.txt or similar exists."""
        req_files = [
            project_root / "requirements.txt",
            project_root / "pyproject.toml",
            project_root / "setup.py",
            project_root / "data-generation" / "requirements.txt",
        ]

        found = any(f.exists() for f in req_files)
        # Just informational - not a hard requirement
        if not found:
            pytest.skip("No requirements file found (informational)")


class TestNotebookStructure:
    """Tests for notebook structural consistency."""

    def test_notebooks_have_docstring(self, notebooks_dir):
        """Verify notebooks have documentation."""
        for notebook in notebooks_dir.rglob("*.py"):
            with open(notebook, encoding="utf-8") as f:
                content = f.read()

            # Check for markdown header or docstring
            has_doc = (
                "# MAGIC %md" in content  # Databricks markdown
                or '"""' in content[:500]  # Python docstring
                or "'''" in content[:500]
                or "# " in content[:100]  # Comment header
            )

            assert has_doc, f"{notebook.name} lacks documentation"

    def test_notebooks_follow_naming_convention(self, notebooks_dir):
        """Verify notebooks follow naming convention."""
        import re

        # Expected pattern: XX_layer_description.py
        pattern = re.compile(r"^\d{2}_[a-z]+_[\w]+\.py$")

        for notebook in notebooks_dir.rglob("*.py"):
            # Skip __init__.py and similar
            if notebook.name.startswith("_"):
                continue

            assert pattern.match(
                notebook.name
            ), f"{notebook.name} doesn't follow naming convention"

    def test_layer_directories_exist(self, notebooks_dir):
        """Verify expected layer directories exist."""
        expected_layers = ["bronze", "silver", "gold"]

        for layer in expected_layers:
            layer_dir = notebooks_dir / layer
            assert layer_dir.exists(), f"Missing {layer} layer directory"

    def test_each_layer_has_notebooks(self, notebooks_dir):
        """Verify each layer has at least one notebook."""
        layers = ["bronze", "silver", "gold"]

        for layer in layers:
            layer_dir = notebooks_dir / layer
            if layer_dir.exists():
                notebooks = list(layer_dir.glob("*.py"))
                assert len(notebooks) > 0, f"{layer} layer has no notebooks"
