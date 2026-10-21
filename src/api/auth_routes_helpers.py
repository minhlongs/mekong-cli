# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Auth route models, constants, and JWT/magic-link helpers."""
from __future__ import annotations

import logging
import os
import re
import sys
import time
from typing import Optional

import jwt
from pydantic import BaseModel, Field

from src.services import resend_client
from src.services.audit_logger import audit_admin_action

logger = logging.getLogger(__name__)

ACCESS_TOKEN_TTL_SECONDS = 60 * 60  # 1 hour
REFRESH_TOKEN_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days
JWT_ALGORITHM = "HS256"

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MEKONG_PUBLIC_BASE_URL_DEFAULT = "https://api.mekong.dev"


class LoginRequest(BaseModel):
    license_key: str = Field(..., min_length=8, max_length=512)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int
    tenant_id: str
    tier: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10, max_length=1024)


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    tenant_id: str
    tier: str


class MagicLinkRequest(BaseModel):
    email: str = Field(..., max_length=320)
    purpose: str = Field(default="login", max_length=32)


class MagicLinkResponse(BaseModel):
    ok: bool
    message: str


class VerifyResponse(BaseModel):
    ok: bool
    jwt: str
    expires_at: str
    scopes: list[str]
    allowed_orgs: list[str]


def _jwt_secret() -> str:
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("CI"):
            return "dev-test-secret-only"
        raise RuntimeError("JWT_SECRET env var is required")
    return secret


def _issue_token(tenant_id: str, license_key: str, tier: str) -> tuple[str, int]:
    now = int(time.time())
    exp = now + ACCESS_TOKEN_TTL_SECONDS
    payload = {
        "tenant_id": tenant_id,
        "license_key": license_key,
        "tier": tier,
        "token_type": "access",
        "iat": now,
        "exp": exp,
    }
    token = jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)
    return token, ACCESS_TOKEN_TTL_SECONDS


def _issue_refresh_token(tenant_id: str, license_key: str, tier: str) -> tuple[str, int]:
    now = int(time.time())
    exp = now + REFRESH_TOKEN_TTL_SECONDS
    payload = {
        "tenant_id": tenant_id,
        "license_key": license_key,
        "tier": tier,
        "token_type": "refresh",
        "iat": now,
        "exp": exp,
    }
    token = jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)
    return token, REFRESH_TOKEN_TTL_SECONDS


def _send_magic_link_bg(email: str, token: str, purpose: str) -> None:
    """Background task: send magic-link email via Resend. Never raises."""
    base_url = os.getenv("MEKONG_PUBLIC_BASE_URL", _MEKONG_PUBLIC_BASE_URL_DEFAULT)
    magic_url = f"{base_url}/v1/auth/verify?token={token}"
    try:
        resend_client.send_magic_link_email(email, magic_url, purpose)
        audit_admin_action(
            scope="magic_link.sent",
            org="none",
            sub=email,
            endpoint="/v1/auth/magic-link",
        )
        logger.info("magic_link.sent", extra={"email": email, "purpose": purpose})
    except Exception as exc:
        logger.error(
            "magic_link.send_failed",
            extra={"email": email, "purpose": purpose, "error": str(exc)},
        )
        print(
            f"[magic_link] WARN: email send failed for {email}: {exc}",
            file=sys.stderr,
        )
