---
description: Execute end of session protocol - record the handoff, report state, do not auto-commit
---

# End of Session Protocol

Execute the complete end-of-session checklist to save all work and state.

## End Session Steps

### 1. Record the handoff on the GitHub issue

There is no external task-management service. The durable record is the issue:

```bash
gh issue comment <n> --body "<branch, commit, dirty paths, commands run and
their actual results, remaining acceptance criteria, blockers, next action>"
```

Reuse the existing issue for the work item rather than opening a new one. If
`gh` is unavailable, say the handoff could not be recorded — do not treat a
local note as a durable record.

### 2. Reconcile the task graph, if there is one

```bash
atlas-forge board --json      # ready / doing / done / failed / blocked_on_human
atlas-forge blocked --json    # who is waiting on a person, and the question
atlas-forge issues --json     # where the DAG and the issues disagree
```

### 3. Git Operations

**Report the state; do not commit on the operator's behalf.**

```bash
git status --porcelain | wc -l
git status --porcelain
git worktree list
```

This checkout carries a large amount of uncommitted, unreviewed work across
several worktrees. `git add -A` would sweep unrelated changes into one
unreviewable commit, so it is **not** part of this protocol. Commit only when
the operator asks, only the paths they name, and never push unless explicitly
requested.

**Never** run `git checkout --`, `git restore`, `git clean`, or `git stash`. The
stash stack is shared across worktrees on this machine and other sessions pop
it.

### 4. Provide Session Summary

```markdown
## 📋 Session Summary

### ⏱️ Work Completed

- [List of completed items]

### 🚧 Work In Progress

- [List of WIP items with status]

### 💡 Discoveries & Decisions

- [New discoveries made]
- [Decisions documented]

### ❌ Issues Encountered

- [Any blockers or failed attempts]

### 📁 Files Modified

- [Key files changed]

### 🎯 Recommended Next Session Focus

1. [Priority 1]
2. [Priority 2]
3. [Priority 3]

### ✅ Checklist

- [ ] Handoff recorded on the GitHub issue
- [ ] Task graph reconciled (`board`, `blocked`, `issues`)
- [ ] Working-tree state reported, not swept into a commit
- [ ] Nothing pushed without an explicit request
```

Confirm all updates have been made.

{input}
