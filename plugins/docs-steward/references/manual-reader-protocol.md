# Manual Reader Protocol

Used by `docs-manual-reader` in Phase 4 (post-edit read).  The agent
walks the edited corpus once, cross-checks against the edit plan, and
emits a classification that controls whether a second editing pass is
allowed.

## Reading order

1. Start at `/README.md`.
2. Note every link in the root README.  Queue them.
3. Visit each linked doc in the order encountered.  For each:
   - Read it as if you had just landed on it from the root.
   - Note new links encountered.
   - Queue any links not already visited.
4. Continue until the queue is empty or all visited docs have been read.
5. Visit any docs that were **not** reachable from the root but exist in
   `doc-inventory.md`.  These are orphans by definition — flag them.

Do not skip around.  Read in the order a user would reach them.

## What to look for

### Tenet 1 — User-facing READMEs

- Is the opening scannable?
- Does the reader know "what is this?" after the first paragraph?
- Are there dense reference details that belong in backing docs?

### Tenet 2 — Root as entry point

- Does the root README orient a first-time reader?
- Are the links from root → section READMEs descriptive?
- Does each linked doc lead somewhere useful?

### Tenet 3 — Coherent narrative

- Does the reading sequence build on itself, or does it require jumping
  back?
- Are there contradictions between sibling docs?
- Do terms get defined before being used?

### Tenet 4 — Section README consistency

- When reading sibling section READMEs in sequence, do they feel like
  members of the same family, or like different products?
- Do they share headings and detail levels?

### Tenet 6 — No duplication

- Does the same explanation appear in two places?
- Is install covered in three READMEs?
- Does a table in one doc repeat content from another?

## Output

Write to `${CACHE_DIR}/post-edit-findings.md` using the shared schema
from `findings-schema.md`, plus a top-level section:

```markdown
## Overall classification

classification: <empty | nits_only | small_local | structural>

reasoning: <one paragraph>
```

Classification semantics:

| Value | Meaning | Orchestrator action |
|---|---|---|
| `empty` | No findings | Skip second pass, proceed to PR |
| `nits_only` | Only `severity: nit` findings | Skip second pass, proceed |
| `small_local` | ≤10 findings, all `severity: minor` or below, all within existing docs | One second-pass edit allowed |
| `structural` | Any `severity: major` or above, OR findings requiring new docs or moved sections | No second pass; surface in PR body |

## Cross-checking the edit plan

The agent receives `${CACHE_DIR}/consolidated-findings.md` (what the
editor was supposed to fix) and `${CACHE_DIR}/edits.log` (what the
editor actually changed).  Use these to:

- Confirm each consolidated finding was addressed in the edited corpus.
- Focus attention on docs the editor touched.
- Check for new issues introduced by the edits (broken cross-refs, new
  duplications, split narratives).
