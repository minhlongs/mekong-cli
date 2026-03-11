# Mekong CLI — Project Status & Management

## Status as of 2026-03-11

**Project:** Mekong CLI v5.0 — AI-operated business platform
**Stage:** Active development — Sprint 2 of Q1 2026
**Health:** YELLOW — CI stability improving, plugin marketplace blocked

---

## Executive Summary

Mekong CLI is a Python CLI tool exposing 289 AI-powered commands across 5 business layers (Founder / Business / Product / Engineer / Ops). The PEV engine (Plan→Execute→Verify) provides unique rollback capability vs competitors. Currently pre-revenue; RaaS billing system built, awaiting first paying customers.

**Key numbers:**
- 289 commands, 245 skills, 176 JSON contracts
- 62 unit tests, ~2.5 min test suite
- Cloudflare-only deploy stack (zero infra cost)
- MCU billing: 3 tiers ($49 / $149 / $499)

---

## Kanban Board

### DONE (Sprint 1 — Merged to main)

| # | Item | Commit | MCU cost |
|---|------|--------|----------|
| D1 | Cloudflare D1/KV/R2/Queues adapters | `f34d70f` `41aef04` | — |
| D2 | Anthropic SDK core engine | `f34d70f` | — |
| D3 | OCOP agricultural export commands | `83f548907` | — |
| D4 | Sophia proposal → Cloudflare Pages | `d8795da55` | — |
| D5 | CI/CD import fix + backend test ignore | `41aef0504` | — |
| D6 | D1 migration files scaffold | untracked | — |

### IN PROGRESS (Sprint 2 — Active)

| # | Item | Owner | ETA | Blocker |
|---|------|-------|-----|---------|
| I1 | Plugin marketplace v1 (install/list/remove) | CTO | Mar 15 | Design doc needed first |
| I2 | `mekong status` AGI score output | CTO | Mar 13 | `agi_score.py` API stable |
| I3 | Rollback coverage: cook + deploy | CTO | Mar 14 | None |
| I4 | MCU gate HTTP 402 user-friendly error | CTO | Mar 12 | None |
| I5 | `make self-test` CI integration | CTO | Mar 18 | Baseline score unknown |

### BLOCKED

| # | Item | Blocked By | Resolution Path |
|---|------|-----------|----------------|
| B1 | Plugin marketplace sandboxing | Design decision not made | Write 1-page design doc, choose option (a) no-sandbox v1 |
| B2 | Cross-session intelligence | Depends on `.mekong/context.json` schema | Schema: `{tasks: [{id, summary, status}], last_updated}` |

### BACKLOG (Next Sprints)

| # | Item | Sprint | Priority |
|---|------|--------|----------|
| BL1 | Swarm mode (`src/core/swarm.py` wired to CLI) | S3 | P1 |
| BL2 | Browser agent GA | S3 | P1 |
| BL3 | `mekong cook --watch` file watcher | S3 | P2 |
| BL4 | `--model` flag per command | S2 tail | P2 |
| BL5 | Supabase adapter | S4 | P2 |
| BL6 | Reflection engine → docs auto-update | S4 | P3 |
| BL7 | `mekong founder/ipo/*` full suite | S5 | P3 |

---

## Milestone Tracker

### Milestone 1: Core PEV Stable — COMPLETE
- [x] `orchestrator.py` plan→execute→verify loop
- [x] Rollback on verifier failure
- [x] Retry policy with exponential backoff
- [x] Universal LLM fallback chain
- Target date: Q4 2025 | Actual: Q4 2025

### Milestone 2: 5-Layer Command Coverage — 85% COMPLETE
- [x] Founder layer: validate, pitch, annual, swot, okr, vc/cap-table
- [x] Business layer: sales, marketing, finance, hr
- [x] Product layer: plan, sprint, roadmap, brainstorm
- [x] Engineer layer: cook, fix, code, test, deploy, review
- [x] Ops layer: audit, health, security, status
- [ ] Founder/IPO full suite (stub only)
- Target date: Q1 2026 | Status: on track

### Milestone 3: RaaS Billing Live — 70% COMPLETE
- [x] MCU billing logic (`src/core/mcu_billing.py`)
- [x] MCU gate (`src/core/mcu_gate.py`) — HTTP 402 on zero balance
- [x] Polar.sh webhook integration planned
- [ ] Polar.sh webhooks end-to-end tested
- [ ] Starter/Pro/Enterprise tiers activated in production
- [ ] First paying customer
- Target date: Q1 2026 | Status: AT RISK (needs focus)

