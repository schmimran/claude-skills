---
name: analyze-writing-voice
description: Analyze a sent-mail export to produce a data-driven written voice profile. Guides export, auto-discovers formats, parses, computes stats, verifies quotes, and writes a findings doc.
argument-hint: "[--work-dir /path/to/output]"
disable-model-invocation: true
---

Analyze the user's sent-mail archive to produce a data-driven written voice profile.

Read `references/lessons-learned.md` before starting. Every guardrail in that file applies to this workflow.

---

## Phase 0 — Export setup

Ask the user for the following (use `AskUserQuestion` if available, otherwise ask in sequence):

1. **Archive directory** — instruct the user:
   > "Create a folder on your machine and drop all your mail archive files into it — one or more exports from any combination of Apple Mail, Outlook for Mac, or Thunderbird. Then tell me the path to that folder. If you haven't exported yet, I can walk you through it — just tell me which mail client(s) you use."
   
   If the user needs export guidance, reference `references/export-guide.md` for step-by-step instructions per client. Do not proceed until the user confirms they have exported and provided a path.

2. **Your email addresses** — ask for all addresses the user sends from (e.g. work + personal), space- or comma-separated. These are used to confirm authorship and filter out mail the user received but didn't write.

3. **Working directory** — where to save analysis outputs. Default: `~/voice-forge-work/YYYY-MM-DD/` (use today's date). The user can override.

After collecting:
- Run `ls -la "$ARCHIVE_DIR"` to confirm the directory exists and contains files.
- If the directory is empty, does not exist, or contains no recognizable archive formats (`.mbox`, `.olm`, `.pst`), stop and guide the user before continuing.
- Create the working directory: `mkdir -p "$WORK_DIR"`
- Resolve the scripts directory:
  ```bash
  SCRIPTS_DIR="$(find . -path "*/voice-forge/scripts" -type d 2>/dev/null | head -1)"
  ```
  If the result is empty, try an absolute search from the home directory. Confirm `$SCRIPTS_DIR/parse_mbox.py` exists before continuing.

---

## Phase 1 — Parse

Launch the `voice-parser` agent with:
- `ARCHIVE_DIR` — the archive drop directory
- `OWNER_EMAILS` — comma-separated list of the user's addresses
- `WORK_DIR` — the working directory
- `SCRIPTS_DIR` — the resolved scripts directory path

**After the agent returns**, read `$WORK_DIR/voice-parser-output.json`. If the file is absent or `row_count` is 0: **STOP**. Tell the user that parsing produced no data, suggest re-checking the archive directory, and do not continue to Phase 2.

---

## Phase 2 — Analyze

Launch the `voice-analyst` agent with:
- `DATASET_PATH` = `$WORK_DIR/email_dataset.json`
- `WORK_DIR`
- `SCRIPTS_DIR`

---

## Phase 3 — Intentional examples + quote verification

Launch the `voice-example-reader` agent with:
- `DATASET_PATH` = `$WORK_DIR/email_dataset.json`
- `WORK_DIR`
- `SCRIPTS_DIR`

**After the agent returns**, read `$WORK_DIR/voice-example-reader-status.json`. If `verify_gate_passed` is false: **STOP**. Report how many quotes failed verification and why, and tell the user that no findings doc will be written until all quotes are verified.

---

## Phase 4 — Findings doc

Ask the user where to save the findings doc. Default: `$WORK_DIR/voice-findings.md`.

Launch the `voice-findings-writer` agent with:
- `WORK_DIR`
- `SAVE_PATH` — the confirmed save location

---

## Phase 5 — Offer next step

Tell the user:

> "Your voice profile is ready at `$SAVE_PATH`.
>
> Run `/build-ghostwriting-skill --findings $SAVE_PATH` to turn it into a personalized ghostwriting skill you can load into Claude Desktop."
