# Deprecation Map

## Candidates for Deprecation

### 1. Basic MemoryStore (src/core/memory.py)

**Status:** WRAPPED (2026-08-20)

**Current:** `memory.py` is a 4-line backward-compat shim re-exporting from
`memory_canonical.py`. The real implementation lives in `memory_canonical.py`
(396 lines). 4 live importers remain (`autonomous.py`, `learner.py`,
`recipe_gen.py`, `smart_router.py`) — all use the shim, not the old dict store.

**Why:** The original `MemoryStore` dict-backed store was migrated wholesale into
`memory_canonical.py` during Phase 7-8 consolidation. The shim preserves import
compatibility.

**Migration path:** None needed. Shim is the stable public surface.

**Risk:** LOW — Already executed; shim verified by 4 importers.

---

### 2. Direct LLM Client Calls (src/core/llm_client.py)

**Status:** WRAPPED (2026-08-21)

**Current:** `LLMRouterAdapter` now delegates to `LLMClient` for all generation
methods (`generate`, `stream`, `structured_output`). `LLMClient` retains its
real production logic (provider failover, caching, hooks, circuit breaker) and
its public API is unchanged. 32 caller files continue to use `LLMClient`
directly — they are not yet migrated to the Protocol interface.

**Why WRAPPED, not DONE:** Adapter now wraps `LLMClient` behind `LLMRouter`
Protocol, but the 32 existing caller files still import `LLMClient` directly.
Full migration of callers to the Protocol is a future task.

**Migration path:** Future — migrate remaining callers from `LLMClient` direct
imports to `LLMRouter` Protocol via `LLMRouterAdapter`. Adapter is ready;
callers are the remaining work.

**Risk:** LOW — Adapter wrapping is live; caller migration deferred.

---

### 3. Dict-Based Prompt Storage (DEFAULT_PROMPTS in agent_dispatcher.py)

**Status:** DEFERRED (2026-08-20)

**Current:** `DEFAULT_PROMPTS` lives in `src/core/agent_dispatcher.py` (not
`commands_registry.py` as the original map assumed). 4 live importers
(`agent_registry.py`, `agent_dispatcher.py`, `test_water_protocol.py`,
`test_agent_dispatcher.py`). `.mekong/agents/` is empty/nonexistent.

**Why:** No markdown source exists to auto-generate prompts from. The dict is
the only prompt source. Build-time generation is not possible without first
creating the markdown files.

**Migration path:** Create `.mekong/agents/*.md` as the single source of truth,
then auto-generate `DEFAULT_PROMPTS` at build time. Deferred — no markdown
source exists yet.

**Risk:** LOW — Deferred until markdown prompt files exist.

---

### 4. Duplicate NOWPayments Module (nowpayments-checkout.py)

**Status:** DONE (2026-08-20)

**Current:** Both `nowpayments_checkout.py` and `nowpayments-checkout.py` existed.

**Action:** Deleted `nowpayments-checkout.py` and `nowpayments-webhook-handler.py`
(hyphen versions). Verified byte-identical to underscore versions via `diff`/`md5`.
Production code (`nowpayments_router.py`) imported the underscore versions.
Tests (`test_billing.py`) loaded hyphenated files via `importlib` — updated to
load the canonical underscore versions instead.

**Risk:** LOW — Verified no production imports of hyphenated files.

---

### 5. Legacy Billing Routes (vn_pilot_billing.py, vn_payments_routes.py)

**Status:** DEFERRED — MEDIUM RISK (2026-08-20)

**Current:** Four billing route modules with overlapping responsibilities:
`billing_routes.py`, `raas_billing_service.py`, `vn_pilot_billing.py`,
`vn_payments_routes.py`. All four are live with distinct importers.

**Why:** Each module serves a different consumer (general API, RaaS service,
VN pilot, VN payments). Merging requires reviewing each module's specific
requirements before consolidation.

**Migration path:** Merge `vn_pilot_billing.py` + `vn_payments_routes.py` into
`billing_routes.py`. Update imports. Deferred — requires dedicated review.

**Risk:** MEDIUM — VN pilot and payments routes may have specific requirements.

---

### 6. Governance Binary Classification

**Status:** DONE (2026-08-20)

**Current:** `Governance` already has `ActionClass` enum (SAFE/REVIEW_REQUIRED/
FORBIDDEN) in `src/core/governance.py:28`. `GovernanceDecision` dataclass
carries `action_class`, `reason`, `requires_approval`, `approved`.
`autonomous.py` and `runtime_adapter.py` both gate on
`decision.action_class`.

**Why:** The risk-level system was already implemented. The binary
SAFE/FORBIDDEN classification was extended with `REVIEW_REQUIRED` as a
third class — no further migration needed.

**Risk:** LOW — Already implemented; backward compatibility preserved.

---

### 7. AgentDispatcher Protocol (duplicate definition)

**Status:** DONE (2026-08-20)

**Current:** `AgentDispatcher` Protocol defined in `protocols.py`. `AgentRegistry` has similar dispatch methods.

**Action:** Removed `AgentDispatcher` Protocol entirely (0 importers). The
`AgentRegistry` class already provides `get()`, `list_agents()`, `discover()`,
and `get_meta()` — the canonical dispatch surface. `build_message_chain()` and
`load_agent_prompt()` live in `src/core/agent_dispatcher.py` as standalone
functions. Updated `test_protocol_compliance.py` (9 → 8 protocols) and
`hybrid_router.py` comment to reference `AgentRegistry`.

**Risk:** LOW — Protocol had 0 importers; removal is safe.

---

## Not Deprecated (Keep As-Is)

| Component | Reason |
|-----------|--------|
| `src/core/memory_client.py` | NeuralMemoryClient may have unique vector features |
| `src/strategies/polymarket/` | Separate domain, not conflicting |
| `src/studio/` | Video studio is a product vertical |
| `src/forest/` | Inngest infrastructure is external dependency |
| `src/commands/` | Canonical Click command registry (43 commands); `commands_registry.py` is the aggregator |
| `src/db/tier_config_repository.py` | Rate-limiting config (DB-backed), distinct from `tiers.py` pricing/credits |
| `src/core/llm_client.py` | Real production LLM client with failover/caching; wrap behind adapter, do not replace |