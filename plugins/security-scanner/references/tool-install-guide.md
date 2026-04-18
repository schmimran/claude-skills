# Tool Install Guide

The security-runner agent checks for and installs these tools before scanning.
All tools are installed as dev dependencies or via npx — no global installs.

## Orchestrator prerequisites

### jq (required)

The orchestrator merges findings from `security-runner` and
`security-supabase-auditor` using `jq`.  It is a hard prerequisite — the
command fails in its prerequisites step if `jq` is not on PATH.

```bash
command -v jq
```

If missing:
- macOS: `brew install jq`
- Debian/Ubuntu: `sudo apt-get install jq`
- RHEL/Fedora: `sudo dnf install jq`

## Required for quick mode

### npm audit
Built into Node.js.  No installation required.  Verify:
```bash
npm audit --version
```
If this fails, the Node.js installation is broken.  Stop and report.

### semgrep (secrets rules)
```bash
# Check if available
npx semgrep --version 2>/dev/null

# If not available, install
npm install --save-dev semgrep
```

## Required for full mode (in addition to above)

### semgrep (OWASP rules)
Same binary as above — just additional rule configs.  No extra install needed.

### nodejsscan
```bash
# Check if available
npx nodejsscan --version 2>/dev/null

# If not available, install
npm install --save-dev nodejsscan
```

## Verifying the Rule Configs

semgrep rule configs are fetched at runtime from the semgrep registry.  They
require internet access.  If the scan environment is air-gapped, these configs
must be pre-downloaded and referenced by local path.  This is out of scope for
v0.1 — flag it if the environment has no outbound internet.

## Supabase auditing (optional)

The `security-supabase-auditor` agent runs alongside `security-runner` when a
Supabase project is detected.  It has two data sources:

### Advisor API (preferred)

Calls `https://api.supabase.com/v1/projects/{ref}/advisors?type=security` via
`curl`.  Requires:

- `SUPABASE_ACCESS_TOKEN` environment variable.  Create a personal access
  token at https://supabase.com/dashboard/account/tokens and export it in
  the shell that runs the scanner.
- A resolvable project ref.  The auditor tries in order:
  `$SUPABASE_PROJECT_REF`, `project_id` in `supabase/config.toml`, and the
  subdomain of `SUPABASE_URL` from any `.env*` file.

No additional tools are installed — `curl` is standard on macOS and Linux.

If the token or project ref is missing, or the API returns a non-200
response, the auditor logs the issue and falls back to static-only.  The
scan does not fail.

### Static fallback

Parses `supabase/migrations/*.sql` and `supabase/config.toml` locally.
Requires no external dependencies.  See `supabase-audit-guide.md` for the
full rule set.

## Tool Failure Handling

If a tool fails to install or run:
1. Log the error to terminal.
2. Skip that tool's findings section in the report.
3. Note the skip in the JSON report under a top-level `skipped_tools` array.
4. Continue with remaining tools.

Do not stop the entire scan because one tool fails.
