# Mail Export Guide

How to export your sent mail from common clients. The goal is to get a file (or files) containing only the mail **you wrote** — sent mail, not your inbox.

All processing happens locally on your machine. Nothing is transmitted to any server.

---

## Apple Mail (.mbox bundle)

1. Open Apple Mail.
2. In the sidebar, click **Sent** (or Cmd-click to select multiple mailboxes — e.g. Sent + an archive folder of old sent mail).
3. From the menu: **Mailbox → Export Mailbox…**
4. Choose a destination folder and click **Choose**.

Apple Mail writes a **bundle directory** — a folder named `Sent.mbox` (not a single file). The actual data file is inside it:

```
Sent.mbox/          ← this is a directory
  mbox              ← this is the file you need
```

Drop the outer `Sent.mbox` bundle directory into your archive folder — voice-forge discovers the inner `mbox` file automatically. Do **not** pass the inner file path directly.

To export multiple mailboxes (e.g. Sent + a sent archive), select all of them with Cmd-click before exporting. Each produces its own `.mbox` bundle. Drop all bundles into the archive directory — voice-forge will parse each one.

---

## Outlook for Mac (.olm)

1. Open Outlook for Mac.
2. From the menu: **Tools → Export…**
3. Select **Outlook for Mac Data File (.olm)** and choose **Mail** (or specific mailboxes).
4. Follow the prompts. Outlook produces a single `.olm` file.

The `.olm` is a ZIP of per-message XML. Drop it into the archive directory. The parser will look for a folder named `Sent Items` inside it. If your Outlook uses a different name (e.g. `Sent`), the parser will print the available folder names so you can identify the right one.

**Size note**: OLM files can be large. The parser streams entries and skips attachments — it never extracts the whole archive. Even a 5 GB OLM will parse without filling your disk.

---

## Thunderbird (.mbox)

The simplest approach is the **ImportExportTools NG** add-on:

1. Install **ImportExportTools NG** from the Thunderbird add-on manager.
2. Right-click your **Sent** folder in the sidebar.
3. **ImportExportTools NG → Export folder** → choose **mbox format**.
4. Save to a location you control. Drop the resulting `.mbox` file into the archive directory.

Alternatively, Thunderbird stores mail in mbox format natively. Your profile directory (`~/.thunderbird/<profile>/Mail/`) contains folders that are already mbox files — you can copy the `Sent` file directly if you can locate it.

---

## Outlook for Windows / Exchange (.pst)

PST format is not directly supported by the bundled parsers. Options:

**Option A — Convert to mbox using `readpst` (recommended):**
```bash
brew install libpst        # macOS
readpst -o /tmp/converted  /path/to/archive.pst
```
`readpst` writes one `.mbox` file per folder. Find the Sent folder output and drop it into the archive directory.

**Option B — Export via Outlook Web (OWA):**
If you have Exchange/Office 365 access, you can export mail via OWA to a `.pst`, but the conversion to mbox is still the most reliable path.

**Option C — Use Thunderbird as an intermediary:**
Import the PST into Thunderbird, then export the Sent folder using ImportExportTools NG (see Thunderbird section above).

---

## Privacy note

All parsing runs on your machine. The archive files are read locally by Python scripts in the `scripts/` directory of this plugin. No data is sent anywhere. The output JSON files stay in the working directory you specify.

For safety, you may want to use a copy of your archive file rather than the original, and delete the working directory when you're done with the analysis.

---

## What to include

**Only export sent mail.** Parsing your inbox (received mail) will skew the analysis — the voice in received mail is not your voice.

If you have multiple accounts or multiple years of sent mail across different clients, export and include all of them. The merge step will combine them and attribute rows to their source.
