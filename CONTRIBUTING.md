# 🤝 Contributing Guide

> **Last Updated:** 2026-04-15 | **Version:** 2.1.0 | **Status:** Active

<div align="center" markdown>

![Contributions](https://img.shields.io/badge/🤝_Contributions-Welcome-brightgreen?style=for-the-badge)
![License](https://img.shields.io/badge/📄_License-MIT-blue?style=for-the-badge)
![PRs](https://img.shields.io/badge/🔀_PRs-Open-orange?style=for-the-badge)

**Thank you for your interest in contributing to the Microsoft Fabric Casino/Gaming POC!**

We welcome contributions from data engineers, architects, and industry experts.

</div>

---

## 📑 Table of Contents

- [📜 Code of Conduct](#-code-of-conduct)
- [🚀 How to Contribute](#-how-to-contribute)
- [🛠️ Development Setup](#️-development-setup)
- [🧪 Running Tests](#-running-tests)
- [🎨 Code Style](#-code-style)
- [📝 Commit Messages](#-commit-messages)
- [📁 Project Structure](#-project-structure)
- [🔀 Pull Request Process](#-pull-request-process)
- [👀 Review Process](#-review-process)
- [❓ Getting Help](#-getting-help)
- [🏆 Recognition](#-recognition)
- [📄 License](#-license)

---

## 📜 Code of Conduct

This project follows the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/). By participating, you agree to abide by its terms.

| Expectation | Description |
|-------------|-------------|
| Be Respectful | Treat all contributors with respect |
| Be Inclusive | Welcome diverse perspectives |
| Be Constructive | Provide helpful feedback |
| Be Professional | Maintain professional standards |

---

## 🚀 How to Contribute

### Reporting Issues

1. **Check existing issues** to avoid duplicates
2. **Use the issue template** when available
3. **Include**:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, Fabric capacity)

```markdown
## Issue Template

**Description:**
[Clear description of the issue]

**Steps to Reproduce:**
1. Step one
2. Step two
3. Step three

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Environment:**
- OS: [e.g., Windows 11, macOS 14]
- Python: [e.g., 3.11.5]
- Fabric Capacity: [e.g., F64]
```

### Suggesting Enhancements

1. Open an issue with the **"Enhancement"** label
2. Describe the **use case** clearly
3. Explain the **proposed solution**
4. Consider **alternatives** and trade-offs

### Pull Requests

```
1. Fork           --> 2. Branch        --> 3. Develop       --> 4. Test
   Repository         from main            your changes         locally

5. Document       --> 6. Submit PR     --> 7. Address       --> 8. Merge
   changes             with template        feedback             (maintainer)
```

---

## 🛠️ Development Setup

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.10+ | Runtime |
| Git | 2.40+ | Version control |
| Azure CLI | 2.50+ | Azure deployment |
| pip | 23.0+ | Package management |

### Environment Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Suppercharge_Microsoft_Fabric.git
cd Suppercharge_Microsoft_Fabric

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\Activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Verify Setup

```bash
# Run tests to verify
pytest validation/unit_tests/ -v

# Check code formatting
ruff format --check .

# Run linter
ruff check .
```

---

## 🧪 Running Tests

### Unit Tests

```bash
# Run all unit tests
pytest validation/unit_tests/ -v

# Run with coverage
pytest validation/unit_tests/ --cov=data_generation --cov-report=html

# Run specific test file
pytest validation/unit_tests/test_generators.py -v
```

### Integration Tests

```bash
# Run all integration tests (includes slow tests)
pytest validation/integration_tests/ -v --slow

# Skip slow tests
pytest validation/integration_tests/ -v --skip-slow
```

### Data Quality Tests

```bash
# Run Great Expectations checkpoints
great_expectations checkpoint run all_checkpoints
```

---

## 🎨 Code Style

We maintain consistent code quality using these tools:

| Tool | Purpose | Config File |
|------|---------|-------------|
| **Black** | Python formatting | `pyproject.toml` |
| **Ruff** | Linting | `pyproject.toml` |
| **MyPy** | Type checking | `pyproject.toml` |
| **isort** | Import sorting | `pyproject.toml` |

### Running Code Quality Tools

```bash
# Format code with Black
black .

# Lint with Ruff
ruff check .

# Auto-fix linting issues
ruff check . --fix

# Type check with MyPy
mypy data_generation/
```

### Style Guidelines

| Guideline | Example |
|-----------|---------|
| Use type hints | `def process(data: pd.DataFrame) -> pd.DataFrame:` |
| Docstrings | Google style docstrings |
| Line length | 88 characters (Black default) |
| Imports | Sorted by isort |

---

## 📝 Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
type(scope): description

[optional body]

[optional footer]
```

### Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(generators): add compliance data generator` |
| `fix` | Bug fix | `fix(bronze): resolve schema mismatch in slot telemetry` |
| `docs` | Documentation | `docs(tutorials): update Day 2 agenda` |
| `style` | Formatting | `style: apply black formatting` |
| `refactor` | Code restructuring | `refactor(silver): simplify deduplication logic` |
| `test` | Tests | `test(generators): add edge case tests for CTR` |
| `chore` | Maintenance | `chore: update dependencies` |

### Examples

```bash
# Feature
git commit -m "feat(generators): add compliance data generator

Adds a new generator for CTR, SAR, and W-2G compliance data
with realistic patterns and configurable thresholds."

# Bug fix
git commit -m "fix(bronze): resolve schema mismatch in slot telemetry

The machine_id column was incorrectly typed as integer instead of string.
This caused issues during joins with the asset master table."

# Documentation
git commit -m "docs(tutorials): update Day 2 agenda

Added new section on Gold layer aggregations and updated
time estimates based on POC feedback."
```

---

## 📁 Project Structure

```
Suppercharge_Microsoft_Fabric/
|-- infra/                     # Infrastructure as Code (Bicep)
|   |-- main.bicep             # Root orchestration
|   |-- modules/               # Reusable modules
|   +-- environments/          # Environment-specific parameters
|
|-- docs/                      # Documentation
|   |-- architecture.md        # Detailed architecture
|   |-- deployment.md          # Deployment guide
|   +-- security.md            # Security & compliance
|
|-- tutorials/                 # Step-by-step tutorials
|   |-- 00-environment-setup/
|   |-- 01-bronze-layer/
|   +-- ...
|
|-- poc-agenda/                # 3-Day POC workshop materials
|-- data_generation/           # Sample data generators
|-- notebooks/                 # Fabric-importable notebooks
|-- validation/                # Tests & data quality
```

---

## 🔀 Pull Request Process

### Before Submitting

- [ ] Tests pass locally (`pytest validation/`)
- [ ] Code follows style guidelines (`black .` && `ruff check .`)
- [ ] Documentation updated (if applicable)
- [ ] No secrets or credentials in code
- [ ] Commit messages follow conventional commit format

### Branch Naming

| Pattern | Use Case | Example |
|---------|----------|---------|
| `feature/description` | New features | `feature/add-compliance-generator` |
| `fix/description` | Bug fixes | `fix/bronze-schema-mismatch` |
| `docs/description` | Documentation | `docs/update-day2-tutorial` |
| `refactor/description` | Code improvements | `refactor/simplify-silver-transforms` |

### PR Template

```markdown
## Summary

[Brief description of changes]

## Changes

- [Change 1]
- [Change 2]
- [Change 3]

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that causes existing functionality to change)
- [ ] Documentation update

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass locally

## Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Documentation updated
- [ ] No secrets or credentials committed
```

---

## 👀 Review Process

```
+------------------+     +------------------+     +------------------+
|   Submit PR      | --> |   Auto Checks    | --> |   Code Review    |
+------------------+     +------------------+     +------------------+
                         | - Tests pass     |     | - Maintainer     |
                         | - Lint clean     |     |   review         |
                         | - No conflicts   |     | - Feedback       |
                         +------------------+     +------------------+
                                                          |
                                                          v
                         +------------------+     +------------------+
                         |   Approved       | <-- |   Address        |
                         |   & Merged       |     |   Feedback       |
                         +------------------+     +------------------+
```

### Review Criteria

| Criterion | Description |
|-----------|-------------|
| Functionality | Does the code work as intended? |
| Tests | Are there adequate tests? |
| Documentation | Is the documentation updated? |
| Code Quality | Does it follow style guidelines? |
| Security | Are there any security concerns? |

---

## ❓ Getting Help

| Channel | Purpose |
|---------|---------|
| GitHub Issues | Bug reports, feature requests |
| Discussions | Questions, ideas, community |
| Pull Requests | Code contributions |

> **Tip:** Tag maintainers for urgent items or if you need guidance on an approach.

---

## 🏆 Recognition

Contributors are recognized in:

| Location | Description |
|----------|-------------|
| README | Acknowledgments section |
| Release Notes | Contributors for each release |
| Contributors File | Full list of contributors |

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

<div align="center" markdown>

**Thank you for contributing!**

Your contributions help make this project better for everyone.

[⬆️ Back to Top](#-contributing-guide) | [📚 Docs](docs/index.md) | [🏠 Main README](README.md)

</div>
