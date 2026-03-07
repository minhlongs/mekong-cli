---
title: "Phase 1: Offline Grace Period (24h)"
description: "Implement 24-hour offline grace period for network failures"
status: completed
priority: P1
effort: 2h
completed: 2026-03-07
---

# Phase 1: Offline Grace Period Implementation

## Objective

Cho phép CLI hoạt động trong 24 giờ khi remote API unavailable, thay vì chỉ 5 phút TTL hiện tại.

## Current State

```python
# src/raas/quota_cache.py
DEFAULT_TTL_SECONDS = 300  # 5 minutes - QUÁ NGẮN!

@dataclass
class QuotaState:
    # Không có field nào track grace period
    pass
```

## Required Changes

### 1.1 Extend QuotaState với Grace Period Fields

**File:** `src/raas/quota_cache.py`

```python
@dataclass
class QuotaState:
    key_id: str
    daily_used: int
    daily_limit: int
    tier: str = "free"
    status: str = "active"
    expires_at_ts: int = 0
    monthly_used: int = 0
    monthly_limit: int = 0
    cached_at: str = ""
    expires_at: str = ""

    # NEW: Grace period support
    grace_period_remaining: int = 86400  # 24h in seconds
    last_online_validation: str = ""     # ISO timestamp
    is_offline_mode: bool = False
```

### 1.2 Update Database Schema

**File:** `src/raas/quota_cache.py`

```sql
ALTER TABLE quota_cache ADD COLUMN grace_period_remaining INTEGER DEFAULT 86400;
ALTER TABLE quota_cache ADD COLUMN last_online_validation TEXT;
ALTER TABLE quota_cache ADD COLUMN is_offline_mode BOOLEAN DEFAULT FALSE;
```

### 1.3 Extend TTL Constants

```python
DEFAULT_TTL_SECONDS = 300  # Cache TTL for normal operation (5 min)
GRACE_PERIOD_SECONDS = 86400  # 24 hours offline grace period
```

### 1.4 Add Grace Period Methods to QuotaState

```python
def is_in_grace_period(self) -> bool:
    """Check if still within offline grace period."""
    if not self.last_online_validation:
        return False
    last_valid = datetime.fromisoformat(self.last_online_validation)
    now = datetime.now(timezone.utc)
    elapsed = (now - last_valid).total_seconds()
    return elapsed < self.grace_period_remaining

def remaining_grace_seconds(self) -> int:
    """Get remaining seconds in grace period."""
    if not self.last_online_validation:
        return 0
    last_valid = datetime.fromisoformat(self.last_online_validation)
    now = datetime.now(timezone.utc)
    elapsed = (now - last_valid).total_seconds()
    return max(0, int(self.grace_period_remaining - elapsed))
```

### 1.5 Update cache_quota Function

**File:** `src/raas/quota_cache.py`

```python
def cache_quota(
    key_id: str,
    daily_used: int,
    daily_limit: int,
    tier: str = "free",
    status: str = "active",
    expires_at_ts: int = 0,
    monthly_used: int = 0,
    monthly_limit: int = 0,
    is_offline_mode: bool = False,
    grace_period_remaining: int = GRACE_PERIOD_SECONDS,
) -> QuotaState:
    """Cache quota state with grace period support."""
    now = datetime.now(timezone.utc)

    state = QuotaState(
        key_id=key_id,
        daily_used=daily_used,
        daily_limit=daily_limit,
        tier=tier,
        status=status,
        expires_at_ts=expires_at_ts,
        monthly_used=monthly_used,
        monthly_limit=monthly_limit,
        cached_at=now.isoformat(),
        expires_at=(now + timedelta(seconds=DEFAULT_TTL_SECONDS)).isoformat(),
        last_online_validation=now.isoformat() if not is_offline_mode else "",
        grace_period_remaining=grace_period_remaining,
        is_offline_mode=is_offline_mode,
    )
    return get_cache().set(state)
```

## Implementation Steps - COMPLETE

1. [x] Update `QuotaState` dataclass với grace period fields
2. [x] Add migration script cho existing cache database
3. [x] Implement grace period checking methods
4. [x] Update `cache_quota()` function signature
5. [x] Update `RaasLicenseGate.check()` để check grace period

## Implementation Complete

## Integration with RaasLicenseGate

**File:** `src/lib/raas_gate.py`

```python
def check(self, command: str) -> Tuple[bool, Optional[str]]:
    # ... existing code ...

    # Try remote validation
    is_valid, info, error = self.validate_remote(self._license_key)

    if not is_valid and error and "unavailable" in error.lower():
        # Remote API failed - check grace period
        cached_state = get_cached_quota(self._key_id)
        if cached_state and cached_state.is_in_grace_period():
            # Allow with warning
            remaining_hours = cached_state.remaining_grace_seconds() // 3600
            console.print(f"[yellow]⚠️  OFFLINE MODE: {remaining_hours}h remaining[/yellow]")
            return True, None
        elif cached_state and not cached_state.is_in_grace_period():
            return False, "Offline grace period expired. Network required."

    # ... rest of validation ...
```

## Output Files

- Modified: `src/raas/quota_cache.py`
- Modified: `src/lib/raas_gate.py`
- New: `scripts/migrate_quota_cache_grace_period.py`

## Success Criteria - ALL MET ✅

- [x] CLI hoạt động khi không có network trong 24h
- [x] Hiển thị warning rõ ràng khi vào offline mode
- [x] Cache database migrated successfully
- [x] Không breaking existing validation flow
