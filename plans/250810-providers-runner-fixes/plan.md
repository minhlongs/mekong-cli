---
title: "Fix Production Cook Blockers: Providers Default Model & Orchestrator Logger"
description: "Minimal fixes for GeminiProvider default-model handling and RecipeOrchestrator missing logger"
status: pending
priority: P1
effort: 2h
branch: main
tags: [providers, orchestrator, cook, blockers]
created: 2026-08-10
---

## Overview

Two blockers preventing production `cook` command:

1. **GeminiProvider** - `chat()` method requires `model: str` (not optional), but callers pass `None` expecting default fallback
2. **RecipeOrchestrator** - `_record_constitutional_metric()` uses `self.logger` but class lacks logger attribute

---

## Files to Modify

| File | Issue | Fix |
|------|-------|-----|
| `src/core/providers.py` | `chat(model: str)` type hint blocks `None` | Change to `model: str \| None`, add `use_model = model or self._default_model` (already exists) |
| `src/core/orchestrator/runner.py` | Missing `self.logger` | Add `import logging` + `self.logger = logging.getLogger(__name__)` in `__init__` |

---

## Phase 1: Fix GeminiProvider Default Model (providers.py)

### Current Code (lines 50-58)
```python
def chat(
    self,
    messages: list[dict[str, str]],
    model: str,  # BLOCKER: not optional
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> LLMResponse:
```

### Fix
```python
def chat(
    self,
    messages: list[dict[str, str]],
    model: str | None = None,  # Make optional with default
    temperature: float = 0.7,
    max_tokens: int = 2048,
    json_mode: bool = False,
) -> LLMResponse:
```

The fallback logic `use_model = model or self._default_model` already exists at line 140.

### Also Apply to Other Providers
Same pattern for `OpenAICompatibleProvider.chat()` and `LiteLLMProvider.chat()` for consistency.

---

## Phase 2: Fix Orchestrator Logger (runner.py)

### Current Code (missing)
No `import logging`, no `self.logger` in `__init__`.

### Fix
```python
# Add import at top (after line 7)
import logging

# Add in __init__ (after line 53 self.telemetry = ...)
self.logger = logging.getLogger(__name__)
```

---

## Validation Commands

```bash
# Test providers fix
python3 -c "
from src.core.providers import GeminiProvider
p = GeminiProvider(api_key='test')
# Should not raise TypeError
import inspect
sig = inspect.signature(p.chat)
print('model param:', sig.parameters['model'])
assert sig.parameters['model'].default is None or sig.parameters['model'].annotation == 'str | None'
print('OK: model is optional')
"

# Test orchestrator logger fix
python3 -c "
from src.core.orchestrator.runner import RecipeOrchestrator
orch = RecipeOrchestrator()
orch._record_constitutional_metric('plan', 0.5, 'test', 1)
print('OK: logger works')
"

# Run affected tests
python3 -m pytest tests/core/test_providers_coverage.py -v
python3 -m pytest tests/core/test_orchestrator_coverage.py -v

# Full test suite
python3 -m pytest tests/ -x --tb=short
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking existing callers passing explicit model | Low | Low | Default params maintain backward compat |
| Logger not configured (no output) | Medium | Low | Standard logging; apps configure root logger |
| Other providers need same fix | Medium | Medium | Apply pattern to all 3 providers |

---

## Rollback Plan

```bash
# If issues, revert specific files
git checkout src/core/providers.py
git checkout src/core/orchestrator/runner.py
```

---

## Success Criteria

- [ ] `GeminiProvider.chat(model=None)` works without TypeError
- [ ] `RecipeOrchestrator._record_constitutional_metric()` logs without AttributeError
- [ ] All provider coverage tests pass
- [ ] All orchestrator coverage tests pass (or only pre-existing mock-related failures remain)
- [ ] `python3 -m pytest tests/ -x` passes