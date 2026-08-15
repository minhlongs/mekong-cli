# Security Review: P0/P1 API Hardening Fixes

**Date:** 2026-03-19
**Reviewer:** code-reviewer agent
**Scope:** `src/routes/billing.ts`, `src/routes/chat.ts`
**Focus:** Rate limiting, replay attack prevention, HMAC verification

---

## Executive Summary

**Rating: FAIL** - Critical security fixes NOT fully implemented

While the security patterns are correctly designed in the middleware, the actual application of these fixes to the target routes is **INCOMPLETE**.

---

## Critical Findings

### FAIL #1: `billing.ts` - authRateLimit NOT applied to regenerate-key endpoint

**Expected:**
```typescript
billingRoutes.post('/tenants/regenerate-key', authRateLimit(), handleAsync(async (c) => {
```

**Actual (line 39):**
```typescript
billingRoutes.post('/tenants/regenerate-key', handleAsync(async (c) => {
```

**Impact:** Brute force attacks on API key regeneration remain possible. Attacker can spam tenant_id + name combinations without rate limiting.

**Fix Required:** Add `authRateLimit()` middleware to line 39.

---

### FAIL #2: `billing.ts` - Polar webhook missing replay protection

**Expected:**
```typescript
// Check event.id before processing
const isDuplicate = await db.prepare(
  'SELECT id FROM webhook_events WHERE provider = ? AND event_id = ?'
).bind('polar', event.id).first()

// Record after processing
await db.prepare(
  'INSERT INTO webhook_events (id, provider, event_id, type) VALUES (?, ?, ?, ?)'
).bind(crypto.randomUUID(), 'polar', event.id, 'order').run()
```

**Actual:** No replay protection code exists in `/billing/webhook` route (lines 70-150).

**Impact:** Attacker can replay Polar webhook events to grant duplicate credits.

**Fix Required:**
1. Add `webhookRateLimit()` middleware
2. Add duplicate check before processing `order.paid` event
3. Add record insertion after successful processing

---

### PASS #1: `chat.ts` - Zalo webhook replay protection implemented

**Implementation (lines 60-73, 99-108):**
```typescript
// Check BEFORE processing
const isDuplicate = await handleDb(
  () => db.prepare('SELECT id FROM webhook_events WHERE provider = ? AND event_id = ?')
    .bind('zalo', msgId).first(),
  ...
)
if (isDuplicate) {
  return c.json({ error: 'Duplicate message detected', code: 'REPLAY_ATTACK' }, 409)
}

// Record AFTER processing
if (msgId) {
  await handleDb(
    () => db.prepare('INSERT INTO webhook_events (id, provider, event_id, type) VALUES (?, ?, ?, ?)')
      .bind(crypto.randomUUID(), 'zalo', msgId, 'message').run(),
    ...
  )
}
```

**Verification:**
- Rate limiting: `webhookRateLimit()` applied (line 13)
- Duplicate check: Before processing (lines 63-73)
- Recording: After processing (lines 100-108)
- HMAC signature: Correctly implemented (lines 20-38)

**Status:** PASS

---

### PASS #2: `chat.ts` - Facebook webhook replay protection implemented

**Implementation (lines 175-188, 213-222):**
```typescript
// Check BEFORE processing
const isDuplicate = await handleDb(
  () => db.prepare('SELECT id FROM webhook_events WHERE provider = ? AND event_id = ?')
    .bind('facebook', mid).first(),
  ...
)
if (isDuplicate) {
  continue // Skip duplicate
}

// Record AFTER processing
if (mid) {
  await handleDb(
    () => db.prepare('INSERT INTO webhook_events (id, provider, event_id, type) VALUES (?, ?, ?, ?)')
      .bind(crypto.randomUUID(), 'facebook', mid, 'message').run(),
    ...
  )
}
```

**Verification:**
- Rate limiting: `webhookRateLimit()` applied (line 126)
- Duplicate check: Before processing (lines 177-187)
- Recording: After processing (lines 214-222)
- HMAC signature: Correctly implemented (lines 134-152)

**Status:** PASS

---

## Schema Gap: `webhook_events` table NOT found

**Issue:** No migration file creates the `webhook_events` table that chat.ts depends on.

**Searched:**
- `migrations/0001_init_raas_schema.sql` - NOT FOUND
- All migration files (0001-0011) - NO MATCH for `webhook_events`

**Required Schema:**
```sql
CREATE TABLE IF NOT EXISTS webhook_events (
  id TEXT PRIMARY KEY,
  provider TEXT NOT NULL,
  event_id TEXT NOT NULL,
  type TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  processed_at TEXT,
  UNIQUE(provider, event_id)
);

CREATE INDEX IF NOT EXISTS idx_webhook_events_provider_event ON webhook_events(provider, event_id);
```

**Impact:** Replay protection will fail at runtime - table doesn't exist.

---

## Security Assessment by Category

| Category | Status | Notes |
|----------|--------|-------|
| Rate limiting middleware | PARTIAL | Correctly designed in `rate-limit-middleware.ts`, NOT applied to billing routes |
| Replay attack prevention | PARTIAL | Correctly implemented in chat.ts, MISSING in billing.ts |
| HMAC signature verification | PASS | Both Zalo and Facebook implement secure HMAC-SHA256 |
| Error handling | PASS | `handleDb()` and `handleAsync()` wrappers properly used |
| Database schema | FAIL | `webhook_events` table migration missing |

