---
name: ralph-start
description: Build a task graph for this repository with atlas-forge plan and decompose. Replaces the retired Archon/Ralph loop wizard.
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

Turn a goal into a validated task graph that `atlas-forge dispatch` can run.

> **This prompt no longer starts a "Ralph Wiggum loop."** That loop was
> described by these files but never had a runner behind it, and its state
> lived in an Archon MCP server that is not running and not installed. The name
> is kept only so existing links keep working. The real surface is documented
> in [ATLAS FORGE orchestration](../FORGE_ORCHESTRATION.md) — read it before
> running anything here, and do not use a flag it has not verified.

## Before you plan

1. Read [ATLAS FORGE orchestration](../FORGE_ORCHESTRATION.md), especially the
   safety rules. This checkout has a large amount of uncommitted work and three
   worktrees.
2. Run `git status --porcelain | wc -l`. If the tree is dirty, say so and
   confirm with the operator before going further. Do **not** run
   `git checkout --`, `git restore`, `git clean`, or `git stash` to tidy it.
3. Check what already exists:

   ```bash
   atlas-forge board --json
   atlas-forge dispatch --dry-run
   ```

   `0 tasks in 0 waves` means `.forge/tasks.json` has not been written yet.
   `dispatch --dry-run` reports that as `ok: false`, `status: "error"` and
   **exit 1**, while `board` reports the same state as `status: ok` / `no
   tasks`. The exit 1 means "no graph built yet", not that the command failed.

## Plan

Read-only. Nothing is written without `--dry-run` being dropped deliberately.

```bash
atlas-forge plan "<goal>" --dry-run --json
```

Read the plan out loud to the operator before saving it. Then, if it is right:

```bash
atlas-forge plan "<goal>" --json
```

Verified options: `--repo`, `--target`, `--dry-run`, `--provider`, `--model`,
`--json`.

## Decompose

`decompose` is a **gate**, not a report. A plan with any task over the
diff-line budget exits 1, and the oversized plan is not left on disk.

```bash
atlas-forge decompose --json
```

If it exits 1, it names each offending task and how many pieces it needs. Split
those tasks and re-run. Do not raise `--budget` to make the gate pass.

To assemble a proposals document into the plan instead:

```bash
atlas-forge decompose --from proposals.json --json
```

The document is `{"tasks": [...]}` or a bare list of objects with `id`,
`title`, `estimate`, `needs`, `note`. It is written only if the check passes.

Verified options: `--repo`, `--from`, `--budget`, `--json`.

## Do not

- Do not invent a `--quick`, `--auto`, `--max-iterations`, `--resume` or
  `--mode` flag on `plan` or `decompose`. The verified flag lists are above.
- Do not write `.forge/tasks.json` by hand, and do not look for
  `scripts/backlog_to_dag.py` — **it is not shipped in this repository.** It is
  the atlas-forge repo's own parser for its own markdown conventions.
- Do not start `dispatch` or `factory` from this prompt. Planning and running
  are separate steps on purpose.

## Report

State the goal, whether the tree was clean, the plan as `plan` returned it, the
`decompose` verdict and exit code, and the resulting task count from
`atlas-forge board`. Then hand off:

- Run one wave: `/ralph-iterate`
- Check progress: `/ralph-status`
- Stop something in flight: `/ralph-cancel`
