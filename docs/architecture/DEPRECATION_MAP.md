# Deprecation Map

## Candidates for Deprecation

### 1. Basic MemoryStore (src/core/memory.py)

**Current:** `MemoryStore` is a basic dict-backed store with `store()`/`retrieve()`/`delete()`/`search()`.

**Replace with:** `ScopedMemoryStore` from `src/core/memory_scope.py` which adds org-scoping.

**Why:** Basic MemoryStore has no isolation, no TTL, no real search. ScopedMemoryStore is strictly better.

**Migration path:** Replace `MemoryStoreAdapter` to use `ScopedMemoryStore` instead. Update callers.

**Risk:** LOW — ScopedMemoryStore is already implemented and tested.

---

### 2. Direct LLM Client Calls (src/core/llm_client.py)

**Current:** `llm_client.py` makes direct calls to LLM APIs, bypassing the `LLMRouter` Protocol.

**Replace with:** `LLMRouterAdapter` which implements the Protocol and handles errors.

**Why:** Direct calls bypass governance, cost estimation, and provider abstraction. `LLMRouterAdapter` is the canonical entry point.

**Migration path:** Update all callers of `llm_client.py` to use `LLMRouterAdapter.generate()`.

**Risk:** MEDIUM — Some callers may rely on direct API features not in the Protocol.

---

### 3. Dict-Based Prompt Storage (DEFAULT_PROMPTS in commands_registry.py)

**Current:** `DEFAULT_PROMPTS` is a hardcoded dict of role → prompt strings.

**Replace with:** Auto-generated from `.mekong/agents/*.md` at build time.

**Why:** Prompts in code drift from markdown files. Single source of truth = markdown.

**Migration path:** Build script reads `.mekong/agents/*.md` → generates `prompts.py`. Import generated module.

**Risk:** LOW — Build-time generation is safe. Fallback to markdown at runtime if generation fails.

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

**Current:** Four billing route modules with overlapping responsibilities.

**Replace with:** Single `billing_routes.py` as canonical entry point.

**Why:** Scattered billing logic makes maintenance hard. `MCUBilling` + `raas/billing_engine.py` should be the backends.

**Migration path:** Merge `vn_pilot_billing.py` + `vn_payments_routes.py` into `billing_routes.py`. Update imports.

**Risk:** MEDIUM — VN pilot and payments routes may have specific requirements. Review before merging.

---

### 6. Governance Binary Classification

**Current:** `Governance.classify()` returns SAFE/REVIEW_REQUIRED/FORBIDDEN.

**Replace with:** Risk-level-based system (LOW/MEDIUM/HIGH/CRITICAL) + `ActionClass`.

**Why:** Binary classification is insufficient for autonomous execution. Risk levels enable automated gating.

**Migration path:** Add `ActionClass` enum (LOW/MEDIUM/HIGH/CRITICAL) to Governance. Keep backward-compatible `is_safe()` method.

**Risk:** LOW — Tests already verify risk-level behavior. Backward compatibility preserved.

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