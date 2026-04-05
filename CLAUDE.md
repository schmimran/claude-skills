# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Claude Code plugin **marketplace** containing reusable plugins. Install the marketplace once to get access to all plugins. Each plugin is self-contained under `plugins/` with its own manifest, commands, agents, and documentation.

## Directory Structure

```
.claude-plugin/
  marketplace.json                # Marketplace catalog — lists all plugins
plugins/
  feature-creator/                # Plugin: feature development pipeline
    .claude-plugin/
      plugin.json                 # Plugin manifest
    commands/
      feature-creator.md          # Orchestrator command — chains the three agents
    agents/
      feature-planner.md          # Agent: fetch issues, analyze repo, post plans
      feature-reviewer.md         # Agent: risk assessment, combined plan, review
      feature-implementer.md      # Agent: branch, code, test, PR
    references/
      plan-template.md            # Template for plan comments
      repo-analysis-guide.md      # What to look for in the target repo
      risk-criteria.md            # Risk rubric (HIGH/MEDIUM/LOW)
      review-checklist.md         # Instructions for the review subagent
      merge-checklist.md          # Pre-merge steps
      pr-template.md              # PR body template
    README.md                     # Plugin-specific documentation
```

Each plugin lives under `plugins/<name>/` and is independently installable. Plugins use the **commands + agents** pattern: commands are user-invocable orchestrators, agents are specialized workers launched by commands.

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
| `feature - planned` | feature-planner agent | Plan posted as issue comment |
| `feature - human review` | feature-reviewer or feature-implementer agent | Flagged as high-risk or implementation failed |
| `feature - in progress` | feature-implementer agent | Branch created, coding underway |
| `feature - complete` | feature-implementer agent | PR created and code-reviewed |

### Plan Comments

Plans are posted as **comments** on the issue (the issue body is never modified). Every plan comment is prefixed with `<!-- claude-feature-planner-v1 -->` so downstream agents can locate it programmatically.

### Error Handling Pattern

When any agent encounters a failure for a specific issue:
1. Post a comment on the issue explaining the error
2. Change the label to `feature - human review`
3. Continue processing remaining issues

### Stuck State Recovery

If an agent crashes or is interrupted while a feature is labeled `feature - in progress`, that issue will be skipped on the next run (since agents query for `feature - planned`, not `feature - in progress`). To recover, manually relabel the stuck issue:
```
gh issue edit <NUMBER> --remove-label "feature - in progress" --add-label "feature - planned"
```
Then delete the orphaned branch if one was created.

### Batch Size

The orchestrator command warns when more than 5 issues are labeled `feature - ready for claude`, but this guard is **advisory only**. The agents each fetch up to 20 issues independently. If strict batch limiting is needed, manually control which issues carry the trigger label.

### Concurrency

This pipeline is single-operator tooling. Do not run multiple instances against the same repository simultaneously.

### Shell Safety

All `gh` commands that pass untrusted content (issue titles, plan text, error messages) must use `--body-file` instead of `--body` to prevent shell injection. Never interpolate issue content directly into shell command strings.

## Plugin Onboarding

### Plugin structure requirements

- Each plugin is a self-contained directory under `plugins/<name>/` with its own `.claude-plugin/plugin.json` and `README.md`
- Plugins use the **commands + agents** pattern: `commands/` for user-facing orchestrators, `agents/` for specialized workers, `references/` for supporting docs
- Plugin directory names must be lowercase with hyphens and match the `name` field in the plugin's `plugin.json`
- After adding a plugin, register it in `.claude-plugin/marketplace.json`

### Version management

- Each plugin tracks its own version in its `plugin.json`
- The `version` in `marketplace.json` entries must match the plugin's `plugin.json` version

### Plugin isolation

- Agents within a plugin can reference sibling files in `references/`
- Agents must NOT reference files outside their plugin's directory
- No shared code between plugins — each plugin is independently installable

### Adding a new plugin checklist

1. Create `plugins/<name>/` with `.claude-plugin/plugin.json`, `commands/`, `agents/`, and `references/`
2. Add a `README.md` in the plugin directory
3. Add an entry to `.claude-plugin/marketplace.json`
4. Update the root `README.md` plugin catalog table
5. Update the Directory Structure section above if the layout pattern changes

## Command Authoring Reference

### Command Frontmatter

Commands live in `commands/*.md` and are user-invocable orchestrators:

| Field | Required | Description |
|-------|----------|-------------|
| `description` | Yes | One-line summary shown in the `/` menu |
| `argument-hint` | No | Shown during autocomplete (e.g., `"[repo-owner/repo-name]"`) |

### Dynamic Variables

- `$ARGUMENTS` — all arguments passed to the command
- `$0`, `$1`, etc. — specific arguments by index

## Agent Authoring Reference

### Agent Frontmatter

Agents live in `agents/*.md` and are specialized workers launched by commands:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Agent identifier, lowercase with hyphens |
| `description` | Yes | One-line summary of the agent's expertise |
| `tools` | Yes | Comma-separated list of tools the agent can use |
| `model` | No | Model to run the agent on: `sonnet`, `opus`, `haiku` |
| `color` | No | UI color indicator: `red`, `yellow`, `green`, `blue` |

### Tool Access

Agents declare tool access with the `tools:` field. Common tool sets:
- Read-only analysis: `Glob, Grep, Read, WebSearch, TodoWrite`
- Full implementation: `Bash, Read, Write, Edit, Grep, Glob, Agent, TodoWrite`

### Guidelines

- Keep agent files focused — one agent, one responsibility
- Use `model: sonnet` for analysis/planning work, `model: opus` for code generation
- Commands launch agents via the `Agent` tool; agents are not independently invocable
- Move reference material to `references/` rather than embedding in agent files

## Conventions

- **Naming**: Directory names are lowercase with hyphens (e.g., `feature-creator`)
- **Issue interaction**: Plans are posted as comments, never by modifying the issue body.
- **Branching**: One branch per feature (`feature/<number>-<slug>`), plus a release branch after all features.
- **Max batch size**: The orchestrator warns when more than 5 features are queued, but the guard is advisory only.

## Local Development

```bash
# Add the marketplace during development
/plugin marketplace add /path/to/claude-skills

# Or test a single plugin directly
claude --plugin-dir /path/to/claude-skills/plugins/feature-creator

# The command is available as:
/feature-creator

# After editing any command or agent file, re-invoke — no restart needed
```

## Prerequisites

- **`gh` CLI**: Must be installed and authenticated (`gh auth status`)
- **Labels**: The target repository must have these labels created (see the feature-creator plugin README for setup commands):
  - `feature - ready for claude`
  - `feature - planned`
  - `feature - human review`
  - `feature - in progress`
  - `feature - complete`

## Build & Test Commands

No build or test commands. This is a pure-markdown plugin repository.


## Behavioral rules for AI contributors

These apply to every Claude Code session in this repo.

1. **Documentation targets.**  When updating docs per the global documentation rule, this includes: CLAUDE.md schema tables, the root README plugin catalog, and each affected plugin's README.
2. **No silent additions.**  Do not add new files, directories, or environment variables without stating what you are adding and why.
