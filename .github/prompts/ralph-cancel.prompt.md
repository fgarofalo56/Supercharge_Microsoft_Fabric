---
name: ralph-cancel
description: Stop an in-flight atlas-forge dispatch or factory run without destroying work.
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

Stop work that is in flight, preserving everything it produced.

> The previous version of this prompt updated Archon documents and offered a
> `--cleanup` flag that ran `git checkout .` and `git clean -fd`. **Archon is
> not running, and those two commands would have destroyed hundreds of
> uncommitted files in this checkout.** Both are gone. See
> [ATLAS FORGE orchestration](../FORGE_ORCHESTRATION.md).

## First, find out what is actually running

```bash
atlas-forge board --json
atlas-forge factory status --json
atlas-forge watch --json          # follows a live run; starts nothing
```

`.forge/dispatch-progress.json` carries `finished`, `in_flight`, and the wave
counters. If nothing is in flight, say so and stop — there is nothing to
cancel.

## Stopping a `dispatch` run

| Command | Effect |
|---|---|
| `atlas-forge pause [run_id] --json` | Stop at the next **wave boundary**. In-flight tasks finish. |
| `atlas-forge cancel [run_id] --json` | Stop and do not resume automatically. |

Prefer `pause` when the current wave is doing useful work — letting it reach a
boundary leaves the graph in a cleaner state to resume from.

## Stopping a `factory` drain

```bash
atlas-forge factory halt --reason "<why, for the next person>" --json
```

This writes a local kill file that every tick checks first. Give a real reason;
it goes into the handoff.

To undo it later:

```bash
atlas-forge factory resume --json     # reports whether there was a halt file
```

After a halt, rows can be left in `doing` with no live lane process behind
them. Count them before changing anything:

```bash
atlas-forge factory requeue --dry-run --json   # counts stale rows, writes nothing
atlas-forge factory requeue --json             # returns them to todo
```

## Never, under any circumstances

These are prohibited in this repository. The working tree holds hundreds of
uncommitted files that represent real unreviewed work, and there are three
worktrees, one with an in-progress merge.

- `git checkout --` / `git checkout .`
- `git restore`
- `git clean` (any flags)
- `git stash` — the stash stack is shared across worktrees on this machine and
  other sessions pop it
- Deleting a failed task's worktree

**Cancelling is not reverting.** A failed or cancelled task deliberately keeps
its worktree so the work is still there to read. That is the evidence. If the
operator genuinely wants changes discarded, that is their decision to make
explicitly, on named paths, not a `--cleanup` flag on a stop command.

Do not commit or push as part of cancelling.

## Report

What was in flight, which stop command was issued and its actual output,
whether the run has confirmed stopped (re-read `factory status` / the progress
file — do not assume), how many rows were left in `doing`, which worktrees and
branches now hold unmerged work and where they are, and what the operator's
options are for resuming:

- Resume the drain: `atlas-forge factory resume`
- Run another wave by hand: `/ralph-iterate`
- See the state: `/ralph-status`
