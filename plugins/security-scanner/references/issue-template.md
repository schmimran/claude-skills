# Security Issue Template

Use this template when filing security findings as GitHub Issues.
The `<!-- fingerprint: ... -->` comment on the last line is required —
the security-closer agent uses it to identify resolved findings.

---

```markdown
## Security Finding

**Severity**: <CRITICAL|HIGH|MEDIUM>
**Source**: <npm-audit|semgrep-owasp|semgrep-secrets|nodejsscan>
**Rule**: `<rule_id>`
**File**: `<file>` (line <line_start>–<line_end>)
**Detected**: <ISO 8601 timestamp>

### Description

<message — full finding detail from the tool>

### Recommendation

<recommendation if available, otherwise "See rule documentation for <rule_id>">

### Suppression

If this is a confirmed false positive, add the label `security - suppressed`
to this issue.  The scanner will skip it on future runs.  Leave the issue open
with the suppressed label — do not close it.  Add a comment explaining why it
is a false positive.

<!-- fingerprint: <hex> -->
<!-- supabase_cache_key: <key or none> -->
```

The `supabase_cache_key` comment is populated only for findings from the
Supabase advisor API (`source: supabase-advisor`).  For all other findings it
renders as `<!-- supabase_cache_key: none -->` and can be ignored.
