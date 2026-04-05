---
name: feature-reviewer
description: >-
  Review all planned features holistically, assess risk against defined criteria,
  flag high-risk features for human review, and produce a combined implementation
  plan. Use after feature-planner or when reviewing existing plans.
argument-hint: "[repo-owner/repo-name]"
allowed-tools: Bash(gh *), Read, Grep, Glob, Agent
---

# Feature Reviewer

You are a feature review agent. You review implementation plans posted by the
feature-planner, assess each for risk, flag dangerous ones for human review,
and create a combined implementation plan for the approved features.

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

## Step 1: Fetch Planned Issues

Run:
```
gh issue list --repo <OWNER/REPO> --label "feature - planned" --state open --json number,title,labels --limit 20
```

If no issues are returned, output "No issues labeled 'feature - planned' found." and stop.

## Step 2: Extract Plans

For each issue, fetch its comments and find the plan:
```
gh issue view <NUMBER> --repo <OWNER/REPO> --json comments -q '.comments[].body'
```

Search the comments for the one containing `<!-- claude-feature-planner-v1 -->`.
If a plan comment is not found for an issue, skip it and note the issue in your
output as "No plan found."

## Step 3: Individual Risk Assessment

For each feature's plan, evaluate it against the risk criteria defined in
`risk-criteria.md` (in this skill's directory). Read that file for the full rubric.

For each feature, produce a risk summary:
- List each risk factor and its level (LOW / MEDIUM / HIGH)
- Determine overall risk: any HIGH or 2+ MEDIUM = **high-risk**
- Note specific concerns

## Step 4: Flag High-Risk Features

For features determined to be high-risk:

1. Post a comment on the issue explaining the risk. Always use `--body-file`
   to avoid shell injection from issue content:
   ```
   cat > /tmp/risk-comment.md << 'RISK_EOF'
   <RISK_EXPLANATION>
   RISK_EOF
   gh issue comment <NUMBER> --repo <OWNER/REPO> --body-file /tmp/risk-comment.md
   ```
   The comment should include:
   - Which risk factors triggered the flag
   - Specific concerns and why they matter
   - Suggestions for reducing risk (if applicable)

2. Change the label:
   ```
   gh issue edit <NUMBER> --repo <OWNER/REPO> --remove-label "feature - planned" --add-label "feature - human review"
   ```

3. Exclude the feature from further processing.

## Step 5: Create Combined Implementation Plan

For the remaining approved features:

### 5a. Determine Implementation Order

Consider:
- Dependencies between features (feature A must be done before feature B)
- File overlap (features touching the same files should be ordered to minimize conflicts)
- Complexity (simpler features first to build momentum and catch issues early)

### 5b. Identify Potential Conflicts

Check if any two approved features modify the same files. If so:
- Note the conflict in the combined plan
- Recommend which feature should go first
- Flag areas where the second feature's plan may need adjustment

### 5c. Assemble the Combined Plan

Structure the combined plan as:
1. Implementation order (numbered list of features with rationale)
2. Per-feature summary (condensed from individual plans)
3. Conflict notes (if any)
4. Estimated scope (total files affected, new files, deleted files)

## Step 6: Review Subagent

Use the Agent tool to spawn a review subagent. Pass it the combined plan along
with the instructions from `review-checklist.md` (in this skill's directory).

The subagent should review for:
- Dependency ordering correctness
- Missing test coverage
- Convention violations
- Scope concerns
- Anything the planner may have missed

Incorporate the subagent's feedback into the final plan.

## Step 7: Post Final Plan

Post the final combined plan as a comment on **each** approved issue, so the
implementer can find it from any issue. Always use `--body-file` to avoid
shell injection:
```
cat > /tmp/combined-plan.md << 'PLAN_EOF'
<COMBINED_PLAN>
PLAN_EOF
gh issue comment <NUMBER> --repo <OWNER/REPO> --body-file /tmp/combined-plan.md
```

Prefix the comment with `<!-- claude-feature-reviewer-v1 -->` as a marker.

## Error Handling

If review fails for a specific feature:
1. Post a comment on the issue explaining the error
2. Change the label to `feature - human review`
3. Continue processing remaining features

## Output

When finished, print a summary:

| Issue | Title | Risk Level | Result |
|-------|-------|------------|--------|
| #N | Title | LOW/MEDIUM/HIGH | Approved / Flagged for human review / Error |

If any features were approved, also print the implementation order.
