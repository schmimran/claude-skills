---
name: dead-air-carousel
description: Build or re-cut one Dead Air carousel from chosen Stories records or an existing post JSON — no story selection; optional Reel with --with-reel.
argument-hint: "<record IDs…> [--format single|bundle|weekly|update] | --from <project path to post JSON> [--with-reel] [--post] [--unattended]"
disable-model-invocation: false
---

Build one Dead Air carousel: $ARGUMENTS

This command is **fire and forget** (SPEC §0). It never asks a question the rules answer, fixes its own failures by cutting copy (at most three passes), stops cleanly when it must, logs every judgment in the calls JSON, and **ends with the §11 report**. It has **one** ask case: whether the carousel is for posting (see phase 8).

## Arguments

- `<record IDs…>`: build from these Stories records, **in this order**. The format comes from the count (1 → single, 4 → bundle) unless `--format` says otherwise. Any other count without `--format` → stop cleanly and say why. A bundle or weekly is always four stories (addendum v2.2 §F); three record IDs are refused. A record that meets the Still-dark rule (posted before, not in the last 14 days, still Flagged; `${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md` §2) in slots 2–4 is built as the Still-dark story (at most one); log it.
- `--from <project path>`: re-cut an existing post (e.g. after a correction). Read that post JSON and its calls from project `dead-air/posts/` (or `posts/legacy/`); write a **new version**, `<date>-<format>-v2.json` (or the next free `-vN`). **Never overwrite the original.** The re-cut keeps the original's `date`, sets `recut_of` to the original's project path, and its calls say what changed and why. A three-story bundle posted before 0.3.0 stays three stories with its original hook: `recut_of` is what lets `render.py` accept it.
- `--with-reel`: also build the lead story's Reel, by the same path as `/dead-air-reel`. Without it, render with `--only carousel` and leave out the review page's Reel. A single, bundle or weekly still needs a `reel` block to pass the copy checks; see phase 4.
- `--post`: the carousel is for posting. Write the IG Posts row without asking.
- `--unattended`: scheduled run. Write the row with Status Ready, and report with SendUserMessage. Also assume unattended when started by a scheduled task.

No story selection. The freshness search and QA still run.

`--format update` takes one record ID and builds the four-slide Update (UpdateCover, Then, Now, Closer) with its ~20 s Reel, per `${CLAUDE_PLUGIN_ROOT}/references/post-schema.md` (update block) and `${CLAUDE_PLUGIN_ROOT}/references/reel-spec.md` §5. Find the latest IG Posts row that carried the record for `of_post`, and copy its story object into `then_story`. If the first pickup is dated on or before that post, stop cleanly: it's a correction, not an Update (`${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md` §1.1). An update has its own Reel, so render it without `--only carousel`.

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
DEAD_AIR_VERSION=0.4.0
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

Then read `${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md`, `${CLAUDE_PLUGIN_ROOT}/references/post-schema.md`, `${CLAUDE_PLUGIN_ROOT}/references/airtable-guide.md` and `${CLAUDE_PLUGIN_ROOT}/references/report-format.md`.

## Phase 1 — Read

- **Record IDs:** fetch each Stories row (every field in config; Notes and Absence evidence in full), plus the IG Posts rows (newest first) for the last ask and the last Flash. A record that doesn't exist, or isn't Flagged with Verified or Probable confirmation, → stop cleanly and name it. This command doesn't choose substitutes.
- **`--from`:** read the post JSON and its `-calls.json` from project `dead-air/posts/`, then `dead-air/posts/legacy/`. If either can't be read, stop cleanly.

## Phase 2 — Shape

Set `format`, `flash` (`${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md` §3, counting queued rows), the `bundle_hook` for a bundle or weekly (§6), and an `ask` that no post scheduled within 48 hours of this one uses (queued rows included). Order the stories as given; don't re-rank. For a re-cut, change only what the correction needs, and log each change.

## Phase 3 — Freshness

