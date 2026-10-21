# Mekong CLI — MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Composed temporal media contracts: the leading-channel declaration.

A composed render lays scripted narration over rendered video. That adds a
sequential verbal channel the 9-axis design model has no slot for, so the
render must declare which channel carries the meaning for each scene. See
docs/design-guidelines-temporal-media.md (RULE-P1, RULE-P4).
"""
from __future__ import annotations

from enum import StrEnum
import re

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Exactly one leading channel per scene. VALUES match the design guideline.
VOICE_LEADING = "voice_leading"
IMAGE_LEADING = "image_leading"
DUAL_LOCK = "dual_lock"

# RULE-P2: dual-lock is capped, not merely discouraged.
MAX_DUAL_LOCK_RATIO = 0.20

# RULE-P4: a presenter avatar may not hold more than half the frame when the
# picture is the meaning carrier.
MAX_AVATAR_FRAME_SHARE = 0.50

# Subjects whose meaning lives in the content, not the face.
FIGURE_SUBJECTS = frozenset({"figure", "document", "table", "chart", "invoice"})

# How a scene's subject is carried, for the scene list the checks read.
SUBJECT_SPECS = frozenset({"none", "avatar", *FIGURE_SUBJECTS})

AVATAR_FRAMES = frozenset({"full", "inset", "off_frame"})

VALUE_PATTERN = re.compile(r"^(?:voice_leading|image_leading|dual_lock)$")
SUBJECT_PATTERN = re.compile(r"^(?:avatar|figure|document|table|chart|invoice|none)$")


class LeadingChannel(StrEnum):
    """Which channel carries the meaning in one scene."""
    VOICE = "voice_leading"
    IMAGE = "image_leading"
    DUAL = "dual_lock"


class TemporalScene(BaseModel):
    """One beat of a composed render and the channel that leads it."""
    model_config = ConfigDict(extra="forbid")

    scene_id: str = Field(..., description="Stable id for this scene")
    leading_channel: LeadingChannel = Field(..., description="Channel that carries meaning here")
    subject: str = Field(default="none", description="What the scene shows")
    avatar_scale: float = Field(default=1.0, description="Presenter area share")
    avatar_frame: str = Field(default="full", description="Presenter placement")

    @model_validator(mode="after")
    def _check(self) -> TemporalScene:
        if self.subject not in SUBJECT_SPECS:
            raise ValueError(f"subject must be one of {sorted(SUBJECT_SPECS)}")
        if self.avatar_frame not in AVATAR_FRAMES:
            raise ValueError(f"avatar_frame must be one of {sorted(AVATAR_FRAMES)}")
        if not 0.0 < self.avatar_scale <= 1.0:
            raise ValueError("avatar_scale must be in (0, 1]")
        return self


__all__ = [
    "AVATAR_FRAMES",
    "DUAL_LOCK",
    "FIGURE_SUBJECTS",
    "IMAGE_LEADING",
    "MAX_AVATAR_FRAME_SHARE",
    "MAX_DUAL_LOCK_RATIO",
    "SUBJECT_SPECS",
    "SUBJECT_PATTERN",
    "TemporalScene",
    "VALUE_PATTERN",
    "VOICE_LEADING",
    "LeadingChannel",
]
