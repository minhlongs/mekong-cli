# Product Sprint Planning — Algo-Trader MVP (6 Weeks)

**Report ID:** `product-sprint-260320-0445-algo-trader`
**Date:** 2026-03-20
**Project:** Algo-Trader (apps/algo-trader)
**Status:** MVP Ready → Beta Launch Prep

---

## Executive Summary

Algo-Trader is a production-grade arbitrage trading platform with 1216 passing tests, 0 TypeScript errors, and 17 completed phases. Current state: **exchange connectors (Binance/OKX/Bybit), spread detection, React dashboard, 270+ tests passing**.

**6-Week MVP Goal:** Launch beta with 5 active traders executing real arbitrage strategies.

---

## 1. MVP Feature Scope (MoSCoW Prioritization)

### MUST-HAVE (Week 1-3) — Core Trading Loop

| Feature | Status | Owner | Deliverable |
|---------|--------|-------|-------------|
| Multi-exchange WS price feeds (Binance/OKX/Bybit) | ✅ Complete | Backend | `WebSocketMultiExchangePriceFeedManager` |
| Fee-aware spread detection | ✅ Complete | Backend | `FeeAwareCrossExchangeSpreadCalculator` |
| Real-time opportunity scanner | ✅ Complete | Backend | `RealtimeArbitrageScanner` |
| Order book depth validation | ✅ Complete | Backend | `OrderBookDepthAnalyzer` |
| Atomic order execution | ✅ Complete | Backend | `ArbitrageExecutionEngine` |
| Circuit breaker + risk limits | ✅ Complete | Backend | `AdaptiveCircuitBreaker` |
| Paper trading mode (dry-run) | ✅ Complete | Backend | `PaperTradingEngine` |
| Telegram alert bot | ✅ Complete | Backend | `TelegramCommandHandler` |
| Basic React dashboard | ✅ Complete | Frontend | 5 pages, Zustand state |
| JWT + API key auth | ✅ Complete | Backend | `raas-gate.ts`, sliding window rate limiter |

### SHOULD-HAVE (Week 4-5) — Beta Readiness

| Feature | Status | Owner | Deliverable |
|---------|--------|-------|-------------|
| Polar.sh billing integration | ✅ Complete | Backend | `subscription-service.ts`, webhooks |
| Tenant position tracking | ✅ Complete | Backend | `TenantArbPositionTracker` |
| Trade history export (CSV/JSON) | ✅ Complete | Backend | `Trade History Exporter` |
| CLI dashboard (terminal UI) | ✅ Complete | Backend | `CLI Dashboard` |
| Interactive setup wizard | ✅ Complete | Backend | `setup` command |
| Quickstart (zero-config) | ✅ Complete | Backend | `quickstart` command |
| Market regime detection | ✅ Complete | Backend | `MarketRegimeDetector` |
| Triangular arbitrage scanner | ✅ Complete | Backend | `TriangularArbitrageLiveScanner` |
| Funding rate arb scanner | ✅ Complete | Backend | `FundingRateArbitrageScanner` |

### COULD-HAVE (Week 6) — Polish & Scale

| Feature | Status | Owner | Deliverable |
|---------|--------|-------|-------------|
| Unified AGI arb command (`arb:agi`) | ✅ Complete | Backend | Orchestrator for all strategies |
| Stealth trading (anti-detection) | ✅ Complete | Backend | `BinhPhapStealthStrategy`, `PhantomOrderCloakingEngine` |
| Mobile-responsive dashboard | ✅ Complete | Frontend | Collapsible sidebar, responsive grids |
| Prometheus + Grafana monitoring | ✅ Complete | Backend | `/metrics` endpoint, auto-provisioned |
| Docker Compose (PostgreSQL + Redis) | ✅ Complete | DevOps | `docker-compose.yml`, multi-stage Dockerfile |

### WON'T-HAVE (Post-MVP)

| Feature | Reason | Deferred To |
|---------|--------|-------------|
| Multi-region deployment (Cloudflare Workers edge) | Not critical for 5 beta traders | Phase 6 |
| Advanced ML ensemble strategies | Complexity overkill for MVP | Phase 6 |
| iOS/Android native apps | Web dashboard sufficient | Phase 7 |
| Social trading / copy trading | Post-beta feature | Phase 8 |

