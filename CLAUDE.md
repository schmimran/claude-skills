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
      feature-creator.md          # Orchestrator command — chains the agents across six phases (0-5)
    agents/
      feature-triager.md          # Agent (Phase 0): shared codebase exploration, bucket issues by predicted file overlap
      feature-planner.md          # Agent: plan every issue in a bucket together, posts per-issue plan comments
      feature-consolidator.md     # Agent: collect plans, cross-bucket conflict analysis
      feature-reviewer.md         # Agent: risk assessment, combined plan, review
      feature-implementer.md      # Agent: branch, code, test, PR
    references/
      triage-guide.md             # Bucketing heuristics, Jaccard overlap rule, max bucket size, singleton handling
      plan-template.md            # Template for plan comments (includes optional Bucket-mates section)
      consolidated-plan-template.md # Bucket-centric template for consolidated plan comments
      repo-analysis-guide.md      # What to look for in the target repo
      risk-criteria.md            # Risk rubric (HIGH/MEDIUM/LOW)
      review-checklist.md         # Instructions for the review subagent
      merge-checklist.md          # Pre-merge steps
      pr-template.md              # PR body template
    README.md                     # Plugin-specific documentation
  security-scanner/               # Plugin: multi-tool security audit for Node.js + Supabase
    .claude-plugin/
      plugin.json                 # Plugin manifest
    commands/
      security-scanner.md         # Orchestrator command — chains the five agents
    agents/
      security-runner.md          # Agent: install tools, run Node.js scans, emit JSON report
      security-supabase-auditor.md # Agent: query Supabase advisor API + scan migrations/config.toml
      security-triager.md         # Agent: fingerprint findings, file new issues, reopen closed on re-detection, skip duplicates
      security-closer.md          # Agent: close resolved findings
      security-advisor.md         # Agent: post expert advisory comments on filed/reopened issues
    references/
      fingerprint-spec.md         # SHA-256 fingerprint algorithm and storage format
      finding-severity-rubric.md  # Severity levels and override rules
      issue-template.md           # Template for filed GitHub Issues
      suppression-guide.md        # How to suppress false positives
      tool-install-guide.md       # Tool installation and failure handling
      supabase-audit-guide.md     # Supabase detection, advisor API, static scan rules
      supabase-rule-catalog.md    # Catalog of Supabase rules with severity + remediation
    README.md                     # Plugin-specific documentation
  docs-steward/                   # Plugin: docs maintenance pipeline (indexes → audit → edit → PR)
    .claude-plugin/
      plugin.json                 # Plugin manifest
    commands/
      docs-steward.md             # Orchestrator command — chains the six phases (0-5)
    agents/
      docs-file-cartographer.md   # Phase 0: annotated file tree with per-file purpose
      docs-symbol-indexer.md      # Phase 0: functions/classes/exports/types → symbols.json
      docs-route-mapper.md        # Phase 0: HTTP routes + CLI + slash commands + public exports
      docs-config-cataloger.md    # Phase 0: env vars + config files + schemas (with referenced flag)
      docs-inventory.md           # Phase 0: every doc file with stated purpose + claims
      docs-history-reconciler.md  # Phase 0: last-90d git history by area with likely doc impact
      docs-protected-extractor.md # Phase 0: extracts CLAUDE.md file-protection rules → protected-files.md
      docs-intent-auditor.md      # Phase 1: doc claims vs code reality
      docs-info-architect.md      # Phase 1: structure, section-README consistency, duplication, gaps
      docs-onboarding-reviewer.md # Phase 1: new-contributor walk through the docs
      docs-reference-validator.md # Phase 1: every intra-repo reference resolves
      docs-example-verifier.md    # Phase 1: code blocks still match the code
      docs-link-checker.md        # NOT in default pipeline: external URL checker (manual use only)
      docs-manual-reader.md       # Phase 4: walks edited corpus as a manual from the root README
      docs-deprecation-hunter.md  # Phase 1: orphan env/config/symbol/command refs → action=delete
      docs-consolidator.md        # Phase 2: merge findings, resolve duplication, emit edit plan or checkpoint
      docs-editor.md              # Phase 3 (and optional Phase 4 second pass): apply edits on a feature branch
      docs-final-reviewer.md      # Phase 5: tenet compliance, PR assembly, push, open PR
    references/
      tenets.md                   # The 8 core tenets (0-7) — loaded by every agent
      findings-schema.md          # Shared finding record shape (id, severity, action, location, tenet_refs, verification)
      claim-verification-protocol.md # Untrusted-docs posture + rigor modes (full/major/sampled) + unverifiable rule
      index-artifact-spec.md      # Format for each Phase 0 artifact
      readme-style-guide.md       # User-facing README voice, structure, link-out rules
      voice-guide.md              # Voice preservation rules for the editor
      checkpoint-criteria.md      # When the consolidator pauses for user adjudication
      manual-reader-protocol.md   # How the manual-reader walks the edited corpus (Phase 4)
      cache-layout.md             # /tmp/docs-steward-cache/ layout and lifecycle
      pr-template.md              # PR body template (sections: findings, deletions, requires-approval, residuals, tenets)
    README.md                     # Plugin-specific documentation
