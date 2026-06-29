# Master Plan Template

The supervisor writes one master plan per feature. It is the single source of truth that both platform briefs are derived from. Fill in every section — do not leave placeholders.

---

```markdown
# Master Plan: <Feature Name>

**Date:** YYYY-MM-DD  
**Branch:** feature/<slug>  
**Backend touched:** yes | no

---

## 1. Feature Summary

<One concise paragraph: what this feature does, who it's for, and why it's being built now.>

---

## 2. Data Model

<Describe any new or changed data entities. If no data model changes: write "No data model changes.">

| Entity | Field | Type | Notes |
|--------|-------|------|-------|
| <EntityName> | <field> | <type> | <constraints, nullable, etc.> |

---

## 3. UX / Behavior Spec

<Describe what the user sees and does on each platform. Write platform-by-platform if the UX differs; write once with "(both platforms)" if it's identical.>

### Happy path
1. <Step 1>
2. <Step 2>
3. <Step 3>

### Edge cases
- **Empty state:** <what is shown when there is no data>
- **Error state:** <what is shown when the API call fails>
- **Loading state:** <what is shown while the request is in flight>
- **Offline:** <behavior with no network connection>
- **Other:** <any other notable edge cases>

### Intentional platform divergences
<List any behaviors that will intentionally differ between iOS and Android. If none: "None — all UX-visible behaviors must match per the parity registry.">

---

## 4. API Interaction Spec

This section is the contract between the backend (implemented by the supervisor) and the two platform clients.

### 4a. Sequence Diagram

```
iOS Client                  Backend                  Android Client
     |                         |                           |
     |-- GET /endpoint ------->|                           |
     |                         |<-- GET /endpoint ---------|
     |<-- 200 { data } --------|                           |
     |                         |-- 200 { data } ---------->|
     |                         |                           |
     |-- POST /endpoint ------>|                           |
     |<-- 201 { result } ------|                           |
```

<Describe the sequence in prose if the diagram alone isn't clear.>

### 4b. Endpoints

For each new or changed endpoint:

#### `<METHOD> <path>`

**Purpose:** <one line>

**Auth:** <Bearer token in Authorization header | no auth | other>

**Request:**
```json
{
  "field": "type — description",
  "optionalField?": "type — description"
}
```

**Response (200/201):**
```json
{
  "field": "type — description"
}
```

**Error responses:**

| Status | Code | Message | When |
|--------|------|---------|------|
| 400 | `VALIDATION_ERROR` | "..." | <condition> |
| 401 | `UNAUTHORIZED` | "..." | <condition> |
| 404 | `NOT_FOUND` | "..." | <condition> |
| 500 | `INTERNAL_ERROR` | "..." | <condition> |

---

## 5. Contract Doc Changes

<Summarize what was added or changed in the contract doc during Phase 2. Reference the exact section headings.>

- Added: `<METHOD> <path>` — <description>
- Modified: `<section>` — <what changed>
- Removed: `<none / something>` — <reason>

---

## 6. Parity Requirements

These behaviors must be identical across iOS and Android from the user's perspective.

| Behavior | Requirement |
|----------|-------------|
| <behavior> | Must match exactly — same copy, same timing, same error message |
| <behavior> | Must match exactly |

**Permitted divergences** (behaviors that may differ by platform design):
- <behavior>: iOS uses <X>, Android uses <Y> — both are acceptable

---

## 7. Open Questions / Decisions Deferred

<List any open questions or decisions left to the platform developers. If none: "None.">

- [ ] <Question or decision for ios-developer>
- [ ] <Question or decision for android-developer>
- [ ] <Shared question — both should flag in their completion report>
```
