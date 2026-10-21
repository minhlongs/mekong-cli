# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Sophia video catalog profiles — avatars, voices, and composition templates."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class AvatarProfile:
    """Presenter / digital avatar definition."""
    id: str
    name: str
    gender: str
    language: str
    provider: str
    preview_url: str
    description: str = ""
    to_dict = asdict


@dataclass(frozen=True)
class VoiceProfile:
    """Voice synthesis profile (ElevenLabs / Azure)."""
    id: str
    name: str
    language: str
    gender: str
    provider: str
    sample_text: str
    preview_url: str = ""
    to_dict = asdict


@dataclass(frozen=True)
class VideoTemplate:
    """Composition template for video layouts."""
    id: str
    name: str
    aspect_ratio: str
    description: str
    recommended_genres: list[str] = field(default_factory=list)
    to_dict = asdict
