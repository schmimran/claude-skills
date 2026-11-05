# Render guide

SPEC §4 and §7 as replaced by addendum v2.2 §A, §B and §I. How a command finds its code, sets up its workspace, renders, and fixes failures.

---

## 1. Setup (every command, phase 0)

Before this, the command's phase 0a has found `DA_ROOT` (addendum v2.2 §A; §2 below) and created the workspace. Then, in order:

1. **Config.** `project_read` the doc `dead-air/settings/config.md`. During the switch to the v2.2 layout, if it's missing, read `dead-air/config.md` instead and put "Config read from the old path dead-air/config.md; move it to dead-air/settings/config.md" at the top of the report. In Claude Code, read `./dead-air/settings/config.md` (then `./dead-air/config.md`) in the working directory. If none works, **stop**: "Can't read dead-air/settings/config.md in the News Blindspots Domestically project." The file holds the Airtable base, table and field IDs, the design-system artifact URL, the playbook URL and the handle. **None of these values are ever written into the plugin**, and the plugin never writes to `settings/`.
2. **Fonts.** `npm i --prefix <DA_WS>/src/fonts @fontsource/big-shoulders-display @fontsource/work-sans @fontsource/ibm-plex-mono`, then pass `--fonts <DA_WS>/src/fonts/node_modules/@fontsource` to every `render.py` run. Google Fonts is blocked in the claude.ai workspace, and these are the same faces. Playwright and ffmpeg are preinstalled there; **never reinstall Playwright**.
3. **Design system.** Artifact `read` of the design-system URL from config with `paths: ["project/tokens.json", "project/components/bundle.css"]`. The folder it saves into is `design_dir` (it must contain `project/tokens.json` and `project/components/bundle.css`). `tokens.css` isn't served; `render.py` builds the CSS variables from `tokens.json`. **Never use `tests/fixtures/design-system/`** for a live run: it is an offline test snapshot. Never edit the design system.
4. **Today.** Take the run date from the current-time tool, in US Eastern time, not from the shell clock. (`DA_DAY` only names the scratch folder.)

### The workspace (addendum v2.2 §I)

All under `./dead-air/` in the session's working directory (`DA_WS`, an absolute path), created by phase 0a:

| Folder | Holds | Uploaded? |
| --- | --- | --- |
| `src/` | the fetched plugin (`src/repo/`), the fonts (`src/fonts/`), the staged cache (`src/cache/v<version>/`) | only `src/cache/v<version>/`, to project `dead-air/cache/v<version>/` |
| `work/<date>/` | scratch: the plan input, row dumps, leads, the clone log | never; deleted at the end of the run |
| `out/<post>/` | rendered PNGs, MP4s, `checks.json`, the bundle zip (§7), review pages | never to the project; the media and the zip go on the review-page artifact |
| `posts/` | the post JSON, calls JSON and `.md` being written | yes, to project `dead-air/posts/`, at delivery |

**No bytecode, no scratch in the repo or the project.** Every script runs as `python3 -B`, setup exports `PYTHONDONTWRITEBYTECODE=1`, and nothing runs `py_compile` (on Nov 5 a syntax check left `__pycache__/` in a claude-skills clone). Every `project_write` uses an **absolute** `local_path` (a relative one failed on Nov 5).

### The project (addendum v2.2 §B)

Four top-level folders under `dead-air/`, each with one owner. Nothing else lives directly under `dead-air/`.

