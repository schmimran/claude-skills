# Discovery Surface Guide

How the orchestrator locates the API directory, web directory, and hot-path
entry point on an arbitrary Node.js / TypeScript repository. Used by the
bug-sweeper command in Phase 0e.

The original prompt this plugin replaces had hard-coded paths
(`apps/api/src/`, `apps/web/public/`, a specific `index.ts`). For a reusable
plugin those have to be discovered, not assumed.

## API directory candidates

Try these in order until one resolves to an existing directory with at
least one `.ts` / `.js` source file:

1. `apps/api/src/`
2. `apps/server/src/`
3. `packages/api/src/`
4. `packages/server/src/`
5. `src/server/`
6. `src/api/`
7. `backend/src/`
8. `server/src/`
9. From `package.json` workspaces: any workspace whose name contains
   `api`, `server`, or `backend`.
10. Fallback: read `package.json`'s `main` or `bin` field. The directory
    containing the entry script is the API directory.

## Web directory candidates

1. `apps/web/`
2. `apps/web/public/`
3. `apps/client/src/`
4. `apps/frontend/src/`
5. `packages/web/src/`
6. `src/client/`
7. `src/web/`
8. `frontend/src/`
9. From `package.json` workspaces: any workspace whose name contains
   `web`, `client`, or `frontend`.

If no web surface is found, that is a valid outcome — many repos are
backend-only. Skip the web reviewer and continue.

## Hot-path entry point heuristics

A "hot path" is a flow that runs without direct user interaction and
therefore is more likely to ship bugs (no human in the loop to notice). Look
for these patterns inside the API directory:

| Pattern | grep |
|---------|------|
| Interval handler | `setInterval\(` |
| Cron job | `cron\.schedule`, `node-cron`, `bullmq.*Worker`, `agenda` |
| Queue consumer | `\.process\(`, `\.consume\(`, `Queue\(` |
| Webhook receiver | route handlers under `/webhooks/`, `/hooks/`, `/callbacks/` |
| SSE / WebSocket | `EventSource`, `new WebSocket`, `ws\.on\(`, `Server-Sent` |
| Schedule sweep / cleanup | identifiers containing `sweep`, `cleanup`, `prune`, `expire`, `inactivity` |

Pick the **first** hot path you find that touches **multiple side effects**
(DB writes + email + state mutation, for example). The tracer is most
valuable on flows that span 3+ files.

If no hot path is identifiable, fall back to the API entry point itself
(`src/index.ts` / `src/server.ts` / the `main` field). The tracer adapts —
its protocol does not depend on the entry point being a "hot path"
specifically.

## Reporting back to the orchestrator

The orchestrator records the discovered surfaces and entry point in its
in-memory state and passes them to the Phase 2 agents. If discovery fails
(no API directory and no entry point), stop with a clear message:

> bug-sweeper requires a Node.js / TypeScript repository with a recognizable
> server entry point. None of the candidate directories were found. Stopping.

Do not attempt to bug-sweep arbitrary repo shapes — the agents are tuned
for Node.js patterns.
