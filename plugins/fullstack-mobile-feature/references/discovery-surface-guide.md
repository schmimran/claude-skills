# Discovery Surface Guide

How to locate the surfaces of an unknown full-stack mobile repo. Run these steps during Phase 0 if no project-fit file exists. Record each finding in `$WORK_DIR/discovery.md` using the key names shown below.

---

## 1. iOS App Root (`ios_root`)

**Goal:** Find the directory that contains the iOS source code.

Search heuristics (run in order; stop at first hit):

1. `find . -name "*.xcodeproj" -maxdepth 4 | head -5` — the directory containing this file is usually the iOS root.
2. `find . -name "*.xcworkspace" -maxdepth 4 | head -5` — same logic for workspace-based projects.
3. `find . -name "*App.swift" -path "*/iOS/*" -o -name "*App.swift" -path "*/ios/*" | head -5` — look for the SwiftUI `@main` entry point.
4. `ls -d iOS/ ios/ App/ Source/` — common top-level names.

Once you have the root, find the main `App` entry file:
```bash
grep -r "@main" <ios_root> --include="*.swift" -l | head -3
```

Record:
```
ios_root: <path>
ios_app_entry: <path to @main file>
```

---

## 2. Android Package Root (`android_root`)

**Goal:** Find the directory containing Android source code.

Search heuristics:

1. `find . -name "build.gradle" -o -name "build.gradle.kts" | xargs grep -l "applicationId" 2>/dev/null | head -3` — the directory of the matching file is the app module root.
2. `find . -path "*/src/main/java/*" -name "*.kt" | head -5` — look for Kotlin sources under the standard Android source set.
3. `ls -d Android/ android/ app/` — common names.

From the app module root, find the `Application` class:
```bash
grep -r "Application()" <android_root> --include="*.kt" -l | head -3
```

Identify the base package name from the `applicationId` in `build.gradle`.

Record:
```
android_root: <path to app module>
android_app_entry: <path to Application class>
android_package: <com.example.app>
```

---

## 3. Backend Root and Layout (`backend_root`, `backend_routes`, `typecheck_cmd`)

**Goal:** Find the Node.js/Express (or equivalent) backend, its module/route structure, and its typecheck command.

Search heuristics:

1. `find . -name "package.json" -maxdepth 3 | xargs grep -l '"express"\|"fastify"\|"hono"\|"@nestjs/core"' 2>/dev/null | head -3` — directory containing this is likely the backend root.
2. `ls -d api/ backend/ server/ src/` — common backend directory names.
3. Look for entry point: `find <backend_root> -name "app.ts" -o -name "index.ts" -o -name "server.ts" | head -3`
4. Look for module/route layout:
   ```bash
   ls <backend_root>/src/modules/ 2>/dev/null || ls <backend_root>/src/routes/ 2>/dev/null
   ```

**Fallback (no Node.js framework found):** If step 1 returns nothing, try `find . -name "package.json" -maxdepth 3 | head -5` without the framework filter to find any JS/TS project, then confirm with the user which is the backend. If the backend is non-Node (Python, Go, etc.), stop and ask the user to provide the backend root path — do not guess.

Discover the typecheck command from `package.json`:
```bash
cat <backend_root>/package.json | grep -A1 '"typecheck"\|"type-check"\|"tsc"'
```
Common values: `tsc --noEmit`, `npm run typecheck`. Fall back to `npx tsc --noEmit` if none found.

Record:
```
backend_root: <path>
backend_entry: <path to entry file>
backend_module_dir: <path to modules or routes dir>
typecheck_cmd: <command string>
```

---

## 4. Contract Doc (`contract_doc`)

**Goal:** Find the mobile API contract document.

Search heuristics (in priority order):

1. `find . -name "MOBILE_API.md" -maxdepth 4 | head -3`
2. `find . -name "API.md" -maxdepth 4 | head -3`
3. `find . -name "openapi.yaml" -o -name "openapi.json" -o -name "swagger.yaml" | head -3`
4. `find . -name "*.md" | xargs grep -l "endpoints\|API\|mobile" 2>/dev/null | head -5`
5. `ls <backend_root>/docs/ <backend_root>/api-docs/ 2>/dev/null`

If no contract doc is found: note this in the discovery summary and flag it to the user. Do not invent one. The master plan will need to create it from scratch.

Record:
```
contract_doc: <path, or "not found">
```

---

## 5. Parity Registry (`parity_registry`)

**Goal:** Find the document that defines which behaviors must match across iOS and Android.

Search heuristics:

1. `find . -name "PLATFORM_PARITY.md" -o -name "PARITY.md" | head -3`
2. `grep -r "parity\|cross-platform" . --include="*.md" -l | head -5`
3. Check if the contract doc contains a "parity" or "cross-platform" section

If no parity registry is found: record `parity_registry: not found`. The fallback rule applies: treat all UX-visible behaviors as requiring parity across platforms.

Record:
```
parity_registry: <path, or "not found">
```

---

## 6. Trunk Branch (`trunk`)

**Goal:** Identify the working trunk that feature branches should be cut from.

```bash
git remote show origin 2>/dev/null | grep "HEAD branch" | awk '{print $NF}'
```

If that fails:
```bash
git branch -r | grep -E "origin/(stage|main|master|develop)" | head -5
```

Priority: prefer `stage` over `main` over `master` over `develop` when multiple exist.

Verify the branch exists locally:
```bash
git branch --list stage main master develop | head -3
```

Record:
```
trunk: <branch name>
```

---

## 7. Monorepo vs Separate-Repo Layout

If iOS, Android, and backend are all in the same repo (monorepo): the above heuristics should work as-is. Record paths relative to the repo root.

If they appear to be in separate repos (e.g., you find only iOS source and no `package.json`): stop Phase 0 and ask the user which repo each surface lives in. Do not guess.

Monorepo indicator: all three surfaces found under the same git root (same `.git` directory).
Separate-repo indicator: `git rev-parse --show-toplevel` returns different paths for different surfaces.

---

## discovery.md Format

Write all findings to `$WORK_DIR/discovery.md` in this format:

```
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
```

Fields that were not found: write `not found` as the value. Never omit a field.
