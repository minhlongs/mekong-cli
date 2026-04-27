# Phase 05: E2E Browser Verification

**Priority:** P1 — Quality gate before announce
**Status:** ☐ Pending
**Effort:** 1 ngày
**Depends on:** Phase 01-04 all live

## Context Links

- Phase 04 — IDE UI MVP
- Phase 03 — License gating
- `tests/raas/test_polar_webhook_e2e.py` — existing webhook E2E tests (FastAPI TestClient, not browser)

## Overview

Tất cả phase 01-04 có unit + integration tests. Phase 05 thêm **browser E2E** verify toàn bộ revenue path từ checkout → IDE login → mission complete → MCU deduct.

## Why Browser E2E

CLAUDE.md global rule (Rule 13B): "**CC CLI PHẢI MỞ BROWSER TEST CHECKOUT FLOW TRƯỚC KHI BÁO DONE**". Webhook unit tests không cover:
- JS hydration errors
- CORS bugs
- Real Polar redirect chain
- Email delivery latency
- SSE reconnect under network drop

## Architecture

```
Playwright test
├── Test 1: Checkout flow
│   1. Goto www.mekongmind.com/pricing
│   2. Click "Get Growth $49"
│   3. Polar checkout opens
│   4. Fill test card 4242 4242 4242 4242
│   5. Submit → success page
│   6. Wait 30s for email arrival (Resend webhook intercept)
│   7. Extract license key from email
│
├── Test 2: IDE login
│   1. Goto ide.mekongmind.com/login
│   2. Paste license key from Test 1
│   3. Submit → redirect /app
│   4. Assert terminal visible
│   5. Assert balance header shows MCU
│
├── Test 3: Mission flow
│   1. (Continue from Test 2) Type "scout user model" + Enter
│   2. Wait for SSE output
│   3. Assert output contains expected pattern
│   4. Assert balance decremented by 1
│
└── Test 4: Insufficient credits
    1. Drain balance to 0 (admin endpoint or DB seed)
    2. Submit mission
    3. Assert HTTP 402 toast with recharge URL
```

## Requirements

### Functional
- Run via `pnpm test:e2e` from monorepo root
- CI-friendly: headless mode, single worker, retry once
- Use Polar test mode + Stripe test cards
- Tests independent: each test sets up + tears down its own user

### Non-Functional
- Total runtime < 5 min
- Stable: < 1% flakiness over 100 runs
- Screenshots on failure, video for last failed test

## Related Code Files

### Create
- `tests/e2e/playwright.config.ts` — Playwright config
- `tests/e2e/fixtures/polar-test.ts` — Polar test mode helpers
- `tests/e2e/fixtures/email-intercept.ts` — Resend webhook receiver mock
- `tests/e2e/specs/01-checkout-flow.spec.ts`
- `tests/e2e/specs/02-ide-login.spec.ts`
- `tests/e2e/specs/03-mission-flow.spec.ts`
- `tests/e2e/specs/04-insufficient-credits.spec.ts`
- `tests/e2e/package.json` — separate Playwright deps
- `.github/workflows/e2e.yml` — nightly run on staging

### Modify
- Root `package.json` (or pnpm workspace) — add e2e scripts

### Delete
- None

## Implementation Steps

1. **Install Playwright**
   ```bash
   cd tests/e2e
   pnpm init && pnpm add -D @playwright/test
   pnpm exec playwright install chromium
   ```

2. **Polar test mode helper** — `fixtures/polar-test.ts`:
   - Wrapper around Polar API to create test customers + force webhook fire
   - Or: real checkout flow but with test products (cents, not dollars)

3. **Email intercept** — Local HTTP server tạm trên port 9999:
   - Replace `RESEND_API_KEY` env trong Playwright test với mock URL
   - Mock URL captures email payload, extracts license key

4. **4 test specs** — viết theo cấu trúc Architecture trên.

5. **CI integration** — `.github/workflows/e2e.yml`:
   - Run nightly on schedule + on PR labeled `needs-e2e`
   - Required secrets: `POLAR_TEST_API_KEY`, `STRIPE_TEST_KEY`
   - Upload artifacts: traces, videos, screenshots on failure

## Todo List

- [ ] `tests/e2e/` workspace setup
- [ ] Playwright config (chromium only initially)
- [ ] Polar test mode helper
- [ ] Email intercept fixture
- [ ] Spec 1: checkout flow
- [ ] Spec 2: IDE login
- [ ] Spec 3: mission flow
- [ ] Spec 4: insufficient credits
- [ ] Run all 4 locally → 100% pass
- [ ] GH Actions workflow
- [ ] Run on staging 3 days, measure flakiness
- [ ] Add screenshots/videos to acceptance docs

## Success Criteria

- All 4 E2E tests pass on staging
- < 5% flakiness over 1 week of nightly runs
- Failure mode: clear screenshot + video + trace
- CI runtime < 5 min per run
- Documented runbook for "how to run E2E locally"

## Risk Assessment

| Risk | Mitigation |
|---|---|
| Polar test API changes | Pin Polar SDK version; alert on test break |
| Stripe test card rejection | Multiple fallback cards documented |
| Email delivery flakiness | Mock vs real toggle; mock for CI, real for staging |
| Browser version drift | Pin Playwright Chromium version |

## Security Considerations

- Test API keys NEVER in repo — GH Actions secrets only
- Playwright traces may contain JWT — strip on upload
- Test license keys không được dùng cho production
- E2E tests không touch production DB — separate test tenant

## Next Steps

After Phase 05 GREEN:
- Announce MVP launch
- Monitor first 100 paid users via PostHog
- Phase 06 (out of scope this plan): Monaco editor, file browser, multi-mission tabs
