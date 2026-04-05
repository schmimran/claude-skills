# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Claude Code skills plugin repository. Install as a plugin to gain access to reusable skills across multiple machines and projects. Skills are updated centrally and propagated via `git pull`.

## Directory Structure

```
.claude-plugin/
  plugin.json                     # Plugin manifest (required)
skills/
  <skill-name>/
    SKILL.md                      # Required — skill definition with YAML frontmatter
    template.md                   # Optional — output templates
    reference.md                  # Optional — detailed reference material
    examples/                     # Optional — example inputs/outputs
    scripts/                      # Optional — helper scripts
```

Multi-stage skills use a flat layout with a shared prefix (e.g., `feature-creator/`, `feature-creator-planning/`, `feature-creator-reviewing/`). The parent skill acts as an orchestrator and may contain supporting `.md` files for its sub-skills.

## Skill Authoring Conventions

### Naming
- Directory names: lowercase with hyphens (e.g., `daily-code-scrub`)
- Prefer gerund form for action-oriented skills (e.g., `code-reviewing`)
- Use descriptive noun-phrases for task-oriented skills (e.g., `daily-code-scrub`)
- Multi-stage sub-skills share a prefix: `<parent>-<stage>` (e.g., `feature-creator-planning`)

### SKILL.md Format
Every skill requires a `SKILL.md` with YAML frontmatter:

```yaml
---
name: skill-name                  # Required — matches directory name
description: What the skill does  # Required — one-line summary
argument-hint: "<args>"           # Optional — shown during autocomplete
allowed-tools: Tool1, Tool2       # Optional — tools the skill can use
context: fork                     # Optional — run in isolated subagent
agent: Plan                       # Optional — subagent type (Explore, Plan, general-purpose)
---
```

### Guidelines
- Keep SKILL.md under 500 lines; move detail into supporting files
- Skills are discovered **one level deep** under `skills/` — do not nest skill directories
- Supporting files (`.md`, scripts) inside a skill directory are loaded on-demand, not as separate skills
- Test changes by editing SKILL.md and re-invoking — no restart needed

## Build & Test Commands

No build or test commands. This is a pure-markdown skills repository.
