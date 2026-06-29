# Project Fit File Spec

## What It Is

The project-fit file is a per-repo configuration file written into the **target repo** (not the plugin) at:

```
.claude/fullstack-mobile-feature/project-fit.md
```

It stores the discovered paths, conventions, and accumulated project memory for a specific repo so that future plugin runs can skip Phase 0 discovery entirely.

**Why it lives in the target repo:** Marketplace plugins install read-only under `~/.claude/plugins/cache/`, so per-repo state cannot live inside the plugin. The fit file lives in the target repo — it is committed with the project, shared with collaborators, and survives fresh clones.

---

## Consent Rule (Non-Negotiable)

The fit file is **never created or updated without explicit user consent**. The plugin must ask:

> "Would you like me to save these paths to `.claude/fullstack-mobile-feature/project-fit.md` for future runs? (yes/no)"

Only create or modify the file when the user answers "yes" (or clearly affirmative). Silence, "maybe", or no response = no. Do not create the directory or the file as a side effect of any other operation.

The same consent rule applies to appending project memory at Phase 7.

---

## File Format

```yaml
---
# fullstack-mobile-feature project-fit
# Managed by the fullstack-mobile-feature plugin. Edit with care.
# Created: YYYY-MM-DD

ios_root: iOS/MyApp/
ios_app_entry: iOS/MyApp/MyApp/MyAppApp.swift
android_root: Android/app/
android_app_entry: Android/app/src/main/java/com/example/app/MyApplication.kt
android_package: com.example.app
backend_root: api/
backend_entry: api/src/index.ts
backend_module_dir: api/src/modules/
typecheck_cmd: npm run typecheck
contract_doc: api/MOBILE_API.md
parity_registry: PLATFORM_PARITY.md
trunk: stage

ios_conventions:
  architecture: MVVM
  state_management: "@Observable / Combine"
  networking: URLSession via APIClient
  auth_storage: Keychain

android_conventions:
  architecture: MVVM + Repository
  di_framework: Hilt
  networking: Retrofit + OkHttp
  auth_storage: EncryptedSharedPreferences
  ui_state: StateFlow
---

## Project Memory

<!-- Append dated entries below. Never delete or overwrite existing entries. -->
```

---

## YAML Frontmatter Fields

| Field | Description |
|-------|-------------|
| `ios_root` | Relative path to iOS source root (directory containing `*.xcodeproj` or `*.xcworkspace`) |
| `ios_app_entry` | Relative path to the SwiftUI `@main` entry file |
| `android_root` | Relative path to Android app module root |
| `android_app_entry` | Relative path to the `Application` subclass |
| `android_package` | Base package name (e.g., `com.example.app`) |
| `backend_root` | Relative path to the backend root directory |
| `backend_entry` | Relative path to backend entry point (`app.ts`, `index.ts`, etc.) |
| `backend_module_dir` | Relative path to the modules or routes directory |
| `typecheck_cmd` | Command to run TypeScript type checking (e.g., `npm run typecheck`) |
| `contract_doc` | Relative path to the mobile API contract document |
| `parity_registry` | Relative path to the platform parity registry |
| `trunk` | The trunk branch name (e.g., `stage`) |
| `ios_conventions` | Key iOS architectural conventions observed in the codebase |
| `android_conventions` | Key Android architectural conventions observed in the codebase |

All paths are relative to the repo root. Use `not found` for fields that could not be discovered.

---

## Project Memory Format

Project memory entries are appended below the YAML frontmatter as dated markdown sections:

```markdown
### YYYY-MM-DD — <feature name>

**Patterns learned:**
- <pattern or convention observed this run>
- <another pattern>

**Gotchas:**
- <a non-obvious pitfall encountered>

**Decisions:**
- <an architectural or product decision made and why>
```

### Append-only rule

Existing project memory entries are **never overwritten or deleted**. Only append new entries at the end. The accumulation of entries is the value — it is a chronological project log.

### What belongs in project memory

Good candidates:
- Non-obvious architectural patterns (e.g., "shared API client is in `Core/Networking/` not `Features/`")
- Parity decisions made this run (e.g., "decided to use platform-native date formatting, not match iOS exactly")
- Gotchas that would trip up a future run (e.g., "Android module uses `sealed interface` for UI state, not sealed class")
- Contract doc update patterns (e.g., "contract doc uses JSDoc-style comments, not OpenAPI")

Do not include:
- Implementation details that belong in code comments
- Temporary workarounds that were fixed before landing
- Speculation about future features

---

## Stale Detection

When the fit file exists, Phase 0 spot-checks 3–4 key paths using `ls` before trusting it:
- `ios_root`, `android_root`, `backend_root`, `contract_doc`

If any path returns "no such file or directory": mark it stale, re-discover that surface, and offer to update the fit file (with consent).
