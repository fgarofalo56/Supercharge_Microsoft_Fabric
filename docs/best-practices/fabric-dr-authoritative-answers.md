---
hero: assets/heroes/best-practices.svg
hero_alt: "Best practice — Fabric DR: Authoritative Answers to Common Enterprise Questions"
type: deep-dive
description: >-
  Sourced answers to the questions enterprises ask most about Microsoft Fabric
  disaster recovery — what survives a regional failover, who rebuilds what,
  whether DR can be tested, and how failback works.
---
# 🧭 Fabric DR: Authoritative Answers to Common Enterprise Questions

<div align="center" markdown>

**Resolving the "read-only vs. operational" Confusion in Microsoft Fabric Disaster Recovery Guidance**

![Category](https://img.shields.io/badge/Category-Resilience-red?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)
![Last Updated](https://img.shields.io/badge/Updated-September_2026-blue?style=for-the-badge)

</div>

---

**Last Updated:** `2026-09-06` | **Version:** 1.0.0

---

!!! abstract "What this page is"
    A companion to [Disaster Recovery & BCDR](disaster-recovery-bcdr.md), written
    for the specific conversation that comes up once an enterprise adopts
    Fabric as its primary data platform and asks: *"what actually happens when
    a region goes down?"*

    Every claim below is cited to Microsoft Learn. Where the official
    documentation is genuinely thin or silent, this page **says so
    explicitly** instead of filling the gap with inference — see
    [Questions to escalate to Microsoft](#questions-to-escalate-to-microsoft).

!!! warning "Not an official Microsoft position"
    This is a community reference summarizing public Microsoft Learn
    documentation as of **September 2026**. For a contractual or
    architectural commitment, confirm specifics with your Microsoft account
    team.

---

## 🎯 The short answer

Two claims circulate about Fabric DR and they sound like they contradict each
other. **They don't — they describe two different layers.**

| Claim | Layer it describes | True? |
|---|---|---|
| "Services become operational after Microsoft-led recovery" | Data plane — OneLake data is reachable read/write via API | ✅ True |
| "Replicated data is read-only; customers must rebuild capacities, workspaces, and artifacts" | Control plane — the Fabric portal and Power BI UI | ✅ Also true |

Microsoft's own reliability guidance states it plainly:

> "In a disaster scenario, the Fabric portal and Power BI are in read-only
> mode, and other Fabric items are unavailable. You can access their data
> stored in OneLake by using APIs or third-party tools. Both portal and Power
> BI retain the ability to perform read-write operations on **that data**."
>
> — [Reliability in Microsoft Fabric][ref-reliability]

So: **the portal is read-only. The OneLake data plane is not.** "Fully
operational services" — the ability to open Power BI, edit a pipeline, run a
notebook — requires the customer to rebuild capacity, workspaces, and items in
a new region. Nothing about that rebuild is automatic, and nothing Microsoft
does restores it for you.

---

## 1️⃣ Conflicting guidance — which statement is right?

Both are right, for the reasons in [the short answer](#the-short-answer)
above. The confusion is almost always a failure to specify *portal* vs.
*data*. When briefing a customer, always ask "operational for whom, doing
what?" before answering "yes" or "no" to "will Fabric work after failover."

---

## 2️⃣ What exactly is available after a Microsoft regional failover?

### Component-by-component

| Component | State after failover | Notes |
|---|---|---|
| **Fabric portal** | Read-only | View only; no create/edit/refresh |
| **Power BI** | Read-only | Reports viewable; **no refresh, no publish** |
| **OneLake data (via API)** | **Read-write** | ADLS Gen2 API, Storage Explorer, OneLake File Explorer |
| **OneLake catalog — Explore tab** | Read-only | View items/workspaces/metadata |
| **OneLake catalog — Govern tab** | Read-only | Insights as of last successful refresh *before* failover |
| **Pipelines / Dataflow Gen2 / Eventstream** | Unavailable | Cannot open or run; must be redeployed to a new region |
| **Warehouse** | Unavailable in place | Cannot cross-region restore; must redeploy schema + reingest |
| **KQL Database / Queryset** | **Inaccessible** | Not protected by OneLake replication; needs its own DR strategy |

[Source: Reliability in Microsoft Fabric][ref-reliability]

### Direct answers to the customer's sub-questions

!!! question "Can reports be accessed and refreshed?"
    **Accessed: yes. Refreshed: no.** Power BI stays read-only through the
    incident. Any metadata-changing operation — refresh, publish, edit — is
    unsupported until the customer completes recovery.

!!! question "Can pipelines run?"
    **No.** Pipelines, Dataflow Gen2, and Eventstream items cannot be opened
    or executed. Data already landed in a Lakehouse/Warehouse destination
    remains reachable via the OneLake API; the orchestration layer does not
    fail over with it.

!!! question "Do workspaces remain usable?"
    **Browsable, not usable.** Workspaces and their items are visible for
    reference. Nothing can be created, edited, or run inside them. Recovery
    means building **new** workspaces on **new** capacity, not reactivating
    the old ones.

!!! question "Is replicated OneLake data read-only or fully operational?"
    **This is the single most misread point in the guidance the customer has
    seen. The data plane is read AND write.** Through the OneLake ADLS Gen2
    API (or a tool built on it), you can read *and write* data in the
    secondary region after failover. It is the *portal experience* that is
    frozen — not the data.

!!! danger "Replication is asynchronous"
    OneLake geo-replication is asynchronous. Anything not yet copied at the
    moment of the disaster **is lost** — plan RPO around this, it is never
    zero. After failover, the new primary also runs with **local redundancy
    only**: you are not geo-protected again until you deliberately
    re-establish it. [Source: Well-Architected reliability guidance for
    Fabric workloads][ref-waf-fabric]

---

## 3️⃣ Customer recovery responsibilities

Fabric's DR model is **replicate-then-rebuild**, not **replicate-then-resume**.
Microsoft keeps your data reachable; you rebuild everything that makes it
*usable* through the portal again.

### Recovery steps (customer-executed)

```text
1. Create a NEW Fabric capacity        → recommend OUTSIDE primary geo
2. Create workspaces on new capacity   → same names if using recovery scripts
3. Create items with SAME names        → required if using the recovery scripts
4. Restore each item                   → per experience-specific guidance
```

[Source: Reliability in Microsoft Fabric — Recovery plan][ref-reliability]

!!! warning "Choose the recovery region deliberately"
    Learn recommends creating the new capacity **outside your primary geo**,
    because compute demand spikes tenant-wide during a real regional event —
    capacity may not be obtainable in the obvious nearby region.

### Shared responsibility

| Responsibility | Owner |
|---|---|
| Baseline infrastructure and platform availability | **Microsoft** |
| Declaring a regional disaster and initiating failover | **Microsoft** |
| Geo-replicating OneLake data | **Microsoft** |
| Power BI BCDR (always on, no opt-in) | **Microsoft** |
| Creating replacement capacity and workspaces | **Customer** |
| Redeploying items, code, and configuration | **Customer** |
| Backing up anything stored **outside** OneLake (pipelines, archived datasets) | **Customer** |
| Reconnecting data sources, gateways, credentials | **Customer** |
| Validating recovery and declaring business resumption | **Customer** |

[Source: Reliability in Microsoft Fabric][ref-reliability]

### Can Git-integrated artifacts simply be redeployed?

**Largely yes — and this is the strongest argument for Git integration as a DR
control, not just a DevOps convenience.** Anything committed to Azure DevOps
or GitHub lives outside the failed region entirely. Notebook, pipeline, and
semantic model *definitions* can be redeployed into new workspaces the moment
new capacity exists.

What Git integration does **not** save you from rebuilding:

- Warehouse and Lakehouse **contents** — definitions are not data; you still
  reingest
- KQL database data — outside OneLake, needs its own backup strategy
- Capacity and workspace creation — always a manual, prerequisite step
- Connections, gateways, and credentials — reconfigured by hand

!!! tip "Practical implication"
    A repo-first operating model (this project's own `fabric-cicd` pipeline is
    an example — see [`scripts/fabric-cicd-deploy.py`](../../scripts/fabric-cicd-deploy.py))
    converts an unbounded rebuild into a bounded, scripted redeploy. That is
    the highest-leverage DR investment available before spending money on a
    second active region.

---

## 4️⃣ Can DR be tested?

The honest answer is **partly no**, and that limit is worth stating plainly to
stakeholders rather than implying more assurance than exists.

**Customers cannot trigger a Fabric regional failover.** Only Microsoft
declares a regional disaster. There is no customer-invoked test-failover
equivalent to Azure Site Recovery's test failover or an Azure SQL
failover-group drill.

Microsoft's own reliability guidance is direct about the limit:

> "Direct chaos testing inside Fabric isn't possible, but you can **validate
> your environment and dependencies**."
>
> — [Reliability considerations for Fabric workloads][ref-waf-fabric]

### What you can genuinely test

| Testable | How |
|---|---|
| **Recovery runbook** | Build capacity + workspaces in a second region on a timer; measure how long it actually takes |
| **Git redeploy path** | Deploy every artifact into a clean workspace from source control, end to end |
| **OneLake API access** | Exercise the ADLS Gen2 global endpoint; confirm read **and** write actually works for your team |
| **Data restore** | Copy from a replicated OneLake location into a rebuilt Lakehouse/Warehouse and validate integrity |
| **Supporting-resource resilience** | Use Azure Chaos Studio to inject network latency/downtime into upstream dependencies (Event Hubs, gateways, source systems) — not Fabric itself |
| **Team readiness** | Run the rehearsal end-to-end, timed, with the people who'd actually execute it in an incident |

[Source: Reliability considerations for Microsoft Fabric workloads][ref-waf-fabric]

!!! danger "What this does NOT give you"
    None of the above proves Microsoft's actual failover mechanism works as
    documented — it proves *your rebuild runbook* works. Confidence in the
    underlying Fabric failover itself has to come from Microsoft's own SLA and
    reliability commitments, not from customer-side testing, because customers
    have no lever to pull the real thing.

---

## 5️⃣ Failback — what happens when the primary region returns?

**This is where public Learn guidance is noticeably thinner than the failover
side, and this page will not pretend otherwise.** The research behind this
page found detailed, citable steps for *failover* and *recovery*. It found no
equivalent step-by-step Microsoft article for *failback* — returning to the
original primary region once it's healthy again.

### What we can say with a source

- Replication is asynchronous in the failover direction, and nothing in
  Microsoft's public guidance suggests failback works differently in kind —
  treat any resynchronization back to the original region as **asynchronous
  and lossy at the margin**, the same caveat as forward replication.
  [Source: Reliability considerations for Fabric workloads][ref-waf-fabric]
- After a failover, the new primary runs with **local redundancy only** until
  geo-replication is deliberately re-established — this applies whether you
  stay in the secondary region or move back.
  [Source: Reliability in Microsoft Fabric][ref-reliability]

### What we cannot confirm from public documentation

!!! warning "Genuine gap — do not let a customer assume otherwise"
    Public Learn documentation does **not** describe:

    - Whether failback is automatic or requires the same manual
      rebuild-in-new-capacity process as the original failover
    - Whether data written to the secondary region during the incident is
      automatically synchronized back to the restored primary, or whether the
      customer must script that migration themselves
    - The customer's specific responsibilities during failback, beyond the
      general principle that Fabric DR is customer-executed rebuild, not
      Microsoft-executed resume
    - The size of the data gap risk if a secondary region is operated as the
      de facto primary for an extended period before failback

    **Do not answer these definitively to a customer.** Escalate them — see
    [Questions to escalate to Microsoft](#questions-to-escalate-to-microsoft).

### Reasonable working assumption, pending confirmation

Given that recovery *into* a secondary region is a manual, scripted, rebuild
process, the safest planning assumption is that failback **is the same
process run in reverse**: stand up new capacity and workspaces in the original
region, redeploy from Git, and reingest or migrate data forward. Treat
"automatic failback" as **unconfirmed** rather than assumed, and validate this
assumption with your Microsoft account team before it enters a runbook.

---

## 6️⃣ Cost versus business risk — comparing the three options

These are qualitative comparisons. No public Learn source publishes concrete
RTO/RPO numbers or cost multipliers for Fabric specifically — treat any
numeric target in a customer conversation as something *you* set contractually
with Microsoft and validate by testing your own runbook (see
[Can DR be tested?](#4️⃣-can-dr-be-tested)), not as a platform guarantee.

| | **A. Microsoft-managed geo-replication only** | **B. Scripted recovery automation** | **C. Active-active, two regions** |
|---|---|---|---|
| **What it is** | Rely on OneLake geo-replication + manual rebuild-on-incident | Pre-built, tested Git-redeploy + capacity-provisioning scripts, triggered on demand | Two live Fabric capacities running concurrently, traffic/workload split or mirrored |
| **Cost** | Lowest — pay for one capacity, storage geo-redundancy included | Low-to-moderate — engineering time to build/maintain scripts; one capacity most of the time | Highest — pay for a second capacity continuously, plus data-sync tooling |
| **Operational complexity** | Low day-to-day; high *during* an incident (manual, first-time-under-pressure rebuild) | Moderate — scripts need maintenance, versioning, and periodic drills | High — ongoing dual-region operations, consistency, and conflict handling |
| **Achievable RTO** | Slow — bounded by how fast humans can execute an undrilled manual rebuild | Faster — bounded by script execution time, which can be measured and improved | Fastest — near-zero if truly active-active, since the second region is already serving |
| **Achievable RPO** | Bounded by OneLake's asynchronous replication lag — not zero, not customer-tunable | Same as A — automation speeds the *rebuild*, not the underlying replication lag | Can approach the smallest RPO of the three, if the sync mechanism between regions is itself synchronous or near-real-time — verify this per data store, it is not a Fabric-wide guarantee |
| **When it fits** | Low-criticality workloads; cost-sensitive; recovery-time tolerance in hours-to-a-day | Most production enterprise workloads — the highest leverage-per-dollar option for most customers | Workloads with near-zero downtime tolerance where the cost of a second live capacity is justified by the cost of an outage |

!!! tip "Where most enterprises land"
    Option B is the practical middle ground for most Fabric estates: it keeps
    cost close to Option A while converting the "unbounded manual rebuild"
    risk of Option A into a measured, drillable, improvable process. This
    project's own [`fabric-cicd` deployment pipeline](../../scripts/fabric-cicd-deploy.py)
    is exactly this pattern — Git as the source of truth, scripted redeploy
    on demand.

---

## 🎬 Worked example — casino workload regional failover

A concrete walkthrough, grounded in this project's own POC assets, of what
the six sections above look like in sequence. This is **illustrative**, built
from this repo's `scripts/fabric-cicd-deploy.py` and F64 capacity model — not
a Microsoft-validated runbook. For the operational, step-by-step version see
[Multi-Region Failover runbook](../runbooks/multi-region-failover.md) and
[Disaster Recovery Execution runbook](../runbooks/disaster-recovery-execution.md).

### Scenario

The casino-gaming POC's primary Fabric capacity (F64, East US 2) becomes
unreachable during a declared Azure regional incident. Slot telemetry
ingestion, the Silver/Gold medallion pipelines, and the Direct Lake Power BI
reports all stop refreshing.

### Use case walkthrough

**Phase 1 — Incident, before any customer action (Microsoft-controlled)**

- Fabric declares the regional disaster; no customer action is possible or
  expected at this point (§1, §2).
- Power BI reports for the casino floor-monitoring dashboard remain
  **viewable** in read-only mode — pit bosses can still see the last
  successfully refreshed KPIs, they just won't update.
- The Bronze/Silver/Gold notebooks in `notebooks/bronze/`, `notebooks/silver/`,
  `notebooks/gold/` cannot be opened or run from the failed workspace.

**Phase 2 — Recovery (customer-executed)**

```bash
# 1. Stand up new Fabric capacity outside the primary geo (manual, portal or CLI)
az resource create --resource-type Microsoft.Fabric/capacities \
  --resource-group rg-casino-dr --name casino-fabric-dr \
  --properties '{"sku":{"name":"F64","tier":"Fabric"}}' \
  --location westus2

# 2. Recreate workspaces on the new capacity with the SAME names
#    (required for the recovery scripts below to resolve item references)

# 3. Redeploy every Git-tracked Fabric item from source control —
#    this project's own fabric-cicd script does exactly this (§3):
python scripts/fabric-cicd-deploy.py \
  --workspace-id <new-dr-workspace-guid> \
  --environment prod \
  --item-type-in-scope Notebook Lakehouse SemanticModel \
  --dry-run   # confirm scope first, then re-run without --dry-run
```

- Lakehouse and Warehouse **definitions** come back from Git via the script
  above; the **data** inside them does not — that's a separate reingest or
  restore-from-OneLake-replica step (§2, §3).
- KQL databases (used by this POC's Real-Time Intelligence /Eventhouse
  slot-telemetry path) are **not preserved through failover at all** and need
  their own backup/restore strategy — they're the one component this
  worked example cannot wave past.

**Phase 3 — Validate, then resume operations**

- Confirm OneLake read/write via the ADLS Gen2 API against the new workspace
  before declaring recovery complete (§2, §4 "what you can genuinely test").
- Resume slot-telemetry ingestion into the new Bronze layer; verify Silver
  dedup and Gold KPI aggregation produce the expected row counts against a
  known-good sample before reconnecting the Power BI semantic model.

**Phase 4 — Failback, when East US 2 is healthy again**

- Per §5, public guidance does not confirm whether this is automatic —
  treat it as the same manual process in reverse: new capacity/workspaces
  back in East US 2, redeploy from Git, migrate any data written during the
  incident forward. Escalate the specifics to your Microsoft account team
  before committing to a runbook.

### Where this maps to the cost/risk options in §6

This worked example follows **Option B (scripted recovery automation)** —
it's why the repo ships `fabric-cicd-deploy.py` as a first-class asset rather
than a one-off script. Option A would stop after Phase 1 and rebuild Phase 2
by hand; Option C would have Phase 2's target capacity already running before
the incident starts.

---

## ❓ Questions to escalate to Microsoft

Take these to your Microsoft account team or FastTrack engineer before they
enter a customer-facing commitment. This page deliberately does not answer
them, because public documentation doesn't either:

1. Is failback to the original primary region automatic, or does it require
   the same manual rebuild process as the original failover?
2. Is data written to the secondary region during an incident automatically
   synchronized back to the restored primary, or must the customer script
   that migration?
3. What are the customer's specific responsibilities during failback, beyond
   "expect a rebuild"?
4. What is the realistic data-gap / RPO exposure if a secondary region
   operates as the de facto primary for an extended period (days to weeks)
   before failback?
5. Are there any current or planned capabilities for customer-triggered DR
   testing (a "test failover" mode), given that direct chaos testing inside
   Fabric is explicitly unsupported today?
6. Does the answer to any of the above differ by SKU, region pair, or whether
   the customer has opted into specific OneLake DR features?

---

## 🔗 Related resources

- **[Disaster Recovery & BCDR](disaster-recovery-bcdr.md)** — full architecture,
  RTO/RPO tiering, OneLake backup strategy, and the failover/failback runbook
  procedures this page summarizes and clarifies
- **[Multi-Region Failover runbook](../runbooks/multi-region-failover.md)** —
  step-by-step operational runbook for executing a regional failover
- **[Disaster Recovery Execution runbook](../runbooks/disaster-recovery-execution.md)** —
  execution checklist and validation steps during a live incident
- **[Capacity Planning & Cost Optimization](capacity-planning-cost-optimization.md)** —
  for sizing the secondary capacity referenced in the cost/risk comparison
  above

---

## 📚 Sources

- [Reliability in Microsoft Fabric][ref-reliability] — Microsoft Learn,
  disaster recovery guide: availability zones, regional failover behavior,
  recovery steps, experience-specific restore guidance
- [Reliability considerations for Microsoft Fabric workloads][ref-waf-fabric] —
  Azure Well-Architected Framework service guide: replication model, RPO/RTO
  planning, DR testing boundaries

[ref-reliability]: https://learn.microsoft.com/en-us/fabric/security/disaster-recovery-guide
[ref-waf-fabric]: https://learn.microsoft.com/en-us/azure/well-architected/service-guides/microsoft-fabric
