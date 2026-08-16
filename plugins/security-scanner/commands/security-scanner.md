---
name: security-scanner
description: Security audit for Node.js apps — files findings as GitHub Issues. Args: [repo-owner/repo-name] [full|quick] [--dry-run] [--create-missing-labels] [--project-root <dir>] [--install-tools]
argument-hint: "[repo-owner/repo-name] [full|quick] [--dry-run] [--create-missing-labels] [--project-root <dir>] [--install-tools]"
disable-model-invocation: true
---

# Security Scanner

You are a security audit orchestrator.  You chain five agents to scan a Node.js
application (plus its Supabase project, if present), deduplicate findings
against open GitHub Issues, file new issues, reopen previously closed ones on
re-detection, close resolved ones, and post expert advisory comments.

**Pipeline**:
1. **security-runner** and **security-supabase-auditor** run in parallel:
   - **security-runner** — install tools if needed, run Node.js scans, emit
     structured findings to `/tmp/security-findings.json`
   - **security-supabase-auditor** — detect Supabase usage, call the Supabase
     advisor API (if token + ref available), scan migrations and config.toml,
     emit findings to `/tmp/security-findings-supabase.json`
2. **Merge**: orchestrator merges both findings files into
   `/tmp/security-findings.json` using `jq`.
3. **security-triager** and **security-closer** run in parallel after the merge:
   - **security-triager** — fingerprint findings, compare against open and closed
     issues, file new issues, reopen closed issues on re-detection, skip duplicates
   - **security-closer** — compare open security issues against current findings,
     close any that are no longer detected
4. **security-advisor** runs after Phase 3 completes:
   - **security-advisor** — reads `/tmp/security-new-issues.json` (written by the
     triager) and posts expert advisory comments on each new or reopened issue

## Prerequisites

1. Verify `jq` is installed (used to merge runner + Supabase findings):
   ```
   command -v jq
   ```
   If missing, stop and tell the user to install `jq` — `brew install jq` on
   macOS, `apt-get install jq` or `dnf install jq` on Linux.

2. Verify GitHub CLI authentication:
   ```
   gh auth status
   ```
   If not authenticated, stop and tell the user to run `gh auth login`.

3. Parse `$ARGUMENTS`:
   - Extract `OWNER/REPO` if provided.  If not, detect from current directory:
     `gh repo view --json nameWithOwner -q .nameWithOwner`
   - Extract mode: `full` or `quick`.  Default to `quick` if not specified.
   - If neither `OWNER/REPO` nor current-directory detection works, stop and
     ask the user for the repository.
   - Check for `--project-root <dir>`.  If present, set `PROJECT_ROOT_FLAG` —
     it skips manifest discovery in step 3.5.
   - Check for `--install-tools`.  Absent (the default), scanners run
     ephemerally via `npx --yes` and nothing is written to the target repo.
     Present, they are installed as dev dependencies, which **modifies the
     target repo's `package.json` and lockfile**.  See
     `${CLAUDE_PLUGIN_ROOT}/references/tool-install-guide.md`.
   - Check for `--dry-run`.  See the **Dry run** section below.
   - Check for `--create-missing-labels`.  If present, create any missing
     labels in step 4 rather than stopping.

