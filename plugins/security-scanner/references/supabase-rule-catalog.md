# Supabase Rule Catalog

Local catalog of Supabase security rules known to the auditor. Each entry
provides a severity override, a remediation URL, and fallback remediation text
used when the Supabase advisor API response has an empty `remediation` field.

## How the auditor resolves remediation

For each finding with `source: supabase-advisor`:

1. If the advisor response includes a non-empty `remediation` URL, use it.
2. Otherwise, look up the advisor `name` in this catalog and use the
   `remediation_url` + `remediation_text` below.
3. If neither the API nor this catalog has a match, the filed issue shows
   `See Supabase Database Advisor docs for <rule_id>` as a neutral placeholder
   and the unknown `name` is logged to terminal.

Catalog entries are keyed by `rule_id` — that is, the advisor `name` field for
API findings or the static detector id for `supabase-schema` / `supabase-config`
findings. All severities here are the plugin's adjusted severity; the advisor
`level` field is consulted only as a fallback when a rule is not in this
catalog.

## Catalog

### Advisor rules (API source)

#### `rls_disabled_in_public`
- **severity**: critical
- **remediation_url**: https://supabase.com/docs/guides/database/postgres/row-level-security
- **remediation_text**: Enable Row Level Security on this table:
  `ALTER TABLE <schema>.<table> ENABLE ROW LEVEL SECURITY;` and add policies
  that restrict access to `auth.uid()` or a specific role. A table in the
  `public` schema with RLS disabled is readable by anyone with the anon key.
- **notes**: The single highest-impact misconfiguration. Any table reachable
  through PostgREST / the client SDK must have RLS enabled.

#### `policy_exists_rls_disabled`
- **severity**: critical
- **remediation_url**: https://supabase.com/docs/guides/database/postgres/row-level-security
- **remediation_text**: Policies are defined on this table but RLS itself is
  not enabled, so the policies have no effect. Run
  `ALTER TABLE <schema>.<table> ENABLE ROW LEVEL SECURITY;`.
- **notes**: Often indicates a developer intended to secure the table but
  forgot the `ENABLE` statement.

#### `rls_enabled_no_policy`
- **severity**: medium
- **remediation_url**: https://supabase.com/docs/guides/database/postgres/row-level-security
- **remediation_text**: RLS is enabled on this table but no policies are
  defined, so no role can read or write. Either add policies scoped to
  `auth.uid()` / a role, or disable RLS if the table is intentionally empty of
  client access.
- **notes**: Symptom of incomplete migration. Medium because data is not
  exposed — the table is simply unreachable.

#### `security_definer_view`
- **severity**: high
- **remediation_url**: https://supabase.com/docs/guides/database/database-linter?lint=0010_security_definer_view
- **remediation_text**: This view runs with the permissions of its owner
  (typically `postgres`), bypassing the querying user's RLS. Recreate the view
  with `security_invoker=true` or convert it to a function that pins
  `search_path` and is `SECURITY INVOKER`.
- **notes**: Classic RLS bypass pattern.

#### `function_search_path_mutable`
- **severity**: high
- **remediation_url**: https://supabase.com/docs/guides/database/database-linter?lint=0011_function_search_path_mutable
- **remediation_text**: Add `SET search_path = ''` (or an explicit schema list)
  to the function definition. A `SECURITY DEFINER` function with a mutable
  `search_path` is vulnerable to search-path hijacking — an attacker who can
  create objects in any schema on the path can inject code that runs as the
  function owner.
- **notes**: Only applies to `SECURITY DEFINER` functions; `SECURITY INVOKER`
  is unaffected.

#### `auth_users_exposed`
- **severity**: critical
- **remediation_url**: https://supabase.com/docs/guides/database/database-linter?lint=0002_auth_users_exposed
- **remediation_text**: A view or function in an API-exposed schema references
  `auth.users`, leaking user identifiers, emails, and metadata to any
  authenticated or anon client. Remove the `auth.users` reference or move the
  view to a non-exposed schema.
- **notes**: Email enumeration / user discovery vector.

#### `extension_in_public`
- **severity**: high
- **remediation_url**: https://supabase.com/docs/guides/database/database-linter?lint=0014_extension_in_public
- **remediation_text**: Move the extension to a dedicated schema (typically
  `extensions`): `DROP EXTENSION <name>; CREATE EXTENSION <name> SCHEMA
  extensions;`. Extensions in `public` pollute the namespace and can mask
  functions via search-path manipulation.
- **notes**: Usually safe to fix in a migration, but verify the extension's
  functions aren't referenced unqualified elsewhere.

#### `extension_versions_outdated`
- **severity**: medium
- **remediation_url**: https://supabase.com/docs/guides/database/extensions
- **remediation_text**: Upgrade the extension to the latest available version:
  `ALTER EXTENSION <name> UPDATE;`. Outdated extensions may ship with known
  CVEs.

