# Finding Severity Rubric

Use this rubric to validate and override tool-reported severity before filing
issues.  Tool-reported severity is a starting point, not the final word.

## Severity Levels

| Level | File as Issue? | Label | Definition |
|-------|---------------|-------|------------|
| critical | Yes | security | Hardcoded secrets, exposed credentials, known exploitable CVE (CVSS ≥ 9.0) |
| high | Yes | security | Known CVE (CVSS 7.0–8.9), injection vulnerability, broken auth pattern |
| medium | Yes | security | Known CVE (CVSS 4.0–6.9), SSRF pattern, insecure deserialization, prototype pollution |
| low | No (log only) | — | Informational, best-practice deviation, low-CVSS CVE |

## Override Rules

These rules take precedence over tool-reported severity:

1. **Secrets are always critical.**  Any finding from `p/secrets` is elevated
   to `critical` regardless of what semgrep reports.

2. **npm-audit critical maps to critical.**  npm's own `critical` level stays
   `critical`.  npm's `high` maps to `high`.  npm's `moderate` maps to
   `medium`.  npm's `low` maps to `low`.

3. **Semgrep INFO is always low.**  Never file an issue for INFO-level semgrep
   findings.

4. **Context matters for SSRF and injection.**  If the finding is in a test
   file (`*.test.*`, `*.spec.*`, `__tests__/`), downgrade one severity level.
   A high becomes medium; a medium becomes low (and is not filed).

## Common False Positive Patterns

These patterns frequently generate false positives.  Note them but do not
suppress automatically — use the suppression mechanism for confirmed false
positives.

- `nodejsscan` flagging `eval()` inside template engines (intentional)
- `semgrep` flagging `Math.random()` in non-security contexts
- `npm-audit` flagging dev-only dependencies for vulnerabilities that only
  affect runtime use
