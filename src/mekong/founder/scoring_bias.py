# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Cognitive bias extraction and risk-level classification for founder assessment."""

from __future__ import annotations

BIAS_DIMENSION_MAP: dict[str, str] = {
    "bias_confirmation": "confirmation_bias",
    "bias_overconfidence": "overconfidence",
    "bias_sunk_cost": "sunk_cost_fallacy",
    "bias_planning": "planning_fallacy",
    "bias_self_serving": "self_serving_bias",
    "bias_anchoring": "anchoring",
    "bias_availability": "availability_heuristic",
    "bias_framing": "framing_effect",
    "bias_status_quo": "status_quo_bias",
    "bias_optimism": "optimism_bias",
}


def classify_risk_level(bias_count: int, risk_scores: dict[str, int]) -> str:
    """Classify overall risk level from bias count and risk profile."""
    avg_risk_raw = (
        sum(risk_scores.values()) / len(risk_scores) / 10
        if risk_scores
        else 5.0
    )

    if bias_count <= 3 or avg_risk_raw < 4:
        return "conservative"
    if bias_count <= 6 or avg_risk_raw < 7:
        return "moderate"
    return "aggressive"


def extract_biases(bias_responses: dict[str, bool]) -> list[str]:
    """Extract identified biases from yes/no responses."""
    return [
        BIAS_DIMENSION_MAP[qid]
        for qid, response in bias_responses.items()
        if response and qid in BIAS_DIMENSION_MAP
    ]
