# Coverage guide

SPEC §5.3 and §12. How `dead-air-coverage` checks the 11 US outlets, and what the search tools can and can't reach.

SPEC §12 asks for this list to be "kept in a reference so the next run doesn't rediscover it". The plugin can't edit itself at run time, so when a run finds a new quirk, the agent reports it, the command puts it in the calls and the report, and Imran folds it into this file in a plugin release.

## The 11 outlets

In grid order: **NYT** (nytimes.com) · **WaPo** (washingtonpost.com) · **WSJ** (wsj.com) · **AP** (apnews.com) · **Reuters** (reuters.com) · **CNN** (cnn.com) · **ABC** (abcnews.go.com) · **NBC** (nbcnews.com) · **CBS** (cbsnews.com) · **Fox** (foxnews.com) · **NPR** (npr.org).

NY Post is checked by the daily scan, but it isn't on the grid and never appears on a slide. Wire copy counts: if NBC ran the AP story, NBC ran it.

## What to check

- **This claim, not the general topic.** Hannibal: did the outlet report that the directive was invoked on Oct 7? Coverage of Oct 7 in general doesn't count. Coverage of an adjacent fact counts as adjacent, and it is reported as such (Oct 31: AP covered the Be'eri probe, and the Times interviewed the general who ordered the tank fire; neither ran the Hannibal orders).
- **The whole period** since the first report, for an old story (Hannibal: since Jul 7, 2024), not a recent window.

## Tool behavior (as of Oct 31, 2026)

| Outlet | WebSearch with `allowed_domains` | Notes |
| --- | --- | --- |
| WaPo, NPR, Fox, NBC, CBS, ABC | works | |
| CNN | works | article pages are **robots-blocked** to WebFetch |
| Reuters, AP, NYT, WSJ | **HTTP 400** | usually `unchecked` in ad-hoc mode, unless a plain query naming the outlet finds the piece |
| X/Twitter | n/a | **robots-blocked** to WebFetch |

**Fallback order** for an outlet that fails:
1. WebSearch with `allowed_domains` set to the outlet.
2. A plain WebSearch naming the outlet and the specific claim.
3. WebFetch of the outlet's own search or section pages.

**Never route around a robots block** (no mirrors, caches or archive copies of a blocked page).

## Verdicts

| Verdict | Means | Grid state |
| --- | --- | --- |
| `ran` | found the piece: URL and date recorded | `ran` (ad-hoc), or `broke` if it originated the story |
| `didn't` | the outlet was searchable, the search worked, and nothing ran | `silent` |
| `unchecked` | the search failed, was blocked, or came back blank for a tool reason | `unchecked`, named in `us` and `meta` |

**Never infer silence from a blank or failed search.** A blank result from a search that returned HTTP 400, timed out, or couldn't be scoped to the outlet is `unchecked`, not `didn't`.

`confidence` is `Probable` unless every outlet was checked. It is `Verified` only for a dashboard row that recorded Verified.

## Counting a foreign outlet from its headline (addendum v2.2 §K)

A foreign outlet counts toward "abroad" if **its own headline**, seen in search results or on its site, states the claim, even when the body is paywalled. (Nov 5: Haaretz counted on the Nathaniel post from its search headline.) **Nothing on the slides may come from text that wasn't read**: a headline-only outlet adds a chip, never a fact, a quote or a date beyond the headline's. Note every headline-only count in the calls: "Haaretz counted from its headline (paywalled; body not read)."
