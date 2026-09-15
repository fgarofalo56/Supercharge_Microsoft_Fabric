---
name: harness-setup
description: Prepare resumable development using native agent tools and GitHub issues.
mode: agent
agent: harness-wizard
---

# Native Harness Setup

Use the current host's available tools, not an external task-management server.
This prompt prepares a campaign; it does not install or start a persistent runner.

> **The external task-management server is gone.** An earlier version of this
> harness tracked projects and tasks in an MCP service that is not running, not
> installed, and not the intended system. Use GitHub issues for durable records
> and `.forge/` for execution state. The multi-task runner is documented in
> [ATLAS FORGE orchestration](../FORGE_ORCHESTRATION.md) — read it before
> running anything, and never use a flag it has not verified.

## Initialize or resume

1. Read `AGENTS.md` and inspect Git status and existing worktrees. Preserve all
   staged, unstaged, and untracked work. Do not resume an old merge without authorization.
2. Inventory repository plans, PRDs, open GitHub issues and PR review findings.
   Use `gh issue` for durable cross-session tracking and the host's native task
   tool for the current session. Reuse existing issues rather than duplicate them.
   If GitHub access is unavailable, report inventory reconciliation as blocked.
3. Give each work item acceptance criteria and links to implementation, executed
   checks, independent review, and release evidence where applicable. An unchecked
   source or inaccessible issue is unverified, not complete.
4. Verify the host's actual execution capabilities and configured model routes.
   In ATLAS FORGE, use `todo` for session tasks, `delegate` for focused work,
   `fleet` for parallel read-only investigation, and `bash_background` with
   `bash_output` for long-running commands. These tools do not automatically
   launch a new agent session when the current session ends.
5. Confirm scoped command permissions before unattended work. Stop on permission
   or authentication failure; do not repeatedly retry or bypass approval.
6. Start with one implementation worker and a pilot bounded to three tasks or
   60 minutes, whichever comes first. Execute the narrowest applicable check
   after each edit, read its output, and obtain review before claiming completion.
7. After three failed attempts on the same task, record the exact blocker in its
   GitHub issue and select another unblocked task. Do not mark blocked work done.
8. At each handoff, record branch/commit, dirty paths, commands and results,
   remaining blockers, and the next action in the relevant GitHub issue. On
   resume, reconcile those records against actual Git state before editing.

## Execution boundaries

- No automatic push, remote merge, deployment, resource deletion, or credential
  expansion without explicit authorization.
- Stop launching work when cancelled; collect background command output and stop
  owned processes using the host's supported controls. Record incomplete work.
- A background shell is not an autonomous agent supervisor. Automatic session
  restart requires a separately verified host runner with supported launch,
  resume, budget, and cancellation controls. In this repository that runner is
  `atlas-forge dispatch` / `atlas-forge factory` (see below); anywhere it is not
  installed, report that blocker rather than simulating it.
- Do not claim endurance, recovery, shipping, or full backlog completion until
  those behaviors have been executed and their evidence recorded.

## The multi-task runner

For work spanning more tasks than one session can hold, hand off to the shipped
pipeline rather than improvising a loop. Full verified surface:
[ATLAS FORGE orchestration](../FORGE_ORCHESTRATION.md).

```
atlas-forge plan "<goal>"      # read-only; --dry-run first
atlas-forge decompose          # a GATE: over-budget tasks exit 1
atlas-forge dispatch --wave 1  # one wave, each task its own worktree + full gates
atlas-forge board              # ready / doing / done / failed / blocked_on_human
atlas-forge integrate --branch <name>   # merge finished branches in dependency order
```

Unattended: `atlas-forge factory run` (`tick`, `status`, `halt`, `resume`,
`requeue`). Stop with `atlas-forge pause` (wave boundary) or `atlas-forge
cancel`; a factory drain stops with `atlas-forge factory halt --reason "<why>"`.

Three things to know before using it here:

1. `atlas-forge dispatch --dry-run` reports **0 tasks in 0 waves** in this
   repository today, with `ok: false`, `status: "error"` and **exit 1**. It
   reads `.forge/tasks.json`, which does not exist here; `board` calls the same
   state `status: ok` / `no tasks`. Read the exit 1 as "no graph built yet",
   and build one with `plan` and `decompose` first.
2. `scripts/backlog_to_dag.py` is **not shipped** in this repository. It is the
   atlas-forge repo's own parser for its own markdown conventions. Nothing but
   `plan` / `decompose` writes `.forge/tasks.json`.
3. `dispatch` branches from `HEAD` and merges finished branches back. **Do not
   point it at a dirty tree** — this checkout holds hundreds of uncommitted,
   unreviewed files. Triage them with the operator first, and never with
   `git checkout --`, `git restore`, `git clean`, or `git stash`.

## Setup report

Report the inventory source and gaps, selected issue, available tools and model
routes, permission blockers, pilot limits, and whether execution is session-bound
or backed by a tested persistent runner. Never report a runner as started merely
because this prompt was read.
