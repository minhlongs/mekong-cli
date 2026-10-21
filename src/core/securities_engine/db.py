# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""SQLite schema initialization and connection management for SecuritiesEngine."""

from __future__ import annotations

import pathlib
import sqlite3

SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS securities_offerings (
    offering_id TEXT PRIMARY KEY,
    enterprise_name TEXT NOT NULL,
    ticker_symbol TEXT NOT NULL,
    tax_id TEXT NOT NULL,
    offering_type TEXT NOT NULL,
    charter_capital_vnd REAL NOT NULL,
    shares_offered INTEGER NOT NULL,
    offering_price_vnd REAL NOT NULL,
    total_offering_value_vnd REAL NOT NULL,
    roe_prior_year_pct REAL NOT NULL,
    two_years_profitable INTEGER NOT NULL,
    has_accumulated_losses INTEGER NOT NULL,
    non_major_shareholder_count INTEGER NOT NULL,
    non_major_ratio_pct REAL NOT NULL,
    audit_verdict TEXT NOT NULL,
    ssc_registration_number TEXT UNIQUE NOT NULL,
    approval_date TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS securities_listings (
    listing_id TEXT PRIMARY KEY,
    ticker_symbol TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    exchange TEXT NOT NULL,
    listed_shares INTEGER NOT NULL,
    par_value_vnd REAL NOT NULL,
    market_cap_vnd REAL NOT NULL,
    charter_capital_vnd REAL NOT NULL,
    roe_pct REAL NOT NULL,
    operating_years INTEGER NOT NULL,
    shareholder_count_non_major INTEGER NOT NULL,
    audit_verdict TEXT NOT NULL,
    listing_decision_number TEXT UNIQUE NOT NULL,
    listing_date TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS margin_accounts (
    account_id TEXT PRIMARY KEY,
    investor_name TEXT NOT NULL,
    investor_id TEXT NOT NULL,
    brokerage_firm TEXT NOT NULL,
    total_asset_value_vnd REAL NOT NULL,
    loan_balance_vnd REAL NOT NULL,
    collateral_value_vnd REAL NOT NULL,
    margin_ratio_pct REAL NOT NULL,
    initial_margin_req_pct REAL NOT NULL,
    maintenance_margin_req_pct REAL NOT NULL,
    call_margin_trigger INTEGER NOT NULL,
    force_sell_trigger INTEGER NOT NULL,
    deficit_amount_vnd REAL NOT NULL,
    status TEXT NOT NULL,
    last_updated TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS securities_firm_safety (
    audit_id TEXT PRIMARY KEY,
    firm_name TEXT NOT NULL,
    tax_id TEXT NOT NULL,
    liquid_capital_vnd REAL NOT NULL,
    market_risk_vnd REAL NOT NULL,
    settlement_risk_vnd REAL NOT NULL,
    operational_risk_vnd REAL NOT NULL,
    total_risk_exposure_vnd REAL NOT NULL,
    capital_adequacy_ratio_pct REAL NOT NULL,
    safety_status TEXT NOT NULL,
    reporting_quarter TEXT NOT NULL,
    audit_date TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS practitioner_licenses (
    license_id TEXT PRIMARY KEY,
    practitioner_name TEXT NOT NULL,
    id_card_or_passport TEXT NOT NULL,
    license_type TEXT NOT NULL,
    ssc_license_number TEXT UNIQUE NOT NULL,
    issue_date TEXT NOT NULL,
    expiry_date TEXT NOT NULL,
    firm_affiliation TEXT NOT NULL,
    compliance_status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize database tables for SecuritiesEngine."""
    conn.executescript(SCHEMA_DDL)
    conn.commit()


def create_connection(
    db_path: pathlib.Path | str,
    memory_conn: sqlite3.Connection | None = None,
) -> tuple[sqlite3.Connection, sqlite3.Connection | None]:
    """Create a configured SQLite connection with row factory and WAL mode."""
    path_str = str(db_path)
    if path_str == ":memory:":
        if memory_conn is None:
            memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
            memory_conn.row_factory = sqlite3.Row
        return memory_conn, memory_conn

    conn = sqlite3.connect(path_str)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn, memory_conn


__all__ = ["SCHEMA_DDL", "init_db", "create_connection"]
