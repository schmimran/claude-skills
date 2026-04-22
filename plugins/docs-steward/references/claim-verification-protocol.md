# Claim Verification Protocol

Loaded by the three source-verifying auditors:

- `docs-intent-auditor`
- `docs-example-verifier`
- `docs-reference-validator`

These auditors operate under Tenet 0 — docs are untrusted until verified
against source.

## What counts as a claim

A claim is any assertion in documentation about the behavior, shape, or
identity of code.  The common forms:

- A function signature, parameter list, or return type.
- A described behavior (what a function does, side effects, error modes).
- An env-var name, default, or effect.
- A config-key name, accepted values, or effect.
- A CLI command, flag, or argument.
- An HTTP route's method, path, or response shape.
- A file path, module path, or exported symbol.
- A code example that calls into the project's own code.

Pure prose that does not reference code (motivation, history, design
rationale) is not a claim for this protocol — the info-architect and
manual-reader cover those.

## The posture

Start every claim with: *"Assume this is wrong and disprove it by reading
source."*  Do not clear a claim on any of these grounds alone:

- "The doc says so."
- "The index signature matches the doc string."
- "It looks plausible."
- "The function name implies the behavior."

Clearing a claim requires opening the referenced file at the referenced
line and confirming the implementation actually supports what the doc
says.

## Rigor modes

The orchestrator's `--rigor` argument is passed as `RIGOR` to the three
auditors.  Each auditor respects the setting when deciding whether to
open source for a given claim.

### `full`

Verify every claim by reading source.  Slowest, most thorough.  Use
when the target repo has a history of drift or before a release.

### `major`

Verify all claims that would produce a `critical` or `major` finding
(incorrect signatures, missing env vars, broken examples, wrong
behavior descriptions).  Trust the index for claims that would only
produce `minor` or `nit` findings (formatting, naming consistency).

### `sampled` (default)

Verify every `critical`/`major` claim, plus a 20% random sample of
`minor`/`nit` claims.  Balances runtime against coverage.  Randomness
is re-seeded per run so the sampled set shifts across invocations.

## Unverifiable claims

Sometimes source verification is impossible:

- The referenced file is generated and not tracked.
- The referenced symbol is in an external dependency.
- The example calls a shell command whose source isn't in the repo.
- The doc describes a third-party API.

When verification is impossible:

1. Record the claim in the finding with `verification: unverified` and
   a `verification_note` explaining why source reading did not apply.
2. Downgrade severity by one step (`critical → major`, `major → minor`,
   `minor → nit`).  The reasoning: if we cannot confirm drift, we
   cannot justify a top-severity finding.
3. Never silently clear — an unverified claim is still a hypothesis,
   just one this run could not test.

## Finding-record fields

Each auditor record adds three fields beyond the base schema:

| Field | Values | Meaning |
|---|---|---|
| `verification` | `verified` \| `unverified` \| `skipped_by_rigor` | Outcome of the source-reading step. |
| `verification_source` | file path + line number | Where the auditor read.  Empty when `verification ≠ verified`. |
| `verification_note` | free text | One-line reason when `unverified` or `skipped_by_rigor`. |

`skipped_by_rigor` applies only under `major` or `sampled` when the
claim was deemed low-severity and not drawn in the sample.  It is not
a downgrade — the claim is simply out of scope for this run's rigor.
