# claude-skills

A Claude Code plugin that automates feature development from GitHub issues through implementation. It plans, reviews for risk, implements, and opens PRs — all from a single command.

## Installation

```bash
# Clone the repo
git clone https://github.com/schmimran/claude-skills.git ~/claude-skills

# Register the plugin in any project
claude plugins add ~/claude-skills
```

Updates propagate automatically via `git pull` in the cloned repo. No reinstallation needed.

## Available Skills

| Skill | Description | Usage |
|-------|-------------|-------|
| `feature-creator` | Full pipeline: plan, review, implement, PR | `/claude-skills:feature-creator` |
| `feature-planner` | Fetch labeled issues, analyze repo, post implementation plans | `/claude-skills:feature-planner` |
| `feature-reviewer` | Review plans for risk, flag dangerous ones, create combined plan | `/claude-skills:feature-reviewer` |
| `feature-implementer` | Create branches, write code, run tests, open PRs | `/claude-skills:feature-implementer` |

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

## Usage Examples

**Run the full pipeline:**
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

[MIT](LICENSE)
