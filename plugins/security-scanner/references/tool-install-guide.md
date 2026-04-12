# Tool Install Guide

The security-runner agent checks for and installs these tools before scanning.
All tools are installed as dev dependencies or via npx — no global installs.

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

## Tool Failure Handling

If a tool fails to install or run:
1. Log the error to terminal.
2. Skip that tool's findings section in the report.
3. Note the skip in the JSON report under a top-level `skipped_tools` array.
4. Continue with remaining tools.

Do not stop the entire scan because one tool fails.
