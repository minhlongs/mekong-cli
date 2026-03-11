# Mekong CLI — Product Roadmap 2026

## Vision
AI-operated business platform: submit a goal, receive a result. Universal LLM, 5-layer enterprise coverage, zero-lock-in.

## Current State (Q1 2026)
- PEV Engine (Plan→Execute→Verify) operational — `src/core/orchestrator.py`
- 289 commands across 5 layers (Founder / Business / Product / Engineer / Ops)
- Universal LLM: 3-env-var config supports OpenRouter, DeepSeek, Qwen, Ollama, any OpenAI-compat endpoint
- MCU billing: Starter $49/200cr, Pro $149/1000cr, Enterprise $499/unlimited — `src/core/mcu_billing.py`
- Cloudflare deploy stack: Pages + Workers + D1 + KV + R2 (zero cost)
- Tôm Hùm autonomous daemon: `apps/openclaw-worker/`
- RaaS gateway: `apps/raas-gateway/` (Cloudflare Worker, Telegram auth)
- Telegram AGI bot: `src/core/telegram_agi.py`

---

## Q1 2026 — Foundation Hardening (March–April)

### Priority: CRITICAL
- [ ] **PEV Loop Stability** — rollback coverage on all 289 command paths (`src/core/orchestrator.py`)
- [ ] **Self-heal + retry policy** — `src/core/retry_policy.py` + `src/core/auto_recovery.py` wired to verifier failures
- [ ] **AGI Score dashboard** — expose `src/core/agi_score.py` output in `mekong status` command
- [ ] **MCU gate hardening** — HTTP 402 flow tested end-to-end for all 3 tiers (`src/core/mcu_gate.py`)
- [ ] **Plugin marketplace v1** — `mekong plugin install <name>` functional (`src/core/plugin_marketplace.py`)

### Priority: HIGH
- [ ] **Cross-session intelligence** — `src/core/cross_session_intelligence.py` persists task context between sessions
- [ ] **World model** — `src/core/world_model.py` tracks company state across `company/init`, `annual`, `okr`
- [ ] **Learner integration** — `src/core/learner.py` feeds from execution history to tune planner prompts

---

## Q2 2026 — Market Expansion

### New Command Layers
- [ ] **`mekong founder/ipo/*`** — Full IPO-day execution suite (currently stub)
- [ ] **`mekong finance/cashflow`** — Runway projector connected to real billing data
- [ ] **`mekong sales/pipeline`** — LeadHunter agent → CRM sync (`src/agents/lead_hunter.py`)
- [ ] **`mekong hr/onboard`** — Automated onboarding workflow using `src/agents/company_agent.py`

### Platform Capabilities
- [ ] **Swarm mode** — Parallel agent execution via `src/core/swarm.py` for multi-step campaigns
- [ ] **DAG scheduler** — Complex dependency graphs via `src/core/dag_scheduler.py`
- [ ] **Browser agent GA** — `src/agents/browser_agent.py` exit beta, integrate with `mekong demo`
- [ ] **Vector memory store** — `src/core/vector_memory_store.py` for long-horizon task context

### Developer Experience
- [ ] **`mekong cook --watch`** — Live re-execution on file change (VS Code extension)
- [ ] **JSON output stability** — `--json` flag consistent across all 289 commands
- [ ] **`make self-test` 100/100** — All factory contracts validated by CI

---

## Q3 2026 — Platform Ecosystem

### Integrations
- [ ] **GitHub Actions integration** — `mekong deploy` triggers from CI/CD context
- [ ] **Slack / Discord notifier** — `src/core/notifier.py` supports Slack webhooks
- [ ] **Polar.sh billing v2** — Subscription lifecycle webhooks → MCU credit sync
- [ ] **Supabase adapter** — `mekong/adapters/` supabase.yaml for DB-backed projects

### Intelligence Layer
- [ ] **Reflection engine** — `src/core/reflection.py` post-task analysis → `docs/` updates
- [ ] **Code evolution** — `src/core/code_evolution.py` self-modifies commands based on success rate
- [ ] **Telemetry pipeline** — `src/core/telemetry_reporter.py` → aggregate usage insights (opt-in)

### Scale Features
- [ ] **Multi-tenant isolation** — `src/core/auth_tenant.py` full SaaS support
- [ ] **Dead letter queue** — `src/core/dead_letter_queue.py` for failed mission recovery
- [ ] **Durable step store** — `src/core/durable_step_store.py` survives daemon restarts

---

## Q4 2026 — Enterprise & Monetization

### Enterprise Tier
- [ ] **SSO / SAML** — `src/core/auth_jwt.py` extended for enterprise IdP
- [ ] **Governance controls** — `src/core/governance.py` approval gates, audit trails
- [ ] **License manager** — `src/core/license_manager.py` per-seat billing
- [ ] **Custom LLM routing** — `src/core/routing_strategy.py` per-org model selection

### Monetization
- [ ] **RaaS v2** — Customer dashboard at agencyos.network with real-time mission tracker
- [ ] **Marketplace revenue** — Plugin revenue share for third-party command authors
- [ ] **Enterprise contracts** — Annual $9,600+ tier with SLA and dedicated support

### Launch Goals
- 1,000 PyPI downloads/month
- 100 paying RaaS customers
- 10 enterprise contracts
- AGI Score: 90/100 on `make self-test`

---

## Feature Discovery Backlog (No-Quarter)
- `mekong brand/identity` — AI-generated brand guide from company.json
- `mekong ux-interview` — Simulated user research with persona archetypes
- `mekong product-discovery` — Jobs-to-be-done analysis against market data
- `mekong competitive/monitor` — Ongoing competitor signal tracking

---

## Dependencies & Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM provider outage | HIGH | Fallback chain: OpenRouter → Ollama (`src/core/fallback_chain.py`) |
| Cloudflare Workers limits | MEDIUM | D1 row limits, KV cold start — monitor via `health_watchdog.py` |
| MCU credit abuse | HIGH | Rate limit client + machine fingerprint (`src/core/machine_fingerprint.py`) |
| Python version fragmentation | LOW | Pin to 3.9+ in setup.py, test matrix in CI |

---

_Roadmap owner: OpenClaw CTO_
_Last updated: 2026-03-11_
