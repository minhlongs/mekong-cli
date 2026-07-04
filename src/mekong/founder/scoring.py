"""Scoring algorithms for founder genome assessment.

Handles Big Five personality scoring (TIPI-10 normalization),
risk profile computation, and cognitive bias classification.

All functions accept validated response structures and return
standardized scores on 1-100 scales.

Caveats about self-report limitations:
- TIPI-10 is a brief screening instrument, not a clinical diagnostic tool.
- Self-reported biases have inherent accuracy limitations.
- Risk tolerance is context-dependent; scores reflect stated preference,
  not necessarily revealed behavior under pressure.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Big Five scoring (TIPI-10)
# ---------------------------------------------------------------------------

# Dimension → (item_id_a, item_id_b) where item_id_a is normal, item_id_b is reverse-scored
_TIPI_DIMENSION_ITEMS: dict[str, tuple[str, str]] = {
    "extraversion": ("tipi_01", "tipi_06"),
    "agreeableness": ("tipi_07", "tipi_02"),
    "conscientiousness": ("tipi_03", "tipi_08"),
    "emotional_stability": ("tipi_09", "tipi_04"),
    "openness": ("tipi_05", "tipi_10"),
}

_TIPI_REVERSE_ITEMS: set[str] = {"tipi_02", "tipi_04", "tipi_06", "tipi_08", "tipi_10"}


def score_big_five(responses: dict[str, int]) -> dict[str, int]:
    """Score Big Five personality traits from TIPI-10 responses.

    Each dimension has 2 items rated 1-7. Reverse-scored items are
    inverted (8 - response). Raw dimension scores (2-14) are then
    linearly normalized to a 1-100 scale.

    Args:
        responses: Mapping of tipi question IDs (e.g. \"tipi_01\") to
            integer responses on the 1-7 Likert scale.

    Returns:
        Dict with keys: openness, conscientiousness, extraversion,
        agreeableness, emotional_stability. Values are integers on 1-100.

    Notes:
        Normalization formula: ((raw_sum - 2) / 12) * 99 + 1
        The neuroticism dimension is derived as 101 - emotional_stability.
    """
    result: dict[str, int] = {}

    for dim_key, (normal_id, reverse_id) in _TIPI_DIMENSION_ITEMS.items():
        normal_val = responses.get(normal_id, 4)
        reverse_val = responses.get(reverse_id, 4)

        # Reverse-score the appropriate item
        if normal_id in _TIPI_REVERSE_ITEMS:
            normal_val = 8 - normal_val
        if reverse_id in _TIPI_REVERSE_ITEMS:
            reverse_val = 8 - reverse_val

        raw_sum = normal_val + reverse_val  # range: 2-14
        normalized = int(round(((raw_sum - 2) / 12) * 99 + 1))
        normalized = max(1, min(100, normalized))

        result[dim_key] = normalized

    # Add neuroticism (inverse of emotional stability)
    result["neuroticism"] = max(1, 101 - result["emotional_stability"])

    return result


# ---------------------------------------------------------------------------
# Risk profile scoring
# ---------------------------------------------------------------------------

_RISK_DIMENSIONS: list[str] = [
    "financial",
    "operational",
    "reputational",
    "compliance",
    "technical",
]


def score_risk(ratings: dict[str, int]) -> dict[str, int]:
    """Convert risk dimension ratings (1-10) to standardized scores (10-100).

    Each dimension is rated on a 1-10 scale. The function converts to
    a 1-100 scale by multiplying by 10, clamping to valid range.

    Args:
        ratings: Mapping of risk dimension to integer rating (1-10).
            Expected keys: financial, operational, reputational,
            compliance, technical.

    Returns:
        Dict with same keys mapped to 10-100 integer scores.

    Notes:
        This is a linear transformation. Values represent stated risk
        tolerance, not actual risk exposure. Context-dependent factors
        (market conditions, team composition, runway) are not captured
        by this score.
    """
    return {
        dim: max(10, min(100, ratings.get(dim, 5) * 10))
        for dim in _RISK_DIMENSIONS
    }


# ---------------------------------------------------------------------------
# Risk level classification
# ---------------------------------------------------------------------------


def classify_risk_level(bias_count: int, risk_scores: dict[str, int]) -> str:
    """Classify overall risk level from bias count and risk profile.

    Uses a two-factor approach: the number of identified cognitive biases
    and the average stated risk tolerance. Classification checks are
    evaluated low-to-high:

    - **conservative**: 0-3 biases OR average risk < 4 (on 1-10 scale)
    - **moderate**: 4-6 biases OR average risk < 7
    - **aggressive**: 7+ biases OR average risk >= 7

    Args:
        bias_count: Number of cognitive biases identified (0-10).
        risk_scores: Dict of risk dimension scores (10-100 scale).

    Returns:
        One of \"conservative\", \"moderate\", or \"aggressive\".

    Notes:
        The \"or\" logic means the lowest-matching condition determines
        the level. This is intentional: a founder with few biases but
        very high risk appetite should still be flagged appropriately.
        Classification is advisory only — it reflects self-reported
        tendencies, not validated psychometric profiling.
    """
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


# ---------------------------------------------------------------------------
# Bias extraction helper
# ---------------------------------------------------------------------------


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


def extract_biases(bias_responses: dict[str, bool]) -> list[str]:
    """Extract identified biases from yes/no responses.

    Args:
        bias_responses: Mapping of bias question IDs to boolean responses
            (True = bias present).

    Returns:
        List of bias dimension names where the response indicates the
        bias is present.

    Notes:
        Each positive response increases the bias count used in
        classify_risk_level. Self-reported bias detection has known
        accuracy limitations (Dunning-Kruger effect, social desirability
        bias).
    """
    return [
        BIAS_DIMENSION_MAP[qid]
        for qid, response in bias_responses.items()
        if response and qid in BIAS_DIMENSION_MAP
    ]
