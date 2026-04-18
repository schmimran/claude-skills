# Suppression Guide

Suppression has two pathways:

1. **Manual suppression** — a human labels an issue `security - suppressed`
   after triaging it.
2. **Agent-applied suppression** — the `security-advisor` auto-suppresses a
   newly filed issue when three high-confidence false-positive signals are all
   present.  A `feature - human review` label is applied so a human validates
   the suppression before it becomes permanent.

## How to Suppress a False Positive (Manual)

1. Open the GitHub Issue for the finding.
2. Add the label `security - suppressed` to the issue.
3. Add a comment explaining why this is a false positive.
4. Leave the issue open.  Do not close it.

The scanner checks for `security - suppressed` before filing duplicates and
before auto-closing.  A suppressed issue will never be auto-closed.

## Agent-Applied Suppression (Autonomous)

The `security-advisor` agent may auto-suppress a newly filed issue when ALL
THREE of the following signals are present simultaneously:

1. **Source** — `supabase-advisor` or `supabase-schema`.
2. **Rule ID** — one of a small set of rules known to be FP-prone on Supabase
   internal tables:
   - `supabase-advisor` source: `rls_disabled_in_public`, `rls_enabled_no_policy`
   - `supabase-schema` source: `missing_rls`, `policy_allows_all`
3. **Table name** — matches a known Supabase-internal or system table such as
   `schema_migrations`, `supabase_migrations`, `supabase_functions`,
   `_realtime`, `_analytics`, `_supabase`, `storage.buckets`, or
   `storage.objects`.

Reopened issues (`type: "reopened"`) are **never** auto-suppressed — a
re-detection always requires human review.

When all three signals match, the advisor:

- Posts a rationale comment explaining the suppression.
- Applies the `security - suppressed` label.
- Applies the `feature - human review` label so a reviewer confirms the call.
- Removes `feature - ready for claude` (no fix work should start).
- Closes the issue as `not planned`.

If you disagree with an auto-suppression, remove the `security - suppressed`
label.  The next scan will re-file the issue if it is still detected.  You
may also want to remove `feature - human review` once you have decided.

## How Suppression Works

The security-triager reads all open issues labeled `security - suppressed`
and extracts their fingerprints at the start of each run.  Any finding whose
fingerprint matches a suppressed issue is skipped — no new issue is filed and
no duplicate counter incremented.

The security-closer explicitly excludes suppressed issues from auto-close logic.

## Removing a Suppression

If you later confirm the finding is real:
1. Remove the `security - suppressed` label.
2. The next scan will re-file the issue as a new finding if it is still detected.

## Required Labels

Create these labels on your target repository before running the scanner:

```bash
gh label create "security" \
  --color D93F0B \
  --description "Security vulnerability finding"

gh label create "security - suppressed" \
  --color CCCCCC \
  --description "Confirmed false positive — scanner will skip this finding"
```
