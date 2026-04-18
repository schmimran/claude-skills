# Supabase Audit Guide

Reference for the `security-supabase-auditor` agent. Covers detection signals,
project ref and token resolution, the Supabase Management API call, static
parsing rules, and the output schema.

## Detection

The auditor only runs if Supabase is in use. Signals, checked in order — any
one match is sufficient:

1. `supabase/config.toml` exists at repo root.
2. `@supabase/supabase-js` is listed in `package.json` `dependencies` or
   `devDependencies`.
3. `SUPABASE_URL` is set in any `.env*` file in the repo root.
4. `supabase/migrations/` exists and contains at least one `.sql` file.

No match → the auditor writes an empty findings file at
`/tmp/security-findings-supabase.json` and logs:

```
Supabase not detected — skipping.
```

## Project ref resolution

Tried in order. First match wins; log which source was used.

1. `$SUPABASE_PROJECT_REF` environment variable.
2. `project_id` field in `supabase/config.toml`.
3. Parse `SUPABASE_URL` from `.env*` — the ref is the subdomain of
   `https://<ref>.supabase.co`.

If no ref resolves, skip the API path and run static-only. Log:

```
No Supabase project ref found — skipping advisor API, running static-only.
```

Do not fail the scan.

## Access token resolution

`$SUPABASE_ACCESS_TOKEN` is the only source. Generate one at
https://supabase.com/dashboard/account/tokens.

If unset, skip the API path. Log:

```
SUPABASE_ACCESS_TOKEN not set — skipping advisor API, running static-only.
```

Never echo the token value to terminal or into any file.

## Advisor API call

Single endpoint, GET, JSON response:

```bash
HTTP_STATUS=$(curl -sS -o /tmp/sec-supabase-advisors.json -w '%{http_code}' \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  "https://api.supabase.com/v1/projects/${PROJECT_REF}/advisors?type=security")
```

Only `type=security` is queried. Performance advisors are intentionally out of
scope.

### Response handling

- **200**: Parse findings. Each finding has the fields listed below.
- **401 / 403**: Token is invalid or missing scope. Log status + first 200
  chars of body. Add `supabase-advisor-api` to `skipped_tools`. Fall back to
  static-only.
- **404**: Project ref is wrong. Log and fall back to static-only.
- **5xx or timeout**: Supabase outage. Log and fall back to static-only.

### Advisor response fields used by the auditor

| Field | Use |
|---|---|
| `name` | becomes `rule_id` (e.g. `rls_disabled_in_public`) |
| `title` | short description |
| `level` | `ERROR` / `WARN` / `INFO` — mapped to severity per rubric |
| `description` | `message` (combined with `detail` if present) |
| `detail` | appended to `message` |
| `remediation` | `recommendation` — URL to Supabase docs |
| `metadata` | entity extraction; see below |
| `cache_key` | stored in issue body as `<!-- supabase_cache_key: <key> -->` |

### Entity extraction from `metadata`

Advisor metadata is shaped differently per rule family. Entity name resolution
tries these keys in order; first non-empty value wins:

1. `metadata.table`
2. `metadata.function`
3. `metadata.view`
4. `metadata.name`

Fallback: `"(unknown)"`. Schema is always `metadata.schema` when present,
otherwise `public`.

The resulting entity identifier is `<schema>.<entity>` — used in both the
fingerprint and the filed issue's `**File**:` analog line.

For `auth_config`-level advisors with no entity (leaked-password protection,
OTP expiry, MFA options), use the literal entity string `auth_config`.

## Static path

Runs unconditionally (independent of the API path — both paths contribute
findings).

### Migration scan

Glob `supabase/migrations/*.sql`. Explicitly **exclude**:

- `supabase/seed.sql` and anything matching `supabase/seed.*.sql`
- Anything under `supabase/tests/**`

Seed and test files routinely contain allow-all policies and fixture grants
that are intentional for local dev — scanning them generates noise.

Detectors (per `supabase-rule-catalog.md` for full rule text):

| rule_id | pattern |
|---|---|
| `missing_rls` | `CREATE TABLE <name>` in `public` with no `ALTER TABLE <name> ENABLE ROW LEVEL SECURITY` later in the same file |
| `policy_allows_all` | `CREATE POLICY` followed by `USING (true)` or `WITH CHECK (true)` |
| `security_definer_no_search_path` | `CREATE FUNCTION ... SECURITY DEFINER` with no `SET search_path` clause before the `AS` body |
| `grant_to_anon` | `GRANT <privs> ON ... TO anon` |
| `view_references_auth_users` | `CREATE VIEW` or `CREATE OR REPLACE VIEW` whose body contains `auth.users` or `auth.identities` |

All use case-insensitive regex. Record `file` (relative path), `line_start`,
and `line_end` (the line of the first matching pattern through the end of the
statement, approximate is fine — `line_band` handles minor drift).

### Config scan

Parse `supabase/config.toml` if present. Flag (see catalog for severity and
fix text):

| rule_id | condition |
|---|---|
| `weak_password_policy` | `[auth] minimum_password_length < 10` |
| `signup_without_confirmation` | `[auth] enable_signup = true` and `[auth.email] enable_confirmations = false` |
| `api_schemas_overexposed` | `[api] schemas` contains anything beyond `public`, `graphql_public`, `storage` |

These findings reflect developer intent for local dev. Production auth config
lives in the Supabase dashboard and comes through the advisor API — note this
in the filed issue body so users don't assume a config.toml fix addresses
production.

## Output schema

Write `/tmp/security-findings-supabase.json`:

```json
{
  "scan_timestamp": "<ISO 8601>",
  "mode": "<quick|full>",
  "repo": "<OWNER/REPO>",
  "skipped_tools": ["supabase-advisor-api"],
  "findings": [
    {
      "fingerprint": "<sha256 hex>",
      "source": "<supabase-advisor|supabase-schema|supabase-config>",
      "rule_id": "<advisor name or static rule_id>",
      "file": "<relative path or null>",
      "line_start": 42,
      "line_end": 45,
      "severity": "<critical|high|medium|low>",
      "title": "<short description>",
      "message": "<description + detail>",
      "recommendation": "<URL from advisor remediation or catalog fallback>",
      "cache_key": "<advisor cache_key or null>",
      "entity": "<schema.entity or null>"
    }
  ]
}
```

Fields `cache_key` and `entity` are optional. All existing finding fields from
`security-runner` output are reused unchanged.

`skipped_tools` is only present when the advisor API was attempted and
failed/unavailable. Empty array or missing if everything ran cleanly.

## Fingerprints

Three canonical strings — see `fingerprint-spec.md` for the full spec:

- `supabase-advisor|<advisor_name>|<schema>.<entity>`
- `supabase-schema|<rule_id>|<file>|<line_band>`
- `supabase-config|<rule_id>|<config_key>`

API and static paths may produce findings with different fingerprints for the
same underlying issue (e.g. RLS disabled seen both by advisor and by migration
scan). That is intentional — each gets its own issue; resolving the
underlying problem causes both to auto-close on the next scan.

## Summary output

After completion, print:

```
## Supabase Auditor Summary

Detection: <detected | not-detected>
API path: <ok | skipped-no-token | skipped-no-ref | skipped-<HTTP status>>
Static path: <ran | skipped>

### Findings

| Source | Critical | High | Medium | Low |
|--------|----------|------|--------|-----|
| supabase-advisor | X | X | X | X |
| supabase-schema  | X | X | X | X |
| supabase-config  | X | X | X | X |
| **Total**        | X | X | X | X |
```

State: `Supabase findings written to /tmp/security-findings-supabase.json`.
