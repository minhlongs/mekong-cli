# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Sophia AI Video Factory — RaaS video generation engine for Vietnam.

Funnel 3 of Mekong CLI (alongside Funnel 1: Zalo OA and Funnel 2: Tax & Accounting).
Re-exports all public and private symbols from sophia_video_models,
sophia_video_providers, and sophia_video_pipeline.
"""
from __future__ import annotations

import logging

from src.services.sophia_video_models import (
    DEFAULT_ARTIFACTS_DIR,
    DEFAULT_JOBS_DIR,
    DEFAULT_SOPHIA_STORAGE_DIR,
    FORBIDDEN_SCRIPT_CHARS,
    SAFE_IDENTIFIER_PATTERN,
    SAFE_JOB_ID_PATTERN,
    AspectRatio,
    AvatarProfile,
    JobStatus,
    LeadingChannel,
    VideoRenderRequest,
    VideoRenderResult,
    VideoTemplate,
    VoiceProfile,
    sanitize_script,
    validate_identifier,
    validate_job_id,
)
from src.services.sophia_video_pipeline import SophiaVideoService
from src.services.sophia_video_providers import (
    AVATAR_CATALOG,
    TEMPLATE_CATALOG,
    VOICE_CATALOG,
    deduct_tenant_mcu,
    estimate_mcu_cost,
    load_design_dna_tokens,
)

logger = logging.getLogger(__name__)

__all__ = [
    "SAFE_IDENTIFIER_PATTERN",
    "SAFE_JOB_ID_PATTERN",
    "FORBIDDEN_SCRIPT_CHARS",
    "DEFAULT_SOPHIA_STORAGE_DIR",
    "DEFAULT_JOBS_DIR",
    "DEFAULT_ARTIFACTS_DIR",
    "AspectRatio",
    "JobStatus",
    "AvatarProfile",
    "VoiceProfile",
    "VideoTemplate",
    "AVATAR_CATALOG",
    "VOICE_CATALOG",
    "TEMPLATE_CATALOG",
    "validate_identifier",
    "validate_job_id",
    "sanitize_script",
    "VideoRenderRequest",
    "VideoRenderResult",
    "SophiaVideoService",
    "estimate_mcu_cost",
    "load_design_dna_tokens",
    "deduct_tenant_mcu",
    "logger",
]
