---
title: "Phase 3: Enhanced Error Messages"
description: "Clear error messages with actionable instructions"
status: completed
priority: P2
effort: 1h
completed: 2026-03-07
---

# Phase 3: Enhanced Error Messages Implementation

## Objective

Cung cấp error messages rõ ràng với actionable instructions khi license validation fails.

## Current Issues

```python
# Current error messages quá chung chung
"License validation failed: Invalid or revoked license key"
"Monthly limit reached: 500/500"
```

**Thiếu:**
- Instructions để fix
- Links để upgrade/renew
- Commands cụ thể để chạy
- Tier-specific guidance

## Error Message Categories

### Category 1: No License

```python
def format_no_license_error(command: str) -> str:
    """
    📋 License Required

    The '{command}' command requires a valid license.

    Current: No license key found

    Options:
    1. Generate free license:
       mekong license generate --tier free

    2. Upgrade to Pro (recommended):
       mekong license generate --tier pro

    3. View pricing:
       mekong license pricing

    Quick Start:
       export RAAS_LICENSE_KEY=raas-free-xxxx-xxxx
    """
```

### Category 2: Invalid License

```python
def format_invalid_license_error(key_preview: str) -> str:
    """
    ❌ Invalid License Key

    License key '{key_preview}' is not valid.

    Possible causes:
    - Typo in the key
    - Incorrect format (should be: raas-[tier]-[id]-[signature])
    - Key from different environment

    To fix:
    1. Generate new key:
       mekong license generate --tier pro

    2. Verify current key:
       mekong license validate

    3. Check environment:
       echo $RAAS_LICENSE_KEY
    """
```

### Category 3: Quota Exceeded

```python
def format_quota_exceeded_error(
    tier: str,
    daily_used: int,
    daily_limit: int,
    monthly_used: int,
    monthly_limit: int,
    command: str,
) -> str:
    """
    ⛔ Quota Exceeded

    Tier: {tier}
    Daily: {daily_used}/{daily_limit} commands
    Monthly: {monthly_used}/{monthly_limit} commands

    Options:

    1. Wait for reset:
       Daily quota resets at midnight UTC
       Monthly quota resets in {days_until_reset} days

    2. Upgrade tier:
       Current: {tier}
       Recommended: pro (unlimited daily, 10,000 monthly)

       mekong license upgrade --tier pro

    3. Use during off-peak:
       Retry after 00:00 UTC for fresh daily quota
    """
```

### Category 4: Rate Limit

```python
def format_rate_limit_error(
    retry_after_seconds: int,
    requests_per_minute: int,
) -> str:
    """
    ⏱️  Rate Limit Exceeded

    Too many requests. Please slow down.

    Limit: {requests_per_minute} requests/minute
    Retry after: {retry_after_seconds} seconds

    Tips:
    - Batch commands when possible
    - Use --batch flag for bulk operations
    - Contact support for higher limits
    """
```

### Category 5: License Revoked

```python
def format_license_revoked(key_id: str) -> str:
    """
    🚫 License Revoked

    Your license has been revoked for violation of terms.

    License ID: {key_id}

    This may happen if:
    - Key was shared publicly
    - Usage patterns violated terms
    - Payment was disputed

    To restore access:
    1. Contact support: support@mekong.dev
    2. Generate new key: mekong license generate
    3. Review terms: mekong license terms
    """
```

### Category 6: License Expired

```python
def format_license_expired(expiry_date: str) -> str:
    """
    ⌛ License Expired

    Your license expired on {expiry_date}.

    Renew now to continue:

    1. Renew same tier:
       mekong license renew --tier pro

    2. Upgrade tier:
       mekong license upgrade --tier enterprise

    3. View options:
       mekong license pricing

    Grace period: None (access blocked)
    """
```

### Category 7: Offline Grace Period

```python
def format_offline_grace_warning(
    remaining_hours: int,
    last_validation: str,
) -> str:
    """
    📡 Offline Mode Active

    Cannot reach license server. Operating in offline mode.

    Remaining grace period: {remaining_hours} hours
    Last online validation: {last_validation}

    Actions:
    1. Check internet connection
    2. Verify RAAS_API_URL is accessible
    3. CLI will auto-revalidate when back online

    Note: Some features may be limited in offline mode
    """
```

## File Structure

**New File:** `src/lib/license_error_messages.py`

```python
"""
License Error Messages — ROIaaS Phase 6f

Centralized error message formatting with actionable instructions.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ErrorContext:
    """Context for error message formatting."""
    tier: Optional[str] = None
    command: Optional[str] = None
    daily_used: int = 0
    daily_limit: int = 0
    monthly_used: int = 0
    monthly_limit: int = 0
    retry_after_seconds: Optional[int] = None
    key_id: Optional[str] = None
    expiry_date: Optional[str] = None
    remaining_hours: Optional[int] = None


def format_error(error_type: str, ctx: ErrorContext) -> str:
    """Format error message by type."""
    formatters = {
        "no_license": format_no_license_error,
        "invalid_license": format_invalid_license_error,
        "quota_exceeded": format_quota_exceeded_error,
        "rate_limit": format_rate_limit_error,
        "revoked": format_license_revoked,
        "expired": format_license_expired,
        "offline_grace": format_offline_grace_warning,
    }

    formatter = formatters.get(error_type)
    if formatter:
        return formatter(ctx)
    return f"Unknown error: {error_type}"


# Export individual formatters
__all__ = [
    "ErrorContext",
    "format_error",
    "format_no_license_error",
    "format_invalid_license_error",
    "format_quota_exceeded_error",
    "format_rate_limit_error",
    "format_license_revoked",
    "format_license_expired",
    "format_offline_grace_warning",
]
```

## Integration

**File:** `src/lib/raas_gate.py`

Replace existing error formatting:

```python
# OLD
return False, f"License validation failed: {error}"

# NEW
from src.lib.license_error_messages import format_error, ErrorContext

ctx = ErrorContext(
    tier=self._license_tier,
    command=command,
    # ... other fields
)
return False, format_error(error_type, ctx)
```

**File:** `src/lib/quota_error_messages.py`

Deprecate and migrate to new `license_error_messages.py`.

## Implementation Steps - COMPLETE

1. [x] Create `src/lib/license_error_messages.py`
2. [x] Implement all error formatters
3. [x] Update `RaasLicenseGate.check()` to use new formatters
4. [x] Deprecate `src/lib/quota_error_messages.py`
5. [x] Add Vietnamese translations (optional)

## Implementation Complete

## Output Files

- New: `src/lib/license_error_messages.py`
- Modified: `src/lib/raas_gate.py`
- Deprecated: `src/lib/quota_error_messages.py`

## Success Criteria - ALL MET ✅

- [x] All error messages include actionable instructions
- [x] Commands cụ thể để fix từng lỗi
- [x] Links đến pricing/docs khi relevant
- [x] Messages under 20 lines (readable)
- [x] Consistent formatting across all errors
