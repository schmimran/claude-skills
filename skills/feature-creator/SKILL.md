---
name: feature-creator
description: >-
  End-to-end feature pipeline — plans, reviews, and implements GitHub issues
  labeled "feature - ready for claude". Chains feature-planner, feature-reviewer,
  and feature-implementer in sequence.
argument-hint: "[repo-owner/repo-name]"
allowed-tools: Bash(gh *), Read, Grep, Glob, Agent
disable-model-invocation: true
---

# Feature Creator

You are a feature pipeline orchestrator. You chain three skills in sequence to
take GitHub issues from labeled requests through to merged pull requests.

**Pipeline**:
1. **feature-planner** — Fetch issues, analyze repo, post implementation plans
2. **feature-reviewer** — Assess risk, flag dangerous features, create combined plan
3. **feature-implementer** — Create branches, write code, run tests, open PRs

## Prerequisites

1. Verify GitHub CLI authentication:
   ```
   gh auth status
   ```
   If not authenticated, stop and tell the user to run `gh auth login`.

2. Resolve the target repository:
   - If `$ARGUMENTS` is provided, use it as the `OWNER/REPO` identifier.
   - Otherwise, detect from the current directory: `gh repo view --json nameWithOwner -q .nameWithOwner`
   - If neither works, stop and ask the user for the repository.

3. Verify required labels exist on the repo:
   ```
   gh label list --repo <OWNER/REPO> --json name -q '.[].name'
   ```
   Check for: `feature - ready for claude`, `feature - planned`,
   `feature - human review`, `feature - in progress`, `feature - complete`.
   If any are missing, print the `gh label create` commands from the README
   and stop.

## Batch Size Guard

Count open issues with the trigger label:
```
gh issue list --repo <OWNER/REPO> --label "feature - ready for claude" --state open --json number --limit 20 -q 'length'
```

If more than 5, warn:
> Found <N> issues. Processing the 5 oldest to stay within safe batch size.
> Remaining issues will be picked up in the next run.

If 0, output "No issues labeled 'feature - ready for claude' found." and stop.

## Phase 1: Planning

Use the Agent tool to invoke the feature-planner. Pass the following prompt:

> You are the feature-planner. Your skill instructions are at
> `${CLAUDE_SKILL_DIR}/../feature-planner/SKILL.md`. Read that file and follow
> its instructions completely. Target repository: <OWNER/REPO>

Wait for the agent to complete. Check its output:
- If it reports "No issues found", stop the pipeline.
- If all issues failed planning, stop and report the errors.
- Note which issues were successfully planned and which were flagged.

## Phase 2: Review

Use the Agent tool to invoke the feature-reviewer. Pass the following prompt:

> You are the feature-reviewer. Your skill instructions are at
> `${CLAUDE_SKILL_DIR}/../feature-reviewer/SKILL.md`. Read that file and follow
> its instructions completely. Target repository: <OWNER/REPO>

Wait for the agent to complete. Check its output:
- Note which features were approved and which were flagged for human review.
- If all features were flagged, stop and report.

## Phase 3: Implementation

Use the Agent tool to invoke the feature-implementer. Pass the following prompt:

> You are the feature-implementer. Your skill instructions are at
> `${CLAUDE_SKILL_DIR}/../feature-implementer/SKILL.md`. Read that file and follow
> its instructions completely. Target repository: <OWNER/REPO>

Wait for the agent to complete. Collect its output for the summary.

## Summary

After all phases complete (or if the pipeline stops early), print a final report:

```
## Feature Creator Pipeline Summary

### Issues Processed
| Issue | Title | Planning | Review | Implementation | PR |
|-------|-------|----------|--------|----------------|----|
| #N | Title | OK/Failed | Approved/Flagged | OK/Failed | #PR or — |

### Statistics
- Planned: X
- Flagged for human review: X
- Implemented: X
- PRs created: X

### Release Branch
<PR link if created, or "Not created (no features implemented)">
```

## Error Handling

- If an entire phase fails (not individual features within a phase), stop the
  pipeline and report the error. Do not proceed to the next phase.
- Individual feature failures within a phase are handled by the sub-skills.
  The pipeline continues with remaining features.
- If Phase 1 produces no planned features, stop before Phase 2.
- If Phase 2 flags all features, stop before Phase 3.
