# dead-air

**Schmim Knews · Dead Air.** @schmimknews is an Instagram account; Dead Air is its segment. It posts stories with obvious American stakes that ran at three or more major foreign outlets and at **none** of the 11 major US outlets (NYT, WaPo, WSJ, AP, Reuters, CNN, ABC, NBC, CBS, Fox, NPR), not counting whoever broke it.

This plugin turns rows from the **News Blind Spots** Airtable dashboard, or any topic you name, into finished, reviewable posts:

- **Carousels:** 1080×1350 PNG slides, with caption and alt text.
- **Reels:** 40–60 s, 1080×1350 MP4s with no audio track (you add the music). Each one is a reported deep dive on a single story, revealed line by line.
- **A dated review page** per post (a claude.ai artifact), plus the post files in the project and a row in the IG Posts table.

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
| `/dead-air` | The daily editor. Reads the dashboard, picks the day's format (single, bundle, weekly) and stories, builds the carousel plus a deep-dive Reel on the lead story, and optionally a second deep-dive Reel. A story we posted that a US outlet has since picked up rides along as an **Update companion** (four slides and a ~20 s Reel) on the same review page; one picked up before our post is reported as a correction instead. Publishes the review page(s), writes the project docs, logs one IG Posts row per post. |
| `/dead-air-carousel` | Builds one carousel from Stories records you name, or re-cuts an existing post as a new `-v2` version. No story selection. Add `--with-reel` for its Reel. |
| `/dead-air-reel` | One reported deep-dive Reel (plus its carousel) on a dashboard record, one or more URLs, or a plain-language topic. Runs a real 11-outlet coverage check for ad-hoc topics. |

Agents (launched by the commands, not run directly): `dead-air-reporter` (reports one story from sources), `dead-air-coverage` (checks the 11 outlets for one claim), `dead-air-qa` (looks at every slide and a frame sheet of the Reel).

### Examples

```
/dead-air
/dead-air --dry-run
/dead-air --reels 1 --format bundle
/dead-air-carousel <record ID> <record ID> <record ID>
/dead-air-carousel --from dead-air/posts/2026-10-31-bundle.json
/dead-air-reel the Hannibal directive on October 7 --families open
/dead-air-reel https://example.com/some-foreign-report --post
```

## Setup

1. **Install.** In claude.ai: Customize → Plugins → Add marketplace → `schmimran/claude-skills`, then install `dead-air`. In Claude Code: `/plugin marketplace add https://github.com/schmimran/claude-skills`.
2. **Project.** Run the commands in the "News Blindspots Domestically" claude.ai project. It needs the Projects tool, the Artifact tool, the Airtable MCP, WebSearch/WebFetch and the Linux workspace (Playwright and ffmpeg are preinstalled there).
3. **Config doc.** The project must have a doc at `dead-air/config.md`. **None of its values belong in this repo.** It holds:
   - the News Blind Spots base ID, and the Stories and IG Posts table IDs;
   - a field-ID map for every field the plugin reads or writes (see [references/airtable-guide.md](references/airtable-guide.md) for the field names);
   - the "Schmim Knews" design-system artifact URL;
   - the "Schmim Knews — Instagram Playbook" doc URL;
   - the Airtable quirks: write by field ID, never by name; leave the Slides attachment field empty; put the Reel slot in Notes.

   In Claude Code, the commands look for the same file at `./dead-air/config.md` in the working directory. Keep that copy out of any git repo.

Without the Projects or Artifact tools (e.g. in Claude Code), a run writes everything to `./dead-air-out/<date>/`, says what it couldn't do, and stops before Airtable.

## How it decides

The rules live in [references/](references/):

| File | Covers |
| --- | --- |
| [editorial-rules.md](references/editorial-rules.md) | format choice, eligibility and ranking, Flash, the grid, the count line, captions and Sources, Reel content, voice |
| [post-schema.md](references/post-schema.md) | post JSON, story object, deep block, update block, calls JSON, plan input |
| [reel-spec.md](references/reel-spec.md) | Reel structure and timing, ad-hoc mode, families slide, Update Reels |
| [render-guide.md](references/render-guide.md) | setup, script lookup, renderer flags and checks, the fix loop |
| [review-page.md](references/review-page.md) | the review page |
| [airtable-guide.md](references/airtable-guide.md) | IG Posts fields (by name) and quirks |
| [coverage-guide.md](references/coverage-guide.md) | which outlets the search tools can and can't reach |
| [report-format.md](references/report-format.md) | the end-of-run report |
| [carousel-spec.md](references/carousel-spec.md) | the historical v3 rules from the hand-built session |

## Scripts

```
python3 scripts/render.py <post.json> <design_dir> <out_dir> [--fonts <dir>] [--only reel|carousel]
                          [--budget hook=5,timeline=12,...] [--open-family 13,5.5]
python3 scripts/review_page.py <post.json> <out_dir> <calls.json> [--companion <update.json> <update-calls.json>]...
                               [--title …] [--h1 …] [--name …]
python3 scripts/plan_day.py <plan-input.json>
```

`render.py` runs the copy checks, renders the carousel and the Reel against the live design system (read from its artifact on every run; never copied into the plugin), and exits 1 on any failure. `review_page.py` builds the day's review page, with any Update companions on it. `plan_day.py` turns the IG Posts and Stories rows into the day's plan: what counts as posted, eligibility, format, Update companions and corrections. See [references/render-guide.md](references/render-guide.md).

## Tests

The fixture tests cover SPEC §13 tests 1–7a, the `mode: adhoc` rule, and spec addendum v2.1 §F (Update companions, corrections, the count-line fix, Update copy checks, Ready-as-posted). They render two approved Oct 31 posts (the bundle, and the Hannibal deep dive whose Reel opens on a families slide) and the Nov 5 gas-transit Update against an **offline snapshot** of the design system in `tests/fixtures/design-system/`. Live runs never use that snapshot.

```bash
python3 -m venv /tmp/da-venv && /tmp/da-venv/bin/pip install playwright && /tmp/da-venv/bin/python -m playwright install chromium
DEAD_AIR_PYTHON=/tmp/da-venv/bin/python plugins/dead-air/tests/run-fixture.sh
```

You need ffmpeg/ffprobe and npm. The fonts install into the gitignored `tests/.fonts/`.

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

## After install (SPEC §14)

1. In the project, run `/dead-air --dry-run` and check the first call in the review page: it says where the scripts were loaded from.
2. If they came from the plugin's own `scripts/`, delete the project copies of the renderer, the review-page builder, the day planner and the spec. If they came from the project copies, keep those in sync with each plugin release.
3. The earlier `dead-air` skill cards from Oct 31 are superseded; don't save them.
