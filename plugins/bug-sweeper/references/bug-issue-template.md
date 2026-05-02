# Bug Issue Template

Format for the GitHub Issue body created by the `bug-sweeper-filer` agent.
The marker on the first line is required — future closer/triager logic
relies on it.

## Title format

```
[bug] <one-line summary, ≤ 100 chars>
```

If the analyst's `title` field already begins with `[bug]`, do not double-prefix.

## Body

```markdown
<!-- claude-bug-sweeper-v1 -->

## Severity

**<HIGH|MEDIUM|LOW>**

## Location

**File:** `<file>`
**Lines:** `<line_start>`–`<line_end>`

```<lang>
<snippet — exact code as read, max 8 lines>
```

## Root Cause

<one-sentence root cause from the analyst>

## Reproduction

<concrete repro steps from the analyst, OR "Trigger the code path at the
location above; see snippet for the failure mode.">

## Suggested Area to Investigate

<short note from the analyst — NOT a fix. Examples:
- "The async sweep loop yields between the email send and the session
   removal; investigate ordering across that boundary."
- "Empty catch swallows the email-send failure while the DB write has
   already committed; investigate compensating logic.">

> This section names the area to investigate. The actual fix is planned and
> implemented by `feature-creator` after the issue is labeled
> `bug - ready for claude`.

## References

- Related commits: <hashes or "none">
- Related issues: <numbers or "none">
- Sweep run: <ISO 8601 UTC timestamp>

---

*Filed by `bug-sweeper`. To remediate, run `/feature-creator` on this
repository — the pipeline picks up issues labeled `bug - ready for claude`.*
```

## Field substitution

| Template token | Source field in `confirmed_bugs[i]` |
|----------------|--------------------------------------|
| Severity | `severity` |
| File | `file` |
| Lines | `line_start`–`line_end` |
| Snippet | `snippet` (preserve indentation) |
| Root Cause | `root_cause` |
| Reproduction | `reproduction` |
| Suggested Area to Investigate | `investigate` |
| Related commits | `references.related_commits[]` |
| Related issues | `references.related_issues[]` |
| Sweep run | `scan_timestamp` from the plan's top-level field |

The language fence (`<lang>`) is `ts` for `.ts`/`.tsx`, `js` for
`.js`/`.jsx`/`.mjs`/`.cjs`, otherwise omit (\`\`\`).

## Why no "Proposed fix" section

Discovery and remediation are split for a reason: the analyst should not
shape feature-creator's plan. feature-creator owns risk assessment, plan
template selection, and implementation order. A "proposed fix" written by
the analyst would either be redundant with feature-creator's plan (waste)
or contradict it (confusion).

The `Suggested Area to Investigate` exists so the human reading the issue
has a starting pointer, not a recipe.
