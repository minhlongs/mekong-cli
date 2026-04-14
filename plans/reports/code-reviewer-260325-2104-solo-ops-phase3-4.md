# Code Review: Solo Ops Phase 3+4 (Group B)

**Date:** 2026-03-25 | **Reviewer:** code-reviewer agent
**Scope:** Drip email retention + upsell, stats server, standup script

## Files Reviewed

| File | LOC | Status |
|------|-----|--------|
| `apps/raas-gateway/src/services/drip-email-scheduler.ts` | 193 | Modified |
| `scripts/solo-ops-stats-server.mjs` | 187 | New |
| `scripts/generate-daily-standup.sh` | 95 | New |

**Total LOC:** 475 | All files under 200-line limit.

## Overall Assessment

Solid additions. Drip scheduler well-structured with idempotent design. Stats server clean, uses only Node.js built-ins. Shell script handles missing files. Two critical issues found: **SQL injection** in drip scheduler and **migration schema mismatch** for new steps.

---

## CRITICAL Issues

### 1. SQL Injection via tenant ID interpolation (drip-email-scheduler.ts:87)

```typescript
const ids = tenants.map((t) => `'${t.id}'`).join(',');
const { results: sentRows } = await db
  .prepare(`SELECT tenant_id, step FROM drip_emails WHERE tenant_id IN (${ids})`)
  .all<{ tenant_id: string; step: string }>();
```

**Problem:** Tenant IDs from DB are string-interpolated into SQL without parameterization. If a tenant ID ever contains a single quote (e.g., from a corrupted insert or UUID edge case), this is exploitable SQL injection. D1 `.prepare()` with `.bind()` should be used instead.

**Fix:** Use parameterized placeholders:
```typescript
const placeholders = tenants.map(() => '?').join(',');
const { results: sentRows } = await db
  .prepare(`SELECT tenant_id, step FROM drip_emails WHERE tenant_id IN (${placeholders})`)
  .bind(...tenants.map(t => t.id))
  .all<{ tenant_id: string; step: string }>();
```

**Severity:** CRITICAL -- OWASP A03 Injection

### 2. Migration schema mismatch -- new steps not in CHECK constraint (migration 0280)

```sql
CHECK(step IN ('day0', 'day2', 'day5', 'day7'))
```

Code now inserts `day14`, `day30`, `upsell` steps, but migration 0280 has a CHECK constraint limiting to only 4 original values. INSERTs for new steps will **fail silently** or throw constraint violation.

**Fix:** Create migration 0281 to ALTER the CHECK constraint:
```sql
-- Migration: 0281_drip_emails_add_retention_steps
-- Recreate table with updated CHECK (SQLite doesn't support ALTER CHECK)
ALTER TABLE drip_emails RENAME TO drip_emails_old;
CREATE TABLE drip_emails (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  step TEXT NOT NULL CHECK(step IN ('day0','day2','day5','day7','day14','day30','upsell')),
  sent_at TEXT DEFAULT (datetime('now')),
  UNIQUE(tenant_id, step),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
INSERT INTO drip_emails SELECT * FROM drip_emails_old;
DROP TABLE drip_emails_old;
CREATE INDEX IF NOT EXISTS idx_drip_emails_tenant ON drip_emails(tenant_id);
```

**Severity:** CRITICAL -- new drip steps will fail at runtime

---

## HIGH Priority

### 3. XSS risk in email HTML templates (drip-email-scheduler.ts:151-181)

`tenant.name`, `tenant.used_credits`, `tenant.tier` are interpolated directly into HTML:
```typescript
`<h2>${subject}</h2><p>${body}</p>`
`<strong>${used_credits}/${limit}</strong> credits (${pct}%) on your ${tier} plan`
```

`used_credits` and `pct` are numbers (safe). But `name` and `tier` are strings from DB -- if a tenant registers with `name = "<script>alert(1)</script>"`, this renders in email clients. Most email clients strip `<script>`, but SVG/event-handler XSS variants can bypass.

**Fix:** Add HTML escaping utility:
```typescript
function esc(s: string): string {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
```
Apply to all `name` and `tier` interpolations in email templates.

**Severity:** HIGH -- email XSS, mitigated by most email clients but not all

### 4. Stats server: error message leaks stack info (solo-ops-stats-server.mjs:151)

```javascript
res.end(JSON.stringify({ error: err.message }));
```

`err.message` may contain file paths or internal details. For a local-only dashboard this is low risk, but if port 3001 is ever exposed:

**Fix:** Return generic error or sanitize:
```javascript
res.end(JSON.stringify({ error: 'Internal server error' }));
console.error('[stats] API error:', err);
```

### 5. Stats server: no host binding -- listens on 0.0.0.0 (solo-ops-stats-server.mjs:173)

```javascript
server.listen(PORT, () => { ... });
```

Without specifying host, Node.js binds to all interfaces (0.0.0.0). On M1 Max with LAN, anyone on the network can access the dashboard.

