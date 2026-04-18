---
name: feature-creator
description: End-to-end feature pipeline — plans, reviews, and implements GitHub issues labeled "feature - ready for claude"
argument-hint: "[repo-owner/repo-name] [--auto-merge]"
disable-model-invocation: true
---

# Feature Creator

You are a feature pipeline orchestrator. You chain agents across five phases to
take GitHub issues from labeled requests through to merged pull requests.

**Pipeline**:
0. **feature-triager** — Shared codebase exploration, group issues into planning buckets
1. **feature-planner** (parallel, one per bucket) — Plan each bucket's issues together
2. **feature-consolidator** — Holistic consistency review, consolidated plan
3. **feature-reviewer** — Assess risk, flag dangerous features, final implementation order
4. **feature-implementer** — Create branches, write code, run tests, open PRs
5. **Merge and cleanup** — Merge feature PRs in order, merge release branch, clean up

## Prerequisites

1. Verify GitHub CLI authentication:
   ```
   gh auth status
   ```
   If not authenticated, stop and tell the user to run `gh auth login`.

2. Resolve the target repository and flags:
   - Parse `$ARGUMENTS`: extract `OWNER/REPO` and check for the `--auto-merge` flag.
   - If no `OWNER/REPO` is given, detect from the current directory: `gh repo view --json nameWithOwner -q .nameWithOwner`
   - If neither works, stop and ask the user for the repository.
   - Note whether `--auto-merge` was passed — this controls Phase 5 behavior.

3. Verify required labels exist on the repo:
   ```
   gh label list --repo <OWNER/REPO> --json name -q '.[].name'
   ```
   Check for: `feature - ready for claude`, `feature - planned`,
   `feature - human review`, `feature - in progress`, `feature - complete`.
   If any are missing, print the `gh label create` commands from the plugin README
   and stop.

## Phase 0: Triage

### 0a. Generate a timestamped bucket manifest path

Capture a single timestamp **once** at the start of Phase 0 and reuse it for
the entire pipeline run. This scopes the manifest path so concurrent pipeline
runs on the same machine do not race on `/tmp/feature-buckets.json`.

```
PIPELINE_TS=$(date +%s)
BUCKET_MANIFEST_PATH="/tmp/feature-buckets-${PIPELINE_TS}.json"
echo "Bucket manifest path: ${BUCKET_MANIFEST_PATH}"
```

Record `BUCKET_MANIFEST_PATH` as a pipeline-scoped variable. You will pass it
to the triager (Phase 0), the planners (Phase 1), and the consolidator
(Phase 2). Do **not** re-derive it later — capture once, reuse.

### 0b. Launch the triager

Use the Agent tool to launch the **feature-triager** agent with this prompt:

> You are the feature-triager. Target repository: <OWNER/REPO>
> Bucket manifest path: <BUCKET_MANIFEST_PATH>
>
> Fetch all open issues labeled `feature - ready for claude`, run one shared
> codebase exploration pass, group the issues into buckets per
> `references/triage-guide.md`, write the manifest to the path above, and post
> per-issue triage comments.

Wait for the triager to complete.

If the triager reports "No issues labeled 'feature - ready for claude' found.",
stop the pipeline and report.

If more than 5 issues were fetched, warn:
> Found <N> issues — this is a large batch. The triager has grouped them into
> <M> buckets. Consider removing the trigger label from lower-priority issues
> to limit the batch size on future runs.

### 0c. Validate the bucket manifest (Suggestion 1 — validation gate)

Immediately after the triager completes, the orchestrator **must** read the
manifest back and assert it is valid JSON with the required top-level keys.
If the file is missing or malformed, halt the pipeline with a clear error —
do **not** launch planners against a broken manifest.

