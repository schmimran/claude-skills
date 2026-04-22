# Index Artifact Spec

Phase 0 agents emit canonical reference artifacts under
`${CACHE_DIR}/indexes/`.  Phase 1 auditors read these files rather than
re-crawling the repo.  This file is the contract between the two phases.

## file-tree.md

Emitted by `docs-file-cartographer`.

Markdown.  A hierarchical tree with one entry per file or directory plus a
one-line purpose:

```markdown
# File Tree

## Top-level

- `/README.md` — Root entry point; marketplace overview + install
- `/CLAUDE.md` — Repo guidance for AI contributors
- `/plugins/` — Individual plugin directories
  - `/plugins/feature-creator/` — Feature development pipeline plugin
    - `/plugins/feature-creator/README.md` — User-facing plugin docs
    - `/plugins/feature-creator/commands/` — Slash command definitions
    - ...
```

Excludes: `.git/`, `node_modules/`, `.claude/docs-cache/`, common build
output paths (`dist/`, `build/`, `target/`, `.next/`, `.venv/`).

## symbols.json

Emitted by `docs-symbol-indexer`.

JSON.  Array of symbol records:

```json
[
  {
    "symbol": "renderIssue",
    "kind": "function",
    "file": "plugins/feature-creator/agents/feature-planner.md",
    "line": 42,
    "visibility": "exported",
    "signature": "renderIssue(issue: Issue): string"
  }
]
```

`kind`: `function | class | method | constant | type | interface | enum | macro`.
`visibility`: `exported | internal | unknown`.
Repo-wide deduplication by `(symbol, file, line)`.

## routes.md

Emitted by `docs-route-mapper`.

Markdown table(s) listing public interfaces.  Separate sections for each
interface kind found in the repo:

- HTTP routes: method, path, handler file:line, middleware chain (if
  detectable).
- CLI commands / slash commands: name, definition file:line, brief
  description.
- Public SDK/library exports: package entry point, named exports.

If no public surface is found for a category, omit that section and state
so in a `## Coverage` footer.

## config.md

Emitted by `docs-config-cataloger`.

Markdown sections per config source:

- `## Environment Variables` — every env var referenced in the code, with
  file:line of first reference, default value (if any), and a flag for
  whether it appears in `.env*` example files.
- `## Config Files` — each config file (`*.config.*`, `config.toml`,
  `settings.json`, etc.), its keys, and which files read those keys.
- `## Schemas` — database schemas, JSON schemas, OpenAPI specs with paths.

Mark every key with a `referenced: <yes|no>` field — the
`docs-deprecation-hunter` uses this directly to flag orphans.

## doc-inventory.md

Emitted by `docs-inventory`.

Markdown.  One entry per doc file with:
- Path
- Stated purpose (from the file's own opening)
- Top-level headings
- A short summary of the claims the doc makes (technical assertions a
  reader would rely on)

Covers: `README.md` (all levels), `CLAUDE.md`, `docs/**`, `/docs/**`,
`.github/**/*.md` user-facing docs, `CHANGELOG.md`.

## glossary.md

Emitted by `docs-glossary-steward`.

Markdown.  Alphabetized canonical definitions:

```markdown
## Marketplace
A catalog of plugins installable together via `/plugin marketplace add`.
**First defined in:** `README.md`
**Alternate forms seen:** "plugin marketplace", "the marketplace"
```

Includes acronyms, product terms, internal jargon.  Each entry notes the
canonical source and any inconsistent variants.

## recent-changes.md

Emitted by `docs-history-reconciler`.

Markdown.  Grouped summary of the last 90 days of git history (or repo
lifetime if shorter), partitioned by area:

```markdown
## plugins/feature-creator (last 90 days)

- 2026-04-05: v0.2.0 release — four new skills (planner, reviewer, etc.)
- 2026-04-18: marketplace install fix (PR #9)
- ...

**Likely doc impact:** `plugins/feature-creator/README.md`, root README plugin table
```

Each section ends with a `Likely doc impact:` list so auditors can
prioritize.
