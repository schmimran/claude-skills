# feature-creator

Automates feature development end-to-end. Point it at a GitHub repository, label your issues, and it will analyze your codebase, write implementation plans, assess risk, write the code, open pull requests, and — if you give it the go-ahead — merge and clean up. Human input is only required when the pipeline flags something as high-risk.

## Quick Start

1. **Install the marketplace** (once per machine):
   ```bash
   /plugin marketplace add https://github.com/schmimran/claude-skills
   ```

2. **Create the required labels** on your target repository (once per repo):
   ```bash
   gh label create "feature - ready for claude" --color 0E8A16 --description "Scoped and ready for automated planning"
   gh label create "feature - planned" --color 1D76DB --description "Implementation plan posted as comment"
   gh label create "feature - human review" --color D93F0B --description "Flagged for human review (high-risk or failed)"
   gh label create "feature - in progress" --color FBCA04 --description "Branch created, implementation underway"
   gh label create "feature - complete" --color 0E8A16 --description "PR created and code-reviewed"
   ```

3. **Label one or more issues** with `feature - ready for claude`.

4. **Run the pipeline** from a Claude Code session in or targeting your repo:
   ```
   /feature-creator owner/repo
   ```
   Or, if your current directory is already the target repo:
   ```
   /feature-creator
   ```

5. **Watch the output.** The pipeline prints a live summary as each phase completes. When it finishes, you'll see a table of every issue with its planning status, risk level, implementation result, and PR link. By default, the pipeline pauses before merging the release branch and asks for your confirmation. Pass `--auto-merge` to skip the pause.

## Prerequisites

1. **GitHub CLI** must be installed and authenticated:
   ```bash
   gh auth status
   ```

2. **Labels** must exist on the target repository (see step 2 in Quick Start above).

## Architecture

| Component | Type | Model | Description |
|-----------|------|-------|-------------|
| `feature-creator` | Command | (inherits) | Full pipeline: plan, consolidate, review, implement, merge, clean up |
| `feature-planner` | Agent | sonnet | Analyze a single issue and post an implementation plan |
| `feature-consolidator` | Agent | sonnet | Collect individual plans, check consistency, create consolidated plan |
| `feature-reviewer` | Agent | sonnet | Review plans for risk, flag dangerous ones, create combined plan |
| `feature-implementer` | Agent | opus | Create branches, write code, run tests, open PRs |

The command orchestrates the four agents. Planner agents run in parallel (one per issue); all other agents run sequentially. Agents are not independently invocable — use the command to run the full pipeline.

## Pipeline

```
GitHub Issues                    Pipeline                            Output
 labeled
"feature - ready       feature-planner agents (parallel)        Plan comments
 for claude"    ------> (one per issue, analyze & plan) ------> on each issue
                                    |
                          feature-consolidator agent
                        (collect plans, consistency       ----> Consolidated plan
                         review, holistic plan)                 on each issue
                                    |
                             feature-reviewer agent
                        (risk assessment, combined plan) -----> High-risk flagged
                                    |                           for human review
                            feature-implementer agent
                        (branch, code, test, PR) ------------> Pull requests
                                    |                           opened
                              Merge & cleanup
                        (feature PRs → release PR) ----------> Merged + branches
                                                               deleted
```

The pipeline moves through five phases:

**Phase 1 — Planning**: The orchestrator gathers repository context once, then launches one planner agent per issue **in parallel**. Each planner receives the repo context and a single issue, explores the affected code, and posts a structured implementation plan as a comment. Issues that are too vague or reference non-existent files are flagged for human review.

**Phase 2 — Consolidation**: The consolidator agent collects all individual plans, analyzes them holistically for conflicts, missing dependencies, redundant work, and architectural inconsistencies. It produces a consolidated plan with a dependency graph, suggested implementation order, and cross-cutting concerns. Before posting, it performs a final review of the consolidated plan for internal consistency.

