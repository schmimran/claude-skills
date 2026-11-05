---
name: dead-air-carousel
description: Build or re-cut one Dead Air carousel from chosen Stories records or an existing post JSON — no story selection; optional Reel with --with-reel.
argument-hint: "<record IDs…> [--format single|bundle|weekly|update] | --from <project path to post JSON> [--with-reel] [--post] [--unattended]"
disable-model-invocation: true
---

Build one Dead Air carousel: $ARGUMENTS

This command is **fire and forget** (SPEC §0). It never asks a question the rules answer, fixes its own failures by cutting copy (at most three passes), stops cleanly when it must, logs every judgment in the calls JSON, and **ends with the §11 report**. It has **one** ask case: whether the carousel is for posting (see phase 8).

## Arguments

- `<record IDs…>`: build from these Stories records, **in this order**. The format comes from the count (1 → single, 3 → bundle) unless `--format` says otherwise. Any other count without `--format` → stop cleanly and say why.
- `--from <project path>`: re-cut an existing post (e.g. after a correction). Read that post JSON and its calls; write a **new version**, `<date>-<format>-v2.json` (or the next free `-vN`). **Never overwrite the original.** The re-cut keeps the original's `date`; its calls say what changed and why.
- `--with-reel`: also build the lead story's Reel, by the same path as `/dead-air-reel`. Without it, render with `--only carousel` and leave out the review page's Reel. A single, bundle or weekly still needs a `reel` block to pass the copy checks; see phase 4.
- `--post`: the carousel is for posting. Write the IG Posts row without asking.
- `--unattended`: scheduled run. Write the row with Status Ready, and report with SendUserMessage. Also assume unattended when started by a scheduled task.

No story selection. The freshness search and QA still run.

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

Do `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §1 (config, workspace, scripts, fonts, design system, today). Read `${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md`, `${CLAUDE_PLUGIN_ROOT}/references/post-schema.md`, `${CLAUDE_PLUGIN_ROOT}/references/airtable-guide.md` and `${CLAUDE_PLUGIN_ROOT}/references/report-format.md`.

## Phase 1 — Read

- **Record IDs:** fetch each Stories row (every field in config; Notes and Absence evidence in full), plus the IG Posts rows (newest first) for the last ask and the last Flash. A record that doesn't exist, or isn't Flagged with Verified or Probable confirmation, → stop cleanly and name it. This command doesn't choose substitutes.
- **`--from`:** read the post JSON and its `-calls.json` from the project. If either can't be read, stop cleanly.

## Phase 2 — Shape

Set `format`, `flash` (`${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md` §3), and an `ask` that differs from the last post's. Order the stories as given; don't re-rank. For a re-cut, change only what the correction needs, and log each change.

## Phase 3 — Freshness

One WebSearch per story for US Tier-A pickup since the row's Last checked. A pickup means that story can't run as dark: stop cleanly and report it, since the stories were Imran's choice and this command doesn't substitute. (For an UPDATE post, the pickup *is* the story.)

## Phase 4 — Report (the lead story's Reel block)

Singles, bundles and weeklies need `reel` = {lead story, deep block} to pass the copy checks, even when only the carousel is rendered. Launch `dead-air-reporter` (`subagent_type: "dead-air:dead-air-reporter"`) on the lead story, with the row, the run date, `families: none` and `DA_ROOT`. If there's no Agent tool, read `${CLAUDE_PLUGIN_ROOT}/agents/dead-air-reporter.md` and follow it inline. For a `--from` re-cut, reuse the existing `reel` block unless the correction touches it.

Record every correction in the calls and the report. **The sources win; never edit the Stories row.**

For a non-Flash **single**, the carousel story's `headline` is the reporter's `headline_short` (a hook-l cover holds about 6 words); `reel.story.headline` keeps the full Flash-length line.

## Phase 5 — Build

Write the post JSON and calls JSON per `${CLAUDE_PLUGIN_ROOT}/references/post-schema.md`, building each grid from the row's recorded checks (`${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md` §4–5). Name them `<date>-<format>` (or `-vN` for a re-cut).

## Phase 6 — Render

```bash
python3 dead-air/render.py dead-air/posts/<name>.json <design_dir> dead-air/out/<name> --only carousel   # drop --only with --with-reel
```

Fix failures per `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §5, at most three passes. With `--with-reel`, put the reported Reel length in the calls' `reel_length`; on a carousel-only run, leave `reel_length` out.

## Phase 7 — QA

Launch `dead-air-qa` (`subagent_type: "dead-air:dead-air-qa"`) with `out_dir`, `post_json`, `calls_json`, the run date and `DA_ROOT`. `FIXES` → back to phase 5. At most three passes; then deliver and list what's left.

## Phase 8 — Deliver

1. **Review page** per `${CLAUDE_PLUGIN_ROOT}/references/review-page.md`. Use `--name dead-air-<date>-<format>-vN` for a re-cut. A carousel-only run has no MP4 or cover to attach, so publish the PNGs only. With no `reel_length` in the calls, `review_page.py` leaves out the Reel panel and the Reel caption.
2. **Project docs:** the post JSON, the calls JSON and `<name>.md` in `dead-air/posts/`.
3. **IG Posts row**, only if the carousel is for posting:
   - `--post` or an unattended run → write the row, Status Ready.
   - otherwise, interactive → this is the command's one question: "Is this carousel for posting? (writes an IG Posts row, Status Ready)". Ask it **after** everything else is delivered, so nothing waits on the answer. If there is no answer, write no row, and say so in the report.

**Never write the Stories table. Never email. Never post to Instagram.**

If a review page can't be published, follow `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §6.

## Phase 9 — Report

The report in `${CLAUDE_PLUGIN_ROOT}/references/report-format.md`. **Always the last step.**
