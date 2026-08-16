# OmniRoute Architecture Patterns for Mekong CLI

## Executive Summary

OmniRoute is a **local-first LLM gateway** with a **chain-of-responsibility combo router** (19 strategies), **12-engine compression pipeline**, **MCP/A2A plugin surface**, and **zero-config strategy defaults**. Mekong CLI is a **Vietnam-focused AI business platform** (billing, tax, Zalo OA, AI video) with **43 Typer commands**, **PEV constitutional engine**, **MCU billing**, and **license-gated middleware**.

This report extracts **concrete code patterns** (not philosophy) from OmniRoute applicable to Mekong's Tier Fallback Chain, Provider Registry, Middleware, and Testing infrastructure.

---

## Relevant Files

### OmniRoute Source Patterns
- `src/domain/fallbackPolicy.ts` — Declarative fallback chain with priority ordering, SQLite persistence, in-memory cache
- `src/domain/policyEngine.ts` — Centralized policy evaluation combining fallback, cost, lockout, circuit-breaker
- `src/domain/lockoutPolicy.ts` — Account lockout logic with failure tracking, exponential backoff, SQLite persistence
- `src/domain/costRules.ts` — Budget thresholds, scheduled resets, cost summaries per API key
- `src/domain/degradation.ts` — Hierarchical degradation: Full → Reduced → Minimal → Safe Default
- `src/domain/quotaCache.ts` — In-memory quota cache per connectionId with background refresh
- `src/domain/tagRouter.ts` — Metadata-driven routing with tag matching (any/all modes)
- `src/lib/db/domainState.ts` — SQLite persistence for all domain state (fallback, budgets, lockout, circuit breakers)
- `src/server/authz/pipeline.ts` — Middleware pipeline: classify → peer-stamp → auth → quota → CORS → route
- `src/proxy.ts` — Next.js middleware matcher for API route protection
- `src/shared/resilience/peerRouting.ts` — Multi-instance peer routing with loop detection
- `src/shared/contracts/quota.ts` — Shared TypeScript contracts for quota responses

### OmniRoute Test Patterns
- `tests/unit/8247-accountfallback-model-unhealthy.test.ts` — Per-model vs connection-wide quota classification
- `tests/unit/8248-accountfallback-nvidia-degraded.test.ts` — Provider-specific error classification (DEGRADED state)
- `tests/unit/8370-priority-affinity-reorder.test.ts` — Regression guard for priority combo ordering
- `tests/unit/8332-combo-vision-fallback.test.ts` — Vision model fallback behavior
- `tests/unit/combo-routing-engine.test.ts` — Full routing engine integration tests

### Mekong CLI Current State
- `src/core/tier_fallback_chain.py` — Tier-balanced fallback (BASIC/PREMIUM/ENTERPRISE/MASTER)
- `src/core/provider_registry.py` — Multi-provider registry with RoutingStrategy ABC
- `src/core/circuit_breaker.py` — Circuit breaker with CLOSED/OPEN/HALF_OPEN states
- `src/core/fallback_chain.py` — ALGO 7 fallback with sensitivity gating
- `src/api/raas_billing_middleware.py` — MCU quota check + credit balance enforcement
- `src/api/raas_auth_middleware.py` — JWT Bearer auth with mk_ prefix keys
- `src/seed/config/tiers.py` — Unified tier config with backward-compatible aliases
- `tests/core/test_tier_fallback_chain.py` — Unit tests for tier fallback chain
- `tests/core/test_provider_registry.py` — Provider registry tests

---

## Patterns

### 1. Tier/Fallback Chain Implementation

**OmniRoute Pattern** (`fallbackPolicy.ts`):
```typescript
// Declarative fallback chain per model, persisted in SQLite
export function registerFallbackChain(model: string, chain: FallbackEntry[]) {
  ensureLoaded();
  const sorted = [...chain]
    .map(e => ({ provider: e.provider, priority: e.priority ?? 0, enabled: e.enabled ?? true }))
    .sort((a, b) => a.priority - b.priority);
  fallbackChains.set(model, sorted);
  saveFallbackChain(model, sorted);
}

export function resolveFallbackChain(model: string, excludeProviders = []) {
  const chain = fallbackChains.get(model);
  if (!chain) return [];
  const excludeSet = new Set(excludeProviders);
  return chain.filter(e => e.enabled && !excludeSet.has(e.provider));
}
```

