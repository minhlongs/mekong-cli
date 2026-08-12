---
title: "Fix Provider Model Routing Regression"
description: "Fix LLM_MODEL env var being sent to all providers instead of respecting provider-specific defaults and model alias resolution"
status: pending
priority: P1
effort: 3h
branch: main
tags: [llm, routing, regression, provider-model]
created: 2026-08-10
---

# Fix Provider Model Routing Regression

## Problem Statement

When running `mekong cook production-demo --strict --verbose`, the global `LLM_MODEL=qwen3.6-35b` is being sent to **all** providers (OmniRoute/Qwen/Gemini) despite each provider having its own default model and the model alias system designed to translate canonical names to provider-specific ones.

### Root Cause (line 432 in `src/core/llm_client.py`):
```python
use_model = model or self.model
```

This causes `self.model` (which defaults to `LLM_MODEL` env var or `"qwen3.6-35b"`) to override **every** provider's default, bypassing:
1. Provider-specific default models (e.g., `gemini-2.5-pro` for Gemini, `qwen3-coder-plus` for Qwen)
2. Model alias resolution in `OpenAICompatibleProvider.chat()` (line 269 in `providers.py`)
3. Backward compatibility for callers who rely on provider defaults

### Expected Behavior:
- **Explicit `model` parameter** → always respected (highest priority)
- **No explicit model** → provider's `_default_model` used → resolved via `resolve_model()` in provider
- **LLM_MODEL env var** → only used for the "primary" (universal) provider, not for auto-detected providers

---

## Architecture Analysis

### Data Flow (Current - Broken)

```
User calls client.chat(model=None)
    │
    ▼
llm_client.py:432  use_model = model or self.model  ──► "qwen3.6-35b" (from LLM_MODEL env)
    │
    ▼
provider.chat(messages, model="qwen3.6-35b", ...)
    │
    ├── OpenAICompatibleProvider.chat() ───────► resolve_model("qwen3.6-35b", "qwen") ──► "qwen3.6-35b" (no alias)
    ├── OpenAICompatibleProvider.chat() ───────► resolve_model("qwen3.6-35b", "openrouter") ──► "qwen3.6-35b" (no alias)
    └── GeminiProvider.chat() ─────────────────► model="qwen3.6-35b" (ignores gemini-2.5-pro default)
```

### Data Flow (Fixed)

```
User calls client.chat(model=None)
    │
    ▼
llm_client.py:432  use_model = model  ──► None (no override)
    │
    ▼
provider.chat(messages, model=None, ...)
    │
    ├── OpenAICompatibleProvider.chat() ───────► resolve_model(self._default_model, "qwen") ──► "qwen3-coder-plus"
    ├── OpenAICompatibleProvider.chat() ───────► resolve_model(self._default_model, "openrouter") ──► "anthropic/claude-sonnet-4"
    └── GeminiProvider.chat() ─────────────────► model=self._default_model ──► "gemini-2.5-pro"
```

### Key Insight
The `resolve_model()` function in `providers.py:269` **already handles** the logic:
```python
use_model = resolve_model(model or self._default_model, self._provider_name)
```

So the fix is simply: **don't pass a model from `LLMClient.chat()` when the caller didn't provide one**.

---

## Phase 1: Core Fix — LLMClient.chat() Model Parameter

### File: `src/core/llm_client.py` (line 432)

**Current:**
```python
use_model = model or self.model
```

**Fixed:**
```python
use_model = model  # None means "use provider default"
```

### Impact Analysis

| Caller Pattern | Before | After |
|---|---|---|
| `client.chat(messages, model="custom-model")` | Uses "custom-model" ✓ | Uses "custom-model" ✓ |
| `client.chat(messages)` with LLM_MODEL set | Uses LLM_MODEL for ALL providers ✗ | Uses each provider's default ✓ |
| `client.chat(messages)` no LLM_MODEL | Uses "qwen3.6-35b" for ALL providers ✗ | Uses each provider's default ✓ |
| Primary provider (LLM_BASE_URL+LLM_API_KEY+LLM_MODEL) | Works ✓ | Works ✓ (LLM_MODEL passed to provider as default) |

