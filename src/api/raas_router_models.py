# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Models and orchestrator conversion helpers for RaaS API router."""

from __future__ import annotations

import datetime as _dt
import sys
from typing import Any, Optional

from src.api.raas_auth_middleware import require_tenant
from src.api.raas_result_models import MissionResultResponse, TaskListResponse, TaskSummary
from src.api.raas_task_models import (
    AgentInfo,
    AgentRunRequest,
    AgentRunResponse,
    StepDetail,
    TaskRequest,
    TaskResponse,
    TaskStatus,
    TaskStatusResponse,
)
from src.api.raas_task_store import TaskRecord, get_task_store
from src.core.error_responses import ErrorCode, error_response
from src.core.input_validation import validate_required, validate_string_length
from src.raas.auth import TenantContext


def _facade() -> Any:
    """Return the parent raas_router module if loaded."""
    return sys.modules.get("src.api.raas_router")


def _build_orchestrator() -> Any:
    """Create a RecipeOrchestrator wired to the LLM client."""
    from src.core.orchestrator import RecipeOrchestrator
    from src.providers.llm.client import get_client

    client = get_client()
    return RecipeOrchestrator(
        llm_client=client if client.is_available else None,
        strict_verification=True,
        enable_rollback=True,
    )


def _goal_to_schema(goal: str) -> Optional[str]:
    """Derive a report layout slug from a goal string."""
    goal_lower = goal.lower()
    _schema_map = [
        (["marketing", "campaign"], "marketing/campaign"),
        (["sales", "pipeline", "crm"], "sales/pipeline"),
        (["finance", "budget", "revenue"], "finance/budget"),
        (["code", "review", "audit"], "engineering/code-review"),
        (["deploy", "deployment", "release"], "engineering/deployment"),
        (["security", "vulnerability", "cve"], "ops/security"),
        (["okr", "objective", "goal"], "strategy/okr"),
        (["sprint", "backlog", "story"], "product/sprint"),
    ]
    for keywords, schema in _schema_map:
        if any(kw in goal_lower for kw in keywords):
            return schema
    return None


def _result_to_record(record: TaskRecord, result: Any) -> TaskRecord:
    """Populate a TaskRecord from an OrchestrationResult in-place."""
    from src.core.orchestrator import OrchestrationStatus

    status_map = {
        OrchestrationStatus.SUCCESS: TaskStatus.SUCCESS,
        OrchestrationStatus.FAILED: TaskStatus.FAILED,
        OrchestrationStatus.PARTIAL: TaskStatus.PARTIAL,
        OrchestrationStatus.ROLLED_BACK: TaskStatus.ROLLED_BACK,
    }
    record.status = status_map.get(result.status, TaskStatus.FAILED)
    record.total_steps = result.total_steps
    record.completed_steps = result.completed_steps
    record.failed_steps = result.failed_steps
    record.success_rate = result.success_rate
    record.errors = result.errors
    record.warnings = result.warnings
    record.steps = [
        StepDetail(
            order=sr.step.order,
            title=sr.step.title,
            passed=sr.verification.passed,
            exit_code=sr.execution.exit_code,
            summary=sr.verification.summary,
        )
        for sr in result.step_results
    ]

    if hasattr(result, "structured_output") and result.structured_output:
        record.result_data = result.structured_output
    elif record.status == TaskStatus.SUCCESS and record.steps:
        record.result_data = {
            "steps": [
                {"order": s.order, "title": s.title, "summary": s.summary}
                for s in record.steps
            ]
        }

    facade = _facade()
    goal_fn = getattr(facade, "_goal_to_schema", _goal_to_schema) if facade else _goal_to_schema
    record.result_schema = goal_fn(record.goal)
    record.completed_at = _dt.datetime.utcnow().isoformat() + "Z"
    return record


__all__ = [
    "AgentInfo",
    "AgentRunRequest",
    "AgentRunResponse",
    "ErrorCode",
    "MissionResultResponse",
    "StepDetail",
    "TaskListResponse",
    "TaskRecord",
    "TaskRequest",
    "TaskResponse",
    "TaskStatus",
    "TaskStatusResponse",
    "TaskSummary",
    "TenantContext",
    "_build_orchestrator",
    "_facade",
    "_goal_to_schema",
    "_result_to_record",
    "error_response",
    "get_task_store",
    "require_tenant",
    "validate_required",
    "validate_string_length",
]
