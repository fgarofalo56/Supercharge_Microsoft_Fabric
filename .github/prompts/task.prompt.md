---
description: Create or manage work items as GitHub issues and atlas-forge tasks
---

# Manage Tasks

Create, update, or manage work items for the current project.

> There is no external task-management service. **Durable** work items are
> GitHub issues. The **execution** graph is `.forge/tasks.json`, written only by
> `atlas-forge plan` and `atlas-forge decompose` — never by hand, and never by
> `scripts/backlog_to_dag.py`, which is not shipped in this repository. See
> [ATLAS FORGE orchestration](../FORGE_ORCHESTRATION.md).

## Task Operations

### List

```bash
gh issue list --state open
gh issue list --state open --label bug
gh issue list --search "authentication"

atlas-forge board --json       # the execution graph, by column
atlas-forge blocked --json     # waiting on a person, with the question
atlas-forge issues --json      # where the graph and the issues disagree
```

### Create

```bash
gh issue create --title "<verb + object>" --label "<area>" --body "<description>

## Acceptance criteria
- [ ] ...
- [ ] ..."
```

Search before you create — reuse an existing issue rather than duplicating it.

### Update

```bash
gh issue comment <n> --body "<progress, commands run, actual results, next action>"
gh issue edit <n> --add-label "blocked"
gh issue close <n> --comment "<what settled it, and the evidence>"
```

An issue is not done because a phrase says so. Close it on evidence: the
implementation, the executed check and its output, and an independent review.

### Put work into the execution graph

```bash
atlas-forge plan "<goal>" --dry-run     # read-only
atlas-forge decompose                   # a GATE: over-budget tasks exit 1
atlas-forge dispatch --dry-run          # preview the waves
```

Bind acceptance criteria to a task so "done" is checkable rather than asserted
(verify these subcommand surfaces with `--help` before scripting them):

```bash
atlas-forge spec --help     # new / add / list / show / compile / defer / verify
atlas-forge story --help    # assign / list / verify
```

### Delete

Do not delete work items. Close the issue with a reason, so the decision
survives.

## Task Guidelines

| Aspect          | Guideline                       |
| --------------- | ------------------------------- |
| **Size**        | 30 min - 4 hours of work, and within the `decompose` diff-line budget |
| **Title**       | Action-oriented (verb + object) |
| **Description** | Include acceptance criteria     |
| **Priority**    | Labels and milestones           |
| **Status Flow** | todo → doing → review → done    |

## Task Templates

**Feature Task:**

```
Title: Implement [feature name]
Description:
- [ ] Design the approach
- [ ] Implement core logic
- [ ] Add error handling
- [ ] Write tests
- [ ] Update documentation
```

**Bug Fix Task:**

```
Title: Fix [bug description]
Description:
- [ ] Reproduce the issue
- [ ] Identify root cause
- [ ] Implement fix
- [ ] Add regression test
- [ ] Verify fix
```

**Refactor Task:**

```
Title: Refactor [component]
Description:
- [ ] Analyze current implementation
- [ ] Plan refactoring approach
- [ ] Implement changes
- [ ] Ensure tests pass
- [ ] Update documentation
```

## Arguments

{input}

- `list`: Show open issues and the board
- `todo`: Show ready work
- `doing`: Show in-progress work
- `create <title>`: Open a new GitHub issue
- `done <issue-number>`: Close an issue, with the evidence that settled it
- `<issue-number>`: Show that issue and its latest handoff
