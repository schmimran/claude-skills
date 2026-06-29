# fullstack-mobile-feature

A Claude Code plugin for **supervisor-coordinated full-stack mobile feature development** across iOS + Android with a shared backend. One command drives intake, planning, parallel implementation, cross peer review, and reconciliation — landing everything on a single feature branch.

---

## What It Does

A single `/fullstack-mobile-feature` slash command acts as **Persona 1: the full-stack lead**. It:

1. **Discovers** the repo layout (iOS root, Android root, backend, contract doc, parity registry) or loads a cached project-fit file.
2. **Runs interactive intake** — asks clarifying questions until the feature is fully understood.
3. **Writes a master plan** including a visualized API interaction spec (sequence diagram + per-endpoint request/response shapes), then implements any backend API changes as the supervisor.
4. **Derives two platform-specific briefs** — one for iOS (SwiftUI/MVVM), one for Android (Kotlin/Compose/Hilt) — both referencing the same API contract.
5. **Launches ios-developer and android-developer in parallel** (implement mode) — they work independently on their respective directories, do not build or test, and return completion reports.
6. **Cross-reviews** — re-launches both developers in parallel (peer-review mode), each reviewing the other's diff and honestly reflecting on whether the peer's approach is better and should be adopted (up to recommending a full redo).
7. **Reconciles** — synthesizes all reports against a priority rubric (correctness → UX consistency → contract fidelity → code quality; sunk cost never factors in) and dispatches targeted fixes until both platforms are consistent and correct.
8. **Lands** — commits everything on one feature branch, optionally runs the backend typecheck, optionally appends project memory to the fit file, and stops. No PR, no mobile build.

---

## Quick Start

### Install

```bash
/plugin marketplace add /path/to/claude-skills
```

### First run

```bash
/fullstack-mobile-feature Add a notification preferences screen
```

On first run in a repo, the supervisor discovers your layout and offers to save a project-fit file. Say yes to skip discovery on future runs.

### Subsequent runs

The supervisor loads the fit file automatically and confirms paths before starting.

---

## Phases

| Phase | Name | What happens |
|-------|------|-------------|
| 0 | Fit & Discovery | Load or discover iOS/Android/backend/contract/parity paths |
| 1 | Intake | Interactive clarifying questions; supervisor confirms understanding |
| 2 | Master Plan + Backend | API interaction spec written; backend changes implemented; feature branch created |
| 3 | Platform Briefs | iOS and Android briefs derived from master plan |
| 4 | Parallel Implementation | ios-developer and android-developer implement in parallel |
| 5 | Cross Peer Review | Each developer reviews the other's diff + self-reflects on convergence |
| 6 | Reconciliation | Supervisor resolves parity gaps, bugs, and convergence proposals |
| 7 | Land | Commit, optional typecheck, optional fit file update, summary |

---

## Project-Fit File

The fit file is a per-repo configuration file stored at `.claude/fullstack-mobile-feature/project-fit.md` **in the target repo** (not the plugin). It stores:

- Discovered paths (iOS root, Android root, backend root, contract doc, parity registry, trunk branch)
- Platform conventions (SwiftUI architecture, Compose DI framework, networking layer, auth storage)
- Project memory: a chronological log of patterns, gotchas, and decisions accumulated across runs

**Consent rule:** The fit file is never created or updated without your explicit "yes." The supervisor asks before creating it (Phase 0) and before appending project memory (Phase 7).

**Why it lives in the target repo:** Plugin installations are read-only caches — per-repo state must live with the repo so it's committed, shared with collaborators, and durable across fresh clones.

See `references/project-fit-spec.md` for the full format.

---

## Agents

### ios-developer

Expert iOS developer (SwiftUI, MVVM, Combine, Keychain, URLSession, async/await). Operates in two modes:

- **implement** — builds the feature from the iOS brief; returns a completion report
- **peer-review** — reviews the Android diff; returns feedback for Android + honest self-reflection on whether to adopt Android's approach

### android-developer

Expert Android developer (Kotlin, Jetpack Compose, Hilt, Retrofit, EncryptedSharedPreferences, StateFlow). Same dual-mode structure, reversed direction.

Both agents are `disable-model-invocation: true` — they are launched only by the supervisor command.

---

## References

| File | Purpose |
|------|---------|
| `discovery-surface-guide.md` | How to locate iOS/Android/backend/contract/parity surfaces on any repo |
| `project-fit-spec.md` | Fit file format, consent rule, project memory schema |
| `master-plan-template.md` | Supervisor's plan template (includes API interaction spec) |
| `platform-brief-template.md` | Per-platform brief template (iOS and Android variants) |
| `completion-report-template.md` | Developer completion report format |
| `peer-review-template.md` | Two-part peer review: feedback for peer + self-reflection/convergence |
| `reconciliation-rubric.md` | Priority order and decision matrix for Phase 6 reconciliation |
| `parity-guardrails.md` | Rules for honoring the parity registry (match behavior, not implementation) |

---

## Limitations

- **No PR is created.** The supervisor lands the branch and stops. Create your PR manually.
- **No mobile builds are run.** Build and test in Xcode / Android Studio as usual.
- **No shared code between platforms.** The plugin deliberately keeps iOS and Android implementations independent — convergence happens through the peer-review and reconciliation loop, not by sharing source files.
- **Never targets `main`.** All branches are cut from the discovered trunk (typically `stage`). The plugin will not touch `main`.
- **Backend typecheck only.** If the backend is touched, `npm run typecheck` (or the discovered equivalent) is run. No test suite is executed.
