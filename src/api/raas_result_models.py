"""
RaaS API — Response models for mission result endpoints.

Provides MissionResultResponse (GET /v1/tasks/{id}/result) and
TaskListResponse (GET /v1/tasks) so result retrieval logic stays
separate from execution/status models.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.api.raas_task_models import TaskStatus


class MissionResultResponse(BaseModel):
    """Payload returned by GET /v1/tasks/{id}/result.

    Contains only the structured output produced by the orchestrator,
    without execution metadata. Designed to be lightweight and cacheable.
    """

    task_id: str = Field(..., description="Task identifier")
    goal: str = Field(..., description="Original goal string")
    result_schema: Optional[str] = Field(
        None, description="Report layout slug (e.g. 'marketing/campaign')"
    )
    result_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured output produced by the orchestrator",
    )
    completed_at: Optional[str] = Field(None, description="ISO-8601 completion timestamp")


class TaskSummary(BaseModel):
    """Lightweight task entry for list responses."""

    task_id: str
    goal: str
    status: TaskStatus
    result_schema: Optional[str] = None
    completed_at: Optional[str] = None
    success_rate: float = 0.0


class TaskListResponse(BaseModel):
    """Paginated list of task summaries for GET /v1/tasks."""

    tasks: List[TaskSummary] = Field(default_factory=list)
    total: int = Field(0, description="Total tasks matching filters (before pagination)")
    limit: int = Field(20, description="Page size used in this response")
    offset: int = Field(0, description="Offset used in this response")


__all__ = ["MissionResultResponse", "TaskSummary", "TaskListResponse"]
