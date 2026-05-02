# Release PR Template

Use this template to construct the release PR body. The orchestrator
(`commands/feature-creator.md`, Phase 5c) populates the placeholders from the
Phase 4 implementation output.

The **`Closes` section is required**. GitHub only auto-closes issues when a PR
merges into the repository's default branch (`main`). Feature and bug-fix PRs
merge into `stage`, so per-issue auto-close does not fire there. The release
PR is the only merge into `main`, so every feature **and bug** issue that
landed in this release must appear as a `Closes #<N>` line in this body —
otherwise the issues will remain open after the release merges and require
manual cleanup.

Before calling `gh pr create`, the orchestrator must confirm that every
successfully-merged issue from Phase 4 (across both types) appears in the
`Closes` section. Missing entries must fail the pre-flight check and block PR
creation.

---

```markdown
# Release <YYYY-MM-DD>

## Summary

This release bundles the following PRs merged into `stage`:

### Features

- #<PR_NUMBER> — <Feature title> (issue #<ISSUE_NUMBER>)
<!-- one line per successfully-merged feature PR; omit this section if none -->

### Bug fixes

- #<PR_NUMBER> — <Bug title> (issue #<ISSUE_NUMBER>)
<!-- one line per successfully-merged bug-fix PR; omit this section if none -->

## Closes

<!--
One `Closes #<N>` line per issue (feature OR bug) that landed in this
release. GitHub parses these keywords on merge into the default branch
and auto-closes the referenced issues. Do NOT remove or rename this
section — the orchestrator's pre-flight check looks for it.
-->

Closes #<ISSUE_NUMBER>
Closes #<ISSUE_NUMBER>
<!-- one line per issue, regardless of type -->

---

Automated by feature-creator.
```

## Section omission rules

- If the run merged only features, omit the `### Bug fixes` heading and its
  body.
- If the run merged only bug fixes, omit the `### Features` heading and its
  body.
- The `## Closes` section is always present and lists both types together —
  GitHub doesn't care about the structure of the body, only that each
  closing keyword resolves to a real issue.
