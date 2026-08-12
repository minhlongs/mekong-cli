# Scout Report: Provider Model Routing Regression

## Issue
`mekong cook production-demo --strict --verbose` fails because `LLM_MODEL=qwen3.6-35b` is sent to all providers instead of respecting provider-specific defaults.

## Root Cause Location
**File:** `src/core/llm_client.py`
**Line:** 432
**Code:** `use_model = model or self.model`

## Current Behavior
- `self.model` defaults to `os.getenv("LLM_MODEL", "qwen3.6-35b")` (line 114)
- When caller invokes `client.chat(messages)` without explicit `model`, the global `LLM_MODEL` overrides every provider's default
- This bypasses the model alias resolution in `OpenAICompatibleProvider.chat()` (line 269)

## Evidence
```bash
# Provider defaults defined in _build_providers_from_env():
# OpenRouter:        "anthropic/claude-sonnet-4"
# AgentRouter:       "claude-sonnet-4-6-20250514"
# Qwen/DashScope:    "qwen3-coder-plus"
# DeepSeek:          "deepseek-chat"
# Anthropic Direct:  "claude-sonnet-4-6-20250514"
# OpenAI Direct:     "gpt-4o"
# Gemini:            "gemini-2.5-pro"
# Primary/Universal: llm_model or self.model (LLM_MODEL respected here correctly)
# Local/Ollama:      LOCAL_LLM_MODEL or OLLAMA_MODEL
# Vietnamese MLX:    VN_LLM_MODEL
```

## Model Alias System (Already Works)
`resolve_model(canonical, provider)` in `model_alias.py` translates:
- `"claude-sonnet-4-6"` → `"qwen3-coder-plus"` (for Qwen)
- `"claude-sonnet-4-6"` → `"deepseek-chat"` (for DeepSeek)
- `"claude-sonnet-4-6"` → `"anthropic/claude-sonnet-4"` (for OpenRouter)
- `"primary"` provider passes canonical unchanged (respects explicit LLM_MODEL)

But `LLMClient.chat()` passes `"qwen3.6-35b"` (no alias exists) → all providers receive wrong model.

## Fix Strategy
Change line 432 from:
```python
use_model = model or self.model
```
to:
```python
use_model = model  # None = use provider default via resolve_model()
```

## Affected Files
1. `src/core/llm_client.py` - Line 432 (1-line fix)
2. `tests/core/test_providers_coverage.py` - Add regression tests
3. `tests/seed/test_seed_llm_client.py` - Add integration tests (optional)

## Test Matrix
| Scenario | Expected Model Sent to Provider |
|---|---|
| `client.chat(msg, model="explicit")` | `"explicit"` |
| `client.chat(msg)` with LLM_MODEL=foo, OpenRouter provider | `None` → resolves to `"anthropic/claude-sonnet-4"` |
| `client.chat(msg)` with LLM_MODEL=foo, Qwen provider | `None` → resolves to `"qwen3-coder-plus"` |
| `client.chat(msg)` with LLM_MODEL=foo, Primary provider | `None` → resolves to `"foo"` (LLM_MODEL) |
| `client.chat(msg)` no LLM_MODEL, Gemini provider | `None` → resolves to `"gemini-2.5-pro"` |

## Risk Level: LOW
- Single line change
- Backward compatible (explicit model still works)
- Provider defaults already correct
- Model alias system already handles translation
- No database/config changes

## Verification Commands
```bash
# Run provider tests
python3 -m pytest tests/core/test_providers_coverage.py -v

# Run full suite
python3 -m pytest tests/ -v

# Manual test
mekong cook production-demo --strict --verbose
```