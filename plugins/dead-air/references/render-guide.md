# Render guide

SPEC §4 and §7. How a command sets up its workspace, finds the scripts, renders, and fixes failures.

---

## 1. Workspace setup (every command, phase 0)

1. **Config.** Read `dead-air/config.md`. In a claude.ai project, use the Projects tool (`project_read`). In Claude Code, read `./dead-air/config.md` in the working directory. If neither works, **stop**: "Can't read dead-air/config.md in the News Blindspots Domestically project." The file holds the Airtable base, table and field IDs, the design-system artifact URL and the playbook URL. **None of these values are ever written into the plugin.**
2. **Workspace.** Create `dead-air/` in the working directory, plus `dead-air/out/<name>/` for each post.
3. **Scripts.** Find `render.py` and `review_page.py` (§2) and copy them into `dead-air/`. Record in the calls where they came from.
4. **Fonts.** Run `npm i @fontsource/big-shoulders-display @fontsource/work-sans @fontsource/ibm-plex-mono` inside `dead-air/`. Google Fonts is blocked in the claude.ai workspace, and these are the same faces. Playwright and ffmpeg are preinstalled there; **never reinstall Playwright**.
5. **Design system.** Artifact `read` of the design-system URL from config with `paths: ["project/tokens.json", "project/components/bundle.css"]`. The folder it saves into is `design_dir` (it must contain `project/tokens.json` and `project/components/bundle.css`). `tokens.css` isn't served; `render.py` builds the CSS variables from `tokens.json`. **Never use `tests/fixtures/design-system/`** for a live run: it is an offline test snapshot. Never edit the design system.
6. **Today.** Take the run date from the current-time tool, in US Eastern time, not from the shell clock.

## 2. Finding the scripts

Try these in order, and stop at the first that has both files:

1. **The plugin's own `scripts/` folder:** `${CLAUDE_PLUGIN_ROOT}/scripts/`. If the variable is empty or unexpanded, and `~/.claude/plugins/installed_plugins.json` exists, find the key under `plugins` that starts with `dead-air@`. Its value is a list of installs; take the last entry's `installPath` and use `<installPath>/scripts/`.
2. **The project docs** `dead-air/render.py` and `dead-air/review_page.py`, via the Projects tool. Imran keeps these in sync with each release until (1) is confirmed to work in claude.ai.

If neither has both files, **stop** and report which places were tried. **Never search the filesystem for the scripts, and never retype a script from memory.**

## 3. Invocation

```
python3 render.py <post.json> <design_dir> <out_dir> [--fonts <dir>] [--only reel|carousel]
                  [--budget hook=5,timeline=12,claims=11,receipt=8,family=8,closer=6]
                  [--open-family 13,5.5]
python3 review_page.py <post.json> <out_dir> <calls.json> [--title "…"] [--h1 "…"] [--name <file stem>]
```

- `--fonts` defaults to the first `node_modules/@fontsource` found next to `render.py`, in the working directory, or in `./dead-air/`.
- `--only carousel` renders just the PNGs. `--only reel` renders just the MP4 and the cover, and refuses an update post (it has no Reel). Copy checks always run in full.
- Each run first deletes the outputs it is about to write (the carousel PNGs, and/or the MP4, cover and `.reel-frames/`), so re-rendering into the same `<out_dir>` never leaves a stale slide or frame behind. Other files in `<out_dir>` (the review HTML, `checks.json`) are left alone.
- The MP4 is cut to exactly the planned length (`-t`), so the length `render.py` prints is the length of the file.
- `--budget` / `--open-family` override the Reel timing ([reel-spec.md](reel-spec.md) §2). Use them only on purpose, and log it.
- `review_page.py` creates `<out_dir>` and prints the path of the HTML file it wrote. Use its `--title`, `--h1` and `--name` flags for standalone deep posts ([review-page.md](review-page.md)). Never post-edit the HTML with `sed`.

**Outputs** in `<out_dir>`: `schmimknews-<date>-<format>-NN.png` (carousel), `-reel.mp4`, `-reel-cover.png`, `checks.json` (`{files, problems}`), and `.reel-frames/` (the per-step frames; QA may use them, but don't publish them).

`render.py` prints `reel: <N> steps, <T> s`. Put `<T>` (rounded) in the calls' `reel_length`.

## 4. Checks

`render.py` exits **1** on any failure and prints each problem.

**Copy checks (run before rendering):**
- story count per format; bundle hook and ask from the fixed sets; `mode` is dashboard or adhoc
- a grid of 11 valid states; Provisional never posts; no `ran` squares except on updates and ad-hoc deep posts
- stat rules; every unchecked outlet named in `us`
- headline 5–14 words with no hedges; bundle titles 6–11 words; 3–5 abroad outlets; topic ≤ 14 characters; `us` ≤ 2 sentences
- every single, bundle or weekly has a `reel`, and the Reel story passes the same checks
- the banned voice list and emoji, across the whole JSON
- caption: line 1 ≤ 125 characters, no hashtag or date in line 1, the method sentence, `#DeadAir #SchmimKnews` + 1–3 subject tags, the same ask as the Closer
- both captions end with `\n\nSources\n` + `sources`; neither is over 2,200 characters
- alt count equals slide count (skipped with `--only reel`)

**Render checks (after layout):** content taller than the canvas; the footer pushed past its line; any `data-maxlines` element over its cap (hook-l 3, hook-m 4, stat 2, lede 4, bundle titles 2, bundle counts 1, `us` 3).

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
- write everything (post JSON, calls JSON, `.md`, PNGs, MP4, review HTML) to `./dead-air-out/<date>/`;
- say exactly what it couldn't do;
- **stop before Airtable.** No IG Posts row is written without a published review page.

Rendering itself needs the design system. If the Artifact tool can't **read** the design-system URL, stop at phase 0 and report it. There is nothing to fall back to: the test snapshot is never used live.
