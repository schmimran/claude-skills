---
name: bug-sweeper
description: Bug-discovery sweep for Node.js, Swift, and Kotlin repos — analyzes, filters false positives, and files confirmed bugs as GitHub Issues labeled `bug - ready for claude`. Args: [repo-owner/repo-name] [--headless] [--dry-run] [--create-missing-labels] [--project-root <dir>] [--languages <list>]
argument-hint: "[repo-owner/repo-name] [--headless] [--dry-run] [--create-missing-labels] [--project-root <dir>] [--languages <list>]"
disable-model-invocation: true
---

# Bug Sweeper

You are a bug-discovery pipeline orchestrator. You chain six agents to scan a
repository, filter false positives, and file each confirmed bug as a GitHub
Issue labeled `bug - ready for claude` for feature-creator to remediate.

Build and dependency-audit signals require a Node.js manifest, which may live
in a subdirectory. Code review covers TypeScript/JavaScript, Swift, and
Kotlin, so a polyglot repo is reviewed across all of its surfaces.

**Pipeline**:
1. **bug-sweeper-runner** — gh issue list + npm run build + npm audit (parallel Bash)
2. **bug-sweeper-reviewer** ×N + **bug-sweeper-tracer** — code-review pass on discovered surfaces (parallel)
3. **bug-sweeper-reconciler** — classify open `bug` issues against current code
4. **bug-sweeper-analyst** — apply false-positive rubric, assign severity, compose plan
5. Self-review (collapsed into the analyst)
6. **bug-sweeper-filer** — file each confirmed bug as a GitHub Issue

This command is **find-only**. It does not propose fixes, plan code changes,
or modify the repo. Remediation is handled by `/feature-creator` after the
issues are filed.

## Phase 0: Mode Detection and Prerequisites

### 0a. Parse `$ARGUMENTS`

- Extract `OWNER/REPO`. If not given, detect from the current directory:
  ```
  gh repo view --json nameWithOwner -q .nameWithOwner
  ```
  If neither works, stop and ask the user for the repository.
- Check for the `--headless` flag. If present, set `HEADLESS=true`.
- Check for `--dry-run`. If present, set `DRY_RUN=true`. See **Dry run** below.
- Check for `--create-missing-labels`. If present, create any missing labels
  in step 0d rather than stopping.
- Check for `--project-root <dir>`. If present, set `PROJECT_ROOT_FLAG` — it
  skips manifest discovery entirely in step 0e.
- Check for `--languages <list>` (comma-separated, e.g.
  `typescript,swift,kotlin`). If present, set `LANGUAGES` and review only
  those. If absent, resolve from `languages:` in `.claude/repo-profile.md`,
  and failing that review every language present in each scope directory.

### 0b. Mode-specific behavior

- **Interactive mode** (`HEADLESS != true`): the command runs through Phase 5
  (analyst self-review), presents the plan, and waits for user confirmation
  before launching the filer. In a Claude Code session, the user is typically
  in plan mode — present the analyst's plan and call `ExitPlanMode` to ask
  for approval.
- **Headless mode** (`HEADLESS == true`): read
  `${CLAUDE_PLUGIN_ROOT}/references/headless-mode.md`. Skip plan mode. Do not call
  `AskUserQuestion`. Run all phases end-to-end. The Phase 5 self-review (in
  the analyst) replaces human approval. This mode is intended for invocation
  from a `/schedule` routine running in permissions-bypass mode.

### 0c. Verify GitHub CLI

```
gh auth status
```

If not authenticated, stop and tell the user to run
`gh auth login`.

### 0d. Verify required labels

```
gh label list --repo <OWNER/REPO> --json name -q '.[].name'
```

bug-sweeper files issues into `feature-creator`'s bug state machine, so the
**entire** state machine must exist on the target repo — not just the labels
bug-sweeper directly applies. Verify all of:

