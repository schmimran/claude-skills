# Findings Schema

All Phase 1 auditors emit findings using the same schema.  The consolidator
merges across auditor files by this schema, so deviating breaks the pipeline.

## Per-finding record

Each finding is a single record in the auditor's findings file:

```yaml
- id: <AUDITOR>-<SHORT_HASH>          # e.g. intent-auditor-a3f91c
  auditor: <auditor-name>             # e.g. docs-intent-auditor
  severity: <critical|major|minor|nit>
  action: <edit|delete|restructure>
  location:
    file: <relative path from repo root>
    line_start: <int|null>
    line_end: <int|null>
    anchor: <heading text or markdown anchor, if applicable>
  claim: |
    <what the doc currently says — verbatim or faithful paraphrase>
  reality: |
    <what the code/index/history actually shows — with file:line references>
  suggested_edit: |
    <concrete edit proposal.  For action=delete, the lines/section to remove.
     For action=restructure, the source and destination.  For action=edit,
     a before/after or a clear replacement.>
  tenet_refs: [<int>, ...]            # tenets invoked, e.g. [1, 6]
```

## File layout

Each auditor writes a single markdown file with YAML front matter plus
records.  Format:

```markdown
---
auditor: <auditor-name>
run_id: <RUN_ID>
finding_count: <int>
---

# <Auditor Display Name> — Findings

## Summary
<one paragraph, what the auditor looked at + headline counts>

## Findings

```yaml
- id: ...
  # ...
```

If an auditor has zero findings, write the file with `finding_count: 0`, a
short summary explaining why nothing was flagged, and an empty
`## Findings` section.  **Do not skip writing the file** — the consolidator
uses the file's existence as proof the auditor ran.

## Severity

| Level | Meaning |
|---|---|
| critical | Doc is actively misleading; a reader following it would make a wrong change or break something |
| major | Significant drift: wrong signature, wrong command, missing required step |
| minor | Cosmetic inconsistency, slightly outdated wording, small ordering issue |
| nit | Style-only: voice, tone, punctuation preference |

## Action

| Value | Meaning |
|---|---|
| edit | Rewrite the claim to match reality |
| delete | Remove deprecated/orphan content entirely (tenet 5) |
| restructure | Move content to its canonical home and replace duplicates with links (tenet 6) |

## Severity + action interaction (editor order)

The editor processes in this order per target file:

1. All `action: delete` findings.
2. All `action: restructure` findings.
3. All `action: edit` findings.

Within each action bucket, `critical > major > minor > nit`.

## Validation

- `id` must be unique within the file.
- `location.file` must be a real path under `REPO_DIR`.
- `suggested_edit` must be non-empty.
- `tenet_refs` must be a non-empty list of ints in `1..7`.

The consolidator rejects any record that fails validation and lists
rejections in `${CACHE_DIR}/consolidator-rejections.md`.