| Folder | Owner | Holds | Read at run time? | Written at run time? |
| --- | --- | --- | --- | --- |
| `dead-air/settings/` | **Imran** | `config.md` | yes, first thing | **never** |
| `dead-air/posts/` | **plugin** | `<name>.json`, `-calls.json`, `.md`; pre-v2 posts in `posts/legacy/` with their original names | yes (no-repeats, the Updates' Then slide) | new files only; never edits an old post |
| `dead-air/cache/v<version>/` | **plugin** | a mirror of `scripts/`, `references/`, `agents/` + `VERSION` | only when §2 steps 1–2 fail | on refresh; keeps the current and the previous version, deletes older ones |
| `dead-air/dev/` | **Imran / Claude Code** | specs, addenda, prompts, comparison runs, notes | **never** | **never** |

Never write to `settings/` or `dev/`. Never delete anything outside `cache/`. Never read code or rules from anywhere but `DA_ROOT`.

## 2. Finding the code and rules (`DA_ROOT`)

Every command's phase 0a runs the same setup block (a test checks the three copies are identical) and stops at the first step that works:

1. **Local install.** `$CLAUDE_PLUGIN_ROOT`, then every `installPath` for `dead-air@…` in `~/.claude/plugins/installed_plugins.json`, then every `~/.claude/plugins/synced/*/dead-air*` folder. A candidate counts only if it has `scripts/render.py` **and** its `.claude-plugin/plugin.json` version equals the command's `DEAD_AIR_VERSION`. Sessions can hold several synced copies side by side (Nov 5: `dead-air` at 0.1.0 and `dead-air~g2` at 0.2.0), so the first match is never taken blindly. **No command names a session-specific path**: on Nov 5 a hard-coded `synced/<uuid>/` path worked in one session and stopped the next two.
2. **The repo, pinned to this release.** A shallow, sparse clone of `schmimran/claude-skills` at tag `dead-air-v<DEAD_AIR_VERSION>` into `DA_WS/src/repo`, then the same version check. If the clone fails and the session has `add_repo`, call it for the repo with read access and retry once. If the tag doesn't exist, the block uses `main`, records the commit SHA, and the report opens with "version mismatch: ran main at <sha>".
3. **The project cache**, `dead-air/cache/v<DEAD_AIR_VERSION>/`, only if its `VERSION` doc's first line is exactly `dead-air <DEAD_AIR_VERSION>`. Each file is downloaded with `project_read` and checked against `VERSION` with `sha256sum -c` (no plugin code needed).
4. **Stop**, naming which of 1–3 failed and why. **Never retype a script from memory, and never use cached files from another version.**

After a successful step 1 or 2 (not a `main` fallback), the command refreshes the cache if it's missing or another version: it stages `scripts/`, `references/` and `agents/` in `DA_WS/src/cache/v<version>/`, writes `VERSION` with `cache_manifest.py`, and uploads `VERSION` last.

The report always says where the code came from: "Code: local install 0.3.0", "Code: repo tag dead-air-v0.3.0", or "Code: project cache v0.3.0 (repo unreachable)".

**Agents.** If an agent type (`dead-air:dead-air-reporter`, `-coverage`, `-qa`) isn't available, the command reads its brief from `DA_ROOT/agents/<name>.md` and does that work in the main thread, under the same rules and output shape. The report says which ran as agents and which ran inline.

## 3. Invocation

Always `python3 -B`, with the scripts' absolute paths under `DA_ROOT/scripts/`:

```
python3 -B render.py <post.json> <design_dir> <out_dir> [--fonts <dir>] [--only reel|carousel]
                  [--budget hook=5,timeline=12,claims=11,receipt=8,family=8,closer=6,
                            update_then=6,update_square=1.5,update_hold=4,update_closer=4]
                  [--open-family 13,5.5]
python3 -B review_page.py <post.json> <out_dir> <calls.json> [--companion <update.json> <update-calls.json>]...
                       [--title "…"] [--h1 "…"] [--name <file stem>]
python3 -B plan_day.py <plan-input.json>
python3 -B bundle_zip.py <post.json> <out_dir> <calls.json>        # §7; also: bundle_zip.py --check <file.zip>
python3 -B cache_manifest.py <DA_ROOT> <out VERSION> [--commit <sha>] [--date YYYY-MM-DD]
```

- `--fonts`: always pass `<DA_WS>/src/fonts/node_modules/@fontsource`. (Without it, `render.py` tries `node_modules/@fontsource` next to itself, in the working directory, then in `./dead-air/`.)
- `--only carousel` renders just the PNGs. `--only reel` renders just the MP4 and the cover. Copy checks always run in full.
- Each run first deletes the outputs it is about to write (the carousel PNGs, and/or the MP4, cover and `.reel-frames/`), so re-rendering into the same `<out_dir>` never leaves a stale slide or frame behind. Other files in `<out_dir>` (the review HTML, `checks.json`) are left alone.
- The MP4 is cut to exactly the planned length (`-t`), so the length `render.py` prints is the length of the file.
- `--budget` / `--open-family` override the Reel timing ([reel-spec.md](reel-spec.md) §2). Use them only on purpose, and log it.
- `review_page.py` creates `<out_dir>` and prints the path of the HTML file it wrote. `--companion` adds an Update companion's section to the day's page (repeat it for a second; at most two). It refuses a companion with a different date or the day's ask. Use its `--title`, `--h1` and `--name` flags for standalone deep posts ([review-page.md](review-page.md)). Never post-edit the HTML with `sed`.

- `plan_day.py` prints the day's plan as JSON ([post-schema.md](post-schema.md) §3). It reads no files but its input and writes nothing.
- `bundle_zip.py` writes `<out_dir>/<bundle>.zip` for one post (§7) and prints its path. It refuses, writes nothing and exits 1 if the naming convention isn't met. `--check <file.zip>` checks an existing zip against the convention.
- `cache_manifest.py` writes the cache's `VERSION` doc for `DA_ROOT` (§2) and prints the files it listed.

**Outputs** in `<out_dir>`: `schmimknews-<date>-<format>-NN.png` (carousel; an update adds its slug, `schmimknews-<date>-update-<slug>-NN.png`), `-reel.mp4`, `-reel-cover.png`, `checks.json` (`{files, problems}`), and `.reel-frames/` (the per-step frames; QA may use them, but don't publish them).

`render.py` prints `reel: <N> steps, <T> s`. Put `<T>` (rounded) in the calls' `reel_length`.

## 4. Checks

`render.py` exits **1** on any failure and prints each problem.

**Copy checks (run before rendering):**
- story count per format (a bundle or weekly is 4; 3 only with `recut_of` and a legacy hook); bundle hook from the fixed set, and "4 abroad. 0 here." only with no `ran` square; at most one `still_dark` story, never story 1, with `count` "Still dark: day <days_dark>."; ask from the fixed set on every format; `mode` is dashboard or adhoc
- a grid of 11 valid states; Provisional never posts; no `ran` squares except on updates and ad-hoc deep posts
- stat rules (no "we could check", "N of the M" or ": nothing"; "None of the 11 …" is fine); every unchecked outlet named in `us`
- headline 5–14 words with no hedges; bundle titles 6–11 words; 3–5 abroad outlets; topic ≤ 14 characters; `us` ≤ 2 sentences
- every single, bundle or weekly has a `reel`, and the Reel story passes the same checks
- the banned voice list and emoji, across the whole JSON
- caption: line 1 ≤ 125 characters, no hashtag or date in line 1, the method sentence, `#DeadAir #SchmimKnews` + 1–3 subject tags, the same ask as the Closer
- both captions end with `\n\nSources\n` + `sources`; neither is over 2,200 characters
- alt count equals slide count (skipped with `--only reel`)
- **update posts:** the `update` block is complete; `slug` is set; not Flash; `then_grid` has no `ran`; every `ran` square has a dated pickup and every pickup a `ran` square; pickups one per outlet, oldest first, none after the run date; no pickup on or before `posted` (that's a correction); `then_story` has every story key; the `still_dark` number equals the silent count; the headline reads "Update: <outlet> ran it <N> days late." with N = pickup date minus the `dateline` date (or `update.breaker_date`); `then_story` passes the story checks

**Render checks (after layout):** content taller than the canvas; the footer pushed past its line; any `data-maxlines` element over its cap (hook-l 3, hook-m 4, stat 2, lede 4, bundle hook 1 (3 on a legacy re-cut), bundle titles 2, bundle counts 1, `us` 3, Update topic line 2, Update `added` and still-dark lines 2 each).

**Text hygiene (automatic):** date ranges ("Oct 12–26") and "Mon D" pairs never break across lines.

## 5. Fixing failures (SPEC §0.2)

- **A copy-check or render-check failure is fixed by cutting copy** and re-running. **Never shrink type, never edit the CSS, never loosen a check, never edit `render.py`.**
- Cut in this order: drop a clause, swap a long word for a shorter true one, shorten a quote to a shorter exact quote. The cut copy must still be true to the source. A cut that changes meaning is a new judgment and goes in the calls.
- A non-Flash single cover holds a headline of about 6 words; a Flash cover holds about 11–12 ([post-schema.md](post-schema.md)).
- At most **three passes**. After the third, deliver what passes and list what didn't in the report.
  - A **render-check** failure still writes every PNG and the MP4 (the script exits 1 only at the end), so the post can be delivered with its problems listed.
  - A **copy-check** failure renders nothing. If one survives three passes, that post can't be delivered: stop it cleanly ([report-format.md](report-format.md)).
- A QA finding goes back to the build step (edit the post JSON), then render again. That loop also gets three passes.

## 6. When the tools aren't there (SPEC §2)

In Claude Code the Projects tool and the Artifact tool may be missing. If a command can't reach the project or publish an artifact:
- keep everything (post JSON, calls JSON, `.md`, PNGs, MP4, review HTML) in the workspace: `DA_WS/posts/` and `DA_WS/out/<post>/`;
- say exactly what it couldn't do;
- **stop before Airtable.** No IG Posts row is written without a published review page.

Rendering itself needs the design system. If the Artifact tool can't **read** the design-system URL, stop at phase 0 and report it. There is nothing to fall back to: the test snapshot is never used live.

## 7. The bundle zip (0.4.0)

Every post gets one zip of its raw media and captions, in a fixed layout, linked from its review page. This is the hand-off to whoever posts it. (A Google Drive route was tried and dropped: the Drive connector sees only files it created and can't carry binaries at a usable cost.)

**The convention. It is documented here once, and `bundle_zip.py` enforces it: a post that doesn't match gets no zip.**

| Part | Rule |
| --- | --- |
| Zip file | `<folder>.zip`, written into the post's render folder `DA_WS/out/<name>/` |
| Root folder | `<folder>` = `<YYYY-MM-DD>_<format><NN>`: the post's date, its format (`bundle` `weekly` `single` `deep` `update`) and a two-digit counter, no separators between format and counter. `2026-11-05_bundle01`, `2026-11-05_deep01`, `2026-11-05_update02`. It is the zip's only top-level entry. |
| Slides | `slide_01.png` … `slide_NN.png`: two digits, contiguous from 01, in posting order, one per `alt` string. Copied byte for byte from `schmimknews-<date>-<format>-NN.png`. |
| Video | `video.mp4`, only when the calls JSON has `reel_length`. Copied byte for byte from `…-reel.mp4`. |
| Captions | `caption_carousel.txt` always; `caption_video.txt` only with a Reel. The post's `caption` and `reel_caption`, UTF-8, plain text, with one trailing newline. |
| Nothing else | No cover PNG, no `checks.json`, no `.reel-frames/`, no subfolders. |

Names are lowercase, use `_` only between the date and the format and inside `slide_`/`video`/`caption_` names, and never change from post to post.

**The counter `NN`** is 01 or higher, and separate for each date and format. Count the post JSONs (not `-calls.json`, not `.md`) in project `dead-air/posts/` and `dead-air/posts/legacy/` whose names contain both the post's date and its format. `NN` = that count + 1 + the number of posts of the same date and format already zipped earlier in this run. So a second bundle on one day is `bundle02`, a `-v2` re-cut gets the next number, and two Update companions on one day are `update01` and `update02`. Without the Projects tool, `NN` is the number of matching post JSONs in `DA_WS/posts/`, this post's own included. Never reuse a number.

**Running it.** After QA, set the calls JSON's `bundle` to the folder name, then `python3 -B <DA_ROOT>/scripts/bundle_zip.py <post.json> <DA_WS>/out/<name> <calls.json>`. It checks the folder name against the post's date and format, the slide count against `alt`, that every source file and caption exists, then builds the zip, reads it back (names, CRC, every media file byte for byte) and only then keeps it. A refusal prints each problem: fix the cause (never the check) and run again. If it can't be fixed, leave `bundle` out of the calls, so the review page has no zip button, and list it under Open calls. Never hand-build a zip.

The zip is published with the review page ([review-page.md](review-page.md)). It is not uploaded to the project, and it is not written to Airtable.
