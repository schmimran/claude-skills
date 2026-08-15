# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Claude Code plugin **marketplace** containing reusable plugins. Install the marketplace once to get access to all plugins. Each plugin is self-contained under `plugins/` with its own manifest, commands, agents, and documentation.

## Directory Structure

```
.claude-plugin/
  marketplace.json                # Marketplace catalog — lists all plugins
plugins/
  feature-creator/                # Plugin: feature & bug-fix development pipeline (parallel state machines)
    .claude-plugin/
      plugin.json                 # Plugin manifest
    commands/
      feature-creator.md          # Orchestrator command — chains the agents across six phases (0-5); processes both feature and bug labels
    agents/
      feature-triager.md          # Agent (Phase 0): shared codebase exploration; buckets features and bugs separately by predicted file overlap
      feature-planner.md          # Agent: plan every issue in a bucket together using type-appropriate template
      feature-consolidator.md     # Agent: collect plans, cross-bucket conflict analysis (per type)
      feature-reviewer.md         # Agent: type-tuned risk assessment, combined plan, review
      feature-implementer.md      # Agent: type-aware branch (feature/<N>- or fix/<N>-), code, test, PR (feat: or fix:)
    references/
      triage-guide.md             # Bucketing heuristics + type-separation rule (features and bugs never share a bucket)
      plan-template.md            # Feature plan template (Bucket-mates optional)
      bug-plan-template.md        # Bug-fix plan template (requires Reproduction Steps, Root Cause, regression test)
      consolidated-plan-template.md # Bucket-centric template for consolidated plan comments
      repo-analysis-guide.md      # What to look for in the target repo
      repo-profile-spec.md        # `.claude/repo-profile.md` standard — branch policy, project roots, verification commands
      risk-criteria.md            # Feature risk rubric (HIGH/MEDIUM/LOW)
      bug-risk-criteria.md        # Bug-tuned risk rubric — different factors than features (some flip)
      review-checklist.md         # Review subagent checklist for feature plans
      bug-review-checklist.md     # Review subagent checklist for bug-fix plans (regression test required)
      merge-checklist.md          # Pre-merge steps with type-aware commit type (feat: vs fix:)
      pr-template.md              # PR body template (Root Cause section for bug fixes)
      release-pr-template.md      # Release PR body template for the release branch PR assembled in Phase 5c
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
  bug-sweeper/                    # Plugin: daily bug-discovery sweep, files issues for feature-creator to remediate
    .claude-plugin/
      plugin.json                 # Plugin manifest
    commands/
      bug-sweeper.md              # Orchestrator command — chains the six phases (0-6); supports --headless mode for routines
    agents/
      bug-sweeper-runner.md       # Phase 1: gh issue list + npm build + npm audit (parallel Bash)
      bug-sweeper-reviewer.md     # Phase 2: targeted code review of one directory (read-only — no Write/Edit)
      bug-sweeper-tracer.md       # Phase 2: end-to-end trace of one high-risk flow (read-only)
      bug-sweeper-reconciler.md   # Phase 3: classify open `bug` issues vs current code (still-open / fixed / docs-only)
      bug-sweeper-analyst.md      # Phase 4 + 5: false-positive filter, severity assignment, plan + self-review
      bug-sweeper-filer.md        # Phase 6: file each confirmed bug as a GitHub Issue with severity label
    references/
      bug-sweep-protocol.md       # End-to-end pipeline contract + global CLAUDE.md overrides for sweeps
      discovery-surface-guide.md  # How to locate API dir, web dir, hot-path entry on arbitrary Node.js repos
      false-positive-rubric.md    # Discard rules (D1–D9) the analyst applies to candidate findings
      severity-rubric.md          # HIGH/MEDIUM/LOW criteria for confirmed bugs
      bug-issue-template.md       # GitHub Issue body format with `<!-- claude-bug-sweeper-v1 -->` marker
      headless-mode.md            # What changes when `--headless` is passed (no plan mode, no AskUserQuestion)
    README.md                     # Plugin-specific documentation
  voice-forge/                    # Plugin: sent-mail voice analysis + personalized ghostwriting skill generator
    .claude-plugin/
      plugin.json                 # Plugin manifest
    commands/
      analyze-writing-voice.md    # Workflow 1: guide export → parse → analyze → verify quotes → findings doc
      build-ghostwriting-skill.md # Workflow 2: confirm-first → synthesize SKILL.md from findings
    agents/
      voice-parser.md             # Phase 1: discover archive formats, run parsers, merge, prove output
      voice-analyst.md            # Phase 2: run analyze_voice.py, interpret stats, write analyst JSON
      voice-example-reader.md     # Phase 3: select intentional examples, fan-out shard reading, verify quotes gate
      voice-findings-writer.md    # Phase 4: assemble findings doc from verified stats + quotes only
      voice-skill-builder.md      # Workflow 2: synthesize SKILL.md + voice-examples.md from findings
    references/
      lessons-learned.md          # 6 hard-won guardrails (export-first, prove-recount, verify-quotes, etc.)
      export-guide.md             # Step-by-step export instructions for Apple Mail, Outlook, Thunderbird, PST
      dataset-schema.md           # Field definitions for the JSON emitted by parsers; greeting/signoff enums
      findings-template.md        # Required structure for the voice findings markdown doc
      ghostwriting-skill-template.md # Required structure for the generated SKILL.md
    scripts/
      parse_mbox.py               # Apple Mail / Thunderbird .mbox → normalized dataset (stdlib only)
      parse_olm.py                # Outlook-for-Mac .olm (streamed, attachments skipped) → dataset
      analyze_voice.py            # Dataset → aggregate voice stats (results.txt)
      select_intentional.py       # Dataset → sharded candidate emails for careful reading
      verify_quotes.py            # Gate: confirms every quote exists verbatim in the dataset
    README.md                     # Plugin-specific documentation
  fullstack-mobile-feature/       # Plugin: supervisor-led multi-agent mobile feature dev (iOS + Android + backend)
    .claude-plugin/
      plugin.json                 # Plugin manifest
    commands/
      fullstack-mobile-feature.md # Supervisor orchestrator — intake, master plan, parallel impl, peer review, reconciliation, land
    agents/
      ios-developer.md            # iOS dev (SwiftUI/MVVM) — dual mode: implement | peer-review
      android-developer.md        # Android dev (Kotlin/Compose/Hilt) — dual mode: implement | peer-review
    references/
      discovery-surface-guide.md  # How to locate iOS/Android/backend/contract/parity surfaces on any repo
      project-fit-spec.md         # Per-repo fit file format, consent rule, project memory schema
      master-plan-template.md     # Supervisor's plan template (data model + UX spec + API interaction spec)
      platform-brief-template.md  # Per-platform dev brief (shared contract + platform-specific guidance)
      completion-report-template.md # Developer completion-report format
      peer-review-template.md     # Two-part review: feedback for peer + self-reflection/convergence verdict
      reconciliation-rubric.md    # Priority order and decision matrix for Phase 6 reconciliation
      parity-guardrails.md        # Rules for honoring the parity registry (match behavior, not implementation)
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
- **Branching**: One branch per change, based on the integration branch — `feature/<number>-<slug>` for features, `fix/<number>-<slug>` for bug fixes — plus a single release branch (`release/<YYYY-MM-DD>`) after all branches are implemented. In *this* repo the integration branch is `stage`. In a *target* repo it is resolved from an explicit flag or that repo's committed `.claude/repo-profile.md` — **never** by parsing prose out of a CLAUDE.md. An earlier version of feature-creator scraped this very sentence with a regex; it broke on every repo that did not happen to contain the phrase. Do not reintroduce prose-derived branch names.
- **Commits**: Conventional commit format, referencing the issue number. `feat: add widget (#42)` for features, `fix: prevent crash on logout (#21)` for bugs.
- **Comment markers**: Used by downstream agents to locate content. Always include the correct marker — extraction will fail otherwise.

| Stage | Feature marker | Bug marker |
|-------|----------------|------------|
| Triager | `<!-- claude-feature-triager-v1 -->` | (shared — same triager handles both) |
| Planner | `<!-- claude-feature-planner-v1 -->` | `<!-- claude-bug-planner-v1 -->` |
| Consolidator | `<!-- claude-feature-consolidator-v1 -->` | `<!-- claude-bug-consolidator-v1 -->` |
| Reviewer | `<!-- claude-feature-reviewer-v1 -->` | `<!-- claude-bug-reviewer-v1 -->` |
| Bug-sweeper issue body | n/a | `<!-- claude-bug-sweeper-v1 -->` |

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

- **`gh` CLI**: Must be installed and authenticated (`gh auth status`).
- **Labels**: Each plugin that files or reads GitHub Issues requires its own label set on the target repository. See the Quick Start section of each plugin's README for the `gh label create` commands.

| Plugin | Labels it defines |
|--------|-------------------|
| feature-creator | Feature state machine: `feature - ready for claude`, `feature - planned`, `feature - human review`, `feature - in progress`, `feature - complete`. Bug state machine (shared with bug-sweeper): `bug`, `bug - ready for claude`, `bug - triaged`, `bug - planned`, `bug - human review`, `bug - in progress`, `bug - complete`, `bug - high`, `bug - medium`, `bug - low`. |
| bug-sweeper | Files issues with `bug`, `bug - ready for claude`, and one of the severity labels (`bug - high|medium|low`) — all defined in feature-creator's set; bug-sweeper does not introduce its own labels |
| security-scanner | Security state machine (its own, shared with no other plugin): `security`, `security - ready for claude`, `security - suppressed`, `security - human review` |

Where label names are shared across plugins (notably `feature - ready for claude` and the entire `bug - *` set), the colors and descriptions in feature-creator's README are canonical — use those when creating labels.

### Security findings do not auto-route to an implementer

security-scanner owns a separate label set and never files under `feature - ready for claude`. It runs unattended with no approval gate, so routing its output into feature-creator's pickup queue would take unreviewed findings straight through plan → branch → code → PR with no human in between.

**A human sits between scan and implementation.** feature-creator's triager excludes any issue carrying the `security` label unless invoked with `--include-security`, and reports how many it excluded. Security findings reach an implementer only when a human has reviewed them and deliberately routed them there.

When adding a new plugin that files issues, give it its own `<type> - ready for claude` label rather than borrowing another plugin's. Sharing a pickup label couples two pipelines' trigger conditions.

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
