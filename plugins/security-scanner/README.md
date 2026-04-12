# security-scanner

Runs a multi-tool security audit of a Node.js web application and files
findings as labeled GitHub Issues.  Deduplicates by fingerprint, files new
issues for novel findings, and auto-closes issues for resolved ones.

## Quick Start

1. **Install the marketplace** (once per machine):
   ```bash
   /plugin marketplace add https://github.com/schmimran/claude-skills
   ```

2. **Create the required labels** on your target repository:
   ```bash
   gh label create "security" \
     --color D93F0B \
     --description "Security vulnerability finding"

   gh label create "security - suppressed" \
     --color CCCCCC \
     --description "Confirmed false positive — scanner will skip this finding"
   ```

3. **Run a quick scan** (before feature work):
   ```bash
   /security-scanner
   ```
   Or target a specific repo:
   ```bash
   /security-scanner owner/repo
   ```

4. **Run a full scan** (weekly, or on demand):
   ```bash
   /security-scanner owner/repo full
   ```

## Prerequisites

- **Node.js** with `npm` available in the shell
- **GitHub CLI** installed and authenticated (`gh auth status`)
- **Internet access** for semgrep rule configs (fetched at runtime)
- Required labels created on the target repository (see Quick Start above)

## Architecture

| Component | Type | Model | Description |
|-----------|------|-------|-------------|
| `security-scanner` | Command | (inherits) | Orchestrates the three-agent pipeline |
| `security-runner` | Agent | sonnet | Installs tools, runs scans, emits JSON report |
| `security-triager` | Agent | sonnet | Fingerprints findings, files new issues, skips duplicates |
| `security-closer` | Agent | sonnet | Closes GitHub Issues for resolved findings |

## Pipeline

```
Target Repo
    |
    v
security-runner
(npm audit + semgrep + nodejsscan)
    |
    v
/tmp/security-findings.json
    |
    v
security-triager                    security-closer
(fingerprint → compare open        (compare open issues
 issues → file new | skip           → close resolved)
 duplicates | skip suppressed)
    |                                     |
    v                                     v
GitHub Issues filed              GitHub Issues closed
```

## Modes

| Mode | Tools | When to Use |
|------|-------|-------------|
| quick (default) | npm audit, semgrep secrets | Before every feature build |
| full | npm audit, semgrep OWASP, semgrep secrets, nodejsscan | Weekly scheduled scan |

## Coverage

| Vulnerability Class | Tool |
|---|---|
| Dependency CVEs | npm audit |
| Hardcoded secrets / API keys | semgrep p/secrets |
| OWASP Top 10 (injection, SSRF, broken auth) | semgrep p/owasp-top-ten |
| Node.js-specific patterns | semgrep p/nodejs |
| Node-specific web vulnerabilities | nodejsscan |

## Deduplication

Each finding is assigned a SHA-256 fingerprint computed from:
- Static analysis: `source|rule_id|file|line_band` (10-line window)
- Dependency: `npm-audit|package_name|cve_id`

The triager checks fingerprints against open issues before filing.  Existing
open issues are skipped.  See `references/fingerprint-spec.md` for the full
specification.

## Suppression (False Positives)

To suppress a finding permanently:
1. Open its GitHub Issue.
2. Add the label `security - suppressed`.
3. Add a comment explaining why it is a false positive.
4. Leave the issue open.

The scanner will skip suppressed findings on all future runs and will never
auto-close them.  See `references/suppression-guide.md` for details.

## Auto-Close

At the end of each scan, the security-closer compares open security issues
against the current findings.  Issues whose fingerprint no longer appears in
the scan output are auto-closed with a comment noting the timestamp.  Suppressed
issues are never auto-closed.

## Scheduling

Wrap in a cron job for weekly full scans:

```bash
# Weekly full scan — Sunday 2am
0 2 * * 0 cd /path/to/your/app && \
  claude -p "/security-scanner owner/repo full" >> ~/security-scan.log 2>&1
```

## Known Limitations (v0.1)

- Air-gapped environments not supported (semgrep requires internet for rule configs)
- DAST (runtime/dynamic analysis) not included — static analysis only
- Infrastructure and environment config not scanned
- Third-party API trust surfaces not covered

## License

[MIT](../../LICENSE)
