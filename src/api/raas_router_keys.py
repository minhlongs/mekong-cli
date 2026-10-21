# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Task submission, status polling, and SSE streaming handlers for RaaS API."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from src.api.raas_router_models import (
    ErrorCode, TaskRequest, TaskResponse, TaskStatus, TaskStatusResponse, TenantContext,
    _build_orchestrator, _facade, _result_to_record, error_response, get_task_store,
    require_tenant, validate_required, validate_string_length,
)

logger = logging.getLogger(__name__)
tasks_router = APIRouter()


def _resolve_store() -> Any:
    facade = _facade()
    return (getattr(facade, "get_task_store", get_task_store) if facade else get_task_store)()


def _resolve_orchestrator() -> Any:
    facade = _facade()
    return (getattr(facade, "_build_orchestrator", _build_orchestrator) if facade else _build_orchestrator)()


def _resolve_result_to_record(record: Any, result: Any) -> Any:
    facade = _facade()
    fn = getattr(facade, "_result_to_record", _result_to_record) if facade else _result_to_record
    return fn(record, result)


@tasks_router.post("/tasks", response_model=TaskResponse, status_code=202)
def submit_task(body: TaskRequest, tenant: TenantContext = Depends(require_tenant)) -> TaskResponse:
    """Submit a goal for execution and return a task_id for polling."""
    error = validate_required(body.goal, "goal") or validate_string_length(
        body.goal, "goal", min_len=1, max_len=10000
    )
    if error:
        raise HTTPException(status_code=400, detail=error.to_dict())

    store = _resolve_store()
    try:
        record = store.create(goal=body.goal, tenant_id=tenant.tenant_id)
        record.status = TaskStatus.RUNNING
        store.update(record)
        result = _resolve_orchestrator().run_from_goal(body.goal)
        record = _resolve_result_to_record(record, result)
    except ValueError as e:
        record = store.create(goal=body.goal, tenant_id=tenant.tenant_id)
        record.status = TaskStatus.FAILED
        record.errors.append(f"validation_error: {e}")
    except Exception as exc:
        record = store.create(goal=body.goal, tenant_id=tenant.tenant_id)
        record.status = TaskStatus.FAILED
        record.errors.append(f"execution_failed: {str(exc)}")

    store.update(record)
    return TaskResponse(task_id=record.task_id, status=record.status, tenant_id=tenant.tenant_id)


@tasks_router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str, tenant: TenantContext = Depends(require_tenant)) -> TaskStatusResponse:
    """Poll full status and result for a previously submitted task."""
    if not task_id or not task_id.strip():
        raise HTTPException(
            status_code=400,
            detail=error_response(ErrorCode.INVALID_INPUT, "Task ID is required and cannot be empty").to_dict(),
        )
    try:
        record = _resolve_store().get(task_id=task_id, tenant_id=tenant.tenant_id)
        if record is None:
            raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
        return TaskStatusResponse(
            task_id=record.task_id, status=record.status, goal=record.goal, tenant_id=record.tenant_id,
            total_steps=record.total_steps, completed_steps=record.completed_steps,
            failed_steps=record.failed_steps, success_rate=record.success_rate,
            errors=record.errors, warnings=record.warnings, steps=record.steps,
            result_data=record.result_data, result_schema=record.result_schema,
            completed_at=record.completed_at,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail={"error": "INTERNAL_ERROR", "message": "Failed to get task status"}
        ) from exc


@tasks_router.get("/tasks/{task_id}/stream")
async def stream_task(task_id: str, tenant: TenantContext = Depends(require_tenant)) -> StreamingResponse:
    """Stream task execution progress as Server-Sent Events (SSE)."""
    if not task_id or not task_id.strip():
        raise HTTPException(
            status_code=400,
            detail=error_response(ErrorCode.INVALID_INPUT, "Task ID is required and cannot be empty").to_dict(),
        )

    store = _resolve_store()
    record = store.get(task_id=task_id, tenant_id=tenant.tenant_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    async def _event_stream() -> AsyncGenerator[str, None]:
        queue: asyncio.Queue[Dict] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def _on_step(step_result: Any, current: Any) -> None:
            asyncio.run_coroutine_threadsafe(
                queue.put({
                    "type": "step", "order": step_result.step.order, "title": step_result.step.title,
                    "passed": step_result.verification.passed, "exit_code": step_result.execution.exit_code,
                    "summary": step_result.verification.summary, "completed": current.completed_steps,
                    "total": current.total_steps,
                }),
                loop,
            )

        future = loop.run_in_executor(
            None, lambda: _resolve_orchestrator().run_from_goal(record.goal, progress_callback=_on_step)
        )
        while not future.done():
            try:
                event = await asyncio.wait_for(queue.get(), timeout=0.5)
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                continue

        while not queue.empty():
            yield f"data: {json.dumps(queue.get_nowait())}\n\n"

        try:
            record_updated = _resolve_result_to_record(record, future.result())
            store.update(record_updated)
            done_event = {
                "type": "complete", "status": record_updated.status.value,
                "success_rate": record_updated.success_rate, "errors": record_updated.errors,
            }
        except Exception as exc:
            done_event = {"type": "error", "message": str(exc)}
        yield f"data: {json.dumps(done_event)}\n\n"

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

