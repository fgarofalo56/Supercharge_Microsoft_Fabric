---
name: prp-ralph
description: Turn a PRP plan into an atlas-forge task graph and run it wave by wave.
mode: agent
tools:
  - filesystem
  - terminal
handoffs:
  - label: Run a wave
    agent: ralph-loop
    prompt: Run one wave of the dispatch graph for this PRP plan
  - label: View Plan
    agent: prp-orchestrator
    prompt: View the current PRP plan
---

## User Input

```text
$ARGUMENTS
```

## Purpose

Combine Ralph Wiggum's iterative persistence with PRP Framework's structured plan execution for enhanced implementation reliability.

## Integration Concept

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RALPH + PRP                                      │
│                                                                     │
│    PRD ─────────────────────────────────────────────────────┐       │
│    │                                                         │       │
│    │  Problem Statement → Phases → Success Criteria         │       │
│    │                                                         │       │
│    └─────────────────────────────────────────────────────────┘       │
│                           │                                          │
│                           ▼                                          │
│    PLAN ────────────────────────────────────────────────────┐       │
│    │                                                         │       │
│    │  Tasks → Patterns → Validation → Acceptance            │       │
│    │                                                         │       │
│    └─────────────────────────────────────────────────────────┘       │
│                           │                                          │
│                           ▼                                          │
│    ┌──────────────────────────────────────────────────────────┐     │
│    │  RALPH LOOP                                               │     │
│    │                                                           │     │
│    │  For each task in plan:                                  │     │
│    │    1. Execute task following patterns                    │     │
│    │    2. Run validation commands                            │     │
│    │    3. Mark task complete in plan                         │     │
│    │    4. All tasks done? → COMPLETE                         │     │
│    │    5. Else → Continue iteration                          │     │
│    │                                                           │     │
│    └──────────────────────────────────────────────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Execution Flow

### 1. Locate Plan

```bash
# Get plan path from arguments
PLAN_PATH="$ARGUMENTS"

# If not provided, check for active plan
if [ -z "$PLAN_PATH" ]; then
    PLAN_PATH=$(ls -t PRPs/plans/*.plan.md | head -1)
fi

# Verify plan exists
cat "$PLAN_PATH"
```

### 2. Parse Plan

Extract from plan.md:
- Summary and user story
- Patterns to mirror
- Files to change
- Step-by-step tasks
- Validation commands
- Acceptance criteria

### 3. Turn the plan into a FORGE task graph

> **`.ralph/config.json` is dead.** Nothing reads it — there was never a runner
> behind the Ralph loop, and the `archon_project_id` / `archon_task_id` it
> carried pointed at an MCP server that is not running. The execution state is
> `.forge/tasks.json`, and the only things that write it are `atlas-forge plan`
> and `atlas-forge decompose`. **`scripts/backlog_to_dag.py` is not shipped in
> this repository.** Verified command surface:
> [ATLAS FORGE orchestration](../FORGE_ORCHESTRATION.md).

Parse the plan's tasks into a proposals document — either `{"tasks": [...]}` or
a bare list of objects with `id`, `title`, `estimate`, `needs`, `note`, where
`needs` carries the plan's phase ordering:

```json
{"tasks": [
  {"id": "p1-t1", "title": "<task from the plan>", "estimate": 80,
   "needs": [], "note": "<acceptance criteria from the plan>"}
]}
```

Then assemble and gate it:

```bash
atlas-forge decompose --from proposals.json --json
```

`decompose` is a **gate, not a report**. If any task exceeds the diff-line
budget it exits 1, names each offender and how many pieces it needs, and the
oversized plan is **not** written to disk. Split those tasks in the PRP plan and
re-run. Never raise `--budget` to make it pass.

Verified options: `--repo`, `--from`, `--budget`, `--json`.

### 4. Run it

```bash
atlas-forge dispatch --dry-run --json    # print the wave plan, run nothing
atlas-forge dispatch --wave 1 --json     # one wave; each task its own worktree + full gates
atlas-forge board --json                 # what settled, what failed, what is blocked
```

There is no `max_iterations` and no `completion_promise`. A task settles when
its **gates pass on its own branch**; a task whose gates are red is red. Bound a
run with the verified flags instead: `--wave`, `--parallel`, `--max-usd`,
`--task-usd`, `--task-minutes` (default 90), `--phase`. Use `--resume` on any
restart or the spend ceiling resets.

Merge finished branches in dependency order, as a separate step:

```bash
atlas-forge integrate --branch <new-branch-name> --json
```

`integrate` re-runs the budget over the real `git diff --numstat`, which is the
half of the check that the planner's own estimate cannot talk past.

Before any of this: `dispatch` branches from `HEAD` and merges finished branches
back, so **do not point it at a dirty tree**. This checkout holds hundreds of
uncommitted files. Triage with the operator first, and never with
`git checkout --`, `git restore`, `git clean`, or `git stash`.

### 5. Generate Plan-Aware Prompt