**Fix:**
```javascript
server.listen(PORT, '127.0.0.1', () => { ... });
```

---

## MEDIUM Priority

### 6. Cutoff window calculation is correct but tight

40-day cutoff (line 74) covers Day 30 + 7-day stale window (maxDays=37) with 3-day margin. Acceptable, but if future steps extend beyond Day 37, this needs updating. Consider deriving from DRIP_STEPS:

```typescript
const maxCutoffDays = Math.max(...DRIP_STEPS.map(s => s.maxDays)) + 3;
```

### 7. readHealthLog reads entire file into memory (solo-ops-stats-server.mjs:34)

```javascript
const lines = readFileSync(path, 'utf8').trim().split('\n').filter(Boolean);
return lines.length ? JSON.parse(lines[lines.length - 1]) : null;
```

If `health.jsonl` grows large (months of data), this loads the entire file to read only the last line. For a local dashboard with 30s refresh, this compounds.

**Fix:** Use `readFileSync` with a reverse buffer reader, or limit the file via logrotate. Low urgency for now.

### 8. Standup script: `bc` dependency not checked (generate-daily-standup.sh:45)

```bash
UPTIME_PCT=$(echo "scale=1; ($LOOPS_OK * 100) / $TOTAL_RUNS" | bc 2>/dev/null || echo "N/A")
```

`bc` fallback to "N/A" is correct (the `|| echo "N/A"` handles it). Good defensive coding. No action needed.

### 9. Standup script: grep -c "Executing:" pattern coupling (generate-daily-standup.sh:29)

If the heartbeat log format changes (e.g., "Executing:" becomes "Running:"), counts break silently to 0. Consider documenting the expected log format.

---

## LOW Priority

### 10. DripStep union type includes 'upsell' but sendStep handles it redundantly

`sendStep` case `'upsell'` calls `this.sendUpsell(tenant)`, but upsell is also handled separately in the main loop (line 112-123). The `sendStep` upsell case is dead code -- it's never reached because upsell is checked outside the DRIP_STEPS loop.

Not harmful, but misleading. Remove `case 'upsell'` from `sendStep` or unify the logic.

### 11. Dashboard CSS is inline in JS (solo-ops-stats-server.mjs:113)

Single long string. Acceptable for a local tool. Would benefit from template literals with better formatting if it grows.

---

## Edge Cases Found by Scout

1. **drip_emails table FK + CHECK**: New steps (`day14`, `day30`, `upsell`) will violate the CHECK constraint in migration 0280. This is a **runtime blocker**.
2. **Upsell fires once, forever**: Upsell is recorded with `INSERT OR IGNORE` and never re-triggers. If a tenant downgrades then returns to >80%, they won't get a second upsell. Intentional? If not, consider a time-based reset.
3. **Day 7 and Day 14 overlap window**: day7 maxDays=14, day14 minDays=14. At exactly 14 days, both day7 (if not sent) and day14 could fire in the same run. Not a bug (both needed), but worth noting.
4. **Stats server `probeEndpoint`**: If all 3 endpoints are down, `buildKpis()` takes ~9s (3 x 3s timeout). HTTP request will hang. Consider reducing timeout to 1.5s or running probes in parallel (already parallel via Promise.all -- this is fine, max wait is 3s).
5. **Standup script KPI file write**: Non-atomic write via heredoc. If stats server reads mid-write, it gets partial JSON. Low risk (30s refresh vs instantaneous write), but `mktemp` + `mv` would be safer.

---

## Positive Observations

- Idempotent drip design via `drip_emails` table + `INSERT OR IGNORE` -- solid pattern
- Clean separation: scheduler handles logic, EmailService handles delivery
- Stats server uses only Node.js built-ins (http, fs, path) -- no dependencies
- Shell script uses `set -euo pipefail` and handles missing log files gracefully
- `bc` fallback with `|| echo "N/A"` is good defensive bash
- EADDRINUSE error handling on stats server -- nice UX touch
- Auto-refresh dashboard at 30s interval -- appropriate for monitoring

---

## Recommended Actions (Priority Order)

1. **[CRITICAL]** Create migration 0281 to update CHECK constraint with new step values
2. **[CRITICAL]** Fix SQL injection -- use parameterized `IN (?)` query
3. **[HIGH]** Add HTML escaping for tenant name/tier in email templates
4. **[HIGH]** Bind stats server to 127.0.0.1 only
5. **[MEDIUM]** Derive cutoff window dynamically from DRIP_STEPS config
6. **[LOW]** Remove dead `case 'upsell'` from sendStep switch

## Metrics

- Type Coverage: Good -- TenantRow, DripStep, DripStepConfig all typed
- Test Coverage: No tests found for new drip steps or stats server
- Linting Issues: 0 syntax errors detected
- File Size: All 3 files under 200 lines

## Unresolved Questions

1. Is the single-fire upsell intentional? Should it re-trigger after X days if usage remains high?
2. Should the stats server require basic auth if it may be exposed beyond localhost?
3. Is migration 0281 already planned but not yet committed?
