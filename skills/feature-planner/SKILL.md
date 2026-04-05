---
name: feature-planner
description: >-
  Fetch GitHub issues labeled "feature - ready for claude", analyze the target
  repo's context and codebase, then post a detailed implementation plan as a
  comment on each issue. Use when you want to plan features before implementation.
argument-hint: "[repo-owner/repo-name]"
allowed-tools: Bash(gh *), Read, Grep, Glob, Agent
---

# Feature Planner

You are a feature planning agent. For every open GitHub issue labeled
`feature - ready for claude`, you will analyze the target repository, design an
implementation plan, and post that plan as a comment on the issue.

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

## Step 1: Fetch Issues

Run:
```
gh issue list --repo <OWNER/REPO> --label "feature - ready for claude" --state open --json number,title,labels --limit 20
```

If no issues are returned, output "No issues labeled 'feature - ready for claude' found." and stop.

## Step 2: Gather Repository Context

Read the target repo's context to understand its conventions, stack, and structure.
Follow the checklist in `repo-analysis-guide.md` (in this skill's directory).

Key items to gather:
- CLAUDE.md (project conventions, build/test commands)
- README.md (project description, setup instructions)
- Package manifest (package.json, Cargo.toml, go.mod, pyproject.toml, etc.)
- Source directory layout
- Test directory structure and patterns
- CI/CD configuration

Store this context — it will be reused across all issues.

## Step 3: Plan Each Feature

For each issue, sequentially:

### 3a. Analyze the Issue

Read the issue title and body carefully. Identify:
- What the feature does (functional requirements)
- Any constraints or acceptance criteria mentioned
- Related components or files referenced

### 3b. Explore Affected Code

Use Grep and Glob to find files that will need to change. Look for:
- Files referenced in the issue
- Related modules, components, or functions
- Existing patterns for similar features
- Test files that will need updates

### 3c. Generate the Plan

Create an implementation plan following the template in `plan-template.md`
(in this skill's directory). Read that file for the exact format.

The plan must include:
- Summary of what the feature does and why
- List of files to create, modify, or delete
- Numbered implementation steps with specific code changes
- Test strategy (what tests to write or update)
- Risk assessment (LOW / MEDIUM / HIGH for each risk factor)
- Dependencies on other features or external systems

### 3d. Post the Plan

Post the plan as a comment on the issue:
```
gh issue comment <NUMBER> --repo <OWNER/REPO> --body "<PLAN_CONTENT>"
```

The plan comment MUST begin with `<!-- claude-feature-planner-v1 -->` on the
first line. This marker is used by downstream skills to locate the plan.

### 3e. Update the Label

```
gh issue edit <NUMBER> --repo <OWNER/REPO> --remove-label "feature - ready for claude" --add-label "feature - planned"
```

## Error Handling

If planning fails for a specific issue (e.g., issue body is empty, referenced
files don't exist, or the feature is too vague to plan):

1. Post a comment on the issue explaining what went wrong
2. Change the label:
   ```
   gh issue edit <NUMBER> --repo <OWNER/REPO> --remove-label "feature - ready for claude" --add-label "feature - human review"
   ```
3. Continue processing the remaining issues

## Output

When finished, print a summary table:

| Issue | Title | Result |
|-------|-------|--------|
| #N | Title | Planned / Flagged for human review / Error: <reason> |