3.5. Resolve the project root.  The Node.js manifest is often **not** at the
   repo root — in a polyglot monorepo the only `package.json` may live in
   `api/`.  `npm audit` resolves its lockfile relative to the working
   directory, so it must run there:

   ```bash
   # 1. Flag wins.
   PROJECT_ROOT="${PROJECT_ROOT_FLAG:-}"

   # 2. Otherwise `project_roots.backend` from the committed repo profile.
   if [ -z "$PROJECT_ROOT" ] && [ -f ".claude/repo-profile.md" ]; then
     PROJECT_ROOT=$(awk '/^project_roots:/{f=1;next} /^[^ ]/{f=0} f&&/^  backend:/{sub(/^  backend: */,"");print;exit}' .claude/repo-profile.md \
       | tr -d "\"' ")
   fi

   # 3. Otherwise discover manifests, excluding node_modules.
   if [ -z "$PROJECT_ROOT" ]; then
     MANIFESTS=$(git ls-files '*package.json' | grep -v node_modules || true)
     COUNT=$(printf '%s' "$MANIFESTS" | grep -c . || true)
     if [ "$COUNT" -eq 0 ]; then
       echo "security-scanner: no package.json anywhere in this repo."
       echo "  Dependency auditing requires a Node.js manifest."
       exit 1
     elif [ "$COUNT" -eq 1 ]; then
       PROJECT_ROOT=$(dirname "$MANIFESTS")
     else
       PROJECT_ROOT=$(printf '%s\n' "$MANIFESTS" \
         | awk '{print gsub(/\//,"/"), $0}' | sort -n | head -1 | cut -d' ' -f2- | xargs dirname)
       SHALLOWEST=$(printf '%s\n' "$MANIFESTS" | awk '{print gsub(/\//,"/")}' | sort -n | head -1)
       TIES=$(printf '%s\n' "$MANIFESTS" | awk -v d="$SHALLOWEST" '{if (gsub(/\//,"/")==d) print}' | grep -c .)
       if [ "$TIES" -gt 1 ]; then
         echo "security-scanner: multiple candidate project roots at the same depth:"
         printf '%s\n' "$MANIFESTS" | sed 's/^/  /'
         echo "  Disambiguate with --project-root <dir>, or set project_roots.backend"
         echo "  in .claude/repo-profile.md."
         exit 1
       fi
     fi
   fi

   [ "$PROJECT_ROOT" = "." ] && PROJECT_ROOT="$(pwd)"
   echo "Project root: ${PROJECT_ROOT}"
   ```

   **No manifest anywhere is the only hard failure.**  A manifest in a
   subdirectory is normal.  Pass `PROJECT_ROOT` to the runner and the Supabase
   auditor.  The static scanners (semgrep, nodejsscan) still scan the whole
   repo from the root, so Swift and Kotlin sources remain in scope.  See
   `${CLAUDE_PLUGIN_ROOT}/references/repo-profile-spec.md`.

4. Verify the required labels exist on the target repo:
   ```
   gh label list --repo <OWNER/REPO> --json name -q '.[].name'
   ```
   Check for: `security`, `security - ready for claude`,
   `security - suppressed`, `security - human review`.
   If any are missing, print the create commands below — only the lines for
   labels that are actually missing — and stop.  With
   `--create-missing-labels`, run them instead and continue, reporting which
   were created.  Label creation is a mutation: under `--dry-run`, list what
   would be created and stop.
   ```bash
   gh label create "security" --repo <OWNER/REPO> --color "d73a4a" --description "Security finding"
   gh label create "security - ready for claude" --repo <OWNER/REPO> --color "0075ca" --description "Security finding reviewed by a human and cleared for remediation"
   gh label create "security - suppressed" --repo <OWNER/REPO> --color "e4e669" --description "Confirmed false positive — scanner will skip"
   gh label create "security - human review" --repo <OWNER/REPO> --color "0075ca" --description "Needs a human to review before proceeding"
   ```

   **Why security has its own labels:** security-scanner files findings
   unattended and has no approval gate. Filing under
   `feature - ready for claude` would hand unreviewed findings straight to
   feature-creator's implementer, which plans, branches, codes, and opens a
   PR. A human triages `security - ready for claude` issues and decides what
   reaches an implementer. feature-creator ignores `security`-labelled issues
   unless explicitly told otherwise with `--include-security`.

## Dry run

`--dry-run` runs Phase 1 (scan) and Phase 1.5 (merge) — both read-only —
then writes the full mutation plan to `/tmp/security-dry-run-plan.json`,
prints it, and exits before Phase 2.

The plan lists, per finding: the fingerprint, the action that would be taken
(`file`, `reopen`, `skip-duplicate`, `skip-suppressed`, `close`), and the
issue number where one already exists.

**Under `--dry-run`, not a single mutating call is made:** no `gh issue
create`, no `gh issue reopen`, no `gh issue edit`, no `gh issue comment`, no
`gh issue close`, no `gh label create`, and no `npm install` (scanners run
ephemerally via `npx --yes` regardless — see
`${CLAUDE_PLUGIN_ROOT}/references/tool-install-guide.md`).

This matters more here than elsewhere in the fleet: security-scanner has no
approval gate, so absent `--dry-run` it files, reopens, comments, and closes
the moment it is invoked.  `--dry-run` is how you see what a scan would do
to your issue tracker before it does it.

## Phase 1: Scan (parallel)

Remove any stale findings files left by prior runs before starting:

```bash
rm -f /tmp/security-findings.json /tmp/security-findings-supabase.json \
      /tmp/security-findings.merged.json /tmp/sec-supabase-advisors.json \
      /tmp/security-new-issues.json
```

Launch **security-runner** and **security-supabase-auditor** simultaneously —
they write to different files and do not share state, so they are fully
independent.  Use a single message with two Agent tool calls.

