"""Tests for IntentClassifier NLU engine."""

import unittest
from unittest.mock import MagicMock

from src.core.nlu import (
    ConversationContext,
    Intent,
    IntentClassifier,
    KEYWORD_MAP,
    VN_COMMAND_MAP,
    classify_intent,
    detect_lang,
)


class TestConversationContext(unittest.TestCase):
    """Test multi-turn conversation tracking."""

    def test_empty_context(self):
        ctx = ConversationContext()
        self.assertEqual(ctx.get_context_summary(), "No previous conversation.")
        self.assertIsNone(ctx.get_last_goal())
        self.assertEqual(ctx.turns, [])

    def test_add_turns_and_summary(self):
        ctx = ConversationContext()
        ctx.add_turn("user", "goal 1")
        ctx.add_turn("assistant", "response 1")
        ctx.add_turn("user", "goal 2")

        summary = ctx.get_context_summary()
        self.assertIn("User: goal 1", summary)
        self.assertIn("Assistant: response 1", summary)
        self.assertIn("User: goal 2", summary)
        self.assertEqual(ctx.get_last_goal(), "goal 2")

    def test_max_turns_truncation(self):
        ctx = ConversationContext()
        ctx.MAX_TURNS = 5
        for i in range(10):
            ctx.add_turn("user", f"goal {i}")
        self.assertEqual(len(ctx.turns), 5)
        self.assertEqual(ctx.turns[0].content, "goal 5")
        self.assertEqual(ctx.turns[-1].content, "goal 9")

    def test_get_last_goal_no_user_turn(self):
        ctx = ConversationContext()
        ctx.add_turn("assistant", "hello")
        self.assertIsNone(ctx.get_last_goal())

    def test_clear(self):
        ctx = ConversationContext()
        ctx.add_turn("user", "hello")
        ctx.clear()
        self.assertEqual(ctx.turns, [])
        self.assertIsNone(ctx.get_last_goal())


class TestLanguageDetection(unittest.TestCase):
    """Test Vietnamese language detection."""

    def test_detect_lang_markers(self):
        self.assertEqual(detect_lang("tạo hóa đơn mới"), "vi")
        self.assertEqual(detect_lang("kiem tra bao cao"), "vi")
        self.assertEqual(detect_lang("zalo broadcast message"), "vi")
        self.assertEqual(detect_lang("vietqr payment"), "vi")

    def test_detect_lang_diacritics(self):
        self.assertEqual(detect_lang("Hôm nay trời rất đẹp"), "vi")
        self.assertEqual(detect_lang("Chào bạn nhé"), "vi")

    def test_detect_lang_english(self):
        self.assertEqual(detect_lang("deploy application to aws"), "en")
        self.assertEqual(detect_lang("run test suite"), "en")