---

## 2. 6-Week Sprint Breakdown

### Week 1: Infrastructure & Onboarding

**Goal:** Zero-config setup, beta trader onboarding flow

| Day | Task | Acceptance Criteria |
|-----|------|---------------------|
| Mon | Interactive setup wizard (`setup` command) | Prompts for API keys, auto-generates `.env`, validates key format |
| Tue | Quickstart command (`quickstart`) | Detects missing `.env` → runs setup → demo backtest → shows next steps |
| Wed | Shell script (`one-click-setup-and-start.sh`) | Prerequisites check → npm/pnpm install → CLI wizard |
| Thu | README update — 3-command quickstart flow | `npm install` → `npm run setup` → `npm run quickstart` |
| Fri | Beta trader invitation system | Email template, license key generation, onboarding checklist |

**Deliverables:**
- `src/cli/setup-wizard-command.ts`
- `src/cli/quickstart-zero-config-command.ts`
- `scripts/one-click-setup-and-start.sh`
- Updated `README.md` with quickstart section

---

### Week 2: Core Trading Loop

**Goal:** WS price feeds, spread detection, atomic execution

| Day | Task | Acceptance Criteria |
|-----|------|---------------------|
| Mon | WebSocket price feed manager | Binance/OKX/Bybit WS, auto-reconnect, emits `price-tick` events |
| Tue | Fee-aware spread calculator | Net spread = gross - fees - slippage, 5min TTL cache |
| Wed | Real-time arbitrage scanner | EventEmitter, emits `opportunity` on profitable spreads |
| Thu | Order book depth analyzer | Fetches L2 order book, calculates actual slippage, returns `viable` flag |
| Fri | Atomic cross-exchange executor | `Promise.allSettled` buy/sell parallel, rollback on partial failure |

**Deliverables:**
- `src/execution/websocket-price-feed-manager.ts`
- `src/execution/fee-aware-spread-calculator.ts`
- `src/execution/realtime-arbitrage-scanner.ts`
- `src/execution/order-book-depth-analyzer.ts`
- `src/execution/atomic-cross-exchange-executor.ts`

---

### Week 3: Risk & Safety

**Goal:** Circuit breaker, dry-run mode, Telegram alerts

| Day | Task | Acceptance Criteria |
|-----|------|---------------------|
| Mon | Adaptive circuit breaker | Per-exchange health tracking, latency-based tripping, failure window pruning |
| Tue | Dry-run simulation mode | `live:dry-run` CLI, real WS feeds + paper orders, no real trades |
| Wed | Telegram alert bot | Trade signals, position PnL, anomaly alerts, daily summaries |
| Thu | Anti-detection safety layer | Order timing jitter ±30%, size jitter ±5%, rate governor |
| Fri | Binh Phap stealth strategy | 13 chapters mapped to anti-detection algorithms, exchange profiles |

**Deliverables:**
- `src/execution/adaptive-circuit-breaker.ts`
- `src/execution/paper-trading-engine.ts`
- `src/notifications/telegram-alert-bot.ts`
- `src/execution/anti-detection-safety-layer.ts`
- `src/execution/binh-phap-stealth-strategy.ts`

---

### Week 4: Billing & Analytics

**Goal:** Polar.sh integration, usage metering, revenue analytics

| Day | Task | Acceptance Criteria |
|-----|------|---------------------|
| Mon | Polar.sh subscription service | 3 tiers (FREE/PRO/ENTERPRISE), webhook verification |
| Tue | Usage quota tracking | Redis-backed, alert thresholds at 80%/90%/100%, 429 on overage |
| Wed | Overage calculator | Pro-rated charges, tier-based rates, invoice generation |
| Thu | Revenue analytics dashboard | MRR, ARR, churn rate, LTV, cohort retention |
| Fri | Tenant position tracking | Per-tenant positions, tier limits, PnL snapshots |

