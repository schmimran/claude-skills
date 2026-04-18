# Fingerprint Specification

Each finding gets a stable fingerprint used for deduplication and auto-close.
The fingerprint must be stable across scans as long as the finding exists, and
must change when the finding is genuinely different.

## Algorithm

Fingerprint = SHA-256 of the canonical string, hex-encoded.

### For static analysis findings (semgrep, nodejsscan)

Canonical string:
```
<source>|<rule_id>|<file>|<line_band>
```

Where:
- `source`: `semgrep-owasp`, `semgrep-secrets`, or `nodejsscan`
- `rule_id`: exact rule identifier from the tool
- `file`: relative path from repo root, forward slashes, no leading slash
- `line_band`: `floor(line_start / 10) * 10`
  (bands findings into 10-line windows — tolerates minor code shifts
  without creating duplicate issues)

Example: `semgrep-secrets|javascript.lang.security.hardcoded-secret|src/config.js|20`

### For dependency findings (npm-audit)

Canonical string:
```
npm-audit|<package_name>|<cve_id>
```

Where:
- `package_name`: exact npm package name
- `cve_id`: CVE identifier if present; otherwise the advisory ID from npm audit

Example: `npm-audit|lodash|CVE-2021-23337`

## Computing in Bash

```bash
echo -n "<canonical_string>" | sha256sum | awk '{print $1}'
```

## Storing in GitHub Issues

The fingerprint is stored in the issue body as an HTML comment on the last line:

```
<!-- fingerprint: <hex> -->
```

This makes it machine-readable without being visible to humans viewing the issue.

### For Supabase advisor findings (supabase-advisor)

Canonical string:
```
supabase-advisor|<advisor_name>|<schema>.<entity>
```

Where:
- `advisor_name`: the `name` field from the Supabase Management API advisor
  response (e.g. `rls_disabled_in_public`)
- `schema`: `metadata.schema` from the advisor response, or `public` if absent
- `entity`: first non-empty of `metadata.table`, `metadata.function`,
  `metadata.view`, `metadata.name`. For `auth_config`-level advisors (leaked
  password protection, OTP expiry, MFA options) with no entity, use the literal
  string `auth_config`.

Example: `supabase-advisor|rls_disabled_in_public|public.profiles`
Example: `supabase-advisor|auth_leaked_password_protection|auth_config`

### For Supabase static schema findings (supabase-schema)

Canonical string:
```
supabase-schema|<rule_id>|<file>|<line_band>
```

Same 10-line banding as other static analysis sources. `rule_id` is the static
detector id (e.g. `missing_rls`, `policy_allows_all`).

Example: `supabase-schema|missing_rls|supabase/migrations/20260410_add_profiles.sql|40`

### For Supabase config findings (supabase-config)

Canonical string:
```
supabase-config|<rule_id>|<config_key>
```

Where:
- `rule_id`: the static detector id (e.g. `weak_password_policy`)
- `config_key`: the TOML path of the offending setting
  (e.g. `auth.minimum_password_length`)

Example: `supabase-config|weak_password_policy|auth.minimum_password_length`

## Supabase Cache Key (Separate from Fingerprint)

Supabase advisor findings carry an additional `cache_key` returned by the
Management API.  This is stored in the issue body as a sibling HTML comment,
alongside (not replacing) the fingerprint:

```
<!-- fingerprint: <hex> -->
<!-- supabase_cache_key: <key> -->
```

The cache key is used only for human cross-reference against the Supabase
dashboard advisor list — it is not used for dedup or auto-close (the
fingerprint does that).  For non-advisor findings the line is omitted or
rendered as `<!-- supabase_cache_key: none -->`.

## Collision Policy

Line-band collisions (two different findings in the same 10-line window of the
same file from the same rule) are acceptable — they will be treated as the same
finding.  In practice this is rare.  If it causes problems in a specific file,
the suppression mechanism handles it.

Note: the Supabase advisor and static paths may produce different fingerprints
for the same underlying issue (e.g. RLS disabled on a table, seen both by the
advisor API and by scanning the migration that created the table).  This is
intentional — each finding files its own issue; fixing the underlying problem
causes both to auto-close on the next scan.