class TestIntentClassifier(unittest.TestCase):
    """Test keyword matching, entity extraction, and LLM fallback."""

    def setUp(self):
        self.classifier = IntentClassifier()

    # -- Intent classification --

    def test_deploy_english(self):
        """'deploy sophia' -> DEPLOY, high confidence."""
        result = self.classifier.classify("deploy sophia")
        self.assertEqual(result.intent, Intent.DEPLOY)
        self.assertGreaterEqual(result.confidence, 0.7)

    def test_deploy_vietnamese(self):
        """'trien khai sophia' -> DEPLOY."""
        result = self.classifier.classify("trien khai sophia")
        self.assertEqual(result.intent, Intent.DEPLOY)

    def test_deploy_vietnamese_diacritics(self):
        """'triển khai sophia' -> DEPLOY."""
        result = self.classifier.classify("triển khai sophia")
        self.assertEqual(result.intent, Intent.DEPLOY)

    def test_audit_keyword(self):
        """'audit security' -> AUDIT."""
        result = self.classifier.classify("audit security")
        self.assertEqual(result.intent, Intent.AUDIT)

    def test_create_keyword(self):
        """'create new project' -> CREATE."""
        result = self.classifier.classify("create new project")
        self.assertEqual(result.intent, Intent.CREATE)

    def test_fix_keyword(self):
        """'fix login bug' -> FIX."""
        result = self.classifier.classify("fix login bug")
        self.assertEqual(result.intent, Intent.FIX)

    def test_status_keyword(self):
        """'status of system' -> STATUS."""
        result = self.classifier.classify("status of system")
        self.assertEqual(result.intent, Intent.STATUS)

    def test_schedule_keyword(self):
        """'schedule daily backup' -> SCHEDULE."""
        result = self.classifier.classify("schedule daily backup")
        self.assertEqual(result.intent, Intent.SCHEDULE)

    def test_unknown_intent(self):
        """'hello world' -> UNKNOWN, low confidence."""
        result = self.classifier.classify("hello world")
        self.assertEqual(result.intent, Intent.UNKNOWN)
        self.assertLess(result.confidence, 0.5)

    def test_case_insensitive(self):
        """'DEPLOY APP' works case-insensitively."""
        result = self.classifier.classify("DEPLOY APP")
        self.assertEqual(result.intent, Intent.DEPLOY)

    def test_multiple_keywords_first_wins(self):
        """First matching intent wins."""
        result = self.classifier.classify("deploy and fix")
        self.assertEqual(result.intent, Intent.DEPLOY)

    def test_report_tiebreaker_over_create(self):
        """Phrase with report and create chooses report."""
        result = self.classifier.classify("create report for Q3")
        self.assertEqual(result.intent, Intent.REPORT)

    def test_confidence_exact_word(self):
        """Exact keyword word match -> high confidence."""
        result = self.classifier.classify("deploy my-app")
        self.assertGreaterEqual(result.confidence, 0.9)

    def test_confidence_substring(self):
        """Substring match (not exact word) -> lower confidence."""
        result = self.classifier.classify("undeployable system")
        self.assertEqual(result.intent, Intent.DEPLOY)

    # -- Entity extraction --

    def test_entity_project(self):
        """'deploy sophia' -> entities['project'] = 'sophia'."""
        result = self.classifier.classify("deploy sophia")
        self.assertEqual(result.entities.get("project"), "sophia")

    def test_entity_interval(self):
        """'run every 10 mins' -> entities['interval'] = '600'."""
        result = self.classifier.classify("schedule every 10 mins")
        self.assertEqual(result.entities.get("interval"), "600")

    def test_entity_interval_hours(self):
        """'run every 2 hours' -> entities['interval'] = '7200'."""
        result = self.classifier.classify("schedule every 2 hours")
        self.assertEqual(result.entities.get("interval"), "7200")

    def test_entity_target(self):
        """'check health of node-1' -> entities['target'] = 'node-1'."""
        result = self.classifier.classify("check health of node-1")
        self.assertEqual(result.entities.get("target"), "node-1")

    def test_entity_file(self):
        """Extracts code or config file paths."""
        result = self.classifier.classify("fix issue in src/core/nlu.py")
        self.assertEqual(result.entities.get("file"), "src/core/nlu.py")

    def test_no_project_for_keyword(self):
        """Project should not be extracted if candidate is a keyword."""
        result = self.classifier.classify("deploy check")
        self.assertNotIn("project", result.entities)

    # -- Raw goal preserved --

    def test_raw_goal_preserved(self):
        """IntentResult stores the original goal string."""
        result = self.classifier.classify("deploy sophia")
        self.assertEqual(result.raw_goal, "deploy sophia")

    # -- LLM fallback --

    def test_has_llm_checks(self):
        self.assertFalse(self.classifier._has_llm())
        mock_client = MagicMock()
        clf_with_llm = IntentClassifier(llm_client=mock_client)
        self.assertTrue(clf_with_llm._has_llm())

        obj_without_gen = object()
        clf_no_gen = IntentClassifier(llm_client=obj_without_gen)
        self.assertFalse(clf_no_gen._has_llm())

    def test_llm_fallback_triggered(self):
        """LLM fallback triggered when confidence < 0.5."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "deploy"
        classifier = IntentClassifier(llm_client=mock_llm)
        result = classifier.classify("vague task")
        mock_llm.generate.assert_called_once()
        self.assertEqual(result.confidence, 0.6)

    def test_llm_fallback_error_graceful(self):
        """LLM fallback failure doesn't crash."""
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = RuntimeError("LLM down")
        classifier = IntentClassifier(llm_client=mock_llm)
        result = classifier.classify("vague task")
        self.assertEqual(result.intent, Intent.UNKNOWN)

    def test_llm_classify_with_generate_json(self):
        """Tests generate_json path with valid JSON dictionary."""
        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {
            "intent": "deploy",
            "confidence": 0.95,
            "secondary_intents": ["audit", "non_existent_intent"],
            "entities": {"project": "mekong-app", "count": 3},
            "reasoning": "Explicit deploy instructions",
        }
        classifier = IntentClassifier(llm_client=mock_llm)
        res = classifier.classify("obscure instruction")
        self.assertEqual(res.intent, Intent.DEPLOY)
        self.assertEqual(res.confidence, 0.95)
        self.assertEqual(res.entities["project"], "mekong-app")
        self.assertEqual(res.entities["count"], "3")
        self.assertEqual(res.secondary_intents, [Intent.AUDIT])

    def test_llm_classify_generate_json_fails_falls_to_generate(self):
        """Tests generate_json throwing exception falling back to generate."""
        mock_llm = MagicMock()
        mock_llm.generate_json.side_effect = ValueError("Not supported")
        mock_llm.generate.return_value = '{"intent": "fix", "confidence": 0.85, "reasoning": "bug patch"}'
        classifier = IntentClassifier(llm_client=mock_llm)
        res = classifier.classify("vague error message")
        self.assertEqual(res.intent, Intent.FIX)
        self.assertEqual(res.confidence, 0.85)

    def test_llm_classify_client_none_direct(self):
        """Direct call to _llm_classify with llm_client=None."""
        clf = IntentClassifier(llm_client=None)
        res = clf._llm_classify("some goal")
        self.assertEqual(res.intent, Intent.UNKNOWN)

    def test_llm_classify_client_missing_generate(self):
        """Direct call to _llm_classify with client lacking generate method."""
        clf = IntentClassifier(llm_client=object())
        res = clf._llm_classify("some goal")
        self.assertEqual(res.intent, Intent.UNKNOWN)

    def test_llm_classify_markdown_json_parsing(self):
        """Parses JSON enclosed in markdown code fences."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = """Here is the result:
