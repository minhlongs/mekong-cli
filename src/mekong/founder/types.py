# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""FounderGenome dataclass — core personality and risk profile for founder assessment."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FounderGenome:
    """Comprehensive founder assessment profile.

    Captures personality traits (Big Five via TIPI-10), core values,
    fears, risk profile across 5 dimensions, cognitive biases, and
    overall risk level classification.

    Notes field documents caveats about self-report limitations so
    consumers understand the reliability boundary of this data.
    """

    version: str
    """Schema version string (e.g. \"1.0.0\")."""

    assessed_at: str
    """ISO 8601 datetime when the assessment was completed."""

    particle_id: str | None
    """Optional ZenOS particle identifier for identity linkage."""

    mission: str
    """Founder's stated mission or purpose statement."""

    values: list[str]
    """Schwartz Values Inventory selections (e.g. self_direction, achievement)."""

    big_five: dict[str, int]
    """Big Five personality trait scores on 1-100 scale.

    Keys: openness, conscientiousness, extraversion, agreeableness, neuroticism
    """

    fears: list[dict]
    """List of fear entries, each with trigger, predicted_behavior, and mitigation."""

    risk_profile: dict[str, int]
    """Risk tolerance scores on 1-100 scale per dimension.

    Keys: financial, operational, reputational, compliance, technical
    """

    cognitive_biases: list[str]
    """Identified cognitive biases (e.g. confirmation_bias, overconfidence)."""

    risk_level: str
    """Overall risk classification: conservative | moderate | aggressive."""

    notes: list[str] = field(default_factory=list)
    """Caveats, limitations, and context documented during assessment."""
