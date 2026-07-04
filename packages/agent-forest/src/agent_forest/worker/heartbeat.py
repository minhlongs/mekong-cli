"""Worker heartbeat — publish liveness to Redis with TTL-based auto-expiry.

Each worker process writes `workers:heartbeat:<id> <unix_ts>` with EX=ttl.
The gateway counts matching keys at /metrics scrape time. Dead workers
drop off naturally once their TTL lapses.
"""

from __future__ import annotations

import os
import socket
import time
from collections.abc import Iterable

import redis

_KEY_PREFIX = "workers:heartbeat:"
_DEFAULT_TTL_SECONDS = 60


def default_worker_id() -> str:
    """Stable-per-process worker ID: hostname-pid. Override via env AGENT_FOREST_WORKER_ID."""
    override = os.getenv("AGENT_FOREST_WORKER_ID", "")
    if override:
        return override
    return f"{socket.gethostname()}-{os.getpid()}"


def publish(r: redis.Redis, worker_id: str, ttl_seconds: int = _DEFAULT_TTL_SECONDS) -> None:
    """Upsert heartbeat key `workers:heartbeat:<id>` with current UTC timestamp + TTL."""
    r.setex(f"{_KEY_PREFIX}{worker_id}", ttl_seconds, int(time.time()))


def iter_heartbeat_keys(r: redis.Redis) -> Iterable[str]:
    """Non-blocking SCAN over heartbeat keyspace."""
    return r.scan_iter(match=f"{_KEY_PREFIX}*")


def count_alive(r: redis.Redis) -> int:
    """Count currently-alive workers (keys with live TTL)."""
    return sum(1 for _ in iter_heartbeat_keys(r))


def last_seen_timestamp(r: redis.Redis) -> int:
    """Max heartbeat timestamp across all alive workers. 0 when no workers."""
    latest = 0
    for key in iter_heartbeat_keys(r):
        raw = r.get(key)
        if raw is None:
            continue
        try:
            ts = int(raw)
        except (TypeError, ValueError):
            continue
        if ts > latest:
            latest = ts
    return latest
