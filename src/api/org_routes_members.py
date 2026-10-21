# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Org creation, summary, and member removal endpoints for VN Org routes."""

from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status

from src.api.org_routes_models import (
    JWTExpiredError,
    JWTInvalidError,
    OrgCreateRequest,
    OrgCreateResponse,
    OrgMeResponse,
    _extract_email_from_jwt,
    _facade,
    _require_scope,
    decode_jwt,
    magic_link_service,
)
from src.services.org_service import (
    InvalidSlugError,
    LastAdminError,
    MemberNotFoundError,
    OrgNotFoundError,
    ReservedSlugError,
    SlugCollisionError,
    create_org,
    get_org_summary,
    remove_member,
)

logger = logging.getLogger(__name__)
members_router = APIRouter()


@members_router.post("/create", response_model=OrgCreateResponse, status_code=201)
async def create_org_endpoint(
    req: OrgCreateRequest,
    authorization: Optional[str] = Header(default=None),
) -> OrgCreateResponse:
    """Create a new org. Caller becomes first org_admin."""
    facade = _facade()
    extract_fn = getattr(facade, "_extract_email_from_jwt", _extract_email_from_jwt) if facade else _extract_email_from_jwt
    create_org_fn = getattr(facade, "create_org", create_org) if facade else create_org
    mls = getattr(facade, "magic_link_service", magic_link_service) if facade else magic_link_service

    founder_email = extract_fn(authorization)

    try:
        result = create_org_fn(req.display_name, founder_email)
    except ReservedSlugError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "slug_reserved"})
    except SlugCollisionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "slug_collision", "suggestions": exc.suggestions},
        )
    except InvalidSlugError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_slug", "message": str(exc)},
        )

    try:
        new_jwt, expires_at = mls.mint_jwt_for_email(founder_email)
    except RuntimeError as exc:
        logger.error("org.create_jwt_remint_failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "jwt_remint_failed", "message": str(exc)},
        )

    logger.info("org.created", extra={"org_id": result["org_id"], "founder": founder_email})
    return OrgCreateResponse(
        org_id=result["org_id"],
        user_id=result["user_id"],
        jwt=new_jwt,
        expires_at=expires_at,
        status=result["status"],
        trial_expires_at=result["trial_expires_at"],
    )


@members_router.get("/me", response_model=OrgMeResponse)
async def get_org_me(
    request: Request,
    org_id: Optional[str] = Query(default=None),
    authorization: Optional[str] = Header(default=None),
) -> OrgMeResponse:
    """Return the requester's org context (org details + member list)."""
    jwt_secret = os.environ.get("MEKONG_JWT_SECRET")
    if not jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth disabled — MEKONG_JWT_SECRET not configured",
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing 'Authorization: Bearer <token>' header",
        )
    raw_token = authorization[len("Bearer "):].strip()

    facade = _facade()
    decode_fn = getattr(facade, "decode_jwt", decode_jwt) if facade else decode_jwt
    summary_fn = getattr(facade, "get_org_summary", get_org_summary) if facade else get_org_summary

    try:
        claims = decode_fn(raw_token, jwt_secret)
    except JWTExpiredError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except JWTInvalidError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    allowed_orgs: list[str] = claims.get("allowed_orgs", [])
    is_legacy = not allowed_orgs

    resolved_org_id = org_id
    if resolved_org_id is None:
        if is_legacy or len(allowed_orgs) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "org_id_required"})
        if len(allowed_orgs) == 1:
            resolved_org_id = allowed_orgs[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "multi_org_jwt_specify_org_id"},
            )

    if not is_legacy and resolved_org_id not in allowed_orgs:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "org_not_in_allowed_orgs"})

    try:
        summary = summary_fn(resolved_org_id)
    except OrgNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "org_not_found"})

    return OrgMeResponse(**summary)


@members_router.delete(
    "/members/{user_id}",
    status_code=204,
    response_class=Response,
    response_model=None,
    dependencies=[Depends(_require_scope(["org_admin", "founder"]))],
)
async def delete_org_member(
    user_id: str,
    authorization: Optional[str] = Header(default=None),
    org_id: Optional[str] = Query(default=None),
) -> None:
    """Remove a member from an org. Cannot remove last org_admin."""
    facade = _facade()
    extract_fn = getattr(facade, "_extract_email_from_jwt", _extract_email_from_jwt) if facade else _extract_email_from_jwt
    remove_fn = getattr(facade, "remove_member", remove_member) if facade else remove_member

    actor_email = extract_fn(authorization)
    if not org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "org_id_required"})

    try:
        remove_fn(org_id, user_id, actor_email)
    except OrgNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "org_not_found"})
    except MemberNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "member_not_found"})
    except LastAdminError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "last_admin_cannot_remove"})
