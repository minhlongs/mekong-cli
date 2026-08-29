---
title: "Super Command #5 — Economic Bus + Capability Bus + Agent Registry"
description: "Clean core/adapter boundary, canonical LLM port, single-source agent registry, capability bus, MCP bridge, x402+MPP payment abstraction, Buzz + Cloudflare adapters, agent-loop E2E"
status: complete
priority: P1
effort: 18h
branch: feat/sc5-economic-capability-buses
tags: [runtime, capability-bus, economic-bus, adapters, registry]
created: 2026-08-29
---

# Super Command #5 — Plan

## 1. Reframed Problem

Runtime v0.3 (PR #10, 7c5f64093) closed the SC#4 gap list but the
core still lacks the three-bus target architecture (Autonomous Runtime +
Capability Bus + Economic Bus). SC#5 builds the smallest correct foundation:
a clean CORE/ADAPTERS boundary, one canonical LLM provider port, a
single-source agent registry (YAML truth), the capability bus with the MCP
bridge, a scheme-agnostic payment abstraction (x402 + MPP, neither
hard-coded), the Buzz and Cloudflare adapters behind protocols, and a
hermetic agent-loop E2E. Hard constraints: no vendor hard-coding, no
marketplace/tokenomics/custody, protected flows untouched,
`.github/workflows/*` untouched, parity 0 new failures.

## 2. Work Checklist

### Wave A — core boundary + ports

- [x] **A1 CORE/ADAPTERS boundary (T1)** — create `src/core/ports/` (pure
  protocols: LLM, runtime, payment) importing NOTHING from adapters.
  Boundary test `tests/test_core_boundary.py` pins it. `src/core/` imports no
  vendor SDK at module level. Agent: fullstack-developer. Acceptance: boundary
  test green; `grep -rn "anthropic\|cloudflare\|openai" src/core/ports/` = 0.
- [x] **A2 Canonical LLM port (T2)** — `src/core/ports/llm.py` defines
  generate/stream/structured_output/tool_call/health. Four thin preset
  adapters (claude/qwen/deepseek/local) under `src/core/adapters/llm/`
  subclass ONE base (no duplication). Two providers prove interface
  satisfaction in tests. Agent: fullstack-developer. Acceptance: 2 providers
  pass same conformance test.
- [x] **A3 Agent registry single-source (T3)** — `src/core/registry/`
  with `agents.yaml` as source of truth, `loader.py` (declarative),
  `dynamic.py` (Python-class discovery adapter). Agent attrs: id/name/role/
  description/capabilities/allowed_tools/risk_level/model_preference/
  max_budget/max_iterations/approval_policy. Acceptance: registry tests green;
  no duplicate agent definitions.
- [x] **A4 Capability bus (T4)** — `src/core/capability.py` (Capability,
  CapabilityBus, CapabilitySource). Every capability carries id/description/
  input_schema/output_schema/risk_level/cost/authorization/execute.
  Agents request `capability.execute(...)`. No marketplace. Acceptance:
  bus tests green; MCP tools registered under `mcp:<name>`.
- [x] **A5 MCP adapter bridge (T5)** — `src/core/adapters/
  mcp_capability_adapter.py` wraps MekongMcpServer tools as Capabilities
  (`mcp:cc_<tool>`), handler delegation strips `cc_` prefix. Acceptance:
  integration test green against the existing in-repo MCP server.
- [x] **A6 Payment abstraction (T6)** — `src/core/adapters/payment/`
  with `PaymentProvider` protocol, `X402SettlementProvider` (canonical) +
  `MPPSettlementProvider` (same 7-method shape). Fail-closed config
  (`X402ConfigError`/`MPPConfigError` on missing — never default-allow).
  Governance-gated settle/request/refund; denial fails closed before
  transport. No custody, no autonomous transactions, scheme not hard-coded.
  Acceptance: both providers pass the same conformance test suite.
- [x] **A7 Buzz adapter (T7)** — `buzz_adapter.py` /
  `buzz_runtime_adapter.py` with fail-loud `BuzzConfigError` at call time
  (never import time), hermetic-by-injection transport. Acceptance: tests
  green with zero-credential runs.
- [x] **A8 Cloudflare adapter isolation (T8)** —
  `src/core/adapters/cloudflare/adapter.py` with
  `CloudflareTransport(Protocol)` `.dispatch(payload) -> dict`. This is the
  SINGLE import site binding core to CF runtime. Acceptance: boundary test
  proves core never imports CF SDK directly.

### Wave B — E2E proof

- [x] **B1 Agent-loop E2E (T9)** — `tests/test_cook_e2e_lifecycle.py`:
  hermetic E2E of the canonical lifecycle via `mekong cook` (tmp_path
  isolation). Proves stage chain goal→plan→delegate→observe→verify→repair→
  remember→commit, telemetry sink with mission_id, billing attempt, repair
  loop ≤3 retries, governance block (forbidden + review-required), dry-run
  plan-only. Acceptance: 6/6 green.

### Wave C — quality gates

- [x] **C1 ruff + pyright + parity** — `ruff check src/ tests/` clean;
  `pyright src/ --pythonversion 3.12` shows ZERO new errors vs baseline
  (4 pre-existing pev_adapter errors remain); pytest parity
  `comm -13 failset_baseline.txt <new>` EMPTY. Acceptance: all three gates
  green in the same run.

## 3. Risks & Gates

| Risk | Mitigation |
|------|------------|
| Payment abstraction drifts into custody/marketplace | Protocol caps at quote/request_payment/verify/refund/usage/check_quota; no wallet, no keys, §18 forbidden-fields check on decode |
| Two LLM adapters duplicate 80% logic | One `ConfigurableLLMAdapter` base + ≤30 LOC preset subclasses |
| Registry YAML drifts from Python truth | YAML is truth; `dynamic.py` only discovers classes; loader merges both; test pins equality |
| Monkey-patched `Capability.execute` confuses type checkers | `setattr()` used at both adapter sites (pyright-clean) |
| MPP mixin false-positives in pyright | Mixin folded into single self-contained class (canonical x402 pattern) |
| Boundary creep (core importing adapters) | `tests/test_core_boundary.py` + grep gate |

## 4. Ship Plan

Pre-deploy checklist (git clean, ruff, pyright, pytest parity) → commit →
push `feat/sc5-economic-capability-buses` → `gh pr create` → CI verify
(`gh run list -L 5` poll, max 5 min) → merge `--squash --delete-branch` →
deploy (CF per repo doctrine) → prod smoke → feature smoke → rollback
readiness → ops/journal. `ship-report.md` records every step.

## 5. Status

ALL TASKS COMPLETE. See `execution.md` for evidence per task.
