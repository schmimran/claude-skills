# Bug Sweep Protocol

End-to-end pipeline contract for the bug-sweeper plugin. Loaded by the
orchestrator and the analyst.

## Pipeline shape

```
Phase 0  Mode detection + label verification + surface discovery
Phase 1  bug-sweeper-runner          (gh issue list, npm build, npm audit)
Phase 2  bug-sweeper-reviewer ×N     (parallel code review by surface)
         bug-sweeper-tracer          (single hot-path trace)
Phase 3  bug-sweeper-reconciler      (classify open `bug` issues)
Phase 4  bug-sweeper-analyst         (false-positive filter, severity, plan)
Phase 5  Self-review (analyst) + approval gate (orchestrator)
Phase 6  bug-sweeper-filer           (create GitHub Issues)
```

## Global CLAUDE.md overrides during a sweep

The bug-sweeper pipeline is read-only on the target repo and only writes
GitHub Issues. The following global tenets are reinterpreted for this
context:

- **Plan mode confirmation gate** — applies in interactive mode only. In
  headless mode, the analyst's Phase 5 self-review replaces human approval.
- **Three-file scope approval** — N/A. The sweep does not modify code.
- **Atomic commits** — N/A. The sweep does not commit.
- **Branch creation** — N/A. The sweep does not branch. Worktree mode is
  handled by the calling environment.
- **Dependency changes** — N/A. The sweep does not touch dependencies. CVEs
  flagged by `npm audit` become findings; remediation (version bumps) is
  handled by feature-creator after the issue is filed.
- **Read every file before modifying** — applies to the analyst when
  promoting candidates to confirmed: every confirmed bug must cite a
  file:line that the analyst itself re-read.

All other tenets remain in force, in particular:
- `gh` commands always use `--body-file` — never interpolate untrusted
  content into shell strings.
- Plan/issue comment markers are required: `<!-- claude-bug-sweeper-v1 -->`
  for issue bodies filed by this plugin.

## Cache layout

| Path | Producer | Consumer |
|------|----------|----------|
| `/tmp/bug-sweeper-signals.json` | runner | analyst |
| `/tmp/bug-sweeper-build.txt` | runner | analyst (raw) |
| `/tmp/bug-sweeper-audit.json` | runner | analyst (raw) |
| `/tmp/bug-sweeper-open-bugs.json` | runner | reconciler |
| `/tmp/bug-sweeper-review-api.json` | reviewer (API) | analyst |
| `/tmp/bug-sweeper-review-web.json` | reviewer (web) | analyst |
| `/tmp/bug-sweeper-trace.json` | tracer | analyst |
| `/tmp/bug-sweeper-reconciliation.json` | reconciler | analyst |
| `/tmp/bug-sweeper-plan.json` | analyst | filer |
| `/tmp/bug-issue-<ID>.md` | filer | gh issue create |
| `/tmp/bug-sweeper-filed.json` | filer | orchestrator |

The orchestrator removes all `/tmp/bug-sweeper-*` and `/tmp/bug-issue-*`
files at the start of each run. Do not assume cache contents persist
between invocations.

## Comment marker

Every issue body filed by this plugin begins with the literal line:

```
<!-- claude-bug-sweeper-v1 -->
```

This marker is reserved for future deduplication and auto-close logic. v0.1.0
does not implement those features but the marker is required so historical
issues remain compatible when those features ship.

## Boundary with feature-creator

bug-sweeper writes issues. feature-creator reads them. The handoff is purely
through GitHub Issues and labels:

- bug-sweeper applies: `bug`, `bug - ready for claude`, severity label
- feature-creator's triager moves the issue through:
  `bug - triaged → bug - planned → bug - in progress → bug - complete`
- feature-creator's reviewer may escalate to `bug - human review`

bug-sweeper does **not**:
- Plan code changes
- Assess implementation risk
- Estimate scope
- Propose specific fixes (only "areas to investigate")
- Modify any code or open any PR
