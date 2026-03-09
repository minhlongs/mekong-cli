---
title: "Phase 6: CLI License Activation Implementation"
description: "Implement `mekong auth activate --key=mk_...` command with secure storage, gateway validation, offline caching, and rate limit enforcement"
status: pending
priority: P1
effort: 8h
branch: master
tags: [raas, license, cli, phase6, auth, gateway]
created: 2026-03-09
---

# Phase 6: CLI License Activation

## Overview

Implement CLI-native license activation with secure storage, RaaS Gateway validation, offline resilience, and rate limiting.

## Key Insights from Codebase Analysis

### Existing Infrastructure (Already Implemented)

| Component | File | Status |
|-----------|------|--------|
| Secure Storage | `src/auth/secure_storage.py` | ✅ Complete - macOS Keychain, Windows Vault, Linux AES-256 |
| RaaS Auth Client | `src/core/raas_auth.py` | ✅ Complete - JWT/mk_ validation, session cache, circuit breaker |
| Gateway Client | `src/core/gateway_client.py` | ✅ Complete - Multi-gateway failover, rate limiting |
| Rate Limit Client | `src/core/rate_limit_client.py` | ✅ Complete - 429 handling, exponential backoff |
| Auth CLI Commands | `src/cli/raas_auth_commands.py` | ✅ Complete - login/logout/status/validate |
| License Commands | `src/commands/license_commands.py` | ✅ Complete - generate/validate/revoke/status/usage |

### Gap Analysis: What's Missing for Phase 6

1. **No `activate` command** - Current flow uses `mekong auth login` but lacks explicit "activation" semantics
2. **No offline validation cache** - Session cache exists but needs explicit offline mode support
3. **No explicit KV-based rate limit enforcement** - Client handles 429 but lacks proactive KV checks
4. **No dashboard sync handshake** - Missing web dashboard activation confirmation

## Architecture

### Validation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  mekong auth activate --key=mk_...                              │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: Secure Storage                                         │
│  - Store mk_... key in platform secure storage                  │
│  - macOS: Keychain | Windows: Credential Vault | Linux: AES-256 │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: Gateway Validation (raas.agencyos.network)             │
│  - POST /v1/auth/validate with X-Cert-ID, X-Cert-Sig            │
│  - Circuit breaker failover: primary → secondary → tertiary     │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: Session Cache (TTL: 5min)                              │
│  - Cache tenant_id, tier, role, features, expires_at            │
│  - Auto-refresh 1min before expiry                              │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: Dashboard Handoff                                      │
│  - Return activation URL: agencyos.network/dashboard/{tenant_id}│
│  - Sync activation event via webhook (async)                    │
└─────────────────────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 5: Rate Limit Initialization                              │
│  - Parse X-RateLimit-Limit, X-RateLimit-Remaining               │
│  - Initialize local token bucket                                │
└─────────────────────────────────────────────────────────────────┘
```

### Offline Resilience

```
┌─────────────────────────────────────────────────────────────────┐
│  Offline Detection & Fallback                                   │
├─────────────────────────────────────────────────────────────────┤
│  1. Gateway unreachable (3 consecutive failures)                │
│  2. Check session cache validity (TTL not expired)              │
│  3. If valid: allow operation with OFFLINE warning              │
│  4. Queue activation event for sync when online                 │
│  5. Background sync daemon retries every 5min                   │
└─────────────────────────────────────────────────────────────────┘
```

### Rate Limit Integration (KV-based)

```
┌─────────────────────────────────────────────────────────────────┐
│  Rate Limit Enforcement                                         │
├─────────────────────────────────────────────────────────────────┤
│  Tier       | Limit/min | Burst |KV Key Format                 │
│  free       | 10        | 5     | rl:{tenant_id}:free          │
│  trial      | 30        | 10    | rl:{tenant_id}:trial         │
│  pro        | 100       | 25    | rl:{tenant_id}:pro           │
│  enterprise | 1000      | 100   | rl:{tenant_id}:enterprise    │
└─────────────────────────────────────────────────────────────────┘
```

## Files to Create

| File | Purpose |
|------|---------|
| `src/cli/activate_commands.py` | New `mekong auth activate` command |
| `src/core/offline_cache.py` | Offline validation cache manager |
| `src/core/activation_sync.py` | Dashboard sync webhook bridge |

## Files to Modify

| File | Changes |
|------|---------|
| `src/cli/raas_auth_commands.py` | Add `activate` subcommand or alias |
| `src/core/raas_auth.py` | Add `activate()` method with offline support |
| `src/core/gateway_client.py` | Add rate limit KV integration |
| `src/main.py` | Register new activate command |

## API Endpoints Required

| Endpoint | Method | Purpose | Headers |
|----------|--------|---------|---------|
| `/v1/auth/activate` | POST | Initial activation | X-Cert-ID, X-Cert-Sig |
| `/v1/auth/validate` | POST | Validate license key | Authorization: Bearer mk_... |
| `/v1/license/status` | GET | Get license status | Authorization: Bearer mk_... |
| `/v1/rate-limit/check` | GET | Check KV rate limit | X-Tenant-ID |
| `/v1/dashboard/sync` | POST | Sync activation to dashboard | X-Webhook-Signature |

## Storage Format

### Secure Storage (Platform Native)

```
macOS Keychain:
  Service: mekong-cli
  Account: {username}
  Label: raas_license_key
  Value: mk_abc123...

