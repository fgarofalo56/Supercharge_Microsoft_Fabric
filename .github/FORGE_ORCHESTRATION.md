# ATLAS FORGE orchestration — the surface that actually exists

This is the single reference for multi-task, multi-session work in this
repository. The prompts and agents under `.github/prompts/` and
`.github/agents/` link here instead of each carrying their own copy of the
command list, so there is one place to correct when the CLI changes.

Every command below was verified with `atlas-forge <command> --help` against
the installed CLI before being written down. **Do not add a command or a flag
to this file that you have not just verified the same way.** If you need
something that does not exist, say so and stop — do not invent it.

---

## What replaced what

This repository previously described an "Archon + Ralph Wiggum loop" harness.
Archon was a project/task-management MCP server; it is not running, is not
installed, and is not the intended system. The Ralph loop had **no runner
behind it** — nothing shipped that could execute an iteration, which is why
every attempt to start one went in circles.

| Old idea | What to use now |
|---|---|
| Archon project / task records | GitHub issues (`gh issue`), plus `.forge/tasks.json` for the execution DAG |
| Archon knowledge-base search | `gh`, repository search, and the `microsoft-docs` / `context7` MCP servers in `.vscode/mcp.json` |
| Archon state documents | `.forge/` on disk (`dispatch-progress.json`, `runs/`, `evidence/`) |
| `/ralph-start` wizard | `atlas-forge plan` then `atlas-forge decompose` |
| `/ralph-iterate` | `atlas-forge dispatch --wave 1` |
| `/ralph-loop` background loop | `atlas-forge dispatch`, or `atlas-forge factory run` for an unattended drain |
| `/ralph-status` | `atlas-forge board`, `atlas-forge watch`, `atlas-forge factory status` |
| `/ralph-cancel` | `atlas-forge pause`, `atlas-forge cancel`, `atlas-forge factory halt` |

### `scripts/backlog_to_dag.py` is NOT shipped

You may see that script referenced in ATLAS FORGE's own documentation or in
transcripts. **It does not exist in this repository and is not part of the
installed CLI.** It is the `atlas-forge` repo's private parser for *its own*
`PRPs/CONSOLIDATED_BACKLOG.md` markdown conventions, which this repository does
not use. Do not try to run it, and do not write instructions that depend on it.

This repository's task graph comes from `atlas-forge plan` and
`atlas-forge decompose`. Nothing else writes `.forge/tasks.json`.

