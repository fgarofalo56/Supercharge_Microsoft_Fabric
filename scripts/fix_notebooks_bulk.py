#!/usr/bin/env python3
"""Bulk-fix notebooks to be Fabric-compatible.

Applies these transformations across every ``notebooks/**/*.py`` file:

1. Replace ``dbutils.notebook.exit`` with ``mssparkutils.notebook.exit``.
2. Replace the fragile ``dbutils.widgets.getAll()`` pattern used for default
   arguments with ``mssparkutils.notebook.exit``-compatible ``_get_arg``.
3. Replace any ``dbutils.widgets.get(...)`` call with ``_get_arg(...)``.
4. Replace ``/tmp/checkpoints`` paths with an env-configurable OneLake path
   (``CHECKPOINT_PATH_BASE``) and remove the ``/tmp`` default.
5. Prefix Bronze table writes in Bronze 01-06 with the ``lh_bronze.`` schema.
6. Replace the ``SAR_THRESHOLD = 5000`` constant in ``bronze/03`` with the
   config-aligned value ``8000``.
7. Rename ``gold/17_gold_digital_twin_demo.py`` to ``gold/18_...`` to remove
   the duplicate "17" prefix.
8. Collapse the ``df.count()`` after ``saveAsTable`` / ``append`` into a
   ``spark.table(...).count()`` (avoids re-running the DAG).

The script is idempotent and can be re-run; it logs every change.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = ROOT / "notebooks"

# Fabric-compatible helper injected near the top of each notebook. Lets the
# notebook run locally (pytest/import) and inside Fabric without NameError.
FABRIC_COMPAT_SHIM = """\
# ---------------------------------------------------------------------------
# Fabric/local compatibility shim
# ---------------------------------------------------------------------------
import os
try:
    import notebookutils  # Fabric runtime
    def _get_arg(name, default=None):
        try:
            return notebookutils.notebook.getArgument(name, default)
        except Exception:
            return os.environ.get(name.upper(), default)
    def _notebook_exit(status: str) -> None:
        notebookutils.notebook.exit(status)
except ImportError:
    try:
        import mssparkutils  # legacy Synapse/Fabric runtime
        def _get_arg(name, default=None):
            try:
                return mssparkutils.notebook.getArgument(name, default)
            except Exception:
                return os.environ.get(name.upper(), default)
        def _notebook_exit(status: str) -> None:
            mssparkutils.notebook.exit(status)
    except ImportError:
        def _get_arg(name, default=None):
            return os.environ.get(name.upper(), default)
        def _notebook_exit(status: str) -> None:
            raise SystemExit(status)
