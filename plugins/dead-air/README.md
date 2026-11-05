# dead-air

**Schmim Knews · Dead Air.** @schmimknews is an Instagram account; Dead Air is its segment. It posts stories with obvious American stakes that ran at three or more major foreign outlets and at **none** of the 11 major US outlets (NYT, WaPo, WSJ, AP, Reuters, CNN, ABC, NBC, CBS, Fox, NPR), not counting whoever broke it.

This plugin turns rows from the **News Blind Spots** Airtable dashboard, or any topic you name, into finished, reviewable posts:

- **Carousels:** 1080×1350 PNG slides, with caption and alt text.
- **Reels:** 40–60 s, 1080×1350 MP4s with no audio track (you add the music). Each one is a reported deep dive on a single story, revealed line by line.
- **A dated review page** per post (a claude.ai artifact), plus the post files in the project and a row in the IG Posts table.
- **A bundle zip** per post, built in your browser from its review page: the slides, the Reel and both captions in one fixed layout (below).

It never posts to Instagram, never sends email, and never writes the Stories table.

## Fire and forget

Run a command once and get finished work back. A run:
- takes the documented default instead of asking, and logs the choice;
- fixes its own copy and layout failures by **cutting copy** (never by shrinking type), up to three passes;
- stops cleanly when it must, naming the step that failed and what you can do;
- always ends with a short report: what was made, why these stories, what was skipped, dashboard corrections, open calls.

The only questions it may ask are whether a `/dead-air-carousel` or `/dead-air-reel` result is for posting, and it asks only after everything else is delivered. Scheduled runs never ask.

## Commands

| Command | What it does |
| --- | --- |
| `/dead-air` | The daily editor. Reads the dashboard and builds the day's **four-story** carousel (a bundle, or the weekly on Sundays): the lead, then new rows, rows passed over on earlier days, and at most one **Still-dark** story resurfaced from long ago. Adds a deep-dive Reel on the lead, and optionally a second one. With fewer than four qualifying stories there is no carousel; the lead's Reel runs as a standalone deep post. A story we posted that a US outlet has since picked up rides along as an **Update companion** (four slides and a ~20 s Reel) on the same review page; one picked up before our post is reported as a correction instead. Publishes the review page(s), writes the project docs, logs one IG Posts row per post. |
| `/dead-air-carousel` | Builds one carousel from Stories records you name, or re-cuts an existing post as a new `-v2` version. No story selection. Add `--with-reel` for its Reel. |
| `/dead-air-reel` | One reported deep-dive Reel (plus its carousel) on a dashboard record, one or more URLs, or a plain-language topic. Runs a real 11-outlet coverage check for ad-hoc topics. |

Agents (launched by the commands, not run directly): `dead-air-reporter` (reports one story from sources), `dead-air-coverage` (checks the 11 outlets for one claim), `dead-air-qa` (looks at every slide and a frame sheet of the Reel).

### Examples

```
/dead-air
/dead-air --dry-run
/dead-air --reels 1 --format weekly
/dead-air-carousel <record ID> <record ID> <record ID> <record ID>
/dead-air-carousel --from dead-air/posts/legacy/bundle-2026-10-22.json
/dead-air-reel the Hannibal directive on October 7 --families open
/dead-air-reel https://example.com/some-foreign-report --post
```

## Setup

1. **Install.** In claude.ai: Customize → Plugins → Add marketplace → `schmimran/claude-skills`, then install `dead-air`. In Claude Code: `/plugin marketplace add https://github.com/schmimran/claude-skills`.
2. **Project.** Run the commands in the "News Blindspots Domestically" claude.ai project. It needs the Projects tool, the Artifact tool, the Airtable MCP, WebSearch/WebFetch and the Linux workspace (Playwright and ffmpeg are preinstalled there).
3. **Config doc.** The project must have a doc at `dead-air/settings/config.md`. **None of its values belong in this repo.** It holds:
   - the News Blind Spots base ID, and the Stories and IG Posts table IDs;
   - a field-ID map for every field the plugin reads or writes (see [references/airtable-guide.md](references/airtable-guide.md) for the field names);
   - the "Schmim Knews" design-system artifact URL;
   - the "Schmim Knews — Instagram Playbook" doc URL;
   - the handle;
   - the Airtable quirks: write by field ID, never by name; leave the Slides attachment field empty; put the Reel slot in Notes.

   In Claude Code, the commands look for the same file at `./dead-air/settings/config.md` in the working directory. Keep that copy out of any git repo.

Without the Projects or Artifact tools (e.g. in Claude Code), a run keeps everything in its workspace (`./dead-air/posts/` and `./dead-air/out/`), says what it couldn't do, and stops before Airtable.

### Where the code comes from

claude.ai chats load this plugin's commands and agents, but not its `scripts/` or `references/`. So every command first finds `DA_ROOT`, the folder holding them, and stops at the first that works:

1. **A local install** whose `plugin.json` version equals the command's `DEAD_AIR_VERSION`: `$CLAUDE_PLUGIN_ROOT`, `installed_plugins.json`, or a synced `~/.claude/plugins/synced/*/dead-air*` copy. Never the first match blindly, and never a hard-coded session path.
2. **This repo at tag `dead-air-v<version>`**, a shallow sparse clone into `./dead-air/src/`. With no tag it uses `main` and says "version mismatch" at the top of the report.
3. **The project cache** `dead-air/cache/v<version>/`, only if its `VERSION` doc matches exactly and every checksum passes.
4. Otherwise it stops and says which step failed. It never retypes a script from memory.

The report always says where the code came from. If an agent type isn't available, the command reads its brief from `DA_ROOT/agents/` and does the work itself, and says so.

### The project layout

| Folder | Owner | Holds | The plugin… |
| --- | --- | --- | --- |
| `dead-air/settings/` | you | `config.md` | reads it first; never writes it |
| `dead-air/posts/` | plugin | every post's JSON, calls JSON and `.md`; pre-v2 posts in `posts/legacy/` | reads it; adds new files only |
| `dead-air/cache/v<version>/` | plugin | a mirror of `scripts/`, `references/`, `agents/` + `VERSION` | reads it only as a fallback; refreshes it, keeping two versions |
| `dead-air/dev/` | you / Claude Code | specs, addenda, prompts, comparison runs | never reads or writes it |

Nothing else lives directly under `dead-air/`. In the session's own workspace, `./dead-air/` holds `src/` (the fetched plugin, fonts, staged cache), `work/<date>/` (scratch, deleted at the end), `out/<post>/` (media, never uploaded to the project) and `posts/` (uploaded to `dead-air/posts/`).

### The bundle (0.4.0)

Every post, Update companions included, gets a **Download bundle zip** button on its review page (one tap on a phone). It saves `<folder>.zip` holding exactly this, and `scripts/bundle_stage.py` refuses to stage anything that doesn't match:

```
2026-11-05_bundle01/
  slide_01.png … slide_NN.png   numbered from 01 with no gaps, in posting order
  video.mp4                     only when a Reel was rendered
  caption_carousel.txt          the carousel caption, plain UTF-8
  caption_video.txt             the Reel caption (only with a Reel)
```

The folder is `<date>_<format><NN>`: format is `bundle`, `weekly`, `single`, `deep` or `update`, and `NN` counts that day's posts of that format (`bundle01`, `bundle02`, `update01`, `update02`), so several runs on one day never mix. The full convention and the counter rule are in [references/render-guide.md](references/render-guide.md) §7.

**How it reaches you.** A published artifact can't serve a `.zip`, and a claude.ai viewer blocks downloads a page starts itself. So the run stages the files under their convention names and publishes them beside the review page; the page zips them in your browser and saves the zip through the viewer's Save prompt (the `downloads` capability). The same prompt now saves the video, cover and slides. A Google Drive route was tried first and dropped: the Drive connector sees only files it created and can't carry binaries at a usable cost.

## How it decides

The rules live in [references/](references/):

| File | Covers |
| --- | --- |
| [editorial-rules.md](references/editorial-rules.md) | format choice, eligibility and ranking, Flash, the grid, the count line, captions and Sources, Reel content, voice |
| [post-schema.md](references/post-schema.md) | post JSON, story object, deep block, update block, calls JSON, plan input |
| [reel-spec.md](references/reel-spec.md) | Reel structure and timing, ad-hoc mode, families slide, Update Reels |
| [render-guide.md](references/render-guide.md) | setup, script lookup, renderer flags and checks, the fix loop, the bundle-zip naming convention |
| [review-page.md](references/review-page.md) | the review page, its downloads and the bundle zip |
| [airtable-guide.md](references/airtable-guide.md) | IG Posts fields (by name) and quirks |
| [coverage-guide.md](references/coverage-guide.md) | which outlets the search tools can and can't reach |
| [report-format.md](references/report-format.md) | the end-of-run report |
| [carousel-spec.md](references/carousel-spec.md) | the historical v3 rules from the hand-built session |

## Scripts

```
python3 -B scripts/render.py <post.json> <design_dir> <out_dir> [--fonts <dir>] [--only reel|carousel]
                          [--budget hook=5,timeline=12,...] [--open-family 13,5.5]
python3 -B scripts/review_page.py <post.json> <out_dir> <calls.json> [--companion <update.json> <update-calls.json>]...
                               [--title …] [--h1 …] [--name …]
python3 -B scripts/plan_day.py <plan-input.json>
python3 -B scripts/bundle_stage.py <post.json> <out_dir> <calls.json> <folder>   # or: --check <dir>
python3 -B scripts/cache_manifest.py <DA_ROOT> <out VERSION> [--commit <sha>] [--date YYYY-MM-DD]
```

Always `python3 -B`: no `__pycache__/` in the repo or the project.

`render.py` runs the copy checks, renders the carousel and the Reel against the live design system (read from its artifact on every run; never copied into the plugin), and exits 1 on any failure. `review_page.py` builds the day's review page, with any Update companions on it, and a download link for every video, cover and slide plus a "Download all slides" zip. `plan_day.py` turns the IG Posts and Stories rows into the day's plan: what counts as posted (queued rows included), the four stories and why each is there, the next open slot, the asks it can't use, Update companions and corrections. `bundle_stage.py` stages a post's hand-off folder and enforces its naming convention (above). `cache_manifest.py` writes the project cache's `VERSION` doc. See [references/render-guide.md](references/render-guide.md).

