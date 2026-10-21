# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Strategist AI Cell — strategic recommendation engine."""

from __future__ import annotations

from src.mekong.cells.strategist_parser import (
    _strip_code_fences,
    parse_strategist_output,
)
from src.mekong.cells.types import CellRecommendation
from src.mekong.constitution.parser import Constitution

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


def _extract_mission(constitution: Constitution) -> str:
    """Extract the mission statement from a constitution, or return a default."""
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
    """Build the system and user prompts for a strategist cell execution."""
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


__all__ = [
    "CellRecommendation",
    "STRATEGIST_SYSTEM_PROMPT",
    "_extract_mission",
    "_strip_code_fences",
    "build_strategist_prompt",
    "parse_strategist_output",
]
