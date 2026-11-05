# dead-air · spec addendum v2.2 (Nov 5, 2026)

Applies on top of SPEC v2 and addendum v2.1 (both shipped in 0.2.0). Where this file disagrees with them, this file wins.

## Why

On Nov 5 the first real `/dead-air` run in a claude.ai chat stopped at setup. In chat sessions, claude.ai loads the plugin's **commands and agents** but not its `scripts/` or `references/`. SPEC §7.1 had a fallback to copies in the project, but they had just been deleted as stale duplicates. Another session restored 0.2.0 copies, but at the top level of `dead-air/`, mixed in with config, specs and post history.

Two problems to fix:
1. **Drift.** Project copies of code and rules must be refreshed by hand on every release. If anyone forgets, the plugin's instructions call code from another version.
2. **Overlap.** Nothing in the project says which files a human owns, which the plugin owns, and which are history. Imran wants those separated so nothing gets deleted or edited by mistake.

## A. The repo is the source of truth for code and rules

**Replaces SPEC §7.1 and §4 step 2.**

Every command's setup resolves `DA_ROOT`, the folder holding `scripts/` and `references/`, in this order, and stops at the first that works:

1. **Local plugin install** (Claude Code): `$CLAUDE_PLUGIN_ROOT`, or the `installPath` for `dead-air@…` in `~/.claude/plugins/installed_plugins.json`, or a synced plugin folder containing `dead-air/scripts/render.py`.
2. **The repo, pinned to this release.** Each command file carries `DEAD_AIR_VERSION` (for example `0.3.0`), and the repo carries a tag `dead-air-v<version>` for every release. Fetch only the plugin folder:
   ```
   git clone --depth 1 --branch dead-air-v$DEAD_AIR_VERSION --filter=blob:none --sparse \
     https://github.com/schmimran/claude-skills.git dead-air/src
   git -C dead-air/src sparse-checkout set plugins/dead-air
   DA_ROOT=dead-air/src/plugins/dead-air
   ```
   If a plain clone fails and the session has the `add_repo` tool, call it for `schmimran/claude-skills` with read access, then retry once. Check that `DA_ROOT/.claude-plugin/plugin.json` has the same version. If the tag doesn't exist, use `main`, record the commit SHA, and put "version mismatch: ran main at <sha>" at the top of the report.
3. **The project cache** (B): `dead-air/cache/v<version>/`, only if its `VERSION` doc matches `DEAD_AIR_VERSION` exactly. Download the cached docs into the workspace with `project_read`, verifying each against the checksums in `VERSION`.
4. **Stop.** Name which of 1–3 failed and why. Never retype a script from memory, and never use cached files from another version.

After a successful step 1 or 2, **refresh the cache** (B) if it's missing or a different version. That's the only time the plugin writes there.

**Agents.** If an agent type (`dead-air:dead-air-reporter`, `-coverage`, `-qa`) isn't available in the session, read its brief from `DA_ROOT/agents/<name>.md` and do that work in the main thread, under the same rules and output shape. Say in the report which agents ran as agents and which ran inline. In the Nov 5 claude.ai chat runs the commands loaded but the scripts, references and agent briefs didn't, so assume the agents may be missing.

