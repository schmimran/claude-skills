---
name: feature-creator
description: End-to-end pipeline — plans, reviews, and implements GitHub issues labeled `feature - ready for claude` or `bug - ready for claude`
argument-hint: "[repo-owner/repo-name] [--auto-merge]"
disable-model-invocation: true
---

# Feature Creator

You are a feature/bug pipeline orchestrator. You chain agents across six phases
(0–5) to take GitHub issues from labeled requests through to merged pull
requests. Two parallel state machines run side by side: one for features
(`feature - *` labels) and one for bug fixes (`bug - *` labels). The triager
buckets them separately; downstream agents apply the correct template, risk
rubric, branch prefix, and commit type per type.

**Pipeline**:
0. **feature-triager** — Shared codebase exploration, group issues into planning buckets (features and bugs in separate buckets)
1. **feature-planner** (parallel, one per bucket) — Plan each bucket's issues together
2. **feature-consolidator** — Holistic consistency review, consolidated plan
3. **feature-reviewer** — Assess risk, flag dangerous features/bugs, final implementation order
4. **feature-implementer** — Create branches, write code, run tests, open PRs
5. **Merge and cleanup** — Merge PRs in order, merge release branch, clean up

## Issue types and labels

| Type | Trigger label | Source |
|------|---------------|--------|
| Feature | `feature - ready for claude` | Filed by humans |
| Bug | `bug - ready for claude` | Filed by `bug-sweeper` (or humans) |

State machines:

```
feature: ready for claude → planned → in progress → complete
                              ↓ (high risk)
                          human review

bug:     ready for claude → triaged → planned → in progress → complete
                                         ↓ (high risk)
                                     human review
```

The bug flow has one extra hop (`triaged`) because bug-sweeper writes the
issue with `bug - ready for claude` and no plan; the triager moves it to
`bug - triaged` after the bucket pass; the planner moves it to `bug - planned`
after the plan is posted.

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
   Check for the **feature** state machine:
   - `feature - ready for claude`, `feature - planned`,
     `feature - human review`, `feature - in progress`, `feature - complete`

   And the **bug** state machine:
   - `bug`, `bug - ready for claude`, `bug - triaged`, `bug - planned`,
     `bug - human review`, `bug - in progress`, `bug - complete`,
     `bug - high`, `bug - medium`, `bug - low`

   If any are missing, print the `gh label create` commands from the plugin
   README and stop.

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
> Fetch all open issues labeled `feature - ready for claude` **or**
> `bug - ready for claude`, run one shared codebase exploration pass, group
> the issues into buckets per `references/triage-guide.md` (features and bugs
> in separate buckets), write the manifest to the path above, and post
> per-issue triage comments.

Wait for the triager to complete.

If the triager reports "No issues labeled `feature - ready for claude` or
`bug - ready for claude` found.", stop the pipeline and report.

If more than 5 issues were fetched (across both label sets), warn:
> Found <N> issues — this is a large batch. The triager has grouped them into
> <M> buckets (features: <X>, bugs: <Y>). Consider removing trigger labels
> from lower-priority issues to limit the batch size on future runs.

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
for i, b in enumerate(data["buckets"]):
    if "type" not in b:
        print(f"ERROR: bucket[{i}] missing required 'type' field")
        sys.exit(1)
    if b["type"] not in ("feature", "bug"):
        print(f"ERROR: bucket[{i}] type must be 'feature' or 'bug', got {b['type']!r}")
        sys.exit(1)
n_feat = sum(1 for b in data["buckets"] if b["type"] == "feature")
n_bug  = sum(1 for b in data["buckets"] if b["type"] == "bug")
print(f"OK: bucket manifest valid — {len(data['buckets'])} bucket(s) (features: {n_feat}, bugs: {n_bug})")
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
- Note which issues (features and bugs) were approved and which were flagged for human review.
- If all issues were flagged, stop and report.
- Record the implementation order from the reviewer's output — you will need it in Phase 5.

## Phase 4: Implementation

Use the Agent tool to launch the feature-implementer agent with the following prompt:

> You are the feature-implementer. Target repository: <OWNER/REPO>

Wait for the agent to complete. Collect its output:
- Record each PR number alongside its issue type (feature or bug) and the
  source issue number — both feature and bug-fix PRs count. The implementer's
  output table includes a `Type` column; use it.
- Record the release branch name.
- Note any issues that failed implementation.

