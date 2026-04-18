# Release PR Template

Use this template to construct the release PR body. The orchestrator
(`commands/feature-creator.md`, Phase 5c) populates the placeholders from the
Phase 4 implementation output.

The **`Closes` section is required**. GitHub only auto-closes issues when a PR
merges into the repository's default branch (`main`). Feature PRs merge into
`stage`, so feature-level auto-close does not fire. The release PR is the only
merge into `main`, so every feature issue that landed in this release must
appear as a `Closes #<N>` line in this body — otherwise the issues will remain
open after the release merges and require manual cleanup.

Before calling `gh pr create`, the orchestrator must confirm that every
successfully-merged feature issue from Phase 4 appears in the `Closes` section.
Missing entries must fail the pre-flight check and block PR creation.

---

```markdown
# Release <YYYY-MM-DD>

## Summary

This release bundles the following merged feature PRs from `stage`:

- #<PR_NUMBER> — <Feature title> (issue #<ISSUE_NUMBER>)
- #<PR_NUMBER> — <Feature title> (issue #<ISSUE_NUMBER>)
<!-- one line per successfully-merged feature PR -->

## Closes

<!--
One `Closes #<N>` line per feature issue landed in this release.
GitHub parses these keywords on merge into the default branch and
auto-closes the referenced issues. Do NOT remove or rename this
section — the orchestrator's pre-flight check looks for it.
-->

Closes #<ISSUE_NUMBER>
Closes #<ISSUE_NUMBER>
<!-- one line per issue -->

---

Automated by feature-creator.
```
