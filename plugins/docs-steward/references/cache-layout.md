# Cache Layout

The pipeline produces structured artifacts under
`<REPO_DIR>/.claude/docs-cache/<RUN_ID>/`.  Downstream agents read
predecessor outputs from this location rather than receiving them via
prompt.

`<RUN_ID>` is a UTC ISO-8601 timestamp with no colons: `20260421T153000Z`.

## Directory structure

```
<REPO_DIR>/.claude/docs-cache/<RUN_ID>/
├── indexes/
│   ├── file-tree.md               # docs-file-cartographer
│   ├── symbols.json               # docs-symbol-indexer
│   ├── routes.md                  # docs-route-mapper
│   ├── config.md                  # docs-config-cataloger
│   ├── doc-inventory.md           # docs-inventory
│   ├── glossary.md                # docs-glossary-steward
│   └── recent-changes.md          # docs-history-reconciler
├── findings/
│   ├── intent-auditor.md
│   ├── info-architect.md
│   ├── onboarding-reviewer.md
│   ├── reference-validator.md
│   ├── example-verifier.md
│   ├── link-checker.md
│   ├── manual-reader.md
│   └── deprecation-hunter.md
├── consolidated-findings.md       # docs-consolidator
├── consolidator-rejections.md     # docs-consolidator (if any records failed validation)
├── checkpoint-required.md         # docs-consolidator (only if checkpoint fires)
├── edits.log                      # docs-editor
├── post-edit-findings.md          # docs-manual-reader (Phase 4)
└── pr-body.md                     # docs-final-reviewer
```

## Gitignore

The orchestrator ensures `.claude/docs-cache/` is in the repo's
`.gitignore` before Phase 0 starts.  Cache artifacts are never committed.

## Retention

Old runs are not auto-deleted in v0.1.0.  The user can inspect prior
runs in place.  A `--clean` flag to prune is out of scope.

## Concurrency

Only one `/docs-steward` run should be active against a given repo at a
time.  If a prior `<RUN_ID>` directory exists without a
`pr-body.md`, the pipeline either:

- Failed mid-run (inspect `edits.log` and re-run), or
- Is currently in a checkpoint wait (inspect `checkpoint-required.md`).

The orchestrator does not lock the cache dir; avoid starting a second
run manually while one is in flight.

## Absolute vs relative paths

All paths **inside** the cache are relative to `<REPO_DIR>`.  Paths
that agents write or read to disk use absolute paths constructed from
`<REPO_DIR>` + relative path, to avoid cwd-dependent behavior in
subagents.
