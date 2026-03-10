"""
Tests for factory/cascade.py CascadeEngine.

Verifies:
- Cascade detection returns suggestions for known trigger keywords
- No suggestions returned for unknown layers
- No suggestions returned when output has no trigger keywords
- build_lineage returns correct structure
- CascadeSuggestion dataclass fields are populated
"""

from __future__ import annotations

import logging

import pytest

from factory.cascade import CascadeEngine, CascadeSuggestion

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def engine() -> CascadeEngine:
    """Shared CascadeEngine instance for all tests."""
    return CascadeEngine()


def test_detect_cascades_founder_to_business(engine: CascadeEngine) -> None:
    """Founder output with 'revenue' should suggest business layer commands."""
    output = "We need to grow revenue and hire a sales team for our GTM strategy."
    suggestions = engine.detect_cascades("founder", output)

    assert suggestions, "Expected at least one cascade suggestion"
    assert all(isinstance(s, CascadeSuggestion) for s in suggestions)
    assert all(s.target_layer == "business" for s in suggestions)


def test_detect_cascades_product_to_engineering(engine: CascadeEngine) -> None:
    """Product output with 'implement' should suggest engineering layer commands."""
    output = "We need to implement the API endpoint and build the database schema."
    suggestions = engine.detect_cascades("product", output)

    assert suggestions, "Expected at least one cascade suggestion"
    assert all(s.target_layer == "engineering" for s in suggestions)


def test_detect_cascades_no_keywords_returns_empty(engine: CascadeEngine) -> None:
    """Output with no trigger keywords should return empty suggestions list."""
    output = "Everything looks good. No changes needed right now."
    suggestions = engine.detect_cascades("founder", output)
    assert suggestions == []


def test_detect_cascades_unknown_layer_returns_empty(engine: CascadeEngine) -> None:
    """An unknown layer name should return empty suggestions, not raise."""
    suggestions = engine.detect_cascades("nonexistent_layer", "some output text")
    assert suggestions == []


def test_detect_cascades_ops_has_no_cascades(engine: CascadeEngine) -> None:
    """Ops is the base layer — detecting cascades should always return empty."""
    output = "deploy ship monitor production CI/CD health uptime rollback"
    suggestions = engine.detect_cascades("ops", output)
    assert suggestions == [], "ops layer should never cascade to another layer"


def test_cascade_suggestion_has_required_fields(engine: CascadeEngine) -> None:
    """Each CascadeSuggestion must have command, reason, target_layer, context."""
    output = "We need revenue from sales and marketing channels."
    suggestions = engine.detect_cascades("founder", output)

    for s in suggestions:
        assert s.command, f"command is empty: {s}"
        assert s.reason, f"reason is empty: {s}"
        assert s.target_layer, f"target_layer is empty: {s}"
        assert isinstance(s.confidence, float)
        assert 0.0 <= s.confidence <= 1.0


def test_build_lineage_empty_session(engine: CascadeEngine) -> None:
    """build_lineage for unknown session should return empty steps."""
    result = engine.build_lineage("nonexistent-session-xyz")
    assert result["session_id"] == "nonexistent-session-xyz"
    assert result["steps"] == []


def test_record_step_then_build_lineage(engine: CascadeEngine) -> None:
    """Recording steps should make them visible in build_lineage."""
    sid = "test-session-001"
    engine.record_step(sid, "founder", "okr")
    engine.record_step(sid, "business", "sales", triggered_by="okr")

    lineage = engine.build_lineage(sid)
    assert lineage["session_id"] == sid
    assert len(lineage["steps"]) == 2
    commands = [s["command"] for s in lineage["steps"]]
    assert "okr" in commands
    assert "sales" in commands
