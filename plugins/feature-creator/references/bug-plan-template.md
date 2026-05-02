# Bug-Fix Plan Comment Template

Use this template when posting implementation plans for issues labeled
`bug - triaged`. The `<!-- claude-bug-planner-v1 -->` marker on the first
line is required — downstream agents (consolidator, reviewer, implementer)
use it to locate the plan programmatically.

For feature issues (`feature - planned` flow), use [`plan-template.md`](plan-template.md)
instead.

---

```markdown
<!-- claude-bug-planner-v1 -->
## Bug Fix Plan for #<NUMBER>: <TITLE>

### Summary

<2-3 sentences: what is broken (the user-visible symptom or failure mode),
the root cause (why the bug exists), and the high-level fix approach.>

### Bucket-mates

<Optional — include only when this issue shares a planning bucket with
other bugs (bucket size > 1). Omit this section entirely for singleton
buckets. Bug buckets never contain feature issues.>

- #<M> — <title> — <short note on shared file edits or within-bucket ordering>

<Within-bucket ordering (if relevant): "Land #<X> before #<Y> because …">

### Reproduction Steps

<Concrete steps that demonstrate the bug today. If the bug-sweeper issue
already provides reproduction steps, restate them here and note any
additional steps you discovered while reading the code.>

1. ...
2. ...

Expected: <what should happen>
Actual: <what does happen>

### Root Cause Analysis

<2-4 sentences: why does the bug exist? What invariant is being violated?
What assumption was wrong? Cite file:line where the defect lives.>

### Affected Files

| Action | File | Description |
|--------|------|-------------|
| Modify | `path/to/buggy.ts` | <what changes — the fix> |
| Modify | `path/to/buggy.test.ts` | Add a regression test that reproduces the bug |

A bug fix that does not include a regression test in this table will be
flagged by the reviewer (see `bug-review-checklist.md`).

### Implementation Steps

1. **<Step title>**
   - <Specific change description>
   - <Code pattern to follow>

2. **Add regression test**
   - <Describe the test case>
   - <Where it goes; why it would have caught the bug>

<Continue as needed.>

### Test Strategy

- **Regression test (REQUIRED)**: <test name and what it verifies>. The
  test must fail against the unfixed code and pass after the fix.
- **Existing tests**: <which existing tests cover the surrounding code, and
  how to verify they still pass>
- **Manual verification**: <steps to reproduce the bug and confirm the fix
  resolves it; mirror the Reproduction Steps above>

### Risk Assessment

Assessed against `bug-risk-criteria.md`.

| Factor | Level | Notes |
|--------|-------|-------|
| Auth / authz touched | LOW/MEDIUM/HIGH | <explanation> |
| Concurrency / async | LOW/MEDIUM/HIGH | <explanation> |
| Hot-path SQL / queries | LOW/MEDIUM/HIGH | <explanation> |
| Removes code external consumers may rely on | LOW/MEDIUM/HIGH | <explanation> |
| Error-handling behavior change | LOW/MEDIUM/HIGH | <explanation> |
| Scope (files touched) | LOW/MEDIUM/HIGH | <count, complexity> |

### Dependencies

- <Other bugs/features this depends on, or "None">
- <New packages required (rare for bug fixes), or "None">
```

## Why this template differs from the feature template

A feature plan answers "what new behavior are we adding and how?" A bug-fix
plan answers "what existing behavior is wrong and how do we restore the
intended behavior?" The sections that change:

- **Summary** focuses on the broken behavior + root cause + fix, not on a
  user-facing capability
- **Reproduction Steps** is required (replaces "user story" / "acceptance
  criteria" from the feature template)
- **Root Cause Analysis** is required and cites file:line (no analog in the
  feature template)
- **Affected Files** must include a regression test entry — the reviewer
  enforces this
- **Test Strategy** has a REQUIRED regression test bullet (a feature plan
  may have unit + integration only)
- **Risk Assessment** uses the bug-tuned rubric, not the feature rubric
- **Dependencies** rarely include new packages (feature plans frequently do)
