# Mekong CLI v6.0 Bootstrap Plan

## Overview
Complete bootstrap from git init to production ship for Mekong CLI v6.0 — AI-operated business platform for Vietnamese one-person companies with 3 core funnels.

## Phase Dependency Graph

```
Phase 1: Foundation (Sequential)
    │
    ├─▶ 1.1 Git & Repo Setup
    ├─▶ 1.2 Environment & Config
    ├─▶ 1.3 Quality Gates (Lint, Type, Test)
    └─▶ 1.4 CI/CD Pipeline
            │
Phase 2: Core Funnels (Parallel - 3 agents)
    │
    ├─▶ 2.1 Zalo OA Funnel
    ├─▶ 2.2 Tax & Accounting Funnel
    └─▶ 2.3 Sophia AI Video Factory
            │
Phase 3: Integration & Billing (Sequential)
    │
    ├─▶ 3.1 MCU Billing System
    ├─▶ 3.2 Polar.sh Webhooks
    ├─▶ 3.3 Tier Gates & License
    └─▶ 3.4 Cross-Funnel Integration Tests
            │
Phase 4: CLI & Developer Experience (Parallel)
    │
    ├─▶ 4.1 CLI Command Completion
    ├─▶ 4.2 TUI & Interactive Mode
    ├─▶ 4.3 Setup Wizard (Bilingual)
    └─▶ 4.4 Documentation (VN/EN)
            │
Phase 5: Testing & Hardening (Sequential)
    │
    ├─▶ 5.1 End-to-End Funnel Tests
    ├─▶ 5.2 Security Audit
    ├─▶ 5.3 Performance & Load Tests
    └─▶ 5.4 Production Deploy & Smoke
            │
Phase 6: Ship & Onboard (Sequential)
    │
    ├─▶ 6.1 Release Tagging
    ├─▶ 6.2 Client Onboarding Guide
    └─▶ 6.3 Post-Launch Monitoring
```

## Detailed Phase Plans

### Phase 1: Foundation (Sequential)

#### 1.1 Git & Repo Setup ✅
- **Status**: Complete
- **Current**: Branch `kongming-kill-list-5.0.0`, main exists
- **Action**: Clean up working tree, commit staged changes

#### 1.2 Environment & Config
- **Files**: `.env.example`, `.env.api.example`, `.env.production.template`
- **Action**: Validate all templates, create `.env` from example
- **Secrets**: SUPABASE, OPENROUTER, ELEVENLABS, D-ID, POLAR

#### 1.3 Quality Gates
```bash
# Python
ruff check src/ tests/
mypy src/
pytest tests/ -v

# TypeScript
cd apps/api && npm run lint && npm run typecheck
cd apps/dashboard && npm run lint && npm run typecheck
```

#### 1.4 CI/CD Pipeline
- GitHub Actions workflow for:
  - Python lint/type/test
  - TypeScript lint/type/test
  - Build & deploy Workers
  - Build & deploy Dashboard (CF Pages)

### Phase 2: Core Funnels (Parallel)

#### 2.1 Zalo OA Funnel (`src/seed/zalo/`)
**Agent 1: zalo-funnel**
```
src/seed/zalo/
├── __init__.py
├── client.py          # Zalo OA API client
├── webhook.py         # FastAPI webhook handler
├── templates.py       # Message templates (VN/EN)
├── automation.py      # Rules engine
├── rate_limiter.py    # KV-based rate limiting
└── tests/
    ├── test_client.py
    ├── test_webhook.py
    └── test_templates.py
```
**API Endpoints**: `/api/webhooks/zalo`, `/api/v1/zalo/*`
**Key Features**:
- Webhook verification (HMAC-SHA256)
- Template messages with i18n
- Automation rules (keyword → action)
- Rate limiting per OA account

#### 2.2 Tax & Accounting Funnel (`src/seed/tax/`)
**Agent 2: tax-funnel**
```
src/seed/tax/
├── __init__.py
├── calculator.py      # TNCN/TNDN/GTGT calculator
├── invoice.py         # TT78 PDF generator
├── compliance.py      # Report generator
├── exporters.py       # MISA/CSV/Excel export
├── config/
│   ├── rates_2024.yaml
│   └── rates_2025.yaml
└── tests/
    ├── test_calculator.py
    ├── test_invoice.py
    └── test_compliance.py
```
**Key Features**:
- Decimal-only arithmetic
- Annual tax rate configs
- TT78-compliant PDF invoices
- Digital signature support
- MISA-compatible export

#### 2.3 Sophia AI Video Factory (`apps/sophia-ai-factory/`)
**Agent 3: sophia-funnel**
```
apps/sophia-ai-factory/
├── package.json
├── wrangler.toml
├── src/
│   ├── index.ts           # Hono entry point
│   ├── video/
│   │   ├── pipeline.ts    # Durable Object orchestrator
│   │   ├── did.ts         # D-ID client
│   │   ├── elevenlabs.ts  # ElevenLabs TTS client
│   │   └── openrouter.ts  # OpenRouter LLM client
│   ├── billing/
│   │   └── mcu.ts         # MCU credit tracker
│   └── webhooks/
│       └── callbacks.ts   # Async completion handlers
├── tests/
│   ├── test_pipeline.ts
│   └── test_billing.ts
└── vitest.config.ts
```
**Key Features**:
- Durable Objects for stateful video pipelines
- 3 AI providers: D-ID (video), ElevenLabs (audio), OpenRouter (script)
- MCU billing per video second
- Webhook callbacks for completion