- `bug` (existing convention)
- `bug - ready for claude` (applied by filer)
- `bug - triaged` (applied by feature-creator's triager)
- `bug - planned` (applied by feature-creator's planner)
- `bug - human review` (applied by feature-creator's reviewer/implementer on escalation)
- `bug - in progress` (applied by feature-creator's implementer)
- `bug - complete` (applied by feature-creator's implementer)
- `bug - high` / `bug - medium` / `bug - low` (applied by filer per analyst severity)

If any are missing, print the **exact** `gh label create` command for each
missing label — copy-pasteable, not a pointer to the README — then stop:

```bash
gh label create "bug" --repo <OWNER/REPO> --force --color d73a4a --description "Defect in the codebase"
gh label create "bug - ready for claude" --repo <OWNER/REPO> --force --color 0E8A16 --description "Bug ready for automated planning (typically filed by bug-sweeper)"
gh label create "bug - triaged" --repo <OWNER/REPO> --force --color 1D76DB --description "Triaged into a bucket; planner will pick it up"
gh label create "bug - planned" --repo <OWNER/REPO> --force --color 1D76DB --description "Implementation plan posted as comment"
gh label create "bug - human review" --repo <OWNER/REPO> --force --color D93F0B --description "Flagged for human review (high-risk or failed)"
gh label create "bug - in progress" --repo <OWNER/REPO> --force --color FBCA04 --description "Branch created, implementation underway"
gh label create "bug - complete" --repo <OWNER/REPO> --force --color 0E8A16 --description "PR created and code-reviewed"
gh label create "bug - high" --repo <OWNER/REPO> --force --color B60205 --description "High-severity bug — data loss, security, hot-path crash, partial commit"
gh label create "bug - medium" --repo <OWNER/REPO> --force --color D93F0B --description "Medium-severity bug — non-critical regression, leak, UI consistency"
gh label create "bug - low" --repo <OWNER/REPO> --force --color FBCA04 --description "Low-severity bug — cosmetic, doc drift, defensive-coding gap"
```

Print only the lines for labels that are actually missing. Colors and
descriptions are feature-creator's canonical set (see the repo CLAUDE.md).

**`--create-missing-labels`**: if that flag was passed, run the commands
above for the missing labels instead of stopping, report which were
created, and continue. Label creation is a mutation — under `--dry-run`,
list what would be created and stop.

Catching this at sweep time prevents filing issues into an incomplete
pipeline (where feature-creator would fail its own pre-flight check on the
same labels later).

### 0e. Resolve the project root

The Node.js manifest is frequently **not** at the repo root — in a polyglot
monorepo the only `package.json` may live in `api/` alongside `iOS/` and
`Android/` trees. Resolve `PROJECT_ROOT` before any `npm` command runs:

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
    echo "bug-sweeper: no package.json anywhere in this repo."
    echo "  This repo has no Node.js surface to build or audit."
    exit 1
  elif [ "$COUNT" -eq 1 ]; then
    PROJECT_ROOT=$(dirname "$MANIFESTS")
  else
    # Prefer the shallowest manifest.
    PROJECT_ROOT=$(printf '%s\n' "$MANIFESTS" \
      | awk '{print gsub(/\//,"/"), $0}' | sort -n | head -1 | cut -d' ' -f2- | xargs dirname)
    SHALLOWEST_COUNT=$(printf '%s\n' "$MANIFESTS" \
      | awk '{print gsub(/\//,"/")}' | sort -n | head -1)
    TIES=$(printf '%s\n' "$MANIFESTS" | awk -v d="$SHALLOWEST_COUNT" '{if (gsub(/\//,"/")==d) print}' | grep -c .)
    if [ "$TIES" -gt 1 ]; then
      echo "bug-sweeper: multiple candidate project roots at the same depth:"
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

`.` (a root manifest) is the common case and still works. Pass `PROJECT_ROOT`
to the runner in Phase 1. See `${CLAUDE_PLUGIN_ROOT}/references/repo-profile-spec.md`.

**No manifest anywhere is the only hard failure.** A manifest in a
subdirectory is normal, not an error.

### 0e2. Discover surfaces

Read `${CLAUDE_PLUGIN_ROOT}/references/discovery-surface-guide.md`. Apply its heuristics to the
target repo to derive:

- `API_DIR` — the primary API/backend source directory (e.g. `apps/api/src/`,
  `src/server/`, `backend/src/`)
- `WEB_DIR` — the primary web/UI source directory (e.g. `apps/web/`,
  `src/client/`, `frontend/src/`)
- `HOT_PATH_ENTRY` — a high-risk flow's entry point (e.g. an interval handler,
  cron job, queue consumer, webhook endpoint, SSE/WebSocket handler)

Search relative to `PROJECT_ROOT` first, then the repo root. In a monorepo the
API directory is typically `${PROJECT_ROOT}/src`, and `project_roots` in the
repo profile may name the `ios` and `android` surfaces directly.

If `API_DIR` or `HOT_PATH_ENTRY` cannot be discovered, the repo may not be
shaped like a Node.js web app. Print what was found, what was missing, and
stop. (`WEB_DIR` is optional — APIs without a web UI are valid.)

### 0f. Clean stale artifacts

```
rm -f /tmp/bug-sweeper-*.json /tmp/bug-sweeper-*.txt /tmp/bug-issue-*.md
```

## Dry run

`--dry-run` runs every read-only phase — signals, review, reconciliation,
analysis, self-review — writes the full mutation plan to
`/tmp/bug-sweeper-plan.json`, prints it, and exits.

**Under `--dry-run`, not a single mutating call is made:** no `gh issue
create`, no `gh issue edit`, no `gh label create`, no `git` write, no `npm
install`, no file edit in the target repo. Phase 6 is skipped entirely.

`--dry-run` overrides `--headless`. If both are passed, the run is a dry
run: the approval gate is moot when nothing will be written.

The read-only phases are safe by construction — the reviewer and tracer
agents hold `tools: Glob, Grep, Read, TodoWrite` and have no write access at
all. The mutation boundary is Phase 6.

## Phase 1: Automated Checks (runner)

Use the Agent tool to launch **bug-sweeper-runner** with this prompt:

> You are the bug-sweeper-runner. Target repository: <OWNER/REPO>
> Project root (run all npm commands here, not at the repo root):
> <PROJECT_ROOT>
> Run gh issue list, npm run build, and npm audit in parallel and write
> /tmp/bug-sweeper-signals.json plus the supporting artifact files.

Wait for completion. If `/tmp/bug-sweeper-signals.json` is missing or
malformed, stop the pipeline.

## Phase 2: Code Review (parallel)

Launch in a single message containing one Agent tool call per discovered
surface (API, web, and any mobile surfaces), plus one tracer on the hot path.
If `WEB_DIR` was not discovered in Phase 0e2, omit the web reviewer.

bug-sweeper-reviewer (API):

> You are the bug-sweeper-reviewer. Target repository: <OWNER/REPO>
> Scope directory: <API_DIR>
> Languages: <LANGUAGES>
> Focus areas: missing awaits, silent error swallowing, async ordering, security vulnerabilities
> Output path: /tmp/bug-sweeper-review-api.json

bug-sweeper-reviewer (web, only if WEB_DIR is set):

> You are the bug-sweeper-reviewer. Target repository: <OWNER/REPO>
> Scope directory: <WEB_DIR>
> Languages: <LANGUAGES>
> Focus areas: state consistency bugs, DOM cleanup gaps, XSS, error recovery in SSE/streaming flows
> Output path: /tmp/bug-sweeper-review-web.json

bug-sweeper-reviewer (iOS, only if `project_roots.ios` is set and `swift` is
in scope):

> You are the bug-sweeper-reviewer. Target repository: <OWNER/REPO>
> Scope directory: <IOS_DIR>
> Languages: swift
> Focus areas: force unwraps on optional/network data, retain cycles in closures, main-thread violations on UI updates, unhandled async throws
> Output path: /tmp/bug-sweeper-review-ios.json

bug-sweeper-reviewer (Android, only if `project_roots.android` is set and
`kotlin` is in scope):

> You are the bug-sweeper-reviewer. Target repository: <OWNER/REPO>
> Scope directory: <ANDROID_DIR>
> Languages: kotlin
> Focus areas: null-assertion (!!) on nullable data, coroutine scope leaks, blocking calls on the main dispatcher, swallowed exceptions in try/catch
> Output path: /tmp/bug-sweeper-review-android.json

bug-sweeper-tracer:

> You are the bug-sweeper-tracer. Target repository: <OWNER/REPO>
> Entry point: <HOT_PATH_ENTRY>
> Output path: /tmp/bug-sweeper-trace.json

Wait for all to complete. Every reviewer emits the same finding shape
regardless of language, so Phases 3–6 need no per-language handling.

## Phase 3: Issue Reconciliation

Use the Agent tool to launch **bug-sweeper-reconciler** with this prompt:

> You are the bug-sweeper-reconciler. Target repository: <OWNER/REPO>
> Open bugs path: /tmp/bug-sweeper-open-bugs.json
> Output path: /tmp/bug-sweeper-reconciliation.json

Wait for completion.

## Phase 4: Analysis

Use the Agent tool to launch **bug-sweeper-analyst** with this prompt:

> You are the bug-sweeper-analyst. Target repository: <OWNER/REPO>
> Signals path: /tmp/bug-sweeper-signals.json
> Review paths: /tmp/bug-sweeper-review-api.json,<WEB_PATH if present>,/tmp/bug-sweeper-trace.json
> Reconciliation path: /tmp/bug-sweeper-reconciliation.json
> Output path: /tmp/bug-sweeper-plan.json

Wait for completion. If `/tmp/bug-sweeper-plan.json` is missing or malformed,
stop the pipeline.

## Phase 5: Self-Review and Approval Gate

The analyst already performed self-review (Step 6 of its protocol). The
orchestrator's job here is to apply the mode-specific approval gate.

**Empty-plan short-circuit (both modes):** Read
`/tmp/bug-sweeper-plan.json` and check `confirmed_bugs`. If the array is
empty, skip Phases 5 and 6 entirely — print "No confirmed bugs to file"
and proceed to the Summary. There is nothing to render or to file.

### Interactive mode

Print a human-readable rendering of the plan: confirmed bugs, false
positives discarded, open issues status, severity counts. Then call
`ExitPlanMode` so the user can review and approve before any GitHub
issue is filed.

If the user does not approve, stop the pipeline. The plan file remains at
`/tmp/bug-sweeper-plan.json` for inspection.

### Headless mode

Skip this entire phase — do not render the plan, do not call
`ExitPlanMode`, do not wait. Proceed directly to Phase 6.

## Phase 6: File Issues

**This is the mutation boundary.** Every write bug-sweeper performs happens
here: `gh issue create` for each confirmed bug, with its `bug`,
`bug - ready for claude`, and severity labels.

Skip this phase entirely if `DRY_RUN=true` — print the plan and stop.

Skip this phase if the empty-plan short-circuit fired in Phase 5.

Use the Agent tool to launch **bug-sweeper-filer** with this prompt:

> You are the bug-sweeper-filer. Target repository: <OWNER/REPO>
> Plan path: /tmp/bug-sweeper-plan.json
> Output path: /tmp/bug-sweeper-filed.json

Wait for completion.

## Summary

Print the final report:

```
## Bug Sweeper Pipeline Summary

Mode: <interactive|headless>
Repository: <OWNER/REPO>
Timestamp: <ISO 8601>

### Signals
- Build: <PASS|FAIL>
- npm audit: <severity counts>
- Open `bug` issues at start: <N>

### Findings
- Confirmed bugs: <N>
- False positives discarded: <N>
- Reconciled open issues: <still-open: X | fixed: X | docs-only: X>

### Filed
- Issues filed: <N>
- Skipped (existing issue): <N>
- Filing errors: <N>

| ID | Severity | Issue |
|----|----------|-------|
| bug-1 | HIGH | #142 |
| bug-2 | MEDIUM | #143 |

### Next Step
Run `/feature-creator <OWNER/REPO>` to remediate the filed bugs. The
remediation pipeline picks up issues labeled `bug - ready for claude`
alongside `feature - ready for claude`.
```

## Error Handling

- If a phase agent exits non-zero, stop the pipeline and report the error.
  Do not proceed to the next phase.
- The pipeline never modifies code on the target repo. The only writes are
  GitHub Issues created in Phase 6 by the filer.
- Headless mode does not suppress errors — an agent failure halts the
  pipeline. The scheduled-task runner records the failure in the routine
  log; the next scheduled run starts fresh.
