# Phase 6: CLI-native License Activation — Implementation Plan

> **Date:** 2026-03-09
> **Status:** ✅ Complete
> **Priority:** CRITICAL

---

## Overview

Implement CLI-native license activation flow that accepts `RAAS_LICENSE_KEY`, validates against RaaS Gateway, stores locally, and gates CLI features based on license tier.

---

## Requirements

### Functional
1. `mekong license-activate <key>` command để validate và lưu license
2. License stored tại `~/.mekong/license.json`
3. Subsequent CLI commands validate license state
4. Feature gating dựa trên license tier (free vs premium)
5. Rate limit enforcement đồng bộ với KV usage

### Non-functional
- All network calls qua Antigravity Proxy (localhost:9191)
- JWT + mk_ API key authentication
- Secure storage với encryption
- Offline fallback khi gateway unavailable

---

## Architecture

```
User → mekong license-activate <key>
              ↓
    RaaSAuthClient.validate_credentials()
              ↓
    Gateway: POST /v1/auth/validate
              ↓
    Response: { tenant_id, tier, features, rate_limit }
              ↓
    SecureStore: ~/.mekong/license.json (encrypted)
              ↓
    CLI Gateway Validator → Enable/Disable features
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/commands/license_activation.py` | CLI command cho license activation |
| `src/core/license_manager.py` | License storage và validation logic |
| `tests/raas/test_license_activation.py` | Test suite |

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/main.py` | + Import license_activation app, + Update FREE_COMMANDS |
| `src/core/raas_auth.py` | + Export validation methods |
| `src/lib/raas_gate_validator.py` | + Check local license state |

---

## Implementation Steps

### Step 1: License Manager Core (30 min)
- [x] Create `LicenseManager` class
- [x] Implement `save_license(license_data)` method
- [x] Implement `get_license()` method
- [x] Implement `is_valid()` method
- [x] Implement `get_tier()` method
- [x] Add encryption for storage

### Step 2: CLI Activation Command (30 min)
- [x] Create `license-activate` Typer app
- [x] Implement `activate(license_key)` command
- [x] Add validation flow với RaaS Gateway
- [x] Add success/error output với Rich
- [x] Register trong `main.py`

### Step 3: Feature Gating (30 min)
- [x] Update `main.py:_validate_startup_license()` để check local license
- [x] Implement feature enable/disable logic via `has_feature()`
- [x] Add license expiry check

### Step 4: Rate Limit Integration (20 min)
- [x] Sync license rate_limit via `get_rate_limit()` method

### Step 5: Testing (30 min)
- [x] Unit tests cho LicenseManager
- [x] Integration tests cho activation flow
- [x] Test feature gating scenarios
- [x] All tests passing (27/27)

### Step 6: Documentation (10 min)
- [x] Implementation report created

---

## Success Criteria

- [ ] `mekong license-activate mk_test_key` validates và stores license
- [ ] License persists across CLI sessions
- [ ] Invalid license rejected với clear error
- [ ] Premium commands blocked khi license invalid/expired
- [ ] Rate limits enforced per tier
- [ ] All tests passing (100%)

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gateway unavailable | High | Offline mode với cached license |
| License file corrupted | Medium | Backup + validation on load |
| Rate limit sync failed | Medium | Fallback to default limits |

---

## Next Steps

1. Implement LicenseManager core
2. Build CLI activation command
3. Integrate với existing auth flow
4. Test end-to-end flow
