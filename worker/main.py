"""Worker — processes jobs from Redis queue with per-user isolation.

In single-server (seed) mode: runs seed/main.py directly in-process.
In Forest mode: spawns isolated subprocess per user via Docker.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s [worker] %(message)s")
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
QUEUE_KEY = "mekong:tasks"
USE_DOCKER = os.getenv("USE_DOCKER", "false").lower() == "true"
REPO_ROOT = Path(__file__).resolve().parent.parent


def _run_in_process(job: dict) -> dict:
    """Direct in-process execution (seed/single-tenant mode)."""
    from seed.main import run as seed_run
    result = seed_run(job["task"])
    return result


def _run_in_docker(job: dict) -> dict:
    """Spawn isolated Docker container per job (forest/multi-tenant mode)."""
    user_id = job.get("user", "anon")
    container_name = f"mekong-worker-{user_id}-{uuid.uuid4().hex[:6]}"
    cmd = [
        "docker", "run", "--rm",
        "--name", container_name,
        "-v", f"{REPO_ROOT}:/app",
        "-w", "/app",
        "-e", f"USER_ID={user_id}",
        "python:3.11-slim",
        "python3", "seed/main.py", job["task"],
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return {
            "outputs": [result.stdout.strip()],
            "stderr": result.stderr,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"outputs": [], "error": "Container timeout after 300s"}
    except Exception as e:
        return {"outputs": [], "error": str(e)}


def process_job(job: dict) -> dict:
    """Route to docker or in-process depending on USE_DOCKER flag."""
    logger.info("Processing job %s for user %s", job.get("id"), job.get("user"))
    if USE_DOCKER:
        return _run_in_docker(job)
    return _run_in_process(job)


def poll_redis() -> None:
    """Long-poll Redis queue for jobs (BLPOP pattern)."""
    try:
        import redis
        r = redis.from_url(REDIS_URL)
        logger.info("Worker connected to Redis. Waiting for jobs...")
        while True:
            item = r.blpop(QUEUE_KEY, timeout=5)
            if item:
                _, raw = item
                job = json.loads(raw)
                result = process_job(job)
                status_key = f"mekong:job:{job['id']}:result"
                r.setex(status_key, 3600, json.dumps(result))
    except ImportError:
        logger.warning("redis-py not installed. Running in stdin mode.")
        _stdin_mode()
    except Exception as e:
        logger.error("Redis error: %s", e)


def _stdin_mode() -> None:
    """Fallback: read JSON job from stdin, print result to stdout."""
    logger.info("Worker stdin mode. Paste JSON job and press Enter.")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            job = json.loads(line)
            result = process_job(job)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"error": str(e)}))


if __name__ == "__main__":
    poll_redis()
