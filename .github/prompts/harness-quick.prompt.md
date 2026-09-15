---
name: harness-quick
description: Prepare a bounded native-tool pilot using repository-derived defaults.
mode: agent
agent: harness-wizard
---

# Quick Harness Setup

Follow [Native Harness Setup](harness-setup.prompt.md). Quick setup reduces
questions, not verification, review, or permission requirements.

Infer the project, languages, dependency commands, and test framework from actual
repository files. Read existing requirements and GitHub issue handoffs before
asking for information already present. Preserve all unrelated work.

| Setting | Default |
|---------|---------|
| Work selection | One authorized, unblocked item with acceptance criteria |
| Pilot budget | Three tasks or 60 minutes, whichever comes first |
| Retry limit | Three failed attempts per task; permission failures stop immediately |
| Model | Current host's available configured model; verify delegate routes |
| Tracking | Native session tasks and existing GitHub issues for handoffs |
| Checks | Narrowest real checks, plus acceptance-required integration checks |
| Review | Independent review; report unavailable reviewers as blocked |
| Execution | Current session; automatic restart requires a tested supervisor |

Do not generate an arbitrary feature count, assume an SDK is installed, or launch
unsupported background-agent commands. Reuse existing issues and obtain permission
before creating new ones. Record baseline command results and the next action.
No automatic commit, push, merge, or deployment. Report setup as prepared, not
running, until actual execution and required lifecycle tests provide evidence.
