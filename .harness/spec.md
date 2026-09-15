# Specification — Fabric backlog reconciliation and verified publication

> **Source:** GitHub issue [#142](https://github.com/fgarofalo56/Supercharge_Microsoft_Fabric/issues/142).
> That issue is the durable record. This file restates its scope so the harness has a
> local specification to read. Where the two disagree, **the issue wins** — re-read it
> rather than trusting this copy.

## Goal

Reconcile every repository-recorded request and open, unshipped item; validate and
update Microsoft Fabric documentation, samples, and walkthroughs; merge eligible PRs;
and verify the published Pages site for the deployed commit.

## Target audience

Fabric architects, data engineers, developers, operators, and workshop participants
using the casino, federal, and enterprise scenarios in this repository.

## Definition of done

Every inventoried request carries an evidence-backed disposition. Approved work is
validated, independently reviewed, merged through required checks, discoverable in
navigation and search, and verified at its published URL. **Blocked or deferred work
stays explicit and is never counted as shipped.**

## Scope areas

1. **Request inventory** — repository plans, issue/PR discussions, deferred PR work,
   implementation, tests, publication evidence. Repository records only. An empty open
   list is not a drained campaign; reconcile closed and merged records too.
2. **Dirty-tree inventory** — read-only pass over the existing staged rename work,
   unstaged edits, untracked files, and all worktrees. Ask which changes belong before
   editing or staging anything.
3. **Workload gap matrix** — official-source-backed mapping of capability to existing
   doc, sample, walkthrough, release status, evidence date, and disposition. Covers
   Data Engineering, Data Factory, Data Science, Data Warehouse, Databases, Industry
   Solutions, Real-Time Intelligence, Fabric IQ, Power BI, plus OneLake, governance,
   security, lifecycle, and capacity. Update existing coverage rather than duplicate.
4. **Publication verification** — strict build behaviour, internal links, navigation and
   search, sample downloads, rendered walkthroughs, deployment commit, published URLs.
5. **Issue #105 reconciliation** — check actual repository and Pages redirects. Do not
   rename the repository blindly.

## Hard constraints

| Constraint | Rule |
|---|---|
| Task ledger | GitHub issues are durable; `.forge/` is execution state. `.harness/state.json` exists by operator decision of 2026-09-15, overriding issue #142 gate 4. **Status does not propagate between them** — reconcile both before declaring the campaign drained. |
| Existing work | 343 dirty entries incl. 159 staged docs-rename files. Preserve. No blanket staging, stash, clean, restore, reset, or destructive checkout. |
| Worktrees | Three exist. Do not operate on those under `temp/` without explicit authorization. |
| Git history | Repo has history. **No `git init`, no "initial commit".** |
| Cloud | No Fabric/Azure deployment, deletion, credential expansion, or billable validation. |
| Merge | Eligible PRs may be merged; never bypass protections, merge unreviewed, or auto-merge every open PR. |
| Evidence | Skipped checks, a green subset, or historical claims are never acceptance. |
| Dispatch | Do not dispatch against the dirty checkout. Resolve ownership and approve a clean base first. |

## Pilot limits

One implementation worker; at most three tasks or 60 minutes, whichever comes first.
Stop affected operations on authentication or permission failure. After three failed
attempts on a task, record the blocker and the exact question. Never silently raise
limits. Agree a monetary ceiling before paid unattended execution.

## Role pipeline

Initializer reconciles requirements → Coder makes scoped changes → Tester executes
applicable checks → independent Reviewer evaluates. **Failed delegation is a review
blocker, not approval.**

## First task candidate

Read-only reconciliation of PR #140 and its deferred documentation against local
changes, CI/review evidence, and the Phase 14/15 plans, producing an inclusion
proposal for operator approval before any implementation or merge.

## Known state at spec authoring (2026-09-15)

- Branch `docs/fabric-dr-authoritative-answers` at `710f889`, **behind origin by 3**.
- 343 dirty entries; 159 staged.
- `.forge/` present and gitignored; no task graph confirmed — recheck before planning.
- Harness contract baseline: 13 tests passing.
- Planner route previously failed on expired Claude OAuth; unresolved at this writing.