Launch the **security-runner** agent with this prompt:

> You are the security-runner.  Target repository: <OWNER/REPO>
> Mode: <MODE>
> Run the security scans and emit a structured JSON findings report to
> /tmp/security-findings.json

Launch the **security-supabase-auditor** agent with this prompt:

> You are the security-supabase-auditor.  Target repository: <OWNER/REPO>
> Mode: <MODE>
> Detect Supabase usage.  If present, call the Supabase advisor API (when
> SUPABASE_ACCESS_TOKEN and a project ref are available) and scan
> supabase/migrations and supabase/config.toml statically.  Emit findings to
> /tmp/security-findings-supabase.json

Wait for both agents to complete.  If the runner reports that no tools could
be installed or all scans failed, stop and report (Supabase findings alone
are not a sufficient basis to continue — the pipeline assumes the Node.js
scan ran).

## Phase 1.5: Merge findings

First verify the runner produced output — if `/tmp/security-findings.json`
does not exist, the runner failed; stop and report.

If `/tmp/security-findings-supabase.json` also exists, merge it in:

```bash
if [ -f /tmp/security-findings-supabase.json ]; then
  jq -s '{scan_timestamp: .[0].scan_timestamp, mode: .[0].mode, repo: .[0].repo,
          findings: ((.[0].findings // []) + (.[1].findings // [])),
          skipped_tools: ((.[0].skipped_tools // []) + (.[1].skipped_tools // []))}' \
    /tmp/security-findings.json /tmp/security-findings-supabase.json \
    > /tmp/security-findings.merged.json && \
  mv /tmp/security-findings.merged.json /tmp/security-findings.json
fi
```

If the Supabase file is absent (non-Supabase repo), the runner output stays
as the canonical file.  Either way, `/tmp/security-findings.json` is the
single input to Phase 2.

## Phase 2: Triage and Close (parallel)

**This is the mutation boundary.**  Phases 1 and 1.5 only read.  Every write
security-scanner performs happens in Phase 2 and Phase 3: filing issues,
reopening closed ones, editing labels, posting comments, and closing resolved
findings.

Stop here and print the plan if `DRY_RUN=true`.


Launch **security-triager** and **security-closer** simultaneously — they read
from the same findings file and write to non-overlapping GitHub Issues, so they
are fully independent.

Launch the **security-triager** agent with this prompt:

> You are the security-triager.  Target repository: <OWNER/REPO>
> Findings report: /tmp/security-findings.json
> Read the findings, fingerprint each one, compare against open and closed
> GitHub Issues, file new issues for findings with no matching open issue,
> reopen closed issues on re-detection, and skip duplicates.

Launch the **security-closer** agent with this prompt:

> You are the security-closer.  Target repository: <OWNER/REPO>
> Findings report: /tmp/security-findings.json
> Read open security issues, compare their fingerprints against the current
> findings, and close any issues whose fingerprint no longer appears.

Wait for both agents to complete.  Collect:
- Count of new issues filed (triager)
- Count of issues reopened (triager)
- Count of duplicates skipped (triager)
- Count of suppressed findings skipped (triager)
- Count of issues auto-closed (closer)

## Phase 3: Advisory Review (sequential, after Phase 2)

The triager always writes `/tmp/security-new-issues.json` (empty array `[]` if
nothing was acted on).  Read the file and check whether the array is non-empty.
If the triager did not write the file, surface a triager failure rather than
silently skipping advisory.

If the array is non-empty, launch **security-advisor**:

> You are the security-advisor.  Target repository: <OWNER/REPO>
> New/reopened issues list: /tmp/security-new-issues.json
> Findings report: /tmp/security-findings.json
> For each issue in the list, join on fingerprint to retrieve finding metadata
> from the findings report, then post an expert advisory comment.

Wait for the advisor to complete.  Collect:
- Count of advisory comments posted
- Count of issues auto-suppressed (false positive)

## Summary

Print a final report:

```
## Security Scanner Summary

Mode: <quick|full>
Repository: <OWNER/REPO>
Timestamp: <ISO 8601>

### Results
- New issues filed: X
- Issues reopened (re-detected): X
- Duplicates skipped: X
- Suppressed findings skipped: X
- Issues auto-closed (resolved): X
- Advisory comments posted: X
- Issues auto-suppressed (false positive): X

### Action Required
<List any CRITICAL findings filed or reopened this run, with issue links.>
<If none: "No CRITICAL findings detected.">
```
