# Merge Checklist

Follow these steps in order after implementation and verification pass.

## 1. Simplify

Run `/simplify` (a built-in Claude Code skill) on all files changed in the branch.
This checks for code reuse opportunities, quality issues, and efficiency
improvements. Fix any issues found.

## 2. Stage and Commit

Stage all changes:
```
git add <specific files changed>
```

Commit with a descriptive message referencing the issue number:
```
git commit -m "<type>: <description>

Closes #<ISSUE_NUMBER>"
```

Use conventional commit types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`.

## 3. Post-conflict diff verification

If you resolved any merge or rebase conflicts on this branch, you must confirm
that conflict resolution did not silently drop the feature's intended changes.

For every file listed as `Create` or `Modify` in the plan's "Affected Files"
table, run:

```
git diff origin/stage -- <planned-file>
```

Every planned `Create`/`Modify` file must show a non-empty diff. If any planned
file shows no diff, conflict resolution silently dropped the feature — do not
push. Abort and escalate: label the issue `feature - human review` with a
comment identifying the file that lost its changes.

## 4. Push

```
git push -u origin <BRANCH_NAME>
```

## 5. Create PR

Create a pull request using the template in `pr-template.md` (in the
`references/` directory of this plugin). Read that file for the exact format.

Always use `--body-file` with a **per-issue unique path** to avoid shell
injection and cross-feature collisions:
```
cat > /tmp/pr-body-<N>.md << 'PR_EOF'
<BODY>
PR_EOF
gh pr create --repo <OWNER/REPO> --title "<TITLE>" --body-file /tmp/pr-body-<N>.md --base stage
```

## 6. Code Review

Run `/code-review` (a built-in Claude Code skill) on the PR. This checks for:
- Security vulnerabilities
- Logic errors
- Performance issues
- Convention violations

## 7. Address Findings

If code review finds issues:
1. Fix each issue
2. Commit the fixes
3. Push to the same branch
4. Run `/code-review` again
5. Repeat until clean

## 8. Done

The PR is ready for merge. The feature-implementer will update the issue label
and move on to the next feature.
