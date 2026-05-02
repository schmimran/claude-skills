# False-Positive Rubric

Rules for ruling out candidate findings during analysis. Used by the
`bug-sweeper-analyst` agent in Phase 4.

A candidate finding is **DISCARDED** if at least one of these patterns
applies. For each discard, record the specific reason cited in the rubric.
Generic dismissals are not acceptable.

## D1: Node.js single-threaded execution

JavaScript on Node.js is single-threaded. A claim that two synchronous code
paths concurrently mutate a shared object is invalid.

A claim is still valid if:

- The code uses worker threads, child processes, or `cluster`
- The code yields between steps via `await`, `setTimeout`, or `setImmediate`
  and another invocation of the same flow could interleave
- The "shared state" lives outside Node's process (DB, Redis, file system)

In short: discard claims about in-process race conditions on plain
JavaScript objects. Keep claims about race conditions across async
boundaries or external systems.

## D2: Optional/nullable already handled

An issue claim that "this could be undefined" should be discarded if:

- TypeScript narrowing already proves the variable is defined at the use
  site (e.g., a guard `if (!x) return` above)
- The function signature marks the argument as required (no `?` or default)
- The call site only invokes the function from places that pass a defined
  value (verify by reading the call sites)

## D3: Already guarded

A claim that "this can throw" should be discarded if there is an enclosing
`try/catch` whose handler does something useful (logs, retries, returns a
typed error). Note the line number of the guard.

A claim that "this can be null" should be discarded if there is an `if`
check or `??` fallback above the use site.

## D4: Intentional silent error

Some catches are intentionally non-fatal: cleanup paths, best-effort
notifications, observability that should not crash the request. Discard
silent-catch claims when:

- The function name contains `cleanup`, `notify`, `track`, `log`,
  `cache`, `prefetch`
- The catch is paired with an explicit comment explaining why the error is
  swallowed
- The error is logged before being swallowed

Do **not** discard silent-catch claims in flows that mutate state — silent
failure in a state-mutating flow is almost always a bug.

## D5: File / line not actually read

If a candidate finding cites a file:line that the analyst could not
re-read in this run, discard it as `unverifiable-citation`. The reviewer
might have hallucinated the snippet. Never confirm a finding from a snippet
alone.

## D6: Transient build or audit failure

A `npm run build` failure caused by:

- A network error fetching a dependency
- A TypeScript version mismatch with the user's local env
- A missing env var that exists in CI

…is not a bug in the repo. Discard with `transient-build-failure`. Distinguish
from real type errors (which are bugs) by reading the actual error output.

A `npm audit` finding marked LOW is generally not worth filing as a bug
issue. Discard LOW-severity audit findings unless the dependency has no
fix available — in which case keep but mark LOW so feature-creator
deprioritizes it.

## D7: Already covered by an open issue

If the reconciliation report has an open `bug` issue marked `still-open`
that describes the same defect, the analyst marks the finding with
`existing_issue: <N>` rather than discarding. The filer skips re-filing.

If the existing issue is `fixed-by-recent-commit` per the reconciler, do
not include the candidate as a confirmed bug — the bug is resolved even
though the issue may still be open.

## D8: Test code or fixtures

Findings inside `*.test.*`, `*.spec.*`, `tests/`, `__tests__/`, `fixtures/`,
`mocks/`, or `__mocks__/` directories are usually intentional (e.g., testing
that a malformed input is rejected). Discard with `test-code-context` unless
the finding is in a test helper that runs in production.

## D9: Generated code

Findings in directories named `generated/`, `dist/`, `build/`, `.next/`,
`coverage/`, `out/`, or files with names matching `*.generated.*` are
generated artifacts. Discard with `generated-code`. The bug, if any, lives
in the source that produced the artifact.

## What is **not** a valid discard reason

- "Seems unlikely"
- "The author probably meant to do this"
- "Existing tests would catch this" (without verifying that they actually do)
- "This pattern is common"

Findings that pass D1–D9 are CONFIRMED. The analyst then assigns severity
per `severity-rubric.md`.
