# Phase 03 — Update Tests

**Context:** [plan.md](plan.md) | [phase-02-recipe-mapping-entities.md](phase-02-recipe-mapping-entities.md)

## Overview
- **Date:** 2026-02-23
- **Priority:** P2
- **Status:** pending (blocked by Phase 01 + 02)
- **Effort:** 30m

## Key Insights
- `test_intent_count` is a sentinel test — MUST update 7 → 12
- `test_all_intents_except_unknown_have_keywords` is self-enforcing — will auto-fail if new intent missing from KEYWORD_MAP
- `test_multiple_keywords_first_wins`: "deploy and fix" → DEPLOY still valid after changes
- No parametrize needed — simple individual test methods keep existing style consistent
- LLM fallback prompt in `_llm_fallback()` lists intents by name — also needs updating (separate step in nlu.py)
- Vietnamese diacritic tests: test both `"tìm kiếm"` (with diacritics) and `"tim kiem"` (without)

## Requirements
- Update `test_intent_count`: 7 → 12
- Add tests for 5 new intents (EN + VN each)
- Add tests for `suggested_recipe` population
- Add tests for `file_path` and `branch` entity extraction
- All 25 existing tests must still PASS

## Related Code Files
- **Modify:** `tests/test_nlu.py`

## Implementation Steps

1. Update `test_intent_count` in `TestIntentEnum`:
   ```python
   def test_intent_count(self):
       """There should be 12 intents."""
       self.assertEqual(len(Intent), 12)
   ```

2. Add import for `INTENT_RECIPE_MAP` in test file imports:
   ```python
   from src.core.nlu import (
       Intent, IntentResult, IntentClassifier, KEYWORD_MAP, INTENT_RECIPE_MAP,
   )
   ```

3. Add 10 new classification tests in `TestIntentClassifier`:
   ```python
   def test_refactor_english(self):
       result = self.classifier.classify("refactor the auth module")
       self.assertEqual(result.intent, Intent.REFACTOR)
       self.assertGreaterEqual(result.confidence, 0.7)

   def test_search_vietnamese_diacritics(self):
       result = self.classifier.classify("tìm kiếm lỗi trong planner")
       self.assertEqual(result.intent, Intent.SEARCH)

   def test_learn_english(self):
       result = self.classifier.classify("learn from past failures")
       self.assertEqual(result.intent, Intent.LEARN)

   def test_test_intent_english(self):
       result = self.classifier.classify("run test suite")
       self.assertEqual(result.intent, Intent.TEST)

   def test_optimize_english(self):
       result = self.classifier.classify("optimize query performance")
       self.assertEqual(result.intent, Intent.OPTIMIZE)
   ```

4. Add `suggested_recipe` tests:
   ```python
   def test_suggested_recipe_populated_on_high_confidence(self):
       result = self.classifier.classify("deploy sophia")
       self.assertNotEqual(result.suggested_recipe, "")

   def test_suggested_recipe_empty_on_unknown(self):
       result = self.classifier.classify("hello world")
       self.assertEqual(result.suggested_recipe, "")
   ```

5. Add entity extraction tests:
   ```python
   def test_entity_file_path(self):
       result = self.classifier.classify("refactor src/core/nlu.py")
       self.assertEqual(result.entities.get("file_path"), "src/core/nlu.py")

   def test_entity_branch(self):
       result = self.classifier.classify("deploy branch feature/auth")
       self.assertEqual(result.entities.get("branch"), "feature/auth")
   ```

6. Add `TestIntentRecipeMap` class:
   ```python
   class TestIntentRecipeMap(unittest.TestCase):
       def test_recipe_map_has_entries(self):
           self.assertGreater(len(INTENT_RECIPE_MAP), 0)

       def test_recipe_map_no_unknown(self):
           self.assertNotIn(Intent.UNKNOWN, INTENT_RECIPE_MAP)

       def test_recipe_map_values_are_strings(self):
           for v in INTENT_RECIPE_MAP.values():
               self.assertIsInstance(v, str)
               self.assertTrue(len(v) > 0)
   ```

## Todo
- [ ] Update `test_intent_count`: 7 → 12
- [ ] Add import for `INTENT_RECIPE_MAP`
- [ ] Add 5 new intent tests (EN keywords)
- [ ] Add 2 VN diacritic tests (SEARCH, TEST)
- [ ] Add `suggested_recipe` population tests (2 tests)
- [ ] Add `file_path` entity test
- [ ] Add `branch` entity test
- [ ] Add `TestIntentRecipeMap` class (3 tests)
- [ ] Run full suite → confirm 100% pass

## Success Criteria
- `python3 -m pytest tests/test_nlu.py -v` → all tests pass (25 existing + ~15 new = ~40 total)
- Zero test failures
- Zero regressions on existing tests

## Risk Assessment
- MEDIUM: `test_entity_file_path` — `_FILE_PATH_RE` must not over-match; test with "refactor src/core/nlu.py" specifically
- LOW: AUDIT's "check" keyword won't conflict with TEST tests if TEST test uses "run test" not "check test"

## Security Considerations
- N/A — test file only

## Next Steps
- Run: `python3 -m pytest tests/test_nlu.py -v`
- If pass: ready to implement with `/cook`
- If fail: debug entity regex patterns first
