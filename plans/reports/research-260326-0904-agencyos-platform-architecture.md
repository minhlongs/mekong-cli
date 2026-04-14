# AgencyOS Platform Architecture — Full Audit 2026-03-26

## Solar System Metaphor (User's Vision)

```
                    ☀️ MEKONG CLI (Core Engine)
                    │  PEV Engine, 342 commands
                    │  Universal LLM routing
                    │
        ┌───────────┼───────────────────────┐
        │           │                       │
   🤖 OpenClaw    🏢 SoloOS              💰 MCU Billing
   AI Agent CTO   Autonomous Ops          Credit system
        │           │                       │
   ┌────┴────┬──────┴─────┬────────┬───────┴──────┐
   │         │            │        │              │
  🌍        🔴           🟡      🟢             🔵
 RaaS    AlgoTrade    Sophia   CashClaw      Well
 Gateway  Trading    AI Factory  Simulator   Wellness
```

## Live Domains (6 active, 2 dead)

| Domain | Status | What | Source |
|--------|--------|------|--------|
| agencyos.network | **200** | Main marketing site | apps/agencyos-landing |
| raas.agencyos.network | **200** | RaaS product landing | packages/raas-landing |
| api.agencyos.network | **200** | RaaS Gateway API v5.0.0 | apps/raas-gateway |
| docs.agencyos.network | **200** | Documentation site | packages/mekong-docs |
| app.agencyos.network | **200** | Admin Dashboard | apps/dashboard |
| dashboard.agencyos.network | **200** | Same dashboard (alias) | apps/dashboard |
| mekong-engine.agencyos.network | **DOWN** | PEV Engine Worker | packages/mekong-engine |
| www.agencyos.network | **404** | Not configured | — |

## Monorepo Structure

### Public Packages (50+ in packages/)

| Category | Packages | Purpose |
|----------|----------|---------|
| **Core SDK** | cli-core, openclaw-engine, raas-core, mekong-engine | Platform foundation |
| **Business** | business, billing, sdk, raas-sdk | Revenue logic |
| **UI** | vibe-ui, agencyos-ui, agencyos-dashboard | Interface components |
| **Agents** | agents, vibe-agents, openclaw-agents, solo-os | AI automation |
| **Integrations** | integrations, vibe-payment, vibe-auth | External connectors |
| **Trading** | trading-core, vibe-arbitrage-engine | AlgoTrade primitives |
| **Landing** | raas-landing, mekong-docs, raas-marketplace | Public sites |

### Private Apps (35 in apps/ — gitignored)

| App | Status | Domain |
|-----|--------|--------|
| raas-gateway | **LIVE** | api.agencyos.network |
| agencyos-landing | **LIVE** | agencyos.network |
| dashboard | **LIVE** | app.agencyos.network |
| raas-landing | **LIVE** | raas.agencyos.network |
| algo-trader | **LIVE** (M1 Max) | local only |
| sophia-factory | Built | not deployed |
| well | Built | not deployed |
| 28 others | Various | not deployed |

## Customer Journey — BLOCKED

```
1. Visit agencyos.network ✅
2. Click "Get Started" → raas.agencyos.network ✅
3. See pricing (Starter $49 → Master $299) ✅
4. Click "Buy" → /billing/checkout?plan=starter ✅
5. Need to register → POST /v1/auth/register → 401 ❌ BLOCKED
6. Cannot login → POST /v1/auth/login → 401 ❌ BLOCKED
7. Polar webhook after payment → 401 ❌ BLOCKED
8. Entire revenue flow = DEAD
```

## API Endpoint Audit

| Endpoint | Method | Expected | Actual | Fix |
|----------|--------|----------|--------|-----|
| /health | GET | 200 public | **200** | OK |
| /billing/checkout/products | GET | 200 public | **200** | OK |
| /v1/auth/register | POST | 200 public | **401** | MUST FIX |
| /v1/auth/login | POST | 200 public | **401** | MUST FIX |
| /v1/webhooks/polar | POST | 200 public | **401** | MUST FIX |
| /v1/billing/pricing | GET | 200 public | **401** | Should be public |
| /v1/onboarding/status | GET | 401 (need auth) | 401 | OK |
| /v1/missions | GET | 401 (need auth) | 401 | OK |

## What Works vs What Doesn't

### WORKS (infrastructure solid)
- CF Workers deployment pipeline
- D1 database (288 migrations applied)
- 324 API routes mounted
- Polar product catalog (4 tiers)
- Landing pages (2 sites live)
- Admin dashboard (live)
- Docs site (live)
- DripEmailScheduler (code ready)
- Onboarding wizard (code ready)
- SoloOS heartbeat (running)

### DOESN'T WORK (revenue blockers)
1. Auth middleware blocks public routes (register/login/webhook)
2. No customer has ever signed up (0 tenants in D1)
3. Polar webhooks would fail (401)
4. mekong-engine.agencyos.network DOWN
5. SoloOS loops all dry_run (no real ops)
6. No monitoring/alerting for real customer issues

## Priority Fix List

| # | Fix | Impact | Effort | Unblocks |
|---|-----|--------|--------|----------|
| 1 | Auth: make register/login/webhook public | CRITICAL | 30min | Customer signup |
| 2 | Test full payment flow with Polar sandbox | CRITICAL | 1h | Revenue |
| 3 | Fix mekong-engine.agencyos.network | HIGH | 15min | SDK users |
| 4 | Enable lead-scan loop (tắt dry_run) | MEDIUM | 5min | Lead generation |
| 5 | Add www → agencyos.network redirect | LOW | 5min | SEO |

## Unresolved Questions

1. Auth middleware: is it global in index.ts or per-route? Need to read the actual code.
2. Has Polar sandbox ever been tested end-to-end?
3. Are there actual Polar products created on polar.sh, or just IDs in code?
4. Dashboard at app.agencyos.network — does it connect to real D1 data?
5. 35 apps in apps/ — which ones are abandoned vs planned?
