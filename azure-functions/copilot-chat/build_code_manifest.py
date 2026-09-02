"""Build the code-metadata manifest used by the Copilot backend for grounding.

Scans the repo for:
  - notebooks/**/*.py        — Fabric-importable notebooks (MAGIC %md headers parsed)
  - data_generation/**/*.py  — generator classes (class names + docstrings)
  - infra/**/*.bicep         — Bicep modules (description decorators + resource names)

Output: code_manifest.json (written next to this script by default), a flat
list of entries:
  {
    "type": "notebook" | "generator" | "bicep",
    "path": "notebooks/bronze/01_bronze_slot_telemetry.py",
    "title": "Bronze Layer: Slot Machine Telemetry",
    "summary": "first ~400 chars of the docstring / MAGIC header / descriptions",
    "keywords": ["bronze", "slot", "telemetry", ...]
  }

Run from the repo root:
    python azure-functions/copilot-chat/build_code_manifest.py

The Copilot backend loads this manifest at cold start (see repo_grounding.py)
so questions like "which notebook handles NOAA bronze ingestion" resolve to
an exact file path instead of a guess.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_PATH = Path(__file__).resolve().parent / "code_manifest.json"

MAX_SUMMARY = 400


def _keywords(text: str) -> list[str]:
    """Cheap keyword extraction: lowercase alphanumeric tokens >= 4 chars,
    stopwords removed, de-duplicated, order preserved."""
    stop = {
        "this",
        "that",
        "with",
        "from",
        "into",
        "the",
        "and",
        "for",
        "are",
        "was",
        "were",
        "have",
        "has",
        "using",
        "used",
        "use",
        "notebook",
        "module",
        "file",
        "data",
        "layer",
        "table",
    }
    seen: dict[str, None] = {}
    for tok in re.findall(r"[a-z0-9_]{4,}", text.lower()):
        if tok not in stop and tok not in seen:
            seen[tok] = None
    return list(seen)[:20]


def _notebook_entry(path: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    # Title: first "# MAGIC # ..." heading
    m = re.search(r"^# MAGIC #\s+(.+)$", text, re.MULTILINE)
    title = m.group(1).strip() if m else path.stem.replace("_", " ")
    # Summary: the MAGIC %md block lines following the title
    magic_lines = [
        re.sub(r"^# MAGIC ?", "", line)
        for line in text.splitlines()
        if line.startswith("# MAGIC")
    ]
    body = "\n".join(magic_lines)
    body = re.sub(r"%md", "", body)
    body = re.sub(r"[#*\-`]+", "", body)
    body = re.sub(r"\s+", " ", body).strip()
    summary = body[:MAX_SUMMARY]
    return {
        "type": "notebook",
        "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "title": title,
        "summary": summary,
        "keywords": _keywords(f"{title} {summary} {path.stem}"),
    }


def _generator_entry(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    entries = []
    for m in re.finditer(
        r'class\s+(\w+\(?(?:BaseGenerator)?\)?)\s*[^:]*:\s*\n\s+"""(.+?)"""',
        text,
        re.DOTALL,
    ):
        class_name = m.group(1).split("(")[0]
        doc = re.sub(r"\s+", " ", m.group(2)).strip()[:MAX_SUMMARY]
        entries.append(
            {
                "type": "generator",
                "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "title": class_name,
                "summary": doc,
                "keywords": _keywords(f"{class_name} {doc} {path.stem}"),
            }
        )
    if not entries and path.name != "__init__.py":
        # Module without a documented class — still index the module itself.
        mod_doc = re.search(r'^"""(.+?)"""', text, re.DOTALL)
        doc = (
            re.sub(r"\s+", " ", mod_doc.group(1)).strip()[:MAX_SUMMARY]
            if mod_doc
            else ""
        )
        entries.append(
            {
                "type": "generator",
                "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "title": path.stem.replace("_", " "),
                "summary": doc,
                "keywords": _keywords(f"{path.stem} {doc}"),
            }
        )
    return entries


def _bicep_entry(path: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    descriptions = re.findall(r"@description\('([^']+)'\)", text)
    resources = re.findall(r"resource\s+(\w+)\s+'([^']+)'", text)
    title = path.stem.replace("-", " ").replace("_", " ")
    parts = descriptions[:6] + [f"{name} ({rtype})" for name, rtype in resources[:6]]
    summary = re.sub(r"\s+", " ", " ".join(parts)).strip()[:MAX_SUMMARY]
    return {
        "type": "bicep",
        "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "title": title,
        "summary": summary,
        "keywords": _keywords(f"{title} {summary} {path.stem}"),
    }


def build_manifest() -> list[dict]:
    entries: list[dict] = []

    for nb in sorted(REPO_ROOT.glob("notebooks/**/*.py")):
        entry = _notebook_entry(nb)
        if entry:
            entries.append(entry)

    for gen in sorted(REPO_ROOT.glob("data_generation/**/*.py")):
        if "__pycache__" in gen.parts or gen.name == "__init__.py":
            continue
        entries.extend(_generator_entry(gen))

    for bicep in sorted(REPO_ROOT.glob("infra/**/*.bicep")):
        entry = _bicep_entry(bicep)
        if entry:
            entries.append(entry)

    return entries


def main() -> int:
    entries = build_manifest()
    OUT_PATH.write_text(
        json.dumps({"version": 1, "entries": entries}, indent=2),
        encoding="utf-8",
    )
    by_type: dict[str, int] = {}
    for e in entries:
        by_type[e["type"]] = by_type.get(e["type"], 0) + 1
    print(f"Wrote {len(entries)} entries to {OUT_PATH}")
    for t, n in sorted(by_type.items()):
        print(f"  {t}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
