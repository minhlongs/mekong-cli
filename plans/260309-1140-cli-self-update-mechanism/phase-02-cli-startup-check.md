---
title: "Phase 2: CLI Startup Check Integration"
description: "Add silent version check on CLI startup with opt-out env var"
status: pending
priority: P1
effort: 2h
branch: master
tags: [phase-6, cli, startup]
created: 2026-03-09
---

# Phase 2: CLI Startup Check Integration

## Overview

Add silent version check to CLI startup flow that runs in background, checks RaaS Gateway for updates, and notifies user when update available.

## Requirements

1. Check version on every CLI invocation (after free commands filter)
2. Opt-out via `MEKONG_NO_UPDATE_CHECK=1` env var
3. Non-blocking: check runs async, doesn't delay command execution
4. Cache result for 24 hours (don't check every command)
5. Notify user only when update available (silent otherwise)

## Context Links

- Main entry: `/Users/macbookprom1/mekong-cli/src/main.py`
- Auto-updater: `/Users/macbookprom1/mekong-cli/src/cli/auto_updater.py`
- Gateway client: `/Users/macbookprom1/mekong-cli/src/core/gateway_client.py`
- RaaS auth: `/Users/macbookprom1/mekong-cli/src/core/raas_auth.py`

## Key Insights

From reading `src/main.py`:
- `main()` is the `@app.callback(invoke_without_command=True)` entry point
- FREE_COMMANDS list already exists for skip logic
- `_validate_startup_license()` runs before commands
- `_check_telemetry_consent()` shows consent prompt

From reading `src/cli/auto_updater.py`:
- `AutoUpdater.check_for_updates()` already exists
- Uses GitHub Releases API directly
- Need to integrate RaaS Gateway endpoint

## Architecture

### New Module: `src/cli/update_checker.py`

```python
class UpdateChecker:
    """Background update checker with caching."""

    CACHE_FILE = "~/.mekong/update_check.json"
    CACHE_TTL_HOURS = 24

    def __init__(self, gateway_client: GatewayClient):
        self.gateway = gateway_client
        self.cache = self._load_cache()

    def should_check(self) -> bool:
        """Check if we should run version check (not cached)."""
        ...

    async def check_version(self) -> Optional[UpdateAvailable]:
        """Check RaaS Gateway for latest version."""
        response = self.gateway.get("/v1/cli/version")
        ...

    def notify_if_available(self):
        """Show notification if update available (non-blocking)."""
        ...
```

### Integration in `src/main.py`

```python
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context, ...) -> None:
    """Mekong CLI - Autonomous AI Agent Framework"""

    # Validate license at startup
    _validate_startup_license(ctx)

    # NEW: Check for updates (non-blocking, opt-out)
    if not os.getenv("MEKONG_NO_UPDATE_CHECK"):
        _check_for_updates_async(ctx)

    # ... rest of main()
```

## Implementation Steps

1. **Create `src/cli/update_checker.py`** with `UpdateChecker` class
2. **Add cache mechanism** (`~/.mekong/update_check.json`)
3. **Integrate with `main()`** callback
4. **Add notification function** (shows message after command completes)
5. **Add `mekong update check`** command for manual check

## Related Code Files

**To Create:**
- `src/cli/update_checker.py` — Update checker module
- `src/cli/update_notification.py` — Notification display

**To Modify:**
- `src/main.py` — Add startup check in `main()`
- `src/cli/update_commands.py` — Add `check` command integration

## Todo List

- [ ] Create `update_checker.py` with `UpdateChecker` class
- [ ] Implement cache mechanism (JSON file, 24h TTL)
- [ ] Add `check_version()` method calling RaaS Gateway
- [ ] Add `notify_if_available()` function
- [ ] Integrate in `main()` callback (async, non-blocking)
- [ ] Add `MEKONG_NO_UPDATE_CHECK` env var check
- [ ] Update `update_commands.py` to use new checker
- [ ] Add tests for `UpdateChecker`

## Success Criteria

- [ ] Version check runs on CLI startup (free commands skip)
- [ ] `MEKONG_NO_UPDATE_CHECK=1` disables check
- [ ] Check runs async (doesn't block command)
- [ ] Notification shows only when update available
- [ ] Cache prevents redundant checks (24h TTL)
- [ ] Manual `mekong update check` command works

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Check blocks CLI | High | Run fully async, timeout after 2s |
| Gateway unreachable | Low | Fail silently, retry next run |
| Cache corruption | Low | Auto-clear on parse error |
| Annoying notifications | Medium | Show only once per update |

## Security Considerations

- No auth required for version check (public info)
- Gateway handles rate limiting
- Cache file permissions: 0600

## Next Steps

After Phase 2 complete:
- Phase 3: Signature verification for downloaded updates
