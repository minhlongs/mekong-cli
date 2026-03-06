---
title: "Phase 6 — License Key Parsing"
description: "Extract key_id and tier from RAAS_LICENSE_KEY env var"
status: completed
priority: P2
effort: 0.5h
parent_plan: 260306-2301-usage-metering-phase4
---

# Phase 6 — License Key Parsing

## Context Links

- Parent Plan: `plans/260306-2301-usage-metering-phase4/plan.md`
- License Generator: `src/lib/license_generator.py`

## Overview

Add `parse_license_key()` helper to extract `key_id` and `tier` from full license key.

## Key Format

```
raas-{tier}-{key_id}-{signature}
# Example: raas-pro-abc1234-aBcDeFgHiJkLmNoPqRsT
```

## Implementation

### Step 1: Add parse_license_key Function

```python
# src/lib/license_generator.py
def parse_license_key(license_key: str) -> tuple[bool, Optional[dict], str]:
    """
    Parse license key to extract key_id and tier.

    Args:
        license_key: Full license key (raas-{tier}-{key_id}-{signature})

    Returns:
        Tuple of (is_valid, parsed_info, error_message)
        parsed_info contains: {"key_id": str, "tier": str}
    """
    if not license_key:
        return False, None, "Empty license key"

    # Parse: raas-{tier}-{key_id}-{signature}
    parts = license_key.split("-", 3)
    if len(parts) < 4:
        return False, None, "Invalid format: expected raas-{tier}-{id}-{signature}"

    if parts[0] != "raas":
        return False, None, "Invalid prefix: must start with 'raas-'"

    tier = parts[1]
    if tier not in {"free", "trial", "pro", "enterprise"}:
        return False, None, f"Invalid tier: {tier}"

    key_id = parts[2]
    # parts[3] is signature (optional to validate)

    parsed_info = {
        "key_id": key_id,
        "tier": tier,
    }

    return True, parsed_info, ""
```

### Step 2: Add to __all__

```python
__all__ = [
    "LicenseKeyGenerator",
    "get_generator",
    "generate_license",
    "validate_license",
    "get_tier_limits",
    "TIER_LIMITS",
    "check_revocation",
    "parse_license_key",  # Add this
]
```

## Success Criteria

- [ ] `parse_license_key()` extracts key_id and tier correctly
- [ ] Invalid keys rejected with clear error
- [ ] Works with all tier formats (free, trial, pro, enterprise)

## Todo List

- [ ] Add `parse_license_key()` function
- [ ] Add to `__all__` exports
- [ ] Test with sample keys

## Test Cases

```python
# Valid pro key
is_valid, parsed, error = parse_license_key("raas-pro-abc1234-signature")
assert is_valid
assert parsed["key_id"] == "abc1234"
assert parsed["tier"] == "pro"

# Invalid format
is_valid, parsed, error = parse_license_key("invalid-key")
assert not is_valid
assert parsed is None

# Invalid tier
is_valid, parsed, error = parse_license_key("raas-invalid-id-sig")
assert not is_valid
```
