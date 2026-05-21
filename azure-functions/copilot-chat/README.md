# Fabby — Supercharge Microsoft Fabric Copilot Backend

Azure Function (Python v2) that powers the chat widget on the docs site.

## What's new in this version

| Mode | Trigger | Behavior |
|---|---|---|
| **1 — In repo** | Question covered by repo docs/code | Direct, cited answer; links to repo files |
| **2 — Fabric, not in repo** | Fabric/Azure topic the repo doesn't cover | Calls Microsoft Learn MCP, cites Learn URLs, **auto-files a `content-gap` GitHub issue** |
| **3 — Off-topic** | Weather, sports, recipes, dating, etc. | Snarky redirect to ask about Fabric, suggests user contact MS sales rep for custom builds |

The Copilot also has a **personality** ("Fabby") — confident, a bit cheeky, never mean. See `function_app.py` `SYSTEM_PROMPT`.

## Files

```
function_app.py          — main HTTP handler + system prompt
ms_learn.py              — Microsoft Learn MCP client (search/fetch tools)
github_issue.py          — files content-gap issues on MS Learn fallback
host.json                — Azure Functions runtime config
requirements.txt         — Python deps (openai, httpx, azure-functions)
local.settings.json.sample — env var template for local dev
```

## Environment variables

### Required

| Variable | Example |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | `https://my-instance.openai.azure.com` |
| `AZURE_OPENAI_KEY` | `<api-key>` |
| `AZURE_OPENAI_DEPLOYMENT` | `gpt-4o-mini` |
| `ALLOWED_ORIGINS` | `https://fgarofalo56.github.io,http://localhost:8000` |

### Optional (enables auto-issue filing for Mode 2 fallbacks)

| Variable | Example |
|---|---|
| `GITHUB_TOKEN` | fine-scoped PAT with `issues: write` on this repo |
| `GITHUB_REPO` | `fgarofalo56/Suppercharge_Microsoft_Fabric` |
| `GITHUB_ISSUE_LABEL` | `content-gap,copilot-suggested` (default) |

When `GITHUB_TOKEN` is empty, the Copilot still answers from Microsoft Learn — it just doesn't create issues.

## Local dev

```bash
cd azure-functions/copilot-chat
cp local.settings.json.sample local.settings.json   # edit with real values
pip install -r requirements.txt
func start
```

Then point the docs site's `copilot-chat.js` `API_BASE` at `http://localhost:7071`.

## Smoke-test Microsoft Learn integration

```bash
cd azure-functions/copilot-chat
python ms_learn.py "Direct Lake limitations"
# → prints the top 3 Learn references as JSON
```

## Deploy

```bash
az login
az functionapp deployment source config-zip \
  --resource-group <rg> --name <func-app> \
  --src <(cd azure-functions/copilot-chat && zip -r - . -x 'local.settings.json' '__pycache__/*')
```

## Architecture

```
[ Docs site /chat widget ]
            │
            │  POST /chat  (CORS-locked to docs origin)
            ▼
[ Azure Function — function_app.chat ]
            │
            ├─ Detects: prompt injection? → block
            ├─ Detects: hard off-topic?   → static snarky reply
            ├─ Otherwise:
            │    │
            │    ├─ Call Azure OpenAI with `search_microsoft_learn` tool
            │    │
            │    ├─ If LLM invokes the tool ──► ms_learn.search_docs()  ──► MS Learn MCP
            │    │      │
            │    │      └─ On success, github_issue.file_content_gap()  ──► GitHub Issues API
            │    │
            │    └─ Return final reply + groundedFromMsLearn flag
            ▼
[ Docs site renders the reply ]
```

## Personality cheat-sheet

The system prompt is in `function_app.py:SYSTEM_PROMPT`. Edit the "Personality"
section there to tune Fabby's tone. The snarky off-topic templates live in
`_SNARKY_REDIRECTS` and randomize per request — add more templates to keep
things fresh.
