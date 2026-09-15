---
name: ralph-status
description: Report dispatch and factory state from atlas-forge board, watch, and factory status. Read-only.
mode: agent
tools:
  - filesystem
  - terminal
---

## User Input

```text
$ARGUMENTS
```

## Purpose

Report what is actually running and what the task graph actually says. This is
a **reporting task**: do not implement anything, do not change task status, do
not commit, and do not start a run.

> The Archon state documents this prompt used to query do not exist — Archon is
> not running and not installed. All FORGE state is on disk under `.forge/`.
> See [ATLAS FORGE orchestration](../FORGE_ORCHESTRATION.md).

## What to read

Run these and report their real output. All are read-only.

```bash
atlas-forge board --json            # the task graph as columns
atlas-forge status --json           # this workspace's newest session
atlas-forge blocked --json          # tasks waiting on a person, with the question
atlas-forge issues --json           # where the task DAG and GitHub issues disagree
atlas-forge factory status --json   # commits landed, then supervisor liveness
```

To follow a run that is already in flight (this starts nothing):

```bash
atlas-forge watch --json
```

Raw progress, if you need it, is `.forge/dispatch-progress.json`. Evidence from
completed waves is under `.forge/runs/` and `.forge/evidence/`.

## How to read the output

- **`0 tasks in 0 waves`** from `atlas-forge dispatch --dry-run` means
  `.forge/tasks.json` has not been written. The two commands disagree about it:
  `board` says `status: ok` / `no tasks`, `dispatch --dry-run` returns
  `ok: false`, `status: "error"` and **exit 1**. Say "no task graph exists yet",
  not "dispatch is broken".
- **`board`'s `ok` means the file could be read.** It is not a verdict on the
  build. Only `decompose` returns `ok` as the verdict itself.
- **`factory status` reports two separate things** — commits landed, and
  whether the supervisor is actually alive. They can disagree. Report both;
  never infer one from the other.
- **A configured prompt is not a running agent.** Configured prompts, active
  shell commands, an active agent session, and a live supervisor are four
  different things and none implies the others.
- **Distinguish historical evidence from checks run against this checkout.** A
  passing record from a previous run is not a current result.

## Also report

- Current branch, and how many paths are dirty (`git status --porcelain | wc -l`).
- Which worktrees exist (`git worktree list`) and whether any has work in flight.
- Open GitHub issues and PRs if `gh` is available (`gh issue list`,
  `gh pr list`); note it as a gap if it is not.

## Do not

- Do not predict "sessions remaining" or a completion percentage without a
  measured basis.
- Do not treat a clean checkout as proof that requirements are complete.
- Do not report a runner as started because you read a prompt that describes
  one.
- Do not start, resume, halt, or requeue anything from this prompt. Use
  `/ralph-iterate` to run and `/ralph-cancel` to stop.

## Report shape

Inventory sources and gaps, task counts per column, what is in flight right
now, blockers with their exact questions, check results including failures and
skips, and the single next action.
