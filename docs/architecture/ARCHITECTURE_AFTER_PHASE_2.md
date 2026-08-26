# Architecture After Phase 2 — Autonomous Runtime v0.1

> Refreshed: 2026-08-26 · Base: `d6138541a` (Wave 3) · Code HEAD: `ada77e6b41`
> Branch `feat/autonomous-runtime-v01` — 9 commits, 33 files changed,
> **+4,783 / −918 lines** (`git diff --stat d6138541a...ada77e6b41`).
> This report stops at the §23 stop condition: foundation shipped, human
> architect review required before any Phase 3 work.

## 1. Before / After

| Area | Before (at `d6138541a`) | After (v0.1) |
|------|------------------------|--------------|
| Mission trace | Plain `run()` never started a mission → `mission_id=None`, truncated traces | `run()` starts mission idempotently; payload path keeps pre-assigned ids; full start/step/finish traces |
| Lifecycle docs | None | Pinned contract: 10 stages ↔ methods, tested by `tests/test_core_lifecycle_contract.py` |
| Capability bus | Defined but 0 production importers | Injected into `mekong run` by default (11 builtin capabilities), failure-tolerant |
| Policy decisions | 3-class governance, silent `GOVERNANCE_AUTO_APPROVE` bypass | Single decision path: 4-level risk map, audit on every decision, loud WARNING bypass, CRITICAL+AUTO registration rejected |
| Payments | `PaymentProvider` had 0 conformant implementations; settle stub | Protocol extended (quote/request/verify/refund); `BillingAdapter` conforms; deterministic idempotent mock; x402-shape pure-data codec |
| Buzz | `send_update` built dicts, posted nothing | Injectable `(url,payload)->int` transport (stdlib urllib), no-op without callback; versioned `BuzzRuntimeAdapter` v0.1 with cooperative cancel |
| Execution isolation | No abstraction | `ExecutionRuntime` Protocol + `LocalExecutionRuntime` (sanitizer-gated shell, confined filesystem, timeouts, cancel) |
| Duplication | PEV planner byte-identical to core planner (691 lines) | Deleted; importers repointed; convergence pinned by tests |
| CLI self-description | CLAUDE.md cited phantom layers (tree/forest/land) + "43 commands" | Accurate layer map, build_app-derived 36 groups |

## 2. Commit ledger

```
37c1b39121 fix(repo): track cli build command sources swallowed by build/ gitignore rule
0cbac9d1c3 feat(core): canonical lifecycle trace + core boundary gate
3ee7a8435f feat(core): wire capability bus into production runtime
d6332b6ce8 test(core): make capability adapter fixtures hermetic
71c79637c0 feat(core): single canonical policy decision path (risk-aware governance)
c16c5bc87f feat(core): economic bus — payment provider interface + mock/x402-shape providers
640d82d87d feat(adapters): buzz transport + versioned runtime adapter interface
33ec5b69b0 feat(core): local-first execution runtime primitive
ada77e6b41 refactor(harness): remove byte-identical PEV planner duplicate
```

## 3. Files changed

**Added** — core/adapters: `tool_capability_adapter.py` (+161),
`payment_mock.py` (+262), `payment_x402_shape.py` (+193),
`buzz_runtime_adapter.py` (+234), `exec_runtime/{__init__,types,local}.py`
(+416); repo: `.gitignore` fix + tracked `src/cli/commands/build/` sources;
docs: `core-contract.md`, `architecture/DEPRECATION.md`.

**Added** — tests (10 files): `test_core_lifecycle_contract.py` (15),
`test_core_boundary.py` (5), `test_tool_capability_adapter.py` (20),
`test_policy_decision_path.py` (26),
`test_agent_registry_consolidated.py` (+10),
`tests/test_payment_providers.py` (28), `test_economic_bus.py` (extended),
`test_buzz_transport.py` (35), `test_local_execution_runtime.py` (38),
`test_pev_planner_converged.py` (4), `test_repo_hygiene.py`.

**Deprecated/removed** — `src/harness/pev/planner.py` deleted (byte-identical
duplicate, cmp-verified before removal); see
[DEPRECATION.md](./DEPRECATION.md).

