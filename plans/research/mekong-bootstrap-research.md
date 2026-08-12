# Mekong CLI v6.0 Bootstrap Research Report

## 1. Current Project State

### ✅ Already Built (Production-Ready)
| Component | Status | Evidence |
|-----------|--------|----------|
| **CLI Core (43 commands)** | Complete | `src/cli/entrypoint.py` — Typer app with 9 sub-apps (strategy, dev, mcp, revenue, setup, outreach, content, finance, sales, ops, bridge, workflow, palette) |
| **API Gateway (Cloudflare Workers)** | Complete | `apps/api/src/index.ts` — FastAPI-like worker with rate limiting, KV, D1, AI binding, webhook handling, LLM routing |
| **Dashboard (Next.js)** | Complete | `apps/dashboard/` — Cloudflare Pages deploy, Supabase auth, Polar/Stripe billing UI |
| **Billing System** | Complete | `src/billing/`, `src/commands/license_commands.py` — MCU credits, Polar.sh webhook, tier enforcement (BASIC/PREMIUM/ENTERPRISE/MASTER), gateway validation |
| **Vietnam Tax Engine** | Complete | `src/commands/thue_dnvn.py` — TNCN progressive, TNDN (20%/17% SME), GTGT calculators with 2024-2026 rates |
| **Zalo OA Integration** | Complete | `src/commands/zalo_oa.py` — send, broadcast, followers, caption gen, article posting |
| **Harness Engineering** | Complete | `HARNESS.md`, `AGENTS.md`, `.ck.json`, `sops/`, `agents/registry.yaml`, `evals/solo-ceo-eval.md` |
| **Test Infrastructure** | Complete | 250+ test files in `tests/`, pytest config, coverage rules, benchmark harness |
| **Documentation** | Extensive | 100+ files in `docs/` covering architecture, deployment, plugins, GTM, pricing |

### ⚠️ Partially Built / Needs Integration
| Component | Status | Gap |
|-----------|--------|-----|
| **Setup Wizard** | Stub only | `src/cli/setup_wizard.py` — just echoes "run company/init", no real onboarding |
| **Sophia AI Video Factory** | Empty dir | `apps/sophia-ai-factory/` exists but no code |
| **Telegram Bot** | Test only | `tests/test_telegram_bot.py` exists, no production integration in CLI |
| **Payment Flow (NOWPayments)** | Config only | `.env.example` has keys, no webhook handler in CLI |
| **Economic Particles** | Scaffold only | `mekong/skel/` planned (Phase 3), `docs/economic-particles.md` exists |

### ❌ Missing / Needs Bootstrapping
| Component | Priority | Notes |
|-----------|----------|-------|
| **End-to-end onboarding** | Critical | No single command that sets up API keys, tier, business profile, Zalo OA, tax config |
| **Production deployment automation** | High | `GO_LIVE_PLAYBOOK.md` is manual 90-min process; no CI/CD |
| **Sophia AI Factory** | High | Core funnel — zero implementation |
| **NOWPayments IPN webhook** | High | Required for Vietnam domestic payments (PayOS) |
| **Telegram bot webhook** | Medium | Protected flow per Sophia handover rules |
| **Multi-tenant isolation** | Medium | Current code assumes single tenant |

---

## 2. Full Bootstrap Requirements (Setup → Ship)

### Phase 0: Environment & Secrets (Day 1)
```bash
# 1. Clone & install
git clone https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli && source scripts/shell-init.sh

# 2. Configure LLM (any OpenAI-compatible)
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-...
export LLM_MODEL=anthropic/claude-sonnet-4

# 3. Core secrets (.env) — REQUIRED
SUPABASE_URL=              # Free tier
SUPABASE_KEY=
OPENROUTER_API_KEY=
ELEVENLABS_API_KEY=        # Sophia voice
D_ID_API_KEY=              # Sophia video

# 4. Vietnam payments
ZALO_APP_ID=
ZALO_OA_ACCESS_TOKEN=
NOWPAYMENTS_API_KEY=       # IPN webhook
NOWPAYMENTS_IPN_SECRET=

# 5. Billing (choose one)
POLAR_API_KEY=             # International
POLAR_WEBHOOK_SECRET=
# OR
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
```

### Phase 1: Database & Auth (Day 2-3)
- **Supabase**: Create project, run migrations from `apps/api/migrations/`
- **D1/KV**: Provision Cloudflare bindings for API Gateway
- **Auth**: Configure magic-link (VN phone) + JWT in `src/auth/`

### Phase 2: Payment Integration (Day 3-4)
| Gateway | Webhook Endpoint | Tier Mapping |
|---------|------------------|--------------|
| Polar.sh | `POST /api/webhooks/polar` | Starter→BASIC, Pro→PREMIUM, Enterprise→ENTERPRISE |
| Stripe | `POST /api/webhooks/stripe` | Same mapping via `STRIPE_PRICE_IDS` |
| NOWPayments | `POST /api/webhooks/nowpayments` | VND pricing, IPN verification |

### Phase 3: Core Funnels (Day 5-10)
| Funnel | Commands to Implement | Integration Points |
|--------|----------------------|-------------------|
| **Zalo OA** | `mekong zalo send`, `broadcast`, `followers`, `caption`, `post` | `ZALO_APP_ID`, `ZALO_OA_ACCESS_TOKEN` |
| **Tax & Accounting** | `mekong tax tncn`, `tndn`, `gtgt`, `invoice` | Embedded rates, PDF generation (TT78) |
| **Sophia Video** | `mekong sophia script`, `voice`, `video`, `publish` | ElevenLabs, D-ID, OpenRouter |