## Tests

The fixture tests cover SPEC §13 tests 1–7a, the `mode: adhoc` rule, spec addendum v2.1 §F (Update companions, corrections, the count-line fix, Update copy checks, Ready-as-posted) and addendum v2.2 §E: four-story bundles with each hook, three-story bundles refused, the Still-dark story, the fill order and topic spread, queued slots and asks, the review page's download links, the version check, the setup block (synced copies, repo tag, `main` fallback), the cache checksums, no writes to `settings/` or `dev/`, no hard-coded session paths and `python3 -B` everywhere. The 0.4.0 tests stage the bundle from real renders (bundle, carousel-only, Update): exact names, bytes and caption text, `--check`, every refusal (bad folder name, wrong date or format, missing slide or video, empty caption, stray or mis-numbered files, stale folder and fields removed), the review page's markup and hostile `bundle` values, and a real Chromium run of the page's own JavaScript with a stubbed `downloads` capability: the zip it builds, the saves it makes, a declined save and the no-capability fallback (needs Playwright, and network for JSZip from cdnjs). They render two approved Oct 31 posts (the bundle, and the Hannibal deep dive whose Reel opens on a families slide) and the Nov 5 gas-transit Update against an **offline snapshot** of the design system in `tests/fixtures/design-system/`. Live runs never use that snapshot.

```bash
python3 -m venv /tmp/da-venv && /tmp/da-venv/bin/pip install playwright && /tmp/da-venv/bin/python -m playwright install chromium
DEAD_AIR_PYTHON=/tmp/da-venv/bin/python plugins/dead-air/tests/run-fixture.sh
```

You need ffmpeg/ffprobe, npm and git. The fonts install into the gitignored `tests/.fonts/`.

### Manual check: test 8 (needs claude.ai tools)

In the claude.ai project, run:

```
/dead-air-reel <a URL to a foreign Tier-A report with no dashboard row>
```

Pass if:
1. the post JSON in `dead-air/posts/<date>-deep-<slug>.json` has `"mode": "adhoc"` and `"record_id": null`;
2. its "Who ran it" slide's grid matches the `dead-air-coverage` verdicts recorded in the calls: every `unchecked` outlet is named in `us` and `meta`, and no outlet is marked silent without a working, outlet-scoped search behind it;
3. `confidence` is `Probable` unless all 11 were checked, and `days_dark` is counted from the first foreign report;
4. a review page was published, and no IG Posts row was written (no `--post`, and you didn't say it was for posting).

### Manual checks for 0.3.0 (addendum v2.2 §E.2–3, need claude.ai)

1. In a chat with no local install, `/dead-air --dry-run`: the report says "Code: repo tag dead-air-v0.3.0", the fixtures-shaped posts render, and `dead-air/cache/v0.3.0/VERSION` appears in the project with a checksum for every file.
2. With GitHub unreachable and that cache in place: the report says "Code: project cache v0.3.0 (repo unreachable)". With a cache of another version: the run stops at phase 0 and says why.

### Manual check for 0.4.0 (needs claude.ai and a phone)

Run `/dead-air --dry-run`. Pass if: the review page has a "Download bundle zip" button under each carousel strip (and under the Update companion's, if any); tapping it on a phone shows the Save prompt for `<date>_<format><NN>.zip`; unzipped, it holds exactly `slide_01.png`…, `video.mp4`, `caption_carousel.txt` and `caption_video.txt` under one folder named `<date>_<format><NN>`; "Download video" shows the same prompt. Run it twice in one day and confirm the second post's folder ends `02`.

## Releasing

1. Bump `version` in `.claude-plugin/plugin.json` **and** `DEAD_AIR_VERSION` in all three command files (and `marketplace.json` and the root README). A fixture test fails if they differ.
2. After merge, tag `dead-air-v<version>` on the merge commit and push the tag.
3. Nothing to copy into the project. The next run refreshes the cache itself.

## Moving the project to the 0.3.0 layout (one time, by hand)

0.3.0 reads `dead-air/settings/config.md`, and falls back to `dead-air/config.md` with a warning in the report until this is done. The plugin moves nothing itself.

| From | To |
| --- | --- |
| `dead-air/config.md` | `dead-air/settings/config.md` |
| `dead-air/render.py`, `review_page.py`, `plan_day.py`, `dead-air/plugin/**` | delete (0.3.0's first run rebuilds the cache) |
| `dead-air/bundle-*.json`, `dead-air/deep-*.json` | `dead-air/posts/legacy/` |
| `dead-air/plugin-spec.md`, `plugin-spec-addendum-*.md`, `claude-code-prompt-*.md` | `dead-air/dev/` |
| `dead-air/compare/**` | `dead-air/dev/compare/` |

Also by hand, with your OK: set Format and Carousel slot on the Oct 10, 16 and 22 IG Posts rows, and add a row (Posted or Skipped) for the Oct 18 bundle. Runs list rows missing Format or slot under Open calls but never write old rows.
