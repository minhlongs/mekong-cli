"""Tests for src.core.nlu (B3 unification)."""

from __future__ import annotations

import pytest


class TestClassifyIntent:
    """Smoke tests: classify_intent returns valid IntentResult."""

    def test_import_classify_intent(self):
        from src.core.nlu import classify_intent

        assert callable(classify_intent)

    def test_returns_intent_result(self):
        from src.core.nlu import IntentResult, classify_intent

        result = classify_intent("Write a Python hello world script")
        assert isinstance(result, IntentResult)

    def test_has_intent_field(self):
        from src.core.nlu import classify_intent

        result = classify_intent("Deploy the service to production")
        assert hasattr(result, "intent")
        assert isinstance(result.intent, str)
        assert len(result.intent) > 0

    def test_has_confidence_field(self):
        from src.core.nlu import classify_intent

        result = classify_intent("Send an invoice to the customer")
        assert hasattr(result, "confidence")
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0

    def test_has_entities_field(self):
        from src.core.nlu import classify_intent

        result = classify_intent("Check the billing status")
        assert hasattr(result, "entities")
        assert isinstance(result.entities, dict)

    def test_known_intents(self):
        from src.core.nlu import classify_intent

        known = {"deploy", "audit", "create", "fix", "report", "schedule", "refactor", "optimize", "migrate", "ke-toan", "thue", "zalo-oa", "vietqr", "bhxh", "unknown"}
        result = classify_intent("generate a financial report for Q3")
        assert result.intent in known, f"Unexpected intent: {result.intent}"

    def test_classifier_in_all_exports(self):
        import src.core.nlu as nlu_mod

        assert "classify_intent" in nlu_mod.__all__
        assert "classify_intent" in dir(nlu_mod)
