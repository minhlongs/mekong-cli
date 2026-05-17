"""Auth routes: license key → JWT.

POST /auth/login   {license_key} → {access_token, expires_in, tenant_id, tier}
POST /auth/refresh {refresh_token} → new access_token (TODO: refresh impl)

The IDE consumes /auth/login to obtain a short-lived JWT for subsequent
mission requests gated by `license_gate`.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Optional

import jwt
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.lib.license_store import get_license_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

ACCESS_TOKEN_TTL_SECONDS = 60 * 60  # 1 hour
JWT_ALGORITHM = "HS256"


class LoginRequest(BaseModel):
    license_key: str = Field(..., min_length=8, max_length=512)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    tenant_id: str
    tier: str


def _jwt_secret() -> str:
    secret = os.environ.get("JWT_SECRET=REDACTED")
    if not secret:
        if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("CI"):
            return "dev-test-secret-only"
        raise RuntimeError("JWT_SECRET=REDACTED env var is required")
    return secret


def _issue_token(tenant_id: str, license_key: str, tier: str) -> tuple[str, int]:
    now = int(time.time())
    exp = now + ACCESS_TOKEN_TTL_SECONDS
    payload = {
        "tenant_id": tenant_id,
        "license_key": license_key,
        "tier": tier,
        "iat": now,
        "exp": exp,
    }
    token = jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)
    return token, ACCESS_TOKEN_TTL_SECONDS


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest) -> LoginResponse:
    store = get_license_store()
    record = store.get(req.license_key)
    if not record:
        raise HTTPException(status_code=401, detail={"error": "invalid_license"})

    if record.get("status") != "active":
        raise HTTPException(status_code=402, detail={"error": "license_inactive"})

    tenant_id = record.get("customer_id")
    tier = record.get("tier", "starter")
    if not tenant_id:
        raise HTTPException(status_code=500, detail={"error": "license_missing_tenant"})

    token, ttl = _issue_token(tenant_id, req.license_key, tier)
    logger.info("auth.login_success", extra={"tenant_id": tenant_id, "tier": tier})
    return LoginResponse(
        access_token=token, expires_in=ttl, tenant_id=tenant_id, tier=tier
    )
