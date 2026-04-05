# Risk Assessment Criteria

Use this rubric to assess the risk level of each planned feature. Evaluate
every applicable factor. A feature is **high-risk** if it has any HIGH factor
or two or more MEDIUM factors.

## HIGH Risk Factors

| Factor | Trigger | Why it's HIGH |
|--------|---------|---------------|
| Database / schema migration | Plan includes DDL changes, migration files, or schema modifications | Schema changes can cause data loss, downtime, or require coordinated deploys |
| Authentication / authorization | Plan touches auth middleware, session management, token handling, or access control | Security-sensitive code has outsized blast radius if wrong |
| Breaking API changes | Plan removes or changes the signature of public API endpoints | Downstream consumers will break without coordinated migration |
| Secrets / credentials | Plan adds, moves, or modifies handling of API keys, tokens, or secrets | Credential mishandling can cause security incidents |
| Data deletion | Plan includes logic that permanently deletes user data | Irreversible data loss if logic is wrong |

## MEDIUM Risk Factors

| Factor | Trigger | Why it's MEDIUM |
|--------|---------|-----------------|
| Cross-cutting scope | Plan touches 10+ files or spans 3+ distinct modules/packages | Large surface area increases chance of unintended side effects |
| External API integration | Plan introduces a new third-party API or service dependency | External dependencies add failure modes and require error handling |
| Configuration changes | Plan modifies environment variables, deploy config, or infrastructure | Config errors can cause outages that are hard to diagnose |
| Performance-sensitive paths | Plan modifies hot paths, database queries, or caching logic | Performance regressions may not be caught by unit tests |
| Concurrent / async logic | Plan introduces or modifies concurrent, async, or queue-based processing | Race conditions and deadlocks are notoriously hard to test |

## LOW Risk Factors

| Factor | Trigger | Why it's LOW |
|--------|---------|--------------|
| UI-only changes | Plan only touches templates, styles, or copy | Visual changes are easy to verify and revert |
| New additive feature | Plan adds new endpoints, components, or modules without changing existing ones | No existing behavior is affected |
| Documentation | Plan only modifies docs, comments, or README | No runtime impact |
| Test-only changes | Plan only adds or updates tests | Improves coverage without affecting production code |
| Refactoring with tests | Plan restructures code but has existing test coverage for all affected paths | Tests provide a safety net |

## How to Apply

1. Read the implementation plan's "Affected Files" and "Implementation Steps"
2. Check each risk factor above against the plan
3. Record which factors apply and at what level
4. Determine overall risk:
   - **Any HIGH factor** → high-risk → flag for human review
   - **2+ MEDIUM factors** → high-risk → flag for human review
   - **1 MEDIUM factor** → acceptable risk → proceed
   - **All LOW** → low risk → proceed
5. When flagging, cite the specific factors and explain why they apply
