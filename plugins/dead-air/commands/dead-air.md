---
name: dead-air
description: Daily Dead Air editor for @schmimknews — reads the dashboard, picks the day's post and any Update companions, builds carousels and Reels, publishes a review page, logs to Airtable.
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

Done means: a published review page, project docs, an IG Posts row per post (the day's post, plus one per Update companion), and a short report.

## Arguments

| Flag | Default | Effect |
| --- | --- | --- |
| `--date YYYY-MM-DD` | today, US Eastern | the run date |
| `--reels 1\|2` | up to 2 | cap the number of deep-dive Reels (an Update companion's short Reel doesn't count) |
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

If `DA_ROOT` is unresolved (e.g. claude.ai doesn't put plugin files on disk), the references and scripts come from the project docs instead: `dead-air/render.py`, `dead-air/review_page.py`, `dead-air/plan_day.py`, and the project's copy of the spec. If any of them is missing, stop cleanly ("Can't reach the dead-air plugin files or their project copies") and report.

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
- **IG Posts:** all rows, newest first by Post date, with Status and Carousel slot.
- **Stories:** rows where Status = Flagged, with every field config lists. Read Notes and Absence evidence in full.
- **Stories behind recent posts:** every row a post from the last 30 days carried, whatever its Status. A Covered one may be an Update or a correction (`${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md` §1.1). For each Covered row, find the first domestic Tier-A pickup and its date from the row's recorded checks.

If Airtable can't be read, stop cleanly at phase 1.

## Phase 2 — Choose

1. **Plan.** Write the rows into `dead-air/out/plan-<date>.json` in the shape of `${CLAUDE_PLUGIN_ROOT}/references/post-schema.md` §3, with your `hold` and `override` calls per row and `--format` as `format_override`. Run `python3 dead-air/plan_day.py dead-air/out/plan-<date>.json`. It applies "Ready with a past slot counts as posted" and the eligibility, ranking, format, Update and correction rules of `${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md` §0–2. **Take its output as the plan; don't re-decide it.** If it fails, stop cleanly at phase 2 and quote the error.
2. **The day's post,** chosen as if no Update were due:
   - **Format** = `day.format`. **Stories** = the top of `day.eligible` (one for a single, three for a bundle or weekly), applying the bundle topic rule (§2) by hand. Log every `day.skipped` row and its reason.
   - **Flash** (§3), against the last posted row.
   - **Reel stories:** the lead story. Then, unless `--reels 1`, the next eligible story as a second Reel candidate (confirmed in phase 4).
   - **Ask:** the next of the three that differs from the last post's ask.
3. **Update companions** = `companions` (at most two, oldest pickup first). Each gets an ask different from the day's post's. Note `deferred_updates` for the report.
4. **Corrections** = `corrections`: no post. Their `line`s go at the top of the report. `unresolved` goes under Open calls.

**No eligible story** (`day.format` is null) → no day's post: stop cleanly with "No eligible story: <the reasons>", and make nothing, companions included (a companion rides along with a day's post; it never runs alone). Still report the corrections.

Log the plan in the calls: "Ready rows with a past slot counted as posted" (once, naming `assumed_posted`), the format and its rule, Flash and why, each story and why, the skips, each companion and each correction.

## Phase 3 — Freshness

For each chosen story of the day's post, run one WebSearch for US Tier-A pickup since the row's Last checked. A pickup drops the story; log and report it, then re-run phase 2 without it. The check window on the slides stays the dashboard's.

Companions aren't re-searched: their grid and `still_dark` come from the row's recorded checks, dated to the scan's latest pass.

## Phase 4 — Report

For each Reel story of the day's post, launch `dead-air-reporter` with the Agent tool (`subagent_type: "dead-air:dead-air-reporter"`). Pass it: the full Stories row, the run date, `families: none`, and `DA_ROOT`. Run the two Reel stories in parallel when there are two. If there's no Agent tool, read `${CLAUDE_PLUGIN_ROOT}/agents/dead-air-reporter.md` and follow it inline.

- A `stop` result for the **lead** story → stop cleanly; nothing is made.
- A `stop` result, or `supports_second_reel: false`, for the **second** story → drop the second Reel and say why. The first post goes ahead.
- Put every `corrections` entry in the calls ("Corrected: …") and in the report's dashboard corrections. **The sources win.** Never edit the Stories row.

For each Update companion, read the late coverage itself (one search, or fetch, per pickup): what it added or changed, in its own words, for `update.added` and each pickup's `note`. Every line traces to a source in the calls. Don't run the reporter on a companion.

For each story, build the grid, `us`, `meta`, `stat`, `confidence` and `days_dark` from the row's **recorded checks**, per `${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md` §4–5. Apply the breaker rule and log it every time it applies.

## Phase 5 — Build

Write `dead-air/posts/<date>-<format>.json` and `<date>-<format>-calls.json` per `${CLAUDE_PLUGIN_ROOT}/references/post-schema.md`:
- the day's post: `stories`, plus `reel` = the lead story (with the reporter's Flash-length `headline`) and its `deep` block. On a **single** whose cover is not Flash, `stories[0].headline` is the reporter's `headline_short` (a hook-l cover holds about 6 words); on a Flash single it can be the full `headline`. `headline_short` is never written into the post JSON as its own key;
- the second Reel, if any: a separate DEEP post, `<date>-deep-<slug>.json` + `-calls.json`. It is five slides (Flash cover, timeline, claims, story slide, Closer).
- each Update companion: `<date>-update-<slug>.json` + `-calls.json`, with `format: "update"`, `flash: false`, its `slug` and its `update` block. Read the original post (`of_post`) from the project and copy its story object, as posted, into `update.then_story`; its grid then is `then_grid`. If `of_post` can't be read, stop that companion cleanly (the day's post goes ahead) and report it.
- captions and alt text per `${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md` §6; the `sources` line from the reporter's `sources_line` (or, for a companion, the original post's sources plus the late coverage) plus the dashboard sources;
- `facts` in the calls: format, Flash, the carousel slot, the Reel slot (2–4 hours after the carousel), the ask. A companion's carousel slot is the next open slot from 3:00pm ET the same day; its Reel goes 2–4 hours later, or the next morning if that runs past 9:00pm ET (§1.1).

