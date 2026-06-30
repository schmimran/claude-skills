# Peer Review Template

Developer agents return this report at the end of *peer-review* mode. Both parts are required. Skipping Part B is not acceptable.

---

```markdown
# Peer Review: <Reviewer Platform> reviews <Peer Platform>

**Reviewer:** iOS Developer | Android Developer  
**Reviewing:** Android implementation | iOS implementation  
**Feature:** <Feature Name>  
**Date:** YYYY-MM-DD

---

## Part A — Feedback for the <Android | iOS> Developer

### Parity Gaps

Behaviors that will produce a different user experience than my own implementation, where the parity registry requires a match.

| Behavior | My implementation | Peer's implementation | Parity verdict |
|----------|------------------|----------------------|----------------|
| <behavior> | <what I did> | <what peer did> | Must fix — registry requires match |
| <behavior> | <what I did> | <what peer did> | Acceptable divergence — registry silent |

If none: "No parity gaps found."

### Aesthetic Parity

Visual and aesthetic differences that would make the apps feel inconsistent to a user who uses both platforms, even if behavior is functionally identical.

| Element | My implementation | Peer's implementation | Verdict |
|---------|------------------|----------------------|---------|
| Colors / theme tokens | <what I used> | <what peer used> | Match / Acceptable divergence / Must fix |
| Typography (sizes, weights, line height) | | | |
| Spacing and padding | | | |
| Iconography style and sizing | | | |
| Animation / transition timing | | | |
| Loading / skeleton state appearance | | | |
| Empty state design | | | |
| Error state presentation | | | |

Acceptable divergence: platform-native navigation chrome (iOS tab bar vs Android bottom nav), system form controls, system fonts when no custom font is specified — these are idiomatic. Everything else should match.

If aesthetics are consistent: "Aesthetic parity: consistent."

### UX Inconsistencies

Interactions, copy, flows, or timing differences that diverge from my implementation in ways the parity registry does not sanction.

- **<File:line>** — <description of the inconsistency and what it should be>

If none: "No UX inconsistencies found."

### Contract Usage Issues

Wrong endpoint, wrong field name, missing error handling, wrong auth header, or response shape mismatch.

- **<File:line>** — <description of the issue>

If none: "No contract usage issues found."

### Bugs or Logic Errors

Off-by-one, wrong state management, missing null/nil check, race condition, memory issue, incorrect business logic.

- **<File:line>** — <description of the bug and suggested fix>

If none: "No bugs found."

### Positive Callouts

Patterns in the peer's code that are genuinely better than my own approach. (Required — if you found none, explain why briefly.)

- **<File:line>** — <description of what is good about this approach>

---

## Part B — Self-Reflection and Convergence

This is an honest assessment of whether the peer's approach is better than mine and whether I should adopt it. Humility over ego.

### Items to Adopt from Peer

For each item where the peer's approach is better:

| Peer approach | Better than mine because | What I would change in my code |
|---------------|-------------------------|-------------------------------|
| <peer's pattern/approach> | <honest reason> | <specific change: file, function, what> |

If none: write "None — I reviewed the peer's implementation carefully and do not find a superior approach in any dimension." Then briefly explain what you compared.

### Overall Convergence Verdict

Choose one and explain:

**`adopt selectively`** — I will incorporate specific items listed above; my overall architecture stands.

**`partial refactor`** — The peer's approach is better in a significant area; I would refactor that area (list which files/components).

**`full redo`** — The peer's approach is fundamentally better. My implementation should be replaced. (This is an acceptable verdict when it is the right call. Sunk cost is not a reason to keep inferior code.)

**`no change`** — My implementation is at least as good as the peer's in all dimensions. (Requires the "None" justification above.)

**Selected verdict:** <verdict>

**Rationale:** <explanation — be specific about what you compared and why you reached this conclusion>
```
