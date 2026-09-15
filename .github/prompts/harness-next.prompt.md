---
name: harness-next
description: Continue one authorized work item using native tools and an evidence-backed handoff.
mode: agent
agent: harness-coder
---

# Next Coding Session

Follow [Native Harness Setup](harness-setup.prompt.md) and the coder role.

1. Read repository instructions and the existing GitHub issue handoff. Inspect
   branch, commit, and dirty paths; preserve unrelated work.
2. Reconcile in-progress work against actual files and execute a targeted baseline
   check before selecting another authorized, unblocked item.
3. Track session steps with native task tools. Implement one bounded item with
   explicit acceptance criteria; execute the narrowest check after each edit.
4. Collect actual test output and obtain independent review through available
   native delegation. Report unavailable workers or missing checks as blockers.
5. Record changes, commands and outcomes, review findings, remaining criteria,
   blockers, and the next action in the existing GitHub issue.

Respect setup's retry, time, and task limits. Stop affected operations on permission
failure. No automatic staging, commits, push, merge, or deployment. On cancellation,
stop new work, collect output, stop owned processes, and preserve the handoff.

This prompt runs within the current host session. Background command tools do not
restart agents; automatic continuation requires a separately tested supervisor.
