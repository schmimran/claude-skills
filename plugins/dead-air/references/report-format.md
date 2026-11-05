# Run report

SPEC §0 and §11. Every command ends with this report, every time: after a full run, a partial run, or a clean stop. It is the last thing the command does.

## Delivery

- **Interactive run:** the final message.
- **Unattended (scheduled) run:** send it with SendUserMessage. If that tool isn't available, it is the final message.

## Shape

A few short lines, in this order. Leave a line out only if it has nothing to say; never pad.

```
Made: <what>, <review page link(s)>
Stories: <which, and why these>
Held back / skipped: <what, and why>
Dashboard corrections to make: <row: field, what the sources say>
Open calls: <judgments Imran should look at>
Didn't finish: <step, why, what Imran can do>   ← only for partial runs or stops
```

Example (from the Oct 31 bundle):

```
Made: Oct 31 bundle (5 slides) + Reel on Powerus, 44 s · <review link> · IG Posts row <id>, Ready, carousel Sat 10am ET, Reel 12–2pm ET
Stories: Powerus, missile delays, third-country deportations. Verified, the three highest days dark not posted this week.
Held back / skipped: Economist peace-plan terms held for the next single; Lukoil waiver skipped (Reuters wire copy unresolved).
Dashboard corrections to make: Powerus: no order value was disclosed (row says ~$22.3M); the merger closed Oct 1 (row says "due to merge").
Open calls: Reuters treated as the Powerus breaker (FT ran it a day earlier); ABC unchecked on all three.
```

## Stopping cleanly (SPEC §0.3)

When a run can't continue (config unreadable, scripts unreachable, design system unreadable, no eligible story, a Reel's only timeline source can't be fetched), it:

1. makes **nothing half-finished**: no review page, no project doc, no Airtable row for the post it couldn't finish;
2. names **exactly which step failed and why**, quoting the error;
3. says **what Imran can do** about it.

```
Didn't finish: phase 0, config. Can't read dead-air/config.md in the News Blindspots Domestically project (Projects tool: "<error>"). Check the doc exists at that path, then run again.
```

A post that was delivered stays delivered. If the second Reel fails after the first post is done, report the first post as made and the second under "Didn't finish".

## Fix-loop leftovers (SPEC §0.2)

If copy, render or QA problems remain after three passes, deliver what passes and list each remaining problem under "Open calls", e.g. `slide 3: stat runs 3 lines after 3 cuts; delivered as is`.
