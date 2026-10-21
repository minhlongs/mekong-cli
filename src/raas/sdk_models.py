# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and parsing helpers for the Mekong RaaS SDK."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx


class MekongAPIError(Exception):
    """Non-2xx response from the RaaS API."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


@dataclass
class StepDetail:
    """Single step result within a completed task."""

    order: int
    title: str
    passed: bool
    exit_code: int
    summary: str


@dataclass
class Task:
    """Task state returned by GET /v1/tasks/{id}."""

    task_id: str
    status: str
    goal: str
    tenant_id: str
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    success_rate: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    steps: List[StepDetail] = field(default_factory=list)


@dataclass
class TaskResult:
    """Immediate response from POST /v1/tasks."""

    task_id: str
    status: str
    tenant_id: str


@dataclass
class AgentInfo:
    """Agent metadata from GET /v1/agents."""

    name: str
    description: str


@dataclass
class AgentResult:
    """Response from POST /v1/agents/{name}/run."""

    agent: str
    status: str
    output: str
    errors: List[str] = field(default_factory=list)


@dataclass
class ContentTemplate:
    """Content template fetched from RaaS Gateway."""

    template_id: str
    name: str
    description: str
    content_type: str
    channel: str
    template: str
    placeholders: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TemplateMetadata:
    """Metadata about available templates."""

    total: int
    categories: List[str]
    channels: List[str]
    content_types: List[str]


@dataclass
class RenderedContent:
    """Rendered content with injected analytics."""

    content_id: str
    template_id: str
    channel: str
    content_type: str
    rendered_content: str
    placeholders_used: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceData:
    """Performance metadata for published content."""

    content_id: str
    template_id: str
    channel: str
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    engagement_rate: float = 0.0
    click_through_rate: float = 0.0
    conversion_rate: float = 0.0
    revenue: float = 0.0
    published_at: str = ""


def _parse_sse_line(line: str) -> Optional[dict]:
    """Parse a single SSE line, returning the JSON payload or None."""
    if not line.startswith("data:"):
        return None
    payload = line[5:].strip()
    if not payload:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return None


def _parse_step(data: dict) -> StepDetail:
    return StepDetail(
        order=data["order"], title=data["title"], passed=data["passed"],
        exit_code=data["exit_code"], summary=data["summary"],
    )


def _parse_task(data: dict) -> Task:
    return Task(
        task_id=data["task_id"], status=data["status"], goal=data["goal"], tenant_id=data["tenant_id"],
        total_steps=data.get("total_steps", 0), completed_steps=data.get("completed_steps", 0),
        failed_steps=data.get("failed_steps", 0), success_rate=data.get("success_rate", 0.0),
        errors=data.get("errors", []), warnings=data.get("warnings", []),
        steps=[_parse_step(s) for s in data.get("steps", [])],
    )


def _raise_for_status(response: httpx.Response) -> None:
    """Raise MekongAPIError for non-2xx responses."""
    if response.is_success:
        return
    try:
        detail = response.json().get("detail", response.text)
    except Exception:
        detail = response.text
    raise MekongAPIError(response.status_code, detail)

