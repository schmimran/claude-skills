# feature-creator

Automates feature development and bug remediation end-to-end. Point it at a GitHub repository, label your issues (`feature - ready for claude` for features, `bug - ready for claude` for bug fixes — typically filed by [bug-sweeper](../bug-sweeper/)), and it will analyze your codebase, write implementation plans (with type-tuned templates), assess risk (with type-tuned rubrics), write the code, open pull requests, and — if you give it the go-ahead — merge and clean up. Human input is only required when the pipeline flags something as high-risk.

## Quick Start

1. **Install the marketplace** if you have not already: see [Installation in the root README](../../README.md#installation).

2. **Create the required labels** on your target repository (once per repo).

   **Feature state machine:**
   ```bash
   gh label create "feature - ready for claude" --color 0E8A16 --description "Scoped and ready for automated planning"
   gh label create "feature - planned" --color 1D76DB --description "Implementation plan posted as comment"
   gh label create "feature - human review" --color D93F0B --description "Flagged for human review (high-risk or failed)"
   gh label create "feature - in progress" --color FBCA04 --description "Branch created, implementation underway"
   gh label create "feature - complete" --color 0E8A16 --description "PR created and code-reviewed"
   ```

   **Bug state machine** (also used by [bug-sweeper](../bug-sweeper/)):
   ```bash
   gh label create "bug" --color d73a4a --description "Defect in the codebase"
   gh label create "bug - ready for claude" --color 0E8A16 --description "Bug ready for automated planning (typically filed by bug-sweeper)"
   gh label create "bug - triaged" --color 1D76DB --description "Triaged into a bucket; planner will pick it up"
   gh label create "bug - planned" --color 1D76DB --description "Implementation plan posted as comment"
   gh label create "bug - human review" --color D93F0B --description "Flagged for human review (high-risk or failed)"
   gh label create "bug - in progress" --color FBCA04 --description "Branch created, implementation underway"
   gh label create "bug - complete" --color 0E8A16 --description "PR created and code-reviewed"
   gh label create "bug - high" --color B60205 --description "High-severity bug — data loss, security, hot-path crash, partial commit"
   gh label create "bug - medium" --color D93F0B --description "Medium-severity bug — non-critical regression, leak, UI consistency"
   gh label create "bug - low" --color FBCA04 --description "Low-severity bug — cosmetic, doc drift, defensive-coding gap"
   ```

3. **Label one or more issues** with either `feature - ready for claude` (features) or `bug - ready for claude` (bugs).

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

| Component | Type | Model | Role |
|-----------|------|-------|------|
| `feature-creator` | Command | (inherits) | Full pipeline: triage, plan, consolidate, review, implement, merge, clean up |
| `feature-triager` | Agent | sonnet | Phase 0 — one shared codebase exploration pass, group issues into planning buckets by predicted file overlap |
| `feature-planner` | Agent | sonnet | Plan every issue in a bucket together, using the triager's shared context |
| `feature-consolidator` | Agent | sonnet | Collect individual plans, cross-bucket conflict analysis, consolidated plan |
| `feature-reviewer` | Agent | sonnet | Review plans for risk, flag dangerous ones, create combined plan |
| `feature-implementer` | Agent | opus | Create branches (`feature/<N>-<slug>` or `fix/<N>-<slug>`), write code, run tests, open PRs (`feat:` or `fix:`) |

The command orchestrates the five agents. The triager runs once up front; planner agents run in parallel (one per bucket); all other agents run sequentially. Agents are not independently invocable — use the command to run the full pipeline.

The triager separates feature buckets from bug buckets, and downstream
agents apply type-specific behavior:

| Concern | Feature path | Bug path |
|---------|--------------|----------|
| Plan template | [`references/plan-template.md`](references/plan-template.md) | [`references/bug-plan-template.md`](references/bug-plan-template.md) |
| Risk rubric | [`references/risk-criteria.md`](references/risk-criteria.md) | [`references/bug-risk-criteria.md`](references/bug-risk-criteria.md) |
| Review checklist | [`references/review-checklist.md`](references/review-checklist.md) | [`references/bug-review-checklist.md`](references/bug-review-checklist.md) |
| Branch prefix | `feature/<N>-<slug>` | `fix/<N>-<slug>` |
| Commit type | `feat:` | `fix:` |

Supporting reference docs live under `references/` — see [CLAUDE.md](../../CLAUDE.md#directory-structure) for the full list and purpose of each.

## Pipeline

```
GitHub Issues                    Pipeline                            Output
 labeled
"feature - ready          feature-triager agent                  Bucket manifest
 for claude"    ------>  (one shared exploration, ------> /tmp/feature-buckets-<TS>.json
                          group issues into buckets)           + triage comment
                                    |                            on each issue
                          feature-planner agents (parallel)
                        (one per bucket, plan together) ------> Plan comments
                                    |                           on each issue
                          feature-consolidator agent
                        (cross-bucket conflict analysis)  ----> Consolidated plan
                                    |                           on each issue
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

The pipeline moves through six phases, 0 through 5.

**Phase 0 — Triage**: The orchestrator captures a timestamp once and derives a run-scoped manifest path (`/tmp/feature-buckets-<TS>.json`). It launches the `feature-triager` agent, which fetches all trigger-labeled issues, runs **one shared codebase exploration pass**, predicts per-issue impacted globs, and groups issues into buckets by Jaccard overlap (≥ 1 shared glob). The manifest is written to the timestamped path and then validated by the orchestrator — if it is missing or malformed, the pipeline halts immediately. See `references/triage-guide.md` for the bucketing rules.

**Phase 1 — Planning**: The orchestrator launches one planner agent **per bucket** (not per issue), in parallel. Each planner reads the shared context and plans every issue in its bucket together, noting shared file edits and proposing a within-bucket ordering. Each plan is posted to its own issue via a per-issue temp file (`/tmp/plan-<N>.md`). Issues too vague to plan are flagged for human review.

**Phase 2 — Consolidation**: The consolidator agent reads the bucket manifest and collects all individual plans. Its analysis is scoped to **cross-bucket** concerns only — within-bucket file overlap was already resolved by each bucket-planner. It produces a bucket-centric consolidated plan with a dependency graph, suggested implementation order, and cross-cutting concerns. An explicit early-exit guard fires only for **true singleton runs** (exactly 1 bucket containing exactly 1 issue); it does NOT fire when one bucket contains multiple issues.

**Phase 3 — Review**: The reviewer agent reads each plan and the consolidated plan, scores features against a risk rubric, and flags anything high-risk for human review. For approved features, it builds on the consolidator's analysis to produce a combined plan with final implementation order and conflict notes.

**Phase 4 — Implementation**: The implementer agent works through approved features one at a time. For each: it creates a branch, writes the code, runs tests (with up to 3 retry attempts), follows the merge checklist (`/simplify` + `/code-review`), and opens a PR.

**Phase 5 — Merge and Cleanup**: Feature PRs are merged in implementation order. The release branch PR is created linking all features. By default, the pipeline pauses here for your confirmation before merging the release branch. Pass `--auto-merge` to skip the pause. After merge, it deletes all feature branches (local and remote), pulls main, and removes any worktree.

### Label Lifecycles

Two parallel state machines run side-by-side. The triager assigns each issue
a `type` (`feature` or `bug`) based on its trigger label and bucketing /
state transitions diverge from there.

**Features:**
```
ready for claude  -->  planned  -->  in progress  -->  complete
                          |               |
                   [reviewer: risky]  [impl failed]
                          |               |
                          +-> human review <-+
```

**Bugs** (one extra hop because `bug-sweeper` is the upstream filer):
```
ready for claude  -->  triaged  -->  planned  -->  in progress  -->  complete
                                        |               |
                                 [reviewer: risky]  [impl failed]
                                        |               |
                                        +-> human review <-+
```

| Label | Set by | Meaning |
|-------|--------|---------|
| `feature - ready for claude` | Human | Feature is scoped and ready for automated planning |
| `feature - planned` | feature-planner agent | Plan posted as issue comment |
| `feature - human review` | consolidator, reviewer, or implementer | Flagged as high-risk, blocking, or implementation failed |
| `feature - in progress` | feature-implementer agent | Branch created, coding underway |
| `feature - complete` | feature-implementer agent | PR created and code-reviewed |
| `bug - ready for claude` | bug-sweeper or human | Bug filed and ready for automated planning |
| `bug - triaged` | feature-triager agent | Bucketed; planner will pick it up |
| `bug - planned` | feature-planner agent (using `bug-plan-template.md`) | Plan posted as issue comment |
| `bug - human review` | consolidator, reviewer, or implementer | Flagged via `bug-risk-criteria.md`, blocking, or impl failed |
| `bug - in progress` | feature-implementer agent | Branch (`fix/<N>-<slug>`) created, coding underway |
| `bug - complete` | feature-implementer agent | PR (`fix:` commit) created and code-reviewed |
| `bug - high` / `bug - medium` / `bug - low` | bug-sweeper (or human) | Severity, applied at file time and preserved through the pipeline |

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

**Plan comment markers** are type-specific so downstream agents can locate the right comment programmatically:

| Stage | Feature marker | Bug marker |
|-------|----------------|------------|
| Triager | `<!-- claude-feature-triager-v1 -->` | `<!-- claude-feature-triager-v1 -->` (shared, since the triager handles both) |
| Planner | `<!-- claude-feature-planner-v1 -->` | `<!-- claude-bug-planner-v1 -->` |
| Consolidator | `<!-- claude-feature-consolidator-v1 -->` | `<!-- claude-bug-consolidator-v1 -->` |
| Reviewer | `<!-- claude-feature-reviewer-v1 -->` | `<!-- claude-bug-reviewer-v1 -->` |
| Bug-sweeper issue body (upstream) | n/a | `<!-- claude-bug-sweeper-v1 -->` |

If you modify the plan format, update the marker version and the extraction logic in the relevant agent.

For plugin structure conventions, authoring reference, and the checklist for adding new plugins, see [CLAUDE.md](../../CLAUDE.md).

## License

[MIT](../../LICENSE)
