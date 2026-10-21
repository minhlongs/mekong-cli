# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Invite creation, acceptance, revocation, and listing endpoints for VN Org routes."""

from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status

from src.api.org_routes_models import (
    InviteCreateRequest, InviteCreateResponse, InviteOut, JoinResponse,
    _extract_email_from_jwt, _facade, _require_scope, magic_link_service,
)
from src.services.org_service import (
    AlreadyMemberError, InvalidInviteScopeError, InviteAlreadyUsedError,
    InviteEmailMismatchError, InviteExpiredError, InviteInvalidError,
    InviteRevokedOrUsedError, OrgNotFoundError, accept_invite, create_invite,
    list_invites, revoke_invite,
)

logger = logging.getLogger(__name__)
invites_router = APIRouter()


@invites_router.post(
    "/invite", response_model=InviteCreateResponse, status_code=201,
    dependencies=[Depends(_require_scope(["org_admin", "founder"]))],
)
async def create_invite_endpoint(
    req: InviteCreateRequest,
    authorization: Optional[str] = Header(default=None),
    org_id: Optional[str] = Query(default=None),
) -> InviteCreateResponse:
    """Send an invite email to invitee_email for the specified org."""
    facade = _facade()
    extract_fn = getattr(facade, "_extract_email_from_jwt", _extract_email_from_jwt) if facade else _extract_email_from_jwt
    create_invite_fn = getattr(facade, "create_invite", create_invite) if facade else create_invite

    actor_email = extract_fn(authorization)
    if not org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "org_id_required"})

    jwt_secret = os.environ.get("MEKONG_JWT_SECRET")
    actor_user_id = actor_email
    if authorization and authorization.startswith("Bearer ") and jwt_secret:
        raw_token = authorization[len("Bearer "):].strip()
        from src.services.admin_token_service import decode_jwt as _decode

        try:
            claims = _decode(raw_token, jwt_secret)
            actor_user_id = claims.get("sub", actor_email)
        except Exception:
            pass

    try:
        result = create_invite_fn(
            org_id=org_id, invitee_email=req.invitee_email,
            scope=req.scope, invited_by_user_id=actor_user_id,
        )
    except InvalidInviteScopeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "invalid_invite_scope", "message": str(exc)},
        )
    except AlreadyMemberError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "already_member"})
    except OrgNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "org_not_found"})

    logger.info("org.invite_created", extra={"org_id": org_id, "invitee": req.invitee_email, "actor": actor_email})
    return InviteCreateResponse(**result)


@invites_router.post("/join", response_model=JoinResponse, status_code=201)
async def join_org_endpoint(
    authorization: Optional[str] = Header(default=None),
    invite: Optional[str] = Query(default=None),
) -> JoinResponse:
    """Join an org by redeeming an invite."""
    facade = _facade()
    extract_fn = getattr(facade, "_extract_email_from_jwt", _extract_email_from_jwt) if facade else _extract_email_from_jwt
    accept_fn = getattr(facade, "accept_invite", accept_invite) if facade else accept_invite
    mls = getattr(facade, "magic_link_service", magic_link_service) if facade else magic_link_service

    joiner_email = extract_fn(authorization)
    if not invite:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "invite_id_required"})

    try:
        result = accept_fn(invite_id=invite, joiner_email=joiner_email)
    except InviteInvalidError:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail={"error": "invite_invalid"})
    except InviteExpiredError:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail={"error": "invite_expired"})
    except InviteRevokedOrUsedError:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail={"error": "invite_used_or_revoked"})
    except InviteEmailMismatchError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "invite_email_mismatch"})

    try:
        new_jwt, expires_at = mls.mint_jwt_for_email(joiner_email)
    except RuntimeError as exc:
        logger.error("org.join_jwt_remint_failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "jwt_remint_failed", "message": str(exc)},
        )

    logger.info("org.join", extra={"org_id": result["org_id"], "joiner": joiner_email, "scope": result["scope"]})
    return JoinResponse(
        org_id=result["org_id"], user_id=result["user_id"],
        scope=result["scope"], jwt=new_jwt, expires_at=expires_at,
    )


@invites_router.delete(
    "/invites/{invite_id}", status_code=204, response_class=Response, response_model=None,
    dependencies=[Depends(_require_scope(["org_admin", "founder"]))],
)
async def revoke_invite_endpoint(
    invite_id: str,
    authorization: Optional[str] = Header(default=None),
    org_id: Optional[str] = Query(default=None),
) -> None:
    """Revoke a pending invite (soft-delete via 'REVOKED' sentinel)."""
    facade = _facade()
    extract_fn = getattr(facade, "_extract_email_from_jwt", _extract_email_from_jwt) if facade else _extract_email_from_jwt
    revoke_fn = getattr(facade, "revoke_invite", revoke_invite) if facade else revoke_invite

    actor_email = extract_fn(authorization)
    try:
        revoke_fn(invite_id=invite_id, actor_email=actor_email)
    except InviteInvalidError:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail={"error": "invite_invalid"})
    except InviteAlreadyUsedError:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail={"error": "invite_already_used_or_revoked"})


@invites_router.get(
    "/invites", response_model=list[InviteOut],
    dependencies=[Depends(_require_scope(["org_admin", "founder"]))],
)
async def list_invites_endpoint(
    org_id: Optional[str] = Query(default=None),
    authorization: Optional[str] = Header(default=None),
) -> list[InviteOut]:
    """List pending (non-expired, non-redeemed) invites for an org."""
    if not org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "org_id_required"})

    facade = _facade()
    list_fn = getattr(facade, "list_invites", list_invites) if facade else list_invites
    return [InviteOut(**item) for item in list_fn(org_id)]

