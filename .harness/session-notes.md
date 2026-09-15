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
