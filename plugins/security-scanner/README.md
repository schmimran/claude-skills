# security-scanner

Runs a multi-tool security audit of a Node.js web application and (when
present) its Supabase project, and files findings as labeled GitHub Issues.
Deduplicates by fingerprint, files new issues for novel findings, reopens
previously closed issues on re-detection, auto-closes resolved ones, and
posts expert advisory comments with root-cause analysis on each acted issue.

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

   gh label create "feature - ready for claude" \
     --color 0075ca \
     --description "Ready for a Claude fixing agent"
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
- **jq** on PATH — used by the orchestrator to merge findings.  Install with
  `brew install jq` (macOS) or `apt-get install jq` / `dnf install jq` (Linux).
- **Internet access** for semgrep rule configs (fetched at runtime)
- Required labels created on the target repository (see Quick Start above)
- **Optional, for Supabase auditing**: `SUPABASE_ACCESS_TOKEN` exported in the
  shell.  Without it, Supabase auditing falls back to static-only scanning of
  `supabase/migrations` and `supabase/config.toml`.  See Supabase Auditing
  below.

## Architecture

| Component | Type | Model | Description |
|-----------|------|-------|-------------|
| `security-scanner` | Command | (inherits) | Orchestrates the five-agent pipeline |
| `security-runner` | Agent | sonnet | Installs tools, runs Node.js scans, emits JSON report |
| `security-supabase-auditor` | Agent | sonnet | Queries Supabase advisor API + scans migrations/config.toml |
| `security-triager` | Agent | sonnet | Fingerprints findings, files new issues, reopens closed issues on re-detection, skips duplicates |
| `security-closer` | Agent | sonnet | Closes GitHub Issues for resolved findings |
| `security-advisor` | Agent | opus | Posts expert advisory comments on newly filed and reopened issues |

## Pipeline

```
Target Repo
    |
    +----------------------------+
    v                            v
security-runner          security-supabase-auditor
(npm audit + semgrep    (advisor API + static scan of
 + nodejsscan)           migrations + config.toml)
    |                            |
    v                            v
/tmp/security-findings   /tmp/security-findings-
       .json                  supabase.json
    \                          /
     \                        /
      v                      v
       jq merge (orchestrator)
                |
                v
     /tmp/security-findings.json
                |
    +-----------+-----------+
    v                       v
security-triager     security-closer
(file new issues |   (close resolved,
 reopen closed    |   skip suppressed)
 on re-detection  |
 skip duplicates  |
 skip suppressed) |
    |                       |
    v                       v
GitHub Issues         GitHub Issues
filed/reopened           closed
    |
    v
/tmp/security-new-issues.json
    |
    v
security-advisor
(post expert advisory
 comment on each
 filed/reopened issue)
    |
    v
Advisory comments posted
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
| Supabase RLS misconfiguration | advisor API + migration scan |
| `SECURITY DEFINER` hygiene, `auth.users` exposure, extensions in `public` | advisor API + migration scan |
| Supabase auth hardening (leaked-password protection, MFA, OTP expiry, weak passwords) | advisor API + config.toml scan |
| API-exposed schema overreach | config.toml scan |

## Deduplication

Each finding is assigned a SHA-256 fingerprint computed from:
- Static analysis: `source|rule_id|file|line_band` (10-line window)
- Dependency: `npm-audit|package_name|cve_id`

The triager checks fingerprints in this order:

1. **Suppressed** (open, `security - suppressed` label) → skip always
2. **Open** (open, `security` label, not suppressed) → skip as duplicate
3. **Closed** (recently closed, up to 200, not suppressed) → reopen + comment
4. **New** → file a new issue

Re-detected closed issues are reopened rather than duplicated, preserving the
history of prior fix attempts.  See `references/fingerprint-spec.md` for the
full fingerprint specification.

## Suppression (False Positives)

To suppress a finding permanently:
1. Open its GitHub Issue.
2. Add the label `security - suppressed`.
3. Add a comment explaining why it is a false positive.
4. Leave the issue open.

The scanner will skip suppressed findings on all future runs and will never
auto-close them.  See `references/suppression-guide.md` for details.

## Advisory Comments

After the triager files or reopens issues, the **security-advisor** agent
(running on Opus) posts an expert comment on each acted issue.

- **Newly filed issues** receive a comment with: root cause analysis, a
  specific fix approach (named functions/patterns, not generic advice), and
  common mistakes to avoid when fixing this class of vulnerability.
- **Reopened issues** receive a comment explaining why the prior fix likely
  failed for this rule/source combination, what to look for differently, and
  an adjusted fix approach.

Advisory comments are labeled with `### Security Advisor Note` so they are
easy to find in the issue timeline.

