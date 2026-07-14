"""SQLite schema management for VN Pilot storage migration.

Provides ensure_schema(conn) — idempotent CREATE TABLE IF NOT EXISTS + indexes.
_db_path() resolves ~/.mekong/pilot.db via _state.CONFIG_DIR at call time
(so monkeypatch on vn_pilot_state.CONFIG_DIR propagates correctly).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import src.api.vn_pilot_state as _state


def _db_path() -> Path:
    """Resolve pilot.db path from CONFIG_DIR at call time."""
    return _state.CONFIG_DIR / "pilot.db"


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Idempotent schema creation. Safe to call multiple times.

    Creates 5 tables (pilots, conversions, poll_responses, pilot_credits)
    plus covering indexes for org_id/zalo/user_id/bank_tx_ref lookups.
    raw_payload TEXT column preserves full JSON for forward-compatibility
    — new fields added by writers surface via json.loads without migration.
    """
    conn.executescript("""
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;
        PRAGMA foreign_keys=ON;

        CREATE TABLE IF NOT EXISTS pilots (
            user_id        TEXT PRIMARY KEY,
            org_id         TEXT NOT NULL DEFAULT 'default',
            name           TEXT NOT NULL,
            zalo           TEXT NOT NULL,
            business_type  TEXT,
            city           TEXT,
            industry       TEXT,
            source         TEXT,
            onboarded_at   TEXT NOT NULL,
            pilot_end_at   TEXT NOT NULL,
            status         TEXT NOT NULL DEFAULT 'active',
            raw_payload    TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_pilots_org
            ON pilots(org_id);
        CREATE INDEX IF NOT EXISTS idx_pilots_org_zalo
            ON pilots(org_id, zalo);

        CREATE TABLE IF NOT EXISTS conversions (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        TEXT NOT NULL,
            org_id         TEXT NOT NULL DEFAULT 'default',
            tier           TEXT NOT NULL,
            monthly_vnd    INTEGER NOT NULL,
            started_at     TEXT NOT NULL,
            recorded_at    TEXT NOT NULL,
            bank_tx_ref    TEXT,
            raw_payload    TEXT NOT NULL,
            UNIQUE(user_id, started_at),
            UNIQUE(bank_tx_ref)
        );
        CREATE INDEX IF NOT EXISTS idx_conv_org
            ON conversions(org_id);
        CREATE INDEX IF NOT EXISTS idx_conv_user
            ON conversions(user_id);
        CREATE INDEX IF NOT EXISTS idx_conv_started
            ON conversions(started_at);

        CREATE TABLE IF NOT EXISTS poll_responses (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id        TEXT NOT NULL,
            score          INTEGER NOT NULL,
            comment        TEXT,
            iso_week       TEXT NOT NULL,
            recorded_at    TEXT NOT NULL,
            raw_payload    TEXT NOT NULL,
            UNIQUE(user_id, iso_week)
        );
        CREATE INDEX IF NOT EXISTS idx_resp_user_week
            ON poll_responses(user_id, iso_week);

        CREATE TABLE IF NOT EXISTS pilot_credits (
            user_id        TEXT PRIMARY KEY,
            balance        INTEGER NOT NULL DEFAULT 0
        );

CREATE TABLE IF NOT EXISTS subscriptions (
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id TEXT NOT NULL,
org_id TEXT NOT NULL DEFAULT 'default',
tier TEXT NOT NULL,
monthly_vnd INTEGER NOT NULL,
credits INTEGER NOT NULL DEFAULT 0,
status TEXT NOT NULL DEFAULT 'active',
started_at TEXT NOT NULL,
last_paid_at TEXT NOT NULL,
next_due_at TEXT NOT NULL,
bank_tx_ref TEXT,
renewal_count INTEGER NOT NULL DEFAULT 0,
raw_payload TEXT NOT NULL,
UNIQUE(user_id, bank_tx_ref)
);
CREATE INDEX IF NOT EXISTS idx_subs_user ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subs_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subs_next_due ON subscriptions(next_due_at);

        CREATE TABLE IF NOT EXISTS magic_link_tokens (
            token        TEXT PRIMARY KEY,
            email        TEXT NOT NULL,
            purpose      TEXT NOT NULL,
            org_id       TEXT,
            expires_at   TEXT NOT NULL,
            redeemed_at  TEXT,
            created_at   TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_magic_link_email_created
            ON magic_link_tokens(email, created_at);
    """)
    conn.commit()
