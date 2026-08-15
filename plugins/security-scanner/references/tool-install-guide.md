# Tool Install Guide

The security-runner agent runs its scanners **ephemerally** with `npx --yes`.

## The default writes nothing to the target repo

A scanner's job is to read a repo, not to modify it. Installing a dev
dependency would rewrite the `package.json` and lockfile of the very repo under
audit — a source change made by a read-only tool, appearing in the user's diff
as if they had made it.

So the default is ephemeral execution:

```bash
npx --yes semgrep …
npx --yes nodejsscan …
```

`--yes` suppresses the interactive install prompt, which would otherwise hang
an unattended run. Packages land in npx's own cache, never in the repo.

**A default-flags run leaves `package.json` and the lockfile untouched.**

## `--install-tools` (opt-in)

Pass `--install-tools` to persist the scanners as dev dependencies instead —
useful for repeated scans on a slow connection, where re-resolving each run is
wasteful:

```bash
npm install --save-dev semgrep nodejsscan
```

This **does** modify the target repo's `package.json` and lockfile. It happens
only when the flag is passed explicitly. Never install as a side effect of a
scan, and never without the flag.

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
# Resolved on demand; no install step, no repo modification.
npx --yes semgrep --version 2>/dev/null
```
If this fails, the environment has no outbound network access to the npm
registry.  Record `tool_status: unavailable` for the secrets scan and continue
with the remaining tools — do not install as a fallback.

## Required for full mode (in addition to above)

### semgrep (OWASP rules)
Same binary as above — just additional rule configs.  Nothing extra to resolve.

### nodejsscan
```bash
npx --yes nodejsscan --version 2>/dev/null
```
Same handling as semgrep: on failure, record `tool_status: unavailable` and
continue.

## Verifying the Rule Configs

semgrep rule configs are fetched at runtime from the semgrep registry.  They
require internet access.  If the scan environment is air-gapped, these configs
must be pre-downloaded and referenced by local path.  This is not supported —
flag it if the environment has no outbound internet.

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
