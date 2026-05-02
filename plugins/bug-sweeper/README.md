# bug-sweeper

Daily bug-discovery sweep for Node.js / TypeScript repositories. Runs build
and audit checks, launches multi-agent code review, filters false positives,
and files each confirmed bug as a labeled GitHub Issue. The downstream
[feature-creator](../feature-creator/) plugin remediates the filed issues.

This plugin is **find-only**. It does not propose fixes, plan code changes,
or modify the repo.

## Quick Start

1. **Install the marketplace** if you have not already: see [Installation in the root README](../../README.md#installation).

2. **Create the required labels** on your target repository (once per repo):
   ```bash
   gh label create "bug" \
     --color d73a4a \
     --description "Defect in the codebase"

   gh label create "bug - ready for claude" \
     --color 0E8A16 \
     --description "Bug filed by bug-sweeper, ready for feature-creator to remediate"

   gh label create "bug - high" \
     --color B60205 \
     --description "High-severity bug — data loss, security, hot-path crash, partial commit"

   gh label create "bug - medium" \
     --color D93F0B \
     --description "Medium-severity bug — non-critical regression, leak, UI consistency"

   gh label create "bug - low" \
     --color FBCA04 \
     --description "Low-severity bug — cosmetic, doc drift, defensive-coding gap"
   ```

   You also need feature-creator's bug state-machine labels — see the
   [feature-creator README](../feature-creator/README.md#quick-start) for
   the full list including `bug - triaged`, `bug - planned`,
   `bug - in progress`, `bug - complete`, and `bug - human review`.

3. **Run an interactive sweep** to inspect findings before any issues are
   filed:
   ```
   /bug-sweeper owner/repo
   ```
   The pipeline enters plan mode at Phase 5 and waits for your approval
   before filing any GitHub issue.

4. **Run a headless sweep** (typically from a `/schedule` routine in
   permissions-bypass mode):
   ```
   /bug-sweeper owner/repo --headless
   ```
   The analyst's Phase 5 self-review replaces human approval. Issues are
   filed automatically.

## Prerequisites

- **Node.js 18+** with `npm 7+` available in the shell (for `npm run build`
  and `npm audit`)
- **GitHub CLI** (`gh`) installed, on `PATH`, and authenticated
  (`gh auth status`)
- The target repository must be a Node.js / TypeScript project with a
  recognizable server entry point. See
  [`references/discovery-surface-guide.md`](references/discovery-surface-guide.md)
  for which directory layouts are recognized.
- Required labels created on the target repository (see Quick Start above)

## Architecture

| Component | Type | Model | Role |
|-----------|------|-------|------|
| `bug-sweeper` | Command | (inherits) | Orchestrates Phases 0–6 |
| `bug-sweeper-runner` | Agent | sonnet | Phase 1 — gh issue list, npm build, npm audit (parallel Bash) |
| `bug-sweeper-reviewer` | Agent | sonnet | Phase 2 — targeted code review of one directory |
| `bug-sweeper-tracer` | Agent | sonnet | Phase 2 — end-to-end trace of one high-risk flow |
| `bug-sweeper-reconciler` | Agent | sonnet | Phase 3 — classify open `bug` issues against current code |
| `bug-sweeper-analyst` | Agent | sonnet | Phase 4 + 5 — false-positive filter, severity, plan, self-review |
| `bug-sweeper-filer` | Agent | sonnet | Phase 6 — file confirmed bugs as GitHub Issues |

None of the discovery / review agents have `Write` or `Edit` access. Only
the filer touches GitHub. This enforces the "find only, never fix" boundary
at the tool layer.

## Pipeline

```
Target Repo
    |
    v
bug-sweeper-runner   (gh, npm build, npm audit — parallel Bash)
    |
    v
/tmp/bug-sweeper-signals.json
    |
    +------- bug-sweeper-reviewer (API surface) ------+
    +------- bug-sweeper-reviewer (web surface) ------+   (parallel)
    +------- bug-sweeper-tracer   (hot path)     -----+
    |
    v
bug-sweeper-reconciler   (classify open `bug` issues)
    |
    v
bug-sweeper-analyst   (false-positive filter, severity, self-review)
    |
    v
/tmp/bug-sweeper-plan.json
    |
    [Phase 5 approval gate — interactive only]
    |
    v
bug-sweeper-filer   (gh issue create with --body-file per bug)
    |
    v
GitHub Issues filed with `bug`, `bug - ready for claude`, severity label
```

## Modes

| Mode | Plan mode | Approval gate | Use case |
|------|-----------|---------------|----------|
| **Interactive** (default) | Enters plan mode at Phase 5 | User approves before filing | Manual run; human reviewing the bug list |
| **Headless** (`--headless`) | Skips plan mode | Self-review replaces approval | Scheduled routine in permissions-bypass mode |

## Coverage

| Bug class | Detected by |
|---|---|
| TypeScript build errors | runner (`npm run build`) |
| Dependency CVEs | runner (`npm audit`) |
| Missing awaits, silent error swallowing, async ordering | reviewer (API surface) |
| State consistency, DOM cleanup, XSS, SSE/streaming error recovery | reviewer (web surface) |
| End-to-end ordering / partial-commit / concurrency in a hot flow | tracer |
| Already-known bugs | reconciler (cross-checks open `bug` issues) |

## Severity → label

| Analyst severity | Label applied |
|---|---|
| HIGH | `bug - high` |
| MEDIUM | `bug - medium` |
| LOW | `bug - low` |

LOW-severity bugs are filed but feature-creator deprioritizes them — LOW
is a queue, not a discard.

## Issue body format

Every issue filed by bug-sweeper begins with the marker
`<!-- claude-bug-sweeper-v1 -->`. The body includes the file:line, severity,
root cause (one sentence), reproduction steps, and a "Suggested area to
investigate" pointer for the human reader. There is no "proposed fix"
section — that is feature-creator's responsibility.

See [`references/bug-issue-template.md`](references/bug-issue-template.md)
for the exact format.

## Handoff to feature-creator

Once an issue is filed with `bug - ready for claude`, feature-creator
processes it through a parallel state machine:

```
bug - ready for claude → bug - triaged → bug - planned → bug - in progress → bug - complete
                                              ↓ (high risk)
                                         bug - human review
```

Branch name: `fix/<N>-<slug>`. Commit type: `fix:`. Plan template:
[`bug-plan-template.md`](../feature-creator/references/bug-plan-template.md).
Risk rubric:
[`bug-risk-criteria.md`](../feature-creator/references/bug-risk-criteria.md).

## Deduplication (current state)

v0.1.0 does **not** fingerprint findings. Each daily run files fresh
issues. The reconciler does cross-check against currently-open `bug`
issues to avoid filing literal duplicates within a single run, but bugs
filed on consecutive days that re-detect the same defect will produce
new issues.

The `<!-- claude-bug-sweeper-v1 -->` marker is reserved on every issue body
so a future closer/triager agent can be added (mirroring security-scanner's
pattern) without breaking historical issues.

## Scheduling

Wrap in a scheduled task for daily runs:

```
Task: bug-sweeper-daily
Cron: 0 7 * * *
Prompt: Run "/bug-sweeper owner/repo --headless"
Mode: permissions-bypass
```

The task must run in a worktree of the target repo so `npm run build` and
`npm audit` operate on a clean checkout. The scheduler is responsible for
worktree creation and cleanup.

## Known Limitations

- Node.js / TypeScript only. Repos using other stacks fall through repo-shape
  discovery and the pipeline halts.
- Test failures (`npm test`) are not collected as a bug signal in v0.1.0.
  Possible future signal — track via README issues.
- No fingerprint-based dedup. Re-detection across runs produces duplicate
  issues. Track via README issues if this becomes a problem.
- Slack/email notifications on HIGH-severity findings are out of scope.

## Possible future signals

- `npm test` results (currently excluded; tests are noisy and often need
  human triage to distinguish flakes from regressions)
- ESLint errors filtered to specific rule sets
- Type-coverage regressions (e.g., new `any` introductions)

If you find yourself wishing the sweep caught a bug class it doesn't, file
an issue against this plugin's directory.

## License

[MIT](../../LICENSE)