Linux (~/.mekong/credentials.enc):
  {
    "raas_license_key": "AES-256-GCM encrypted mk_...",
    "tenant_id": "encrypted tenant",
    "last_sync": "ISO8601 timestamp"
  }
```

### Session Cache (~/.mekong/session.json)

```json
{
  "tenant_id": "tenant_abc123",
  "tier": "pro",
  "role": "user",
  "license_key": "mk_...last4",
  "features": ["feature1", "feature2"],
  "expires_at": "2026-12-31T23:59:59Z",
  "cached_at": "2026-03-09T13:41:00Z",
  "ttl_seconds": 300,
  "refresh_token": "optional_future_use"
}
```

### Rate Limit State (In-memory with persistence)

```json
{
  "tenant_id": "tenant_abc123",
  "tier": "pro",
  "limit": 100,
  "remaining": 95,
  "reset_at": "2026-03-09T14:00:00Z",
  "kv_last_check": "2026-03-09T13:55:00Z"
}
```

## Implementation Phases

### Phase 1: Activate Command (2h)
- [ ] Create `src/cli/activate_commands.py`
- [ ] Implement `mekong auth activate --key=mk_...` command
- [ ] Integrate with existing `RaaSAuthClient.login()`
- [ ] Add activation success/failure output with dashboard link

### Phase 2: Offline Cache (2h)
- [ ] Create `src/core/offline_cache.py`
- [ ] Implement offline validation with TTL check
- [ ] Add queued events for sync
- [ ] Test offline mode scenarios

### Phase 3: Rate Limit KV Integration (2h)
- [ ] Modify `src/core/rate_limit_client.py` for KV checks
- [ ] Add `/v1/rate-limit/check` endpoint integration
- [ ] Implement tier-based limits from gateway response
- [ ] Add rate limit status command

### Phase 4: Dashboard Sync (2h)
- [ ] Create `src/core/activation_sync.py`
- [ ] Implement webhook bridge for activation events
- [ ] Add dashboard handoff URL generation
- [ ] Test sync flow with webhook

## Success Criteria

1. `mekong auth activate --key=mk_...` works and stores credentials securely
2. Validation succeeds against RaaS Gateway with JWT response
3. Offline mode allows operations with cached validation (5min TTL)
4. Rate limits enforced per tier with KV-based tracking
5. Dashboard shows activation status after sync

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gateway downtime | High | Circuit breaker + offline cache |
| Secure storage fails | Medium | Fallback to encrypted file |
| Rate limit KV unavailable | Medium | Local token bucket fallback |
| Dashboard sync fails | Low | Async retry queue |

## Security Considerations

- License keys NEVER logged or printed in full (mask with `mk_...last4`)
- All gateway calls use HTTPS with certificate pinning
- Device certificates for API auth (X-Cert-ID, X-Cert-Sig)
- Secure storage with platform-native encryption
- Session cache file permissions: 0o600 (owner rw only)

## Related Files

- `src/auth/secure_storage.py` - Platform secure storage
- `src/core/raas_auth.py` - Auth client with session management
- `src/core/gateway_client.py` - Gateway with circuit breaker
- `src/core/rate_limit_client.py` - Rate limit handling
- `src/cli/raas_auth_commands.py` - Existing auth CLI
- `src/commands/license_commands.py` - License management

## Next Steps

1. Review and approve this plan
2. Create tasks for each phase
3. Implement Phase 1 (Activate Command)
4. Test with local gateway mock
5. Deploy and verify with production gateway

---

## Unresolved Questions

1. Should `activate` be a separate command or alias of `login`?
2. What's the exact KV store format for rate limits (Redis vs Cloudflare KV)?
3. Dashboard webhook signature scheme for sync verification?
4. Should offline mode have a shorter TTL (e.g., 1min) for security?
