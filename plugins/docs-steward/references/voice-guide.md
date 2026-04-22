# Voice Guide

Applied by `docs-editor` when rewriting content.

## Rule of least surprise

Match the voice already present in the target doc.  Changing a doc's voice
is not a drift-fix — it is a rewrite, and is only warranted if a finding
explicitly calls for it with `action: restructure` and a tenet reference.

## When inferring voice from the existing corpus

Sample voice from the root README first, then the nearest sibling docs.
If these disagree, pick the majority voice across the repo's user-facing
docs (not internal `CLAUDE.md`).

## Defaults when the doc is essentially empty

Fall back to:

- Second person neutral ("You can run...", "Run...").
- Active voice.
- Present tense.
- No emoji.
- No exclamation points.
- Sentence case for headings unless the repo has established title case.
- Code blocks in fenced triple-backtick with language hint where known.

## Preserving intent during edits

A drift edit replaces incorrect content with correct content.  It does
**not**:

- Reword correct-but-stylistically-imperfect prose.
- Rearrange sections unless the finding calls for `action: restructure`.
- Add meta-commentary ("This section has been updated...").
- Add dates, authors, or change markers — git history is the record.

## Deletion over annotation

Per tenet 5, when content is stale, delete it.  Do not leave:

- "Deprecated: ..."  markers.
- "Note: this used to ..."  sidebars.
- Commented-out sections.

The exception is when the finding explicitly marks `action: edit` and the
edit requires noting a transition for the reader — in which case the
transition note is brief and in the same voice as the rest of the doc.

## Links

- Use relative paths for intra-repo links: `[text](path/to/file.md)`.
- Use full URLs for external links, with descriptive anchor text.
- Never link to line numbers that are likely to drift (prefer section
  anchors).  Exception: `CLAUDE.md` reference tables where line numbers
  are inspected by agents.