**Paths, stated in the command.** Phase 0 of every command names every path it uses: `DA_ROOT/scripts/`, `DA_ROOT/references/`, `DA_ROOT/agents/`, `dead-air/settings/config.md`, `dead-air/posts/`, `dead-air/cache/`. No run should have to search the project for them. (The Nov 5 fix session flagged that 0.2.0's fallback named only the three scripts.)

The report always states where the code came from: "Code: local install 0.3.0", "Code: repo tag dead-air-v0.3.0", or "Code: project cache v0.3.0 (repo unreachable)".

## B. Project layout: who owns what

**Replaces SPEC §2's project rows.** Four top-level folders under `dead-air/`, each with one owner. Nothing else lives directly under `dead-air/`.

| Folder | Owner | Holds | Read at run time? | Written at run time? |
| --- | --- | --- | --- | --- |
| `dead-air/settings/` | **Imran** | `config.md`: Airtable IDs, artifact URLs, handle. The only file a human edits that the plugin reads. | Yes, first thing | **Never** |
| `dead-air/posts/` | **Plugin** | The post archive: `<date>-<format>.json`, `-calls.json`, `.md`. Pre-v2 posts sit in `posts/legacy/` with their original names. | Yes (no-repeats, Updates' "Then" slide) | Yes, new files only; never edits an old post |
| `dead-air/cache/v<version>/` | **Plugin** | A mirror of `scripts/`, `references/` and `agents/` from the release, plus a `VERSION` doc (version, commit SHA, date, sha256 of every file). Fallback only. | Only when steps 1–2 of A fail | Yes, on refresh. Keeps the current and the previous version, deletes older ones |
| `dead-air/dev/` | **Imran / Claude Code** | Specs, addenda, Claude Code prompts, comparison runs, notes. The design record. | **Never** | **Never** |

Rules every command follows:
- **Never write to `settings/` or `dev/`.** Never delete anything outside `cache/`.
- **Never read code or rules from anywhere but `DA_ROOT`.** A rules file found elsewhere in the project is ignored.
- Updates' "Then" slide looks for the original post in `posts/` first, then `posts/legacy/`.

## C. Releases

Add to the repo's plugin release checklist (README and `CLAUDE.md` for this plugin):
1. Bump `version` in `plugin.json` **and** `DEAD_AIR_VERSION` in all three command files. A test fails if they differ.
2. After merge, tag `dead-air-v<version>` on the merge commit and push the tag.
3. Nothing to copy into the project. The next run refreshes the cache itself.

## D. Migration (one time, after 0.3.0 is installed)

Done by hand in the claude.ai project, not by the plugin. During the switch, 0.3.0 reads `dead-air/settings/config.md` and falls back to `dead-air/config.md` with a warning in the report.

| From | To |
| --- | --- |
| `dead-air/config.md` | `dead-air/settings/config.md` |
| `dead-air/render.py`, `review_page.py`, `plan_day.py`, `dead-air/plugin/**` | delete (0.3.0's first run rebuilds the cache) |
| `dead-air/bundle-*.json`, `dead-air/deep-*.json` | `dead-air/posts/legacy/` |
| `dead-air/plugin-spec.md`, `plugin-spec-addendum-*.md`, `claude-code-prompt-*.md` | `dead-air/dev/` |
| `dead-air/compare/**` | `dead-air/dev/compare/` |

## E. Tests

1. `DEAD_AIR_VERSION` matches `plugin.json` in all three commands.
2. A dry run with no local install fetches the tag into `dead-air/src`, renders the fixtures, and writes `cache/v<version>/VERSION` with correct checksums (manual, claude.ai).
3. With the repo unreachable and a matching cache, the run uses the cache and says so. With a mismatched cache, it stops.
4. No command writes under `settings/` or `dev/` (grep the commands for those paths in write calls).

---

# Part 2 · Findings from the first real run (Nov 5, "Dead-air scripts" chat)

The run made the right editorial calls: a single on the FT oil story under rule 2, the gas-transit Update as a companion, a second Reel on Jasper Nathaniel, two QA passes that caught real errors (a "police and troops" line the run itself had flagged as a dashboard error; a source missing for one timeline entry), quotes checked word for word, and three IG Posts rows. What follows is what went wrong or was missing.

## F. Every daily carousel carries at least four stories

**Replaces SPEC §8.1 rules 2, 4 and 5 and the "single" daily format. Imran, Nov 5: a one-story carousel isn't a post.**

1. The day's carousel is always a **bundle of 4 stories**: BundleCover, four story slides, Closer (6 slides). The weekly is also 4. `single` stays in the schema for ad-hoc use but is never chosen by `/dead-air`.
2. **Story 1 is the lead.** Rule 2 (a Verified row with all 11 checked and silent since the last post) makes a row the lead; otherwise the top of the §8.2 ranking. The day's Reel is a deep dive on the lead, as now.
3. **Stories 2–4 fill the page**, in this order of preference:
   a. Eligible rows never posted, by the usual ranking (Verified before Probable, days dark, outlets checked).
   b. Rows passed over on earlier days (eligible then, not chosen), by days dark.
   c. **Still dark:** rows posted before but not in the last 14 days, still Flagged, by days dark (longest first). Their count line becomes "Still dark: day <N>." and the story slide's kicker reads "Dead Air · Still dark". At most one Still-dark story per carousel.
4. Never as fillers: Provisional rows, rows with an open counting question, Covered rows, and anything in a post from the last 7 days.
5. Topic spread: no more than two stories from one dashboard topic when an alternative exists.
6. **Fewer than 4 qualifying stories:** no carousel that day. The Reel still runs on its own, and the report says which slots couldn't be filled and why.
7. **Bundle hook:** one line only, so four stories fit (tested Nov 5: the two-line "3 US stories. 11 US outlets. Dead air." pushes the footer into the keep-out zone at four stories; a one-line hook fits). New set: "4 stories. Dead air." · "This week's dead air." (weekly) · "4 ran abroad. 0 ran here." (only when all four have no domestic Tier-A, breaker excluded). Story-slide kickers become "Dead Air · n of 4".
8. A fifth story needs a BundleCover variant in the design system (smaller numerals). Not in this release.

## G. Review page: download links

**Imran, Nov 5: grabbing the video from a phone should be one tap.**

- Under every Reel: a **"Download video"** button: `<a href="<file>.mp4" download="<file>.mp4">`, full-width, at least 48px tall.
- Under every carousel strip: **"Download all slides"**, which zips the PNGs in the browser with JSZip from cdnjs (pinned version) and saves `<post>-slides.zip`. Each slide also gets its own small download link, for phones that can't open zips.
- The Reel cover gets its own link ("Download cover").
- Same `download` attribute on every link, so iOS Safari saves the file instead of opening it.

## H. Finding the plugin: bugs from the run

1. **A hard-coded session path.** The run found its files only because the command text named `/root/.claude/plugins/synced/<uuid>/dead-air`, a path from one specific session. In other sessions that UUID differs, which is why the first two chats that morning stopped at setup. Remove every hard-coded path. Search `~/.claude/plugins/synced/*/` for folders whose name starts with `dead-air` and contain `scripts/render.py`.
2. **More than one synced copy.** Sessions can hold several synced versions side by side (seen Nov 5: `dead-air` at 0.1.0 and `dead-air~g2` at 0.2.0). Read each `.claude-plugin/plugin.json` and use the folder whose version equals `DEAD_AIR_VERSION`. Never take the first match.
3. **The standard resolver printed "unresolved"** while a synced copy was on disk, because it only checks `CLAUDE_PLUGIN_ROOT` and `installed_plugins.json`. Steps 1–2 here become part of A's step 1.
4. **Projects uploads need absolute paths.** `project_write` with a relative `local_path` failed on Nov 5. Every command uses absolute paths for uploads.

## I. Workspace hygiene: no bytecode or scratch in the repo or the project

1. Run every script as `python3 -B` and export `PYTHONDONTWRITEBYTECODE=1` in setup. Never run `py_compile` inside a repo clone. (Nov 5: a syntax check left `__pycache__/` in the claude-skills clone; the session spotted and removed it.)
2. Fixed workspace layout, created in setup, all under `./dead-air/` in the session's working directory, **never uploaded**:
   - `src/` the fetched plugin (A)
   - `work/<date>/` scratch: plan inputs, row dumps, leads, checks
   - `out/<post>/` rendered PNGs, MP4s, review pages
   - `posts/` the JSON and calls being written, uploaded to the project at delivery
3. Uploads to the project are allowed only from `posts/` to `dead-air/posts/`, and from `src/` to `dead-air/cache/v<version>/`. Nothing from `work/` or `out/` ever goes to the project; media lives on the review-page artifact.
4. The final step deletes `work/`.

## J. Airtable hygiene

1. **Queued posts hold their slots.** A Ready row with a future Carousel slot (Nov 5 made one: the Nathaniel deep dive, Fri Nov 6 8:00am) counts as already posted for no-repeats, Flash and asks, and its slot is taken. The next run schedules after it.
2. **Old rows missing Format or slot.** The Oct 10, 16 and 22 rows have neither, so the run inferred them. One-time backfill, by hand with Imran's OK: set Format and Carousel slot from the project files. The plugin should never write old rows itself.
3. **Posts without rows.** The Oct 18 bundle exists in the project with no IG Posts row, so no rule can see it. One-time fix: add a row (Status Posted or Skipped, as Imran says).
4. **Asks rotate across queued posts too.** No two posts scheduled within 48 hours share an ask.

## K. Counting a foreign outlet from its headline

Nov 5: Haaretz was counted on the Nathaniel post from a search headline only (paywalled). Rule: a foreign outlet counts toward "abroad" if its own headline (seen in search or on its site) states the claim, even if the body is paywalled. Nothing on the slides may come from text that wasn't read. Note it in the calls.