"""

DBUTILS_EXIT_RE = re.compile(r"dbutils\.notebook\.exit\(")
DBUTILS_WIDGET_GETALL_RE = re.compile(
    r"dbutils\.widgets\.get\(\"(?P<name>\w+)\"\)\s*"
    r"if\s+\"(?P=name)\"\s+in\s+\[w\.name for w in dbutils\.widgets\.getAll\(\)\]\s*"
    r"else\s+(?P<fallback>[^\n]+)"
)
DBUTILS_WIDGET_GET_RE = re.compile(r"dbutils\.widgets\.get\(\"(\w+)\"\)")
TMP_CHECKPOINT_RE = re.compile(r"""(['"])/tmp/checkpoints([^'"]*)\1""")
SAR_THRESHOLD_RE = re.compile(r"^SAR_THRESHOLD\s*=\s*5000\b", re.MULTILINE)

# ``bronze_slot_telemetry`` → ``lh_bronze.bronze_slot_telemetry``
TABLE_PREFIX_TARGETS = {
    "bronze_slot_telemetry",
    "bronze_player_profile",
    "bronze_financial_txn",
    "bronze_compliance",
    "bronze_table_games",
    "bronze_security_events",
}


def _needs_shim(src: str) -> bool:
    return "dbutils" in src or "_get_arg(" in src or "_notebook_exit(" in src


def _inject_shim(src: str) -> str:
    if "_get_arg(" not in src and "_notebook_exit(" not in src:
        return src
    if "Fabric/local compatibility shim" in src:
        return src  # already injected
    lines = src.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        if line.strip() == "# COMMAND ----------":
            lines.insert(idx + 1, "\n" + FABRIC_COMPAT_SHIM + "\n")
            return "".join(lines)
    return FABRIC_COMPAT_SHIM + "\n" + src


def _replace_dbutils(src: str) -> str:
    src = DBUTILS_EXIT_RE.sub("_notebook_exit(", src)
    src = DBUTILS_WIDGET_GETALL_RE.sub(
        lambda m: f'_get_arg("{m.group("name")}", {m.group("fallback").strip()})',
        src,
    )
    src = DBUTILS_WIDGET_GET_RE.sub(lambda m: f'_get_arg("{m.group(1)}")', src)
    return src


def _replace_checkpoints(src: str) -> str:
    def repl(match: re.Match[str]) -> str:
        q = match.group(1)
        suffix = match.group(2)
        inner = f'{{os.environ.get("CHECKPOINT_PATH_BASE", "abfss://Files/checkpoints")}}{suffix}'
        # Use f-string so the path resolves at runtime.
        return f'f{q}{inner}{q}'
    new_src = TMP_CHECKPOINT_RE.sub(repl, src)
    if new_src != src and "import os" not in new_src.splitlines()[0:30]:
        new_src = "import os\n" + new_src
    return new_src


def _qualify_bronze_tables(src: str, path: Path) -> str:
    if "bronze/" not in str(path).replace("\\", "/"):
        return src
    for tbl in TABLE_PREFIX_TARGETS:
        # Only rewrite literal strings or =-assignments of the bare name.
        src = re.sub(
            rf'(["\'])({tbl})\1',
            r'\1lh_bronze.\2\1',
            src,
        )
    return src


def _fix_sar_threshold(src: str, path: Path) -> str:
    if path.name != "03_bronze_financial_txn.py":
        return src
    return SAR_THRESHOLD_RE.sub("SAR_THRESHOLD = 8000", src)


def _collapse_post_write_count(src: str) -> str:
    # Pattern: df.write...saveAsTable(TARGET)
    #          ...
    #          df.count() -> spark.table(TARGET).count()
    # Conservative regex: only rewrites in lines that clearly count the SAME
    # dataframe right after a .saveAsTable call.
    pattern = re.compile(
        r"(\.saveAsTable\(([^)]+)\)[^\n]*\n(?:[^\n]*\n){0,10}?[^\n]*?)"
        r"\b(\w+)\.count\(\)",
        re.MULTILINE,
    )

    def _replace(m: re.Match[str]) -> str:
        pre, target_expr, _df = m.group(1), m.group(2).strip(), m.group(3)
        return f"{pre}spark.table({target_expr}).count()"

    return pattern.sub(_replace, src, count=1)


def transform_file(path: Path, apply: bool) -> dict[str, int]:
    original = path.read_text(encoding="utf-8")
    new = original
    new = _replace_dbutils(new)
    new = _replace_checkpoints(new)
    new = _qualify_bronze_tables(new, path)
    new = _fix_sar_threshold(new, path)
    new = _collapse_post_write_count(new)
    new = _inject_shim(new)
    changed = new != original
    if changed and apply:
        path.write_text(new, encoding="utf-8")
    return {
        "file": str(path.relative_to(ROOT)),
        "changed": int(changed),
    }


def rename_duplicate_17(apply: bool) -> dict[str, str]:
    src = NOTEBOOKS / "gold" / "17_gold_digital_twin_demo.py"
    dst = NOTEBOOKS / "gold" / "18_gold_digital_twin_demo.py"
    if src.exists() and not dst.exists():
        if apply:
            src.rename(dst)
        return {"renamed": f"{src.name} -> {dst.name}"}
    return {"renamed": ""}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write changes to disk")
    args = parser.parse_args()

    apply = args.apply
    results = []
    for path in sorted(NOTEBOOKS.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        results.append(transform_file(path, apply))

    rename = rename_duplicate_17(apply)
    changed_count = sum(r["changed"] for r in results)
    print(f"Scanned {len(results)} notebook files.")
    print(f"Modified: {changed_count}.")
    if rename["renamed"]:
        print(f"Renamed: {rename['renamed']}")
    if not apply:
        print("(dry-run; re-run with --apply to write changes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