```json
{"intent": "optimize", "confidence": 0.88, "entities": "not_a_dict", "reasoning": "Speeding up"}
```"""
        classifier = IntentClassifier(llm_client=mock_llm)
        res = classifier.classify("xyz foobar qux")
        self.assertEqual(res.intent, Intent.OPTIMIZE)
        self.assertEqual(res.confidence, 0.88)
        self.assertEqual(res.entities, {})

    def test_llm_classify_single_intent_word(self):
        """Parses single intent word from raw text response."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "STATUS"
        classifier = IntentClassifier(llm_client=mock_llm)
        res = classifier.classify("xyz foobar qux")
        self.assertEqual(res.intent, Intent.STATUS)

    def test_llm_classify_gibberish_response(self):
        """Falls back to UNKNOWN when response is totally unrecognized."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "blablabla incomprehensible"
        classifier = IntentClassifier(llm_client=mock_llm)
        res = classifier.classify("xyz foobar qux")
        self.assertEqual(res.intent, Intent.UNKNOWN)

    def test_llm_classify_malformed_json_fallback_to_intent_word(self):
        """Malformed JSON braces triggers JSONDecodeError and falls back to word match."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "{not: valid json} AUDIT"
        classifier = IntentClassifier(llm_client=mock_llm)
        res = classifier._llm_classify("goal")
        self.assertEqual(res.intent, Intent.UNKNOWN)

    def test_llm_classify_malformed_json_fallback_to_single_intent(self):
        """Malformed JSON where remaining text or direct call falls to single word."""
        mock_llm = MagicMock()
        # When json.loads raises JSONDecodeError, falls through to response_upper
        mock_llm.generate.return_value = "{broken json"
        classifier = IntentClassifier(llm_client=mock_llm)
        res = classifier._llm_classify("goal")
        self.assertEqual(res.intent, Intent.UNKNOWN)

    def test_parse_llm_response_invalid_intent_value(self):
        """Handles invalid intent in json dictionary."""
        clf = IntentClassifier()
        res = clf._parse_llm_response({"intent": "does_not_exist", "confidence": -0.5}, "goal")
        self.assertEqual(res.intent, Intent.UNKNOWN)
        self.assertEqual(res.confidence, 0.0)

    def test_classify_batch(self):
        """Classifies multiple goals in order."""
        results = self.classifier.classify_batch(["deploy app", "fix error"])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].intent, Intent.DEPLOY)
        self.assertEqual(results[1].intent, Intent.FIX)


class TestClassifyIntentConvenience(unittest.TestCase):
    """Test top-level classify_intent function."""

    def test_classify_intent(self):
        res = classify_intent("deploy sophia")
        self.assertEqual(res.intent, Intent.DEPLOY)


class TestVNCommandMap(unittest.TestCase):
    """Test VN_COMMAND_MAP entries."""

    def test_command_map_mappings(self):
        self.assertEqual(VN_COMMAND_MAP["ke-toan"], Intent.KE_TOAN)
        self.assertEqual(VN_COMMAND_MAP["thue"], Intent.THUE)
        self.assertEqual(VN_COMMAND_MAP["zalo"], Intent.ZALO_OA)
        self.assertEqual(VN_COMMAND_MAP["vietqr"], Intent.VIETQR)
        self.assertEqual(VN_COMMAND_MAP["bhxh"], Intent.BHXH)


class TestIntentEnum(unittest.TestCase):
    """Test Intent enum values."""

    def test_all_intents_are_strings(self):
        """All intent values are lowercase strings."""
        for intent in Intent:
            self.assertIsInstance(intent.value, str)
            self.assertEqual(intent.value, intent.value.lower())

    def test_intent_count(self):
        """11 original + 5 VN business intents = 16 total."""
        self.assertEqual(len(Intent), 16)


class TestKeywordMap(unittest.TestCase):
    """Test KEYWORD_MAP structure."""

    def test_all_intents_except_unknown_have_keywords(self):
        """Every non-UNKNOWN intent has keywords."""
        for intent in Intent:
            if intent != Intent.UNKNOWN:
                self.assertIn(intent, KEYWORD_MAP)
                self.assertGreater(len(KEYWORD_MAP[intent]), 0)

    def test_unknown_not_in_map(self):
        """UNKNOWN should not be in the keyword map."""
        self.assertNotIn(Intent.UNKNOWN, KEYWORD_MAP)


if __name__ == "__main__":
    unittest.main()
