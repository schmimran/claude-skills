# Post schema

SPEC §6. A post has three files in the project's `dead-air/posts/` folder:

| File | Holds |
| --- | --- |
| `<name>.json` | the post JSON: what `render.py` renders |
| `<name>-calls.json` | the calls JSON: facts and judgment calls for the review page and the audit trail |
| `<name>.md` | the review link, IG Posts row ID, slots, stories, dashboard corrections, Reel sources |

`<name>` is `<date>-<format>` (e.g. `2026-10-31-bundle`). A standalone `/dead-air-reel` post is `<date>-deep-<slug>` (e.g. `2026-10-31-deep-hannibal`). An Update companion is `<date>-update-<slug>` (e.g. `2026-11-05-update-gas-transit`). A re-cut is `<date>-<format>-v2`, then `-v3`, and so on. A file is never overwritten.

The fixtures in `tests/fixtures/` are complete examples of the bundle, deep and update shapes. Their record IDs are placeholders (`recFIXTURE…`) or `null`.

---

## 1. Post JSON

### Top level

| Key | Type | Rule |
| --- | --- | --- |
| `date` | `YYYY-MM-DD` | Run date, US Eastern. |
| `format` | `single` · `bundle` · `weekly` · `deep` · `update` | [editorial-rules.md](editorial-rules.md) §1 |
| `slug` | string | **Required** on update posts: lowercase words joined by hyphens (`gas-transit`). It goes into every file name (`schmimknews-<date>-update-<slug>-NN.png`), so two Updates on one day never collide. Ignored on other formats. |
| `mode` | `dashboard` (default) · `adhoc` | `adhoc` allows `ran` squares, on deep posts only. Any other value is rejected. |
| `flash` | bool | [editorial-rules.md](editorial-rules.md) §3. Always `true` for deep, always `false` for update (rejected otherwise). |
| `bundle_hook` | string | Bundles and weeklies only; one of the three fixed hooks. |
| `ask` | string | One of the three fixed asks, on every format; never the same as the last post. An Update companion's ask differs from the day's post's. |
| `stories` | list | 1 story (single, deep, update) or 3 (bundle, weekly). On an update, the one story is the story **now**: its grid has the late pickups as `ran`. |
| `reel` | `{story, deep}` | **Required** for single, bundle and weekly: the Reel's lead story as a full story object, plus its deep block. Not used on deep or update posts. |
| `deep` | object | **Required** for deep posts. |
| `update` | object | **Required** for update posts; see the update block below. |
| `caption`, `reel_caption` | string | [editorial-rules.md](editorial-rules.md) §6. Both end with `"\n\nSources\n" + sources`. |
| `sources` | string | One line: every source the post draws on, `Outlet via Carrier (Mon D, YYYY); …`. |
| `alt` | list of strings | One per carousel slide, in order. No "receipts". |

### Story object

| Key | Rule |
| --- | --- |
| `record_id` | Stories record ID. Ad-hoc: `null`. |
| `topic` | 14 characters max ("Pakistan", "Deportations"). Sits in the story-slide kicker. |
| `headline` | Single, deep and update posts, and every Reel story. On an update it is exactly `Update: <outlet short> ran it <N> days late.` ([editorial-rules.md](editorial-rules.md) §8). On a non-Flash single, use the reporter's `headline_short`. One declarative sentence: named actors, no outlet, no date, no hedges. 5–14 words. It must fit **3 lines at hook-l** (non-Flash cover) or **4 lines at hook-m** (Flash cover; every deep Reel is Flash). Measured against the design system: hook-l holds about **6 words** in 3 lines; hook-m holds about 11–12. SPEC §6.1's "12 words or fewer" holds only for Flash covers. |
| `title`, `count` | Bundles: title 6–11 words, two lines max. Count is one line: `<outlet> ran it · <N> others didn't · <days> days` or `<non-list source> broke it · <N> didn't · <days> days`. |
| `grid` | 11 states in fixed order NYT, WaPo, WSJ, AP, Reuters, CNN, ABC, NBC, CBS, Fox, NPR: `silent` · `broke` · `ran` · `unchecked`. |
| `stat` | [editorial-rules.md](editorial-rules.md) §5. 2 lines max. Not used on update posts (the UpdateCover leaves the stat slot empty). |
| `claim` | The story slide's lede, 4 lines max at 48 px (about 150 characters). |
| `dateline` | `Reported <Mon D, YYYY> · <who broke it>` or `Published …`. |
| `abroad` | 3–5 `{name, country}`, foreign Tier-A only. No state wires (Anadolu, TRT, Xinhua, TASS, PressTV). |
| `us` | 1–2 sentences, 3 lines max: breaker and date, check window, count, unchecked outlets by name. |
| `confidence` | `Verified` or `Probable`, copied exactly from the dashboard row. Ad-hoc: from the coverage agent (`Probable` unless every outlet was checked). |
| `days_dark` | Copied exactly from the dashboard row. Ad-hoc: **always compute it** from the first foreign report to the run date. SPEC §6.1 says it may be omitted, but the story slide prints it, and `render.py` fails with a KeyError when it's missing. |
| `meta` | Hook line: `<who broke it> <Mon D> · checked <window> · <outlet> not checked`. |