### Backward Compatibility
- **Explicit model parameter**: Fully preserved
- **Primary provider**: Uses `llm_model or self.model` at provider creation (line 226) — unchanged
- **Provider defaults**: Now respected via `resolve_model()` in each provider
- **Cache key**: Changes from `(messages, "qwen3.6-35b", temp)` to `(messages, None, temp)` — cache will differentiate by provider since provider loop is outside cache check

---

## Phase 2: Provider Default Model Audit

Verify each provider has correct `_default_model` set at construction:

| Provider | Construction Site | Default Model | Status |
|---|---|---|---|
| OpenRouter | llm_client.py:245 | `anthropic/claude-sonnet-4` | ✓ |
| AgentRouter | llm_client.py:245 | `claude-sonnet-4-6-20250514` | ✓ |
| Qwen/DashScope | llm_client.py:261 | `qwen3-coder-plus` | ✓ |
| DeepSeek | llm_client.py:261 | `deepseek-chat` | ✓ |
| Anthropic Direct | llm_client.py:274 | `claude-sonnet-4-6-20250514` | ✓ |
| OpenAI Direct | llm_client.py:284 | `gpt-4o` | ✓ |
| Gemini | llm_client.py:308 | `gemini-2.5-pro` | ✓ |
| Primary (Universal) | llm_client.py:226 | `llm_model or self.model` | ✓ |
| Local/Ollama | llm_client.py:301 | `LOCAL_LLM_MODEL` or `OLLAMA_MODEL` | ✓ |
| Vietnamese MLX | llm_client.py:326 | `VN_LLM_MODEL` or `qwen3-8b` | ✓ |

**No changes needed** — all providers already have sensible defaults.

---

## Phase 3: Model Alias Resolution Verification

### Current Flow (providers.py:267-269)
```python
from src.core.model_alias import resolve_model
use_model = resolve_model(model or self._default_model, self._provider_name)
```

### `resolve_model()` Logic (model_alias.py:69-97)
1. If `canonical_model` starts with `ollama:` → extract model name
2. If `provider_name == "primary"` → return canonical_model unchanged (respects explicit LLM_MODEL)
3. Look up `MODEL_ALIASES[canonical_model][provider_name]` → return mapped name or fallback

### Test Coverage (test_subagent_reviewer.py)
- `resolve_model("claude-sonnet-4-6", "qwen")` → `"qwen3-coder-plus"` ✓
- `resolve_model("claude-sonnet-4-6", "deepseek")` → `"deepseek-chat"` ✓
- `resolve_model("claude-sonnet-4-6", "openrouter")` → `"anthropic/claude-sonnet-4"` ✓
- `resolve_model("claude-sonnet-4-6", "primary")` → `"claude-sonnet-4-6"` ✓
- `resolve_model("ollama:qwen2.5:7b", "qwen")` → `"qwen2.5:7b"` ✓

