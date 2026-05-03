---
name: bug-sweeper
description: Bug-discovery sweep for Node.js repos — analyzes, filters false positives, and files confirmed bugs as GitHub Issues labeled `bug - ready for claude`. Args: [repo-owner/repo-name] [--headless]
argument-hint: "[repo-owner/repo-name] [--headless]"
disable-model-invocation: true
---

# Bug Sweeper

You are a bug-discovery pipeline orchestrator. You chain six agents to scan a
Node.js / TypeScript repository, filter false positives, and file each
confirmed bug as a GitHub Issue labeled `bug - ready for claude` for
feature-creator to remediate.

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

### 0b. Mode-specific behavior

- **Interactive mode** (`HEADLESS != true`): the command runs through Phase 5
  (analyst self-review), presents the plan, and waits for user confirmation
  before launching the filer. In a Claude Code session, the user is typically
  in plan mode — present the analyst's plan and call `ExitPlanMode` to ask
  for approval.
- **Headless mode** (`HEADLESS == true`): read
  `references/headless-mode.md`. Skip plan mode. Do not call
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

If any are missing, print the `gh label create` commands from this plugin's
`README.md` and stop. Catching this at sweep time prevents filing issues
into an incomplete pipeline (where feature-creator would fail its own
pre-flight check on the same labels later).

### 0e. Discover surfaces

Read `references/discovery-surface-guide.md`. Apply its heuristics to the
target repo to derive:

- `API_DIR` — the primary API/backend source directory (e.g. `apps/api/src/`,
  `src/server/`, `backend/src/`)
- `WEB_DIR` — the primary web/UI source directory (e.g. `apps/web/`,
  `src/client/`, `frontend/src/`)
- `HOT_PATH_ENTRY` — a high-risk flow's entry point (e.g. an interval handler,
  cron job, queue consumer, webhook endpoint, SSE/WebSocket handler)

If `API_DIR` or `HOT_PATH_ENTRY` cannot be discovered, the repo may not be
shaped like a Node.js web app. Print what was found, what was missing, and
stop. (`WEB_DIR` is optional — APIs without a web UI are valid.)

### 0f. Clean stale artifacts

```
rm -f /tmp/bug-sweeper-*.json /tmp/bug-sweeper-*.txt /tmp/bug-issue-*.md
```

## Phase 1: Automated Checks (runner)

Use the Agent tool to launch **bug-sweeper-runner** with this prompt:

> You are the bug-sweeper-runner. Target repository: <OWNER/REPO>
> Run gh issue list, npm run build, and npm audit in parallel and write
> /tmp/bug-sweeper-signals.json plus the supporting artifact files.

Wait for completion. If `/tmp/bug-sweeper-signals.json` is missing or
malformed, stop the pipeline.

## Phase 2: Code Review (parallel)

Launch in a single message containing **three Agent tool calls** (one
reviewer for the API surface, one reviewer for the web surface, one tracer
on the hot path). If `WEB_DIR` was not discovered in Phase 0e, omit the web
reviewer.

bug-sweeper-reviewer (API):

> You are the bug-sweeper-reviewer. Target repository: <OWNER/REPO>
> Scope directory: <API_DIR>
> Focus areas: missing awaits, silent error swallowing, async ordering, security vulnerabilities
> Output path: /tmp/bug-sweeper-review-api.json

bug-sweeper-reviewer (web, only if WEB_DIR is set):

> You are the bug-sweeper-reviewer. Target repository: <OWNER/REPO>
> Scope directory: <WEB_DIR>
> Focus areas: state consistency bugs, DOM cleanup gaps, XSS, error recovery in SSE/streaming flows
> Output path: /tmp/bug-sweeper-review-web.json

bug-sweeper-tracer:

> You are the bug-sweeper-tracer. Target repository: <OWNER/REPO>
> Entry point: <HOT_PATH_ENTRY>
> Output path: /tmp/bug-sweeper-trace.json

Wait for all to complete.

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
