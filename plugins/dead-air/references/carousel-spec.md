# Schmim Knews · Dead Air — post generation spec (v3, 2026-10-31)

> **Historical reference.** This is the v3 rule set used by hand in the claude.ai project on Oct 31. The plugin's contract is SPEC v2 (Nov 5), split into [editorial-rules.md](editorial-rules.md), [post-schema.md](post-schema.md), [reel-spec.md](reel-spec.md), [render-guide.md](render-guide.md), [review-page.md](review-page.md) and [airtable-guide.md](airtable-guide.md). Where this file and those disagree, they win. This copy has been reconciled to them (Nov 5): the renderer name, the deep-dive cap, the timeline length, the headline length, the Sources block and the calls rules.

The rules the `dead-air` plugin follows. Brand on every slide is SCHMIM KNEWS; Dead Air is the segment. Visual contract: the "Schmim Knews" design system (URL in dead-air/config.md). Reasoning: "Schmim Knews — Instagram Playbook" (URL in dead-air/config.md). v2 changes the playbook in three places, on Imran's instruction of Oct 31: cadence (one run a day producing a carousel plus one or two deep-dive Reels; 3–8 carousels a week), delivery (dated review page + project doc, no email), and no repeats within a week. Everywhere else the playbook wins over this file.

Renderer: `render.py`. Review page: `review_page.py` (both found as described in [render-guide.md](render-guide.md) §2). Every post: `dead-air/posts/<date>-<format>.json` (render input), `-calls.json` (review-page facts and calls) and `.md` (links and calls).

## 0. What one daily run makes

1. **The day's post:** a carousel in the format section 1 picks, plus its Reel: a deep dive on the post's lead story (section 5).
2. **Optionally a second Reel:** a DEEP post on the next eligible story, if its public record supports a 4–6 event timeline and at least three sourced statements. It has its own carousel too; Imran may post only the Reel. If no second story qualifies, say why and stop at one.

Every Reel needs real reporting: read the source articles (WebFetch the foreign Tier-A pieces and any wire copy) for the timeline, who says what, and what is not established. Every line on a deep-dive slide must trace to a source named in the post's calls. Where a dashboard row and the sources disagree (an order value, a merger status), the sources win; flag the row to Imran and do not edit it.

> **Superseded in part by spec addendum v2.1 (Nov 5, 2026).** An Update no longer takes the day or renders as one cover: it is a four-slide companion post with its own Reel, and a pickup dated on or before our post is a correction. See [editorial-rules.md](editorial-rules.md) §0–1 and [post-schema.md](post-schema.md). The rules below are kept as history.

## 1. Choose the format (cadence-agnostic)

Read the IG Posts table (IDs in the project doc `dead-air/config.md`), newest first by Post date.

1. **Status change first.** If a story in any post from the last 30 days is now Covered on the dashboard (a Tier-A outlet ran it after we posted), the post is an UPDATE for that story. It outranks everything.
2. **Override.** A Flagged row that reached Verified with all 11 checked and silent since the last post: SINGLE.
3. **Weekly.** If the post is on a Sunday and no weekly ran in the last 6 days: WEEKLY bundle, "This week's dead air.", the week's three highest-confidence rows; repeats from this week allowed.
4. **Alternate.** Otherwise do the opposite of the last post: after a single or deep dive, BUNDLE; after a bundle or weekly, SINGLE. A deep dive counts as a single. (SPEC v2 drops v3's once-in-7-days cap on deep dives: a second deep Reel can run any day the next eligible story's record supports a 4–6 event timeline and three sourced statements.)
5. **Fallback.** Fewer than three eligible rows for a bundle: SINGLE, noted in the post's calls.

## 2. Pick the stories

Eligible: Status = Flagged, Confirmation = Verified or Probable (Provisional never posts), plus:
- **No repeats within a week:** not in any IG Posts row from the last 7 days (the weekly is the only exception).
- **Not twice in 14 days:** no story more than twice in any 14 days, the weekly included.
- **Open questions block:** skip a row whose Notes or Absence evidence leave a counting question open (wire copy unresolved, originator status unconfirmed, "Covered?" pending a ruling). Say which ones you skipped and why.
- **Never posted before** beats previously posted at the same confidence.

Rank: Verified before Probable, then days dark (higher first), then the number of outlets checked silent. In a bundle, avoid two from the same dashboard topic when an eligible alternative at the same confidence exists. Strongest goes first.

