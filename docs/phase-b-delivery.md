# Phase B: Agentic Core — MVC/NĂNG GIAO BÀN GIAO

> **Date:** 2026-07-07 | **Plan:** `plans/260706-0003-agentic-core-phase-b/` | **Status:** In-Progress (B4 done, B5 scaffolded, B6–B7 running)

---

## Overview

Phase B delivers the agentic core pipeline: a unified PEV (Plan-Execute-Verify) loop that routes natural-language goals through intent classification, agent construction, step-by-step execution, and persistent memory. Seven waves consolidate four years of accumulated scaffolding into a clean, testable, config-driven system.

---

## Components

| ID / Mã | Name / Tên | Status / Trạng thái | Report / Báo cáo |
|---------|-----------|---------------------|-------------------|
| B1 | Dead Code Scrub / Loại bỏ code chết | done | `reports/ceo-handover-status-report.md` §2.2 |
| B2 | Usage Tracker Merge / Gộp usage tracker | done | `reports/ceo-handover-status-report.md` §2.2 |
| B3 | NLU Unification / Thống nhất NLU | done | `reports/ceo-handover-status-report.md` §2.2 |
| B4 | Memory Bridge / Cầu nối bộ nhớ | **done** | `reports/completion-260706-1021-phase-b4-closeout-report.md` |
| B5 | PEV Parser Real / Parser PEV thật | scaffolded | `reports/kickoff-260706-1021-phase-b5-pev-parser-real.md` |
| B6 | Agent Factory / Nhà máy agent | done | `reports/ceo-handover-status-report.md` §2.2 |
| B7 | Integration + Validation / Tích hợp + xác thực | ~95% | `reports/ceo-handover-status-report.md` §2.2 |

---

## Architecture Changes

**Layer impact:** All waves touch `src/` layers with import-path changes.

| Layer | Touched by | Change |
|-------|-----------|--------|
| seed | B2, B4, B6 | Usage import canonicalized; MemoryBridge lazy-imported; agents wired through factory |
| tree | B2, B3 | Usage tracker consumers updated; NLU delegates to `classify_intent()` |
| forest | B4, B5, B7 | MemoryBridge adapters; PEV pipeline wired end-to-end |
| land | No direct change | Receives clean public contracts |

**New import pattern (B2 + B6):**

```python
from src.usage import track_usage     # B2: single entry point
from src.agents.factory import AgentFactory  # B6: config-driven
factory = AgentFactory("config/agents.yaml")
ceo = factory.create("ceo", llm=llm, memory=memory)
```

**MemoryBridge protocol (B4):** 8 methods across 4 backends (`seed`, `memory`, `scoped`, `pev`). All lazy-imported via `get_bridge()` factory.

---

## Protected Flows Status

| Flow | Status | Note |
|------|--------|------|
| Setup Wizard (BYOK) | green | No changes this phase |
| Telegram Bot | green | No changes this phase |
| Payment (NOWPayments) | green | No changes this phase |

---

## Testing

| Suite | Result | Source |
|-------|--------|--------|
| B4 memory bridge integration | 72/72 pass | `tests/core/test_memory_bridge_integration.py` |
| B4 memory tests | 16/16 pass | `tests/test_memory.py` |
| B7 PEV pipeline | 23/23 pass | `test_pev_23/23` |
| B7 pipeline manager | 29/29 pass | `test_pipeline_manager 29/29` |
| B6 Agent Factory | 23/23 pass | Per handover report |
| Ruff lint (post-B1) | 0 errors target | 313 errors existed before Phase A cleanup |
| Full suite | Partial | Legacy module collection errors remain (outside Phase B scope) |

---

## Key Decisions / QUYẾT ĐỊNH CHÍNH

1. **B4 risk accepted:** 7 memory modules unified via protocol — backward compat preserved, no breaking changes.
2. **B5 recipe format:** Standard Markdown with YAML frontmatter + `## Steps` sections.
3. **B6 config-driven:** Agent roles, prompts, and capabilities live in YAML, not code.
4. **Payment provider:** NOWPayments primary; Polar.sh and PayPal banned per CLAUDE.md.

---

## Next Steps / BƯỚC TIẾP THEO

- **Phase C Revenue** (`plans/260706-1243-phase-c-revenue/`) — Stripe webhook idempotency, 14-day trial system, HubSpot CRM sync, VietQR payment
- B1 residual: verify no remaining `src/zenpay/` imports after 12-file scrub
- Full suite green: resolve legacy module collection errors (snake_modules)

---

*Tài liệu này được tạo bởi docs-manager trong khi Phase B implementation chạy song song.*
