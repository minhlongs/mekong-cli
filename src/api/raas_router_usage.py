# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Task listing, result retrieval/saving, and agent execution handlers for RaaS API."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from src.api.raas_router_models import (
    AgentInfo,
    AgentRunRequest,
    AgentRunResponse,
    ErrorCode,
    MissionResultResponse,
    TaskListResponse,
    TaskStatus,
    TaskSummary,
    TenantContext,
    _facade,
    error_response,
    get_task_store,
    require_tenant,
    validate_required,
)

logger = logging.getLogger(__name__)
usage_router = APIRouter()


def _resolve_store() -> Any:
    facade = _facade()
    return (getattr(facade, "get_task_store", get_task_store) if facade else get_task_store)()


@usage_router.get("/tasks", response_model=TaskListResponse)
def list_tasks(
    tenant: TenantContext = Depends(require_tenant),
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    status: Optional[str] = Query(None, description="Filter by TaskStatus value"),
) -> TaskListResponse:
    """List tasks for the authenticated tenant with pagination and optional status filter."""
    store = _resolve_store()
    records = store.list_tasks(tenant_id=tenant.tenant_id, limit=limit, offset=offset, status=status)
    summaries = [
        TaskSummary(
            task_id=r.task_id,
            goal=r.goal,
            status=r.status,
            result_schema=r.result_schema,
            completed_at=r.completed_at,
            success_rate=r.success_rate,
        )
        for r in records
    ]
    all_records = store.list_tasks(tenant_id=tenant.tenant_id, limit=10000, offset=0, status=status)
    return TaskListResponse(tasks=summaries, total=len(all_records), limit=limit, offset=offset)


@usage_router.get("/tasks/{task_id}/result", response_model=MissionResultResponse)
def get_task_result(task_id: str, tenant: TenantContext = Depends(require_tenant)) -> Any:
    """Return only the structured result payload for a completed task."""
    if not task_id or not task_id.strip():
        raise HTTPException(status_code=400, detail="task_id is required")

    record = _resolve_store().get(task_id=task_id, tenant_id=tenant.tenant_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    if record.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
        raise HTTPException(status_code=404, detail="Task not yet complete.")
    if not record.result_data:
        return JSONResponse(status_code=204, content=None)

    return MissionResultResponse(
        task_id=record.task_id,
        goal=record.goal,
        result_schema=record.result_schema,
        result_data=record.result_data,
        completed_at=record.completed_at,
    )


@usage_router.patch("/tasks/{task_id}/result", response_model=MissionResultResponse)
def save_task_result(
    task_id: str, body: Dict[str, Any], tenant: TenantContext = Depends(require_tenant)
) -> MissionResultResponse:
    """Store structured result data on an existing task (called by orchestrator)."""
    if not task_id or not task_id.strip():
        raise HTTPException(status_code=400, detail="task_id is required")

    try:
        schema = body.pop("_result_schema", None)
        record = _resolve_store().save_result(
            task_id=task_id, tenant_id=tenant.tenant_id, data=body, schema=schema
        )
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    if record is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    return MissionResultResponse(
        task_id=record.task_id,
        goal=record.goal,
        result_schema=record.result_schema,
        result_data=record.result_data or {},
        completed_at=record.completed_at,
    )


@usage_router.get("/agents", response_model=List[AgentInfo])
def list_agents(tenant: TenantContext = Depends(require_tenant)) -> List[AgentInfo]:
    """List all agents registered in AGENT_REGISTRY."""
    from src.agents import registry

    agents: List[AgentInfo] = []
    for name in registry.list_agents():
        cls = registry.get(name)
        description = (cls.__doc__ or "").strip().splitlines()[0] if cls.__doc__ else name
        agents.append(AgentInfo(name=name, description=description))
    return agents


@usage_router.post("/agents/{name}/run", response_model=AgentRunResponse)
def run_agent(
    name: str, body: AgentRunRequest, tenant: TenantContext = Depends(require_tenant)
) -> AgentRunResponse:
    """Run a named agent directly with a goal."""
    if not name or not name.strip():
        raise HTTPException(
            status_code=400,
            detail=error_response(ErrorCode.INVALID_INPUT, "Agent name is required").to_dict(),
        )
    error = validate_required(body.goal, "goal")
    if error:
        raise HTTPException(status_code=400, detail=error.to_dict())

    from src.agents import registry

    if name not in registry:
        available = registry.list_agents()
        raise HTTPException(
            status_code=404,
            detail={"error": "NOT_FOUND", "message": f"Agent '{name}' not found", "available_agents": available},
        )
    try:
        agent = registry.get(name)()
        exec_result = agent.execute(agent.plan(body.goal))
        return AgentRunResponse(
            agent=name, status="success", output=str(exec_result) if exec_result is not None else ""
        )
    except TimeoutError:
        raise HTTPException(status_code=504, detail={"error": "TIMEOUT", "message": f"Agent '{name}' timed out"})
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": "AGENT_EXECUTION_ERROR", "message": f"Agent '{name}' failed: {str(exc)}"},
        ) from exc
