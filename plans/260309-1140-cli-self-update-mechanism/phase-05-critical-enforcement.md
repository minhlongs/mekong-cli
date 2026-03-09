---
title: "Phase 5: Enforce Critical Updates"
description: "Implement forced update flow for security/critical patches"
status: pending
priority: P1
effort: 1.5h
branch: master
tags: [phase-6, security, enforcement]
created: 2026-03-09
---

# Phase 5: Enforce Critical Updates

## Overview

Implement mechanism to force users to update when critical security patches or breaking changes are released. Block CLI usage until update applied.

## Requirements

1. Gateway returns `is_critical` flag in version response
2. CLI blocks execution if critical update pending
3. Show clear message explaining requirement
4. Provide update command in error message
5. Bypass for `--help` and version commands

## Context Links

- Gateway endpoint: Phase 1 (`/v1/cli/version`)
- License validation: `/Users/macbookprom1/mekong-cli/src/lib/raas_gate_validator.py`
- Main entry: `/Users/macbookprom1/mekong-cli/src/main.py`

## Key Insights

From reading `src/main.py`:
- `_validate_startup_license()` already blocks commands
- FREE_COMMANDS list for bypass
- Pattern: check → block with message → `raise SystemExit(1)`

## Architecture

### Critical Update Detection

```
┌─────────────────────────────────────────────────────────┐
│  CLI Startup Flow                                       │
├─────────────────────────────────────────────────────────┤
│  1. Validate license (existing)                        │
│  2. Check for updates (Phase 2)                        │
│  3. IF critical update available:                      │
│     - Block command execution                          │
│     - Show message with update instructions            │
│     - Provide direct update command                    │
│     - Exit with code 2 (UPDATE_REQUIRED)               │
└─────────────────────────────────────────────────────────┘
```

### Response Format (Gateway)

```json
{
  "latest_version": "3.0.1",
  "is_critical": true,
  "critical_reason": "security_fix",
  "min_supported_version": "3.0.0",
  "message": "Critical security patch - update required"
}
```

### CLI Error Display

```
╔══════════════════════════════════════════════════════╗
║          CRITICAL UPDATE REQUIRED                    ║
╠══════════════════════════════════════════════════════╣
║  Version 3.0.1 is required for security reasons.    ║
║                                                       ║
║  Your version: 3.0.0                                ║
║  Reason: CVE-2026-12345 - Remote code execution      ║
║                                                       ║
║  Run the following command to update:               ║
║    $ mekong update                                  ║
║                                                       ║
║  Or download manually:                               ║
║    https://github.com/.../releases/tag/v3.0.1       ║
╚══════════════════════════════════════════════════════╝
```

## Implementation Steps

1. **Add `is_critical`** to Gateway response (Phase 1)
2. **Add `check_critical_update()`** to `UpdateChecker`
3. **Block in `main()`** if critical pending
4. **Show rich error panel** with instructions
5. **Add exit code** for update required

## Related Code Files

**To Create:**
- (None - modifications only)

**To Modify:**
- `apps/raas-gateway/src/cli-version-handler.js` — Add `is_critical` field
- `src/cli/update_checker.py` — Check for critical flag
- `src/main.py` — Block on critical update
- `src/core/exceptions.py` — Add `CriticalUpdateRequired` exception

## Todo List

- [ ] Add `is_critical` and `critical_reason` to Gateway response
- [ ] Add `check_critical_update()` to `UpdateChecker`
- [ ] Create `CriticalUpdateRequired` exception
- [ ] Add block logic in `main()` (after license check)
- [ ] Show rich error panel with instructions
- [ ] Add exit code 2 for update required
- [ ] Add bypass for `--help` and `--version`
- [ ] Write tests for critical update flow

## Success Criteria

- [ ] Gateway can set `is_critical: true`
- [ ] CLI detects critical update
- [ ] CLI blocks execution with clear message
- [ ] Update command provided in message
- [ ] Bypass works for help/version
- [ ] Exit code 2 (not 1) for critical update

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| False positive blocks users | High | Test thoroughly, easy rollback |
| Gateway marks all critical | Medium | Rate limit critical flags |
| User stuck without internet | Medium | Allow `--skip-update-check` flag |

## Security Considerations

- Critical flag must come from authenticated Gateway
- Don't allow bypass in production builds
- Log critical update enforcement events

## Next Steps

After Phase 5 complete:
- Phase 6: Tests and validation
