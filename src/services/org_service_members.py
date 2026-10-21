# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Org creation, summary retrieval, and member management."""
from __future__ import annotations

import json
import secrets
import sqlite3
from typing import Any

from src.services.audit_logger import audit_admin_action
from src.services.org_service_models import (
    LastAdminError,
    MemberNotFoundError,
    OrgNotFoundError,
    ReservedSlugError,
    SlugCollisionError,
    _now_iso,
    _open_conn,
    _slug_exists,
    _trial_expires_iso,
    canonicalize_slug,
    is_reserved_slug,
    suggest_alternatives,
)


def create_org(display_name: str, founder_email: str) -> dict[str, Any]:
    """Create a new org with founder as first org_admin member."""
    slug = canonicalize_slug(display_name)
    if is_reserved_slug(slug):
        raise ReservedSlugError(f"Slug '{slug}' is reserved and cannot be used.")

    user_id = "opc_org_" + secrets.token_urlsafe(6)
    now = _now_iso()
    trial_expires = _trial_expires_iso()
    raw_payload = json.dumps({"display_name": display_name, "founder_email": founder_email})

    conn = _open_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        if _slug_exists(conn, slug):
            conn.rollback()
            raise SlugCollisionError(slug, suggest_alternatives(slug))

        conn.execute(
            "INSERT INTO orgs (org_id, display_name, status, platform_fee_paid_until, "
            "trial_expires_at, created_at, created_by_email, polar_org_subscription_id, raw_payload) "
            "VALUES (?, ?, 'unverified', NULL, ?, ?, ?, NULL, ?)",
            (slug, display_name, trial_expires, now, founder_email, raw_payload),
        )
        conn.execute(
            "INSERT INTO org_members (org_id, user_id, email, scope, joined_at, invited_by) "
            "VALUES (?, ?, ?, 'org_admin', ?, NULL)",
            (slug, user_id, founder_email, now),
        )
        conn.commit()
    except SlugCollisionError:
        raise
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        raise SlugCollisionError(slug, suggest_alternatives(slug)) from exc
    finally:
        conn.close()

    audit_admin_action(scope="org.created", org=slug, sub=founder_email, endpoint="/v1/org/create")
    return {
        "org_id": slug,
        "user_id": user_id,
        "display_name": display_name,
        "status": "unverified",
        "trial_expires_at": trial_expires,
    }


def get_org_summary(org_id: str) -> dict[str, Any]:
    """Return org metadata + member list."""
    conn = _open_conn()
    try:
        org_row = conn.execute(
            "SELECT org_id, display_name, status, trial_expires_at, "
            "platform_fee_paid_until, created_at, created_by_email FROM orgs WHERE org_id = ?",
            (org_id,),
        ).fetchone()
        if org_row is None:
            raise OrgNotFoundError(f"Org '{org_id}' not found")
        member_rows = conn.execute(
            "SELECT user_id, email, scope, joined_at FROM org_members WHERE org_id = ? ORDER BY joined_at",
            (org_id,),
        ).fetchall()
    finally:
        conn.close()

    members = [
        {"user_id": r["user_id"], "email": r["email"], "scope": r["scope"], "joined_at": r["joined_at"]}
        for r in member_rows
    ]
    return {
        "org_id": org_row["org_id"],
        "display_name": org_row["display_name"],
        "status": org_row["status"],
        "trial_expires_at": org_row["trial_expires_at"],
        "platform_fee_paid_until": org_row["platform_fee_paid_until"],
        "created_at": org_row["created_at"],
        "created_by_email": org_row["created_by_email"],
        "member_count": len(members),
        "members": members,
    }


def remove_member(org_id: str, user_id: str, actor_email: str) -> None:
    """Remove a member from an org. Cannot remove the last org_admin."""
    conn = _open_conn()
    try:
        if conn.execute("SELECT 1 FROM orgs WHERE org_id = ?", (org_id,)).fetchone() is None:
            raise OrgNotFoundError(f"Org '{org_id}' not found")
        member_row = conn.execute(
            "SELECT scope FROM org_members WHERE org_id = ? AND user_id = ?", (org_id, user_id)
        ).fetchone()
        if member_row is None:
            raise MemberNotFoundError(f"User '{user_id}' not in org '{org_id}'")
        if member_row["scope"] == "org_admin":
            admin_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM org_members WHERE org_id = ? AND scope = 'org_admin'", (org_id,)
            ).fetchone()["cnt"]
            if admin_count <= 1:
                raise LastAdminError(f"Cannot remove the last org_admin from '{org_id}'")
        conn.execute("DELETE FROM org_members WHERE org_id = ? AND user_id = ?", (org_id, user_id))
        conn.commit()
    finally:
        conn.close()

    audit_admin_action(scope="org.member_removed", org=org_id, sub=actor_email, endpoint="/v1/org/members")
