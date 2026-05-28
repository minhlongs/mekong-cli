"""Tests for HITLConfidenceGate."""
import pytest

from src.core.hitl_confidence_gate import (
    EscalationRequest,
    GateDecision,
    GateThresholds,
    HITLConfidenceGate,
    format_escalation_message,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _gate(**kw) -> HITLConfidenceGate:
    return HITLConfidenceGate(**kw)


def _eval(gate: HITLConfidenceGate, confidence: float) -> EscalationRequest:
    return gate.evaluate(confidence, "t1", "agent-x", "deploy service", "reason")


# ---------------------------------------------------------------------------
# Decision routing
# ---------------------------------------------------------------------------

def test_high_confidence_autonomous():
    req = _eval(_gate(), 0.90)
    assert req.decision is GateDecision.AUTONOMOUS


def test_mid_confidence_review():
    req = _eval(_gate(), 0.70)
    assert req.decision is GateDecision.ESCALATE_REVIEW


def test_low_confidence_block():
    req = _eval(_gate(), 0.50)
    assert req.decision is GateDecision.ESCALATE_BLOCK


# ---------------------------------------------------------------------------
# Boundary values (0.85 and 0.60 are inclusive lower bounds)
# ---------------------------------------------------------------------------

def test_boundary_exactly_autonomous_min():
    req = _eval(_gate(), 0.85)
    assert req.decision is GateDecision.AUTONOMOUS


def test_boundary_exactly_review_min():
    req = _eval(_gate(), 0.60)
    assert req.decision is GateDecision.ESCALATE_REVIEW


def test_boundary_just_below_review_min():
    req = _eval(_gate(), 0.599)
    assert req.decision is GateDecision.ESCALATE_BLOCK


def test_boundary_just_below_autonomous_min():
    req = _eval(_gate(), 0.849)
    assert req.decision is GateDecision.ESCALATE_REVIEW


# ---------------------------------------------------------------------------
# Custom thresholds
# ---------------------------------------------------------------------------

def test_custom_thresholds():
    gate = _gate(thresholds=GateThresholds(autonomous_min=0.95, review_min=0.70))
    assert _eval(gate, 0.94).decision is GateDecision.ESCALATE_REVIEW
    assert _eval(gate, 0.95).decision is GateDecision.AUTONOMOUS
    assert _eval(gate, 0.69).decision is GateDecision.ESCALATE_BLOCK


def test_invalid_thresholds_raise():
    with pytest.raises(ValueError):
        GateThresholds(autonomous_min=0.50, review_min=0.80)  # review > autonomous


# ---------------------------------------------------------------------------
# should_proceed shortcut
# ---------------------------------------------------------------------------

def test_should_proceed_true():
    assert _gate().should_proceed(0.90) is True
    assert _gate().should_proceed(0.85) is True


def test_should_proceed_false():
    assert _gate().should_proceed(0.84) is False
    assert _gate().should_proceed(0.00) is False


# ---------------------------------------------------------------------------
# Stats tracking
# ---------------------------------------------------------------------------

def test_stats_tracking():
    gate = _gate()
    _eval(gate, 0.90)  # autonomous
    _eval(gate, 0.70)  # review
    _eval(gate, 0.50)  # block
    _eval(gate, 0.91)  # autonomous

    stats = gate.get_stats()
    assert stats["total_evaluations"] == 4
    assert stats["autonomous_count"] == 2
    assert stats["review_count"] == 1
    assert stats["block_count"] == 1
    assert stats["escalation_rate"] == pytest.approx(0.50)


def test_stats_zero_division_safe():
    stats = _gate().get_stats()
    assert stats["escalation_rate"] == 0.0
    assert stats["total_evaluations"] == 0


# ---------------------------------------------------------------------------
# format_escalation_message
# ---------------------------------------------------------------------------

def test_format_message_includes_key_fields():
    gate = _gate()
    req = gate.evaluate(0.70, "task-42", "agent-7", "restart db", "low signal")
    msg = format_escalation_message(req)

    assert "task-42" in msg
    assert "agent-7" in msg
    assert "restart db" in msg
    assert "70.0%" in msg
    assert "low signal" in msg
    assert "ESCALATE_REVIEW" in msg.upper() or "REQUESTING HUMAN REVIEW" in msg.upper()


def test_format_message_no_reasoning():
    gate = _gate()
    req = gate.evaluate(0.40, "t2", "bot", "delete file")
    msg = format_escalation_message(req)
    assert "Reasoning" not in msg
