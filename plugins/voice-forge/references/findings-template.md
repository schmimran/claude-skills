# Voice Findings Template

Use this template when writing the voice-findings doc. Fill every section from verified data only. Sections marked **[required]** must be present. Never skip the caveats.

---

```markdown
# Voice Analysis: [Name / Description]

**Analyzed:** [Date]
**Data sources:** [list archive files and formats]
**Total messages:** [N] | **Authored (non-empty body):** [N]
**Date range:** [earliest] → [latest]

---

## ⚠️ Caveats

**Audience classification is heuristic.** The business/personal split is based on recipient
email domain. Vendors, contractors, landlords, and anyone on a custom domain are classified
as "business." Treat any audience breakdown as directional, not precise.

**Measured habits may diverge from stated preferences.** This document reports what the
data shows. Where stated and measured habits conflict, both are noted and the skill defaults
to measured unless the user opts for aspirational mode.

---

## Data Summary [required]

| Metric | Value |
|---|---|
| Total messages | [N] |
| Authored (non-empty) | [N] |
| Date range | [start] → [end] |
| Sources | [list] |
| Audience split (heuristic) | business: N, personal: N, self: N |

---

## Core Voice [required]

### Greetings

[dominant form + %]
[second form + % if notable]
[% with no greeting]

### Sign-offs

[dominant form + %]
[any notable variation]

### Length

| Audience | Median words |
|---|---|
| Overall | [N] |
| Business | [N] |
| Personal | [N] |
| Self | [N] |

### Sentence style

- Median avg sentence length: [N] words
- Fragment rate: [N]% (short sentences of 1–3 words)
- This suggests [terse/conversational/formal] delivery.

### Punctuation and formatting tics

[List any non-zero rates for: double_space, two_dot_ellipsis, space_before_bang, space_before_q, smiley, lowercase_open, numbered_list. If a tic is < 5% skip it unless it's distinctive.]

---

## By-Audience Breakdown [required]

### Business (n=[N])
- Greeting: [dominant form + %]
- Sign-off: [dominant form + %]
- Median words: [N]
- Notable: [any characteristics worth calling out]

### Personal (n=[N])
- Greeting: [dominant form + %]
- Sign-off: [dominant form + %]
- Median words: [N]
- Notable: [any characteristics]

### Self-addressed (n=[N])
[Brief note — often used for reminders/drafts; may not reflect voice]

---

## By-Era Trends [include if data spans > 3 years]

| Era | n | Median words | No-greeting % | Fragment % |
|---|---|---|---|---|
| [era] | [N] | [N] | [N]% | [N]% |

[1–2 sentences interpreting the trend, if any]

---

## Intentional Writing Examples [required if any verified quotes exist]

These excerpts show deliberate word choice under conditions that require care: de-escalation,
pushback, bad news, persuasion, feedback. All excerpts are verbatim from the dataset.

### [Category name, e.g. Ownership / Accountability]

> "[verified excerpt]"

### [Category name, e.g. De-escalation / Empathy]

> "[verified excerpt]"

[Continue for each represented category. If no verified examples exist for a category, omit the heading rather than noting its absence — unless absence is itself informative.]

---

## Characterization [required]

[3–5 sentences. Concrete and specific. Cite actual dominant forms and numbers.
Example: "X writes short, direct business emails — median 45 words — opening with the
recipient's name only (no comma, no greeting word), 52% of the time. Sign-offs are
almost always 'name or nothing' (81%). Sentences are short; fragments appear in 38%
of messages. In careful communication, X leads with empathy before getting to the
ask, and closes by offering a path forward rather than leaving the recipient with a
problem."]

---

## Measured vs Stated Divergences [include if applicable]

[If the user has a prior style guide or stated preferences that differ from measured data,
document the divergences here. Example: "User describes their sign-off as 'Cheers'; measured
rate is 4%. Dominant measured sign-off is name_or_none (81%)."]

[If there are no known divergences, omit this section.]

---

## Next Steps

Run `/build-ghostwriting-skill --findings [path to this file]` to generate a personalized
ghostwriting skill from this analysis.
```
