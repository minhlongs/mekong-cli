# Complete Credentials Inventory — OpenClaw Mekong CLI

**Date:** 2026-03-20
**Project:** OpenClaw (Mekong CLI) — RaaS Gateway
**Status:** 75% configured (placeholders need replacement)

---

## 🎯 P0 — Critical (Required for GTM Launch)

### Cloudflare Workers (raas-gateway)

| Secret | Status | How to Set |
|--------|--------|------------|
| `JWT_SECRET` | ❌ Missing | `wrangler secret put JWT_SECRET` |
| `POLAR_WEBHOOK_SECRET` | ❌ Placeholder | `wrangler secret put POLAR_WEBHOOK_SECRET` |
| `SERVICE_TOKEN` | ✅ Set (hidden) | Already in Cloudflare |

**Account ID:** `f691e83094f776311a1bfe3f8b126f1c`

### Cloudflare Resources

| Resource | Name | ID | Status |
|----------|------|-----|--------|
| **D1 Database** | `mekong-raas-db` | `a0aa4f88-da5b-4616-84aa-7e559e37c91c` | ✅ Ready |
| **KV (Rate Limit)** | `RATE_LIMIT_KV` | `982a12a5ea414244988a51d743eb14e7` | ✅ Ready |
| **KV (Session)** | `SESSION_KV` | `ba8c93a931524b7e97027dbad43b31c0` | ✅ Ready |

---

## 💳 Polar.sh (Payment/Billing)

| Key | Current Value | Required |
|-----|---------------|----------|
| `POLAR_API_KEY` | `sk_test_placeholder` | `sk_live_...` or `sk_test_...` |
| `POLAR_WEBHOOK_SECRET` | `whsec_placeholder` | `whsec_...` |
| **Products Needed** | ❌ Not Created | 12 products (4 tiers × 3 apps) |

### Products to Create:

| App | Tier | Price | Status |
|-----|------|-------|--------|
| raas-gateway | Starter | $29/mo | ⏳ Pending |
| raas-gateway | Pro | $99/mo | ⏳ Pending |
| raas-gateway | Agency | $199/mo | ⏳ Pending |
| raas-gateway | Master | $399/mo | ⏳ Pending |
| well | Starter | $49/mo | ⏳ Pending |
| well | Pro | $199/mo | ⏳ Pending |
| well | Agency | $499/mo | ⏳ Pending |
| well | Master | $999/mo | ⏳ Pending |
| algo-trader | Starter | $49/mo | ⏳ Pending |
| algo-trader | Pro | $199/mo | ⏳ Pending |
| algo-trader | Agency | $499/mo | ⏳ Pending |
| algo-trader | Master | $999/mo | ⏳ Pending |

---

## 🗄️ Supabase (Database/Auth)

### Current Configuration:

| Project | URL | Anon Key | Service Key | Status |
|---------|-----|----------|-------------|--------|
| **well** | `https://jcbahdioqoepvoliplqy.supabase.co` | ✅ Valid | ✅ Valid | ✅ Ready |
| **mekong (root)** | `https://zumgrvmwmpstsigefuau.supabase.co` | ✅ Valid | ⚠️ Placeholder | ⚠️ Partial |
| **sophia** | `https://placeholder.supabase.co` | ❌ Placeholder | ❌ Placeholder | ❌ Not Configured |

---

## 🤖 LLM Providers

| Provider | Key | Status |
|----------|-----|--------|
| **DashScope (Qwen)** | `LLM_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1` | ✅ Configured |
| **Anthropic** | `ANTHROPIC_AUTH_TOKEN=` | ❌ Empty |
| **OpenRouter** | Not found | ❌ Not Configured |
| **Gemini** | `GEMINI_API_KEY=` | ❌ Empty |

---

## 💰 PayOS (Vietnamese Payment Gateway)

| Key | Value | Status |
|-----|-------|--------|
| `PAYOS_CLIENT_ID` | `2de33052-8493-4d13-9502-91b473845c12` | ✅ Configured |
| `PAYOS_API_KEY` | `07463cc4-e804-4f17-a5fe-355ff48e9010` | ✅ Configured |
| `PAYOS_CHECKSUM_KEY` | `d559bc91037674422e1b457e1bd81be7043fb034205e7c064cf5f374ebe44e01` | ✅ Configured |

