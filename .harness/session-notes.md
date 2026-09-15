# Session Notes

## Session 1 — 2026-09-15

**Agent:** harness-coder
**Branch:** `docs/fabric-dr-authoritative-answers` @ `710f889` (behind origin by 3)
**Task:** task-001 — Reconcile PR #140 and its deferred documentation against the local tree
**Status:** done (read-only; no implementation)

### Context

`.harness/state.json` did not exist at session start. Operator authorised creating it,
overriding issue #142 gate 4, which had named GitHub issues the sole durable ledger.
**Consequence: status does not propagate.** Marking a task done here does not close the
matching GitHub issue. Both must be reconciled before the campaign is called drained.
The spec's constraints table was corrected to match.

Six tasks were derived from `.harness/spec.md`'s five scope areas plus its named first
candidate. task-001 selected as highest `task_order` (100) with nothing in `doing`.

### Evidence gathered

PR #140, head `f051eb9`:

| Property | Value |
|---|---|
| State | OPEN, **draft** |
| Reviews | **0** (`REVIEW_REQUIRED`) |
| Merge state | **BEHIND** |
| CI on head | 13 checks SUCCESS, `Enable auto-merge` SKIPPED |

File comparison, 100 PR files against the local tree:

| Classification | Count |
|---|---|
| Missing locally | **0** |
| Identical | 42 |
| Diverged | 58 |

Diverged files concentrate in `docs/best-practices` (27), `docs/notebooks` (7),
`docs/compliance-templates` (6), `.github/workflows` (3).

### Principal finding — local tree carries a regression the PR does not

In `docs/best-practices/01-workspaces-naming.md` the **local** side points the
"Best Practices" breadcrumb and footer link at `01-workspaces-naming.md` — the page
linking to itself. The PR side points at `../best-practices.md`, the real parent.

Verified: `docs/best-practices.md` **exists**, and at least **9** local files under
`docs/best-practices/` carry a self-referential link. Sampled instances include
`performance-parallelism.md`, `error-handling-monitoring.md`,
`alerting-data-activator.md`, and the numbered `07`–`11` set.

**The PR's version is correct; local regressed it.** This inverts the naive reading
that 58 diverged files means the PR is stale.

### Merge eligibility

Not eligible, on three independent counts: draft status, zero reviews with
`REVIEW_REQUIRED`, and `BEHIND` merge state. The 13 green checks are evidence for
`f051eb9` only — **not** for this dirty checkout, per the spec's evidence constraint.

### What was not done

No edits to tracked files. No staging, stash, clean, restore, reset, or checkout.
No merge. No `temp/` worktree operations. No cloud calls. Dirty and staged counts
unchanged by the reconciliation pass itself.

### Open questions for the operator

1. Should the self-referential navigation links be repaired locally, or resolved by
   bringing PR #140's version across? The two paths produce different diffs.
2. PR #140 is `BEHIND`. Does it get updated and reviewed, or superseded?
3. Branch is 3 commits behind origin — task-003 covers this and needs approval before
   any history operation.

### Next task

task-002 — Inventory the dirty tree and assign ownership to every entry (order 95).
Also read-only. Remains blocked on operator input for entries whose owner is unclear.

---

## Sessions 2-3 — 2026-09-15 (loop, stopped at pilot bound)

**Agent:** harness-coder | **Branch:** docs/fabric-dr-authoritative-answers @ `6102ca0`
**Tasks:** task-002 (order 95), task-003 (order 90) — both done, both read-only
**Stopped:** pilot limit of 3 tasks reached (task-001, 002, 003). Not raised silently.

### task-002 — dirty-tree ownership inventory

243 entries: 200 modified, 43 untracked. Two populations with opposite dispositions.

**(a) 151 files, equal +/- — mechanical link rewrites.** Includes the 15 carrying the
self-referential "Best Practices" bug. **All 15 are modified; 0 pre-existing on disk** —
the working tree introduced this, it was not inherited. Correcting session 1: I said
">=9" from a grep matching only `0[0-9]-` prefixes; the true figure is **15**.

**(b) 49 files, real content change, net -3610 lines.** Sampled two large deletions:

| File | Change | Verdict |
|---|---|---|
| `.github/agents/harness-wizard.agent.md` | 537 -> 68 lines | **KEEP** — deliberate Archon removal; strips `archon-*` tool declarations and hardcoded `claude-sonnet-4` |
| `docs/features/variable-libraries.md` | 513 -> 256 lines | **KEEP** — factual correction, not loss. v1.0.0 documented a "Secret" type with Key Vault binding **absent from the official spec** and omitted **value sets** (the actual GA mechanism). v2.0.0 cites Microsoft Learn and adds Connection/Item reference types. |

The second nearly got flagged as content loss on line count alone. Reading the
replacement text reversed that.

**43 untracked:** 9 new `docs/features/` pages, 13 `docs/**/README.md` mirrors,
6 `infra/ci-runners/`, 4 `tests/`, plus `AGENTS.md` and `FORGE_ORCHESTRATION.md`.

### task-003 — branch divergence

**Divergence, not simple lag.** `HEAD...@{u}` = **1 ahead, 3 behind**; the 1 is my
commit `6102ca0`. Merge base `710f889`.

The 3 upstream commits (`c9cd67e` merge, `fa017bb`, `ca8fe01`) touch **exactly one
file**: `requirements-docs.txt` — `mkdocs-redirects` 1.2.2->1.2.3, `pillow`
12.2.0->12.3.0. Both dependabot bumps. That file is **not** locally dirty.

**Zero collisions** against all 243 dirty entries. Integration is low-risk.

A first pass appeared to show `.harness/*` changing upstream — an artefact of reading
a symmetric diff as one-directional. Upstream has no `.harness/`. Re-checked before
reporting.

### Verification

HEAD unchanged at `6102ca0`. Tree 243 dirty / 0 staged before and after both tasks.
No merge, rebase, pull, reset, stash, clean, or `temp/` worktree operation.

### Blocking decisions

1. **The 15 self-referential files** — repair locally, or take PR #140's correct
   version? Now known to be working-tree-introduced, which favours repairing here.
2. **PR #140 is BEHIND** — update and review, or supersede?
3. **Upstream integration** — approved as low-risk, but needs your go-ahead.

### Next

task-004, Fabric workload gap matrix (order 80). Requires a new pilot authorisation.
