"""GitHub Issues client — auto-file content-gap issues.

When the Copilot answers a Fabric/Azure question by falling back to
Microsoft Learn (because the repo doesn't cover it), we file a
`content-gap` issue with the question, the Learn URLs the Copilot
cited, and a short summary of what was answered. The repo maintainer
sees a real backlog of content the docs should add next.

Configuration via env vars (set in Azure Function App settings):
  GITHUB_TOKEN        — fine-scoped PAT with `issues: write` on this repo
  GITHUB_REPO         — "owner/repo"   (e.g. "fgarofalo56/Suppercharge_Microsoft_Fabric")
  GITHUB_ISSUE_LABEL  — comma-separated labels (default: "content-gap,copilot-suggested")

Silently no-ops when GITHUB_TOKEN is unset so dev / local runs don't error.
"""
from __future__ import annotations
import hashlib
import logging
import os
import re

import httpx

DEFAULT_LABELS = "content-gap,copilot-suggested"
HTTP_TIMEOUT = 15.0

# Tiny in-memory cache so we don't create duplicate issues from the same
# question repeated in a short window. Cleared on cold start.
_dedupe: set[str] = set()
_DEDUPE_MAX = 500


def _fingerprint(question: str) -> str:
    norm = re.sub(r"\s+", " ", question.lower().strip())[:200]
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def file_content_gap(question: str, learn_refs: list[dict], summary: str = "") -> str | None:
    """File a content-gap GitHub issue. Returns the issue URL or None."""
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO")
    if not token or not repo:
        logging.info("github_issue: skipped (token or repo not configured)")
        return None

    fp = _fingerprint(question)
    if fp in _dedupe:
        logging.info("github_issue: deduped (recent identical question)")
        return None
    if len(_dedupe) > _DEDUPE_MAX:
        _dedupe.clear()
    _dedupe.add(fp)

    labels = [l.strip() for l in os.environ.get("GITHUB_ISSUE_LABEL", DEFAULT_LABELS).split(",") if l.strip()]

    # Build the body
    cite_lines = []
    for r in learn_refs[:6]:
        title = r.get("title") or "Microsoft Learn"
        url = r.get("url") or r.get("source") or r.get("link") or ""
        if url:
            cite_lines.append(f"- [{title}]({url})")

    body = (
        f"**The Copilot answered a user question that isn't covered in the repo.**\n\n"
        f"### Question asked\n\n> {question.strip()[:1200]}\n\n"
        f"### Microsoft Learn citations the Copilot used\n\n"
        + ("\n".join(cite_lines) if cite_lines else "_(no citations captured)_")
        + "\n\n"
        f"### Copilot answer summary\n\n{summary.strip()[:1500] or '_(no summary captured)_'}\n\n"
        f"---\n"
        f"_Filed automatically by the documentation Copilot. "
        f"Close this issue once the topic is covered in the repo, or add it to a roadmap doc._"
    )

    short = re.sub(r"\s+", " ", question.strip())[:80]
    title = f"Copilot fallback: {short}{'…' if len(question) > 80 else ''}"

    api = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {"title": title, "body": body, "labels": labels}

    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            r = client.post(api, json=payload, headers=headers)
        if r.status_code in (200, 201):
            url = r.json().get("html_url")
            logging.info("github_issue: filed %s", url)
            return url
        logging.warning("github_issue: HTTP %s — %s", r.status_code, r.text[:200])
        return None
    except Exception as e:
        logging.warning("github_issue: failed — %s", e)
        return None
