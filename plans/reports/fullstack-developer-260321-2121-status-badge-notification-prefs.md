# Phase Implementation Report

### Executed Phase
- Phase: status-badge + notification-preferences
- Plan: none (direct task)
- Status: completed

### Files Modified
| File | Lines | Action |
|------|-------|--------|
| `apps/raas-gateway/migrations/0040_notification_prefs.sql` | 18 | NEW |
| `apps/raas-gateway/src/routes/status-badge.ts` | 140 | NEW |
| `apps/raas-gateway/src/routes/notification-preferences.ts` | 169 | NEW |

### Tasks Completed
- [x] Migration `0040_notification_prefs.sql` — `notification_preferences` table with UNIQUE tenant_id, all specified columns, FK to tenants, index
- [x] `statusBadge` Hono router — 5 public endpoints:
  - `GET /badge/status` — SVG with KV cache 60s, DB health check → green/yellow
  - `GET /badge/status.json` — shields.io-compatible JSON
  - `GET /badge/uptime` — SVG from `uptime:current` KV key, defaults to 99.9%
  - `GET /badge/version` — SVG hardcoded v5.0.0
  - `GET /badge/missions` — SVG from DB count, KV-cached 5 min
- [x] `notificationPreferences` Hono router — 4 auth-guarded endpoints:
  - `GET /v1/notifications/preferences` — upsert default row, return formatted prefs
  - `PUT /v1/notifications/preferences` — partial update, validates emailDigest enum
  - `POST /v1/notifications/test` — email via EmailService or webhook via fetch, 422 if unconfigured
  - `GET /v1/notifications/channels` — parallel DB queries, returns 3 channels with config status

### Tests Status
- Type check: pass (tsc --noEmit → 0 errors)
- Unit tests: n/a (no test runner configured in raas-gateway)
- Integration tests: n/a

### Issues Encountered
- None. File size reduced from 252 → 169 lines by tightening interface definitions and condensing imports.
- `statusBadge` and `notificationPreferences` routers are NOT yet registered in `src/routes/index.ts` — that file is outside this task's file ownership boundary. The consuming phase must add:
  ```ts
  import { statusBadge } from './status-badge';
  import { notificationPreferences } from './notification-preferences';
  // ...
  routes.route('/badge', statusBadge);
  routes.route('/v1/notifications', notificationPreferences);
  ```

### Next Steps
- Route registration in `src/routes/index.ts` required before endpoints are live
- `uptime:current` KV key needs to be populated by a scheduled job or status update flow
- `webhook_url` column assumed to exist on `tenants` table (used in test + channels endpoints)

### Unresolved Questions
- Is `webhook_url` already a column on `tenants`? If not, a migration is needed before the test/channels endpoints work correctly.
- Should `/badge/*` routes be mounted at a different prefix (e.g. `/status/badge`)?
