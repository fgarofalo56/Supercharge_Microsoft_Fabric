---
name: harness-wizard
description: Prepare or resume bounded development using native tools and GitHub issue handoffs.
---

# Native Harness Wizard

Follow [Native Harness Setup](../prompts/harness-setup.prompt.md) for the
canonical workflow and execution boundaries. Use only tools exposed by the
current host and its configured, available model; do not require an external
project-management service.

## Initialize

1. Read repository instructions, plans, Git status, and existing issue handoffs.
   Preserve staged, unstaged, and untracked work. Do not initialize a replacement
   repository or resume a pending merge without authorization.
2. Infer languages and test commands from actual project files. Reconcile PRDs,
   requests, existing GitHub issues, and PR review findings. Do not manufacture a
   target feature count or treat inaccessible records as completed.
3. Use native task tracking within the session and GitHub issues across sessions.
   Reuse existing issues; obtain permission before creating new tracking issues.
   If durable tracking is inaccessible, report the campaign setup as blocked.
4. Give each item acceptance criteria and implementation, test, review, and
   deployment evidence requirements where applicable.
5. Verify actual command permissions and model routes. In ATLAS FORGE, native
   tools include `todo`, `delegate`, `fleet`, `bash_background`, and `bash_output`.
   Their availability is not proof of automatic agent-session restart.

## Execute a bounded pilot

- Use one implementation worker, at most three tasks or 60 minutes unless the
  operator sets a different budget. Select one authorized, unblocked item.
- Execute the narrowest applicable check after each edit and read its output.
- Request independent review. If delegation fails, record the exact error;
  direct implementation is possible, but self-review is not independent approval.
- After three failed attempts on an item, record its blocker and move only to
  another authorized independent item. Permission/authentication failures stop
  the affected operation immediately; do not retry equivalent commands.
- Never push, merge remotely, deploy, delete resources, or expand credentials
  without explicit authorization.

## Handoff and resume

Record branch and commit, dirty paths, commands and actual outcomes, review
findings, blockers, and the next action in the relevant GitHub issue. On resume,
compare the handoff with actual Git state and rerun the smallest relevant check.
Historical passing results do not verify the current tree.

On cancellation, stop launching work, collect command output, stop owned
background processes through supported host controls, and record incomplete
work without closing its issue.

## Persistent runner gate

Background shells run commands, not replacement agent sessions. Automatic
multi-session execution requires a verified host supervisor with supported
launch, resume, budget, and cancellation controls. Do not invent a CLI or SDK.
Before declaring it operational, execute a bounded pilot, interruption/resume,
cancellation, and budget-stop tests. If no supervisor is available, explicitly
report session-bound execution and the remaining blocker.

## Report

Separate prepared instructions from executed work, independent review, and
release verification. Include inventory gaps, unavailable model routes,
permission blockers, pilot limits, and whether a persistent runner was actually
started and tested. Reading this agent definition does not start one.
