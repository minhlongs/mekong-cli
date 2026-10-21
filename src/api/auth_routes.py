# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Auth routes: license key → JWT + VN magic-link auth."""
from __future__ import annotations

import logging
import os

import jwt
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from engine.license.license_store import get_license_store
from src.api.auth_routes_helpers import (
    ACCESS_TOKEN_TTL_SECONDS,
    JWT_ALGORITHM,
    REFRESH_TOKEN_TTL_SECONDS,
    LoginRequest,
    LoginResponse,
    MagicLinkRequest,
    MagicLinkResponse,
    RefreshRequest,
    RefreshResponse,
    VerifyResponse,
    _EMAIL_RE,
    _MEKONG_PUBLIC_BASE_URL_DEFAULT,
    _issue_refresh_token,
    _issue_token,
    _jwt_secret,
    _send_magic_link_bg,
)
from src.services import magic_link_service, resend_client
from src.services.audit_logger import audit_admin_action

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])
vn_auth_router = APIRouter(prefix="/v1/auth", tags=["VN Magic-Link Auth"])


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest) -> LoginResponse:
    record = get_license_store().get(req.license_key)
    if not record:
        raise HTTPException(status_code=401, detail={"error": "invalid_license"})
    if record.get("status") != "active":
        raise HTTPException(status_code=402, detail={"error": "license_inactive"})

    tenant_id = record.get("customer_id")
    tier = record.get("tier", "starter")
    if not tenant_id:
        raise HTTPException(status_code=500, detail={"error": "license_missing_tenant"})

    token, ttl = _issue_token(tenant_id, req.license_key, tier)
    refresh_token, _ = _issue_refresh_token(tenant_id, req.license_key, tier)
    logger.info("auth.login_success", extra={"tenant_id": tenant_id, "tier": tier})
    return LoginResponse(
        access_token=token, refresh_token=refresh_token, expires_in=ttl,
        tenant_id=tenant_id, tier=tier,
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(req: RefreshRequest) -> RefreshResponse:
    try:
        claims = jwt.decode(req.refresh_token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail={"error": "token_expired"})
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail={"error": "invalid_token"})

    if claims.get("token_type") != "refresh":
        raise HTTPException(status_code=401, detail={"error": "invalid_token_type"})

    license_key = claims.get("license_key")
    tenant_id = claims.get("tenant_id")
    if not license_key or not tenant_id:
        raise HTTPException(status_code=401, detail={"error": "malformed_claims"})

    record = get_license_store().get(license_key)
    if not record:
        raise HTTPException(status_code=401, detail={"error": "invalid_license"})
    if record.get("status") != "active":
        raise HTTPException(status_code=402, detail={"error": "license_inactive"})

    current_tier = record.get("tier", claims.get("tier", "starter"))
    tenant_id = record.get("customer_id") or tenant_id

    new_access_token, ttl = _issue_token(tenant_id, license_key, current_tier)
    new_refresh_token, _ = _issue_refresh_token(tenant_id, license_key, current_tier)
    logger.info("auth.refresh_success", extra={"tenant_id": tenant_id, "tier": current_tier})
    return RefreshResponse(
        access_token=new_access_token, refresh_token=new_refresh_token,
        token_type="Bearer", expires_in=ttl, tenant_id=tenant_id, tier=current_tier,
    )


@vn_auth_router.post("/magic-link", response_model=MagicLinkResponse)
async def request_magic_link(
    req: MagicLinkRequest, background_tasks: BackgroundTasks
) -> MagicLinkResponse:
    """Mint a magic-link token and send email (enumeration-safe)."""
    ok_response = MagicLinkResponse(
        ok=True, message="Nếu email tồn tại, liên kết đăng nhập đã được gửi."
    )
    if not _EMAIL_RE.match(req.email):
        raise HTTPException(status_code=422, detail={"error": "invalid_email_format"})

    if not magic_link_service.check_rate_limit(req.email):
        logger.warning("magic_link.rate_limited", extra={"email": req.email})
        audit_admin_action(
            scope="magic_link.rate_limited", org="none", sub=req.email, endpoint="/v1/auth/magic-link"
        )
        return ok_response

    token = magic_link_service.mint_token(req.email, req.purpose)
    background_tasks.add_task(_send_magic_link_bg, req.email, token, req.purpose)
    audit_admin_action(
        scope="magic_link.minted", org="none", sub=req.email, endpoint="/v1/auth/magic-link"
    )
    return ok_response


@vn_auth_router.get("/verify", response_model=VerifyResponse)
async def verify_magic_link(
    token: str = Query(..., min_length=10, max_length=128),
) -> VerifyResponse:
    """Verify magic-link token and mint 24h JWT."""
    try:
        result = magic_link_service.verify_and_redeem(token)
    except (
        magic_link_service.MagicLinkInvalid,
        magic_link_service.MagicLinkExpired,
        magic_link_service.MagicLinkAlreadyRedeemed,
    ):
        raise HTTPException(status_code=401, detail={"error": "invalid_or_expired_link"})

    email, purpose = result["email"], result["purpose"]
    jwt_token, expires_at = magic_link_service.mint_jwt_for_email(email)

    try:
        claims = jwt.decode(jwt_token, os.getenv("MEKONG_JWT_SECRET", ""), algorithms=["HS256"])
    except Exception:
        claims = {}

    scopes = claims.get("scopes", ["none"])
    allowed_orgs = claims.get("allowed_orgs", [])
    audit_admin_action(
        scope="magic_link.verified", org=allowed_orgs[0] if allowed_orgs else "none",
        sub=email, endpoint="/v1/auth/verify",
    )
    logger.info("magic_link.verified", extra={"email": email, "purpose": purpose, "scopes": scopes})
    return VerifyResponse(
        ok=True, jwt=jwt_token, expires_at=expires_at, scopes=scopes, allowed_orgs=allowed_orgs
    )


__all__ = [
    "ACCESS_TOKEN_TTL_SECONDS", "JWT_ALGORITHM", "REFRESH_TOKEN_TTL_SECONDS",
    "LoginRequest", "LoginResponse", "MagicLinkRequest", "MagicLinkResponse",
    "RefreshRequest", "RefreshResponse", "VerifyResponse",
    "_EMAIL_RE", "_MEKONG_PUBLIC_BASE_URL_DEFAULT", "_issue_refresh_token",
    "_issue_token", "_jwt_secret", "_send_magic_link_bg",
    "login", "refresh", "request_magic_link", "resend_client", "router",
    "verify_magic_link", "vn_auth_router",
]
