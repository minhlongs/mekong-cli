# Phase 02 — Populate suggested_recipe + Entity Patterns

**Context:** [plan.md](plan.md) | [phase-01-extend-intents.md](phase-01-extend-intents.md)

## Overview
- **Date:** 2026-02-23
- **Priority:** P2
- **Status:** pending (blocked by Phase 01)
- **Effort:** 30m

## Key Insights
- `IntentResult.suggested_recipe` field exists but is NEVER populated — always `""`
- `SmartRouter` checks `intent_result.suggested_recipe` first before tag-based matching
- Recipe files are `.md` files in `recipes/` dir — but dir may not exist in test env
  - `suggested_recipe` stores a recipe NAME (stem), not full path
- Entity extraction: `_PROJECT_RE` is anchored to 6 action verbs — needs expanding for new intents
- `_FILE_PATH_RE`: pattern `[\w./]+\.(py|ts|js|md|yaml|json)` — safe, no false positives for short words
- `_BRANCH_RE`: `(?:branch|nhánh)\s+([\w/-]+)` — needs branch keyword `"branch"` in text

## Requirements
- Add `INTENT_RECIPE_MAP` dict mapping intent → suggested recipe name
- Populate `result.suggested_recipe` in `classify()` when confidence ≥ 0.7
- Add `_FILE_PATH_RE` and `_BRANCH_RE` entity extraction
- Export `INTENT_RECIPE_MAP` in `__all__`

## Related Code Files
- **Modify:** `src/core/nlu.py`

## Architecture

```python
# Module-level constant
INTENT_RECIPE_MAP: Dict[Intent, str] = {
    Intent.DEPLOY:   "deploy-app",
    Intent.FIX:      "fix-bugs",
    Intent.TEST:     "run-tests",
    Intent.AUDIT:    "security-audit",
    Intent.CREATE:   "create-project",
    Intent.REFACTOR: "refactor-code",
    Intent.SEARCH:   "search-codebase",
    Intent.OPTIMIZE: "optimize-performance",
    # STATUS, SCHEDULE, LEARN → no recipe (too context-dependent)
}

# In classify():
result.suggested_recipe = INTENT_RECIPE_MAP.get(intent, "") if confidence >= 0.7 else ""
```

## Implementation Steps

1. Add `INTENT_RECIPE_MAP` dict after `KEYWORD_MAP` in `nlu.py`:
   - Map 8 intents to recipe name strings
   - LEARN, STATUS, SCHEDULE left unmapped (no standard recipe)

2. In `classify()` method, after creating `result`, add:
   ```python
   if confidence >= 0.7:
       result.suggested_recipe = INTENT_RECIPE_MAP.get(intent, "")
   ```

3. Add new entity regex patterns (after existing `_TARGET_RE`):
   ```python
   _FILE_PATH_RE = re.compile(
       r"[\w./][\w./]*\.(py|ts|js|md|yaml|json|toml|sh)",
       re.IGNORECASE,
   )
   _BRANCH_RE = re.compile(
       r"(?:branch|nhánh|nhanh)\s+([\w/.-]+)",
       re.IGNORECASE,
   )
   ```

4. In `_extract_entities()`, add extraction for new patterns:
   ```python
   # File path
   match = _FILE_PATH_RE.search(goal)
   if match:
       entities["file_path"] = match.group(0)

   # Branch name
   match = _BRANCH_RE.search(goal)
   if match:
       entities["branch"] = match.group(1)
   ```

5. Add `INTENT_RECIPE_MAP` to `__all__`

## Todo
- [ ] Add `INTENT_RECIPE_MAP` after KEYWORD_MAP
- [ ] Populate `suggested_recipe` in `classify()` when confidence ≥ 0.7
- [ ] Add `_FILE_PATH_RE` regex
- [ ] Add `_BRANCH_RE` regex
- [ ] Add file_path + branch extraction in `_extract_entities()`
- [ ] Export `INTENT_RECIPE_MAP` in `__all__`

## Success Criteria
- `classify("deploy sophia")` → `suggested_recipe == "deploy-app"`
- `classify("refactor src/core/nlu.py")` → `entities["file_path"] == "src/core/nlu.py"`
- `classify("switch to branch feature/auth")` → `entities["branch"] == "feature/auth"`
- `classify("hello world")` → `suggested_recipe == ""` (confidence too low)

## Risk Assessment
- LOW: `_FILE_PATH_RE` may match version numbers like "3.11" — exclude with negative lookahead if needed
- LOW: `suggested_recipe` is just a string — no file access, no I/O risk

## Security Considerations
- Regex patterns use controlled character classes — no ReDoS risk
- No user input reaches file system via these patterns

## Next Steps
→ Phase 03: Update tests
