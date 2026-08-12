---
title: "Fix Binh Phap Escalation Tests — Backward-Compatible Provider Restoration"
description: "Restore ESCALATION_PROVIDERS dict and local MLX semantics broken by refactor 83f67f94c"
status: pending
priority: P1
effort: 2h
branch: main
tags: [binh-phap, escalation, tests, backward-compatibility]
created: 2026-08-10
---

## Context

Commit `83f67f94c` (i18n refactor) removed the `ESCALATION_PROVIDERS` dictionary and changed "local_mlx" from M1 Max MLX server → Anthropic Fable. This broke 13 tests in `test_binh_phap_dispatcher.py` and `test_binh_phap_dag_integration.py`.

The LLMClient model-selection fix in `mekong-cli-core` is **working correctly** (25/25 tests pass). Only the Python-side Binh Phap escalation layer is broken.

## Root Cause Analysis

| File | Change in 83f67f94c | Impact |
|------|---------------------|--------|
| `src/core/binh_phap_escalation.py` | Removed `ESCALATION_PROVIDERS` dict | `ImportError` in tests |
| `src/core/binh_phap_escalation.py` | "local_mlx" → Fable (cloud) | Wrong base_url/provider_name |
| `src/core/binh_phap_escalation.py` | Removed MLX/Ollama fallback chain | No local inference resilience |

**Expected behavior (from original `c7ed614ed` and tests):**
- `local_mlx` → M1 Max MLX Server (`http://localhost:8001/v1`, model `qwen3.6-35b`, provider `rapid-mlx`)
- `local_mlx` fallback → Ollama (`http://localhost:11434/v1`, model `qwen3.5-9b`, provider `ollama-fallback`)
- `cloud_sonnet` → Anthropic Sonnet (`https://api.anthropic.com/v1`, `claude-sonnet-4-6`)
- `cloud_opus` → Anthropic Opus (`https://api.anthropic.com/v1`, `claude-opus-4-6`)
- Env var overrides: `MLX_BASE_URL`, `MLX_MODEL`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `ANTHROPIC_BASE_URL`

## Plan

### Phase 1: Restore ESCALATION_PROVIDERS with ZuneF Support (src/core/binh_phap_escalation.py)

**Files to modify:** `src/core/binh_phap_escalation.py`

**Changes:**
1. Add back `ESCALATION_PROVIDERS` dict with original local MLX config + cloud configs
2. Keep the new `_first_env` and `_resolve` helpers for ZuneF env var priority
3. Make `resolve_llm_provider()` use `ESCALATION_PROVIDERS` for known levels, fall back to `_resolve` for aliases
4. Preserve `create_provider_for_level()` with ZuneF/Anthropic key logic

**Specific implementation:**
```python
ESCALATION_PROVIDERS: dict[str, dict[str, str]] = {
    "local_mlx": {
        "base_url": "http://localhost:8001/v1",
        "model": "qwen3.6-35b",
        "provider_name": "rapid-mlx",
        "fallback_url": "http://localhost:11434/v1",
        "fallback_model": "qwen3.5-9b",
        "fallback_name": "ollama-fallback",
    },
    "cloud_sonnet": {
        "base_url": "https://api.anthropic.com/v1",
        "model": "claude-sonnet-4-6",
        "provider_name": "anthropic-sonnet",
    },
    "cloud_opus": {
        "base_url": "https://api.anthropic.com/v1",
        "model": "claude-opus-4-6",
        "provider_name": "anthropic-opus",
    },
}
```

`resolve_llm_provider(escalation_level)` logic:
- If `escalation_level` in `ESCALATION_PROVIDERS`: return config with env overrides (MLX_BASE_URL, OLLAMA_BASE_URL, ANTHROPIC_BASE_URL)
- Else if alias ("strategic", "cloud_opus", "AUTONOMOUS"): use `_resolve("OPUS", OPUS_MODEL)`
- Else if alias ("cloud_sonnet", "standard"): use `_resolve("SONNET", "claude-sonnet-4-6")`
- Else (local_mlx, tactical, default): use `_resolve("FABLE", FABLE_MODEL)` — but this should NOT be the default for "local_mlx"

**Key fix:** "local_mlx" must stay in ESCALATION_PROVIDERS and return local MLX config, not fall through to Fable.

### Phase 2: Verify Fix with Tests

**Commands:**
```bash
# Python Binh Phap tests
python3 -m pytest tests/test_binh_phap_dispatcher.py -v
python3 -m pytest tests/test_binh_phap_dag_integration.py -v

# Ensure LLM tests still pass
cd packages/mekong-cli-core && npx vitest run tests/unit/llm.test.ts
```

### Phase 3: Check for Cascading Effects

Verify no other code depends on the broken "local_mlx" → Fable behavior:
- `src/core/binh_phap_dispatcher.py` — uses `resolve_llm_provider()` 
- `src/core/binh_phap/topology.py` — `LLM_ROUTING` maps to "local_mlx", "cloud_sonnet", "cloud_opus"

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking ZuneF env var priority | Low | Medium | Preserve `_resolve()` for cloud providers |
| Breaking create_provider_for_level | Low | High | Keep existing logic, only fix config source |
| Other tests failing | Low | Low | Run full test suite after fix |

## Backwards Compatibility

- ✅ `ESCALATION_PROVIDERS` dict exported (tests import it)
- ✅ `resolve_llm_provider("local_mlx")` returns local MLX config
- ✅ `resolve_llm_provider("cloud_sonnet")` returns Anthropic Sonnet
- ✅ `resolve_llm_provider("cloud_opus")` returns Anthropic Opus
- ✅ Env var overrides work (MLX_BASE_URL, OLLAMA_BASE_URL, ANTHROPIC_BASE_URL)
- ✅ ZuneF env vars take priority for cloud providers
- ✅ Fallback chain: MLX → Ollama for local_mlx

## Success Criteria

- [ ] `test_binh_phap_dispatcher.py` — 14/14 pass
- [ ] `test_binh_phap_dag_integration.py` — 19/19 pass (or at least no regressions from this fix)
- [ ] `mekong-cli-core` LLM tests — 25/25 still pass
- [ ] No new import errors

## Rollback Plan

If fix causes regressions:
```bash
git checkout HEAD -- src/core/binh_phap_escalation.py
```

## Files to Modify

1. `src/core/binh_phap_escalation.py` — Primary fix (restore ESCALATION_PROVIDERS + fix routing)

## Test Commands

```bash
# Primary validation
python3 -m pytest tests/test_binh_phap_dispatcher.py -v
python3 -m pytest tests/test_binh_phap_dag_integration.py -v

# Regression check
cd packages/mekong-cli-core && npx vitest run tests/unit/llm.test.ts
python3 -m pytest tests/test_model_selector.py -v
python3 -m pytest tests/test_local_adapter.py -v
```