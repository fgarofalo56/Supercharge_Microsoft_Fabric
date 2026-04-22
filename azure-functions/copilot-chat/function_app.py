"""
Supercharge Microsoft Fabric — AI Copilot Chat Backend

Azure Function (v2) that proxies chat requests to Azure OpenAI with
repository-aware system prompt. Supports streaming via SSE.

Environment Variables (required):
  AZURE_OPENAI_ENDPOINT    — e.g. https://myinstance.openai.azure.com
  AZURE_OPENAI_KEY         — API key
  AZURE_OPENAI_DEPLOYMENT  — deployment name (e.g. gpt-4o-mini)
  ALLOWED_ORIGINS          — comma-separated origins for CORS
"""

import json
import logging
import os
import time
from collections import defaultdict

import azure.functions as func
from openai import AzureOpenAI

app = func.FunctionApp()

# ── Rate limiting (in-memory, per-instance) ─────────────────────
_rate_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT = 20        # requests per window
RATE_WINDOW = 60       # seconds


def _rate_limited(ip: str) -> bool:
    now = time.time()
    window = _rate_store[ip]
    # Prune old entries
    _rate_store[ip] = [t for t in window if now - t < RATE_WINDOW]
    if len(_rate_store[ip]) >= RATE_LIMIT:
        return True
    _rate_store[ip].append(now)
    return False


# ── System prompt with full repo context ────────────────────────
SYSTEM_PROMPT = """You are the **Supercharge Microsoft Fabric Copilot**, an AI assistant embedded in the documentation site for the Supercharge Microsoft Fabric repository. You have deep knowledge of the entire codebase and documentation.

## Repository Overview
This is a production-ready POC for Microsoft Fabric targeting the **casino/gaming industry** and **7 federal agency domains** (USDA, SBA, NOAA, EPA, DOI, DOT/FAA, Tribal Healthcare). The stack includes Bicep IaC, PySpark notebooks, KQL, DAX, and Power BI on Microsoft Fabric F64 SKU.

## Directory Structure
```
infra/              — Bicep IaC modules (capacity, warehouse, SQL DB, pipelines, alerts)
docs/               — 35 feature docs + 37 best practice guides
  features/         — Fabric IQ, RTI, Direct Lake, Mirroring, Dataflow Gen2, Data Activator, etc.
  best-practices/   — Medallion, capacity planning, BCDR, security, FinOps, testing, etc.
tutorials/          — 37 step-by-step tutorials (00-36)
data_generation/    — 16 Python data generators (casino + federal + streaming)
  open_data/        — Real federal dataset download scripts (USDA, SBA, NOAA, EPA, DOI)
notebooks/          — 55+ Fabric-importable notebooks
  bronze/           — 17 Bronze ingestion notebooks
  silver/           — 16 Silver transformation notebooks
  gold/             — 18 Gold KPI/analytics notebooks
scripts/            — Deployment scripts (fabric-cicd)
validation/         — 612 unit tests + 9 Great Expectations suites
```

## Key Patterns
- **Medallion Architecture**: Bronze (raw, append-only) → Silver (cleansed, validated) → Gold (business KPIs, star schema)
- **Notebook format**: Databricks notebook source with `# COMMAND ----------` separators; uses `mssparkutils` (NOT `dbutils`)
- **Delta Lake**: All tables use Delta format with schema enforcement
- **Direct Lake**: Primary BI connectivity — Power BI reads Delta directly from OneLake

## Compliance Thresholds (Casino/Gaming)
- CTR (Currency Transaction Report): $10,000
- SAR (Suspicious Activity Report): structuring pattern $8,000–$9,900
- W-2G (Gambling Winnings): $1,200 (slots), $600 (table games/keno), $5,000 (poker)
- PII handling: SSN hashed with salt from `FABRIC_POC_HASH_SALT` env var, card numbers masked

## Federal Agency Domains
- **USDA**: Crop production, commodity prices, food safety
- **SBA**: Loan programs, disaster loans, business demographics
- **NOAA**: Weather observations, storm events, climate data
- **EPA**: Air quality (AQI), water quality, Superfund sites
- **DOI**: Earthquake data, wildfire incidents, land management

## Common Troubleshooting
- `dbutils` errors → Replace with `mssparkutils` (Phase 11 migration)
- `/tmp` checkpoint errors → Use OneLake paths via `CHECKPOINT_PATH_BASE`
- Missing `lh_bronze.*` namespace → Ensure Lakehouse is attached and use three-part naming
- Notebook import errors → Check `# Databricks notebook source` header line

## Response Guidelines
- Always cite specific file paths when referencing code or docs (e.g., `notebooks/bronze/01_bronze_slot_telemetry.py`)
- Link to relevant tutorials by number (e.g., "See Tutorial 03 - Gold Layer")
- Use code examples in PySpark, KQL, or DAX as appropriate
- For compliance questions, always include the specific regulatory threshold
- If asked about something not in the repo, say so clearly
"""


