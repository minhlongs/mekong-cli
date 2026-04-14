# Error Handling Fixes Implementation Plan

**Planner:** a0d4dec4526a43f3d
**Date:** 2026-03-19
**Status:** Complete — Ready for implementation

---

## Summary

Created comprehensive 4-phase implementation plan to fix critical error handling gaps identified in scout report (`plans/reports/scout-error-handling-260319.md`).

## Plan Location

`plans/error-handling-fixes-260319/`

| File | Purpose |
|------|---------|
| `plan.md` | Overview with phase table, dependencies, success criteria |
| `phase-01-payment-vn-fixes.md` | CRITICAL — Fix 3 payment routes (handleAsync, handleDb, validateJsonBody) |
| `phase-02-chat-fixes.md` | CRITICAL — Remove duplicate handleAsync, import from types/error.ts |
| `phase-03-webhook-utilities.md` | HIGH — Extract shared webhook utilities (replay attack, timestamp validation) |
| `phase-04-edge-case-guards.md` | MEDIUM — Add Retry-After headers, timestamp guards, verification |

## Priority Fixes

1. **CRITICAL — payment-vn.ts** (Phase 1)
   - 3 routes lacking `handleAsync` wrapper
   - Missing `handleDb` for 5+ DB operations
   - Inconsistent error response format

2. **CRITICAL — chat.ts** (Phase 2)
   - Remove duplicate `handleAsync` (lines 308-318)
   - Import from `types/error.ts` for standardized format

3. **HIGH — Webhook utilities** (Phase 3)
   - Extract `ensureWebhookEventsTable`, `isDuplicateWebhookEvent`, `recordWebhookEvent`
   - Create `handleWebhook()` higher-order function

4. **MEDIUM — Edge cases** (Phase 4)
   - Add `Retry-After` headers to rate limit responses
   - Timestamp validation for all webhooks
   - Negative credit guard

## Effort Estimate

| Phase | Effort |
|-------|--------|
| Phase 1 | 2h |
| Phase 2 | 1h |
| Phase 3 | 2h |
| Phase 4 | 1h |
| **Total** | **6h** |

## Expected Impact

- **100% error handling coverage** across all API routes
- **Standardized error format** with `code` field in all responses
- **Eliminated code duplication** for webhook handling
- **Improved security** with consistent replay attack detection

## Next Steps

1. Review and approve plan
2. Execute phases in order (1 → 2 → 3 → 4)
3. Verify build + tests pass
4. Deploy to production

---

**Unresolved Questions:** None
