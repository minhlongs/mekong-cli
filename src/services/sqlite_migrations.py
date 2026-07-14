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

        CREATE TABLE IF NOT EXISTS orgs (
 org_id TEXT PRIMARY KEY, display_name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'unverified', platform_fee_paid_until TEXT, trial_expires_at TEXT NOT NULL, created_at TEXT NOT NULL, created_by_email TEXT NOT NULL, polar_org_subscription_id TEXT, raw_payload TEXT NOT NULL );
CREATE INDEX IF NOT EXISTS idx_orgs_status ON orgs(status);
CREATE INDEX IF NOT EXISTS idx_orgs_created_at ON orgs(created_at);

CREATE TABLE IF NOT EXISTS org_members (
 org_id TEXT NOT NULL, user_id TEXT NOT NULL, email TEXT NOT NULL, scope TEXT NOT NULL DEFAULT 'org_admin', joined_at TEXT NOT NULL, invited_by TEXT, PRIMARY KEY (org_id, user_id) );
CREATE INDEX IF NOT EXISTS idx_members_org ON org_members(org_id);
CREATE INDEX IF NOT EXISTS idx_members_email ON org_members(email);

CREATE TABLE IF NOT EXISTS org_invites (
 invite_id TEXT PRIMARY KEY, org_id TEXT NOT NULL, invitee_email TEXT NOT NULL, invited_by_user_id TEXT, scope TEXT NOT NULL DEFAULT 'member', expires_at TEXT NOT NULL, created_at TEXT NOT NULL, redeemed_at TEXT );
CREATE INDEX IF NOT EXISTS idx_invites_org ON org_invites(org_id);
CREATE INDEX IF NOT EXISTS idx_invites_email ON org_invites(invitee_email);

CREATE TABLE IF NOT EXISTS polar_webhook_events (
 event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, received_at TEXT NOT NULL, org_id TEXT, raw_payload TEXT NOT NULL, processed_ok INTEGER NOT NULL DEFAULT 1 );
CREATE INDEX IF NOT EXISTS idx_webhook_events_org ON polar_webhook_events(org_id);
CREATE INDEX IF NOT EXISTS idx_webhook_events_type ON polar_webhook_events(event_type);

CREATE TABLE IF NOT EXISTS audit_log (
 id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT NOT NULL, org TEXT, sub TEXT, endpoint TEXT NOT NULL, detail TEXT, created_at TEXT NOT NULL );
CREATE INDEX IF NOT EXISTS idx_audit_org ON audit_log(org);
CREATE INDEX IF NOT EXISTS idx_audit_scope ON audit_log(scope);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at);

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
