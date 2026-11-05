---
name: dead-air
description: Daily Dead Air editor for @schmimknews — reads the dashboard, builds the day's four-story carousel and its Reel plus any Update companions, publishes a review page, logs to Airtable.
argument-hint: "[--date YYYY-MM-DD] [--reels 1|2] [--format bundle|weekly] [--dry-run] [--unattended]"
disable-model-invocation: true
---

Run today's Dead Air post from the News Blind Spots dashboard: $ARGUMENTS

This command is **fire and forget** (SPEC §0). Imran runs it once and gets finished work back.
- **Never ask a question the rules answer.** Where a rule names a default, take it and log the choice in the calls JSON. `/dead-air` has no ask cases at all.
- **Fix your own failures:** cut copy and re-render, up to three passes. QA findings go back to the build step. Never shrink type, edit CSS or loosen a check.
- **Stop cleanly when you must:** make nothing half-finished, name the step that failed and why, and say what Imran can do.
- **Log every judgment call** in the calls JSON.
- **End with the §11 report.** Every run, including a stop.

Done means: a published review page, project docs, an IG Posts row per post (the day's carousel, plus one per Update companion and per second-Reel deep post), and a short report.

## Arguments

| Flag | Default | Effect |
| --- | --- | --- |
| `--date YYYY-MM-DD` | today, US Eastern | the run date |
| `--reels 1\|2` | up to 2 | cap the number of deep-dive Reels (an Update companion's short Reel doesn't count) |
| `--format bundle\|weekly` | chosen by the rules | force the weekly on a non-Sunday, or a bundle on a Sunday; log it. A single is never the day's post. |
| `--dry-run` | off | render and publish the review page, write project docs, **skip Airtable** |
| `--unattended` | off | scheduled run: report with SendUserMessage. Also assume unattended when started by a scheduled task. |

---

## Phase 0 — Setup

**Paths this run uses.** Use these. Never search the project or the filesystem for them.

| Path | Holds | This run |
| --- | --- | --- |
| `DA_ROOT/scripts/` | `render.py`, `review_page.py`, `plan_day.py`, `cache_manifest.py` | runs them, always as `python3 -B` |
| `DA_ROOT/references/` | the rules | reads them |
| `DA_ROOT/agents/` | the agent briefs | reads one only when its agent type isn't available |
| project `dead-air/settings/config.md` | Imran's config: Airtable IDs, artifact URLs, handle | reads it first; **never writes** |
| project `dead-air/posts/` (+ `posts/legacy/`) | the post archive | reads it; adds new files only, never edits an old post |
| project `dead-air/cache/v<version>/` | a mirror of `scripts/`, `references/`, `agents/` + `VERSION` | reads it only if steps 1–2 fail; refreshes it (0b) |
| project `dead-air/dev/` | specs, prompts, notes | **never reads or writes** |
| workspace `DA_WS/src/` | the fetched plugin, the fonts, the staged cache | uploads only the staged cache, to `dead-air/cache/v<version>/` |
| workspace `DA_WS/work/<date>/` | scratch: plan input, row dumps, leads | never uploaded; deleted at the end |
| workspace `DA_WS/out/<post>/` | PNGs, MP4s, review pages | never uploaded to the project; media goes on the review page |
| workspace `DA_WS/posts/` | the post JSON, calls JSON and `.md` being written | uploaded to project `dead-air/posts/` at delivery |

**Never write to `settings/` or `dev/`. Never delete anything outside `cache/`.** A rules file found anywhere else in the project is ignored: code and rules come from `DA_ROOT` only.

### 0a. Find the code and rules (`DA_ROOT`)

Run this block once, as is:

```bash
# --- dead-air setup: identical in all three commands (a test checks) ---
DEAD_AIR_VERSION=0.3.0
export PYTHONDONTWRITEBYTECODE=1
DA_WS="$PWD/dead-air"; DA_DAY="$(date +%F)"
DA_REPO="${DEAD_AIR_REPO:-https://github.com/schmimran/claude-skills.git}"
mkdir -p "$DA_WS/work/$DA_DAY" "$DA_WS/out" "$DA_WS/posts"
da_ver() { python3 -B -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$1/.claude-plugin/plugin.json" 2>/dev/null; }
da_candidates() {
  [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && echo "$CLAUDE_PLUGIN_ROOT"
  python3 -B -c 'import json,os
p=os.path.expanduser("~/.claude/plugins/installed_plugins.json")
d=json.load(open(p)).get("plugins",{}) if os.path.isfile(p) else {}
for k,v in d.items():
    if k.startswith("dead-air@"):
        for i in (v if isinstance(v,list) else [v]): print(i.get("installPath",""))' 2>/dev/null
  for s in "$HOME"/.claude/plugins/synced/*/dead-air*; do [ -d "$s" ] && echo "$s"; done
}
DA_ROOT=""; DA_FROM=""; DA_COMMIT=unknown; DA_TRIED=""
# Step 1: a local install whose plugin.json version equals DEAD_AIR_VERSION. Never the first match blindly.
while IFS= read -r c; do
  [ -n "$c" ] && [ -f "$c/scripts/render.py" ] || continue
  v="$(da_ver "$c")"
  if [ "$v" = "$DEAD_AIR_VERSION" ]; then DA_ROOT="$c"; DA_FROM="local install $v"; break; fi
  DA_TRIED="$DA_TRIED; $c is ${v:-unversioned}"
done < <(da_candidates)
# Step 2: the repo, pinned to the release tag (main only if the tag is missing).
if [ -z "$DA_ROOT" ]; then
  rm -rf "$DA_WS/src/repo"; mkdir -p "$DA_WS/src"
  for ref in "dead-air-v$DEAD_AIR_VERSION" main; do
    if git clone -q --depth 1 --branch "$ref" --filter=blob:none --sparse "$DA_REPO" "$DA_WS/src/repo" 2>>"$DA_WS/work/$DA_DAY/clone.log" \
       && git -C "$DA_WS/src/repo" sparse-checkout set plugins/dead-air 2>>"$DA_WS/work/$DA_DAY/clone.log"; then
      c="$DA_WS/src/repo/plugins/dead-air"; DA_COMMIT="$(git -C "$DA_WS/src/repo" rev-parse HEAD)"; v="$(da_ver "$c")"
      if [ "$ref" = main ] && [ -f "$c/scripts/render.py" ]; then DA_ROOT="$c"; DA_FROM="version mismatch: ran main at $DA_COMMIT (plugin.json says ${v:-nothing})"
      elif [ "$v" = "$DEAD_AIR_VERSION" ]; then DA_ROOT="$c"; DA_FROM="repo tag dead-air-v$DEAD_AIR_VERSION"
      else DA_TRIED="$DA_TRIED; tag $ref holds version ${v:-nothing}"; fi
      break
    fi
    rm -rf "$DA_WS/src/repo"
  done
  [ -z "$DA_ROOT" ] && DA_TRIED="$DA_TRIED; repo: $(tail -1 "$DA_WS/work/$DA_DAY/clone.log" 2>/dev/null)"
elif git -C "$DA_ROOT" rev-parse HEAD >/dev/null 2>&1; then DA_COMMIT="$(git -C "$DA_ROOT" rev-parse HEAD)"; fi
if [ -n "$DA_ROOT" ]; then DA_ROOT="$(cd "$DA_ROOT" && pwd)"; fi
echo "DEAD_AIR_VERSION=$DEAD_AIR_VERSION"; echo "DA_WS=$DA_WS"; echo "DA_DAY=$DA_DAY"
echo "DA_ROOT=${DA_ROOT:-unresolved}"; echo "DA_FROM=${DA_FROM:-none}"; echo "DA_COMMIT=$DA_COMMIT"; echo "DA_TRIED=${DA_TRIED#; }"
# --- end dead-air setup ---
```

Shell state doesn't carry from one Bash call to the next. Copy the printed `DA_ROOT`, `DA_WS` and `DA_DAY` values into every later command **as literal absolute paths**, and run every script as `python3 -B` so no bytecode is written. Never run `py_compile`.

1. **`DA_ROOT` printed** → step 1 (local install) or step 2 (the repo at tag `dead-air-v<DEAD_AIR_VERSION>`) worked. `DA_FROM` says which. If it begins `version mismatch`, that line goes at the top of the report.
2. **Unresolved, and the clone failed** → if the session has the `add_repo` tool, call it for `schmimran/claude-skills` with read access and run the block once more.
3. **Still unresolved → the project cache.** `project_read` the doc `dead-air/cache/v<DEAD_AIR_VERSION>/VERSION`. Use the cache only if its first line is exactly `dead-air <DEAD_AIR_VERSION>`. Download every file it lists to `DA_WS/src/cache/v<DEAD_AIR_VERSION>/<path>` with `project_read` (absolute local paths), save `VERSION` beside them, then verify:
   ```bash
   cd "<DA_WS>/src/cache/v<DEAD_AIR_VERSION>" && sed '1,/^files$/d' VERSION | sha256sum -c --quiet && echo CACHE_OK
   ```
   `CACHE_OK` → `DA_ROOT` is that folder; the code line reads "Code: project cache v<DEAD_AIR_VERSION> (repo unreachable)".
4. **Otherwise stop cleanly:** "Didn't finish: phase 0, code. Local install: <DA_TRIED>. Repo: <the clone error>. Cache: <missing / other version / checksum failed>." **Never retype a script from memory, and never use cached files from another version.**

Below, `${CLAUDE_PLUGIN_ROOT}` means `DA_ROOT`. The calls list starts with "Code: <DA_FROM>" (e.g. "Code: local install 0.3.0", "Code: repo tag dead-air-v0.3.0").

### 0b. Refresh the project cache

Only after step 1 or 2, and only when `DA_FROM` doesn't begin `version mismatch`. `project_read` `dead-air/cache/v<DEAD_AIR_VERSION>/VERSION`. If it's missing, or its first line isn't `dead-air <DEAD_AIR_VERSION>`, stage and upload the mirror:

```bash
V=<DEAD_AIR_VERSION>; C="<DA_WS>/src/cache/v$V"; rm -rf "<DA_WS>/src/cache" && mkdir -p "$C"
cp -r "<DA_ROOT>/scripts" "<DA_ROOT>/references" "<DA_ROOT>/agents" "$C/" && find "$C" -name __pycache__ -prune -exec rm -rf {} +
python3 -B "<DA_ROOT>/scripts/cache_manifest.py" "<DA_ROOT>" "$C/VERSION" --commit <DA_COMMIT> --date <run date>
```

It prints the files it listed. Upload each to `dead-air/cache/v<DEAD_AIR_VERSION>/<path>` with `project_write` and an **absolute** `local_path`, and `VERSION` **last**, so a half-finished upload never looks complete. Then delete cached versions older than the one before this, and only under `dead-air/cache/`. A failed upload isn't a stop: say so in the report. This is the only time the plugin writes to `cache/`.

### 0c. Agents

The agent types `dead-air:dead-air-reporter`, `dead-air:dead-air-coverage` and `dead-air:dead-air-qa` may be missing (in the Nov 5 claude.ai runs they were). Wherever a phase launches one and the type, or the Agent tool, isn't available: read its brief from `${CLAUDE_PLUGIN_ROOT}/agents/<name>.md` and do that work in the main thread under the same rules and output shape. Log which agents ran as agents and which ran inline; the report says so.

### 0d. Shared setup

Do `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §1 in order: config, fonts, design system, today. Each is a clean stop on failure, with the message given there.

Then read:
- `${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md`
- `${CLAUDE_PLUGIN_ROOT}/references/post-schema.md`
- `${CLAUDE_PLUGIN_ROOT}/references/airtable-guide.md`
- `${CLAUDE_PLUGIN_ROOT}/references/report-format.md`

## Phase 1 — Read

Use the Airtable MCP with the IDs from config (field IDs, never names; see the Airtable guide).
- **IG Posts:** all rows, newest first by Post date, with Status, Format, Carousel slot, Flash, ask (the Closer line in Caption) and Stories. Queued rows (Ready, slot ahead) count.
- **Stories:** rows where Status = Flagged, with every field config lists and the record's created time. Read Notes and Absence evidence in full.
- **Stories behind recent posts:** every row a post from the last 30 days carried, whatever its Status. A Covered one may be an Update or a correction (`${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md` §1.1). For each Covered row, find the first domestic Tier-A pickup and its date from the row's recorded checks.

If Airtable can't be read, stop cleanly at phase 1.

## Phase 2 — Choose

1. **Plan.** Write the rows into `<DA_WS>/work/<DA_DAY>/plan-<date>.json` in the shape of `${CLAUDE_PLUGIN_ROOT}/references/post-schema.md` §3, with your `hold` and `override` calls per row and `--format` as `format_override`. Run `python3 -B <DA_ROOT>/scripts/plan_day.py <that file>`. It applies what counts as posted (queued rows included), eligibility, ranking, the four-story fill, the topic spread, Updates, corrections, the next open slot and the blocked asks (`${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md` §0–2). **Take its output as the plan; don't re-decide it.** If it fails, stop cleanly at phase 2 and quote the error.
2. **The day's carousel** = `day`: `format` is `bundle` or `weekly`, `stories` are the four in order (slot 1 is the lead; `slot` says why each is there; a `still_dark` story carries its `count`). Log every `day.skipped` row and its reason, and `day.note` if the topic spread was relaxed.
   - **Flash** (§3), against the newest posted or queued row (`last_flash`).
   - **Reel stories:** the lead. Then, unless `--reels 1`, story 2 as a second Reel candidate (confirmed in phase 4). A Still-dark story is never a Reel candidate.
   - **Slot:** `next_slot`. **Ask:** one not in `blocked_asks`.
3. **No carousel** (`day.format` is null, §F.6): make no carousel. If `day.reel_only` names a lead, its Reel still runs **on its own, as a standalone deep post** (`<date>-deep-<slug>`: five slides plus Reel, built as in `/dead-air-reel`, dashboard mode). The report lists `day.unfilled`. With no lead at all, stop cleanly: "No eligible story: <the reasons>".
4. **Update companions** = `companions` (at most two, oldest pickup first). Each gets an ask different from the day's post's and not in `blocked_asks`. Note `deferred_updates` for the report. Companions ride along with whatever the day makes, the carousel or the standalone deep post; with nothing made, none run.
5. **Corrections** = `corrections`: no post. Their `line`s go at the top of the report. `unresolved` goes under Open calls. `incomplete_rows` (IG Posts rows missing Format or slot) go under Open calls too; never fill them in.

Log the plan in the calls: "Posted and Ready rows count as posted, queued ones included" (once, naming `assumed_posted` and `queued`), the format and its rule, Flash and why, each story, its slot and why, the skips, each companion and each correction.

## Phase 3 — Freshness

For each chosen story, run one WebSearch for US Tier-A pickup since the row's Last checked. A pickup drops the story; log and report it, then re-run phase 2 without it (pass it as `hold`). The check window on the slides stays the dashboard's.

Companions aren't re-searched: their grid and `still_dark` come from the row's recorded checks, dated to the scan's latest pass.

## Phase 4 — Report

For each Reel story, launch `dead-air-reporter` with the Agent tool (`subagent_type: "dead-air:dead-air-reporter"`). Pass it: the full Stories row, the run date, `families: none`, and `DA_ROOT`. Run the two Reel stories in parallel when there are two. Inline fallback per 0c.

- A `stop` result for the **lead** story → stop cleanly; nothing is made.
- A `stop` result, or `supports_second_reel: false`, for the **second** story → drop the second Reel and say why. The first post goes ahead.
- Put every `corrections` entry in the calls ("Corrected: …") and in the report's dashboard corrections. **The sources win.** Never edit the Stories row.

For each Update companion, read the late coverage itself (one search, or fetch, per pickup): what it added or changed, in its own words, for `update.added` and each pickup's `note`. Every line traces to a source in the calls. Don't run the reporter on a companion.

For each story, build the grid, `us`, `meta`, `stat`, `title`, `count`, `confidence` and `days_dark` from the row's **recorded checks**, per `${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md` §4–5. A Still-dark story gets `"still_dark": true` and the `count` from the plan ("Still dark: day <N>."). Apply the breaker rule and log it every time it applies.

## Phase 5 — Build

Write to `<DA_WS>/posts/` `<date>-<format>.json` and `<date>-<format>-calls.json` per `${CLAUDE_PLUGIN_ROOT}/references/post-schema.md`:
- the day's carousel: four `stories`, the `bundle_hook` (`${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md` §6), plus `reel` = the lead story (with the reporter's Flash-length `headline`) and its `deep` block;
- the second Reel, if any, or the standalone Reel on a no-carousel day: a separate DEEP post, `<date>-deep-<slug>.json` + `-calls.json`, five slides (Flash cover, timeline, claims, story slide, Closer);
- each Update companion: `<date>-update-<slug>.json` + `-calls.json`, with `format: "update"`, `flash: false`, its `slug` and its `update` block. Read the original post (`of_post`) from project `dead-air/posts/`, then `dead-air/posts/legacy/`, and copy its story object, as posted, into `update.then_story`; its grid then is `then_grid`. If `of_post` can't be read, stop that companion cleanly (the day's post goes ahead) and report it.
- captions and alt text per `${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md` §6; the `sources` line from the reporter's `sources_line` (or, for a companion, the original post's sources plus the late coverage) plus the dashboard sources;
- `facts` in the calls: format, Flash, the carousel slot, the Reel slot (2–4 hours after the carousel), the ask, and "Code: <DA_FROM>". A companion's carousel slot is the next open slot from 3:00pm ET the same day, after any queued row; its Reel goes 2–4 hours later, or the next morning if that runs past 9:00pm ET (§1.1).

## Phase 6 — Render

```bash
python3 -B <DA_ROOT>/scripts/render.py <DA_WS>/posts/<name>.json <design_dir> <DA_WS>/out/<name> --fonts <DA_WS>/src/fonts/node_modules/@fontsource
```

Run it once per post, each into its own folder. Fix failures per `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §5: cut copy, re-run, at most three passes. Write each cut back into the post JSON, and log any cut that changes meaning. Put the reported Reel length in `reel_length`.

An update's copy-check failure that is about facts, not length (a `ran` square without a pickup, a wrong "N days late", a pickup on or before our post), is never fixed by cutting: correct the facts from the sources, or drop that companion and report why.

## Phase 7 — QA

Launch `dead-air-qa` (`subagent_type: "dead-air:dead-air-qa"`) for each post, companions included, with `out_dir`, `post_json`, `calls_json`, the run date and `DA_ROOT`. Inline fallback per 0c.
- `FIXES` → apply them to the post JSON (phase 5), then go back to phase 6. At most three QA passes.
- After three passes, deliver and list the remaining fixes under Open calls.

## Phase 8 — Deliver

For each review page, in this order:
1. **Review page:** follow `${CLAUDE_PLUGIN_ROOT}/references/review-page.md`. Run `python3 -B <DA_ROOT>/scripts/review_page.py` for the day's post with one `--companion <update.json> <update-calls.json>` per Update companion: they share the day's page. For a deep post, use `--title "Dead Air: <Slug>" --h1 "Dead Air · <The subject>" --name dead-air-<slug>` (its own page; on a no-carousel day the companions go on it). Publish each page as a **new** artifact with the media of every post on it. If the artifact can't be published, follow `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §6 and skip steps 2–3.
2. **Project docs:** for each post, upload the post JSON, the calls JSON and `<name>.md` from `<DA_WS>/posts/` to project `dead-air/posts/` with `project_write` and **absolute** `local_path`s. New files only. The `.md` holds the review link, the IG Posts row ID (added after step 3), the slots, the stories, the dashboard corrections and the Reel sources. Nothing from `work/` or `out/` is uploaded.
3. **IG Posts rows** (skip with `--dry-run`): per `${CLAUDE_PLUGIN_ROOT}/references/airtable-guide.md`, **one row per post**, Status Ready: the day's carousel, each companion (Format `update`, the same review link) and any deep post. Then update each `.md` with its row ID.

**Never write the Stories table. Never email. Never post to Instagram.**

## Phase 9 — Report and clean up

Delete `<DA_WS>/work/`. Then send the report in `${CLAUDE_PLUGIN_ROOT}/references/report-format.md`: the code line and any "version mismatch" line first, then "Correction due" lines, then what was made (with the links, companions included), the stories and why, unfilled slots, what was held back or skipped (deferred Updates included), the dashboard corrections to make, Ready rows more than 7 days past their slot (`stale_ready`), and the open calls. In an unattended run, send it with SendUserMessage if available. **This is always the last step.**
