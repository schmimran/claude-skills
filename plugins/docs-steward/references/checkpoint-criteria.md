# Checkpoint Criteria

The `docs-consolidator` pauses the pipeline when it cannot produce a
coherent edit plan.  When any of the triggers below fire, the consolidator
writes `${CACHE_DIR}/checkpoint-required.md` and exits without writing
`consolidated-findings.md`.  The orchestrator then stops Phase 3 and
surfaces the file to the user.

## Triggers

### 1. Conflict density

More than **20%** of findings have at least one direct conflict with
another finding targeting the same file + location.

A direct conflict is two findings with `action: edit` (or one `edit` and
one `delete`) on the same `location.file` + overlapping line range, whose
`suggested_edit` values are mutually exclusive.

### 2. Structural incoherence

The consolidator cannot place content into a coherent information
architecture.  Signals:

- Tenet-6 resolution has three or more candidate canonical homes for the
  same content and no clear winner by depth-specificity heuristic.
- Section READMEs that the `docs-info-architect` flagged as structurally
  inconsistent with no majority pattern to normalize toward.

### 3. Production config deletion

Any `action: delete` finding targeting a file the consolidator classifies
as a production config (file path matches `*production*`, `*prod*`,
`config/prod/**`, or the file contains a `NODE_ENV=production`-style
pragma).  The severity is raised to `critical` and the user adjudicates
before the editor runs.

### 4. Secret-adjacent deletions

Any `action: delete` finding whose target key name matches `*_SECRET`,
`*_TOKEN`, `*_PASSWORD`, `*_KEY`, or `*_CREDENTIAL` (case-insensitive),
even if the deprecation-hunter believes the key is unreferenced.  Never
auto-delete these; always escalate.

### 5. Large-scale deletion

The total `action: delete` count exceeds **50** records, or any single
file would be reduced to under 20% of its current size.  Mass deletions
are typically signs of a misfire in the deprecation-hunter (e.g. missed
references in a language the symbol indexer does not cover).

## Checkpoint file format

`${CACHE_DIR}/checkpoint-required.md`:

```markdown
# Docs Steward Checkpoint — Adjudication Required

**Run ID:** <RUN_ID>
**Trigger(s):** <list of triggers from above>

## What the consolidator saw

<one paragraph, plain language>

## Options

1. **Adjudicate and resume** — resolve the conflicts below, edit
   `consolidated-findings.md` by hand, then re-run with `--resume
   <RUN_ID>`.
2. **Abort** — delete `${CACHE_DIR}` and re-run from scratch, possibly
   with narrower scope.

## Conflicts / issues to resolve

<numbered list with finding IDs, file paths, and short descriptions>
```

## Orchestrator behavior on checkpoint

The orchestrator:

1. Reads and prints the full checkpoint file to the user.
2. Stops without creating a branch or making any edits.
3. Leaves `${CACHE_DIR}` in place for inspection and manual adjudication.
4. Exits with a non-zero status code so scheduled runs surface as failed.

Resumption (the `--resume` flag) is out of scope for v0.1.0; after
adjudication, re-run the pipeline with the same arguments.
