# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
RaaS API — /v1/ route handlers facade: tasks, agents, SSE streaming.

Mounts onto the existing gateway FastAPI app via include_router().
All routes require Bearer auth resolved by raas_auth_middleware.require_tenant.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from src.api.raas_router_keys import (  # noqa: F401
    get_task_status,
    stream_task,
    submit_task,
    tasks_router,
)
from src.api.raas_router_models import (  # noqa: F401
    AgentInfo,
    AgentRunRequest,
    AgentRunResponse,
    ErrorCode,
    MissionResultResponse,
    StepDetail,
    TaskListResponse,
    TaskRecord,
    TaskRequest,
    TaskResponse,
    TaskStatus,
    TaskStatusResponse,
    TaskSummary,
    TenantContext,
    _build_orchestrator,
    _goal_to_schema,
    _result_to_record,
    error_response,
    get_task_store,
    require_tenant,
    validate_required,
    validate_string_length,
)
from src.api.raas_router_usage import (  # noqa: F401
    get_task_result,
    list_agents,
    list_tasks,
    run_agent,
    save_task_result,
    usage_router,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["RaaS v1"])
router.include_router(tasks_router)
router.include_router(usage_router)

__all__ = ["router"]
