# docs-steward

Actively reconciles documentation against the deployed code.  Runs on
demand, builds canonical reference indexes of the repo, audits docs
through multiple critic personas, edits the docs on a feature branch,
re-reads the result to verify coherence, and opens a single PR.

## Quick Start

1. **Install the marketplace** (once per machine):
   ```bash
   /plugin marketplace add https://github.com/schmimran/claude-skills
   ```

2. **Run against the current repo**:
   ```bash
   /docs-steward
   ```
   Or target a specific repo:
   ```bash
   /docs-steward owner/repo
   ```

3. Review the PR the plugin opens.  It lists every edit, every
   deletion, and any residual items the automated re-read couldn't
   resolve.

## Prerequisites

- **GitHub CLI** installed and authenticated (`gh auth status`).
- **Git** with a clean working tree in the target repo (the editor
  refuses to proceed with uncommitted changes).
- **Internet access** (the link-checker hits external URLs).

## What it does

The plugin chains six phases:

1. **Phase 0 — Index build** (7 parallel agents).  Emit canonical
   reference artifacts to `.claude/docs-cache/<run-id>/indexes/`:
   file tree, symbol index, public-surface map, config catalogue,
   doc inventory, glossary, recent-changes summary.
2. **Phase 1 — Drift audit** (8 parallel auditors).  Each auditor
   reads the indexes + docs and writes a findings file.
3. **Phase 2 — Consolidation**.  Merge findings, resolve
   duplication, detect conflicts.  Stops for user adjudication when
   it can't produce a coherent plan.
4. **Phase 3 — Editing**.  Apply the plan on a feature branch with
   one commit per doc file.  Deletions → restructures → edits.
5. **Phase 4 — Manual re-read**.  The same persona that did the
   walk in Phase 1 re-reads the edited corpus.  One small-fix loop
   is allowed.
6. **Phase 5 — Final review + PR**.  Tenet compliance check, PR
   body assembled, branch pushed, single PR opened.

## Core tenets

Every agent loads these at the start of its run.  They are the
ground rules the plugin enforces.

1. **READMEs are user-facing** — fast-scanning, links to backing
   docs for depth.
2. **Root README is the entry point** — a first-time reader starts
   there and gets coherent ongoing context.
3. **The corpus must read as a manual** — verified by the
   `docs-manual-reader` persona who walks the docs like a user,
   once before edits and once after.
4. **Section READMEs are consistent** — same components, comparable
   depth.
5. **Deprecated/orphaned content is removed, not annotated** —
   including unused env keys and config values.
6. **No duplication** — one canonical home, links everywhere else.
7. **Post-edit re-read** — the manual-reader verifies coherence
   after the editor's pass.

Full text in [`references/tenets.md`](references/tenets.md).

## Architecture

| Component | Type | Model | Role |
|-----------|------|-------|------|
| `docs-steward` | Command | (inherits) | Orchestrator |
| `docs-file-cartographer` | Agent | sonnet | Builds `file-tree.md` |
| `docs-symbol-indexer` | Agent | sonnet | Builds `symbols.json` |
| `docs-route-mapper` | Agent | sonnet | Builds `routes.md` |
| `docs-config-cataloger` | Agent | sonnet | Builds `config.md` |
| `docs-inventory` | Agent | sonnet | Builds `doc-inventory.md` |
| `docs-glossary-steward` | Agent | sonnet | Builds `glossary.md` |
| `docs-history-reconciler` | Agent | sonnet | Builds `recent-changes.md` |
| `docs-intent-auditor` | Agent | sonnet | Flags doc-vs-code drift |
| `docs-info-architect` | Agent | opus | Structure + duplication + gaps |
| `docs-onboarding-reviewer` | Agent | opus | Simulates new-contributor walk |
| `docs-reference-validator` | Agent | sonnet | Validates internal references |
| `docs-example-verifier` | Agent | sonnet | Validates code blocks |
| `docs-link-checker` | Agent | sonnet | Validates external URLs |
| `docs-manual-reader` | Agent | opus | Walks corpus as a manual (Phase 1 + 4) |
| `docs-deprecation-hunter` | Agent | sonnet | Finds orphans to delete |
| `docs-consolidator` | Agent | opus | Merges findings, triggers checkpoints |
| `docs-editor` | Agent | opus | Applies edits on the branch |
| `docs-final-reviewer` | Agent | opus | Tenet check + PR |

## Cache layout

All Phase 0/1 artifacts and intermediate state live under
`<REPO_DIR>/.claude/docs-cache/<RUN_ID>/`.  This directory is
gitignored by the orchestrator at the start of every run.  Old runs
are not auto-pruned — you can inspect any prior run in place.

See [`references/cache-layout.md`](references/cache-layout.md) for
the full structure.

## Checkpoint behavior

The consolidator stops the pipeline and asks for adjudication when
it can't produce a coherent plan.  Triggers include high conflict
density, structural incoherence, production config deletions,
secret-adjacent deletions, and large-scale deletions.  Details in
[`references/checkpoint-criteria.md`](references/checkpoint-criteria.md).

When a checkpoint fires, the plugin exits without creating a branch
or editing files.  Inspect the cache (`checkpoint-required.md`),
adjudicate, and re-run.

## What does NOT happen automatically

- **The PR is never auto-merged** — a human always reviews.  The
  plugin is architecturally prohibited from merging, even if
  explicitly instructed.  If asked to merge, it will refuse and ask
  you to do so in a fresh session.
- **The feature branch always originates from the remote default
  branch** — regardless of any global or repo-level `CLAUDE.md`
  instruction.  This is a non-overridable invariant.
- **Code-level deletions of deprecated symbols are not performed** —
  only docs, config files, and env templates are in scope for
  deletion.  Orphan code symbols are flagged in findings for human
  follow-up.
- **New docs are not generated from scratch** — the plugin assumes
  docs exist to steward.  Gaps are flagged; creation is a human
  decision.
- **Real `.env` files are not touched** — only `.env.example` and
  equivalent templates.  Secrets are never deleted, only flagged.

## References

- [`references/tenets.md`](references/tenets.md) — the seven rules
  enforced across every agent.
- [`references/findings-schema.md`](references/findings-schema.md) —
  shared finding record shape.
- [`references/index-artifact-spec.md`](references/index-artifact-spec.md)
  — Phase 0 artifact formats.
- [`references/readme-style-guide.md`](references/readme-style-guide.md)
  — user-facing README voice and structure.
- [`references/voice-guide.md`](references/voice-guide.md) — voice
  preservation rules for the editor.
- [`references/checkpoint-criteria.md`](references/checkpoint-criteria.md)
  — when the consolidator pauses.
- [`references/manual-reader-protocol.md`](references/manual-reader-protocol.md)
  — how the manual-reader walks the corpus.
- [`references/cache-layout.md`](references/cache-layout.md) —
  `.claude/docs-cache/` structure and lifecycle.
- [`references/pr-template.md`](references/pr-template.md) — PR body
  template.

## License

[MIT](../../LICENSE)
