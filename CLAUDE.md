# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Claude Code plugin containing the **feature-creator** pipeline. It automates the flow from GitHub issues to implementation plans to reviewed code to pull requests. Install as a plugin, update via `git pull`.

## Directory Structure

```
.claude-plugin/
  plugin.json                     # Plugin manifest (required)
skills/
  feature-creator/
    SKILL.md                      # Orchestrator — chains the three phases
  feature-planner/
    SKILL.md                      # Phase 1: fetch issues, analyze repo, post plans
    plan-template.md              # Template for plan comments
    repo-analysis-guide.md        # What to look for in the target repo
  feature-reviewer/
    SKILL.md                      # Phase 2: risk assessment, combined plan, review
    risk-criteria.md              # Risk rubric (HIGH/MEDIUM/LOW)
    review-checklist.md           # Instructions for the review subagent
  feature-implementer/
    SKILL.md                      # Phase 3: branch, code, test, PR
    merge-checklist.md            # Pre-merge steps
    pr-template.md                # PR body template
```

Skills are discovered **one level deep** under `skills/`. Supporting `.md` files inside a skill directory are loaded on-demand, not as separate skills.

## Feature-Creator Pipeline

### Label Lifecycle

```
[human]               [planner]          [implementer]        [implementer]
ready for claude  -->  planned  -------->  in progress  ------->  complete
                          |                     |
                   [reviewer: risky]     [impl failed]
                          |                     |
                          +-->  human review  <-+
```

| Label | Set by | Meaning |
|-------|--------|---------|
| `feature - ready for claude` | Human | Issue is scoped and ready for automated planning |
| `feature - planned` | feature-planner | Plan posted as issue comment |
| `feature - human review` | feature-reviewer or feature-implementer | Flagged as high-risk or implementation failed |
| `feature - in progress` | feature-implementer | Branch created, coding underway |
| `feature - complete` | feature-implementer | PR created and code-reviewed |

### Plan Comments

Plans are posted as **comments** on the issue (the issue body is never modified). Every plan comment is prefixed with `<!-- claude-feature-planner-v1 -->` so downstream skills can locate it programmatically.

### Error Handling Pattern

When any skill encounters a failure for a specific issue:
1. Post a comment on the issue explaining the error
2. Change the label to `feature - human review`
3. Continue processing remaining issues

### Concurrency

This pipeline is single-operator tooling. Do not run multiple instances against the same repository simultaneously.

## Skill Authoring Reference

### SKILL.md Frontmatter

Every skill requires a `SKILL.md` with YAML frontmatter:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Skill identifier, lowercase with hyphens, matches directory name |
| `description` | Yes | One-line summary. Claude uses this to decide when to auto-invoke. Front-load the use case. |
| `argument-hint` | No | Shown during autocomplete (e.g., `"[repo-owner/repo-name]"`) |
| `allowed-tools` | No | Tools the skill can use without per-use permission |
| `context` | No | Set to `fork` to run in an isolated subagent |
| `agent` | No | Subagent type when `context: fork` is set: `Explore`, `Plan`, or `general-purpose` |
| `disable-model-invocation` | No | `true` to prevent Claude from auto-invoking (use for side-effect operations) |
| `user-invocable` | No | `false` to hide from `/` menu (use for background knowledge) |
| `model` | No | Override model for this skill (`sonnet`, `opus`, `haiku`) |
| `effort` | No | Override effort level: `low`, `medium`, `high`, `max` |
| `paths` | No | Glob patterns to auto-activate only when working with matching files |

### Tool Restrictions

Restrict Bash access with pattern syntax: `Bash(gh *)` allows only `gh` commands. Full `Bash` grants unrestricted shell access.

### Dynamic Variables

- `$ARGUMENTS` — all arguments passed to the skill
- `$0`, `$1`, etc. — specific arguments by index
- `${CLAUDE_SKILL_DIR}` — path to the skill's directory

### Guidelines

- Keep SKILL.md under 500 lines; move detail into supporting files
- Do not nest skill directories under `skills/`
- Test changes by editing SKILL.md and re-invoking (no restart needed)
- Use `context: fork` + `agent: Explore` for read-only research tasks
- Use `context: fork` + `agent: Plan` for planning tasks that should not modify files

## Conventions

- **Naming**: Directory names are lowercase with hyphens (e.g., `feature-planner`)
- **Multi-stage skills**: Use a flat layout with shared prefix. Each stage is independently invocable.
- **Issue interaction**: Plans are posted as comments, never by modifying the issue body.
- **Branching**: One branch per feature (`feature/<number>-<slug>`), plus a release branch after all features.
- **Max batch size**: The orchestrator processes at most 5 features per run.

## Local Development

```bash
# Test the plugin during development
claude --plugin-dir /path/to/claude-skills

# Individual skills are available as:
/claude-skills:feature-planner
/claude-skills:feature-reviewer
/claude-skills:feature-implementer
/claude-skills:feature-creator

# After editing any SKILL.md, re-invoke the skill — no restart needed
```

## Prerequisites

- **`gh` CLI**: Must be installed and authenticated (`gh auth status`)
- **Labels**: The target repository must have these labels created (see README for setup commands):
  - `feature - ready for claude`
  - `feature - planned`
  - `feature - human review`
  - `feature - in progress`
  - `feature - complete`

## Build & Test Commands

No build or test commands. This is a pure-markdown skills repository.
