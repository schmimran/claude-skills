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
│   ├── recent-changes.md          # docs-history-reconciler
│   └── protected-files.md         # docs-protected-extractor
├── findings/
│   ├── intent-auditor.md
│   ├── info-architect.md
│   ├── onboarding-reviewer.md
│   ├── reference-validator.md
│   ├── example-verifier.md
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
are inspectable at `/tmp/docs-steward-cache/<RUN_ID>/` until then.

The orchestrator auto-prunes run directories older than 7 days at the
start of each run:

```bash
find /tmp/docs-steward-cache -maxdepth 1 -mindepth 1 -type d -mtime +7 \
  -exec rm -rf {} + 2>/dev/null || true
```

This includes checkpoint-paused runs (those with `checkpoint-required.md`
but no `pr-body.md`).  If you need to resume a paused run, do so before
7 days have elapsed or re-run the pipeline from scratch.

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
