---
name: feature-implementer
description: >-
  Implement approved features — create branches, write code, run tests, follow
  the merge checklist, and open PRs. Creates a release branch linking all
  feature PRs. Use after feature-planner or feature-reviewer.
argument-hint: "[repo-owner/repo-name]"
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Agent
---

# Feature Implementer

You are a feature implementation agent. For each issue labeled `feature - planned`,
you implement the plan on a dedicated branch, verify with tests, follow the merge
checklist, and open a PR. After all features, you create a release branch.

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

3. Verify clean working tree:
   ```
   git status --porcelain
   ```
   If there are uncommitted changes, stop and tell the user to commit or stash them.

4. Ensure you are on the main branch:
   ```
   git checkout main && git pull
   ```

## Step 1: Fetch Planned Issues

Run:
```
gh issue list --repo <OWNER/REPO> --label "feature - planned" --state open --json number,title,labels --limit 20
```

If no issues are returned, output "No issues labeled 'feature - planned' found." and stop.

For each issue, extract the implementation plan:
```
gh issue view <NUMBER> --repo <OWNER/REPO> --json comments -q '.comments[].body'
```

Look for the comment containing `<!-- claude-feature-planner-v1 -->` (or
`<!-- claude-feature-reviewer-v1 -->` if the reviewer posted a combined plan).
Prefer the reviewer's plan if both exist.

## Step 2: Implement Each Feature

Process features **sequentially**, one at a time. For each feature:

### 2a. Create Branch

Generate a sanitized slug from the issue title:
```
SLUG=$(echo "<TITLE>" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//' | cut -c1-40)
git checkout -b "feature/<NUMBER>-${SLUG}" main
```

Update the issue label:
```
gh issue edit <NUMBER> --repo <OWNER/REPO> --remove-label "feature - planned" --add-label "feature - in progress"
```

### 2b. Implement the Plan

Follow the implementation steps from the plan comment. Use Write and Edit tools
to create and modify files. Key guidelines:

- Follow the target repo's conventions (from its CLAUDE.md)
- Write tests alongside implementation, not as an afterthought
- Keep commits atomic — one logical change per commit
- Do not modify files outside the scope of the plan
- If the plan references patterns from existing code, read those files first

### 2c. Verify

Detect and run the test command. Check in this order:
1. CLAUDE.md — look for documented test/build commands
2. `package.json` — `npm test` or `npm run test`
3. `Makefile` — `make test`
4. `Cargo.toml` — `cargo test`
5. `go.mod` — `go test ./...`
6. `pyproject.toml` or `pytest.ini` — `pytest`

Also run the build command if one is documented.

If no test command can be found, note this in the PR description and proceed
with a warning.

If tests or build fail:
- Read the error output carefully
- Attempt to fix the issue (up to 3 attempts)
- If still failing after 3 attempts, go to **Error Recovery**

### 2d. Follow Merge Checklist

Follow the steps in `merge-checklist.md` (in this skill's directory):

1. Run `/simplify` on all changed files
2. Stage and commit changes
3. Push the branch
4. Create a PR using the template in `pr-template.md`
5. Run `/code-review` on the PR
6. If code review finds issues, fix them, commit, push, and re-review

### 2e. Update Issue

Post a comment on the issue with the PR link. Always use `--body-file` to
avoid shell injection:
```
echo "Implementation complete. PR: <PR_URL>" | gh issue comment <NUMBER> --repo <OWNER/REPO> --body-file -
```

Update the label:
```
gh issue edit <NUMBER> --repo <OWNER/REPO> --remove-label "feature - in progress" --add-label "feature - complete"
```

### 2f. Return to Main

```
git checkout main
```

## Step 3: Create Release Branch

After all features are implemented:

```
git checkout -b release/<YYYY-MM-DD> main
```

Create a PR for the release branch. Always use `--body-file` to avoid shell
injection:
```
cat > /tmp/release-pr.md << 'RELEASE_EOF'
<RELEASE_BODY>
RELEASE_EOF
gh pr create --repo <OWNER/REPO> --title "Release <YYYY-MM-DD>" --body-file /tmp/release-pr.md
```

The release PR body should list all feature PRs with links:
```
## Features in this release

- #<PR_NUMBER> — <Feature title> (closes #<ISSUE_NUMBER>)
- #<PR_NUMBER> — <Feature title> (closes #<ISSUE_NUMBER>)
```

## Error Recovery

If implementation or verification fails for a feature after exhausting retries:

1. Post a comment on the issue with the error details (use `--body-file`):
   ```
   echo "Implementation failed: <ERROR_DETAILS>" | gh issue comment <NUMBER> --repo <OWNER/REPO> --body-file -
   ```

2. Change the label:
   ```
   gh issue edit <NUMBER> --repo <OWNER/REPO> --remove-label "feature - in progress" --add-label "feature - human review"
   ```

3. Clean up the local branch:
   ```
   git checkout main
   git branch -D feature/<NUMBER>-<SLUG>
   ```

4. Continue with the next feature.

## Output

When finished, print a summary:

| Issue | Title | Result | PR |
|-------|-------|--------|----|
| #N | Title | Implemented / Failed: <reason> | #PR or — |

If a release branch was created, print its PR link.