### Deep block

| Key | Rule |
| --- | --- |
| `timeline_lede` | One short line framing the arc ("From India to Rawalpindi in eleven weeks."). |
| `timeline` | 4–6 `{d, e, key}`. `d` like "Sep 16" (or a time, "7:18 am", when the day is fixed). `e` is one sentence. `key: true` on 2–3 pivotal dates. |
| `timeline_note` | `As of <Mon D>: …`: what is still not public. |
| `family` | Optional families slide: `quote`, `who`, `quote2` (optional), `src`, `kicker` (optional), `open` (optional). See [reel-spec.md](reel-spec.md) §4. |
| `claims` | 3–4 `{who, src, say}`. `src` says where and when ("CEO Andrew Fox, Sep 17"). Exact quotes only inside curly quotation marks; otherwise paraphrase. |
| `unknown` | What the record does not establish, 1–3 short sentences. |
| `us_small` | Optional `{name, country}` list: non-list US outlets that ran it, shown as dashed chips and never counted. |

### Update block (`update`)

Addendum v2.1 §B. Everything the Then and Now slides need that the story object doesn't hold.

```json
{"of_post": "dead-air/bundle-2026-10-22.json",
 "posted": "2026-10-22",
 "topic_line": "Trump's envoys pitched Kyiv on reopening Russian gas transit.",
 "then_story": { /* the story object as we posted it */ },
 "then_grid": ["broke","silent","silent","silent","silent","silent","silent","silent","silent","silent","silent"],
 "pickups": [{"outlet": "WSJ", "date": "Nov 1", "note": "own report, US, European and Ukrainian officials"},
             {"outlet": "Reuters", "date": "Nov 2", "note": "carried the WSJ report"}],
 "added": ["The WSJ sourced it to US, European and Ukrainian officials.",
           "European governments reject it; EU law ends Russian gas imports by end-2027."],
 "still_dark": "Eight of the 11 still haven't, as of Nov 2."}
```

| Key | Rule |
| --- | --- |
| `of_post` | Project path of the post we're updating: `dead-air/posts/<date>-<format>.json`, or `dead-air/bundle-<date>.json` for pre-v2 posts. |
| `posted` | That post's date, `YYYY-MM-DD`. Every pickup must be **after** it; one on or before it is a correction, not an Update (rejected). |
| `topic_line` | What "it" is, one sentence, under the cover headline in `lede`. 2 lines max (rejected if missing or longer). |
| `then_story` | The story object **copied from `of_post`**, as posted: `topic`, `claim`, `dateline`, `abroad`, `us` (the count as we said it then), `confidence`, `days_dark` (each required; rejected if missing). Not in the addendum's sample: `render.py` can't read project files, and the Then slide is that story slide. A `grid` here must equal `then_grid`. It passes the same story checks as any other (except the stat). |
| `then_grid` | The grid as it stood on our post date. No `ran` squares (rejected). |
| `pickups` | One `{outlet, date, note}` per late pickup, oldest first (rejected otherwise), one entry per outlet (rejected if repeated). `outlet` is the grid's short name (`WSJ`, `Reuters`); `date` reads `Mon D` and is never after the run date. Every `ran` square in the now-grid has exactly one pickup, and every pickup has a `ran` square (rejected otherwise). `note` is for the calls and the caption, not the slides. |
| `added` | 2–3 short lines: what the late coverage added or changed, from its own text. Carousel only; the Reel leaves them out. |
| `breaker_date` | Optional, `YYYY-MM-DD`: the hatched US breaker's date, when it differs from the date in the story's `dateline` (the breaker rule: FT Sep 16 in the dateline, Reuters Sep 17 hatched). "N days late" counts from it. |
| `still_dark` | How many are still dark, with the date of the scan's latest pass. Its first number (digits or a word) equals the now-grid's silent count (rejected otherwise). |

