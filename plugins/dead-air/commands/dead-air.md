---
name: dead-air
description: Daily Dead Air editor for @schmimknews — reads the News Blind Spots dashboard, picks format and stories, builds the carousel and its deep-dive Reel, publishes a review page, logs to Airtable.
argument-hint: "[--date YYYY-MM-DD] [--reels 1|2] [--format single|bundle|weekly|deep] [--dry-run] [--unattended]"
disable-model-invocation: true
---

Run today's Dead Air post from the News Blind Spots dashboard: $ARGUMENTS

This command is **fire and forget** (SPEC §0). Imran runs it once and gets finished work back.
- **Never ask a question the rules answer.** Where a rule names a default, take it and log the choice in the calls JSON. `/dead-air` has no ask cases at all.
- **Fix your own failures:** cut copy and re-render, up to three passes. QA findings go back to the build step. Never shrink type, edit CSS or loosen a check.
- **Stop cleanly when you must:** make nothing half-finished, name the step that failed and why, and say what Imran can do.
- **Log every judgment call** in the calls JSON.
- **End with the §11 report.** Every run, including a stop.

Done means: a published review page, project docs, an IG Posts row, and a short report.

## Arguments

| Flag | Default | Effect |
| --- | --- | --- |
| `--date YYYY-MM-DD` | today, US Eastern | the run date |
| `--reels 1\|2` | up to 2 | cap the number of Reels |
| `--format single\|bundle\|weekly\|deep` | chosen by the rules | override the format choice; log it |
| `--dry-run` | off | render and publish the review page, write project docs, **skip Airtable** |
| `--unattended` | off | scheduled run: report with SendUserMessage. Also assume unattended when started by a scheduled task. |

---

## Phase 0 — Setup

### 0a. Find the plugin

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

Below, `${CLAUDE_PLUGIN_ROOT}` means `DA_ROOT`. **Never search the filesystem** for the plugin.

If `DA_ROOT` is unresolved (e.g. claude.ai doesn't put plugin files on disk), the references and scripts come from the project docs instead: `dead-air/render.py`, `dead-air/review_page.py`, and the project's copy of the spec. If any of them is missing, stop cleanly ("Can't reach the dead-air plugin files or their project copies") and report.

### 0b. Shared setup

Read `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` and do §1 in order: config, workspace, scripts, fonts, design system, today. Each of these is a clean stop on failure, with the exact message given there.

Then read:
- `${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md`
- `${CLAUDE_PLUGIN_ROOT}/references/post-schema.md`
- `${CLAUDE_PLUGIN_ROOT}/references/airtable-guide.md`
- `${CLAUDE_PLUGIN_ROOT}/references/report-format.md`

Start the calls list now. Its first entries are where the scripts came from, and the run date.

## Phase 1 — Read

Use the Airtable MCP with the IDs from config (field IDs, never names; see the Airtable guide).
- **IG Posts:** all rows, newest first by Post date.
- **Stories:** rows where Status = Flagged, with every field config lists. Read Notes and Absence evidence in full.

If Airtable can't be read, stop cleanly at phase 1.

## Phase 2 — Choose

Apply `${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md` in order:
1. **Format** (§1), unless `--format` was given.
2. **Flash** (§3).
3. **Stories** (§2): eligibility, then ranking, then the bundle topic rule. List every skipped row and its reason.
4. **Reel stories:** the lead story. Then, unless `--reels 1`, the next eligible story as a second Reel candidate (confirmed in phase 4).
5. **Ask:** the next of the three that differs from the last post's ask.

**No eligible story** → stop cleanly: "No eligible story: <the reasons>". Make nothing.

Log the plan in the calls: the format and why, Flash and why, each story and why, the skips.

## Phase 3 — Freshness

For each chosen story, run one WebSearch for US Tier-A pickup since the row's Last checked. A pickup drops the story; log and report it, then re-run phase 2 without it. The check window on the slides stays the dashboard's.

## Phase 4 — Report

For each Reel story, launch `dead-air-reporter` with the Agent tool (`subagent_type: "dead-air:dead-air-reporter"`). Pass it: the full Stories row, the run date, `families: none`, and `DA_ROOT`. Run the two Reel stories in parallel when there are two. If there's no Agent tool, read `${CLAUDE_PLUGIN_ROOT}/agents/dead-air-reporter.md` and follow it inline.

- A `stop` result for the **lead** story → stop cleanly; nothing is made.
- A `stop` result, or `supports_second_reel: false`, for the **second** story → drop the second Reel and say why. The first post goes ahead.
- Put every `corrections` entry in the calls ("Corrected: …") and in the report's dashboard corrections. **The sources win.** Never edit the Stories row.

For each story, build the grid, `us`, `meta`, `stat`, `confidence` and `days_dark` from the row's **recorded checks**, per `${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md` §4–5. Apply the breaker rule and log it every time it applies.

## Phase 5 — Build

Write `dead-air/posts/<date>-<format>.json` and `<date>-<format>-calls.json` per `${CLAUDE_PLUGIN_ROOT}/references/post-schema.md`:
- the day's post: `stories`, plus `reel` = the lead story (with the reporter's Flash-length `headline`) and its `deep` block. On a **single** whose cover is not Flash, `stories[0].headline` is the reporter's `headline_short` (a hook-l cover holds about 6 words); on a Flash single it can be the full `headline`. `headline_short` is never written into the post JSON as its own key;
- the second Reel, if any: a separate DEEP post, `<date>-deep-<slug>.json` + `-calls.json`. It is five slides (Flash cover, timeline, claims, story slide, Closer).
- captions and alt text per `${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md` §6; the `sources` line from the reporter's `sources_line` plus the dashboard sources;
- `facts` in the calls: format, Flash, the carousel slot, the Reel slot (2–4 hours after the carousel), the ask.

