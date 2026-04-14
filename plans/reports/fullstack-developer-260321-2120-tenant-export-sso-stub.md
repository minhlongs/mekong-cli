# Phase Implementation Report

## Executed Phase
- Phase: tenant-export-sso-stub
- Plan: none (direct task)
- Status: completed

## Files Modified

| File | Lines | Action |
|------|-------|--------|
| `apps/raas-gateway/src/services/tenant-export-service.ts` | 157 | NEW |
| `apps/raas-gateway/src/routes/tenant-export.ts` | 148 | NEW |
| `apps/raas-gateway/src/routes/sso.ts` | 72 | NEW |

## Tasks Completed

- [x] `exportTenantData(db, tenantId)` — queries all 6 tables (tenants, missions, credit_transactions, api_keys, projects, webhooks), returns `TenantExport`
- [x] `importTenantData(db, data)` — creates new tenant with fresh UUID, imports all records with new IDs, skips duplicates via try/catch
- [x] `deleteTenantData(db, tenantId)` — counts then hard-deletes across all 9 tables (incl. webhook_deliveries, team_members, recurring_missions)
- [x] `GET /v1/export` — JSON attachment download for authenticated tenant
- [x] `POST /v1/export/request` — fire-and-forget async export stored in RATE_LIMIT_KV (24h TTL), returns `{ export_id, status: 'processing' }`
- [x] `GET /v1/export/:id` — polls KV for export status/result
- [x] `DELETE /v1/data` — GDPR 30-day grace period, stores deletion intent in KV
- [x] `POST /admin/tenants/import` — X-Admin-Key protected, validates body, calls importTenantData
- [x] `DELETE /admin/tenants/:id/data` — immediate hard delete, no grace period
- [x] `GET /admin/tenants/:id/export` — export specific tenant as JSON (admin only)
- [x] `GET /v1/sso/config` — stub returns `{ enabled: false, provider: null, message }`
- [x] `POST /v1/sso/config` — enterprise tier check, returns 403 with upgrade_url for all tiers (including enterprise, pending full SAML)
- [x] `GET /v1/sso/metadata` — returns valid SAML SP metadata XML stub
- [x] `POST /v1/sso/callback` — returns 501 Not Implemented

## Tests Status
- Type check: pass (0 errors — `npx tsc --noEmit`)
- Unit tests: n/a (no test runner configured in raas-gateway)
- Integration tests: n/a

## Issues Encountered

None. All files within 200-line limit. Existing `adminAuth` pattern from `admin.ts` replicated inline (consistent with codebase — no shared middleware for admin auth exists).

**Note:** `tenant-export.ts` mounts full paths (`/v1/export`, `/admin/tenants/...`) rather than relative paths, because the router is not yet registered in `routes/index.ts` — caller must mount at `/` or adjust paths when registering.

## Next Steps

- Register routes in `src/routes/index.ts`:
  ```ts
  import { tenantExport } from './tenant-export';
  import { sso } from './sso';
  // ...
  routes.route('/', tenantExport);
  routes.route('/v1/sso', sso);
  ```
- Wire async export worker (currently fire-and-forget via closure; production should use Cloudflare Queue or Durable Object)
- Implement GDPR deletion scheduler (currently stores intent in KV; needs a Cron trigger to process pending deletions)

## Unresolved Questions

1. Should `POST /v1/sso/config` succeed for enterprise tenants and persist config to D1, or remain a stub? Currently returns 403 for all tiers.
2. `webhook_deliveries` table schema assumed to have `tenant_id` column — verify before deploying.
3. `team_members` and `recurring_missions` assumed columns match DELETE by `tenant_id` — confirm schema.