One WebSearch per story for US Tier-A pickup since the row's Last checked. A pickup means that story can't run as dark: stop cleanly and report it, since the stories were Imran's choice and this command doesn't substitute. (For an UPDATE post, the pickup *is* the story.)

## Phase 4 — Report (the lead story's Reel block)

Singles, bundles and weeklies need `reel` = {lead story, deep block} to pass the copy checks, even when only the carousel is rendered. Launch `dead-air-reporter` (`subagent_type: "dead-air:dead-air-reporter"`) on the lead story, with the row, the run date, `families: none` and `DA_ROOT`. Inline fallback per 0c. For a `--from` re-cut, reuse the existing `reel` block unless the correction touches it.

Record every correction in the calls and the report. **The sources win; never edit the Stories row.**

For a non-Flash **single**, the carousel story's `headline` is the reporter's `headline_short` (a hook-l cover holds about 6 words); `reel.story.headline` keeps the full Flash-length line.

## Phase 5 — Build

Write the post JSON and calls JSON to `<DA_WS>/posts/` per `${CLAUDE_PLUGIN_ROOT}/references/post-schema.md`, building each grid from the row's recorded checks (`${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md` §4–5). Name them `<date>-<format>` (or `-vN` for a re-cut).

## Phase 6 — Render

```bash
python3 -B <DA_ROOT>/scripts/render.py <DA_WS>/posts/<name>.json <design_dir> <DA_WS>/out/<name> --fonts <DA_WS>/src/fonts/node_modules/@fontsource --only carousel   # drop --only with --with-reel
```

Fix failures per `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §5, at most three passes. With `--with-reel`, put the reported Reel length in the calls' `reel_length`; on a carousel-only run, leave `reel_length` out.

## Phase 7 — QA

Launch `dead-air-qa` (`subagent_type: "dead-air:dead-air-qa"`) with `out_dir`, `post_json`, `calls_json`, the run date and `DA_ROOT`; inline fallback per 0c. `FIXES` → back to phase 5. At most three passes; then deliver and list what's left.

## Phase 8 — Deliver

1. **Bundle zip:** build it with `python3 -B <DA_ROOT>/scripts/bundle_zip.py <post.json> <DA_WS>/out/<name> <calls.json> <folder>`, where `<folder>` is its `<date>_<format><NN>` name (a re-cut gets the next NN; the script records `bundle` in the calls JSON itself). Without `--with-reel` the zip holds the slides and `caption_carousel.txt` only. `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §7 has the naming convention, how NN is counted, and what to do when it refuses.
2. **Review page** per `${CLAUDE_PLUGIN_ROOT}/references/review-page.md`, built with `python3 -B <DA_ROOT>/scripts/review_page.py`. Use `--name dead-air-<date>-<format>-vN` for a re-cut. A carousel-only run has no MP4 or cover to attach, so publish the PNGs and the bundle zip only. With no `reel_length` in the calls, `review_page.py` leaves out the Reel panel and the Reel caption.
3. **Project docs:** upload the post JSON, the calls JSON and `<name>.md` from `<DA_WS>/posts/` to project `dead-air/posts/` with `project_write` and absolute `local_path`s. New files only; nothing from `work/` or `out/`. The `.md` records the bundle folder name.
4. **IG Posts row**, only if the carousel is for posting:
   - `--post` or an unattended run → write the row, Status Ready.
   - otherwise, interactive → this is the command's one question: "Is this carousel for posting? (writes an IG Posts row, Status Ready)". Ask it **after** everything else is delivered, so nothing waits on the answer. If there is no answer, write no row, and say so in the report.

**Never write the Stories table. Never email. Never post to Instagram.**

If a review page can't be published, follow `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §6.

## Phase 9 — Report

Delete `<DA_WS>/work/`. Then the report in `${CLAUDE_PLUGIN_ROOT}/references/report-format.md`, starting with the code line. **Always the last step.**
