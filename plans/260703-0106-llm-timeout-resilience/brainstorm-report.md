# Brainstorm: LLM Timeout Resilience

**Date:** 2026-07-02
**Branch:** fix/layer2-ruff-tech-debt
**Mode:** Deep + Parallel plan

---

## Problem Statement

LLM calls fail with `"Provider API request failed. Request timed out"` even after a prior per-provider timeout bump (60→120s). The upstream LiteLLM proxy has its own internal timeout that mekong-cli cannot control. The client-side timeout increase was addressing the wrong layer — the failure originates at the proxy, not at the mekong socket.

## Root Cause

1. **Wrong layer targeted** — `_timeout_for()` in `llm_client.py` controls `urllib.request.urlopen()` timeout, but the proxy rejects requests before the client's socket timeout fires.
2. **Uncaught timeout exceptions** — `LiteLLMProvider` uses `httpx.Client(timeout=120.0)` but does NOT catch `httpx.TimeoutException`. It propagates unhandled rather than falling through the failover chain.
3. **Circuit breaker over-sensitivity** — Timeouts count as full failures (same as 500 errors). 3 consecutive slow providers → circuit opens for 30s, blocking a provider that may recover quickly.
4. **Hardcoded 30s in executor.py** — `requests.request(..., timeout=30)` for recipe API steps, no configuration.

## Chosen Approach: Timeout-Aware Failover

| Aspect | Decision |
|--------|----------|
| User-facing behavior on timeout | **Hybrid** — try next provider silently, surface error only if ALL providers exhaust |
| Circuit breaker + timeouts | **Exclude** — timeouts don't count toward circuit breaker threshold |
| Scope | **Full audit** — LLM calls + executor + any other hardcoded timeout |
| Error classification | New `ProviderSoftFailure` for timeouts (vs hard failures for 5xx/connection errors) |

## Changes (3 files)

### 1. `src/core/llm_client.py`
- Add timeout exception detection in the main `chat()` error handler
- On timeout: log event → skip circuit breaker → try next provider
- Only surface error after ALL providers exhaust
- Log per-provider timeout value at construction

### 2. `src/core/providers.py`
- `LiteLLMProvider.chat()`: Add `except httpx.TimeoutException` → raise `ProviderSoftFailure`
- Same for `litellm_provider.py` standalone class (108 lines, legacy)

### 3. `src/core/executor.py`
- Make 30s hardcoded timeout configurable via `MEKONG_API_CALL_TIMEOUT` env var
- Log when executor API call times out

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|-----------|
| Timeout exception type varies by provider | Low | Scout confirms URLError, RuntimeError, httpx.TimeoutException — all catchable |
| ProviderSoftFailure changes error flow | Medium | Only triggers on timeout; existing hard error paths untouched |
| Executor timeout change breaks recipes | Low | Default stays 30s, only makes it configurable |

## What Stays Unchanged

- Circuit breaker for hard errors (5xx, connection refused)
- Provider priority order
- All public API signatures
- Existing test behavior (extended, not replaced)