**Modified** — `runtime_adapter.py` (+79 net incl. cancel hook),
`governance.py` (risk-aware rewrite), `protocols.py` (+60),
`billing_adapter.py`, `buzz_adapter.py`, `agent_registry.py`,
`commands/run.py` (bus injection), `harness/pev/{__init__,orchestrator}.py`
(repoint).

## 4. Dependency graph (text)

```
 mekong run (src/commands/run.py)
   └─▶ MekongCoreRuntimeImpl (src/core/runtime_adapter.py)
         ├─ stages: goal→plan→delegate→execute→observe→verify→repair→remember→commit
         ├─ execute() gates: Governance.classify_risk ▶ cost ceiling ▶ dispatch
         ├─▶ InMemoryCapabilityBus ◀── ToolCapabilityAdapter ◀── ToolRegistry
         │                         └── McpCapabilityAdapter ◀── FastMCP server
         ├─▶ Governance (audit trail)          [ONE decision path]
         ├─▶ MemorySeparation / memory stores   [remember stage]
         └─▶ BillingAdapter ─▶ MCUBilling       [commit stage]

 BuzzRuntimeAdapter ─▶ MekongCoreRuntimeImpl.run_from_payload (same loop)
   └─▶ BuzzAdapter.send_update ─▶ injectable transport (urllib POST)

 LocalExecutionRuntime ┐
 (future CF/Docker)    ┴─ satisfy ExecutionRuntime Protocol (exec_runtime)

 PaymentProvider ◀── BillingAdapter | MockPaymentProvider | x402-shape codec
 LLMRouter ◀── llm_router_adapter ─▶ llm_client (requests→OpenRouter) [*transitional*]
```

## 5. Key flows

**MCP:** external FastMCP server → `sync_from_mcp()` → capabilities tagged
`source=MCP` on the bus → e2e test executes `mcp:*` through the same bus +
governance path as builtins. Client-side MCP consumption deferred.

**Buzz:** payload `{goal|text, mission_id?, callback_url?}` → session/mission
assignment → core loop under tracer → outcome {completed, cancelled, failed}
POSTed via transport when callback present; approval requests deny-by-default.

**Payment:** `quote(amount,currency,recipient,scheme)` →
`request_payment(PaymentRequest w/ idempotency_key)` → `PaymentReceipt` →
`verify(receipt)` → `refund`. Mock replays return identical receipts and
settle exactly once. Real settlement does not exist in v0.1.

## 6. Security boundaries (enforced)

1. **Vendor-SDK gate** — no anthropic/openai imports anywhere in
   `src/core/`; HTTP-lib allowlist enumerated exactly
   (`tests/test_core_boundary.py`).
2. **Shell sanitizer** — string commands pass
   `CommandSanitizer(strict_mode=True)`; injection patterns blocked
   (tested: `rm -rf /`, chaining, backticks).
3. **Filesystem confinement** — resolve-then-verify inside sandbox root,
   symlink-aware; traversal escapes raise.
4. **Governance deny + always-audit** — CRITICAL denied unconditionally;
   every decision writes an audit entry; bypass is loud.
5. **No custody** — economic code holds no keys/wallets/network; x402
   decode rejects key-like fields; negative tests assert receipts/logs stay
   secret-free.
6. **Protected paths untouched** — `src/gateway.py`, `src/raas/nowpayments_*`,
   `src/api/billing_routes.py`, `src/middleware/license_gate.py`,
   `src/lib/raas_gate/` all byte-unchanged (diff grep empty).
7. **No new dependencies** — transports use stdlib urllib.

## 7. Test coverage

Suite at code HEAD (E6 parity run): **277 failed / 7,650 passed /
75 skipped** with `--ignore=tests/test_world_model.py` (known hang, escrowed);
normalized fail-set diff vs base baseline = **exact match, 0 new failures**.
~181 new tests across 9 new suites + extensions (ledger in §3). The 277
failures are the pre-existing baseline carried from Wave 3 — not caused by
this branch, but they cap the honesty of any "green" claim.

## 8. Gaps (deferred by design — stop condition)

