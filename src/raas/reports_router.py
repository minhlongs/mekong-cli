# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Serve OpenClaw daemon reports via API.

Reports sit in ~/mekong-cli/content/openclaw-reports/ — this makes them
accessible via https://api.cashclaw.cc/raas/reports so the world can see
what the autonomous daemon produces. Transparency = trust.
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/raas", tags=["Reports"])

_REPORTS_DIR = Path.home() / "mekong-cli" / "content" / "openclaw-reports"

# Simple in-memory rate limiter: 30 requests per minute per IP
_RATE_LIMIT = 30
_RATE_WINDOW = 60
_rate_store: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(request: Request) -> None:
    """Raise 429 if client exceeds rate limit."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - _RATE_WINDOW
    hits = _rate_store[client_ip]
    _rate_store[client_ip] = [t for t in hits if t > window_start]
    if len(_rate_store[client_ip]) >= _RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    _rate_store[client_ip].append(now)


class ReportSummary(BaseModel):
    filename: str
    department: str
    date: str
    size_bytes: int


class ReportDetail(BaseModel):
    filename: str
    content: str
    department: str
    date: str


@router.get("/reports", response_model=List[ReportSummary])
def list_reports(request: Request, limit: int = 20, dept: str | None = None):
    """List recent daemon reports, newest first."""
    _check_rate_limit(request)
    if not _REPORTS_DIR.exists():
        return []

    files = sorted(_REPORTS_DIR.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)

    results = []
    for f in files[:limit * 2]:  # overfetch then filter
        parts = f.stem.split("-")
        department = parts[2] if len(parts) > 2 else "unknown"
        date = parts[0] if parts else ""

        if dept and department != dept:
            continue

        results.append(ReportSummary(
            filename=f.name,
            department=department,
            date=date,
            size_bytes=f.stat().st_size,
        ))

        if len(results) >= limit:
            break

    return results


@router.get("/reports/stats")
def report_stats(request: Request):
    """Daemon activity stats. MUST be declared before /reports/{filename}."""
    _check_rate_limit(request)
    if not _REPORTS_DIR.exists():
        return {"total": 0, "departments": {}}

    files = list(_REPORTS_DIR.glob("*.md"))
    depts: dict[str, int] = {}
    for f in files:
        parts = f.stem.split("-")
        dept = parts[2] if len(parts) > 2 else "unknown"
        depts[dept] = depts.get(dept, 0) + 1

    return {
        "total": len(files),
        "departments": depts,
        "latest": sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)[0].name if files else None,
    }


@router.get("/reports/{filename}")
def get_report(request: Request, filename: str):
    """Get full report content by filename."""
    _check_rate_limit(request)
    # Security: prevent path traversal BEFORE constructing path
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    filepath = _REPORTS_DIR / filename
    resolved = filepath.resolve()
    if not resolved.is_relative_to(_REPORTS_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not filepath.exists() or filepath.suffix != ".md":
        raise HTTPException(status_code=404, detail="Report not found")

    parts = filepath.stem.split("-")
    return ReportDetail(
        filename=filepath.name,
        content=filepath.read_text(),
        department=parts[2] if len(parts) > 2 else "unknown",
        date=parts[0] if parts else "",
    )
