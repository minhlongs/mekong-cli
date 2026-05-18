"""Org routes — org creation, member listing, member removal.

Endpoints:
  POST /v1/org/create                  — any valid JWT; creates org + re-mints JWT
  GET  /v1/org/me?org_id=<slug>        — any valid JWT scope; returns org summary
  DELETE /v1/org/members/{user_id}     — org_admin or founder scope required

JWT re-mint: after org creation the caller's JWT gains allowed_orgs=[org_id]
and scopes include org_admin. Client must swap the bearer token.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from src.api.vn_pilot_auth import _require_scope
from src.services import magic_link_service
from src.services.admin_token_service import JWTExpiredError, JWTInvalidError, decode_jwt
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

org_router = APIRouter(prefix="/v1/org", tags=["VN Org"])


# ---------- Pydantic models ----------


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


# ---------- Auth helpers ----------


def _extract_email_from_jwt(authorization: Optional[str]) -> str:
    """Decode bearer JWT and return sub (email) claim.

    Raises HTTPException 401 on any failure.
    """
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

    # Allow legacy admin token through (returns a placeholder email)
    legacy = os.environ.get("MEKONG_ADMIN_TOKEN")
    if legacy and raw_token == legacy:
        return "admin@legacy"

    try:
        claims = decode_jwt(raw_token, jwt_secret)
    except JWTExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except JWTInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    email = claims.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT missing sub claim",
        )
    return email


# ---------- Endpoints ----------


@org_router.post(
    "/create",
    response_model=OrgCreateResponse,
    status_code=201,
)
async def create_org_endpoint(
    req: OrgCreateRequest,
    authorization: Optional[str] = Header(default=None),
) -> OrgCreateResponse:
    """Create a new org. Caller becomes first org_admin.

    Returns a fresh JWT with the new org_id in allowed_orgs and
    org_admin in scopes. Client must swap bearer token.

    - 201: created successfully
    - 409: slug taken (with suggestions) or reserved
    - 422: display_name too short/long for slug generation
    - 401/503: auth failure
    """
    founder_email = _extract_email_from_jwt(authorization)

    try:
        result = create_org(req.display_name, founder_email)
    except ReservedSlugError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "slug_reserved"},
        )
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

    # Re-mint JWT so caller's token includes the new org
    try:
        new_jwt, expires_at = magic_link_service.mint_jwt_for_email(founder_email)
    except RuntimeError as exc:
        logger.error("org.create_jwt_remint_failed: %s", exc)
        # Org was created; JWT re-mint failed — return partial data with empty jwt
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "jwt_remint_failed", "message": str(exc)},
        )

    logger.info(
        "org.created",
        extra={"org_id": result["org_id"], "founder": founder_email},
    )

    return OrgCreateResponse(
        org_id=result["org_id"],
        user_id=result["user_id"],
        jwt=new_jwt,
        expires_at=expires_at,
        status=result["status"],
        trial_expires_at=result["trial_expires_at"],
    )


@org_router.get("/me", response_model=OrgMeResponse)
async def get_org_me(
    request: Request,
    org_id: Optional[str] = Query(default=None),
    authorization: Optional[str] = Header(default=None),
) -> OrgMeResponse:
    """Return the requester's org context (org details + member list).

    Auth: any valid JWT (no scope restriction — membership is the gate).
    org_id must be provided as query param OR derivable from JWT allowed_orgs
    (single-org members can omit it).

    - 200: org summary
    - 400: org_id ambiguous (multi-org JWT, param required) or missing
    - 403: org_id not in JWT allowed_orgs
    - 404: org not found
    - 401/503: auth failure
    """
    jwt_secret = os.environ.get("MEKONG_JWT_SECRET")
    legacy = os.environ.get("MEKONG_ADMIN_TOKEN")

    if not jwt_secret and not legacy:
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

    # Legacy admin token bypasses org resolution restriction
    is_legacy = legacy and raw_token == legacy
    allowed_orgs: list[str] = []

    if not is_legacy:
        if not jwt_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="JWT auth disabled",
            )
        try:
            claims = decode_jwt(raw_token, jwt_secret)
        except JWTExpiredError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
            )
        except JWTInvalidError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        allowed_orgs = claims.get("allowed_orgs", [])

    # Resolve org_id: from param, or auto-resolve for single-org JWTs
    resolved_org_id = org_id
    if resolved_org_id is None:
        if is_legacy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "org_id_required"},
            )
        if len(allowed_orgs) == 1:
            resolved_org_id = allowed_orgs[0]
        elif len(allowed_orgs) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "multi_org_jwt_specify_org_id"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "org_id_required"},
            )

    # Enforce org membership unless legacy token
    if not is_legacy and resolved_org_id not in allowed_orgs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "org_not_in_allowed_orgs"},
        )

    try:
        summary = get_org_summary(resolved_org_id)
    except OrgNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "org_not_found"},
        )

    return OrgMeResponse(**summary)


@org_router.delete(
    "/members/{user_id}",
    status_code=204,
    dependencies=[Depends(_require_scope(["org_admin", "founder"]))],
)
async def delete_org_member(
    user_id: str,
    authorization: Optional[str] = Header(default=None),
    org_id: Optional[str] = Query(default=None),
) -> None:
    """Remove a member from an org. Cannot remove last org_admin.

    - 204: removed successfully
    - 404: org or member not found
    - 409: last admin protection
    - 403: insufficient scope (enforced by dependency)
    """
    actor_email = _extract_email_from_jwt(authorization)

    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "org_id_required"},
        )

    try:
        remove_member(org_id, user_id, actor_email)
    except OrgNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "org_not_found"},
        )
    except MemberNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "member_not_found"},
        )
    except LastAdminError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "last_admin_cannot_remove"},
        )
