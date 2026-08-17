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

**Current:** Both `nowpayments_checkout.py` and `nowpayments-checkout.py` exist.

**Replace with:** Delete `nowpayments-checkout.py` (hyphen version).

**Why:** Likely a stale copy from a rename. Underscore is the codebase convention.

**Migration path:** `grep -rn "nowpayments-checkout" src/` — if no imports, delete.

**Risk:** LOW — Only delete if no imports found.

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

**Current:** `AgentDispatcher` Protocol defined in `protocols.py`. `AgentRegistry` has similar dispatch methods.

**Replace with:** `AgentRegistry` implements `AgentDispatcher` Protocol.

**Why:** Single dispatch system. `AgentRegistry` already has `get()` + prompt loading.

**Migration path:** Add `dispatch()` and `build_message_chain()` to `AgentRegistry`. Remove standalone `AgentDispatcher` Protocol.

**Risk:** LOW — Protocol is structural typing; implementations are already compatible.

---

## Not Deprecated (Keep As-Is)

| Component | Reason |
|-----------|--------|
| `src/core/memory_client.py` | NeuralMemoryClient may have unique vector features |
| `src/strategies/polymarket/` | Separate domain, not conflicting |
| `src/studio/` | Video studio is a product vertical |
| `src/forest/` | Inngest infrastructure is external dependency |