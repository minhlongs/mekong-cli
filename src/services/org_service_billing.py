# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Org billing webhook state transitions (Polar.sh subscription hooks)."""
from __future__ import annotations

from src.services.audit_logger import audit_admin_action
from src.services.org_service_models import _open_conn


def mark_org_paid(
    org_id: str,
    polar_subscription_id: str,
    period_end: str,
) -> None:
    """Mark an org as paid after Polar subscription.created webhook.

    Idempotent: if org is already active with same subscription_id, no-op.

    Args:
        org_id: Org slug.
        polar_subscription_id: Polar subscription ID.
        period_end: ISO timestamp of current period end.
    """
    conn = _open_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")

        existing = conn.execute(
            "SELECT status, polar_org_subscription_id FROM orgs WHERE org_id = ?",
            (org_id,),
        ).fetchone()

        if existing is None:
            conn.rollback()
            return

        if (
            existing["status"] == "active"
            and existing["polar_org_subscription_id"] == polar_subscription_id
        ):
            conn.rollback()
            return

        conn.execute(
            """
            UPDATE orgs
            SET status = 'active',
                polar_org_subscription_id = ?,
                platform_fee_paid_until = ?
            WHERE org_id = ?
            """,
            (polar_subscription_id, period_end, org_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    audit_admin_action(
        scope="org.paid",
        org=org_id,
        sub=polar_subscription_id,
        endpoint="/v1/billing/webhook/org",
    )


def mark_org_cancelled(org_id: str) -> None:
    """Mark an org as cancelled after Polar subscription.cancelled webhook.

    Looks up org by polar_org_subscription_id to handle any org_id aliasing.
    Falls back to org_id if subscription_id not found.

    Args:
        org_id: Org slug (used for audit log; lookup is by polar_subscription_id).
    """
    conn = _open_conn()
    try:
        row = conn.execute(
            "SELECT org_id FROM orgs WHERE org_id = ? AND polar_org_subscription_id IS NOT NULL",
            (org_id,),
        ).fetchone()

        if row is None:
            row = conn.execute(
                "SELECT 1 FROM orgs WHERE org_id = ?",
                (org_id,),
            ).fetchone()
            if row is None:
                return

        conn.execute(
            "UPDATE orgs SET status = 'cancelled' WHERE org_id = ?",
            (org_id,),
        )
        conn.commit()
    finally:
        conn.close()

    audit_admin_action(
        scope="org.cancelled",
        org=org_id,
        sub="polar_webhook",
        endpoint="/v1/billing/webhook/org",
    )