### Phase 3: Integration & Billing (Sequential)

#### 3.1 MCU Billing System (`src/billing/mcu.py`)
- Singleton `MCUBilling` class
- Credit ledger with audit trail
- Tier-based limits (BASIC/PREMIUM/ENTERPRISE/MASTER)
- Real-time balance checks

#### 3.2 Polar.sh Webhooks (`src/api/billing_endpoints.py`)
- Idempotent webhook handler
- Event deduplication via `event_id`
- Tier activation on `subscription.active`
- Graceful downgrade on `subscription.cancelled`

#### 3.3 Tier Gates & License (`src/middleware/license_gate.py`)
- JWT validation + balance check middleware
- Applied to all premium routes
- License file at `~/.mekong/license.json`

#### 3.4 Cross-Funnel Integration Tests
- Test full flow: Payment → Tier → Feature Access
- Test MCU deduction across funnels
- Test webhook reliability with retries

### Phase 4: CLI & Developer Experience (Parallel)

#### 4.1 CLI Command Completion
- Complete all 43 wired commands
- Fix any broken imports
- Add missing command handlers

#### 4.2 TUI & Interactive Mode (`cli/tui/`)
- Warp-style command palette
- Block-based output rendering
- tmux integration for multi-pane

#### 4.3 Setup Wizard (`cli/commands/setup.py`)
- Bilingual (VN/EN) prompts
- API key entry with validation
- Tier selection
- Auto-generate `.env`

#### 4.4 Documentation (`docs/`)
```
docs/
├── README.md                    # ≤300 lines, bilingual
├── project-overview-pdr.md      # Product Dev Requirements
├── code-standards.md            # Coding conventions
├── system-architecture.md       # Architecture diagrams
├── development-roadmap.md       # Phase tracking
├── project-changelog.md         # Version history
├── user-onboarding-flow.md      # CEO guide with emoji
├── operator-runbook.md          # Operations guide
└── api/
    ├── zalo.md
    ├── tax.md
    └── sophia.md
```

### Phase 5: Testing & Hardening (Sequential)

#### 5.1 End-to-End Funnel Tests
```bash
# Each funnel has real API test
pytest tests/e2e/zalo/ -v
pytest tests/e2e/tax/ -v
pytest tests/e2e/sophia/ -v
```
- Real Zalo webhook simulation
- Real tax calculation with official rates
- Real video generation (test mode)

#### 5.2 Security Audit
- `bandit -r src/` for Python
- `npm audit` for Node.js
- Secret scanning (gitguardian)
- Dependency vulnerability check

#### 5.3 Performance & Load Tests
- API Gateway: 1000 req/min sustained
- Video pipeline: 10 concurrent generations
- MCU billing: 1000 operations/sec

#### 5.4 Production Deploy & Smoke
```bash
# Deploy all workers
wrangler deploy --env production  # apps/api
wrangler deploy --env production  # apps/sophia-ai-factory
# Deploy dashboard
npm run deploy:dashboard          # CF Pages

# Smoke tests
curl https://api.mekong.dev/health
curl https://sophia.mekong.dev/health
```

### Phase 6: Ship & Onboard (Sequential)

#### 6.1 Release Tagging
```bash
git tag -a v6.0.0 -m "Mekong CLI v6.0 - Three Funnels GA"
git push origin v6.0.0
```

#### 6.2 Client Onboarding Guide
- Bilingual step-by-step with emoji
- API key setup screenshots
- First campaign walkthrough
- Troubleshooting FAQ

#### 6.3 Post-Launch Monitoring
- Sentry alerts configured
- PostHog dashboards live
- Uptime monitoring (CF Health Checks)
- Weekly metrics review cadence

## Success Criteria

| Metric | Target |
|--------|--------|
| All 3 funnels deployed | ✅ |
| E2E tests passing | 100% |
| Security audit | 0 critical |
| API p99 latency | <500ms |
| Build passes | 0 errors |
| Bilingual docs | 100% coverage |
| CEO can onboard solo | ✅ |

## Resource Allocation

| Phase | Agents | Duration | Parallel |
|-------|--------|----------|----------|
| 1 | 1 (sequential) | 2h | No |
| 2 | 3 (parallel) | 4h | Yes |
| 3 | 1 (sequential) | 2h | No |
| 4 | 2 (parallel) | 3h | Partial |
| 5 | 1 (sequential) | 3h | No |
| 6 | 1 (sequential) | 1h | No |

**Total Wall Time**: ~15h (with parallelization)
**Total Agent Hours**: ~24h

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Zalo API changes | Medium | High | Adapter pattern, versioned client |
| Tax law update | Low | High | Config-driven rates, annual review |
| CF Workers limits | Low | Medium | Durable Objects, batching |
| Polar webhook failures | Medium | High | Idempotency, dead letter queue |
| Bilingual sync drift | Medium | Low | Single-source i18n, automated check |