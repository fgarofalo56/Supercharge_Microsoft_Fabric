---
hero: assets/heroes/features.svg
hero_alt: Fabric feature — Fabric Data Agent API — Programmatic Agent Management
type: feature
---
# 🔌 Fabric Data Agent API — Programmatic Agent Management

<div align="center" markdown>

**Build, Manage, and Invoke Data Agents from CI/CD, Custom Apps, and Backend Services**

![Category](https://img.shields.io/badge/Category-AI_%26_ML-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-September_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-09-07` | **Version:** 1.0.0

---

## 🎯 Overview

The **Fabric data agent public API** (announced July 2026) lets you manage data sources and data agents **programmatically** — from local development, CI/CD pipelines, internal portals, containers, Azure Functions, and backend services. Combined with the [Fabric data agent SDK](https://aka.ms/fabric/data-agent/sdk/docs), the API turns data agents from portal-only artifacts into fully automatable platform resources.

Data agents can also be invoked as a **tool inside Microsoft Foundry Agent Service**, where the Fabric data agent handles NL2SQL over enterprise data while the Foundry agent handles orchestration and response generation.

### What You Can Automate

| Scenario | How the API Helps |
|----------|-------------------|
| **CI/CD for agents** | Create, update, and publish data agents as part of deployment pipelines |
| **Environment promotion** | Replicate agent configurations across dev/test/prod workspaces |
| **Custom chat surfaces** | Embed governed Q&A in internal portals and line-of-business apps |
| **Backend integration** | Invoke agents from Azure Functions, containers, and backend services |
| **Foundry orchestration** | Use the data agent as a tool in multi-step Foundry agent workflows |

---

## 🏗️ Foundry Agent Service Integration

The Fabric data agent integrates with [Microsoft Foundry Agent Service](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/fabric) as a tool:

1. **Build and publish** a Fabric data agent in the Fabric portal
2. **Create a Foundry connection** to the data agent (workspace ID + artifact ID from the agent URL: `.../groups/<workspace_id>/aiskills/<artifact_id>...`)
3. **Create a Foundry agent** with the Fabric tool enabled
4. When a user sends a query, the Foundry agent determines whether to invoke the Fabric data agent, which generates queries using the **end user's identity** (On-Behalf-Of)

```bash
# Get an access token for the Foundry Agent REST API
export AGENT_TOKEN=$(az account get-access-token \
  --scope "https://ai.azure.com/.default" --query accessToken -o tsv)

# Create a thread
curl --request POST \
  --url $AZURE_AI_FOUNDRY_PROJECT_ENDPOINT/threads?api-version=$API_VERSION \
  -H "Authorization: Bearer $AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d ''
```

> ⚠️ `AGENT_TOKEN` is a credential. Keep it secret and never check it into source control.

### Identity Passthrough and Access Control

This integration uses **identity passthrough (On-Behalf-Of)** — the Fabric tool runs queries using the identity of the signed-in user:

- Give each end user access to the Fabric data agent **and** its underlying data sources, or the tool call fails
- **User identity authentication only** — service principal authentication is **not** supported for the Fabric data agent
- Row-level and column-level security continue to apply

### Minimum Permissions by Data Source

| Data source | Minimum permission |
|-------------|-------------------|
| Power BI semantic model | Read (RLS/CLS still apply) |
| Lakehouse | Read on the lakehouse item (and table access, if enforced) |
| Warehouse | Read (`SELECT` on relevant tables) |
| KQL database | Reader role on the database |
| Mirrored database | Read access to the mirrored database and its selected data |
| Ontology | Read access to the ontology and its bound data sources |
| Microsoft Graph | Delegated access to the M365 content requested by the signed-in user |

---

## ⚙️ Prerequisites

1. **Paid F2 or higher** Fabric capacity, or Power BI Premium P1+ with Fabric enabled
2. **Published** Fabric data agent (unpublished agents can't be invoked)
3. Data agent and Foundry project in the **same tenant**
4. Data agent and its data sources on capacities in the **same region** — cross-region queries fail
5. `Foundry User` Azure RBAC role (formerly Azure AI User) for developers and end users
6. [Cross-geo processing tenant settings](https://learn.microsoft.com/fabric/data-science/data-agent-tenant-settings) configured if your deployment requires them

### SDK and API Support

| Surface | Python SDK | C# SDK | JS SDK | Java SDK | REST API |
|---------|-----------|--------|--------|----------|----------|
| Foundry Agent Service | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 🎰 Casino/Gaming POC Applications

| Use Case | Application |
|----------|-------------|
| **Compliance chatbot** | Embed a CTR/SAR data agent in the compliance team's internal portal via the API |
| **CI/CD for agents** | Promote the player-analytics agent from dev to prod with the same pipeline as notebooks |
| **Foundry orchestration** | Multi-step agent that checks SAR thresholds (Fabric tool) then drafts a case summary |
| **Federal helpdesk** | Backend service invokes a grant-data agent to answer constituent questions |

---

## ⚠️ Limitations & Troubleshooting

| Issue | Cause | Resolution |
|-------|-------|------------|
| `Artifact Id should not be empty` | Invalid `workspace_id` or `artifact_id` in the connection | Recreate the connection; copy IDs from the agent URL path |
| `unauthorized` | End user lacks access to the agent or its data sources | Grant access in Fabric; confirm user identity auth |
| `Cannot find the requested item` | Agent isn't published or configuration changed | Publish the agent; confirm data sources are valid |
| Agent doesn't use the Fabric tool | Tool not configured or prompt doesn't trigger it | Add tool guidance to instructions ("For sales data, use the Fabric tool") or force with `tool_choice` |
| Cross-region failure | Data source capacity in a different region | Keep agent and data sources in the same region |

---

## 🔗 Related Documents

- [Data Agents](data-agents.md) — Creating and configuring data agents in the portal
- [Fabric IQ Conversational Analytics](fabric-iq-conversational-analytics.md) — The M365 Copilot surface for data answers
- [Fabric MCP](fabric-mcp.md) — Model Context Protocol access to Fabric items
- [Fabric REST APIs](fabric-rest-apis.md) — The broader platform API surface
- [AI Copilot Configuration](ai-copilot-configuration.md) — Capacity and tenant prerequisites

---

## 📚 Microsoft Learn References

- [Fabric data agent concepts](https://learn.microsoft.com/fabric/data-science/concept-data-agent)
- [Fabric data agent SDK](https://aka.ms/fabric/data-agent/sdk/docs)
- [Use the Microsoft Fabric data agent with Foundry Agent Service](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/fabric)
- [Fabric data agent configurations](https://learn.microsoft.com/fabric/data-science/data-agent-configurations)
- [Data agent sharing and permissions](https://learn.microsoft.com/fabric/data-science/data-agent-sharing)

---

> 📝 **Document Metadata**
> - **Author**: Documentation Team
> - **Reviewers**: AI/ML Team, Platform Engineering
> - **Classification**: Internal
> - **Next Review**: 2026-12-07
