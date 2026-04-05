# feature-creator

Automates feature development from GitHub issues through implementation. It plans, reviews for risk, implements, and opens PRs.

## Skills

| Skill | Description |
|-------|-------------|
| `feature-creator` | Full pipeline: plan, review, implement, PR |
| `feature-planner` | Fetch labeled issues, analyze repo, post implementation plans |
| `feature-reviewer` | Review plans for risk, flag dangerous ones, create combined plan |
| `feature-implementer` | Create branches, write code, run tests, open PRs |

Each skill can be run independently or chained via the `feature-creator` orchestrator.

## Pipeline Overview

```
GitHub Issues                    Skills Pipeline                     Output
 labeled
"feature - ready       feature-planner                        Plan comments
 for claude"    ------> (analyze repo, create plans) -------> on each issue
                                    |
                              feature-reviewer
                        (risk assessment, combined plan) ---> High-risk flagged
                                    |                         for human review
                             feature-implementer
                        (branch, code, test, PR) ----------> Pull requests
                                    |                         opened
                              Release branch
                        (links all feature PRs) ------------> Integration PR
```

### Label Lifecycle

```
ready for claude  -->  planned  -->  in progress  -->  complete
                          |               |
                   [reviewer: risky]  [impl failed]
                          |               |
                          +-> human review <-+
```

## Prerequisites

1. **GitHub CLI** must be installed and authenticated:
   ```bash
   gh auth status
   ```

2. **Labels** must exist on the target repository. Run these once per repo:
   ```bash
   gh label create "feature - ready for claude" --color 0E8A16 --description "Scoped and ready for automated planning"
   gh label create "feature - planned" --color 1D76DB --description "Implementation plan posted as comment"
   gh label create "feature - human review" --color D93F0B --description "Flagged for human review (high-risk or failed)"
   gh label create "feature - in progress" --color FBCA04 --description "Branch created, implementation underway"
   gh label create "feature - complete" --color 0E8A16 --description "PR created and code-reviewed"
   ```

## Usage

After installing the `claude-skills` marketplace:

```
/claude-skills:feature-creator
```

**Plan features only** (useful for reviewing plans before implementation):
```
/claude-skills:feature-planner
```

**Implement already-planned features** (skip planning and review):
```
/claude-skills:feature-implementer
```

## License

[MIT](../../LICENSE)
