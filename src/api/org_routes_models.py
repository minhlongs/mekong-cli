# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Pydantic models and JWT auth helpers for VN Org routes."""

from __future__ import annotations

import os
import sys
from typing import Any, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from src.api.vn_pilot_auth import _require_scope
from src.services import magic_link_service
from src.services.admin_token_service import JWTExpiredError, JWTInvalidError, decode_jwt


def _facade() -> Any:
    """Return the parent org_routes module if loaded."""
    return sys.modules.get("src.api.org_routes")


class OrgCreateRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=120)


class OrgCreateResponse(BaseModel):
    org_id: str
    user_id: str
    jwt: str
    expires_at: str
    status: str
    trial_expires_at: str


class OrgMemberOut(BaseModel):
    user_id: str
    email: str
    scope: str
    joined_at: str


class OrgMeResponse(BaseModel):
    org_id: str
    display_name: str
    status: str
    trial_expires_at: str
    platform_fee_paid_until: Optional[str]
    created_at: str
    created_by_email: str
    member_count: int
    members: list[OrgMemberOut]


class InviteCreateRequest(BaseModel):
    invitee_email: str = Field(..., min_length=3, max_length=254)
    scope: str = Field(default="readonly")


class InviteCreateResponse(BaseModel):
    invite_id: str
    expires_at: str


class JoinRequest(BaseModel):
    pass


class JoinResponse(BaseModel):
    org_id: str
    user_id: str
    scope: str
    jwt: str
    expires_at: str


class InviteOut(BaseModel):
    invite_id: str
    invitee_email: str
    scope: str
    expires_at: str
    created_at: str


def _extract_email_from_jwt(authorization: Optional[str]) -> str:
    """Decode bearer JWT and return sub (email) claim."""
    jwt_secret = os.environ.get("MEKONG_JWT_SECRET")
    if not jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT auth disabled — MEKONG_JWT_SECRET not set",
        )
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing 'Authorization: Bearer <token>' header",
        )
    raw_token = authorization[len("Bearer "):].strip()

    facade = _facade()
    decode_fn = getattr(facade, "decode_jwt", decode_jwt) if facade else decode_jwt
    try:
        claims = decode_fn(raw_token, jwt_secret)
    except JWTExpiredError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except JWTInvalidError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    email = claims.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT missing sub claim")
    return email


__all__ = [
    "InviteCreateRequest",
    "InviteCreateResponse",
    "InviteOut",
    "JoinRequest",
    "JoinResponse",
    "JWTExpiredError",
    "JWTInvalidError",
    "OrgCreateRequest",
    "OrgCreateResponse",
    "OrgMeResponse",
    "OrgMemberOut",
    "_extract_email_from_jwt",
    "_facade",
    "_require_scope",
    "decode_jwt",
    "magic_link_service",
]
