"""Multi-tenant FastAPI gateway — JWT auth + Redis queue + per-user isolation."""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from fastapi import Depends, FastAPI, Form, HTTPException, Header
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    print("Install: pip install fastapi uvicorn")
    sys.exit(1)

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "mekong-seed-secret-change-in-prod")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

app = FastAPI(title="Mekong Gateway", version="2.0.0")

# In-memory job store (replace with Redis in prod)
_jobs: dict[str, dict] = {}
_users: dict[str, str] = {"admin": "admin123"}  # username → password (demo only)
_tokens: dict[str, str] = {}  # token → username


def _create_token(username: str) -> str:
    token = str(uuid.uuid4())
    _tokens[token] = username
    return token


def _get_current_user(authorization: str = Header(default="")) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization[7:]
    user = _tokens.get(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def _check_credits(user: str) -> None:
    """Billing gate: raise 402 if user has no credits (stub for Polar.sh integration)."""
    # TODO: integrate with Polar.sh webhook credit tracking
    pass


@app.post("/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if _users.get(username) != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = _create_token(username)
    return {"token": token, "username": username}


@app.post("/task")
async def submit_task(
    task: str = Form(...),
    current_user: str = Depends(_get_current_user),
):
    _check_credits(current_user)
    job_id = str(uuid.uuid4())[:8]
    _jobs[job_id] = {
        "id": job_id,
        "user": current_user,
        "task": task,
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "outputs": [],
    }
    # Dispatch to worker (async — fire and forget in single-server mode)
    from threading import Thread
    Thread(target=_process_job, args=(job_id,), daemon=True).start()
    return {"job_id": job_id, "status": "queued"}


def _process_job(job_id: str) -> None:
    job = _jobs.get(job_id)
    if not job:
        return
    job["status"] = "running"
    try:
        from seed.main import run as seed_run
        result = seed_run(job["task"])
        job["outputs"] = result.get("outputs", [])
        job["test_result"] = result.get("test_result", {})
        job["status"] = "completed"
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        logger.error("Job %s failed: %s", job_id, e)


@app.get("/task/{job_id}")
async def get_task(job_id: str, current_user: str = Depends(_get_current_user)):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["user"] != current_user:
        raise HTTPException(status_code=403, detail="Access denied")
    return job


@app.get("/health")
async def health():
    return {"status": "ok", "jobs": len(_jobs)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8766, reload=False)
