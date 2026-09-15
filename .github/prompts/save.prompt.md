---
description: Save current session context as a checkpoint without ending session
---

# Save Checkpoint

Save the current session state without ending the session.

## Save Operations

### 1. Record a checkpoint on the GitHub issue

There is no external task-management service. The durable record is the issue
for the work item:

```bash
gh issue comment <n> --body "Checkpoint <timestamp>

Focus: <what we are working on>
Progress: <what has been done, with the commands run and their actual results>
Next: <what remains>
Discoveries: <...>
Blockers: <...>"
```

Reuse the existing issue; do not open a new one per checkpoint. If `gh` is
unavailable, say the checkpoint could not be recorded durably.

### 2. Snapshot the task graph (if one exists)

```bash
atlas-forge board --json
atlas-forge blocked --json
```

FORGE keeps its own run state on disk under `.forge/` — `dispatch-progress.json`,
`runs/`, `evidence/`. You do not need to copy it anywhere.

### 3. Git Status Check

```bash
git status -sb
```

If there are significant changes worth committing:

```bash
git add -A
git commit -m "wip: [description of current work]"
```

## Confirmation

```markdown
## ✅ Checkpoint Saved

### 📝 Session Memory Updated

- Focus: [current focus]
- Progress: [what's done]
- Next: [what's remaining]

### 📋 Task Status

- [Task]: [status/progress]

### 🌿 Git State

- Uncommitted changes: [yes/no]
- Last commit: [if made]

### ⏰ Checkpoint Time

[timestamp]

---

_Session continues. Use `/end` when finished._
```

This is a checkpoint, not end of session. Work can continue.

{input}
