# Review Checklist for Bug-Fix Plans

Used by the review subagent spawned from `feature-reviewer` when the plan
under review is for a `bug - planned` issue. For feature plans, use
[`review-checklist.md`](review-checklist.md) instead.

You are reviewing one or more bug-fix plans. Be specific and actionable.

## Check 1: Root Cause is Identified, Not Just the Symptom

- Does the plan's "Root Cause Analysis" cite a file and line number?
- Does the explanation match the cited code? (Re-read the file at the
  cited line.)
- If the plan describes only the symptom and proposes a fix without
  identifying the root cause, flag it. Symptom-only fixes often re-emerge
  in different forms.

## Check 2: Regression Test is Included

- Does the "Affected Files" table include a `Modify` or `Create` entry for
  a test file?
- Does the "Test Strategy" describe a regression test that:
  1. Fails against the unfixed code, AND
  2. Passes after the fix?
- If the plan does not include a regression test, flag it as **HIGH**
  severity. A bug fix without a regression test is a re-emergence waiting
  to happen.

Exceptions:
- A pure documentation fix does not need a regression test.
- A dependency version bump (CVE patch) may rely on the upstream's tests
  rather than introducing a new one — the plan must say so explicitly.

## Check 3: Dependency Order

- Does the implementation order respect dependencies between bugs in the
  same bucket?
- If bug B's fix depends on bug A's fix, is A scheduled first?

## Check 4: File Conflicts

- Do any two bug fixes in the bucket modify the same file?
- If so, is the ordering correct? The bug whose fix is more structural
  (e.g., refactors a function) should land before the one making a small
  change to that function.

## Check 5: Convention Compliance

- Do file modifications follow the project's naming and style conventions?
- Does the regression test follow the project's existing test patterns
  (test framework, fixture conventions, mocking rules)?
- If the plan introduces a new test file, does it sit in the right
  directory?

## Check 6: Scope Reasonableness

- Is each bug-fix plan achievable in a single implementation pass?
- If a bug fix touches 5+ files, has the plan articulated why? A wide-scope
  fix may indicate a misdiagnosed root cause — flag it for human review.
- Does the plan stay focused on the bug, or does it bundle in unrelated
  cleanup? Bundled cleanup is a feature-creator anti-pattern — flag it.

## Check 7: Behavioral Compatibility

- Does the fix change behavior in any way that downstream consumers may
  rely on (even if the prior behavior was buggy)?
- If the plan removes a function, public method, or API endpoint, does it
  document why this is safe and what migration callers need (if any)?

## Check 8: Missing Considerations

- Does the plan account for **why** the bug existed in the first place?
  (e.g., "this code was added before TypeScript strict mode was enabled,
  so the null case was never type-checked")
- Are there other places in the codebase that follow the same buggy
  pattern? If so, does the plan address them or call them out as out of
  scope?
- Does the plan update any relevant documentation (READMEs, CLAUDE.md,
  inline comments) to prevent future regressions?

## Output Format

Return your review as a structured list:

### Issues Found

1. **[Severity: HIGH/MEDIUM/LOW]** <description of the issue and which bug
   it affects>
   - **Suggestion**: <how to fix it>

### Approved

If no HIGH issues are found, state: "Plan is approved with the above notes."
If HIGH issues are found, state: "Plan needs revision before implementation."

## Bug-vs-feature differences in this checklist

- **Test Coverage** check is renamed **Regression Test is Included** and
  raised in priority — a missing regression test is HIGH severity.
- **Missing Considerations** explicitly asks "why did the bug exist?" so
  the plan addresses the original cause, not just the symptom.
- **Behavioral Compatibility** is new — bug fixes can break downstream
  consumers who adapted to the bug.
- The original "Test Coverage" check from the feature checklist is folded
  into Check 2.
