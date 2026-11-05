---
name: dead-air-reel
description: Build one reported Dead Air deep-dive Reel (plus its carousel) on any topic — a dashboard record, URLs, or a plain-language topic — with an honest 11-outlet coverage check.
argument-hint: "<topic | record ID | URL…> [--families open|close] [--post] [--unattended]"
disable-model-invocation: false
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

Then read `${CLAUDE_PLUGIN_ROOT}/references/reel-spec.md`, `${CLAUDE_PLUGIN_ROOT}/references/editorial-rules.md`, `${CLAUDE_PLUGIN_ROOT}/references/post-schema.md`, `${CLAUDE_PLUGIN_ROOT}/references/airtable-guide.md`, `${CLAUDE_PLUGIN_ROOT}/references/coverage-guide.md` and `${CLAUDE_PLUGIN_ROOT}/references/report-format.md`.

## Phase 1 — Frame

Resolve the topic:
- **Record ID or title fragment:** fetch the Stories row. If several rows match a fragment, take the best match (exact title, then Flagged, then most recent) and log the choice.
- **URL or topic:** no row. `record_id: null`, `mode: "adhoc"`.

Restate the topic as one sentence and name the angle the record likely supports. Write both into the calls as the first entry, "Angle." If the brief overclaims, the call reads "Brief said X; the record supports Y; the Reel uses Y." **Don't ask; proceed.**

Pick the slug for the file names: 1–2 lowercase words (e.g. `hannibal`). The post is `<date>-deep-<slug>`.

## Phase 2 — Report

Launch `dead-air-reporter` (`subagent_type: "dead-air:dead-air-reporter"`) with: the row or the topic and URLs, the run date, `families: <none|open|close>`, and `DA_ROOT`. Inline fallback per 0c.

- A `stop` result → stop cleanly. Name what was missing and what Imran could supply (e.g. a reachable copy of the source).
- `family: null` when one was asked for → build without it, and say why in the report. Never substitute a weaker quote.
- Every correction goes in the calls and the report. **The sources win.**

## Phase 3 — Coverage

- **Dashboard mode:** build the grid, `us`, `meta`, `stat`, `confidence` and `days_dark` from the row's recorded checks, then run the one freshness WebSearch for US Tier-A pickup since Last checked. If there's a pickup, log it and go on in ad-hoc mode (`mode: "adhoc"`, the pickup as `ran`), since the Reel was asked for.
- **Ad-hoc mode:** launch `dead-air-coverage` (`subagent_type: "dead-air:dead-air-coverage"`) with the claim, the reporter's `first_foreign_report`, the window "since <first report date>", the run date and `DA_ROOT` (inline fallback per 0c). Build the story slide from its verdicts per `${CLAUDE_PLUGIN_ROOT}/references/reel-spec.md` §3: `ran` squares allowed, every `unchecked` named in `us` and `meta`, `confidence` from the agent, `days_dark` from the first foreign report to the run date (**always set**). Apply the breaker rule to `broke_candidate` and log it. Put the agent's `calls` in the calls, and its `new_quirks` in the report.

## Phase 4 — Build

Write `<DA_WS>/posts/<date>-deep-<slug>.json` and `-calls.json` per `${CLAUDE_PLUGIN_ROOT}/references/post-schema.md`: `format: "deep"`, `flash: true`, the `ask` (one no post scheduled within 48 hours of this one uses, queued rows included; after a families slide, not "Send this to someone who reads the Times."), the families block, the captions with the Sources line, and alt text for every carousel slide.

## Phase 5 — Render

```bash
python3 -B <DA_ROOT>/scripts/render.py <DA_WS>/posts/<date>-deep-<slug>.json <design_dir> <DA_WS>/out/<date>-deep-<slug> --fonts <DA_WS>/src/fonts/node_modules/@fontsource
```

Render the full post: the deep carousel (5 slides, or 6 with families) and the Reel. Fix failures per `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §5, at most three passes.

## Phase 6 — QA

Launch `dead-air-qa` (`subagent_type: "dead-air:dead-air-qa"`) with `out_dir`, `post_json`, `calls_json`, the run date and `DA_ROOT`; inline fallback per 0c. `FIXES` → back to phase 4. At most three passes; then deliver and list what's left.

## Phase 7 — Deliver

1. **Bundle zip:** build it with `python3 -B <DA_ROOT>/scripts/bundle_zip.py <post.json> <DA_WS>/out/<date>-deep-<slug> <calls.json> <date>_deep<NN>` (the script records `bundle` in the calls JSON itself). `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §7 has the naming convention, how NN is counted, and what to do when it refuses.
2. **Review page** per `${CLAUDE_PLUGIN_ROOT}/references/review-page.md`:
   `python3 -B <DA_ROOT>/scripts/review_page.py <post.json> <DA_WS>/out/<name> <calls.json> --title "Dead Air: <Slug>" --h1 "Dead Air · <The subject>" --name dead-air-<slug>`
   Publish it as a new artifact with its media and its bundle zip. If it can't be published, follow `${CLAUDE_PLUGIN_ROOT}/references/render-guide.md` §6.
3. **Project docs:** upload the post JSON, the calls JSON and `<date>-deep-<slug>.md` from `<DA_WS>/posts/` to project `dead-air/posts/` with `project_write` and absolute `local_path`s. New files only; nothing from `work/` or `out/`. The `.md` records the bundle folder name.

## Phase 8 — IG Posts row

Per `${CLAUDE_PLUGIN_ROOT}/references/airtable-guide.md`, Format `deep`, Status Ready. Write it only:
- with `--post`, or in an unattended run: write it;
- otherwise, interactive → ask once, **after** everything is delivered: "Is this Reel for posting? (writes an IG Posts row, Status Ready)". With no answer, write no row, and say so in the report.

**Never write the Stories table. Never email. Never post to Instagram.**

## Phase 9 — Report

Delete `<DA_WS>/work/`. Then the report in `${CLAUDE_PLUGIN_ROOT}/references/report-format.md`: the code line and which agents ran inline, what was made, with the link and the Reel's length; the angle and any claim held back; the coverage findings (which outlets ran it, which couldn't be checked); corrections; open calls. **Always the last step.**
