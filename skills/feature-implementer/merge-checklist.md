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

## 3. Push

```
git push -u origin <BRANCH_NAME>
```

## 4. Create PR

Create a pull request using the template in `pr-template.md`. Read that file
for the exact format.

Always use `--body-file` to avoid shell injection from untrusted content:
```
cat > /tmp/pr-body.md << 'PR_EOF'
<BODY>
PR_EOF
gh pr create --repo <OWNER/REPO> --title "<TITLE>" --body-file /tmp/pr-body.md --base main
```

## 5. Code Review

Run `/code-review` (a built-in Claude Code skill) on the PR. This checks for:
- Security vulnerabilities
- Logic errors
- Performance issues
- Convention violations

## 6. Address Findings

If code review finds issues:
1. Fix each issue
2. Commit the fixes
3. Push to the same branch
4. Run `/code-review` again
5. Repeat until clean

## 7. Done

The PR is ready for merge. The feature-implementer will update the issue label
and move on to the next feature.
