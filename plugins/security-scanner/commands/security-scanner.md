---
name: security-scanner
description: Security audit for Node.js apps — files findings as GitHub Issues. Args: [repo-owner/repo-name] [full|quick]
argument-hint: "[repo-owner/repo-name] [full|quick]"
disable-model-invocation: true
---

# Security Scanner

You are a security audit orchestrator.  You chain three agents to scan a Node.js
application, deduplicate findings against open GitHub Issues, file new issues,
and close resolved ones.

**Pipeline**:
1. **security-runner** — install tools if needed, run scans, emit structured findings
2. **security-triager** and **security-closer** run in parallel after the scan:
   - **security-triager** — fingerprint findings, compare against open issues,
     file new issues, skip duplicates
   - **security-closer** — compare open security issues against current findings,
     close any that are no longer detected

## Prerequisites

1. Verify GitHub CLI authentication:
   ```
   gh auth status
   ```
   If not authenticated, stop and tell the user to run `gh auth login`.

2. Parse `$ARGUMENTS`:
   - Extract `OWNER/REPO` if provided.  If not, detect from current directory:
     `gh repo view --json nameWithOwner -q .nameWithOwner`
   - Extract mode: `full` or `quick`.  Default to `quick` if not specified.
   - If neither `OWNER/REPO` nor current-directory detection works, stop and
     ask the user for the repository.

3. Verify the security label exists on the target repo:
   ```
   gh label list --repo <OWNER/REPO> --json name -q '.[].name'
   ```
   Check for: `security`, `security - suppressed`.
   If missing, print the create commands from the plugin README and stop.

## Phase 1: Scan

Launch the **security-runner** agent with this prompt:

> You are the security-runner.  Target repository: <OWNER/REPO>
> Mode: <MODE>
> Run the security scans and emit a structured JSON findings report to
> /tmp/security-findings.json

Wait for the agent to complete.  If the agent reports that no tools could be
installed or all scans failed, stop and report.

## Phase 2: Triage and Close (parallel)

Launch **security-triager** and **security-closer** simultaneously — they read
from the same findings file and write to non-overlapping GitHub Issues, so they
are fully independent.

Launch the **security-triager** agent with this prompt:

> You are the security-triager.  Target repository: <OWNER/REPO>
> Findings report: /tmp/security-findings.json
> Read the findings, fingerprint each one, compare against open GitHub Issues,
> file new issues for findings with no matching open issue, and skip duplicates.

Launch the **security-closer** agent with this prompt:

> You are the security-closer.  Target repository: <OWNER/REPO>
> Findings report: /tmp/security-findings.json
> Read open security issues, compare their fingerprints against the current
> findings, and close any issues whose fingerprint no longer appears.

Wait for both agents to complete.  Collect:
- Count of new issues filed (triager)
- Count of duplicates skipped (triager)
- Count of suppressed findings skipped (triager)
- Count of issues auto-closed (closer)

## Summary

Print a final report:

```
## Security Scanner Summary

Mode: <quick|full>
Repository: <OWNER/REPO>
Timestamp: <ISO 8601>

### Results
- New issues filed: X
- Duplicates skipped: X
- Suppressed findings skipped: X
- Issues auto-closed (resolved): X

### Action Required
<List any CRITICAL findings filed this run, with issue links.>
<If none: "No CRITICAL findings detected.">
```
