---
title: "Phase 6: CLI Self-Update Mechanism for RaaS"
description: "Implement CLI self-update mechanism with RaaS Gateway validation, signature verification, and usage metering"
status: pending
priority: P1
effort: 8h
branch: master
tags: [phase-6, cli, raas, auto-update, security]
created: 2026-03-09
---

# Phase 6: CLI Self-Update Mechanism

## Overview

Implement secure CLI self-update mechanism that checks RaaS Gateway for latest version, enforces updates on critical patches, validates signatures, and logs usage for Phase 4 metering.

## Key Requirements

1. **RaaS Gateway Integration** — Check `raas.agencyos.network` for latest version
2. **JWT/mk_ API Key Auth** — Use existing auth infrastructure (`src/core/raas_auth.py`)
3. **Enforce Update on Critical Patches** — Breaking changes force update
4. **Silent Startup Check** — Opt-out via `MEKONG_NO_UPDATE_CHECK` env var
5. **Signature Validation** — Validate via AgencyOS public key
6. **Usage Metering** — Log to Phase 4 usage tracker (`src/usage/decorators.py`)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  mekong CLI Startup                                                     │
├─────────────────────────────────────────────────────────────────────────┤
│  1. Check MEKONG_NO_UPDATE_CHECK env → skip if set                     │
│  2. Spawn background update check (non-blocking)                       │
│  3. Call RaaS Gateway: GET /v1/cli/version                             │
│  4. Compare versions → if newer available:                             │
│     - Check if security/critical update → enforce                     │
│     - Validate signature via AgencyOS public key                       │
│     - Download + install atomically                                    │
│  5. Log usage event → src/usage/usage_tracker.py                       │
└─────────────────────────────────────────────────────────────────────────┘
```

## Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | RaaS Gateway version endpoint | pending |
| 2 | CLI startup check integration | pending |
| 3 | Signature verification system | pending |
| 4 | Usage metering integration | pending |
| 5 | Enforce critical updates | pending |
| 6 | Tests and validation | pending |

## Related Files

**To Create:**
- `src/core/cli_version_checker.py` — Version check logic
- `src/core/signature_verifier.py` — Signature validation
- `src/cli/update_checker.py` — Startup check integration
- `tests/core/test_cli_version_checker.py`
- `tests/core/test_signature_verifier.py`

**To Modify:**
- `src/main.py` — Add startup check in `main()` callback
- `apps/raas-gateway/index.js` — Add `/v1/cli/version` endpoint
- `src/cli/auto_updater.py` — Integrate with existing updater
- `src/usage/usage_tracker.py` — Add `update_check` event type

## Dependencies

- `src/core/raas_auth.py` — JWT/mk_ API key auth
- `src/core/gateway_client.py` — Gateway requests
- `src/usage/usage_tracker.py` — Usage metering
- `apps/raas-gateway/index.js` — Cloudflare Worker endpoint

## Success Criteria

- [ ] `mekong update check` command works with RaaS Gateway auth
- [ ] Startup check runs silently (opt-out via env var)
- [ ] Critical updates enforced automatically
- [ ] Signature validation passes via AgencyOS public key
- [ ] Usage events logged to Phase 4 tracker
- [ ] All tests pass (62 existing + new tests)

## Risks

| Risk | Mitigation |
|------|------------|
| Gateway unreachable | Fallback to existing GitHub Releases logic |
| Signature validation fails | Block update, alert user |
| Update breaks CLI | Atomic install with rollback |
| Rate limit on startup | Cache version check for 24h |

## Next Steps

1. Read existing code patterns (DONE)
2. Create implementation plan (DONE)
3. Implement Phase 1: Gateway endpoint
4. Implement Phase 2: CLI integration
5. Implement Phase 3: Signature verification
6. Implement Phase 4: Usage metering
7. Run tests + validation

## Unresolved Questions

1. Should signature validation use GPG or Ed25519? (Current code has GPG stub)
2. What constitutes a "critical" update? (Semver major? Security flag in release?)
3. Should startup check block CLI execution or run fully async?
