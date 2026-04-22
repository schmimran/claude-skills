# README Style Guide

Applies to every `README.md` in the repo.  Enforced by `docs-info-architect`
and `docs-manual-reader`; applied by `docs-editor`.

## Tenets invoked

1 (user-facing), 2 (root is entry point), 4 (section consistency), 6 (no
duplication).

## Structure

A README should have, in order, the components that apply:

1. **Title** — H1, matches the directory or project name.
2. **One-paragraph overview** — what this is, in plain language, answers
   "what is this for?" in one breath.
3. **Quick Start** or **Installation** — copy-pasteable commands for the
   most common path.
4. **Usage** — the one or two most common invocations, with minimal context.
5. **Architecture / Components** (when there are multiple parts) — a short
   table or list linking to each component.
6. **Prerequisites** (when non-obvious) — tools, auth, env vars needed.
7. **Contributing / Development** (at root only, or where meaningful at a
   section) — links out to a dedicated `CONTRIBUTING.md` or `CLAUDE.md`
   rather than inlining.
8. **License** (at root only).

Section READMEs (e.g. under `plugins/<name>/`) use the same ordering but
omit Overview-of-the-whole-repo framing and global install steps; they
assume the reader has already landed via the root.

## Voice

- **Scannable**: bullets and tables for facts; paragraphs for concepts only.
- **Direct**: "Run X to do Y."  Not "You might want to run X so that Y can
  happen."
- **Link out for depth**: one sentence in the README, link to the full
  reference doc.
- **No marketing**: no emoji, exclamation points, or superlatives unless
  the repo's existing voice already uses them.
- **Code blocks are copy-pasteable**: assume the reader will run them
  verbatim.

## Length targets (soft)

| README | Target length |
|---|---|
| Root | 100–300 lines |
| Section (plugin/module) | 50–300 lines |
| Subsection | <100 lines — if longer, probably belongs in a backing doc |

These are soft targets.  The editor does not cut content solely for length,
but a README running 500+ lines is a strong signal content should move to
backing docs with links.

## What does NOT belong in a README

- Full API reference (goes in `docs/api.md` or generated output).
- Full architecture description (goes in `docs/architecture.md` or
  `CLAUDE.md`).
- Exhaustive config-key catalog (goes in `docs/configuration.md`).
- History or changelog detail (goes in `CHANGELOG.md`).
- Internal implementation notes (goes in `CLAUDE.md` or inline comments).

When the docs-editor finds such content in a README, it restructures
(tenet 6): moves the content to its canonical backing doc, leaves a link.

## What a good link looks like

- **Bad:** `See the contribution guide for more details.`
- **Good:** `See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add a
  plugin.` — use actual link, name the target, state what the reader will
  find there.

## Section README consistency (tenet 4)

Section READMEs under a common parent (e.g. every plugin's README) should:

- Open with the same kind of one-paragraph description.
- Have the same top-level headings where applicable.
- Use the same table format for components (if they have components).
- Link back to the root README in roughly the same way.

When sibling READMEs drift in structure, the `docs-info-architect` flags it
and the editor normalizes the weaker ones toward the strongest.
