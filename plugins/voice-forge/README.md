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
/analyze-writing-voice [--work-dir /path/to/output]
/build-ghostwriting-skill --findings /path/voice-findings.md
```

## Quick start

1. Export your sent mail ([per-client instructions](references/export-guide.md)), create a folder, and drop all archive files into it.
2. Run `/analyze-writing-voice` — it will ask for the folder path and your email address(es).
4. Review the findings doc it produces.
5. Optionally run `/build-ghostwriting-skill` to generate the ghostwriting skill.

## Prerequisites

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

All parsing and analysis runs locally. The archive files are read by Python scripts in the `scripts/` directory. No data is sent to any server. The output files (JSON dataset, findings doc, skill) stay in the working directory you specify.

## Labels

This plugin does not file GitHub Issues and does not require any labels.
