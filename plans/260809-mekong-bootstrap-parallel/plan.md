---
title: "Mekong CLI v6.0 Parallel Bootstrap Plan"
description: "Parallel execution plan for 3 core funnels (Zalo OA, Tax & Accounting, Sophia AI Video)"
status: phase2-complete
priority: P0
effort: 12h
branch: kongming-kill-list-5.0.0
tags: [bootstrap, parallel, funnels, v6.0]
created: 2026-08-09
---

# Mekong CLI v6.0 Parallel Bootstrap Plan

## Dependency Graph

```
Phase 1: Foundation (Sequential) ──────────────────────► 1.1-1.4 (Done)
                                                              │
Phase 2: Core Funnels (PARALLEL - 3 agents) ─────────────────┼──►
                                                              │
    ┌─────────────────┬─────────────────┬─────────────────┐   │
    │ 2.1 Zalo OA     │ 2.2 Tax & Acct  │ 2.3 Sophia AI   │   │
    │ Funnel          │ Funnel          │ Video Factory   │   │
    │ (Agent 1)       │ (Agent 2)       │ (Agent 3)       │   │
    └─────────────────┴─────────────────┴─────────────────┘   │
                                                              │
Phase 3: Integration & Billing (Sequential) ◄─────────────────┘
    3.1 MCU Billing ──► 3.2 Polar Webhooks ──► 3.3 Tier Gates ──► 3.4 Integration Tests
                                                              │
Phase 4: CLI & DX (Parallel - 2 agents) ──────────────────────┼──►
    ┌──────────────────────┬──────────────────────┐            │
    │ 4.1-4.2 CLI/TUI      │ 4.3-4.4 Setup/Docs   │            │
    └──────────────────────┴──────────────────────┘            │
                                                              │
Phase 5: Testing & Hardening (Sequential) ────────────────────┤
    5.1 E2E Tests ──► 5.2 Security ──► 5.3 Perf ──► 5.4 Deploy
                                                              │
Phase 6: Ship & Onboard (Sequential) ─────────────────────────┘
    6.1 Release ──► 6.2 Onboard ──► 6.3 Monitor
```

## Execution Strategy

**Parallel Groups:**
- Group A (Phase 2): 3 agents running independently on separate funnels
- Group B (Phase 4): 2 agents on CLI/TUI vs Setup/Docs

**Sequential Dependencies:**
- Phase 3 waits for all Phase 2 funnels complete
- Phase 5 waits for Phase 3 & 4 complete
- Phase 6 waits for Phase 5 complete

## File Ownership Matrix

| Phase | Files Owned | No Overlap With |
|-------|-------------|-----------------|
| 2.1 Zalo | `src/seed/zalo/**`, `tests/e2e/zalo/**`, `src/api/zalo_routes.py` | 2.2, 2.3 |
| 2.2 Tax | `src/seed/tax/**`, `tests/e2e/tax/**`, `src/api/tax_routes.py` | 2.1, 2.3 |
| 2.3 Sophia | `apps/sophia-ai-factory/**`, `tests/e2e/sophia/**` | 2.1, 2.2 |
| 3.1 MCU | `src/billing/mcu.py`, `src/billing/ledger.py` | - |
| 3.2 Polar | `src/api/billing_endpoints.py`, `src/services/polar_client.py` | - |
| 3.3 Tier Gates | `src/middleware/license_gate.py`, `src/seed/auth/tier_gate.py` | - |
| 4.1-4.2 CLI | `cli/**`, `src/cli/**` | 4.3-4.4 |
| 4.3-4.4 Setup/Docs | `docs/**`, `cli/commands/setup.py` | 4.1-4.2 |
| 5.1-5.4 Tests | `tests/**` (all funnel tests) | - |

## Phase Details

### Phase 2.1: Zalo OA Funnel (Agent: zalo-funnel)

**Context Links:** Parent plan → `../mekong-bootstrap-plan.md`, Architecture → `../../docs/architecture/system-architecture.md`

