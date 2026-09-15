---
description: Execute the mandatory startup checklist before beginning work
---

# Session Start Protocol

Execute the complete startup checklist before we begin any work.

## Startup Steps

### 1. Load Project Context

- Check for `.github/copilot-instructions.md` and read it
- Check for any project-specific configuration files

### 2. Load Task Context

There is no external task-management service. Read the sources that exist:

```bash
gh issue list --state open          # durable work items
gh pr list --state open             # anything awaiting review
atlas-forge board --json            # the task graph, if one exists
atlas-forge blocked --json          # anything waiting on a person
atlas-forge status --json           # this workspace's newest session
```

If `atlas-forge dispatch --dry-run` says `0 tasks in 0 waves`, that means
`.forge/tasks.json` has not been written. It exits 1 with `status: "error"`,
while `board` calls the same state `status: ok` / `no tasks` — read it as "no
graph built yet". If `gh` is unavailable, report the inventory as **blocked**
rather than guessing.

### 3. Review Git Status

Check what has changed:

```bash
git status
git log --oneline -5
git branch --show-current
```

### 4. Check for Blockers

- Review any tasks marked as blocked
- Check for failing tests or builds
- Note any pending PRs needing attention

### 5. Project Status Briefing

Provide a structured briefing:

```markdown
## 📊 Project Status Briefing

### Current State

- **Branch**: [current branch]
- **Last Commit**: [commit message]
- **Uncommitted Changes**: [yes/no - list if any]

### Open Work

- **In Progress**: [from `atlas-forge board` "doing", and assigned open issues]
- **Blocked**: [from `atlas-forge blocked` — include the exact question]
- **Ready (Todo)**: [top 3]

### Session Memory

- **Last Session Focus**: [from the latest handoff comment on the relevant issue]
- **Decisions Made**: [list]
- **Blockers**: [list]

### 🎯 Recommended Next Steps

1. [Option A - Continue previous work]
2. [Option B - New priority items]
3. [Option C - Maintenance tasks]
```

Do not skip any steps. Actually execute the commands, don't just describe them.

{input}
