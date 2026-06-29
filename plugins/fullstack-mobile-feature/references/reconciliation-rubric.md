# Reconciliation Rubric

The supervisor applies this rubric in Phase 6 to synthesize completion reports and peer reviews into concrete dispatch decisions. Priority is ordered — higher-priority issues are resolved first, regardless of the volume of lower-priority issues.

---

## Priority Order

### 1. Correctness (highest priority)

A feature that doesn't work for the user gets fixed first, on either platform.

Indicators: the developer flagged an open question about behavior, the peer found a bug, or the completion report shows a deviation from the brief that affects functionality.

Resolution: dispatch a targeted fix to the responsible agent. Be precise — name the file, the function, and the expected behavior.

### 2. UX Consistency

If the two platforms will produce a different user experience for the same action, and that difference is not sanctioned by the parity registry, it must be resolved.

The parity registry is the arbiter. If the registry requires a match and the implementations differ: one platform must change. Prefer the approach that better serves the user experience; do not default to "keep both" or "split the difference."

Indicators: parity gaps flagged in either peer review, or observable differences in the UX spec vs implementation.

Resolution: dispatch a targeted change to the platform that deviates from the parity-correct behavior. State the exact behavior expected.

### 3. API Contract Fidelity

Both platforms must call the API exactly as documented in the contract doc. Wrong endpoints, wrong field names, missing error handling, and auth header omissions are contract violations.

Indicators: "Contract Usage Issues" in either peer review, or shape mismatches in either completion report.

Resolution: dispatch a targeted fix to the agent with the contract violation. Reference the exact endpoint and field from the contract doc.

### 4. Code Quality / Convergence

Adopt superior patterns from one platform into the other when doing so doesn't cost correctness or consistency.

Indicators: "Items to Adopt from Peer" in either peer review, convergence verdicts of `adopt selectively` or `partial refactor`.

Resolution: dispatch targeted refactor tasks. Do not force convergence for its own sake — only when the superior pattern is clear and the cost is proportionate.

A `full redo` verdict from a developer agent must be taken seriously. Review it against priorities 1–3. If the full redo is necessary to fix correctness, consistency, or contract issues, approve it. If it's purely a code quality preference and priorities 1–3 are clean, the supervisor decides whether the quality gain justifies the cost.

### 5. Sunk Cost (never a factor)

How much work went into an implementation is irrelevant to whether it should be kept. A full redo is acceptable when it is the right call. Never let sunk cost influence a reconciliation decision.

---

## Decision Matrix

For each open item (from completion reports and peer reviews), apply this matrix:

| Item type | Severity | Default action |
|-----------|----------|----------------|
| Bug or incorrect behavior | Any | Fix it (Priority 1) |
| Parity gap — registry requires match | Any | Fix the deviating platform (Priority 2) |
| Parity gap — registry silent | Significant UX impact | Fix; note as new parity requirement |
| Parity gap — registry silent | Minor / cosmetic | Accept both; note in reconciliation log |
| Contract violation | Any | Fix it (Priority 3) |
| Convergence: `adopt selectively` | — | Dispatch targeted adoption to the proposing agent |
| Convergence: `partial refactor` | — | Dispatch refactor; scope to named files/components |
| Convergence: `full redo` | Covers Priority 1–3 issues | Approve redo |
| Convergence: `full redo` | Pure quality preference | Supervisor judgment |
| Convergence: `no change` | — | Accept; no dispatch needed |
| Positive callout | — | Consider for optional adoption; not required |

---

## Dispatch Format

When sending round-3 tasks back to a developer agent, be precise:

```
You are in implement mode for a targeted round-3 fix.

ISSUE: <description of the specific issue>
PRIORITY: <Correctness | UX Consistency | Contract | Convergence>
FILE(S): <exact file paths>
EXPECTED BEHAVIOR: <what the code should do after the fix>
CURRENT BEHAVIOR: <what it does now>

Fix only the items listed. Do not refactor anything else. Return an updated completion report covering only the changed files.
```

---

## Iteration Rule

Continue reconciliation rounds until both platforms have no open issues in Priority 1, 2, or 3.

**Maximum 3 rounds.** If after 3 full reconciliation rounds Priority 1–3 issues remain unresolved, stop and escalate to the user:

> "After 3 reconciliation rounds, the following issues remain unresolved. I recommend we address them manually before landing: [list]"

Do not commit with known Priority 1–3 issues open.

---

## Reconciliation Log Format

Write `$WORK_DIR/reconciliation.md` as a decision log:

```markdown
# Reconciliation Log: <Feature Name>

## Round 1

| Issue | Platform | Priority | Decision | Dispatched to |
|-------|----------|----------|----------|---------------|
| <issue> | iOS | P2 | Fix deviating behavior | ios-developer |
| <issue> | Android | P3 | Fix wrong field name | android-developer |

## Round 2
...

## Final Status

All Priority 1–3 issues resolved. Cleared for landing.
```
