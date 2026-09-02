"""Feedback pipeline — thumbs up/down storage + GitHub escalation.

Every feedback event (👍 / 👎, optional comment) is written to Azure Table
Storage so maintainers can analyse satisfaction trends. A thumbs-down
*with a comment* additionally files a GitHub issue so it lands in the
actionable backlog — mirroring the csa-inabox pattern (Cosmos + forward)
but on the cheapest durable store available to a Function App.

Configuration (env vars):
  FEEDBACK_TABLE_CONNECTION — Azure Storage connection string. When unset,
      falls back to AzureWebJobsStorage (always present in a Function App).
      When both are unset (bare local dev), feedback is logged only.
  FEEDBACK_TABLE_NAME       — table name (default: "copilotfeedback")
  GITHUB_TOKEN / GITHUB_REPO — reused from github_issue.py for escalation
  GITHUB_FEEDBACK_LABEL     — labels for feedback issues
      (default: "copilot-feedback,triage")

Abuse control: the /feedback route in function_app.py rate-limits per IP
before calling this module; this module additionally dedupes identical
(rating, message, comment) triples per session so a double-click can't
double-file an issue.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import time
import uuid

import httpx

DEFAULT_FEEDBACK_LABELS = "copilot-feedback,triage"
HTTP_TIMEOUT = 15.0
TABLE_NAME = os.environ.get("FEEDBACK_TABLE_NAME", "copilotfeedback")

# In-memory dedupe: (session, fingerprint) pairs seen this instance lifetime.
_dedupe: set[str] = set()
_DEDUPE_MAX = 1000


# ── PII redaction ────────────────────────────────────────────────
# Feedback text (question, answer excerpt, comment) is user-supplied and
# may contain PII even though the Copilot never asks for it. We redact
# the common patterns *before* anything is written to Table Storage or
# GitHub so neither store ever holds raw PII. This is defence-in-depth —
# the frontend already truncates, but the backend is the trust boundary.
_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Email addresses
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[email]"),
    # US SSN (###-##-#### or #########)
    (re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"), "[ssn]"),
    # Credit/debit card numbers (13–19 digits, optional separators)
    (re.compile(r"\b(?:\d[ -]?){13,19}\b"), "[card]"),
    # Phone numbers (US-ish, with optional country code / separators)
    (re.compile(r"\b(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}\b"), "[phone]"),
    # IPv4 addresses
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[ip]"),
]


def redact_pii(text: str) -> str:
    """Return ``text`` with common PII patterns replaced by placeholders.

    Applied to every user-supplied field before storage or escalation.
    Not a guarantee — a determined user can always phrase PII to dodge a
    regex — but it removes the accidental cases (paste-an-error-with-an-
    email-in-it) that make up the real risk.
    """
    if not text:
        return text
    out = text
    for pattern, placeholder in _PII_PATTERNS:
        out = pattern.sub(placeholder, out)
    return out


def _hash_session(session_id: str) -> str:
    """Hash the session ID so stored rows can't be tied back to a browser
    session token. Correlation within feedback analysis still works (same
    session → same hash) but the raw token is never persisted."""
    if not session_id:
        return ""
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:32]


def _fingerprint(*parts: str) -> str:
    norm = "|".join(re.sub(r"\s+", " ", p.lower().strip())[:300] for p in parts)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def _connection_string() -> str | None:
    # Azure Functions sets the mixed-case 'AzureWebJobsStorage' — the
    # SIM112 suggestion (all-caps) would never match the real variable.
    return os.environ.get("FEEDBACK_TABLE_CONNECTION") or os.environ.get(
        "AzureWebJobsStorage"  # noqa: SIM112
    )


def _store_table(entity: dict) -> bool:
    """Write one entity to Azure Table Storage via the REST API.

    Uses the connection-string account key to sign requests — no extra
    SDK dependency (azure-data-tables would work too, but the REST call
    keeps requirements.txt at three packages). Returns True on success.
    """
    conn = _connection_string()
    if not conn:
        logging.info("feedback: no storage connection — logged only")
        return False
    if conn.startswith("UseDevelopmentStorage"):
        logging.info("feedback: dev storage — logged only")
        return False

    parts = dict(kv.split("=", 1) for kv in conn.split(";") if "=" in kv)
    account = parts.get("AccountName")
    key = parts.get("AccountKey")
    suffix = parts.get("TableEndpointSuffix", "core.windows.net")
    if not account or not key:
        logging.warning("feedback: connection string missing AccountName/AccountKey")
        return False

    import base64
    import hmac
    from datetime import datetime, timezone

    url = f"https://{account}.table.{suffix}/{TABLE_NAME}"
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    string_to_sign = f"{now}\n/{account}/{TABLE_NAME}"
    signature = base64.b64encode(
        hmac.new(
            base64.b64decode(key),
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    ).decode("utf-8")

    headers = {
        "Authorization": f"SharedKeyLite {account}:{signature}",
        "x-ms-date": now,
        "x-ms-version": "2019-02-02",
        "Accept": "application/json;odata=nometadata",
        "Content-Type": "application/json",
    }

    # Table Storage requires typed payloads for non-string fields; keep
    # everything a string/int for simplicity.
    payload = {
        "PartitionKey": entity["PartitionKey"],
        "RowKey": entity["RowKey"],
        "Rating": entity["rating"],
        "Comment": entity.get("comment", "")[:2000],
        "UserMessage": entity.get("user_message", "")[:1000],
        "AssistantReply": entity.get("assistant_reply", "")[:1000],
        "PagePath": entity.get("page_path", "")[:300],
        "SessionId": entity.get("session_id", "")[:64],
        "CreatedUtc": entity["created_utc"],
    }

    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            # Ensure table exists (204/409 both fine), then insert.
            client.post(
                f"https://{account}.table.{suffix}/Tables",
                json={"TableName": TABLE_NAME},
                headers={
                    **headers,
                    "Authorization": f"SharedKeyLite {account}:"
                    + base64.b64encode(
                        hmac.new(
                            base64.b64decode(key),
                            f"{now}\n/{account}/Tables".encode(),
                            hashlib.sha256,
                        ).digest()
                    ).decode("utf-8"),
                },
            )
            r = client.post(url, json=payload, headers=headers)
        if r.status_code in (200, 201, 204):
            return True
        logging.warning(
            "feedback: table insert HTTP %s — %s", r.status_code, r.text[:200]
        )
        return False
    except Exception as e:
        logging.warning("feedback: table insert failed — %s", e)
        return False


def _file_feedback_issue(
    rating: str, comment: str, user_message: str, assistant_reply: str, page_path: str
) -> str | None:
    """Escalate a thumbs-down-with-comment to a GitHub issue."""
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO")
    if not token or not repo:
        return None

    labels = [
        lbl.strip()
        for lbl in os.environ.get(
            "GITHUB_FEEDBACK_LABEL", DEFAULT_FEEDBACK_LABELS
        ).split(",")
        if lbl.strip()
    ]

    body = (
        "**A user gave the Copilot a thumbs-down with feedback.**\n\n"
        f"### User question\n\n> {user_message.strip()[:800] or '_(not captured)_'}\n\n"
        f"### Copilot answer (truncated)\n\n> {assistant_reply.strip()[:800] or '_(not captured)_'}\n\n"
        f"### User feedback\n\n> {comment.strip()[:1200]}\n\n"
        f"### Context\n\n- Page: `{page_path or 'unknown'}`\n"
        f"- Rating: {rating}\n\n"
        "---\n_Filed automatically by the Copilot feedback pipeline. "
        "Use this to improve grounding, prompts, or docs coverage._"
    )

    short = re.sub(r"\s+", " ", comment.strip())[:70] or "negative feedback"
    title = f"Copilot feedback: {short}{'…' if len(comment.strip()) > 70 else ''}"

    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            r = client.post(
                f"https://api.github.com/repos/{repo}/issues",
                json={"title": title, "body": body, "labels": labels},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
        if r.status_code in (200, 201):
            url = r.json().get("html_url")
            logging.info("feedback: filed issue %s", url)
            return url
        logging.warning("feedback: GitHub HTTP %s — %s", r.status_code, r.text[:200])
        return None
    except Exception as e:
        logging.warning("feedback: GitHub filing failed — %s", e)
        return None


def record_feedback(
    *,
    rating: str,
    comment: str = "",
    user_message: str = "",
    assistant_reply: str = "",
    page_path: str = "",
    session_id: str = "",
) -> dict:
    """Record one feedback event. Returns {"stored": bool, "issue_url": str|None}.

    ``rating`` must be "up" or "down". A "down" rating with a non-empty
    comment also files a GitHub issue. Never raises.
    """
    if rating not in ("up", "down"):
        return {"stored": False, "issue_url": None, "error": "invalid rating"}

    # Redact PII from every user-supplied field before it touches storage
    # or GitHub. The raw values are used only for the in-memory dedupe
    # fingerprint (never persisted).
    safe_comment = redact_pii(comment)
    safe_user_message = redact_pii(user_message)
    safe_assistant_reply = redact_pii(assistant_reply)
    safe_session = _hash_session(session_id)

    fp = _fingerprint(session_id, rating, user_message, comment)
    if fp in _dedupe:
        logging.info("feedback: deduped identical event")
        return {"stored": True, "issue_url": None, "deduped": True}
    if len(_dedupe) > _DEDUPE_MAX:
        _dedupe.clear()
    _dedupe.add(fp)

    entity = {
        "PartitionKey": time.strftime("%Y-%m"),
        "RowKey": uuid.uuid4().hex,
        "rating": rating,
        "comment": safe_comment,
        "user_message": safe_user_message,
        "assistant_reply": safe_assistant_reply,
        "page_path": page_path,
        "session_id": safe_session,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    stored = _store_table(entity)

    issue_url = None
    if rating == "down" and safe_comment.strip():
        issue_url = _file_feedback_issue(
            rating, safe_comment, safe_user_message, safe_assistant_reply, page_path
        )

    logging.info(
        "feedback: rating=%s stored=%s issue=%s page=%s",
        rating,
        stored,
        bool(issue_url),
        page_path[:60],
    )
    return {"stored": stored, "issue_url": issue_url}
