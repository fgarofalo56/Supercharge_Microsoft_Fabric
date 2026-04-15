"""Validate Fabric-compatible structure for all notebooks under notebooks/."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

NOTEBOOKS_ROOT = Path(__file__).resolve().parent.parent / "notebooks"
COMMAND_SEPARATOR = "# COMMAND ----------"


def collect_notebooks() -> list[Path]:
    return sorted(NOTEBOOKS_ROOT.rglob("*.py"))


def check_compiles(path: Path) -> str | None:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
        return None
    except SyntaxError as exc:
        return f"SyntaxError at line {exc.lineno}: {exc.msg}"


def check_dbutils(path: Path) -> str | None:
    source = path.read_text(encoding="utf-8")
    if "dbutils." in source:
        return "contains dbutils. reference (Fabric uses mssparkutils instead)"
    return None


def check_separators(path: Path) -> str | None:
    source = path.read_text(encoding="utf-8")
    if COMMAND_SEPARATOR not in source:
        return f"missing '{COMMAND_SEPARATOR}' cell separator"
    return None


def main() -> int:
    notebooks = collect_notebooks()
    if not notebooks:
        print(f"No notebooks found under {NOTEBOOKS_ROOT}")
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    passed = 0

    for nb in notebooks:
        rel = nb.relative_to(NOTEBOOKS_ROOT.parent)
        label = str(rel)

        syntax_err = check_compiles(nb)
        if syntax_err:
            errors.append(f"[FAIL] {label}: {syntax_err}")
            continue

        sep_err = check_separators(nb)
        if sep_err:
            errors.append(f"[FAIL] {label}: {sep_err}")
            continue

        dbutils_warn = check_dbutils(nb)
        if dbutils_warn:
            warnings.append(f"[WARN] {label}: {dbutils_warn}")

        passed += 1

    total = len(notebooks)
    failed = total - passed

    print(f"\nNotebook validation: {NOTEBOOKS_ROOT}")
    print(f"  Total : {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Warnings: {len(warnings)}")

    for w in warnings:
        print(w)
    for e in errors:
        print(e)

    if errors:
        print("\nValidation FAILED.")
        return 1

    print("\nValidation PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
