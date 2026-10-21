# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Default org seeder — Phase 9 P06.

Seeds the reserved 'default' org row and backfills all existing pilots
from the pilots table into org_members as readonly scope.
"""
from __future__ import annotations

from src.services.audit_logger import _audit_path, _flock_append
from src.services.default_org_seeder_helpers import (
    DEFAULT_ORG_DISPLAY_NAME,
    DEFAULT_ORG_ID,
    FOUNDER_USER_ID,
    PLATFORM_FEE_PAID_UNTIL,
    SEED_RAW_PAYLOAD,
    TRIAL_EXPIRES_AT,
    _P02_TABLES,
    _db_path,
    _now_iso,
    _open_conn,
    _synthetic_email,
    _tables_present,
    verify_prereqs,
)


def seed_default_org(
    founder_email: str,
    dry_run: bool = False,
) -> dict[str, int]:
    """Seed the 'default' org and backfill pilots into org_members."""
    verify_prereqs()

    now = _now_iso()
    conn = _open_conn()

    try:
        pilot_rows = conn.execute(
            "SELECT user_id, onboarded_at FROM pilots WHERE org_id = 'default' "
            "OR org_id IS NULL"
        ).fetchall()

        if dry_run:
            existing_orgs = conn.execute(
                "SELECT COUNT(*) AS cnt FROM orgs WHERE org_id = ?",
                (DEFAULT_ORG_ID,),
            ).fetchone()["cnt"]

            existing_members = conn.execute(
                "SELECT COUNT(*) AS cnt FROM org_members WHERE org_id = ?",
                (DEFAULT_ORG_ID,),
            ).fetchone()["cnt"]

            total_to_insert = 1 + 1 + len(pilot_rows)
            orgs_would_insert = 1 if existing_orgs == 0 else 0
            members_to_insert = 1 + len(pilot_rows)
            members_would_insert = max(0, members_to_insert - existing_members)

            return {
                "orgs_inserted": orgs_would_insert,
                "members_inserted": members_would_insert,
                "pilots_seeded": max(0, members_would_insert - (1 if existing_members == 0 else 0)),
                "skipped": total_to_insert - orgs_would_insert - members_would_insert,
            }

        conn.execute("BEGIN IMMEDIATE")

        cursor_org = conn.execute(
            """
            INSERT OR IGNORE INTO orgs
                (org_id, display_name, status, platform_fee_paid_until,
                 trial_expires_at, created_at, created_by_email,
                 polar_org_subscription_id, raw_payload)
            VALUES (?, ?, 'active', ?, ?, ?, ?, NULL, ?)
            """,
            (
                DEFAULT_ORG_ID,
                DEFAULT_ORG_DISPLAY_NAME,
                PLATFORM_FEE_PAID_UNTIL,
                TRIAL_EXPIRES_AT,
                now,
                founder_email,
                SEED_RAW_PAYLOAD,
            ),
        )
        orgs_inserted = cursor_org.rowcount

        cursor_founder = conn.execute(
            """
            INSERT OR IGNORE INTO org_members
                (org_id, user_id, email, scope, joined_at, invited_by)
            VALUES (?, ?, ?, 'org_admin', ?, NULL)
            """,
            (DEFAULT_ORG_ID, FOUNDER_USER_ID, founder_email, now),
        )
        founder_inserted = cursor_founder.rowcount

        pilots_seeded = 0
        for row in pilot_rows:
            user_id = row["user_id"]
            joined_at = row["onboarded_at"] or now
            email = _synthetic_email(user_id)
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO org_members
                    (org_id, user_id, email, scope, joined_at, invited_by)
                VALUES (?, ?, ?, 'readonly', ?, ?)
                """,
                (DEFAULT_ORG_ID, user_id, email, joined_at, FOUNDER_USER_ID),
            )
            pilots_seeded += cur.rowcount

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    members_inserted = founder_inserted + pilots_seeded
    total_attempted = 1 + 1 + len(pilot_rows)
    skipped = total_attempted - orgs_inserted - members_inserted

    audit_record = {
        "event": "phase_9_p06_seed",
        "orgs_inserted": orgs_inserted,
        "members_inserted": members_inserted,
        "pilots_seeded": pilots_seeded,
        "ts": now,
    }
    try:
        _flock_append(_audit_path(), audit_record)
    except IOError:
        pass

    return {
        "orgs_inserted": orgs_inserted,
        "members_inserted": members_inserted,
        "pilots_seeded": pilots_seeded,
        "skipped": skipped,
    }


__all__ = [
    "FOUNDER_USER_ID",
    "DEFAULT_ORG_ID",
    "DEFAULT_ORG_DISPLAY_NAME",
    "PLATFORM_FEE_PAID_UNTIL",
    "TRIAL_EXPIRES_AT",
    "SEED_RAW_PAYLOAD",
    "_P02_TABLES",
    "_now_iso",
    "_synthetic_email",
    "_open_conn",
    "_tables_present",
    "verify_prereqs",
    "seed_default_org",
    "_db_path",
    "_flock_append",
    "_audit_path",
]