## Auto-Close

At the end of each scan, the security-closer compares open security issues
against the current findings.  Issues whose fingerprint no longer appears in
the scan output are auto-closed with a comment noting the timestamp.  Suppressed
issues are never auto-closed.

## Supabase Auditing

If the target repo uses Supabase, the scanner adds a dedicated auditor covering
the data model (RLS coverage, policies, `SECURITY DEFINER` hygiene,
`auth.users` exposure, storage buckets, extensions in `public`) and
configuration (auth hardening, API schemas).

### Detection

The Supabase auditor runs automatically if any of these signals are present
(no flag to enable, no flag to disable):

1. `supabase/config.toml` exists.
2. `@supabase/supabase-js` is in `package.json`.
3. `SUPABASE_URL` is set in any `.env*` file.
4. `supabase/migrations/` has at least one `.sql` file.

### Two data sources

The auditor prefers the **Supabase advisor API**, which is authoritative for
live project state:

```
GET https://api.supabase.com/v1/projects/{ref}/advisors?type=security
```

To enable the API path, export:

```bash
# Create at https://supabase.com/dashboard/account/tokens
export SUPABASE_ACCESS_TOKEN=sbp_...
```

The project ref is auto-detected in this order:
`SUPABASE_PROJECT_REF` → `project_id` in `supabase/config.toml` →
`SUPABASE_URL` subdomain from `.env*`.

If the token or ref is missing, or the API returns a non-200 response, the
auditor logs the issue and falls back to **static scanning** of
`supabase/migrations/*.sql` and `supabase/config.toml`.  Seed files
(`supabase/seed.sql`) and tests under `supabase/tests/**` are excluded — they
routinely contain allow-all policies that are intentional for local dev.

Both paths produce findings with the same schema.  Advisor findings carry
Supabase's official remediation URL directly in the filed issue's
Recommendation section.  For advisor rules with empty `remediation`, a local
catalog (`references/supabase-rule-catalog.md`) provides the fallback fix
text.

### Severity highlights

- `rls_disabled_in_public`, allow-all policies, `auth.users` exposed → **critical**
- `SECURITY DEFINER` without pinned `search_path`, extensions in `public`,
  leaked-password protection disabled → **high**
- RLS enabled but no policies, long OTP expiry, weak password policy → **medium**

See `references/finding-severity-rubric.md` for the full mapping.

### What about `config.toml`?

Local `supabase/config.toml` reflects **developer intent** for local
environments.  Production auth config lives in the Supabase dashboard and
comes through the advisor API.  Findings from config.toml are labeled as
such in the issue body so you don't assume a config.toml fix addresses
production.

## Scheduling

Wrap in a cron job for weekly full scans:

```bash
# Weekly full scan — Sunday 2am
0 2 * * 0 cd /path/to/your/app && \
  claude -p "/security-scanner owner/repo full" >> ~/security-scan.log 2>&1
```

## Known Limitations

- Air-gapped environments not supported (semgrep requires internet for rule
  configs; the Supabase advisor API also requires outbound internet)
- DAST (runtime/dynamic analysis) not included — static + advisor-level only
- Infrastructure and environment config not scanned
- Third-party API trust surfaces not covered
- Supabase Edge Functions are scanned only to the extent that semgrep covers
  their `.ts` / `.js` sources — no Supabase-specific runtime checks

## License

[MIT](../../LICENSE)
