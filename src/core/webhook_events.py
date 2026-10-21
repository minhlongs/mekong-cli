# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Webhook Event Payloads.

Pydantic models for all webhook event payloads sent to AgencyOS.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

MissionStatus = Literal["pending", "planning", "running", "completed", "failed", "cancelled"]
StepStatus = Literal["pending", "running", "completed", "failed", "skipped"]
Priority = Literal["low", "normal", "high", "critical"]


class PlanStep(BaseModel):
    """Individual step in a mission plan."""
    order: int = Field(..., description="Execution order (0-indexed)")
    title: str = Field(..., description="Human-readable step description")
    agent: str = Field(..., description="Agent assigned to this step")
    params: dict[str, Any] = Field(default_factory=dict, description="Step parameters")
    estimated_duration: int = Field(0, description="Estimated seconds to complete")
    dependencies: list[int] = Field(default_factory=list, description="Dependent step orders")


class MissionCreatedPayload(BaseModel):
    """Payload for mission.created event."""
    mission_id: str = Field(..., description="Unique mission identifier")
    goal: str = Field(..., description="Natural language goal")
    tenant_id: str = Field(..., description="AgencyOS tenant ID")
    priority: Priority = Field(default="normal", description="Mission priority level")
    webhook_url: str | None = Field(None, description="Callback URL for results")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    estimated_credits: int = Field(1, description="Estimated credit cost")


class PlanPayload(BaseModel):
    """Payload for mission.planning event."""
    mission_id: str = Field(..., description="Parent mission ID")
    plan_id: str = Field(..., description="Unique plan identifier")
    steps: list[PlanStep] = Field(..., description="Execution steps")
    total_estimated_duration: int = Field(0, description="Estimated duration in seconds")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StepStartPayload(BaseModel):
    """Payload for mission.step.started event."""
    mission_id: str = Field(..., description="Parent mission ID")
    step_order: int = Field(..., description="Step order in plan")
    step_title: str = Field(..., description="Human-readable title")
    agent: str = Field(..., description="Executing agent name")
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    retry_count: int = Field(0, description="Retry attempt (0 = first try)")


class StepDonePayload(BaseModel):
    """Payload for mission.step.completed event."""
    mission_id: str = Field(..., description="Parent mission ID")
    step_order: int = Field(..., description="Step order in plan")
    step_title: str = Field(..., description="Human-readable title")
    exit_code: int = Field(0, description="Process exit code (0 = success)")
    duration_seconds: float = Field(..., description="Actual execution time")
    stdout: str = Field("", description="Standard output (truncated)")
    stderr: str = Field("", description="Standard error (truncated)")
    artifacts: list[str] = Field(default_factory=list, description="Generated file paths")
    credits_used: int = Field(1, description="Credits consumed by this step")
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StepFailPayload(BaseModel):
    """Payload for mission.step.failed event."""
    mission_id: str = Field(..., description="Parent mission ID")
    step_order: int = Field(..., description="Step order in plan")
    step_title: str = Field(..., description="Human-readable title")
    error_message: str = Field(..., description="Error description")
    error_type: str = Field(..., description="Exception class name")
    exit_code: int = Field(..., description="Process exit code (non-zero)")
    duration_seconds: float = Field(..., description="Time until failure")
    retry_count: int = Field(..., description="Retry attempt number")
    max_retries: int = Field(3, description="Maximum retry attempts")
    retry_after_seconds: int | None = Field(None, description="Suggested wait time before retry")
    failed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MissionMetrics(BaseModel):
    """Execution metrics for mission completion."""
    llm_calls: int = Field(0, description="Total LLM API calls")
    llm_tokens_in: int = Field(0, description="Input tokens consumed")
    llm_tokens_out: int = Field(0, description="Output tokens consumed")
    self_heal_count: int = Field(0, description="Auto-recovery attempts")
    retry_count: int = Field(0, description="Total retries across all steps")
    cache_hits: int = Field(0, description="LLM cache hits")
    cache_misses: int = Field(0, description="LLM cache misses")

    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0


class MissionDonePayload(BaseModel):
    """Payload for mission.completed event."""
    mission_id: str = Field(..., description="Unique mission ID")
    goal: str = Field(..., description="Original goal")
    status: Literal["completed"] = "completed"
    total_duration_seconds: float = Field(..., description="Total execution time")
    total_steps: int = Field(..., description="Number of steps executed")
    successful_steps: int = Field(..., description="Steps completed successfully")
    failed_steps: int = Field(0, description="Steps that failed then recovered")
    total_credits_used: int = Field(..., description="Final credit cost")
    artifacts: list[str] = Field(default_factory=list, description="All generated file paths")
    metrics: MissionMetrics = Field(..., description="Performance metrics")
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MissionFailPayload(BaseModel):
    """Payload for mission.failed event."""
    mission_id: str = Field(..., description="Unique mission ID")
    goal: str = Field(..., description="Original goal")
    status: Literal["failed"] = "failed"
    error_message: str = Field(..., description="Final error description")
    error_type: str = Field(..., description="Exception class name")
    failed_step_order: int = Field(..., description="Step that caused failure")
    total_duration_seconds: float = Field(..., description="Time until failure")
    partial_steps_completed: int = Field(0, description="Steps completed before failure")
    credits_refunded: int = Field(..., description="Credits to refund to tenant")
    retry_exhausted: bool = Field(True, description="Whether all retries were attempted")
    failed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CreditsLowPayload(BaseModel):
    """Payload for credits.low event."""
    tenant_id: str = Field(..., description="AgencyOS tenant ID")
    current_balance: int = Field(..., description="Remaining credits")
    threshold: int = Field(10, description="Low balance threshold")
    recommended_top_up: int = Field(100, description="Suggested purchase amount")
    last_mission_cost: int = Field(0, description="Credits used by last mission")
    warned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


WEBHOOK_EVENT_PAYLOADS: dict[str, type[BaseModel]] = {
    "mission.created": MissionCreatedPayload,
    "mission.planning": PlanPayload,
    "mission.step.started": StepStartPayload,
    "mission.step.completed": StepDonePayload,
    "mission.step.failed": StepFailPayload,
    "mission.completed": MissionDonePayload,
    "mission.failed": MissionFailPayload,
    "credits.low": CreditsLowPayload,
}

__all__ = [
    "MissionStatus", "StepStatus", "Priority", "MissionCreatedPayload", "PlanPayload",
    "PlanStep", "StepStartPayload", "StepDonePayload", "StepFailPayload",
    "MissionDonePayload", "MissionMetrics", "MissionFailPayload", "CreditsLowPayload",
    "WEBHOOK_EVENT_PAYLOADS",
]
