# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Database schema initialization and connection management for InheritanceEngine."""

from __future__ import annotations

import sqlite3

SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS estates (
    estate_id TEXT PRIMARY KEY,
    decedent_name TEXT NOT NULL,
    decedent_id_number TEXT NOT NULL,
    decedent_dob TEXT NOT NULL,
    date_of_death TEXT NOT NULL,
    place_of_death TEXT NOT NULL,
    last_residence TEXT NOT NULL,
    place_of_opening TEXT NOT NULL,
    administrator_name TEXT,
    administrator_contact TEXT,
    succession_type TEXT NOT NULL DEFAULT 'INTESTATE',
    dedicated_worship_amount REAL NOT NULL DEFAULT 0.0,
    dedicated_worship_description TEXT,
    is_settled INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS estate_assets (
    asset_id TEXT PRIMARY KEY,
    estate_id TEXT NOT NULL,
    asset_name TEXT NOT NULL,
    category TEXT NOT NULL,
    estimated_value REAL NOT NULL,
    is_sole_ownership INTEGER NOT NULL DEFAULT 1,
    ownership_share REAL NOT NULL DEFAULT 1.0,
    net_estate_value REAL NOT NULL,
    legal_document_ref TEXT,
    location TEXT,
    is_for_worship INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (estate_id) REFERENCES estates(estate_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS estate_obligations (
    obligation_id TEXT PRIMARY KEY,
    estate_id TEXT NOT NULL,
    creditor_name TEXT NOT NULL,
    obligation_name TEXT NOT NULL,
    priority TEXT NOT NULL,
    amount REAL NOT NULL,
    paid_amount REAL NOT NULL DEFAULT 0.0,
    is_settled INTEGER NOT NULL DEFAULT 0,
    legal_basis TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (estate_id) REFERENCES estates(estate_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS wills (
    will_id TEXT PRIMARY KEY,
    estate_id TEXT NOT NULL,
    will_form TEXT NOT NULL,
    will_status TEXT NOT NULL DEFAULT 'VALID',
    date_created TEXT NOT NULL,
    place_created TEXT NOT NULL,
    notary_office_or_ubnd TEXT,
    notary_number TEXT,
    notary_date TEXT,
    witness_1_name TEXT,
    witness_1_id TEXT,
    witness_2_name TEXT,
    witness_2_id TEXT,
    oral_will_recorded_date TEXT,
    oral_will_certified_date TEXT,
    executor_name TEXT,
    worship_estate_assigned REAL NOT NULL DEFAULT 0.0,
    worship_manager_name TEXT,
    contents_summary TEXT,
    is_revoked INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (estate_id) REFERENCES estates(estate_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS heirs (
    heir_id TEXT PRIMARY KEY,
    estate_id TEXT NOT NULL,
    full_name TEXT NOT NULL,
    id_number TEXT NOT NULL,
    dob TEXT NOT NULL,
    relationship TEXT NOT NULL,
    heir_rank TEXT NOT NULL,
    is_alive_at_opening INTEGER NOT NULL DEFAULT 1,
    is_conceived_before_opening INTEGER NOT NULL DEFAULT 0,
    is_minor_or_disabled INTEGER NOT NULL DEFAULT 0,
    is_disqualified_art621 INTEGER NOT NULL DEFAULT 0,
    is_forgiven_in_will INTEGER NOT NULL DEFAULT 0,
    has_disclaimed_art620 INTEGER NOT NULL DEFAULT 0,
    is_substitutional_art652 INTEGER NOT NULL DEFAULT 0,
    substituting_for_name TEXT,
    eligibility_status TEXT NOT NULL DEFAULT 'ELIGIBLE',
    testamentary_share_percent REAL NOT NULL DEFAULT 0.0,
    testamentary_fixed_amount REAL NOT NULL DEFAULT 0.0,
    allocated_amount REAL NOT NULL DEFAULT 0.0,
    allocated_percentage REAL NOT NULL DEFAULT 0.0,
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (estate_id) REFERENCES estates(estate_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS disclaimers (
    disclaimer_id TEXT PRIMARY KEY,
    estate_id TEXT NOT NULL,
    heir_id TEXT NOT NULL,
    heir_name TEXT NOT NULL,
    declaration_date TEXT NOT NULL,
    notary_or_ubnd_office TEXT NOT NULL,
    notary_document_number TEXT NOT NULL,
    reason TEXT,
    is_for_debt_evasion INTEGER NOT NULL DEFAULT 0,
    is_valid INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (estate_id) REFERENCES estates(estate_id) ON DELETE CASCADE,
    FOREIGN KEY (heir_id) REFERENCES heirs(heir_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS division_agreements (
    agreement_id TEXT PRIMARY KEY,
    estate_id TEXT NOT NULL,
    division_date TEXT NOT NULL,
    procedure_type TEXT NOT NULL,
    notary_office TEXT NOT NULL,
    notary_doc_ref TEXT,
    public_posting_start_date TEXT,
    public_posting_end_date TEXT,
    public_posting_ubnd TEXT,
    total_gross_assets REAL NOT NULL,
    total_obligations_paid REAL NOT NULL,
    total_worship_amount REAL NOT NULL,
    total_distributable_estate REAL NOT NULL,
    distribution_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (estate_id) REFERENCES estates(estate_id) ON DELETE CASCADE
);
"""


def init_db(conn: sqlite3.Connection) -> None:
    """Execute SQLite schema scripts with foreign keys enabled."""
    conn.executescript(SCHEMA_DDL)


def create_connection(
    db_path: str, memory_conn: sqlite3.Connection | None = None
) -> tuple[sqlite3.Connection, sqlite3.Connection | None]:
    """Obtain or cache connection depending on disk vs memory mode."""
    if db_path == ":memory:":
        if memory_conn is None:
            memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
            memory_conn.row_factory = sqlite3.Row
            memory_conn.execute("PRAGMA foreign_keys = ON;")
        return memory_conn, memory_conn
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn, memory_conn


__all__ = ["init_db", "create_connection", "SCHEMA_DDL"]
