---
name: ralph-iterate
description: Run one wave of the task graph with atlas-forge dispatch --wave 1. Replaces the retired Archon/Ralph manual iteration.
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

Execute a single, bounded wave of the task graph and stop, so a human can read
the result before the next one starts.

> **This is no longer a "Ralph iteration."** There was never a runner behind
> that loop, and its state lived in an Archon MCP server that is not running.
> The real surface is [ATLAS FORGE orchestration](../FORGE_ORCHESTRATION.md).
> Do not use a flag it has not verified.

## Preconditions

1. A task graph must exist. `atlas-forge dispatch --dry-run` reporting
   `0 tasks in 0 waves` means `.forge/tasks.json` is missing — that is an empty
   graph, not a failure. Run `/ralph-start` first.
2. Read the safety rules in [ATLAS FORGE orchestration](../FORGE_ORCHESTRATION.md).
   `dispatch` branches every root task from `--base` (default `HEAD`) and merges
   finished branches back. Over a dirty tree that interleaves unreviewed work
   with generated work. Confirm with the operator before running against a
   dirty checkout.
3. Check nothing is already in flight:

   ```bash
   atlas-forge watch --json     # follows a run already running; starts nothing
   atlas-forge board --json
   ```

## Dry run first

```bash
atlas-forge dispatch --dry-run --json
```

This prints the wave plan and runs nothing. Read which tasks are in wave 1 and
confirm they are the ones you meant.

## Run one wave

```bash
atlas-forge dispatch --wave 1 --json
```

`--wave N` runs at most N waves and then stops; `0` runs them all. Each task
gets an isolated checkout on `forge/<task-id>`, its own agent, and **the full
gate suite** — a task whose gates are red is red, because the next thing that
happens to its branch is a merge into everything else.

Useful verified options:

| Flag | Meaning |
|---|---|
| `--wave <int>` | Run at most this many waves, then stop. 0 runs them all. |
| `--parallel <int>` | Tasks at once. 0 uses the default. |
| `--base <str>` | Commit every root task branches from. Default `HEAD`. |
| `--phase <str>` | Run only this phase. Refuses if it depends on unsettled work. |
| `--max-usd <float>` | Ceiling for the whole run. 0 means no ceiling. |
| `--task-usd <float>` | Ceiling for one task across its attempts. |
| `--task-minutes <float>` | Wall-clock ceiling for one task. Default 90. |
| `--resume` | Carry the plan's earlier spend into this run's ceiling. |
| `--mode <str>` | Permission mode for each task's agent. Default `auto`. |
| `--dry-run` | Print the wave plan and run nothing. |

Use `--resume` on any restart of a killed run. Without it every restart gets a
fresh `--max-usd`, so a plan killed and restarted through the night can spend a
multiple of its ceiling without ever exceeding it once.

Re-running the command retries whatever did not settle. Finished tasks are
skipped. A failed task **keeps its worktree** so the work is still there to
read — do not delete it.

## After the wave

```bash
atlas-forge board --json      # columns: blocked, ready, doing, done, failed, dropped, blocked_on_human
atlas-forge blocked --json    # every task waiting on a person, and the exact question
```

`board`'s `ok` only means the file could be read. It is not a green build.

Merging finished branches is a separate step and is not run from here:

```bash
atlas-forge integrate --branch <new-branch-name> --json
```

## Do not

- Do not commit, push, merge, or deploy on the operator's behalf unless the
  current task explicitly authorises it.
- Do not run `git checkout .`, `git restore`, `git clean`, or `git stash`.
- Do not invent `--verbose` or `--skip-commit`; they are not flags on
  `dispatch`.
- Do not report a wave as complete because the command was issued. Report what
  `board` and the dispatch envelope actually printed, including failures and
  skips.

## Report

Wave number, tasks attempted, tasks settled, tasks failed with their branch
names and worktree paths, anything now `blocked_on_human` with its question,
spend against ceiling, and the next action.
