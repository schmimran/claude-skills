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

## Collision Policy

Line-band collisions (two different findings in the same 10-line window of the
same file from the same rule) are acceptable — they will be treated as the same
finding.  In practice this is rare.  If it causes problems in a specific file,
the suppression mechanism handles it.
