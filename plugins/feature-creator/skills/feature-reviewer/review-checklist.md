# Review Checklist for Combined Implementation Plan

You are reviewing a combined implementation plan that covers multiple features.
Your job is to find problems, gaps, and improvements. Be specific and actionable.

## Check 1: Dependency Order

- Does the implementation order respect inter-feature dependencies?
- If feature B uses something introduced by feature A, is A scheduled first?
- Are there circular dependencies? If so, flag them — they indicate the features
  need to be redesigned or split differently.

## Check 2: File Conflicts

- Do any two features modify the same file?
- If so, is the ordering correct? The feature making more foundational changes
  should go first.
- Will the second feature's plan still be valid after the first feature's changes?
  If not, note what needs to be adjusted.

## Check 3: Test Coverage

- Does each feature's plan include tests for the new behavior?
- Are edge cases covered (empty inputs, error states, boundary conditions)?
- If a feature modifies existing behavior, are existing tests updated?
- Is there an integration test strategy for features that interact?

## Check 4: Convention Compliance

- Do new files follow the project's naming conventions?
- Do new functions/components follow the project's patterns?
- Are new dependencies justified and consistent with the project's stack?
- Does the plan follow the build/test workflow documented in the project's CLAUDE.md?

## Check 5: Scope Reasonableness

- Is each feature's plan achievable in a single implementation pass?
- Are there steps that seem too large or vague? If so, suggest breaking them down.
- Is the total scope across all features reasonable (rough heuristic: more than
  30 files across all features warrants caution)?

## Check 6: Missing Considerations

- Does the plan account for error handling in new code paths?
- Are there logging or observability gaps?
- Does the plan update relevant documentation (README, API docs, CLAUDE.md)?
- Are there migration steps needed (data backfill, feature flags)?

## Output Format

Return your review as a structured list:

### Issues Found
1. **[Severity: HIGH/MEDIUM/LOW]** <description of the issue and which feature it affects>
   - **Suggestion**: <how to fix it>

### Approved
If no HIGH issues are found, state: "Plan is approved with the above notes."
If HIGH issues are found, state: "Plan needs revision before implementation."
