# Plan: LLM Timeout Resilience

**Branch:** fix/layer2-ruff-tech-debt
**Status:** implemented
**Mode:** TDD — tests-first per phase
**Source:** `plans/260703-0106-llm-timeout-resilience/brainstorm-report.md`

## Context

LLM calls fail with "Provider API request failed. Request timed out" even after per-provider timeout bump (60s→120s). Root cause: upstream LiteLLM proxy has its own internal timeout. We need timeout-aware failover — try next provider silently on timeout, don't trip circuit breaker, only surface error if ALL providers exhaust.

## Phases

| # | Phase | Status | File |
|---|-------|--------|------|
| 1 | Tests for timeout behavior + soft failure | ✅ complete | `phase-01-tests.md` |
| 2 | ProviderSoftFailure exception + LiteLLM timeout handling | ✅ complete | `phase-02-providers.md` |
| 3 | LLMClient timeout detection + circuit breaker exclusion | ✅ complete | `phase-03-llmclient.md` |
| 4 | Executor timeout config + verification | ✅ complete | `phase-04-executor.md` |

## Acceptance Criteria

- [x] LiteLLMProvider catches `httpx.TimeoutException` → raises `ProviderSoftFailure`
- [x] `litellm_provider.py` standalone also catches timeout → `ProviderSoftFailure`
- [x] LLMClient.on timeout: tries next provider, skips circuit breaker, no user-visible error
- [x] Circuit breaker / ProviderHealth excludes `ProviderSoftFailure` from failure count
- [x] Error surfaced to user only when ALL providers exhaust
- [x] executor.py timeout configurable via `MEKONG_API_CALL_TIMEOUT` env var (default 30)
- [ ] All existing tests pass (`pytest tests/`)
- [x] No public API signature changes

## Files Changed

| File | Lines | Change |
|------|-------|--------|
| `src/core/providers.py` | +17 | `ProviderSoftFailure` class (L40-50), LiteLLM timeout handler (L450-452), export (L469) |
| `src/core/litellm_provider.py` | +5 | Import (L11), standalone timeout handler (L64-66) |
| `src/core/llm_client.py` | +40/-12 | Import `ProviderSoftFailure`, dedicated `except ProviderSoftFailure` branch (L502-510) |
| `src/core/executor.py` | +3/-1 | `MEKONG_API_CALL_TIMEOUT` env var (L10, L133) |
| `tests/core/test_providers_coverage.py` | +229 | 5 new test functions covering soft failure + failover |

## Verification

```bash
cd /Users/macbook/mekong-cli
pytest tests/core/test_providers_coverage.py -v --tb=short
python3 -m pytest tests/ -x  # full suite
```
