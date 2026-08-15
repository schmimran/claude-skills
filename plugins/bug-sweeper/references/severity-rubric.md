# Severity Rubric

Used by the `bug-sweeper-analyst` agent to assign HIGH / MEDIUM / LOW to
each confirmed bug. Severity flows through to the issue label
(`bug - high`, `bug - medium`, `bug - low`) and is preserved through the
pipeline.

Note that no downstream agent reads the severity label to order work —
feature-creator sequences by dependency, file overlap, and complexity. The
label is a signal for humans triaging the queue.

A bug receives a single severity. If two factors point to different levels,
take the higher one.

## HIGH

Any of:

- **Data loss or data corruption** — code writes incorrect or partial data
  to a database, file, or external store
- **Security-relevant** — authentication / authorization gap, injection,
  secret exposure, missing input validation on a privileged path
- **Crash on a hot path** — an unhandled exception in a flow that runs
  unattended (cron, webhook, queue consumer, SSE, periodic sweep)
- **Silent error swallowing in a state-mutating flow** — a try/catch that
  returns success while a partial mutation has been committed
- **Async ordering bug that corrupts state** — missing `await` whose
  Promise affects a subsequent step's correctness
- **`npm audit` critical or high CVE** — direct dependency on a vulnerable
  version with a fix available

## MEDIUM

Any of:

- **Regression in a non-critical flow** — observable wrong behavior, but
  the flow is user-initiated (so the user can retry) and does not corrupt
  state
- **Error recovery gap** — an error path that fails to clean up resources
  but the next request rebuilds them automatically
- **State consistency bug in UI** — UI state diverges from server state
  briefly (e.g., stale list after a write)
- **DOM cleanup gap** — `addEventListener` without removal, `setInterval`
  without `clearInterval` causing leaks but not immediate failure
- **`npm audit` moderate CVE** — direct dependency on a vulnerable version
- **Test-runner-or-build TypeScript error** — `npm run build` fails with a
  type error that prevents shipping but does not affect runtime once
  bypassed

## LOW

Any of:

- **Cosmetic** — UI text, spacing, or copy issues
- **Documentation drift in code** — comment or JSDoc says X but code does Y
- **Defensive-coding gap with no observed failure mode** — code could be
  more defensive but no current input triggers the path
- **`npm audit` low CVE** — usually filed only if there is no fix available
  on a higher-severity dependency

LOW-severity bugs are filed and expected to sit in the queue until a human
picks them up.

## Cross-checks

After assigning severities, the analyst verifies:

- Two bugs with the **same failure mode** in **similar contexts** have the
  **same severity**. If they don't, articulate why or correct one.
- The aggregate distribution is plausible. If 90% of confirmed bugs are
  HIGH, the analyst is being too aggressive — re-read and demote where
  warranted.
- A LOW severity must not be on a code path the user described in the
  issue title as critical. Re-read the issue body and the cited code
  before keeping LOW.

## Examples

| Description | Severity | Why |
|---|---|---|
| `await` missing on `db.write()` in a webhook handler | HIGH | Silent partial commit on a hot path |
| `await` missing on `analytics.track()` in a request handler | LOW | Best-effort, error is swallowed intentionally; filed only if it leaks resources |
| Empty catch around `email.send()` after a `db.write()` succeeded | HIGH | Partial commit: the row exists but the user is never notified |
| Empty catch around `cache.delete()` in cleanup function | LOW | Cleanup paths often fail benignly; document or move on |
| `setInterval` callback that mutates a `Map` and never clears the interval | MEDIUM | Memory leak; not immediate failure but accrues over time |
| `innerHTML = userInput` in a UI component | HIGH | XSS, security-relevant |
| `dangerouslySetInnerHTML={{__html: trustedConst}}` | LOW | Pattern is suspicious but the data flow makes it safe; document |
