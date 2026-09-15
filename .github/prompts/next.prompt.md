---
description: Determine what to work on next from GitHub issues and the atlas-forge task graph
---

# What's Next?

Analyze current state and provide options for what to work on next.

## Check Current Context

There is no external task-management service. Read what exists:

### 1. In-Progress Work

```bash
atlas-forge board --json            # the "doing" column
gh issue list --state open --assignee @me
```

### 2. Pending Tasks

```bash
gh issue list --state open
atlas-forge board --json            # the "ready" column
```

### 3. Blockers

```bash
atlas-forge blocked --json          # each task waiting on a person, and the question
gh pr list --state open             # anything stuck awaiting review
```

### 4. Recent Context

The last handoff is a comment on the relevant GitHub issue:

```bash
gh issue view <n> --comments
```

`0 tasks in 0 waves` from `atlas-forge dispatch --dry-run` means
`.forge/tasks.json` has not been written. It exits 1 with `status: "error"`,
while `board` calls the same state `status: ok` / `no tasks` — read it as "no
graph built yet". If `gh` is unavailable, report the inventory as **blocked**
rather than guessing.

## Provide Options

```markdown
## 🎯 What Should I Work On Next?

### Option A: Continue Previous Work

**Task**: [In-progress task title]
**Status**: [Current progress]
**Next Action**: [Specific next step]
**Estimated Time**: [X minutes/hours]

---

### Option B: New Priority Items

**Ranked by importance:**

1. **[Task Title]** (Priority: X/100)
   - Why: [Reason for priority]
   - Action: [First step]
   - Time: [Estimate]

2. **[Task Title]** (Priority: X/100)
   - Why: [Reason]
   - Action: [First step]
   - Time: [Estimate]

3. **[Task Title]** (Priority: X/100)
   - Why: [Reason]
   - Action: [First step]
   - Time: [Estimate]

---

### Option C: Maintenance Tasks

- [ ] Documentation updates needed
- [ ] Test coverage improvements
- [ ] Refactoring opportunities
- [ ] Dependency updates

---

### ⚠️ Blockers to Resolve First

- [Any blockers that should be addressed]

---

**My Recommendation**: [Option X] because [reason]
```

Be specific about what the next action would be for each option.

{input}
