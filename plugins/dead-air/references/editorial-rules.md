# Editorial rules

SPEC §8 and §9. These rules decide what Dead Air posts and how it reads. Where the "Schmim Knews — Instagram Playbook" doc disagrees on cadence, delivery or wording, this file wins.

The renderer enforces everything marked **(rejected)**. Every other rule is a judgment call: the agent applies it and records it in the calls JSON (see [post-schema.md](post-schema.md)).

---

## 1. Format choice (`/dead-air`)

Read the IG Posts table newest first by Post date. Take the first rule that applies:

1. **Status change.** A story posted in the last 30 days is now Covered on the dashboard → **UPDATE** for that story. Hook: "Update: <outlet> ran it <Mon D>."; stat: "<N> days late."; that outlet's square is `ran`. This outranks everything.
2. **Override.** A Flagged row reached Verified with all 11 outlets checked and silent since the last post → **SINGLE**.
3. **Weekly.** It's a Sunday and no weekly ran in the last 6 days → **WEEKLY** bundle of the week's three highest-confidence rows. Repeats are allowed. Hook: "This week's dead air."
4. **Alternate.** Do the opposite of the last post: after a single or deep → **BUNDLE**; after a bundle or weekly → **SINGLE**.
5. **Fallback.** Fewer than three eligible rows for a bundle → **SINGLE**. Note the fallback in the calls.

`--format` on the command overrides this; log the override.

There is no 7-day cap on deep posts. The v3 carousel spec had one; SPEC §5.1 replaced it with the second-Reel rule below.

## 2. Eligibility and ranking

**Eligible:** Status = Flagged, and Confirmation = Verified or Probable. Provisional never posts **(rejected)**.

**Not eligible:**
- any story in a post from the last 7 days (the weekly is the only exception);
- any story already in two posts within the last 14 days;
- any row whose Notes or Absence evidence leave a counting question open: wire copy unresolved, originator status unconfirmed, a "Covered?" ruling pending. Name every skipped row and the reason in the calls and the report.

**Ranking:**
1. Never posted beats previously posted, at the same confidence.
2. Verified before Probable.
3. Days dark, higher first.
4. Number of outlets checked silent, higher first.

**Bundles:** avoid two stories from the same dashboard topic when an eligible alternative at the same confidence exists. Put the strongest first.

**Reel story:** the post's lead story. A **second Reel** (a DEEP post with its own five-slide carousel) runs only when the next eligible story's public record supports 4–6 dated events **and** at least three sourced statements. If none qualifies, say why and stop at one.

**Freshness (phase 3):** run one WebSearch per chosen story for US Tier-A pickup since the row's Last checked. A pickup drops the story; report it. A fresh search is not a full pass, so the check window on the slides stays the dashboard's.

## 3. Flash

- Every deep dive and every Reel cover is Flash.
- Carousels: positions 3, 5 and 7 of each nine posts, counting from the newest.
- Never two Flash covers in a row: check the last IG Posts row's Flash box.
- On a bundle day the BundleCover takes the Flash.

## 4. The grid

- Fixed order: **NYT, WaPo, WSJ, AP, Reuters, CNN, ABC, NBC, CBS, Fox, NPR** **(rejected** if not 11 valid states**)**.
- `broke` is the US Tier-A originator. It is excluded from the count.
- An outlet never verified for this claim is `unchecked`. It renders as silent, and it must be named in `us` **(rejected)** and in `meta`. **Never mark an unchecked outlet silent.**
- `ran` squares are allowed only in UPDATE posts and in ad-hoc deep posts (`"mode": "adhoc"`) **(rejected** otherwise**)**.
- NY Post is checked by the scan but is not on the grid and never appears on a slide.
- Wire copy counts: if NBC ran the AP story, NBC ran it.
- **Breaker rule (open question for Imran):** if a foreign outlet broke a story first and a US Tier-A outlet followed a day later, the dashboard treats the US outlet as the originator (Powerus: FT Sep 16, Reuters Sep 17, so Reuters is hatched). Record this in the calls every time it applies.

## 5. The count line (`stat`)

The stat is a plain sentence a stranger understands, and it must be literally true of the grid. It states the silent count as a number or a word **(rejected** if missing**)** and names the breaker if there is one **(rejected** if missing**)**. Unchecked outlets go in `meta` and `us`, never in the stat.

Rejected phrasing: "we could check", "of the N", ": nothing". Imran turned down "9 of the 10 we could check: nothing" on Oct 31.

| Situation | Pattern |
| --- | --- |
| Breaker | "Reuters ran it. Nine other major US outlets didn't." |
| No breaker, all 11 checked | "None of the 11 biggest US newsrooms ran it." |
| No breaker, some unchecked | "Ten major US outlets didn't run it." |

