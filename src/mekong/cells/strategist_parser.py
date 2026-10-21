# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Output parsing utilities for Strategist AI Cell responses."""

from __future__ import annotations

import json
import re
from typing import Any

from src.mekong.cells.types import CellRecommendation


def _strip_code_fences(raw: str) -> str:
    """Remove markdown code fences and leading/trailing whitespace from *raw*."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def parse_strategist_output(raw: str) -> CellRecommendation:
    """Parse and validate the LLM response into a ``CellRecommendation``."""
    cleaned = _strip_code_fences(raw)

    if not cleaned:
        raise ValueError("Strategist output is empty")

    try:
        data: dict[str, Any] = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Strategist output is not valid JSON: {exc}\nRaw: {raw[:500]}"
        ) from exc

    recommendation = data.get("recommendation")
    if not recommendation or not str(recommendation).strip():
        raise ValueError(
            "Strategist output missing required field: 'recommendation'"
        )

    confidence = data.get("confidence")
    if confidence is None:
        raise ValueError(
            "Strategist output missing required field: 'confidence'"
        )
    try:
        confidence = float(confidence)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Strategist 'confidence' must be a number, got: {confidence}"
        ) from exc
    if not (0.0 <= confidence <= 1.0):
        raise ValueError(
            f"Strategist 'confidence' must be between 0.0 and 1.0, got: {confidence}"
        )

    rationale = data.get("rationale")
    if not rationale or not str(rationale).strip():
        raise ValueError(
            "Strategist output missing required field: 'rationale' (must be non-empty)"
        )

    impact = str(data.get("estimated_impact", "medium")).lower()
    if impact not in ("low", "medium", "high"):
        impact = "medium"

    risk_factors_raw = data.get("risk_factors", [])
    if isinstance(risk_factors_raw, list):
        risk_factors = [str(rf) for rf in risk_factors_raw]
    else:
        risk_factors = []

    return CellRecommendation(
        recommendation=str(recommendation),
        confidence=confidence,
        rationale=str(rationale),
        risk_factors=risk_factors,
        estimated_impact=impact,
    )
