---
name: dead-air-reel
description: Build one reported Dead Air deep-dive Reel (plus its carousel) on any topic — a dashboard record, URLs, or a plain-language topic — with an honest 11-outlet coverage check.
argument-hint: "<topic | record ID | URL…> [--families open|close] [--post] [--unattended]"
disable-model-invocation: true
---

Build one reported deep-dive Reel: $ARGUMENTS

This command is **fire and forget** (SPEC §0). It never asks a question the rules answer, fixes its own failures by cutting copy (at most three passes), stops cleanly when it must, logs every judgment in the calls JSON, and **ends with the §11 report**.

**It never asks about the angle.** When the brief claims more than the record supports, it builds the documented version and says so in the report. (SPEC §0 overrides §5.3 step 3, per Imran.) Its one ask case is whether the post is for posting (phase 8).

## Arguments

`<topic>` is any of:
- a Stories record ID or title fragment → **dashboard mode** (the grid comes from the row's recorded checks);
- one or more URLs → **ad-hoc mode**;
- a plain-language topic ("the Hannibal directive on October 7"), or a screenshot of someone else's post with "do a quick deep dive into this" → **ad-hoc mode**.

| Flag | Effect |
| --- | --- |
| `--families open\|close` | add a families slide (`deep.family`). `open` puts it first in the Reel; `close` puts it before the Closer. |
| `--post` | it's for posting: write the IG Posts row without asking |
| `--unattended` | scheduled run: write the row, and report with SendUserMessage. Also assume unattended when started by a scheduled task. |

`/dead-air` builds its Reels with the same reporter, coverage check and renderer.

---

## Phase 0 — Setup

Resolve `DA_ROOT` exactly as in `/dead-air` phase 0a:

```bash
DA_ROOT="${CLAUDE_PLUGIN_ROOT:-}"
if [ ! -f "$DA_ROOT/scripts/render.py" ] && [ -f "$HOME/.claude/plugins/installed_plugins.json" ]; then
  DA_ROOT="$(python3 -c 'import json,os
p=json.load(open(os.path.expanduser("~/.claude/plugins/installed_plugins.json"))).get("plugins",{})
k=[k for k in p if k.startswith("dead-air@")]
print(p[k[0]][-1]["installPath"] if k else "")')"
fi
if [ -f "$DA_ROOT/scripts/render.py" ]; then echo "DA_ROOT=$DA_ROOT"; else echo "DA_ROOT=unresolved"; fi
```

Below, `${CLAUDE_PLUGIN_ROOT}` means `DA_ROOT`. Never search the filesystem for it. If it's unresolved, use the project copies of the scripts and the spec, or stop cleanly if they're missing.

Do `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §1 (config, workspace, scripts, fonts, design system, today). Read `${CLAUDE_PLUGIN_ROOT}/references/reel-spec.md`, `${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md`, `${CLAUDE_PLUGIN_ROOT}/references/post-schema.md` and `${CLAUDE_PLUGIN_ROOT}/references/report-format.md`.

## Phase 1 — Frame

Resolve the topic:
- **Record ID or title fragment:** fetch the Stories row. If several rows match a fragment, take the best match (exact title, then Flagged, then most recent) and log the choice.
- **URL or topic:** no row. `record_id: null`, `mode: "adhoc"`.

Restate the topic as one sentence and name the angle the record likely supports. Write both into the calls as the first entry, "Angle." If the brief overclaims, the call reads "Brief said X; the record supports Y; the Reel uses Y." **Don't ask; proceed.**

Pick the slug for the file names: 1–2 lowercase words (e.g. `hannibal`). The post is `<date>-deep-<slug>`.

## Phase 2 — Report

Launch `dead-air-reporter` (`subagent_type: "dead-air:dead-air-reporter"`) with: the row or the topic and URLs, the run date, `families: <none|open|close>`, and `DA_ROOT`. If there's no Agent tool, read `${CLAUDE_PLUGIN_ROOT}/agents/dead-air-reporter.md` and follow it inline.

- A `stop` result → stop cleanly. Name what was missing and what Imran could supply (e.g. a reachable copy of the source).
- `family: null` when one was asked for → build without it, and say why in the report. Never substitute a weaker quote.
- Every correction goes in the calls and the report. **The sources win.**

## Phase 3 — Coverage

- **Dashboard mode:** build the grid, `us`, `meta`, `stat`, `confidence` and `days_dark` from the row's recorded checks, then run the one freshness WebSearch for US Tier-A pickup since Last checked. If there's a pickup, log it and go on in ad-hoc mode (`mode: "adhoc"`, the pickup as `ran`), since the Reel was asked for.
- **Ad-hoc mode:** launch `dead-air-coverage` (`subagent_type: "dead-air:dead-air-coverage"`) with the claim, the reporter's `first_foreign_report`, the window "since <first report date>", the run date and `DA_ROOT`. Build the story slide from its verdicts per `${CLAUDE_PLUGIN_ROOT}/references/reel-spec.md` §3: `ran` squares allowed, every `unchecked` named in `us` and `meta`, `confidence` from the agent, `days_dark` from the first foreign report to the run date (**always set**). Apply the breaker rule to `broke_candidate` and log it. Put the agent's `calls` in the calls, and its `new_quirks` in the report.

## Phase 4 — Build

Write `dead-air/posts/<date>-deep-<slug>.json` and `-calls.json` per `${CLAUDE_PLUGIN_ROOT}/references/post-schema.md`: `format: "deep"`, `flash: true`, the `ask` (different from the last post's; after a families slide, not "Send this to someone who reads the Times."), the families block, the captions with the Sources line, and alt text for every carousel slide.

## Phase 5 — Render

```bash
python3 dead-air/render.py dead-air/posts/<date>-deep-<slug>.json <design_dir> dead-air/out/<date>-deep-<slug>
```

Render the full post: the deep carousel (5 slides, or 6 with families) and the Reel. Fix failures per `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §5, at most three passes.

## Phase 6 — QA

Launch `dead-air-qa` (`subagent_type: "dead-air:dead-air-qa"`) with `out_dir`, `post_json`, `calls_json`, the run date and `DA_ROOT`. `FIXES` → back to phase 4. At most three passes; then deliver and list what's left.

## Phase 7 — Deliver

1. **Review page** per `${CLAUDE_PLUGIN_ROOT}/references/review-page.md`:
   `python3 dead-air/review_page.py <post.json> dead-air/out/<name> <calls.json> --title "Dead Air: <Slug>" --h1 "Dead Air · <The subject>" --name dead-air-<slug>`
   Publish it as a new artifact with its media. If it can't be published, follow `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §6.
2. **Project docs:** the post JSON, the calls JSON and `<date>-deep-<slug>.md` in `dead-air/posts/`.

## Phase 8 — IG Posts row

Per `${CLAUDE_PLUGIN_ROOT}/references/airtable-guide.md`, Format `deep`, Status Ready. Write it only:
- with `--post`, or in an unattended run: write it;
- otherwise, interactive → ask once, **after** everything is delivered: "Is this Reel for posting? (writes an IG Posts row, Status Ready)". With no answer, write no row, and say so in the report.

**Never write the Stories table. Never email. Never post to Instagram.**

## Phase 9 — Report

The report in `${CLAUDE_PLUGIN_ROOT}/references/report-format.md`: what was made, with the link and the Reel's length; the angle and any claim held back; the coverage findings (which outlets ran it, which couldn't be checked); corrections; open calls. **Always the last step.**
