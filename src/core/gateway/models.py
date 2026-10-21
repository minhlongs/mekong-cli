# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Gateway request/response models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .models_sub import (
    AutoRecipeInfo,
    GovernanceCheckRequest,
    HaltRequest,
    MemoryEntryInfo,
    MemoryStatsResponse,
    NLUParseRequest,
    NLUParseResponse,
    PresetAction,
    ProjectInfo,
    RecipeGenerateRequest,
    RecipeGenerateResponse,
    RecipeValidateRequest,
    RecipeValidateResponse,
    ScheduleAddRequest,
    ScheduleJobInfo,
    SwarmDispatchRequest,
    SwarmNodeInfo,
    SwarmRegisterRequest,
)

VERSION = "1.0.0"


class CommandRequest(BaseModel):
    """Incoming command from the cloud brain."""

    goal: str = Field(..., min_length=1, description="High-level goal to execute")
    token: str = Field(..., min_length=1, description="API authentication token")


class StepSummary(BaseModel):
    """Summary of a single execution step."""

    order: int
    title: str
    passed: bool
    exit_code: int
    summary: str


class HumanSummary(BaseModel):
    """Non-dev friendly summary in both languages."""

    en: str
    vi: str


class CommandResponse(BaseModel):
    """Response returned to the cloud caller."""

    status: str
    goal: str
    total_steps: int
    completed_steps: int
    failed_steps: int
    success_rate: float
    errors: list[str]
    warnings: list[str]
    steps: list[StepSummary]
    trace: dict[str, Any] | None = None
    human_summary: HumanSummary | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str = VERSION
    engine: str = "Plan-Execute-Verify"


__all__ = [
    "VERSION",
    "CommandRequest",
    "StepSummary",
    "HumanSummary",
    "CommandResponse",
    "HealthResponse",
    "PresetAction",
    "ProjectInfo",
    "SwarmNodeInfo",
    "SwarmRegisterRequest",
    "SwarmDispatchRequest",
    "ScheduleJobInfo",
    "ScheduleAddRequest",
    "MemoryEntryInfo",
    "MemoryStatsResponse",
    "NLUParseRequest",
    "NLUParseResponse",
    "RecipeGenerateRequest",
    "RecipeGenerateResponse",
    "RecipeValidateRequest",
    "RecipeValidateResponse",
    "AutoRecipeInfo",
    "GovernanceCheckRequest",
    "HaltRequest",
]
