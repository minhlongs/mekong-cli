"""License gate FastAPI dependency.

Verifies JWT, checks license is active, and ensures non-zero MCU balance
before any mission endpoint executes.

Returns the resolved tenant_id and stores it on `request.state` for handlers.

Failure modes:
  HTTP 401 — missing or invalid JWT
  HTTP 402 — license inactive or zero credit balance
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import jwt
from fastapi import HTTPException, Request

from src.lib.license_store import get_license_store
from src.raas.credits import CreditStore

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"


def _jwt_secret() -> str:
    secret = os.environ.get("JWT_SECRET=REDACTED")
    if not secret:
        if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("CI"):
            return "dev-test-secret-only"
        raise RuntimeError("JWT_SECRET=REDACTED env var is required")
    return secret


def _recharge_url() -> str:
    return os.environ.get("RECHARGE_URL", "https://www.mekongmind.com/billing")


def _extract_bearer(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return None


async def license_gate(request: Request) -> str:
    """FastAPI dependency. Returns tenant_id on success."""
    token = _extract_bearer(request)
    if not token:
        raise HTTPException(status_code=401, detail={"error": "missing_token"})

    try:
        claims = jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail={"error": "token_expired"})
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail={"error": "invalid_token"})

    tenant_id = claims.get("tenant_id")
    license_key = claims.get("license_key")
    if not tenant_id or not license_key:
        raise HTTPException(status_code=401, detail={"error": "malformed_claims"})

    store = get_license_store()
    if not store.is_active(license_key):
        raise HTTPException(
            status_code=402,
            detail={"error": "license_inactive", "recharge_url": _recharge_url()},
        )

    credits = CreditStore()
    if credits.get_balance(tenant_id) <= 0:
        raise HTTPException(
            status_code=402,
            detail={"error": "no_credits", "recharge_url": _recharge_url()},
        )

    request.state.tenant_id = tenant_id
    request.state.license_key = license_key
    return tenant_id
