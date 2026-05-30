# Lessons Learned

Hard-won guardrails from the original hand-run session that produced this plugin. Every agent in voice-forge must read this file and follow these rules. They exist because each one was violated at least once in the source session, producing incorrect or fabricated output.

---

## Rule 1 — Export first; never assume the file exists

Before running any parser, the user must have confirmed:
- They have produced a mail export
- They have placed it in the archive directory
- The directory exists and contains at least one recognizable file

Do not infer that an export is present from context. Confirm with `ls`. If the directory is empty or the path is wrong, stop and guide the user — do not proceed with a missing input.

---

## Rule 2 — Prove output, then recount before reporting any number

After any parse or analysis step:
1. Run `ls -la` on the output directory and confirm the expected file is present
2. Reload the output file and count rows from the reloaded data — not from script stdout
3. Only report a row count after this recount

**Why this matters**: In the original session, a parser silently errored and produced zero rows. The harness returned confident-sounding counts that were fabricated. A subsequent step failed when it couldn't find a file it expected to exist. By then, a full analysis doc had been drafted from nothing.

If `ls` shows the file is missing, or if the recount is 0: **STOP**. Do not continue downstream. Do not write an analysis of empty data.

---

## Rule 3 — Verify every quote before it ships (non-optional gate)

`verify_quotes.py` is the only thing that prevents fabricated examples from reaching the findings doc. In the original session, a reading pass invented plausible quotes and cited row indexes that weren't in the file.

The gate rule: no quote goes into the findings doc unless `verify_quotes.py` exits 0 for it. Non-zero exit = fabricated or mislocated quote = discard it.

When a quote fails verification:
- Drop it from `quotes.json`
- Re-run verify on the reduced set
- If no quotes survive, report this rather than substituting invented content

The verify step is a Bash command, not an AI judgment call. Use it.

---

## Rule 4 — Audience classification is heuristic; always state the caveat

The business/personal split in `analyze_voice.py` is domain-based: if the recipient's domain is not in the webmail list (gmail.com, icloud.com, etc.), the email is classified as "business." This means:
- Vendors on custom domains → business
- Landlords, doctors, accountants → business
- Old-school personal contacts with ISP addresses → may land in business

This split is **directional, not exact**. Always include this caveat in:
- Any findings doc section that uses the audience split
- The findings template's caveat section
- The ghostwriting skill's register routing notes

Never present the business/personal split as precise segmentation.

---

## Rule 5 — Measured voice may diverge from stated voice; report it, don't hide it

If the user has a prior style guide, stated preferences, or a self-description of how they write, compare it against the measured data. Where they diverge, report the divergence plainly:

> "You described your sign-off as 'Cheers,' but it appears in only 3% of measured messages. The dominant measured sign-off is 'name_or_none' at 82%."

The generated ghostwriting skill defaults to **measured** habits unless the user explicitly requests aspirational mode. Do not silently upgrade habits to match what the user wishes they did.

---

## Rule 6 — Stream large archives; never blanket-extract

OLM files can be 10 GB or more. The bundled `parse_olm.py` already streams entries from the zip and skips attachments — do not replace this approach with code that extracts the whole archive to disk.

For mbox files: `mailbox.mbox()` is lazy and does not load the full file at once.

If a user provides an unusually large archive (> 1 GB), remind them that parsing sent-only mail is the right scope. Parsing an entire inbox will be slow and produce off-voice signal from received mail.
