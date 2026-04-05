# Plan Comment Template

Use this template when posting implementation plans as issue comments.
The `<!-- claude-feature-planner-v1 -->` marker on the first line is required —
downstream skills use it to locate the plan programmatically.

---

```markdown
<!-- claude-feature-planner-v1 -->
## Implementation Plan for #<NUMBER>: <TITLE>

### Summary
<2-3 sentences: what the feature does, why it matters, and the high-level approach.>

### Affected Files

| Action | File | Description |
|--------|------|-------------|
| Create | `path/to/new-file.ts` | <what this file does> |
| Modify | `path/to/existing.ts` | <what changes and why> |
| Delete | `path/to/obsolete.ts` | <why it's being removed> |

### Implementation Steps

1. **<Step title>**
   - <Specific change description>
   - <Code pattern or approach to follow>

2. **<Step title>**
   - <Specific change description>

<Continue as needed. Each step should be atomic and independently testable
where possible.>

### Test Strategy

- **Unit tests**: <what to test, which files>
- **Integration tests**: <if applicable, what to test>
- **Manual verification**: <steps to verify the feature works>

### Risk Assessment

| Factor | Level | Notes |
|--------|-------|-------|
| Database changes | LOW/MEDIUM/HIGH | <explanation> |
| Security impact | LOW/MEDIUM/HIGH | <explanation> |
| Breaking changes | LOW/MEDIUM/HIGH | <explanation> |
| Scope | LOW/MEDIUM/HIGH | <number of files, complexity> |

### Dependencies

- <Other issues this depends on, or "None">
- <External services or APIs required>
- <New packages or dependencies needed>
```
