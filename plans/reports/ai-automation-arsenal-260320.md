# AI Automation Arsenal — OpenClaw

**Date:** 2026-03-20
**Mission:** Tự triển khai bằng AI lực có sẵn (Zero Human Intervention)

---

## 📊 Current AI Arsenal Inventory

### 1. Claude Code CLI (CC CLI) — Primary Weapon

**Location:** `mekong` CLI wrapper
**Commands:** 319+ commands available

```bash
# Core automation commands
/cook "task description" --auto     # Full implementation
/plan "task" --auto                 # Auto planning
/test                               # Run tests
/deploy                             # Deploy to production
/review                             # Code review
/debug "issue"                      # Debug issues
```

**Auto Mode Capabilities:**
- ✅ Research → Plan → Code → Test → Review → Finalize
- ✅ Spawns subagents: researcher, planner, tester, reviewer
- ✅ Creates/updates tasks automatically
- ✅ Generates reports to `/plans/reports/`

**Limitations:**
- ❌ Cannot do browser-based actions (login, dashboard clicks)
- ❌ Cannot set Cloudflare secrets (`wrangler secret put`)
- ❌ Cannot create Polar.sh products (API limitation)

---

### 2. Playwright — Browser Automation

**Status:** ✅ Installed
**Location:** `npx playwright`

**Use Cases:**
- Login to dashboards (Polar.sh, Google, Vercel)
- Click-through automation
- Form filling
- Screenshot/audit trail

**Example Script:**
```typescript
// scripts/create-polar-products-playwright.ts
import { test, expect } from '@playwright/test';

test('create 12 Polar products', async ({ page }) => {
  await page.goto('https://polar.sh/dashboard/login');
  await page.fill('[name=email]', process.env.POLAR_EMAIL!);
  await page.fill('[name=password]', process.env.POLAR_PASSWORD!);
  await page.click('button[type=submit]');

  for (const product of PRODUCTS) {
    await page.click('text=New Product');
    await page.fill('[name=name]', product.name);
    await page.fill('[name=price]', String(product.priceAmount));
    await page.click('button[type=submit]');
  }
});
```

**Run Command:**
```bash
npx playwright test scripts/create-polar-products-playwright.ts
```

---

### 3. Python Scripts — Backend Automation

**Available Scripts:** 100+ scripts in repo

| Script | Purpose | Location |
|--------|---------|----------|
| `ck-help.py` | CLI help generator | `.claude/scripts/` |
| `scan_skills.py` | Skills catalog scanner | `.claude/scripts/` |
| `generate_catalogs.py` | Catalog generator | `.claude/scripts/` |
| `i18n-audit.ts` | i18n validation | `.claude/scripts/` |
| `cloudflare_deploy.py` | CF deployment | `.claude/skills/devops/` |
| `db_migrate.py` | Database migrations | `.claude/skills/databases/` |
| `gemini_batch_process.py` | Batch AI processing | `.claude/skills/ai-multimodal/` |

**Run Pattern:**
```bash
# Python scripts
python .claude/scripts/ck-help.py
python .claude/scripts/scan_skills.py

# With venv (for skills)
~/.claude/skills/.venv/bin/python3 script.py
```

---

### 4. MCP Servers — Tool Integration

**Available MCP Tools:**
- File system operations
- Shell command execution
- Web search/fetch
- Database connections
- Git operations

**Usage via CC CLI:**
```bash
# MCP auto-discovers tools
/cook "Use MCP to fetch API docs and implement integration"
```

---

### 5. GitHub Actions — CI/CD Automation

**Current Workflows:**
- ✅ Auto-build on push
- ✅ Test execution
- ✅ Vercel deployment
- ✅ Release publishing

**Trigger Pattern:**
```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pnpm install
      - run: pnpm build
      - run: vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
```

**Automation:**
```bash
# Trigger deployment
git add .
git commit -m "feat: new feature"
git push origin main
# → GitHub Actions → Vercel deploy
```

---

### 6. Cloudflare Workers API — Edge Automation

**Available via wrangler CLI:**

```bash
# Deploy Workers
cd apps/raas-gateway
wrangler deploy

# Set secrets (requires human or CI/CD)
wrangler secret put JWT_SECRET
wrangler secret put POLAR_WEBHOOK_SECRET

# Query D1 database
wrangler d1 execute mekong-raas-db --command "SELECT * FROM users"

# Manage KV storage
wrangler kv:key put --binding=RATE_LIMIT_KV --key=user:123 --value="data"
```