### Milestone 4: Plugin Marketplace v1 — 10% COMPLETE
- [x] `src/core/plugin_marketplace.py` file exists
- [ ] `mekong plugin install` functional
- [ ] Plugin registry with 3+ example plugins
- [ ] Security model documented
- Target date: Q2 2026

### Milestone 5: 1,000 PyPI Downloads/Month — NOT STARTED
- [ ] PyPI package published with correct metadata
- [ ] README install section clear
- [ ] CI publishes on tag
- Target date: Q3 2026

---

## Project Health Indicators

### Code Quality
| Metric | Status | Notes |
|--------|--------|-------|
| `python3 -m pytest` | PASSING | 62 tests, 0 failures |
| CI pipeline | YELLOW | Fixed in `41aef0504`, monitoring |
| Type hints | PARTIAL | Core modules typed, agents incomplete |
| `make self-test` | UNKNOWN | Not yet in CI — Sprint 2 action |
| TODO/FIXME count | ~12 | Audit needed |

### Architecture
| Component | Status | Notes |
|-----------|--------|-------|
| PEV Engine | STABLE | `src/core/orchestrator.py` |
| LLM Client | STABLE | `src/core/llm_client.py` — 7 provider fallback |
| MCU Billing | STABLE | `src/core/mcu_billing.py` |
| Plugin System | ALPHA | Not yet functional from CLI |
| Tôm Hùm Daemon | BETA | `apps/openclaw-worker/` |
| Telegram AGI | BETA | `src/core/telegram_agi.py` |
| Cloudflare Stack | STABLE | Pages + Workers + D1 + KV + R2 |
| RaaS Gateway | BETA | `apps/raas-gateway/` |

### Dependencies
| Dependency | Version | Risk |
|------------|---------|------|
| Python | 3.9.6 (system) | LOW — 3.9+ compatible |
| Typer | latest | LOW |
| Rich | latest | LOW |
| FastAPI | latest | LOW |
| Cloudflare Workers | N/A | MEDIUM — API limits |
| Polar.sh billing | N/A | MEDIUM — webhook testing needed |

---

## Team & Capacity

| Role | Agent | Capacity | Focus |
|------|-------|----------|-------|
| CTO / Lead | OpenClaw | 100% | Architecture, P0 tasks |
| Execution | CC CLI subagent | On-demand | Implementation tasks |
| Customer | Human reviewer | ~10% | Approve, review, strategic |

**Current sprint load:** CTO at ~90% (8-9 tasks in sprint). Risk of scope creep from backlog pull.

---

## Risks & Mitigations

| Risk | Severity | Probability | Status | Mitigation |
|------|----------|-------------|--------|------------|
| Plugin sandboxing decision delay | HIGH | HIGH | ACTIVE | Decide in week 1 of S2 |
| CI red blocks sprint velocity | MEDIUM | MEDIUM | MONITORING | `make lint-ci` added to pre-commit |
| Polar.sh webhook untested | HIGH | MEDIUM | ACTIVE | Schedule integration test this sprint |
| `make self-test` below threshold | MEDIUM | MEDIUM | UNKNOWN | Baseline immediately |
| LLM cost spike (OpenRouter) | LOW | LOW | MONITORING | Qwen fallback saves ~70% |

---

## Communication & Reporting

| Report | Frequency | Location |
|--------|-----------|----------|
| Sprint status | Daily (async) | `.mekong/tasks/` |
| Sprint retrospective | Bi-weekly | `reports/overnight/product/retrospective.md` |
| Product roadmap | Monthly | `reports/overnight/product/roadmap-2026.md` |
| CI/CD status | Per push | GitHub Actions |
| AGI score | Per `mekong status` | Terminal output |

---

## Next Actions (This Week)

1. **Mon 2026-03-11:** Write plugin isolation design doc → unblock B1
2. **Tue 2026-03-12:** Fix MCU 402 error message (I4) — 4 hours
3. **Wed 2026-03-13:** AGI score in `mekong status` (I2) — 4 hours
4. **Thu 2026-03-14:** Rollback coverage cook + deploy (I3) — 8 hours
5. **Fri 2026-03-15:** Plugin install MVP (I1) — first working version

---

_Status owner: OpenClaw CTO_
_Updated: 2026-03-11_
_Next review: 2026-03-18_
