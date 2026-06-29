# Completion Report Template

Developer agents return this report at the end of *implement* mode. Fill in every section — do not omit sections with "N/A"; write "None" instead.

---

```markdown
# Completion Report: <Feature Name>

**Platform:** iOS | Android  
**Date:** YYYY-MM-DD

---

## 1. Files Changed

| File | Action | Description |
|------|--------|-------------|
| `<path/File.swift>` | Created | <one line: what this file does> |
| `<path/File.kt>` | Modified | <one line: what was added/changed> |

---

## 2. Key Decisions

Architectural or product choices made during implementation that weren't explicitly specified in the brief.

| Decision | Chosen approach | Rationale |
|----------|-----------------|-----------|
| <decision> | <approach taken> | <why> |

---

## 3. Deviations from Brief

Anything that differs from what the brief specified. Be specific — the supervisor needs to understand what changed and whether it affects parity.

| Brief said | What was done instead | Reason |
|------------|----------------------|--------|
| <brief instruction> | <actual implementation> | <reason> |

If there are no deviations: write "None."

---

## 4. Contract Usage

For each endpoint called:

| Endpoint | Called as specified? | Notes |
|----------|---------------------|-------|
| `<METHOD> <path>` | Yes | — |
| `<METHOD> <path>` | No — <what differed> | <reason> |

**Shape mismatches noticed** (field names or types in the contract doc that don't match what the backend actually returns, if observable):
- <mismatch, if any>

---

## 5. Open Questions

Things the supervisor or peer reviewer should know. Include anything uncertain, incomplete, or that may affect parity.

- [ ] <Question or flag>
- [ ] <Question or flag>

If none: "None."
```
