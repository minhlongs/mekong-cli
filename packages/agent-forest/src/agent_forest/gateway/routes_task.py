"""Task endpoints: enqueue job, fetch status, list jobs."""

from __future__ import annotations

import uuid

import redis
from fastapi import APIRouter, Depends, HTTPException, Query, status

from agent_forest import queue as q
from agent_forest.gateway.deps import current_user, get_redis_client
from agent_forest.models import (
    FeedbackAccepted,
    FeedbackRequest,
    JobRecord,
    TaskEnqueued,
    TaskRequest,
)
from agent_forest.users import User
from agent_forest.webhook import WebhookRejected, validate_webhook_url
from agent_forest.worker.signals import emit_user_feedback

router = APIRouter(tags=["tasks"])


@router.post("/task", response_model=TaskEnqueued, status_code=status.HTTP_202_ACCEPTED)
def create_task(
    body: TaskRequest,
    user: User = Depends(current_user),
    r: redis.Redis = Depends(get_redis_client),
) -> TaskEnqueued:
    if body.webhook_url:
        try:
            validate_webhook_url(body.webhook_url)
        except WebhookRejected as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid webhook_url: {exc}",
            ) from exc
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    record = q.enqueue_job(
        r,
        job_id=job_id,
        user_id=user.user_id,
        prompt=body.prompt,
        webhook_url=body.webhook_url,
    )
    return TaskEnqueued(
        job_id=job_id, status=record["status"], created_at=record["created_at"]
    )


@router.get("/task/{job_id}", response_model=JobRecord)
def get_task(
    job_id: str,
    user: User = Depends(current_user),
    r: redis.Redis = Depends(get_redis_client),
) -> JobRecord:
    data = q.get_job(r, user.user_id, job_id)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobRecord(**_as_job_kwargs(data))


@router.get("/tasks", response_model=list[JobRecord])
def list_tasks(
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(current_user),
    r: redis.Redis = Depends(get_redis_client),
) -> list[JobRecord]:
    jobs = q.list_jobs(r, user.user_id, limit=limit)
    return [JobRecord(**_as_job_kwargs(j)) for j in jobs]


@router.post(
    "/task/{job_id}/feedback",
    response_model=FeedbackAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def submit_feedback(
    job_id: str,
    body: FeedbackRequest,
    user: User = Depends(current_user),
    r: redis.Redis = Depends(get_redis_client),
) -> FeedbackAccepted:
    """Record user rating for a completed job — forwards to mekongd signals."""
    data = q.get_job(r, user.user_id, job_id)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    forwarded = emit_user_feedback(
        body.rating, user.user_id, job_id, note=body.note
    )
    return FeedbackAccepted(job_id=job_id, rating=body.rating, forwarded=forwarded)


def _as_job_kwargs(data: dict[str, str]) -> dict[str, object]:
    return {
        "job_id": data.get("job_id", ""),
        "user_id": data.get("user_id", ""),
        "prompt": data.get("prompt", ""),
        "status": data.get("status", ""),
        "created_at": data.get("created_at", ""),
        "updated_at": data.get("updated_at", ""),
        "webhook_url": data.get("webhook_url") or None,
        "result": data.get("result") or None,
        "error": data.get("error") or None,
    }
