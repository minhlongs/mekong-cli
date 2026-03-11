# Mekong CLI — Product Retrospective

## Sprint 1 Retrospective (Q1 2026, Sprint 1)
**Period:** 2026-02-24 to 2026-03-07
**Format:** Solo CTO + CC CLI subagent team
**Facilitator:** OpenClaw CTO

---

## What We Shipped (Sprint 1 Actual)

### Delivered
- [x] Cloudflare migration: Workers + D1 + KV + Queues + R2 (`feat(cloudflare)`)
- [x] Anthropic SDK core engine injection (`feat(ai): inject official Anthropic SDK`)
- [x] OCOP agricultural export commands with contracts (`feat(ocop)`)
- [x] Sophia proposal migration to Cloudflare Pages (`feat(sophia-proposal)`)
- [x] CI/CD fix: import names + backend test ignore for cc-cli workflow
- [x] D1 migration files scaffolded: `apps/algo-trader/src/db/migrations/`
- [x] Cloudflare adapters: D1 client, KV cache, Queues producer/consumer, R2 storage

### Not Delivered (Rolled to Sprint 2)
- [ ] Plugin marketplace v1 — scoped too large, underestimated sandboxing
- [ ] `mekong status` AGI score integration — dependency on `agi_score.py` stabilization
- [ ] `make self-test` 100/100 — factory contract coverage at ~80%
- [ ] Cross-session intelligence — deprioritized for infra work

---

## Went Well

### 1. Cloudflare Migration Execution Quality
The Cloudflare infra migration (`D1 + KV + R2 + Queues`) was clean — adapters are standalone files with clear interfaces. No existing code broken. Pattern: write new adapter → import in job file → do not modify core.

**Lesson:** The adapter pattern in `src/jobs/` works. Stick to it for all future provider integrations.

### 2. PEV Loop Reliability on `cook`
`mekong cook` had 0 reported crashes during sprint. Rollback triggered correctly in 3 known failure cases in testing. Verifier exit code check + LLM assessment dual-mode working well.

**Lesson:** The dual-mode verifier (shell exit code + LLM review) is more reliable than either alone. Keep both paths.

### 3. Universal LLM Fallback Chain
`src/core/fallback_chain.py` correctly fell back from OpenRouter timeout → DeepSeek → Ollama in 2 manual tests. No mission loss.

**Lesson:** Fallback chain order matters — document it publicly. Users don't know it exists. Add to README.

### 4. OCOP Domain Commands
Adding `mekong ocop/*` commands with domain-specific contracts demonstrated the extensibility model clearly. New commands took ~2 hours each to scaffold from JSON contract to working CLI.

**Lesson:** 2 hours per new command = viable for community contributors. Write a CONTRIBUTING guide with this template.

---

## What Didn't Go Well

### 1. Plugin Marketplace Underscoped
Estimated 2 days. Actual: blocked at day 1 on sandboxing decision (subprocess isolation vs importlib vs venv). No decision made → deferred entirely.

**Root cause:** Didn't spike on sandboxing options before putting in sprint. Treated as implementation when it was actually a design decision.

**Action:** Before S2-01, write a 1-page design doc: "Plugin isolation strategy v1". Options: (a) no sandbox, trust PyPI, (b) subprocess isolation, (c) venv per plugin. Choose (a) for v1 with documented security warning.

### 2. CI/CD Workflow Fragility
`fix(ci): correct import names` commit required mid-sprint — CI was red for 6 hours. Import naming inconsistency between main and cc-cli workflow was a pre-existing issue.

**Root cause:** Different test scopes in different workflow files — not audited before sprint start.

**Action:** Add `make lint-ci` target that validates all workflow YAML files against known import paths. Run in pre-commit.

### 3. `make self-test` Score Unknown
Ended sprint without a clear `make self-test` baseline score. Factory contracts exist (`factory/contracts/`) but automated validation coverage unknown.

**Root cause:** No CI step runs `make self-test`. It's manual only.

**Action:** Add `make self-test` as a required CI step. Target: run on every PR, gate on score >= 80.

### 4. Context Drift Between Sessions
Multiple CC CLI subagent sessions during sprint lost context about what had been partially implemented. Required re-reading code at start of each session.

**Root cause:** No `.mekong/context.json` or session summary mechanism.

**Action:** Sprint 2 S2-07: cross-session context file. Even a simple JSON with last 3 task summaries would eliminate 20 min of re-orientation per session.

---

## Metrics

| Metric | Target | Actual | Delta |
|--------|--------|--------|-------|
| P0 items shipped | 5 | 4 | -1 (plugin deferred) |
| Test count | 65 | 62 | -3 |
| CI green rate | 100% | 83% | -17% (6h red) |
| `make self-test` | 95/100 | unknown | N/A |
| Rollback triggered correctly | 100% | 100% | on target |
| LLM fallback worked | 100% | 100% | on target |

---

## Feedback from Usage

### Internal (CTO usage)
- `mekong cook --dry-run` is used more than `cook` alone — users want to see the plan first. Consider making dry-run the default flow.
- `--verbose` flag is essential for debugging. Output could be more structured (JSON mode for tooling).
- Error messages on LLM timeout are cryptic (`ConnectionError: ...`). Need user-friendly wrapper.

### External Signals (GitHub, community)
- Most-searched landing page section: "How It Works" (PEV diagram) — architecture resonates
- Most-clicked README link: Ollama free tier setup — price sensitivity confirmed
- Issue filed: "Add `--model` flag to override LLM_MODEL per command" — high demand

---

## Action Items for Sprint 2

| # | Action | Owner | Priority |
|---|--------|-------|----------|
| R1 | Write plugin isolation design doc before starting S2-01 | CTO | P0 |
| R2 | Add `make lint-ci` to validate workflow YAML files | CTO | P1 |
| R3 | Add `make self-test` to CI pipeline | CTO | P1 |
| R4 | Implement S2-07: `.mekong/context.json` cross-session | CTO | P1 |
| R5 | Add `--model` flag to `cook` and `fix` commands | CTO | P2 |
| R6 | Write CONTRIBUTING guide with "2-hour command template" | CC CLI | P2 |
| R7 | Improve LLM timeout error message to user-friendly format | CTO | P2 |

---

## Product Retrospective: Quarterly (Q4 2025 → Q1 2026)

### What Changed
- Migrated from Vercel/Supabase stack → Cloudflare-only (Pages + Workers + D1)
- Added Cloudflare bindings as first-class adapters
- Tôm Hùm daemon architecture stabilized
- Telegram AGI bot (`src/core/telegram_agi.py`) integrated
- Factory contracts: 176 JSON machine contracts defined

### What Stayed the Same (Intentionally)
- PEV loop architecture — do not redesign
- 3-var LLM config (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`) — do not add complexity
- MCU billing tiers — $49/$149/$499 positioning confirmed by beta users
- MIT license — open source strategy validated

### Q1 2026 Theme Shift
From: "Build the system"
To: "Harden and monetize the system"

The architecture is proven. Q1–Q2 focus: reliability, plugin ecosystem, RaaS revenue.

---

## Retrospective Cadence

| Review | Frequency | Format |
|--------|-----------|--------|
| Sprint retro | Bi-weekly | This document |
| Quarterly product retro | Quarterly | Appended to this file |
| Post-mortem (if incident) | Ad-hoc | `reports/overnight/ops/postmortem-*.md` |

---

_Retro owner: OpenClaw CTO_
_Next retro: 2026-03-21 (end of Sprint 2)_
