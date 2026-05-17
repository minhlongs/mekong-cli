# IDE + Polar MVP — Browser E2E

Playwright specs verifying the revenue path:

```
1. Checkout flow      → Polar test card → license email
2. IDE login          → license key → /app
3. Mission flow       → submit goal → SSE output → MCU decremented
4. Insufficient credits → drained balance → 402 toast
```

## Prerequisites

These tests require live infrastructure:
- `https://www.mekongmind.com/pricing` reachable
- `https://api.mekong.dev/auth/login` returning JWT
- `https://ide.mekongmind.com/login` deployed
- Polar test mode credentials provisioned (`POLAR_TEST_API_KEY`)
- A test license seeded in `LicenseStore` with non-zero MCU balance

Until Phase 01 + Phase 02 + Phase 03 + Phase 04 are deployed, these specs
are **expected to fail**. Treat them as scaffolding.

## Run locally

```bash
pnpm install -D @playwright/test
pnpm exec playwright install chromium
pnpm exec playwright test --config tests/e2e/config/playwright.config.ts \
  tests/e2e/ide-polar-mvp/
```

## Required env

```
POLAR_TEST_API_KEY=...
TEST_LICENSE_KEY=lic_test_...
TEST_TENANT_ID=cus_test_...
IDE_BASE_URL=https://ide.mekongmind.com
API_BASE_URL=https://api.mekong.dev
```