**Parallelization Info:** Runs in parallel with 2.2 and 2.3. Exclusive ownership of `src/seed/zalo/` and Zalo-related API routes.

**Overview:** Build complete Zalo Official Account integration for customer communication automation.

**Key Insights:**
- Zalo OA API uses REST + Webhook (HMAC-SHA256)
- Need message template engine with VN/EN i18n
- Rate limiting per OA account (KV-based)
- Webhook at `/api/webhooks/zalo`

**Requirements:**
1. Zalo OA API client with auth token management
2. Webhook handler with signature verification
3. Message templates (text, image, carousel) with i18n
4. Automation rules engine (keyword → action)
5. Rate limiter (100 req/min per OA)

**Architecture:**
```
src/seed/zalo/
├── client.py          # API client (REST)
├── webhook.py         # FastAPI webhook handler
├── templates.py       # Jinja2 templates VN/EN
├── automation.py      # Rules engine
├── rate_limiter.py    # Cloudflare KV
├── models.py          # Pydantic models
└── tests/
    ├── test_client.py
    ├── test_webhook.py
    ├── test_templates.py
    └── test_automation.py
```

**Related Code Files (EXCLUSIVE):**
- `src/seed/zalo/**` (new)
- `src/api/zalo_routes.py` (new - FastAPI routes)
- `tests/e2e/zalo/**` (new)
- `contracts/zalo-webhook.json` (new)

**File Ownership:** This phase exclusively owns all files under `src/seed/zalo/` and `src/api/zalo_routes.py`

**Implementation Steps:**
1. Create `src/seed/zalo/` directory structure
2. Implement `client.py` with token refresh
3. Implement `webhook.py` with HMAC verification
4. Implement `templates.py` with VN/EN i18n
5. Implement `automation.py` rules engine
6. Implement `rate_limiter.py` with KV
7. Create FastAPI routes in `src/api/zalo_routes.py`
8. Write unit tests for each module
9. Write E2E tests simulating Zalo webhook
10. Add to API gateway routing

**Todo List:**
- [x] Create directory structure
- [x] Implement client.py
- [x] Implement webhook.py
- [x] Implement templates.py
- [x] Implement automation.py
- [x] Implement rate_limiter.py
- [x] Create API routes
- [x] Write unit tests
- [x] Write E2E tests
- [x] Integration test with API gateway

**Success Criteria:**
- [ ] Zalo webhook receives & verifies messages
- [ ] Template messages render in VN & EN
- [ ] Automation rules execute on keywords
- [ ] Rate limiting enforces 100 req/min
- [ ] All unit tests pass (>80% coverage)
- [ ] E2E test passes with real webhook simulation

**Conflict Prevention:**
- Only touches `src/seed/zalo/` and `src/api/zalo_routes.py`
- No imports from `src/seed/tax/` or `apps/sophia-ai-factory/`
- Uses shared `src/seed/config/` for env only

**Risk Assessment:**
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Zalo API changes | Medium | High | Adapter pattern, versioned client |
| Webhook verification fails | Low | High | Comprehensive test vectors |
| Rate limit too strict | Low | Medium | Configurable via env |

**Security Considerations:**
- HMAC-SHA256 webhook verification mandatory
- No tokens in logs
- Rate limiting prevents abuse
- Input sanitization on all webhook payloads

---

### Phase 2.2: Tax & Accounting Funnel (Agent: tax-funnel)

**Context Links:** Parent plan → `../mekong-bootstrap-plan.md`, Architecture → `../../docs/architecture/system-architecture.md`

**Parallelization Info:** Runs in parallel with 2.1 and 2.3. Exclusive ownership of `src/seed/tax/` and Tax-related API routes.

**Overview:** Build Vietnam tax compliance engine (TNCN/TNDN/GTGT) with TT78 invoice generation.