1. Real multi-step `plan()`; multi-agent `delegate()` (both stubs).
2. GoalEngine protocol conformance (`src/mekongcli` engine stays live).
3. MemoryStore convergence — 0 conformant implementations, 3-way split.
4. Harness verifier merge + DAG scheduler swap.
5. MCP client-side consumption of external servers.
6. Real x402/MPP settlement, marketplace, tokenomics, custody.
7. New CLI surface (mk mission/agent/run/approve/…).
8. Full sandbox/App Factory beyond the `ExecutionRuntime` primitive.
9. Tier-config duality; 4 payment route families; COMMAND_REGISTRY rewrite;
   funnel restoration (Zalo/tax/vn-setup).
10. MOVE `llm_client.py` out of core/ (46 file references).
11. Carried over: `LLMRouter.tool_call()` missing (no v0.1 lane); native
    streaming absent; world_model hang unfixed; NetworkPolicy placeholder.

## 9. Debt register

- `GOVERNANCE_AUTO_APPROVE` remains an env var — fine for solo ops, wrong
  for multi-tenant.
- Unknown risk levels fail open to SAFE (documented, deliberate).
- Audit sink failure-tolerant to memory only — no durable queue.
- `InMemoryCapabilityBus` — no persistence or cross-process sharing.
- Baseline suite redness (277) masks regressions in covered areas; parity
  discipline compensates but is manual.
- Docs outside this set (roadmap, COMMAND_REGISTRY, several architecture/
  maps) still describe pre-Wave-3 reality.

## 10. Scores — 10 dimensions (/100, brutally honest)

| Dimension | Score | Justification |
|-----------|------:|---------------|
| Architecture | **72** | One lifecycle, four buses, enforced boundaries; dragged down by stub planner/delegate and memory split |
| Autonomy | **55** | Risk map + audit + declarative agents exist; approvals are env-var only, unknown-risk fails open, no human-in-loop surface |
| Prod-readiness | **40** | Mock-only payments, unenforced network policy, 277 baseline failures, single-node bus |
| Provider-neutrality | **80** | Test-enforced SDK gate with exact allowlist; one transitional HTTP module left in core |
| Capability coverage | **60** | Builtins + MCP wired end-to-end; no persistence, no authz model beyond risk level, aliases inflate counts |
| Policy coherence | **78** | Genuinely one decision path, audited; fail-open default and env bypass are honest scars |
| Economic-readiness | **45** | Interface + idempotent mock + shape codec are solid scaffolding; zero real settlement, NOWPayments migration untouched |
| Buzz-readiness | **65** | Versioned facade, injectable transport, cooperative cancel; in-process only, no auth/retry/backoff |
| Docs completeness | **70** | Full v0.1 set now accurate and link-checked; legacy docs stale |
| Test depth | **68** | 181 targeted contract/gate/negative tests; overall suite still carries a red baseline |
| **Average** | **63** | Honest v0.1: correct skeleton, intentionally shallow flesh |

## 11. Top 10 next actions

Ordered by leverage; each names the dimension(s) it moves most.

1. **Real multi-step `plan()` via GoalEngine conformance** (arch +5, autonomy +8) — biggest single unlock; effort L.
2. **Multi-agent `delegate()`** (autonomy +8, arch +4) — depends on #1; needs registry-driven dispatch tests.
3. **Conformant MemoryStore + convergence** (arch +6, prod +4) — removes the oldest structural lie; ~20 consumers to migrate carefully.
4. **Merge harness verifier into protocols.VerificationEngine; swap DAG scheduler stub** (arch +5, test +3) — behavior-changing, needs its own lane.
5. **NOWPayments → PaymentProvider remount behind a reviewed flag** (econ +20) — protected-flow lane with replay tests; do NOT rush.
6. **Real x402 settlement provider** (econ +10, prod +5) — only after #5 proves the adapter pattern on live rails.
7. **Enforced NetworkPolicy in exec runtime** (prod +8, security posture) — replace deny-all placeholder struct with real enforcement.
8. **Human approval surface for REVIEW_REQUIRED** (autonomy +12) — CLI/UI approval inbox replacing GOVERNANCE_AUTO_APPROVE for HIGH risk.
9. **MCP client-side consumption** (capability +8) — makes the runtime a first-class MCP citizen.
10. **CLI primitives (mk mission/agent/run/approve/…) + COMMAND_REGISTRY regeneration** (docs +8, dev-experience) — after contracts stabilize.

**STOP here per §23.** Human architect review required before Phase 3.