#### `auth_leaked_password_protection`
- **severity**: high
- **remediation_url**: https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection
- **remediation_text**: Enable leaked-password protection in the Supabase
  dashboard under Authentication → Providers → Email. When enabled, Supabase
  checks new passwords against HaveIBeenPwned and rejects known-breached
  passwords.
- **notes**: No SQL fix — dashboard setting only.

#### `auth_otp_long_expiry`
- **severity**: medium
- **remediation_url**: https://supabase.com/docs/guides/auth/auth-email-passwordless
- **remediation_text**: Reduce OTP expiry to 3600 seconds (1 hour) or less in
  Authentication → Providers → Email. Long-lived OTPs extend the window for
  interception attacks.

#### `auth_insufficient_mfa_options`
- **severity**: medium
- **remediation_url**: https://supabase.com/docs/guides/auth/auth-mfa
- **remediation_text**: Enable at least one MFA factor (TOTP recommended) in
  Authentication → Multi-Factor Authentication.

#### `no_primary_key`
- **severity**: low
- **remediation_url**: https://supabase.com/docs/guides/database/database-linter?lint=0001_no_primary_key
- **remediation_text**: Add a primary key to the table. Not a direct security
  issue, but tables without primary keys break Supabase Realtime replication
  and complicate auditing.
- **notes**: Logged only; not filed as an issue (below medium threshold).

### Static rules (migration source — `supabase-schema`)

#### `missing_rls`
- **severity**: critical
- **remediation_url**: https://supabase.com/docs/guides/database/postgres/row-level-security
- **remediation_text**: This migration creates a table in `public` without
  enabling RLS. Append `ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;` and
  add policies before deploying.
- **detector**: `CREATE TABLE` in schema `public` with no matching
  `ENABLE ROW LEVEL SECURITY` in the same migration file.

#### `policy_allows_all`
- **severity**: critical
- **remediation_url**: https://supabase.com/docs/guides/database/postgres/row-level-security#policies
- **remediation_text**: A policy with `USING (true)` or `WITH CHECK (true)`
  grants unconditional access. Scope it to `auth.uid() = user_id` or a role
  check. If the table is intentionally world-readable, add a comment
  documenting that and suppress the finding.
- **detector**: `CREATE POLICY` followed by `USING (true)` or `WITH CHECK (true)`.

#### `security_definer_no_search_path`
- **severity**: high
- **remediation_url**: https://supabase.com/docs/guides/database/database-linter?lint=0011_function_search_path_mutable
- **remediation_text**: Append `SET search_path = ''` (or an explicit schema
  list) to the function definition. Without this, the function is vulnerable
  to search-path hijacking.
- **detector**: `CREATE FUNCTION ... SECURITY DEFINER` with no
  `SET search_path` clause in the same statement.

#### `grant_to_anon`
- **severity**: high
- **remediation_url**: https://supabase.com/docs/guides/database/postgres/roles
- **remediation_text**: `GRANT` statements targeting `anon` expose data to
  unauthenticated clients. Replace with `authenticated` or revoke entirely
  and use RLS policies instead.
- **detector**: `GRANT ... TO anon` on a table.

#### `view_references_auth_users`
- **severity**: critical
- **remediation_url**: https://supabase.com/docs/guides/database/database-linter?lint=0002_auth_users_exposed
- **remediation_text**: Views in `public` or any API-exposed schema must not
  reference `auth.users` or `auth.identities`. Remove the reference or move
  the view to a non-exposed schema.
- **detector**: `CREATE OR REPLACE VIEW` (or `CREATE VIEW`) with body
  referencing `auth.users` / `auth.identities`.

### Static rules (config.toml source — `supabase-config`)

#### `weak_password_policy`
- **severity**: medium
- **remediation_url**: https://supabase.com/docs/guides/auth/password-security
- **remediation_text**: Set `[auth] minimum_password_length = 12` (or higher)
  in `supabase/config.toml`. The current value is below 10. Note: production
  auth config lives in the Supabase dashboard — this finding reflects
  developer intent for local environments.

#### `signup_without_confirmation`
- **severity**: medium
- **remediation_url**: https://supabase.com/docs/guides/auth/auth-email
- **remediation_text**: Either set `[auth.email] enable_confirmations = true`
  or set `[auth] enable_signup = false`. Signup without email confirmation
  allows account creation with arbitrary addresses.

#### `api_schemas_overexposed`
- **severity**: medium
- **remediation_url**: https://supabase.com/docs/guides/api#api-schemas
- **remediation_text**: Remove non-default schemas from `[api] schemas`. The
  default exposed set is `["public", "graphql_public", "storage"]`; every
  additional schema exposes its tables and functions to PostgREST.

## Adding new rules

New advisor rules show up over time as Supabase updates its linter. When the
auditor encounters a rule not in this catalog:

1. The finding is still filed (using the API-returned `remediation` if
   present).
2. The unknown rule name is logged to terminal.
3. Add the rule to this catalog in a follow-up change so the severity and
   fallback remediation are both captured for future scans.