---

## 🎰 Stripe (Legacy/Backup)

| Key | Current Value | Status |
|-----|---------------|--------|
| `STRIPE_SECRET_KEY` | `sk_test_dummy` | ❌ Test Only |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | `pk_test_dummy` | ❌ Test Only |
| `STRIPE_WEBHOOK_SECRET` | `whsec_dummy` | ❌ Test Only |

---

## 📡 RaaS Gateway Configuration

| Key | Value | Status |
|-----|-------|--------|
| `VITE_RAAS_GATEWAY_URL` | `https://raas.agencyos.network` | ✅ Configured |
| `VITE_RAAS_LICENSE_KEY` | `RAAS-1234567890-ABCD1234` | ⚠️ Dev Only |
| `RAAS_GATEWAY_URL` | `https://raas.agencyos.network/api` | ✅ Configured |
| `AGENCYOS_WEBHOOK_URL` | `https://agencyos.network/api/webhooks/usage-alerts` | ✅ Configured |

---

## 📊 Vercel Projects (OIDC Tokens)

| Project | Environment | Status |
|---------|-------------|--------|
| `agencyos-landing` | development | ✅ Token Available |
| `agencyos-web` | development | ✅ Token Available |
| `apex-os` | development | ✅ Token Available |
| `well` | development | ✅ Token Available |

---

## 🔐 Crypto/Trading APIs (Algo-Trader)

| Exchange | Key | Secret | Status |
|----------|-----|--------|--------|
| **Binance** | `BINANCE_API_KEY=` | `BINANCE_SECRET=` | ❌ Empty |
| **Bybit** | `BYBIT_API_KEY=` | `BYBIT_SECRET=` | ❌ Empty |
| **OKX** | `OKX_API_KEY=` | `OKX_SECRET=` | ❌ Empty |
| **Polymarket** | `POLYMARKET_API_KEY=` | `POLYMARKET_API_SECRET=` | ❌ Empty |

---

## ⚠️ Missing/ACTION REQUIRED

### Immediate Actions (Block GTM):

1. **Set Cloudflare Secrets:**
   ```bash
   cd apps/raas-gateway
   wrangler secret put JWT_SECRET
   wrangler secret put POLAR_WEBHOOK_SECRET
   ```

2. **Create Polar.sh Products:**
   - Login: https://polar.sh/dashboard
   - Create 12 products (4 tiers × 3 apps)
   - Copy product IDs to env files

3. **Update Supabase (sophia):**
   - Create project at https://supabase.com
   - Replace placeholder URLs and keys

4. **Configure LLM Provider:**
   - Option A: Set `ANTHROPIC_API_KEY=sk-ant-...`
   - Option B: Set `OPENROUTER_API_KEY=sk-or-...`
   - Option C: Keep using DashScope (Qwen) — already configured

### Medium Priority:

5. **Configure Trading APIs** (if using algo-trader):
   - Get API keys from Binance/Bybit/OKX
   - Update `.env` in `apps/algo-trader`

6. **Update Stripe Keys** (if using as backup):
   - Replace test keys with live keys
   - Update webhook secret

---

## 📋 Commands Quick Reference

```bash
# Cloudflare Secrets
cd apps/raas-gateway
wrangler secret put JWT_SECRET
wrangler secret put POLAR_WEBHOOK_SECRET
wrangler secret put SERVICE_TOKEN

# Polar.sh Dashboard
open https://polar.sh/dashboard

# Supabase Dashboard
open https://supabase.com/dashboard

# Anthropic API Keys
open https://console.anthropic.com/settings/keys

# OpenRouter API Keys
open https://openrouter.ai/keys
```

---

## 🗒️ Notes

- **75% configured** — Infrastructure is ready (D1, KV, AI binding)
- **P0 blocker:** Polar.sh products + Cloudflare secrets
- **PayOS configured** — Ready for Vietnamese payments
- **Vercel OIDC tokens** — Auto-generated, valid for deployments

---

**Report Location:** `/plans/reports/complete-credentials-inventory-260320.md`
**Next Action:** Set Cloudflare secrets + Create Polar.sh products