**Verification needed**: Ensure `GeminiProvider` also uses alias resolution (currently doesn't — passes model directly to SDK).

---

## Phase 4: Focused Tests to Add/Update

### File: `tests/core/test_providers_coverage.py`

#### Test 1: LLMClient respects provider defaults when no model specified
```python
def test_llmclient_uses_provider_defaults_when_no_model():
    """LLMClient.chat(model=None) should not override provider defaults."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key", "LLM_MODEL": "forced-model"}):
        client = LLMClient()
        # Find openrouter provider
        openrouter = next(p for p in client.providers if p.name == "openrouter")
        assert openrouter._default_model == "anthropic/claude-sonnet-4"
        
        # Mock provider.chat to capture received model
        captured = {}
        original_chat = openrouter.chat
        def capture_chat(messages, model, temperature, max_tokens, json_mode):
            captured["model"] = model
            return LLMResponse(content="ok", model=model or openrouter._default_model)
        openrouter.chat = capture_chat
        
        client.chat([{"role": "user", "content": "test"}])
        
        # Provider should receive None, not "forced-model"
        assert captured["model"] is None
```

#### Test 2: Explicit model parameter still works
```python
def test_llmclient_explicit_model_overrides_provider_default():
    """Explicit model= parameter should be passed through."""
    client = LLMClient(providers=[MockProvider()])
    captured = {}
    client.providers[0].chat = lambda m, model, **kw: captured.update(model=model) or LLMResponse(content="ok", model=model)
    
    client.chat([{"role": "user", "content": "test"}], model="explicit-model")
    assert captured["model"] == "explicit-model"
```

#### Test 3: Primary provider uses LLM_MODEL as default
```python
def test_primary_provider_uses_llm_model_env():
    """Primary (universal) provider should use LLM_MODEL as its default."""
    with patch.dict(os.environ, {"LLM_BASE_URL": "http://test", "LLM_API_KEY": "key", "LLM_MODEL": "custom-model"}):
        client = LLMClient()
        primary = next(p for p in client.providers if p.name == "primary")
        assert primary._default_model == "custom-model"
```

#### Test 4: Cache key uses None when no model specified
```python
def test_cache_key_differentiates_by_provider_when_no_model():
    """Cache should store separate entries per provider when model=None."""
    client = LLMClient(providers=[MockProvider(name="p1"), MockProvider(name="p2")], enable_cache=True)
    # ... verify cache keys include provider identity
```

### File: `tests/seed/test_seed_llm_client.py` (or new `tests/core/test_llm_client.py`)

Add integration tests for the full routing behavior.

---

## Phase 5: Risk Assessment & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Cache behavior changes (different keys) | Medium | Low | Cache miss = slight latency, not correctness issue |
| Callers implicitly relying on LLM_MODEL being sent to all providers | Low | Medium | No such callers found in grep; add test to prevent regression |
| GeminiProvider not using alias resolution | Medium | Medium | Add alias resolution to GeminiProvider in follow-up |
| Provider defaults changed inadvertently | Low | High | Unit tests verify each provider's `_default_model` |

---

## Phase 6: Rollback Plan

If issues discovered post-deploy:
1. Revert `llm_client.py:432` to `use_model = model or self.model`
2. No database migrations, no config changes — pure code revert
3. Deploy via `mekong deploy:full` (2 min rollback)

---

## Phase 7: Success Criteria (Measurable)

- [ ] `mekong cook production-demo --strict --verbose` completes without "model not found" errors from providers
- [ ] Unit tests pass: `python3 -m pytest tests/core/test_providers_coverage.py -v`
- [ ] Each provider receives `model=None` when caller doesn't specify (verified via test capture)
- [ ] Explicit `model="custom"` still reaches provider as `"custom"`
- [ ] Primary provider still uses `LLM_MODEL` as its default
- [ ] Cache hit rate unchanged (or improved via provider-differentiated keys)

---

## File Ownership

| Phase | Files | Owner |
|---|---|---|
| 1 | `src/core/llm_client.py` (line 432) | Core fix |
| 2 | `src/core/llm_client.py` (provider construction) | Audit only — no changes |
| 3 | `src/core/providers.py` (GeminiProvider) | Follow-up if needed |
| 4 | `tests/core/test_providers_coverage.py` | Test additions |
| 5-7 | Documentation only | — |

---

## Dependencies

- **Blocker**: None — pure code change in `llm_client.py`
- **Parallel**: Test additions can be written before/after fix
- **Follow-up**: Add model alias resolution to `GeminiProvider.chat()` if needed

---

## Next Steps

1. Implement Phase 1 fix (1 line change)
2. Add Phase 4 tests
3. Run full test suite: `python3 -m pytest tests/ -v`
4. Manual verification: `mekong cook production-demo --strict --verbose`
5. Deploy and verify SHA match