---
title: "Phase 6: CLI Command Authorization & Usage Enforcement"
description: "Implement per-command authorization layer with RaaS Gateway validation, usage metering, and quota enforcement across all CLI commands"
status: pending
priority: P1
effort: 8h
branch: master
tags: [raas, phase6, authorization, usage-metering, security]
created: 2026-03-09
---

# Phase 6: CLI Command Authorization & Usage Enforcement

## Overview

Implement centralized authorization layer that validates RaaS license and enforces usage quotas for **EVERY** CLI command invocation. This is the critical revenue protection layer that prevents unauthorized usage and ensures accurate billing attribution.

## Problem Statement

Current implementation has:
- ✅ Startup license validation in `main.py` via `_validate_startup_license()`
- ✅ Local license storage via `LicenseManager` (~/.mekong/license.json)
- ✅ Gateway client with circuit breaker in `gateway_client.py`
- ✅ Usage auto-instrumentation in `usage_auto_instrument.py`
- ✅ Sync client for metrics in `sync_client.py`

**GAPS:**
- ❌ No per-command authorization check (only at startup)
- ❌ Commands can bypass authorization if startup check skipped
- ❌ No command-level feature gating (e.g., `/popup-cro` requires PRO tier)
- ❌ Usage events emitted AFTER command execution (too late for rejection)
- ❌ No centralized quota enforcement before command runs

## Requirements

### Functional Requirements

1. **Pre-Command Authorization**
   - Validate license BEFORE every command execution (not just at startup)
   - Check license expiry, rate limits, and quota remaining
   - Block execution with clear error message if unauthorized

2. **Per-Command Tier Gating**
   - FREE tier: `cook`, `plan`, `status`, `config`, `doctor` (basic commands)
   - PRO tier: `binh-phap`, `agi`, `deploy`, `monitor`, `analytics` (advanced)
   - ENTERPRISE tier: `tier-admin`, `license-admin`, `raas-maintenance` (admin)

3. **Usage Attribution**
   - Every command must include JWT/mk_ API key in gateway request
   - `X-JWT-Attribution` header for JWT tokens
   - `X-RaaS-Tenant-ID` header for mk_ API keys
   - Idempotency key per command invocation

4. **Quota Enforcement**
   - Check rate limit BEFORE command execution
   - Check monthly quota BEFORE command execution
   - Return `429 Too Many Requests` with reset time if exceeded

5. **Audit Logging**
   - Log every command invocation to RaaS Gateway `/v2/audit`
   - Include: command name, tenant ID, timestamp, exit code, duration
   - Debug mode via `--raas-debug` exports full trace

### Non-Functional Requirements

- **Latency**: Authorization check < 100ms (cached validation)
- **Availability**: Offline mode with cached license (24h grace period)
- **Security**: No command execution without valid authorization
- **Observability**: Full audit trail for compliance

## Architecture

