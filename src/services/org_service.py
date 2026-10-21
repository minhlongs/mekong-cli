# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Org service — slug canonicalization, org creation, member management, invites.

Backed by the SQLite orgs + org_members + org_invites tables (P02/P03 schemas).
All writes are atomic via explicit transactions. Zero new pip dependencies.
"""
from __future__ import annotations

import src.api.vn_pilot_state as _state
from src.services import magic_link_service, resend_client
from src.services.audit_logger import audit_admin_action
from src.services.org_service_billing import (
    mark_org_cancelled,
    mark_org_paid,
)
from src.services.org_service_invites import (
    _build_invite_email_body,
    accept_invite,
    create_invite,
    list_invites,
    revoke_invite,
)
from src.services.org_service_members import (
    create_org,
    get_org_summary,
    remove_member,
)
from src.services.org_service_models import (
    RESERVED_SLUGS,
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
    _ALLOW_RE,
    _COLLAPSE_RE,
    _SLUG_MAX,
    _SLUG_MIN,
    _VALID_INVITE_SCOPES,
    _db_path,
    _invite_expires_iso,
    _now_iso,
    _open_conn,
    _slug_exists,
    _trial_expires_iso,
    _txn,
    canonicalize_slug,
    is_reserved_slug,
    suggest_alternatives,
)
from src.services.sqlite_migrations import ensure_schema

__all__ = [
    "RESERVED_SLUGS",
    "_SLUG_MAX",
    "_SLUG_MIN",
    "_COLLAPSE_RE",
    "_ALLOW_RE",
    "_VALID_INVITE_SCOPES",
    "InvalidSlugError",
    "ReservedSlugError",
    "SlugCollisionError",
    "OrgNotFoundError",
    "MemberNotFoundError",
    "LastAdminError",
    "AlreadyMemberError",
    "InviteInvalidError",
    "InviteExpiredError",
    "InviteRevokedOrUsedError",
    "InviteEmailMismatchError",
    "InvalidInviteScopeError",
    "InviteAlreadyUsedError",
    "_db_path",
    "_open_conn",
    "_txn",
    "_now_iso",
    "_trial_expires_iso",
    "_invite_expires_iso",
    "canonicalize_slug",
    "is_reserved_slug",
    "suggest_alternatives",
    "_slug_exists",
    "create_org",
    "get_org_summary",
    "remove_member",
    "_build_invite_email_body",
    "create_invite",
    "accept_invite",
    "revoke_invite",
    "list_invites",
    "mark_org_paid",
    "mark_org_cancelled",
    "_state",
    "magic_link_service",
    "resend_client",
    "audit_admin_action",
    "ensure_schema",
]