```
# File must exist and be non-empty
if [ ! -s "${BUCKET_MANIFEST_PATH}" ]; then
  echo "ERROR: bucket manifest missing or empty at ${BUCKET_MANIFEST_PATH} — halting pipeline"
  exit 1
fi

# Must parse as JSON and contain the expected top-level keys
python3 - "${BUCKET_MANIFEST_PATH}" <<'PY'
import json, sys
path = sys.argv[1]
try:
    with open(path) as f:
        data = json.load(f)
except Exception as e:
    print(f"ERROR: bucket manifest is not valid JSON: {e}")
    sys.exit(1)
missing = [k for k in ("shared_context", "buckets") if k not in data]
if missing:
    print(f"ERROR: bucket manifest missing required keys: {missing}")
    sys.exit(1)
if not isinstance(data["buckets"], list) or len(data["buckets"]) == 0:
    print("ERROR: bucket manifest has no buckets")
    sys.exit(1)
print(f"OK: bucket manifest valid — {len(data['buckets'])} bucket(s)")
PY
```

If the check fails, stop the pipeline and surface the error to the user. Do
not attempt to recover automatically — a malformed manifest indicates a
triager bug that must be fixed before any planner can run.

Load the manifest into memory for use in Phase 1:

```
BUCKET_MANIFEST_JSON=$(cat "${BUCKET_MANIFEST_PATH}")
```

## Phase 1: Planning

### 1a. Launch one planner per bucket (parallel)

Iterate over the `buckets` array in the validated manifest. For each bucket,
use the Agent tool to launch a **feature-planner** agent. Launch **all agents
in a single message** so they run in parallel.

Each planner receives this prompt:

> You are the feature-planner. Target repository: <OWNER/REPO>
> Bucket manifest path: <BUCKET_MANIFEST_PATH>
> Your bucket ID: <BUCKET_ID>
>
> Plan every issue in this bucket together. Read the bucket manifest for your
> `shared_context`, the issues in your bucket, the predicted globs, and the
> rationale. Produce one plan comment per issue (written to
> `/tmp/plan-<ISSUE_NUMBER>.md`) that is aware of its bucket-mates.

Pass the full `BUCKET_MANIFEST_PATH` so each planner reads the same file that
the triager wrote — the timestamp suffix guarantees there is no collision
with a concurrent pipeline run.

Wait for all parallel planners to complete. Collect results:
- Which issues were successfully planned
- Which issues were flagged for human review
- Which issues failed with errors

If all issues failed planning, stop the pipeline and report.
If no issues were successfully planned, stop before Phase 2.

## Phase 2: Consolidation

Use the Agent tool to launch the feature-consolidator agent with the following prompt:

> You are the feature-consolidator. Target repository: <OWNER/REPO>
> Bucket manifest path: <BUCKET_MANIFEST_PATH>

Wait for the agent to complete. Check its output:
- Note any features that were flagged due to blocking inconsistencies.
- If all features were flagged, stop and report.

## Phase 3: Review

Use the Agent tool to launch the feature-reviewer agent with the following prompt:

> You are the feature-reviewer. Target repository: <OWNER/REPO>

Wait for the agent to complete. Check its output:
- Note which features were approved and which were flagged for human review.
- If all features were flagged, stop and report.
- Record the implementation order from the reviewer's output — you will need it in Phase 5.

## Phase 4: Implementation

Use the Agent tool to launch the feature-implementer agent with the following prompt:

> You are the feature-implementer. Target repository: <OWNER/REPO>

Wait for the agent to complete. Collect its output:
- Record each feature PR number and the release branch name.
- Note any features that failed implementation.

## Phase 5: Merge and Cleanup

Only proceed if at least one feature PR was successfully created.

### 5a. Check auto-merge flag

If `--auto-merge` was passed in `$ARGUMENTS`, proceed automatically through all
steps without pausing. Otherwise, pause before merging the release branch (5c)
to give the user a final review opportunity.

### 5b. Merge feature PRs

For each PR in the Phase 4 output list (which already reflects implementation order):

```
gh pr merge <PR_NUMBER> --repo <OWNER/REPO> --squash --delete-branch
```

If a merge fails, post a comment on the corresponding issue, change its label to
`feature - human review`, and continue with the next PR.

### 5c. Create and merge the release branch PR

The release PR merges `stage` into `main` (the default branch). GitHub only
auto-closes issues when a PR merges into the default branch, so this is the
only opportunity in the pipeline to auto-close feature issues — every feature
issue successfully merged in Phase 5b must appear as a `Closes #<N>` line in
this PR body. Do **not** emit any explicit `gh issue close` calls; rely on
GitHub's closing keywords.

