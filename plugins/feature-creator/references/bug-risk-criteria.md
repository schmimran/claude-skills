# Bug-Fix Risk Assessment Criteria

Use this rubric when reviewing a plan attached to an issue labeled
`bug - planned`. For feature plans, use [`risk-criteria.md`](risk-criteria.md)
instead.

A bug fix is **high-risk** if it has any HIGH factor or two or more MEDIUM
factors. High-risk bugs are flagged for human review (`bug - human review`).

The bug-fix rubric differs from the feature rubric: where features ask "is
the new code safe?", bug fixes ask "will the change cause a regression or
break assumptions downstream?" Some factors that raise feature risk lower
bug-fix risk and vice versa.

## HIGH Risk Factors (bug-specific)

| Factor | Trigger | Why it's HIGH |
|--------|---------|---------------|
| Authentication / authorization | Plan touches auth middleware, session management, token handling, or access control | Security blast radius is the same regardless of whether code is added or fixed |
| Concurrency / async logic | Plan modifies await ordering, Promise composition, queue/worker logic, or retry behavior | Concurrency bugs often have asymmetric blast radius: the fix can introduce a new race that takes weeks to surface |
| Hot-path SQL or query logic | Plan changes a query that runs on every request, in a sweep, or in a webhook handler | Hot-path query changes can cascade into latency or load issues |
| Removes code external consumers may rely on | Plan removes a function, API endpoint, or behavior that downstream code may have come to depend on (even if buggy) | Downstream code sometimes "depends on" the broken behavior; removing it is a breaking change |
| Schema / migration touched | Plan includes DDL, migration files, or schema changes | Same reasoning as feature rubric — irreversible if wrong |
| Data deletion or destructive change | Plan permanently deletes user data or backfills with deletion | Irreversible data loss if logic is wrong |
| Error handling that swallows previously-surfaced errors | Plan changes a catch / handler so errors that used to be propagated now return a default | Masks future bugs; harder to detect in production |
| Secrets / credentials | Plan modifies how API keys, tokens, or secrets are read or stored | Same reasoning as feature rubric |

## MEDIUM Risk Factors (bug-specific)

| Factor | Trigger | Why it's MEDIUM |
|--------|---------|-----------------|
| Cache invalidation | Plan changes when caches are populated, evicted, or read | Cache bugs are quiet failures; correctness regressions are easy to miss |
| Retry / timeout / backoff | Plan modifies retry logic, timeouts, or backoff parameters | Wrong values cascade into thundering-herd or stuck-flow problems |
| Data backfill | Plan includes a data backfill or one-time migration step | Backfills are easy to misorder; verifying completeness is hard |
| Cross-cutting scope | Plan touches 5+ files or spans 2+ distinct modules to fix one bug | Suggests the root cause may be wider than diagnosed; verify by re-reading the bug-sweeper issue |
| External API integration changed | Plan modifies how a third-party API is called | Behavior change at a trust boundary |
| Performance-sensitive path | Plan modifies hot paths, indexed query construction, or memoization | Performance regressions may not be caught by tests |
| New dependency / version bump | Plan bumps a dependency to fix a CVE or get a patched API | Version bumps drag in unrelated changes; risk depends on the dep |

## LOW Risk Factors (bug-specific)

| Factor | Trigger | Why it's LOW |
|--------|---------|--------------|
| UI-only fix | Plan only touches templates, styles, or copy | Visual changes are easy to verify and revert |
| Documentation / comment fix | Plan only modifies docs, comments, or error messages | No runtime impact |
| Adds missing validation | Plan adds an input check that previously was not present | Lowers risk rather than raising it; no existing valid input is rejected |
| Adds missing await / null-check on a non-critical path | Plan inserts a single guard or `await` in a request handler with existing error handling | Defensive edit; tightens correctness without changing happy-path behavior |
| Modifies a private internal function | Plan changes a non-exported helper used in 1-2 places | Bounded blast radius |
| Test-only change | Plan only adds or updates regression tests | Improves coverage without affecting production code |

## How to apply

1. Read the bug fix plan's "Reproduction Steps", "Root Cause Analysis",
   "Affected Files", and "Implementation Steps".
2. Check each risk factor above against the plan.
3. Record which factors apply and at what level.
4. Determine overall risk:
   - **Any HIGH factor** → high-risk → flag for human review (`bug - human review`)
   - **2+ MEDIUM factors** → high-risk → flag for human review
   - **1 MEDIUM factor** → acceptable risk → proceed
   - **All LOW** → low risk → proceed
5. When flagging, cite the specific factors and explain why they apply.

## Why some factors flip vs. the feature rubric

| Factor | Feature rubric | Bug rubric | Why |
|--------|----------------|------------|-----|
| "Adds new validation" | MEDIUM (new behavior, potential edge cases) | LOW (no existing valid input is rejected) | Direction: bugs *add* a missing check; features add a new gate |
| "Modifies a private internal function" | MEDIUM (callers may break) | LOW (callers are inside the same module — easy to verify) | Bug fixes target known callers; features may have broader call sites |
| "Removes deprecated code" | LOW–MEDIUM (deprecation expected the removal) | HIGH (the removal *is* the bug fix; downstream may have come to rely on the broken behavior) | Removing buggy code can break callers that adapted to the bug |
| "Cross-cutting scope" | MEDIUM at 10+ files | MEDIUM at 5+ files | A bug fix that touches many files often signals a misdiagnosed root cause |
