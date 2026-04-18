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
1. **feature-planner** (parallel, one per issue) — Analyze repo, post individual plans
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

## Phase 1: Planning

### 1a. Fetch Issues and Repo Context

Fetch the full list of open issues with the trigger label:
```
gh issue list --repo <OWNER/REPO> --label "feature - ready for claude" --state open --json number,title,labels --limit 20
```

If 0 issues, output "No issues labeled 'feature - ready for claude' found." and stop.

If more than 5 issues, warn:
> Found <N> issues — this is a large batch. Agents will process all of them.
> Consider manually removing the trigger label from lower-priority issues to
> limit the batch size for this run.

Store the full issue list — you will use it to launch parallel planner agents.

Next, gather repository context. Read the target repo's key files to understand
its conventions, stack, and structure:
- **CLAUDE.md** — project conventions, build/test commands, architecture notes
- **README.md** — project description, setup instructions, tech stack
- **Package manifest** — check for package.json, Cargo.toml, go.mod, pyproject.toml, or equivalent
- **Source layout** — use Glob to identify top-level directories (src/, lib/, app/, components/, etc.)
- **Test patterns** — use Glob to find test files (*.test.*, *.spec.*, test/, tests/, __tests__/)
- **CI/CD config** — check .github/workflows/, .gitlab-ci.yml, Jenkinsfile, .circleci/

Summarize the findings into a **repo context block** covering:
1. Language(s) and framework(s)
2. How to run tests and build
3. Directory conventions for new features
4. Existing patterns relevant to the batch of features
5. CI checks that must pass

### 1b. Parallel Planning

For each issue in the list, use the Agent tool to launch a **feature-planner**
agent. Launch **all agents in a single message** so they run in parallel. Each
agent receives this prompt:

> You are the feature-planner. Target repository: <OWNER/REPO>
> Plan this single issue: #<NUMBER> — <TITLE>
>
> Repository context:
> <REPO_CONTEXT_BLOCK>

Wait for all parallel agents to complete. Collect results:
- Which issues were successfully planned
- Which issues were flagged for human review
- Which issues failed with errors

If all issues failed planning, stop the pipeline and report.
If no issues were successfully planned, stop before Phase 2.

## Phase 2: Consolidation

Use the Agent tool to launch the feature-consolidator agent with the following prompt:

> You are the feature-consolidator. Target repository: <OWNER/REPO>

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
