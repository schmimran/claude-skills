# Platform Brief Template

The supervisor derives one brief per platform from the master plan. Each brief is self-contained — the developer agent should not need to read the master plan directly.

Write an iOS brief and an Android brief. Adjust section 5 (Platform-Specific Guidance) for each platform. Everything else references the same shared contract and parity requirements.

---

```markdown
# <iOS | Android> Brief: <Feature Name>

**Platform:** iOS (SwiftUI/MVVM) | Android (Kotlin/Compose/Hilt)  
**Date:** YYYY-MM-DD  
**Branch:** feature/<slug> (already created — check it out before starting)

---

## 1. Feature Summary

<One sentence referencing the master plan.>

See master plan for full UX spec, data model, and API interaction diagrams.

---

## 2. Platform Paths

These are the real paths in this repo (from the fit/discovery step). Use them exactly.

| Surface | Path |
|---------|------|
| Source root | `<ios_root>` or `<android_root>` |
| Main app entry | `<ios_app_entry>` or `<android_app_entry>` |
| Existing feature modules | `<path to features/ or modules/ dir>` |
| Networking layer | `<path to shared API client or Retrofit setup>` |
| Contract doc | `<contract_doc>` |
| Parity registry | `<parity_registry>` |

Before writing any code: read 2–3 existing feature modules at the paths above to calibrate naming conventions, file organization, and patterns.

---

## 3. API Contract Reference

Implement these exact endpoints. Do not deviate from the field names, types, or error codes.

### `<METHOD> <path>`

**Auth:** <Bearer token in Authorization header | no auth>

**Request body:**
```json
{
  "field": "<type>"
}
```

**Success response (<status>):**
```json
{
  "field": "<type>"
}
```

**Error codes to handle:**
- `400 VALIDATION_ERROR` — show inline validation message
- `401 UNAUTHORIZED` — redirect to login / refresh token
- `404 NOT_FOUND` — show empty state
- `500 INTERNAL_ERROR` — show generic error state

<Repeat for each endpoint the platform must call.>

---

## 4. Parity Requirements

These behaviors **must match** the other platform from the user's perspective. Your implementation may differ — what must match is the experience.

| Behavior | Requirement |
|----------|-------------|
| <behavior> | Exact match — same copy, same timing |
| <behavior> | Exact match |

**You are not required to match:**
- <behavior>: use platform-native idiom (e.g., iOS uses sheet, Android uses bottom sheet)
- <behavior>: <rationale>

Read the parity registry at `<parity_registry>` for the full list. When in doubt, match.

---

## 5. Platform-Specific Implementation Guidance

### [iOS only]

- **Architecture:** MVVM with `@Observable` (or `ObservableObject` if the existing codebase uses it — match what you see)
- **Networking:** Use the existing `APIClient` / `URLSession` wrapper (found at `<path>`). Do not instantiate URLSession directly.
- **Auth token:** Read from Keychain using the existing `KeychainManager` (or equivalent found in the codebase).
- **Navigation:** Follow the existing navigation pattern (NavigationStack / NavigationPath or coordinator pattern — observe what's there).
- **Error presentation:** Use the pattern you see in existing features (Alert, inline error view, etc.).
- **Loading state:** Use a `@State var isLoading: Bool` or the existing loading indicator component.
- **Naming conventions:** Match existing feature files exactly (e.g., `FooView.swift`, `FooViewModel.swift`, `FooService.swift`).

### [Android only]

- **Architecture:** MVVM with Repository. `@HiltViewModel`, `StateFlow<UiState>` where `UiState` is a sealed interface/class.
- **Networking:** Use the existing Retrofit service pattern (found at `<path>`). Add a new `@GET`/`@POST` to the existing API interface or create a new service interface following the same pattern.
- **Auth token:** Read from `EncryptedSharedPreferences` using the existing auth repository/manager.
- **Navigation:** Follow the existing NavHost/NavController pattern.
- **Error presentation:** Follow the existing pattern (Snackbar, inline error composable, etc.).
- **Loading state:** Model as part of `UiState` sealed interface (e.g., `Loading`, `Success`, `Error` states).
- **Naming conventions:** Match existing feature packages and file names (e.g., `FooScreen.kt`, `FooViewModel.kt`, `FooRepository.kt`, `FooApiService.kt`).
- **DI:** Add Hilt `@Provides` / `@Binds` in the existing or new module. Follow the existing module structure.

---

## 6. Files to Create / Modify

<List the files you expect to create or modify. This is a starting estimate — adjust as you discover the codebase.>

**Create:**
- `<path/NewFile.swift>` — <purpose>
- `<path/NewFile.kt>` — <purpose>

**Modify:**
- `<path/ExistingFile.swift>` — <what to add>
- `<path/ExistingFile.kt>` — <what to add>

---

## 7. Out of Scope

- **Do not build or run tests.** The user builds in Xcode / Android Studio.
- **Do not touch the other platform's directory.**
- **Do not touch backend code** (backend changes were implemented by the supervisor in Phase 2).
- **Do not update the parity registry** (read-only during a feature run).
- **Do not add dependencies** without flagging it in your completion report.

---

## 8. Return Format

When done, return your completion report in the format from `references/completion-report-template.md`. Be specific and honest — the supervisor and peer reviewer read it.
```