Before rendering, run one fresh search per story for any US Tier-A pickup since the row's Last checked. A pickup → drop the story and say so. A fresh search is not a full pass: the check window on the slides stays the dashboard's.

## 3. Flash

The cover is Flash for every deep dive, and on positions 3, 5 and 7 of each nine posts counting from the newest. Never two Flash covers in a row (check the last IG Posts row's Flash box). On a bundle day the BundleCover takes the Flash.

## 4. Build the post JSON

Bundle-level: `date` (YYYY-MM-DD), `format` (single | bundle | weekly | deep | update), `flash`, `ask` (rotate the three, never the same as the last post): "Follow for the next one." / "Send this to someone who reads the Times." / "Save this. Check back in a week.", `bundle_hook` for bundles (one of "3 US stories. 11 US outlets. Dead air.", "This week's dead air." (weekly), "3 things they ran abroad. 0 ran here." (only when all three are 0 of 11)), `caption`, `reel_caption`, `sources` (one line, see section 6), `alt` (one string per slide), `reel` {story, deep} for every single, bundle and weekly (the Reel's lead story as a full story object with a hook `headline`, plus its `deep` block), and for deep dives `deep` {timeline_lede, timeline[{d,e,key}], timeline_note, claims[{who,src,say}], unknown, us_small[{name,country}], optional family}.

Per story:
- `record_id`: the Stories record.
- `topic`: short subject, 14 characters max ("Pakistan", "Deportations"). It sits in the kicker of the story slide.
- `headline` (single/deep/update): one declarative sentence, named actors, no outlet, no date, no reportedly/allegedly/according to. Sentence case. Must fit 3 lines at hook-l (4 on Flash). Measured: about 6 words at hook-l, about 11–12 on a Flash cover.
- `title`, `count` (bundle): title 6–11 words, two lines max; count "<breaker> ran it · <N> others didn't · <days> days" (or "<non-list source> broke it · <N> didn't · <days> days"), one line.
- `grid`: 11 states in fixed order NYT, WaPo, WSJ, AP, Reuters, CNN, ABC, NBC, CBS, Fox, NPR: silent | broke | ran | unchecked. `broke` = the US Tier-A originator (excluded from the count). `unchecked` = any outlet the dashboard never verified for this claim; it renders as silent and must be named in `us`. NY Post is checked by the scan but is not on the grid and never appears on a slide.
- `stat`: a plain sentence a stranger understands, literally true of the grid. It states the silent count (number or word) and names the breaker if there is one. Unchecked outlets go in `meta` and `us`, never in the stat. Never "we could check", "of the N", or ": nothing" (Imran, Oct 31). Patterns:
  - breaker: "Reuters ran it. Nine other major US outlets didn't."
  - no breaker, all 11 checked: "None of the 11 biggest US newsrooms ran it."
  - no breaker, some unchecked: "Ten major US outlets didn't run it."
- `claim`: the full story for the story slide's lede, 4 lines max at 48px (about 150 characters in practice).
- `dateline`: "Reported <Mon D, YYYY> · <who broke it>" or "Published …".
- `abroad`: 3–5 {name, country}, Foreign Tier-A only, no state wires.
- `us`: one or two sentences, 3 lines max: breaker and date, check window from the dashboard, count, unchecked outlets by name.
- `confidence`, `days_dark`: copy the dashboard row exactly.
- `meta`: hook line, "<who broke it> <Mon D> · checked <window> · <outlet> not checked".

## 5. Render

`python3 render.py <post.json> <design_dir> <out_dir>`. design_dir = the folder an Artifact `read` of the design system saved (it holds project/tokens.json and project/components/bundle.css; tokens.css is generated from tokens.json because the design system does not serve it). Fonts come from npm (@fontsource/big-shoulders-display, work-sans, ibm-plex-mono) because Google Fonts is blocked in the workspace; same faces.

Slides: SINGLE = HookCover, Receipt, Closer. BUNDLE/WEEKLY = BundleCover, Receipt × 3, Closer. DEEP = HookCover (Flash), DeepTimeline, DeepClaims, Receipt, Closer. UPDATE = one HookCover ("Update: <outlet> ran it <Mon D>.", stat "<N> days late.", that outlet's square `ran`).

Reel (Imran, Oct 31, modelled on the Oct 22 Board of Peace cut): the lead story as a deep dive, HookCover (Flash) → DeepTimeline → DeepClaims → story slide → Closer, at 1080×1350. Each line appears on its own and the slide holds when full. Time budget per slide: hook 5 s, timeline 12, claims 11, story slide 8, closer 6 (about 42–45 s). No audio track: Imran adds music. reel-cover.png is the finished hook slide. Substance first: the story fills four of the five slides, and the US check is one slide near the end.

Families slide (optional `deep.family` {quote, who, quote2?, src, kicker?, open?}): a survivor's or bereaved relative's on-record words, sourced in the calls; exact quotes only, from an official or named-outlet translation, and never someone who has asked that their words not be used against the side the post is about. Without `open` it sits before the Closer. With `open: true` it opens the Reel, before the Flash hook, and its finished frame holds about 5.5 s, deliberately too long (Imran, Oct 31); the carousel keeps the Flash cover first with the families slide second, and the Reel cover image stays the Flash hook. Kicker: "Deep dive · <place>" when it opens, "Deep dive · 04 <place>" when it closes.

Deep-dive copy: timeline 4–6 dated entries, one sentence each, key dates marked; `timeline_note` says what is still unknown as of the run date. Claims: 3–4 named sources with where and when they said it; exact quotes only in quotation marks, otherwise paraphrase; include the subject's own denial or explanation. `unknown`: what the record does not establish.

The renderer fails on: a count line that's insider phrasing or not true of the grid, a post without a `reel`, unchecked outlet not named, banned voice words, emoji, caption rules, line caps, overflow, overflow on any Reel slide. Fix by cutting copy, never by shrinking type. Then open every PNG and look.

## 6. Caption

Line 1 (125 characters max, no date, no prefix, no hashtag): the editorial line; be unkind to the outlets, exact about the facts. Blank. The facts in prose, 2–3 sentences (breaker, abroad, silent, check window, unchecked). Blank. The ask (same as the Closer). Blank. "Counts as reported abroad at 3+ major foreign outlets; counts as missing at home when none of the 11 major US outlets ran it, not counting whoever broke it. Board: news.schmim.com" Blank. #DeadAir #SchmimKnews plus 1–3 subject tags, 5 max. No emoji. Reel caption: one or two plain sentences on the Reel's story, blank, #DeadAir #SchmimKnews.

Then, at the end of every caption block (carousel caption and Reel caption alike), a blank line, "Sources" on its own line, and one line listing every source the slides and captions draw on: outlet, and the wire or outlet it came through, with the date, separated by semicolons ("Haaretz via Times of Israel (Jul 7, 2024); ABC Australia (Sep 7, 2024); AP via PBS (Jul 11, 2024); ..."). Include coverage critiques relied on, labelled "on coverage". The same line goes in the post's `sources` field; the renderer fails a caption that doesn't end with it, or one over Instagram's 2,200 characters (Imran, Oct 31).

## 7. Voice (the renderer rejects these)

fr, lowkey, no cap, it's giving, "the girls who", "not X doing Y", WAKE UP, "mainstream media", "they don't want you to know", amid, sparks, slams, in the wake of, underscores, reportedly, allegedly, receipt(s). Any emoji.

## 8. Deliver

1. Write `posts/<date>-<format>-calls.json` ({reel_length, facts[[label, value]], calls[[bold lead, text]]}), run `python3 review_page.py <post.json> <out_dir> <calls.json>`, and publish the HTML it writes as a new artifact with the PNGs, reel.mp4 and reel-cover.png as `files`. One review page per post.
2. Project docs: `dead-air/posts/<date>-<format>.json`, `-calls.json` and `.md` (review link, Airtable row ID, slots, stories, dashboard corrections, Reel sources).
3. IG Posts row (written by field ID from config; see [airtable-guide.md](airtable-guide.md)): Post "Dead Air · <date> · <format>", Post date, Format, Flash, Carousel slot (7:30–8:30am ET weekdays, 10am ET weekends; next open slot), Caption, Reel caption, Alt text, Slide files, Review page, Stories, Status Ready, Post JSON (pointer to the project doc), Notes (Reel slot 2–4 hours after the carousel, plus the calls).
4. No email.

## 9. Wording on anything the audience sees

No "receipts" (Oct 31, Imran): no slide, cue, kicker, caption, alt text or Reel frame uses the word. Nothing that oversells: no "proof", "exposed", "they hid". The swipe cue is "Swipe →". Story slides' kicker reads "Dead Air" (single) or "Dead Air · n of 3" (bundle). The Reel ends on the Closer, whose headline is "Not censorship. Omission.". "Receipt" survives only as the internal name of the story-slide component in the design system.