**Deliverables:**
- `src/billing/subscription-service.ts`
- `src/billing/usage-metering-service.ts`
- `src/billing/overage-calculator.ts`
- `src/analytics/revenue-analytics.ts`
- `src/core/tenant-position-tracker.ts`

---

### Week 5: Dashboard UI

**Goal:** React SPA, real-time updates, mobile-responsive

| Day | Task | Acceptance Criteria |
|-----|------|---------------------|
| Mon | API client + TypeScript types | Typed fetch wrapper, error handling, retry logic |
| Tue | React hooks (signals, PnL, admin) | `useSignals`, `usePnlAnalytics`, `useAdminControls` |
| Wed | Dashboard components | StatsRow, SignalsPanel, PnLAnalyticsChart, AdminControls |
| Thu | WebSocket real-time updates | `use-dashboard-websocket.ts`, Zustand store integration |
| Fri | Mobile-responsive design | Collapsible sidebar, responsive grids, horizontal scroll tables |

**Deliverables:**
- `dashboard/src/lib/api-client.ts`
- `dashboard/src/types/api.ts`
- `dashboard/src/hooks/use-signals.ts`
- `dashboard/src/hooks/use-pnl-analytics.ts`
- `dashboard/src/components/stats-row.tsx`
- `dashboard/src/components/signals-panel.tsx`
- `dashboard/src/components/pnl-analytics-chart.tsx`
- `dashboard/src/components/admin-controls.tsx`

---

### Week 6: Unified Commands & Beta Prep

**Goal:** Single-command trading, beta onboarding, load testing

| Day | Task | Acceptance Criteria |
|-----|------|---------------------|
| Mon | Unified AGI arb command (`arb:agi`) | Orchestrates all strategies: cross-exchange + triangular + funding rate |
| Tue | Market regime detector integration | Adaptive params per regime (trending/ranging/volatile/calm) |
| Wed | Beta trader onboarding docs | Step-by-step guide, troubleshooting, FAQ |
| Thu | Load testing (7k-23k RPS target) | k6 scripts, p95 < 14ms latency |
| Fri | Go-live checklist & runbook | Pre-flight checks, rollback plan, support channels |

**Deliverables:**
- `src/cli/arb-agi-auto-execution-commands.ts`
- `src/execution/market-regime-detector.ts`
- `docs/beta-onboarding.md`
- `tests/load/raas-gateway-load-test.js`
- `docs/golive-checklist.md`

---

## 3. User Stories (15+ Stories)

### Onboarding & Setup (Stories 1-3)

**Story 1: Zero-Config Quickstart**
> As a new beta trader, I want to start trading in under 5 minutes without manual configuration.

- [ ] `setup` command prompts for API keys
- [ ] `.env` auto-generated with smart defaults
- [ ] `quickstart` runs demo backtest
- [ ] README shows 3-command flow

**Story 2: Exchange Key Management**
> As a trader, I want to securely store API keys for multiple exchanges.

- [ ] Support Binance, OKX, Bybit
- [ ] Validate key format (min length)
- [ ] Encrypt keys at rest
- [ ] Never log or expose secrets

**Story 3: Telegram Phone Trading**
> As a trader, I want to monitor and control trades from my phone.

- [ ] `/status` shows active positions
- [ ] `/balance` shows portfolio value
- [ ] `/arb_live` starts live trading
- [ ] `/stop` halts all trading
- [ ] `/kill` emergency stop

---

### Core Trading (Stories 4-8)

**Story 4: Real-Time Spread Detection**
> As a trader, I want to see profitable arbitrage opportunities in real-time.

- [ ] WS price feeds from all 3 exchanges
- [ ] Fee-aware spread calculation
- [ ] Dashboard shows spread > 0.08%
- [ ] Auto-refresh every 5 cycles

**Story 5: Order Book Depth Validation**
> As a trader, I want to verify liquidity before executing.

- [ ] Fetch L2 order book from each exchange
- [ ] Calculate actual slippage for target size
- [ ] Return `viable` flag if slippage < threshold
- [ ] Discard opportunities with insufficient depth

**Story 6: Atomic Cross-Exchange Execution**
> As a trader, I want simultaneous buy/sell execution to eliminate leg risk.