### Authorization Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLI Command Invocation                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: Command Authorization Middleware (NEW)                 │
│  ├─ Check if command is FREE (skip auth)                        │
│  ├─ Load cached license from LicenseManager                     │
│  ├─ Validate: not expired, has feature, under quota             │
│  └─ If invalid → Block with error message                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (if valid)
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: Pre-Flight Gateway Check (async, <100ms timeout)       │
│  ├─ POST /v1/license/verify (lightweight)                       │
│  ├─ Check rate limit remaining                                  │
│  └─ If fail → Use cached validation (grace period)              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (if valid)
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: Command Execution                                      │
│  └─ Execute command logic                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: Post-Command Usage Event (non-blocking)                │
│  ├─ Emit to /v2/usage with attribution                          │
│  ├─ Log to /v2/audit                                            │
│  └─ Cache on failure for later sync                             │
└─────────────────────────────────────────────────────────────────┘
```

### Command Tier Map

| Command | Current Tier | Target Tier | Feature Gate |
|---------|--------------|-------------|--------------|
| `cook` | FREE | FREE | `cli:cook` |
| `plan` | FREE | FREE | `cli:plan` |
| `status`, `config`, `doctor` | FREE | FREE | (none) |
| `license-*`, `auth`, `validate` | FREE | FREE | (none) |
| `binh-phap` | (none) | PRO | `strategy:binh-phap` |
| `agi` | (none) | PRO | `agents:agi` |
| `deploy`, `monitor` | (none) | PRO | `ops:deploy` |
| `analytics`, `dashboard` | (none) | PRO | `analytics:view` |
| `tier-admin`, `license-admin` | (none) | ENTERPRISE | `admin:tier` |
| `raas-maintenance` | (none) | ENTERPRISE | `admin:maintenance` |
| `sync-raas`, `billing` | (none) | PRO | `billing:sync` |
| `update` | FREE | FREE (security) | (none) |
| `security-cmd` | FREE | FREE | (none) |

## Files to Modify

### New Files

| File | Purpose |
|------|---------|
| `src/core/command_authorizer.py` | Centralized command authorization logic |
| `src/core/quota_enforcer.py` | Rate limit and quota checking |
| `src/middleware/auth_middleware.py` | Typer middleware for pre-command auth |
| `tests/core/test_command_authorizer.py` | Unit tests for authorization |
| `tests/core/test_quota_enforcer.py` | Unit tests for quota checking |

### Modified Files

| File | Changes |
|------|---------|
| `src/main.py` | Add middleware, replace `_validate_startup_license()` with new flow |
| `src/core/license_manager.py` | Add `has_command_access()` method, grace period logic |
| `src/core/gateway_client.py` | Add `/v1/license/verify` lightweight endpoint |
| `src/cli/usage_auto_instrument.py` | Move usage emit to POST-execute (already correct) |
| `src/commands_registry.py` | Register tier requirements per command |
| `src/cli/raas_auth_commands.py` | Add `refresh-license` command for manual refresh |

### Unchanged (Already Correct)

- `src/core/raas_auth.py` - Auth client already handles JWT/mk_ validation
- `src/core/raas_audit_logger.py` - Audit logging already implemented
- `src/raas/sync_client.py` - Sync logic already implemented

## Implementation Steps

### Phase 6.1: Command Authorization Core (2h)

**Goal:** Implement `CommandAuthorizer` class with tier checking

1. Create `src/core/command_authorizer.py`:
   ```python
   class CommandAuthorizer:
       COMMAND_TIERS = {
           "cook": "free", "plan": "free", "status": "free",
           "binh-phap": "pro", "agi": "pro", "deploy": "pro",
           "tier-admin": "enterprise", "license-admin": "enterprise",
       }

       def authorize_command(self, command: str) -> AuthResult:
           # 1. Check if command is FREE
           # 2. Load license from LicenseManager
           # 3. Check tier >= required tier
           # 4. Check feature gate enabled
           # 5. Check not expired
           # 6. Return AuthResult(valid, error)
   ```

2. Create `src/core/quota_enforcer.py`:
   ```python
   class QuotaEnforcer:
       def check_rate_limit(self) -> tuple[bool, int]:
           # Check KV store for rate limit state
           # Return (can_proceed, reset_in_seconds)

       def check_monthly_quota(self) -> tuple[bool, int]:
           # Check remaining monthly quota
           # Return (can_proceed, remaining)
   ```

3. Unit tests for both classes

### Phase 6.2: Typer Middleware Integration (2h)

**Goal:** Intercept all commands before execution

1. Create `src/middleware/auth_middleware.py`:
   ```python
   from typer import Context

   def auth_middleware(ctx: Context):
       """Pre-command authorization check."""
       command = ctx.invoked_subcommand or ""

       # Skip FREE commands
       if command in FREE_COMMANDS:
           return

       # Authorize
       authorizer = get_command_authorizer()
       result = authorizer.authorize_command(command)

       if not result.valid:
           console.print(f"[red]Authorization Error:[/red] {result.error}")
           raise SystemExit(1)

       # Check quota
       enforcer = get_quota_enforcer()
       can_proceed, reset_in = enforcer.check_rate_limit()
       if not can_proceed:
           console.print(f"[red]Rate limit exceeded. Reset in {reset_in}s[/red]")
           raise SystemExit(1)
   ```

2. Update `src/main.py`:
   ```python
   @app.callback()
   def main(ctx: typer.Context):
       auth_middleware(ctx)  # NEW: Run before any command
       # ... rest of existing logic
   ```

3. Remove `_validate_startup_license()` (redundant now)

### Phase 6.3: Gateway Pre-Flight Check (2h)

**Goal:** Lightweight validation with graceful degradation

1. Add to `src/core/gateway_client.py`:
   ```python
   def verify_license_lightweight(self) -> VerifyResult:
       """
       POST /v1/license/verify (lightweight, <100ms)
       Returns: valid, tier, rate_limit_remaining, quota_remaining
       """
   ```

2. Add to `src/core/command_authorizer.py`:
   ```python
   def authorize_with_preflight(self, command: str) -> AuthResult:
       # Try pre-flight check (100ms timeout)
       # If timeout/fail, use cached validation with grace period
       # Grace period: 24h for expired network, 1h for invalid license
   ```

3. Add to `src/core/license_manager.py`:
   ```python
   def is_within_grace_period(self) -> tuple[bool, str]:
       # Check if within 24h grace for network issues
   ```

### Phase 6.4: Command Registry Tier Mapping (1h)

**Goal:** Declare tier requirements for all commands

1. Update `src/cli/commands_registry.py`:
   ```python
   COMMAND_REGISTRY = {
       "cook": {"tier": "free", "feature": "cli:cook"},
       "plan": {"tier": "free", "feature": "cli:plan"},
       "binh-phap": {"tier": "pro", "feature": "strategy:binh-phap"},
       # ... all commands
   }

   def get_command_tier(command: str) -> str:
       return COMMAND_REGISTRY.get(command, {}).get("tier", "free")

   def get_command_feature(command: str) -> str:
       return COMMAND_REGISTRY.get(command, {}).get("feature", "")
   ```

2. Update `src/core/license_manager.py`:
   ```python
   def has_feature(self, feature: str) -> bool:
       # Check if license has feature enabled
       # Default features for each tier
   ```

### Phase 6.5: Usage Attribution Enhancement (1h)

**Goal:** Ensure every command has proper attribution

1. Update `src/cli/usage_auto_instrument.py`:
   ```python
   def emit_event(self, command: str) -> Optional[str]:
       # Add tenant_id from JWT attribution
       # Add idempotency key
       # Add command tier to metadata
   ```

2. Update `src/core/raas_audit_logger.py`:
   ```python
   def log_command_execution(
       self,
       command: str,
       exit_code: int,
       duration_ms: float,
   ) -> AuditResult:
       # Log command execution with timing
   ```

### Phase 6.6: Testing & Validation (1h)

**Goal:** Verify all commands go through authorization

1. Create integration tests:
   ```python
   def test_free_commands_no_auth():
       # FREE commands should work without license

   def test_pro_commands_blocked_without_license():
       # PRO commands should fail without valid license

   def test_pro_commands_allowed_with_license():
       # PRO commands should work with PRO license

   def test_rate_limit_enforcement():
       # Commands should block when rate limit exceeded
   ```

2. Manual testing:
   ```bash
   # Test FREE commands without license
   unset RAAS_LICENSE_KEY
   mekong cook "test"  # Should work

   # Test PRO commands without license
   mekong binh-phap "test"  # Should fail with auth error

   # Test PRO commands with license
   export RAAS_LICENSE_KEY=mk_pro_key
   mekong binh-phap "test"  # Should work

   # Test rate limiting
   for i in {1..100}; do mekong cook "test"; done  # Should hit limit
   ```

## Success Criteria

### Functional Acceptance

- [ ] FREE commands work without license (backward compatible)
- [ ] PRO/ENTERPRISE commands blocked without valid license
- [ ] Rate limit enforced BEFORE command execution
- [ ] Clear error messages for each failure mode:
  - No license: "Activate license: mekong license-activate mk_..."
  - Expired: "License expired on YYYY-MM-DD. Renew: mekong renewal"
  - Rate limit: "Rate limit exceeded. Reset in 300s"
  - Quota: "Monthly quota exceeded. Upgrade tier: mekong tier-admin"
- [ ] Offline grace period works (24h network failure, 1h invalid)
- [ ] All commands emit usage events with correct attribution

### Performance

- [ ] Authorization overhead < 100ms (cached)
- [ ] Pre-flight check timeout < 200ms
- [ ] No blocking network calls during command execution

### Security

- [ ] Zero command execution without authorization (except FREE)
- [ ] No bypass via environment variables or flags
- [ ] Audit trail complete for all commands

### Documentation

- [ ] Update `README.md` with command tier table
- [ ] Add authorization troubleshooting guide to `docs/`
- [ ] Document `--raas-debug` flag for debugging

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Network calls slow down commands | High | Pre-flight timeout <100ms, cached validation |
| False positive blocks legitimate users | High | Grace period, clear error messages |
| Backward compatibility break | Medium | FREE commands unchanged, graceful degradation |
| Rate limit too aggressive | Medium | Conservative defaults, easy override via `tier-admin` |

## Dependencies

- **External:** RaaS Gateway `/v1/license/verify` endpoint must exist
- **Internal:** `LicenseManager`, `GatewayClient`, `TelemetryReporter` already implemented

## Open Questions

1. Should `update` command be FREE even for security patches? **Proposal:** Yes, security updates always FREE
2. What is the grace period duration for network failures? **Proposal:** 24h
3. Should there be a `--no-auth` flag for local dev? **Proposal:** No, use FREE commands or `MEKONG_DEV_MODE=true`
4. How to handle enterprise on-prem without gateway access? **Proposal:** `RAAS_OFFLINE_MODE=true` with manual license file

## Next Steps

1. **Review & approve plan** → Get sign-off on tier mapping and grace periods
2. **Implement Phase 6.1** → Command authorization core
3. **Implement Phase 6.2** → Typer middleware
4. **Implement Phase 6.3** → Gateway pre-flight
5. **Implement Phase 6.4** → Command registry
6. **Implement Phase 6.5** → Usage attribution
7. **Implement Phase 6.6** → Testing & validation
8. **Deploy & monitor** → Watch for auth failures in production

---

## Related Files

- `src/main.py` - Entry point with middleware
- `src/core/license_manager.py` - License storage
- `src/core/gateway_client.py` - Gateway communication
- `src/core/raas_auth.py` - Auth validation
- `src/cli/usage_auto_instrument.py` - Usage tracking
- `src/raas/sync_client.py` - Metrics sync

## Commands Requiring Updates

Based on `src/commands/` and `src/cli/` directories:

**FREE (no change needed):**
- `cook`, `plan`, `status`, `config`, `doctor`, `clean`, `test`, `build`, `deploy` (basic), `lint`, `docs`, `env`, `help`, `version`, `init`, `health`, `analytics` (view only)

**PRO (require authorization):**
- `binh-phap`, `agi`, `monitor`, `security`, `ci`, `dashboard`, `roi`, `billing`, `sync-raas`, `raas-auth`, `usage`, `diagnostic`

**ENTERPRISE (admin only):**
- `license-admin`, `tier-admin`, `raas-maintenance`, `license-activation` (activation is FREE, admin is ENTERPRISE)
