# Reel spec

SPEC §1, §5.3, §7.3 and §8.7, with addendum v2.1 §B. Each Reel is a **reported deep dive on one story**, revealed line by line: 40–60 s, 1080×1350 MP4, no audio (Imran adds music). Standard length is about 44 s. A Reel that opens on a families slide runs about 57 s.

The one exception is an **Update companion's Reel**: about 20 s, built from its Then and Now slides (§5).

`/dead-air` and `/dead-air-reel` build Reels the same way: the same reporter, the same coverage check and the same `render.py`.

---

## 1. Structure

| # | Slide | Kicker | Budget |
| --- | --- | --- | --- |
| (0) | Families, when `deep.family.open` is true | "Deep dive · <place>" | 13 s, final frame holds 5.5 s |
| 1 | Flash HookCover: the story as one sentence, the stat, the grid, the meta line | "Deep dive · <date>" | 5 s |
| 2 | DeepTimeline: lede, 4–6 dated events, "As of" note | "Deep dive · 01 What happened" | 12 s |
| 3 | DeepClaims: "What each side says.", 3–4 named claims, "Not established" | "Deep dive · 02 Both sides" | 11 s |
| 4 | Story slide: claim, dateline, abroad chips, the 11-outlet grid, `us`, confidence | "Deep dive · 03 Who ran it" | 8 s |
| (5) | Families, when present and not `open` | "Deep dive · 04 <place>" | 8 s |
| 6 | Closer: "Not censorship. Omission.", the method, the ask | "How we check" | 6 s |

**Substance first:** the story fills the hook, timeline, claims and story slides. That US outlets didn't run it is one slide near the end, never the hook.

**Cover:** `reel-cover.png` is always the finished Flash hook, even when the families slide opens the Reel. The carousel always keeps the Flash hook first; an opening families slide is second in the carousel.

## 2. Timing (what `render.py` does)

- Every element marked `data-r` is one reveal step; `data-r="+"` joins the step before it. Hidden steps use `visibility:hidden`, so the layout never shifts.
- Each slide's finished frame holds 2 s. The rest of its budget is split across its steps by word count, and no step is shorter than 0.8 s.
- An opening families slide gets 13 s, and its finished frame holds 5.5 s. That is deliberately a couple of seconds too long (Imran, Oct 31).
- The frames are stitched at 30 fps: H.264 `-preset veryfast -crf 18`, yuv420p, faststart, no audio track.
- Update Reels use fixed holds instead (§5).
- The budgets can be overridden with `--budget` and `--open-family` (see [render-guide.md](render-guide.md)). Don't override them in a normal run; if you do, record the override in the calls.

Fixture results: the bundle's Reel is 25 steps and about 44 s; the Hannibal Reel is 28 steps and about 57 s. With the families slide closing instead of opening, Hannibal is about 52 s. The Nov 5 gas-transit Update is 5 steps and 17 s.

## 3. Ad-hoc Reels (`/dead-air-reel`)

The topic can be a Stories record ID or title fragment, one or more URLs, a plain-language topic, or a screenshot of someone else's post.

**Before reporting.** Restate the topic as one sentence and give the angle the record is likely to support. If the brief asserts something the reporter can't confirm, build the **documented version** and say so in the calls and the report. Never ask about the angle (SPEC §0 overrides §5.3 step 3).
- Worked example: Imran's Oct 31 brief on Imran Khan's ouster. The record supported "a documented US warning, timed to a vote, delivered to the ambassador and passed to the army and ISI chiefs, plus denials". It did not support "the Biden administration gave a green light". **A Reel never states the stronger claim.**

**Lessons from the Hannibal post (Oct 31):**
- **The headline is only as strong as the record.** "Israel's army fired on Israelis being dragged into Gaza" was supported; "deliberately killed its own hostages" was not, and wasn't used.
- **Quotes must be exact and from a named outlet's translation.** A line that exists in only one unofficial translation stays out. So does anyone who asked not to be used against the side the post is about.
- **Verbs follow the sources.** "Try to seize", not "seize". "Could be carrying" captives. Drop a date when the source didn't give one.

**Coverage slide in ad-hoc mode.** Set `"mode": "adhoc"`. The story slide reports what the coverage agent actually found for each of the 11 outlets: ran it (`ran`), didn't (`silent`), or couldn't check (`unchecked`, named in `us` and `meta`). Never claim silence that wasn't verified.
- `days_dark` counts from the first foreign report. Always set it; the slide prints it.
- `confidence` is `Probable` unless every outlet was checked.
- `abroad` names the foreign Tier-A outlets that carried it (Hannibal: Haaretz, Yedioth Ahronoth, Times of Israel, ABC Australia).
- If several US outlets ran it, the honest slide is about **how** they covered it (e.g. "ran Khan's claim, called it unfounded; did not run the cable's text"). The stat must state the real count.

## 4. Families slide (`deep.family`, optional)

Use it only when a families slide is asked for (`--families open|close`), or in `/dead-air` when the record has words that pass every test below.

- A survivor's or bereaved relative's **on-record** words.
- **Exact quotes only**, from an official or named-outlet translation. One unofficial translation is not enough.
- **Never** someone who has said they don't want their words used against the side the post is about.
- Fields: `quote` (headline, 4 lines max), `who` (who they are and what they're talking about, 4 lines max), `quote2` (optional second voice), `src` (where each quote was published), `kicker`, `open`.
- Default position: just before the Closer. `open: true` puts it at the front of the Reel (see §1).
- Every quote and its outlet goes in the calls. Record anything held back and why (Hannibal: one relative's line existed in a single unofficial translation, and she had cautioned against blaming the army).

**Emotional register.** When a stronger register is wanted, the only lever is a stronger on-record quote. If none exists, say so; never strengthen our own verbs.

## 5. Update Reels (addendum v2.1 §B)

An Update companion's Reel shows what we posted, then who ran it since, one outlet at a time. It is built from carousel slides 2 (Then) and 3 (Now). Each step is a static frame with a fixed hold, not a word-count split:

| Step | Shows | Budget key | Seconds |
| --- | --- | --- | --- |
| 1 | The Then slide, fully revealed: the story and the grid as we posted it. Identical to carousel slide 2. | `update_then` | 6 |
| 2 … n+1 | The Now slide. The grid starts with only the breaker. Each step lights the next pickup's square (in `pickups` order) and adds its date to the line under the grid. The still-dark line's space is kept but hidden, so nothing shifts. | `update_square` | 1.5 each |
| n+2 | The same, plus the still-dark line. | `update_hold` | 4 |
| n+3 | The Closer, fully revealed. | `update_closer` | 4 |

Total: 14 + 1.5 × (number of pickups) seconds, so about 17 s for two pickups and 20 s for four.

- **The `added` lines are carousel-only.** The Reel has no time to read them.
- **Cover:** `reel-cover.png` is the UpdateCover (carousel slide 1). It is never Flash.
- **No audio.** Same encoding as every Reel.
- `update_closer` is the addendum's "closer 4". It has its own key so the deep Reels' 6 s `closer` doesn't change.