**Phase 3 — Review**: The reviewer agent reads each plan and the consolidated plan, scores features against a risk rubric, and flags anything high-risk for human review. For approved features, it builds on the consolidator's analysis to produce a combined plan with final implementation order and conflict notes.

**Phase 4 — Implementation**: The implementer agent works through approved features one at a time. For each: it creates a branch, writes the code, runs tests (with up to 3 retry attempts), follows the merge checklist (`/simplify` + `/code-review`), and opens a PR.

**Phase 5 — Merge and Cleanup**: Feature PRs are merged in implementation order. The release branch PR is created linking all features. By default, the pipeline pauses here for your confirmation before merging the release branch. Pass `--auto-merge` to skip the pause. After merge, it deletes all feature branches (local and remote), pulls main, and removes any worktree.

### Label Lifecycle

```
ready for claude  -->  planned  -->  in progress  -->  complete
                          |               |
                   [reviewer: risky]  [impl failed]
                          |               |
                          +-> human review <-+
```

| Label | Set by | Meaning |
|-------|--------|---------|
| `feature - ready for claude` | Human | Issue is scoped and ready for automated planning |
| `feature - planned` | feature-planner agent | Plan posted as issue comment |
| `feature - human review` | feature-consolidator, feature-reviewer, or feature-implementer agent | Flagged as high-risk, blocking inconsistency, or implementation failed |
| `feature - in progress` | feature-implementer agent | Branch created, coding underway |
| `feature - complete` | feature-implementer agent | PR created and code-reviewed |

## Pausing Before Merge

By default, the pipeline pauses after merging all feature PRs and creating the release branch PR. It prints the release PR link and asks for your confirmation before merging. This gives you a final review opportunity before the changes land on main.

To skip the pause and run the full pipeline end-to-end without stopping, pass `--auto-merge`:

```
/feature-creator owner/repo --auto-merge
```

In autonomous mode, feature PRs are merged in implementation order, the release branch is merged, branches are deleted, and the session is cleaned up — all without prompting. Use this for scheduled runs or when you're confident in the pipeline's output.

In either mode, features flagged as high-risk during Phase 3 (or flagged for blocking inconsistencies during Phase 2) are never automatically merged — they always require human intervention.

## Batch Size and Concurrency

The pipeline warns if more than 5 issues are labeled `feature - ready for claude` at once. This warning is **advisory only** — agents will process all of them (up to 20 per run). To limit a batch, manually remove the trigger label from lower-priority issues before running.

**Do not run multiple instances against the same repository simultaneously.** This pipeline is single-operator tooling.

## Error Recovery

If the pipeline crashes or is interrupted while an issue is labeled `feature - in progress`, that issue will be skipped on the next run (agents only query for `feature - planned`). To recover:

```bash
gh issue edit <NUMBER> --remove-label "feature - in progress" --add-label "feature - planned"
```

Then delete the orphaned branch if one was created:

```bash
git branch -D feature/<NUMBER>-<slug>
git push origin --delete feature/<NUMBER>-<slug>
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

## Development Notes

To test changes to agents or commands locally without installing from GitHub:

```bash
# Load the plugin directly from your local checkout
claude --plugin-dir /path/to/claude-skills/plugins/feature-creator

# The command is then available as:
/feature-creator
```

**Plan comment markers**: Plans posted by the planner begin with `<!-- claude-feature-planner-v1 -->`, consolidated plans from the consolidator begin with `<!-- claude-feature-consolidator-v1 -->`, and combined plans from the reviewer begin with `<!-- claude-feature-reviewer-v1 -->`. These markers are how downstream agents locate the right comment programmatically. If you modify the plan format, update the marker version and update the extraction logic in the relevant agent.

For plugin structure conventions, authoring reference, and the checklist for adding new plugins, see [CLAUDE.md](../../CLAUDE.md).

## License

[MIT](../../LICENSE)
