Update the `dead-air` plugin in this repo (schmimran/claude-skills) to spec addendum v2.2, as version 0.3.0.

The addendum is `dead-air-handoff/SPEC-ADDENDUM-v2.2.md` (unzipped at the repo root; don't commit it). It sits on top of SPEC v2 and v2.1 and wins where they disagree. It comes from the first real claude.ai run on Nov 5. Part 1 makes the repo the source of truth for code and rules (fetched by release tag, with a version-checked project cache) and separates the project into settings/posts/cache/dev. Part 2 covers what the run exposed: four-story daily carousels, download links on the review page, path and version bugs in finding the plugin, workspace hygiene, and Airtable hygiene.

How I want it done:
1. Read the addendum, the current commands, references, scripts and tests. Give me a plan (files touched, schema changes, the new bundle hooks, the review-page download UI, how setup resolves DA_ROOT) and wait for my OK.
2. Feature branch, repo conventions as before.
3. Tests: everything in §E, plus: a 4-story bundle renders clean with each new one-line hook; a 3-story bundle is refused for /dead-air; a Still-dark filler gets its kicker and count line; the review page has a download link for every MP4 and PNG and a zip button; no hard-coded session path appears in any command (grep); `python3 -B` everywhere.
4. Update every reference file so the addendum is the rule everywhere, not a note on top. Add the release checklist (§C) to the plugin README and CLAUDE.md.
5. Bump to 0.3.0 in plugin.json and DEAD_AIR_VERSION in all three commands. After I merge, tag `dead-air-v0.3.0`.
6. Open a PR listing the addendum sections covered and anything you couldn't do.

Same rule as before: no Airtable IDs, record IDs or artifact URLs in the repo.
