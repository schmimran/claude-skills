# feature-creator

Automates feature development from GitHub issues through implementation. It plans, reviews for risk, implements, and opens PRs.

## Architecture

| Component | Type | Model | Description |
|-----------|------|-------|-------------|
| `feature-creator` | Command | (inherits) | Full pipeline: plan, review, implement, PR |
| `feature-planner` | Agent | sonnet | Fetch labeled issues, analyze repo, post implementation plans |
| `feature-reviewer` | Agent | sonnet | Review plans for risk, flag dangerous ones, create combined plan |
| `feature-implementer` | Agent | opus | Create branches, write code, run tests, open PRs |

The command orchestrates the three agents in sequence. Agents are not independently invocable — use the command to run the full pipeline.

## Pipeline Overview

```
GitHub Issues                    Pipeline                            Output
 labeled
"feature - ready       feature-planner agent                   Plan comments
 for claude"    ------> (analyze repo, create plans) -------> on each issue
                                    |
                             feature-reviewer agent
                        (risk assessment, combined plan) ---> High-risk flagged
                                    |                         for human review
                            feature-implementer agent
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
/feature-creator
```

Or specify a repository explicitly:

```
/feature-creator owner/repo
```

## Scheduling

The pipeline can be wrapped in a scheduled task for recurring automation:

```
Task ID: feature-pipeline
Cron: 0 9 * * 1-5 (weekdays at 9am)
Prompt: "Run /feature-creator <OWNER/REPO>"
```

Use the `/schedule` skill or `create_scheduled_task` tool to set this up.

## License

[MIT](../../LICENSE)
