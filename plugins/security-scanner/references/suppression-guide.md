# Suppression Guide

## How to Suppress a False Positive

1. Open the GitHub Issue for the finding.
2. Add the label `security - suppressed` to the issue.
3. Add a comment explaining why this is a false positive.
4. Leave the issue open.  Do not close it.

The scanner checks for `security - suppressed` before filing duplicates and
before auto-closing.  A suppressed issue will never be auto-closed.

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
