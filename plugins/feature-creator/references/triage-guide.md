# Triage Guide

Heuristics and rules for grouping issues into planning buckets. Used by the
`feature-triager` agent in Phase 0 of the feature-creator pipeline. Applies
to **both** features (`feature - ready for claude`) and bugs
(`bug - ready for claude`).

## Goal

Group issues that are likely to touch the same files into a single bucket so
that one planner agent can reason about them together. This cuts redundant
codebase exploration and catches within-bucket file conflicts at plan time
instead of at implementation time.

## Type-Separation Rule (Absolute)

**Features and bugs are bucketed independently.** A feature and a bug never
share a bucket, even if their predicted globs overlap. The downstream
planner, consolidator, reviewer, and implementer apply different templates,
risk rubrics, plan markers, branch prefixes, and commit types per type —
mixing types inside a bucket would make those agents misclassify the
bucket.

The triager:
1. Fetches `feature - ready for claude` issues and `bug - ready for claude`
   issues separately
2. Tags each issue with its `type` (`"feature"` or `"bug"`)
3. Runs the bucketing rules below **per type**
4. Emits a single manifest containing buckets of both types, each with a
   `type` field

If a feature and a bug both touch `apps/api/src/sweep.ts`, they end up in
two separate buckets even if those buckets are otherwise singletons. This
is intentional.

## Bug Issue Body Recognition

Bug issues filed by upstream discovery agents (e.g. `bug-sweeper`) begin
with the marker `<!-- claude-bug-sweeper-v1 -->` and contain explicit
`**File:**` and `**Lines:**` fields in their body. When such a body is
present, the triager **must** prefer those explicit citations over
keyword heuristics when computing predicted globs.

Bugs filed by humans may not include explicit file:line citations. Fall
back to keyword heuristics in that case.

(This rule does not link to upstream-plugin documentation: the marker
string and field names above are the only details the triager needs at
runtime, so feature-creator stays installable without any specific
upstream filer present.)

## Predicting Impacted Globs

For each issue, derive a set of predicted impacted file globs using these
signals, in order of confidence:

1. **Explicit paths in the issue body.** If the body contains a literal path
   like `src/auth/middleware.ts` or `plugins/feature-creator/**`, include it
   verbatim. Expand bare filenames to their containing directory glob (e.g.
   `middleware.ts` → `src/**/middleware.ts`) when the directory is unambiguous
   from the shared context.

2. **Keyword-to-path heuristics.** Apply the table below. A single issue may
   match multiple keywords — include all matching globs.

3. **Title component signals.** If the title names a known component or
   directory (e.g. "feature-creator: …"), include that component's primary glob.

### Keyword-to-Path Table

| Keyword(s) in issue | Glob |
|---------------------|------|
| `auth`, `login`, `session`, `token` | `src/auth/**`, `**/auth/**` |
| `style`, `color`, `theme`, `css`, `token` (visual) | `src/styles/**`, `**/*.css`, `**/theme/**` |
| `route`, `routing`, `navigation` | `src/routes/**`, `**/router/**` |
| `api`, `endpoint`, `handler` | `src/api/**`, `**/handlers/**`, `**/routes/**` |
| `db`, `schema`, `migration`, `model` | `**/migrations/**`, `**/models/**`, `**/schema*` |
| `test`, `spec`, `e2e` | `**/*.test.*`, `**/*.spec.*`, `test/**`, `tests/**` |
| `ci`, `workflow`, `pipeline`, `action` | `.github/workflows/**`, `.gitlab-ci.yml` |
| `doc`, `readme`, `claude.md` | `**/README.md`, `**/CLAUDE.md`, `docs/**` |
| `config`, `env`, `settings` | `**/*.config.*`, `.env*`, `config/**` |
| `feature-creator`, `planner`, `consolidator`, `reviewer`, `implementer`, `triager` | `plugins/feature-creator/**` |
| `security-scanner`, `security-runner`, `security-triager`, `security-closer`, `security-advisor`, `supabase` | `plugins/security-scanner/**` |
| `marketplace`, `plugin.json`, `plugin manifest` | `.claude-plugin/**`, `plugins/*/.claude-plugin/**` |
| `bug-sweeper`, `bug-sweeper-runner`, `bug-sweeper-reviewer`, `bug-sweeper-tracer`, `bug-sweeper-reconciler`, `bug-sweeper-analyst`, `bug-sweeper-filer` | `plugins/bug-sweeper/**` |

