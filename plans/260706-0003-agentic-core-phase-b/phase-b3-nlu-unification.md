# Phase B3: NLU Unification (Steps 9-10)

## Goal
Single intent classifier — eliminate duplication between `src/core/nlu.py` and `src/harness/pev/nlu.py`.

## Analysis
- `src/core/nlu.py` — production-ready, hybrid keyword+LLM, ~50 intents (DEPLOY/AUDIT/CREATE/FIX/STATUS + VN business intents)
- `src/harness/pev/nlu.py` — stub with only 5 intents (BUILD/FIX/REFACTOR/DEPLOY/REVIEW)

## Implementation
1. Expand `src/harness/pev/nlu.py` to delegate to `src/core/nlu.py` for all non-PEV-specific intents
2. Add PEV-specific intents (RECIPE_PARSE, STEP_EXECUTE, VERIFY) to `src/core/nlu.py`
3. Remove duplicate logic from harness version — single source of truth

## New Import Pattern
```python
from src.nlu import classify_intent  # unified entry point
```

## Verification
- `classify_intent("deploy the app")` → DEPLOY (unchanged)
- `classify_intent("build a recipe for X")` → BUILD or PEV-specific
- All existing NLU tests pass
- No regression in `src/core/nlu.py` callers

## Risk: LOW (delegation pattern, no behavior change)
