---
description: Get current project status briefing - tasks, git state, blockers
---

# Project Status Briefing

Provide a comprehensive status update on the current project.

## Check Current State

### 1. Task Status

There is no external task-management service. Read what exists:

```bash
atlas-forge board --json       # ready / doing / done / failed / blocked_on_human
atlas-forge blocked --json     # tasks waiting on a person, and the exact question
atlas-forge issues --json      # where the task graph and GitHub issues disagree
gh issue list --state open
gh pr list --state open
```

`0 tasks in 0 waves` from `atlas-forge dispatch --dry-run` means
`.forge/tasks.json` has not been written; it exits 1 with `status: "error"`
while `board` calls the same state `status: ok` / `no tasks`. `board`'s `ok`
means the file could be read; it is not a build verdict.

### 2. Git Status

```bash
git status -sb
git log --oneline -5
git branch --show-current
git stash list
```

### 3. Check for Issues

- Any failing tests or builds
- Uncommitted changes
- Stashed work

## Status Report

```markdown
## 📊 Current Status

### 🌿 Git State

- **Branch**: [current branch]
- **Tracking**: [ahead/behind status]
- **Uncommitted Changes**: [list or "clean"]
- **Stashes**: [count]

### 📋 Tasks and Issues

| Status        | Count | Top Items |
| ------------- | ----- | --------- |
| Doing         | X     | [list]    |
| Review        | X     | [list]    |
| Todo          | X     | [top 3]   |
| Done (recent) | X     | [last 3]  |

Give totals only for the inventory you actually reconciled, and name any source
you could not read.

### ⚠️ Blockers

- [Any blocking issues]

### 💡 Recent Activity

- [What was done this session]

### 🎯 Recommended Next Steps

1. [Immediate priority]
2. [Secondary priority]
3. [If time permits]
```

Keep the report concise but complete.

{input}