```

Each plugin lives under `plugins/<name>/` and is independently installable. Plugins use the **commands + agents** pattern: commands are user-invocable orchestrators, agents are specialized workers launched by commands.

## Plugin System

### Structure requirements

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
| `name` | Recommended | Slash command name (e.g., `feature-creator` → `/feature-creator`). Inferred from filename if omitted. |
| `description` | Yes | One-line summary shown in the `/` menu. Keep under 200 characters. |
| `argument-hint` | No | Shown during autocomplete (e.g., `"[repo-owner/repo-name]"`) |
| `disable-model-invocation` | No | Set `true` for commands with destructive side effects — prevents accidental auto-invocation |

### Dynamic Variables

- `$ARGUMENTS` — all arguments passed to the command
- `$0`, `$1`, etc. — specific arguments by index

## Agent Authoring Reference

### Agent Frontmatter

Agents live in `agents/*.md` and are specialized workers launched by commands:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Agent identifier, lowercase with hyphens |
| `description` | Yes | One-line summary of the agent's expertise. Keep under 200 characters. |
| `tools` | Yes | Comma-separated list of tools the agent can use |
| `model` | No | Model to run the agent on: `sonnet`, `opus`, `haiku` |
| `color` | No | UI color indicator: `red`, `yellow`, `green`, `blue` |
| `disable-model-invocation` | No | Set `true` for agents that should only be launched by their orchestrator command |

### Tool Access

Agents declare tool access with the `tools:` field. Common tool sets:
- Read-only analysis: `Glob, Grep, Read, WebSearch, TodoWrite`
- Full implementation: `Bash, Read, Write, Edit, Grep, Glob, Agent, TodoWrite`

### Guidelines

- Keep agent files focused — one agent, one responsibility
- Use `model: sonnet` for analysis/planning work, `model: opus` for code generation
- Commands launch agents via the `Agent` tool; agents are not independently invocable
- Move reference material to `references/` rather than embedding in agent files
- Use `--body-file` for all `gh` commands that pass issue titles, plan text, or error messages — never interpolate untrusted content into shell strings

## Conventions

- **Naming**: Directory names are lowercase with hyphens (e.g., `feature-creator`)
- **Issue interaction**: Plans are posted as comments, never by modifying the issue body
- **Branching**: One branch per feature (`feature/<number>-<slug>`), plus a release branch (`release/<YYYY-MM-DD>`) after all features
- **Commits**: Conventional commit format, referencing the issue number (e.g., `feat: add widget (#42)`)
- **Comment markers**: Plan comments are prefixed with `<!-- claude-feature-planner-v1 -->`, consolidated plans with `<!-- claude-feature-consolidator-v1 -->`, and combined reviewer plans with `<!-- claude-feature-reviewer-v1 -->`. Downstream agents use these markers to locate content programmatically. Always include the correct marker or extraction will fail.

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
- **Labels**: The target repository must have the five pipeline labels created. See the feature-creator plugin README for the setup commands.

## Build & Test Commands

No build or test commands. This is a pure-markdown plugin repository.

## Behavioral Rules for AI Contributors

These apply to every Claude Code session in this repo.

1. **Documentation targets.** When updating docs per the global documentation rule, this includes: CLAUDE.md schema tables, the root README plugin catalog, and each affected plugin's README.
2. **No silent additions.** Do not add new files, directories, or environment variables without stating what you are adding and why.
3. **Agent isolation.** Agents must not reference files outside their plugin directory. Each plugin must be independently installable.
4. **Shell safety.** Follow the `--body-file` rule in Agent Authoring Guidelines above — it applies to every plugin, not just feature-creator.
5. **Version sync.** When modifying an existing plugin, update `version` in both `plugin.json` and `marketplace.json` simultaneously — they must always match.
6. **New plugin completeness.** Do not create a new plugin directory without completing all 5 steps of the Adding a New Plugin checklist above.
7. **Issue body immutability.** The issue body is never modified. All communication (plans, risk assessments, error reports) happens via comments.
8. **Plan comment markers.** Always include the correct marker prefix (see Conventions above). Downstream agents will fail to locate comments if the marker is missing or wrong.