**Automation Script:**
```bash
#!/bin/bash
# scripts/deploy-raas-gateway.sh
cd apps/raas-gateway
wrangler deploy
echo "Deployed to: https://raas-gateway.<subdomain>.workers.dev"
```

---

### 7. Polar.sh API — Payment Automation

**Available Endpoints:**
```
✅ GET  /v1/products          — List products
✅ GET  /v1/products/{id}     — Get product
✅ POST /v1/checkouts         — Create checkout
✅ GET  /v1/subscriptions     — List subscriptions
✅ POST /v1/benefit_grants    — Grant benefits
❌ POST /v1/products          — NOT AVAILABLE (must use dashboard)
```

**Automation Script (Existing):**
```typescript
// scripts/create-polar-products.ts
#!/usr/bin/env node
import { PolarClient } from './packages/mekong-cli-core/src/payments/polar-client.js';

// Lists existing products
// Displays configuration for 12 products to create
// Cannot create products via API (limitation)
```

**Run:**
```bash
export POLAR_API_KEY=sk_live_xxx
npx tsx scripts/create-polar-products.ts
```

---

## 🎯 Full Automation Strategy

### Level 1: What CC CLI Can Do ALONE (No Human)

| Task | Status | Time |
|------|--------|------|
| Code implementation | ✅ Auto | Variable |
| Run tests | ✅ Auto | 5-30m |
| Code review | ✅ Auto | 5-15m |
| Generate reports | ✅ Auto | 2-5m |
| Git commit/push | ✅ Auto | 1-2m |
| Deploy via CI/CD | ✅ Auto | 5-10m |

### Level 2: What Requires Playwright (Browser)

| Task | Status | Time to Build | Time to Run |
|------|--------|---------------|-------------|
| Polar.sh product creation | 🔶 Build Script | 2-3h | 5m |
| Google login automation | ✅ Available | N/A | 2m |
| Vercel dashboard config | 🔶 Build Script | 2h | 3m |
| Supabase dashboard setup | 🔶 Build Script | 2h | 3m |

### Level 3: What Requires Human (Cannot Automate)

| Task | Reason | Time |
|------|--------|------|
| Set `wrangler secret put` | Requires interactive prompt | 5m |
| 2FA authentication | Security requirement | 2m |
| Payment method setup | Legal/Compliance | 10m |
| Domain verification (DNS) | External system | 5-60m |

---

## 🚀 Recommended Automation Path

### Immediate (Today) — Playwright Script

**Build Playwright automation for Polar.sh:**

1. **Create script:**
```bash
mkdir -p scripts/e2e
cat > scripts/e2e/create-polar-products.spec.ts
```

2. **Implementation:**
```typescript
import { test, expect } from '@playwright/test';

const PRODUCTS = [
  { name: 'RaaS Gateway - Starter', price: 2900, mcu: '50' },
  { name: 'RaaS Gateway - Pro', price: 9900, mcu: '200' },
  // ... 12 products
];

test('Create 12 Polar products', async ({ page }) => {
  // Login
  await page.goto('https://polar.sh/dashboard/login');
  await page.fill('[name="email"]', process.env.POLAR_EMAIL!);
  await page.fill('[name="password"]', process.env.POLAR_PASSWORD!);
  await page.click('button[type="submit"]');

  // Create products
  for (const product of PRODUCTS) {
    await page.click('text=New Product');
    await page.fill('[name="name"]', product.name);
    await page.fill('[name="price_amount"]', String(product.price));
    await page.click('button[type="submit"]');
    await expect(page.getByText('Product created')).toBeVisible();
  }
});
```

3. **Run:**
```bash
npx playwright test scripts/e2e/create-polar-products.spec.ts
```

---

### Medium (This Week) — Full CI/CD Pipeline

**GitHub Actions + Wrangler:**

```yaml
# .github/workflows/deploy-raas.yml
name: Deploy RaaS Gateway

on:
  push:
    branches: [main]
    paths: ['apps/raas-gateway/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v2
        with:
          version: 8

      - run: pnpm install
      - run: pnpm --filter raas-gateway build

      - name: Deploy to Cloudflare
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CF_API_TOKEN }}
          command: deploy
          workingDirectory: apps/raas-gateway
```