**Mekong Current** (`tier_fallback_chain.py`):
```python
# Tier-based chain (not model-based), hardcoded in resolve_tier_chain()
def resolve_tier_chain(tier: str) -> TierFallbackChain:
    if tier == "BASIC":
        return TierFallbackChain(
            tier=tier,
            primary=FallbackCandidate(tier=tier, provider="openai", model="gpt-4o-mini"),
            fallbacks=(FallbackCandidate(tier=tier, provider="gemini", model="gemini-1.5-flash"),),
        )
    # ... PREMIUM, ENTERPRISE, MASTER
```

**Applicable Pattern**: Move from **hardcoded tier chains** to **declarative model-level chains persisted in SQLite**. This enables:
- Per-model fallback (not just per-tier)
- Runtime registration via admin API
- Excluding already-tried providers via `excludeProviders`
- Priority-based ordering (lower = higher priority)

### 2. Multi-Provider Routing Architecture

**OmniRoute Pattern** (`policyEngine.ts`):
```typescript
export interface PolicyRequest {
  model: string;
  provider?: string;
  connectionId?: string;
  estimatedInputTokens?: number;
  estimatedCostUsd?: number;
  tier?: "free" | "basic" | "premium" | "enterprise";
}

export function evaluatePolicies(req: PolicyRequest): PolicyResult {
  const result: PolicyResult = { allowed: true, appliedPolicies: [] };
  
  // 1. Lockout check (fail-fast)
  if (req.connectionId) {
    const lockout = checkLockout(req.connectionId, req.provider);
    if (lockout.locked) {
      result.allowed = false;
      result.reason = "account_locked";
      return result;
    }
  }
  
  // 2. Budget check
  const budget = checkBudget(req.provider, req.estimatedCostUsd);
  if (!budget.allowed) {
    result.allowed = false;
    result.reason = "budget_exceeded";
    return result;
  }
  
  // 3. Fallback chain resolution
  const fallbackChain = resolveFallbackChain(req.model, req.provider ? [req.provider] : []);
  if (fallbackChain.length > 0) {
    result.fallbackProviders = fallbackChain.map(f => f.provider);
  }
  
  return result;
}
```

**Mekong Current**: Billing check in middleware (`raas_billing_middleware.py`), provider selection in `provider_registry.py`, but **no unified policy engine** combining lockout + budget + fallback.

**Applicable Pattern**: Create **unified policy evaluation** before LLM call:
1. Check account lockout (per provider + model)
2. Check MCU budget / tier limits
3. Resolve fallback chain excluding failed providers
4. Return structured `PolicyResult` with `allowed`, `fallbackProviders`, `maxTokens`, `reason`

### 3. Middleware Enforcement Patterns

**OmniRoute Pattern** (`server/authz/pipeline.ts`):
```typescript
export async function runAuthzPipeline(request: NextRequest, opts) {
  // 1. Classify route (chat, models, dashboard, etc.)
  const classification = classifyRoute(request);
  
  // 2. Peer stamp for multi-instance routing
  const peerResult = await resolveStampedPeer(request, env);
  
  // 3. Auth (JWT, API key, dashboard session)
  const authResult = await runAuthPipeline(request, classification);
  
  // 4. Quota check
  const quotaResult = await checkQuota(authResult.subject, classification);
  if (!quotaResult.allowed) {
    return rejectionResponse(quotaResult.reason, 429);
  }
  
  // 5. CORS headers
  applyCorsHeaders(response, request);
  
  // 6. Set decision headers
  response.headers.set("X-OmniRoute-Decision", decision);
  response.headers.set("X-OmniRoute-Route-Class", classification.routeClass);
  
  return response;
}
```

**Mekong Current**: Separate middlewares (`raas_auth_middleware.py`, `raas_billing_middleware.py`, `license_gate.py`) but **no unified pipeline** with decision headers.

**Applicable Pattern**: Build **single authz pipeline** with:
- Route classification (task, agent, streaming, admin)
- Decision headers (`X-Mekong-Decision`, `X-Mekong-Tier`, `X-Mekong-Fallback`)
- Fail-closed quota enforcement
- Peer routing for multi-instance (future)

### 4. Configuration & Environment Patterns

**OmniRoute Pattern** (`.env.example`):
```bash
# Required secrets (documented with generation commands)
JWT_SECRET=                    # openssl rand -base64 48
API_KEY_SECRET=               # openssl rand -hex 32
INITIAL_PASSWORD=CHANGEME

# Storage & Database
DATA_DIR=./data               # SQLite, logs, backups
DB_ENCRYPTION_KEY=            # optional, encrypt DB at rest

# Feature flags with clear defaults
ENABLE_MCP=true
ENABLE_A2A=true
ENABLE_COMPRESSION=true
COMPRESSION_ENGINES=rtk,caveman

# Provider-specific (optional, auto-discovered)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
OPENROUTER_API_KEY=

# Quota & circuit breaker tuning
QUOTA_REFRESH_INTERVAL_MS=60000
CIRCUIT_BREAKER_THRESHOLD=3
CIRCUIT_BREAKER_RECOVERY_MS=30000
```

