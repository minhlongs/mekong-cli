---
title: "Phase 4: Usage Metering Integration"
description: "Log update events to RaaS Phase 4 usage tracker"
status: pending
priority: P2
effort: 1h
branch: master
tags: [phase-6, usage-metering, phase-4]
created: 2026-03-09
---

# Phase 4: Usage Metering Integration

## Overview

Log CLI update events to RaaS usage tracker for Phase 4 metering requirements. Track update checks, downloads, and installs.

## Requirements

1. Track `update_check` events (when CLI checks for version)
2. Track `update_download` events (when update downloaded)
3. Track `update_install` events (when update installed)
4. Include version info, success/failure, platform
5. Async tracking (don't block update flow)

## Context Links

- Usage tracker: `/Users/macbookprom1/mekong-cli/src/usage/usage_tracker.py`
- Usage decorators: `/Users/macbookprom1/mekong-cli/src/usage/decorators.py`
- Auto-updater: `/Users/macbookprom1/mekong-cli/src/cli/auto_updater.py`

## Key Insights

From reading `src/usage/usage_tracker.py`:
- `UsageTracker.track_command()` and `track_feature()` exist
- Uses idempotency keys for deduplication (24h TTL)
- Async operations (`async def`)
- PostgreSQL backend via `LicenseRepository`

From reading `src/usage/decorators.py`:
- `@track_usage()` decorator pattern
- Extracts `license_key_id` from env
- Silent failure on tracking errors

## Architecture

### New Event Types

```python
# Add to UsageTracker
async def track_update_event(
    self,
    key_id: str,
    event_type: Literal["update_check", "update_download", "update_install"],
    old_version: str,
    new_version: str,
    success: bool,
    is_security_update: bool,
    metadata: Dict[str, Any],
) -> tuple[bool, str]:
    """Track update-related events."""
```

### Integration Points

1. **Update check** → `track_update_event("update_check", ...)`
2. **Update download** → `track_update_event("update_download", ...)`
3. **Update install** → `track_update_event("update_install", ...)`

## Implementation Steps

1. **Add `track_update_event()`** to `UsageTracker`
2. **Update `UsageEvent`** dataclass for update events
3. **Add decorator** `@track_update()` for convenience
4. **Integrate in `AutoUpdater`** methods
5. **Add database migration** if needed

## Related Code Files

**To Create:**
- (None - extend existing modules)

**To Modify:**
- `src/usage/usage_tracker.py` — Add `track_update_event()`
- `src/usage/decorators.py` — Add `@track_update()` decorator
- `src/cli/auto_updater.py` — Call tracking methods
- `src/db/queries/license-queries.py` — Add update event queries if needed

## Todo List

- [ ] Add `track_update_event()` method to `UsageTracker`
- [ ] Add event type validation for update events
- [ ] Add `@track_update()` convenience decorator
- [ ] Update `AutoUpdater.update()` to track events
- [ ] Update `AutoUpdater.check_for_updates()` to track checks
- [ ] Add tests for update tracking
- [ ] Verify events appear in dashboard

## Success Criteria

- [ ] `track_update_event()` works with existing infrastructure
- [ ] Events are deduplicated (idempotency keys)
- [ ] Tracking is async (non-blocking)
- [ ] Silent failure on errors
- [ ] Events visible in RaaS dashboard

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tracking blocks update | Medium | Always async, timeout 2s |
| Duplicate events | Low | Idempotency keys handle |
| DB unavailable | Low | Silent failure, no user impact |

## Security Considerations

- No PII in tracking data
- License key hashed (existing pattern)
- Platform info only for analytics

## Next Steps

After Phase 4 complete:
- Phase 5: Enforce critical updates
