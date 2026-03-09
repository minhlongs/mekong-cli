# Phase 6: CLI Self-Update Mechanism - Implementation Plan Summary

**Date:** 2026-03-09
**Plan Directory:** `/Users/macbookprom1/mekong-cli/plans/260309-1140-cli-self-update-mechanism/`
**Priority:** P1 (High)
**Estimated Effort:** 8 hours total

---

## Executive Summary

Comprehensive plan for implementing CLI self-update mechanism with RaaS Gateway integration, signature verification, usage metering, and critical update enforcement.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Phase 6 Implementation Architecture                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐            │
│  │   Gateway    │────▶│   CLI        │────▶│   Signature  │            │
│  │   Endpoint   │     │   Checker    │     │   Verifier   │            │
│  │   (Phase 1)  │     │   (Phase 2)  │     │   (Phase 3)  │            │
│  └──────────────┘     └──────────────┘     └──────────────┘            │
│         │                    │                      │                    │
│         ▼                    ▼                      ▼                    │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐            │
│  │   Usage      │     │   Critical   │     │   Tests      │            │
│  │   Metering   │     │   Enforce    │     │   (Phase 6)  │            │
│  │   (Phase 4)  │     │   (Phase 5)  │     │              │            │
│  └──────────────┘     └──────────────┘     └──────────────┘            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Phases Summary

| Phase | Description | Effort | Status |
|-------|-------------|--------|--------|
| 1 | RaaS Gateway `/v1/cli/version` endpoint | 2h | pending |
| 2 | CLI startup check with caching | 2h | pending |
| 3 | Ed25519 signature verification | 2h | pending |
| 4 | Usage metering integration | 1h | pending |
| 5 | Critical update enforcement | 1.5h | pending |
| 6 | Comprehensive tests | 1.5h | pending |

## Key Files

### Plan Files Created

```
plans/260309-1140-cli-self-update-mechanism/
├── plan.md                              # Overview plan
├── phase-01-gateway-endpoint.md         # Gateway endpoint
├── phase-02-cli-startup-check.md        # CLI integration
├── phase-03-signature-verification.md   # Security
├── phase-04-usage-metering.md           # Metering
├── phase-05-critical-enforcement.md     # Enforcement
├── phase-06-tests-validation.md         # Tests
└── reports/
    └── planner-260309-1140-summary.md   # This file
```

### Code Files To Create

- `apps/raas-gateway/src/cli-version-handler.js` — Gateway handler
- `src/cli/update_checker.py` — Update checker
- `src/core/signature_verifier.py` — Signature verification
- `tests/core/test_update_checker.py` — Tests
- `tests/core/test_signature_verifier.py` — Tests

### Code Files To Modify

- `apps/raas-gateway/index.js` — Add route
- `src/main.py` — Add startup check
- `src/cli/auto_updater.py` — Integrate verification
- `src/usage/usage_tracker.py` — Add update events

## Implementation Sequence

**Recommended order:**

1. **Phase 1** (Gateway endpoint) — Foundation for all other phases
2. **Phase 2** (CLI check) — Depends on Phase 1
3. **Phase 4** (Usage metering) — Independent, can parallelize
4. **Phase 3** (Signatures) — Security critical, depends on Phase 2
5. **Phase 5** (Enforcement) — Depends on Phase 2
6. **Phase 6** (Tests) — Tests all phases

**Parallel opportunities:**
- Phase 4 can run parallel with Phase 2-3
- Phase 6 tests can be written as each phase completes

## Dependencies

| Phase | Depends On |
|-------|------------|
| Phase 1 | None |
| Phase 2 | Phase 1 |
| Phase 3 | Phase 2 |
| Phase 4 | None (uses existing infra) |
| Phase 5 | Phase 2 |
| Phase 6 | All phases |

## Success Criteria (Definition of Done)

- [ ] `mekong update check` returns version from RaaS Gateway
- [ ] Startup check runs silently (24h cache)
- [ ] `MEKONG_NO_UPDATE_CHECK=1` disables check
- [ ] Signature validation blocks tampered updates
- [ ] Critical updates enforce upgrade
- [ ] Usage events logged to Phase 4 tracker
- [ ] All 62+ tests pass

## Unresolved Questions

1. **Signature algorithm:** Ed25519 vs GPG? (Recommendation: Ed25519 - pure Python, no system deps)
2. **Critical update definition:** Semver major? Security flag? (Recommendation: Gateway-controlled flag)
3. **Startup check blocking:** Sync or async? (Recommendation: Async with 2s timeout)
4. **Key management:** How to rotate signing keys? (Recommendation: Document in Phase 3)

## Risk Summary

| Risk | Severity | Mitigation |
|------|----------|------------|
| Gateway unavailable | Medium | Fallback to GitHub Releases |
| Signature key leaked | Critical | Key rotation procedure |
| False positive critical block | High | Test thoroughly, easy bypass |
| Cache corruption | Low | Auto-clear on error |

## Next Actions

To begin implementation:

```bash
# 1. Start with Phase 1
/cook "Phase 1: Add /v1/cli/version endpoint to RaaS Gateway"

# 2. Then Phase 2
/cook "Phase 2: Add CLI startup check with caching"

# 3. Continue through phases
```

---

**Report saved to:** `/Users/macbookprom1/mekong-cli/plans/reports/planner-260309-1140-cli-self-update-summary.md`
