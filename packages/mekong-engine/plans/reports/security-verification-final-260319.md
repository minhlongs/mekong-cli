# Security Verification Report - P0/P1 Fixes

**Date:** 2026-03-19
**Scope:** mekong-engine API routes
**Files Verified:** `src/routes/billing.ts`, `src/routes/chat.ts`

---

## Verification Checklist Results

### 1. billing.ts - POST /billing/tenants/regenerate-key

| Check | Status | Evidence |
|-------|--------|----------|
| authRateLimit() middleware applied | ✅ **PASS** | Line 40: `billingRoutes.post('/tenants/regenerate-key', authRateLimit(), handleAsync(async (c) => {` |
| Zod validation on request body | ✅ **PASS** | Lines 42-43: `regenerateKeySchema.safeParse()` with schema defined at lines 20-23 |

**Summary:** Both P0 security controls correctly applied.

---

### 2. billing.ts - POST /billing/webhook (Polar.sh)

| Check | Status | Evidence |
|-------|--------|----------|
| webhookRateLimit() middleware applied | ✅ **PASS** | Line 71: `billingRoutes.post('/webhook', webhookRateLimit(), handleAsync(async (c) => {` |
| ensureWebhookEventsTable() called at start | ✅ **PASS** | Line 74: `await ensureWebhookEventsTable(db)` |
| isDuplicateWebhookEvent() check before processing | ✅ **PASS** | Lines 104-113: Duplicate check with `isDuplicateWebhookEvent(db, 'polar', event.id)` |
| recordWebhookEvent() called after processing | ✅ **PASS** | Lines 164-170: `recordWebhookEvent(db, 'polar', event.id, event.type)` |

**Additional Security Controls Found:**
- Signature verification (lines 80-93)
- Timestamp validation for replay attack prevention (lines 116-127)

**Summary:** All P0 security controls correctly applied + bonus timestamp validation.

---

### 3. chat.ts - POST /webhook/zalo

| Check | Status | Evidence |
|-------|--------|----------|
| webhookRateLimit() middleware applied | ✅ **PASS** | Line 13: `chatRoutes.post('/webhook/zalo', webhookRateLimit(), handleAsync(async (c) => {` |
| msg_id duplicate check before processing | ✅ **PASS** | Lines 60-73: Duplicate check using `db.prepare('SELECT id FROM webhook_events WHERE provider = ? AND event_id = ?').bind('zalo', msgId).first()` |
| webhook_events record after processing | ✅ **PASS** | Lines 99-108: `db.prepare('INSERT INTO webhook_events (id, provider, event_id, type) VALUES (?, ?, ?, ?)').bind(crypto.randomUUID(), 'zalo', msgId, 'message').run()` |

**Additional Security Controls Found:**
- HMAC signature verification (lines 17-39)

**Summary:** All P0 security controls correctly applied.

---

### 4. chat.ts - POST /webhook/facebook

| Check | Status | Evidence |
|-------|--------|----------|
| webhookRateLimit() middleware applied | ✅ **PASS** | Line 126: `chatRoutes.post('/webhook/facebook', webhookRateLimit(), handleAsync(async (c) => {` |
| mid duplicate check before processing | ✅ **PASS** | Lines 175-188: Duplicate check using `db.prepare('SELECT id FROM webhook_events WHERE provider = ? AND event_id = ?').bind('facebook', mid).first()` |
| webhook_events record after processing | ✅ **PASS** | Lines 213-222: `db.prepare('INSERT INTO webhook_events (id, provider, event_id, type) VALUES (?, ?, ?, ?)').bind(crypto.randomUUID(), 'facebook', mid, 'message').run()` |

**Additional Security Controls Found:**
- Facebook signature verification (lines 130-153)

**Summary:** All P0 security controls correctly applied.

---

## Overall Assessment

| Route | P0/P1 Controls | Additional Controls | Status |
|-------|----------------|---------------------|--------|
| POST /billing/tenants/regenerate-key | 2/2 | - | ✅ GREEN |
| POST /billing/webhook | 4/4 | Signature, Timestamp | ✅ GREEN |
| POST /webhook/zalo | 3/3 | Signature | ✅ GREEN |
| POST /webhook/facebook | 3/3 | Signature | ✅ GREEN |

**Total:** 12/12 security controls verified ✅

---

## Security Controls Summary

### Rate Limiting
- `authRateLimit()` applied to authenticated endpoints
- `webhookRateLimit()` applied to all webhook endpoints

### Input Validation
- Zod schemas for all POST body validation
- Safe parsing with `.safeParse()` and error handling

### Replay Attack Prevention
- Webhook events table created on startup
- Duplicate event ID checks before processing
- Event recording after successful processing
- Timestamp validation (5-minute window) on Polar webhook

### Signature Verification
- Polar.sh HMAC-SHA256 verification
- Zalo OA signature verification
- Facebook Messenger signature verification

---

## Unresolved Questions

None. All P0/P1 security fixes verified as correctly implemented.
