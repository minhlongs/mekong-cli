---
title: "Phase 1 — License Revocation & Expiration Handling"
description: "Handle license revocation and expiration scenarios with proper error messages"
status: completed
priority: P1
effort: 1h
parent_plan: 260307-0326-phase6c-license-enforcement
---

# Phase 1 — License Revocation & Expiration Handling

## Context Links

- Parent Plan: `plans/260307-0326-phase6c-license-enforcement/plan.md`
- License Gate: `src/lib/raas_gate.py`
- Quota Cache: `src/raas/quota_cache.py`
- Error Messages: `src/lib/quota_error_messages.py`

## Overview

Handle license revocation and expiration scenarios with proper error messages.

### Implementation

#### 1. `_license_status()` Method (src/lib/raas_gate.py)

```python
def _license_status(self) -> QuotaState:
    """Check license status (revoked/expired/valid)."""
    if not self.license_key:
        return QuotaState(status="unlicensed", expires_at_ts=None)

    try:
        payload = self._decode_license()
        if not payload:
            return QuotaState(status="invalid", expires_at_ts=None)

        # Check revocation
        if self._is_revoked(payload.get("key_id")):
            return QuotaState(status="revoked", expires_at_ts=None)

        # Check expiration
        if payload.get("exp"):
            exp_ts = payload["exp"]
            if time.time() > exp_ts:
                return QuotaState(status="expired", expires_at_ts=exp_ts)

        return QuotaState(status="valid", expires_at_ts=payload.get("exp"))
    except Exception:
        return QuotaState(status="invalid", expires_at_ts=None)
```

#### 2. `_license_expires_at()` Method (src/lib/raas_gate.py)

```python
def _license_expires_at(self) -> int | None:
    """Get license expiration timestamp."""
    if not self.license_key:
        return None

    try:
        payload = self._decode_license()
        if not payload:
            return None
        return payload.get("exp")
    except Exception:
        return None
```

#### 3. QuotaState Enhancement (src/raas/quota_cache.py)

Added `status` and `expires_at_ts` fields:

```python
@dataclass
class QuotaState:
    """Current quota state for a tenant."""
    quota_available: int
    quota_total: int
    usage: int
    status: str  # "valid", "expired", "revoked", "invalid", "unlicensed"
    expires_at_ts: int | None = None

    @property
    def is_expired(self) -> bool:
        if self.expires_at_ts is None:
            return False
        return time.time() > self.expires_at_ts
```

#### 4. Error Messages (src/lib/quota_error_messages.py)

```python
def format_license_revoked() -> str:
    """Format license revoked error message."""
    return (
        "❌ License key has been revoked.\n"
        "Please contact support to restore access."
    )


def format_license_expired(expires_at_ts: int) -> str:
    """Format license expired error message."""
    from datetime import datetime
    expires_at = datetime.fromtimestamp(expires_at_ts)
    return (
        f"❌ License key expired on {expires_at.strftime('%Y-%m-%d')}.\n"
        "Please renew your subscription to continue using the service."
    )
```

## Key Insights

- License status checked BEFORE quotaLimits
- Revoked licenses return immediate 401/403
- Expired licenses show expiration date
- Remote API (Polar) returns 401/403/429 for license issues

## Requirements

### Functional
- Detect revoked licenses and return 401/403
- Detect expired licenses and show expiration date
- Handle remote API errors (401/403/429) gracefully

### Non-Functional
- No performance impact on valid licenses
- Clear error messages for users
- Consistent error formatting

## Related Code Files

### To Modify
- `src/lib/raas_gate.py` - Added _license_status(), _license_expires_at()
- `src/raas/quota_cache.py` - Added status, expires_at_ts to QuotaState
- `src/lib/quota_error_messages.py` - Added format_license_revoked(), format_license_expired()

---

## Success Criteria

- [x] Revoked licenses detected with 401/403 response
- [x] Expired licenses detected with human-readable date
- [x] Error messages show clear remediation steps
- [x] Integration tests pass (21 tests)
- [x] Remote API errors handled gracefully

## Todo List

- [x] Add _license_status() method
- [x] Add _license_expires_at() method
- [x] Enhance QuotaState with status, expires_at_ts
- [x] Create format_license_revoked() function
- [x] Create format_license_expired() function
- [x] Write integration tests
- [x] Test with revoked license
- [x] Test with expired license
- [x] Test with valid license

## Test Cases

```python
# test_license_gate_integration.py
def test_license_revoked():
    state = gate._license_status()
    assert state.status == "revoked"
    assert state.is_revoked

def test_license_expired():
    state = gate._license_status()
    assert state.status == "expired"
    assert state.is_expired

def test_valid_license():
    state = gate._license_status()
    assert state.status == "valid"
    assert not state.is_expired
```

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| False positive revocation | High | Check Polar API first, fallback to cache |
| Expired date formatting bug | Medium | Use datetime.fromtimestamp() |
| Remote API timeout | Medium | Timeout = 5s, fallback to last known state |

## Next Steps

1. Phase 2: Quota Limit Enforcement
2. Phase 3: Usage Tracking
3. Phase 4: Reporting