Bug-specific keywords (apply when an issue's `type` is `bug` and the body
does not contain explicit file paths):

| Keyword(s) in issue | Glob |
|---------------------|------|
| `crash`, `regression`, `broken`, `fails`, `error`, `exception` | use the file path in the body's `**File:**` line if present, otherwise apply the table above |
| `await`, `async`, `promise`, `race condition` | `apps/api/src/**`, `**/handlers/**`, `**/sweep*` |
| `xss`, `injection`, `csrf`, `sanitize` | `apps/web/**`, `**/views/**`, `**/templates/**` |
| `leak`, `memory`, `cleanup`, `timeout`, `interval` | `**/sweep*`, `**/cleanup*`, `**/cron*` |
| `cve`, `vulnerability`, `npm audit` | `package.json`, `package-lock.json` |

Extend the table when recurring signals emerge. If nothing matches, the issue
falls to a singleton bucket (see below).

## Grouping Rule (Jaccard ≥ 1, within type)

Two issues share a bucket if and only if **both** of these hold:

1. They are the same `type` (both features or both bugs).
2. Their predicted-glob sets share **at least one glob** — equivalently,
   `|A ∩ B| ≥ 1`. Glob comparison is a literal-string match on normalized
   glob text; do not attempt to expand wildcards for comparison.

Bucketing is transitive **within a type**: if feature A shares a glob with
feature B, and feature B shares a different glob with feature C, all three
go in the same bucket. Start with each issue in its own set and union any
two sets that satisfy both rules above; repeat until stable.

Cross-type unioning is never performed.

## Maximum Bucket Size

A bucket holds at most **4 issues**. If a transitive bucket would exceed 4:

1. **Secondary keyword affinity.** Score every pair of issues in the bucket by
   the number of shared keyword hits (beyond the single-glob minimum). Split
   the oversize bucket along the weakest link — the pair with the lowest
   secondary affinity — into two buckets. Re-check for cap compliance and
   repeat if needed.
2. Each resulting sub-bucket inherits the rationale suffix `"(split from <orig>)"`.

The cap is a **throughput guardrail**: a single planner agent reasons more
reliably about 4 issues than about 10. Do not exceed it.

## Singleton Rule

An issue with **zero glob overlap** with any other issue becomes its own
singleton bucket. Singletons are valid and expected — the downstream planner
handles them the same way as multi-issue buckets, just with one issue in the
`issues` array and no "Bucket-mates" section in the plan.

An issue whose body cannot be fetched is also placed in a singleton bucket
with rationale `"fetch failed — singleton fallback"` so the pipeline can
continue.

## Rationale Format

Every bucket must include a short `rationale` string naming the shared concern
that put those issues together. Keep it to a noun phrase under 60 characters.

Examples:

- `"color tokens"`
- `"feature-creator orchestrator"`
- `"auth middleware + session handling"`
- `"singleton — no overlap with batch"`
- `"split from b1 — weakest secondary affinity"`

The rationale is surfaced in the triage comment on each issue and in the
consolidated plan's per-bucket summary.

## Bucket Manifest Schema

The triager emits this JSON structure (to the path passed by the orchestrator):

```json
{
  "shared_context": "<markdown summary>",
  "buckets": [
    {
      "id": "b1",
      "type": "feature",
      "issues": [
        { "number": 14, "title": "..." }
      ],
      "predicted_globs": ["plugins/feature-creator/**"],
      "rationale": "feature-creator orchestrator"
    },
    {
      "id": "b2",
      "type": "bug",
      "issues": [
        { "number": 21, "title": "[bug] missing await in inactivity sweep" }
      ],
      "predicted_globs": ["apps/api/src/**", "**/sweep*"],
      "rationale": "inactivity sweep async ordering"
    }
  ]
}
```

Top-level required keys: `shared_context` (string) and `buckets` (array).
Each bucket entry must include the `type` field (`"feature"` or `"bug"`).
The orchestrator validates these immediately after the triager completes.
A malformed manifest halts the pipeline.