The story object (`stories[0]`) needs no `stat`. Its `dateline` must carry a date as `Mon D, YYYY`, which the "N days late" check uses unless `update.breaker_date` is set. Its `meta` reads `<breaker> <Mon D> · <outlet> <Mon D> · …`.

### Slides per format

| Format | Carousel | Reel |
| --- | --- | --- |
| single | HookCover, story slide, Closer (3) | `reel.story` + `reel.deep` as a deep sequence |
| bundle, weekly | BundleCover, story slide × 3, Closer (5) | same |
| deep | Flash HookCover, [families if `open`], DeepTimeline, DeepClaims, story slide, [families if not `open`], Closer (5, or 6 with families) | the carousel's slides; a families slide marked `open` moves in front of the hook |
| update | UpdateCover, Then, Now, Closer (4) | Then, one step per pickup, the still-dark line, the Closer: about 20 s ([reel-spec.md](reel-spec.md) §5) |

`alt` must have exactly one string per carousel slide.

---

## 2. Calls JSON

```json
{"reel_length": "44 s",
 "facts": [["Format", "Bundle"], ["Flash", "No (…)"], ["Carousel", "Sat Oct 31, 10:00am ET"], ["Reel", "12:00–2:00pm ET"], ["Ask", "…"]],
 "calls": [["Bold lead.", "Plain explanation."]]}
```

- `reel_length`: the length `render.py` reports, e.g. "44 s". Leave it out when no Reel was rendered (carousel-only runs); the review page then omits its Reel panel. Update posts have a Reel, so their calls carry it.
- `facts`: label/value pairs shown at the top of the review page.
- `calls`: one `[lead, explanation]` pair per judgment.

**The calls must include** every correction to the dashboard, every source a Reel used, every unchecked outlet, the check window, any breaker-rule judgment, what was held back or skipped and why, and every default a command took instead of asking (SPEC §0.5). Someone reading only the calls should be able to audit the run without the transcript.

---

## 3. Plan input (`plan_day.py`)

`/dead-air` phase 2 writes what phase 1 read into `dead-air/out/plan-<date>.json` and runs `python3 dead-air/plan_day.py <that file>`. Field names here are the script's own, not Airtable's; map them from the rows by field ID.

```json
{"run_date": "2026-11-05", "now": "2026-11-05T06:00:00-05:00", "format_override": null,
 "ig_posts": [{"id": "<IG Posts row ID>", "post_date": "2026-10-31", "format": "bundle", "status": "Ready",
               "carousel_slot": "2026-10-31T10:00:00-04:00", "stories": ["<Stories record ID>", "…"]}],
 "stories": [{"id": "<Stories record ID>", "status": "Flagged", "confirmation": "Verified", "days_dark": 40,
              "silent": 10, "override": false, "hold": null, "first_pickup": null}]}
```

- `ig_posts`: every IG Posts row. `carousel_slot` is an ISO datetime with its offset; Airtable's UTC form (`2026-10-31T14:00:00.000Z`) is fine as is. A slot without an offset stops the script.
- `stories`: every Flagged row, plus every row that a post from the last 30 days carried (they may now be Covered).
- `override`: your call on [editorial-rules.md](editorial-rules.md) §1 rule 1 for that row. `hold`: the counting question that makes it ineligible, or `null`. `first_pickup`: for a Covered row, `{"outlet", "date": "YYYY-MM-DD"}` of the first domestic Tier-A pickup; `null` otherwise.

It prints `assumed_posted`, `stale_ready`, `day` (`format`, `rule`, ranked `eligible`, `skipped` with reasons), `companions` (at most two), `deferred_updates`, `corrections` (each with its report `line`) and `unresolved`. The plan file stays in `out/`: it holds record IDs and is never committed or published.
