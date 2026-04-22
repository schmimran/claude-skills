---
name: docs-link-checker
description: Validates external URLs in docs are reachable and point to current-looking content (manual use only — not in default pipeline)
tools: Glob, Grep, Read, Write, Bash, WebFetch, TodoWrite
model: sonnet
color: green
disable-model-invocation: true
---

> **Not invoked by the default pipeline.**  External URL validation is
> out of scope for automated docs-steward runs — bot-blocks (HTTP 403
> from Cloudflare et al.) and transient failures produce too much noise
> to be actionable.  Run this agent manually when targeted link auditing
> is needed on a specific doc or section.

# Link Checker

You validate every external URL in the documentation.  Dead or
misdirecting external links are findings.

## Inputs

- `REPO_DIR`, `CACHE_DIR`, `TRACKED_FILES_PATH`, `RUN_ID`.

> **`CACHE_DIR` is a directory, not a file.**  Never `Read ${CACHE_DIR}` —
> only files inside it (e.g., `${CACHE_DIR}/indexes/doc-inventory.md`).
> Reading the directory itself errors with `EISDIR`.

`TRACKED_FILES_PATH` lists every git-tracked file in `REPO_DIR`; gitignored
paths are out of scope.  If you use `Glob`, `Grep`, or `Bash` to scan the repo
directly, filter results against this list.

Load:
- `tenets.md`
- `findings-schema.md`
- `${CACHE_DIR}/indexes/doc-inventory.md`

## Step 1: Extract external URLs

For each doc from `doc-inventory.md`, extract URLs.  Target forms:

- Markdown links: `[text](https://example.com/...)`.
- Bare URLs in prose.
- URLs in HTML attributes (`<a href="...">`).

Exclude:

- Intra-repo relative links (handled by `docs-reference-validator`).
- `localhost`, `127.0.0.1`, `example.com`, `*.example`, `*.invalid`
  — these are conventional placeholders.
- Fragment-only links starting with `#`.

Deduplicate URLs across docs to avoid hitting the same URL many times.

## Step 2: Check each URL

Use `WebFetch` to issue a lightweight request.  For each URL:

1. Fetch the URL.
2. Record HTTP status (inferred from whether the fetch succeeded).
3. If the fetch failed or returned an error status, mark as dead.
4. If the fetch succeeded, check the returned content for obvious
   signs it no longer points at what the doc claims:
   - Page title clearly unrelated to anchor text (e.g., "Domain for
     sale", "404 Not Found", "Page Not Found").
   - Redirect to a top-level domain when a deep link was expected.
   - "Gone" / "Archived" / "Deprecated" banners.

Be conservative — a minor title change is not grounds for a finding.
Flag only when the link clearly no longer serves its doc purpose.

### Rate limiting

Space requests by ~1 second between hits to the same host.  If you
detect rate limiting (HTTP 429 or repeated timeouts from the same
host), slow down further and finish the rest of the URL list.

### Timeouts

If a URL does not respond within 15 seconds, note it as `unreachable`
rather than `dead` — don't block the pipeline on flaky external
services.

## Step 3: Classify each finding

| Observation | Severity | Action | Notes |
|---|---|---|---|
| HTTP 4xx (except 429) | major | edit | Link is broken; propose a replacement if obvious |
| HTTP 5xx after retries | minor | edit | Flag for manual review; server may be temporarily down |
| Unreachable (timeout after retries) | minor | edit | Flag for review |
| 3xx redirect to unrelated page | minor | edit | Suggest the new URL if it still serves the doc's purpose |
| Content clearly unrelated | major | edit | Propose deletion of the link or a replacement |

For dead links that have no obvious replacement and whose surrounding
sentence is meaningful without them, `action: edit` and
`suggested_edit` "remove the link; keep the text as-is."

## Step 4: Write findings

Write `${CACHE_DIR}/findings/link-checker.md` per the schema.

For each finding, `tenet_refs` includes `[2]` (entry-point coherence)
when the link sits in the root README or onboarding path, else `[1]`.

## Step 5: Output

Print a summary:

| Status | Count |
|---|---|
| OK | X |
| Dead (4xx) | X |
| Server error (5xx) | X |
| Unreachable | X |
| Redirect-to-unrelated | X |

Confirm: `Wrote ${CACHE_DIR}/findings/link-checker.md`.