Construct the release PR body using the template in
`references/release-pr-template.md` (read that file for the exact format).
Populate it from the Phase 4 output:

- The **Summary** section lists one line per successfully-merged feature PR,
  including PR number, title, and issue number.
- The **Closes** section has one `Closes #<ISSUE_NUMBER>` line per feature
  issue that was successfully merged in Phase 5b.

Only include features that were successfully merged. Features that failed to
merge or were labeled `feature - human review` must NOT appear in the Closes
section — those issues remain open for manual follow-up.

**Pre-flight check (required before `gh pr create`).** Build the set of issue
numbers for every PR merged successfully in Phase 5b. For each issue number,
confirm the composed body contains a matching `Closes #<N>` line. If any
merged issue is missing, fail with an error and stop — do not create the PR.
This guarantees the release merge into `main` will auto-close every feature
issue landed in this release.

Write the body to `/tmp/release-pr-body.md` and create the PR with
`--body-file`:

```
cat > /tmp/release-pr-body.md << 'RELEASE_EOF'
<POPULATED_TEMPLATE_BODY>
RELEASE_EOF

# Pre-flight: confirm every merged issue number appears as a Closes line
for N in <merged_issue_numbers>; do
  if ! grep -q "^Closes #${N}\b" /tmp/release-pr-body.md; then
    echo "ERROR: release PR body missing 'Closes #${N}' — aborting"
    exit 1
  fi
done

gh pr create --repo <OWNER/REPO> --base main --head release/<YYYY-MM-DD> \
  --title "Release <YYYY-MM-DD>" --body-file /tmp/release-pr-body.md
```

**If `--auto-merge` was NOT passed**: Stop here. Print the release PR link and ask:
> All feature PRs have been merged. Release PR: <URL>
> Respond to confirm and I will merge the release branch and clean up.

Wait for explicit user confirmation before continuing to step 5d.

**If `--auto-merge` was passed**: Proceed immediately to step 5d.

### 5d. Merge the release branch

```
gh pr merge <RELEASE_PR_NUMBER> --repo <OWNER/REPO> --squash
```

### 5e. Cleanup

Follow the global cleanup conventions from `~/.claude/CLAUDE.md`:

```
git checkout main && git pull

# Delete remote feature branches (always run — --delete-branch in 5b handles
# GitHub's remote ref but local tracking refs require explicit cleanup)
git push origin --delete feature/<N>-<slug>   # for each feature branch

# Delete local feature branches
git branch -D feature/<N>-<slug>              # for each feature branch

# Delete release branch (local and remote)
git branch -D release/<YYYY-MM-DD>
git push origin --delete release/<YYYY-MM-DD>

# If running in a git worktree, remove it
git worktree remove .claude/worktrees/<name>
```

### 5f. Memory

Per the global "After a feature is complete" conventions: if any non-obvious
patterns, architectural decisions, or environment variables were introduced in
the target repository during this run, save them to Claude Code memory.

Do not save ephemeral details (PR numbers, branch names, issue counts).

## Summary

After all phases complete (or if the pipeline stops early), print a final report:

```
## Feature Creator Pipeline Summary

### Issues Processed
| Issue | Title | Planning | Consolidation | Review | Implementation | PR |
|-------|-------|----------|---------------|--------|----------------|----|
| #N | Title | OK/Failed | Included/Flagged | Approved/Flagged | OK/Failed | #PR or — |

### Statistics
- Planned: X
- Flagged for human review: X
- Implemented: X
- Merged: X

### Release
<Release PR link and merge status, or "Not created (no features implemented)">
```

## Error Handling

- If an entire phase fails (not individual features within a phase), stop the
  pipeline and report the error. Do not proceed to the next phase.
- Individual feature failures within a phase are handled by the agents.
  The pipeline continues with remaining features.
- If Phase 1 produces no planned features, stop before Phase 2.
- If Phase 2 flags all features, stop before Phase 3.
- If Phase 3 flags all features, stop before Phase 4.
- If Phase 4 produces no PRs, skip Phase 5.
