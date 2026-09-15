---
hero: assets/heroes/features.svg
hero_alt: Fabric feature — AI Functions in Fabric Data Warehouse — LLM-Powered T-SQL
type: feature
---
# 🧠 AI Functions in Fabric Data Warehouse — LLM-Powered T-SQL (Preview)

<div align="center" markdown>

**Analyze, Classify, Summarize, and Transform Text Directly in SQL Queries**

![Category](https://img.shields.io/badge/Category-AI_%26_ML-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-September_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-09-11` | **Version:** 1.0.0

> **Validation scope:** Reviewed against Microsoft Learn; SQL examples have not been executed against a Fabric capacity.

---

## 🎯 Overview

Fabric Data Warehouse and the SQL analytics endpoint provide **built-in AI functions (preview)** that call LLMs directly from T-SQL. You can perform advanced text processing — sentiment analysis, classification, entity extraction, summarization, translation, grammar correction, and prompt-based generation — **without leaving your data environment** or building separate ML pipelines.

These are the SQL-flavored siblings of the [notebook AI Functions](https://learn.microsoft.com/fabric/data-science/ai-functions/overview) (`df.ai.<function>()` in pandas/PySpark) and the [AI Prompt in Dataflow Gen2](dataflow-gen2-ai-prompt-transform.md) — one capability family across three experiences.

### Available Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `AI_ANALYZE_SENTIMENT(text)` | Detect sentiment: `positive`, `negative`, `mixed`, `neutral` | `SELECT AI_ANALYZE_SENTIMENT('This hotel was great!')` → `positive` |
| `AI_CLASSIFY(text, class1, class2, ...)` | Classify text into provided labels | `SELECT AI_CLASSIFY('Room was dirty','service','dirt','food')` → `dirt` |
| `AI_EXTRACT(text, class1, class2, ...)` | Extract entities as JSON properties | `SELECT AI_EXTRACT('Check-in was late','sentiment','problem')` → `{"sentiment":"Negative",...}` |
| `AI_SUMMARIZE(text)` | Summarize text | `SELECT AI_SUMMARIZE('The hotel was clean and staff were friendly.')` → `Clean hotel, friendly staff.` |
| `AI_GENERATE_RESPONSE(prompt, data)` | Generate a response from a prompt | `SELECT AI_GENERATE_RESPONSE('Reply in 20 words:', 'The room was noisy.')` |
| `AI_TRANSLATE(text, lang_code)` | Translate to a target language | `SELECT AI_TRANSLATE('The hotel was great','de')` → `Das Hotel war großartig.` |
| `AI_FIX_GRAMMAR(text)` | Fix grammar | `SELECT AI_FIX_GRAMMAR('Th room are clean')` → `The rooms are clean` |

Supported translation languages: `de`, `en`, `fr`, `it`, `es`, `el`, `pl`, `sv`, `fi`, `cs`.

---

## 🏗️ Production Patterns

### Pattern 1: Enrich Once, Analyze Everywhere (Recommended)

AI functions call external AI APIs — **avoid applying them repeatedly in SELECT queries over the same dataset**. Precompute and materialize results:

```sql
-- Materialize AI enrichment into a gold table
INSERT INTO gold.hotel_reviews
SELECT sentiment, time_reported, problem
FROM hotel_reviews
CROSS APPLY
OPENJSON(
    AI_EXTRACT(reviews_text, 'sentiment', 'time_reported', 'problem')
) WITH (
    sentiment VARCHAR(1000),
    time_reported VARCHAR(100),
    problem VARCHAR(1000)
);
```

### Pattern 2: Guard Against NULL Updates

By default, AI functions return `NULL` for processing failures, including safety blocks, input limits, and transient service errors. For an in-place update, `ISNULL` preserves the existing value on failure; it does not protect against an incorrect non-NULL model response. Preserve raw source text separately and review generated changes before regulatory use. The following example applies only to a derived Warehouse table, not append-only Bronze data or the read-only SQL analytics endpoint:

```sql
UPDATE HotelDW.dbo.hotel_reviews
SET reviews_text = ISNULL(AI_FIX_GRAMMAR(reviews_text), reviews_text);
```

### Pattern 3: Power BI Consumption

Enrich warehouse data with AI functions, then analyze the materialized results across Power BI reports — the enrichment runs once in the warehouse, and every report consumer benefits without per-query LLM costs.

---

## ⚙️ Prerequisites

1. **Tenant switch**: Admin must enable [the tenant switch for Copilot and other features powered by Azure OpenAI](https://learn.microsoft.com/fabric/admin/service-admin-portal-copilot)
2. **Cross-geo processing**: May need to be enabled depending on your location — see [available regions for Azure OpenAI Service](https://learn.microsoft.com/fabric/fundamentals/copilot-fabric-overview#available-regions-for-azure-openai-service)
3. **Capacity**: Paid Fabric capacity (**F2 or higher**, or any P edition)
4. **Region**: AI functions work only in [supported regions](https://learn.microsoft.com/fabric/fundamentals/copilot-fabric-overview#available-regions-for-azure-openai-service)

---

## 🎰 Casino/Gaming POC Applications

Use synthetic or approved, minimized inputs. Generated summaries and edits are review aids, not filing decisions or replacements for original evidence; validate accuracy and applicable cross-geo processing permissions before using sensitive narratives.

| Use Case | T-SQL Application |
|----------|-------------------|
| **Guest feedback triage** | `AI_CLASSIFY` guest survey comments into `service`, `cleanliness`, `gaming`, `dining` for routing |
| **SAR narrative assistance** | `AI_SUMMARIZE` long incident reports into concise case summaries for compliance review |
| **Multilingual guest services** | `AI_TRANSLATE` guest communications for international VIP services |
| **Compliance data quality** | `AI_FIX_GRAMMAR` on free-text fields before regulatory submission |
| **Incident entity extraction** | `AI_EXTRACT` pulls `persons`, `locations`, `amounts` from security incident narratives as JSON |

---

## ⚠️ Limitations & Performance

| Consideration | Detail |
|---------------|--------|
| **NULL returns** | Default processing failures return `NULL`; inspect failed rows before selectively retrying. Microsoft Learn currently documents up to **99 KB of input text**; this is a text-size limit, not a token count. See the source for current limits and `ON ERROR` options. |
| **Throughput** | Microsoft Learn quotes **20–100 rows/second** in its introduction and approximately **10–30 text values/second** for larger batches in its remarks. These are indicative, not guaranteed; benchmark representative inputs and materialize results. |
| **Preview status** | No SLA; not recommended for production workloads without validation |
| **Vector type** | The `vector` data type is **not** supported in Warehouse even though AI functions are — use Eventhouse for vector search |
| **Cost** | Each call consumes capacity CUs — see [Capacity Planning](../best-practices/capacity-planning-cost-optimization.md) |

---

## 🔗 Related Documents

- [AI-Powered Prompt Transform](dataflow-gen2-ai-prompt-transform.md) — The Dataflow Gen2 flavor of AI enrichment
- [Fabric SQL Database](fabric-sql-database.md) — The operational database sibling of the Warehouse
- [Eventhouse Vector Database](eventhouse-vector-database.md) — Vector search for embeddings (not supported in Warehouse)
- [Prompt Engineering for Fabric](prompt-engineering-fabric.md) — Prompt design for `AI_GENERATE_RESPONSE`
- [AI Copilot Configuration](ai-copilot-configuration.md) — The tenant switch that gates AI functions

---

## 📚 Microsoft Learn References

- [Use AI functions in Fabric Data Warehouse (preview)](https://learn.microsoft.com/fabric/data-warehouse/ai-functions)
- [AI Functions overview (notebooks, warehouse, dataflows)](https://learn.microsoft.com/fabric/data-science/ai-functions/overview)
- [AI_ANALYZE_SENTIMENT (Transact-SQL)](https://learn.microsoft.com/sql/t-sql/functions/ai-analyze-sentiment-transact-sql?view=fabric&preserve-view=true)
- [AI_EXTRACT (Transact-SQL)](https://learn.microsoft.com/sql/t-sql/functions/ai-extract-transact-sql?view=fabric&preserve-view=true)
- [Copilot tenant settings](https://learn.microsoft.com/fabric/admin/service-admin-portal-copilot)

---

> 📝 **Document Metadata**
> - **Author**: Documentation Team
> - **Reviewers**: Data Engineering, AI/ML Team, Compliance
> - **Classification**: Internal
> - **Next Review**: 2026-12-07
