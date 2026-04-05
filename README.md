# claude-skills

A personal collection of reusable [Claude Code](https://claude.ai/code) skills, structured as a plugin repository. Install once, use everywhere, update via `git pull`.

## Installation

```bash
# Clone the repo (one-time setup)
git clone https://github.com/schmimran/claude-skills.git ~/claude-skills

# In any project, register the plugin
claude plugins add ~/claude-skills
```

All skills in the `skills/` directory are automatically discovered.

## Available Skills

| Skill | Description |
|-------|-------------|
| `daily-code-scrub` | Daily maintenance pass — linting, dependency checks, dead code removal |
| `feature-creator` | Multi-agent workflow: GitHub issue to plan to review to implementation |

### feature-creator Sub-skills

| Stage | Skill | Description |
|-------|-------|-------------|
| 1 | `feature-creator-planning` | Analyze GitHub issue and create implementation plan |
| 2 | `feature-creator-reviewing` | Review plan against project architecture |
| 3 | `feature-creator-implementing` | Execute plan, write code, open PR |

## Usage

```
/daily-code-scrub
/feature-creator 42
```

## Creating New Skills

1. Create a directory under `skills/` with a hyphenated lowercase name
2. Add a `SKILL.md` with YAML frontmatter (`name`, `description` at minimum)
3. Keep `SKILL.md` under 500 lines — use supporting files for additional detail
4. See [CLAUDE.md](CLAUDE.md) for full authoring conventions

## How Updates Work

This repo is installed as a plugin via a local path. When you `git pull` in the cloned repo, every project using the plugin picks up the changes on the next invocation. No reinstallation needed.

## License

[MIT](LICENSE)
