# Core Tenets

Every agent in the docs-steward pipeline loads this file at the start of its
run.  These are non-negotiable.  The consolidator and final-reviewer validate
compliance before the PR opens.

## 1. READMEs are user-facing

READMEs are written for fast scanning by a real human landing on a repo or
directory for the first time.  They are **not** reference dumps.  Dense
reference detail lives in backing docs (architecture, API reference,
contribution guide, etc.) and is linked from the README.

**Heuristics:**
- Opening paragraph answers "what is this?" in one breath.
- Installation / quick-start within the first screen.
- Tables and bullets over paragraphs for scannable facts.
- Link out to deeper docs rather than inlining details.

## 2. Root README is the entry point

A reasonable first-time user should be able to start at `/README.md` and get
coherent ongoing context — understanding structure, installation, usage, and
how to contribute — by following links only.  No required knowledge is
assumed beyond the repo's stated audience.

**Heuristics:**
- Every directory a user is expected to understand has a linked entry from
  the root.
- No dead ends: every linked doc leads somewhere useful.
- The reading path from root → every other doc is traceable.

## 3. The corpus must read as a manual

At least one persona (the `docs-manual-reader`) walks the docs like a human
user, starting at the root README, following links, and treating the whole
body as a single linear manual.  This exercise is the ground-truth test of
coherence.  The same persona re-reads after edits.

## 4. Section READMEs are consistent

Section-level READMEs (e.g., `plugins/<name>/README.md`) share the same
top-level components where applicable:

1. Overview / what this is
2. Installation or activation (if applicable)
3. Usage / quick start
4. Architecture or components table
5. Contribution or development notes (if applicable)
6. Links to backing docs

Level of detail is comparable across peers.  One section README should not
be ten times the size of its sibling for an equivalent surface area.

## 5. Deprecated/orphaned content is removed, not annotated

Stale variables, config keys, env keys, commands, and doc references are
deleted.  Do not leave behind `// deprecated` markers, "legacy" sections, or
notes saying "this used to be..."  The git history is the record.

**Exceptions (flag but do not delete automatically):**
- Anything named `*_SECRET`, `*_TOKEN`, `*_PASSWORD`, `*_KEY`.
- Items in production config files (the consolidator raises severity and
  triggers a checkpoint).

## 6. No duplication

Information lives in exactly one canonical place.  Everywhere else, link to
it.  When duplicate content is detected, the consolidator picks the
canonical home (deepest-specific doc wins; README links out).

## 7. Post-edit re-read

After the first edit pass, the manual-reader re-reads the entire corpus from
the root README.  Residual issues either:

- Trigger a second (and only a second) edit pass for small/local fixes.
- Surface in the PR body for human review if they are structural.

## Voice

Preserve the existing voice unless a finding explicitly requires rewriting.
When in doubt, err toward the style of the root README.  Do not introduce
emoji, exclamation points, or marketing tone unless those already exist in
the target doc.
