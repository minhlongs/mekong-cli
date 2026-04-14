# Phase Implementation Report

### Executed Phase
- Phase: Wave 3.4 — Annual Billing + Dunning Management
- Plan: Task #126
- Status: completed

### Files Modified
- CREATED `apps/raas-gateway/migrations/0024_dunning.sql` — 29 lines, dunning_events + win_back_emails tables + indexes
- CREATED `apps/raas-gateway/src/routes/dunning.ts` — 110 lines, 5 admin-only endpoints
- MODIFIED `apps/raas-gateway/src/routes/billing.ts` — added `annual_tiers` array to GET /billing/pricing response
- MODIFIED `apps/raas-gateway/src/routes/index.ts` — added import + mount for dunning at `/admin/dunning`

### Tasks Completed
- [x] Migration 0024: dunning_events table with FK to tenants
- [x] Migration 0024: win_back_emails table with FK to tenants
- [x] Migration 0024: indexes on tenant_id and status
- [x] GET /admin/dunning/active — active dunning cases (status != resolved)
- [x] GET /admin/dunning/stats — active count, at-risk revenue (cents + USD), avg resolution hours
- [x] POST /admin/dunning/resolve/:id — manual resolve with 404 guard
- [x] GET /admin/dunning/win-back — campaign list + aggregate stats
- [x] POST /admin/dunning/win-back/:tenantId — tenant existence check + insert record
- [x] billing.ts: annual_tiers added to pricing response (4 tiers, only in pricing handler)
- [x] index.ts: import dunning + mount at /admin/dunning

### Tests Status
- Type check: pass (0 errors — `npx tsc --noEmit`)
- Unit tests: n/a (no test suite exists for this service)
- Integration tests: n/a

### Issues Encountered
- index.ts had been updated since last read (onboarding route added); re-read before editing — no conflict

### Next Steps
- Polar webhook handler in billing.ts should emit dunning_events on `subscription.updated` with payment failure status
- win-back email dispatch (actual email send via Resend/SES) is not wired — POST /dunning/win-back/:tenantId records the intent but does not send; connect to email provider in follow-up wave
- Docs impact: minor (new admin endpoints, annual pricing)
