# claude-skills

A Claude Code plugin marketplace. Install it once to get access to all plugins, with updates propagating automatically.

## Installation

```bash
/plugin marketplace add https://github.com/schmimran/claude-skills
```

## Available Plugins

| Plugin | Description | Docs |
|--------|-------------|------|
| [feature-creator](plugins/feature-creator/) | Feature development pipeline — GitHub issues to implementation plans to PRs | [README](plugins/feature-creator/README.md) |

## Adding a New Plugin

1. Create a directory under `plugins/<name>/` with:
   - `.claude-plugin/plugin.json` (plugin manifest)
   - `skills/` (skill definitions)
   - `README.md` (plugin documentation)
2. Register the plugin in `.claude-plugin/marketplace.json`
3. Update this table

See [CLAUDE.md](CLAUDE.md) for full conventions and the plugin onboarding checklist.

## License

[MIT](LICENSE)
