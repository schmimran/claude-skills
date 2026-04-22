# claude-skills

A Claude Code plugin marketplace. Install it once to get access to all plugins, with updates propagating automatically.

## How It Works

Each plugin in this marketplace is a **slash command** backed by a set of specialized AI agents. You install the marketplace once, and every plugin becomes immediately available in your Claude Code sessions — no per-plugin installation needed. When a plugin is updated, you get the new version automatically on next use.

Plugins are self-contained: each lives in its own directory with its own agents, reference documents, and configuration. They don't share code with each other, so you can install the whole marketplace without worrying about interference between plugins.

## Installation

```bash
/plugin marketplace add https://github.com/schmimran/claude-skills
```

## Available Plugins

| Plugin | Version | Description | Docs |
|--------|---------|-------------|------|
| [feature-creator](plugins/feature-creator/) | 0.5.0 | Feature development pipeline — GitHub issues to implementation plans to PRs | [README](plugins/feature-creator/README.md) |
| [security-scanner](plugins/security-scanner/) | 0.4.0 | Multi-tool security audit for Node.js web apps and Supabase projects — files findings as GitHub Issues with deduplication, reopen on re-detection, and expert advisory comments | [README](plugins/security-scanner/README.md) |
| [docs-steward](plugins/docs-steward/) | 0.3.0 | Docs maintenance pipeline — builds canonical indexes of a repo, audits docs for drift, duplication, orphans, and onboarding gaps, then actively edits docs and opens a PR | [README](plugins/docs-steward/README.md) |

## What Each Plugin Does

**feature-creator** — Give it a GitHub repository and some labeled issues, and it handles the full development cycle automatically. It reads your codebase, writes a detailed implementation plan for each issue, checks whether each change is risky (and flags anything dangerous for human review), writes the code, runs your tests, opens pull requests, and — if you want — merges and cleans up. The only time it stops to ask is when it flags something as high-risk, or when you've asked it to pause before the final merge.

**security-scanner** — Runs a multi-tool security audit against a Node.js web app and, when present, its Supabase project. Files findings as labeled GitHub Issues, deduplicates by fingerprint so you don't get the same issue twice, reopens previously closed issues when a scan re-detects them, auto-closes resolved ones, and adds expert advisory comments with root-cause analysis on every new or reopened issue.

**docs-steward** — Brings documentation in line with what the code actually does. Builds canonical indexes of the repo (files, symbols, routes, config, doc inventory, glossary, recent history), runs eight critic personas in parallel to find drift, duplication, stale references, orphan config keys, and onboarding gaps, then actively edits the docs on a feature branch — deleting deprecated content, moving duplicated content to a single canonical home, and fixing stale claims. A manual-reader persona re-reads the edited corpus before opening a single PR. The PR is never auto-merged.

## Contributing a Plugin

See [CLAUDE.md](CLAUDE.md) for the plugin authoring conventions, structure requirements, and the step-by-step checklist for adding a new plugin.

## License

[MIT](LICENSE)
