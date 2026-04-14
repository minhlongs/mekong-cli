# Phase Implementation Report

### Executed Phase
- Phase: usage-export-invoice-endpoints
- Plan: none (direct task)
- Status: completed

### Files Modified
- `apps/raas-gateway/src/routes/usage-export.ts` — created, 143 lines
- `apps/raas-gateway/src/routes/index.ts` — 3 additions: import, 2 route mounts, 3 OpenAPI paths

### Tasks Completed
- [x] Read credits.ts, auth.ts, index.ts for patterns
- [x] Read migrations for credit_transactions and subscriptions schema
- [x] Created `usage-export.ts` with 3 endpoints
- [x] GET /v1/usage/export — D1 query with optional date range, returns text/csv with Content-Disposition
- [x] GET /v1/invoices — merges purchase credit_transactions + subscriptions into invoice shape, sorted by date desc
- [x] GET /v1/invoices/:id — resolves inv-sub-<id> (subscriptions) and inv-<txnId> (purchases)
- [x] Wired into index.ts: `routes.route('/v1/usage', usageExport)` + `routes.route('/v1/invoices', usageExport)`
- [x] Added 3 OpenAPI path entries (usage/export, invoices, invoices/{id})
- [x] Auth + rate-limit middleware on all endpoints

### Tests Status
- Type check: pass (0 errors, `npx tsc --noEmit`)
- Unit tests: not run (no test harness in gateway)
- Integration tests: n/a

### Issues Encountered
- File was initially 226 lines — compacted by merging the double import, hoisting TIER_PRICE + helpers to module scope, and collapsing single-field conditionals. Final: 143 lines.
- Both /v1/usage and /v1/invoices mount the same Hono router instance. This is intentional: the router's sub-paths (/export, /, /:id) match correctly under each mount prefix.

### Next Steps
- Deploy: `wrangler deploy` in apps/raas-gateway
- Consider a `billing_events` table migration if finer-grained invoice tracking is needed
- price_cents in metadata is used when present (set by Polar/Stripe webhooks); fallback is credits × 500 cents
