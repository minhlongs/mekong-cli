# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Sophia AI Video Factory — Enums, dataclasses, validation helpers, and Pydantic models."""
from __future__ import annotations

from src.services.sophia_video_profiles import AvatarProfile, VideoTemplate, VoiceProfile
from src.services.sophia_video_validators import (
    FORBIDDEN_SCRIPT_CHARS, SAFE_IDENTIFIER_PATTERN, SAFE_JOB_ID_PATTERN,
    sanitize_script, validate_identifier, validate_job_id,
)

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.services.sophia_temporal_media import (
    FIGURE_SUBJECTS,
    MAX_AVATAR_FRAME_SHARE,
    MAX_DUAL_LOCK_RATIO,
    TemporalScene,
    LeadingChannel,
)


DEFAULT_SOPHIA_STORAGE_DIR = Path(".mekong/sophia")
DEFAULT_JOBS_DIR = DEFAULT_SOPHIA_STORAGE_DIR / "jobs"
DEFAULT_ARTIFACTS_DIR = DEFAULT_SOPHIA_STORAGE_DIR / "artifacts"


class AspectRatio(StrEnum):
    """Supported video aspect ratios."""
    VERTICAL_9_16 = "9:16"
    LANDSCAPE_16_9 = "16:9"
    SQUARE_1_1 = "1:1"


class JobStatus(StrEnum):
    """State machine for video render jobs."""
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class VideoRenderRequest(BaseModel):
    """Input payload for generating a Sophia AI video."""
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=2, max_length=128, description="Video title or slug")
    script: str = Field(..., min_length=10, max_length=10000, description="Narration or dialog text")
    leading_channel: LeadingChannel = Field(
        ...,
        description=(
            "Channel that carries meaning across the render: voice_leading, "
            "image_leading, or dual_lock. No implicit default — see "
            "docs/design-guidelines-temporal-media.md RULE-P1."
        ),
    )
    scenes: list[TemporalScene] = Field(
        default_factory=list,
        description="Per-scene leading-channel and subject declaration. May be empty for single-shot renders.",
    )
    avatar_id: str = Field(default="sophia-anchor-vi-01", description="ID of avatar presenter")
    voice_id: str = Field(default="elevenlabs-vi-hoang-01", description="ID of voice synthesis model")
    aspect_ratio: AspectRatio = Field(default=AspectRatio.VERTICAL_9_16, description="Video aspect ratio")
    template: str = Field(default="news_anchor", description="Template layout ID")
    design_dna_name: str | None = Field(default=None, description="Optional approved Design DNA name to style video")
    tenant_id: str = Field(default="default", description="Tenant ID for quota and MCU billing")
    dry_run: bool = Field(default=False, description="Simulate generation without invoking paid APIs")
    subtitles_enabled: bool = Field(default=True, description="Render dynamic subtitles / captions")
    background_music: str | None = Field(default=None, description="Optional background music track name")
    webhook_url: str | None = Field(default=None, description="Optional completion webhook URL")

    @field_validator("title")
    @classmethod
    def _validate_title(cls, v: str) -> str:
        if not (cleaned := v.strip()):
            raise ValueError("Title must not be empty")
        return cleaned

    @field_validator("avatar_id", "voice_id", "template", "tenant_id")
    @classmethod
    def _validate_ids(cls, v: str) -> str:
        return validate_identifier(v, "identifier")

    @field_validator("design_dna_name")
    @classmethod
    def _validate_dna(cls, v: str | None) -> str | None:
        return validate_identifier(v, "design DNA name") if v is not None else None

    @field_validator("script")
    @classmethod
    def _validate_script(cls, v: str) -> str:
        return sanitize_script(v)

    @model_validator(mode="after")
    def _validate_temporal_contract(self) -> VideoRenderRequest:
        """Enforce RULE-P2 (dual-lock cap) and RULE-P4 (no face lock) on scenes."""
        if self.scenes:
            dual = sum(1 for s in self.scenes if s.leading_channel is LeadingChannel.DUAL)
            if dual / len(self.scenes) > MAX_DUAL_LOCK_RATIO:
                raise ValueError(
                    f"RULE-P2: {dual}/{len(self.scenes)} scenes are dual_lock, above the "
                    f"{MAX_DUAL_LOCK_RATIO:.0%} cap. Redundancy must stay the exception."
                )
            for scene in self.scenes:
                if scene.subject in FIGURE_SUBJECTS and scene.avatar_scale > MAX_AVATAR_FRAME_SHARE:
                    raise ValueError(
                        f"RULE-P4: scene '{scene.scene_id}' shows a {scene.subject} while the "
                        f"avatar holds {scene.avatar_scale:.0%} of the frame. The avatar must "
                        "recede below half frame while content is the subject."
                    )
        return self


class VideoRenderResult(BaseModel):
    """Output descriptor for a Sophia video generation job."""
    model_config = ConfigDict(extra="forbid")

    job_id: str
    title: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    video_url: str | None = None
    local_artifact_path: str | None = None
    duration_seconds: float = 0.0
    credits_used: int = 0
    aspect_ratio: str
    template: str
    avatar_id: str
    voice_id: str
    design_dna_applied: str | None = None
    created_at: str
    completed_at: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_summary(self) -> str:
        """Formatted human-readable summary string."""
        lines = [
            f"🎬 Video Job: {self.job_id} [{self.status.value}]",
            f"  Title: {self.title}",
            f"  Aspect Ratio: {self.aspect_ratio} | Template: {self.template}",
            f"  Avatar: {self.avatar_id} | Voice: {self.voice_id}",
            f"  Duration: {self.duration_seconds:.1f}s | Credits Used: {self.credits_used} MCU",
        ]
        for label, val in [("Design DNA", self.design_dna_applied), ("URL", self.video_url), ("File", self.local_artifact_path), ("Error", self.error)]:
            if val:
                lines.append(f"  {label}: {val}")
        return "\n".join(lines)
