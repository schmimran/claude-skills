# Cache Layout

The pipeline produces structured artifacts under
`/tmp/docs-steward-cache/<RUN_ID>/`.  Downstream agents read
predecessor outputs from this location rather than receiving them via
prompt.

`<RUN_ID>` is a UTC ISO-8601 timestamp with no colons: `20260421T153000Z`.

## Directory structure

```
/tmp/docs-steward-cache/<RUN_ID>/
├── indexes/
│   ├── tracked-files.txt          # orchestrator — git ls-files snapshot (gitignore boundary)
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

## Storage location

The cache lives in `/tmp/` — no gitignore entry in the target repo is
needed.  Cache artifacts are never committed to the repo.

## Retention

Cache directories in `/tmp/` are cleared by the OS on reboot.  Prior runs
are inspectable at `/tmp/docs-steward-cache/<RUN_ID>/` until then.  A
`--clean` flag to prune explicitly is out of scope.

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
