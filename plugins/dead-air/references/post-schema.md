# Post schema

SPEC §6. A post has three files in the project's `dead-air/posts/` folder:

| File | Holds |
| --- | --- |
| `<name>.json` | the post JSON: what `render.py` renders |
| `<name>-calls.json` | the calls JSON: facts and judgment calls for the review page and the audit trail |
| `<name>.md` | the review link, IG Posts row ID, slots, stories, dashboard corrections, Reel sources |

`<name>` is `<date>-<format>` (e.g. `2026-10-31-bundle`). A standalone `/dead-air-reel` post is `<date>-deep-<slug>` (e.g. `2026-10-31-deep-hannibal`). A re-cut is `<date>-<format>-v2`, then `-v3`, and so on. A file is never overwritten.

The fixtures in `tests/fixtures/` are complete, approved examples of both shapes. Their record IDs are placeholders (`recFIXTURE…`) or `null`.

---

## 1. Post JSON

### Top level

| Key | Type | Rule |
| --- | --- | --- |
| `date` | `YYYY-MM-DD` | Run date, US Eastern. |
| `format` | `single` · `bundle` · `weekly` · `deep` · `update` | [editorial-rules.md](editorial-rules.md) §1 |
| `mode` | `dashboard` (default) · `adhoc` | `adhoc` allows `ran` squares, on deep posts only. Any other value is rejected. |
| `flash` | bool | [editorial-rules.md](editorial-rules.md) §3. Always `true` for deep. |
| `bundle_hook` | string | Bundles and weeklies only; one of the three fixed hooks. |
| `ask` | string | One of the three fixed asks; never the same as the last post. |
| `stories` | list | 1 story (single, deep, update) or 3 (bundle, weekly). |
| `reel` | `{story, deep}` | **Required** for single, bundle and weekly: the Reel's lead story as a full story object, plus its deep block. Not used on deep or update posts. |
| `deep` | object | **Required** for deep posts. |
| `caption`, `reel_caption` | string | [editorial-rules.md](editorial-rules.md) §6. Both end with `"\n\nSources\n" + sources`. |
| `sources` | string | One line: every source the post draws on, `Outlet via Carrier (Mon D, YYYY); …`. |
| `alt` | list of strings | One per carousel slide, in order. No "receipts". |

### Story object

| Key | Rule |
| --- | --- |
| `record_id` | Stories record ID. Ad-hoc: `null`. |
| `topic` | 14 characters max ("Pakistan", "Deportations"). Sits in the story-slide kicker. |
| `headline` | Single, deep and update posts, and every Reel story. On a non-Flash single, use the reporter's `headline_short`. One declarative sentence: named actors, no outlet, no date, no hedges. 5–14 words. It must fit **3 lines at hook-l** (non-Flash cover) or **4 lines at hook-m** (Flash cover; every deep Reel is Flash). Measured against the design system: hook-l holds about **6 words** in 3 lines; hook-m holds about 11–12. SPEC §6.1's "12 words or fewer" holds only for Flash covers. |
| `title`, `count` | Bundles: title 6–11 words, two lines max. Count is one line: `<outlet> ran it · <N> others didn't · <days> days` or `<non-list source> broke it · <N> didn't · <days> days`. |
| `grid` | 11 states in fixed order NYT, WaPo, WSJ, AP, Reuters, CNN, ABC, NBC, CBS, Fox, NPR: `silent` · `broke` · `ran` · `unchecked`. |
| `stat` | [editorial-rules.md](editorial-rules.md) §5. 2 lines max. |
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

### Slides per format

| Format | Carousel | Reel |
| --- | --- | --- |
| single | HookCover, story slide, Closer (3) | `reel.story` + `reel.deep` as a deep sequence |
| bundle, weekly | BundleCover, story slide × 3, Closer (5) | same |
| deep | Flash HookCover, [families if `open`], DeepTimeline, DeepClaims, story slide, [families if not `open`], Closer (5, or 6 with families) | the carousel's slides; a families slide marked `open` moves in front of the hook |
| update | one HookCover | none |

`alt` must have exactly one string per carousel slide.

---

## 2. Calls JSON

```json
{"reel_length": "44 s",
 "facts": [["Format", "Bundle"], ["Flash", "No (…)"], ["Carousel", "Sat Oct 31, 10:00am ET"], ["Reel", "12:00–2:00pm ET"], ["Ask", "…"]],
 "calls": [["Bold lead.", "Plain explanation."]]}
```

- `reel_length`: the length `render.py` reports, e.g. "44 s". Leave it out when no Reel was rendered (update posts, carousel-only runs); the review page then omits its Reel panel.
- `facts`: label/value pairs shown at the top of the review page.
- `calls`: one `[lead, explanation]` pair per judgment.

**The calls must include** every correction to the dashboard, every source a Reel used, every unchecked outlet, the check window, any breaker-rule judgment, what was held back or skipped and why, and every default a command took instead of asking (SPEC §0.5). Someone reading only the calls should be able to audit the run without the transcript.
