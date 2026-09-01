---
description: Log a missing Fabric feature or documentation gap as a GitHub issue
---

# Log Missing Feature

You have identified a capability, feature, or documentation gap that this POC does not cover yet. File it as a GitHub issue so it is tracked instead of silently worked around.

## Steps

1. **Confirm the gap is real**
   - Search `docs/features/` and `docs/best-practices/` for existing coverage.
   - Search open issues: `gh issue list --search "<keywords>"`.
   - If it already exists, link to it instead of filing a duplicate.

2. **Research the official state** (Microsoft Docs MCP)
   - Use `microsoft_docs_search` for the feature's current GA/preview status and guidance.
   - Capture the most relevant Microsoft Learn URL — it goes in the issue body.

3. **Choose the template**
   - New capability or missing Fabric feature → `.github/ISSUE_TEMPLATE/feature_request.md` (label: `enhancement`)
   - Documentation gap or stale doc → `.github/ISSUE_TEMPLATE/documentation-request.md` (label: `documentation`)

4. **File the issue**

```bash
gh issue create \
  --title "[FEATURE] <concise title>" \
  --label "enhancement" \
  --body "## 🚀 Feature Description
<what is missing>

## 🎯 Motivation
<why the POC needs it>

## 💡 Proposed Solution
<what coverage should look like — doc, notebook, generator, Bicep module>

## 📚 Microsoft Documentation Reference
<Microsoft Learn URL from step 2>

## 📍 Where the Gap Was Found
<repo path or workflow where the gap surfaced>

## 📋 POC Impact
- [ ] New feature doc required (docs/features/)
- [ ] New notebook(s) needed
- [ ] New data generator needed
- [ ] New Bicep module needed
- [ ] New tests needed"
```

5. **Report back** — give the user the issue number and URL.

## Notes

- Use `documentation` label and the `[DOCS]` title prefix for doc gaps.
- If the gap was discovered while doing other work, finish the current task first unless the gap blocks it.
- Do not file issues for features already documented in `docs/features/` — update the existing doc instead.
