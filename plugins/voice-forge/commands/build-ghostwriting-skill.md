---
name: build-ghostwriting-skill
description: Turn a voice-forge findings doc into a personalized ghostwriting skill for Claude Desktop. Requires an existing findings doc from /analyze-writing-voice. Confirms before starting.
argument-hint: "--findings /path/voice-findings.md"
disable-model-invocation: true
---

Build a personalized ghostwriting skill from a voice-forge findings doc.

This is a distinct, heavier step that the user must explicitly opt into. **Do not start any work until the user confirms in Step 0.**

---

## Step 0 — Confirm (mandatory, do not skip)

Ask the user the following before doing anything else:

1. **Confirm** — "Do you want to build a ghostwriting skill from this findings doc? This will create a `voice-skill/` directory in your work folder. (yes/no)"
   - If anything other than a clear yes: stop. Do not proceed.

2. **Findings path** — default to `$ARGUMENTS` if provided, otherwise ask for the path to the `voice-findings.md` file produced by `/analyze-writing-voice`.

3. **Voice mode** — which voice should the skill encode?
   - `measured` (default) — uses the person's actual measured habits from the data
   - `aspirational` — uses habits the user wants to cultivate (user must describe them)
   - `both-labeled` — includes both, clearly labeled so Claude can distinguish

4. **Work directory** — where to write the output. Default: same directory as the findings doc. Offer to let the user override.

---

## Step 1 — Build

Launch the `voice-skill-builder` agent with:
- `FINDINGS_PATH` — confirmed path to the findings doc
- `VOICE_MODE` — `measured`, `aspirational`, or `both-labeled`
- `WORK_DIR` — output directory

After the agent completes, tell the user:

> "Your ghostwriting skill is ready at `$WORK_DIR/voice-skill/`.
>
> To use it: open Claude Desktop, go to Settings → Skills, and point it at that directory."
