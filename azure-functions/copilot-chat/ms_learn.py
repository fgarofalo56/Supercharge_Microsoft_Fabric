"""Microsoft Learn MCP client — minimal HTTP wrapper.

The official MS Learn MCP server at https://learn.microsoft.com/api/mcp
speaks JSON-RPC 2.0 over HTTP+SSE. For the Copilot chat backend we only
need two tools:
  - microsoft_docs_search  — keyword search over learn.microsoft.com
  - microsoft_docs_fetch   — fetch a specific Learn page as markdown

This module exposes them as plain Python functions and falls back to a
graceful empty result on failure so the Copilot never crashes when MS
Learn is rate-limited or offline.
"""

from __future__ import annotations

import json
import logging
import uuid

import httpx

MCP_URL = "https://learn.microsoft.com/api/mcp"
HTTP_TIMEOUT = 25.0


def _try_parse_json(text: str):
    """Parse text as JSON, returning None when it isn't valid JSON."""
    if not text or text[0] not in "{[":
        return None
    try:
        return json.loads(text)
    except ValueError:
        return None


def _call_mcp(tool: str, arguments: dict) -> list[dict]:
    """Invoke an MCP tool and return parsed content items.

    Returns a list of dicts like:
        [{"title": "...", "url": "...", "excerpt": "..."}]
    On any error (HTTP, parse, timeout) returns an empty list so the
    Copilot can degrade gracefully.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            r = client.post(MCP_URL, json=payload, headers=headers)
        if r.status_code != 200:
            logging.warning("MS Learn MCP %s -> HTTP %s", tool, r.status_code)
            return []
        # The server responds as SSE frames ("event: message\ndata: {...}").
        # Collect every data: payload and use the last one — earlier frames
        # may be progress notifications.
        text = r.text.strip()
        body: dict = {}
        data_lines = [
            line.split("data:", 1)[1].strip()
            for line in text.splitlines()
            if line.lstrip().startswith("data:")
        ]
        if data_lines:
            body = json.loads(data_lines[-1])
        else:
            body = r.json()
        result = body.get("result", {}) if isinstance(body, dict) else {}
        content = result.get("content", []) or []
        items: list[dict] = []
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                # The text block is a JSON-encoded envelope:
                #   {"results": [{"title": ..., "content": ..., "contentUrl": ...}]}
                # Older shapes may be a bare list/dict or plain text.
                txt = str(c.get("text", "")).strip()
                parsed = _try_parse_json(txt)
                if isinstance(parsed, dict) and isinstance(parsed.get("results"), list):
                    for entry in parsed["results"]:
                        if isinstance(entry, dict):
                            items.append(
                                {
                                    "title": entry.get("title") or "Microsoft Learn",
                                    "url": entry.get("contentUrl") or entry.get("url"),
                                    "excerpt": str(entry.get("content") or "")[:600],
                                }
                            )
                    continue
                if isinstance(parsed, list):
                    items.extend(parsed)
                    continue
                if isinstance(parsed, dict):
                    items.append(parsed)
                    continue
                # Not JSON — the text block is a plain-text answer.
                items.append({"excerpt": txt[:600], "title": "Microsoft Learn"})
        return items
    except Exception as e:
        logging.warning("MS Learn MCP %s failed: %s", tool, e)
        return []


def search_docs(query: str, max_results: int = 5) -> list[dict]:
    """Return up to N Microsoft Learn references for `query`.

    Each result has at least: title, url, excerpt.
    """
    items = _call_mcp("microsoft_docs_search", {"query": query[:300]})
    return items[:max_results]


def fetch_doc(url: str) -> str | None:
    """Return the markdown body of a Microsoft Learn page, or None."""
    items = _call_mcp("microsoft_docs_fetch", {"url": url})
    for item in items:
        if isinstance(item, dict):
            text = item.get("text") or item.get("excerpt") or item.get("content")
            if text:
                return str(text)
    return None


def format_citations(refs: list[dict]) -> str:
    """Render a markdown bullet list of MS Learn citations."""
    lines = []
    for r in refs:
        title = r.get("title") or r.get("name") or "Microsoft Learn"
        url = r.get("url") or r.get("source") or r.get("link")
        if url:
            lines.append(f"- [{title}]({url})")
        else:
            lines.append(f"- {title}")
    return "\n".join(lines)


# Diagnostic helper — only used for local smoke tests.
if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "Direct Lake limitations"
    refs = search_docs(q, max_results=3)
    print(json.dumps(refs, indent=2))