- [ ] `Promise.allSettled` for parallel orders
- [ ] Rollback on partial failure
- [ ] Track order status per leg
- [ ] Report net PnL after fees

**Story 7: Circuit Breaker Protection**
> As a trader, I want automatic halts on exchange failures.

- [ ] Per-exchange health tracking
- [ ] Latency-based tripping (P95 > threshold)
- [ ] Failure window pruning
- [ ] Auto-recovery on health restore

**Story 8: Market Regime Adaptation**
> As a trader, I want trading parameters to adapt to market conditions.

- [ ] Classify regime (trending/ranging/volatile/calm)
- [ ] Suggest adaptive spread/cooldown/size params
- [ ] Emit `regime-change` events
- [ ] Scanner auto-adjusts thresholds

---

### Risk Management (Stories 9-11)

**Story 9: Paper Trading Mode**
> As a new trader, I want to practice with simulated trades before risking real capital.

- [ ] `live:dry-run` CLI command
- [ ] Real WS feeds, paper orders
- [ ] Track simulated PnL
- [ ] Graceful shutdown with report

**Story 10: Anti-Detection Stealth**
> As a trader, I want to avoid exchange bot detection.

- [ ] Order timing jitter ±30%
- [ ] Size jitter ±5%
- [ ] Rate governor (calls/min, orders/hour)
- [ ] Exchange response monitoring (429/418 auto-pause)
- [ ] Balance checkpoint auto-stop

**Story 11: Emergency Kill Switch**
> As a trader, I want an instant stop button for emergencies.

- [ ] `/kill` Telegram command
- [ ] Immediate halt to all trading
- [ ] Close all open positions
- [ ] Send confirmation alert

---

### Billing & Analytics (Stories 12-15)

**Story 12: Subscription Tiers**
> As a customer, I want flexible pricing tiers based on my trading volume.

- [ ] FREE: $0, 1,000 trades/month
- [ ] PRO: $49, 10,000 trades/month
- [ ] ENTERPRISE: custom, 100,000 trades/month
- [ ] Polar.sh webhook integration

**Story 13: Usage Metering & Alerts**
> As a trader, I want to track my monthly usage and receive alerts.

- [ ] Redis-backed usage tracking
- [ ] Alert thresholds at 80%, 90%, 100%
- [ ] 429 response when quota exceeded
- [ ] Dashboard shows usage gauge

**Story 14: Revenue Analytics**
> As the business owner, I want to track MRR, churn, and LTV.

- [ ] MRR/ARR calculation
- [ ] Churn rate (logo + revenue)
- [ ] LTV:CAC ratio
- [ ] Cohort retention analysis

**Story 15: Trade History Export**
> As a trader, I want to export my trade history for tax reporting.

- [ ] CSV/JSON export formats
- [ ] Filter by date range, exchange, strategy
- [ ] Include fees, PnL, timestamps
- [ ] One-click download button

---

## 4. Success Metrics

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Latency** | < 500ms p95 | WS tick → opportunity detection |
| **Detection Accuracy** | 95%+ | True positives / total opportunities |
| **Alert Delivery** | < 1s | Opportunity → Telegram send |
| **Execution Time** | < 2s | Opportunity → atomic order fill |
| **Circuit Breaker Trip** | < 100ms | Failure detection → halt |
| **API Response** | < 14ms p95 | `/api/v1/arb/scan` endpoint |

### Business Targets (6 Weeks)

| Metric | Target | Current |
|--------|--------|---------|
| **Beta Traders** | 5 active | 0 |
| **Daily Trades** | 50+ | 0 |
| **Win Rate** | 60%+ | N/A |
| **Avg ROI/Trade** | 0.5%+ | N/A |
| **MRR** | $245 (5 × $49) | $0 |
| **Churn** | < 10% | N/A |

### Quality Gates

| Gate | Target | Status |
|------|--------|--------|
| **Tests** | 100% pass | ✅ 1216 tests |
| **TypeScript** | 0 errors | ✅ 0 errors |
| **`any` types** | 0 (prod code) | ✅ 0 |
| **console.log** | 0 (prod code) | ✅ 0 |
| **TODO/FIXME** | 0 | ✅ 0 |
| **Binh Phap Fronts** | 6/6 | ✅ Passing |

