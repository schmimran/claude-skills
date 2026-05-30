# voice-forge

Analyze your sent-mail archive to produce a data-driven written voice profile, then optionally generate a personalized ghostwriting skill for Claude Desktop.

Generic and privacy-respecting: you supply your own mail export and email addresses at runtime. All processing happens locally on your machine.

## What it does

**Workflow 1 — `/analyze-writing-voice`**

Give it a folder containing your sent-mail exports. The plugin discovers the formats, runs the appropriate parsers, and produces:

- Aggregate voice statistics: greeting patterns, sign-offs, sentence length, punctuation tics, by-audience and by-era breakdowns
- Intentional writing examples: emails from the archive where you were choosing words deliberately (de-escalation, pushback, bad news, feedback, persuasion)
- A verified findings doc: every quote is string-verified against the source data before it's included

**Workflow 2 — `/build-ghostwriting-skill`**

Turns the findings doc into a `voice-skill/` directory containing a `SKILL.md` that tells Claude exactly how to write in your voice: greetings, sign-offs, length targets by audience, punctuation habits, and rhetorical moves for high-stakes communication.

## Commands

```
/analyze-writing-voice
/build-ghostwriting-skill --findings /path/voice-findings.md
```

`/analyze-writing-voice` takes no arguments. It scans the folder you attach to
the session, detects your sender addresses, and confirms once before running.
Outputs land in a `voice-forge-work/` folder inside your attached exports folder.

## Execution requirement (Cowork / Claude Desktop only)

`/analyze-writing-voice` runs **only in a Cowork or Claude Desktop session**. It
resolves its bundled scripts from the mounted plugin directory and reads your
exports from an attached folder under `/sessions`. In a plain terminal session
neither is available, so the command fast-fails with a clear message instead of
guessing. (See Rule 7 in [`references/lessons-learned.md`](references/lessons-learned.md).)

## Quick start

1. Export your sent mail ([per-client instructions](references/export-guide.md)), create a folder, and drop all archive files into it.
2. Attach that folder to a Cowork or Claude Desktop session.
3. Run `/analyze-writing-voice` — it scans the attached folder, detects your sender address(es), and asks you to confirm once before parsing.
4. Review the findings doc it produces (saved to `voice-forge-work/voice-findings.md` inside your exports folder).
5. Optionally run `/build-ghostwriting-skill` to generate the ghostwriting skill.

## Prerequisites

- **A Cowork or Claude Desktop session** with your exports folder attached
- **Python 3** (standard library only — no pip dependencies)
- A local mail export (`.mbox`, `.olm`, or `.mbox` bundle from Apple Mail)

## Supported formats

| Format | Client | Parser |
|---|---|---|
| `.mbox` (file or Apple Mail bundle) | Apple Mail, Thunderbird | `scripts/parse_mbox.py` |
| `.olm` | Outlook for Mac | `scripts/parse_olm.py` |
| `.pst` | Outlook for Windows | Not directly supported — convert to mbox first (see export guide) |

Mixed-client setups work: drop an `.olm` and one or more `.mbox` files into the same folder and the plugin will parse and merge them.

## Privacy

All parsing and analysis runs locally. The archive files are read by Python scripts in the `scripts/` directory. No data is sent to any server. The output files (JSON dataset, findings doc, skill) stay in a `voice-forge-work/` folder inside the exports folder you attach.

## Labels

This plugin does not file GitHub Issues and does not require any labels.