**Key Insights:**
- Decimal-only arithmetic for currency (no float)
- Annual tax rate configs (2024, 2025, 2026...)
- TT78-compliant PDF invoices with digital signature
- MISA/ERP export compatibility

**Requirements:**
1. TNCN (Personal Income Tax) calculator
2. TNDN (Corporate Income Tax) calculator
3. GTGT (VAT) calculator
4. TT78 PDF invoice generator
5. Compliance report generator
6. MISA/CSV/Excel exporters
7. Config-driven tax rates

**Architecture:**
```
src/seed/tax/
├── calculator.py      # TNCN/TNDN/GTGT calculator
├── invoice.py         # TT78 PDF generator (ReportLab)
├── compliance.py      # Report generator
├── exporters.py       # MISA/CSV/Excel export
├── config/
│   ├── rates_2024.yaml
│   ├── rates_2025.yaml
│   └── rates_2026.yaml
├── models.py          # Pydantic models
└── tests/
    ├── test_calculator.py
    ├── test_invoice.py
    ├── test_compliance.py
    └── test_exporters.py
```

**Related Code Files (EXCLUSIVE):**
- `src/seed/tax/**` (new)
- `src/api/tax_routes.py` (new)
- `tests/e2e/tax/**` (new)
- `contracts/tax-invoice.json` (new)

**File Ownership:** This phase exclusively owns all files under `src/seed/tax/` and `src/api/tax_routes.py`

**Implementation Steps:**
1. Create `src/seed/tax/` directory structure
2. Create tax rate configs (2024-2026)
3. Implement `calculator.py` with Decimal arithmetic
4. Implement `invoice.py` TT78 PDF generator
5. Implement `compliance.py` report generator
6. Implement `exporters.py` for MISA/CSV/Excel
7. Create FastAPI routes in `src/api/tax_routes.py`
8. Write unit tests with official test cases
9. Write E2E tests with real tax scenarios
10. Add to API gateway routing

**Todo List:**
- [x] Create directory structure
- [x] Create tax rate configs
- [x] Implement calculator.py
- [x] Implement invoice.py
- [x] Implement compliance.py
- [x] Implement exporters.py
- [x] Create API routes
- [x] Write unit tests
- [x] Write E2E tests
- [x] Integration test with API gateway

**Success Criteria:**
- [ ] TNCN/TNDN/GTGT calculations match official rates
- [ ] TT78 PDF invoices valid per Vietnam tax law
- [ ] Digital signature support for e-invoices
- [ ] MISA export format compatible
- [ ] All unit tests pass (>80% coverage)
- [ ] E2E test passes with real tax scenarios

**Conflict Prevention:**
- Only touches `src/seed/tax/` and `src/api/tax_routes.py`
- No imports from `src/seed/zalo/` or `apps/sophia-ai-factory/`
- Uses shared `src/seed/config/` for env only

**Risk Assessment:**
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Tax law changes | Low | High | Config-driven rates, annual update |
| PDF generation fails | Low | High | Multiple lib fallbacks (ReportLab/WeasyPrint) |
| Decimal precision | Low | High | Use Python Decimal everywhere |

**Security Considerations:**
- No financial data in logs
- Input validation on all tax params
- Digital signature for invoice integrity

---

### Phase 2.3: Sophia AI Video Factory (Agent: sophia-funnel)

**Context Links:** Parent plan → `../mekong-bootstrap-plan.md`, Architecture → `../../docs/architecture/system-architecture.md`

**Parallelization Info:** Runs in parallel with 2.1 and 2.2. Exclusive ownership of `apps/sophia-ai-factory/` (TypeScript/Cloudflare Workers).

**Overview:** Build AI Video Factory on Cloudflare Workers with D-ID, ElevenLabs, OpenRouter integration and MCU billing.

**Key Insights:**
- Cloudflare Workers + Durable Objects for stateful pipelines
- 3 AI providers: D-ID (avatar video), ElevenLabs (TTS), OpenRouter (script)
- MCU billing per video second
- Webhook callbacks for async completion