### Phase 4: Onboarding Wizard (Day 10-12)
```python
# Single command: mekong setup init
# 1. Select business type (shop_online, cafe, freelancer, dich_vu, san_xuat)
# 2. Enter location (city, bank)
# 3. Paste API keys (guided, masked input)
# 4. Choose tier (BASIC/PREMIUM/ENTERPRISE/MASTER)
# 5. Activate license (Polar/Stripe checkout)
# 6. Verify Zalo OA connection
# 7. Generate first tax estimate
# 8. Create first Sophia video
```

### Phase 5: Deploy & Go-Live (Day 12-14)
```bash
# Dashboard
cd apps/dashboard && npm run build && npx wrangler pages deploy .next --project-name=mekong-ide

# API Gateway
cd apps/api && npx wrangler deploy

# CLI binary
pnpm build:prod  # outputs ./mekong binary
```

### Phase 6: Smoke Test (Day 14)
Per `GO_LIVE_PLAYBOOK.md`:
1. Gateway health: `curl https://api.cashclaw.cc/health`
2. Pricing returns 3 checkout URLs
3. Polar URLs return 302
4. Auth rejects unauthenticated (401)
5. Webhook HMAC verifier loads
6. Credit deduction dry-run
7. Founder buys Starter ($49) → credits arrive → run paid command

---

## 3. Technical Challenges & Validation Needs

| Challenge | Severity | Validation Approach |
|-----------|----------|---------------------|
| **Polar.sh rejected Sophia** | Critical | Must use NOWPayments + PayOS for VN domestic; Polar only for international |
| **VN tax law changes yearly** | High | Embed 2024-2026 rates; add `mekong tax update-rates` command to fetch from `thuedientu.gdt.gov.vn` |
| **Zalo OA rate limits** | High | Implement exponential backoff, queue in `src/daemon/scheduler.py` |
| **Sophia video pipeline latency** | Medium | Async job queue (Celery/Redis or Cloudflare Queues); progress webhook to Telegram |
| **Multi-tenant credit isolation** | High | Each tenant gets dedicated MCU bucket; enforce via `src/middleware/license_gate.py` |
| **CLI binary size** | Medium | `pnpm build:prod` targets bun-darwin-arm64; test on Intel Mac + Linux |
| **Telegram webhook reliability** | Medium | Use Cloudflare Workers as ingress; retry with dead-letter queue |
| **VN phone auth (magic link)** | Medium | Integrate with Viettel/Vinaphone OTP APIs or Zalo login |

---

## 4. Best Practices for AI Business Platform

### Architecture Principles (from HARNESS.md)
1. **Context Budget ≤40k tokens** — Every subagent gets minimal SOP fragment
2. **Harness Engineering** — Shape environment around agents (guardrails, evals, observability)
3. **CEO Solo Model** — One human delegates to 4 layer agents (Business, Product, Eng, Ops)
4. **High-Risk Gates** — Billing, DB writes, deployments require explicit approval

### Code Standards (from CLAUDE.md / development-rules.md)
- **Zero `:any` types** — Strict TypeScript/Python typing
- **Zod validation** on all API inputs
- **Server Actions** for mutations (not API routes)
- **Tier enum**: `BASIC | PREMIUM | ENTERPRISE | MASTER` (uppercase only)
- **Canonical imports** — `@/seed/auth/better-auth-session`, `@/seed/db/client`, `@/seed/config/tiers`
- **No console.log** in production

### Vietnam-Specific Patterns
- **Bilingual docs** (Vietnamese + English) — Required for CEO non-tech users
- **Offline-first tax calc** — No API dependency for TNCN/TNDN/GTGT
- **Zalo OA as primary channel** — Not email/SMS
- **PayOS/VietQR for domestic** — Stripe/Polar blocked or limited in VN
- **Rapid-MLX local LLM** — Qwen 3.6-35B on Apple Silicon (4.2x Ollama)

### Deployment Strategy
- **Manual first** — Founder deploys per `GO_LIVE_PLAYBOOK.md` (90 min)
- **CI/CD after 10 customers** — `.github/workflows/dashboard.yml` later
- **Cloudflare edge** — Workers for API, Pages for Dashboard, KV/D1 for state
- **Observability** — Sentry (all layers), OpenTelemetry traces, Prometheus metrics

---

## 5. Ranked Recommendation

| Rank | Action | Rationale |
|------|--------|-----------|
| **1** | Implement `mekong setup init` wizard | Unblocks everything; single entry point for non-tech CEO |
| **2** | Build NOWPayments IPN webhook + PayOS integration | Required for Vietnam revenue; Polar rejected |
| **3** | Implement Sophia AI Video Factory (script→voice→video) | Core differentiator; 3rd funnel |
| **4** | Wire Telegram bot webhook to CLI commands | Protected flow per Sophia handover rules |
| **5** | Automate deployment (GitHub Actions) | Reduces 90-min manual playbook to push-to-deploy |
| **6** | Add multi-tenant isolation tests | Needed before external customers |

---

## Unresolved Questions

1. **Sophia video hosting** — D-ID returns MP4; store on R2? CDN? Cost at scale?
2. **Zalo OA official account approval** — Requires business license; timeline?
3. **VN tax filing automation** — Current code calculates only; HTKK/HTQL e-filing API access?
4. **Polar.sh rejection details** — Was it Sophia specifically or all VN-facing products?
5. **Team tier (MASTER)** — How many seats? Reseller model?