"""Redis-backed job queue. Namespaced keys per user to prevent cross-tenant access."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import redis

TASK_QUEUE = "task_queue"


def job_key(user_id: str, job_id: str) -> str:
    return f"job:{user_id}:{job_id}"


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def enqueue_job(
    r: redis.Redis,
    *,
    job_id: str,
    user_id: str,
    prompt: str,
    webhook_url: str | None,
    ttl_seconds: int = 7 * 24 * 3600,
) -> dict[str, Any]:
    """Persist job metadata and push id onto the shared task queue."""
    created = now_iso()
    record = {
        "job_id": job_id,
        "user_id": user_id,
        "prompt": prompt,
        "webhook_url": webhook_url or "",
        "status": "queued",
        "created_at": created,
        "updated_at": created,
        "result": "",
        "error": "",
    }
    key = job_key(user_id, job_id)
    r.hset(key, mapping=record)
    r.expire(key, ttl_seconds)
    r.lpush(TASK_QUEUE, key)
    return record


def get_job(r: redis.Redis, user_id: str, job_id: str) -> dict[str, str] | None:
    data = r.hgetall(job_key(user_id, job_id))
    if not data:
        return None
    return _decode_mapping(data)


def list_jobs(r: redis.Redis, user_id: str, limit: int = 20) -> list[dict[str, str]]:
    pattern = f"job:{user_id}:*"
    jobs: list[dict[str, str]] = []
    for key in r.scan_iter(pattern, count=500):
        data = r.hgetall(key)
        if data:
            jobs.append(_decode_mapping(data))
    jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)
    return jobs[:limit]


def update_job_status(
    r: redis.Redis,
    user_id: str,
    job_id: str,
    *,
    status: str,
    result: str | None = None,
    error: str | None = None,
) -> None:
    updates: dict[str, str] = {"status": status, "updated_at": now_iso()}
    if result is not None:
        updates["result"] = result
    if error is not None:
        updates["error"] = error
    r.hset(job_key(user_id, job_id), mapping=updates)


def pop_job_key(r: redis.Redis, timeout: int = 5) -> str | None:
    """Blocking pop used by worker. Returns full key (`job:{user_id}:{job_id}`)."""
    result = r.brpop(TASK_QUEUE, timeout=timeout)
    if not result:
        return None
    _, key = result
    if isinstance(key, bytes):
        key = key.decode("utf-8")
    return key


def parse_job_key(key: str) -> tuple[str, str] | None:
    parts = key.split(":")
    if len(parts) != 3 or parts[0] != "job":
        return None
    return parts[1], parts[2]


def _decode_mapping(raw: dict[Any, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in raw.items():
        key = k.decode("utf-8") if isinstance(k, bytes) else str(k)
        val = v.decode("utf-8") if isinstance(v, bytes) else str(v)
        out[key] = val
    return out