## Phase 5: Merge and Cleanup

Only proceed if at least one PR (feature or bug-fix) was successfully created.

### 5a. Check auto-merge flag

If `--auto-merge` was passed in `$ARGUMENTS`, proceed automatically through all
steps without pausing. Otherwise, pause before merging the release branch (5c)
to give the user a final review opportunity.

### 5b. Merge PRs

For each PR in the Phase 4 output list (which already reflects implementation
order — both feature and bug-fix PRs):

```
gh pr merge <PR_NUMBER> --repo <OWNER/REPO> --squash --delete-branch
```

If a merge fails, post a comment on the corresponding issue, change its label
to the **type-appropriate** human-review label, and continue with the next PR:

- Feature issue → `feature - human review`
- Bug issue → `bug - human review`

### 5c. Create and merge the release branch PR

The release PR merges `stage` into `main` (the default branch). GitHub only
auto-closes issues when a PR merges into the default branch, so this is the
only opportunity in the pipeline to auto-close issues — every feature **or
bug** issue successfully merged in Phase 5b must appear as a `Closes #<N>`
line in this PR body. Do **not** emit any explicit `gh issue close` calls;
rely on GitHub's closing keywords.

Construct the release PR body using the template in
`references/release-pr-template.md` (read that file for the exact format).
Populate it from the Phase 4 output:

- The **Summary** section lists one line per successfully-merged PR,
  including PR number, type marker (`feat` or `fix`), title, and issue
  number. Group features and bug fixes into separate sub-sections so a
  human reader can scan them at a glance.
- The **Closes** section has one `Closes #<ISSUE_NUMBER>` line per merged
  issue, **regardless of type**. The pre-flight check below depends on
  every merged issue being represented.

Only include PRs that were successfully merged. PRs that failed to merge or
were labeled `feature - human review` / `bug - human review` must NOT appear
in the Closes section — those issues remain open for manual follow-up.

**Pre-flight check (required before `gh pr create`).** Build the set of
issue numbers for every PR merged successfully in Phase 5b — across both
types. For each issue number, confirm the composed body contains a matching
`Closes #<N>` line. If any merged issue is missing, fail with an error and
stop — do not create the PR. This guarantees the release merge into `main`
will auto-close every feature **and bug** issue landed in this release.

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
> All PRs have been merged. Release PR: <URL>
> Respond to confirm and I will merge the release branch and clean up.

Wait for explicit user confirmation before continuing to step 5d.

**If `--auto-merge` was passed**: Proceed immediately to step 5d.

### 5d. Merge the release branch

```
gh pr merge <RELEASE_PR_NUMBER> --repo <OWNER/REPO> --squash
```

### 5e. Cleanup

Follow the global cleanup conventions from `~/.claude/CLAUDE.md`. Branch
prefix is `feature/` for feature issues and `fix/` for bug issues — clean up
both:

```
git checkout main && git pull

# Delete remote branches (always run — --delete-branch in 5b handles
# GitHub's remote ref but local tracking refs require explicit cleanup)
git push origin --delete feature/<N>-<slug>   # for each feature branch
git push origin --delete fix/<N>-<slug>       # for each bug-fix branch

# Delete local branches
git branch -D feature/<N>-<slug>              # for each feature branch
git branch -D fix/<N>-<slug>                  # for each bug-fix branch

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
| Issue | Type | Title | Planning | Consolidation | Review | Implementation | PR |
|-------|------|-------|----------|---------------|--------|----------------|----|
| #N | feature/bug | Title | OK/Failed | Included/Flagged | Approved/Flagged | OK/Failed | #PR or — |

### Statistics
| | Features | Bugs |
|-|----------|------|
| Planned | X | X |
| Flagged for human review | X | X |
| Implemented | X | X |
| Merged | X | X |

### Release
<Release PR link and merge status, or "Not created (nothing implemented)">
```

## Error Handling

- If an entire phase fails (not individual issues within a phase), stop the
  pipeline and report the error. Do not proceed to the next phase.
- Individual issue failures within a phase are handled by the agents.
  The pipeline continues with remaining issues.
- If Phase 1 produces no planned issues (across both types), stop before Phase 2.
- If Phase 2 flags all issues, stop before Phase 3.
- If Phase 3 flags all issues, stop before Phase 4.
- If Phase 4 produces no PRs (across both types), skip Phase 5.
