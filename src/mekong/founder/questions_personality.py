# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""TIPI-10 personality and Schwartz Values question sets for founder assessment."""

from __future__ import annotations

from typing import Any

_LIKERT_7_OPTIONS: list[dict[str, Any]] = [
    {"value": 1, "label": "Disagree strongly"},
    {"value": 2, "label": "Disagree moderately"},
    {"value": 3, "label": "Disagree a little"},
    {"value": 4, "label": "Neutral"},
    {"value": 5, "label": "Agree a little"},
    {"value": 6, "label": "Agree moderately"},
    {"value": 7, "label": "Agree strongly"},
]


def _tipi_item(
    qid: str, text: str, dimension: str, reverse_scored: bool
) -> dict[str, Any]:
    return {
        "id": qid,
        "text": text,
        "type": "likert_7",
        "options": [dict(o) for o in _LIKERT_7_OPTIONS],
        "dimension": dimension,
        "reverse_scored": reverse_scored,
    }


TIPI_QUESTIONS: list[dict[str, Any]] = [
    _tipi_item("tipi_01", "I see myself as extraverted, enthusiastic.", "extraversion", False),
    _tipi_item("tipi_02", "I see myself as critical, quarrelsome.", "agreeableness", True),
    _tipi_item("tipi_03", "I see myself as dependable, self-disciplined.", "conscientiousness", False),
    _tipi_item("tipi_04", "I see myself as anxious, easily upset.", "emotional_stability", True),
    _tipi_item("tipi_05", "I see myself as open to new experiences, complex.", "openness", False),
    _tipi_item("tipi_06", "I see myself as reserved, quiet.", "extraversion", True),
    _tipi_item("tipi_07", "I see myself as sympathetic, warm.", "agreeableness", False),
    _tipi_item("tipi_08", "I see myself as disorganized, careless.", "conscientiousness", True),
    _tipi_item("tipi_09", "I see myself as calm, emotionally stable.", "emotional_stability", False),
    _tipi_item("tipi_10", "I see myself as conventional, uncreative.", "openness", True),
]

SCHWARTZ_VALUES: list[dict[str, str]] = [
    {"id": "self_direction", "label": "Self-Direction", "description": "Independent thought and action; choosing, creating, exploring."},
    {"id": "stimulation", "label": "Stimulation", "description": "Excitement, novelty, and challenge in life."},
    {"id": "hedonism", "label": "Hedonism", "description": "Pleasure and sensuous gratification for oneself."},
    {"id": "achievement", "label": "Achievement", "description": "Personal success through demonstrating competence according to social standards."},
    {"id": "power", "label": "Power", "description": "Social status and prestige, control or dominance over people and resources."},
    {"id": "security", "label": "Security", "description": "Safety, harmony, and stability of society, relationships, and self."},
    {"id": "conformity", "label": "Conformity", "description": "Restraint of actions, inclinations, and impulses likely to upset or harm others."},
    {"id": "tradition", "label": "Tradition", "description": "Respect, commitment, and acceptance of the customs and ideas that traditional culture or religion provide."},
    {"id": "benevolence", "label": "Benevolence", "description": "Preserving and enhancing the welfare of those with whom one is in frequent personal contact."},
    {"id": "universalism", "label": "Universalism", "description": "Understanding, appreciation, tolerance, and protection for the welfare of all people and nature."},
]