```markdown
# Ralph Loop: PRP Plan Execution

## Plan
**Path**: [PLAN_PATH]
**Feature**: [FEATURE_NAME]

## Summary
[From plan]

## User Story
[From plan]

## Patterns to Mirror
[From plan - actual code patterns with file:line references]

## Tasks to Complete

[Task list from plan with checkboxes]

## Per-Iteration Protocol

### 1. Check Plan Status
Review which tasks are done, find next incomplete task.

### 2. Execute Task
Following PRP methodology:
- ACTION: What to do
- MIRROR: Code patterns to follow
- VALIDATE: Commands to run

### 3. Run Validation
```bash
[VALIDATION_COMMANDS]
```

### 4. Update Plan
If task passes:
- Mark task checkbox as complete [x]
- Add timestamp and notes

### 5. Completion Check
- All plan tasks complete? → <promise>PLAN_COMPLETE</promise>
- Tasks remaining? → Continue to next task

## Validation Commands
```bash
[From plan]
```

## Acceptance Criteria
[From plan - checkboxes]

## Escape Hatch
If stuck on a task for 3 iterations:
1. Document blocker in plan
2. Mark task as [BLOCKED]
3. Move to next task or <promise>BLOCKED</promise>
```

### 5. Start Ralph Loop

```bash
& @ralph-loop --config .ralph/config.json
```

## Plan Task Tracking

### During Iteration

Ralph tracks progress in the plan file:

```markdown
## Step-by-Step Tasks

### Task 1: Set up database schema ✅
- ACTION: Create migration file
- MIRROR: `src/db/migrations/001_users.sql:1-30`
- VALIDATE: `npm run migrate`
- **Status**: Complete (Iteration 2)
- **Commit**: abc123

### Task 2: Implement API endpoints ✅
- ACTION: Create CRUD handlers
- MIRROR: `src/api/users.ts:15-45`
- VALIDATE: `npm test -- --grep "API"`
- **Status**: Complete (Iteration 4)
- **Commit**: def456

### Task 3: Add input validation 🔄
- ACTION: Add Zod schemas
- MIRROR: `src/validators/user.ts:1-20`
- VALIDATE: `npm test -- --grep "validation"`
- **Status**: In Progress (Iteration 5)

### Task 4: Write integration tests ⏳
- ACTION: Create test suite
- MIRROR: `tests/integration/users.test.ts`
- VALIDATE: `npm run test:integration`
- **Status**: Pending
```

## Commands

```bash
# Start Ralph with specific plan
/prp-ralph PRPs/plans/auth-feature.plan.md

# Auto-detect most recent plan
/prp-ralph

# With options
/prp-ralph --max-iterations 20 --mode background

# Check status
/prp-ralph --status
```

## Report Generation

On completion, Ralph creates an implementation report:

```markdown
# Implementation Report: [FEATURE_NAME]

## Summary
Successfully implemented [FEATURE] following PRP plan.

## Plan Reference
- Plan: PRPs/plans/auth-feature.plan.md
- PRD: PRPs/prds/auth-feature.prd.md (if exists)

## Execution Stats
| Metric | Value |
|--------|-------|
| Total Iterations | 8 |
| Duration | 45m |
| Tasks Completed | 5/5 |
| Files Changed | 12 |
| Tests Added | 15 |

## Tasks Completed
1. ✅ Set up database schema (Iteration 2)
2. ✅ Implement API endpoints (Iteration 4)
3. ✅ Add input validation (Iteration 6)
4. ✅ Write integration tests (Iteration 7)
5. ✅ Update documentation (Iteration 8)

## Validation Results
- Build: ✅ Pass
- Unit Tests: ✅ 45/45
- Integration: ✅ 12/12
- Lint: ✅ Clean

## Files Changed
| File | Action | Lines |
|------|--------|-------|
| src/api/auth.ts | Created | +120 |
| src/db/migrations/002_auth.sql | Created | +35 |
| tests/auth.test.ts | Created | +200 |
| ... | ... | ... |

## Acceptance Criteria
- [x] User can register with email
- [x] User can log in
- [x] Sessions are managed properly
- [x] Passwords are hashed securely

## Next Steps
- Create PR: `/pr-create`
- Review changes: `git diff main`

---
Generated: [TIMESTAMP]
Ralph Loop: [LOOP_ID]
```

## Output

```markdown
## 🔄 Ralph + PRP Integration Started

### Plan
- Path: PRPs/plans/auth-feature.plan.md
- Feature: User Authentication
- Tasks: 5

### Task Status
| # | Task | Status |
|---|------|--------|
| 1 | Database schema | ✅ Done |
| 2 | API endpoints | ✅ Done |
| 3 | Input validation | 🔄 Current |
| 4 | Integration tests | ⏳ Pending |
| 5 | Documentation | ⏳ Pending |

### Ralph Configuration
- Max Iterations: 10
- Mode: Background
- Completion: PLAN_COMPLETE

### Monitor
```bash
/ralph-status    # Loop progress
/prp-status      # Plan overview
cat PRPs/plans/auth-feature.plan.md
```

---
🚀 Ralph will iterate until all plan tasks are complete.
```

## Status View

```markdown
## 🔄 Ralph + PRP Status

### Plan Progress
- Feature: User Authentication
- Tasks: 3/5 complete (60%)

### Current Task
**Task 4: Write integration tests**
- Iteration: 7
- Status: In progress
- Pattern: tests/integration/users.test.ts

### Ralph Loop
- Iteration: 7/10
- Duration: 28m
- Mode: Running

### Validation
- Build: ✅ Pass
- Unit Tests: ✅ 45/45
- Integration: ⚠️ 8/12 (4 pending)

### Acceptance Criteria
- [x] User registration works
- [x] Login flow complete
- [~] Session management ◄── In progress
- [ ] Password reset flow
```
