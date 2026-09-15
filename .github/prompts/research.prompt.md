---
description: Research a topic using the repository, Microsoft Docs, GitHub, and the web
---

# Research

Investigate a topic and produce an actionable, cited report.

> There is no project knowledge-base server. The `rag_search_knowledge_base`,
> `rag_search_code_examples`, `rag_get_available_sources` and
> `rag_read_full_page` tools this prompt used to call belonged to an Archon MCP
> server that is not running and not installed. Search the sources that exist.

## Search Workflow

### 1. Search this repository first

Most questions about this project are already answered here, and a repo answer
beats a web answer.

```bash
grep -ri "<keywords>" docs/ PRPs/ notebooks/ src/ 2>/dev/null | head -40
gh issue list --search "<keywords>" --state all     # decisions and their reasoning
```

`docs/`, `PRPs/plans/`, and the runbooks under `docs/runbooks/` carry most of
the standing decisions.

### 2. Microsoft documentation

For anything Fabric, Azure, Power BI, or Synapse, use the `microsoft.docs.mcp`
server configured in `.vscode/mcp.json`. It is authoritative and current;
prefer it over a general web search.

### 3. Library and framework docs

Use the Context7 MCP server where configured, for API syntax, configuration,
and version-migration questions.

### 4. The open web

`WebSearch` / `WebFetch`, last, and always cited.

## Query Best Practices

| ✅ Good Queries       | ❌ Bad Queries                          |
| --------------------- | --------------------------------------- |
| `authentication JWT`  | `how to implement user authentication`  |
| `React useState`      | `React hooks useState useEffect`        |
| `pgvector similarity` | `implement vector search in PostgreSQL` |
| `FastAPI middleware`  | `how to create middleware in FastAPI`   |

**Keep queries to 2-5 keywords for best results.**

## Research Report Template

````markdown
## 🔍 Research: [Topic]

### Query Used

`[search query]`

### Key Findings

#### Finding 1: [Title]

- **Source**: [URL/page]
- **Summary**: [Key points]
- **Relevance**: [How it applies]

#### Finding 2: [Title]

...

### Code Examples

```[language]
// Relevant example
```
````

### Recommendations

1. [Recommendation based on findings]
2. [Alternative approach if applicable]

### Related Topics to Explore

- [Topic 1]
- [Topic 2]

```

## Arguments

{input}

If a topic is provided, search for it directly.
If no topic, ask what to research.
```
