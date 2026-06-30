# Parity Guardrails

Rules for honoring the parity registry throughout the feature development workflow. All agents — supervisor, ios-developer, android-developer — must follow these rules.

---

## Core Principle: Match Behavior, Not Implementation

The parity registry defines what must be **identical from the user's perspective**. It does not prescribe how the code achieves that identity.

**What must match:** the user experience — copy, timing, flow, outcomes, error messages.

**What may differ:** implementation — SwiftUI vs Compose, Combine vs StateFlow, URLSession vs Retrofit, Keychain vs EncryptedSharedPreferences.

Example:
- ✅ Both platforms show "No items yet" on the empty state — that copy is parity-required.
- ✅ iOS uses a `Text("No items yet")` in a VStack; Android uses a `Text("No items yet")` in a Column. Implementation differs, behavior matches.
- ❌ iOS shows "No items yet" and Android shows "Nothing to see here" — parity violation.

---

## Rules

### Rule 1: Do Not Invent Parity

If a behavior is not in the parity registry, do not assume it must match. Platforms may diverge where the registry is silent.

When the registry is silent on a behavior:
- Developer agents make platform-idiomatic choices (e.g., iOS uses a swipe-to-dismiss sheet, Android uses a bottom sheet).
- Flag the divergence in the completion report under "Key Decisions."
- The supervisor decides in reconciliation whether to add it to parity requirements.

### Rule 2: Parity Registry Is Read-Only During a Feature Run

No agent modifies the parity registry file during a feature run, even if the master plan introduces new parity requirements.

The supervisor may **recommend** additions to the parity registry as part of the master plan, but the actual file update is left for the user to make (or approved explicitly in Phase 7 if the user asks).

Exception: if the parity registry doesn't exist, the supervisor notes this in the master plan and applies the fallback rule (below). The supervisor does not create a parity registry during the run.

### Rule 3: Fallback When Registry Is Absent

If no parity registry is found (discovery returned `parity_registry: not found`):

**Treat all UX-visible behaviors as requiring parity.** This is the conservative default.

"UX-visible behaviors" means: copy (text, labels, error messages), flow (screen sequence, navigation), outcomes (what happens after each action), and empty/error/loading states.

The supervisor notes this fallback in the master plan so both developers know the rule they're operating under.

### Rule 4: Parity Conflict Resolution

If an implementation contradicts the parity registry:

1. **Developer agent:** Flag it in the completion report under "Open Questions." Do not silently work around it — the supervisor needs to see it.
2. **Peer reviewer:** Flag it under "Parity Gaps" in Part A of the peer review. Note whether the registry requires a match.
3. **Supervisor (reconciliation):** Apply Priority 2 from the reconciliation rubric — fix the deviating platform.

If the registry requirement itself seems wrong (e.g., it requires parity for something that should differ by platform): note it in the reconciliation log. Do not unilaterally ignore the registry. Escalate to the user.

### Rule 5: Parity Is About the User, Not the Code

When assessing parity in peer review, compare what the **user would experience**, not what the code looks like.

Ask: "If a user ran this feature on iOS and then on Android, would they notice a difference?" If yes, and the registry requires a match, it's a parity gap.

Animated vs instant transitions, different loading indicator styles, different keyboard types for the same input field — these are parity gaps if the registry requires a match.

### Rule 6: Aesthetic Parity Is High Priority

Visual consistency is as important as behavioral consistency. Even when the parity registry is silent, the two apps should look and feel like they belong to the same product family.

This includes: color palette and theme tokens, typography scale and weights, spacing and padding rhythm, iconography style and sizing, animation duration and easing, loading and skeleton states, empty state illustrations and copy, and error presentation patterns.

**Acceptable aesthetic divergence:** platform-native navigation chrome (iOS tab bar vs Android bottom nav), platform-native form controls, system fonts when no custom font is specified. These are idiomatic and expected.

**Unacceptable aesthetic divergence:** one platform using a filled button style and the other an outlined button for the same action; different loading indicator designs for the same flow; mismatched empty state copy or illustration style; different color values for the same semantic element (primary action, destructive action, etc.).

When the parity registry is absent, apply the aesthetic parity default: flag any visible aesthetic gap in the peer review and let the supervisor decide in reconciliation.

---

## Parity Registry Format (Expected)

The plugin expects the parity registry to be a markdown file (e.g., `PLATFORM_PARITY.md`) with sections or a table listing required behaviors:

```markdown
# Platform Parity Registry

| Behavior | iOS | Android | Match required? |
|----------|-----|---------|-----------------|
| Empty state copy | "No items yet" | "No items yet" | Yes |
| Error state copy | <error message> | <error message> | Yes |
| Pull-to-refresh | Supported | Supported | Yes — must exist on both |
| Navigation style | Pushed sheet | Bottom sheet | No — platform-native |
```

If the registry uses a different format, the supervisor reads and interprets it at Phase 0. The principle is the same: identify which behaviors must match and which may differ.
