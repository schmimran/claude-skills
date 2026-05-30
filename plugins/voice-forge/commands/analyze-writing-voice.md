---
name: analyze-writing-voice
description: Analyze a sent-mail export to produce a data-driven written voice profile. Guides export, auto-discovers formats, parses, computes stats, verifies quotes, and writes a findings doc.
disable-model-invocation: true
---

Analyze the user's sent-mail archive to produce a data-driven written voice profile.

> **This command runs only in a Cowork or Claude Desktop session.** It relies on
> the mounted plugin directory and an attached folder under `/sessions`. It will
> not work in a plain terminal session — there is no `/sessions` mount to scan.

Read `references/lessons-learned.md` before starting. Every guardrail in that file applies to this workflow.

---

## Phase 0 — Setup (opening message → pre-parse scan → single confirmation)

### Step 0a — Resolve plugin paths (fast-fail)

Resolve the scripts and references directories from the mounted plugin under
`/sessions`. Both lookups must succeed before anything else runs:

```bash
_VF_ROOT="$(find /sessions -type d -name voice-forge 2>/dev/null | head -1)"
SCRIPTS_DIR="$_VF_ROOT/scripts"
PLUGIN_REFS_DIR="$_VF_ROOT/references"

if [ -z "$SCRIPTS_DIR" ] || [ ! -f "$SCRIPTS_DIR/parse_mbox.py" ]; then
  echo "ERROR: could not locate voice-forge scripts under /sessions."
  echo "This command runs only in a Cowork or Claude Desktop session where the"
  echo "voice-forge plugin is mounted. Aborting."
  exit 1
fi
if [ -z "$PLUGIN_REFS_DIR" ] || [ ! -f "$PLUGIN_REFS_DIR/lessons-learned.md" ]; then
  echo "ERROR: could not locate voice-forge references under /sessions. Aborting."
  exit 1
fi
echo "SCRIPTS_DIR=$SCRIPTS_DIR"
echo "PLUGIN_REFS_DIR=$PLUGIN_REFS_DIR"
```

If either guard fires, stop and tell the user this command must run inside a
Cowork or Claude Desktop session. Do not fall back to scanning the whole
filesystem.

### Step 0b — Opening message

Show the user this message before scanning (do not ask a questionnaire):

> "I'll analyze your sent mail to build a data-driven voice profile. Attach a
> folder containing your sent-mail exports to this session — one or more files
> from any combination of Apple Mail (`.mbox` bundle), Outlook for Mac (`.olm`),
> or Thunderbird (`.mbox`).
>
> If you haven't exported yet, tell me which mail client you use and I'll walk
> you through it. Only export **sent** mail — received mail is not your voice."

If the user needs export guidance, reference `references/export-guide.md` for
step-by-step instructions per client.

### Step 0c — Pre-parse scan

Scan the attached session folder(s) under `/sessions` for recognizable archive
files and derive the inputs automatically — do not prompt for the path:

```bash
# Locate the directory containing any archive file.
ATTACHED_DIR="$(find /sessions -type f \( -iname '*.olm' -o -iname '*.mbox' \) 2>/dev/null \
  | head -1 | xargs -r dirname)"
# Apple Mail bundles are directories named *.mbox — also detect those.
if [ -z "$ATTACHED_DIR" ]; then
  ATTACHED_DIR="$(find /sessions -type d -iname '*.mbox' 2>/dev/null \
    | head -1 | xargs -r dirname)"
fi

if [ -z "$ATTACHED_DIR" ]; then
  echo "No mail archive (.mbox / .olm) found in the attached session folder."
  exit 1
fi
echo "ATTACHED_DIR=$ATTACHED_DIR"
ls -la "$ATTACHED_DIR"
```

If no archive is found, stop and ask the user to attach a folder containing
their exports (point them at `references/export-guide.md` if they haven't
exported yet). Do not proceed.

Derive the candidate owner email addresses by sampling the senders of the
discovered archives. Run the parser's discovery over a small sample and tally
the most frequent `From:` addresses, then propose them as `OWNER_EMAILS`:

```bash
OWNER_EMAILS="$(find "$ATTACHED_DIR" -type f \( -iname '*.mbox' -o -path '*.mbox/mbox' \) 2>/dev/null \
  | head -3 \
  | xargs -r grep -hoE '^From: .*<([^>]+)>|^From: ([^ ]+@[^ ]+)' 2>/dev/null \
  | grep -oE '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' \
  | sort | uniq -c | sort -rn | head -3 | awk '{print $2}' | paste -sd ',' -)"
echo "Detected sender addresses: ${OWNER_EMAILS:-<none — ask the user>}"
```

If the sample is split (e.g. a 50/50 mix across work and personal domains) or no
addresses are detected (e.g. OLM-only, where `From:` headers aren't in the file),
include the detected addresses in the confirmation below and ask the user to
confirm or supply the complete set.

### Step 0d — Set work directory

Anchor all outputs to the attached exports folder so the user finds them next to
their archive:

```bash
WORK_DIR="$ATTACHED_DIR/voice-forge-work"
mkdir -p "$WORK_DIR"
echo "WORK_DIR=$WORK_DIR"
```

### Step 0e — Single confirmation gate

Present a single confirmation summarizing what was detected, then proceed once
the user confirms (this is the only gate in Phase 0):

> "Here's what I found:
> - **Exports folder:** `$ATTACHED_DIR` (`<N>` archive file(s))
> - **Your addresses:** `$OWNER_EMAILS`
> - **Outputs will be saved to:** `$WORK_DIR`
>
> Shall I proceed? If the addresses are wrong or incomplete, give me the full
> list and I'll use that instead."

Only continue after the user confirms. If the user corrects `OWNER_EMAILS`, use
their list.

---

## Phase 1 — Parse

Launch the `voice-parser` agent with:
- `ARCHIVE_DIR` = `$ATTACHED_DIR` — the attached exports folder
- `OWNER_EMAILS` — comma-separated list of the user's addresses (confirmed above)
- `WORK_DIR` — `$ATTACHED_DIR/voice-forge-work`
- `SCRIPTS_DIR` — the resolved scripts directory path
- `PLUGIN_REFS_DIR` — the resolved references directory path

**After the agent returns**, read `$WORK_DIR/voice-parser-output.json`. If the file is absent or `row_count` is 0: **STOP**. Tell the user that parsing produced no data, suggest re-checking the attached exports folder, and do not continue to Phase 2.

---

## Phase 2 — Analyze

Launch the `voice-analyst` agent with:
- `DATASET_PATH` = `$WORK_DIR/email_dataset.json`
- `WORK_DIR`
- `SCRIPTS_DIR`
- `PLUGIN_REFS_DIR`

---

## Phase 3 — Intentional examples + quote verification

Launch the `voice-example-reader` agent with:
- `DATASET_PATH` = `$WORK_DIR/email_dataset.json`
- `WORK_DIR`
- `SCRIPTS_DIR`
- `PLUGIN_REFS_DIR`

**After the agent returns**, read `$WORK_DIR/voice-example-reader-status.json`. If `verify_gate_passed` is false: **STOP**. Report how many quotes failed verification and why, and tell the user that no findings doc will be written until all quotes are verified.

---

## Phase 4 — Findings doc

The findings doc is saved alongside the other outputs — do not prompt for a path:

```bash
SAVE_PATH="$WORK_DIR/voice-findings.md"
```

Launch the `voice-findings-writer` agent with:
- `WORK_DIR`
- `SAVE_PATH` = `$WORK_DIR/voice-findings.md`
- `PLUGIN_REFS_DIR`

---

## Phase 5 — Offer next step

Tell the user:

> "Your voice profile is ready at `$SAVE_PATH`.
>
> Run `/build-ghostwriting-skill --findings $SAVE_PATH` to turn it into a personalized ghostwriting skill you can load into Claude Desktop."