A stat holds 2 lines on the cover. "Reuters reported it. Nine other major US outlets didn't." runs 3 lines on a non-Flash cover; the "ran it" version fits.

## 6. Captions

The carousel caption, in this order, with a blank line between each part:

1. **Line 1:** the editorial line. 125 characters max, no date, no prefix, no hashtag **(rejected)**. Unkind to the outlets, exact about the facts.
2. **The facts in prose,** 2–3 sentences: breaker, abroad, silent, check window, unchecked.
3. **The ask,** the same line as the Closer **(rejected** if different**)**.
4. **The method sentence**, verbatim **(rejected** if missing**)**:
   "Counts as reported abroad at 3+ major foreign outlets; counts as missing at home when none of the 11 major US outlets ran it, not counting whoever broke it. Board: news.schmim.com"
5. **Hashtags:** `#DeadAir #SchmimKnews` plus 1–3 subject tags, 5 max **(rejected)**.
6. **Sources:** see below.

**Reel caption:** one or two plain sentences on the Reel's story, a blank line, `#DeadAir #SchmimKnews`, then Sources.

**Sources (every caption, Imran Oct 31):** both captions end with a blank line, `Sources` on its own line, then the post's `sources` line, character for character **(rejected)**. That line lists every source the slides and captions draw on, semicolon-separated: outlet, carrier and date ("Haaretz via Times of Israel (Jul 7, 2024)"). Coverage critiques are labelled "on coverage". Every source in it must also appear in the calls. Each caption is 2,200 characters max **(rejected)**.

**Ask:** one of "Follow for the next one." · "Send this to someone who reads the Times." · "Save this. Check back in a week." **(rejected** otherwise**)**. Never the same as the last post. Don't follow a grieving relative with a jab: the Hannibal post changed its ask for that reason.

**Bundle hook:** one of "3 US stories. 11 US outlets. Dead air." · "This week's dead air." (weekly) · "3 things they ran abroad. 0 ran here." (only when all three are 0 of 11) **(rejected** otherwise**)**.

## 7. Reel content

- **Substance first.** The story fills four of the five slides: the hook, what happened, who says what, then the US check, then the Closer. That the story wasn't reported here is one slide near the end, never the hook. Imran rejected a 7.5 s "headline, count, branding" Reel because it said nothing.
- **The hook is the story,** not the count: "Pakistan's army is buying drones from a company tied to Trump's sons."
- **Every line traces to a named source** recorded in the calls.
- **Anger and sympathy come from the record, not the copy.** When a stronger emotional register is wanted, the answer is a stronger on-record quote, never a stronger verb of ours. If none exists, say so in the report and offer what does exist.
- **Sources win over the dashboard.** When the row and the sources disagree, the sources win and the discrepancy goes in the calls and the report as a dashboard correction. The dashboard row is never edited. (Oct 31: the row's "$22.3M" order value and "due to merge" were both wrong.)
- **No claim stronger than the record.** If the brief asks for one, report the documented version instead (see [reel-spec.md](reel-spec.md)).
- **Sourcing order:** lead with named, on-record American institutional voices US viewers will recognize: officials, members of Congress, former officials, US outlets that published the documents. The subject's own advocates get one line. Always include the subject's denial or explanation. Never label, sort or describe anyone by race, on screen or in notes.
- **Families slide:** see [reel-spec.md](reel-spec.md) §4.

## 8. Voice and wording

**Banned (rejected anywhere in the post JSON):** fr, lowkey, no cap, it's giving, "the girls who", "not X doing Y", WAKE UP, "mainstream media", "they don't want you to know", amid, sparks, slams, in the wake of, underscores, reportedly, allegedly, receipt(s). Any emoji.

**Not in headlines (rejected):** "according to", reportedly, allegedly.

**No "receipts" anywhere the audience sees:** no slide, cue, kicker, caption, alt text or Reel frame. "Receipt" survives only as the internal name of the design system's story-slide component.

**Nothing that oversells:** no "proof", "exposed", "they hid", "bombshell". These aren't machine-checked, so QA looks for them.

**Fixed wording:**
- Swipe cue: "Swipe →".
- Story-slide kicker: "Dead Air" (single) or "Dead Air · n of 3" (bundle).
- Deep-dive kickers: "Deep dive · 01 What happened", "02 Both sides", "03 Who ran it". A families slide is "Deep dive · 04 <place>" when it closes and "Deep dive · <place>" when it opens. A deep dive's story slide drops the topic from its kicker.
- Tagline: "Not censorship. Omission." It is the Closer's headline. There is no other tagline.

**Style:** US spelling. Headlines are written in sentence case (the slide uppercases them). Dates read "Oct 17" on slides and "October 17" in prose.