## Phase 6 — Render

```bash
python3 dead-air/render.py dead-air/posts/<name>.json <design_dir> dead-air/out/<name>
```

Run it once per post, each into its own folder. Fix failures per `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §5: cut copy, re-run, at most three passes. Write each cut back into the post JSON, and log any cut that changes meaning. Put the reported Reel length in `reel_length`.

An update's copy-check failure that is about facts, not length (a `ran` square without a pickup, a wrong "N days late", a pickup on or before our post), is never fixed by cutting: correct the facts from the sources, or drop that companion and report why.

## Phase 7 — QA

Launch `dead-air-qa` (`subagent_type: "dead-air:dead-air-qa"`) for each post, companions included, with `out_dir`, `post_json`, `calls_json`, the run date and `DA_ROOT`. Inline fallback as in phase 4.
- `FIXES` → apply them to the post JSON (phase 5), then go back to phase 6. At most three QA passes.
- After three passes, deliver and list the remaining fixes under Open calls.

## Phase 8 — Deliver

For each review page, in this order:
1. **Review page:** follow `${CLAUDE_PLUGIN_ROOT}/references/review-page.md`. Run `review_page.py` for the day's post with one `--companion <update.json> <update-calls.json>` per Update companion: they share the day's page. For a second-Reel deep post, use `--title "Dead Air: <Slug>" --h1 "Dead Air · <The subject>" --name dead-air-<slug>` (its own page). Publish each page as a **new** artifact with the media of every post on it. If the artifact can't be published, follow `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §6 and skip steps 2–3.
2. **Project docs:** for each post, write the post JSON, the calls JSON and `<name>.md` to `dead-air/posts/` with the Projects tool. The `.md` holds the review link, the IG Posts row ID (added after step 3), the slots, the stories, the dashboard corrections and the Reel sources.
3. **IG Posts rows** (skip with `--dry-run`): per `${CLAUDE_PLUGIN_ROOT}/references/airtable-guide.md`, **one row per post**, Status Ready: the day's post, each companion (Format `update`, the same review link) and any second-Reel deep post. Then update each `.md` with its row ID.

**Never write the Stories table. Never email. Never post to Instagram.**

## Phase 9 — Report

Send the report in `${CLAUDE_PLUGIN_ROOT}/references/report-format.md`: any "Correction due" lines first, then what was made (with the links, companions included), the stories and why, what was held back or skipped (deferred Updates included), the dashboard corrections to make, Ready rows more than 7 days past their slot (`stale_ready`), and the open calls. In an unattended run, send it with SendUserMessage if available. **This is always the last step.**