**Mekong Current**: Uses `.env` but **no comprehensive documented `.env.example`** with generation commands and feature flags.

**Applicable Pattern**: Create **comprehensive `.env.example`** with:
- Required secrets + generation commands
- Feature flags with defaults
- Tuning parameters (circuit breaker, quota refresh)
- Clear sections: Required, Storage, Features, Providers, Tuning

### 5. Test Patterns for Multi-Provider Scenarios

**OmniRoute Pattern** (regression guards with issue numbers):
```typescript
// tests/unit/8247-accountfallback-model-unhealthy.test.ts
test("#8247: per-model-quota provider 403 insufficient_quota is NOT connection-wide creditsExhausted", () => {
  assert.equal(hasPerModelQuota("openai-compatible-cegp", "gpt-5.6-luna"), true);
  const result = checkFallbackError(403, UPSTREAM_BODY, 0, "gpt-5.6-luna", "openai-compatible-cegp");
  assert.ok(!result.creditsExhausted); // Model-scoped, not connection-wide
  assert.equal(result.shouldFallback, true);
  assert.equal(result.reason, "quota_exhausted");
});

test("#8247: non-per-model-quota provider still terminals on 403", () => {
  assert.equal(hasPerModelQuota("openai", "gpt-5.6-luna"), false);
  const result = checkFallbackError(403, UPSTREAM_BODY, 0, "gpt-5.6-luna", "openai");
  assert.equal(result.creditsExhausted, true); // Connection-wide terminal
});

// tests/unit/8248-accountfallback-nvidia-degraded.test.ts
test("#8248: nvidia NIM DEGRADED function-state 400 is fallback-worthy", () => {
  const body = 'Function id "uuid" submitted for inference is DEGRADED';
  const res = checkFallbackError(400, body, 0, null, "nvidia");
  assert.equal(res.shouldFallback, true);
  assert.equal(res.reason, "model_unhealthy");
});

test("#8248: malformed-request 400 branch still wins over DEGRADED pattern", () => {
  const res = checkFallbackError(400, "messages must alternate...", 0, null, "nvidia");
  assert.equal(res.shouldFallback, true);
  assert.equal(res.reason, "model_capacity"); // Higher priority match
});
```

**Mekong Current**: Tests exist but **no issue-numbered regression guards** for provider-specific error classification.

**Applicable Pattern**: Adopt **issue-numbered regression tests** for:
- Per-model vs connection-wide quota classification
- Provider-specific error patterns (NVIDIA DEGRADED, OpenAI 429, Anthropic overloaded)
- Priority ordering of error classifiers
- Tier-aware fallback behavior

---

## Risks

### 1. SQLite Persistence for Domain State
**OmniRoute** uses SQLite for fallback chains, budgets, lockout, circuit breakers (`domainState.ts`). **Mekong** currently uses in-memory maps (`fallback_chain.py`, `circuit_breaker.py`, `provider_registry.py`).

**Risk**: If Mekong scales to multi-instance, in-memory state will diverge. Need to adopt SQLite persistence **before** multi-instance deployment.

**Mitigation**: 
- Extract `domainState.py` from `src/core/` with same tables as OmniRoute
- Wire `tier_fallback_chain.py` to persist chains
- Wire `circuit_breaker.py` to persist state
- Add `reset_all_breakers()` for testing (already exists)

### 2. Missing Per-Model Quota Classification
**OmniRoute** distinguishes per-model quota (model-scoped) vs connection-wide quota via `hasPerModelQuota(provider, model)`. **Mekong** has no such distinction — all 429s treated equally.

**Risk**: False positives — per-model quota exhaustion triggers full provider failover instead of model-level fallback.

**Mitigation**: Add `has_per_model_quota(provider: str, model: str) -> bool` to `provider_registry.py` and use in fallback chain logic.

### 3. No Provider-Specific Error Classification
**OmniRoute** has `checkFallbackError(status, body, retryCount, model, provider)` that classifies:
- NVIDIA "DEGRADED" function state → `model_unhealthy`
- OpenAI "insufficient_quota" → `quota_exhausted` (model or connection scoped)
- Anthropic "overloaded" → `model_capacity`
- Generic 5xx → `upstream_error`

