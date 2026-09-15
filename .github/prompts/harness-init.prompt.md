---
name: harness-init
description: Reconcile requirements and prepare a native-tool development handoff.
mode: agent
agent: harness-initializer
---

# Initialize Harness

Follow [Native Harness Setup](harness-setup.prompt.md) and the initializer role.

1. Read repository instructions, Git state, requirements, and existing GitHub issue
   handoffs. Preserve unrelated changes; do not reinitialize the repository.
2. Reconcile requirements with implementation and evidence. Reuse existing issues;
   obtain permission before creating missing tracking issues. Report inaccessible
   sources as unverified rather than claiming a complete backlog inventory.
3. Derive bounded work items and acceptance criteria from requirements, not a
   fixed feature count. Identify dependencies and required test/review evidence.
4. Execute the narrowest baseline check using actual repository commands.
5. Record branch, dirty paths, results, blockers, and the next authorized item in
   the existing GitHub issue. Use native task tracking for this session.

No automatic commits, push, deployment, or generic initialization scripts.
Prepared instructions do not start a persistent runner; automatic session restart
requires an available, tested host supervisor as described in setup.
