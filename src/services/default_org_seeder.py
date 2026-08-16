# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Default org seeder — Phase 9 P06.

Seeds the reserved 'default' org row and backfills all existing pilots
from the pilots table into org_members as readonly scope.

Public API:
    verify_prereqs() -> None      — raises RuntimeError on bad env/missing schema
    seed_default_org(founder_email, dry_run) -> dict[str, int]

DRY: reuses sqlite_migrations._db_path(), audit_logger.append_audit_event,
     org_service.RESERVED_SLUGS (for test cross-check only).

Idempotent: INSERT OR IGNORE throughout; safe to re-run after partial failure.
Single BEGIN/COMMIT transaction; rollback on any error.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone

from src.services.sqlite_migrations import _db_path
from src.services.audit_logger import _flock_append, _audit_path

# ---------- Constants ----------

FOUNDER_USER_ID = "opc_founder_001"
DEFAULT_ORG_ID = "default"
DEFAULT_ORG_DISPLAY_NAME = "Founder Default Org"
PLATFORM_FEE_PAID_UNTIL = "2099-12-31"
TRIAL_EXPIRES_AT = "2099-12-31"
SEED_RAW_PAYLOAD = '{"seed":"phase-9-p06"}'

_P02_TABLES = frozenset({"orgs", "org_members"})


# ---------- Internal helpers ----------


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"


def _synthetic_email(user_id: str) -> str:
    return f"{user_id}@pilot.mekong.local"


def _open_conn() -> sqlite3.Connection:
    """Open WAL-mode connection to pilot.db."""
    db = _db_path()
    conn = sqlite3.connect(str(db), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _tables_present(conn: sqlite3.Connection) -> bool:
    """Return True if both P02 tables (orgs, org_members) exist."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN (?,?)",
        tuple(_P02_TABLES),
    ).fetchall()
    return {r["name"] for r in rows} == _P02_TABLES


# ---------- Public API ----------


def verify_prereqs() -> None:
    """Raise RuntimeError if environment or schema prerequisites are not met.

    Checks:
    1. MEKONG_PILOT_STORAGE == "sqlite"
    2. pilot.db exists
    3. orgs + org_members tables present (P02 schema)

    Raises:
        RuntimeError: with human-readable hint for each failure.
    """
    storage = os.getenv("MEKONG_PILOT_STORAGE", "").lower()
    if storage != "sqlite":
        raise RuntimeError(
            "MEKONG_PILOT_STORAGE must be 'sqlite' to run the seeder. "
            f"Current value: '{storage}'. "
            "Run: export MEKONG_PILOT_STORAGE=sqlite"
        )

    db = _db_path()
    if not db.exists():
        raise RuntimeError(
            f"pilot.db not found at {db}. "
            "Run scripts/migrate-jsonl-to-sqlite.py first."
        )

    conn = _open_conn()
    try:
        if not _tables_present(conn):
            raise RuntimeError(
                "P02 schema (orgs + org_members tables) not present in pilot.db. "
                "Ensure Phase 9 P02 has been deployed before running this seeder."
            )
    finally:
        conn.close()


def seed_default_org(
    founder_email: str,
    dry_run: bool = False,
) -> dict[str, int]:
    """Seed the 'default' org and backfill pilots into org_members.

    Steps (single transaction):
    1. INSERT OR IGNORE default org row (status=active, perpetual billing).
    2. INSERT OR IGNORE founder as org_admin.
    3. SELECT all pilots; INSERT OR IGNORE each as org_members(scope=readonly).
    4. Append audit log entry on success (skipped on dry_run).

    Args:
        founder_email: Email stored as created_by_email and founder member email.
        dry_run:       If True, compute counts but do NOT write to DB or audit log.

    Returns:
        Dict with keys:
            orgs_inserted   — 0 or 1
            members_inserted — 0..N+1 (founder + pilots)
            pilots_seeded   — 0..N pilot members inserted
            skipped         — rows that already existed (INSERT OR IGNORE no-ops)

    Raises:
        RuntimeError: if verify_prereqs() fails (caller must run it first,
                      or will be re-raised here if called standalone).
    """
    verify_prereqs()

    now = _now_iso()
    conn = _open_conn()

    try:
        # ---------- Step 1: collect pilot rows (read before transaction) ----------
        pilot_rows = conn.execute(
            "SELECT user_id, onboarded_at FROM pilots WHERE org_id = 'default' "
            "OR org_id IS NULL"
        ).fetchall()

        if dry_run:
            # Count what WOULD be inserted (rows not already in target tables)
            existing_orgs = conn.execute(
                "SELECT COUNT(*) AS cnt FROM orgs WHERE org_id = ?",
                (DEFAULT_ORG_ID,),
            ).fetchone()["cnt"]

            existing_members = conn.execute(
                "SELECT COUNT(*) AS cnt FROM org_members WHERE org_id = ?",
                (DEFAULT_ORG_ID,),
            ).fetchone()["cnt"]

            total_to_insert = 1 + 1 + len(pilot_rows)  # org + founder + pilots
            orgs_would_insert = 1 if existing_orgs == 0 else 0
            # founder + N pilots
            members_to_insert = 1 + len(pilot_rows)
            members_would_insert = max(0, members_to_insert - existing_members)

            return {
                "orgs_inserted": orgs_would_insert,
                "members_inserted": members_would_insert,
                "pilots_seeded": max(0, members_would_insert - (1 if existing_members == 0 else 0)),
                "skipped": total_to_insert - orgs_would_insert - members_would_insert,
            }

        # ---------- Step 2: single transaction ----------
        conn.execute("BEGIN IMMEDIATE")

        # --- Insert default org ---
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

        # --- Insert founder as org_admin ---
        cursor_founder = conn.execute(
            """
            INSERT OR IGNORE INTO org_members
                (org_id, user_id, email, scope, joined_at, invited_by)
            VALUES (?, ?, ?, 'org_admin', ?, NULL)
            """,
            (DEFAULT_ORG_ID, FOUNDER_USER_ID, founder_email, now),
        )
        founder_inserted = cursor_founder.rowcount

        # --- Backfill pilots ---
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

    # ---------- Step 3: audit log ----------
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
        pass  # best-effort; never block seed success

    return {
        "orgs_inserted": orgs_inserted,
        "members_inserted": members_inserted,
        "pilots_seeded": pilots_seeded,
        "skipped": skipped,
    }