---

## 5. Beta Onboarding Plan

### Beta Trader Profile

| Criteria | Target |
|----------|--------|
| **Experience** | 2+ years crypto trading |
| **Capital** | $10k+ deployable |
| **Tech Savvy** | Comfortable with CLI, API keys |
| **Location** | US/EU time zones (sync support) |
| **Commitment** | 2-week trial, daily feedback |

### Onboarding Timeline

**Week -1: Preparation**

| Day | Task | Owner |
|-----|------|-------|
| Mon | Beta invitation email template | Marketing |
| Tue | License key generation (5 keys) | Engineering |
| Wed | Onboarding checklist + FAQ | Docs |
| Thu | Support Slack channel setup | Ops |
| Fri | Beta trader welcome packet | CS |

**Week 1-2: Trial Period**

| Day | Activity | Deliverable |
|-----|----------|-------------|
| Day 1 | Welcome call, setup walkthrough | Trader setup complete |
| Day 2-3 | Paper trading mode | First simulated trades |
| Day 4-5 | Go live (small size) | First real arbitrage trades |
| Week 1 Feedback | Survey + 1:1 interview | Feedback report |
| Week 2 | Scale up size, monitor | Daily PnL reports |
| Week 2 Feedback | Conversion discussion | Paid subscription or churn |

### Feedback Loop

**Daily:**
- Automated Telegram summary (trades, PnL, issues)
- Slack channel: `#beta-traders` for support

**Weekly:**
- Monday: Week ahead plan, feature roadmap
- Friday: Feedback survey (5 questions, 10 min)

**Bi-Weekly:**
- 1:1 interview (30 min) — deep dive on experience
- Product roadmap review — prioritize beta requests

### Beta Metrics Dashboard

| Metric | Week 1 | Week 2 | Target |
|--------|--------|--------|--------|
| Active traders | 5 | 5 | 5 |
| Trades executed | — | — | 50/day |
| Avg win rate | — | — | 60%+ |
| Issues reported | — | — | < 5/week |
| NPS score | — | — | 8+/10 |
| Conversion rate | — | — | 80%+ |

---

## 6. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Exchange API rate limits | High | Medium | Rate governor, jitter, exchange-specific profiles |
| Partial execution (leg risk) | Medium | High | Atomic executor with rollback, circuit breaker |
| Beta trader churn | Medium | High | Daily support, rapid bug fixes, conversion incentives |
| Regulatory scrutiny | Low | High | Terms of service, KYC for ENTERPRISE tier, legal review |
| Cloud infrastructure cost | Low | Medium | Usage metering, overage charges, cost alerts |

---

## 7. Unresolved Questions

1. **Beta trader selection criteria** — Who are the 5 beta traders? Internal team or external?
2. **Pricing tier thresholds** — Are 1k/10k/100k trade limits appropriate for target market?
3. **Support SLA** — What's the target response time for beta trader support requests?
4. **Compliance review** — Do we need legal review before beta launch (SEC, CFTC implications)?
5. **Insurance/reserve fund** — Should we maintain a reserve fund for exchange hacks or bugs?

---

## 8. Next Steps

1. **Immediate (This Week):**
   - [ ] Finalize beta trader list (5 names)
   - [ ] Send invitation emails
   - [ ] Generate license keys
   - [ ] Setup support Slack channel

2. **Week 1-2:**
   - [ ] Onboard 5 beta traders
   - [ ] Monitor daily PnL and issues
   - [ ] Collect Week 1 feedback

3. **Week 3-4:**
   - [ ] Implement beta feedback (bug fixes, UX improvements)
   - [ ] Scale trade sizes
   - [ ] Prepare public launch announcement

4. **Week 5-6:**
   - [ ] Convert beta traders to paid subscriptions
   - [ ] Public launch (Twitter, Discord, Reddit)
   - [ ] Open waitlist for next cohort

---

**Report Status:** ✅ Complete
**Plan Status:** Task #56 updated to `in_progress`
**Next Owner:** Implementation team (2 backend, 1 frontend, 1 quant)