---

### Long (Next Month) — Multi-Agent System

**Spawn multiple CC CLI agents in parallel:**

```bash
# Terminal 1: Backend API
cd apps/raas-gateway && mekong --auto /cook "Add new billing endpoint"

# Terminal 2: Frontend UI
cd apps/well && mekong --auto /cook "Add checkout button component"

# Terminal 3: Tests
cd packages/testing && mekong --auto /cook "Write E2E tests for checkout flow"

# Terminal 4: Docs
cd docs && mekong --auto /cook "Update API documentation"
```

---

## 📋 AI Agent Teams Configuration

**Team: `content-marketing-automation`** (Already configured)
- 12 members available
- Config: `~/.claude/teams/content-marketing-automation/config.json`

**Spawn Pattern:**
```bash
# Via /team skill
/team spawn researcher "Research competitors"
/team spawn writer "Write blog posts"
/team spawn designer "Create social media graphics"
```

---

## 🔧 Quick Start Scripts

### Script 1: Full Stack Deploy
```bash
#!/bin/bash
# scripts/full-deploy.sh
set -e

echo "🚀 Starting full deployment..."

# 1. Build all packages
pnpm build

# 2. Run tests
pnpm test

# 3. Commit and push
git add .
git commit -m "chore: deployment $(date +%Y%m%d-%H%M)"
git push origin main

# 4. Wait for CI/CD
echo "⏳ Waiting for GitHub Actions..."
gh run watch

# 5. Verify production
curl -I https://agencyos.network

echo "✅ Deployment complete!"
```

### Script 2: Polar Products via Playwright
```bash
#!/bin/bash
# scripts/auto-polar-products.sh
set -e

echo "🎯 Creating Polar.sh products..."

# Install Playwright if needed
npx playwright install chromium

# Run automation
npx playwright test scripts/e2e/create-polar-products.spec.ts --headed

# Extract product IDs
echo "📋 Copy product IDs to .env files:"
echo "   POLAR_STARTER_PRODUCT_ID=pro_xxx"
echo "   POLAR_PRO_PRODUCT_ID=pro_xxx"
```

### Script 3: Cloudflare Secrets (CI/CD)
```bash
#!/bin/bash
# scripts/set-cf-secrets.sh
# NOTE: This requires secrets to be piped via stdin

cd apps/raas-gateway

# Set secrets from environment variables
echo "$JWT_SECRET" | wrangler secret put JWT_SECRET
echo "$POLAR_WEBHOOK_SECRET" | wrangler secret put POLAR_WEBHOOK_SECRET
echo "$SERVICE_TOKEN" | wrangler secret put SERVICE_TOKEN

echo "✅ Cloudflare secrets set!"
```

---

## 💡 Key Insights

### What We Learned:

1. **80% can be automated** with CC CLI + Playwright
2. **20% requires human** (secrets, 2FA, legal compliance)
3. **Polar.sh API limitation** is the biggest blocker
4. **Playwright is the bridge** for dashboard automation

### Best Practices:

1. **Auto-approve what can be auto** (`--auto` flag)
2. **Use Playwright for browser actions**
3. **CI/CD for deployments** (GitHub Actions + Wrangler)
4. **Document everything** in `/plans/reports/`

---

## 📊 Automation Score

| Category | Auto % | Human % | Notes |
|----------|--------|---------|-------|
| Code Implementation | 100% | 0% | CC CLI --auto |
| Testing | 100% | 0% | Auto-run tests |
| Code Review | 95% | 5% | Human approval for critical |
| Deployment | 90% | 10% | Secrets need CI/CD |
| Polar Products | 0% | 100% | API limitation |
| Cloudflare Secrets | 50% | 50% | Can automate via CI/CD |

**Overall: 75% can be fully automated**

---

## 🎯 Next Actions

| Priority | Action | Owner | Time |
|----------|--------|-------|------|
| P0 | Build Playwright Polar script | CC CLI | 3h |
| P1 | Setup GitHub Actions for CF | CC CLI | 1h |
| P2 | Create secret management | Human | 30m |
| P3 | Test full automation pipeline | Both | 1h |

---

**Report:** `/plans/reports/ai-automation-arsenal-260320.md`
**Owner:** OpenClaw CTO Daemon
**Status:** Ready for implementation