def _cors_headers(origin: str | None) -> dict[str, str]:
    allowed = os.environ.get("ALLOWED_ORIGINS", "https://fgarofalo56.github.io").split(",")
    allowed = [o.strip() for o in allowed]
    if origin in allowed or "*" in allowed:
        return {
            "Access-Control-Allow-Origin": origin or "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    return {}


@app.route(route="chat", methods=["POST", "OPTIONS"], auth_level=func.AuthLevel.ANONYMOUS)
def chat(req: func.HttpRequest) -> func.HttpResponse:
    origin = req.headers.get("Origin")
    cors = _cors_headers(origin)

    # CORS preflight
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=cors)

    # Rate limit
    client_ip = req.headers.get("X-Forwarded-For", req.headers.get("X-Real-IP", "unknown"))
    if _rate_limited(client_ip):
        return func.HttpResponse(
            json.dumps({"error": "Rate limit exceeded. Please wait a moment."}),
            status_code=429,
            headers={**cors, "Content-Type": "application/json"},
        )

    # Parse body
    try:
        body = req.get_json()
    except Exception:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            headers={**cors, "Content-Type": "application/json"},
        )

    user_message = body.get("message", "").strip()
    if not user_message:
        return func.HttpResponse(
            json.dumps({"error": "Empty message"}),
            status_code=400,
            headers={**cors, "Content-Type": "application/json"},
        )

    history = body.get("history", [])
    page_context = body.get("pageContext", {})

    # Build messages array
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add page context
    if page_context.get("path"):
        messages.append({
            "role": "system",
            "content": f"The user is currently viewing: {page_context.get('title', 'Unknown')} ({page_context.get('path', '')})",
        })

    # Add conversation history (last N turns)
    for msg in history[-20:]:
        if msg.get("role") in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"][:2000]})

    messages.append({"role": "user", "content": user_message[:4000]})

    # Call Azure OpenAI
    try:
        client = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_KEY"],
            api_version="2025-04-01-preview",
        )

        response = client.chat.completions.create(
            model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            messages=messages,
            temperature=0.3,
            max_completion_tokens=2000,
            stream=True,
        )

        # Stream response as ndjson
        def generate():
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield json.dumps({"content": chunk.choices[0].delta.content}) + "\n"
            yield "data: [DONE]\n"

        # Azure Functions v2 doesn't support true streaming, so collect and return
        parts = []
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                parts.append(chunk.choices[0].delta.content)

        reply = "".join(parts)

        return func.HttpResponse(
            json.dumps({"reply": reply}),
            status_code=200,
            headers={**cors, "Content-Type": "application/json"},
        )

    except KeyError as e:
        logging.error("Missing environment variable: %s", e)
        return func.HttpResponse(
            json.dumps({"error": f"Server misconfigured: missing {e}"}),
            status_code=500,
            headers={**cors, "Content-Type": "application/json"},
        )
    except Exception as e:
        logging.error("Azure OpenAI error: %s — %s", type(e).__name__, e)
        return func.HttpResponse(
            json.dumps({"error": f"Failed to generate response: {type(e).__name__}: {e}"}),
            status_code=500,
            headers={**cors, "Content-Type": "application/json"},
        )
