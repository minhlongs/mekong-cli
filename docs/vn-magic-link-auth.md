# VN Hub — Magic-Link Auth

Phase 9 P01. Passwordless email authentication for the VN Hub platform.

## Overview

Two public endpoints:

```
POST /v1/auth/magic-link   — request a login link (enumeration-safe, rate-limited)
GET  /v1/auth/verify        — exchange token for 24h JWT
```

No passwords. No OAuth. A 15-minute single-use link sent to the user's email.

---

## Required Environment Variables

Add to `/Library/LaunchDaemons/com.mekong.gateway.plist`:

```xml
<key>EnvironmentVariables</key>
<dict>
  <!-- Resend.com API key (required for sending) -->
  <key>RESEND_API_KEY</key>
  <string>re_xxxxxxxxxxxxxxxxxxxx</string>

  <!-- Sender address — must be on a Resend-verified domain -->
  <key>MEKONG_MAGIC_LINK_FROM</key>
  <string>noreply@mekong.dev</string>

  <!-- Public base URL used to construct the verify link in the email -->
  <key>MEKONG_PUBLIC_BASE_URL</key>
  <string>https://api.mekong.dev</string>

  <!-- Existing — used for JWT signing -->
  <key>MEKONG_JWT_SECRET</key>
  <string>your-secret-here-min-32-chars</string>
</dict>
```

Reload: `sudo launchctl kickstart -k system/com.mekong.gateway`

---

## API Contract

### POST /v1/auth/magic-link

**Request:**
```json
{ "email": "boss@acme.vn", "purpose": "login" }
```

`purpose` values: `"login"` (default) | `"signup"` | `"join_invite"`

**Response (always 200):**
```json
{ "ok": true, "message": "Nếu email tồn tại, liên kết đăng nhập đã được gửi." }
```

Behavior:
- Returns 200 regardless of whether `email` is registered (enumeration resistance)
- Sends email in a BackgroundTask (non-blocking, fire-and-forget)
- Rate limit: 5 tokens per email per hour. 6th request → 200, no email sent
- Invalid email format → 422

### GET /v1/auth/verify?token=...

**Success (200):**
```json
{
  "ok": true,
  "jwt": "eyJhbGc...",
  "expires_at": "2026-05-19T03:00:00Z",
  "scopes": ["org_admin"],
  "allowed_orgs": ["acme-org"]
}
```

New user (no org memberships):
```json
{
  "ok": true,
  "jwt": "eyJhbGc...",
  "expires_at": "2026-05-19T03:00:00Z",
  "scopes": ["none"],
  "allowed_orgs": []
}
```

**Failure (401):**
```json
{ "detail": { "error": "invalid_or_expired_link" } }
```

Single error code for all failure modes (expired, already used, not found) — no info leak.

---

## JWT Claim Shape

```json
{
  "sub": "boss@acme.vn",
  "scopes": ["org_admin"],
  "allowed_orgs": ["acme-org"],
  "iat": 1716000000,
  "exp": 1716086400
}
```

- `scopes`: union of all `org_members.scope` rows for the email. `["none"]` if new user.
- `allowed_orgs`: list of `org_id` values the user belongs to.
- TTL: 24 hours.
- Algorithm: HS256, signed with `MEKONG_JWT_SECRET`.

---

## Vietnamese Email Template

**Subject:** `Liên kết đăng nhập Mekong Hub của bạn`

**Body (HTML + plaintext fallback, VN-only):**
- Greeting + action button ("Đăng nhập")
- Magic URL as text fallback
- Disclaimer: link expires in 15 minutes, single-use

---

## Rate Limit

- Max 5 tokens per email per hour (rolling window)
- Checked via SQLite `COUNT(*)` on indexed `(email, created_at)` — DB-backed, no in-memory state
- Multi-host limitation: rate limit is per-host (single SQLite file). For multi-host deployments,
  move rate limit to Redis/shared DB. Acceptable for V1 single-host M1 gateway.
- Over-cap requests: 200 returned, no email sent, audit log entry written

---

## Resend.com Domain Verification

1. Login at https://resend.com/domains
2. Add your domain (e.g. `mekong.dev`)
3. Add DNS records shown by Resend:
   - **SPF**: TXT record on `@` or subdomain
   - **DKIM**: TXT record (CNAME for auto-rotation)
   - **DMARC**: TXT record `v=DMARC1; p=quarantine; rua=mailto:you@mekong.dev`
4. Wait for DNS propagation (usually < 10 min on Cloudflare)
5. Click "Verify" in Resend dashboard
6. Update `MEKONG_MAGIC_LINK_FROM` to match the verified domain

---

## Curl Smoke Checks

```bash
# Request a magic link
curl -s -X POST https://api.mekong.dev/v1/auth/magic-link \
  -H "Content-Type: application/json" \
  -d '{"email":"boss@acme.vn","purpose":"login"}' | jq .

# Verify token (copy from email)
TOKEN="paste-token-from-email-here"
curl -s "https://api.mekong.dev/v1/auth/verify?token=$TOKEN" | jq .

# Decode JWT (verify claims shape)
JWT=$(curl -s "https://api.mekong.dev/v1/auth/verify?token=$TOKEN" | jq -r .jwt)
echo "$JWT" | cut -d. -f2 | base64 -d 2>/dev/null | jq .
```

---

## Token GC

`magic_link_tokens` rows accumulate over time. The `purge_expired()` function
deletes tokens expired more than 24 hours ago. Wire it into the daily cron:

```python
# In scripts/check-org-trials.py (P05 cron — DRY)
from src.services.magic_link_service import purge_expired
deleted = purge_expired(grace_hours=24)
print(f"Purged {deleted} expired magic link tokens")
```