**Requirements:**
1. Hono-based Worker entry point
2. Durable Object video pipeline orchestrator
3. D-ID client (avatar video generation)
4. ElevenLabs client (text-to-speech)
5. OpenRouter client (script generation)
6. MCU credit tracker (Durable Object)
7. Webhook callbacks for completion

**Architecture:**
```
apps/sophia-ai-factory/
├── package.json
├── wrangler.toml
├── src/
│   ├── index.ts           # Hono entry + routes
│   ├── video/
│   │   ├── pipeline.ts    # Durable Object orchestrator
│   │   ├── did.ts         # D-ID client
│   │   ├── elevenlabs.ts  # ElevenLabs client
│   │   └── openrouter.ts  # OpenRouter client
│   ├── billing/
│   │   └── mcu.ts         # MCU credit tracker (DO)
│   └── webhooks/
│       └── callbacks.ts   # Async completion handlers
├── tests/
│   ├── test_pipeline.ts
│   ├── test_billing.ts
│   └── test_integration.ts
└── vitest.config.ts
```

**Related Code Files (EXCLUSIVE):**
- `apps/sophia-ai-factory/**` (new)
- `tests/e2e/sophia/**` (new)
- `contracts/sophia-video.json` (new)

**File Ownership:** This phase exclusively owns all files under `apps/sophia-ai-factory/`

**Implementation Steps:**
1. Create `apps/sophia-ai-factory/` with package.json
2. Configure `wrangler.toml` with Durable Objects bindings
3. Implement `src/index.ts` Hono entry
4. Implement `video/pipeline.ts` Durable Object
5. Implement 3 AI provider clients
6. Implement `billing/mcu.ts` credit tracker
7. Implement `webhooks/callbacks.ts` async handlers
8. Write unit tests for each module
9. Write E2E tests with test-mode AI providers
10. Deploy to Cloudflare Workers staging

**Todo List:**
- [ ] Create project structure
- [ ] Configure wrangler.toml
- [ ] Implement index.ts
- [ ] Implement pipeline.ts (DO)
- [ ] Implement did.ts
- [ ] Implement elevenlabs.ts
- [ ] Implement openrouter.ts
- [ ] Implement mcu.ts
- [ ] Implement callbacks.ts
- [ ] Write unit tests
- [ ] Write E2E tests
- [ ] Deploy to staging

**Success Criteria:**
- [ ] Video pipeline creates avatar video from script
- [ ] TTS generates audio from text
- [ ] Script generation via OpenRouter works
- [ ] MCU credits deducted per video second
- [ ] Webhook callbacks fire on completion
- [ ] All unit tests pass
- [ ] E2E test passes in test mode
- [ ] Deployed to CF Workers staging

**Conflict Prevention:**
- Only touches `apps/sophia-ai-factory/` (TypeScript)
- No Python imports - completely separate stack
- Communicates via HTTP API only
- MCU billing via shared contract (HTTP)

**Risk Assessment:**
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| CF Workers cold start | Low | Medium | Warm binding, min instances |
| AI provider API changes | Medium | High | Versioned clients, fallback |
| Durable Object limits | Low | High | Batch operations, pagination |
| MCU sync across funnels | Medium | High | Shared billing API, idempotency |

**Security Considerations:**
- API keys encrypted in Workers secrets
- Webhook signature verification
- Rate limiting per user tier
- No PII in video metadata

---

## Next Steps

After all 3 Phase 2 funnels complete:
1. **Phase 3**: Integration & Billing (sequential)
2. **Phase 4**: CLI & Developer Experience (parallel)
3. **Phase 5**: Testing & Hardening (sequential)
4. **Phase 6**: Ship & Onboard (sequential)

## Validation

Run validation interview before implementation:
```
/plan:validate /Users/macbook/mekong-cli/plans/260809-mekong-bootstrap-parallel/plan.md
```