**Mekong** has generic `RateLimitError`, `ConnectionError`, `TimeoutError` only.

**Risk**: Inability to distinguish retryable vs terminal errors per provider.

**Mitigation**: Implement `classify_provider_error(status: int, body: str, provider: str, model: str) -> ErrorClassification` with provider-specific patterns.

### 4. Tier Enum Case Sensitivity
**OmniRoute** uses lowercase: `"free" | "basic" | "premium" | "enterprise"`.
**Mekong** uses uppercase: `BASIC | PREMIUM | ENTERPRISE | MASTER` (enforced in `tiers.py`).

**Risk**: Interop issues if sharing config or contracts.

**Mitigation**: Keep Mekong uppercase (matches `TIER_CONFIG` contract), document clearly. Add normalization in any shared layer.

---

## Unresolved Questions

1. **Should Mekong adopt OmniRoute's "Auto-Combo" strategy engine?**
   - OmniRoute scores 14 factors (latency, cost, quality, context window, etc.) to auto-build combo chains
   - Mekong's `tier_fallback_chain.py` is static per tier
   - **Recommendation**: Not for MVP. Add `RoutingStrategy.AUTO` to `provider_registry.py` later if needed.

2. **MCP/A2A integration scope?**
   - OmniRoute has full MCP server + A2A agent cards
   - Mekong has `src/core/mcp_server.py` stub
   - **Recommendation**: Defer to post-go-live. Current `A2A` in `src/lib/a2a/` is private.

3. **Compression pipeline (RTK + Caveman)?**
   - OmniRoute saves 15-95% tokens via 12 engines
   - Mekong has no compression
   - **Recommendation**: Optional middleware (`src/middleware/token_compression.py`) — add if token costs become bottleneck.

4. **Peer routing for multi-instance?**
   - OmniRoute uses `X-OmniRoute-Peer-Trace` header for loop detection
   - Mekong is single-instance currently
   - **Recommendation**: Add header schema now (`X-Mekong-Peer-Trace`) for future-proofing, implement later.

---

## Actionable Next Steps for Mekong

| Priority | Task | Source Pattern | Target File |
|----------|------|----------------|-------------|
| P0 | Create `src/core/domain_state.py` with SQLite persistence | `domainState.ts` | NEW |
| P0 | Add `has_per_model_quota()` to `provider_registry.py` | `accountFallback.ts` | `provider_registry.py` |
| P0 | Implement `classify_provider_error()` with provider patterns | `checkFallbackError()` | NEW `error_classifier.py` |
| P1 | Build unified `PolicyEngine` combining lockout+budget+fallback | `policyEngine.ts` | NEW `policy_engine.py` |
| P1 | Add decision headers to authz pipeline | `X-OmniRoute-Decision` | `license_gate.py` / middleware |
| P1 | Create comprehensive `.env.example` with generation commands | `.env.example` | `.env.example` |
| P2 | Add issue-numbered regression tests for error classification | `8247-*.test.ts`, `8248-*.test.ts` | `tests/core/test_error_classification.py` |
| P2 | Wire `tier_fallback_chain.py` to persist in SQLite | `fallbackPolicy.ts` | `tier_fallback_chain.py` + `domain_state.py` |
| P3 | Add `RoutingStrategy.AUTO` to `provider_registry.py` | `auto_combo.py` | `provider_registry.py` |
| P3 | Add peer routing header schema | `peerRouting.ts` | `gateway_models.py` |

---

## Anti-Patterns to Avoid

| Anti-Pattern | OmniRoute Approach | Mekong Risk |
|--------------|-------------------|-------------|
| Hardcoded fallback chains in code | Declarative, persisted, admin-editable | Current `resolve_tier_chain()` is hardcoded |
| Single global circuit breaker | Per-service breakers with registry | Current `get_circuit_breaker()` is good |
| No distinction between model/connection quota | `hasPerModelQuota(provider, model)` | Missing — all 429s treated as connection-wide |
| Generic error handling | Provider-specific classification with priority | Current `fallback_chain.py` catches broad exceptions |
| In-memory state for multi-instance | SQLite persistence for all domain state | Current in-memory maps won't survive scaling |
| No decision headers for debugging | `X-OmniRoute-Decision`, `X-OmniRoute-Route-Class` | Missing — hard to trace routing decisions |
| Tests without issue numbers | `#8247`, `#8248` regression guards | Current tests lack traceability to issues |
