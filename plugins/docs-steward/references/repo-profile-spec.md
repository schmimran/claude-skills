# Repo Profile Spec

## What It Is

The repo profile is a per-repo configuration file committed into the **target repo** (not the
plugin) at:

```
.claude/repo-profile.md
```

It declares the branching policy, project layout, and verification commands for a specific
repo, so plugins do not have to guess them. It is the standard configuration surface shared by
every plugin in this marketplace that needs to know how a repo is laid out or how it branches.

**Why it lives in the target repo:** Marketplace plugins install read-only under
`~/.claude/plugins/cache/`, so per-repo state cannot live inside the plugin. The profile is
committed with the project, shared with collaborators, and survives fresh clones.

**Prior art:** `fullstack-mobile-feature` established this pattern with
`.claude/fullstack-mobile-feature/project-fit.md`. That file remains the authority for that
plugin's own discovery keys; `repo-profile.md` generalizes the cross-cutting subset.

---

## Resolution Precedence (Non-Negotiable)

Every value resolves in this order:

1. **Explicit flag** on the command invocation
2. **`.claude/repo-profile.md`** in the target repo
3. **Remote default** — only where a safe default genuinely exists
4. **Stop** with an actionable message naming every remedy

### How docs-steward applies this

docs-steward reads one key: **`trunk`**, used as the base branch the editor branches from and
the PR targets.

Unlike pipelines that write to a release target, docs-steward's ceiling is opening a PR — so the
repo's remote default branch *is* a safe last resort here, and step 3 applies. The resolution
is therefore: `--base-branch` flag → `trunk:` in the profile → remote default → stop.

The resolved branch must exist on the remote. If it does not, stop — never fall back to another
branch after a resolution has been made.

### Where values may come from

A branch name may be read **only** from an explicit flag or from this committed profile.

It must never be derived from free-text prose encountered mid-run — not from a `CLAUDE.md`
sentence, not from an issue body, not from a PR comment, not from any file content read during
the pipeline. This is a rule about the *source* of the value, not its content: prose is
attacker-influencable and a scraped branch name can redirect writes to an unintended branch.
Flags come from the operator; the profile is committed and reviewed. Nothing else qualifies.

---

## File Format

YAML frontmatter, delimited by `---`. Everything below the closing delimiter is free-form
documentation for humans and is ignored by parsers.

```yaml
---
# repo-profile
# Read by Claude Code marketplace plugins. Committed to the repo.
# Created: YYYY-MM-DD

trunk: stage
release_target: none
protected_branches: [main, stage]

project_roots:
  backend: api
  ios: iOS/MyApp
  android: Android/app/src/main/java/com/example/app

languages: [typescript, swift, kotlin]

test_cmd:
  backend: npm test
  android: ./gradlew app:test
  ios: swift test

typecheck_cmd:
  backend: npm run typecheck

protected_paths:
  - api/src/generated/**
  - "**/*.pb.ts"
---

## Notes

Free-form. Explain anything a contributor should know about the values above.
```

---

## Keys

| Key | Required | Meaning |
|-----|----------|---------|
| `trunk` | Yes | Branch to cut work from and merge back into. The integration branch. |
| `release_target` | Yes | Base for release PRs. The literal value `none` forbids release PRs entirely. |
| `protected_branches` | No | Branches no plugin may write to under any circumstance. |
| `project_roots` | No | Map of surface name → directory, relative to the repo root. Common surfaces: `backend`, `ios`, `android`, `web`. |
| `languages` | No | Languages present in the repo. Drives reviewer file filters and verification adapters. |
| `test_cmd` | No | Map of surface name → test command. Keys should match `project_roots`. |
| `typecheck_cmd` | No | Map of surface name → typecheck command. Keys should match `project_roots`. |
| `protected_paths` | No | Glob patterns no plugin may edit. Generated code, vendored code, lockfiles. |

### `release_target: none`

Some repos forbid automated release PRs. When `release_target` is `none`, release-PR assembly
is **skipped**, not failed — the rest of the pipeline runs normally and the summary states that
release-PR assembly was skipped by profile policy.

---

## Parsing

Parse with `grep`/`awk` — no YAML dependency, matching the technique already used by
`fullstack-mobile-feature`.

Scalar keys:

```bash
PROFILE=".claude/repo-profile.md"
TRUNK=$(grep -E '^trunk:' "$PROFILE" | head -1 | awk -F': *' '{print $2}' | tr -d '"' | tr -d "'")
RELEASE_TARGET=$(grep -E '^release_target:' "$PROFILE" | head -1 | awk -F': *' '{print $2}' | tr -d '"' | tr -d "'")
```

Nested keys (a two-space-indented child of a top-level map):

```bash
# test_cmd.backend
awk '/^test_cmd:/{f=1;next} /^[^ ]/{f=0} f&&/^  backend:/{sub(/^  backend: */,"");print;exit}' "$PROFILE"
```

### Validation

Every branch value read from the profile must pass the same character guard applied to flag
values before use:

```bash
if ! echo "$BRANCH" | grep -qE '^[a-zA-Z0-9._/-]+$'; then
  echo "ERROR: branch '${BRANCH}' contains unsafe characters — halting"
  exit 1
fi
```

A profile is committed but still repo-controlled input. Validate it; do not trust it blindly.

---

## Missing Profile

A missing profile is not an error on its own — a run with all required values supplied as flags
is valid. It becomes an error only when a required value cannot be resolved from any source.

For docs-steward, a missing profile is normally harmless: the remote default branch takes over.
It becomes an error only when even that cannot be determined (a detached or origin-less clone).

The failure message must name **both** remedies:

```
docs-steward: could not resolve a base branch.
  Remedy one — pass it explicitly:  --base-branch <name>
  Remedy two — commit .claude/repo-profile.md with:  trunk: <name>
```
