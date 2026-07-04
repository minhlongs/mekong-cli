"""Org routes — org creation, member listing, member removal, invite flow.

Endpoints (P02):
  POST /v1/org/create                  — any valid JWT; creates org + re-mints JWT
  GET  /v1/org/me?org_id=<slug>        — any valid JWT scope; returns org summary
  DELETE /v1/org/members/{user_id}     — org_admin or founder scope required

Endpoints (P03):
  POST /v1/org/invite?org_id=<slug>    — org_admin scope; sends invite email
  POST /v1/org/join?invite=<id>        — any valid JWT (post magic-link verify)
  DELETE /v1/org/invites/{invite_id}   — org_admin scope; revokes invite
  GET  /v1/org/invites?org_id=<slug>   — org_admin scope; list pending invites

JWT re-mint: after org creation or join, caller gets fresh JWT with updated
allowed_orgs + scopes. Client must swap bearer token.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field

from src.api.vn_pilot_auth import _require_scope
from src.services import magic_link_service
from src.services.admin_token_service import JWTExpiredError, JWTInvalidError, decode_jwt
from src.services.org_service import (
    AlreadyMemberError,
    InviteAlreadyUsedError,
    InviteEmailMismatchError,
    InviteExpiredError,
    InviteInvalidError,
    InviteRevokedOrUsedError,
    InvalidInviteScopeError,
    InvalidSlugError,
    LastAdminError,
    MemberNotFoundError,
    OrgNotFoundError,
    ReservedSlugError,
    SlugCollisionError,
    accept_invite,
    create_invite,
    create_org,
    get_org_summary,
    list_invites,
    remove_member,
    revoke_invite,
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


# P03 models

class InviteCreateRequest(BaseModel):
    invitee_email: str = Field(..., min_length=3, max_length=254)
    scope: str = Field(default="readonly")


class InviteCreateResponse(BaseModel):
    invite_id: str
    expires_at: str


class JoinRequest(BaseModel):
    pass  # joiner_email taken from JWT sub; invite_id from query param


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

    # Require authenticated JWT — legacy admin token bypass removed
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
    allowed_orgs: list[str] = []

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
    response_class=Response,
    response_model=None,
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


# =============================================================================
# Phase 9 P03 — Invite endpoints
# =============================================================================


@org_router.post(
    "/invite",
    response_model=InviteCreateResponse,
    status_code=201,
    dependencies=[Depends(_require_scope(["org_admin", "founder"]))],
)
async def create_invite_endpoint(
    req: InviteCreateRequest,
    authorization: Optional[str] = Header(default=None),
    org_id: Optional[str] = Query(default=None),
) -> InviteCreateResponse:
    """Send an invite email to invitee_email for the specified org.

    Auth: org_admin or founder JWT scope required.
    org_id taken from query param (required).

    - 201: invite created, email sent (or re-sent if pending invite existed)
    - 400: org_id missing
    - 409: invitee is already a member
    - 422: invalid scope value
    - 404: org not found
    - 401/403/503: auth errors
    """
    actor_email = _extract_email_from_jwt(authorization)

    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "org_id_required"},
        )

    # Resolve actor's user_id from org_members so it can be stored on the invite row
    jwt_secret = os.environ.get("MEKONG_JWT_SECRET")
    actor_user_id = actor_email  # fallback if JWT decode fails
    if authorization and authorization.startswith("Bearer ") and jwt_secret:
        raw_token = authorization[len("Bearer "):].strip()
        from src.services.admin_token_service import decode_jwt as _decode
        try:
            claims = _decode(raw_token, jwt_secret)
            # sub is email; use email as user_id proxy (invite.invited_by_user_id)
            actor_user_id = claims.get("sub", actor_email)
        except Exception:
            pass

    try:
        result = create_invite(
            org_id=org_id,
            invitee_email=req.invitee_email,
            scope=req.scope,
            invited_by_user_id=actor_user_id,
        )
    except InvalidInviteScopeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_invite_scope", "message": str(exc)},
        )
    except AlreadyMemberError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "already_member"},
        )
    except OrgNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "org_not_found"},
        )

    logger.info(
        "org.invite_created",
        extra={"org_id": org_id, "invitee": req.invitee_email, "actor": actor_email},
    )
    return InviteCreateResponse(**result)


@org_router.post(
    "/join",
    response_model=JoinResponse,
    status_code=201,
)
async def join_org_endpoint(
    authorization: Optional[str] = Header(default=None),
    invite: Optional[str] = Query(default=None),
) -> JoinResponse:
    """Join an org by redeeming an invite.

    Auth: any valid JWT (invitee must have verified via magic-link first).
    invite_id taken from query param (required).

    - 201: joined; response includes fresh JWT with new org in allowed_orgs
    - 400: invite_id missing or email mismatch
    - 410: invite expired or revoked/used
    - 401/503: auth failure
    """
    joiner_email = _extract_email_from_jwt(authorization)

    if not invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invite_id_required"},
        )

    try:
        result = accept_invite(invite_id=invite, joiner_email=joiner_email)
    except InviteInvalidError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"error": "invite_invalid"},
        )
    except InviteExpiredError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"error": "invite_expired"},
        )
    except InviteRevokedOrUsedError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"error": "invite_used_or_revoked"},
        )
    except InviteEmailMismatchError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invite_email_mismatch"},
        )

    # Re-mint JWT so new org membership is reflected in bearer token
    try:
        new_jwt, expires_at = magic_link_service.mint_jwt_for_email(joiner_email)
    except RuntimeError as exc:
        logger.error("org.join_jwt_remint_failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "jwt_remint_failed", "message": str(exc)},
        )

    logger.info(
        "org.join",
        extra={
            "org_id": result["org_id"],
            "joiner": joiner_email,
            "scope": result["scope"],
        },
    )
    return JoinResponse(
        org_id=result["org_id"],
        user_id=result["user_id"],
        scope=result["scope"],
        jwt=new_jwt,
        expires_at=expires_at,
    )


@org_router.delete(
    "/invites/{invite_id}",
    status_code=204,
    response_class=Response,
    response_model=None,
    dependencies=[Depends(_require_scope(["org_admin", "founder"]))],
)
async def revoke_invite_endpoint(
    invite_id: str,
    authorization: Optional[str] = Header(default=None),
    org_id: Optional[str] = Query(default=None),
) -> None:
    """Revoke a pending invite (soft-delete via 'REVOKED' sentinel).

    Auth: org_admin or founder JWT scope required.

    - 204: revoked successfully
    - 410: invite not found, already used, or already revoked
    - 401/403/503: auth errors
    """
    actor_email = _extract_email_from_jwt(authorization)

    try:
        revoke_invite(invite_id=invite_id, actor_email=actor_email)
    except InviteInvalidError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"error": "invite_invalid"},
        )
    except InviteAlreadyUsedError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"error": "invite_already_used_or_revoked"},
        )


@org_router.get(
    "/invites",
    response_model=list[InviteOut],
    dependencies=[Depends(_require_scope(["org_admin", "founder"]))],
)
async def list_invites_endpoint(
    org_id: Optional[str] = Query(default=None),
    authorization: Optional[str] = Header(default=None),
) -> list[InviteOut]:
    """List pending (non-expired, non-redeemed) invites for an org.

    Auth: org_admin or founder JWT scope required.
    org_id required as query param.

    - 200: list of pending invites (may be empty)
    - 400: org_id missing
    - 401/403/503: auth errors
    """
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "org_id_required"},
        )

    pending = list_invites(org_id)
    return [InviteOut(**item) for item in pending]