---

## Medium Priority Issues

### M1: Timestamp validation on Polar webhook (lines 101-113)

**Current:**
```typescript
const timestamp = event.timestamp ?? event.created_at
if (timestamp) {
  const eventTime = new Date(timestamp).getTime()
  const now = Date.now()
  const age = now - eventTime
  if (age > 5 * 60 * 1000) { // 5 minutes
    return c.json({ error: 'Webhook timestamp too old...', code: 'REPLAY_ATTACK' }, 401)
  }
}
```

**Issue:** Timestamp check is good BUT relies on client-provided timestamp which can be spoofed. Combined with event.id deduplication, this provides defense-in-depth. Without event.id check, timestamp alone is insufficient.

**Status:** Acceptable as secondary control, but NOT a replacement for event.id deduplication.

---

### M2: Facebook webhook silently skips duplicates (line 186)

**Current:**
```typescript
if (isDuplicate) {
  continue // Skip duplicate but continue processing other events
}
```

**Issue:** Silent skip makes debugging harder. Should log duplicate detection for audit trail.

**Recommendation:** Add logging:
```typescript
if (isDuplicate) {
  console.log(`Duplicate Facebook message skipped: ${mid}`)
  continue
}
```

---

## Positive Observations

1. **HMAC implementation is correct** - Both Zalo and Facebook use proper HMAC-SHA256 with constant-time comparison via string equality on hex strings.

2. **Rate limit middleware design is sound** - Uses sliding window with KV storage, proper TTL, returns `Retry-After` header.

3. **Error handling wrappers** - `handleDb()` and `handleAsync()` provide consistent error responses without leaking stack traces.

4. **Zod validation** - Input validation present on billing endpoints (lines 14-22, 27-28, 41-42).

---

## Required Fixes (Prioritized)

### P0 - CRITICAL (Fix before deployment)

1. **Add authRateLimit to billing.ts line 39:**
   ```typescript
   billingRoutes.post('/tenants/regenerate-key', authRateLimit(), handleAsync(async (c) => {
   ```

2. **Add webhookRateLimit to billing.ts line 70:**
   ```typescript
   billingRoutes.post('/webhook', webhookRateLimit(), handleAsync(async (c) => {
   ```

3. **Add replay protection to Polar webhook (after line 99):**
   ```typescript
   // Check for replay attack
   const eventId = event.id
   if (eventId) {
     const isDuplicate = await db.prepare(
       'SELECT id FROM webhook_events WHERE provider = ? AND event_id = ?'
     ).bind('polar', eventId).first()
     if (isDuplicate) {
       return c.json({ error: 'Duplicate webhook event', code: 'REPLAY_ATTACK' }, 409)
     }
   }

   // ... process event ...

   // Record after processing
   if (eventId) {
     await db.prepare(
       'INSERT INTO webhook_events (id, provider, event_id, type) VALUES (?, ?, ?, ?)'
     ).bind(crypto.randomUUID(), 'polar', eventId, event.type).run()
   }
   ```

4. **Create migration file `migrations/0012_webhook_events_table.sql`:**
   ```sql
   CREATE TABLE IF NOT EXISTS webhook_events (
     id TEXT PRIMARY KEY,
     provider TEXT NOT NULL,
     event_id TEXT NOT NULL,
     type TEXT NOT NULL,
     created_at TEXT NOT NULL DEFAULT (datetime('now')),
     processed_at TEXT,
     UNIQUE(provider, event_id)
   );

   CREATE INDEX IF NOT EXISTS idx_webhook_events_provider_event
     ON webhook_events(provider, event_id);
   ```

---

## Verification Commands

After fixes applied, verify:

```bash
# 1. Check authRateLimit is applied
grep -n "authRateLimit()" src/routes/billing.ts

# 2. Check webhookRateLimit is applied
grep -n "webhookRateLimit()" src/routes/billing.ts

# 3. Check replay protection in billing.ts
grep -n "webhook_events" src/routes/billing.ts

# 4. Check migration exists
ls -la migrations/0012_webhook_events_table.sql

# 5. Run migrations
npx wrangler d1 execute <DATABASE> --local --file=migrations/0012_webhook_events_table.sql
```

---

## Summary

| Route | Rate Limiting | Replay Protection | HMAC | Status |
|-------|---------------|-------------------|------|--------|
| POST /billing/tenants/regenerate-key | MISSING | N/A | N/A | FAIL |
| POST /billing/webhook (Polar) | MISSING | MISSING | PASS | FAIL |
| POST /webhook/zalo | PASS | PASS | PASS | PASS |
| POST /webhook/facebook | PASS | PASS | PASS | PASS |

**Overall: FAIL** - 2 of 4 security fixes incomplete.

**Blocking Issues:**
- `authRateLimit` not imported or applied in billing.ts
- `webhookRateLimit` not applied to Polar webhook
- No replay protection on Polar webhook
- `webhook_events` table migration missing

---

## Next Steps

1. Apply P0 fixes listed above
2. Create and run migration for `webhook_events` table
3. Re-run this security review
4. Add integration tests for:
   - Rate limiting on regenerate-key endpoint
   - Replay attack detection on all webhooks
   - HMAC signature validation failures
