---
name: harness-resume
description: Reconcile a GitHub issue handoff with the checkout and resume authorized work.
mode: agent
agent: harness-wizard
---

# Resume Harness

Follow [Native Harness Setup](harness-setup.prompt.md).

1. Read repository instructions and the existing GitHub issue handoff using
   available GitHub access. Report inaccessible records; do not invent state.
2. Inspect the actual branch, commit, staged, unstaged, and untracked changes.
   Preserve unrelated work and reconcile differences with the recorded handoff.
3. Identify incomplete acceptance criteria, review findings, blockers, and owned
   background processes. Collect available output before launching replacements;
   do not duplicate work whose outcome is still unknown.
4. Execute the smallest relevant baseline check. Historical passing results do
   not verify the current checkout. Stop affected operations on permission failure.
5. Restore the current session's native task list from reconciled work. Continue
   the authorized in-progress item before selecting another unblocked item.
6. Record commands, outcomes, remaining work, and the next action in the existing
   GitHub issue at handoff. Missing test or review evidence remains incomplete.

Respect setup's budgets, retry limits, and cancellation procedure. Do not push,
merge, deploy, or discard changes without authorization. This prompt resumes work
inside the current session; automatic session restart requires a tested host
supervisor, not a background shell command.
