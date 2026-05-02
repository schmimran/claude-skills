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

Conventional commit type **must match the issue type**:

| Issue type | Commit type |
|------------|-------------|
| Feature (`feature - planned`) | `feat:` |
| Bug (`bug - planned`) | `fix:` |

Other conventional types (`refactor`, `test`, `docs`, `chore`) may be used
if the change genuinely matches one of those — but the issue type takes
precedence over secondary cleanup. A bug fix that also adds a test is still
`fix:`, not `test:`.

Example for a feature:
```
git commit -m "feat: add dark mode toggle to settings

Closes #42"
```

Example for a bug:
```
git commit -m "fix: await db.write before removing session in inactivity sweep

Closes #21"
```

## 3. Post-conflict diff verification

If you resolved any merge or rebase conflicts on this branch, you must confirm
that conflict resolution did not silently drop the feature's intended changes.

For every file listed as `Create` or `Modify` in the plan's "Affected Files"
table, run:

```
git diff origin/stage -- <planned-file>
```

Every planned `Create`/`Modify` file must show a non-empty diff. If any planned
file shows no diff, conflict resolution silently dropped the change — do not
push. Abort and escalate: label the issue per type (`feature - human review`
or `bug - human review`) with a comment identifying the file that lost its
changes.

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
