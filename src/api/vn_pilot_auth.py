"""VN Pilot — admin token auth dependency."""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Header, HTTPException, status


def _require_admin_token(authorization: Optional[str] = Header(default=None)) -> None:
    """Bearer-token gate for founder-only admin endpoints.

    Reads MEKONG_ADMIN_TOKEN at request time (so launchctl setenv updates
    take effect without code reload — useful for token rotation).

    - 503: env var not configured
    - 401: missing or malformed Authorization header
    - 403: token mismatch
    """
    expected = os.environ.get("MEKONG_ADMIN_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin endpoints disabled — MEKONG_ADMIN_TOKEN not set on gateway",
        )
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing 'Authorization: Bearer <token>' header",
        )
    received = authorization[len("Bearer "):].strip()
    if received != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token",
        )
