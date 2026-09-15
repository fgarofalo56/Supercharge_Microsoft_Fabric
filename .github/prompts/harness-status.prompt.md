---
name: harness-status
description: Report evidence-backed progress, verification gaps, and runner status without changing work.
mode: agent
agent: harness-coder
---

# Harness Status

Follow [Native Harness Setup](harness-setup.prompt.md). This is a reporting task;
do not implement features, change issue status, commit, or launch a campaign.

1. Read repository instructions, Git state, requirements, existing GitHub issues,
   and their latest handoffs. Identify inaccessible sources and inventory gaps.
2. Reconcile completion claims with implementation, executed tests, independent
   review, and release evidence where required. Distinguish historical evidence
   from checks executed against the current checkout.
3. Report pending, in-progress, review-needed, blocked, and evidenced-complete
   items. Give totals only for the reconciled inventory; do not infer that every
   PRD, request, or issue is complete from a partial list.
4. Run a narrow authorized health check when needed and report actual output,
   failures, and skips. Stop affected operations on permission failure.
5. Inspect available native background-command status without launching duplicate
   work. Separate configured prompts, active commands, active agent sessions,
   and a tested persistent supervisor. None implies the others.
6. If a task graph exists, read it from the shipped runner rather than guessing.
   All read-only, all starting nothing:

   ```bash
   atlas-forge board --json            # ready / doing / done / failed / blocked_on_human
   atlas-forge watch --json            # follows a run already in flight
   atlas-forge factory status --json   # commits landed, THEN supervisor liveness
   atlas-forge blocked --json          # tasks waiting on a person, and the question
   atlas-forge issues --json           # where the DAG and GitHub issues disagree
   ```

   `0 tasks in 0 waves` from `dispatch --dry-run` means `.forge/tasks.json` has
   not been written; it returns `ok: false`, `status: "error"` and exit 1, while
   `board` calls the same state `status: ok` / `no tasks`. Report it as "no
   graph built yet". `board`'s `ok` only means the file could be read; it is
   not a build verdict. `factory status` reports
   landed commits and supervisor liveness separately, and they can disagree —
   report both, infer neither. Verified flags:
   [ATLAS FORGE orchestration](../FORGE_ORCHESTRATION.md).

Include branch and dirty paths, inventory sources, current item, check results,
review gaps, blockers, and the next action. Do not predict sessions remaining
without a measured basis. A clean checkout is not proof of completed requirements.
Automatic restart, cancellation, recovery, and budget enforcement are unverified
unless actual supervisor lifecycle tests provide evidence.

This prompt changes nothing: do not start, pause, cancel, halt, resume, or
requeue a run, and never `git checkout --`, `git restore`, `git clean`, or
`git stash`.
