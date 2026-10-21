# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Fear, risk, and cognitive bias question sets for founder assessment."""

from __future__ import annotations

from typing import Any

FEAR_FIELDS: list[str] = ["trigger", "predicted_behavior", "mitigation"]

FEAR_QUESTIONS: list[dict[str, Any]] = [
    {"id": "fear_01", "text": "What situation as a founder most triggers your anxiety or fear?", "type": "short_text", "field": "trigger", "dimension": "fear"},
    {"id": "fear_02", "text": "When that trigger appears, what behavior do you typically predict from yourself?", "type": "short_text", "field": "predicted_behavior", "dimension": "fear"},
    {"id": "fear_03", "text": "What mitigation strategy would you apply to reduce the impact of this fear?", "type": "short_text", "field": "mitigation", "dimension": "fear"},
    {"id": "fear_04", "text": "Describe a second situation that triggers anxiety as a founder.", "type": "short_text", "field": "trigger", "dimension": "fear"},
    {"id": "fear_05", "text": "For the second trigger, what behavior do you predict?", "type": "short_text", "field": "predicted_behavior", "dimension": "fear"},
    {"id": "fear_06", "text": "For the second trigger, what is your mitigation strategy?", "type": "short_text", "field": "mitigation", "dimension": "fear"},
    {"id": "fear_07", "text": "Describe a third situation that triggers anxiety as a founder.", "type": "short_text", "field": "trigger", "dimension": "fear"},
    {"id": "fear_08", "text": "For the third trigger, what behavior do you predict?", "type": "short_text", "field": "predicted_behavior", "dimension": "fear"},
    {"id": "fear_09", "text": "For the third trigger, what is your mitigation strategy?", "type": "short_text", "field": "mitigation", "dimension": "fear"},
    {"id": "fear_10", "text": "Describe a fourth situation that triggers anxiety as a founder.", "type": "short_text", "field": "trigger", "dimension": "fear"},
    {"id": "fear_11", "text": "For the fourth trigger, what behavior do you predict?", "type": "short_text", "field": "predicted_behavior", "dimension": "fear"},
    {"id": "fear_12", "text": "For the fourth trigger, what is your mitigation strategy?", "type": "short_text", "field": "mitigation", "dimension": "fear"},
    {"id": "fear_13", "text": "Describe a fifth situation that triggers anxiety as a founder.", "type": "short_text", "field": "trigger", "dimension": "fear"},
    {"id": "fear_14", "text": "For the fifth trigger, what behavior do you predict?", "type": "short_text", "field": "predicted_behavior", "dimension": "fear"},
    {"id": "fear_15", "text": "For the fifth trigger, what is your mitigation strategy?", "type": "short_text", "field": "mitigation", "dimension": "fear"},
]

RISK_DIMENSIONS: list[str] = [
    "financial",
    "operational",
    "reputational",
    "compliance",
    "technical",
]

_LIKERT_10_OPTIONS: list[dict[str, Any]] = [
    {"value": 1, "label": "Extremely risk-averse"},
    {"value": 2, "label": ""},
    {"value": 3, "label": ""},
    {"value": 4, "label": ""},
    {"value": 5, "label": "Moderate"},
    {"value": 6, "label": ""},
    {"value": 7, "label": ""},
    {"value": 8, "label": ""},
    {"value": 9, "label": ""},
    {"value": 10, "label": "Extremely risk-seeking"},
]


def _risk_item(qid: str, text: str, dimension: str) -> dict[str, Any]:
    return {
        "id": qid,
        "text": text,
        "type": "likert_10",
        "options": [dict(o) for o in _LIKERT_10_OPTIONS],
        "dimension": dimension,
    }


RISK_QUESTIONS: list[dict[str, Any]] = [
    _risk_item("risk_financial", "How comfortable are you taking financial risks with company capital?", "financial"),
    _risk_item("risk_operational", "How much operational uncertainty are you willing to accept?", "operational"),
    _risk_item("risk_reputational", "How willing are you to risk public reputation for strategic gains?", "reputational"),
    _risk_item("risk_compliance", "How comfortable are you operating in regulatory grey areas?", "compliance"),
    _risk_item("risk_technical", "How much technical debt or unproven technology are you willing to adopt?", "technical"),
]

_YES_NO_OPTIONS: list[dict[str, Any]] = [
    {"value": True, "label": "Yes"},
    {"value": False, "label": "No"},
]


def _bias_item(qid: str, text: str, dimension: str, bias_label: str) -> dict[str, Any]:
    return {
        "id": qid,
        "text": text,
        "type": "yes_no",
        "options": [dict(o) for o in _YES_NO_OPTIONS],
        "dimension": dimension,
        "bias_label": bias_label,
    }


BIAS_QUESTIONS: list[dict[str, Any]] = [
    _bias_item("bias_confirmation", "Do you find yourself seeking evidence that confirms your existing beliefs more than evidence that challenges them?", "confirmation_bias", "Confirmation Bias"),
    _bias_item("bias_overconfidence", "Do you consistently rate your abilities higher than objective measures suggest?", "overconfidence", "Overconfidence Bias"),
    _bias_item("bias_sunk_cost", "Do you continue investing in failing projects because of what you have already put in?", "sunk_cost_fallacy", "Sunk Cost Fallacy"),
    _bias_item("bias_planning", "Do your projects consistently take longer and cost more than you initially estimated?", "planning_fallacy", "Planning Fallacy"),
    _bias_item("bias_self_serving", "Do you attribute successes to your own abilities and failures to external factors?", "self_serving_bias", "Self-Serving Bias"),
    _bias_item("bias_anchoring", "Do you rely heavily on the first piece of information you receive when making decisions?", "anchoring", "Anchoring Bias"),
    _bias_item("bias_availability", "Do you judge the likelihood of events based on how easily examples come to mind?", "availability_heuristic", "Availability Heuristic"),
    _bias_item("bias_framing", "Does the way a choice is presented (as a gain vs. a loss) strongly influence your decision?", "framing_effect", "Framing Effect"),
    _bias_item("bias_status_quo", "Do you prefer keeping things as they are rather than making changes?", "status_quo_bias", "Status Quo Bias"),
    _bias_item("bias_optimism", "Do you believe positive outcomes are more likely to happen to you than to others?", "optimism_bias", "Optimism Bias"),
]
