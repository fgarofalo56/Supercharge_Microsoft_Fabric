---
name: harness-ralph
description: Run a bounded native-tool development cycle with verified handoffs.
mode: agent
agent: harness-coder
---

# Iterative Harness Development

Follow [Native Harness Setup](harness-setup.prompt.md). This compatibility entry
point uses the native coder workflow; it does not install or launch a daemon.
Treat user arguments as requested scope, not permission to bypass execution gates.

## Bounded cycle

1. Reconcile repository requirements, the existing GitHub issue handoff, and actual
   Git state. Preserve unrelated changes and resume incomplete authorized work.
2. Track steps with native session tasks. Select one unblocked item with explicit
   acceptance criteria and execute its targeted baseline check.
3. Implement in small steps, executing the narrowest applicable check after each
   edit. Collect actual output from background commands before judging results.
4. Obtain independent review through available native delegation. An unavailable
   worker is a review blocker, not approval. Fix findings and rerun affected checks.
5. Record implementation, test and review evidence, remaining criteria, blockers,
   and the next action in the existing GitHub issue before moving to another item.

Stop at three tasks or 60 minutes, whichever comes first. After three failed
attempts on one item, record it as blocked. Permission or authentication failures
stop the affected operation immediately. Never equate a completion phrase, issue
status, or passing subset of tests with all requirements being satisfied.

## Continuation and cancellation

Native background tools run commands, not replacement agent sessions. For work
that must outlive this session, hand off to the shipped runner rather than
improvising a loop: `atlas-forge dispatch` (each task in its own worktree with
the full gate suite) or `atlas-forge factory run` for an unattended drain. Its
verified command and flag surface is
[ATLAS FORGE orchestration](../FORGE_ORCHESTRATION.md); do not use a flag that
file has not verified. Build the task graph first with `/ralph-start` —
`dispatch --dry-run` reports *0 tasks in 0 waves* here because
`.forge/tasks.json` does not exist yet. `board` calls that `status: ok` / `no
tasks`; `dispatch --dry-run` returns `ok: false`, `status: "error"` and exit 1
for the same state, meaning "no graph built yet" rather than a failed run.

Its lifecycle behaviour in this repository is unverified until you have executed
it and recorded the evidence. Until then report session-bound execution; do not
claim that an unattended loop started, and never report a runner as running
because you read a prompt describing one.

On cancellation, stop new work, collect output, and stop owned processes through
host controls — `atlas-forge pause` stops at the next wave boundary,
`atlas-forge cancel` stops without auto-resume, `atlas-forge factory halt
--reason "<why>"` stops a drain. Preserve the handoff. A failed task keeps its
worktree on purpose; that is the evidence, so leave it.

No automatic commit, push, merge, deployment, resource deletion, or credential
expansion. **Never `git checkout --`, `git restore`, `git clean`, or
`git stash`** — this checkout holds hundreds of uncommitted files and the stash
stack is shared across worktrees on this machine. Report completed, blocked, and
unverified work separately using [Harness Status](harness-status.prompt.md).
