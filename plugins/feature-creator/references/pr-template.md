# PR Template

Use this template when creating pull requests for implemented features and
bug fixes. The `## Root Cause` section is required for bug fixes and omitted
for features.

---

```markdown
## Summary

<2-3 sentences describing what this PR does and why, taken from the
implementation plan.>

## Root Cause

<Bug fixes only — omit this section for features. 2-3 sentences explaining
why the bug existed: what invariant was violated, what assumption was wrong,
or what code path was overlooked. This belongs in the PR body so reviewers
and future archaeologists can understand the fix without opening the issue.>

## Changes

| File | Change |
|------|--------|
| `path/to/file` | <what was done> |

## Testing

- <Tests added or updated>
- <For bug fixes: name of the regression test and what it verifies>
- <Build verification result>
- <Manual verification steps, if any>

## Related Issue

Closes #<ISSUE_NUMBER>

---
*Automated by feature-implementer*
```

## Title format

| Issue type | PR title prefix |
|------------|-----------------|
| Feature | `feat: <description>` |
| Bug | `fix: <description>` |

The conventional-commit prefix in the title matches the commit type used for
the squash-merge. See `merge-checklist.md` for the per-type guidance.