For the same reason, `atlas-forge drift-check` ("is `.forge/tasks.json` still
what `PRPs/CONSOLIDATED_BACKLOG.md` generates?") has no meaning here — this
repository has no `CONSOLIDATED_BACKLOG.md`.

---

## An empty board exits 1. Read this before concluding anything is broken.

`.forge/tasks.json` does not exist in this repository yet, and the two commands
that report on it **disagree about whether that is an error**. Both outputs
below were measured on 2026-09-14 in this checkout.

`atlas-forge board` calls it fine:

```console
$ atlas-forge board
board — status: ok
no tasks — /tasks add <title>
$ echo $?
0
```

`atlas-forge dispatch --dry-run` calls the *same state* an error:

```console
$ atlas-forge dispatch --dry-run
dispatch — status: error
dispatched 0/0 task(s) in 0 wave(s), 0 at once at peak
$ echo $?
1
```

```console
$ atlas-forge dispatch --dry-run --json
{
  "ok": false,
  "command": "dispatch",
  "status": "error",
  "data": {
    "outcome": "planned",
    "ok": false,
    "waves": 0,
    "peak": 0,
    "plan": [],
    "stranded": [],
    "detail": "0 tasks in 0 waves. Nothing ran."
  }
}
```

**`ok: false`, `status: "error"` and exit 1 here mean "no task graph has been
built yet."** They do not mean the install is broken, the command failed, or
FORGE is misconfigured. Nothing ran because there was nothing to run.

This is the exact shape that sent an earlier session in circles: it read the
non-zero exit as a broken tool and went looking for the missing piece, instead
of building the task graph. If you hit it, run `atlas-forge plan` and
`atlas-forge decompose` — then dry-run again.

Two related traps in the same area:

- The `/tasks add <title>` that `board` suggests is an **in-session slash
  command**, not a CLI subcommand. `atlas-forge tasks` does not exist; it exits
  with `No such command 'tasks'`.
- `board`'s `ok` only ever means "the file could be read." It is not a verdict
  on the build. `decompose` is the opposite — there, `ok` *is* the verdict.

---

## The pipeline

```
init  ->  plan  ->  decompose  ->  dispatch  ->  integrate
                        |             |
                        |             +--  factory run   (same thing, unattended, on a timer)
                        |
                        +--  writes/validates .forge/tasks.json
```

### `atlas-forge init`

Sets this repository up for FORGE: surveys first, then scaffolds `.forge/`.

```
--yes / -y                  Take every default; no prompts.
--workspace / --no-workspace  Scaffold the .forge/ layout. [default: workspace]
--repo <str>                Repository root. [default: .]
```

**This repository is already initialised** — `.forge/` exists with
`config.toml`, `hooks.json`, `mcp.json`, `agents/`, `commands/`, `personas/`,
`workflows/`, `worktrees/`. Do not re-run `init` expecting it to build a task
list; it does not create tasks.

### `atlas-forge plan "<goal>"`

Plans a change without touching anything — the planner runs read-only.

```
<goal>            (required positional) What you want done.
--repo <str>      Repository root to plan against. [default: .]
--target <str>    Target branch.
--dry-run         Return the plan without saving it.
--provider <str>  / --model <str>
--json            Emit a machine-readable JSON envelope.
```

Start with `--dry-run` and read the plan before you let it save anything.

### `atlas-forge decompose`

Holds every task to the diff-line budget. This is a **gate, not a report**: a
plan containing a task over budget exits 1 and the oversized plan is not left
on disk. With `--from`, a proposals document becomes the plan — and it is
written **only if the check passes**.

```
--repo <str>      [default: .]
--from <str>      Proposals JSON to assemble into a plan. `-` reads stdin.
--budget <int>    Max diff lines per task. 0 uses config. [default: 0]
--json            Emit a machine-readable JSON envelope.
```

The `--from` document is either `{"tasks": [...]}` or a bare list of objects
with `id`, `title`, `estimate`, `needs`, `note`.

Note that an estimate is the planner's guess about its own output. The
independent check is `git diff --numstat` re-run after the work exists, which
belongs to `integrate` — a green `decompose` is not proof the diffs stayed
small.

### `atlas-forge dispatch`

Runs the plan: every unsettled task in its own worktree on `forge/<task-id>`,
a wave at a time, each with the full gate suite. A task whose gates are red is
red. Re-running retries whatever did not settle; finished tasks are skipped.

```
--repo <str>            [default: .]
--base <str>            Commit every root task branches from. [default: HEAD]
--parallel <int>        Tasks at once. 0 uses the default. [default: 0]
--mode <str>            Permission mode for each task's agent. [default: auto]
--provider <str> / --model <str>
--resume                Carry the plan's earlier spend into this run's ceiling.
--max-usd <float>       Ceiling for the whole run. 0 means no ceiling. [default: 0.0]
--task-usd <float>      Ceiling for one task across its attempts. [default: 0.0]
--task-minutes <float>  Wall-clock ceiling for one task. [default: 90.0]
--watch                 Follow the run already in flight instead of starting one.
--phase <str>           Run only this phase.
--wave <int>            Run at most this many waves, then stop. 0 runs them all. [default: 0]
--dry-run               Print the wave plan and run nothing.
--json                  Emit a machine-readable JSON envelope.
```

`dispatch` reads `<root>/.forge/tasks.json`. **That file does not exist in this
repository today.** See [An empty board exits 1](#an-empty-board-exits-1-read-this-before-concluding-anything-is-broken)
below before you read anything into that.

Use `--resume` when restarting a killed run, or every restart gets a fresh
`--max-usd` and the plan can spend a multiple of its ceiling without ever
exceeding it once.

### `atlas-forge integrate`

Merges every finished task's branch onto one integration branch, in dependency
order, and re-checks the real diff sizes against the budget.

```
--repo <str>      [default: .]
--branch <str>    Integration branch name. Never reused.
--budget <int>    Max diff lines per task. 0 uses config. [default: 0]
--json            Emit a machine-readable JSON envelope.
```

---

## The unattended drain

`atlas-forge factory` is the dark factory: drain the backlog unattended on a
timer. It is the *same* execution machinery as `dispatch`, wrapped in a
supervisor loop with a kill file.

| Subcommand | What it does | Verified flags |
|---|---|---|
| `factory tick` | One bounded cycle: preflight, one wave of at most `lanes` rows, validate, merge, settle. | `--repo`, `--dry-run`, `--parallel`, `--only`, `--json` |
| `factory run` | Tick until the board is drained or something says stop. | `--repo`, `--interval`, `--parallel`, `--only`, `--max-ticks`, `--json` |
| `factory status` | Commits landed first, then whether the supervisor is actually alive. | `--repo`, `--json` |
| `factory halt` | Stop the factory: a local kill file every tick checks first. | `--repo`, `--reason`, `--json` |
| `factory resume` | Remove the halt file so the next tick runs. Reports whether there was one. | `--repo`, `--json` |
| `factory requeue` | Return every `doing` row with no live lane process to `todo`. | `--repo`, `--dry-run`, `--json` |

`--only` takes comma-separated row ids and is per-invocation, never from
config. A named row that is not ready is reported and never dispatched.

Read `factory status` carefully: it reports landed commits *and* supervisor
liveness separately, because those two can disagree.

---

## Observing a run

| Command | Answers | Verified flags |
|---|---|---|
| `atlas-forge board` | The task graph as columns — blocked, ready, doing, done, failed, dropped, blocked_on_human. | `--repo`, `--width`, `--json` |
| `atlas-forge watch` | Follow the `dispatch` run already in flight in this repository. | `--repo`, `--json` |
| `atlas-forge status` | Everything about this workspace's newest session, without opening it. | `--repo`, `--json` |
| `atlas-forge blocked` | Every task waiting on a person, and the exact question. | `--repo`, `--json` |
| `atlas-forge issues` | Where the task DAG and the GitHub issues disagree. | `--repo`, `--json` |
| `atlas-forge adopt` | Survey this repository and rank what is worth doing. Changes nothing. | `--repo`, `--json` |
| `atlas-forge replay` | One dispatch wave, replayed: what it ran, on what, and where the proof is. | (verify before use) |

`board`'s `ok` means "the file could be read" — unlike `decompose`, where `ok`
is the verdict itself. Do not read a green `board` as a green build.

`watch` does not start anything. The progress lives on disk
(`.forge/dispatch-progress.json`), so an overnight run started detached can be
watched afterwards, from anywhere, as many times as you like.

---

## Stopping a run

| Command | Effect |
|---|---|
| `atlas-forge pause [run_id]` | Ask an in-flight `dispatch` to stop at its next **wave boundary**. `--json`. |
| `atlas-forge cancel [run_id]` | Ask an in-flight `dispatch` to stop and not resume automatically. `--json`. |
| `atlas-forge factory halt --reason "<why>"` | Write the kill file the next factory tick checks first. |
| `atlas-forge factory requeue` | After a halt, return abandoned `doing` rows to `todo`. `--dry-run` counts first. |

**Cancelling never means reverting.** Do not run `git checkout .`,
`git restore`, `git clean`, or `git stash` to "clean up" after a cancelled run.
A failed task deliberately keeps its worktree so the work is still there to
read. Destroying it destroys the evidence and, in a repository with
uncommitted work, destroys unrelated work as well. See the safety rules below.

---

## Safety rules for this repository

These are not general advice; they are specific to the state this checkout is
in, and they override any convenience step a prompt suggests.

1. **The working tree is dirty and the dirt is real work.** There are hundreds
   of modified and untracked files representing unreviewed changes. `dispatch`
   and `factory` branch from `HEAD` and merge finished branches back; a drain
   run over a dirty tree will interleave unreviewed work with generated work
   and make the result unreviewable. **Triage the working tree before running
   any drain.**

2. **Never run `git checkout --`, `git restore`, `git clean`, or `git stash`.**
   `git stash` in particular is shared across worktrees on this machine and
   other sessions pop it. No prompt in this repository may instruct these.

3. **There are three worktrees.** The main checkout plus two under `temp/`,
   one of which has an in-progress merge. Leave worktrees you did not create
   alone; `atlas-forge worktree` manages only FORGE's own.

4. **Do not commit or push on the operator's behalf** unless the current task
   explicitly authorises it. Leave edits uncommitted and report them.

5. **A prompt being read is not a runner being started.** Never report a
   dispatch, a factory, or a loop as running because you read instructions that
   describe one. Report what `factory status` / `watch` / `board` actually
   printed.

---

## Where task work should actually come from

Until a task graph exists, there is nothing for `dispatch` to run. Candidate
sources, in the order worth measuring:

- **Open GitHub issues and PRs** — `gh issue list`, `gh pr list`. Durable
  across sessions; `atlas-forge issues` reconciles them against the DAG.
- **The uncommitted working tree** — triage first; see safety rule 1.
- **Unticked items in `PRPs/plans/*.md`** — the phase plans in this repository
  carry checkbox lists.
- **`TODO` / `FIXME` markers** in source and notebooks.
- **Failing and skipped tests** — a skip is an untested claim.

Turn the chosen items into a plan with `atlas-forge plan`, hold them to budget
with `atlas-forge decompose`, and only then `dispatch`.
