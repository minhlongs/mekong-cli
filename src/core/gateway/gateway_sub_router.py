# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Swarm, schedule, memory, and governance router for Mekong Gateway."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.core.event_bus import EventType, get_event_bus
from src.core.gateway.gateway_helpers import require_swarm_token
from src.core.gateway.models import (
    MemoryEntryInfo,
    MemoryStatsResponse,
    ScheduleAddRequest,
    ScheduleJobInfo,
    SwarmDispatchRequest,
    SwarmNodeInfo,
    SwarmRegisterRequest,
)
from src.core.memory_canonical import MemoryStore
from src.core.scheduler import Scheduler
from src.core.swarm import SwarmRegistry

sub_router = APIRouter()
swarm_registry = SwarmRegistry()
scheduler = Scheduler()
memory_store = MemoryStore()


@sub_router.post("/swarm/register")
def swarm_register(
    req: SwarmRegisterRequest,
    _auth: None = Depends(require_swarm_token),
) -> SwarmNodeInfo:
    node = swarm_registry.register_node(
        name=req.name, host=req.host, port=req.port, token=req.token,
    )
    now_iso = datetime.now().isoformat()
    return SwarmNodeInfo(
        id=node.id, name=node.name, host=node.host,
        port=node.port, token=req.token,
        registered_at=now_iso, last_seen=now_iso, status=node.status,
    )


@sub_router.get("/swarm/nodes")
def swarm_list_nodes(_auth: None = Depends(require_swarm_token)) -> list[SwarmNodeInfo]:
    swarm_registry.check_all_health(timeout=2.0)
    return [
        SwarmNodeInfo(
            id=n.id, name=n.name, host=n.host, port=n.port, token=n.token,
            registered_at=datetime.fromtimestamp(n.last_heartbeat).isoformat() if n.last_heartbeat > 0 else datetime.now().isoformat(),
            last_seen=datetime.fromtimestamp(n.last_heartbeat).isoformat() if n.last_heartbeat > 0 else "never",
            status=n.status,
        )
        for n in swarm_registry.list_nodes()
    ]


@sub_router.post("/swarm/dispatch")
def swarm_dispatch(
    req: SwarmDispatchRequest,
    _auth: None = Depends(require_swarm_token),
) -> Any:
    node = swarm_registry.get_node(req.node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    bus = get_event_bus()
    bus.emit(EventType.GOAL_STARTED, {"node_id": req.node_id, "goal": req.goal})
    result = swarm_registry.dispatch_goal(req.node_id, req.goal)
    bus.emit(EventType.GOAL_COMPLETED, {"node_id": req.node_id, "result": result})
    return result


@sub_router.delete("/swarm/nodes/{node_id}")
def swarm_remove_node(
    node_id: str,
    _auth: None = Depends(require_swarm_token),
) -> dict[str, str]:
    removed = swarm_registry.remove_node(node_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"status": "removed", "node_id": node_id}


@sub_router.get("/memory/recent")
def memory_recent(limit: int = 20) -> list[MemoryEntryInfo]:
    entries = memory_store.recent(limit)
    return [
        MemoryEntryInfo(
            goal=e.goal, status=e.status, timestamp=e.timestamp,
            duration_ms=e.duration_ms, error_summary=e.error_summary,
            recipe_used=e.recipe_used,
        )
        for e in entries
    ]


@sub_router.get("/memory/stats")
def memory_stats() -> MemoryStatsResponse:
    return MemoryStatsResponse(**memory_store.stats())


@sub_router.get("/memory/search")
def memory_search(q: str = "") -> list[MemoryEntryInfo]:
    entries = memory_store.query(q) if q else memory_store.recent()
    return [
        MemoryEntryInfo(
            goal=e.goal, status=e.status, timestamp=e.timestamp,
            duration_ms=e.duration_ms, error_summary=e.error_summary,
            recipe_used=e.recipe_used,
        )
        for e in entries
    ]


@sub_router.post("/schedule/jobs")
def schedule_add_job(req: ScheduleAddRequest) -> ScheduleJobInfo:
    job = scheduler.add_job(
        name=req.name, goal=req.goal, job_type=req.job_type,
        interval_seconds=req.interval_seconds, daily_time=req.daily_time,
    )
    return ScheduleJobInfo(
        id=job.id, name=job.name, goal=job.goal, job_type=job.job_type,
        interval_seconds=job.interval_seconds, daily_time=job.daily_time,
        enabled=job.enabled, last_run=job.last_run, next_run=job.next_run,
        run_count=job.run_count,
    )


@sub_router.get("/schedule/jobs")
def schedule_list_jobs() -> list[ScheduleJobInfo]:
    return [
        ScheduleJobInfo(
            id=j.id, name=j.name, goal=j.goal, job_type=j.job_type,
            interval_seconds=j.interval_seconds, daily_time=j.daily_time,
            enabled=j.enabled, last_run=j.last_run, next_run=j.next_run,
            run_count=j.run_count,
        )
        for j in scheduler.list_jobs()
    ]


@sub_router.delete("/schedule/jobs/{job_id}")
def schedule_remove_job(job_id: str) -> dict[str, str]:
    if not scheduler.remove_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": "removed", "job_id": job_id}


__all__ = ["memory_store", "scheduler", "sub_router", "swarm_registry"]