## Phase 6 — Render

```bash
python3 dead-air/render.py dead-air/posts/<name>.json <design_dir> dead-air/out/<name>
```

Fix failures per `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §5: cut copy, re-run, at most three passes. Write each cut back into the post JSON, and log any cut that changes meaning. Put the reported Reel length in `reel_length`.

## Phase 7 — QA

Launch `dead-air-qa` (`subagent_type: "dead-air:dead-air-qa"`) for each post, with `out_dir`, `post_json`, `calls_json`, the run date and `DA_ROOT`. Inline fallback as in phase 4.
- `FIXES` → apply them to the post JSON (phase 5), then go back to phase 6. At most three QA passes.
- After three passes, deliver and list the remaining fixes under Open calls.

## Phase 8 — Deliver

For each post, in this order:
1. **Review page:** follow `${CLAUDE_PLUGIN_ROOT}/references/review-page.md`. Run `review_page.py` with no flags for the day's post. For a second-Reel deep post, use `--title "Dead Air: <Slug>" --h1 "Dead Air · <The subject>" --name dead-air-<slug>`. Publish each as a **new** artifact with its media. If the artifact can't be published, follow `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §6 and skip steps 2–3.
2. **Project docs:** write the post JSON, the calls JSON and `<name>.md` to `dead-air/posts/` with the Projects tool. The `.md` holds the review link, the IG Posts row ID (added after step 3), the slots, the stories, the dashboard corrections and the Reel sources.
3. **IG Posts row** (skip with `--dry-run`): per `${CLAUDE_PLUGIN_ROOT}/references/airtable-guide.md`, one row per post with Status Ready. Then update the `.md` with the row ID.

**Never write the Stories table. Never email. Never post to Instagram.**

## Phase 9 — Report

Send the report in `${CLAUDE_PLUGIN_ROOT}/references/report-format.md`: what was made (with the links), the stories and why, what was held back or skipped, the dashboard corrections to make, and the open calls. In an unattended run, send it with SendUserMessage if available. **This is always the last step.**
