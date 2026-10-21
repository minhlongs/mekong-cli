# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Org routes facade — org creation, member listing/removal, and invite flow."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from src.api.org_routes_invites import (  # noqa: F401
    create_invite_endpoint,
    invites_router,
    join_org_endpoint,
    list_invites_endpoint,
    revoke_invite_endpoint,
)
from src.api.org_routes_members import (  # noqa: F401
    create_org_endpoint,
    delete_org_member,
    get_org_me,
    members_router,
)
from src.api.org_routes_models import (  # noqa: F401
    InviteCreateRequest,
    InviteCreateResponse,
    InviteOut,
    JoinRequest,
    JoinResponse,
    JWTExpiredError,
    JWTInvalidError,
    OrgCreateRequest,
    OrgCreateResponse,
    OrgMeResponse,
    OrgMemberOut,
    _extract_email_from_jwt,
    _require_scope,
    decode_jwt,
    magic_link_service,
)
from src.services.org_service import (  # noqa: F401
    AlreadyMemberError,
    InvalidInviteScopeError,
    InvalidSlugError,
    InviteAlreadyUsedError,
    InviteEmailMismatchError,
    InviteExpiredError,
    InviteInvalidError,
    InviteRevokedOrUsedError,
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
org_router.include_router(members_router)
org_router.include_router(invites_router)

__all__ = ["org_router"]
