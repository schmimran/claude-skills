# Headless Mode

Concrete checklist when `--headless` is passed to `/bug-sweeper`. This is
the mode used when the command is invoked from a `/schedule` routine
running in permissions-bypass.

## What changes

| Concern | Interactive | Headless |
|---------|-------------|----------|
| Plan mode | Enter plan mode at Phase 5 | Skip plan mode entirely |
| `AskUserQuestion` calls | Allowed for ambiguity | Forbidden — never call |
| `ExitPlanMode` at Phase 5 | Required, gates Phase 6 | Skipped — Phase 6 runs immediately |
| Three-file scope rule | N/A (read-only sweep) | N/A |
| Approval before filing | Required | Replaced by analyst's Phase 5 self-review |

## What does **not** change

- Every confirmed bug must cite a file:line that the analyst re-read.
- Every issue body uses `--body-file` and starts with the
  `<!-- claude-bug-sweeper-v1 -->` marker.
- The pipeline halts on agent errors. Headless does not silently absorb
  failures.
- The runner's checks are non-fatal individually but a missing
  `signals.json` halts the pipeline.

## What the analyst's self-review does in headless

The analyst's Step 6 (self-review) runs the same checks regardless of mode:

- Drop confirmed bugs whose file:line was not re-read
- Flag inconsistent severities
- Drop duplicates that touch the same lines
- Cross-check against the reconciliation report

In headless mode, the analyst's output **is** the final plan. The
orchestrator does not present it to the user. The filer reads the plan and
files issues without further confirmation.

## Detection at the orchestrator

```
HEADLESS=false
for arg in $ARGUMENTS; do
  case "$arg" in
    --headless) HEADLESS=true ;;
  esac
done
```

If `HEADLESS=true`, the orchestrator's Phase 5 prints the plan summary
without entering plan mode and without calling `ExitPlanMode`. Phase 6
launches the filer immediately.

## Recommended schedule shape

```
Task: bug-sweeper-daily
Cron: 0 7 * * * (every day at 7am)
Prompt: Run "/bug-sweeper <OWNER/REPO> --headless"
Mode: permissions-bypass
```

The task should run in a worktree of the target repo so the runner's
`npm run build` and `npm audit` operate on a clean checkout. The scheduler
is responsible for worktree creation and cleanup — bug-sweeper does not
manage worktrees.
