# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Scoring algorithms for founder genome assessment."""

from __future__ import annotations

from src.mekong.founder.scoring_bias import (
    BIAS_DIMENSION_MAP,
    classify_risk_level,
    extract_biases,
)

_TIPI_DIMENSION_ITEMS: dict[str, tuple[str, str]] = {
    "extraversion": ("tipi_01", "tipi_06"),
    "agreeableness": ("tipi_07", "tipi_02"),
    "conscientiousness": ("tipi_03", "tipi_08"),
    "emotional_stability": ("tipi_09", "tipi_04"),
    "openness": ("tipi_05", "tipi_10"),
}

_TIPI_REVERSE_ITEMS: set[str] = {"tipi_02", "tipi_04", "tipi_06", "tipi_08", "tipi_10"}

_RISK_DIMENSIONS: list[str] = [
    "financial",
    "operational",
    "reputational",
    "compliance",
    "technical",
]


def score_big_five(responses: dict[str, int]) -> dict[str, int]:
    """Score Big Five personality traits from TIPI-10 responses."""
    result: dict[str, int] = {}

    for dim_key, (normal_id, reverse_id) in _TIPI_DIMENSION_ITEMS.items():
        normal_val = responses.get(normal_id, 4)
        reverse_val = responses.get(reverse_id, 4)

        if normal_id in _TIPI_REVERSE_ITEMS:
            normal_val = 8 - normal_val
        if reverse_id in _TIPI_REVERSE_ITEMS:
            reverse_val = 8 - reverse_val

        raw_sum = normal_val + reverse_val
        normalized = int(round(((raw_sum - 2) / 12) * 99 + 1))
        normalized = max(1, min(100, normalized))

        result[dim_key] = normalized

    result["neuroticism"] = max(1, 101 - result["emotional_stability"])
    return result


def score_risk(ratings: dict[str, int]) -> dict[str, int]:
    """Convert risk dimension ratings (1-10) to standardized scores (10-100)."""
    return {
        dim: max(10, min(100, ratings.get(dim, 5) * 10))
        for dim in _RISK_DIMENSIONS
    }


__all__ = [
    "BIAS_DIMENSION_MAP",
    "_RISK_DIMENSIONS",
    "_TIPI_DIMENSION_ITEMS",
    "_TIPI_REVERSE_ITEMS",
    "classify_risk_level",
    "extract_biases",
    "score_big_five",
    "score_risk",
]
