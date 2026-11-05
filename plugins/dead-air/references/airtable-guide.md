# Airtable guide

SPEC §2 and §10.3, plus the quirks recorded in the project doc `dead-air/config.md`.

The **News Blind Spots** base has two tables this plugin touches. A separate daily scan owns the base.

| Table | This plugin |
| --- | --- |
| **Stories** | **Read only. Never create, update or delete a Stories row**, even when the sources prove it wrong. Dashboard errors go in the calls and in the report as "dashboard corrections to make". |
| **IG Posts** | Writes one new row per post. Never edits an old row, except to change Status or add to Notes when Imran asks. |

**No IDs live in this repo.** The base ID, table IDs and every field ID come from `dead-air/config.md` at run time. This file describes fields **by name only**.

---

## Quirks (from config.md)

1. **Write with field IDs, never names.** Map each field name below to its ID from config. Writes by name fail or land in the wrong field.
2. **The Slides attachment field stays empty.** Don't upload PNGs or the MP4 to Airtable. The filenames go in **Slide files** (text), and the media lives on the review page.
3. **"Reel slot" goes in Notes.** There is no Reel-slot field. Write it as the first line of Notes.

If config.md is missing an ID the run needs, stop before writing the row and report which field it was. Don't guess, and don't fall back to field names.

## Reading (phase 1 of `/dead-air`)

- **IG Posts:** all rows, newest first by **Post date**. Used for: the last post's format, Flash box and ask; stories posted in the last 7 and 14 days; the last weekly; posts from the last 30 days whose story is now Covered.
- **Stories:** rows where **Status** = Flagged, with every field config lists. Read **Notes** and **Absence evidence** in full: they decide eligibility ([editorial-rules.md](editorial-rules.md) §2). The grid, `confidence`, `days_dark` and the check window come from the row's recorded checks.

## Writing the IG Posts row (phase 8)

Write it only after the review page is published. When the row is written depends on the command:

| Command | Row written |
| --- | --- |
| `/dead-air` | always (not with `--dry-run`) |
| `/dead-air-carousel` | only when it's for posting: ask in an interactive run; in an unattended run, write it with Status Ready |
| `/dead-air-reel` | only with `--post`, when Imran says so, or in an unattended run (Format `deep`) |

| Field | Value |
| --- | --- |
| **Post** | `Dead Air · <date> · <format>` |
| **Post date** | the run date |
| **Format** | single · bundle · weekly · deep · update |
| **Flash** | checked if the cover is Flash |
| **Carousel slot** | 7:30–8:30am ET on weekdays, 10am ET on weekends; the next open slot not already taken by an IG Posts row |
| **Caption** | the post's `caption` |
| **Reel caption** | the post's `reel_caption` |
| **Alt text** | the `alt` strings, one line per slide |
| **Slide files** | the filenames, one per line, MP4 included |
| **Review page** | the artifact link |
| **Stories** | the record IDs used (linked records); none for an ad-hoc post |
| **Status** | Ready |
| **Post JSON** | a pointer to the project doc, e.g. `dead-air/posts/2026-10-31-bundle.json` |
| **Notes** | line 1: `Reel slot: <time range> ET` (2–4 hours after the carousel). Then the dashboard corrections, the Reel sources, and anything skipped. |

Record the new row's ID in the post's `.md`, and give it in the report.

## Never

- Never write the Stories table.
- Never email anyone, and never post to Instagram.
- Never put a base, table, field or record ID into the plugin, a commit or a PR.
