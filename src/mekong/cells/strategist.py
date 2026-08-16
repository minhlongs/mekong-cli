# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Strategist AI Cell — strategic recommendation engine.

Provides prompt-building and output-parsing utilities for the strategist cell,
which analyzes business questions against a particle's constitution and produces
structured strategic recommendations.
"""

from __future__ import annotations

import json
import re
from typing import Any

from src.mekong.cells.types import CellRecommendation
from src.mekong.constitution.parser import Constitution

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STRATEGIST_SYSTEM_PROMPT = """You are a Strategist AI Cell operating under the ZenOS constitution for "{particle_name}".

Your role is to analyze strategic questions and provide reasoned recommendations
that align with the particle's founding principles.

Mission Statement:
{mission_statement}

You MUST respond with a valid JSON object containing exactly these fields:
- recommendation: your strategic recommendation (string, REQUIRED)
- confidence: confidence score between 0.0 and 1.0 (number, REQUIRED)
- rationale: detailed explanation of your reasoning (string, REQUIRED, MUST be non-empty)
- risk_factors: list of potential risks (array of strings)
- estimated_impact: 'low', 'medium', or 'high' (string)

Respond ONLY with the JSON object. Do NOT wrap it in markdown code fences."""


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


def _extract_mission(constitution: Constitution) -> str:
    """Extract the mission statement from a constitution, or return a default.

    Searches for an article whose title contains "mission". Falls back to
    the first article's content, then to a generic default.
    """
    for article in constitution.articles:
        if "mission" in article.title.lower():
            return article.content.strip()

    if constitution.articles:
        return constitution.articles[0].content.strip()

    return "No mission statement defined."


def build_strategist_prompt(
    particle: str,
    constitution: Constitution,
    question: str,
) -> tuple[str, str]:
    """Build the system and user prompts for a strategist cell execution.

    Parameters
    ----------
    particle:
        The name of the particle (e.g. ``"test-particle"``).
    constitution:
        The parsed ``Constitution`` object for the particle.
    question:
        The strategic question to analyze.

    Returns
    -------
    tuple[str, str]
        A ``(system_prompt, user_prompt)`` pair ready to send to the LLM.
    """
    mission = _extract_mission(constitution)

    system_prompt = STRATEGIST_SYSTEM_PROMPT.replace(
        "{particle_name}", particle
    ).replace(
        "{mission_statement}", mission
    )

    articles_summary = "\n".join(
        f"Article {a.number}: {a.title}" for a in constitution.articles
    )

    user_prompt = (
        f"Strategic Question: {question}\n\n"
        f"Particle Constitution:\n{articles_summary}\n\n"
        f"Analyze the question above in the context of the particle's constitution "
        f"and mission. Provide a strategic recommendation with confidence score, "
        f"rationale, risk factors, and estimated impact."
    )

    return system_prompt, user_prompt


# ---------------------------------------------------------------------------
# Output parser
# ---------------------------------------------------------------------------


def _strip_code_fences(raw: str) -> str:
    """Remove markdown code fences and leading/trailing whitespace from *raw*."""
    cleaned = raw.strip()

    # Remove opening ```json or ``` markers (with optional language hint)
    cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
    # Remove closing ``` markers
    cleaned = re.sub(r"\s*```$", "", cleaned)

    return cleaned.strip()


def parse_strategist_output(raw: str) -> CellRecommendation:
    """Parse and validate the LLM response into a ``CellRecommendation``.

    Accepts raw LLM output (possibly wrapped in markdown code fences),
    extracts the JSON payload, and validates the required fields.

    Parameters
    ----------
    raw:
        The raw string returned by the LLM.

    Returns
    -------
    CellRecommendation
        The parsed and validated recommendation.

    Raises
    ------
    ValueError
        If the response cannot be parsed as JSON, or if ``recommendation``,
        ``confidence``, or ``rationale`` fail validation.
    """
    cleaned = _strip_code_fences(raw)

    if not cleaned:
        raise ValueError("Strategist output is empty")

    try:
        data: dict[str, Any] = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Strategist output is not valid JSON: {exc}\nRaw: {raw[:500]}"
        ) from exc

    # Validate required fields
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

    # Build the recommendation with optional fields
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
